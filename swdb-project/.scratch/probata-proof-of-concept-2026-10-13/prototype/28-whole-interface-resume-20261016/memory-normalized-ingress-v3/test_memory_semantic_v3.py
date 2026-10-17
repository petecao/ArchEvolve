"""2026-10-16 ET. Source-only memory observer rebind; no actual complete TU."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'memory-normalized-ingress-v2';MODULES=HERE/'observer/modules'
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('memory controls forbid child/native/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':raise RuntimeError('memory controls forbid installed project imports')
sys.addaudithook(audit)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)

class Controls(unittest.TestCase):
    def test_exact_observer_inverses_and_old_unchanged_modules(self):
        inverse=json.loads((HERE/'exact-inverses-v3.json').read_bytes())
        for relative,row in inverse['files'].items():
            text=(HERE/relative).read_text()
            for change in reversed(row['replacements']):
                self.assertEqual(text.count(change['new']),change['count']);text=text.replace(change['new'],change['old'])
            self.assertEqual(text.encode(),Path(row['basis']['path']).read_bytes())
        old=json.loads((OLD/'observer/fixed-memory-modules-v1.json').read_bytes())['modules']
        changed={'memory_normalized_compiler_adapter_v1.py','memory_normalized_capture_ingress_v1.py','observation_source_bridge_v1.py'}
        for row in old:
            if row['file'] not in changed:self.assertEqual((MODULES/row['file']).read_bytes(),(OLD/'observer/modules'/row['file']).read_bytes())
        for name in ('memory_normalized_compiler_adapter_v1.py','memory_normalized_capture_ingress_v1.py'):
            self.assertEqual((MODULES/name).read_bytes(),(WHOLE/'production-union-v1/proposed/swdb/_dx100_whole'/name).read_bytes())

    def test_inventory_exact15_and_distinct_readers(self):
        manifest=json.loads((HERE/'observer/fixed-memory-modules-v2.json').read_bytes());rows=manifest['modules']
        self.assertEqual(len(rows),15);self.assertEqual(len({row['module'] for row in rows}),15)
        for row in rows:
            raw=(MODULES/row['file']).read_bytes();self.assertEqual((len(raw),sha(raw)),(row['bytes'],row['sha256']))
        self.assertEqual(sha((MODULES/'compiler_unit_adapter_v3.py').read_bytes()),'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        self.assertEqual(sha((MODULES/'compiler_unit_adapter_v4.py').read_bytes()),'b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6')

    def test_real_memory_consumer_physical_and_same_module_gates(self):
        tree=ast.parse((MODULES/'memory_normalized_capture_ingress_v1.py').read_bytes())
        loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and ast.unparse(n.target)=='(module, expected)')
        gate=next(n for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
            and n.value.func.id=='need' and len(n.value.args)==2 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=='one selected semantic full-TU consumer required')
        ns={'Path':Path,'hashlib':hashlib,'need':need}
        for alias,name in {'codec':'lossless_gzip_v2.py','normalizer':'role_normalized_gzip_v2.py','closed':'closed_python_surface.py',
            'memory_compiler':'memory_normalized_compiler_adapter_v1.py'}.items():ns[alias]=SimpleNamespace(__file__=str(MODULES/name))
        reader=SimpleNamespace(__file__=str(MODULES/'compiler_unit_adapter_v4.py'));ns['source']=SimpleNamespace(semantic_compiler=reader)
        ns['memory_compiler'].consumer=reader;ns['memory_compiler'].CONSUMER_SHA=sha((MODULES/'compiler_unit_adapter_v4.py').read_bytes())
        for alias,key in [('codec','CODEC_SHA'),('normalizer','NORMALIZER_SHA'),('closed','CLOSED_SHA'),('memory_compiler','MEMORY_COMPILER_SHA')]:ns[key]=sha(Path(ns[alias].__file__).read_bytes())
        def absolute(row,**_):need(sha(Path(row['path']).read_bytes())==row['sha256'],'actual physical reader differs')
        ns['reads']=SimpleNamespace(absolute=absolute)
        code=compile(ast.Module(body=[loop,gate],type_ignores=[]),'<exact-memory-reader-gates>','exec');exec(code,ns)
        ns['source'].semantic_compiler=SimpleNamespace(__file__=str(MODULES/'compiler_unit_adapter_v3.py'))
        with self.assertRaises(ValueError):exec(code,ns)
        ns['source'].semantic_compiler=SimpleNamespace(__file__=reader.__file__)
        with self.assertRaises(ValueError):exec(code,ns)

    def test_real18_control_readset_and_changed_module_refusal(self):
        policy=json.loads((HERE/'observer/observation-policy-template-v2.json').read_bytes())
        observer=runpy.run_path(str(HERE/'observer/observe_memory_entry_v1.py'),run_name='memory_control_functions_only')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();selected=dict(policy,controls={})
            for name,row in policy['controls'].items():
                source=HERE/'observer'/name if (HERE/'observer'/name).exists() else MODULES/name
                raw=source.read_bytes();target=root/name;target.write_bytes(raw)
                selected['controls'][name]={'path':str(target),'bytes':len(raw),'sha256':sha(raw)}
            values,modules=observer['controls'](selected,root);self.assertEqual((len(values),len(modules)),(18,15))
            for name in ('compiler_unit_adapter_v3.py','compiler_unit_adapter_v4.py','memory_normalized_compiler_adapter_v1.py'):
                (root/name).write_bytes(values[name]+b'\n')
                with self.assertRaises(ValueError):observer['controls'](selected,root)
                (root/name).write_bytes(values[name])

    def test_genuine_memory_capture_and_three_root_consumer_unchanged(self):
        policy=json.loads((HERE/'observer/observation-policy-template-v2.json').read_bytes())
        previous=json.loads((OLD/'observer/observation-policy-template-v1.json').read_bytes())
        expected=json.loads(json.dumps(previous['capture']).replace('memory-unit-observation-2baf722f-v2','memory-unit-observation-2baf722f-v3'))
        self.assertEqual(policy['capture'],expected);self.assertIsNone(policy['capture']['prepared'])
        self.assertEqual(policy['capture']['original']['abi']['sha256'],'493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c')
        for name in ('source_memory_selection_v1.py','memory_source_preparation_v1.py','memory_capture_facts_v1.json'):
            self.assertEqual((MODULES/name).read_bytes(),(OLD/'observer/modules'/name).read_bytes())
        text=(MODULES/'memory_normalized_capture_ingress_v1.py').read_text()
        self.assertIn('tu = source.semantic_compiler.resolve_locations(source.semantic_compiler.parse_json_roots',text)
        self.assertIn("'whole-interface-original-tu-preparation-1'",(HERE/'observer/observe_memory_entry_v1.py').read_text())

if __name__=='__main__':unittest.main(verbosity=2)

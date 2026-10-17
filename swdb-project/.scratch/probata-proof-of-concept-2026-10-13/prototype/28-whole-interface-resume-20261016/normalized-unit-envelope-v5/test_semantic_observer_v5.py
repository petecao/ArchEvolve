"""2026-10-16 ET. Exact semantic module/physical/receipt seams; no large TU."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'normalized-unit-envelope-v4'
DEPENDENTS=WHOLE/'abi-semantic-dependents-v1'
ENV=runpy.run_path(str(HERE/'test_envelope_v5.py'),run_name='no_child_envelope_pure_functions')
SMALL=runpy.run_path(str(WHOLE/'abi-enum-repair-v1/test_enum_repair_v1.py'),run_name='reviewed_actual_small_ABI_metadata_controls')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def nodes(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def module(name):return HERE/'observer/modules'/name

class SemanticObserverControls(unittest.TestCase):
    def test_all_exact_source_inverses_and_legacy_reader_preserved(self):
        for relative,row in json.loads((HERE/'exact-inverses-v5.json').read_bytes())['files'].items():
            text=(HERE/relative).read_text()
            for change in reversed(row['replacements']):
                self.assertEqual(text.count(change['new']),change['count']);text=text.replace(change['new'],change['old'])
            original=Path(row['basis']['path']).read_bytes()
            self.assertEqual(sha(original),row['basis']['sha256']);self.assertEqual(text.encode(),original)
        self.assertEqual(sha(module('compiler_unit_adapter_v3.py').read_bytes()),'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        self.assertEqual(sha(module('compiler_unit_adapter_v4.py').read_bytes()),'b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6')
        old=nodes(module('compiler_unit_adapter_v3.py'));new=nodes(module('compiler_unit_adapter_v4.py'))
        for name in old:
            if name!='observed_abi':self.assertEqual(old[name],new[name])

    def test_real_primitive_pin_loop_and_same_reader_gate(self):
        path=module('normalized_capture_ingress_v2.py');tree=ast.parse(path.read_bytes())
        loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple)
            and ast.unparse(n.target)=='(module, expected)')
        gate=next(n for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and len(n.value.args)==2
            and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=='normalized adapter must use the same selected semantic compiler module')
        def need(ok,message):
            if not ok:raise ValueError(message)
        def absolute(row):
            raw=Path(row['path']).read_bytes();need((len(raw),sha(raw))==(row['bytes'],row['sha256']),'actual physical module pin differs')
        ns={'Path':Path,'hashlib':hashlib,'need':need,'reads':SimpleNamespace(absolute=absolute)}
        for key,file in {'normalizer':'role_normalized_gzip_v2.py','codec':'lossless_gzip_v2.py',
            'closed':'closed_python_surface.py','normalized_compiler':'normalized_compiler_adapter_v1.py'}.items():
            ns[key]=SimpleNamespace(__file__=str(module(file)))
        reader=SimpleNamespace(__file__=str(module('compiler_unit_adapter_v4.py')))
        ns['source']=SimpleNamespace(compiler=SimpleNamespace(__file__=str(module('compiler_unit_adapter_v3.py'))),semantic_compiler=reader)
        ns['normalized_compiler'].consumer=reader;ns['normalized_compiler'].CONSUMER_SHA=sha(module('compiler_unit_adapter_v4.py').read_bytes())
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.Assign)],type_ignores=[]),'<exact-ingress-constants>','exec'),ns)
        code=compile(ast.Module(body=[loop,gate],type_ignores=[]),'<real-physical-and-object-identity-gates>','exec')
        exec(code,ns)
        ns['source'].semantic_compiler=ns['source'].compiler
        with self.assertRaises(ValueError):exec(code,ns)
        ns['source'].semantic_compiler=reader
        ns['normalized_compiler'].consumer=SimpleNamespace(__file__=reader.__file__)
        with self.assertRaises(ValueError):exec(code,ns)
        ns['normalized_compiler'].consumer=reader
        ns['normalized_compiler'].CONSUMER_SHA='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
        with self.assertRaises(ValueError):exec(code,ns)

    def test_preparation_tail_real_ABI_reader_and_receipt_merge_both_families(self):
        # Only the exact adapter tail is executed. The large full-TU validation
        # prefix is not exercised or claimed by this small deterministic seam.
        for filename,row in zip(('normalized_compiler_adapter_v1.py','memory_normalized_compiler_adapter_v1.py'),SMALL['ACTUAL']):
            path=DEPENDENTS/'proposed/swdb/_dx100_whole'/filename
            tree=ast.parse(path.read_bytes());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_unit')
            start=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(
                isinstance(t,ast.Name) and t.id in ('legacy_path','path') for t in n.targets))
            tail=copy.deepcopy(function);tail.body=function.body[start:]
            def prepare(api,**kwargs):
                observation=SMALL['run_reader'](SMALL['proposal'],kwargs['abi_raw'],row)
                return {'schema':'whole-interface-original-tu-preparation-1','raw_full_tu_sha256':ns['EXPANDED_SHA'],
                    'original_source_sha256':ns.get('SOURCE_SHA'), 'public_admission':False,'abi_observation':observation}
            consumer=SimpleNamespace(__file__=str(module('compiler_unit_adapter_v4.py')),prepare_unit=prepare)
            ns={'Path':Path,'hashlib':hashlib,'consumer':consumer,'abi_transport':SMALL['helper']}
            selected=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef)) and (not isinstance(n,ast.FunctionDef) or n.name=='need')]
            exec(compile(ast.Module(body=selected,type_ignores=[]),'<exact-adapter-constants>','exec'),ns)
            ns['check_cases']=lambda prepared:None  # Caller/source-case census is outside this ABI tail seam.
            exec(compile(ast.Module(body=[tail],type_ignores=[]),'<exact-adapter-semantic-ABI-tail>','exec'),ns)
            result=ns['prepare_unit']({},transport_kind=ns['KIND'],full_tu_raw=b'not-a-TU-and-not-admitted',abi_raw=row['raw'],
                source_path='/not-consumed-by-tail',source_bytes=b'',probe_path=row['path'],probe_bytes=row['probe'],
                declarations=[],compiler_capture_pin='a'*64,full_tu_compressed_bytes=1,full_tu_expanded_limit=1)
            observed=result['abi_observation'];semantic=observed['semantic_enum_interpretation']
            self.assertEqual(observed['original_raw_probe_sha256'],sha(row['raw']))
            self.assertEqual(observed['raw_probe_sha256'],sha(row['derived']))
            self.assertEqual(observed['paired_type_role_transport'],row['receipt'])
            self.assertEqual(semantic['role_derived_strict_ABI']['sha256'],sha(row['derived']))
            self.assertIs(semantic['interpretation_is_reversible_AST_transport'],False)
            self.assertIs(result['public_admission'],False)
            ns['consumer']=SimpleNamespace(__file__=str(module('compiler_unit_adapter_v3.py')),prepare_unit=prepare)
            with self.assertRaises(ValueError):ns['prepare_unit']({},transport_kind='',full_tu_raw=b'',abi_raw=row['raw'],
                source_path='',source_bytes=b'',probe_path=row['path'],probe_bytes=row['probe'],declarations=[],
                compiler_capture_pin='',full_tu_compressed_bytes=1,full_tu_expanded_limit=1)

    def test_real_16_control_stage_and_hash_rechecks(self):
        ns=ENV['namespace']();command=json.loads((HERE/'command-v5.json').read_bytes());policy=json.loads((HERE/'envelope-policy-v5.json').read_bytes())
        observer=runpy.run_path(str(HERE/'observer/observe_entry_v3.py'),run_name='observer_control_functions_only')
        with tempfile.TemporaryDirectory() as directory:
            raw=Path(directory).resolve()/ns['RAW_NAME'];(raw/'control').mkdir(parents=True)
            selected=json.loads(json.dumps(policy).replace(command['raw'],str(raw)))
            for name,origin in command['stage_sources'].items():
                target=raw/'control'/name;target.write_bytes(Path(origin['path']).read_bytes());selected['controls'][name]=ns['pin'](target)
            observed=json.loads(json.dumps(json.loads((HERE/'observation-policy-v1.json').read_bytes())).replace(command['raw'],str(raw)))
            for name in observed['controls']:observed['controls'][name]={**selected['controls'][name],'path':str(raw/'observer/control'/name)}
            target=raw/'control/observation-policy-v1.json';target.write_text(json.dumps(observed,sort_keys=True,separators=(',',':')))
            selected['controls'][target.name]=ns['pin'](target);selected['observer_policy']={**ns['pin'](target),'path':str(raw/'observer/control'/target.name)}
            ns['stage_layout'](raw,selected)
            values,modules=observer['controls'](observed,raw/'observer/control')
            self.assertEqual((len(values),len(modules)),(16,14))
            self.assertEqual(set(values),set(ns['OBSERVER_CONTROLS']))
            for name in ('compiler_unit_adapter_v3.py','compiler_unit_adapter_v4.py','normalized_compiler_adapter_v1.py'):
                file=raw/'observer/control'/name;file.write_bytes(values[name]+b'\n')
                with self.assertRaises(ValueError):observer['controls'](observed,raw/'observer/control')
                file.write_bytes(values[name])

    def test_explicit_module_order_original_capture_and_public_equality_boundary(self):
        manifest=json.loads((HERE/'observer/fixed-modules-v3.json').read_bytes());rows=manifest['modules'];order={r['module']:i for i,r in enumerate(rows)}
        self.assertEqual(manifest['compatibility_module_alias'],{})
        self.assertLess(order['swdb._dx100_whole.compiler_unit_adapter_v3'],order['swdb.dx100_checked_source'])
        self.assertLess(order['swdb._dx100_whole.compiler_unit_adapter_v4'],order['swdb.dx100_checked_source'])
        self.assertLess(order['swdb._dx100_whole.abi_role_transport_v1'],order['swdb._dx100_whole.normalized_compiler_adapter_v1'])
        selected=json.loads((HERE/'observation-policy-v1.json').read_bytes());old=json.loads((OLD/'observation-policy-v1.json').read_bytes())
        self.assertEqual(selected['capture'],json.loads(json.dumps(old['capture']).replace('unit-observation-2baf722f-v4','unit-observation-2baf722f-v5')))
        self.assertIsNone(selected['capture']['prepared'])
        public=module('normalized_capture_ingress_v2.py').read_text();private=module('normalized_unit_observation_v1.py').read_text()
        self.assertIn("need(prepared==reads.document(selected['prepared'])",public)
        self.assertNotIn("need(prepared==reads.document(selected['prepared'])",private)
        for source in (public,private):
            self.assertIn('tu=source.semantic_compiler.resolve_locations(source.semantic_compiler.parse_json_roots',source)
            self.assertNotIn('tu=source.compiler.resolve_locations',source)

if __name__=='__main__':unittest.main(verbosity=2)

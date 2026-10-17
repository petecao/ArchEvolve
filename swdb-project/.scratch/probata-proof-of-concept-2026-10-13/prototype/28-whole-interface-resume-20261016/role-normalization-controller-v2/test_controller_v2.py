"""Source/AST/local synthetic quota tests; never execute controller/bootstrap."""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent
EVENTS=[]
def child_audit(event,args):
    if event.startswith(('subprocess.','socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise AssertionError('no child/network/native '+event)
sys.addaudithook(child_audit)
SOURCE=(HERE/'normalization_controller_v2.py').read_bytes();TREE=ast.parse(SOURCE)
def extract(names,ns):
    nodes=[n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==names;exec(compile(ast.Module(nodes,type_ignores=[]),'inert_projected_controller','exec'),ns);return ns
def literal(name):return ast.literal_eval(next(n.value for n in TREE.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
class Controls(unittest.TestCase):
    def test_embedded_policy_sources_and_all_input_bindings_agree(self):
        policy=json.loads(base64.b64decode(literal('POLICY_B64')))
        self.assertEqual((HERE/'source_policy_v2.json').read_bytes(),base64.b64decode(literal('POLICY_B64')))
        for name,key in [('NORMALIZER_B64','normalizer'),('CENSUS_B64','census')]:
            raw=base64.b64decode(literal(name));self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(policy[key]['bytes'],policy[key]['sha256']))
        self.assertEqual(len(policy['original_commands']),4);self.assertEqual([r['returncode'] for r in policy['original_commands']],[0]*4)
        for row in policy['original_commands']:
            for key in ('stdout','stderr'):
                output=row[key];self.assertEqual(policy['physical_inputs'][output['path']],{k:output[k] for k in ('bytes','sha256')})
    def test_exact_template_substitution_and_closed_command_profile(self):
        template=(HERE/'controller_template.py').read_text();entry=SOURCE.decode()
        for key in ('POLICY','NORMALIZER','CENSUS'):entry=entry.replace(literal(key+'_B64'),'__'+key+'_B64__',1)
        self.assertEqual(entry,template)
        command=json.loads((HERE/'command_v2.json').read_bytes());self.assertEqual(command['stdin']['sha256'],hashlib.sha256(SOURCE).hexdigest())
        self.assertEqual(command['limits']['expanded_normalized_bytes'],201326592)
        self.assertEqual((literal('TOTAL'),literal('FILE'),literal('RESERVE'),literal('FLOOR')),(268435456,134217728,1048576,53687091200))
        self.assertNotIn('SWDB_VERIFIER_RUN_TOKEN',command['closed_environment']);self.assertFalse(command['actual_executed'])
    def test_projected_write_gate_uses_next_bytes_and_preserves_reserve(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='quota-only-') as temp:
            root=Path(temp).resolve();(root/'control').mkdir();(root/'component').mkdir();target=root/'component/a';target.write_bytes(b'x'*90)
            ns={'Path':Path,'OUT':root,'FILES':{'component/a'},'DIRS':{root,root/'control',root/'component'},'TOTAL':100,'FILE':100,'RESERVE':10,'FLOOR':0,
                'stat':stat,'shutil':shutil,'time':SimpleNamespace(monotonic=lambda:0),'START':0}
            extract({'Refused','need','extent','write_gate'},ns)
            ns['write_gate'](0)
            with self.assertRaises(ns['Refused']):ns['write_gate'](1)
            ns['write_gate'](10,True)
            with self.assertRaises(ns['Refused']):ns['write_gate'](11,True)
            self.assertEqual(target.stat().st_size,90)
            ns['FLOOR']=shutil.disk_usage(root).free+1
            with self.assertRaises(ns['Refused']):ns['write_gate'](0,True)
    def test_topology_alias_and_special_inputs_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='pin-only-') as temp:
            root=Path(temp).resolve();actual=root/'actual';actual.write_bytes(b'abc');alias=root/'alias';alias.symlink_to(actual)
            ns={'Path':Path,'stat':stat,'hashlib':hashlib};extract({'Refused','need','stable','pin'},ns)
            self.assertEqual(ns['pin'](actual)['sha256'],hashlib.sha256(b'abc').hexdigest())
            with self.assertRaises(ns['Refused']):ns['pin'](alias)
            with self.assertRaises(ns['Refused']):ns['pin'](root)
    def test_primitive_bytes_checked_before_exec(self):
        ns={'hashlib':hashlib};extract({'Refused','need','sha','load'},ns)
        source=b'value=3\n';expected={'bytes':len(source),'sha256':hashlib.sha256(source).hexdigest()}
        self.assertEqual(ns['load'](source,'inert_bytes',expected)['value'],3)
        with self.assertRaises(ns['Refused']):ns['load'](source+b'value=4\n','inert_bytes',expected)
    def test_early_audit_and_resource_setters_are_closed_before_imports(self):
        boot=(HERE/'bootstrap_v2.py').read_text();tree=ast.parse(boot)
        ns={}
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'OUTPUT_ROOT','OUTPUT_PATHS'} for t in node.targets):
                exec(compile(ast.Module([node],type_ignores=[]),'inert_bootstrap_constants','exec'),ns)
        hook=next(n for n in tree.body if getattr(n,'name',None)=='bootstrap_audit');exec(compile(ast.Module([hook],type_ignores=[]),'inert_audit_only','exec'),ns)
        audit=ns['bootstrap_audit'];audit('open',(ns['OUTPUT_PATHS'][0],'x',64|128|1));audit('open',('/read','rb',524288))
        for args in [('/outside','x',64|128|1),(ns['OUTPUT_PATHS'][0],'w',64|1),(3,'w',1)]:
            with self.assertRaises(PermissionError):audit('open',args)
        for event in ('os.remove','os.rename','resource.setrlimit','ctypes.dlopen','subprocess.Popen','socket.connect'):
            with self.assertRaises(PermissionError):audit(event,())
        self.assertLess(boot.index('resource.setrlimit(resource.RLIMIT_AS'),boot.index('sys.addaudithook'))
        self.assertLess(boot.index('sys.addaudithook'),boot.index('import hashlib'))
        self.assertIn('resource.RLIMIT_CPU,(950,950)',boot)
        self.assertIn(str(len(SOURCE)+1),boot);self.assertIn(hashlib.sha256(SOURCE).hexdigest(),boot)
    def test_no_existing_root_failure_write_and_no_main_or_children(self):
        text=SOURCE.decode();self.assertIn('if OWNED_OUTPUT_ROOT and OUT.is_dir()',text)
        self.assertLess(text.index('need(not os.path.lexists(OUT)'),text.index('OWNED_OUTPUT_ROOT=True'))
        self.assertNotIn('subprocess.run(',text);self.assertEqual(EVENTS,[])
    def test_delayed_final_close_and_pin_refuse_settled_success(self):
        for delayed in ('close','pin','extent'):
            clock={'now':899.9};expected={'bytes':10,'sha256':'a'*64}
            class FakeSink:
                def __init__(self,*args):pass
                def write(self,value):return len(value)
                def close(self):
                    if delayed=='close':clock['now']=901
            def final_pin(path):
                if delayed=='pin':clock['now']=901
                return expected
            def final_extent():
                if delayed=='extent':clock['now']=901
            ns={'Sink':FakeSink,'canonical':lambda value:b'{}','RESERVE':1048576,'OUT':Path('/inert'),
                'START':0,'time':SimpleNamespace(monotonic=lambda:clock['now']),'pin':final_pin,'extent':final_extent}
            extract({'Refused','need','save','settled_success'},ns)
            ns['save']('result.json',{},True)
            with self.assertRaises(ns['Refused']):ns['settled_success'](expected)
    def test_settled_publication_has_checks_before_and_after_flush(self):
        main=next(n for n in TREE.body if getattr(n,'name',None)=='main')
        calls=[n for n in main.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)]
        names=[n.value.func.id if isinstance(n.value.func,ast.Name) else None for n in calls]
        self.assertEqual(names[-4:],['save','settled_success','print','settled_success'])
        printing=calls[-2].value;self.assertTrue(any(k.arg=='flush' and isinstance(k.value,ast.Constant) and k.value.value is True for k in printing.keywords))
        self.assertIn('completion_requires_controller_zero_exit_and_settled_publication',SOURCE.decode())
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,
        'entry_sha256':hashlib.sha256(SOURCE).hexdigest(),'actual_controller_bootstrap_or_resource_limits_executed':False}))
    raise SystemExit(not result.wasSuccessful())

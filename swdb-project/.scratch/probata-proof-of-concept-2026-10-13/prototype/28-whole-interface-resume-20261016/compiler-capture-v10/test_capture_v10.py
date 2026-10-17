"""Narrow V9 write-bound repair plus inherited strict stream controls, inert."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('no-child v10 controls '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;INGRESS=WHOLE/'streaming-minify-v1';OLD=WHOLE/'compiler-capture-v9'
def load(path):
    ns={'__name__':'inert_v10_controls','__file__':str(path)};exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns
V9=load(OLD/'test_capture_v9.py');STREAM=V9['STREAM'];NEW=load(INGRESS/'strict_minify_v2.py');OLD_M=STREAM['M'];STREAM['M']=NEW
D=json.loads((HERE/'compiler-capture-v10-inverse.json').read_bytes());P=json.loads((HERE/'linux_compiler_capture_policy_v10.json').read_bytes());C=json.loads((HERE/'linux_compiler_capture_command_v10.json').read_bytes())
class Controls(unittest.TestCase):
    def test_exact_entry_inverse_and_all_function_ASTs(self):
        text=(HERE/'linux_compiler_capture_v10.py').read_text();old=Path(D['predecessor']['path']).read_text()
        for edit in reversed(D['entry_edits']):self.assertEqual(text.count(edit['new']),1);text=text.replace(edit['new'],edit['old'],1)
        self.assertEqual(text,old)
        before=V9['functions'](old);after=V9['functions']((HERE/'linux_compiler_capture_v10.py').read_bytes())
        for name in before:
            if name!='main':self.assertEqual(before[name],after[name])
    def test_minifier_emit_only_inverse(self):
        text=(INGRESS/'strict_minify_v2.py').read_text();old=Path(D['minifier_predecessor']['path']).read_text()
        for edit in reversed(D['minifier_edits']):self.assertEqual(text.count(edit['new']),1);text=text.replace(edit['new'],edit['old'],1)
        self.assertEqual(text,old)
        before=ast.parse(old);after=ast.parse((INGRESS/'strict_minify_v2.py').read_bytes())
        for a,b in zip(before.body,after.body):
            if isinstance(a,ast.ClassDef) and a.name=='Minifier':
                for x,y in zip(a.body,b.body):
                    if isinstance(x,ast.FunctionDef) and x.name=='emit':continue
                    self.assertEqual(ast.dump(x),ast.dump(y))
            else:self.assertEqual(ast.dump(a),ast.dump(b))
    def test_maximum_string_flush_never_exceeds64KiB(self):
        class Sink(io.BytesIO):
            def write(self,value):self_outer.assertLessEqual(len(value),65536);return super().write(value)
        self_outer=self;raw=b'{"prefix":0,"x":"'+b'a'*1048574+b'"}'
        out=Sink();r=NEW['minify'](io.BytesIO(raw),out,raw_limit=2147483648,retained_limit=134217728,check=lambda:None)
        self.assertEqual(out.getvalue(),raw);self.assertEqual(r['minified_bytes'],len(raw));self.assertEqual(json.loads(out.getvalue()),json.loads(raw))
    def test_near_total_limit_refuses_without_hard_cap_or_reserve_overshoot(self):
        total=268435456;reserve=1048576;used=total-reserve;writes=[]
        class Stop(ValueError):pass
        def check():
            if used>total-reserve:raise Stop('prospective aggregate limit')
        class Sink:
            def write(self,value):
                nonlocal used
                writes.append(len(value));used+=len(value);self_outer.assertLessEqual(used,total);return len(value)
        self_outer=self;raw=b'{"prefix":0,"x":"'+b'a'*1048574+b'"}'
        with self.assertRaises(Stop):NEW['minify'](io.BytesIO(raw),Sink(),raw_limit=2147483648,retained_limit=134217728,check=check)
        self.assertTrue(writes);self.assertLessEqual(max(writes),65536);self.assertLessEqual(used,total-reserve+65536)
    def test_policy_command_inverses_and_physical_pins(self):
        self.assertEqual(V9['inverse'](copy.deepcopy(P),D['policy_edits']),json.loads(Path(D['old_policy']['path']).read_bytes()))
        self.assertEqual(V9['inverse'](copy.deepcopy(C),D['command_edits']),json.loads(Path(D['old_command']['path']).read_bytes()))
        for row in C['controller_inputs']:
            data=Path(row['path']).read_bytes();self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),(row['bytes'],row['sha256']))
        self.assertEqual(C['argv'][-1],hashlib.sha256((HERE/'linux_compiler_capture_policy_v10.json').read_bytes()).hexdigest())
        self.assertEqual(C['root_guard'],V9['COMMAND']['root_guard']);self.assertEqual(C['node'],V9['COMMAND']['node'])
        for key in ('budgets','native_runtime','startup_roles','zlib_binding','source_inputs','guard_files'):self.assertEqual(P[key],V9['POLICY'][key])
        self.assertEqual(C['expanded_caller_stream_limit_bytes'],2147483648);self.assertEqual(C['caller_ast_phase_seconds'],120)
    def test_no_child(self):self.assertEqual(EVENTS,[]);self.assertEqual(V9['EVENTS'],[]);self.assertEqual(STREAM['EVENTS'],[])
if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Controls),unittest.defaultTestLoader.loadTestsFromTestCase(V9['Controls']),unittest.defaultTestLoader.loadTestsFromTestCase(STREAM['Controls'])]);result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS+V9['EVENTS']+STREAM['EVENTS'],
        'entry_sha256':hashlib.sha256((HERE/'linux_compiler_capture_v10.py').read_bytes()).hexdigest(),'minifier_sha256':hashlib.sha256((INGRESS/'strict_minify_v2.py').read_bytes()).hexdigest(),'controls_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'synthetic no-child bounded-write/inverse controls; no actual compiler/controller/native'}))
    sys.exit(not result.wasSuccessful())

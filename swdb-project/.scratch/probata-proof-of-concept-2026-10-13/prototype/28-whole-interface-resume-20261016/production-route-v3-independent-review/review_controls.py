"""Independent stdlib-only AST/physical-pin controls; no project import/main."""
import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent;ROUTE=HERE.parent/'production-route-v3'
EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise AssertionError('no child/network/native '+event)
sys.addaudithook(audit)
def selected(path,names,ns):
    tree=ast.parse(path.read_bytes());nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns);return ns
def literal(path,name):
    for n in ast.parse(path.read_bytes()).body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return ast.literal_eval(n.value)
    raise AssertionError(name)
SOURCE=ROUTE/'proposed/swdb/dx100_checked_source.py'
class Unit:pass
class Controls(unittest.TestCase):
    def test_legacy_prelude_bytes_remain_equal_and_default_does_not_import(self):
        base=ROUTE/'base-source/cbmc_translator.py';new=ROUTE/'proposed/swdb/cbmc_translator.py'
        self.assertEqual(literal(base,'PRELUDE'),literal(new,'PRELUDE'))
        oldns={'PRELUDE':literal(base,'PRELUDE'),'TOOL_ID':'closed','TOOL_VERSION':'1','ORACLE_CAPACITY':'capacity'}
        newns=dict(oldns)
        selected(base,{'prelude'},oldns);selected(new,{'prelude'},newns)
        self.assertEqual(oldns['prelude'](),newns['prelude']())
    def test_checked_native_failure_override_is_fatal_and_precedes_oracle(self):
        ns={'SourceUnit':Unit,'WHOLE_NATIVE_FAILURE':literal(SOURCE,'WHOLE_NATIVE_FAILURE')}
        selected(SOURCE,{'Refused','need','native_prelude'},ns)
        raw=literal(ROUTE/'proposed/swdb/cbmc_translator.py','PRELUDE');result=ns['native_prelude'](Unit(),raw)
        failure=ns['WHOLE_NATIVE_FAILURE']
        self.assertIn('#if defined(SWDB_NATIVE)',failure);self.assertIn('_Exit(0)',failure)
        self.assertIn('printf(" end=%s\\n",end); fflush(stdout);',failure)
        self.assertNotIn('longjmp',failure);self.assertNotIn('dws_local_leave',failure)
        self.assertLess(result.index('static void swdb_whole_native_stop'),result.index('static long long swdb_next(void)'))
        self.assertLess(result.index('#undef SWDB_CHECK'),result.index('static long long swdb_next(void)'))
        with self.assertRaises(ns['Refused']):ns['native_prelude'](object(),raw)
    def test_typed_malformed_unit_fallback_precedes_policy_work(self):
        ns={'FUNCTION':'whole_interface_source_fixture'}
        selected(SOURCE,{'checked_unit_format'},ns)
        for proof_unit in ('truthy',['function'],7,True,None):
            self.assertIsNone(ns['checked_unit_format'](None,'id',{'proof_unit':proof_unit}))
    def test_real_receiver_pin_gate_refuses_cross_role_alias_and_changed_bytes(self):
        receiver={'dataclass':dataclass,'Path':Path,'stat':stat,'hashlib':hashlib,'re':re}
        selected(ROUTE/'proposed/swdb/_dx100_whole/receiver_state_draws_v2.py',
            {'Refused','need','digest','Pin','stable_metadata','check_file'},receiver)
        ns={'source':SimpleNamespace(need=receiver['need'],receiver=SimpleNamespace(**receiver)),'Path':Path,'hashlib':hashlib}
        selected(ROUTE/'proposed/swdb/dx100_checked_adapter.py',{'check_role_inputs'},ns)
        expected={'c':'C-body','cxx':'original-C++-body'}
        with tempfile.TemporaryDirectory(dir=HERE,prefix='independent-role-') as temp:
            c=Path(temp).resolve()/'job.c';cxx=c.with_name('view.cc');c.write_text(expected['c']);cxx.write_text(expected['cxx'])
            ns['check_role_inputs'](expected,[('c',c),('cxx',cxx)])
            for inputs in ([('c',cxx)],[('cxx',c)],[('invalid',c)]):
                with self.assertRaises(receiver['Refused']):ns['check_role_inputs'](expected,inputs)
            alias=c.with_name('alias.c');alias.symlink_to(c)
            with self.assertRaises(receiver['Refused']):ns['check_role_inputs'](expected,[('c',alias)])
            c.write_text('changed')
            with self.assertRaises(receiver['Refused']):ns['check_role_inputs'](expected,[('c',c)])
    def test_fresh_process_branch_retains_one_line_exit_and_fixed_draw_lvalues(self):
        harness=ast.get_source_segment((ROUTE/'proposed/swdb/cbmc_translator.py').read_text(),
            next(n for n in ast.parse((ROUTE/'proposed/swdb/cbmc_translator.py').read_bytes()).body if getattr(n,'name',None)=='harness'))
        self.assertIn('if (fgets(swdb_line, sizeof swdb_line, stdin)) return 3;',harness)
        self.assertTrue(any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='draw'
            and isinstance(n.slice,ast.Constant) and n.slice.value=='c_lvalue' for n in ast.walk(ast.parse(harness))))
        self.assertIn('setup already drew each slot exactly once',harness)
        profile=ast.get_source_segment(SOURCE.read_text(),next(n for n in ast.parse(SOURCE.read_bytes()).body if getattr(n,'name',None)=='harness_profile'))
        self.assertIn('dws_prepare_receiver_v1();',profile);self.assertIn('dws_choice_table[',profile)
    def test_no_child(self):self.assertEqual(EVENTS,[])
if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'child_events':EVENTS,
        'scope':'AST-projected primitives and local synthetic bytes only; no compiler/native/actual/source-route main'}))
    raise SystemExit(not r.wasSuccessful())

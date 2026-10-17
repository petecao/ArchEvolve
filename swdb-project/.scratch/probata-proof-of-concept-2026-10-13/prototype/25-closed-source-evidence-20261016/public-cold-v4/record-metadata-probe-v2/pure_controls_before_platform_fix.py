"""2026-10-16 ET. Root/record diagnostic controls, no main/remote/project imports."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        EVENTS.append(event);raise RuntimeError('pure record probe forbids '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
RAW=(HERE/'record-probe-v2.py').read_bytes();N={'__name__':'inert_record_diagnostic'};exec(compile(RAW,'inert_record_diagnostic','exec'),N);exec(compile(N['FUNCTION_BYTES'],'inert_extracted_functions','exec'),N)
EXPECTED=json.loads(N['EXPECTED_BYTES'])
class Controls(unittest.TestCase):
    def test_root_junit_complete_cheap_path_uses_all_five_real_names(self):
        class Fake:
            def json(self,path):return {'runtime':{'compiler':'pinned'}}
            def read(self,path):
                names=''.join('<testcase classname="tests.test_vector_reallocation_closed_public_workflow" name="test_public_closed_source_proof_and_exact_opt_in_controls['+case+']" />' for case in N['CASES'])
                return ('<testsuites><testsuite tests="5" errors="0" failures="0" skipped="0">'+names+'</testsuite></testsuites>').encode()
        old=N.get('P');N['P']=Fake()
        try:self.assertEqual(N['root_junit']({'linux_clang_components':{'compiler':'pinned'}}),{'runtime':{'compiler':'pinned'}})
        finally:N['P']=old
    def test_original_int_plan_and_exact_float_plan_are_distinct_without_coercion(self):
        base={'bounds':None,'budget_seconds':300,'defines':[],'function':'vector_realloc_v3_no_growth','contract':N['CONTRACT'],'contract_sha256':'a'*64}
        float_plan=dict(base,budget_seconds=300.0)
        self.assertEqual(base,float_plan);self.assertNotEqual(N['digest'](base),N['digest'](float_plan));self.assertIs(type(base['budget_seconds']),int);self.assertIs(type(float_plan['budget_seconds']),float)
    def test_type_audit_preserves_python_result_but_catches_nested_bool_int_and_float(self):
        before=N['TYPE_CONFUSION_COUNT']
        for left,right in ((True,1),(300,300.0),({'threads':True},{'threads':1})):
            self.assertTrue(N['compare_trace']([lambda:left,lambda:right],['Eq'],'pure',1))
        self.assertEqual(N['TYPE_CONFUSION_COUNT']-before,3)
        self.assertTrue(N['compare_trace']([lambda:300.0,lambda:300.0],['Eq'],'pure',2))
        self.assertEqual(N['TYPE_CONFUSION_COUNT']-before,3)
    def test_equality_chain_evaluates_once_and_preserves_short_circuit(self):
        calls=[]
        def value(mark,result):calls.append(mark);return result
        self.assertTrue(N['compare_trace']([lambda:value('a',1),lambda:value('b',1),lambda:value('c',1)],['Eq','Eq'],'pure',3));self.assertEqual(calls,['a','b','c'])
        calls.clear();self.assertFalse(N['compare_trace']([lambda:value('a',1),lambda:value('b',2),lambda:value('c',2)],['Eq','Eq'],'pure',4));self.assertEqual(calls,['a','b'])
    def test_semantic_failures_are_collected_and_physical_failure_stays_hard(self):
        before=N['PREDICATE_COUNT'];N['observe'](False,'first','pure',5);N['observe'](True,'second','pure',6);self.assertEqual(N['PREDICATE_COUNT']-before,2)
        with self.assertRaises(ValueError):N['need'](False,'physical pin mismatch')
    def test_readers_and_expected_context_are_frozen(self):
        for name in ('FUNCTION_BYTES','EXPECTED_BYTES','YAML_BYTES'):self.assertEqual(hashlib.sha256(N[name]).hexdigest(),N[name+'_SHA'])
        self.assertEqual(hashlib.sha256(N['YAML_BYTES']).hexdigest(),'d06565898c7350e3df500c51c8f84b936174574b09b9d5e30601f27b36367938');self.assertEqual(len(N['RECORD_PINS']),5);self.assertEqual(len(EXPECTED['catalog_documents']),91)
    def test_original_record_integer_plan_is_preserved_in_extracted_body(self):
        tree=ast.parse(N['FUNCTION_BYTES']);record=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='record_check');plan=next(n.value for n in record.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='plan' for t in n.targets))
        budget=next(v for k,v in zip(plan.keys,plan.values) if isinstance(k,ast.Constant) and k.value=='budget_seconds');self.assertIs(type(budget.value),int);self.assertEqual(budget.value,300)
    def test_audit_forbids_writes_children_network_caps_and_project_imports(self):
        for event,args in [('open',('/x','w',1)),('open',('/x',None,64)),('subprocess.Popen',()),('socket.connect',()),('resource.setrlimit',()),('import',('swdb',)),('import',('yaml',))]:
            with self.subTest(event=event),self.assertRaises((RuntimeError,ValueError)):N['audit'](event,args)
    def test_complete_publication_budget_sample_under_four_MiB(self):
        pin={'path':'/'+('p'*1023),'bytes':134217728,'sha256':'f'*64,'stable':[9223372036854775807]*9}
        group={'case':'default_method','function':'source_result_check','line':9999,'reason':'r'*160,'passed':999999,'failed':0}
        payload={'physical_inputs':[pin]*1024,'predicate_groups':[group]*512,'failure_samples':[dict(group,passed=False)]*64,'type_conflation_samples':[{'left_sha256':'a'*64,'right_sha256':'b'*64,'left_type':'float','right_type':'int','line':9999}]*16}
        self.assertLess(len(json.dumps(payload,sort_keys=True,separators=(',',':')).encode())+1,4194304)
    def test_no_main_or_children(self):self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'skips':len(result.skipped),'child_events':EVENTS,'probe_main_or_remote_or_project_execution':False,'source_sha256':hashlib.sha256(RAW).hexdigest()}));sys.exit(not result.wasSuccessful())

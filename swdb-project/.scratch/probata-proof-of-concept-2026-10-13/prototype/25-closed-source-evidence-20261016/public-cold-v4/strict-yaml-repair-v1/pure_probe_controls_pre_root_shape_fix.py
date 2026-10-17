"""2026-10-16 ET. Complete semantic comparison controls; no probe main/remote read."""
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
        EVENTS.append(event);raise RuntimeError('pure probe control forbids '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
RAW=(HERE/'semantic-probe-v1.py').read_bytes();NS={'__name__':'pure_probe_controls'};exec(compile(RAW,'inert-semantic-probe','exec'),NS)
EXPECTED=json.loads((HERE/'probe-expected.json').read_bytes());Y={'__name__':'pure_reader'};exec(compile(NS['READER_BYTES'],'inert-reader','exec'),Y)
RUNTIME={'lowering_identity':{'c_lowering':{'id':'test-current-lowering','sha256':'7'*64}}}
class Controls(unittest.TestCase):
    def test_exact_embedded_reader_expected_and_root_record_pins(self):
        self.assertEqual(NS['READER_BYTES'],(HERE/'record_yaml_subset_v3.py').read_bytes());self.assertEqual(NS['EXPECTED_BYTES'],(HERE/'probe-expected.json').read_bytes())
        self.assertEqual(hashlib.sha256(NS['READER_BYTES']).hexdigest(),NS['READER_SHA']);self.assertEqual(hashlib.sha256(NS['EXPECTED_BYTES']).hexdigest(),NS['EXPECTED_SHA']);self.assertEqual(len(EXPECTED['record_json_pins']),5)
    def test_all_five_full_expected_methods_contracts_and_proofs_compare(self):
        outcomes=[]
        for case in NS['CASES']:
            method=NS['expected_method'](EXPECTED,case,RUNTIME)
            proof={'id':'proof.synthetic.'+case,'case':case,'method':method,'contract':EXPECTED['contracts'][case],'goals':[{'status':'valid' if case=='safe' else 'not_proven'}],'flags':[True,False,None,1,1.5]}
            for value in (method,EXPECTED['contracts'][case],proof):
                result,actual=NS['compare'](json.dumps(value).encode(),value,Y);self.assertTrue(result['parsed']);self.assertTrue(result['complete_semantic_equality']);self.assertEqual(actual,value);outcomes.append(result)
        self.assertEqual(len(outcomes),15)
    def test_method_modes_and_immutable_template_are_exact(self):
        before=copy.deepcopy(EXPECTED);safe=NS['expected_method'](EXPECTED,'safe',RUNTIME);stale=NS['expected_method'](EXPECTED,'stale_method',RUNTIME);default=NS['expected_method'](EXPECTED,'default_method',RUNTIME)
        self.assertEqual(len(safe['lineup']),9);self.assertEqual(len(safe['c_lowering']['translators']),5);self.assertEqual(safe['c_lowering']['translators'][0],RUNTIME['lowering_identity']['c_lowering'])
        self.assertEqual(stale['c_lowering']['translators'][:-1],safe['c_lowering']['translators'][:-1]);self.assertEqual(stale['c_lowering']['translators'][-1]['sha256'],'0'*64);self.assertEqual(default['c_lowering']['translators'],safe['c_lowering']['translators'][:1]);self.assertEqual(default['id'],'method.wp-vector-closed-default-v1');self.assertEqual(EXPECTED,before)
    def test_whole_object_changes_and_bool_integer_types_do_not_compare_equal(self):
        target=NS['expected_method'](EXPECTED,'safe',RUNTIME);changed=copy.deepcopy(target);changed['models']['std_pair']['sha256']='0'*64
        result,_=NS['compare'](json.dumps(changed).encode(),target,Y);self.assertTrue(result['parsed']);self.assertFalse(result['complete_semantic_equality'])
        for actual,wanted in ((True,1),(1,True),({'missing':None},{})):
            result,_=NS['compare'](json.dumps(actual).encode(),wanted,Y);self.assertFalse(result['complete_semantic_equality'])
    def test_unknown_yaml_syntax_refuses_without_content(self):
        for value in (b'a: &PRIVATE_MARKER value\n',b'a: !!python/object:PRIVATE_MARKER {}\n',b'a: 1\na: 2\n'):
            result,actual=NS['compare'](value,{},Y);self.assertFalse(result['parsed']);self.assertFalse(result['complete_semantic_equality']);self.assertIsNone(actual);self.assertNotIn('PRIVATE_MARKER',json.dumps(result))
    def test_root_json_duplicate_and_nonfinite_refuse(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.assertRaises(ValueError):NS['strict_json'](raw)
    def test_inherited_nofollow_read_audit_and_stable_ast_exact(self):
        old=ast.parse((HERE.parent/'yaml-diagnostic-v3/diagnostic-v3.py').read_bytes());new=ast.parse(RAW)
        def funcs(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        a,b=funcs(old),funcs(new)
        for name in ('need','stable','read','audit'):self.assertEqual(a[name],b[name])
    def test_complete15_output_with_all21_pins_stays_below_cap(self):
        actual=json.loads((HERE.parents[3]/'evidence/t25-public-v4-yaml-diagnostic-actual-v3-20261016.json').read_bytes());rows=[]
        for row in actual['rows']:
            rows.append({'case':row['case'],'phase':row['phase'],'input':row['input'],'comparison':{'parsed':True,'complete_semantic_equality':True,'actual_semantic_sha256':'f'*64,'expected_semantic_sha256':'f'*64,'counts':dict.fromkeys(('objects','arrays','strings','integers','reals','booleans','nulls'),8388608),'retained_record_content_pin_equal':True}})
        extra={'relative':'closed-project-runtime.json','bytes':8388608,'sha256':'f'*64,'stable':[9223372036854775807]*9}
        payload={'rows':rows,'root_runtime_input':extra,'record_json_inputs':[dict(extra,relative=r['path']) for r in EXPECTED['record_json_pins']],'all15_complete_semantic_equal':True,'all21_input_content_and_nine_stat_rechecks_equal':True,'inputs':21,'yaml_files':15}
        self.assertLess(len(json.dumps(payload,sort_keys=True).encode()),24576)
    def test_no_children_or_probe_main(self):self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,'probe_main_or_remote_execution':False,'complete_synthetic_comparison_rows':15,'probe_sha256':hashlib.sha256(RAW).hexdigest()}));sys.exit(not result.wasSuccessful())

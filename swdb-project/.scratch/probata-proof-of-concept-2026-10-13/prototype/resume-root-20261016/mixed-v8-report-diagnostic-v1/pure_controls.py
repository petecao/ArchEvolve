"""2026-10-16 ET. No-child all-context and output-redaction controls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ATTEMPTS=[]


def block(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.') or event in {'os.system','os.exec','os.fork','os.posix_spawn','ctypes.dlopen'}:
        ATTEMPTS.append(event);raise RuntimeError('no child/native/network in diagnostic controls')


sys.addaudithook(block)
N={'__name__':'_pure'}
exec(compile((HERE/'diagnostic.py').read_text(),str(HERE/'diagnostic.py'),'exec'),N)
N['need']=lambda value,label:None if value else (_ for _ in ()).throw(ValueError(label))
N['digest']=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
N['pin']=lambda path:{'bytes':0,'sha256':'h'}
N['CONTEXT']={'raw_regular_pins':{}}


def reports(directory,*,mismatch=False,wrong=False):
    goal={'goal':'native1','property':'p1','function':'f','line':1,'smoke':False,'passed':True}
    native=[goal];standard=copy.deepcopy(native)
    if mismatch:standard[0]['goal']='different-standard-id'
    props=[{'property':'p1','id':'opaque1','variant':'IPLemma','dependencies':[],
            'description':'DO_NOT_EXPORT_FORMULA','call_context':'DO_NOT_EXPORT_CONTEXT'}]
    documents={'wp-inventory.json':{'complete':True,'version':'1','goals':native,'properties':props,'property_closure':{}},
               'wp-goals.json':standard}
    record={'id':'record','subject':{'id':'c_model.fixture','kind':'c_model'},'pins':{},'goals':copy.deepcopy(native)}
    data={'wp-properties.csv':b'Kind\tFunction\tProperty\tDescription\tStatus\nlemma\tf\tp1\tDO_NOT_EXPORT_CSV\tValid\n',
          'frama-c.log':b'EXPORT GOAL native1\n(* use int.Int *)\n'}
    N['read']=lambda path:copy.deepcopy(documents[Path(path).name])
    N['read_bytes']=lambda path:data[Path(path).name]
    return documents,record


def cbmc_reports(directory,wrong=False):
    record={'id':'record','subject':{'kind':'library_summary','id':'contract.fixture_pair_pointer_wrong_identity' if wrong else 'contract.fixture_pair_pointer_values'},
            'goals':[{'goal':'native-reach','property':'swdb_reach.end','status':'failure'},
                     {'goal':'native-post','property':'contract.fixture_pair_pointer_wrong_identity#post.ensures1' if wrong else 'post.safe','status':'failure' if wrong else 'success'}],
            'settings':{'agreement':{'verdict':'agree','runs':49,'sampled':False,'c_output_sha256':'h','cxx_output_sha256':'h'},
                        'forms':{'cxx':'refuted (counterexample replayed)' if wrong else 'proven'}},
            'counterexample':{'replay':{'replayed':wrong,'secret_trace':'DO_NOT_EXPORT_TRACE'}}}
    document=[{'result':[{'property':'native-reach','status':'FAILURE','description':'reach'},
                         {'property':'native-post','status':'FAILURE' if wrong else 'SUCCESS','description':'post'}]}]
    N['read']=lambda path:copy.deepcopy(document)
    return document,record


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HERE);self.directory=Path(self.temp.name)
        for name in ('wp_input.c','replay_cxx.cc'):(self.directory/name).write_text('')

    def tearDown(self):self.temp.cleanup()

    def test_WP_identity_failure_does_not_hide_remaining_predicates(self):
        _,record=reports(self.directory,mismatch=True)
        result=N['wp_diagnostic'](self.directory,record)
        checks={r['predicate']:r for r in result['predicates']}
        self.assertFalse(checks['complete native/standard WP goal identity']['value'])
        self.assertTrue(checks['retained full WP query input']['value'])
        self.assertEqual(result['native_only_goal_ids'],['native1'])
        self.assertEqual(result['standard_only_goal_ids'],['different-standard-id'])
        self.assertIn('CSV',result)

    def test_all_six_contexts_return_independent_matrices(self):
        outputs=[]
        for index in range(6):
            _,record=reports(self.directory,mismatch=index%2==0);record['id']='record'+str(index)
            outputs.append(N['wp_diagnostic'](self.directory,record))
        self.assertEqual(len(outputs),6)
        self.assertTrue(all(len(o['predicates'])==7 for o in outputs))

    def test_owner_field_difference_is_separate_from_goal_identity(self):
        docs,record=reports(self.directory);docs['wp-goals.json'][0]['passed']=False
        result=N['wp_diagnostic'](self.directory,record);checks={r['predicate']:r['value'] for r in result['predicates']}
        self.assertTrue(checks['complete native/standard WP goal identity'])
        self.assertFalse(checks['native/standard property owner'])
        self.assertEqual(result['shared_owner_field_differences'],[{'goal':'native1','fields':['passed']}])

    def test_duplicate_human_property_labels_are_reported(self):
        docs,record=reports(self.directory);docs['wp-inventory.json']['properties'].append({**docs['wp-inventory.json']['properties'][0],'id':'opaque2'})
        result=N['wp_diagnostic'](self.directory,record)
        self.assertEqual(result['duplicate_property_labels'],['p1'])
        self.assertIn('CSV',result)

    def test_raw_description_callcontext_and_CSV_text_are_hashed(self):
        _,record=reports(self.directory);result=N['wp_diagnostic'](self.directory,record)
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(result))
        self.assertEqual(result['CSV']['headers'],['Kind','Function','Property','Description','Status'])

    def test_CBMC_safe_all_remaining_predicates(self):
        _,record=cbmc_reports(self.directory);result=N['cbmc_diagnostic'](self.directory,record)
        self.assertTrue(all(row['value'] is True for row in result['predicates']))

    def test_CBMC_wrong_checks_replay_without_exporting_trace(self):
        _,record=cbmc_reports(self.directory,wrong=True);result=N['cbmc_diagnostic'](self.directory,record)
        self.assertTrue(all(row['value'] is True for row in result['predicates']))
        self.assertNotIn('DO_NOT_EXPORT_TRACE',json.dumps(result))
        self.assertTrue(result['replay_metadata']['replayed'])

    def test_CBMC_multiple_failures_do_not_stop_matrix(self):
        _,record=cbmc_reports(self.directory,wrong=True);record['goals'][0]['status']='unknown'
        record['settings']['agreement']['runs']=48;record['settings']['forms']['cxx']='wrong'
        result=N['cbmc_diagnostic'](self.directory,record);checks={r['predicate']:r['value'] for r in result['predicates']}
        self.assertFalse(checks['actual CBMC status/record agreement'])
        self.assertFalse(checks['exact bounded49 independent C/C++ draws'])
        self.assertFalse(checks['original C++ counterexample replay artifact'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print('child_native_network_attempts='+repr(ATTEMPTS))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)

"""2026-10-16 ET. Strict emitter-form controls; no project/remote/tool execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        EVENTS.append(event);raise RuntimeError('strict reader control forbids '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
NAME=sys.argv[1] if len(sys.argv)==2 else 'record_yaml_subset_v3.py'
RAW=(HERE/NAME).read_bytes();Y={'__name__':'pure_reader'};exec(compile(RAW,'inert-strict-reader','exec'),Y)
class Controls(unittest.TestCase):
    def test_plain_sha_beginning_binary_prefix_is_text(self):
        value='0b'+'a'*62
        self.assertEqual(Y['loads'](('sha256: '+value+'\n').encode()),{'sha256':value})
    def test_explicit_long_scalar_keys_match_complete_nested_json(self):
        key='/data/source/'+('a'*150)+'/file.c';quoted='q'*128
        raw=('hashes:\n    ? '+key+'\n    : 0badbeef\n    ? '+json.dumps(quoted)+'\n    : [true, null, 1]\nnext: done\n').encode()
        self.assertEqual(Y['loads'](raw),{'hashes':{key:'0badbeef',quoted:[True,None,1]},'next':'done'})
    def test_actual_implicit_numbers_and_unsupported_syntax_still_refuse(self):
        for value in ('0b101','0xFF','0123','0o777','1_000','+12','yes','.NaN','@x','`x','&anchor value','*anchor','!!python/object:thing {}'):
            with self.subTest(value=value),self.assertRaises(ValueError):Y['loads'](('value: '+value+'\n').encode())
    def test_explicit_short_collection_missing_value_and_duplicate_keys_refuse(self):
        key='x'*128
        cases=['? short\n: value\n','? [a, b]\n: value\n','? '+key+'\n  : wrong-indent\n','? '+key+'\nwrong: value\n','? '+key+'\n: first\n? '+key+'\n: second\n',key+': first\n? '+key+'\n: second\n']
        for raw in cases:
            with self.subTest(raw_shape=len(raw)),self.assertRaises((ValueError,TypeError,IndexError)):Y['loads'](raw.encode())
    def test_ten_retained_real_fixture_records_still_parse(self):
        poc=HERE.parents[3];prep=json.loads((poc/'evidence/t25-explicit-method-selection-repair-preparation-v2-20261016.json').read_bytes())
        self.assertEqual(len(prep['retained_record_observations']),10)
        for row in prep['retained_record_observations']:
            raw=Path(row['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256']);record=Y['loads'](raw)
            self.assertEqual(record['pins']['method_version'],row['method']);self.assertEqual(record['subject'],row['subject']);self.assertEqual(record['verdict'],row['verdict'])
    def test_no_children_or_reader_main(self):self.assertEqual(EVENTS,[])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,'reader':NAME,'reader_sha256':hashlib.sha256(RAW).hexdigest(),'remote_or_project_or_compiler_execution':False}));sys.exit(not result.wasSuccessful())

"""Pure source/AST/JSON budget inverse controls; no runtime bootstrap."""
import ast
import hashlib
import json
from pathlib import Path
import shlex
import unittest
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'compiler-duplicate-census-v2'
class Controls(unittest.TestCase):
    def test_whole_source_exact_text_and_AST_inverse(self):
        new=(HERE/'complete_duplicate_census_v3.py').read_text();old=(OLD/'complete_duplicate_census_v2.py').read_text()
        marker="time.monotonic()-started<600,'bounded metadata diagnostic deadline exceeded'"
        self.assertEqual(new.count(marker),1);self.assertEqual(new.replace(marker,marker.replace('<600,','<90,'),1),old)
        tree=ast.parse(new);target=next(n for n in tree.body if getattr(n,'name',None)=='inspect')
        count=0
        for n in ast.walk(target):
            if isinstance(n,ast.Constant) and type(n.value) is int and n.value==600:n.value=90;count+=1
        self.assertEqual(count,1);self.assertEqual(ast.dump(tree,include_attributes=False),ast.dump(ast.parse(old),include_attributes=False))
    def test_bootstrap_exact_inverse_and_caps(self):
        inverse=json.loads((HERE/'budget-v3-exact-inverse.json').read_bytes());new=(HERE/'readonly_bootstrap_v4.py').read_text();old=(OLD/'readonly_bootstrap_v3.py').read_text()
        for row in reversed(inverse['bootstrap_edits']):self.assertEqual(new.count(row['after']),1);new=new.replace(row['after'],row['before'],1)
        self.assertEqual(new,old)
        tree=ast.parse((HERE/'readonly_bootstrap_v4.py').read_bytes());calls=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='setrlimit']
        self.assertEqual([(n.value.args[0].attr,ast.literal_eval(n.value.args[1])) for n in calls],[('RLIMIT_AS',(536870912,536870912)),('RLIMIT_CPU',(650,650))])
    def test_command_envelope_inverse_and_caps(self):
        new=json.loads((HERE/'complete-census-command-v3.json').read_bytes());old=json.loads((OLD/'complete-census-command-v2.json').read_bytes())
        changed={'CPU_seconds','internal_wall_seconds','outer_timeout_seconds','local_transport_timeout_seconds','bootstrap','stdin','python_argv','remote_argv','remote_shell_command','predecessor_command','scope'}
        self.assertEqual({k:v for k,v in new.items() if k not in changed},{k:v for k,v in old.items() if k not in changed})
        self.assertEqual([new[k] for k in ('CPU_seconds','internal_wall_seconds','outer_timeout_seconds','local_transport_timeout_seconds')],[650,600,660,700])
        self.assertEqual(new['remote_argv'],shlex.split(new['remote_shell_command']))
        expected=list(old['remote_argv']);expected[3]='660s';expected[expected.index(old['python_argv'][4])]=new['python_argv'][4]
        self.assertEqual(new['remote_argv'],expected)
        payload=(HERE/'complete_duplicate_census_v3.py').read_bytes();self.assertEqual(new['stdin']['sha256'],hashlib.sha256(payload).hexdigest())
        self.assertEqual(new['stdin']['bytes'],len(payload));self.assertEqual(new['address_space_bytes'],536870912);self.assertEqual(new['stdout_bytes'],32768)
    def test_all_previous_pure_controls_green_without_actual_main(self):
        for name,tests in [('pure-census-controls.log',15),('pure-bootstrap-controls.log',4)]:
            row=json.loads((HERE/name).read_text().splitlines()[-1]);self.assertEqual(row['tests'],tests)
            self.assertEqual((row['errors'],row['failures'],row['skips']),(0,0,0))
        self.assertFalse(json.loads((HERE/'pure-bootstrap-controls.log').read_text().splitlines()[-1])['bootstrap_executed'])
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'actual_reader_or_bootstrap_executed':False}))
    raise SystemExit(not result.wasSuccessful())

"""Pure AST/byte controls; never run shell, launcher, child or compiler."""
import ast,hashlib,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
V9=WHOLE.parent/'resume-root-20261016/launch_reviewed_main_v9.py'
V11=HERE/'launch_observer_loader_v11.py'
ROOT=WHOLE/'normalized-unit-envelope-v2-actual'
def audit(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('source controls forbid child/native/network')
sys.addaudithook(audit)
def selection_assert(path):
 return next(node for node in ast.parse(path.read_bytes()).body if isinstance(node,ast.Assert)and ast.unparse(node.test).startswith('run_unset in'))
def run_adapter(path,unsets,output=None):
 tree=ast.parse(path.read_bytes());value=next(node.value for node in tree.body if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='script'for t in node.targets))
 remote=ast.parse(value.right.value)
 assignment=next(node for node in remote.body if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='adapted_run'for t in node.targets))
 condition=next(node for node in remote.body if isinstance(node,ast.If)and ast.unparse(node.test)=="cfg['run_environment_unset']")
 legacy=(ROOT/'retained-legacy-v2.sh').read_text();out=Path(output or '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2')
 ns={'run':legacy,'old':Path('/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative'),'out':out,'source':Path('/data1/yanruj/probata-resume-20261016-2baf722f'),'cfg':{'rss_cap_bytes':4294967296,'run_environment_unset':unsets}}
 exec(compile(ast.Module(body=[assignment,condition],type_ignores=[]),'<exact-owned-launcher-run-adaptation>','exec'),ns)
 return ns['adapted_run']
class Controls(unittest.TestCase):
 def test_exact_three_edit_inverse(self):
  source=V11.read_text();inverse=json.loads((HERE/'inverse-v11.json').read_bytes())
  for row in reversed(inverse['replacements']):self.assertEqual(source.count(row['new']),1);source=source.replace(row['new'],row['old'],1)
  self.assertEqual(source,V9.read_text())
  self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),'ec56a126e27ee74af10305652863a4eeebdb6b3bcf11a38d1970f3a8e45a5761')
 def test_only_exact_unset_pair_is_added(self):
  check=selection_assert(V11)
  for values in ([],['LIBRARY_PATH'],['LIBRARY_PATH','LD_LIBRARY_PATH']):exec(compile(ast.Module(body=[check],type_ignores=[]),'<unset-enum>','exec'),{'run_unset':values})
  for values in (['LD_LIBRARY_PATH'],['LD_PRELOAD'],['LIBRARY_PATH','LD_LIBRARY_PATH','LD_PRELOAD'],['LIBRARY_PATH; evil'],['LD_LIBRARY_PATH','LIBRARY_PATH'],'LIBRARY_PATH',None):
   with self.assertRaises(AssertionError):exec(compile(ast.Module(body=[check],type_ignores=[]),'<unset-enum>','exec'),{'run_unset':values})
 def test_prior_library_only_adaptation_matches_actual_refused_G624_bytes(self):
  before=run_adapter(V9,['LIBRARY_PATH']);after=run_adapter(V11,['LIBRARY_PATH'])
  self.assertEqual(before,after);self.assertEqual(before,(ROOT/'retained-actual-v2.sh').read_text())
  self.assertEqual(hashlib.sha256(before.encode()).hexdigest(),'e936a0092186bf1b4985ad203421412e882875d1aafd3b35d031b282f2fd0c3e')
 def test_prior_no_unset_behavior_unchanged(self):self.assertEqual(run_adapter(V9,[]),run_adapter(V11,[]))
 def test_pair_unsets_after_exports_and_before_watch_interpreter(self):
  source=run_adapter(V11,['LIBRARY_PATH','LD_LIBRARY_PATH']);old=run_adapter(V9,['LIBRARY_PATH'])
  self.assertEqual(source.replace('unset LIBRARY_PATH LD_LIBRARY_PATH\n','unset LIBRARY_PATH\n'),old)
  self.assertEqual(source.count('unset LIBRARY_PATH LD_LIBRARY_PATH\n'),1)
  self.assertLess(source.index('export LD_LIBRARY_PATH='),source.index('unset LIBRARY_PATH LD_LIBRARY_PATH\n'))
  self.assertLess(source.index('unset LIBRARY_PATH LD_LIBRARY_PATH\n'),source.index('"$PROBATA_PYTHON" "$PROBATA_OUTPUT/watch.py"'))
 def test_caps_guard_source_staging_and_worker_protocol_unchanged(self):
  source=V11.read_text()
  for token in ("rss_cap in (4294967296,8589934592)","sum(row['bytes'] for row in controls)<=1024**2","cfg['rss_cap_bytes']","assert cfg['sha']" ):
   if token=="assert cfg['sha']":continue
   self.assertIn(token,source)
  self.assertIn("assert launch['reviewed_wrapper_reuse']=={'execute.py':'ea774376",source)
  self.assertIn("'source mount needs10GiB floor",source)
  self.assertIn("'raw disk needs20GiB floor plus4GiB reserved budget'",source)
if __name__=='__main__':unittest.main(verbosity=2)

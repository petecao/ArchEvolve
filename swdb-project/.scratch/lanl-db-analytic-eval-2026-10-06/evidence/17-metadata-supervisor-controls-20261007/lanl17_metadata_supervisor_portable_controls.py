"""Portable wiring controls only; no Linux/process/campaign admission."""
import importlib.util,json,os,signal,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
SUP=Path('/private/tmp/lanl17_metadata_supervisor.py')
HELPER=Path('/private/tmp/lanl17_parent_helpers_caps_a2.py')
PROJECT=Path('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project')

def load():
 s=importlib.util.spec_from_file_location('metadata_supervisor',SUP);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m

class Returned:
 returncode=0
 pid=991234
 def wait(self,timeout):return self.returncode

class Controls(unittest.TestCase):
 def setUp(self):
  self.m=load();self.temp=tempfile.TemporaryDirectory(prefix='lanl17-supervisor-portable-');self.root=Path(self.temp.name)
  self.ctx=self.m.load_context(HELPER,PROJECT)
  self.events=[]
  self.ctx.stop_group=lambda child,grace_seconds:self.events.append(('stop_group',child))
  self.ctx.helper.cleanup_owned=lambda:self.cleanup()
 def tearDown(self):self.temp.cleanup()
 def cleanup(self):self.events.append(('cleanup_owned',));return {'subreaper':True,'terminated_owned_processes':[],'survivors':{}}
 def run_control(self,child,**kw):
  with mock.patch.object(self.m,'enable_subreaper',return_value=None),mock.patch.object(self.m.subprocess,'Popen',return_value=child):
   return self.m.supervise(self.ctx,'prepare',[sys.executable,'private-not-printed'],timeout_s=.2,receipt=self.root/'receipt.json',stdout=self.root/'stdout',stderr=self.root/'stderr',fixture=True,**kw)
 def test_mismatched_helper_refuses_before_import_or_launch(self):
  bad=self.root/'changed.py';bad.write_bytes(HELPER.read_bytes()+b'\n')
  with mock.patch.object(self.m,'load_module') as imported:
   with self.assertRaises(self.m.Refusal):self.m.load_context(bad,PROJECT)
   imported.assert_not_called()
 def test_disallowed_action_refuses_before_child_launch(self):
  with mock.patch.object(self.m.subprocess,'Popen') as launched:
   with self.assertRaises(self.m.Refusal):self.m.supervise(self.ctx,'run-campaign',[],timeout_s=1,receipt=self.root/'r',stdout=self.root/'o',stderr=self.root/'e',fixture=True)
   launched.assert_not_called()
 def test_nonfinite_or_nonpositive_timeout_refuses(self):
  for cap in (0,-1,float('inf'),float('nan')):
   with self.assertRaises(self.m.Refusal):self.m.supervise(self.ctx,'prepare',[],timeout_s=cap,receipt=self.root/'r',stdout=self.root/'o',stderr=self.root/'e',fixture=True)
 def test_linux_only_subreaper_gate(self):
  with mock.patch.object(self.m.sys,'platform','darwin'):
   with self.assertRaises(self.m.Refusal):self.m.enable_subreaper()
 def test_failed_subreaper_never_launches_or_cleans_unowned_descendants(self):
  with mock.patch.object(self.m,'enable_subreaper',side_effect=self.m.Refusal('unavailable')),mock.patch.object(self.m.subprocess,'Popen') as launched:
   code,proof=self.m.supervise(self.ctx,'prepare',[sys.executable,'fixture'],timeout_s=.2,receipt=self.root/'receipt.json',stdout=self.root/'stdout',stderr=self.root/'stderr',fixture=True)
  launched.assert_not_called();self.assertEqual(self.events,[])
  self.assertEqual(code,1);self.assertEqual(proof['state'],'supervisor_error')
  self.assertFalse(proof['cleanup']['subreaper']);self.assertEqual(proof['child_exit'],None)
 def test_returned_leader_still_runs_owned_cleanup(self):
  code,proof=self.run_control(Returned())
  self.assertEqual(code,0);self.assertEqual([e[0] for e in self.events],['stop_group','cleanup_owned'])
  self.assertEqual(proof['state'],'child_returned');self.assertEqual(proof['cleanup']['survivors'],{})
  self.assertNotIn('argv',proof);self.assertNotIn('private-not-printed',json.dumps(proof));self.assertTrue(proof['fixture'])
  self.assertEqual(self.m.seal({k:v for k,v in proof.items() if k!='identity_sha256'}),proof)
 def test_timeout_unwinds_cleanup_and_seals_timeout(self):
  class Timeout(Returned):
   returncode=None
   def wait(self,timeout):raise subprocess.TimeoutExpired('secret-argument',timeout)
  code,proof=self.run_control(Timeout())
  self.assertEqual(code,124);self.assertTrue(proof['timed_out']);self.assertEqual(proof['state'],'timeout')
  self.assertEqual([e[0] for e in self.events],['stop_group','cleanup_owned'])
  self.assertNotIn('secret-argument',json.dumps(proof))
 def test_external_term_unwinds_finally_and_restores_handlers(self):
  before={s:signal.getsignal(s) for s in self.m.SIGNALS}
  class Terminated(Returned):
   returncode=None
   def wait(self,timeout):os.kill(os.getpid(),signal.SIGTERM)
  code,proof=self.run_control(Terminated())
  self.assertEqual(code,143);self.assertEqual(proof['signal_received'],'SIGTERM');self.assertEqual(proof['state'],'signal')
  self.assertEqual([e[0] for e in self.events],['stop_group','cleanup_owned'])
  self.assertEqual({s:signal.getsignal(s) for s in self.m.SIGNALS},before)
 def test_survivor_never_reports_success(self):
  self.ctx.helper.cleanup_owned=lambda:{'subreaper':True,'terminated_owned_processes':[],'survivors':{123:{'ppid':1,'start_time':'fixture'}}}
  code,proof=self.run_control(Returned());self.assertNotEqual(code,0);self.assertEqual(proof['state'],'cleanup_failed')
  self.assertTrue(proof['cleanup']['survivors'])

if __name__=='__main__':
 unittest.main(verbosity=2)

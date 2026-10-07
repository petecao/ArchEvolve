"""Bounded sleep-process alarm/cleanup fixture only. Updated: 2026-10-07 ET."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
sys.dont_write_bytecode=True
source=Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket14/ArchEvolve')
sys.path.insert(0,str(source/'swdb-project'))
from swdb.processes import stop_group
runner=Path('/private/tmp/lanl14-pr-final-local-runner-catalog-caps-20261007-a4.py')
envelope=Path('/private/tmp/lanl14-pr-final-local-envelope-catalog-caps-20261007-a4.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert sha(runner)=='d0209039a6f39f6824229918db3c927d47f68c468f90382aa58deecbd0be7ed7'
assert sha(envelope)=='99ed6a5922c6e65e4be0cd3dcc1cb0fa5f37469fe85a3d0751af5a59aa3c69d2'
state={};child=None;sibling=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'],start_new_session=True)
saved_spec=importlib.util.spec_from_file_location;saved_itimer=signal.setitimer
old_handlers={value:signal.getsignal(value) for value in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
def fixture_main():
 global child
 child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'],start_new_session=True)
 try:child.wait(timeout=5)
 finally:
  state['finally_reached']=True;stop_group(child,grace_seconds=1)
def fixture_spec(name,path,*args,**kwargs):
 spec=saved_spec(name,path,*args,**kwargs)
 if Path(path)==runner:
  exec_module=spec.loader.exec_module
  def with_fixture(module):exec_module(module);module.main=fixture_main
  spec.loader.exec_module=with_fixture
 return spec
def fixture_itimer(which,seconds,*args):
 if seconds:
  assert which==signal.ITIMER_REAL and seconds==10000;state['bound_s']=seconds
  return saved_itimer(which,.25,*args)
 return saved_itimer(which,seconds,*args)
try:
 importlib.util.spec_from_file_location=fixture_spec;signal.setitimer=fixture_itimer
 try:runpy.run_path(str(envelope),run_name='__main__')
 except SystemExit as exc:assert exc.code==2;state['alarm_exit']=True
 else:raise AssertionError('Alarm did not unwind runner finally')
 assert state=={'bound_s':10000,'finally_reached':True,'alarm_exit':True}
 assert child.poll() is not None
 try:os.killpg(child.pid,0)
 except ProcessLookupError:state['owned_group_empty']=True
 else:raise AssertionError('Owned process group survived')
 assert sibling.poll() is None;state['separate_sibling_survived']=True
finally:
 importlib.util.spec_from_file_location=saved_spec;signal.setitimer=saved_itimer;saved_itimer(signal.ITIMER_REAL,0)
 for value,handler in old_handlers.items():signal.signal(value,handler)
 stop_group(child,grace_seconds=1);stop_group(sibling,grace_seconds=1)
assert subprocess.check_output(['git','status','--porcelain'],cwd=source)==b''
module_hashes={p.relative_to(source/'swdb-project/swdb').as_posix():sha(p) for p in sorted((source/'swdb-project/swdb').rglob('*.py'))}
assert len(module_hashes)==185 and digest(module_hashes)=='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
pins={'14-pr-final-freeze-request-20261007-a1.json':'2ee4a07880bb1bca74b5e3611d0a7147befc9ebabb340a832935c4c32443fe90','14-check-pr-final-replay-20261007.py':'86df23903c131913cd952d3648cfed58e43824982308082bb235579d4b7da3bf'}
for name,pin in pins.items():assert sha(source/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence'/name)==pin
proof={'format':'swdb.lanl14-local-metadata-envelope-cleanup-proof.v1','updated':'2026-10-07 ET','scope':'Bounded local sleep-process fixture; only the fixture alarm shortened to0.25s. Actual envelope observes10000s and unwinds existing finally; no application/compiler/provider/remote execution or actual PR acceptance.',
 'envelope_sha256':sha(envelope),'runner_sha256':sha(runner),'global_bound_s':state['bound_s'],'alarm_unwinds_child_finally':state['finally_reached'],'owned_group_empty':state['owned_group_empty'],'separate_sibling_survived':state['separate_sibling_survived'],
 'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'source_clean':True,'estimator_sha256':digest(module_hashes),'module_count':len(module_hashes),'preserved_request_and_checker_file_pins':pins,'application_execution':0,'provider_calls':0,'remote_actions':0}
proof['identity_sha256']=digest(proof);out=Path('/private/tmp/lanl14-local-envelope-cleanup-proof-catalog-caps-20261007-a4.json');out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'proof':str(out),'identity_sha256':proof['identity_sha256'],'owned_group_empty':True,'separate_sibling_survived':True}))

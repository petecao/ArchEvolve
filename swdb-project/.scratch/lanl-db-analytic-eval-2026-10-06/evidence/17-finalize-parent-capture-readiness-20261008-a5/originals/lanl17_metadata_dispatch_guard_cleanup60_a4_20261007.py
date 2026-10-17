"""Parent-reviewed prepare/finalize admission only; imports execute no action.

Parent wraps the actual invocation in its prescribed finite timeout. This guard
then execs the pinned metadata supervisor through the selected inner timeout.
No Store/science/provider/lease acquisition; helper tails are passed unchanged.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import socket
import subprocess
import sys

sys.dont_write_bytecode=True
HELPER=Path('/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py')
HELPER_SHA='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
SUPERVISOR=Path('/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py')
SUPERVISOR_SHA='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
PROCESSES_SHA='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
SMOKE_SHA='4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6'
FIXTURE_SHA='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
RUNS=Path('/data/yanruj/EvolveSWDB_runs')
SOURCE_PARENT=Path('/data1/yanruj')
LEASE_ROOT=SOURCE_PARENT/'lact-host-lease'
LOGIN=SOURCE_PARENT/'.codex'
HOME_TOKEN='SWDB_LANL17_ORIGINAL_CODEX_HOME'
EXPECTED_CLEANUP=RUNS/'lanl17-cleanup-smoke-20261007-a4/receipt.json'
EXPECTED_SUPERVISOR_PROOF=RUNS/'lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json'
LIMITS={'prepare':{'wait':18000,'term':18120,'kill':60,'parent':18300},
        'finalize':{'wait':78000,'term':78120,'kill':60,'parent':78300}}

class Refusal(ValueError):pass
def require(condition,reason):
 if not condition:raise Refusal(reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value,*,ensure_ascii=False):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=ensure_ascii).encode()).hexdigest()
def sealed(path,*,ensure_ascii=True):
 require(path.is_file() and not path.is_symlink() and path.stat().st_size<=4*1024*1024,'bounded regular receipt/manifest required')
 value=json.loads(path.read_text());require(value['identity_sha256']==digest({k:v for k,v in value.items() if k!='identity_sha256'},ensure_ascii=ensure_ascii),'receipt/manifest seal differs')
 return value
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],timeout=120).decode().strip()
def python_tree(root,ref):
 rows=subprocess.check_output(['git','-C',str(root),'ls-tree','-rz',ref,'--','swdb-project/swdb'],timeout=120)
 return {r.split(b'\t',1)[1].decode():r.split(b'\t',1)[0].decode() for r in rows.split(b'\0') if r and r.split(b'\t',1)[1].endswith(b'.py')}
def clean_project(project,revision=None):
 require(project.is_absolute() and project.name=='swdb-project' and not project.is_symlink(),'explicit regular project directory required')
 root=project.parent;head=git(root,'rev-parse','HEAD')
 require(not git(root,'status','--porcelain'),'cleanup source checkout must stay clean')
 if revision is not None:require(head==revision,'source checkout differs from required finalR')
 modules={p.relative_to(project/'swdb').as_posix():sha(p) for p in sorted((project/'swdb').rglob('*.py'))}
 require(len(modules)==185 and digest(modules)==F6 and sha(project/'swdb/processes.py')==PROCESSES_SHA,'frozen F6/process bytes differ')
 return root,head
def all_free():
 rows={name:json.loads((LEASE_ROOT/(name+'.meta.json')).read_text()) for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
 require(all(row['state']=='released' for row in rows.values()),'metadata requires both socket and legacy leases released')
 return {name:row['state'] for name,row in rows.items()}
def proof(path,expected_path,expected_format,identity,*,ensure_ascii=True):
 require(path.is_absolute() and path==expected_path and path.resolve(strict=True)==expected_path,'explicit fresh a4 proof path required; old69 proof is refused')
 require(re.fullmatch('[0-9a-f]{64}',identity) is not None,'parent-reviewed actual proof identity required')
 value=sealed(path,ensure_ascii=ensure_ascii);require(value['identity_sha256']==identity and value['format']==expected_format and value['passed'] is True,'parent-reviewed exact actual proof differs')
 require(value['host']=='mbit10' and path.stat().st_uid==os.getuid(),'actual cleanup host/receipt owner differs')
 if 'uid' in value:require(value['uid']==os.getuid(),'actual serialized cleanup UID differs')
 require(value['helper_sha256']==HELPER_SHA and value['processes_py_sha256']==PROCESSES_SHA,'actual helper/process pin differs')
 require(value['provider_calls']==value['application_outcomes']==0 and value['cleanup']['subreaper'] is True and value['cleanup']['survivors']=={},'actual proof must have no outcomes/providers/owned survivors')
 return value
def parent_envelope(action):
 parent=Path('/proc')/str(os.getppid());require(parent.stat().st_uid==os.getuid(),'metadata parent UID differs')
 argv=parent.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
 require(Path(argv[0]).name=='timeout' and argv[1:4]==['--signal=TERM','--kill-after=60s',str(LIMITS[action]['parent'])+'s'],'exact finite parent timeout envelope required')
 require(len(argv)>5 and Path(argv[4]).name in ('python3','python3.12') and Path(argv[5]).resolve(strict=True)==Path(__file__).resolve(strict=True),'parent envelope must directly own this guard')
 return {'pid':os.getppid(),'start_time':parent.joinpath('stat').read_text().rsplit(')',1)[1].split()[19],'argv_sha256':digest(argv),'timeout_s':LIMITS[action]['parent'],'kill_after_s':60}
def tail_values(action,tail):
 p=argparse.ArgumentParser(add_help=False,allow_abbrev=False)
 names=('source-sha','cleanup-proof','source-ref','source','raw','tag') if action=='prepare' else ('manifest',)
 for name in names:
  require(tail.count('--'+name)==1,'helper argument must occur exactly once: '+name)
  p.add_argument('--'+name,required=True)
 require(len(tail)==2*len(names),'helper tail must contain only its original reviewed arguments')
 return p.parse_args(tail)

def main():
 p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
 p.add_argument('--action',required=True,choices=sorted(LIMITS));p.add_argument('--final-source-sha',required=True)
 p.add_argument('--project',required=True,type=Path);p.add_argument('--control',required=True,type=Path)
 p.add_argument('--guard-sha256',required=True);p.add_argument('--cleanup-proof',required=True,type=Path);p.add_argument('--cleanup-proof-identity',required=True)
 p.add_argument('--supervisor-proof',required=True,type=Path);p.add_argument('--supervisor-proof-identity',required=True)
 p.add_argument('arguments',nargs=argparse.REMAINDER);args=p.parse_args()
 require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()!=0,'mbit10 Linux non-root required')
 require(re.fullmatch('[0-9a-f]{40}',args.final_source_sha) is not None,'explicit full finalR commit required')
 require(re.fullmatch('[0-9a-f]{64}',args.guard_sha256) is not None and sha(__file__)==args.guard_sha256,'reviewed guard bytes differ')
 require(HELPER.is_file() and not HELPER.is_symlink() and sha(HELPER)==HELPER_SHA,'selected cleanup60 helper bytes differ')
 require(SUPERVISOR.is_file() and not SUPERVISOR.is_symlink() and sha(SUPERVISOR)==SUPERVISOR_SHA,'selected cleanup60 supervisor bytes differ')
 outer=parent_envelope(args.action);leases=all_free();root,cleanup_head=clean_project(args.project)
 require(git(root,'rev-parse',args.final_source_sha+'^{commit}')==args.final_source_sha,'finalR object is unavailable; parent must deliver it first')
 final_code=python_tree(root,args.final_source_sha)
 require(len(final_code)==185 and final_code==python_tree(root,cleanup_head),'finalR Python blobs differ from clean tested F6 cleanup source')
 require(os.environ.get('HOME')==pwd.getpwuid(os.getuid()).pw_dir,'account HOME must remain unchanged')
 require(os.environ.get('CODEX_HOME') and Path(os.environ['CODEX_HOME']).resolve(strict=True)==LOGIN.resolve(strict=True),'verified original CODEX_HOME must be restored before guard invocation')
 if HOME_TOKEN in os.environ:require(Path(os.environ[HOME_TOKEN]).resolve(strict=True)==LOGIN.resolve(strict=True),'original task token differs')
 require((LOGIN/'auth.json').is_file(),'authentication existence only; credential contents remain unread')
 cleanup=proof(args.cleanup_proof,EXPECTED_CLEANUP,'swdb.lanl17-linux-cleanup-smoke.v1',args.cleanup_proof_identity)
 require(cleanup['smoke_script_sha256']==SMOKE_SHA and cleanup['platform']=='linux' and cleanup['unrelated_sibling_survived'] is True,'original4d primitive proof differs')
 require(cleanup['same_group_after_returned_leader']=='terminated' and cleanup['detached_session']=='terminated_and_reaped','original4d cleanup proof incomplete')
 meta=proof(args.supervisor_proof,EXPECTED_SUPERVISOR_PROOF,'swdb.lanl17-metadata-supervisor-linux-fixture.v1',args.supervisor_proof_identity,ensure_ascii=False)
 require(meta['supervisor_sha256']==SUPERVISOR_SHA and meta['fixture_script_sha256']==FIXTURE_SHA and meta['estimator_sha256']==F6,'new supervisor fixture pins differ')
 require(meta['cleanup_errors']==[] and meta['failure_type'] is None and [r['case'] for r in meta['cases']]==['returned','timeout','term'],'three actual supervisor cases required')
 require(all(row['passed'] is True and row['supervisor_exit']==code and row['unrelated_sibling_survived'] is True and row['owned_after']=='terminated_and_reaped' for row,code in zip(meta['cases'],(0,124,143))),'actual supervisor case cleanup differs')
 tail=list(args.arguments)
 if tail and tail[0]=='--':tail=tail[1:]
 values=tail_values(args.action,tail)
 if args.action=='prepare':
  require(values.source_sha==args.final_source_sha and Path(values.cleanup_proof)==args.cleanup_proof,'unchanged helper tail must bind explicit finalR and new actual proof')
  source,raw=Path(values.source),Path(values.raw)
  require(source.is_absolute() and source.parent.resolve(strict=True)==SOURCE_PARENT.resolve(strict=True) and source.name.startswith('ArchEvolve-lanl17-'),'fresh dedicated source scope required')
  require(raw.is_absolute() and raw.parent.resolve(strict=True)==RUNS.resolve(strict=True) and raw.name.startswith('lanl17-'),'fresh dedicated raw scope required')
  require(not source.exists() and not source.is_symlink() and not raw.exists() and not raw.is_symlink(),'fresh source/raw only; preserve prior attempts')
  require(re.fullmatch('[a-z0-9-]+',values.tag) is not None,'original helper tag syntax differs')
 else:
  manifest_path=Path(values.manifest);manifest=sealed(manifest_path);source,raw=Path(manifest['source']),Path(manifest['raw'])
  require(manifest['source_commit']==args.final_source_sha and manifest['helper_sha256']==HELPER_SHA and manifest['estimator_sha256']==F6,'retained manifest differs from explicit finalR/helper/F6')
  require(manifest_path.is_absolute() and manifest_path.resolve(strict=True)==(raw/'manifest.json').resolve(strict=True),'retained canonical manifest required')
  require(manifest['linux_cleanup_proof']['path']==str(args.cleanup_proof) and manifest['linux_cleanup_proof']['receipt']==cleanup and manifest['linux_cleanup_proof']['sha256']==sha(args.cleanup_proof),'frozen actual cleanup proof differs')
  require(args.project.resolve(strict=True)==(source/'swdb-project').resolve(strict=True),'finalize supervisor project must be the actual frozen source')
  clean_project(args.project,args.final_source_sha)
 require(args.control.is_absolute() and args.control.parent.resolve(strict=True)==RUNS.resolve(strict=True) and args.control.name.startswith('lanl17-metadata-'),'fresh separate metadata control directory required')
 require(not args.control.exists() and not args.control.is_symlink() and args.control!=raw,'never overwrite raw/control attempts')
 limits=LIMITS[args.action];timeout=shutil.which('timeout');require(timeout is not None,'GNU timeout prerequisite missing')
 argv=[timeout,'--signal=TERM','--kill-after=60s',str(limits['term'])+'s',sys.executable,str(SUPERVISOR),
       '--helper',str(HELPER),'--project',str(args.project),'--action',args.action,'--timeout-s',str(limits['wait']),
       '--receipt',str(args.control/'supervisor-receipt.json'),'--stdout',str(args.control/'helper.stdout'),'--stderr',str(args.control/'helper.stderr'),'--',*tail]
 require(all_free()==leases,'lease state changed during metadata preflight')
 require(sha(HELPER)==HELPER_SHA and sha(SUPERVISOR)==SUPERVISOR_SHA,'controls changed before exec')
 args.control.mkdir()
 registration={'format':'swdb.lanl17-metadata-dispatch-preregistration.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'action':args.action,'final_source_commit':args.final_source_sha,'cleanup_source_commit':cleanup_head,'source_code_equivalent_F6':True,
  'source':str(source),'raw':str(raw),'project':str(args.project),'guard_sha256':args.guard_sha256,'helper_sha256':HELPER_SHA,
  'supervisor_sha256':SUPERVISOR_SHA,'processes_sha256':PROCESSES_SHA,'estimator_sha256':F6,
  'actual_cleanup_proof':{'path':str(args.cleanup_proof),'file_sha256':sha(args.cleanup_proof),'identity_sha256':cleanup['identity_sha256']},
  'actual_supervisor_proof':{'path':str(args.supervisor_proof),'file_sha256':sha(args.supervisor_proof),'identity_sha256':meta['identity_sha256']},
  'limits':limits,'parent_envelope':outer,'leases_before_exec':leases,'argv_sha256':digest(argv),'helper_tail_sha256':digest(tail),
  'account_HOME_unchanged':True,'CODEX_HOME_original_verified':True,'auth_file_exists':True,'authentication_contents_read':False,
  'scope':'Parent metadata action admission only; full helper validation remains; no scientific/campaign/provider budget change or numerical eligibility claim.'}
 registration['identity_sha256']=digest(registration)
 (args.control/'preregistration.json').write_text(json.dumps(registration,indent=2)+'\n')
 print(json.dumps({'action':args.action,'final_source_commit':args.final_source_sha,'control':str(args.control),'preregistration_identity':registration['identity_sha256'],'argv_sha256':registration['argv_sha256'],'limits':limits}),flush=True)
 os.execv(timeout,argv)

if __name__=='__main__':
 try:main()
 except Refusal as exc:
  print('metadata guard refused: '+str(exc),file=sys.stderr);sys.exit(2)
 except (KeyError,ValueError,FileNotFoundError,subprocess.SubprocessError) as exc:
  print('metadata guard refused: '+type(exc).__name__,file=sys.stderr);sys.exit(2)

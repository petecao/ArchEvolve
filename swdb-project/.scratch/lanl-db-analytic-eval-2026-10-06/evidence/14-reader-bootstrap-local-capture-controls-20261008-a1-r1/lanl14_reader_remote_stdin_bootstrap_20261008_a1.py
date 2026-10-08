"""SOURCE ONLY: reader preflight/original custody, then exact GNU -> 503f -> 690.
No selected main runs unless a parent supplies and reviews actual exported pins.
"""
import argparse,hashlib,json,os,platform,pwd,re,socket,stat,subprocess,sys,time,types
from pathlib import Path
UID=114316761
PRIMARY=Path('/data1/yanruj/ArchEvolve')
CROOT=Path('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
PROJECT=CROOT/'swdb-project'
SOURCE=Path('/data1/yanruj/ArchEvolve-lanl-generality-final-20261007-a1')
EXPORT=Path('/data1/yanruj/ArchEvolve-lanl-generality-final-export-20261007-a1')
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl-generality-final-20261007-a1')
ADMIN=RAW.parent/'lanl14-export-reader-administration-20261007-a1'
CONTROL=ADMIN/'lanl14-export-reader-control-reader-a1'
EVIDENCE=Path('.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
ARCHIVE=PRIMARY/'swdb-project'/EVIDENCE
SUP=ARCHIVE/'14-export-reader-lifecycle-supervisor-controls-20261007-a1/lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py'
READER=ARCHIVE/'14-lossless-report-export-controls-20261007-a1/lanl14_readonly_nine_export_admission_lossless_gzip_20261007_a1.py'
READONLY=ARCHIVE/'14-completed-report-transfer-mode-controls-20261008-a1/lanl14_correct_completed_report_transfer_modes_20261008_a1.py'
CLEANUP=Path('/data1/yanruj/lanl17-control-20261006.py')
PY=Path('/usr/bin/python3.12');GNU=Path('/usr/bin/timeout');GIT=Path('/usr/bin/git')
R='c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
M='e452b68e7d98cf949ad1be24b1471ee265f0f9811e0f8735f91f38a517cfea8b'
SUPSHA='503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f'
READSHA='6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570'
HSH='ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7'
CLEANSH='31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
PROCSH='bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
PYSH='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
GNUSH='12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'
GITSH='06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'
COUNT=EVIDENCE/'14-generality-counts-mbit10-20261006-a1.json'
COUNTSH='3679c37e531aea944e0e7efb227f460c72e63bdd6f5577251db9ac972660c3e1'
TARGETS={'cpu':{'id':'mbit10.cpu.lanl20261006.t1.services.v1','sha256':'9fec46b1ab4c8ac2e8e501e61cf137c075ec40b6eef128a247cf28dd54fca76b'},'dx100':{'id':'dx100-e4fc4af-functional-analytic-v1.t4.estimated.a2','sha256':'f436047a21f77eda649f99aa5ceb5b5c8cb13e4ab7eed770441e7faad07aaf02'},'maple':{'id':'maple-isca2022.fpga-reference.t2','sha256':'74face99dcf178f0c9d7e057b77a840245fff0f2f33e500db677516cbd3ee7e8'}}
STARTUP=('BASH_ENV','ENV','PYTHONHOME','LD_PRELOAD','LD_LIBRARY_PATH','SOCKET_LANE_REEXEC','SOCKET_LANE_NODE_DIR','LACT_LEASE_ROOT','LACT_LEASE_NAME','LACT_NUMACTL','LOCKDIR')
MAXJSON=8*1024*1024;MAXFILE=100*1024*1024
class Refusal(ValueError):pass
class Parser(argparse.ArgumentParser):
 def error(self,message):raise Refusal('argument_contract')
def require(ok,code):
 if not ok:raise Refusal(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return tuple(getattr(s,n) for n in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def boot_read(path,maximum,expected,size,owner=UID):
 p=Path(path);require(p.is_absolute() and '..' not in p.parts,'absolute_path')
 for q in (p,*p.parents):require(not q.is_symlink(),'no_symlink')
 s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and not s.st_mode&0o022 and s.st_size==size and size<=maximum,'bootstrap_source_type_mode_size')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  require(stamp(os.fstat(fd))==stamp(s),'bootstrap_opened_stat')
  chunks=[];total=0
  while total<=maximum:
   b=os.read(fd,min(1024*1024,maximum-total+1))
   if not b:break
   chunks.append(b);total+=len(b)
  raw=b''.join(chunks)
  require(len(raw)==size and sha(raw)==expected and stamp(os.fstat(fd))==stamp(s)==stamp(p.lstat()),'bootstrap_returned_bytes')
 finally:os.close(fd)
 return raw

def reader_tail(a):
 return ['--checkout',str(EXPORT),'--export-commit',a.export_commit,'--source-commit',R,'--manifest-sha256',M,'--receipt-sha256',a.receipt_sha256,'--receipt-identity-sha256',a.receipt_identity_sha256,'--tag','final-20261007-a1','--receipt',str(EVIDENCE/'14-generality-final-final-20261007-a1-export.json'),'--report',a.report_relative,'--request',str(EVIDENCE/'14-generality-final-final-20261007-a1-request.json'),'--markdown',str(EVIDENCE/'14-generality-final-final-20261007-a1-report.md'),'--count-receipt',str(COUNT),'--count-receipt-sha256',COUNTSH,'--target-pins',json.dumps(TARGETS,sort_keys=True,separators=(',',':'))]
def full_argv(a):
 return [str(GNU),'--signal=TERM','--kill-after=60s','14520s',str(PY),'-B',str(SUP),'--cleanup-helper',str(CLEANUP),'--project',str(PROJECT),'--selected-source',str(READER),'--action','reader','--timeout-s','14400','--python',str(PY),'--python-sha256',PYSH,'--supervisor-sha256',SUPSHA,'--cwd',str(EXPORT/'swdb-project'),'--control-directory',str(CONTROL),'--',*reader_tail(a)]
def explicit_env():
 return {'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(EXPORT/'swdb-project'),'OMP_NUM_THREADS':'1','OMP_THREAD_LIMIT':'1','OMP_DYNAMIC':'FALSE','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'}
def main():
 os.umask(0o077)
 p=Parser(description=__doc__)
 for name in ('expected-primary','export-commit','receipt-sha256','receipt-identity-sha256','report-relative'):p.add_argument('--'+name,required=True)
 p.add_argument('--metadata-seconds',required=True,type=int)
 a=p.parse_args()
 require(all(re.fullmatch('[a-f0-9]{40}',v) for v in (a.expected_primary,a.export_commit)),'exact_commits')
 require(all(re.fullmatch('[a-f0-9]{64}',v) for v in (a.receipt_sha256,a.receipt_identity_sha256)),'exact_receipt_pins')
 require(type(a.metadata_seconds)is int and 60<=a.metadata_seconds<=3600,'metadata_bound')
 require(a.report_relative in {str(EVIDENCE/'14-generality-final-final-20261007-a1-report.json'),str(EVIDENCE/'14-generality-final-final-20261007-a1-report.json.gz')},'actual_report_route')
 require(not any(k in os.environ for k in STARTUP),'startup_override')
 require(re.fullmatch('[a-f0-9]{64}',str(globals().get('__source_sha256__',''))),'verified_stdin_source_pin')
 require(sys.platform=='linux' and platform.machine()=='x86_64' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and Path(sys.executable).resolve()==PY and sys.flags.dont_write_bytecode and not sys.flags.optimize,'native_account_flags')
 for native_path,native_size,native_sha in ((PY,8020928,PYSH),(GNU,39880,GNUSH),(GIT,4019024,GITSH)):
  native_raw=boot_read(native_path,128*1024*1024,native_sha,native_size,0)
  require(native_raw[:6]==b'\x7fELF\x02\x01' and int.from_bytes(native_raw[18:20],'little')==62 and os.access(native_path,os.X_OK),'native_before_reviewed_import')
 helper_raw=boot_read(READONLY,MAXJSON,HSH,29985)
 h=types.ModuleType('lanl14_reader_exact_readonly_primitives');h.__file__=str(READONLY)
 exec(compile(helper_raw,str(READONLY),'exec'),h.__dict__) # Future only; __name__ is not __main__.
 require(h.__name__!='__main__','readonly_main_uncalled')
 budget=h.Budget(a.metadata_seconds)
 native=h.native(budget)
 gn,body=h.read_file(GNU,128*1024*1024,budget,GNUSH,True,0)
 require(gn['bytes']==39880 and body[:6]==b'\x7fELF\x02\x01' and int.from_bytes(body[18:20],'little')==62 and not gn['stat']['st_mode']&0o022 and gn['stat']['st_mode']&0o111,'GNU_pin')
 native[str(GNU)]=gn
 # Read-only exact sources: no correction.main or fchmod is referenced.
 pins={}
 for path,size,digest in ((SUP,14547,SUPSHA),(READER,37647,READSHA),(PROJECT/'swdb/processes.py',912,PROCSH),(CLEANUP,38190,CLEANSH),(READONLY,29985,HSH)):
  pin,_=h.read_file(path,MAXJSON,budget,digest)
  require(pin['bytes']==size and stat.S_IMODE(pin['stat']['st_mode'])==0o644,'selected_code0644')
  pins[str(path)]=pin
 def git(root,*args):
  budget.check()
  result=subprocess.run([str(GIT),'-C',str(root),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(25,max(.001,budget.deadline-time.monotonic())),env={**os.environ,**explicit_env()},check=False)
  require(result.returncode==0 and len(result.stdout)<=1024*1024,'readonly_git')
  return result.stdout.decode().strip()
 require(git(PRIMARY,'rev-parse','HEAD')==git(PRIMARY,'rev-parse','origin/yanrujhou_main')==a.expected_primary and git(PRIMARY,'branch','--show-current')=='yanrujhou_main','delivered_primary')
 require(git(PRIMARY,'status','--porcelain','--untracked-files=all')=='?? swdb-project/records/.retention.lock','primary_exact_untracked_retention')
 lock=PRIMARY/'swdb-project/records/.retention.lock';s=lock.lstat()
 require(not lock.is_symlink() and stat.S_ISREG(s.st_mode) and (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_nlink,s.st_size,stat.S_IMODE(s.st_mode))==(2097,54947305,UID,0,1,0,0o666),'retention_original_stat')
 with lock.open('rb') as f:require(f.read(1)==b'' and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(lock.lstat()),'retention_empty_stable')
 require(git(CROOT,'rev-parse','HEAD')==C and not git(CROOT,'status','--porcelain'),'C_exact_clean')
 r14=h.source_identity(budget)
 require(git(EXPORT,'rev-parse','HEAD')==a.export_commit and git(EXPORT,'branch','--show-current')=='codex/lanl-generality-estimate-evidence-20261007-a1' and not git(EXPORT,'status','--porcelain'),'pure_E_clean')
 require(git(EXPORT,'rev-list','--parents','-n','1',a.export_commit).split()==[a.export_commit,R],'pure_E_sole_R_parent')
 receipt_path=EXPORT/'swdb-project'/EVIDENCE/'14-generality-final-final-20261007-a1-export.json'
 receipt,rpin=h.read_json(receipt_path,budget,a.receipt_sha256,True)
 require(receipt['identity_sha256']==a.receipt_identity_sha256 and receipt['format']=='swdb.lanl14-final-report-export.v1' and receipt['source_commit']==R and receipt['source_clean'] is True and receipt['manifest_sha256']==M,'actual_export_receipt')
 require(receipt['exporter_sha256']=='928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e' and receipt['provider_calls']==receipt['application_timings']==0 and receipt['raw_transferred'] is False and receipt['cleanup_survivors']=={} and receipt['prior_record_library_app_bytes_preserved'] is True and receipt['validation'].startswith('OK: '),'export_scope')
 acceptance=receipt['acceptance']
 require(acceptance['identity_sha256']==h.true_digest({k:v for k,v in acceptance.items() if k!='identity_sha256'}) and acceptance['all_nine_public_estimates'] is True and acceptance['final_estimator_sha256']==F6 and acceptance['source_commit']==R and acceptance['source_clean'] is True and acceptance['manifest_sha256']==M,'inherited_original_acceptance')
 require(acceptance['provider_calls']==acceptance['application_timings']==0 and acceptance['raw_transferred'] is False and acceptance['prior_record_library_app_bytes_preserved'] is True and acceptance['validation'].startswith('OK: '),'inherited_complete_scope')
 closure=receipt['new_records'];require(len(closure)==receipt['new_canonical_records']==18 and len({r['id'] for r in closure})==18 and len({r['path'] for r in closure})==18,'18_unique_canonical')
 require(sum(r['kind']=='protocol' for r in closure)==sum(r['kind']=='estimate' for r in closure)==9,'9_protocol_9_estimate')
 metadata={str(Path('swdb-project')/EVIDENCE/n) for n in ('14-generality-final-final-20261007-a1-export.json',Path(a.report_relative).name,'14-generality-final-final-20261007-a1-request.json','14-generality-final-final-20261007-a1-report.md')}
 canonical=set()
 record_pins={}
 for row in closure:
  rel=Path(row['path']);require(bool(rel.parts) and not rel.is_absolute() and '..' not in rel.parts and rel.suffix in ('.yaml','.yml'),'canonical_relative_path')
  path=EXPORT/'swdb-project/records'/rel
  pin,_=h.read_file(path,MAXFILE,budget,row['file_sha256']);require(pin['bytes']==row['bytes'],'new_record_pin_size')
  canonical.add(str(Path('swdb-project/records')/rel));record_pins[row['id']]=pin
 changed=[r.split('\t') for r in git(EXPORT,'diff','--name-status',R,a.export_commit).splitlines()]
 require(len(changed)==22 and all(r[0]=='A' for r in changed) and {r[1] for r in changed}==canonical|metadata,'22_additions_prior_blobs_modes_preserved')
 def yaml_count(rev):return sum(v.endswith(('.yaml','.yml')) for v in git(EXPORT,'ls-tree','-r','--name-only',rev,'--','swdb-project/records').splitlines())
 require(yaml_count(R)==686 and yaml_count(a.export_commit)==704,'canonical_membership686_704')
 transfer=receipt['report_transfer'];require(transfer['exported']['path']==a.report_relative and transfer['encoding'] in ('identity','gzip'),'receipt_selected_representation')
 expected_name='14-generality-final-final-20261007-a1-report.json'+('.gz' if transfer['encoding']=='gzip' else '')
 require(Path(a.report_relative).name==expected_name,'encoding_path')
 tp,_=h.read_file(EXPORT/'swdb-project'/a.report_relative,MAXFILE,budget,transfer['exported']['sha256']);require(tp['bytes']==transfer['exported']['bytes'],'transfer_byte_pin')
 countpin,_=h.read_file(EXPORT/'swdb-project'/COUNT,MAXJSON,budget,COUNTSH)
 modules={}
 for project in (PROJECT,EXPORT/'swdb-project'):
  selected=sorted((project/'swdb').rglob('*.py'));require(len(selected)==185,'185_modules')
  values={p.relative_to(project/'swdb').as_posix():h.read_file(p,MAXJSON,budget)[0]['sha256'] for p in selected}
  require(h.true_digest(values)==F6,'same_F6');modules[str(project)]=values
 leases=h.released(budget)
 for root in (ADMIN,PROJECT,EXPORT,SOURCE,RAW):h.checked(root,True)
 require(stat.S_IMODE(ADMIN.lstat().st_mode)==0o700 and not CONTROL.exists() and not CONTROL.is_symlink(),'fresh_CONTROL_private_ADMIN')
 originals=[ADMIN/n for n in ('reader-invocation-preregistration-a1.json',)]
 require(all(not p.exists() and not p.is_symlink() for p in originals),'fresh_reader_preregistration')
 require(all(not CONTROL.is_relative_to(p) and not p.is_relative_to(CONTROL) for p in (PROJECT,EXPORT,SOURCE,RAW)),'control_disjoint')
 argv=full_argv(a);overrides=explicit_env()
 prereg={'format':'swdb.lanl14-original-reader-invocation-preregistration.v1','sealed':False,'scientific_admission':False,'execution_not_yet_started':True,'created_utc':h.now(),'expected_primary':a.expected_primary,'export_commit':a.export_commit,'source_commit':R,'manifest_identity_sha256':M,'uid':UID,'cwd':str(EXPORT/'swdb-project'),'public_argv':argv,'explicit_environment_overrides':overrides,'inherited_environment_or_auth_dumped':False,'native':native,'source_pins':pins,'actual_export_receipt':rpin,'receipt_identity_sha256':a.receipt_identity_sha256,'report_transfer_file_pin':tp,'count_receipt_file_pin':countpin,'new_canonical_byte_pins':record_pins,'F6':F6,'modules':185,'released_leases':leases,'R14_source_identity':r14,'retention_original_stat':stamp(s),'GNU_outer_s':14520,'GNU_KILL_s':60,'unchanged_reader_wait_s':14400,'metadata_preflight_s':a.metadata_seconds,'stdin_bootstrap_sha256':globals().get('__source_sha256__'),'stdin_bootstrap_hash_verified_by_parent_loader':True,'postflight_is_separate_parent_metadata':True,'original_child_stdout_stderr_remain_remote':True,'selected_reader_format':'swdb.lanl14-selected-nine-export-admission.v1','no_admitted_flag_invented':True,'actual_receipt_and_cleanup_checks_required_after_execution':True,'no_retry':True}
 h.private_json(originals[0],prereg)
 # Recheck immutable inputs immediately before replacement. No main of the read-only helper.
 for path,pin in pins.items():require(h.read_file(path,MAXJSON,budget,pin['sha256'])[0]==pin,'immediate_code_recheck')
 for project,values in modules.items():
  selected=sorted((Path(project)/'swdb').rglob('*.py'))
  current={p.relative_to(Path(project)/'swdb').as_posix():h.read_file(p,MAXJSON,budget)[0]['sha256'] for p in selected}
  require(len(selected)==185 and current==values and h.true_digest(current)==F6,'immediate_C_E_modules')
 for pin in record_pins.values():require(h.read_file(pin['path'],MAXFILE,budget,pin['sha256'])[0]==pin,'immediate_new_canonical_stat_hash')
 require(h.read_file(EXPORT/'swdb-project'/a.report_relative,MAXFILE,budget,tp['sha256'])[0]==tp,'immediate_transfer_stat_hash')
 require(h.read_file(EXPORT/'swdb-project'/COUNT,MAXJSON,budget,COUNTSH)[0]==countpin,'immediate_count_pin')
 require(h.read_file(receipt_path,MAXJSON,budget,a.receipt_sha256)[0]==rpin,'immediate_receipt_recheck')
 require(h.released(budget)==leases and h.source_identity(budget)==r14,'immediate_lease_R14_recheck')
 require(git(PRIMARY,'rev-parse','HEAD')==git(PRIMARY,'rev-parse','origin/yanrujhou_main')==a.expected_primary and git(PRIMARY,'status','--porcelain','--untracked-files=all')=='?? swdb-project/records/.retention.lock' and git(CROOT,'rev-parse','HEAD')==C and not git(CROOT,'status','--porcelain') and git(EXPORT,'rev-parse','HEAD')==a.export_commit and not git(EXPORT,'status','--porcelain'),'immediate_refs_clean')
 require(stamp(lock.lstat())==stamp(s) and boot_read(READONLY,MAXJSON,HSH,29985)==helper_raw,'immediate_original_helper')
 require(h.native(budget)=={k:v for k,v in native.items() if k!=str(GNU)},'immediate_native')
 require(h.read_file(GNU,128*1024*1024,budget,GNUSH,False,0)[0]==gn,'immediate_GNU')
 os.chdir(EXPORT/'swdb-project')
 os.execve(GNU,argv,{**os.environ,**overrides})
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  data={'status':'refused_or_startup_failed','error_class':type(exc).__name__,'error_sha256':sha(str(exc).encode()),'scientific_admission':False}
  sys.stdout.write(json.dumps(data,separators=(',',':'))+'\n');raise SystemExit(2)

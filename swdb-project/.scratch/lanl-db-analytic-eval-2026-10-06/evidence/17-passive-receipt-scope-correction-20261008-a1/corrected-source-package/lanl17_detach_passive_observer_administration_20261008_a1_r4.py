"""SOURCE-ONLY preparation: one detached passive observer invocation, never a cleanup or SSH exemption."""
import argparse, datetime, hashlib, json, os, pathlib, re, shlex, socket, stat, subprocess, sys, time
P = pathlib.Path
UID = 114316761
BASE = P('/data1/yanruj')
PRIMARY = BASE/'ArchEvolve'
E = BASE/'ArchEvolve-lanl-generality-final-export-20261007-a1'
R = BASE/'ArchEvolve-lanl-generality-final-20261007-a1'
C = BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
OBSERVER_SHA = '50ad9bf511f90429a040bf5c25cc9a4bd15b12cb28419ad414d586269e5cdc99'
REVIEW = BASE/'lanl-account-pam-service-identification-20261008-a1/parent-review.json'
REVIEW_SHA = 'fcf92eee1c4b8bdfaed979dc8bedab004c6c4b7e2b1410c7614bc92d60349f4a'
NATIVE = {
 '/usr/bin/tmux': (1102608, '034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd'),
 '/usr/bin/python3.12': (8020928, 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
 '/usr/bin/timeout': (39880, '12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),
 '/usr/bin/git': (4019024, '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
 '/usr/bin/bash': (1446024, 'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),
}
ENV = {'PATH':'/usr/bin:/bin', 'LC_ALL':'C', 'PYTHONDONTWRITEBYTECODE':'1',
       'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1',
       'NUMEXPR_NUM_THREADS':'1', 'SHELL':'/usr/bin/bash', 'GIT_OPTIONAL_LOCKS':'0',
       'GIT_TERMINAL_PROMPT':'0'}

def need(value, reason):
 if not value: raise ValueError(reason)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def stamp(s):
 return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','nlink','uid','gid','size','mtime_ns','ctime_ns')}
def strict(raw):
 def pairs(rows):
  result={}
  for key,value in rows:
   need(key not in result,'duplicate_json_key'); result[key]=value
  return result
 def bad(value): raise ValueError('nonfinite_json')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def route(path):
 need(path.is_absolute() and path.resolve(strict=True)==path and
      not any(q.is_symlink() for q in (path,*path.parents)), 'canonical_nonsymlink_route')
 return path.lstat()
def file_bytes(path, cap, owner, digest=None, size=None, exact_mode=None):
 before=route(path)
 need(stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1
      and not before.st_mode&0o7022 and before.st_size<=cap,'exact_regular_owner_mode_bound')
 if size is not None: need(before.st_size==size,'exact_file_size')
 if exact_mode is not None: need(stat.S_IMODE(before.st_mode)==exact_mode,'exact_file_mode')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  need(stamp(os.fstat(fd))==stamp(before),'stable_file_open')
  pieces=[]; total=0
  while True:
   part=os.read(fd,min(1024*1024,cap-total+1))
   if not part: break
   total+=len(part); need(total<=cap,'bounded_returned_file'); pieces.append(part)
  raw=b''.join(pieces)
  need(len(raw)==before.st_size and stamp(os.fstat(fd))==stamp(before)
       and stamp(path.lstat())==stamp(before),'stable_returned_bytes')
 finally: os.close(fd)
 need(digest is None or sha(raw)==digest,'exact_returned_file_sha')
 return raw,{'path':str(path),'bytes':len(raw),'sha256':sha(raw),'stat':stamp(before)}
def private_dir(path):
 s=route(path); need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700,'owned_private_directory')
 return stamp(s)
def write_original(path, raw):
 need(len(raw)<=16384,'bounded_original_metadata')
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 try:
  with os.fdopen(fd,'wb') as out:
   out.write(raw); out.flush(); os.fsync(out.fileno())
 except: raise
 return file_bytes(path,16384,UID,sha(raw),len(raw),0o600)[1]
def emit(path,value):
 return write_original(path,(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode())
def process(pid):
 path=P('/proc')/str(pid)
 with (path/'stat').open('rb') as source: raw=source.read(16384+1)
 need(len(raw)<=16384,'proc_stat_bound')
 tail=raw[raw.rfind(b')')+2:].split(); start=int(tail[19]); parent=int(tail[1])
 with (path/'status').open('rb') as source: body=source.read(32768+1)
 need(len(body)<=32768,'proc_status_bound')
 fields={}
 for row in body.decode().splitlines():
  if ':' in row:
   key,value=row.split(':',1); need(key not in fields,'duplicate_proc_status'); fields[key]=value.strip()
 with (path/'stat').open('rb') as source: end=source.read(16384+1)
 need(len(end)<=16384,'proc_stat_bound')
 last=end[end.rfind(b')')+2:].split()
 need(int(last[19])==start and int(last[1])==parent and int(fields['PPid'])==parent,'stable_public_process_identity')
 return {'pid':pid,'start_ticks':start,'parent_pid':parent,'name':fields['Name'],
         'uids':[int(x) for x in fields['Uid'].split()]}
def ancestry():
 rows=[]; pid=os.getpid(); seen=set()
 for unused in range(64):
  need(pid not in seen,'ancestor_cycle'); seen.add(pid); item=process(pid); rows.append(item)
  if item['parent_pid']==0: return rows
  pid=item['parent_pid']
 raise ValueError('ancestor_depth_bound')
def bind_transport():
 rows=ancestry(); choices=[r for r in rows[1:] if r['name']=='sshd' and r['uids']==[UID]*4]
 need(bool(choices),'current_launch_account_sshd_ancestor_required')
 child=choices[0]; parent=process(child['parent_pid'])
 need(parent['name']=='sshd' and parent['uids']==[0]*4,'current_root_sshd_parent_required')
 need(process(child['pid'])==child and process(parent['pid'])==parent,'launch_transport_identity_closed')
 return {'account_transport':child,'root_parent_public_identity':parent,
         'launcher_ancestry':rows,'protected_transport_references_observed':False}
def gone(original):
 try: current=process(original['pid'])
 except (FileNotFoundError,ProcessLookupError): return True,'original_PID_absent'
 if current['start_ticks']!=original['start_ticks']: return True,'PID_reused_original_start_absent'
 return False,'original_transport_still_live'
def inputs(own,own_sha,observer):
 private_dir(BASE)
 need(own.is_relative_to(BASE) and observer.is_relative_to(BASE)
      and own!=observer and not any(p.is_relative_to(q) for p in (own,observer) for q in (PRIMARY,E,R,C)),'private_sources_outside_projects')
 own_raw,own_pin=file_bytes(own,256*1024,UID,own_sha)
 unused,observer_pin=file_bytes(observer,58755,UID,OBSERVER_SHA,58755)
 unused,review_pin=file_bytes(REVIEW,256*1024,UID,REVIEW_SHA,3258)
 native={}
 for path,(size,digest) in NATIVE.items():
  unused,native[path]=file_bytes(P(path),16*1024*1024,0,digest,size,0o755)
 return {'wrapper':own_pin,'observer':observer_pin,'service_review':review_pin,'native':native}
def launch(args):
 own=P(__file__).absolute(); pins=inputs(own,args.source_sha256,P(args.observer_source))
 transport=bind_transport(); folder=P(args.control_directory)
 need(folder.parent==BASE and folder.name.startswith('lanl17-detached-observer-') and len(folder.name)<=48
      and not os.path.lexists(folder),'fresh_direct_private_control_directory')
 os.mkdir(folder,0o700); private_dir(folder)
 config={'format':'swdb.lanl17-detached-passive-observer-administration-configuration.v1','sealed':False,
         'created_utc':now(),'expected_primary':args.expected_primary,
         'transport':transport,'inputs':pins,'control_directory':str(folder),
         'environment_overrides':ENV,'transport_wait_seconds':60,'observer_timeout_seconds':1200,
         'observer_KILL_after_seconds':60,'worker_wait_seconds':1275,'scientific_action':False}
 cp=emit(folder/'configuration.json',config)
 config_raw=b'set-option -g default-shell /usr/bin/bash\nset-option -g update-environment ""\nset-option -g exit-empty on\n'
 tp=write_original(folder/'tmux.conf',config_raw)
 socket_path=folder/'tmux.sock'; need(len(str(socket_path).encode())<100,'bounded_UNIX_socket_path')
 worker=['/usr/bin/python3.12','-B',str(own),'--worker','--control-directory',str(folder),
         '--configuration-sha256',cp['sha256'],'--source-sha256',args.source_sha256]
 command='exec '+shlex.join(worker)
 argv=['/usr/bin/tmux','-S',str(socket_path),'-f',str(folder/'tmux.conf'),'new-session','-d',
       '-s','passive-observer-administration','-c',str(BASE),command]
 config_again=file_bytes(folder/'configuration.json',16384,UID,cp['sha256'])[1]
 need(config_again==cp and inputs(own,args.source_sha256,P(args.observer_source))==pins,'launch_inputs_rechecked')
 out=os.open(folder/'launch.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 err=os.open(folder/'launch.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 start=now()
 try:
  with os.fdopen(out,'wb') as so,os.fdopen(err,'wb') as se:
   child=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=BASE,env=ENV,timeout=15)
   so.flush(); se.flush(); os.fsync(so.fileno()); os.fsync(se.fileno())
  receipt={'format':'swdb.lanl17-detached-passive-observer-launch.v1','sealed':False,'started_utc':start,'ended_utc':now(),
           'tmux_client_exit_code':child.returncode,'configuration':cp,'tmux_configuration':tp,'worker_argv':worker,
           'tmux_argv':argv,'transport_termination_or_observer_completion_claimed':False,'scientific_action':False}
  pin=emit(folder/'launch-status.json',receipt)
  print(json.dumps({'launch_status':pin,'tmux_client_exit_code':child.returncode},sort_keys=True))
  return child.returncode
 except BaseException as error:
  emit(folder/'launch-failure.json',{'sealed':False,'failure_utc':now(),'error_class':type(error).__name__,
       'error_sha256':sha(str(error).encode()),'observer_completion_claimed':False})
  raise

def worker(args):
 folder=P(args.control_directory); private_dir(BASE); private_dir(folder)
 need(folder.parent==BASE and folder.name.startswith('lanl17-detached-observer-'),'exact_worker_private_route')
 raw,configuration_pin=file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)
 cfg=strict(raw); own=P(__file__).absolute(); observer=P(cfg['inputs']['observer']['path'])
 need(cfg['control_directory']==str(folder) and cfg['sealed'] is False and cfg['format']=='swdb.lanl17-detached-passive-observer-administration-configuration.v1'
      and cfg['inputs']['wrapper']['sha256']==args.source_sha256 and cfg['environment_overrides']==ENV
      and cfg['transport_wait_seconds']==60 and cfg['observer_timeout_seconds']==1200
      and cfg['observer_KILL_after_seconds']==60 and cfg['worker_wait_seconds']==1275,'exact_worker_configuration')
 state={'format':'swdb.lanl17-detached-passive-observer-administration-status.v1','sealed':False,'started_utc':now(),
        'expected_primary':cfg['expected_primary'],'configuration':configuration_pin,
        'inputs':cfg['inputs'],'state':'preflight','scientific_admission':False,'capacity_admission':False,
        'SSH_role_exemption':False,'global_consumer_clearance_claimed':False}
 try:
  need(inputs(own,args.source_sha256,observer)==cfg['inputs'],'exact_detached_inputs')
  original=cfg['transport']['account_transport']
  need(not any(item['pid']==original['pid'] and item['start_ticks']==original['start_ticks'] for item in ancestry()),
       'worker_not_under_original_transport')
  start=time.monotonic(); observed=None
  while time.monotonic()-start<=60:
   ended,basis=gone(original)
   if ended: observed={'observed_utc':now(),'basis':basis,'bound_original':original}; break
   time.sleep(.1)
  need(observed is not None,'original_transport_did_not_disappear_within_60s')
  state['transport_original_termination']=observed
  need(inputs(own,args.source_sha256,observer)==cfg['inputs'] and
       file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)[0]==raw,'immediate_detached_source_and_request_recheck')
  argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','1200s','/usr/bin/python3.12','-B',str(observer),
        '--expected-primary',cfg['expected_primary'],'--source-sha256',OBSERVER_SHA,'--account-service-review',str(REVIEW),'--account-service-review-sha256',REVIEW_SHA]
  state['observer_argv']=argv; state['observer_started_utc']=now()
  so_fd=os.open(folder/'observer.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  se_fd=os.open(folder/'observer.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(so_fd,'wb') as so,os.fdopen(se_fd,'wb') as se:
   state['state']='observer_launch_started'
   state['owned_child_liveness_or_descendants_are_NOT_inferred_clear']=True
   child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=BASE,env=ENV,start_new_session=True)
   state['state']='observer_running'
   state['observer_pid']=child.pid
   try: code=child.wait(timeout=1275)
   except subprocess.TimeoutExpired:
    state['state']='GNU_supervision_not_returned_within_wrapper_wait'; state['observer_exit_code']=None
    state['owned_child_liveness_or_descendants_are_NOT_inferred_clear']=True; raise
   finally:
    so.flush(); se.flush(); os.fsync(so.fileno()); os.fsync(se.fileno())
  state['observer_exit_code']=code; state['state']='observer_completed' if code==0 else 'observer_refused_or_failed'
  state['observer_stdout']=file_bytes(folder/'observer.stdout',32*1024*1024,UID)[1]
  state['observer_stderr']=file_bytes(folder/'observer.stderr',256*1024,UID)[1]
  need(inputs(own,args.source_sha256,observer)==cfg['inputs'] and
       file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)[0]==raw,'post_observer_immutable_inputs')
  return code
 except BaseException as error:
  state['error_class']=type(error).__name__; state['error_sha256']=sha(str(error).encode())
  if state['state']=='preflight': state['state']='preflight_refused_no_observer_launch'
  elif state['state']=='observer_completed': state['state']='administrative_postflight_failed'
  return 1
 finally:
  state['ended_utc']=now(); emit(folder/'status.json',state)

def main():
 os.umask(0o077)
 need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact_Linux_account_host')
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--worker',action='store_true'); parser.add_argument('--source-sha256',required=True)
 parser.add_argument('--control-directory',required=True); parser.add_argument('--configuration-sha256')
 parser.add_argument('--expected-primary'); parser.add_argument('--observer-source')
 args=parser.parse_args(); need(re.fullmatch('[a-f0-9]{64}',args.source_sha256),'own_source_exact_SHA')
 if args.worker:
  need(re.fullmatch('[a-f0-9]{64}',args.configuration_sha256 or '') and args.expected_primary is None
       and args.observer_source is None,'worker_only_closed_arguments')
  return worker(args)
 need(args.configuration_sha256 is None and re.fullmatch('[a-f0-9]{40}',args.expected_primary or '')
      and args.observer_source is not None,'launcher_exact_parent_revision_and_source')
 return launch(args)
if __name__=='__main__':
 try: sys.exit(main())
 except BaseException as error:
  if isinstance(error,SystemExit): raise
  print(json.dumps({'sealed':False,'error_class':type(error).__name__,'error_sha256':sha(str(error).encode()),
                    'no_observer_success_plan_or_admission_inferred':True},sort_keys=True),file=sys.stderr)
  sys.exit(1)

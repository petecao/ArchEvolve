"""SOURCE-ONLY preparation: detached unchanged R4r2 storage administration, never an SSH exemption."""
import argparse, datetime, hashlib, json, os, pathlib, re, shlex, socket, stat, subprocess, sys, time
P = pathlib.Path
UID = 114316761
BASE = P('/data1/yanruj')
PRIMARY = BASE/'ArchEvolve'
E = BASE/'ArchEvolve-lanl-generality-final-export-20261007-a1'
R = BASE/'ArchEvolve-lanl-generality-final-20261007-a1'
C = BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
GUARD_SHA = '96e033426d492fab3be2a07757ab1e89665a7a67d0f06d3941f274b1214dd294'
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
def inputs(own,own_sha,guard):
 private_dir(BASE)
 need(own.is_relative_to(BASE) and guard.is_relative_to(BASE)
      and own!=guard and not any(p.is_relative_to(q) for p in (own,guard) for q in (PRIMARY,E,R,C)),'private_sources_outside_projects')
 own_raw,own_pin=file_bytes(own,256*1024,UID,own_sha)
 unused,guard_pin=file_bytes(guard,88521,UID,GUARD_SHA,88521)
 unused,review_pin=file_bytes(REVIEW,256*1024,UID,REVIEW_SHA,3258)
 native={}
 for path,(size,digest) in NATIVE.items():
  unused,native[path]=file_bytes(P(path),16*1024*1024,0,digest,size,0o755)
 return {'wrapper':own_pin,'guard':guard_pin,'service_review':review_pin,'native':native}
def plan_binding(plan, digest, selected, expected_primary):
 need(plan.is_absolute() and plan.parent==BASE and plan.name.startswith('lanl-consumed-source-parent-plan-'),
      'original_guard_direct_parent_plan_route')
 body,pin=file_bytes(plan,2*1024*1024,UID,digest,exact_mode=0o600)
 document=strict(body)
 need(type(document) is dict and document.get('format')=='swdb.consumed-detached-source-parent-plan.v1'
      and document.get('canonical_ensure_ascii') is True,'original_guard_parent_plan_format')
 encoded=json.dumps({k:v for k,v in document.items() if k!='identity_sha256'},sort_keys=True,
                    separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
 need(document.get('identity_sha256')==sha(encoded) and document.get('guard_source_sha256')==GUARD_SHA
      and document.get('expected_primary')==expected_primary and document.get('selected_rows')==selected,
      'original_guard_plan_source_order_revision_and_seal')
 return {'file':pin,'identity_sha256':document['identity_sha256'],'checked_at':document['checked_at'],
         'original_300s_plan_freshness_and_all_admission_checks_remain_in_unchanged_guard':True}
def fresh_guard_output(attempt):
 need(re.fullmatch('a[1-9][0-9]*',attempt),'original_guard_fresh_attempt_token')
 path=BASE/('lanl-consumed-detached-source-guard-20261007-'+attempt)
 need(not os.path.lexists(path),'original_guard_receipt_attempt_already_exists')
 return str(path)
def inspect_prior(args, own_sha):
 if not args.remove:
  need(args.inspection_directory is None and args.inspection_status_sha256 is None
       and args.inspection_stdout_sha256 is None,'inspection_does_not_reuse_prior_request')
  return None
 need(args.inspection_directory is not None and re.fullmatch('[a-f0-9]{64}',args.inspection_status_sha256 or '')
      and re.fullmatch('[a-f0-9]{64}',args.inspection_stdout_sha256 or ''),'parent_reviewed_successful_inspection_pins_required')
 folder=P(args.inspection_directory); private_dir(folder)
 need(folder.parent==BASE and folder.name.startswith('lanl17-detached-r4-'),'original_inspection_private_route')
 status_raw,status_pin=file_bytes(folder/'status.json',16384,UID,args.inspection_status_sha256)
 body,stdout_pin=file_bytes(folder/'guard.stdout',256*1024,UID,args.inspection_stdout_sha256)
 status=strict(status_raw); result=strict(body)
 need(status['format']=='swdb.lanl17-detached-exact-R4-administration-status.v1' and status['sealed'] is False
      and status['state']=='guard_completed' and status['guard_exit_code']==0 and status['remove_requested'] is False
      and status['expected_primary']==args.expected_primary and status['selected_rows']==args.select
      and status['inputs']['wrapper']['sha256']==own_sha and status['inputs']['guard']['sha256']==GUARD_SHA
      and status['inputs']['service_review']['sha256']==REVIEW_SHA
      and status['guard_stdout']==stdout_pin and 'error_class' not in status,'exact_default_inspection_custody')
 need(re.fullmatch('a[1-9][0-9]*',status['guard_attempt']) and status['guard_attempt']!=args.attempt,
      'distinct_default_and_removal_guard_attempts')
 receipt_path=BASE/('lanl-consumed-detached-source-guard-20261007-'+status['guard_attempt'])/'receipt.json'
 need(result['format']=='swdb.consumed-source-guard-return.v1' and result['path']==str(receipt_path)
      and result['admitted'] is True and result['removed_count']==0 and result['failure'] is None,
      'successful_original_default_return')
 private_dir(receipt_path.parent)
 receipt_raw,receipt_pin=file_bytes(receipt_path,256*1024,UID,result['sha256'],result['bytes'],0o600)
 receipt=strict(receipt_raw)
 encoded=json.dumps({k:v for k,v in receipt.items() if k!='identity_sha256'},sort_keys=True,
                    separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
 need(receipt['format']=='swdb.consumed-detached-source-guard.v1' and receipt['canonical_ensure_ascii'] is True
      and receipt['identity_sha256']==result['identity_sha256']==sha(encoded)
      and receipt['remove_requested'] is False and receipt['admitted'] is True and receipt['removed_rows']==[]
      and receipt['failure'] is None and receipt['selected_rows']==args.select
      and receipt['expected_primary']==args.expected_primary and receipt['guard_source_sha256']==GUARD_SHA
      and receipt['reviewed_plan_file_sha256']==status['reviewed_plan']['file']['sha256']
      and receipt['reviewed_plan_identity_sha256']==status['reviewed_plan']['identity_sha256']
      and receipt['scientific_admission'] is False and receipt['capacity_admission'] is False,
      'successful_original_default_receipt_and_plan_custody')
 return {'status':status_pin,'stdout':stdout_pin,'original_guard_receipt':receipt_pin,
         'default_reviewed_plan':status['reviewed_plan'],
         'same_ordered_rows_source_primary_required':True,
         'removal_requires_separately_fresh_parent_plan_in_unchanged_guard':True,
         'parent_review_is_inherited_explicit_invocation_authority':True}
def launch(args):
 own=P(__file__).absolute(); pins=inputs(own,args.source_sha256,P(args.guard_source))
 transport=bind_transport(); folder=P(args.control_directory)
 need(folder.parent==BASE and folder.name.startswith('lanl17-detached-r4-') and len(folder.name)<=48
      and not os.path.lexists(folder),'fresh_direct_private_control_directory')
 prior=inspect_prior(args,args.source_sha256)
 plan=plan_binding(P(args.plan),args.plan_sha256,args.select,args.expected_primary)
 output=fresh_guard_output(args.attempt)
 need(not any(p.is_relative_to(BASE/name) for p in (own,P(args.guard_source),P(args.plan),folder) for name in args.select),
      'administrative_sources_plan_and_control_outside_selection')
 os.mkdir(folder,0o700); private_dir(folder)
 config={'format':'swdb.lanl17-detached-exact-R4-administration-configuration.v1','sealed':False,
         'created_utc':now(),'expected_primary':args.expected_primary,'remove_requested':args.remove,
         'selected_rows':args.select,'guard_attempt':args.attempt,'reviewed_plan':plan,'guard_output_directory':output,
         'transport':transport,'inputs':pins,'prior_reviewed_inspection':prior,'control_directory':str(folder),
         'environment_overrides':ENV,'transport_wait_seconds':60,'guard_timeout_seconds':3660,
         'guard_KILL_after_seconds':60,'worker_wait_seconds':3735,'scientific_action':False}
 cp=emit(folder/'configuration.json',config)
 config_raw=b'set-option -g default-shell /usr/bin/bash\nset-option -g update-environment ""\nset-option -g exit-empty on\n'
 tp=write_original(folder/'tmux.conf',config_raw)
 socket_path=folder/'tmux.sock'; need(len(str(socket_path).encode())<100,'bounded_UNIX_socket_path')
 worker=['/usr/bin/python3.12','-B',str(own),'--worker','--control-directory',str(folder),
         '--configuration-sha256',cp['sha256'],'--source-sha256',args.source_sha256]
 command='exec '+shlex.join(worker)
 argv=['/usr/bin/tmux','-S',str(socket_path),'-f',str(folder/'tmux.conf'),'new-session','-d',
       '-s','exact-R4-administration','-c',str(BASE),command]
 config_again=file_bytes(folder/'configuration.json',16384,UID,cp['sha256'])[1]
 need(config_again==cp and inputs(own,args.source_sha256,P(args.guard_source))==pins
      and plan_binding(P(args.plan),args.plan_sha256,args.select,args.expected_primary)==plan
      and fresh_guard_output(args.attempt)==output,'launch_inputs_rechecked')
 out=os.open(folder/'launch.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 err=os.open(folder/'launch.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 start=now()
 try:
  with os.fdopen(out,'wb') as so,os.fdopen(err,'wb') as se:
   child=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=BASE,env=ENV,timeout=15)
   so.flush(); se.flush(); os.fsync(so.fileno()); os.fsync(se.fileno())
  receipt={'format':'swdb.lanl17-detached-exact-R4-launch.v1','sealed':False,'started_utc':start,'ended_utc':now(),
           'tmux_client_exit_code':child.returncode,'configuration':cp,'tmux_configuration':tp,'worker_argv':worker,
           'tmux_argv':argv,'transport_termination_or_guard_completion_claimed':False,'scientific_action':False}
  pin=emit(folder/'launch-status.json',receipt)
  print(json.dumps({'launch_status':pin,'tmux_client_exit_code':child.returncode},sort_keys=True))
  return child.returncode
 except BaseException as error:
  emit(folder/'launch-failure.json',{'sealed':False,'failure_utc':now(),'error_class':type(error).__name__,
       'error_sha256':sha(str(error).encode()),'guard_completion_claimed':False})
  raise

def worker(args):
 folder=P(args.control_directory); private_dir(BASE); private_dir(folder)
 need(folder.parent==BASE and folder.name.startswith('lanl17-detached-r4-'),'exact_worker_private_route')
 raw,configuration_pin=file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)
 cfg=strict(raw); own=P(__file__).absolute(); guard=P(cfg['inputs']['guard']['path'])
 need(cfg['control_directory']==str(folder) and cfg['sealed'] is False and cfg['format']=='swdb.lanl17-detached-exact-R4-administration-configuration.v1'
      and cfg['inputs']['wrapper']['sha256']==args.source_sha256 and cfg['environment_overrides']==ENV
      and cfg['transport_wait_seconds']==60 and cfg['guard_timeout_seconds']==3660
      and cfg['guard_KILL_after_seconds']==60 and cfg['worker_wait_seconds']==3735
      and type(cfg['remove_requested']) is bool and type(cfg['selected_rows']) is list
      and 1<=len(cfg['selected_rows'])<=18 and len(set(cfg['selected_rows']))==len(cfg['selected_rows'])
      and all(type(x) is str and re.fullmatch('ArchEvolve-lanl-[A-Za-z0-9-]{1,96}',x) for x in cfg['selected_rows'])
      and re.fullmatch('[a-f0-9]{40}',cfg['expected_primary'])
      and re.fullmatch('a[1-9][0-9]*',cfg['guard_attempt']),'exact_worker_configuration')
 state={'format':'swdb.lanl17-detached-exact-R4-administration-status.v1','sealed':False,'started_utc':now(),
        'expected_primary':cfg['expected_primary'],'remove_requested':cfg['remove_requested'],'configuration':configuration_pin,
        'selected_rows':cfg['selected_rows'],'guard_attempt':cfg['guard_attempt'],'reviewed_plan':cfg['reviewed_plan'],
        'inputs':cfg['inputs'],'state':'preflight','scientific_admission':False,'capacity_admission':False,
        'SSH_role_exemption':False,'global_consumer_clearance_claimed':False}
 try:
  need(inputs(own,args.source_sha256,guard)==cfg['inputs'],'exact_detached_inputs')
  plan=P(cfg['reviewed_plan']['file']['path']); plan_sha=cfg['reviewed_plan']['file']['sha256']
  need(plan_binding(plan,plan_sha,cfg['selected_rows'],cfg['expected_primary'])==cfg['reviewed_plan']
       and fresh_guard_output(cfg['guard_attempt'])==cfg['guard_output_directory'],'exact_detached_plan_and_attempt')
  need(not any(p.is_relative_to(BASE/name) for p in (own,guard,plan,folder) for name in cfg['selected_rows']),
       'detached_administration_outside_selection')
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
  if cfg['remove_requested']:
   original_prior=cfg['prior_reviewed_inspection']; need(type(original_prior) is dict,'original_default_inspection_required')
   closed_prior=argparse.Namespace(remove=True,expected_primary=cfg['expected_primary'],select=cfg['selected_rows'],attempt=cfg['guard_attempt'],
    inspection_directory=str(P(original_prior['status']['path']).parent),
    inspection_status_sha256=original_prior['status']['sha256'],inspection_stdout_sha256=original_prior['stdout']['sha256'])
   need(inspect_prior(closed_prior,args.source_sha256)==original_prior,'detached_original_default_custody_rechecked')
  else: need(cfg['prior_reviewed_inspection'] is None,'default_has_no_inherited_inspection_request')
  need(inputs(own,args.source_sha256,guard)==cfg['inputs'] and
       file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)[0]==raw
       and plan_binding(plan,plan_sha,cfg['selected_rows'],cfg['expected_primary'])==cfg['reviewed_plan']
       and fresh_guard_output(cfg['guard_attempt'])==cfg['guard_output_directory'],'immediate_detached_source_and_request_recheck')
  argv=['/usr/bin/timeout','--signal=TERM','--kill-after=60s','3660s','/usr/bin/python3.12','-B',str(guard),
        '--expected-primary',cfg['expected_primary'],'--plan',str(plan),'--plan-sha256',plan_sha,
        '--attempt',cfg['guard_attempt']]
  for name in cfg['selected_rows']: argv.extend(['--select',name])
  if cfg['remove_requested']: argv.append('--remove')
  state['guard_argv']=argv; state['guard_started_utc']=now()
  so_fd=os.open(folder/'guard.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  se_fd=os.open(folder/'guard.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(so_fd,'wb') as so,os.fdopen(se_fd,'wb') as se:
   state['state']='guard_launch_started'
   state['owned_child_liveness_or_descendants_are_NOT_inferred_clear']=True
   child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=so,stderr=se,cwd=BASE,env=ENV,start_new_session=True)
   state['state']='guard_running'
   state['guard_pid']=child.pid
   try: code=child.wait(timeout=3735)
   except subprocess.TimeoutExpired:
    state['state']='GNU_supervision_not_returned_within_wrapper_wait'; state['guard_exit_code']=None
    state['owned_child_liveness_or_descendants_are_NOT_inferred_clear']=True; raise
   finally:
    so.flush(); se.flush(); os.fsync(so.fileno()); os.fsync(se.fileno())
  state['guard_exit_code']=code; state['state']='guard_completed' if code==0 else 'guard_refused_or_failed'
  state['guard_stdout']=file_bytes(folder/'guard.stdout',256*1024,UID)[1]
  state['guard_stderr']=file_bytes(folder/'guard.stderr',256*1024,UID)[1]
  need(inputs(own,args.source_sha256,guard)==cfg['inputs'] and
       file_bytes(folder/'configuration.json',16384,UID,args.configuration_sha256)[0]==raw
       and plan_binding(plan,plan_sha,cfg['selected_rows'],cfg['expected_primary'])==cfg['reviewed_plan'],'post_guard_immutable_inputs')
  return code
 except BaseException as error:
  state['error_class']=type(error).__name__; state['error_sha256']=sha(str(error).encode())
  if state['state']=='preflight': state['state']='preflight_refused_no_guard_launch'
  elif state['state']=='guard_completed': state['state']='administrative_postflight_failed'
  return 1
 finally:
  state['ended_utc']=now(); emit(folder/'status.json',state)

def main():
 os.umask(0o077)
 need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact_Linux_account_host')
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--worker',action='store_true'); parser.add_argument('--source-sha256',required=True)
 parser.add_argument('--control-directory',required=True); parser.add_argument('--configuration-sha256')
 parser.add_argument('--expected-primary'); parser.add_argument('--guard-source'); parser.add_argument('--remove',action='store_true')
 parser.add_argument('--select',action='append'); parser.add_argument('--plan'); parser.add_argument('--plan-sha256'); parser.add_argument('--attempt')
 parser.add_argument('--inspection-directory'); parser.add_argument('--inspection-status-sha256'); parser.add_argument('--inspection-stdout-sha256')
 args=parser.parse_args(); need(re.fullmatch('[a-f0-9]{64}',args.source_sha256),'own_source_exact_SHA')
 if args.worker:
  need(re.fullmatch('[a-f0-9]{64}',args.configuration_sha256 or '') and args.expected_primary is None
       and args.guard_source is None and args.remove is False and args.inspection_directory is None
       and args.inspection_status_sha256 is None and args.inspection_stdout_sha256 is None
       and args.select is None and args.plan is None and args.plan_sha256 is None and args.attempt is None,'worker_only_closed_arguments')
  return worker(args)
 need(args.configuration_sha256 is None and re.fullmatch('[a-f0-9]{40}',args.expected_primary or '')
      and args.guard_source is not None and re.fullmatch('[a-f0-9]{64}',args.plan_sha256 or '')
      and args.plan is not None and re.fullmatch('a[1-9][0-9]*',args.attempt or '')
      and type(args.select) is list and 1<=len(args.select)<=18 and len(set(args.select))==len(args.select)
      and all(re.fullmatch('ArchEvolve-lanl-[A-Za-z0-9-]{1,96}',x) for x in args.select),
      'launcher_exact_parent_revision_source_ordered_rows_and_fresh_plan')
 return launch(args)
if __name__=='__main__':
 try: sys.exit(main())
 except BaseException as error:
  if isinstance(error,SystemExit): raise
  print(json.dumps({'sealed':False,'error_class':type(error).__name__,'error_sha256':sha(str(error).encode()),
                    'no_guard_or_cleanup_success_inferred':True},sort_keys=True),file=sys.stderr)
  sys.exit(1)

# Source-only sparse derivative: fixed eight originals and original True guard receipt; no guard execution.
import argparse,pathlib,os,stat,json,hashlib,base64,datetime,re
P=pathlib.Path;UID=114316761;BASE=P('/data1/yanruj')
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def read(p,cap):
 assert p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=cap
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  b=f.read(cap+1);assert len(b)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())
 return b,{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'stat':stamp(s)}
PACKET_CAP=64*1024*1024
WRAPPER_SHA='e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec'
GUARD_SHA='d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
CONTROL_PREFIX='lanl17-detached-sparse-'
TERMINAL_STATES=('guard_completed','guard_refused_or_failed','preflight_refused_no_guard_launch','administrative_postflight_failed','guard_launch_started','guard_running','GNU_supervision_not_returned_within_wrapper_wait')
FILES=[('status.json',16384),('configuration.json',16384),('tmux.conf',16384),('launch-status.json',16384),('launch.stdout',16384),('launch.stderr',16384),('guard.stdout',256*1024),('guard.stderr',256*1024)]
RECEIPT_CAP=256*1024
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:assert k not in d;d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def parsed_original(item):
 if item is None:return None,'absent'
 try:
  value=strict(item[0])
 except (ValueError,AssertionError,UnicodeError,RecursionError) as error:return None,'unparseable_'+type(error).__name__
 return (value,'object') if type(value) is dict else (None,'not_an_object')
def wrapper_custody(retained,folder):
 status,sp=parsed_original(retained.get('status.json'));config,cp=parsed_original(retained.get('configuration.json'))
 result={'status_json_observation':sp,'configuration_json_observation':cp,'selected_source_pins_bound':False,
         'actual_guard_attempt':None,'derived_guard_receipt_path':None,'reported_state':None,
         'possible_guard_launch_recorded':False,'terminal_guard_exit_recorded':False,
         'configuration_pin_matches_status':None,'wrapper_stdout_pin_matches_original':None}
 if status is not None:
  result['reported_state']=status.get('state') if status.get('state') in TERMINAL_STATES else 'unrecognized_or_missing'
  result['possible_guard_launch_recorded']=any(k in status for k in ('guard_started_utc','guard_argv','guard_pid'))
  result['terminal_guard_exit_recorded']=type(status.get('guard_exit_code')) is int
  inputs=status.get('inputs')
  if status.get('format')=='swdb.lanl17-detached-library-sparse-administration-status.v1' and status.get('sealed') is False and type(inputs) is dict:
   wrapper=inputs.get('wrapper');guard=inputs.get('guard')
   if type(wrapper) is dict and type(guard) is dict and all(k in wrapper and k in guard for k in ('sha256','bytes')):
    assert wrapper['sha256']==WRAPPER_SHA and wrapper['bytes']==24114 and guard['sha256']==GUARD_SHA and guard['bytes']==180887
    result['selected_source_pins_bound']=True
    attempt=status.get('guard_attempt')
    if type(attempt) is str and re.fullmatch('a[1-9][0-9]*',attempt):
     result['actual_guard_attempt']=attempt
     result['derived_guard_receipt_path']='/data1/yanruj/lanl-library-preserving-sparse-retirement-20261008-'+attempt+'/receipt.json'
   if 'scientific_admission' in status:assert status['scientific_admission'] is False
   if 'capacity_admission' in status:assert status['capacity_admission'] is False
  if 'configuration' in status and 'configuration.json' in retained:result['configuration_pin_matches_status']=status['configuration']==retained['configuration.json'][1]
  if 'guard_stdout' in status and 'guard.stdout' in retained:result['wrapper_stdout_pin_matches_original']=status['guard_stdout']==retained['guard.stdout'][1]
 if config is not None and config.get('format')=='swdb.lanl17-detached-library-sparse-administration-configuration.v1':
  assert config.get('sealed') is False and config.get('control_directory')==folder
  if result['selected_source_pins_bound']:
   assert config.get('inputs')==status['inputs']
   for key in ('guard_attempt','expected_primary','selected_rows','retire_requested','reviewed_plan'):
    if key in status and key in config:assert status[key]==config[key]
   if result['actual_guard_attempt'] is not None:assert config.get('guard_output_directory')==str(P(result['derived_guard_receipt_path']).parent)
 return result
def receipt_custody(retained,wrapper,receipt_item,availability):
 receipt,rp=parsed_original(receipt_item);returned,op=parsed_original(retained.get('guard.stdout'))
 result={'receipt_availability':availability,'receipt_json_observation':rp,'guard_stdout_json_observation':op,
         'receipt_seal_policy':'explicit canonical_ensure_ascii=True; whole original object minus identity_sha256',
         'receipt_seal_verification':'unavailable','stdout_receipt_byte_identity_binding':'unavailable',
         'receipt_publication_failure_recorded':False,'no_success_liveness_capacity_or_scientific_admission_inferred':True}
 identity=None
 if receipt is not None:
  if receipt.get('format')=='swdb.library-preserving-sparse-retirement-guard.v1' and receipt.get('canonical_ensure_ascii') is True and type(receipt.get('identity_sha256')) is str:
   body=json.dumps({k:v for k,v in receipt.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
   identity=hashlib.sha256(body).hexdigest()
   result['receipt_seal_verification']='verified_original_True_policy' if receipt['identity_sha256']==identity else 'invalid_original_seal'
  else:result['receipt_seal_verification']='missing_or_different_original_policy_or_format'
 if returned is not None and returned.get('format')=='swdb.library-preserving-sparse-retirement-return.v1':
  result['receipt_publication_failure_recorded']=returned.get('receipt_publication_failed') is True
  keys=('path','bytes','sha256','identity_sha256')
  if all(k in returned for k in keys):
   if returned['path']!=wrapper['derived_guard_receipt_path']:result['stdout_receipt_byte_identity_binding']='different_original_return_path'
   elif receipt_item is None:result['stdout_receipt_byte_identity_binding']='original_return_claims_receipt_but_receipt_absent'
   elif (type(returned['bytes']) is int and returned['bytes']==receipt_item[1]['bytes'] and returned['sha256']==receipt_item[1]['sha256']
         and result['receipt_seal_verification']=='verified_original_True_policy' and returned['identity_sha256']==identity):
    result['stdout_receipt_byte_identity_binding']='verified_exact_original_bytes_and_identity'
   else:result['stdout_receipt_byte_identity_binding']='different_or_incomplete_original_byte_or_identity_pin'
  elif any(k in returned for k in keys):result['stdout_receipt_byte_identity_binding']='incomplete_original_return_pin'
  elif result['receipt_publication_failure_recorded']:result['stdout_receipt_byte_identity_binding']='original_publication_failure_return_without_receipt_pin'
 return result
a=argparse.ArgumentParser();a.add_argument('--control-directory',required=True);args=a.parse_args()
assert os.getuid()==os.geteuid()==UID
folder=P(args.control_directory);assert folder.parent==BASE and folder.name.startswith(CONTROL_PREFIX) and len(folder.name)<=48
assert folder.resolve(strict=True)==folder and not any(q.is_symlink() for q in (folder,*folder.parents))
directory_identities={}
for directory in (BASE,folder):
 s=directory.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
 directory_identities[str(directory)]=(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)
originals=[];retained={};missing=[];read_total=0
for name,cap in FILES:
 p=folder/name
 if not os.path.lexists(p):missing.append(name);continue
 b,fp=read(p,cap);read_total+=len(b);assert read_total<=PACKET_CAP
 retained[name]=(b,fp);originals.append({**fp,'original_bytes_base64':base64.b64encode(b).decode('ascii')})
wrapper=wrapper_custody(retained,str(folder));receipt_item=None;receipt_directory_identity=None
receipt_path=P(wrapper['derived_guard_receipt_path']) if wrapper['derived_guard_receipt_path'] is not None else None
availability='not_addressed_without_source_bound_original_status_attempt';receipt_original=None
if receipt_path is not None:
 availability='absent'
 if os.path.lexists(receipt_path.parent):
  directory=receipt_path.parent;assert directory.resolve(strict=True)==directory and not any(q.is_symlink() for q in (directory,*directory.parents))
  s=directory.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
  receipt_directory_identity=(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)
  if os.path.lexists(receipt_path):
   receipt_item=read(receipt_path,RECEIPT_CAP);read_total+=len(receipt_item[0]);assert read_total<=PACKET_CAP
   receipt_original={**receipt_item[1],'original_bytes_base64':base64.b64encode(receipt_item[0]).decode('ascii')};availability='present'
receipt_observation=receipt_custody(retained,wrapper,receipt_item,availability)
for name,(b,fp) in retained.items():
 p=folder/name;assert not any(q.is_symlink() for q in (p,*p.parents)) and stamp(p.lstat())==fp['stat']
for name in missing:assert not os.path.lexists(folder/name)
if 'status.json' in retained:
 assert read(folder/'status.json',16384)==retained['status.json'];read_total+=len(retained['status.json'][0])
if receipt_path is not None:
 if receipt_directory_identity is None:assert not os.path.lexists(receipt_path.parent)
 else:
  s=receipt_path.parent.lstat();assert not any(q.is_symlink() for q in (receipt_path.parent,*receipt_path.parent.parents)) and (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)==receipt_directory_identity
  if receipt_item is None:assert not os.path.lexists(receipt_path)
  else:assert read(receipt_path,RECEIPT_CAP)==receipt_item;read_total+=len(receipt_item[0])
assert read_total<=PACKET_CAP
for route,identity in directory_identities.items():
 directory=P(route);s=directory.lstat();assert not any(q.is_symlink() for q in (directory,*directory.parents)) and (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)==identity
packet={'format':'swdb.lanl17-detached-library-sparse-original-custody-transfer.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'control_directory':str(folder),'originals':originals,'missing_original_names':missing,'original_bytes_read':read_total,'packet_byte_limit':PACKET_CAP,
        'wrapper_custody_observation':wrapper,'guard_receipt_original':receipt_original,'guard_receipt_availability':availability,'guard_receipt_custody_observation':receipt_observation,
        'state_label_is_not_launch_or_liveness_proof':True,'selected_wrapper_source_sha256':WRAPPER_SHA,'selected_guard_source_sha256':GUARD_SHA,
        'all_streams_scope':'original_bounded_administrative_custody_not_numerical_raw_output','no_success_or_admission_inferred':True}
encoded=json.dumps(packet,sort_keys=True).encode();assert len(encoded)+1<=PACKET_CAP
print(encoded.decode())

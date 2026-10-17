# Source-only derivative: exact R4 administrative originals; no guard execution or semantic admission.
import argparse,pathlib,os,stat,json,hashlib,base64,re
P=pathlib.Path
PACKET_CAP=64*1024*1024
WRAPPER_SHA='52f379d99721c51677ba44a1e9f3d55138527e26be1073c6267fbe09c8a93853'
GUARD_SHA='a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb'
CONTROL_ROUTES=('/data1/yanruj/lanl17-detached-r4-inspection-a1','/data1/yanruj/lanl17-detached-r4-removal-a1')
TERMINAL_STATES=('guard_completed','guard_refused_or_failed','preflight_refused_no_guard_launch','administrative_postflight_failed','guard_launch_started','guard_running','GNU_supervision_not_returned_within_wrapper_wait')
FILES=[('status.json',16384),('configuration.json',16384),('tmux.conf',16384),('launch-status.json',16384),('launch.stdout',16384),('launch.stderr',16384),('guard.stdout',256*1024),('guard.stderr',256*1024)]
RECEIPT_CAP=256*1024
def sha(b):return hashlib.sha256(b).hexdigest()
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:assert k not in d;d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def local_read(p,cap):
 assert p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=cap
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  b=f.read(cap+1);assert len(b)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())
 return b,stamp(s)
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
  if status.get('format')=='swdb.lanl17-detached-exact-R4-administration-status.v1' and status.get('sealed') is False and type(inputs) is dict:
   wrapper=inputs.get('wrapper');guard=inputs.get('guard')
   if type(wrapper) is dict and type(guard) is dict and all(k in wrapper and k in guard for k in ('sha256','bytes')):
    assert wrapper['sha256']==WRAPPER_SHA and wrapper['bytes']==24000 and guard['sha256']==GUARD_SHA and guard['bytes']==88872
    result['selected_source_pins_bound']=True
    attempt=status.get('guard_attempt')
    if type(attempt) is str and re.fullmatch('a[1-9][0-9]*',attempt):
     result['actual_guard_attempt']=attempt
     result['derived_guard_receipt_path']='/data1/yanruj/lanl-consumed-detached-source-guard-20261007-'+attempt+'/receipt.json'
   if 'scientific_admission' in status:assert status['scientific_admission'] is False
   if 'capacity_admission' in status:assert status['capacity_admission'] is False
  if 'configuration' in status and 'configuration.json' in retained:result['configuration_pin_matches_status']=status['configuration']==retained['configuration.json'][1]
  if 'guard_stdout' in status and 'guard.stdout' in retained:result['wrapper_stdout_pin_matches_original']=status['guard_stdout']==retained['guard.stdout'][1]
 if config is not None and config.get('format')=='swdb.lanl17-detached-exact-R4-administration-configuration.v1':
  assert config.get('sealed') is False and config.get('control_directory')==folder
  if result['selected_source_pins_bound']:
   assert config.get('inputs')==status['inputs']
   for key in ('guard_attempt','expected_primary','selected_rows','remove_requested','reviewed_plan'):
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
  if receipt.get('format')=='swdb.consumed-detached-source-guard.v1' and receipt.get('canonical_ensure_ascii') is True and type(receipt.get('identity_sha256')) is str:
   body=json.dumps({k:v for k,v in receipt.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
   identity=hashlib.sha256(body).hexdigest()
   result['receipt_seal_verification']='verified_original_True_policy' if receipt['identity_sha256']==identity else 'invalid_original_seal'
  else:result['receipt_seal_verification']='missing_or_different_original_policy_or_format'
 if returned is not None and returned.get('format')=='swdb.consumed-source-guard-return.v1':
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
a=argparse.ArgumentParser();a.add_argument('--packet',required=True);a.add_argument('--output-directory',required=True);args=a.parse_args();os.umask(0o077)
p=P(args.packet);assert p.parent==P('/private/tmp')
b,packet_stat=local_read(p,PACKET_CAP);d=strict(b)
assert d['format']=='swdb.detached-R4-administration-original-custody-transfer.v1' and d['sealed'] is False and d['no_success_or_admission_inferred'] is True and d['state_label_is_not_launch_or_liveness_proof'] is True and d['packet_byte_limit']==PACKET_CAP
assert d['selected_wrapper_source_sha256']==WRAPPER_SHA and d['selected_guard_source_sha256']==GUARD_SHA
remote=P(d['control_directory']);assert str(remote) in CONTROL_ROUTES
label='inspection' if str(remote)==CONTROL_ROUTES[0] else 'removal'
dest=P(args.output_directory);assert dest==P('/private/tmp')/('lanl17-detached-r4-'+label+'-originals-20261008-a1') and not os.path.lexists(dest)
allowed=dict(FILES);seen=set();decoded=[];total=0
for pin in d['originals']:
 rp=P(pin['path']);name=rp.name;assert rp.parent==remote and name in allowed and name not in seen;seen.add(name)
 raw=base64.b64decode(pin['original_bytes_base64'],validate=True);total+=len(raw);assert total<=PACKET_CAP
 assert len(raw)==pin['bytes']<=allowed[name] and sha(raw)==pin['sha256'] and pin['stat']['uid']==114316761 and pin['stat']['nlink']==1 and stat.S_ISREG(pin['stat']['mode']) and stat.S_IMODE(pin['stat']['mode'])==0o600 and pin['stat']['size']==len(raw)
 decoded.append((name,raw,pin))
byname={name:(raw,{k:v for k,v in pin.items() if k!='original_bytes_base64'}) for name,raw,pin in decoded}
missing=[name for name,cap in FILES if name not in seen];assert missing==d['missing_original_names']
wrapper=wrapper_custody(byname,str(remote));assert wrapper==d['wrapper_custody_observation']
receipt_pin=d['guard_receipt_original'];receipt_item=None;availability=d['guard_receipt_availability']
if wrapper['derived_guard_receipt_path'] is None:
 assert availability=='not_addressed_without_source_bound_original_status_attempt' and receipt_pin is None
elif availability=='absent':assert receipt_pin is None
else:
 assert availability=='present' and type(receipt_pin) is dict and receipt_pin['path']==wrapper['derived_guard_receipt_path']
 raw=base64.b64decode(receipt_pin['original_bytes_base64'],validate=True);total+=len(raw);assert total<=PACKET_CAP
 assert len(raw)==receipt_pin['bytes']<=RECEIPT_CAP and sha(raw)==receipt_pin['sha256'] and receipt_pin['stat']['uid']==114316761 and receipt_pin['stat']['nlink']==1 and stat.S_ISREG(receipt_pin['stat']['mode']) and stat.S_IMODE(receipt_pin['stat']['mode'])==0o600 and receipt_pin['stat']['size']==len(raw)
 receipt_item=(raw,{k:v for k,v in receipt_pin.items() if k!='original_bytes_base64'})
 assert 'guard-receipt/receipt.json' not in allowed;allowed['guard-receipt/receipt.json']=RECEIPT_CAP;decoded.append(('guard-receipt/receipt.json',raw,receipt_pin))
assert receipt_custody(byname,wrapper,receipt_item,availability)==d['guard_receipt_custody_observation']
assert local_read(p,PACKET_CAP)==(b,packet_stat)
os.mkdir(dest,0o700);ds=dest.lstat();assert dest.resolve(strict=True)==dest and not any(q.is_symlink() for q in (dest,*dest.parents)) and stat.S_ISDIR(ds.st_mode) and ds.st_uid==os.getuid() and stat.S_IMODE(ds.st_mode)==0o700
directory_identity=(ds.st_dev,ds.st_ino,ds.st_uid,ds.st_gid,ds.st_mode);receipt_subdirectory_identity=None
if receipt_item is not None:
 os.mkdir(dest/'guard-receipt',0o700);rs=(dest/'guard-receipt').lstat();assert stat.S_ISDIR(rs.st_mode) and rs.st_uid==os.getuid() and stat.S_IMODE(rs.st_mode)==0o700
 receipt_subdirectory_identity=(rs.st_dev,rs.st_ino,rs.st_uid,rs.st_gid,rs.st_mode)
result=[]
for name,raw,pin in decoded:
 assert (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))(dest.lstat())==directory_identity
 if '/' in name:assert (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))((dest/'guard-receipt').lstat())==receipt_subdirectory_identity and not (dest/'guard-receipt').is_symlink()
 out=dest/name;fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 got,local_stat=local_read(out,allowed[name]);assert got==raw
 result.append({'local_path':str(out),'remote_original_path':pin['path'],'bytes':len(raw),'sha256':sha(raw),'remote_original_stat':pin['stat'],'local_original_stat':local_stat})
receipt={'format':'swdb.detached-R4-original-local-byte-custody.v1','sealed':False,'source_packet':{'path':str(p),'bytes':len(b),'sha256':sha(b),'stat':packet_stat},
         'originals':result,'missing_original_names':missing,'wrapper_custody_observation':wrapper,'guard_receipt_availability':availability,
         'guard_receipt_custody_observation':d['guard_receipt_custody_observation'],'original_stream_and_seal_policies_unchanged':True,'semantic_or_success_or_capacity_admission':False}
receipt_raw=(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode();assert len(receipt_raw)<=65536
fd=os.open(dest/'local-custody.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
with os.fdopen(fd,'wb') as f:f.write(receipt_raw);f.flush();os.fsync(f.fileno())
assert local_read(dest/'local-custody.json',65536)[0]==receipt_raw and local_read(p,PACKET_CAP)==(b,packet_stat)
assert (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))(dest.lstat())==directory_identity
if receipt_subdirectory_identity is not None:assert not (dest/'guard-receipt').is_symlink() and (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))((dest/'guard-receipt').lstat())==receipt_subdirectory_identity
print(json.dumps({'output_directory':str(dest),'originals':[{'relative_name':str(P(x['local_path']).relative_to(dest)),'bytes':x['bytes'],'sha256':x['sha256']} for x in result],
                  'missing_original_names':missing,'guard_receipt_availability':availability,'raw_original_bytes_preserved':True,'no_admission_inferred':True},sort_keys=True))

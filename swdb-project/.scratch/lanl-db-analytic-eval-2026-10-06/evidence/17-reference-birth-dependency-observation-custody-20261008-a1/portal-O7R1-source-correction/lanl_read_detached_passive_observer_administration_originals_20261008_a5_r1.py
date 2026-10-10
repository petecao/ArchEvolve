import argparse,pathlib,os,stat,json,hashlib,base64,datetime
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
WRAPPER_SHA='ee885d56e99c591b2f1298153a97f43ab78687bdc7fecbc2e830349abae26669'
OBSERVER_SHA='83e3d4dbac5d2215d591e09c8dd01aa441c1b6b0151ff18ee8a494ed9826c524'
TERMINAL_STATES=('observer_completed','observer_refused_or_failed','preflight_refused_no_observer_launch','administrative_postflight_failed','observer_launch_started','observer_running','GNU_supervision_not_returned_within_wrapper_wait')
FILES=[('status.json',16384),('configuration.json',16384),('tmux.conf',16384),('launch-status.json',16384),('launch.stdout',16384),('launch.stderr',16384),('observer.stdout',32*1024*1024),('observer.stderr',256*1024)]
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:assert k not in d;d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
a=argparse.ArgumentParser();a.add_argument('--control-directory',required=True);args=a.parse_args()
assert os.getuid()==os.geteuid()==UID
folder=P(args.control_directory);assert folder==BASE/'lanl17-detached-observer-a5' and folder.resolve(strict=True)==folder and not any(q.is_symlink() for q in (folder,*folder.parents))
for directory in (BASE,folder):
 s=directory.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
folder_identity=(s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)
status,pin=read(folder/'status.json',16384);d=strict(status)
assert d['format']=='swdb.lanl17-detached-passive-observer-administration-status.v1' and d['sealed'] is False and d['state'] in TERMINAL_STATES and type(d['ended_utc']) is str
assert d['inputs']['wrapper']['sha256']==WRAPPER_SHA and d['inputs']['wrapper']['bytes']==16091 and d['inputs']['observer']['sha256']==OBSERVER_SHA and d['inputs']['observer']['bytes']==87833
assert d['scientific_admission'] is False and d['capacity_admission'] is False
if d['state'] in ('observer_completed','observer_refused_or_failed','administrative_postflight_failed'):assert type(d.get('observer_exit_code')) is int
originals=[];retained={};missing=[];read_total=len(status)
for name,cap in FILES:
 p=folder/name
 if not os.path.lexists(p):
  assert name.startswith('observer.') and d['state']=='preflight_refused_no_observer_launch';missing.append(name);continue
 b,fp=read(p,cap);read_total+=len(b);assert read_total<=PACKET_CAP
 retained[name]=(b,fp);originals.append({**fp,'original_bytes_base64':base64.b64encode(b).decode('ascii')})
assert retained['status.json']==(status,pin)
config,config_pin=retained['configuration.json'];cfg=strict(config)
assert config_pin==d['configuration'] and cfg['format']=='swdb.lanl17-detached-passive-observer-administration-configuration.v1' and cfg['sealed'] is False and cfg['control_directory']==str(folder) and cfg['inputs']==d['inputs']
assert read(folder/'status.json',16384)==(status,pin);read_total+=len(status);assert read_total<=PACKET_CAP
for name,(b,fp) in retained.items():
 p=folder/name;assert not any(q.is_symlink() for q in (p,*p.parents)) and stamp(p.lstat())==fp['stat']
s=folder.lstat();assert (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)==folder_identity
packet={'format':'swdb.detached-passive-observer-administration-original-custody-transfer.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'control_directory':str(folder),'originals':originals,'missing_original_stream_names':missing,'original_bytes_read':read_total,'packet_byte_limit':PACKET_CAP,'state_label_is_not_launch_or_liveness_proof':True,'possible_observer_launch_recorded':any(k in d for k in ('observer_started_utc','observer_argv','observer_pid')),'terminal_observer_exit_recorded':type(d.get('observer_exit_code')) is int,'selected_wrapper_source_sha256':WRAPPER_SHA,'selected_observer_source_sha256':OBSERVER_SHA,'observer_stdout_scope':'original_bounded_compact_passive_administrative_metadata_not_numerical_raw_output','no_success_or_admission_inferred':True}
encoded=json.dumps(packet,sort_keys=True).encode();assert len(encoded)+1<=PACKET_CAP
print(encoded.decode())

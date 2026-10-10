import argparse,pathlib,os,stat,json,hashlib,base64
P=pathlib.Path
PACKET_CAP=64*1024*1024
WRAPPER_SHA='6453bfc0d74259d497569eb018e91ff7972b8812d39a3eacc6fe51324cf9709f'
OBSERVER_SHA='50ad9bf511f90429a040bf5c25cc9a4bd15b12cb28419ad414d586269e5cdc99'
TERMINAL_STATES=('observer_completed','observer_refused_or_failed','preflight_refused_no_observer_launch','administrative_postflight_failed','observer_launch_started','observer_running','GNU_supervision_not_returned_within_wrapper_wait')
FILES=[('status.json',16384),('configuration.json',16384),('tmux.conf',16384),('launch-status.json',16384),('launch.stdout',16384),('launch.stderr',16384),('observer.stdout',32*1024*1024),('observer.stderr',256*1024)]
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
a=argparse.ArgumentParser();a.add_argument('--packet',required=True);a.add_argument('--output-directory',required=True);args=a.parse_args();os.umask(0o077)
p=P(args.packet);assert p.parent==P('/private/tmp')
b,packet_stat=local_read(p,PACKET_CAP);d=strict(b)
assert d['format']=='swdb.detached-passive-observer-administration-original-custody-transfer.v1' and d['sealed'] is False and d['no_success_or_admission_inferred'] is True and d['state_label_is_not_launch_or_liveness_proof'] is True and d['packet_byte_limit']==PACKET_CAP
assert d['selected_wrapper_source_sha256']==WRAPPER_SHA and d['selected_observer_source_sha256']==OBSERVER_SHA
remote=P(d['control_directory']);assert remote==P('/data1/yanruj/lanl17-detached-observer-a3')
dest=P(args.output_directory);assert dest.parent==P('/private/tmp') and dest.name=='lanl17-detached-passive-observer-originals-20261008-a3' and not os.path.lexists(dest)
allowed=dict(FILES);seen=set();decoded=[];total=0
for pin in d['originals']:
 rp=P(pin['path']);name=rp.name;assert rp.parent==remote and name in allowed and name not in seen;seen.add(name)
 raw=base64.b64decode(pin['original_bytes_base64'],validate=True);total+=len(raw);assert total<=PACKET_CAP
 assert len(raw)==pin['bytes']<=allowed[name] and sha(raw)==pin['sha256'] and pin['stat']['uid']==114316761 and pin['stat']['nlink']==1 and stat.S_ISREG(pin['stat']['mode']) and stat.S_IMODE(pin['stat']['mode'])==0o600 and pin['stat']['size']==len(raw)
 decoded.append((name,raw,pin))
assert {'status.json','configuration.json','tmux.conf','launch-status.json','launch.stdout','launch.stderr'}<=seen
byname={name:(raw,pin) for name,raw,pin in decoded};status,status_pin=byname['status.json'];s=strict(status)
assert s['format']=='swdb.lanl17-detached-passive-observer-administration-status.v1' and s['sealed'] is False and s['state'] in TERMINAL_STATES and type(s['ended_utc']) is str
assert s['inputs']['wrapper']['sha256']==WRAPPER_SHA and s['inputs']['wrapper']['bytes']==15359 and s['inputs']['observer']['sha256']==OBSERVER_SHA and s['inputs']['observer']['bytes']==58755
assert s['scientific_admission'] is False and s['capacity_admission'] is False
if s['state'] in ('observer_completed','observer_refused_or_failed','administrative_postflight_failed'):assert type(s.get('observer_exit_code')) is int
missing=[name for name,cap in FILES if name not in seen];assert missing==d['missing_original_stream_names'] and (not missing or s['state']=='preflight_refused_no_observer_launch')
config,config_pin=byname['configuration.json'];cfg=strict(config);bare_pin={k:v for k,v in config_pin.items() if k!='original_bytes_base64'}
assert s['configuration']==bare_pin and cfg['format']=='swdb.lanl17-detached-passive-observer-administration-configuration.v1' and cfg['sealed'] is False and cfg['control_directory']==str(remote) and cfg['inputs']==s['inputs']
assert local_read(p,PACKET_CAP)==(b,packet_stat)
os.mkdir(dest,0o700);ds=dest.lstat();assert dest.resolve(strict=True)==dest and not any(q.is_symlink() for q in (dest,*dest.parents)) and stat.S_ISDIR(ds.st_mode) and ds.st_uid==os.getuid() and stat.S_IMODE(ds.st_mode)==0o700
directory_identity=(ds.st_dev,ds.st_ino,ds.st_uid,ds.st_gid,ds.st_mode)
result=[]
for name,raw,pin in decoded:
 assert (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))(dest.lstat())==directory_identity
 out=dest/name;fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 got,local_stat=local_read(out,allowed[name]);assert got==raw
 result.append({'local_path':str(out),'remote_original_path':pin['path'],'bytes':len(raw),'sha256':sha(raw),'remote_original_stat':pin['stat'],'local_original_stat':local_stat})
receipt={'format':'swdb.detached-passive-observer-original-local-byte-custody.v1','sealed':False,'source_packet':{'path':str(p),'bytes':len(b),'sha256':sha(b),'stat':packet_stat},'originals':result,'original_stream_and_seal_policies_unchanged':True,'semantic_or_success_or_capacity_admission':False}
receipt_raw=(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode();assert len(receipt_raw)<=65536
fd=os.open(dest/'local-custody.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
with os.fdopen(fd,'wb') as f:f.write(receipt_raw);f.flush();os.fsync(f.fileno())
assert local_read(dest/'local-custody.json',65536)[0]==receipt_raw and local_read(p,PACKET_CAP)==(b,packet_stat)
assert (lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,x.st_mode))(dest.lstat())==directory_identity
print(json.dumps({'output_directory':str(dest),'originals':[{'basename':P(x['local_path']).name,'bytes':x['bytes'],'sha256':x['sha256']} for x in result],'raw_original_bytes_preserved':True,'no_admission_inferred':True},sort_keys=True))

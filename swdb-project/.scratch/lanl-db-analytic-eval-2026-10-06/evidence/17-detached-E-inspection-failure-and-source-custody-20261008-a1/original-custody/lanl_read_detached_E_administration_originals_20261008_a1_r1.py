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
a=argparse.ArgumentParser();a.add_argument('--control-directory',required=True);args=a.parse_args()
assert os.getuid()==os.geteuid()==UID
folder=P(args.control_directory);assert folder.parent==BASE and folder.name in ('lanl14-detached-e-inspection-a1','lanl14-detached-e-removal-a1') and folder.resolve()==folder and not any(q.is_symlink() for q in (folder,*folder.parents))
s=folder.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
status,pin=read(folder/'status.json',16384);d=json.loads(status);assert d['format']=='swdb.lanl14-detached-exact-E-administration-status.v1' and d['sealed'] is False and d['state'] in ('guard_completed','guard_refused_or_failed','preflight_refused_no_guard_launch','administrative_postflight_failed')
assert d['state']=='preflight_refused_no_guard_launch' or type(d.get('guard_exit_code')) is int
originals=[]
for name,cap in [('status.json',16384),('configuration.json',16384),('tmux.conf',16384),('launch-status.json',16384),('launch.stdout',16384),('launch.stderr',16384),('guard.stdout',262144),('guard.stderr',262144)]:
 p=folder/name
 if not p.exists():
  assert name.startswith('guard.') and d['state']=='preflight_refused_no_guard_launch';continue
 b,fp=read(p,cap);originals.append({**fp,'original_bytes_base64':base64.b64encode(b).decode('ascii')})
assert read(folder/'status.json',16384)==(status,pin)
print(json.dumps({'format':'swdb.detached-E-administration-original-custody-transfer.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'control_directory':str(folder),'originals':originals,'legacy_state_label_is_not_launch_or_liveness_proof':True,'possible_guard_launch_recorded':any(k in d for k in ('guard_started_utc','guard_argv','guard_pid')),'terminal_guard_exit_recorded':type(d.get('guard_exit_code')) is int,'E_path_present':os.path.lexists(BASE/'ArchEvolve-lanl-generality-final-export-20261007-a1'),'capacity_bytes':{m:os.statvfs(m).f_bavail*os.statvfs(m).f_frsize for m in ('/data1','/data')},'no_success_or_admission_inferred':True},sort_keys=True))

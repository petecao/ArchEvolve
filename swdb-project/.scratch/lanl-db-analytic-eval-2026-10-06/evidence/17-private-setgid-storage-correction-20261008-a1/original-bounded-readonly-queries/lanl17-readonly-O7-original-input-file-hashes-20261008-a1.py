import pathlib,os,stat,json,hashlib,datetime,time,socket,pwd,signal
P=pathlib.Path;UID=114316761;ROOT=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-t1-counts-20261006-a1')
EXPECTED={'bc-counted/normalized.bc':'8c15ca5a8491f0e2d394abb0122cb9b3039327b179720d6bb058ef0b79ab6acf','bc-counted/source.json':'00a4d6af06c67c3f26f9914090e1752a8a9fac39c9f7790e16bce87b6905c943','bfs-counted/normalized.bc':'a65f27c06439fbf5212d2ec42bf0647e8b3538ebe2382bec52e31fdf05e3126a','bfs-counted/source.json':'1e743800d737bd1688b6b94a9494c3fd7746ba5105ad423d3eb8659cca0734ae'}
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def alarm(s,f):raise TimeoutError('finite_120_second_read')
signal.signal(signal.SIGALRM,alarm);signal.alarm(120);begin=time.monotonic();total=0
assert os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj' and socket.gethostname().split('.')[0]=='mbit10'
private=P('/data/yanruj');ps=private.lstat();assert stat.S_ISDIR(ps.st_mode) and ps.st_uid==UID and stat.S_IMODE(ps.st_mode)==0o700
result={'format':'swdb.original-O7-input-file-hash-observation.v1','sealed':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[],'per_file_byte_cap':512*1024**2,'total_byte_cap':1024**3,'seconds_cap':120,'raw_file_bodies_transferred':False}
for rel,expected in EXPECTED.items():
 p=ROOT/rel;assert p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents));s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and s.st_size<=512*1024**2
 h=hashlib.sha256();count=0;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  assert stamp(os.fstat(f.fileno()))==stamp(s)
  while True:
   assert time.monotonic()-begin<120
   b=f.read(1024*1024)
   if not b:break
   count+=len(b);total+=len(b);assert count<=512*1024**2 and total<=1024**3;h.update(b)
  assert count==s.st_size and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat())
 result['files'].append({'path':str(p),'bytes':count,'sha256':h.hexdigest(),'stat':stamp(s),'original_expected_sha256':expected,'original_hash_matches':h.hexdigest()==expected})
assert {k:stamp(private.lstat())[k] for k in ('dev','ino','mode','uid','gid')}=={k:stamp(ps)[k] for k in ('dev','ino','mode','uid','gid')}
result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['bytes_read']=total;result['elapsed_seconds']=time.monotonic()-begin
print(json.dumps(result,sort_keys=True));signal.alarm(0)

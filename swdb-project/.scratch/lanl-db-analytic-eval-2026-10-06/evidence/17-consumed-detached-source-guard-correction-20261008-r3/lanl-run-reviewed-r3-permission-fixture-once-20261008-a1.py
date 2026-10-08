"""One local synthetic permission fixture; no guard main or remote action."""
import datetime,hashlib,json,os,pathlib,signal,subprocess,time
P=pathlib.Path
PY=P('/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12')
PY_SHA='08fa4dbadc420090dfee2acf433b827ae05541f728d1478d96879122f53b4328'
TEST=P('/private/tmp/lanl_consumed_source_guard_r3_permission_isolated_test_source_20261008.py')
SOURCE=P('/private/tmp/lanl_consumed_detached_source_guard_r3_20261008.py')
ROOT=P('/private/tmp/lanl-consumed-source-r3-permission-fixture-actual-20261008-a1')
PINS={TEST:'cda7f3cdc0ca496e85ab6addd90a1a8688f47460cd1732455a3c0623866a47f4',SOURCE:'552cd7424138adcf025db119e0a132e0bc70d733d61aaaddda0effe2932c5371',PY:PY_SHA}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,data):
 b=(json.dumps(data,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert all(not p.is_symlink() and sha(p)==h for p,h in PINS.items())
assert not os.path.lexists(ROOT)
os.umask(0o077);ROOT.mkdir(mode=0o700)
argv=[str(PY),'-B',str(TEST)]
write(ROOT/'start.json',{'started_utc':now(),'argv':argv,'timeout_s':60,'pins':{str(p):h for p,h in PINS.items()},'synthetic_only':True,'guard_main':False,'scientific_admission':False})
started=time.monotonic();child=None;timed_out=False;code=None
with (ROOT/'stdout').open('xb') as out,(ROOT/'stderr').open('xb') as err:
 try:
  child=subprocess.Popen(argv,cwd=ROOT,env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},stdout=out,stderr=err,start_new_session=True)
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:timed_out=True
 finally:
  if child is not None:
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:child.wait(timeout=15)
   except subprocess.TimeoutExpired:
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    child.wait(timeout=5)
elapsed=time.monotonic()-started
assert all(sha(p)==h for p,h in PINS.items())
logs={name:{'bytes':(ROOT/name).stat().st_size,'sha256':sha(ROOT/name)} for name in ('stdout','stderr')}
assert all(v['bytes']<=65536 for v in logs.values())
stderr=(ROOT/'stderr').read_text()
passed=code==0 and not timed_out and '\nRan 8 tests in ' in stderr and stderr.rstrip().endswith('OK')
d={'format':'swdb.consumed-source-r3-permission-synthetic-fixture-actual.v1','canonical_ensure_ascii':True,'ended_utc':now(),'returncode':code,'timeout':timed_out,'elapsed_s':elapsed,'actual_test_bodies':8 if passed else None,'passed':passed,'pins':{str(p):h for p,h in PINS.items()},'original_unsealed_logs':logs,'old_six_R2_cases_repeated':False,'guard_main_or_remote_or_permissions_or_removal':False,'scientific_admission':False}
d['identity_sha256']=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
pin=write(ROOT/'receipt.json',d)
print(json.dumps({'root':str(ROOT),'passed':passed,'returncode':code,'receipt':pin,'identity_sha256':d['identity_sha256']}))
raise SystemExit(0 if passed else 1)

import concurrent.futures,datetime,hashlib,json,pathlib,subprocess,time
P=pathlib.Path
jobs=[('lanl14-final-report-status','lanl14-readonly-final-report-status-20261007-a2.py','9157fe1ca50222a5f572e9556d0426306c499062acd6d612e3f9148423b0125e'),('lanl14-owned-final-runtime-tree','lanl14-read-owned-final-runtime-custody-descendants-20261007-a1.py','4e1db51eebc1c2756baee4780561e4fb5cea8caafbca0717f944a6588ddffba4'),('lanl-cpu-future-status','lanl-cpu-future-status-with-report-retry-20261007-a4.py','b8dcec92f447a4d988137d413839a608998088b2c8692fdf55a340867316f54b')]
def pin(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def run(j):
 name,src,expected=j;p=P('/private/tmp')/src;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==expected
 argv=['ssh','-T','-o','BatchMode=yes','mbit10','/usr/bin/env','GIT_OPTIONAL_LOCKS=0','/usr/bin/timeout','--signal=TERM','--kill-after=60','180','/usr/bin/python3.12','-B','-']
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic()
 cp=subprocess.run(argv,input=b,capture_output=True,timeout=260)
 out=P('/private/tmp')/(name+'-observed-20261008-a8.json');err=out.with_suffix('.stderr')
 for q,v in [(out,cp.stdout),(err,cp.stderr)]:
  with q.open('xb') as f:f.write(v)
 r=dict(format='swdb.parent-readonly-status-original-transport.v1',sealed=False,argv=argv,source=pin(p,b),started_utc=start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-tick,returncode=cp.returncode,stdout=pin(out,cp.stdout),stderr=pin(err,cp.stderr))
 dest=P('/private/tmp')/(name+'-parent-status-transport-20261008-a8.json')
 with dest.open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
 assert cp.returncode==0 and not cp.stderr
 json.loads(cp.stdout)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(run,jobs):print(json.dumps(r,sort_keys=True))

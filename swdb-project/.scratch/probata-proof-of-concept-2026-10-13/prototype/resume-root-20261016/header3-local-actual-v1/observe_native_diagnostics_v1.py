"""2026-10-16 ET. Local finite passive actual13 status invocation, no rerun."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,time

HERE=Path(__file__).resolve().parent
EV=HERE.parents[2]/'evidence'
label=sys.argv[1]
assert label.replace('-','').isalnum()and len(label)<64
prefix='t25-owned-swap-header3-public-v1-'+label
source=(HERE/'native-diagnostics-v1.py').read_bytes()
argv=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10','/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/timeout','--signal=TERM','--kill-after=5s','60s','/usr/bin/python3','-I','-B','-']
started=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
p=subprocess.run(argv,input=source,capture_output=True,timeout=75)
def pin(path):
    b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
op=EV/(prefix+'-stdout-20261016.json');ep=EV/(prefix+'-stderr-20261016.txt')
for path,raw in [(op,p.stdout),(ep,p.stderr)]:
    with path.open('xb')as stream:stream.write(raw)
receipt={'date':'2026-10-16 ET','started_utc':started,'elapsed_seconds':time.monotonic()-clock,
         'argv':argv,'stdin_sha256':hashlib.sha256(source).hexdigest(),'exit_code':p.returncode,
         'stdout':pin(op),'stderr':pin(ep),'within_output_cap':len(p.stdout)<=262144 and len(p.stderr)<=65536,
         'native_verifier_compiler_or_job_rerun':False,'remote_mutation':False}
path=EV/(prefix+'-execution-20261016.json')
with path.open('x')as stream:json.dump(receipt,stream,sort_keys=True,indent=2);stream.write('\n')
print(json.dumps(pin(path)))
raise SystemExit(0 if p.returncode==0 and receipt['within_output_cap']else 1)

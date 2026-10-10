"""Compact read-only phase state; no parsing of forecasts or native outcomes."""
import datetime, json, os, pathlib
P=pathlib.Path
base=P('/data/yanruj/EvolveSWDB_runs')
def read(root,name):
 p=root/name
 if not p.is_file():return None
 assert p.stat().st_size<=1024*1024
 return p.read_text().strip()
rows=[]
for phase,folder in [('model','lanl-analytic-cpu-model-20261006-a3'),('development','lanl-analytic-cpu-development-20261006-a3'),('holdout','lanl-analytic-cpu-holdout-20261006-a3'),('band-report','lanl-analytic-cpu-band-report-20261006-a3'),('band-report-a4','lanl-analytic-cpu-band-report-20261007-a4')]:
 root=base/folder
 if not root.exists():
  rows.append({'phase':phase,'prepared_raw_exists':False});continue
 lane=json.loads(read(root,'lane.json') or '{}').get('socket_lane',{})
 files=sorted((p for p in root.iterdir() if p.is_file() and p.suffix in ('.stdout','.stderr')),key=lambda p:p.stat().st_mtime_ns)
 rows.append({'phase':phase,'prepared_raw_exists':True,'started_utc':read(root,'started.txt'),'completed_utc':read(root,'completed.txt'),
 'runner_exit':read(root,'runner-exit-code.txt'),'outer_exit':read(root,'exit-code.txt'),'acceptance_present':(root/'acceptance.json').is_file(),
 'runner_error':read(root,'runner-error.txt'),'output_files':[{'name':p.name,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files],
 'lane':{k:lane.get(k) for k in ('node','lease_generation','started_utc','ended_utc','exit_code','numa_memory_policy')},
 'published_files':len(list((root/'records').rglob('*.yaml'))),
 'final_cleanup':json.loads(read(root,'final-cleanup.json') or 'null')})
leases={n:json.loads((P('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text())['state'] for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phases':rows,'leases':leases,
 'capacity_bytes':{mount:os.statvfs(mount).f_bavail*os.statvfs(mount).f_frsize for mount in ('/data1','/data')},
 'memory_available_bytes':int(next(line.split()[1] for line in P('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024,
 'load':os.getloadavg(),'scope':'Read-only output-file/custody status; no forecast or native outcome parsing.'}))

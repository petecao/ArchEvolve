import datetime,json,pathlib
P=pathlib.Path
raw=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a1')
control=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-control-20261007-a1')
def read(p):return p.read_text().strip() if p.exists() else None
lane=json.loads(read(control/'lane.json') or '{}').get('socket_lane',{})
cases=[]
for name in ('returned','timeout','term'):
 p=raw/name/'supervisor-receipt.json'
 if p.exists():
  d=json.loads(p.read_text());cases.append({'case':name,'state':d['state'],'supervisor_exit':d['supervisor_exit'],'survivors':d['cleanup']['survivors']})
actual=json.loads(read(raw/'receipt.json') or 'null')
print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':read(control/'exit-code.txt'),'lane':{k:lane.get(k) for k in ('node','lease_generation','started_utc','ended_utc','exit_code','numa_memory_policy')},'case_receipts':cases,'actual_receipt_present':actual is not None,'passed':None if actual is None else actual['passed'],'failure_type':None if actual is None else actual['failure_type'],'survivors':None if actual is None else actual['cleanup']['survivors'],'leases':{n:json.loads((P('/data1/yanruj/lact-host-lease')/(n+'.meta.json')).read_text())['state'] for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}}))

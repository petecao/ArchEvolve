"""Parent dispatch admission; no active controls or scientific recipe changes."""
import hashlib, importlib.util, json, math, os, pathlib, subprocess, sys
sys.dont_write_bytecode=True
P=pathlib.Path
C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
assert len(sys.argv)==2 and sys.argv[1] in ('development','holdout','report')
phase=sys.argv[1]
controls=P('/data1/yanruj/lanl-cpu-controls-20261007-a1')
model_helper=controls/'lanl-dispatch-cpu-model-continuation-a3.py'
assert hashlib.sha256(model_helper.read_bytes()).hexdigest()=='90f28f9ad2dd65f87e74d194d376e26e4af7bd45d654fdba8c8a633afb33b7bc'
spec=importlib.util.spec_from_file_location('parent_actual_model_admission',model_helper)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.clean();cleanup=m.cleanup_module();cleanup.all_free()
capacity={
 'memory_available_bytes':int(next(line.split()[1] for line in P('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024,
 'free_disk_bytes':{mount:os.statvfs(mount).f_bavail*os.statvfs(mount).f_frsize for mount in ('/data1','/data')},
 'load_average':os.getloadavg(),
}
assert capacity['memory_available_bytes']>=80*1024**3
assert capacity['free_disk_bytes']['/data1']>=21*1024**3
assert capacity['free_disk_bytes']['/data']>=10*1024**3
def accepted(name):
 raw=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+name+'-20261006-a3')
 assert (raw/'runner-exit-code.txt').read_text().strip()=='0'
 assert (raw/'exit-code.txt').read_text().strip()=='0'
 assert json.loads((raw/'final-cleanup.json').read_text())['survivors']=={}
 lane=json.loads((raw/'lane.json').read_text())['socket_lane']
 assert lane['node']==0 and lane['exit_code']==0 and lane['ended_utc'] and lane['numa_memory_policy']=='bind:0'
 proof=m.sealed(json.loads((raw/'acceptance.json').read_text()))
 assert proof['phase']==name and proof['source_commit']==C and proof['source_clean'] is True
 assert proof['validation'].startswith('OK: ')
 return proof
model=accepted('model')
assert model['estimator_sha256']==F6 and model['ready_for_development'] is True
assert model['application_performance_timings_collected'] is False
assert len(model['estimates'])==4
assert {row['id'] for row in model['estimates']}=={'lanl.cpu.'+k+'.g'+str(g)+'.t1.estimate.v1' for k in ('bfs','bc') for g in (16,17)}
assert all(type(row['seconds']) in (int,float) and math.isfinite(row['seconds']) and row['seconds']>0 and row['evidence_kind']=='execution' and row['estimator_sha256']==F6 for row in model['estimates'])
if phase in ('holdout','report'):
 development=accepted('development')
 assert development['frozen_model_acceptance']['identity_sha256']==model['identity_sha256']
 assert development['protocols']==model['protocols']
 assert development['application_performance_timings_collected'] is True
 assert development['ready_for_holdout'] is True
 assert set(development['bands'])=={'bfs','bc'}
 assert all(row['state']=='development' and type(row['width_log']) in (int,float) and math.isfinite(row['width_log']) and row['width_log']>=0 for row in development['bands'].values())
if phase=='report':
 heldout=accepted('holdout')
 assert heldout['frozen_model_acceptance']['identity_sha256']==model['identity_sha256']
 assert heldout['protocols']==model['protocols']
 assert heldout['application_performance_timings_collected'] is True
 assert set(heldout['bands'])=={'bfs','bc'}
 # A failed held-out width is a scientific result; report it unchanged.
 assert all(row['state'] in ('validated','failed') for row in heldout['bands'].values())
 helper=controls/'lanl-dispatch-cpu-band-report-a4-metadata2400-cleanup60-hashlib.py'
 expected='543b79ea40a54537ee23b37ec1f44afbc8b135cad3fff25fb82d35db7b5130c7'
 argv=['python3',str(helper),C]
else:
 helper=controls/'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py'
 expected='804fb08298bf1469c6098dfcd1a50710f2cc941f9478895482c1fe7d901e6ecb'
 argv=['python3',str(helper),phase,C]
assert hashlib.sha256(helper.read_bytes()).hexdigest()==expected
cleanup.all_free();m.clean()
print(json.dumps({'phase':phase,'source_commit':C,'estimator_sha256':F6,'model_acceptance_identity':model['identity_sha256'],'selected_helper_sha256':expected,'capacity':capacity,'scientific_native_deadline_s':900}),flush=True)
subprocess.run(argv,check=True,timeout=240)

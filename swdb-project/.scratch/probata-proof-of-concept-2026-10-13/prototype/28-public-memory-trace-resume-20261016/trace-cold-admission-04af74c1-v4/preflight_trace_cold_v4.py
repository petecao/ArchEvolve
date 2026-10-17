"""Passive exact staged/runtime check plus finite original job observation only."""
from datetime import datetime,timezone
import hashlib,json,os,stat,sys
from pathlib import Path
CONTEXT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v4')
RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v4'
PROJECT='/data1/yanruj/probata-resume-20261016-04af74c1/swdb-project'
POLICY_SHA='71168a009a546c8aed54a141145f8472c7bbfe0a2791f20c2355993b1872f89f'
READER_SHA='3c7e4445fd6b12fe37f294843eb386f1189e567ad15a8904db541cffe71d50e3'
reader_path=CONTEXT/'control/trace_cold_audit_v4.py';b=reader_path.read_bytes();assert hashlib.sha256(b).hexdigest()==READER_SHA
ns={'__name__':'passive_trace_preflight_only','__file__':str(reader_path)};exec(compile(b,str(reader_path),'exec'),ns)
sys.addaudithook(ns['deny_passive'])
pf=CONTEXT/'control/trace-cold-policy-04af74c1-v4.json';rawpolicy=pf.read_bytes();assert hashlib.sha256(rawpolicy).hexdigest()==POLICY_SHA
policy=ns['validate_admission_policy'](json.loads(rawpolicy))
common=ns['module_from_bytes']('reviewed_cold_primitives_v1.py',ns['bootstrap_bytes'](policy['reader_files']['reviewed_cold_primitives_v1.py']))
physical=common.Physical();physical.pin(pf,POLICY_SHA);physical.pin(reader_path,READER_SHA)
expected=common.strict_json(physical.read(policy['source_policy']))
metadata_path=Path(RAW)/'control/python-physical-metadata-v2.json'
physical.pin(metadata_path,expected['control_files'][metadata_path.name]);metadata=common.strict_json(metadata_path.read_bytes())
closed=ns['module_from_bytes']('closed_python_surface.py',physical.read(policy['reader_files']['closed_python_surface.py']))
normalized=ns['normalized_runtime'](expected,metadata)
pure=common.pure_runtime_helpers(physical.read(policy['original_entry']).decode(),physical)
runtime=common.runtime_closure(normalized,closed,pure,physical);python=closed.verify_python_metadata(metadata)
control=CONTEXT/'control';staged=[]
for path in sorted(control.iterdir()):
 assert stat.S_ISREG(path.lstat().st_mode) and path.resolve()==path
 staged.append({'path':str(path),'bytes':path.stat().st_size,'sha256':physical.pin(path)})
assert len(staged)==19 and sum(row['bytes'] for row in staged)==701808
assert not os.path.lexists(CONTEXT/'reader-source-cache')
leases={}
for name in ('mbit10-evaluation-node1','mbit10-evaluation'):
 path=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');b=path.read_bytes()
 leases[name]={'path':str(path),'sha256':hashlib.sha256(b).hexdigest(),'metadata':common.strict_json(b)}
pids=[p for p in Path('/proc').iterdir() if p.name.isdigit()];assert len(pids)<50000
processes=[];failures=[];tokens=[RAW.encode(),str(CONTEXT).encode(),PROJECT.encode()]
for path in pids:
 try:command=(path/'cmdline').read_bytes()
 except OSError as error:failures.append({'pid':int(path.name),'type':type(error).__name__});continue
 if any(token in command for token in tokens):processes.append({'pid':int(path.name),'argv':[part.decode('utf-8','replace') for part in command.split(b'\0') if part]})
physical.unchanged()
print(json.dumps({'date':'2026-10-16 ET','observed_utc':datetime.now(timezone.utc).isoformat(),'classification':'PASSIVE_PREFLIGHT_AND_FINITE_SETTLEMENT_OBSERVATION','original_raw':RAW,'source_commit':expected['source_commit'],'reader_sha256':READER_SHA,'policy_sha256':POLICY_SHA,'staged_files':staged,'runtime':runtime,'python':python,'physical_checks':physical.checks,'target_and_legacy_leases':leases,'scanned_processes':len(pids),'selected_live_processes':processes,'proc_read_failures':failures,'reader_audit_executed':False,'scientific_reexecution':False,'continuing_process_absence_claim':False,'separate_final_null_watchdog_inferred':False},sort_keys=True,indent=2,allow_nan=False))

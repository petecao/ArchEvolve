"""Read-only compact report startup failure custody. Updated 2026-10-07 ET."""
import ast,datetime,hashlib,json,pathlib,socket,subprocess
P=pathlib.Path;C='f893fed400347ed23d92e917d8bde21b75e5375d'
assert socket.gethostname().split('.')[0]=='mbit10'
source=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
raw=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a3')
helper=P('/data1/yanruj/lanl-cpu-controls-20261007-a1/lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=60).strip()
assert git('rev-parse','HEAD')==C and not git('status','--porcelain')
h=helper.read_bytes();assert sha(h)=='dd74dbbe238c1d0c8222d894acd94ef1d344049da257d2a0d744afefb3d2b120'
template=next(ast.literal_eval(n.value) for n in ast.parse(h).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNNER_TEMPLATE' for t in n.targets))
expected=template.replace('SOURCE_VALUE',repr(str(source))).replace('RAW_VALUE',repr(str(raw))).replace('COMMIT_VALUE',repr(C)).encode()
runner=(raw/'runner.py').read_bytes();assert runner==expected
err=(raw/'dispatch-error.log').read_bytes();assert len(err)<8192
signal=next(line for line in err.decode().splitlines() if line.startswith('NameError:'))
assert "name 'hashlib' is not defined" in signal
prereg_bytes=(raw/'preregistration.json').read_bytes();prereg=json.loads(prereg_bytes)
assert prereg['source_commit']==C and prereg['source_clean'] is True
assert (raw/'exit-code.txt').read_text().strip()=='1'
lane=json.loads((raw/'lane.json').read_bytes())['socket_lane']
assert lane['node']==0 and lane['lease_generation']==508 and lane['exit_code']==1 and lane['ended_utc'] and lane['numa_memory_policy']=='bind:0'
leases={name:json.loads((P('/data1/yanruj/lact-host-lease')/(name+'.meta.json')).read_bytes())['state'] for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
assert all(v=='released' for v in leases.values())
assert not (raw/'started.txt').exists() and not (raw/'acceptance.json').exists()
assert not list((raw/'records').rglob('*.yaml'))
assert not any(p.suffix in ('.stdout','.stderr') for p in raw.iterdir())
imports=[alias.name for node in ast.parse(template).body if isinstance(node,ast.Import) for alias in node.names]
assert 'hashlib' not in imports
result={'format':'swdb.cpu-band-report-startup-failure-custody.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':C,'source_clean':True,'raw_directory':str(raw),'selected_helper_sha256':sha(h),'generated_runner_sha256':sha(runner),'generated_runner_exact_selected_template':True,'preregistration_sha256':sha(prereg_bytes),'error_log_sha256':sha(err),'error_signal':signal,'error_line':105,'standalone_runner_standard_imports':imports,'missing_binding':'hashlib','outer_exit':1,'lane':{k:lane[k] for k in ('node','lease_generation','started_utc','ended_utc','exit_code','numa_memory_policy')},'leases':leases,'started_record_absent':True,'acceptance_absent':True,'published_canonical_records':0,'scientific_stage_output_files':0,'startup_stopped_before_cleanup_bootstrap':True,'raw_transferred':False,'scope':'Compact failure signal and content hashes only; raw logs/output remain remote. This failed administrative startup does not alter admitted native/model/band evidence. Preserve this attempt and use a fresh retry directory.'}
result['identity_sha256']=sha(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
print(json.dumps(result,indent=2,allow_nan=False))

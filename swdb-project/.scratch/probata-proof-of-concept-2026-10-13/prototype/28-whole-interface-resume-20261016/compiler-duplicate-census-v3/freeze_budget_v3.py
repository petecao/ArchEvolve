"""Pin passive-budget source packet; never actual census/bootstrap execution."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-duplicate-census-v2'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):return json.loads(path.read_bytes())
prior=doc(OLD/'complete-census-source-packet-v2.json');assert pin(OLD/'complete-census-source-packet-v2.json')['sha256']=='df107e528109f41ef09be25f8a715b8b04aa48f1083b7b4e5580213ddb88ff7a'
for row in prior['files']+prior['inputs']+prior['primary_sources']+[prior['prior_actual_first_duplicate']]:assert pin(Path(row['path']))==row
validation={}
for name,expected in [('pure-census-controls.log',15),('pure-bootstrap-controls.log',4),('pure-budget-controls.log',4)]:
    row=json.loads((HERE/name).read_text().splitlines()[-1]);assert row['tests']==expected and row['errors']==row['failures']==row['skips']==0;validation[name]=row
throughput=WHOLE/'census-throughput-v1';measurement=doc(throughput/'synthetic-throughput-result.json')
assert measurement['child_events']==[] and measurement['rows'][0]['complete'] is True and measurement['rows'][1]['complete'] is False
files=[pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='complete-census-source-packet-v3.json']
out={'date':'2026-10-16 ET','schema':'complete-census-source-packet-3','status':'frozen source-only passive budget successor; new independent review/root admission required',
    'files':files,'predecessor':pin(OLD/'complete-census-source-packet-v2.json'),'predecessor_files_rehashed_unchanged':len(prior['files']+prior['inputs']+prior['primary_sources'])+1,
    'inputs':prior['inputs'],'primary_sources':prior['primary_sources'],'prior_actual_first_duplicate':prior['prior_actual_first_duplicate'],
    'throughput_evidence':[pin(throughput/'synthetic_throughput.py'),pin(throughput/'synthetic-throughput-result.json')],
    'throughput_is_synthetic_scaled_local_Mac_only':True,'full_sized_throughput_completed':False,'actual_target_runtime_rate_inferred':False,
    'validation':validation,'source_exact_inverse':True,'whole_module_AST_inverse':True,'bootstrap_exact_inverse':True,
    'passive_profile':{'address_space_bytes':536870912,'internal_wall_seconds':600,'CPU_seconds':650,'outer_seconds':660,'local_transport_seconds':700,'stdout_bytes_including_newline':32768},
    'capture_scientific_resource_caps_unchanged':True,'actual_complete_census_executed':False,'old_once_only_admission_reused':False,
    'AST_or_normalized_writes':False,'arbitrary_duplicate_keys_admitted':False,'public_source_ABI_or_proof_admission':False}
path=HERE/'complete-census-source-packet-v3.json';path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(pin(path)))

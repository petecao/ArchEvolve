"""Compact retained flags/unwind/array-length metadata only; no audit."""
from pathlib import Path
import hashlib,json,sys
BASE=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-trace-cold-04af74c1-v3/control')
f=BASE/'trace_cold_audit_v3.py';b=f.read_bytes();assert hashlib.sha256(b).hexdigest()=='a323298395677ed638d1e92a53fd0d386f54cab5eb815c266d8cdd1d3aff63aa'
ns={'__name__':'compact_retained_trace_flags','__file__':str(f)};exec(compile(b,str(f),'exec'),ns);sys.addaudithook(ns['deny_passive'])
p=BASE/'trace-cold-policy-04af74c1-v3.json';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='e2fe50f515a9eb287d5a559909671f01451dec932c4ec5d6256d9de472c86531';policy=ns['validate_admission_policy'](json.loads(b))
common=ns['module_from_bytes']('reviewed_cold_primitives_v1.py',ns['bootstrap_bytes'](policy['reader_files']['reviewed_cold_primitives_v1.py']));physical=common.Physical();expected=common.strict_json(physical.read(policy['source_policy']))
raw=Path(policy['raw']);meta_path=raw/'control/python-physical-metadata-v2.json';physical.pin(meta_path,expected['control_files'][meta_path.name]);metadata=common.strict_json(meta_path.read_bytes());closed=ns['module_from_bytes']('closed_python_surface.py',physical.read(policy['reader_files']['closed_python_surface.py']));yaml,_=common.admit_reader(policy,ns['normalized_runtime'](expected,metadata),closed,physical)
groups={};cases=[]
for row in policy['records']:
 p=Path(row['record']['path']);physical.pinned(row['record']);record=common.safe_yaml(yaml,p.read_bytes());settings=record['settings'];fixture=p.parent.parent.parent
 methods=[]
 for candidate in (fixture/'library/methods').glob('*.yaml'):
  rel=str(candidate.relative_to(raw));physical.pinned({'path':str(candidate),**policy['raw_manifest']['files'][rel]});method=common.safe_yaml(yaml,candidate.read_bytes())
  if method['id']==record['pins']['method_version']['id']:methods.append((candidate,method))
 assert len(methods)==1
 candidate,method=methods[0];flags=next(t['flags'] for t in method['lineup'] if t['tool']=='cbmc')
 values={'actual_settings_flags':settings['flags'],'actual_unwind':settings['unwind'],'actual_array_length':settings['array_length'],'method_flags':flags,'method_sha256':policy['raw_manifest']['files'][str(candidate.relative_to(raw))]['sha256']}
 key=common.digest(values);groups.setdefault(key,{'projection':values,'cases':[]})['cases'].append(row['case'])
 cases.append({'case':row['case'],'record_sha256':row['record']['sha256'],'projection_sha256':key})
physical.unchanged();assert not Path(policy['reader_admission']['pycache_prefix']).exists()
print(json.dumps({'classification':'PASSIVE_TRACE_FLAGS_SCALARS_METADATA_ONLY','groups':groups,'cases':cases,'physical_checks':physical.checks,'reader_audit_executed':False,'scientific_reexecution':False},indent=2,sort_keys=True))

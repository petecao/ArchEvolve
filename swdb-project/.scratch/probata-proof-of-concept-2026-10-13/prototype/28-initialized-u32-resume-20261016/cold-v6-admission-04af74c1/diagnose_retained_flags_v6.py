"""Passive compact retained flag mismatch diagnostic; no audit or child."""
from pathlib import Path
import hashlib,json,sys,types
BASE=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v6/control')
reader_path=BASE/'initialized_cold_audit_v6.py';raw=reader_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='02744c321c9bc60535f374d0b47b4d634b54e02c9786a31351c77859c3d8b598'
ns={'__name__':'compact_retained_flags_diagnostic','__file__':str(reader_path)}
exec(compile(raw,str(reader_path),'exec'),ns)
sys.addaudithook(ns['deny_children'])
physical=ns['Physical']();p=BASE/'initialized-cold-policy-04af74c1-v6.json'
physical.pin(p,'d808194fac3c7fae403ba494e712179f68f87d1d7e420068a80ec6561524eb14')
policy=ns['strict_json'](p.read_bytes());expected=ns['strict_json'](physical.read(policy['source_policy']))
mods=ns['load_reviewed_modules'](policy,physical)
yaml,python=ns['admit_reader'](policy,expected,mods['closed_python_surface.py'],physical)
rows=[]
for row in policy['records']:
 path=Path(row['record']['path']);physical.pinned(row['record']);record=ns['safe_yaml'](yaml,path.read_text())
 methodpath=path.parent.parent.parent/'library/methods/dx100-initialized-register-partial-fixture-v1.yaml'
 rel=str(methodpath.relative_to(policy['raw']));pin=policy['raw_manifest']['files'][rel]
 physical.pinned({'path':str(methodpath),**pin});method=ns['safe_yaml'](yaml,methodpath.read_text())
 flags=next(tool['flags'] for tool in method['lineup'] if tool['tool']=='frama-c-wp')
 actual=record['settings']['flags'];wanted=[*flags,'-machdep','x86_64','-wp-timeout','30','-wp-par','1','-wp-smoke-tests']
 rows.append({'expected_result':row['expected_result'],'record_sha256':row['record']['sha256'],'method_sha256':pin['sha256'],'method_flags':flags,'actual_settings_flags':actual,'cold_expected_flags':wanted,'equal':actual==wanted,'actual_flag_count':len(actual),'cold_flag_count':len(wanted),'prefix_equal':actual[:len(wanted)]==wanted,'extra_after_expected':actual[len(wanted):]})
physical.unchanged();assert not Path(policy['reader_admission']['pycache_prefix']).exists()
print(json.dumps({'classification':'PASSIVE_FLAGS_MISMATCH_METADATA_ONLY','records':rows,'physical_checks':physical.checks,'reader_audit_executed':False,'scientific_reexecution':False},indent=2,sort_keys=True))

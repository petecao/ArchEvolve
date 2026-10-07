"""Run one reviewed synthetic custody batch; no actual control or campaign main."""
import ast,datetime,hashlib,json,pathlib,re,subprocess,time
P=pathlib.Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
interpreter=P('/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3')
test=P('/private/tmp/lanl17_parent_capture_custody_isolated_regression_a3_20261007.py')
source=P('/private/tmp/lanl17_parent_capture_projection_producer_a3_20261007.py')
prep=P('/private/tmp/lanl17-parent-capture-custody-regression-source-proof-20261007-a3.json')
note=P('/private/tmp/lanl17-parent-capture-custody-regression-source-handoff-20261007-a3.md')
pins=[(test,'e1fbd54de38492f1706002f6755b8d5d09c5ad5fb21a7f2a3b3ca3ca132048f7',14003),(source,'32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6',46165),(note,'97c55556a10e7836dc4c2ed9da8533dbad3fad7a00edfc359bf0f148c9a26634',None)]
for p,h,n in pins:
    assert p.is_file() and not p.is_symlink() and sha(p.read_bytes())==h
    if n is not None:assert p.stat().st_size==n
d=json.loads(prep.read_bytes());assert d['identity_sha256']=='7ac9e87f563311422760d91439ad3731a8eb5ac1a5858aa7da93a9be28a830c5'
assert sha(json.dumps({k:v for k,v in d.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())==d['identity_sha256']
assert d['case_count']==12 and d['execution']['tests_run'] is False
tree=ast.parse(source.read_bytes());named={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in ('Refused','require','need','sha','hex64','regular','hash_file','returned_bytes','manifest_output_roots'):
    assert sha(ast.dump(named[name],include_attributes=False).encode())==d['exact_AST_fragment_sha256'][name]
paths={name:P('/private/tmp/lanl17-parent-capture-custody-regression-actual-20261007-a3.'+name) for name in ('start.json','stdout','stderr','json')}
assert all(not p.exists() and not p.is_symlink() for p in paths.values())
started=datetime.datetime.now(datetime.timezone.utc).isoformat();begin=time.monotonic()
start={'format':'swdb.lanl17-isolated-custody-test-start.v1','started_utc':started,'test_source':str(test),'test_source_sha256':pins[0][1],'producer_source_sha256':pins[1][1],'state':'original_unsealed_start_before_one_synthetic_subprocess','scientific_admission':False}
with paths['start.json'].open('x') as stream:stream.write(json.dumps(start,indent=2)+'\n')
with paths['stdout'].open('xb') as out,paths['stderr'].open('xb') as err:
    result=subprocess.run([str(interpreter),'-B',str(test)],stdout=out,stderr=err,timeout=60,check=False)
elapsed=time.monotonic()-begin;ended=datetime.datetime.now(datetime.timezone.utc).isoformat()
for p,h,n in pins:assert sha(p.read_bytes())==h
err=paths['stderr'].read_text();actual_count=re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$',err,re.M)
case_count=int(actual_count[0][0]) if len(actual_count)==1 else None
observed_ok=bool(re.search(r'^OK$',err,re.M))
receipt={'format':'swdb.lanl17-isolated-custody-regression-actual.v1','started_utc':started,'ended_utc':ended,'canonical_ensure_ascii':True,
         'actual_subprocess_returncode':result.returncode,'actual_reported_case_count':case_count,'actual_reported_OK':observed_ok,'elapsed_parent_seconds':elapsed,
         'original_preparation_identity':d['identity_sha256'],'test_source':{'path':str(test),'bytes':test.stat().st_size,'sha256':pins[0][1]},'producer_source':{'path':str(source),'bytes':source.stat().st_size,'sha256':pins[1][1]},
         'outputs':{name:{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'original_sealed':False} for name,p in paths.items() if name!='json'},
         'source_and_preparation_preserved':True,'batch_invocations':1,'scientific_admission':False,'actual_campaign_or_input_capture':False,
         'scope':'One actual synthetic local 12-case batch: exact custody-helper/guard/diagnostic AST only. Original producer/main/role builders/Store/SWDB/auditor/collector/SSH/native/provider never executed; original 47/18 checks not repeated. This establishes selected helper regression behavior only.'}
receipt['identity_sha256']=sha(json.dumps(receipt,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
with paths['json'].open('x') as stream:stream.write(json.dumps(receipt,indent=2,ensure_ascii=True,allow_nan=False)+'\n')
print(json.dumps({'path':str(paths['json']),'bytes':paths['json'].stat().st_size,'sha256':sha(paths['json'].read_bytes()),'identity_sha256':receipt['identity_sha256'],'returncode':result.returncode,'cases':case_count,'OK':observed_ok,'scientific_admission':False}))
assert result.returncode==0 and case_count==12 and observed_ok

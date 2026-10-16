"""Inert focused10 packet authoring from frozen Git and isolated pure canonical files."""
import ast,base64,copy,hashlib,json,subprocess,zlib
from pathlib import Path
repo=Path('/private/tmp/probata-resume-t25');rev='e99d09b1699b32525cd4c44cead21ed2fc6f4917';remote='/data1/yanruj/probata-reviewed-e99d09b1/swdb-project';P=Path('/private/tmp');prefix='probata-t25-copy-prefix10-';suffix='-v1-e99d09b1-20261016'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(x):return(json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def pin(p):p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),*a],timeout=60)
def blob(path,r=rev):return git('show',r+':swdb-project/'+path)
def save(name,b,ext='.json'):
 p=P/(prefix+name+suffix+ext)
 with p.open('xb')as f:f.write(b)
 return pin(p)
oldpacket=json.loads((P/'probata-t25-copy-step15-packet-v3-3a48da2f-20261016.json').read_bytes());oldentry=Path(oldpacket['entry']['path']).read_bytes();oldx=Path(oldpacket['expected']['path']).read_bytes();oldcmd=json.loads(Path(oldpacket['root_command']['path']).read_bytes())
for key in ['entry','expected','root_command']:assert pin(oldpacket[key]['path'])==oldpacket[key]
x=json.loads(oldx);x.update(source_commit=rev,remote_project=remote,method_id='method.wp-copy-prefix10-diagnostic-v1',status='INERT: exact-source/root-entry review and coordinator admission mandatory',scope='Ten isolated source-equivalent copied-prefix cases, each full originalA+range and one exhaustive integercase. Complete61 canonical precheck,51unexecuted includingnumericC; no previous14proofs/prefix result/sibling theorem imported, no public proofrecord/model/caller/originalv2/ticket acceptance.')
x['resource_policy'].update(root_whole_seconds=1500,root_outer_seconds=1620,profile_seconds=1300,leaf_timeout_seconds=180)
x['cost_estimate']='Ten fresh math leaves; unchanged30s/full-three canonicalportfolio/cache-none. Simple worst90s×10=900s leaves400s setup/report margin in1300profile,1500whole1620outer,8GiB1worker2GiBraw. This is an estimate, not solverpolicychange or resultprediction; all61complete publictargets later stillrequired.'
rows=[]
for item in git('ls-tree','-r','-z',rev,'--','swdb-project/swdb').split(b'\0'):
 if not item:continue
 meta,path=item.decode().split('\t',1);mode,kind,oid=meta.split();assert mode in {'100644','100755'}and kind=='blob';relative=path.removeprefix('swdb-project/');rows.append({'path':path,'relative':relative,'blob':oid,'sha256':sha(blob(relative))})
x['source_blobs']=rows
for row in x['test_helper_pins']:row['sha256']=sha(blob(row['relative']))
for relative,tree in x['source_consumer_trees'].items():tree['oid']=git('rev-parse',rev+':swdb-project/'+relative).decode().strip()
# Recipe independently validated against retained genuine046 runtime; current context must be freshly equal at launch.
materializer=(P/'probata-t25-qualified-grow38-public-materialize-v2-37ffe407-20261016.py').read_text();fn=next(n for n in ast.parse(materializer).body if isinstance(n,ast.FunctionDef)and n.name=='identity');ns={'ast':ast,'json':json,'copy':copy,'sha':sha,'blob':blob};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<passive digest recipe>','exec'),ns)
actual=json.loads((P/'probata-t25-cell4-setup-only-metadata-v1-20261016.json').read_bytes())['metadata']['cell4-setup-only-profile/compiler-runtime.json']['content'];assert ns['identity']('046f6b9e64d45777a8032951ced04f942fc9c3c2',actual['runtime'],actual['identity'])==actual['identity']
runtime=copy.deepcopy(actual['runtime']);changes=[]
for i,value in enumerate(runtime['frontend']):
 for flag in ['-fdebug-compilation-dir=','-fcoverage-compilation-dir=']:
  if value==flag+'/data1/yanruj/probata-reviewed-046f6b9e/swdb-project':runtime['frontend'][i]=flag+remote;changes.append(flag)
assert len(changes)==2;runtime['check']['sha256']=sha(blob('swdb/stdlib_provenance.py'))
x['linux_project_identity_derivation']={'runtime':runtime,'predicted_identity':ns['identity'](rev,runtime,actual['identity']),'scope':'Prospective source/context reconstruction only. Actual Linux current runtime/identity must equal this before setup, never old Mac/3a/188 identities.'}
preparer=P/'probata-t25-prefix10-pure-canonical-v1-e99d09b1-20261016';receipt=json.loads((preparer/'preparer-receipt.json').read_bytes());manifest=json.loads((preparer/'canonical/manifest.json').read_bytes());assert receipt['source_commit']==rev and receipt['target_count']==61 and not receipt['external_native_attempts']
for r in receipt['files']:assert sha(blob(r['relative']))==r['sha256']
x.update(canonical_manifest_sha256=receipt['manifest_sha256'],model=manifest['model'],logical_obligations=manifest['logical_obligations'],target_ids=[r['id']for r in manifest['obligations']],diagnostic_ids=receipt['focused_ids'],typed_source_image=manifest['typed_source_image'],canonical_files=receipt['canonical_files'])
x['explicit_method_binding']['qualified_model']=manifest['model'];assert len(x['target_ids'])==61 and len(x['diagnostic_ids'])==10 and len(x['canonical_files'])==70
expected=save('expected',js(x))
s=oldentry.decode().replace(sha(oldx),expected['sha256']).replace('copy-step15','copy-prefix10').replace('fifteen','ten').replace('Fifteen','Ten').replace('All52','All61').replace('complete52','complete61').replace('full52','full61').replace("'model_target_count':52","'model_target_count':61").replace("'full_targets':52,'diagnostic_targets':15","'full_targets':61,'diagnostic_targets':10").replace('!=52','!=61').replace('!=15','!=10').replace('exact15independent','exact10independent')
assert 'all_ten_producer_proven'in s and 'all_fifteen'not in s and '!=52'not in s;ast.parse(s);entry=save('entry',s.encode(),'.py')
cmd=copy.deepcopy(oldcmd);boot=cmd[6]
for a,b in [(sha(oldentry),entry['sha256']),(sha(oldx),expected['sha256']),(base64.b64encode(zlib.compress(oldentry,9)).decode(),base64.b64encode(zlib.compress(s.encode(),9)).decode()),(base64.b64encode(zlib.compress(oldx,9)).decode(),base64.b64encode(zlib.compress(js(x),9)).decode())]:assert a in boot;boot=boot.replace(a,b)
boot=boot.replace('copy-step15','copy-prefix10');ast.parse(boot);cmd[6]=boot;assert len(cmd)==9 and len(boot.encode())<120000
command=save('root-command',js(cmd))
# Preserve source-first review: no actual class/tool/helper probe, entry/main or project import here.
literals={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(boot).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in {'ENTRY_SHA256','EXPECTED_SHA256','ENTRY_COMPRESSED_BASE64','EXPECTED_COMPRESSED_BASE64'}}
assert zlib.decompress(base64.b64decode(literals['ENTRY_COMPRESSED_BASE64'],validate=True))==s.encode()and zlib.decompress(base64.b64decode(literals['EXPECTED_COMPRESSED_BASE64'],validate=True))==js(x)
inverse=boot.replace('copy-prefix10','copy-step15')
for a,b in [(entry['sha256'],sha(oldentry)),(expected['sha256'],sha(oldx)),(literals['ENTRY_COMPRESSED_BASE64'],base64.b64encode(zlib.compress(oldentry,9)).decode()),(literals['EXPECTED_COMPRESSED_BASE64'],base64.b64encode(zlib.compress(oldx,9)).decode())]:assert a in inverse;inverse=inverse.replace(a,b)
assert inverse==oldcmd[6]
oldfunctions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(oldentry).body if isinstance(n,ast.FunctionDef)};newfunctions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};assert oldfunctions.keys()==newfunctions.keys()and all(oldfunctions[n]==newfunctions[n]for n in oldfunctions if n!='main')
plan={'status':'INERT; source publication/independent static/root actual admission mandatory','source_commit':rev,'remote_project':remote,'shared_source_with_initialized_u32_pair':True,'root_kind':'t25-copy-prefix10-diagnostic-v1','entry':entry,'expected':expected,'root_command':command,'predecessor_focused15_packet':pin(P/'probata-t25-copy-step15-packet-v3-3a48da2f-20261016.json'),'preparer':pin(P/'probata-t25-prefix10-canonical-author-v1-e99d09b1-20261016.py'),'preparer_receipt':pin(preparer/'preparer-receipt.json'),'prefix_source_review':pin(P/'probata-t25-copy-prefix-ten-case-independent-source-review-v2-e0e8a435-20261016.md'),'source_query_equivalence_review':pin(P/'probata-t25-prefix-actual-binding-and-equivalence-review-v1-20261016.md'),'canonical_manifest_sha256':x['canonical_manifest_sha256'],'canonical_files':70,'physical_reference_C_files':5,'complete_model_targets':61,'fresh_diagnostic_targets':10,'unexecuted_model_targets':51,'old_results_imported':0,'public_proof_record_created':False,'full_public_model_required_after_diagnostic':True,'resource_policy':x['resource_policy'],'cost_estimate':x['cost_estimate'],'ordinary_policy':'Each row genuine WpAdapter/tools/seed/report/foundation/Typed/check_generated→engine.check_launch, normal native/property/CSV/Extern reader and source-lemma ownership; no certificate filtering or source overlays. Full original A/range and both exhaustive cases, allfiveconclusions required.','aggregate_identity_policy':'Per-leaf IDs/property/goal and complete multiplicity, no cross-leaf short-goal singleton assumption; source lemma ownership stays per row.','source_package_count':len(rows),'helper_count':len(x['test_helper_pins']),'consumer_roots':x['source_consumer_trees'],'hardened_bootstrap_inverse_predecessor_equal':True,'embedded_roundtrip_exact':True,'nonmain_helpers_AST_equal':True,'model_acceptance':False,'original_v2_acceptance':False,'caller_acceptance':False,'ticket_closure':False,'independent_static_review_pending':True,'actual_native_task_hypothesis_review_pending':True}
p=save('packet',js(plan));print(json.dumps({'packet':p,'entry':entry,'expected':expected,'command':command,'package':len(rows),'helpers':len(x['test_helper_pins']),'bootstrap_utf8_bytes':len(boot.encode()),'prospective_compiler_identity':x['linux_project_identity_derivation']['predicted_identity']['c_lowering']},indent=2))

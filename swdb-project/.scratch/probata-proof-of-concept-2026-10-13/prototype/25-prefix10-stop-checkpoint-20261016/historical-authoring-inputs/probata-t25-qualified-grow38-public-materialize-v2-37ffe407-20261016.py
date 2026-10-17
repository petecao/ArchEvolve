"""Pure packet authoring from immutable Git and retained metadata. Never execute an actual entry."""
import ast,base64,copy,hashlib,json,subprocess,zlib
from pathlib import Path
REPO=Path('/private/tmp/probata-resume-t25');REV='37ffe407a10888ff9628c75f37ba770995a3ecd5';OLD='046f6b9e64d45777a8032951ced04f942fc9c3c2'
PREFIX='/private/tmp/probata-t25-qualified-grow38-public-';SUFFIX='-v1-37ffe407-20261016'
PURE=Path('/private/tmp/probata-t25-grow38-preparer-only-v3-37ffe407-20261016');PROJECT='/data1/yanruj/probata-reviewed-37ffe407/swdb-project'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(o):return(json.dumps(o,indent=2,sort_keys=True)+'\n').encode()
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(REPO),*a])
def blob(path,rev=REV):return git('show',rev+':swdb-project/'+path)
def pin(p):p=Path(p);b=p.read_bytes();return{'path':str(p),'sha256':sha(b),'bytes':len(b)}
def save(name,data,ext='.json'):
 p=Path(PREFIX+name+SUFFIX+ext)
 with p.open('xb')as f:f.write(data)
 return pin(p)
def literals(source,names):
 tree=ast.parse(source);return{n.targets[0].id:ast.dump(n.value,include_attributes=False)for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in names}
# Independent, explicit digest recipe; verified below against a retained actual046 composite.
TAIL=['array_domains.py','vector_ownership.py','vector_reallocation_model.py','vector_reallocation_calls.py','vector_reallocation_vcs.py','vector_reallocation_inventory.py','vector_reallocation_view.py','vector_reallocation_lifetime.py','vector_reallocation_capacity.py','vector_reallocation_caller_vcs.py','heap_reallocation.mlw','vector_pipeline.py','model_domains.py','standard_model_view.py','helper_windows.py','nested_entry_reads.py','dx_array_domains.py','standard_range_calls.py','member_windows.py','stdlib_source_admission.py','dx100_source_selector.py','dx100_size_source.py','dx100_stream_source.py','dx100_stream_model.py','dx100_allocation_source.py','dx100_register_source.py','dx100_register_model.py']
def identity(rev,runtime,template):
 b=lambda n:blob('swdb/'+n,rev)
 tree=ast.parse(b('c_lowering.py'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='identity');digest=next(n for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='digest'for t in n.targets))
 calls=sorted((n for n in ast.walk(digest)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='with_name'),key=lambda n:(n.lineno,n.col_offset))
 tail=[ast.literal_eval(n.args[0])for n in calls]
 bounded=sha(b('bounded_initialization.py')+b('proof_semantics.py')+b('bounded_std_initialization.py'))
 pointer=sha(b('wp_pointer_bounds.py'))
 raw=b('c_lowering.py')+b('terminal_release.py')+b('cpu_effects.py')+b('cpu_memory_admission.py')+bounded.encode()+pointer.encode()+b''.join(b(n)for n in tail)+json.dumps(runtime,sort_keys=True).encode()
 result=copy.deepcopy(template);result['c_lowering']['sha256']=sha(raw);return result
old_expected_path=Path('/private/tmp/probata-t25-qualified-grow24-public-expected-v1-046f6b9e-20261016.json');oldx=old_expected_path.read_bytes();d=json.loads(oldx)
actual_path=Path('/private/tmp/probata-t25-cell4-setup-only-metadata-v1-20261016.json');observation=json.loads(actual_path.read_bytes())['metadata']['cell4-setup-only-profile/compiler-runtime.json']['content']
old_runtime=observation['runtime'];old_identity=observation['identity']
if identity(OLD,old_runtime,old_identity)!=old_identity:raise ValueError('independent digest recipe fails actual046 composite')
names={'TOOL_ID','TOOL_VERSION','NAMING_RULES','RULES'}
if literals(blob('swdb/c_lowering.py'),names)!=literals(blob('swdb/c_lowering.py',OLD),names):raise ValueError('compiler naming/tool constants changed')
runtime=copy.deepcopy(old_runtime);cwd_old='/data1/yanruj/probata-reviewed-046f6b9e/swdb-project';changed=[]
for i,token in enumerate(runtime['frontend']):
 for flag in ('-fdebug-compilation-dir=','-fcoverage-compilation-dir='):
  if token==flag+cwd_old:runtime['frontend'][i]=flag+PROJECT;changed.append(flag)
if sorted(changed)!=['-fcoverage-compilation-dir=','-fdebug-compilation-dir=']:raise ValueError('frontend context template shape changed')
runtime['check']['sha256']=sha(blob('swdb/stdlib_provenance.py'))
predicted=identity(REV,runtime,old_identity)
# Read only regular immutable package blobs and the eight direct standard-seed inputs.
rows=[]
for item in git('ls-tree','-r','-z',REV,'--','swdb-project/swdb').split(b'\0'):
 if not item:continue
 meta,path=item.decode().split('\t',1);mode,kind,oid=meta.split()
 if mode not in {'100644','100755'}or kind!='blob':raise ValueError('nonregular source package blob')
 relative=path.removeprefix('swdb-project/');rows.append({'path':path,'relative':relative,'blob':oid,'sha256':sha(blob(relative))})
d['source_blobs']=rows;d['source_commit']=REV
for row in d['test_helper_pins']:row['sha256']=sha(blob(row['relative']))
for relative,tree in d['source_consumer_trees'].items():tree['oid']=git('rev-parse',REV+':swdb-project/'+relative).decode().strip()
manifest=json.loads((PURE/'canonical/manifest.json').read_bytes());receipt=json.loads((PURE/'preparer-receipt.json').read_bytes())
if receipt['source_commit']!=REV or len(manifest['obligations'])!=38:raise ValueError('wrong pure canonical input')
for row in receipt['files']:
 if sha(blob(row['relative']))!=row['sha256']:raise ValueError('materialized pure module differs from current frozen Git')
d['model']=manifest['model'];d['explicit_method_binding']['qualified_model']=manifest['model']
d['logical_obligations']=manifest['logical_obligations'];d['target_ids']=[r['id']for r in manifest['obligations']]
d['canonical_manifest_sha256']=sha((PURE/'canonical/manifest.json').read_bytes());d['canonical_files']=receipt['canonical_files'];d['canonical_reference_files']=receipt['physical_reference_files'];d['typed_source_image']=manifest['typed_source_image']
d['method_id']='method.wp-qualified-grow38-v1';d['remote_project']=PROJECT
recipe_names=['c_lowering.py','terminal_release.py','cpu_effects.py','cpu_memory_admission.py','bounded_initialization.py','proof_semantics.py','bounded_std_initialization.py','wp_pointer_bounds.py']+TAIL
recipe={'source_files':[{'relative':'swdb/'+n,'sha256':sha(blob('swdb/'+n))}for n in recipe_names],
 'ordered_tail':TAIL,'runtime':runtime,'predicted_identity':predicted,
 'actual046_recipe_reconstruction_equal':True,'old_actual_observation':pin(actual_path),
 'scope':'Prospective pure reconstruction of the exact current source digest and context-specific Linux runtime. The unchanged public compiler must freshly observe this full runtime and identity; this predicted identity is not an actual37 observation or proof.',
 'allowed_frontend_template_replacements':{'from':cwd_old,'to':PROJECT,'tokens':changed}}
d.pop('linux_project_identity_pin');d['linux_project_identity_derivation']=recipe
d['scope']='One complete qualified v3 grow mathematical C-body profile, all38 fresh targets including fifteen exact copy-invariant conjuncts and numeric C kernel. Two top-level logical groups and three physical reference C files retained. Normal public CLI, canonical/source/setup, ordinary/RTE/init/smoke/dependency/schema/persistence checks. Original-v2, generic caller and ticket acceptance remain false.'
d['resource_policy'].update(root_whole_seconds=2400,root_outer_seconds=2520,profile_seconds=2200,public_timeout_seconds=2100)
d['cost_estimate']='Root-selected2400whole/2520outer/2200profile/2100public,8GiB1worker/2GiBraw. Scripted38-run native/schema controls24.29465s are interface evidence only. Prior actual046 grow24 stopped at copy.establish; fifteen equivalent leaves are fresh and have no completed proof timing. No success guarantee or budget-only remedy claimed.'
d['prior_results_not_reused']+=['046G596partialgrow24','046G621partialctor30','4bab scripted38-interface controls']
d['status']='INERT, all actual admission and execution reserved for root after independent packet review'
x=save('expected',js(d))
oldentry_path=Path('/private/tmp/probata-t25-qualified-grow24-public-entry-v1-046f6b9e-20261016.py');oldentry=oldentry_path.read_bytes();s=oldentry.decode().replace(sha(oldx),x['sha256']).replace('grow24','grow38').replace('complete24','complete38').replace('full24','full38').replace('!=24','!=38').replace("'fresh_targets':24","'fresh_targets':38").replace('targets=24','targets=38').replace('synthetic34','synthetic48')
s=s.replace("        if lowering_identity!=expected['linux_project_identity_pin']['identity']:raise ValueError('current exact046 project compiler/source composite differs from actualG594 observation')", "        if str(project)!=expected['remote_project']:raise ValueError('project cwd differs from the exact derived compiler context')\n        if project_runtime!=expected['linux_project_identity_derivation']['runtime']:raise ValueError('fresh project runtime differs from source/context-derived Linux template')\n        if lowering_identity!=expected['linux_project_identity_derivation']['predicted_identity']:raise ValueError('fresh current source compiler composite differs from independent exact digest reconstruction')")
needle="        if manifest['logical_obligations']!=expected['logical_obligations']:raise ValueError('complete logical projection AND/source-definition binding differs')"
s=s.replace(needle,needle+"\n        if manifest['typed_source_image']!=expected['typed_source_image']:raise ValueError('canonical typed-source image differs')\n        physical=[{'path':str(p.relative_to(canonical)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(canonical.rglob('*'))if p.is_file()]\n        if physical!=expected['canonical_files']:raise ValueError('complete canonical payload/reference physical membership differs')\n        if [r for r in physical if r['path'].startswith('references/')]!=expected['canonical_reference_files']or len(expected['canonical_reference_files'])!=3:raise ValueError('all three physical reference C files required')",1)
needle="        if view['logical_obligations']!=expected['logical_obligations']:raise ValueError('actual projection split receipt differs')"
s=s.replace(needle,needle+"\n        if view['typed_source_image']!=expected['typed_source_image']:raise ValueError('actual qualified source-image binding differs')",1)
s=s.replace("'model':manifest['model'],'fresh_targets':38", "'model':manifest['model'],'logical_groups':len(manifest['logical_obligations']),'physical_reference_files':expected['canonical_reference_files'],'fresh_targets':38")
if "linux_project_identity_pin"in s or '!=24'in s or 'targets=24'in s:raise ValueError('stale profile binding')
ast.parse(s);entry=save('entry',s.encode(),'.py')
oldcommand_path=Path('/private/tmp/probata-t25-qualified-grow24-public-root-command-v2-046f6b9e-20261016.json');command=json.loads(oldcommand_path.read_bytes());boot=command[6]
for before,after in [(sha(oldentry),entry['sha256']),(sha(oldx),x['sha256']),(base64.b64encode(zlib.compress(oldentry,9)).decode(),base64.b64encode(zlib.compress(s.encode(),9)).decode()),(base64.b64encode(zlib.compress(oldx,9)).decode(),base64.b64encode(zlib.compress(js(d),9)).decode())]:
 if before not in boot:raise ValueError('hardened embedding predecessor absent')
 boot=boot.replace(before,after)
boot=boot.replace('grow24','grow38');ast.parse(boot);command[6]=boot
if len(boot.encode())>=120000:raise ValueError('bootstrap exceeds admitted single-argv ceiling')
cmd=save('root-command',js(command))
review=json.loads(Path('/private/tmp/probata-t25-qualified-grow24-public-root-source-change-review-v1-046f6b9e-20261016.json').read_bytes())
review.update(source_commit=REV,entry=entry,expected=x,command=cmd,resource_policy=d['resource_policy'],scope=d['scope'],source_package_checks=len(rows))
changed=git('diff','--name-only',review['baseline'],REV,'--','swdb-project/swdb').decode().splitlines();review['files_after']={p:sha(git('show',REV+':'+p))for p in changed}
review['inner_independent_review']=pin('/private/tmp/probata-t25-copy-establish-and15-independent-source-review-a20f7a98-20261016.md')
review['review_evidence']=pin('/private/tmp/probata-t25-copy-establish-and15-independent-source-review-a20f7a98-20261016.json')
review['actual_native_setup']={'scope':'Prior actual046 runtime physical components retained as template; no current37 runtime or proof acceptance inferred','reference':pin(actual_path)}
review['scripted_public_controls']=pin('/private/tmp/probata-t25-root-grow38-public-controls-v1-20261016/result.json')
review['proof_acceptance']=False;review['status']='INERT current37 allowlist candidate; root independently reviews before actual execution'
allow=save('root-source-change-review',js(review))
plan={'created':'2026-10-16 ET','status':'INERT; independent root review and admission mandatory; no actual entry/bootstrap executed',
 'source_commit':REV,'root_kind':'t25-qualified-grow38-public-v1','remote_source':str(Path(PROJECT).parent),'reuse_existing_shared_remote_checkout':True,
 'entry':entry,'expected':x,'root_command':cmd,'root_source_change_review':allow,'hardened_root_command_predecessor':pin(oldcommand_path),
 'scope':d['scope'],'resource_policy':d['resource_policy'],'cost_estimate':d['cost_estimate'],'current_targets':38,'check_lemmas':37,'numeric_C_kernels':1,
 'logical_groups':2,'physical_reference_C_files':d['canonical_reference_files'],'canonical_manifest_sha256':d['canonical_manifest_sha256'],'model':d['model'],
 'normal_public_route':True,'direct_private_adapter_construction':False,'actual_package_overlays':False,'old_records_imported':0,
 'actual_goal_census':'Derived from all38 current native inventories/normal readers and exact aggregate multiset; no forced synthetic48 goal count; numeric smoke required.',
 'compiler_context':recipe,'source_package_count':len(rows),'test_helper_count':len(d['test_helper_pins']),'opaque_consumer_roots':d['source_consumer_trees'],
 'pure_preparer':pin('/private/tmp/probata-t25-grow38-pure-materialization-v3-37ffe407-20261016.py'),'pure_preparer_receipt':pin(PURE/'preparer-receipt.json'),
 'preparer_history':{'v1':'Import whitelist refused before canonical generation; partial external preparer directory retained.','v2':'Exact unchanged-module import closure generated same canonical bytes without locate/identity/probes. Superseded by the restricted literals-only v3; all artifacts retained.'},
 'independent_AND15_review':pin('/private/tmp/probata-t25-copy-establish-and15-independent-source-review-a20f7a98-20261016.md'),
 'scripted_interface_controls':pin('/private/tmp/probata-t25-root-grow38-public-controls-v1-20261016/result.json'),
 'committed_scripted_control_cold_summary':{'git_path':'swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-and15-scripted-public-controls-4babafd2-20261016.json','sha256':sha(blob('.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-and15-scripted-public-controls-4babafd2-20261016.json'))},
 'allowed_execution_root_only':['read-only Git byte/membership checks','selected Clang locator/version and runtime wrapper/frontend/header/parser metadata','normal seed YAML/header/reference closure and Store','existing OCaml/native helper and report module compilation','38 normal public WP leaves, unchanged canonical portfolio/per-goal30/cache-none/RTE/init/smoke','normal native inventory/JSON/CSV readers/schema/persistence'],
 'proof_gate':'Fresh all38 complete proof and independent complete source/task/hypothesis/support/import/resource cold audit required; producer exit alone is not model acceptance.',
 'original_v2_acceptance':False,'caller_acceptance':False,'ticket_closure':False}
planref=save('plan',js(plan));print(json.dumps({'entry':entry,'expected':x,'root_command':cmd,'allowlist':allow,'plan':planref,'bootstrap_bytes':len(boot.encode()),'sources':len(rows),'predicted_identity':predicted},indent=2))

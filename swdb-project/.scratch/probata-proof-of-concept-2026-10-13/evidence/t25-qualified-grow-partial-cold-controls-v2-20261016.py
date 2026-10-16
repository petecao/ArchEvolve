"""Pure retained metadata and source-only parser controls; no actual tools/probes/imports."""
from pathlib import Path
import json,runpy,copy,hashlib,ast
import pytest
B=Path('/private/tmp');R=runpy.run_path(str(B/'probata-t25-qualified-grow-partial-cold-reader-v2-20261016.py'));P=json.loads((B/'probata-t25-qualified-grow-partial-cold-policy-v2-20261016.json').read_text());M=P['metadata'];REC=P['record'];E=P['expected']
def target_data(index):
 run=REC['settings']['heap_model_runs'][index];prefix=str(Path(run['cwd']).relative_to(Path(P['raw'])));files=M['files'];return (copy.deepcopy(files[prefix+'/wp-inventory.json']['content']),copy.deepcopy(files[prefix+'/wp-goals.json']['content']),copy.deepcopy(REC['goals'][index]),copy.deepcopy(P['canonical_manifest']['obligations'][index]),files[prefix+'/wp-properties.csv']['content'])
def test_actual_partial_classification():
 out=R['check_record'](REC,E);assert out['attempted']==3 and out['direct_valid']==2 and len(out['unexecuted'])==17 and not out['model_acceptance']
@pytest.mark.parametrize('index',[0,1,2])
def test_all_retained_native_inventory_csv(index):
 out=R['target_census'](*target_data(index));assert out['ordinary']==1 and out['smokes']==0 and out['properties']==2 and out['CSV_rows']==0
@pytest.mark.parametrize('mutation',['claim_proven','failure_removed','goals_missing','extra_run','unexecuted_missing','smoke_fake','function_fake','extern_assumption','wrong_method','nonfresh','caller_promoted'])
def test_partial_promotion_or_census_refused(mutation):
 r=copy.deepcopy(REC);e=copy.deepcopy(E)
 if mutation=='claim_proven':r['verdict']='proven'
 elif mutation=='failure_removed':r['failure_class']=None
 elif mutation=='goals_missing':r['goals'].pop()
 elif mutation=='extra_run':r['settings']['heap_model_runs'].append(copy.deepcopy(r['settings']['heap_model_runs'][-1]))
 elif mutation=='unexecuted_missing':e['target_ids'].pop()
 elif mutation=='smoke_fake':r['goals'][0]['smoke']=True
 elif mutation=='function_fake':r['goals'][0]['function']='invented'
 elif mutation=='extern_assumption':r['assumptions'][0]['kind']='assumed_clause'
 elif mutation=='wrong_method':r['pins']['method_version']['id']='wrong'
 elif mutation=='nonfresh':r['settings']['session']='reuse'
 elif mutation=='caller_promoted':r['settings']['heap_model_view']['qualification']['original_contract_proved']=True
 with pytest.raises(AssertionError):R['check_record'](r,e)
@pytest.mark.parametrize('index',[0,1,2])
@pytest.mark.parametrize('mutation',['missing_goal','duplicate_property','property_owner','desired_dependency','extern','smoke','result_error','native_wrong','winner','CSVrow'])
def test_native_census_refusals(index,mutation):
 inv,native,goal,target,csv=target_data(index)
 if mutation=='missing_goal':inv['goals']=[]
 elif mutation=='duplicate_property':inv['properties'].append(copy.deepcopy(inv['properties'][0]))
 elif mutation=='property_owner':inv['properties'][1]['function']='helper'
 elif mutation=='desired_dependency':inv['properties'][1]['dependencies']=['same_result']
 elif mutation=='extern':inv['properties'][1]['extern']=True
 elif mutation=='smoke':inv['goals'][0]['smoke']=True
 elif mutation=='result_error':inv['goals'][0]['results']=['failed']
 elif mutation=='native_wrong':native[0]['goal']='wrong'
 elif mutation=='winner':native[0]['provers'][1]['success']=int(not native[0]['provers'][1]['success'])
 elif mutation=='CSVrow':csv+='x\tx\tx\tx\tx\tx\tx\n'
 with pytest.raises(AssertionError):R['target_census'](inv,native,goal,target,csv)
def test_exact_all20_canonical_obligations_and_actual3_source_hashes():
 assert P['canonical_manifest']['obligations']==REC['settings']['heap_model_view']['obligations']
 for index,(filename,text) in enumerate(P['canonical_C'].items()):assert hashlib.sha256(text.encode()).hexdigest()==next(t['sha256'] for t in P['canonical_manifest']['obligations'] if t['path']==filename)
def test_actual_printed_context_names_and_no_project_lemma_declarations():
 logs=P['actual_task_metadata']['logs'];assert len(logs)==3
 for row in logs:
  b=row['printed_theories'][0];assert [d['kind'] for d in b['declarations']].count('goal')==1 and not any(d['kind'] in {'axiom','lemma'} for d in b['declarations'])
 assert len(P['actual_task_metadata']['materialized_tasks'])==14 and all(t['last_assertion_is_negation'] for t in P['actual_task_metadata']['materialized_tasks'])
def test_transitive_source_import_closure_pure():
 prefix=Path('/Users/yanrujhou/.opam/framac-33');heap=B/'probata-t25-mac-qualified-generation-v1-01771a83-20261016/component/inputs/theory/heap_reallocation.mlw';roots=set(P['actual_task_metadata']['logs'][0]['direct_imports']);seen={}
 def pin(path):h=hashlib.sha256(Path(path).read_bytes()).hexdigest();seen[str(path)]=h;return h
 out=R['imported_context'](roots,prefix/'share/why3/stdlib',prefix/'share/frama-c/share/wp/why3',heap,pin);assert len(out)>9 and out['heap_reallocation.Heap']['proposition_declarations']==[]
def test_same_source_projection_template_parses_without_a_proof_claim():
 text=(B/'probata-t25-mac-qualified-generation-v1-01771a83-20261016/component/frama-generation.log').read_text();blocks=R['printed_blocks'](text);assert blocks[0]['queries']==P['actual_task_metadata']['logs'][2]['printed_theories'][0]['queries']
def test_context_recomputed_for_both_actual_compiler_cwds_without_probe():
 project=B/'probata-root-t25-controls-01771a83/swdb-project'
 for k in ['runtime-provenance.json','qualified-grow-profile/heap-project-runtime-provenance.json']:
  r=M['files'][k]['content'];assert R['lowerer_projection'](project,r['runtime'])==r['lowering_identity']['c_lowering']['sha256']
def test_no_executable_tools_production_imports_or_raw_writes():
 tree=ast.parse((B/'probata-t25-qualified-grow-partial-cold-reader-v2-20261016.py').read_text())
 for n in ast.walk(tree):
  if isinstance(n,ast.Import):assert all(q.name in {'hashlib','json','re','sys','stat','ast','math'} for q in n.names)
  if isinstance(n,ast.ImportFrom):assert n.module in {'pathlib','collections'}
  if isinstance(n,ast.Attribute):assert n.attr not in {'Popen','system','exec_command','write_bytes','write_text','unlink','mkdir'}

def test_complete_source_certificate_setup_runtime_bindings():
 project=B/'probata-root-t25-controls-01771a83/swdb-project'
 def pin(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 R['check_bindings'](REC,project,pin)
@pytest.mark.parametrize('mut',['certificate','view','model','std','compiler','setup_input','setup_plan','setup_summary','code'])
def test_source_record_binding_mutations_refused(mut):
 r=copy.deepcopy(REC);project=B/'probata-root-t25-controls-01771a83/swdb-project'
 if mut=='certificate':r['pins']['heap_model_view_certificate']['sha256']='0'*64
 elif mut=='view':r['pins']['heap_model_view_check']['sha256']='0'*64
 elif mut=='model':r['pins']['vector_reallocation_model']['sha256']='0'*64
 elif mut=='std':r['pins']['std_models']['sha256']='0'*64
 elif mut=='compiler':r['proof_setup_check']['hashes']['compiler_runtime']='0'*64
 elif mut=='setup_input':r['proof_setup_check']['runs'][0]['hashes']['wp_input.c']='0'*64
 elif mut=='setup_plan':r['proof_setup_check']['runs'][1]['run_plan_sha256']='0'*64
 elif mut=='setup_summary':r['proof_setup_check']['runs'][0]['hashes']['summaries']='0'*64
 elif mut=='code':r['pins']['code']['sha256']='0'*64
 with pytest.raises(AssertionError):R['check_bindings'](r,project,lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest())

def test_captured_actual_module_files208_distinct_from416_checks():
 assert len(M['files']['source-manifest.json']['content'])==208 and M['module_physical_git_checks']==416
 assert R['check_module_manifest'](M)=={'files':208,'physical_git_checks':416}
 # Reproduce the exact pre-dispatch V1 expression against actual captured data.
 src=(B/'probata-t25-qualified-grow-partial-cold-reader-v1-20261016.py').read_text();tree=ast.parse(src);bad=[n for n in ast.walk(tree) if isinstance(n,ast.Assert) and ast.get_source_segment(src,n.test)=="len(m['files']['source-manifest.json']['content'])==416"]
 assert len(bad)==1
 expression=ast.Expression(bad[0].test);assert eval(compile(expression,'<retained-v1-source-expression>','eval'),{'len':len},{'m':M}) is False

def test_all208_captured_module_pins_match_physical_frozen017_source():
 root=B/'probata-root-t25-controls-01771a83'
 for relative,h in M['files']['source-manifest.json']['content'].items():assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==h

@pytest.mark.parametrize('mutation',['missing_module','extra_module','checks415','checks208','invalid_digest'])
def test_module_census_refuses_captured_metadata_mutations(mutation):
 m=copy.deepcopy(M);manifest=m['files']['source-manifest.json']['content']
 if mutation=='missing_module':manifest.pop(next(iter(manifest)))
 elif mutation=='extra_module':manifest['swdb-project/swdb/invented_module.py']='0'*64
 elif mutation=='checks415':m['module_physical_git_checks']=415
 elif mutation=='checks208':m['module_physical_git_checks']=208
 elif mutation=='invalid_digest':manifest[next(iter(manifest))]='Z'*64
 with pytest.raises(AssertionError):R['check_module_manifest'](m)

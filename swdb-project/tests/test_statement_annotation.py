"""Statement claims, independent simulated ranks and provider-role fixtures.

Updated: 2026-10-05 ET (shared tests/testkit); 2026-10-03. Fixtures never constitute real-provider or lab evidence.
"""

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, REPO
from swdb import annotation, artifacts, callgrind_lines, provider_roles, rewrite
from swdb.bfs_profiling import parse_callgrind_lines, _tdstep_source
from swdb.cli import Failure
from swdb.schemas import SchemaSet
from swdb import paths, vocab


def small_source(tmp_path, count=7):
    root = tmp_path/'source'; root.mkdir()
    (root/'src').mkdir()
    code = '\n'.join(f'int value{i} = a[{i}];' for i in range(count))+'\n'
    (root/'src/bfs.cc').write_text(code)
    pattern = {'id':'read-a', 'steps':[{'address_shape':'stream'}], 'update_kind':'read', 'semantics':{}}
    rows = [{'id':f'statement-{i}', 'source':{'path':'src/bfs.cc', 'lines':[i+11,i+11]},
             'code':line, 'access_pattern_steps':[{'pattern':'read-a','step':0}], 'depends_on':[]}
            for i,line in enumerate(code.splitlines())]
    impl = {'id':'test-implementation','access_patterns':[pattern], 'extensions':{'statements':{
            'function':'TDStep','annotations':rows}}}
    source = {'id':'test-source','implementation':impl['id'], 'artifact':artifacts.identify(root),
        'context':{'source_derivation':{'removed_pinned_line_ranges':[[1,10]]}}}
    response = {'statements':[{'statement':r['id'], 'pattern_class':[annotation._pattern_class(pattern)],
        'index_provenance':[], 'expected_cost_rank':i+1, 'basis':'code_reading'} for i,r in enumerate(rows)],
        'unresolved':[]}
    metadata = {'model':'fixture-model','effort':'high','prompt_sha256':'b'*64,
        'classification':'contract_fixture','workspace_manifest':{'input_sha256s':{'source':'a'*64}}}
    annotated = annotation.append_claims(impl,response,metadata,annotation.mapped_statements(impl,source))
    return impl, source, annotated


def costs_profile(source, misses):
    rows = []
    for i,value in enumerate(misses):
        rows.append({'path':str(Path(source['artifact']['path'])/'src/bfs.cc'),'function':'TDStep',
                     'line':i+1,'events':{'DLmr':value,'DLmw':0}, 'basis':'simulated',
                     'source_artifact_sha256':source['artifact']['sha256']})
    return {'id':'line-profile','implementation':source['implementation'],'source_snapshot':source['id'],
            'per_line_memory':rows}


def test_compressed_names_subpositions_repeated_lines_and_inclusive_edges():
    rows = parse_callgrind_lines(FIXTURES/'profile/callgrind-lines.out')
    row = next(r for r in rows if r['line']==77 and r['function'].endswith('&)'))
    assert row['events']['DLmr']==3  # repeated self costs sum
    assert any('push_back' in r['function'] for r in rows)  # shared cfn/fn name ID
    assert not any(r['line']==84 for r in rows)  # inclusive calls cost excluded
    assert next(r for r in rows if r['line']==83)['events']['DLmw']==1
    assert all(r['basis']=='simulated' for r in rows)


@pytest.mark.parametrize('body,message',[
    ('fl=(8)\nfn=f\n1 1','undefined'),
    ('fl=f\nfn=f\n* 1','preceding'),
    ('fl=f\nfn=f\n1 -1','malformed'),
    ('fl=f\nfn=f\n1 9223372036854775808','bound'),
    ('fl=f\nfn=f\ncalls=1 1','lacks'),
    ('fl=f\nfn=f\n1 1\npart: 1\npart: 2','multipart'),
])
def test_bad_per_line_data_is_refused(body,message):
    with pytest.raises(Failure, match=message):
        callgrind_lines.parse(('events: Ir\n'+body+'\n').encode())


def test_independent_line_validator_checks_hierarchy_and_duplicate_identity():
    row={'path':'bfs.cc','function':'TDStep','line':1,'events':{'DLmr':2,'D1mr':1},'basis':'simulated'}
    with pytest.raises(Failure,match='exceeds'):
        callgrind_lines.validate([row])
    row['events']['D1mr']=2
    with pytest.raises(Failure,match='duplicate'):
        callgrind_lines.validate([row,row])
    with pytest.raises(Failure,match='invalid'):
        callgrind_lines.validate([{**row,'basis':'measured'}])
    with pytest.raises(Failure,match='invalid'):
        callgrind_lines.validate([{**row,'execution':'bad'}])
    with pytest.raises(Failure,match='invalid'):
        callgrind_lines.validate([{**row,'execution':{'source':-1}}])


def test_scalar_source_derivation_claims_do_not_overwrite_facts(tmp_path):
    impl, source, annotated = small_source(tmp_path)
    original = copy.deepcopy(impl)
    mapped = annotation.mapped_statements(impl,source)
    assert mapped[0]['lines']==[1,1] and mapped[0]['original_source']['lines']==[11,11]
    assert mapped[0]['mapping_method']=='removed_pinned_line_ranges'
    assert impl==original
    assert annotated['access_patterns'][0]['steps']==impl['access_patterns'][0]['steps']
    assert len(annotated['extensions']['statements']['annotations'][0]['agent_claims'])==3
    assert annotated['access_patterns'][0]['agent_claims'][0]['basis']=='code_reading'
    assert annotation._last_claim(annotation.statements(annotated)[0],'expected_cost_rank')['basis']=='inferred'


def test_scalar_derivation_refuses_deleted_and_ambiguous_statements(tmp_path):
    impl, source, _ = small_source(tmp_path)
    source['context']['source_derivation']['removed_pinned_line_ranges']=[[1,11]]
    with pytest.raises(Failure,match='removed'):
        annotation.mapped_statements(impl,source)
    source['context']['source_derivation']['removed_pinned_line_ranges']=[[1,10]]
    impl['extensions']['statements']['annotations'][0]['code']='not a statement'
    with pytest.raises(Failure,match='uniquely'):
        annotation.mapped_statements(impl,source)


def test_later_source_annotations_preserve_earlier_snapshot_mappings(tmp_path):
    impl,source,annotated=small_source(tmp_path)
    previous=copy.deepcopy(annotated)
    next_source={**source,'id':'next-source'}
    response={'statements':[{'statement':r['id'],
        'pattern_class':annotation._last_claim(r,'pattern_class')['value'],
        'index_provenance':annotation._last_claim(r,'index_provenance')['value'],
        'expected_cost_rank':annotation._last_claim(r,'expected_cost_rank')['value'],
        'basis':'code_reading'} for r in annotation.statements(annotated)],'unresolved':[]}
    metadata={'model':'fixture','effort':'high','prompt_sha256':'b'*64,
        'classification':'contract_fixture','workspace_manifest':{'input_sha256s':{'source':'a'*64}}}
    later=annotation.append_claims(annotated,response,metadata,annotation.mapped_statements(impl,next_source))
    mappings=later['extensions']['statements']['source_mappings']
    assert len(mappings)==14
    assert mappings[:7]==previous['extensions']['statements']['source_mappings']
    assert {r['source_snapshot'] for r in mappings}=={source['id'],next_source['id']}
    assert annotated==previous


def test_statement_costs_use_verified_source_identity_across_baseline_copies(tmp_path):
    impl, source, _ = small_source(tmp_path)
    profile = costs_profile(source, [7,6,5,4,3,2,1])
    copied = tmp_path/'baseline-copy/src/bfs.cc'
    copied.parent.mkdir(parents=True)
    copied.write_bytes((Path(source['artifact']['path'])/'src/bfs.cc').read_bytes())
    for row in profile['per_line_memory']:
        row.update(path=str(copied), source_path='src/bfs.cc', source_file_sha256=artifacts.file_hash(copied))
    assert [c['value'] for c in annotation.statement_costs(impl,source,profile,verify_raw=False)] == [7,6,5,4,3,2,1]
    for row in profile['per_line_memory']:
        row['source_file_sha256']='f'*64
    with pytest.raises(Failure,match='no rows'):
        annotation.statement_costs(impl,source,profile,verify_raw=False)


def test_real_profile_driver_accepts_the_existing_pinned_workload(tmp_path, monkeypatch):
    import runpy
    from types import SimpleNamespace
    driver = runpy.run_path(str(REPO/'tools/typed_library_profile_driver.py'),run_name='driver_test')
    root = tmp_path/'scalar'; code=root/'benchmarks/gapbs/src/bfs.cc'
    code.parent.mkdir(parents=True); code.write_text('void TDStep() {}\n')
    source={'id':driver['SOURCE'],'implementation':'dx100-bfs-scalar',
            'artifact':{'sha256':driver['SOURCE_SHA256']}}
    workload=yaml.safe_load((REPO/'records/workloads'/f"{driver['WORKLOAD']}.yaml").read_text())
    class Store:
        def get(self, identity, kind):
            return source if kind=='source_snapshot' else workload
    monkeypatch.setattr(artifacts,'verify',lambda value:root)
    args=SimpleNamespace(source_snapshot=driver['SOURCE'],workload=driver['WORKLOAD'])
    actual=driver['validate_inputs'](args,Store())
    assert actual==(source,workload)
    workload['definition']['sources']=[1]
    with pytest.raises(Failure,match='Kronecker18 source0'):
        driver['validate_inputs'](args,Store())


def test_rank_score_and_contradiction_rule(tmp_path):
    impl, source, annotated = small_source(tmp_path)
    scored, report = annotation.score(annotated,source,costs_profile(source,[1,2,3,4,5,6,7]),verify_raw=False)
    assert report['spearman_rank_correlation']==-1
    assert report['top_3_overlap']==0
    assert sum(r['contradicted'] for r in report['statements'])==6
    assert annotation._last_claim(annotation.statements(scored)[0],'expected_cost_rank')['contradicted_by']
    assert not annotation._last_claim(annotation.statements(scored)[0],'pattern_class')['contradicted_by']
    assert impl['access_patterns'][0]['steps']==scored['access_patterns'][0]['steps']
    table=annotation.statement_table(scored,report)
    assert '| statement-0 | 1–1 |' in table and 'simulated' in table and 'Draft' in table


def test_tied_ranks_and_top_three_boundary_do_not_invent_order(tmp_path):
    _,source,annotated=small_source(tmp_path)
    _,report=annotation.score(annotated,source,costs_profile(source,[9,9,8,8,1,0,0]),verify_raw=False)
    assert [r['callgrind_rank'] for r in report['statements']]==[1.5,1.5,3.5,3.5,5,6.5,6.5]
    assert report['top_3_overlap']==pytest.approx(2.5/3)
    _,constant=annotation.score(annotated,source,costs_profile(source,[0]*7),verify_raw=False)
    assert constant['spearman_rank_correlation'] is None
    assert constant['top_3_overlap']==pytest.approx(3/7)


def test_only_real_facts_contradict_pattern_and_index_claims(tmp_path):
    _,source,annotated=small_source(tmp_path)
    row=annotation.statements(annotated)[0]
    row['annotation_facts']=[{'field':'index_provenance','value':['statement-1'],'basis':'code_reading','evidence':'reader'}]
    scored,_=annotation.score(annotated,source,costs_profile(source,[7,6,5,4,3,2,1]),verify_raw=False)
    assert not annotation._last_claim(annotation.statements(scored)[0],'index_provenance')['contradicted_by']
    row['annotation_facts'][0]['basis']='reported'
    scored,_=annotation.score(annotated,source,costs_profile(source,[7,6,5,4,3,2,1]),verify_raw=False)
    assert annotation._last_claim(annotation.statements(scored)[0],'index_provenance')['contradicted_by'][0]['basis']=='reported'


def test_role_inputs_and_lane_refusal_precede_workspace(tmp_path,monkeypatch):
    role=provider_roles.Role('read_only_fixture',{'type':'object'})
    for name,content in [('workloads/input.json','{}'),('code.cc','void TDStepMAA() {}'),
                         ('context.json',json.dumps({'evaluator':{'answer':'hidden'}}))]:
        with pytest.raises(Failure):
            provider_roles.prepare(role,{name:content},tmp_path/'blocked',{'kind':'external_fixture'})
    from swdb import provider_guard
    monkeypatch.setattr(provider_guard,'verified_lane',lambda: (_ for _ in ()).throw(provider_guard.GuardError('mbit10 lane required')))
    with pytest.raises(Failure,match='mbit10 lane'):
        provider_roles.run(role,{'code.cc':'source'},'read',{'kind':'codex'},tmp_path/'real')
    assert not (tmp_path/'real').exists()


def test_fixture_role_uses_shared_launcher_and_retains_settings(tmp_path):
    role=provider_roles.Role('read_only_fixture',{'type':'object','additionalProperties':False,
        'required':['observed'],'properties':{'observed':{'type':'string'}}})
    program=tmp_path/'fixture.py'
    program.write_text('import json\nfrom pathlib import Path\nprint(json.dumps({"observed":Path("source.cc").read_text()}))\n')
    configfile=tmp_path/'provider.yaml'
    configfile.write_text(yaml.safe_dump({'kind':'external_fixture','command':[sys.executable,str(program)],
                                        'timeout_s':5,'total_seconds':5}))
    result,metadata=provider_roles.run(role,{'source.cc':'visible source'},'read source',
                                     rewrite.configuration(configfile),tmp_path/'role')
    assert result=={'observed':'visible source'}
    assert metadata['role']=='read_only_fixture' and metadata['classification']=='contract_fixture'
    assert metadata['prompt_sha256']==artifacts.file_hash(tmp_path/'role/prompt.txt')
    assert metadata['workspace_manifest']['login_copy_deleted']
    assert metadata['audit']['passed']


def test_role_refuses_input_modifications(tmp_path):
    program=tmp_path/'fixture.py'
    program.write_text('import json\nfrom pathlib import Path\nPath("source.cc").write_text("changed")\nprint("{}")\n')
    configfile=tmp_path/'provider.yaml'
    configfile.write_text(yaml.safe_dump({'kind':'external_fixture','command':[sys.executable,str(program)],
                                        'timeout_s':5,'total_seconds':5}))
    with pytest.raises(Failure,match='immutable'):
        provider_roles.run(provider_roles.Role('fixture',{'type':'object'}),{'source.cc':'source'},'read',
                           rewrite.configuration(configfile),tmp_path/'role')


def test_tdstep_function_identity_keeps_exact_debug_lines_and_other_functions(tmp_path):
    source=tmp_path/'source.cc'
    code='void Helper() {}\nvoid TDStep() {\n  Helper();\n}\nvoid DOBFS() {}\n'
    source.write_text(code)
    start=code.index('void TDStep')
    brace=code.index('{',start)+1
    rewritten=_tdstep_source(source,[{'kind':'function','name':'TDStep','byte_range':[start,code.index('}',brace)+1],
                                    'insertion_range':[brace,code.index('}',brace)+1]}]).decode()
    assert '__attribute__((noinline)) void TDStep' in rewritten
    assert rewritten.startswith('#line 1 ')
    assert 'swdb_statement::Scope' not in rewritten
    assert rewritten.split('\n',1)[1].replace('__attribute__((noinline)) ','')==code
    assert 'void Helper() {}' in rewritten and 'void DOBFS() {}' in rewritten


def test_agent_claim_schema_accepts_only_claim_bases(tmp_path):
    _,_,annotated=small_source(tmp_path)
    vocabs,_=vocab.load_all(paths.VOCAB)
    schema=SchemaSet(paths.SCHEMAS,vocabs).merged('implementation')['$defs']['agent_claim']
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(schema)
    claim=annotation.statements(annotated)[0]['agent_claims'][0]
    assert not list(validator.iter_errors(claim))
    for change in ({'basis':'simulated'},{'prompt_sha256':'unknown'},{'input_sha256s':{}},
                   {'contradicted_by':[{'basis':'code_reading','evidence':'reader','rule':'different'}]}):
        assert list(validator.iter_errors({**claim,**change}))


@pytest.mark.parametrize('kind',['codex','claude'])
def test_annotate_fixture_role_through_public_cli(workspace_proposal_setup,tmp_path,kind):
    records,runs,source,_=workspace_proposal_setup
    impl=records.read('implementations/gapbs-bfs-do.yaml')
    file=Path(source['artifact']['path'])/'src/bfs.cc'
    lines=file.read_text().splitlines()
    position=next(i+1 for i,line in enumerate(lines) if 'NodeID curr_val = parent[v];' in line)
    pattern=impl['access_patterns'][0]
    impl['extensions']={'statements':{'function':'TDStep','annotations':[{
        'id':'fixture-statement','source':{'path':'src/bfs.cc','lines':[position,position]},
        'code':lines[position-1].strip(),'access_pattern_steps':[{'pattern':pattern['id'],'step':0}],
        'depends_on':[],'basis':'code_reading'}]}}
    records.write('implementations/gapbs-bfs-do.yaml',impl)
    program=tmp_path/'annotation-provider.py'
    program.write_text('''import json,sys
from pathlib import Path
if "--version" in sys.argv:
    print("0.0-role-fixture")
    raise SystemExit(0)
kind=sys.argv[1].split("=",1)[1]
ctx=json.loads(Path("statement-context.json").read_text())
source=Path("statement-source.cc").read_text()
assert "TDStep(" in source and "BFSVerifier" not in source
rows=[]
for i,s in enumerate(ctx["statements"]):
    classes=[{"pattern":p["id"],"address_shapes":[v["address_shape"] for v in p["steps"]],"update_kind":p["update_kind"]}
        for p in ctx["access_patterns"] if p["id"] in {v["pattern"] for v in s["access_pattern_steps"]}]
    rows.append({"statement":s["id"],"pattern_class":classes,"index_provenance":[],"expected_cost_rank":i+1,"basis":"code_reading"})
result={"statements":rows,"unresolved":[]}
if kind=="codex":
    print(json.dumps({"type":"item.completed","item":{"type":"command_execution","command":"cat statement-context.json statement-source.cc","exit_code":0}}))
    Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps(result))
    print(json.dumps({"type":"turn.completed","usage":{"output_tokens":10}}))
else:
    print(json.dumps({"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"statement-context.json"}}]}}))
    print(json.dumps({"type":"result","subtype":"success","is_error":False,"structured_output":result}))
''')
    config=tmp_path/'provider.yaml'
    config.write_text(yaml.safe_dump({'kind':'external_fixture','emulates':kind,
        'command':[sys.executable,str(program),'--fixture-kind='+kind],'timeout_s':10,'total_seconds':10}))
    result=records.swdb('annotate',impl['id'],'--source-snapshot',source['id'],'--provider-config',config,
        '--runs-dir',runs,'--id',f'annotation-{kind}','--format','json')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['classification']=='contract_fixture'
    persisted=records.read('implementations/gapbs-bfs-do.yaml')
    claims=annotation.statements(persisted)[0]['agent_claims']
    assert len(claims)==3
    from swdb.provider_adapters import PINS
    assert claims[0]['model']==PINS[kind]['model'] and claims[0]['effort']==PINS[kind]['effort']
    assert claims[0]['classification']=='contract_fixture'
    assert persisted['access_patterns'][0]['steps']==pattern['steps']
    assert records.validate().returncode==0
    # Public scoring reparses real fixture bytes, preserves a sealed profile's
    # digest when its derived costs already match, and refuses later tampering.
    from swdb.workflow import record
    raw=tmp_path/f'statement-{kind}.callgrind'
    raw.write_text(f'''events: Ir Dr Dw D1mr D1mw DLmr DLmw
summary: 10 3 1 2 1 1 1
totals: 10 3 1 2 1 1 1
fl={file}
fn=TDStep()
{position} 10 3 1 2 1 1 1
''')
    rows=parse_callgrind_lines(raw)
    rows[0].update(source_artifact_sha256=source['artifact']['sha256'],artifact_sha256='a'*64,
        raw_artifact=str(raw),raw_sha256=artifacts.file_hash(raw),
        execution={'source':0,'source_position':0,'repetition':0,'tdstep_position':0},
        counter_validation={'state':'valid','method':callgrind_lines.METHOD},
        source_path='src/bfs.cc',source_file_sha256=artifacts.file_hash(file))
    profile=record('region_profile',f'annotation-costs-{kind}',message_version='1.0',
        producer={'name':'annotation-fixture','role':'operator','test_client':True},request={},
        implementation=impl['id'],source_snapshot=source['id'],
        outcome={'state':'partial','stage':'fixture','reason':'synthetic Callgrind counts'},
        stages=[],regions=[],dynamic_memory=[],executions=[],raw_artifacts=[],
        reasons=['contract fixture'],gain_claim=False,per_line_memory=rows)
    profile['statement_memory']=annotation.statement_costs(persisted,source,profile)
    rel=f"region_profiles/{profile['id']}.yaml"
    records.write(rel,profile)
    sealed_digest=artifacts.digest(profile)
    table=tmp_path/f'josh-table-{kind}.md'
    scored=records.swdb('annotate-score',impl['id'],'--source-snapshot',source['id'],
        '--region-profile',profile['id'],'--table',table,'--format','json')
    assert scored.returncode==0,scored.stderr
    report=json.loads(scored.stdout)
    assert report['spearman_rank_correlation'] is None and report['top_3_overlap']==1
    assert report['statements'][0]['value']==2 and table.is_file()
    assert artifacts.digest(records.read(rel))==sealed_digest==report['region_profile_sha256']
    saved_claims=records.read('implementations/gapbs-bfs-do.yaml')
    raw.write_text(raw.read_text()+'# changed after scoring\n')
    refused=records.swdb('annotate-score',impl['id'],'--source-snapshot',source['id'],
        '--region-profile',profile['id'],'--format','json')
    assert refused.returncode==1 and 'raw hash changed' in refused.stderr
    assert records.read('implementations/gapbs-bfs-do.yaml')==saved_claims


def test_second_tdstep_collection_preserves_roi_rows_and_retains_all_workers_from_one_dump(tmp_path):
    from swdb.bfs_profiling import _memory, METRICS
    source=tmp_path/'bfs.cc'
    code='void TDStep() {\n int v = 1;\n}\n'
    source.write_text(code)
    build=tmp_path/'build';build.mkdir()
    folder=tmp_path/'run';folder.mkdir()
    graph_path=tmp_path/'graph.json';graph_path.write_text('{}')
    data={'build':{'directory':str(build)},'artifacts':{},'context':{'repetitions':1,'sources':[0],
        'threads':1,'candidate_sha256':'a'*64},'regions':[{'kind':'function','name':'TDStep',
        'path':'bfs.cc','byte_range':[0,len(code)-1],'insertion_range':[code.index('{')+1,len(code)-1]}],
        'executions':[],'dynamic_memory':[]}
    class Session:
        def __init__(self):
            self.folder=folder;self.commands=[]
        def execute(self,stage,command,budget,env=None,**kwargs):
            self.commands.append((stage,command))
            log=folder/(stage+'.stdout')
            log.write_text('valgrind-3.fixture\n')
            if stage.endswith('_build'):
                Path(command[-1]).write_text('fixture-binary '+stage)
            if stage.endswith('_execution'):
                Path(command[-1]).write_text(json.dumps({'format':'swdb.bfs.native.trial.v1','source':0,
                    'roi':'bfs.complete_call.v1','configured_threads':1,'duration_s':0.1,'parents':[0,0]}))
                raw=Path(next(c.split('=',1)[1] for c in command if c.startswith('--callgrind-out-file=')))
                header='desc: Trigger: Client Request\nevents: Ir Dr Dw D1mr D1mw DLmr DLmw\nsummary: 10 5 2 3 1 2 1\ntotals: 10 5 2 3 1 2 1\n'
                if stage=='memory_execution':
                    Path(str(raw)+'.1').write_text(header)
                else:
                    header='desc: Trigger: Client Request\nevents: Ir Dr Dw D1mr D1mw DLmr DLmw\nsummary: 30 15 6 9 3 6 3\ntotals: 30 15 6 9 3 6 3\n'
                    Path(str(raw)+'.1').write_text(header+f'fl={source}\nfn=TDStep()\n2 10 5 2 3 1 2 1\n'
                        'fn=TDStep() [clone ._omp_fn.0]\n2 10 5 2 3 1 2 1\nfn=DOBFS()\n4 10 5 2 3 1 2 1\n')
            return log
        def save(self):
            pass
    session=Session()
    _memory(session,data,{'per_line':True,'memory_model':{'collector':sys.executable}},source,[],
        sys.executable,[],graph_path,{'num_vertices':2,'adjacency':[[1],[]]}, {},
        {'build_seconds':10,'run_seconds':10})
    assert {r['metric'] for r in data['dynamic_memory']}==set(METRICS)
    assert all(r['scope']=='ROI' and r['attribution_granularity']=='whole BFS call' for r in data['dynamic_memory'])
    assert len(data['per_line_memory'])==2
    assert sum(r['events']['DLmr']+r['events']['DLmw'] for r in data['per_line_memory'])==6
    assert all(r['execution']['dump_position']==0 and 'tdstep_position' not in r['execution']
               and r['raw_artifact'].endswith('.1') for r in data['per_line_memory'])
    assert {r['function'] for r in data['per_line_memory']}=={'TDStep()','TDStep() [clone ._omp_fn.0]'}
    assert all('whole-call cache history' in r['collector']['model_limits'] for r in data['per_line_memory'])
    assert all(r['basis']=='simulated' for r in data['per_line_memory'])
    assert '-g' in data['artifacts']['statement_binary']['flags']
    assert [stage for stage,_ in session.commands].count('statement_memory_execution')==1

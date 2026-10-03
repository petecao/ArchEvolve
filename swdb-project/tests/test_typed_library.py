"""Public typed-library shape, evidence and promotion behavior. Updated: 2026-10-03 ET."""
import copy
import json
import pytest
import yaml
from conftest import run_swdb


def entry():
    return {'kind':'rewrite_contract','id':'contract.fixture',
            'provenance':{'origin':{'intrinsic_specification':'fixture-1'}},
            'clauses':[{'id':'bounds','role':'legality','statement':'Index stays in bounds.',
                        'formal':{'language':'extensa_predicate','predicate':'0 <= i < n'},
                        'formal_label':'stated','discharge_mode':'runtime_guard',
                        'negative_control':{'id':'bad-index','check':'bounds'}}],
            'pattern_key':[{'roles':['index','target'],'address_shapes':['stream','single_valued_indirect'],'update_kind':'read'}],
            'strategies':[],'uses_intrinsics':[],'uses_library_operations':[],
            'runtime_guards':[], 'knobs':[{'name':'chunk_size','default':4,'range':{'min':1,'max':8},'origin':'fixture-1','legality_clause':'bounds'}],
            'preservation_obligations':[],'correctness_check':{'kernel':'fixture','check':'fixture'},
            'execution_witness':{'check':'fixture'},'negative_controls':[
                {'id':kind,'kind':kind,'check':'fixture'} for kind in ('overlapping_pointer','double_claim','dropped_operand')],
            'requirement_map':[]}


@pytest.fixture
def library(records):
    root=records.path.parent/'library'
    folder=root/'rewrite_contracts';folder.mkdir(parents=True)
    path=folder/'fixture.yaml';path.write_text(yaml.safe_dump(entry()))
    return records,root,path


def test_library_grammar_parses_with_only_swdb_dependencies(library):
    records,root,_=library
    result=run_swdb('validate','--records',records.path,'--library',root)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('case',['proven','unknown-function','no-control','missing-kind','bad-knob','tier','collision','wrong-folder','bad-role'])
def test_invalid_library_entries_fail_public_validate(library,case):
    records,root,path=library;data=entry()
    if case=='proven': data['clauses'][0]['formal_label']='proven'
    elif case=='unknown-function': data['clauses'][0]['formal']['predicate']='system(i)'
    elif case=='no-control': data['clauses'][0]['negative_control']={'id':'none','reason':'no test'}
    elif case=='missing-kind': data['negative_controls']=data['negative_controls'][:2]
    elif case=='bad-knob': data['knobs'][0]['default']=9
    elif case=='tier': data['tier']='shared'
    elif case=='collision': records.write('reviews/collision.yaml',{'kind':'review','id':'contract.fixture'})
    elif case=='wrong-folder':
        path.unlink();path=root/'intrinsics'/'fixture.yaml';path.parent.mkdir()
    else: data['pattern_key'][0]['roles']=['VertexOffsets']
    path.write_text(yaml.safe_dump(data))
    result=run_swdb('validate','--records',records.path,'--library',root)
    assert result.returncode==1,result.stdout+result.stderr
    assert 'fixture' in result.stderr


def test_promotion_requires_current_certification_and_keeps_normative_hash(library):
    records,root,path=library
    failed=run_swdb('promote','contract.fixture','--records',records.path,'--library',root)
    assert failed.returncode==1 and 'certification' in failed.stderr
    from swdb.artifacts import digest
    sha=digest(entry())
    records.write('certifications/fixture.yaml',{'schema_version':'0.4','kind':'certification','id':'fixture-cert',
        'status':'draft','created':'2026-10-03','updated':'2026-10-03',
        'provenance':[{'id':'fixture','kind':'agent_run','description':'Isolated execution-record test double; no measured certification claim.','uri':None}],
        'entry':{'id':'contract.fixture','content_sha256':sha},'command':{'version':'fixture','sources_sha256':'0'*64},
        'host':{},'matrix':[{'status':'passed'}],'negative_controls':[{'status':'rejected'}],
        'verdict':'certified','evidence_basis':'simulated','evidence_kind':'execution'})
    before=path.read_bytes()
    result=run_swdb('promote','contract.fixture','--records',records.path,'--library',root,'--format','json')
    assert result.returncode==0,result.stderr
    assert path.read_bytes()==before
    review=json.loads(result.stdout);assert review['target']['content_sha256']==sha
    got=records.swdb('get','contract.fixture','--format','json')
    assert got.returncode==0,got.stderr
    assert json.loads(got.stdout)['tier']=='shared'
    data=entry();data['knobs'][0]['default']=5;path.write_text(yaml.safe_dump(data))
    got=records.swdb('get','contract.fixture','--format','json')
    assert got.returncode==0 and json.loads(got.stdout)['tier']=='experimental'


@pytest.mark.parametrize('reviewer', ['Unrelated reviewer', 'Contract fixture', ''])
def test_promotion_refuses_an_undesignated_reviewer(library, reviewer):
    records, root, _ = library
    result = run_swdb('promote', 'contract.fixture', '--records', records.path,
                      '--library', root, '--reviewer', reviewer)
    assert result.returncode == 1 and 'designated reviewer Yan-Ru Jhou' in result.stderr
    assert not list((records.path / 'reviews').glob('review.contract.fixture.*.yaml'))


def test_fixture_receipt_and_arbitrary_review_do_not_grant_state(library):
    from swdb.library import Library
    from swdb.store import Store, Record
    records, root, _ = library
    lib = Library(root)
    pin = {'id': 'contract.fixture', 'content_sha256': lib.content_sha256('contract.fixture')}
    certification = {'kind': 'certification', 'id': 'certification.fixture', 'entry': pin,
                     'verdict': 'certified', 'evidence_kind': 'contract_fixture'}
    review = {'kind': 'review', 'id': 'review.fixture', 'target': pin,
              'reviewer': 'Yan-Ru Jhou', 'evidence': [certification['id']]}
    def state():
        rows = [Record(str(i), row) for i, row in enumerate([certification, review])]
        return lib.state(pin['id'], Store(records.path, indexed_records=rows))
    assert state() == {'tier': 'experimental', 'status': 'draft'}
    certification['evidence_kind'] = 'execution'
    review['reviewer'] = 'Unrelated reviewer'
    assert state() == {'tier': 'experimental', 'status': 'certified'}
    review['reviewer'] = 'Yan-Ru Jhou'
    assert state() == {'tier': 'shared', 'status': 'certified'}


@pytest.mark.parametrize('changed', ['intrinsic', 'lowering'])
def test_dependency_changes_require_fresh_receipt_and_review(library, changed):
    """A contract's own hash stays fixed when nested semantics are edited."""
    from swdb.library import Library
    from swdb.store import Store, Record
    records, root, path = library
    contract = entry()
    contract['uses_intrinsics'] = ['intrinsic.fixture']
    path.write_text(yaml.safe_dump(contract))
    intrinsic = {'kind': 'intrinsic', 'id': 'intrinsic.fixture',
                 'lowerings': ['lowering.fixture'], 'intent': 'original semantics'}
    lowering = {'kind': 'lowering', 'id': 'lowering.fixture',
                'intrinsic': 'intrinsic.fixture', 'build_defines': {}}
    for folder, data in [('intrinsics', intrinsic), ('lowerings', lowering)]:
        target = root / folder / 'fixture.yaml'
        target.parent.mkdir()
        target.write_text(yaml.safe_dump(data))
    lib = Library(root)
    pin = {'id': contract['id'], 'content_sha256': lib.content_sha256(contract['id'])}
    certificate = {'kind': 'certification', 'id': 'certificate.original', 'entry': pin,
                   'dependencies': lib.dependency_pins(contract['id']),
                   'verdict': 'certified', 'evidence_kind': 'execution'}
    review = {'kind': 'review', 'id': 'review.original', 'target': pin,
              'reviewer': 'Yan-Ru Jhou', 'evidence': [certificate['id']]}
    rows = [certificate, review]
    def state():
        store = Store(records.path, indexed_records=[Record(str(i), row) for i, row in enumerate(rows)])
        return Library(root).state(contract['id'], store)
    assert state() == {'tier': 'shared', 'status': 'certified'}
    edited = intrinsic if changed == 'intrinsic' else lowering
    edited['intent'] = 'changed semantics'
    folder = 'intrinsics' if changed == 'intrinsic' else 'lowerings'
    (root / folder / 'fixture.yaml').write_text(yaml.safe_dump(edited))
    lib = Library(root)
    assert lib.content_sha256(contract['id']) == pin['content_sha256']
    assert state() == {'tier': 'experimental', 'status': 'draft'}
    fresh = dict(certificate, id='certificate.fresh', dependencies=lib.dependency_pins(contract['id']))
    rows.append(fresh)
    assert state() == {'tier': 'experimental', 'status': 'certified'}
    rows.append(dict(review, id='review.fresh', evidence=[fresh['id']]))
    assert state() == {'tier': 'shared', 'status': 'certified'}
    assert [row['id'] for row in lib.dependency_pins(intrinsic['id'])] == [lowering['id']]
    assert [row['id'] for row in lib.dependency_pins(lowering['id'])] == [intrinsic['id']]
    unbound = dict(fresh)
    unbound.pop('dependencies')
    assert not lib.current_certification(unbound)


@pytest.mark.parametrize('field,value',[('clauses',42),('knobs',{}),('pattern_key',[42]),('uses_intrinsics',[{}]),('provenance',[])])
def test_malformed_types_fail_without_a_traceback(library,field,value):
    records,root,path=library;data=entry();data[field]=value;path.write_text(yaml.safe_dump(data))
    result=run_swdb('validate','--records',records.path,'--library',root)
    assert result.returncode==1,result.stderr
    assert 'Traceback' not in result.stderr


@pytest.mark.parametrize('bounds',[{'min':{},'max':8},{'choices':42},{'min':False,'max':True}])
def test_malformed_knob_bounds_fail_without_traceback(library,bounds):
    records,root,path=library;data=entry();data['knobs'][0]['range']=bounds
    path.write_text(yaml.safe_dump(data))
    result=run_swdb('validate','--records',records.path,'--library',root)
    assert result.returncode==1 and 'Traceback' not in result.stderr


@pytest.mark.parametrize('case,expected',[
    ('native','draft'),('fixture','draft'),('no-exit','refuted'),
    ('no-witness','refuted'),('incomplete','inconclusive'),('complete','evaluated_on_target'),
    ('l3-violation','refuted'),('positive-and-refuted','refuted')])
def test_target_status_requires_real_target_completion_and_witness(library,case,expected):
    from swdb.library import Library
    from swdb.store import Store,Record
    records,root,path=library;data=entry()
    data['execution_witness']={'gem5':{'case':'read_only_executed'}}
    path.write_text(yaml.safe_dump(data));lib=Library(root)
    pin={'id':'contract.fixture','content_sha256':lib.content_sha256('contract.fixture')}
    check={'passed':True,'continuation':{'normal_exit_observed':True},
           'coverage':{'read_only_executed':{'state':'observed'}}}
    evaluation={'kind':'evaluation','id':'evaluation.fixture','candidate':'candidate.fixture',
        'evidence_kind':'execution','context':{'target':'target.fixture','backend':'dx100-gem5-se','candidate_sha256':'a'*64},
        'correctness':{'state':'passed','checks':[check]},'outcome':{'state':'complete','stage':'execution'},
        'stages':[{'stage':'simulation','state':'complete'}]}
    if case=='native': evaluation['context']['backend']='bfs-native'
    elif case=='fixture': evaluation['evidence_kind']='contract_fixture'
    elif case=='no-exit': check['continuation']['normal_exit_observed']=False
    elif case=='no-witness': check['coverage']={}
    elif case=='incomplete':
        evaluation['outcome']={'state':'timed_out','stage':'simulation'}
        evaluation['stages'][0]['state']='timed_out';check['coverage']={}
    elif case=='l3-violation': check['parent_gather_race']={'outcome':'refuted'}
    rows=[{'kind':'hardware_target','id':'target.fixture','backend':{'id':'dx100-gem5-se'}},
          {'kind':'candidate','id':'candidate.fixture','proposal':'proposal.fixture','artifact':{'sha256':'a'*64}},
          {'kind':'proposal','id':'proposal.fixture','request':{'library':{'contract':pin,'entries':[]}}},evaluation]
    if case == 'positive-and-refuted':
        refuted = copy.deepcopy(evaluation)
        refuted['id'] = 'evaluation.refuted'
        refuted['correctness']['checks'][0]['coverage'] = {'read_only_executed': {'state': 'unobserved'}}
        rows.append(refuted)
    store=Store(records.path,indexed_records=[Record(str(i),row) for i,row in enumerate(rows)])
    assert lib.state('contract.fixture',store)['status']==expected


@pytest.mark.parametrize('changed', ['witness', 'dependency'])
def test_target_status_cannot_reinterpret_a_stale_contract(library, changed):
    from swdb.library import Library
    from swdb.store import Store, Record
    records, root, _ = library
    lib = Library(root)
    lib.entries['intrinsic.fixture'] = {'kind': 'intrinsic', 'id': 'intrinsic.fixture',
                                        'lowerings': ['lowering.fixture']}
    lib.entries['lowering.fixture'] = {'kind': 'lowering', 'id': 'lowering.fixture',
                                      'intrinsic': 'intrinsic.fixture'}
    contract = lib.entries['contract.fixture']
    contract['uses_intrinsics'] = ['intrinsic.fixture']
    contract['execution_witness'] = {'gem5': {'case': 'read_only_executed'}}
    contract_pin = {'id': contract['id'], 'content_sha256': lib.content_sha256(contract['id'])}
    rows = [
        {'kind': 'hardware_target', 'id': 'target.fixture', 'backend': {'id': 'dx100-gem5-se'}},
        {'kind': 'candidate', 'id': 'candidate.fixture', 'proposal': 'proposal.fixture', 'artifact': {'sha256': 'a' * 64}},
        {'kind': 'proposal', 'id': 'proposal.fixture', 'request': {'library': {
            'contract': contract_pin, 'entries': lib.dependency_pins(contract['id'])}}},
        {'kind': 'evaluation', 'id': 'evaluation.fixture', 'candidate': 'candidate.fixture',
         'evidence_kind': 'execution', 'context': {'target': 'target.fixture', 'backend': 'dx100-gem5-se', 'candidate_sha256': 'a' * 64},
         'outcome': {'state': 'complete', 'stage': 'execution'},
         'stages': [{'stage': 'simulation', 'state': 'complete'}],
         'correctness': {'state': 'passed', 'checks': [
             {'passed': True, 'continuation': {'normal_exit_observed': True},
              'coverage': {'isolation_probe_witness': {'state': 'observed'}}}]}}]
    store = Store(records.path, indexed_records=[Record(str(i), row) for i, row in enumerate(rows)])
    assert lib.state('lowering.fixture', store)['status'] == 'refuted'
    if changed == 'witness':
        contract['execution_witness']['gem5']['case'] = 'isolation_probe_witness'
    else:
        # The lowering subject remains fixed while its intrinsic dependency changes.
        lib.entries['intrinsic.fixture']['intent'] = 'changed semantics'
    assert lib.state('lowering.fixture', store) == {'tier': 'experimental', 'status': 'draft'}


@pytest.fixture(scope='module')
def public_preparation_state_records():
    """Published prepare/build receipts; no remote execution. Updated: 2026-10-03 ET."""
    from swdb import paths
    from swdb.store import Store
    store = Store(paths.RECORDS)
    run = 'typed-library-bfs-gem5-20261003-a1'
    builds = [store.get(run + '.' + name + '.build', 'evaluation') for name in
              ('baseline.primary', 'candidate.primary', 'candidate.diagnostic')]
    assert all(builds)
    proposal = store.get(run + '.proposal', 'proposal')
    candidate = store.get(run + '.proposal.candidate-1', 'candidate')
    execution = store.get('bfs-t17-ac10-companion-20260928-a3.execute', 'evaluation')
    checkpoint = store.get('bfs-dx100-smoke-20260925-a3', 'evaluation')
    assert proposal and candidate and execution and checkpoint
    # Keep the actual certification/review/proposal identities, and isolate
    # target-state derivation from unrelated historical evaluations.
    records = [row.data for row in store.records if row.data['kind'] != 'evaluation']
    return records, builds, proposal['request']['library'], candidate, execution, checkpoint


@pytest.mark.parametrize('case', ['prepare', 'failed-compile', 'discovery', 'collection', 'package'])
def test_public_preparation_processes_do_not_establish_target_state(public_preparation_state_records, case):
    from swdb import paths
    from swdb.library import Library
    from swdb.store import Store, Record
    records, published_builds, section, _, _, _ = public_preparation_state_records
    builds = copy.deepcopy(published_builds)
    if case != 'prepare':
        build = builds[1]
        build['provenance'] = [{'id': 'test-double', 'kind': 'agent_run', 'uri': None,
                               'description': 'Isolated non-execution state test double copied from a public build.'}]
        stage = 'candidate_compile' if case == 'failed-compile' else case
        state = 'failed' if case == 'failed-compile' else 'complete'
        build['outcome'] = {'state': state, 'stage': stage, 'reason': 'Isolated process-stage regression.'}
        build['stages'] = [{'stage': stage, 'state': state}]
        # Even apparent correctness cannot confer target status without a run.
        build['correctness'] = {'state': 'failed' if case == 'discovery' else 'passed', 'checks': [
            {'passed': True, 'continuation': {'normal_exit_observed': True},
             'coverage': {'read_only_executed': {'state': 'observed'}}}]}
    store = Store(paths.RECORDS, indexed_records=[Record(str(i), row)
                  for i, row in enumerate(records + builds)])
    lib = Library(paths.HOME / 'library', store)
    cited = [section['contract']] + section['entries']
    assert cited
    assert {pin['id']: lib.state(pin['id']) for pin in cited} == {
        pin['id']: {'tier': 'shared', 'status': 'certified'} for pin in cited}


@pytest.mark.parametrize('case,expected', [('observed', 'evaluated_on_target'),
    ('missing-witness', 'refuted'), ('failed-witness', 'refuted'),
    ('no-normal-exit', 'refuted'), ('no-correctness', 'refuted'),
    ('timed-out', 'inconclusive'), ('running', 'inconclusive')])
def test_public_execution_stage_retains_witness_and_completion_rules(public_preparation_state_records, case, expected):
    from swdb import paths
    from swdb.library import Library
    from swdb.store import Store, Record
    records, builds, section, candidate, published_execution, _ = public_preparation_state_records
    execution = copy.deepcopy(published_execution)
    assert any(stage['stage'] == 'simulation' for stage in execution['stages'])
    execution['provenance'] = [{'id': 'test-double', 'kind': 'agent_run', 'uri': None,
                              'description': 'Isolated target-state test double copied from a public companion execution.'}]
    execution['id'] = 'evaluation.target-state-test-double'
    execution['candidate'] = candidate['id']
    execution['context']['candidate_sha256'] = candidate['artifact']['sha256']
    check = execution['correctness']['checks'][0]
    check['execution'] = execution['id']
    assert execution['outcome']['state'] == 'complete' and execution['correctness']['state'] == 'passed'
    assert check['passed']
    # This public companion has a valid bounded v2 exit witness. Its unchanged
    # normal-exit flag is false; a missing witness cannot replace that proof.
    assert check['continuation']['normal_exit_observed'] is False
    if case == 'no-normal-exit':
        check['continuation'].pop('exit_witness')
    check['coverage']['read_only_executed'] = {'state': 'observed'}
    if case == 'missing-witness':
        del check['coverage']['read_only_executed']
    elif case == 'failed-witness':
        check['coverage']['read_only_executed']['state'] = 'unobserved'
    elif case == 'no-correctness':
        execution['correctness'] = {'state': 'unverified', 'checks': []}
    elif case in {'timed-out', 'running'}:
        state = 'timed_out' if case == 'timed-out' else 'running'
        execution['outcome'] = {'state': state, 'stage': 'simulation', 'reason': 'Isolated incomplete execution.'}
        execution['correctness'] = {'state': 'unverified', 'checks': []}
        simulation = next(stage for stage in execution['stages'] if stage['stage'] == 'simulation')
        simulation['state'] = state
    store = Store(paths.RECORDS, indexed_records=[Record(str(i), row)
                  for i, row in enumerate(records + builds + [execution])])
    lib = Library(paths.HOME / 'library', store)
    cited = [section['contract']] + section['entries']
    assert {pin['id']: lib.state(pin['id'])['status'] for pin in cited} == {
        pin['id']: expected for pin in cited}


@pytest.mark.parametrize('case', ['retained-failure', 'running', 'checkpoint-complete'])
def test_public_checkpoint_guest_attempt_remains_inconclusive(public_preparation_state_records, case):
    """A real guest starts before timed simulation. Updated: 2026-10-03 ET."""
    from swdb import paths
    from swdb.library import Library
    from swdb.store import Store, Record
    records, builds, section, candidate, _, published_checkpoint = public_preparation_state_records
    assert published_checkpoint['outcome']['stage'] == 'checkpoint'
    assert published_checkpoint['outcome']['state'] == 'missing_observation'
    assert 'checkpoint' in {stage['stage'] for stage in published_checkpoint['stages']}
    assert not {'simulation', 'execution'} & {stage['stage'] for stage in published_checkpoint['stages']}
    execution = copy.deepcopy(published_checkpoint)
    execution['provenance'] = [{'id': 'test-double', 'kind': 'agent_run', 'uri': None,
                              'description': 'Isolated target-state test double copied from a public failed checkpoint guest attempt.'}]
    execution['id'] = 'evaluation.checkpoint-state-test-double'
    execution['candidate'] = candidate['id']
    execution['context']['candidate_sha256'] = candidate['artifact']['sha256']
    if case != 'retained-failure':
        state = 'running' if case == 'running' else 'complete'
        execution['outcome'] = {'state': state, 'stage': 'checkpoint', 'reason': None}
        checkpoint = next(stage for stage in execution['stages'] if stage['stage'] == 'checkpoint')
        checkpoint['state'] = state
        # Apparent positive checks still cannot qualify a checkpoint as the
        # required timed execution or establish its accelerator witness.
        if case == 'checkpoint-complete':
            execution['correctness'] = {'state': 'passed', 'checks': [
                {'passed': True, 'continuation': {'normal_exit_observed': True},
                 'coverage': {'read_only_executed': {'state': 'observed'}}}]}
    store = Store(paths.RECORDS, indexed_records=[Record(str(i), row)
                  for i, row in enumerate(records + builds + [execution])])
    lib = Library(paths.HOME / 'library', store)
    cited = [section['contract']] + section['entries']
    assert {pin['id']: lib.state(pin['id']) for pin in cited} == {
        pin['id']: {'tier': 'shared', 'status': 'inconclusive'} for pin in cited}


@pytest.fixture
def bounded_v2_target(library, tmp_path):
    """Real parser/seal artifacts in an isolated fixture, not measured evidence."""
    from test_dx100_witness import evaluation
    from swdb.library import Library
    records, root, path = library
    contract = entry()
    contract['execution_witness'] = {'gem5': {'case': 'read_only_executed'}}
    path.write_text(yaml.safe_dump(contract))
    lib = Library(root)
    pin = {'id': contract['id'], 'content_sha256': lib.content_sha256(contract['id'])}
    data = evaluation(tmp_path)
    data.update(kind='evaluation', candidate='candidate.fixture', evidence_kind='execution',
                provenance=[{'id': 'test-double', 'kind': 'agent_run', 'uri': None,
                             'description': 'Isolated v2 parser/seal target-state test double.'}])
    data['context'].update(target='target.fixture', backend='dx100-gem5-se',
                           candidate_sha256='a' * 64)
    data['build']['adapter'] = 'dx100.complete_call.v2'
    data['correctness']['checks'][0]['coverage'] = {'read_only_executed': {'state': 'observed'}}
    rows = [
        {'kind': 'hardware_target', 'id': 'target.fixture', 'backend': {'id': 'dx100-gem5-se'}},
        {'kind': 'candidate', 'id': 'candidate.fixture', 'proposal': 'proposal.fixture',
         'artifact': {'sha256': 'a' * 64}},
        {'kind': 'proposal', 'id': 'proposal.fixture', 'request': {
            'library': {'contract': pin, 'entries': []}}}]
    return records, lib, data, rows


def bounded_v2_state(fixture, evaluations):
    from swdb.store import Store, Record
    records, lib, _, rows = fixture
    store = Store(records.path, indexed_records=[Record(str(i), row)
                  for i, row in enumerate(rows + evaluations)])
    return lib.state('contract.fixture', store)['status']


@pytest.mark.parametrize('normal', [False, True])
def test_v2_target_completion_uses_exact_sealed_exit_evidence(bounded_v2_target, normal):
    from pathlib import Path
    from swdb.artifacts import file_hash
    fixture = bounded_v2_target
    data = fixture[2]
    check = data['correctness']['checks'][0]
    if normal:
        continuation = check['continuation']
        continuation.update(normal_exit_observed=True, stop_reason='normal_exit',
                            exit_cause='exiting with last active thread context')
        seal = data['context']['sealed_roi']
        Path(seal['path']).write_text(json.dumps({key: value for key, value in seal.items()
                                               if key not in {'path', 'sha256'}}))
        seal['sha256'] = check['sealed_roi']['sha256'] = file_hash(seal['path'])
    assert bounded_v2_state(fixture, [data]) == 'evaluated_on_target'


@pytest.mark.parametrize('case', [
    'missing-witness', 'incomplete-witness', 'nonzero-exit', 'wrong-execution',
    'wrong-source', 'wrong-parser', 'wrong-binding', 'failed-process',
    'missing-coverage', 'refuted-l3', 'request-checker', 'context-checker',
    'check-checker', 'continuation-checker', 'contradictory-normal',
    'changed-trace', 'changed-output', 'changed-seal', 'naked-completed-flag'])
def test_invalid_v2_completion_cannot_fall_back_to_normal_exit_flags(bounded_v2_target, case):
    from pathlib import Path
    fixture = bounded_v2_target
    data = fixture[2]
    check = data['correctness']['checks'][0]
    continuation = check['continuation']
    if case == 'missing-witness':
        continuation.pop('exit_witness')
    elif case == 'incomplete-witness':
        continuation['exit_witness']['completed'] = False
    elif case == 'nonzero-exit':
        continuation['exit_witness']['exit_request']['status'] = 1
    elif case == 'wrong-execution':
        check['execution'] = 'another-execution'
    elif case == 'wrong-source':
        check['source'] = 1
    elif case == 'wrong-parser':
        data['context']['verification_parser']['sha256'] = '0' * 64
    elif case == 'wrong-binding':
        data['context']['execution_binding_sha256'] = '0' * 64
    elif case == 'failed-process':
        data['stages'][0].update(state='failed', returncode=1)
    elif case == 'missing-coverage':
        check['coverage'] = {}
    elif case == 'refuted-l3':
        check['parent_gather_race'] = {'outcome': 'refuted'}
    elif case == 'request-checker':
        data['request']['verification']['checker'] = 'dx100.bfs.verifier.v1'
    elif case == 'context-checker':
        data['context']['verifier'] = 'dx100.bfs.verifier.v1'
    elif case == 'check-checker':
        check['checker'] = 'dx100.bfs.verifier.v1'
    elif case == 'continuation-checker':
        continuation['checker'] = 'dx100.bfs.verifier.v1'
    elif case == 'contradictory-normal':
        continuation['normal_exit_observed'] = True
    elif case.startswith('changed-'):
        reference = {'changed-trace': data['context']['post_roi_trace'],
                     'changed-output': check['output'],
                     'changed-seal': data['context']['sealed_roi']}[case]
        with Path(reference['path']).open('a') as stream:
            stream.write('Changed retained bytes.\n')
    else:
        check['continuation'] = {'normal_exit_observed': True,
                                 'exit_witness': {'completed': True}}
    assert bounded_v2_state(fixture, [data]) == 'refuted'


@pytest.mark.parametrize('case,expected', [
    ('wrapper-only', 'draft'), ('actual-component', 'evaluated_on_target'),
    ('malformed-wrapper', 'evaluated_on_target'), ('refuted-component', 'refuted')])
def test_aggregation_wrapper_cannot_invent_another_target_execution(bounded_v2_target, case, expected):
    from swdb.artifacts import digest
    fixture = bounded_v2_target
    component = fixture[2]
    wrapper = copy.deepcopy(component)
    wrapper['id'] = 'aggregate.fixture'
    wrapper['component_evaluations'] = [{'evaluation': component['id'], 'sha256': digest(component)}]
    wrapper['outcome']['stage'] = 'aggregation'
    wrapper['stages'][0]['component_evaluation'] = component['id']
    if case == 'malformed-wrapper':
        wrapper['component_evaluations'][0]['sha256'] = '0' * 64
        wrapper['correctness']['checks'][0]['continuation']['exit_witness']['completed'] = False
    elif case == 'refuted-component':
        component['correctness']['checks'][0]['coverage'] = {}
    evaluations = [wrapper] if case == 'wrapper-only' else [component, wrapper]
    assert bounded_v2_state(fixture, evaluations) == expected

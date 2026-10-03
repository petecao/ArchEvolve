"""Public typed-library shape, evidence and promotion behavior. Created: 2026-10-03."""
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
        'correctness':{'state':'passed','checks':[check]},'outcome':{'state':'complete'}}
    if case=='native': evaluation['context']['backend']='bfs-native'
    elif case=='fixture': evaluation['evidence_kind']='contract_fixture'
    elif case=='no-exit': check['continuation']['normal_exit_observed']=False
    elif case=='no-witness': check['coverage']={}
    elif case=='incomplete':
        evaluation['outcome']['state']='incomplete';check['coverage']={}
    elif case=='l3-violation': check['parent_gather_race']={'outcome':'refuted'}
    rows=[{'kind':'hardware_target','id':'target.fixture','backend':{'id':'dx100-gem5-se'}},
          {'kind':'candidate','id':'candidate.fixture','proposal':'proposal.fixture','artifact':{'sha256':'a'*64}},
          {'kind':'proposal','id':'proposal.fixture','request':{'library':{'contract':pin,'entries':[]}}},evaluation]
    if case == 'positive-and-refuted':
        import copy
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
         'outcome': {'state': 'complete'}, 'correctness': {'state': 'passed', 'checks': [
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

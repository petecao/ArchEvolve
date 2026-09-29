"""Reassessment admission and orchestration contracts; no empirical evidence.

Created: 2026-09-26 (Eastern Time). Metadata execution labels below are synthetic.
"""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import bfs_native_campaign as campaign
from swdb import artifacts, bfs_native, bfs_protocol, profile_package
from swdb.cli import Failure
from test_bfs_native_campaign import inputs as admission_inputs, seal, seal_package
from test_bfs_campaign_reuse import reuse_case, reuse_seed


def pin(record):
    return {'id': record['id'], 'sha256': artifacts.digest(record)}


@pytest.fixture
def case(admission_inputs):
    _, packages, frozen, proposal, records, lane, expected = admission_inputs
    source = records['source']; root = Path(source['artifact']['path'])
    text = (root/'source.cc').read_text()
    region = {'id':'fixture-function','kind':'function','path':'source.cc','byte_range':[0,len(text.encode())],
              'text':text,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'lines':[1,1]}
    protections = [{'path':'source.cc','kind':'file','sha256':artifacts.file_hash(root/'source.cc')}]
    source.update(kind='source_snapshot',application='fixture-application',revision='a'*40,protections=protections)
    source['context'].update(application='fixture-application',source={'commit':'a'*40})
    records['baseline'].update(protections=copy.deepcopy(protections),context=copy.deepcopy(source['context']))
    historic = []
    for index,package in enumerate(packages):
        primary = records[package['evaluation']]
        primary['build'].update(compiler='/fixture/c++',compiler_version=['fixture compiler'],flags=['-O3'],
            template_sha256='c'*64,wrapper_sha256='d'*64,execution_environment=bfs_native.controlled_environment(4))
        primary['build'].pop('native_runtime')  # Original records never observed inherited variables.
        primary['context']['function']='DOBFS'
        primary['context']['workload'].update(adjacency_order_sha256='a'*64,canonical_file_sha256='e'*64)
        package.update(regions=[copy.deepcopy(region)],region_profile='fixture-profile-'+str(index),
                       context={**profile_package._context(primary),'build':copy.deepcopy(primary['build']),
                                'workload':copy.deepcopy(primary['context']['workload']),
                                'primary_binary_sha256':primary['build']['binary_sha256']})
        package['evidence']['evaluation_sha256']=artifacts.digest(primary)
        old=copy.deepcopy(package);old['requested_id']='origin-'+package['requested_id']
        seal_package(old);historic.append(old);records[old['id']]=old
        fresh=copy.deepcopy(primary);fresh['id']='fresh-'+primary['id'];fresh['context']['threads']=1
        fresh['build']['native_runtime']={'version':1,'environment':{**bfs_native.controlled_environment(1),
                                                                  **dict.fromkeys(bfs_native.RUNTIME_INHERITED)}}
        fresh['build']['execution_environment']=bfs_native.controlled_environment(1)
        records[fresh['id']]=fresh
        snapshot=copy.deepcopy(source);snapshot['id']='fresh-source-'+str(index);records[snapshot['id']]=snapshot
        package.update(evaluation=fresh['id'],source_snapshot=snapshot['id'],
            context={**profile_package._context(fresh),'build':copy.deepcopy(fresh['build']),
                     'workload':copy.deepcopy(fresh['context']['workload']),
                     'primary_binary_sha256':fresh['build']['binary_sha256']})
        package['evidence']['evaluation_sha256']=artifacts.digest(fresh)
        seal_package(package);records[package['id']]=package
    settings=copy.deepcopy(frozen['settings']);settings.update(threads=1,sampling={},native_runtime=copy.deepcopy(records[packages[0]['evaluation']]['build']['native_runtime']))
    frozen=seal('protocol','fresh-policy',settings=settings,workload_identities=frozen['workload_identities'],
                frozen_at='2026-09-26T20:00:00-04:00',state='frozen');records[frozen['id']]=frozen
    proposal.update(profile_package=historic[0]['id'],regions=[region['id']],intent='Preserve the exact original fixture intent.',
        constraints={'editable_files':['source.cc'],'preserve_correctness':True,'preserve_roi':True},
        payload={'kind':'patch','content':'original supplied fixture patch'})
    submitted={'id':proposal['id'],'kind':'proposal','request':copy.deepcopy(proposal),
               'candidate':proposal['id']+'.candidate-1','outcome':{'state':'candidate_created'},'repair_budget':None}
    candidate={'id':submitted['candidate'],'kind':'candidate','source_snapshot':source['id'],'fixture_only':True}
    records[submitted['id']]=submitted;records[candidate['id']]=candidate
    manifest={'version':1,'kind':'native_candidate_reassessment',
        'origin':{'proposal':pin(submitted),'candidate':pin(candidate),'profile_package':pin(historic[0]),
                  'source_snapshot':pin(source),'request_sha256':artifacts.digest(proposal),
                  'baseline_packages':[pin(row) for row in historic]},
        'assessment':{'protocol':pin(frozen),'packages':[pin(row) for row in packages]},
        'transition':{'from_threads':4,'to_threads':1,'native_runtime':copy.deepcopy(settings['native_runtime'])}}
    return SimpleNamespace(manifest=manifest,proposal=proposal,candidate=candidate,submitted=submitted,
        packages=packages,historic=historic,frozen=frozen,records=records,lane=lane,expected=expected,source=source)


def validate(case):
    return campaign.validate_reassessment(case.manifest,case.proposal,case.candidate['id'],case.packages,
        case.frozen,case.records.__getitem__,case.lane,case.expected)


def reseal(case):
    """Adversarially reseal metadata copies; semantic mismatches must still reject."""
    for package in case.packages+case.historic:
        previous_id=package['id']
        primary=case.records[package['evaluation']]
        package['context'].update(profile_package._context(primary))
        package['context'].update(build=copy.deepcopy(primary['build']),workload=copy.deepcopy(primary['context']['workload']),
                                  primary_binary_sha256=primary['build']['binary_sha256'])
        package['evidence']['evaluation_sha256']=artifacts.digest(primary)
        seal_package(package)
        case.records.pop(previous_id,None);case.records[package['id']]=package
    case.proposal['profile_package']=case.historic[0]['id']
    case.submitted['request']=copy.deepcopy(case.proposal)
    origin=case.manifest['origin']
    for kind,record in [('proposal',case.submitted),('candidate',case.candidate),
                        ('profile_package',case.historic[0]),('source_snapshot',case.source)]:origin[kind]=pin(record)
    origin['baseline_packages']=[pin(row) for row in case.historic]
    origin['request_sha256']=artifacts.digest(case.proposal)
    case.manifest['assessment']['packages']=[pin(row) for row in case.packages]


def test_explicit_transition_keeps_unknown_origin_inputs_unknown_and_does_not_mutate_records(case):
    before=copy.deepcopy((case.records,case.proposal,case.manifest))
    rows,receipt=validate(case)
    assert set(rows)=={'kronecker','uniform_random'}
    for evidence in receipt['origin_runtime_evidence'].values():
        assert evidence['policy'] is None and set(evidence['unobserved'])==set(bfs_native.RUNTIME_INHERITED)
        assert evidence['controlled']['OMP_NUM_THREADS']=='4'
    assert receipt['transition']['native_runtime']['environment']['OMP_NUM_THREADS']=='1'
    assert receipt['gain_claim'] is receipt['provider_calls'] is receipt['repair_calls'] is False
    assert (case.records,case.proposal,case.manifest)==before
    with pytest.raises(ValueError,match='first supplied package'):
        campaign.validate_inputs(case.packages,case.frozen,case.proposal,case.records.__getitem__,case.lane,case.expected)


@pytest.mark.parametrize('fault',['version_bool','version_float','extra','missing','from_bool','from_other','to_bool',
    'runtime_bool','runtime_active','runtime_missing','origin_digest','fresh_digest','protocol_digest',
    'request_digest','package_order','origin_package_omitted','history_duplicate'])
def test_manifest_shape_and_all_explicit_bindings_fail_closed(case,fault):
    manifest=case.manifest
    if fault.startswith('version_'):manifest['version']=True if fault=='version_bool' else 1.0
    elif fault=='extra':manifest['ignored']=True
    elif fault=='missing':manifest.pop('origin')
    elif fault=='from_bool':manifest['transition']['from_threads']=True
    elif fault=='from_other':manifest['transition']['from_threads']=2
    elif fault=='to_bool':manifest['transition']['to_threads']=True
    elif fault=='runtime_bool':manifest['transition']['native_runtime']['version']=True
    elif fault=='runtime_active':manifest['transition']['native_runtime']['environment']['OMP_WAIT_POLICY']='ACTIVE'
    elif fault=='runtime_missing':manifest['transition']['native_runtime']['environment'].pop('GOMP_SPINCOUNT')
    elif fault=='origin_digest':manifest['origin']['candidate']['sha256']='0'*64
    elif fault=='fresh_digest':manifest['assessment']['packages'][1]['sha256']='0'*64
    elif fault=='protocol_digest':manifest['assessment']['protocol']['sha256']='0'*64
    elif fault=='request_digest':manifest['origin']['request_sha256']='0'*64
    elif fault=='package_order':manifest['assessment']['packages'].reverse()
    elif fault=='origin_package_omitted':manifest['origin']['baseline_packages'].pop(0)
    else:manifest['origin']['baseline_packages'][1]=manifest['origin']['baseline_packages'][0]
    with pytest.raises((ValueError,Failure)):validate(case)


@pytest.mark.parametrize('fault',['source_manifest','protections','application','function','source_context',
    'missing_region','region_extent','region_hash','compiler','flags','binary','graph','historical_graph',
    'fresh_runtime','fresh_runtime_bool','fresh_controlled','fresh_entry','old_controlled','old_inherited','old_runtime_bool','old_runtime_null','old_fixture'])
def test_resealed_semantic_or_runtime_changes_are_not_silently_reassessed(case,fault):
    package=case.packages[1];primary=case.records[package['evaluation']]
    snapshot=case.records[package['source_snapshot']];old=case.records[case.historic[1]['evaluation']]
    if fault=='source_manifest':snapshot['artifact']['files'][0]['bytes']+=1
    elif fault=='protections':snapshot['protections']=[]
    elif fault=='application':snapshot['application']='another'
    elif fault=='function':snapshot['context']['function']='Another'
    elif fault=='source_context':snapshot['context']['source']['commit']='f'*40
    elif fault=='missing_region':package['regions']=[]
    elif fault=='region_extent':package['regions'][0]['byte_range'][1]-=1
    elif fault=='region_hash':package['regions'][0]['source_sha256']='0'*64
    elif fault=='compiler':primary['build']['compiler']='/another/compiler'
    elif fault=='flags':primary['build']['flags']=['-O0']
    elif fault=='binary':primary['build']['binary_sha256']='0'*64
    elif fault=='graph':primary['context']['workload']['adjacency_order_sha256']='0'*64
    elif fault=='historical_graph':old['context']['workload']['id']=case.records[case.historic[0]['evaluation']]['context']['workload']['id']
    elif fault=='fresh_runtime':primary['build']['native_runtime']['environment']['OMP_THREAD_LIMIT']='1'
    elif fault=='fresh_runtime_bool':primary['build']['native_runtime']['version']=True
    elif fault=='fresh_controlled':primary['build']['execution_environment']['OMP_NUM_THREADS']='4'
    elif fault=='fresh_entry':primary['context']['function']='Another'
    elif fault=='old_controlled':old['build']['execution_environment']['OMP_PLACES']='threads'
    elif fault in {'old_inherited','old_runtime_bool'}:
        old['build']['native_runtime']={'version':1,'environment':{**bfs_native.controlled_environment(4),**dict.fromkeys(bfs_native.RUNTIME_INHERITED)}}
        if fault=='old_inherited':old['build']['native_runtime']['environment']['OMP_WAIT_POLICY']='ACTIVE'
        else:old['build']['native_runtime']['version']=True
    elif fault=='old_runtime_null':old['build']['native_runtime']=None
    else:old['request']['fixture']=True
    reseal(case)
    with pytest.raises((ValueError,Failure)):validate(case)


@pytest.mark.parametrize('fault',['without_candidate','provider','repair'])
def test_reassessment_options_reject_before_any_public_call(reuse_case,tmp_path,fault):
    worker=reuse_case.worker;worker.args.reassessment=tmp_path/'unused.json'
    if fault=='without_candidate':worker.args.existing_candidate=None
    else:setattr(worker.args,fault+'_config',tmp_path/'never-read.json')
    with pytest.raises(ValueError,match='reassessment'):worker.acquire_candidate(reuse_case.request)
    assert worker.receipt['stages']==[]


def test_reassessment_acquisition_still_uses_actual_public_gets_and_exact_patch_replay(reuse_case,tmp_path):
    case=reuse_case;case.worker.args.reassessment=tmp_path/'manifest-read-by-run.json'
    before=artifacts.digest(case.proposal)
    result=case.worker.acquire_candidate(case.request)
    assert artifacts.digest(result)==before
    assert case.worker.receipt['candidate_acquisition']['patch_binding']['candidate_sha256']==case.candidate['artifact']['sha256']
    assert {row['command'][3] for row in case.worker.receipt['stages'] if row['command'][1:3]==['-m','swdb']}=={'get'}
    assert list(case.worker.args.source_runs_dir.iterdir())==[]


def test_build_failure_in_reassessment_does_not_submit_repair_or_reset_origin_budget(case,tmp_path,monkeypatch):
    args=SimpleNamespace(id='fixture-reassessment',protocol=case.frozen['id'],packages=[row['id'] for row in case.packages],
        proposal=tmp_path/'proposal.json',reassessment=tmp_path/'manifest.json',existing_candidate=case.candidate['id'],
        provider_config=None,repair_config=None,records=tmp_path/'records',lane=case.lane,source_runs_dir=tmp_path/'sources')
    args.proposal.write_text(json.dumps(case.proposal));args.reassessment.write_text(json.dumps(case.manifest))
    worker=campaign.Driver.__new__(campaign.Driver);worker.args=args;worker.folder=tmp_path
    worker.receipt={'families':{},'candidate_rounds':[],'repair_attempts':[]};worker.save=lambda:None
    calls=[]
    def call(command,rid,*args,**kwargs):
        calls.append(command);assert command=='get'
        return case.records.get(rid,{})
    worker.call=call
    monkeypatch.setattr(campaign.bfs_protocol,'_validate_settings',lambda *args:None)  # Minimal synthetic protocol fixture.
    case.frozen['settings']['sampling']={};case.manifest['assessment']['protocol']=pin(case.frozen)
    args.reassessment.write_text(json.dumps(case.manifest))
    monkeypatch.setattr(campaign.artifacts,'source_root',lambda *args:Path(case.expected['path']))
    monkeypatch.setattr(campaign.subprocess,'check_output',lambda *args,**kwargs:'fixture-code\n')
    budget={'max_repairs':2,'total_seconds':1800,'used_seconds':62.419636563397944,'repairs':0}
    def acquire(proposal):
        origin=case.manifest['origin'];worker.receipt['candidate_acquisition']={'repair_budget':copy.deepcopy(budget)}
        for kind in ('proposal','candidate','profile_package','source_snapshot'):
            worker.receipt['candidate_acquisition'].update({kind:origin[kind]['id'],kind+'_sha256':origin[kind]['sha256']})
        return case.submitted
    worker.acquire_candidate=acquire  # Public acquisition and replay are exercised separately above.
    worker.evaluate=lambda name,*args:{'id':name,'outcome':{'state':'failed','stage':'build'},'correctness':{'state':'unverified'}}
    worker.collect=lambda *args:None
    def request(command,value,*args,**kwargs):
        calls.append(command);assert command=='compare-evaluations'
        return None
    worker.request=request
    worker.run()
    assert worker.receipt['state']=='incomplete' and len(worker.receipt['candidate_rounds'])==1
    assert worker.receipt['repair_attempts']==[] and not {'submit','repair'}&set(calls)
    assert worker.receipt['reassessment']['repair_budget_preserved']==budget
    assert worker.receipt['reassessment']['origin_runtime_evidence'][case.historic[0]['id']]['policy'] is None

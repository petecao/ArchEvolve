"""Exact OpenMP site classes through public frozen estimates,2026-10-06 ET; profile sets 2026-10-12 ET."""
import copy
import pytest
from testkit.cpu_service import clock_case
from testkit.cpu_openmp import native_receipt
from testkit.analytic import digest

ASSUMPTION={'regime':'prepared_legal_serialized_T1_sequences','transfer_basis':'inferred',
    'probe_kind':'per_event_steady_clock_empty_window','dynamic_bounds':'unverified',
    'runtime_internal_state':'unverified','next_outcome_policy':'max_constructed_success_failure_median',
    'physical_instruction_latency':False,'physical_upper_bound':False}


def setup(data,target, *, missing_rate=False, bad_flags=False, wrong_site=False, no_projection=False, malformed_parameter=False, unknown_profile_set=False):
    data['unmodeled_calls'][0]['name']='__kmpc_dispatch_next_4'
    data['static_analysis']['source_ir_sha256']='b'*64
    data.pop('identity_sha256',None);data['identity_sha256']=digest(data);char_hash=digest(data)
    signature=copy.deepcopy(native_receipt()['services'][17]['denominator']['proof']['static_projection']['calls'][17])
    signature.update(site=29,region='fixture.region',llvm_function='fixture.omp_outlined')
    if bad_flags:signature['ident_flags']['signed_decimal']='999'
    projection={'format':'swdb.openmp-call-projection.v1','characterization':{'id':data['id'],'sha256':char_hash},
        'source_ir_sha256':'b'*64,'source_json_sha256':'c'*64,'all_source_json_sites_cross_checked':True,'calls':[signature]}
    projection['identity_sha256']=digest(projection)
    model=target['mechanisms'][-1]
    model['selector'].update(characterization_sha256=char_hash,openmp_projections=[] if no_projection else [projection])
    model['selector']['calls']=[{'name':'__kmpc_dispatch_next_4','unit':'seconds/call','scope_assumption':copy.deepcopy(ASSUMPTION),
        'abi_sites':[{'characterization_sha256':char_hash,'site':999 if wrong_site else 29,'region':'fixture.region',
            'profile_indexes':[17,18],'parameter':'omp_max','source_parameters':[{'profile_index':17,'parameter':'success'},
                {'profile_index':18,'parameter':'failure'}]}]}]
    if unknown_profile_set:model['selector']['openmp_profile_set']='a9'
    if malformed_parameter:model['selector']['calls'][0]['abi_sites'][0]['source_parameters'][0]['parameter']=[]
    model['parameters']={name:{'value':value,'basis':'unknown' if value is None else 'inferred' if name=='omp_max' else 'reported',
        'unit':'seconds/call','source':'Synthetic independent legal probe only.'} for name,value in
        [('success',.1),('failure',None if missing_rate else .2),('omp_max',None if missing_rate else .2)]}


def test_exact_openmp_site_uses_both_return_classes_once_and_preserves_full_coverage(records,tmp_path):
    data=clock_case(records,tmp_path,setup=setup)
    overhead=data['regions'][0]['overheads'][0]
    assert overhead['seconds']==.8 and data['seconds']==2.8
    assert overhead['inputs']['covered_calls']==[{'site':29,'execution_count':4}]
    assert records.validate().returncode==0


@pytest.mark.parametrize('option',['missing_rate','bad_flags','wrong_site','no_projection','malformed_parameter','unknown_profile_set'])
def test_unsupported_openmp_class_or_missing_return_cost_stays_unknown(records,tmp_path,option):
    data=clock_case(records,tmp_path,setup=lambda d,t:setup(d,t,**{option:True}))
    overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None and overhead['inputs']['covered_calls']==[]
    assert any('openmp' in reason for reason in overhead['missing'])


def test_openmp_constructed_return_cost_cannot_override_context_admission(records,tmp_path):
    def blocked(data,target):
        setup(data,target)
        target['mechanisms'][-1]['selector']['calibration_admission']={'failure':['service_runtime.libomp']}
    data=clock_case(records,tmp_path,setup=blocked)
    model=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and model['inputs']['covered_calls']==[]
    assert 'openmp.all_constructed_return_costs' in model['missing']
    assert 'selector.calibration_admission' not in model['missing']



def test_frozen_services_v1_site_classes_are_unchanged_by_the_a2_set():
    import yaml
    from conftest import REPO
    from swdb.analytic_cpu_openmp import profile_indexes
    from swdb.cpu_openmp_profiles import PROFILE_SETS
    path=REPO/'records/target_descriptions/mbit10.cpu.lanl20261006.t1.services.v1.yaml'
    target=yaml.load(path.read_text(),Loader=yaml.CSafeLoader)
    model=[m for m in target['mechanisms'] if 'openmp_projections' in m.get('selector',{})][0]
    assert 'openmp_profile_set' not in model['selector']
    signatures={(p['characterization']['sha256'],c['site'],c['region']):c for p in model['selector']['openmp_projections'] for c in p['calls']}
    rows=[row for call in model['selector']['calls'] if 'abi_sites' in call for row in call['abi_sites']]
    assert len(rows)==106
    for row in rows:
        signature=signatures[(row['characterization_sha256'],row['site'],row['region'])]
        assert profile_indexes(signature)==row['profile_indexes']==profile_indexes(signature,PROFILE_SETS['a2'])

"""Constructed bulk profiles through frozen public estimates, 2026-10-06 ET."""
import pytest
from testkit.cpu_service import clock_case

PROFILES=['dynamic_length_disjoint_align4','dynamic_length_overlap_forward4_align4','dynamic_length_overlap_backward4_align4']
ASSUMPTION={'regime':'prepared_reused_bulk_buffers','transfer_basis':'inferred','profile_policy':'max_constructed_profiles_median',
    'source_overlap':'unverified','source_alignment':'unverified','physical_upper_bound':False}


def bulk_case(records,tmp_path,*,alter=None):
    def setup(char,target):
        model=target['mechanisms'][-1];selection=model['selector']['calls'][0]
        selection['scope_assumption']=dict(ASSUMPTION);params={};bins=[]
        for size in (8,16):
            profiles=[]
            for i,(regime,value) in enumerate(zip(PROFILES,(.1,.2,.3))):
                name=f'raw_{size}_{i}';params[name]={'value':value,'unit':'seconds/call','basis':'reported','source':'Hand separate profile.'}
                profiles.append({'regime':regime,'parameter':name,'calibration':'fixture.bulk','service':f'bulk.{i+1}.{size}'})
            envelope=f'envelope_{size}';params[envelope]={'value':.3,'unit':'seconds/call','basis':'inferred','source':'Maximum independently retained profile medians.'}
            bins.append({'bytes':size,'parameter':envelope,'source_profiles':profiles})
        selection['bins']=bins;model['parameters']=params
        if alter is not None:alter(selection,params)
    return clock_case(records,tmp_path,events=3,shaped=True,shaped_name='llvm.memmove.p0.p0.i64',setup=setup)


def test_full_exact_bulk_bins_clear_site_under_explicit_inferred_profile_scenario(records,tmp_path):
    data=bulk_case(records,tmp_path);overhead=data['regions'][0]['overheads'][0]
    assert overhead['seconds']==pytest.approx(.9) and data['seconds']==pytest.approx(2.9)
    assert overhead['inputs']['covered_calls']==[{'site':29,'execution_count':3}]
    assert 'proven' in ' '.join(overhead['notes'])
    assert records.validate().returncode==0


@pytest.mark.parametrize('failure',['missing_profile','tampered_max','unknown_profile','physical_claim','unmatched_bin'])
def test_bulk_scenario_never_waives_partial_rates_bins_or_unsupported_physical_claim(records,tmp_path,failure):
    def change(selection,params):
        if failure=='missing_profile':selection['bins'][0]['source_profiles'].pop()
        elif failure=='tampered_max':params['envelope_8']['value']=.2
        elif failure=='unknown_profile':params['raw_8_0'].update(value=None,basis='unknown');params['envelope_8'].update(value=None,basis='unknown')
        elif failure=='physical_claim':selection['scope_assumption']['physical_upper_bound']=True
        else:selection['bins'].pop()
    data=bulk_case(records,tmp_path,alter=change);overhead=data['regions'][0]['overheads'][0]
    assert data['seconds'] is None and overhead['seconds'] is None
    assert overhead['inputs']['covered_calls']==[]


@pytest.mark.parametrize('size,known',[(8,True),(16,False)])
def test_constant_copy_requires_its_independently_proved_exact_eight_byte_bin(records,tmp_path,size,known):
    def setup(char,target):
        model=target['mechanisms'][-1];selection=model['selector']['calls'][0]
        selection.update(scope_assumption=dict(ASSUMPTION),bins=[{'bytes':size,'parameter':'copy_s','source_profiles':[
            {'regime':'constant8_noalias_align8','parameter':'copy_s','calibration':'fixture.bulk.copy','service':'bulk.0.8'}]}])
        model['parameters']={'copy_s':{'value':.1,'basis':'reported','unit':'seconds/call','source':'Independent hand8B copy.'}}
        call=char['regions'][0]['call_shape_counts']['calls'][0]
        call['known_length_bins']=[{'bytes':size,'execution_count':dict(call['execution_count'])}]
    data=clock_case(records,tmp_path,events=3,shaped=True,shaped_name='llvm.memcpy.p0.p0.i64',setup=setup)
    overhead=data['regions'][0]['overheads'][0]
    if known:
        assert data['seconds']==pytest.approx(2.3) and overhead['inputs']['covered_calls']==[{'site':29,'execution_count':3}]
    else:
        assert data['seconds'] is None and overhead['seconds'] is None and overhead['inputs']['covered_calls']==[]

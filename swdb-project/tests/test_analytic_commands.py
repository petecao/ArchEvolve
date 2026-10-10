"""Description-driven live command observations through public characterize.
Created: 2026-10-06 ET. Values prove logical fixture conventions only.
Updated: 2026-10-09 ET (code review): coalescing, multi-field layout, row-splitting
window, outside-operand policy and per-trial execution-gap cases.
"""
import json
import hashlib
import yaml
import pytest
from conftest import REPO,run_swdb
from testkit.analytic import digest,target_description,characterize_command,freeze_protocol


def logical_rows(data,target_hash):
    return [r['address_stream_counts'][target_hash] for r in data['regions']
        if r['address_stream_counts'][target_hash]['line_requests']['value']]


# Straddle reads 4 bytes at 62+64i, i<6: lines (i,i+1). Window 4 holds two reads.
# Row is offset>>7; channel bit 6 alternates by line. Hand-computed per window:
# unique lines {0,1,2},{2,3,4},{4,5,6}; rows/window 2 (row only) or 3 (channel+row).
@pytest.mark.parametrize('coalescing,layout,expected',[
    ('window_unique_lines',None,(9,6,3)),
    ('window_unique_lines',{'channel':[{'lsb':6,'bits':1}]},(9,9,3)),
    ('none',{'channel':[{'lsb':6,'bits':1}]},(12,9,3)),
])
def test_coalesced_and_multi_field_layout_counts_match_hand_computation(records,tmp_path,llvm22,coalescing,layout,expected):
    data,target_hash=characterize_command(records,tmp_path,llvm22,coalescing=coalescing,layout=layout,extra=('--run-arg','straddle'))
    observed=logical_rows(data,target_hash)
    assert [(o['line_requests']['value'],o['row_groups']['value'],o['windows']['value']) for o in observed]==[expected]
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_window_boundary_inside_one_row_counts_the_row_in_each_window(records,tmp_path,llvm22):
    # Lines 0..5 have rows 0,0,1,1,2,2. Windows {0,1,2},{3,4,5} hold rows {0,1},{1,2}.
    data,target_hash=characterize_command(records,tmp_path,llvm22,window=3)
    observed=logical_rows(data,target_hash)
    assert [(o['line_requests']['value'],o['row_groups']['value'],o['windows']['value']) for o in observed]==[(6,4,2)]


def test_second_heap_operand_is_counted_and_noted_under_default_scratch_policy(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,source='commands_two_operands.cpp')
    observed=logical_rows(data,target_hash)
    assert [o['line_requests']['value'] for o in observed]==[6]
    assert any('6 target-role accesses' in note for note in observed[0]['notes'])
    raw=json.loads((tmp_path/'counted/counts.json').read_text())
    assert sum(c['outside_operand_accesses'] for c in raw['semantic_commands'].values())==6


def test_second_heap_operand_is_unknown_when_declared_unknown(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,source='commands_two_operands.cpp',outside='unknown')
    rows=[r['address_stream_counts'][target_hash] for r in data['regions']
        if 'target_access_outside_declared_operand' in r['address_stream_counts'][target_hash]['missing']]
    assert rows and all(o['line_requests']['value'] is None and o['staged_bytes']['value'] is None for o in rows)
    assert all(not o['line_requests']['value'] for r in data['regions'] for o in [r['address_stream_counts'][target_hash]])


def test_trial_command_gap_withholds_known_setup_executions(records,tmp_path,llvm22):
    setup={'model':'offload_setup','accounting':'additive_overhead','selector':{'event_ids':['fixture.read']},
        'parameters':{'seconds_per_event':{'value':1.0,'basis':'reported','source':'Hand-computed fixture only.','unit':'seconds/event'}}}
    data,_=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','deep'),mechanisms=[setup])
    assert 'command_nesting_state_budget' in data['observation_contract']['semantic_commands']['missing']
    protocol=freeze_protocol(records.path,tmp_path,tmp_path/'target.yaml',roi='fixture.command.v1',input_id='tiny-sym')
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.command',
        '--target-description',tmp_path/'target.yaml','--protocol',protocol,'--id','fixture.deep.setup','--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads(result.stdout)
    executed=[b for r in report['regions'] for b in r['overheads'] if b['model']=='offload_setup' and b['inputs']['executions']]
    assert executed and all(b['seconds'] is None and 'accelerator_calls.execution_coverage' in b['missing'] for b in executed)



def test_real_command_alias_counts_once_and_closes_final_partial_window(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22)
    calls=[call for region in data['regions'] for call in region['accelerator_calls']]
    executed=[call for call in calls if call['execution_count']['value']]
    assert len(executed)==1 and executed[0]['execution_count']['value']==1
    assert executed[0]['active_elements']['value']==6
    observed=next(region['address_stream_counts'][target_hash] for region in data['regions']
        if region['address_stream_counts'][target_hash]['line_requests']['value'])
    assert observed['line_requests']['value']==6
    assert observed['row_groups']['value']==3
    assert observed['grouped_row_hits']['value']==3
    assert observed['grouped_row_hit_fraction']['value']==.5
    assert observed['windows']['value']==2
    assert observed['staged_bytes']['value']==24
    assert observed['placement_assumption_sha256']==digest(data['observation_contract']['functional_observation']['placement'])
    assert data['observation_contract']['semantic_commands']['complete'] is True
    raw=(tmp_path/'counted/counts.json').read_text()
    assert all(name not in raw for name in ('allocation_base','address_sequence','decoded_rows'))
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr


def test_actual_straddling_range_expands_before_each_logical_window(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','straddle'))
    observed=next(r['address_stream_counts'][target_hash] for r in data['regions']
        if r['address_stream_counts'][target_hash]['line_requests']['value'])
    assert observed['line_requests']['value']==12
    assert observed['row_groups']['value']==6 and observed['windows']['value']==3
    assert observed['staged_bytes']['value']==24


def test_unknown_window_keeps_known_logical_requests_and_unknown_row_groups(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,window=None)
    observed=next(r['address_stream_counts'][target_hash] for r in data['regions']
        if r['address_stream_counts'][target_hash]['line_requests']['value'])
    assert observed['line_requests']['value']==6 and observed['row_groups']['value'] is None
    assert 'logical_window_policy' in observed['missing']


def test_row_budget_does_not_turn_partial_groups_into_complete_rows(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--state-budget','1'))
    observed=next(r['address_stream_counts'][target_hash] for r in data['regions']
        if r['address_stream_counts'][target_hash]['line_requests']['value'])
    assert observed['line_requests']['value']==6 and observed['row_groups']['value'] is None
    assert 'state_budget.window_rows' in observed['missing']


def test_unregistered_global_target_keeps_object_and_request_scope_unknown(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','unknown'))
    observed=[r['address_stream_counts'][target_hash] for r in data['regions']
        if 'semantic_target_object_identity' in r['address_stream_counts'][target_hash]['missing']]
    assert observed and all(o['line_requests']['value'] is None for o in observed)


def test_throwing_alias_cleanup_keeps_later_caller_store_in_host_domain(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','throw'))
    assert any('command_unwind' in r['address_stream_counts'][target_hash]['missing'] for r in data['regions'])
    host_stores=[a for r in data['regions'] for a in r['access_patterns']
        if a['source_location']['function']=='main' and a['update_kind']=='write' and a['element_count']['value']]
    assert host_stores


def test_reference_check_reads_same_target_array_without_adding_logical_requests(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22)
    requests=sum(r['address_stream_counts'][target_hash]['line_requests']['value'] for r in data['regions'])
    assert requests==6
    raw=json.loads((tmp_path/'counted/counts.json').read_text())
    assert sum(c['bookkeeping_accesses'] for c in raw['semantic_commands'].values())>=6


def test_offload_only_region_is_retained_in_each_trial(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--function','fixture_read'))
    assert len(data['trials'])==1
    assert sum(c['execution_count']['value'] for r in data['trials'][0]['regions'] for c in r['accelerator_calls'])==1


def test_signed_negative_active_extent_is_unknown_on_unwind(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','throw'))
    called=[c for r in data['regions'] for c in r['accelerator_calls'] if c['execution_count']['value']]
    assert called and all(c['active_elements']['value'] is None for c in called)


def test_unmatched_target_producer_never_infers_zero_traffic(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,producer='fixture_missing')
    observed=[r['address_stream_counts'][target_hash] for r in data['regions'] if 'target_access_source_role' in r['address_stream_counts'][target_hash]['missing']]
    assert observed and all(o['line_requests']['value'] is None and o['staged_bytes']['value'] is None for o in observed)


def test_guard_budget_shadows_deeper_frames_and_restores_host_domain(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--run-arg','deep'))
    assert 'command_nesting_state_budget' in data['observation_contract']['semantic_commands']['missing']
    assert all(r['address_stream_counts'][target_hash]['line_requests']['value'] is None for r in data['regions'])
    assert any(a['source_location']['function']=='main' and a['update_kind']=='write' and a['element_count']['value'] for r in data['regions'] for a in r['access_patterns'])


def test_negative_logical_request_count_is_refused_after_fixture_resigning(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22)
    observed=next(r['address_stream_counts'][target_hash] for r in data['regions'] if r['address_stream_counts'][target_hash]['line_requests']['value'])
    observed['line_requests']['value']=-1
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.command.yaml',data)
    result=records.validate()
    assert result.returncode==1
    assert 'nonnegative' in result.stdout+result.stderr or 'minimum' in result.stdout+result.stderr


@pytest.mark.parametrize('trial',[False,True])
def test_window_policy_hash_tamper_is_refused_at_aggregate_and_trial_scope(records,tmp_path,llvm22,trial):
    data,target_hash=characterize_command(records,tmp_path,llvm22)
    rows=data['trials'][0]['regions'] if trial else data['regions']
    rows[0]['address_stream_counts'][target_hash]['window_policy_sha256']='f'*64
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.command.yaml',data)
    result=records.validate()
    assert result.returncode==1 and 'window_policy_sha256' in result.stdout+result.stderr


def test_proven_no_application_memory_setup_is_excluded_but_counted_as_event(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,setup=True,extra=('--run-arg','setup'))
    calls=[c for r in data['regions'] for c in r['accelerator_calls'] if c['execution_count']['value']]
    assert len(calls)==1 and calls[0]['event']=='fixture.setup' and calls[0]['execution_count']['value']==1
    assert calls[0]['active_elements']['value']==0 and calls[0]['useful_bytes']['value']==0
    assert all(r['address_stream_counts'][target_hash]['line_requests']['value']==0 for r in data['regions'])
    raw=json.loads((tmp_path/'counted/counts.json').read_text())
    assert sum(c['bookkeeping_accesses'] for c in raw['semantic_commands'].values())>=8
    assert any(a['source_location']['function']=='main' and a['update_kind']=='write' and a['element_count']['value'] for r in data['regions'] for a in r['access_patterns'])
    assert records.validate().returncode==0


def test_pinned_bookkeeping_helper_opaque_calls_do_not_contaminate_target_reads(records,tmp_path,llvm22):
    data,target_hash=characterize_command(records,tmp_path,llvm22,extra=('--build-flag=-DFIXTURE_BOOKKEEPING_EXTERNAL',))
    assert sum(r['address_stream_counts'][target_hash]['line_requests']['value'] for r in data['regions'])==6
    raw=json.loads((tmp_path/'counted/counts.json').read_text())
    assert sum(sum(c['opaque_calls'].values()) for c in raw['semantic_commands'].values())==1
    assert not any(c['missing'] for c in raw['semantic_commands'].values())
    assert sum(c['execution_count']['value'] for r in data['regions'] for event in r['accelerator_calls'] for c in event['functional_bookkeeping']['opaque_calls'])==1

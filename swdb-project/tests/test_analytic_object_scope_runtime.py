"""Public observer callback protocol; independent lifecycle fixtures. Updated: 2026-10-06 ET."""
import json
import os
import subprocess
import pytest
from conftest import REPO


@pytest.fixture(scope='module')
def callback_binary(tmp_path_factory):
    # Compile once, without instrumentation: this drives the externally exported
    # observer protocol and reads its public compact output, never internal methods.
    directory=tmp_path_factory.mktemp('scope-callbacks')
    compiler=os.environ.get('SWDB_LLVM_BIN','/opt/homebrew/opt/llvm/bin')+'/clang++'
    binary=directory/'observer'
    built=subprocess.run([compiler,'-O2','-std=c++11',
        str(REPO/'tests/fixtures/analytic/object_scope_callbacks.cpp'),
        str(REPO/'swdb/llvm/CountingRuntime.cpp'),'-o',str(binary)],capture_output=True,text=True)
    assert built.returncode==0,built.stderr
    return binary


def callback_counts(callback_binary,tmp_path,mode,*,budget=524288):
    path=tmp_path/'counts.json'
    result=subprocess.run([callback_binary,mode],env=dict(os.environ,
        SWDB_ROI_GATED='1',SWDB_COUNTS_OUTPUT=str(path),SWDB_STATE_BUDGET=str(budget)),capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    raw=json.loads(path.read_text())
    assert all(name not in json.dumps(raw) for name in ('allocation_base','object_address','address_sequence'))
    return [trial['memory_service_counts']['0'] for trial in raw['trials']]


def test_exact_abi_aliases_share_view_identity_and_retire_on_exit(callback_binary,tmp_path):
    first,second=callback_counts(callback_binary,tmp_path,'aliases')
    assert first['object_scope_counts']=={'full_allocation_requests':0,'bounded_view_requests':1,
        'unresolved_requests':0,'bounded_view_line_union':1}
    assert first['lifetime_line_union'] is None
    assert second['unknown_object_requests']==1
    assert second['object_scope_counts']['bounded_view_requests']==0


def test_overlapping_distinct_views_are_unknown_until_one_retires(callback_binary,tmp_path):
    first,second=callback_counts(callback_binary,tmp_path,'overlap')
    assert first['unknown_object_requests']==1
    assert first['object_scope_counts']['bounded_view_line_union'] is None
    assert second['unknown_object_requests']==0
    assert second['object_scope_counts']['bounded_view_requests']==1


def test_view_exit_preserves_containing_full_storage_and_explicit_lifetime_end_retires_it(callback_binary,tmp_path):
    first,second=callback_counts(callback_binary,tmp_path,'full-alias')
    assert first['object_scope_counts']['full_allocation_requests']==1
    assert first['object_scope_counts']['bounded_view_requests']==0
    assert first['lifetime_line_union']==1
    assert second['unknown_object_requests']==1


def test_stackrestore_retires_only_objects_added_since_checkpoint(callback_binary,tmp_path):
    first,second=callback_counts(callback_binary,tmp_path,'restore')
    assert first['lifetime_line_union']==2
    assert second['object_scope_counts']['full_allocation_requests']==1
    assert second['unknown_object_requests']==1


def test_unwind_retires_child_view_and_keeps_parent_allocation(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'unwind')
    assert memory['object_scope_counts']['full_allocation_requests']==1
    assert memory['object_scope_counts']['bounded_view_requests']==0
    assert memory['unknown_object_requests']==1


@pytest.mark.parametrize('mode',['overflow','unknown'])
def test_unproved_or_overflowing_extent_stays_unknown(callback_binary,tmp_path,mode):
    [memory]=callback_counts(callback_binary,tmp_path,mode)
    assert memory['unknown_object_requests']==1
    assert 'source_object_extent_unknown' in memory['missing']


def test_state_budget_preserves_requests_and_names_unresolved_view(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'budget',budget=1)
    assert sum(r['requests'] for r in memory['requests'])==2
    assert memory['object_scope_counts']['bounded_view_requests']==1
    assert memory['unknown_object_requests']==1
    assert 'state_budget.object_registry' in memory['missing']


def test_lifetime_start_on_live_storage_preserves_allocation_identity(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'repeat-start')
    assert memory['object_scope_counts']['full_allocation_requests']==2
    assert memory['lifetime_line_union']==1
    assert memory['logical_first_read_pages']==1


def test_stackrestore_uses_storage_creation_order_not_lifetime_start_order(callback_binary,tmp_path):
    first,second=callback_counts(callback_binary,tmp_path,'late-life')
    assert first['lifetime_line_union']==second['lifetime_line_union']==1
    assert first['unknown_object_requests']==second['unknown_object_requests']==0
    assert second['logical_first_read_pages']==0


def test_request_overflow_is_unknown_instead_of_wrapping_to_zero(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'request-overflow')
    assert memory['requests'][0]['requests'] is None
    assert memory['unknown_object_requests'] is None
    assert memory['object_scope_counts']['unresolved_requests'] is None
    assert 'request_count_overflow' in memory['missing']


def test_unresolved_stackrestore_names_checkpoint_unknown(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'unknown-restore')
    assert memory['unknown_object_requests']==1
    assert 'stackrestore_checkpoint_unknown' in memory['missing']


def test_nonlocal_control_flow_forgets_source_frames_and_views(callback_binary,tmp_path):
    [memory]=callback_counts(callback_binary,tmp_path,'abandon')
    assert memory['unknown_object_requests']==2
    assert memory['object_scope_counts']['bounded_view_requests']==0
    assert 'nonlocal_control_flow' in memory['missing']


def test_process_finalization_closes_scope_callbacks_before_late_source_destructors(callback_binary,tmp_path):
    path=tmp_path/'counts.json'
    result=subprocess.run([callback_binary,'shutdown'],env=dict(os.environ,
        SWDB_ROI_GATED='1',SWDB_COUNTS_OUTPUT=str(path)),capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert 'closed=1' in result.stderr
    assert json.loads(path.read_text())['trials']

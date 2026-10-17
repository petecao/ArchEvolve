"""2026-10-16 ET. Prospective actual public30 profile; missing tools/inputs fail, never skip.

Do not execute without root's separate runtime/guard admission. Each invocation
uses the real public CLI, persisted proof record, actual model-native replay
and complete finite policy checks. No C++/hardware correspondence is claimed.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

CASE_IDS=['command_wrong_owner_negative', 'covered_store_next_thread_load_positive', 'critical_end_wait_positive', 'critical_end_without_wait_negative', 'different_region_noncover_negative', 'disjoint_owned_tiles_positive', 'history_exact_issue_negative', 'history_latest_positive', 'other_thread_cpu_read_positive', 'outside_critical_store_positive', 'owned_tile_positive', 'pair_command_half_negative', 'pair_cpu_half_read_negative', 'pair_owned_positive', 'pair_wrong_owner_negative', 'pending_read_lifetime_end_negative', 'pending_store_cpu_read_negative', 'prior_cpu_store_old_value_negative', 'prior_cpu_store_visible_positive', 'ready_always_one_negative', 'ready_always_zero_negative', 'ready_cpu_read_negative', 'ready_relation_positive', 'same_region_read_read_noncover_negative', 'same_region_write_cover_positive', 'u32_command_half_positive', 'u32_cpu_half_read_positive', 'u32_disjoint_half_positive', 'u64_second_half_conflict_negative', 'wrong_owner_negative']

def read(row):
    from swdb.dx100_finite_trace import receiver
    return receiver.Inputs().read(row)

@pytest.mark.parametrize('case_id',CASE_IDS)
def test_actual_finite_public(case_id):
    from swdb import yamlio
    from swdb._dx100_finite import finite_checks_v1 as checks
    selected=os.environ.get('SWDB_FINITE_ACTUAL_SELECTION')
    assert selected, 'root must select the exact physical public-profile/command-plan input'
    selection_pin=json.loads(selected);selection=checks.strict(read(selection_pin))
    assert set(selection)=={'schema','profile','command_plan'} and selection['schema']=='finite-public-actual-selection-1'
    profile=checks.strict(read(selection['profile']));command=checks.strict(read(selection['command_plan']))
    assert len(profile['cases'])==30 and {row['case_id'] for row in profile['cases']}==set(CASE_IDS)
    assert command['required_public_count']==30 and command['required_skips']==0
    rows=[row for row in profile['cases'] if row['case_id']==case_id];jobs=[row for row in command['jobs'] if row['case_id']==case_id]
    assert len(rows)==len(jobs)==1
    row,job=rows[0],jobs[0]
    assert job['contract']==row['contract'] and job['conditional_predicted_verdict']==row['conditional_predicted_verdict']
    done=subprocess.run(job['argv'],cwd=job['cwd'],env={**os.environ,**command['environment']},capture_output=True,text=True,timeout=1800)
    assert done.returncode==0,done.stderr[-2000:]
    output=checks.strict(done.stdout)
    assert type(output) is dict and set(output)=={'record','path'}
    record=output['record'];persisted=yamlio.load(Path(output['path']))
    assert persisted==record
    checks.public_record(record,row,profile)
    # Re-read exact controls at settlement; no callback/accepted Boolean authority.
    assert checks.strict(read(selection['profile']))==profile
    assert checks.strict(read(selection['command_plan']))==command
    assert checks.strict(read(selection_pin))==selection

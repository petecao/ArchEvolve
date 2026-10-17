"""CPU outcome beside explicit analytic state; isolated catalog. 2026-10-09 ET.

Updated 2026-10-09 23:10 ET (code review F8/F9): Extensa evaluations add no pairing stage
or evaluator scope; archived unpaired states carry no prediction.
"""
import copy

import pytest

from testkit.bfs_native import build_evaluation_setup, evaluate
from testkit.native_catalog import seed_native_contract_records
from testkit.proposals import build_proposal_setup


@pytest.fixture
def evaluation_setup(records, tmp_path):
    seed_native_contract_records(records)
    return build_evaluation_setup(build_proposal_setup(records, tmp_path, copy_all=False), tmp_path)


def test_cpu_evaluation_adds_unavailable_estimate_without_changing_fixture_timing(evaluation_setup):
    result, data=evaluate(evaluation_setup, sources=[0,4], repetitions=2)
    assert result.returncode==0,result.stderr
    assert data['outcome']['state']=='complete' and data['correctness']['state']=='passed'
    assert [t['duration_s'] for t in data['timing']]==[.025]*4
    assert data['summary']['median_roi_seconds']==.025 and data['gain_claim'] is False
    pair=data['paired_estimate']
    assert pair['state']=='unavailable' and pair['seconds'] is None
    assert pair['native_timing_decides'] is True
    assert 'matched_counted_evaluator_scope' in pair['missing']
    assert 'analytic_pairing' in [row['stage'] for row in data['stages']]
    checked=evaluation_setup[0].validate()
    assert checked.returncode==0,checked.stdout+checked.stderr
    # F9: an archived unpaired slot may not smuggle in a prediction or the removed state.
    archive=evaluation_setup[0]
    path='evaluations/'+data['id']+'.yaml'
    original=archive.read(path)
    for change in ({'seconds':.01},{'kernel_seconds':.01},{'state':'known'}):
        altered=copy.deepcopy(original);altered['paired_estimate'].update(change)
        archive.write(path,altered)
        rejected=archive.validate()
        assert rejected.returncode!=0 and 'paired_estimate' in rejected.stdout+rejected.stderr,change
    archive.write(path,original)
    assert archive.validate().returncode==0

    missing_result, missing=evaluate(evaluation_setup, id='eval-explicit-missing-estimate', analytic_estimate='missing.estimate')
    assert missing_result.returncode==0,missing_result.stderr
    assert missing['outcome']['state']=='complete' and missing['timing'][0]['duration_s']==.025
    assert missing['paired_estimate']['state']=='excluded'
    assert missing['paired_estimate']['missing']==['requested_estimate_admission']
    records,runs,request,_=evaluation_setup
    explicit=records.swdb('evaluate',request(id='eval-extensa-excluded'),'--runs-dir',runs,
        '--mode','extensa','--campaign','extensa-native-bfs-20261006-a1','--format','json',env={'SWDB_NATIVE_FIXTURE':'pass'})
    assert explicit.returncode==0,explicit.stderr
    import json
    excluded=json.loads(explicit.stdout)
    assert excluded['mode']=='extensa' and excluded['timing'][0]['duration_s']==.025
    assert excluded['paired_estimate']['state']=='excluded'
    assert excluded['paired_estimate']['missing']==['ArchEvolve_mode']
    # F8: the Extensa record gains only the explicit exclusion, no pairing stage or scope.
    assert 'analytic_pairing' not in [row['stage'] for row in excluded['stages']]
    assert 'analytic_evaluator_scope' not in excluded['context']

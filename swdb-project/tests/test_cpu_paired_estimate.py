"""Existing CPU timing keeps its outcome beside explicit analytic state. Created: 2026-10-06 ET."""
from testkit.bfs_native import evaluate


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
    checked=evaluation_setup[0].validate()
    assert checked.returncode==0,checked.stdout+checked.stderr

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

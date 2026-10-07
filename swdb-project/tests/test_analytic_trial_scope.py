"""Public trial-window scope correction. Updated: 2026-10-06 ET."""
import json
from conftest import REPO, run_swdb


def test_public_count_labels_each_trial_window_without_changing_root_scope(records,tmp_path,llvm22):
    records.add_stub()
    result=run_swdb('characterize','--records',records.path,
        '--source',REPO/'tests/fixtures/analytic/trial_scopes.cpp',
        '--implementation','stub-impl','--input','tiny-sym',
        '--function','scoped_kernel','--fixture','--counting-pipeline','source-normalized-v2',
        '--id','fixture.trial.scopes','--llvm-bin',llvm22,'--output',tmp_path/'counted',
        '--timeout-s','30','--format','json',timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    value=json.loads(result.stdout)
    assert len(value['trials'])==2
    def check(regions,calls,scope):
        for region in regions:
            assert all(c['scope']==scope for c in region['operation_counts'].values())
            assert all(c['scope']==scope for c in region['dynamic_counts'].values())
            for access in region['access_patterns']:
                assert access['element_count']['scope']==scope
                assert access['bytes_accessed']['scope']==scope
            for row in region['call_shape_counts']['calls']:
                assert row['scope']==scope and row['execution_count']['scope']==scope
        assert calls
        assert all(c['execution_count']['scope']==scope and c['size_bytes']['scope']==scope for c in calls)
    check(value['regions'],value['unmodeled_calls'],'per_run')
    for trial in value['trials']:check(trial['regions'],trial['unmodeled_calls'],'per_trial')
    assert sum(a['element_count']['value'] for r in value['trials'][1]['regions'] for a in r['access_patterns']) > sum(a['element_count']['value'] for r in value['trials'][0]['regions'] for a in r['access_patterns'])

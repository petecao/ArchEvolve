"""Public trial-window scope correction. Updated: 2026-10-09 ET (isolated record closure;
code review F4: a multi-window root is labeled per_trial)."""
import json
from conftest import REPO, run_swdb


def test_public_count_labels_each_trial_window_and_its_trial_zero_root(records,tmp_path,llvm22):
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
    # 2026-10-09 ET (code review F4): with two windows the root repeats trial 0, so it is per_trial.
    check(value['regions'],value['unmodeled_calls'],'per_trial')
    assert value['counting']['top_level_counts']['trial_position']==0
    for trial in value['trials']:check(trial['regions'],trial['unmodeled_calls'],'per_trial')
    assert sum(a['element_count']['value'] for r in value['trials'][1]['regions'] for a in r['access_patterns']) > sum(a['element_count']['value'] for r in value['trials'][0]['regions'] for a in r['access_patterns'])


def test_public_estimate_reconciles_sealed_legacy_trial_scope_only_in_context(records,tmp_path):
    import hashlib
    import yaml
    from testkit.analytic import freeze_protocol
    records.copy_closure('bfs.functional.kron-g16.t4.characterization.objects.a2')
    path=records.path/'workload_characterizations/bfs.functional.kron-g16.t4.characterization.objects.a2.yaml'
    original=hashlib.sha256(path.read_bytes()).hexdigest()
    counted=records.read(path.relative_to(records.path))
    assert all(c['execution_count']['scope']=='per_run' for t in counted['trials'] for c in t['unmodeled_calls'])
    target=tmp_path/'target.yaml'
    target.write_text(yaml.safe_dump(counted['observation_contract']['counted_target_description_snapshot'],sort_keys=False))
    protocol=freeze_protocol(records.path,tmp_path,target,roi=counted['binding']['roi'],threads=4,
        input_id=counted['input'],arguments=counted['source']['run_arguments'])
    result=run_swdb('estimate','--records',records.path,'--characterization',counted['id'],
        '--target-description',target,'--protocol',protocol,'--id','fixture.legacy.scopes.estimate',
        '--format','json',timeout=240)
    assert result.returncode==0,result.stdout+result.stderr
    value=json.loads(result.stdout)
    proofs=value['extensions']['legacy_trial_scope_reconciliations']
    assert [p['position'] for p in proofs]==list(range(5))
    assert all(p['basis']=='inferred' and p['counted_payload_sha256']==counted['binding']['execution_receipt']['counted_payload_sha256'] for p in proofs)
    assert all(c['execution_count']['scope']=='per_trial' for t in value['trials'] for r in t['regions'] for b in r['bounds'] if b['model']=='unmodeled_calls' for c in b['inputs']['calls'])
    assert value['seconds'] is None  # Scope correction supplies no missing resource cost.
    assert hashlib.sha256(path.read_bytes()).hexdigest()==original

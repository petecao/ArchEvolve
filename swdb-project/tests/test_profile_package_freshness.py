"""Public strategy queries retain packages but expose stale evidence. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-27."""

import json
from pathlib import Path

import pytest

from testkit.profile_packages import _assemble, _callgrind_profile


@pytest.mark.parametrize('fault', [None, 'audit', 'raw-changed', 'raw-unavailable'])
def test_strategy_queries_recheck_retained_memory_without_mutating_package(package_setup, tmp_path, fault):
    records, request, _, profile, _ = package_setup
    _callgrind_profile(profile, tmp_path)
    records.write('region_profiles/package-diagnostics.yaml', profile)
    package = _assemble(records, tmp_path, request)
    if fault == 'audit':
        profile.setdefault('extensions', {})['post_collection_audit'] = {
            'scope': 'dynamic_memory', 'state': 'invalid', 'reason': 'fixture audit after assembly'}
        records.write('region_profiles/package-diagnostics.yaml', profile)
    elif fault == 'raw-changed':
        Path(profile['dynamic_memory'][0]['raw_artifact']).write_text('changed after assembly\n')
    elif fault == 'raw-unavailable':
        Path(profile['dynamic_memory'][0]['raw_artifact']).unlink()
    expected = 'invalid' if fault in {'audit', 'raw-changed'} else 'unverified' if fault else 'valid'
    selected = tmp_path/'query-index.sqlite'
    forward = records.swdb('profile-strategies', package['id'], '--db', selected, '--format', 'json')
    assert selected.is_file()
    assert forward.returncode == 0, forward.stderr
    data = json.loads(forward.stdout)
    assert data['evidence_validation']['state'] == expected
    assert data['performance_guarantee'] is False
    reverse = records.swdb('strategy-regions', 'software_prefetch', '--package', package['id'], '--db', selected, '--format', 'json')
    assert reverse.returncode == 0, reverse.stderr
    matches = json.loads(reverse.stdout)['profiled_matches']
    assert matches and all(row['evidence_validation']['state'] == expected for row in matches)
    assert all(row['profile_support'] != 'compatible_profile_evidence' for row in matches)
    if fault:
        assert data['evidence_validation']['reasons']
    retained = records.swdb('get', package['id'], '--db', selected, '--format', 'json')
    assert retained.returncode == 0 and json.loads(retained.stdout) == package


def test_hotspots_selected_index_still_checks_actual_memory_bytes(package_setup,tmp_path,monkeypatch):
    records, request, evaluation, profile, candidate = package_setup
    _callgrind_profile(profile,tmp_path)
    records.write('region_profiles/package-diagnostics.yaml',profile)
    selected=tmp_path/'hotspots.sqlite'
    args=('bfs-hotspots',profile['id'],'--kind','loop','--db',selected,'--format','json')
    before=records.swdb(*args)
    assert before.returncode==0,before.stderr
    assert selected.is_file() and json.loads(before.stdout)['memory_validation']['state']=='consistent'
    # Mutate valid descendants after the single SQL SELECT. Chain members must
    # remain from that selected snapshot, then refresh together next time.
    from types import SimpleNamespace
    from swdb import db,workflow
    import copy
    original=db.sql
    def mutate_after_select(path,query):
        rows=original(path,query)
        changed=copy.deepcopy(evaluation);changed['outcome']['reason']='later metadata observation'
        records.write('evaluations/'+evaluation['id']+'.yaml',changed)
        changed_profile=copy.deepcopy(profile);changed_profile['reasons']=['later metadata observation']
        records.write('region_profiles/'+profile['id']+'.yaml',changed_profile)
        return rows
    monkeypatch.setattr(db,'sql',mutate_after_select)
    chain=workflow.get_record(SimpleNamespace(records=records.path,db=selected,id=candidate['id'],chain=True))['records']
    assert chain[evaluation['id']]==evaluation and chain[profile['id']]==profile
    monkeypatch.setattr(db,'sql',original)
    Path(profile['dynamic_memory'][0]['raw_artifact']).write_text('changed without a metadata write\n')
    after=records.swdb(*args)
    assert after.returncode==0,after.stderr
    assert json.loads(after.stdout)['memory_validation']['state']=='invalid'

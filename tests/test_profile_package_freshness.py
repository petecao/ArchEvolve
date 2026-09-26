"""Public strategy queries retain packages but expose stale evidence. Updated: 2026-09-25."""

import json
from pathlib import Path

import pytest

from test_profile_packages import package_seed, package_setup, _assemble, _callgrind_profile


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
    forward = records.swdb('profile-strategies', package['id'], '--format', 'json')
    assert forward.returncode == 0, forward.stderr
    data = json.loads(forward.stdout)
    assert data['evidence_validation']['state'] == expected
    assert data['performance_guarantee'] is False
    reverse = records.swdb('strategy-regions', 'software_prefetch', '--package', package['id'], '--format', 'json')
    assert reverse.returncode == 0, reverse.stderr
    matches = json.loads(reverse.stdout)['profiled_matches']
    assert matches and all(row['evidence_validation']['state'] == expected for row in matches)
    assert all(row['profile_support'] != 'compatible_profile_evidence' for row in matches)
    if fault:
        assert data['evidence_validation']['reasons']
    retained = records.swdb('get', package['id'], '--format', 'json')
    assert retained.returncode == 0 and json.loads(retained.stdout) == package

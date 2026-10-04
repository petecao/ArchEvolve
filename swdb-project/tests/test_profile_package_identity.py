"""Public profile-package seal downgrade regressions. Dated 2026-09-26 ET.

All records are temporary contract fixtures; no empirical evidence is changed.
"""
import copy
import json

import pytest

from test_profile_packages import package_seed, package_setup, _assemble
from test_proposals import proposal_setup


@pytest.mark.parametrize('fault', ['version', 'all-fields', 'complete-unsealed', 'execution-fixture'])
def test_public_readback_rejects_removing_package_seal(package_setup, tmp_path, fault):
    records, request, _, _, _ = package_setup
    package = _assemble(records, tmp_path, request)
    assert records.swdb('get', package['id'], '--format', 'json').returncode == 0
    changed = copy.deepcopy(package)
    changed['regions'][0]['text'] = 'Synthetic changed source text after assembly'
    changed.pop('package_version')
    if fault != 'version':
        changed.pop('requested_id')
        changed.pop('identity_sha256')
    if fault == 'complete-unsealed':
        changed.update(id='unsealed-complete', completeness='complete')
    elif fault == 'execution-fixture':
        changed['id'] = 'unsealed-execution-fixture'
        changed['evidence']['classification'] = 'execution'
    records.write(f"profile_packages/{package['id']}.yaml", changed)
    retrieved = records.swdb('get', changed['id'], '--format', 'json')
    assert retrieved.returncode == 1, retrieved.stdout
    assert 'retained identity' in retrieved.stderr
    rebuilt = records.swdb('build')
    assert rebuilt.returncode == 1 and 'retained identity' in rebuilt.stderr


def test_explicit_unsealed_fixture_survives_public_index_rebuild(proposal_setup):
    records, _, _, _ = proposal_setup
    original = records.swdb('get', 'test-package', '--format', 'json')
    assert original.returncode == 0, original.stderr
    package = json.loads(original.stdout)
    assert package['completeness'] == 'fixture'
    assert package['evidence']['classification'] == 'contract_fixture'
    assert 'package_version' not in package
    assert records.swdb('build').returncode == 0
    retrieved = records.swdb('get', package['id'], '--format', 'json')
    assert retrieved.returncode == 0 and json.loads(retrieved.stdout) == package

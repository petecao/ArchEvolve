"""2026-10-16 ET. Public prove trust plumbing; version-only external stand-in.

No formal tool runs: ordinary CPU writes deliberately stop this fixture before
launch. The semantics clone tests records, not any new DX100 behavior.
"""
import hashlib
import json

import pytest
import yaml

from test_level_rule import CLANG, TOP, proof_seed, seed, template  # noqa: F401 (scripted record fixtures)


from testkit.dx100_trust import TRUST, run_semantics_fixture


@pytest.mark.parametrize('adapter', ['cbmc', 'wp'])
@pytest.mark.parametrize('mark', [True, False, 'true'])
@pytest.mark.parametrize('mutate', [False, True])
def test_a_prelaunch_semantics_verdict_lists_each_pinned_rule_marked_as_trusted(tmp_path, adapter, mark, mutate):
    result, records, semantics, marker = run_semantics_fixture(tmp_path, adapter, mark, mutate)
    if isinstance(mark, str):
        assert result.returncode == 1 and 'record_assumption must be a boolean' in result.stderr
        assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))
        return
    if mutate and adapter == 'cbmc':
        assert result.returncode == 1 and 'trust entry changed' in result.stderr, result.stdout + result.stderr
        assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))
        return
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load((records.path / json.loads(result.stdout)['path']).read_text())
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct'
    assert record['settings']['verifier_launched'] is False and not marker.exists()
    got = [row for row in record['assumptions']
           if row['reference']['id'].startswith('semantics.dx100_trust_fixture#')]
    expected = [{'kind': 'proof_semantics',
                 'reference': {'id': 'semantics.dx100_trust_fixture#' + name,
                               'sha256': hashlib.sha256(semantics.read_bytes()).hexdigest()},
                 # WP's cached version probe happens during validation, before
                 # the job's Library is loaded. Its new, validated snapshot is
                 # legitimate; CBMC's probe above occurs after that snapshot.
                 'sentence': 'Changed after validation.' if mutate and name == 'one_instance' else sentence}
                for name, sentence in TRUST.items()] if mark else []
    assert got == expected


def test_the_five_explicit_semantics_trust_entries_never_cap_candidate_level(seed):
    """Fixture records test the level rule; no proven hardware result is created."""
    assumptions = [{'kind': 'proof_semantics',
                    'reference': {'id': 'semantics.dx100_trust_fixture#' + name, 'sha256': 'e' * 64},
                    'sentence': sentence} for name, sentence in TRUST.items()]
    seed.proof('t28_trust', bounds=TOP, assumptions=[CLANG, *assumptions])
    level = seed.level()
    assert level['level'] == 'proven_unbounded'
    assert all(not record['caps'] for unit in level['proof_units'] for record in unit['records'])
    assert [{k: row[k] for k in ('kind', 'reference', 'sentence')}
            for row in level['assumptions'] if row['kind'] == 'proof_semantics'] == assumptions

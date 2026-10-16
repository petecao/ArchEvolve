"""2026-10-15 ET. Public prove trust plumbing; version-only external stand-in.

No formal tool runs: ordinary CPU writes deliberately stop this fixture before
launch. The semantics clone tests records, not any new DX100 behavior.
"""
import hashlib
import json
import shutil
import sys

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_level_rule import CLANG, TOP, proof_seed, seed, template  # noqa: F401 (scripted record fixtures)


TRUST = {
    'mmio_ordering': 'The pinned MMIO implements call semantics including ordering; its wait fence lacks a memory clobber, a portability note independent of candidate artifacts.',
    'cross_core_filter': 'A DX100 store remains visible if the snoop filter drops its line before the write reaches L3.',
    'cross_core_write_buffer': 'A DX100 store remains visible when L3 passes a write below it because no block can be allocated.',
    'no_stale_cpu_copy': 'No stale CPU copy survives a DX100 store (owner Eric).',
    'one_instance': 'All commands belong to one DX100 instance.',
}


@pytest.mark.parametrize('adapter', ['cbmc', 'wp'])
@pytest.mark.parametrize('mark', [True, False, 'true'])
@pytest.mark.parametrize('mutate', [False, True])
def test_a_prelaunch_semantics_verdict_lists_each_pinned_rule_marked_as_trusted(tmp_path, adapter, mark, mutate):
    from swdb import c_lowering, cbmc_adapter, cbmc_translator
    library = tmp_path / 'library'
    for folder in ('proof_semantics', 'dx100'):
        shutil.copytree(REPO / 'library' / folder, library / folder)
    old = library / 'proof_semantics/dx100_bfs_0_1.yaml'
    data = yaml.safe_load(old.read_text())
    data.update(id='semantics.dx100_trust_fixture', version='0.2', sequence=2)
    data['rules'] += [{'id': name, 'statement': sentence, 'assumed': {'owner': 'Eric'}, 'record_assumption': mark}
                     for name, sentence in TRUST.items()]
    old.unlink()
    semantics = library / 'proof_semantics/dx100_trust_fixture.yaml'
    semantics.write_text(yaml.safe_dump(data, sort_keys=False))
    units = library / 'proof_units'
    units.mkdir()
    source = 'void maa_const(int value, int reg);\nint trust_fixture(int *p) { maa_const(7, 0); p[0] = 7; return 7; }\n'
    (units / 'trust.cc').write_text(source)
    contracts = library / 'rewrite_contracts'
    contracts.mkdir()
    contract = {
        'id': 'contract.dx100_trust_fixture', 'kind': 'rewrite_contract', 'formal_frame': 1, 'version': '1.0',
        'provenance': {'origin': {'intrinsic_specification': 'ticket28-record-plumbing-fixture'}},
        'proof_unit': {'source': {'root': 'library', 'path': 'proof_units/trust.cc',
                                  'sha256': hashlib.sha256(source.encode()).hexdigest()}, 'function': 'trust_fixture',
                       'array_domains': {'p': {'extent': '1'}}},
        'concurrency_frame': [{'array': 'p', 'shared_actions': [], 'history_reads': False}],
        'clauses': [{'id': 'result', 'role': 'postcondition', 'statement': 'Synthetic trust-record fixture.',
                     'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'wrong-result', 'check': 'result'},
                     'acsl': {'text': r'assigns p[0]; ensures \result == 7;', 'uses': []},
                     'proof_placement': {'once': 'self'}}],
        'pattern_key': [{'roles': ['index', 'target'], 'address_shapes': ['stream', 'single_valued_indirect'],
                         'update_kind': 'read'}],
        'strategies': [], 'uses_intrinsics': [], 'uses_library_operations': [], 'runtime_guards': [], 'knobs': [],
        'preservation_obligations': [], 'correctness_check': {'kernel': 'fixture', 'check': 'fixture'},
        'execution_witness': {'check': 'fixture'},
        'negative_controls': [{'id': kind, 'kind': kind, 'check': 'fixture'}
                              for kind in ('overlapping_pointer', 'double_claim', 'dropped_operand')],
        'requirement_map': []}
    (contracts / 'trust.yaml').write_text(yaml.safe_dump(contract, sort_keys=False))
    methods = library / 'methods'
    methods.mkdir()
    method = yaml.safe_load((FIXTURES / 'proof/methods/contract-fixture-1.yaml').read_text())
    method['c_lowering']['translators'] = [c_lowering.identity()['c_lowering'], cbmc_translator.identity()]
    next(row for row in method['lineup'] if row['tool'] == 'cbmc')['flags'] = list(cbmc_adapter.FROZEN)
    next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')['flags'] += [
        '-rte-initialized', '@all', '-wp-no-filter-init', '-machdep', 'x86_64']
    (methods / 'contract-fixture-1.yaml').write_text(yaml.safe_dump(method, sort_keys=False))
    marker = tmp_path / 'must-not-launch-solver'
    mutation = (f'    import yaml\n    path = Path({str(semantics)!r})\n'
                '    data = yaml.safe_load(path.read_text())\n'
                '    data["rules"][-1]["statement"] = "Changed after validation."\n'
                '    path.write_text(yaml.safe_dump(data, sort_keys=False))\n') if mutate else ''
    version_only = tmp_path / 't28-version-only-adapter.py'
    version_only.write_text('import sys\nfrom pathlib import Path\n'
                            'if sys.argv[1:] == ["--version"]:\n' + mutation +
                            '    print("6.11"); sys.exit(0)\n'
                            f'Path({str(marker)!r}).touch()\nraise SystemExit(99)\n')
    frama = tmp_path / 't28-scripted-typechecker.py'
    frama.write_text('import sys\nfrom pathlib import Path\n'
                     'if sys.argv[1:] == ["-version"]:\n' + mutation +
                     '    print("33.0"); sys.exit(0)\n'
                     f'if "-wp" in sys.argv: Path({str(marker)!r}).touch(); sys.exit(99)\n'
                     'raise SystemExit(0)\n')
    why3 = tmp_path / 'scripted-why3.conf'
    labels = {'z3': 'Z3', 'cvc5': 'CVC5', 'alt-ergo': 'Alt-Ergo'}
    why3.write_text(''.join(f'[prover]\nname = "{labels[row["tool"]]}"\nversion = "{row["version"]}"\n'
                            'command = "/usr/bin/false"\n'
                            for row in method['lineup'] if row['tool'] in labels))
    records = make_records(tmp_path)
    result = run_swdb('prove', '--records', records.path, '--summary', contract['id'], '--adapter', adapter,
                      '--bounds', '{"threads": 1, "input_size": 1}', '--runs-dir', tmp_path / 'runs',
                      '--format', 'json', env={'SWDB_CBMC': f'{sys.executable} {version_only}',
                                              'SWDB_FRAMA_C': f'{sys.executable} {frama}' if adapter == 'wp' else 'none',
                                              'WHY3CONFIG': str(why3),
                                              'SWDB_VERIFIER_LOCK': str(tmp_path / 'standin-only.lock')})
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

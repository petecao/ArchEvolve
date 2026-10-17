"""2026-10-16 ET. Root-admitted original-partial initialized-u32 actual pair.

An opt-in test exit reports workflow checks only. Source/body/hardware/current0.2
and whole-interface acceptance require their independent evidence and decisions.
"""
import hashlib
import json
import os
import re
from pathlib import Path

import pytest
import yaml

from swdb.acsl_subset import tokens
from swdb.dx100_initialized_register_model import STATEMENT
from swdb.dx100_initialized_register_source import KIND, PARTIAL_CONTRACT, PARTIAL_METHOD, SEMANTICS_ID
from testkit.dx100_initialized_register import prove_initialized_register
from testkit.dx100_initialized_register_outcomes import assert_initialized_native_outcome


@pytest.mark.skipif(os.environ.get('SWDB_DX100_INITIALIZED_REGISTER_ACTUAL') != '1', reason='requires root source/runtime/guard admission')
@pytest.mark.parametrize('expected', [711, 1107], ids=['correct-initialized-result', 'wrong-crossregister-result'])
def test_actual_initialized_u32_original_partial_pair(tmp_path, expected):
    result, records, entry, marker = prove_initialized_register(tmp_path, expected, actual=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists(), 'named stand-ins must not run in an actual profile'
    record = yaml.safe_load((records.path / json.loads(result.stdout)['path']).read_text())
    assert record['subject'] == {'kind': 'partial_library_summary', 'id': PARTIAL_CONTRACT}
    assert record['pins']['method_version']['id'] == PARTIAL_METHOD
    assert record['pins']['proof_semantics'] == {'id': SEMANTICS_ID, 'sha256': hashlib.sha256(entry.read_bytes()).hexdigest()}
    settings = record['settings']['proof_semantics']
    assert settings['unit_requires'] == [] and settings['unit_ensures'] == []
    assert settings['original_assigns_frame'] == ['REG_count', 'SPD_count', 'region_count', '__swdb_dx_reg_words[0..1]']
    assert settings['unit_correctness_policy'] == {
        'kind': 'partial-normal-return-v1', 'source_policy': KIND, 'semantics': record['pins']['proof_semantics']}
    assert settings['termination_policy'] == 'conditional normal return; no hardware liveness'
    definitions = settings['source_definitions']
    assert definitions and {c['call'] for c in definitions} == {'init_MAA', 'get_new_reg', 'get_reg'}
    assert all(c['kind'] == KIND for c in definitions)
    assert record['proof_setup_check']['verdict'] == 'passed'
    assert record['proof_setup_check']['hashes']['dx100_initialized_register_source']
    assert record['settings']['verifier_launched'] is True
    flags = record['settings']['flags']
    assert all(f in flags for f in ('-wp-rte', '-rte-initialized', '-wp-no-filter-init', '-wp-smoke-tests'))
    for name, value in [('-rte-initialized', '@all'), ('-wp-cache', 'none'), ('-wp-par', '1'), ('-wp-timeout', '30')]:
        assert flags.count(name) == 1 and flags[flags.index(name) + 1] == value
    # Frama33's source-pinned smoke default is 2 seconds; no override is added.
    assert '-wp-smoke-timeout' not in flags
    assert flags.count('-wp-prover') == 1
    assert set(flags[flags.index('-wp-prover') + 1].split(',')) == {'z3', 'cvc5', 'alt-ergo'}
    sentences = [a['sentence'] for a in record['assumptions']]
    assert STATEMENT in sentences
    assert not any('dx_state_initialized' in s or 'as if it finished at issue' in s for s in sentences)
    for evidence in [record['evidence']['adapter_log'], *record['evidence']['reports']]:
        assert hashlib.sha256(Path(evidence['path']).read_bytes()).hexdigest() == evidence['sha256']
    reports = {}
    for evidence in record['evidence']['reports']:
        reports.setdefault(evidence.get('name'), []).append(evidence)
    assert len(reports.get('wp_input', [])) == len(reports.get('wp_inventory', [])) == 1
    text = Path(reports['wp_input'][0]['path']).read_text()
    assert text.count('/* swdb-anchor trust_fixture.contract */') == 1
    unit = text.split('/* swdb-anchor trust_fixture.contract */', 1)[1]
    formal = re.match(r'\s*/\*@(?P<contract>.*?)\*/\s*int trust_fixture\(void\)\s*\{', unit, re.S)
    assert formal is not None
    frames = re.findall(r'\bassigns\b([^;]*);', formal['contract'])
    assert len(frames) == 1
    assert [token.text for token in tokens(frames[0])] == [
        'REG_count', ',', 'SPD_count', ',', 'region_count', ',', '__swdb_dx_reg_words', '[', '0', '..', '1', ']']
    assert r'requires 0 <= REG_count <= 31;' in text
    assert 'get_new_reg_unsigned_int_args1(7' in text and 'get_new_reg_unsigned_int_args1(11' in text
    assert text.count(r'terminates \false;') == 3
    assert_initialized_native_outcome(record, expected)

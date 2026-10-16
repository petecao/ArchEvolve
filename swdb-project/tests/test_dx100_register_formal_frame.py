"""2026-10-16 ET. Public validation of the register frame's declaration scope.

The scripted parser checks one declaration-visibility rule; it is not Frama-C
and grants no ACSL, solver, source-model, or hardware correctness acceptance.
"""
import json
import sys

import pytest
import yaml

from conftest import run_swdb
from testkit.dx100_register import prove_register


@pytest.mark.parametrize('case', ['correct-result', 'wrong-result', 'unknown-bank', 'no-register-policy'])
def test_register_formal_half_declares_only_the_admitted_bank(tmp_path, case):
    expected = 1107 if case == 'wrong-result' else 711
    result, records, _, marker = prove_register(tmp_path, expected)
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker.exists(), 'fixture uses the explicitly scripted exit99 verifier'
    contract_path = tmp_path / 'library/rewrite_contracts/trust.yaml'
    contract = yaml.safe_load(contract_path.read_text())
    if case == 'unknown-bank':
        contract['clauses'][0]['acsl']['text'] = contract['clauses'][0]['acsl']['text'].replace(
            '__swdb_dx_reg_words', '__swdb_dx_unknown_words')
    if case == 'no-register-policy':
        contract['proof_unit'].pop('correctness_policy')
    contract_path.write_text(yaml.safe_dump(contract, sort_keys=False))
    parser = tmp_path / 'declaration-visibility-only.py'
    observations = tmp_path / 'declaration-visibility.jsonl'
    parser.write_text('''import json,re,sys
from pathlib import Path
if sys.argv[1:] == ['-version']:
    print('33.0'); raise SystemExit(0)
assert '-wp' not in sys.argv, 'this control must never launch WP'
source = Path(sys.argv[-1]).read_text()
uses = [(m.start(),m.group(1)) for m in re.finditer(r'assigns\\s+(__swdb_dx_\\w+)\\[0\\.\\.1\\]', source)]
declarations = [(m.start(),m.group(1)) for m in re.finditer(r'static\\s+unsigned\\s+int\\s+(__swdb_dx_\\w+)\\[32\\]\\s*;', source)]
visible = all(sum(name == symbol and at < use for at,name in declarations) == 1 for use,symbol in uses)
with Path(''' + repr(str(observations)) + ''').open('a') as out:
    out.write(json.dumps({'source':source,'uses':len(uses),'declarations':len(declarations),'visible':visible})+'\\n')
if not visible:
    print('[kernel:annot-error] formal_half.c:5: Warning: unbound logic variable __swdb_dx_reg_words. Ignoring specification of function trust_fixture')
    raise SystemExit(1)
''')
    checked = run_swdb('validate', '--records', records.path, '--library', tmp_path / 'library',
                       env={'SWDB_FRAMA_C': f'{sys.executable} {parser}', 'SWDB_CBMC': 'none'})
    rows = [json.loads(line) for line in observations.read_text().splitlines()]
    framed = [row for row in rows if row['uses']]
    if case in {'unknown-bank', 'no-register-policy'}:
        assert checked.returncode != 0, checked.stdout + checked.stderr
        assert 'unbound logic variable' in checked.stderr
        assert framed and any(not row['visible'] for row in framed)
        return
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert framed and all(row['visible'] for row in framed)
    assert all(f'assigns __swdb_dx_reg_words[0..1]; ensures \\result == {expected};' in row['source']
               for row in framed), 'the original two-cell frame and result clause remain intact'
    assert all('static unsigned int __swdb_dx_reg_words[32];' in row['source']
               and 'set_reg_unsigned_int' not in row['source']
               and 'get_reg_unsigned_int' not in row['source'] for row in framed)


def test_unknown_register_semantics_refuses_before_verifier_launch(tmp_path):
    def unknown_semantics(contract):
        contract['proof_unit']['correctness_policy']['semantics']['id'] = 'semantics.missing_register'
    result, _, _, marker = prove_register(tmp_path, 711, contract_mutate=unknown_semantics)
    assert result.returncode != 0
    assert not marker.exists()
    assert 'correctness_policy' in result.stderr
    assert 'Traceback' not in result.stderr

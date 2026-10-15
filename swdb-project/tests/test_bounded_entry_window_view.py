"""Binding regression at the checked view API; created 2026-10-15 ET.

The paired C/C++ differential cannot detect a binding change shared by both
generated views. This checks that the preparer preserves the original scope.
"""
import pytest
import yaml

from conftest import FIXTURES

from swdb import bounded_entry_windows as view, c_lowering, cbmc_translator as tr


@pytest.mark.skipif(bool(c_lowering.locate().missing), reason='real Clang AST binds source declarations')
@pytest.mark.parametrize('hidden_header', [False, True])
def test_generated_entry_snapshot_cannot_shadow_a_source_global(tmp_path, hidden_header):
    case = yaml.safe_load((FIXTURES / 'proof/regression_corpus/bounded-window-snapshot-global-shadow.yaml').read_text())
    given = case['input']
    source = tmp_path / 'shadow.cc'
    if hidden_header:
        (tmp_path / 'state.h').write_text('int swdb_window_extent_p = 9;\n#define STATE_LOOKUP swdb_window_extent_p\n')
        source.write_text('#include "state.h"\n'
            'int shadow(int *p, int n) { (void)(p+n); return STATE_LOOKUP; }\n')
    else:
        source.write_text(given['source'])
    declarations = given['array_domains']
    lowered = c_lowering.lower(source, 'shadow', array_domains=declarations,
        array_domain_contract={'id': 'contract.fixture_shadow', 'sha256': 'a'*64})
    interface = tr.Interface('shadow', 'int', lowered.parameters)
    _, plan = tr.harness(interface, [tr.Clause('requires', given['requires'], 'fixture#pre')],
        sizes={'n': given['capacity']}, cap=given['capacity'], array_domains=declarations)
    with pytest.raises(view.Refused, match='reserved.*name|instrumentation name'):
        view.prepare(lowered, source, plan.array_domains)

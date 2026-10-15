"""Binding regression at the checked view API; created 2026-10-15 ET.

The paired C/C++ differential cannot detect a binding change shared by both
generated views. This checks that the preparer preserves the original scope.
"""
import pytest

from swdb import bounded_entry_windows as view, c_lowering, cbmc_translator as tr


@pytest.mark.skipif(bool(c_lowering.locate().missing), reason='real Clang AST binds source declarations')
def test_generated_entry_snapshot_cannot_shadow_a_source_global(tmp_path):
    source = tmp_path / 'shadow.cc'
    source.write_text('int swdb_window_extent_p = 9;\n'
        'int shadow(int *p, int n) { (void)(p+n); return swdb_window_extent_p; }\n')
    declarations = {'p': {'extent': 'n'}}
    lowered = c_lowering.lower(source, 'shadow', array_domains=declarations,
        array_domain_contract={'id': 'contract.fixture_shadow', 'sha256': 'a'*64})
    interface = tr.Interface('shadow', 'int', lowered.parameters)
    _, plan = tr.harness(interface, [tr.Clause('requires', 'n == 2', 'fixture#pre')],
        sizes={'n': 4}, cap=4, array_domains=declarations)
    with pytest.raises(view.Refused, match='reserved.*name|instrumentation name'):
        view.prepare(lowered, source, plan.array_domains)

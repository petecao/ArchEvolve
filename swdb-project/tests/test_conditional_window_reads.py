"""Pure conditional-return reads at public lowering/preparation seams, 2026-10-15 ET."""
import pytest
from swdb import c_lowering, wp_pointer_bounds

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')


def lower(tmp_path, expression):
    path = tmp_path/'unit.cc'
    path.write_text('int unit(int *a,int n,int x) { return '+expression+'; }\n')
    return c_lowering.lower(path, 'unit', array_domains={'a': {'extent': 'n'}},
                            array_domain_contract='contract.fixture_conditional')


def test_conditional_return_checks_only_the_evaluated_array_branch(tmp_path):
    lowered = lower(tmp_path, 'x + (n > 0 ? a[0] : 0)')
    text, report = wp_pointer_bounds.prepare(lowered, lowered.text)
    access, = [r for r in report['sites'] if r.get('kind') == 'access']
    assert access['evaluation_path'] == ['(((integer)n) > 0)']
    assert '==>' in access['window_guard']
    assert 'assert swdb_window_access_' in text
    assert '(n > 0) ? a[0] : 0' in text
    assert 'requires' not in text


@pytest.mark.parametrize('expression', [
    'n++ > 0 ? a[0] : 0',
    'n > 0 && x > 0 ? a[0] : 0',
    'n > 0 ? a[x++] : 0',
    'n > 0 ? a[0] : __atomic_fetch_add(&x,1,0)',
])
def test_effects_or_short_circuit_in_conditional_return_remain_refused(tmp_path, expression):
    lowered = lower(tmp_path, expression)
    with pytest.raises(wp_pointer_bounds.Refused):
        wp_pointer_bounds.prepare(lowered, lowered.text)

"""Entry-window mathematical bindings; created 2026-10-15 ET (tickets24/36)."""
import itertools

import pytest

from swdb import array_domains


PARAMETERS = [('a', 'const int *', True), ('n', 'int', False), ('m', 'unsigned int', False)]


def test_entry_window_freezes_every_scalar_in_mathematical_integer_arithmetic():
    bound = array_domains.bind({'a': {'extent': 'n * m - 1'}}, PARAMETERS)
    window = bound['windows']['a']
    assert window['element_type'] == 'int'
    assert window['parameters'] == ['m', 'n']
    assert window['entry_acsl'] == '((\\at((integer)n,Pre) * \\at((integer)m,Pre)) - 1)'
    assert len(bound['declarations_sha256']) == 64


@pytest.mark.parametrize('expression', ['n-m', '-n*m+2', '(n-2)*(m+1)', 'n*n-m*m'])
def test_interval_contains_all_integer_draws_including_negative_products(expression):
    tree = array_domains.bind({'a': {'extent': expression}}, PARAMETERS)['windows']['a']['extent_tree']
    low, high = array_domains.interval(tree, {'n': (-3, 4), 'm': (0, 5)})
    for n, m in itertools.product(range(-3, 5), range(6)):
        value = eval(expression, {'__builtins__': {}}, {'n': n, 'm': m})
        assert low <= value <= high


def test_interval_uses_unbounded_mathematical_products():
    tree = array_domains.bind({'a': {'extent': 'n*m'}}, PARAMETERS)['windows']['a']['extent_tree']
    assert array_domains.interval(tree, {'n': (2**64-1, 2**64-1), 'm': (2, 2)}) == (2**65-2, 2**65-2)


@pytest.mark.parametrize('bounds', [{'n': (0, 3)}, {'n': (0, 3), 'm': (4, 2)}, {'n': (False, 3), 'm': (0, 2)}])
def test_interval_refuses_missing_invalid_or_boolean_draw_bounds(bounds):
    tree = array_domains.bind({'a': {'extent': 'n*m'}}, PARAMETERS)['windows']['a']['extent_tree']
    with pytest.raises(array_domains.Refused):
        array_domains.interval(tree, bounds)


def test_binding_does_not_accept_a_valid_shape_with_a_noninteger_parameter():
    with pytest.raises(array_domains.Refused, match='integer parameter'):
        array_domains.bind({'a': {'extent': 'm'}}, [('a', 'int *', True), ('m', 'double', False)])

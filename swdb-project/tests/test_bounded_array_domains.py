"""Bounded harness domain planning controls; created 2026-10-15 ET.

The public harness seam plans buffer capacity, never certifies source accesses.
"""
import pytest

from swdb import cbmc_translator as tr

UNIT = tr.Interface('touch', 'void', (('a', 'int *', True), ('n', 'int', False)))


def test_signed_negative_draws_cannot_silently_narrow_to_nonnegative_extents():
    with pytest.raises(tr.Untranslatable, match='array domain.*negative'):
        tr.harness(UNIT, [], sizes={'n': 3}, cap=3, array_domains={'a': {'extent': 'n'}})


def test_existing_nonnegative_requires_permits_planning_without_new_assumptions():
    rows = [tr.Clause('requires', 'n >= 0', 'contract#nonnegative')]
    legacy, _ = tr.harness(UNIT, rows, sizes={'n': 3}, cap=3)
    planned, plan = tr.harness(UNIT, rows, sizes={'n': 3}, cap=3, array_domains={'a': {'extent': 'n'}})
    assert planned == legacy
    assert plan.array_domains['scalar_intervals']['n'] == [0, 3]
    window = plan.array_domains['windows']['a']
    assert window['extent_interval'] == [0, 3]
    assert window['physical_capacity'] == 3 and window['nonnull'] is True
    assert window['entry_acsl'] == r'\at((integer)n,Pre)'
    assert plan.array_domains['admission'] == 'planner_only'
    assert plan.array_domains['source_operations_checked'] is False
    assert plan.array_domains['scalar_provenance']['n'][-1]['clause'] == 'contract#nonnegative'


@pytest.mark.parametrize('requires', ['n >= 0 || n < 0', 'n >= 0 ==> n < 4',
                                      'n >= 0 && n < 4 ==> n == 0', '!(n < 0)',
                                      'n + 0 >= 0', '(n >= 0 ? n < 4 : n < 0)'])
def test_conditional_or_unsupported_requires_cannot_narrow_draws(requires):
    with pytest.raises(tr.Untranslatable, match='negative'):
        tr.harness(UNIT, [tr.Clause('requires', requires, 'c#r')], sizes={'n': 3}, cap=3,
                   array_domains={'a': {'extent': 'n'}})


@pytest.mark.parametrize('extent,cap,reason', [('n + 1', 3, 'exceeds physical capacity'),
                                            ('n * 18446744073709551615', 3, '55340232221128654845'),
                                            ('n - n', 3, 'negative')])
def test_capacity_uses_all_draws_and_mathematical_integer_arithmetic(extent, cap, reason):
    with pytest.raises(tr.Untranslatable, match=reason):
        tr.harness(UNIT, [tr.Clause('requires', 'n >= 0', 'c#r')], sizes={'n': 3}, cap=cap,
                   array_domains={'a': {'extent': extent}})


def test_repeated_variable_correlation_is_conservatively_refused():
    # n-n is mathematically zero, but interval planning is allowed to overapproximate.
    with pytest.raises(tr.Untranslatable, match='negative'):
        tr.harness(UNIT, [tr.Clause('requires', 'n >= 0', 'c#r')], sizes={'n': 3}, cap=3,
                   array_domains={'a': {'extent': 'n - n'}})


@pytest.mark.parametrize('requires,expected', [('(0 <= n && n < 3)', [0, 2]),
                                              ('0 <= n <= 2', [0, 2]), ('2 == n', [2, 2])])
def test_original_conjunction_and_chain_bounds_have_exact_provenance(requires, expected):
    text, plan = tr.harness(UNIT, [tr.Clause('requires', requires, 'c#r')], sizes={'n': 3}, cap=3,
                            array_domains={'a': {'extent': 'n'}})
    assert plan.array_domains['windows']['a']['extent_interval'] == expected
    assert 'size bound' in text and text.count('SWDB_ASSUME(') == 2


def test_empty_existing_contract_domain_is_refused_instead_of_vacuously_accepted():
    with pytest.raises(tr.Untranslatable, match='empty bounded scalar domain'):
        tr.harness(UNIT, [tr.Clause('requires', 'n >= 4', 'c#r')], sizes={'n': 3}, cap=3,
                   array_domains={'a': {'extent': 'n'}})


def test_plan_does_not_reinterpret_physical_validity_as_exact_logical_allocation():
    rows = [tr.Clause('requires', r'\valid(a + (0 .. 2))', 'c#valid')]
    original, legacy = tr.harness(UNIT, rows, sizes={'n': 3}, cap=3)
    text, plan = tr.harness(UNIT, rows, sizes={'n': 3}, cap=3, array_domains={'a': {'extent': '1'}})
    assert original == text and plan.draws == legacy.draws
    assert plan.array_domains['windows']['a']['extent_interval'] == [1, 1]
    assert plan.array_domains['windows']['a']['physical_capacity'] == 3


def test_zero_extent_retains_nonnull_real_buffer_and_zero_element_draws():
    text, plan = tr.harness(UNIT, [], sizes={'n': 0}, cap=0, array_domains={'a': {'extent': '0'}})
    assert 'swdb_buf_a[1]' in text
    assert plan.array_domains['windows']['a']['allocated_elements'] == 1
    assert not any(draw['role'] == 'element' for draw in plan.draws)


def test_changed_declarations_are_rebound_instead_of_trusting_previous_plan_metadata():
    declarations = {'a': {'extent': '1'}}
    _, first = tr.harness(UNIT, [], sizes={'n': 3}, cap=3, array_domains=declarations)
    first.array_domains['windows']['a']['physical_capacity'] = 100
    declarations['a']['extent'] = '4'
    with pytest.raises(tr.Untranslatable, match='exceeds physical capacity 3'):
        tr.harness(UNIT, [], sizes={'n': 3}, cap=3, array_domains=declarations)


@pytest.mark.parametrize('domains', [[], False, {'a': {'extent': 'n', 'certificate': 'trusted'}}])
def test_malformed_or_forged_declarations_do_not_skip_planning(domains):
    with pytest.raises(tr.Untranslatable, match='array.domain'):
        tr.harness(UNIT, [], sizes={'n': 3}, cap=3, array_domains=domains)


def test_unbounded_unsigned64_comparisons_cannot_justify_math_interval_narrowing():
    unit = tr.Interface('touch', 'void', (('a', 'int *', True), ('n', 'uint64_t', False)))
    with pytest.raises(tr.Untranslatable, match='exceeds physical capacity'):
        tr.harness(unit, [tr.Clause('requires', 'n <= 3', 'c#r')], sizes={}, cap=3,
                   array_domains={'a': {'extent': 'n'}})


def test_runtime_check_refuses_declared_windows_before_reading_or_compiling_source(tmp_path):
    from swdb import check_mode
    library = {'contract': {'proof_unit': {'array_domains': {'a': {'extent': 'n'}}}}}
    with pytest.raises(tr.Untranslatable, match='source-origin.*nonnull'):
        check_mode.run(library, 'contract', tmp_path / 'must-not-read.cc', 'touch', {'threads': 1, 'n': 3},
                       (), 0.0, 'fixture', tmp_path / 'out')
    assert not (tmp_path / 'out' / 'runtime_check.cc').exists()


@pytest.mark.parametrize('requires,extent', [('n >= 010', 'n - 10'),
                                            ('n <= -9223372036854775808', 'n + 9223372036854775808')])
def test_c_literal_radix_or_signedness_cannot_strengthen_math_draw_intervals(requires, extent):
    unit = tr.Interface('touch', 'void', (('a', 'int *', True), ('n', 'long long', False)))
    with pytest.raises(tr.Untranslatable, match='array domain'):
        tr.harness(unit, [tr.Clause('requires', requires, 'c#r')], sizes={'n': 20}, cap=20,
                   array_domains={'a': {'extent': extent}})


def test_imported_summary_domains_cannot_be_replaced_by_unchecked_stub_assumptions():
    rows = [tr.Clause('assigns', r'\nothing', 'summary#frame')]
    with pytest.raises(tr.Untranslatable, match='summary.*call.*array_domains'):
        tr.stub(UNIT, 'void touch(int *a, int n)', rows, 'summary', '0' * 64,
                array_domains={'a': {'extent': 'n'}})

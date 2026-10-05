"""knob_range and schedule_range checks and their controls. Created: 2026-10-04 ET (ticket 68).

Both promoted contracts name these checks; before ticket 68 no run could report them. A candidate
that uses the campaign knob interface with a static_assert certifies (its knob control is rejected
by knob_range even though the out-of-range value also stops its build). A candidate with an
out-of-range assignment or schedule is refused on the matrix by the named check.
"""
import re
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_legality as legality
from swdb.cli import Failure
from swdb.library import Library

from test_certification_controls import _certify, _controls, _replace

ROOT = Path(__file__).resolve().parents[1]


def _entry(name='contract.bfs_read_offload'):
    return Library(ROOT / 'library').get(name)


def test_both_promoted_contracts_name_the_checks_and_are_covered():
    for name in ('contract.bfs_read_offload', 'contract.bc_read_offload'):
        entry = _entry(name)
        assert legality.applies(entry)
        assert legality.clause_check(entry, 'frontier_threshold') == 'knob_range'
        assert legality.clause_check(entry, 'schedule') == 'schedule_range'
    assert set(legality.CHECKS) <= c.producible_checks()


@pytest.mark.parametrize('text,value', [('64', 64), ('(16384/2)', 8192), ('0x10u', 16), ('1<<4', 16),
                                        ('-(7/2)', -3), ('-7%3', -1), ('2147483647L', 2147483647), ('010', 8)])
def test_integer_constant_expressions(text, value):
    assert legality.evaluate(text) == value


@pytest.mark.parametrize('text', ['n', 'static_cast<int>(4)', '(1', '', '1/0', 'sizeof(int)'])
def test_non_constants_are_refused(text):
    with pytest.raises(ValueError):
        legality.evaluate(text)


def _probe(assignments, tile_size=1024):
    entry = _entry()
    text = ''.join(f'swdb_knob_probe_begin {k["name"]} ( {assignments.get(k["name"], legality.knob_macro(k["name"]))} ) '
                   'swdb_knob_probe_end\n' for k in entry['knobs'])
    return legality.knob_check(text, entry, tile_size)


def test_knob_range_reads_assignments_and_keeps_defaults():
    ok, problems, knobs = _probe({})
    assert ok and {k['name']: (k['value'], k['source']) for k in knobs} == {
        'frontier_threshold': (64, 'contract_default'), 'chunk_size': (1024, 'contract_default'),
        'schedule': ('dynamic', 'contract_default'), 'schedule_granularity': (1, 'contract_default')}
    assert _probe({'frontier_threshold': '1', 'chunk_size': '1024', 'schedule': 'static'})[0]
    for bad in ({'frontier_threshold': '0'}, {'chunk_size': '2048'}, {'chunk_size': '0'}, {'schedule': 'guided'},
                {'schedule_granularity': '0'}, {'frontier_threshold': 'threshold_variable'}):
        ok, problems, _ = _probe(bad)
        assert not ok and len(problems) == 1, (bad, problems)


def _schedule(lines, main='main.cc'):
    return legality.schedule_check(f'# 1 "{main}"\n' + '\n'.join(lines) + f'\n# 1 "other.h"\n#pragma omp for schedule(guided)\n',
                                   _entry(), 1024, main)


def test_schedule_range_scans_worksharing_loops_of_the_main_file_only():
    ok, problems, rows = _schedule(['#pragma omp for schedule(dynamic,1)', '#pragma omp parallel for',
                                    '#pragma omp for schedule(monotonic: static, 64) nowait', '#pragma omp barrier',
                                    '#pragma omp simd aligned(p : 16)'])
    assert ok, problems
    assert [(r['kind'], r['chunk']) for r in rows] == [('dynamic', 1), ('default', None), ('static', 64)]
    for bad in ('#pragma omp for schedule(guided)', '#pragma omp parallel for schedule(runtime)',
                '#pragma omp for schedule(dynamic, 0)', '#pragma omp for schedule(dynamic, chunk)',
                '#pragma omp for schedule(auto)'):
        ok, problems, _ = _schedule([bad])
        assert not ok and len(problems) == 1, bad


def test_knob_control_uses_the_campaign_knob_block_or_adds_one():
    entry = _entry()
    campaign = ('// swdb campaign knob values for workload class kronecker\n'
                '#define SWDB_KNOB_FRONTIER_THRESHOLD 1\n#include <x>\n')
    assert legality.knob_control(campaign, entry) == (
        '// swdb campaign knob values for workload class kronecker\n'
        '#define SWDB_KNOB_FRONTIER_THRESHOLD 0\n#include <x>\n')
    plain = '#include <x>\n'
    assert legality.knob_control(plain, entry) == legality.CONTROL_BLOCK + '\n#define SWDB_KNOB_FRONTIER_THRESHOLD 0\n' + plain


def test_schedule_control_sets_guided_on_every_worksharing_loop():
    source = ('#pragma omp parallel\n#pragma omp for schedule(dynamic, (1)) nowait\n'
              '  #pragma omp parallel for reduction(+ : s) // comment\n#pragma omp barrier\n')
    assert legality.schedule_control(source) == (
        '#pragma omp parallel\n#pragma omp for schedule(guided) nowait\n'
        '  #pragma omp parallel for reduction(+ : s) schedule(guided) // comment\n#pragma omp barrier\n')
    with pytest.raises(Failure, match='mutation site: schedule_out_of_range'):
        legality.schedule_control('#pragma omp parallel\n')


def test_contract_pairs_for_the_legality_checks_are_recorded_as_unexercisable():
    entry = _entry()
    controls = [{'id': name, 'status': 'rejected', 'observed_checks': sorted(checks)}
                for name, checks in legality.CONTROLS.items()]
    rows = [r for r in c.clause_controls(entry, controls) if r['clause'] in ('frontier_threshold', 'schedule')]
    assert [(r['clause'], r['control'], r['source'], r['enforceable'], r['matched']) for r in rows] == [
        ('frontier_threshold', 'chunk_off_by_one', 'contract', False, False),
        ('frontier_threshold', 'knob_out_of_range', 'certifier', True, True),
        ('schedule', 'shared_context', 'contract', False, False),
        ('schedule', 'schedule_out_of_range', 'certifier', True, True)]
    assert {r.get('reason') for r in rows if not r['enforceable']} == {'control_cannot_exercise_check'}


# --- real certifications (g++ with OpenMP) ---------------------------------------------------

KNOB_HEADER = ('#ifndef SWDB_KNOB_FRONTIER_THRESHOLD\n#define SWDB_KNOB_FRONTIER_THRESHOLD 64\n#endif\n'
               'static_assert(SWDB_KNOB_FRONTIER_THRESHOLD >= 1, "frontier threshold is outside the contract range");\n')


def knob_interface(source):
    """Ticket 20's rewrite reading its threshold from the campaign knob interface, with a static_assert."""
    source = _replace(source, '#ifndef SWDB_FRONTIER_THRESHOLD\n', KNOB_HEADER + '#ifndef SWDB_FRONTIER_THRESHOLD\n')
    return _replace(source, 'queue.size()>=SWDB_FRONTIER_THRESHOLD;', 'queue.size()>=SWDB_KNOB_FRONTIER_THRESHOLD;')


def guided(source):
    """Correct results, but the accelerated loop's schedule is outside the contract's choices."""
    return _replace(source, '#pragma omp for schedule(dynamic,1)', '#pragma omp for schedule(guided)')


def test_knob_interface_candidate_certifies_and_its_static_assert_does_not_hide_the_control(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, knob_interface)
    assert record['verdict'] == 'certified', _controls(record)
    assert len(record['negative_controls']) == 20
    knob = [x for x in record['negative_controls'] if x['id'] == 'knob_out_of_range']
    # The out-of-range value trips the candidate's static_assert, but knob_range named it first.
    assert all(x['status'] == 'rejected' and x['reason'] == 'knob_range' and x['build']['returncode'] != 0
               for x in knob), knob
    cell = record['matrix'][0]['legality_checks']
    assert [s['status'] for s in cell] == ['passed', 'passed']
    assert {k['name']: k['source'] for k in cell[0]['knobs']}['frontier_threshold'] == 'assignment'
    rows = {(r['clause'], r['source']): r for r in record['clause_controls']}
    assert rows[('frontier_threshold', 'certifier')]['matched'] and rows[('schedule', 'certifier')]['matched']


def test_out_of_range_schedule_is_refused_by_schedule_range(tmp_path, monkeypatch):
    record = _certify(tmp_path, monkeypatch, guided)
    assert record['verdict'] == 'failed'
    assert {x['reason'] for x in record['matrix']} == {'schedule_range'}
    # The runs themselves pass: only the named structural check refuses the candidate.
    assert all(re.search(r'Verification\s*:?\s*PASS', x['run']['stdout']) for x in record['matrix'])

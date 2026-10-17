"""knob_range and schedule_range checks and their controls. Created: 2026-10-04 ET (ticket 68).

Both promoted contracts name these checks; before ticket 68 no run could report them. A candidate
that uses the campaign knob interface with a static_assert certifies (its knob control is rejected
by knob_range even though the out-of-range value also stops its build). A candidate with an
out-of-range assignment or schedule is refused on the matrix by the named check.
"""
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


def test_knob_interface_candidate_certifies_and_its_static_assert_does_not_hide_the_control(tmp_path, monkeypatch, *, certification_store):
    record = _certify(tmp_path, monkeypatch, knob_interface, certification_store=certification_store)
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


def test_out_of_range_schedule_is_refused_by_schedule_range(tmp_path, monkeypatch, *, certification_store):
    record = _certify(tmp_path, monkeypatch, guided, certification_store=certification_store)
    assert record['verdict'] == 'failed'
    assert {x['reason'] for x in record['matrix']} == {'schedule_range'}
    # The runs themselves pass: only the named structural check refuses the candidate.
    # Ticket 70 (certify 1.3): the result check is recorded per cell, never read from printed output.
    assert all(x['result_check']['passed'] and x['observed_checks'] == [] for x in record['matrix'])


# --- rules v2 (certify 1.6; 2026-10-05 ET review fixes C4 and C24) ------------------------------------

T20_KNOBS = ('#ifndef SWDB_FRONTIER_THRESHOLD\n#define SWDB_FRONTIER_THRESHOLD 64\n#endif\n'
             '#ifndef SWDB_CHUNK_SIZE\n#define SWDB_CHUNK_SIZE TILE_SIZE\n#endif\n'
             'bool a = queue.size()>=SWDB_FRONTIER_THRESHOLD; size_t b = SWDB_CHUNK_SIZE;\n')


def _probe_v2(source, expansions, tile_size=1024):
    """knob_check v2 on a probe text whose spellings expand as given (unexpanded when absent)."""
    entry = _entry()
    text = ''.join(f'swdb_knob_probe_begin {k["name"]} swdb_knob_spelling_{i} ( {expansions.get(m, m)} ) '
                   'swdb_knob_probe_end\n'
                   for k in entry['knobs'] for i, m in enumerate(legality.knob_spellings(k['name'])))
    return legality.knob_check(text, entry, tile_size, rules='v2', source=source)


def _rows(knobs):
    return {k['name']: (k['value'], k['source'], k['macro']) for k in knobs}


def test_v2_reads_the_spelling_the_promoted_patches_use():
    ok, problems, knobs = _probe_v2(T20_KNOBS, {'SWDB_FRONTIER_THRESHOLD': '64', 'SWDB_CHUNK_SIZE': '1024'})
    assert ok, problems
    assert _rows(knobs) == {'frontier_threshold': (64, 'assignment', 'SWDB_FRONTIER_THRESHOLD'),
                            'chunk_size': (1024, 'assignment', 'SWDB_CHUNK_SIZE'),
                            'schedule': (None, 'unverified', None),
                            'schedule_granularity': (None, 'unverified', None)}


def test_a_threshold_of_zero_is_rejected_by_knob_range():
    """C4: ticket 20's spelling with a threshold of 0. Rules v1 (certify 1.3-1.5) probed only
    SWDB_KNOB_FRONTIER_THRESHOLD and recorded the contract default 64; v2 reads the 0."""
    source = T20_KNOBS.replace('SWDB_FRONTIER_THRESHOLD 64', 'SWDB_FRONTIER_THRESHOLD 0')
    ok, problems, knobs = _probe_v2(source, {'SWDB_FRONTIER_THRESHOLD': '0', 'SWDB_CHUNK_SIZE': '1024'})
    assert not ok and len(problems) == 1 and 'SWDB_FRONTIER_THRESHOLD' in problems[0]
    assert _rows(knobs)['frontier_threshold'] == (0, 'assignment', 'SWDB_FRONTIER_THRESHOLD')
    v1_ok, _, v1_knobs = _probe({})   # the v1 probe of the same candidate never sees the short spelling
    assert v1_ok and _rows(v1_knobs)['frontier_threshold'] == (64, 'contract_default', 'SWDB_KNOB_FRONTIER_THRESHOLD')


def test_a_knob_the_candidate_does_not_use_is_unverified_never_the_default():
    ok, problems, knobs = _probe_v2('int x = 0;\n', {})
    assert {name: row[1] for name, row in _rows(knobs).items()} == dict.fromkeys(
        ('frontier_threshold', 'chunk_size', 'schedule', 'schedule_granularity'), 'unverified')
    # Only the knob whose clause names knob_range must be verified.
    assert not ok and len(problems) == 1 and problems[0].startswith('frontier_threshold: no assignment')


def test_used_spellings_must_agree_and_unused_defaults_do_not_count():
    both = T20_KNOBS + 'bool c = queue.size()>=SWDB_KNOB_FRONTIER_THRESHOLD;\n'
    ok, problems, _ = _probe_v2(both, {'SWDB_FRONTIER_THRESHOLD': '64', 'SWDB_KNOB_FRONTIER_THRESHOLD': '1',
                                       'SWDB_CHUNK_SIZE': '1024'})
    assert not ok and 'disagree' in problems[0]
    # A short-form default the code never reads (the campaign knob interface is read) does not count.
    interface = ('#define SWDB_KNOB_FRONTIER_THRESHOLD 1\n#ifndef SWDB_FRONTIER_THRESHOLD\n'
                 '#define SWDB_FRONTIER_THRESHOLD 64\n#endif\nbool c = n >= SWDB_KNOB_FRONTIER_THRESHOLD;\n')
    ok, problems, knobs = _probe_v2(interface, {'SWDB_FRONTIER_THRESHOLD': '64', 'SWDB_KNOB_FRONTIER_THRESHOLD': '1'})
    assert ok, problems
    assert _rows(knobs)['frontier_threshold'] == (1, 'assignment', 'SWDB_KNOB_FRONTIER_THRESHOLD')


def test_used_spellings_skip_guards_definitions_and_comments():
    spellings = legality.knob_spellings('frontier_threshold')
    text = ('#ifndef SWDB_FRONTIER_THRESHOLD\n#define SWDB_FRONTIER_THRESHOLD 64\n#endif\n'
            '#if defined(SWDB_KNOB_FRONTIER_THRESHOLD)\n#endif\n// SWDB_KNOB_FRONTIER_THRESHOLD\n')
    assert legality.used_spellings(text, spellings) == set()
    assert legality.used_spellings(text + '#define T SWDB_FRONTIER_THRESHOLD\n', spellings) == {'SWDB_FRONTIER_THRESHOLD'}
    assert legality.used_spellings(text + 'static_assert(SWDB_KNOB_FRONTIER_THRESHOLD > 0, "");\n', spellings) == \
        {'SWDB_KNOB_FRONTIER_THRESHOLD'}


def test_v2_knob_control_sets_the_spelling_the_candidate_reads():
    entry = _entry()
    assert legality.knob_control(T20_KNOBS, entry, 'v2') == (
        legality.CONTROL_BLOCK + '\n#define SWDB_FRONTIER_THRESHOLD 0\n' + T20_KNOBS)
    campaign = ('// swdb campaign knob values for workload class kronecker\n'
                '#define SWDB_KNOB_FRONTIER_THRESHOLD 1\n#include <x>\nint t = SWDB_KNOB_FRONTIER_THRESHOLD;\n')
    assert legality.knob_control(campaign, entry, 'v2') == campaign.replace('THRESHOLD 1', 'THRESHOLD 0')
    # v1 (certify 1.3-1.5) is unchanged: it sets SWDB_KNOB_<NAME>, which ticket 20's code never reads.
    assert legality.knob_control(T20_KNOBS, entry) == (
        legality.CONTROL_BLOCK + '\n#define SWDB_KNOB_FRONTIER_THRESHOLD 0\n' + T20_KNOBS)


def test_schedule_control_v2_also_mutates_pragma_operators():
    """C24: a candidate that writes its worksharing loops only with _Pragma no longer aborts."""
    source = ('_Pragma("omp parallel")\n{\n  _Pragma ( "omp for schedule(dynamic, 1) nowait" )\n'
              '  for (int i = 0; i < n; ++i) {}\n}\n#define LOOP _Pragma("omp parallel for")\n_Pragma("omp barrier")\n')
    with pytest.raises(Failure, match='mutation site: schedule_out_of_range'):
        legality.schedule_control(source)
    assert legality.schedule_control(source, 'v2') == source.replace(
        '_Pragma ( "omp for schedule(dynamic, 1) nowait" )', '_Pragma("omp for schedule(guided) nowait")').replace(
        '_Pragma("omp parallel for")', '_Pragma("omp parallel for schedule(guided)")')
    mixed = '#pragma omp for schedule(static)\n' + source
    assert legality.schedule_control(mixed, 'v2').count('schedule(guided)') == 3


def zero_threshold(source):
    """Ticket 20's rewrite with its frontier threshold default set to 0 (outside the contract's 1..2^31-1)."""
    return _replace(source, '#define SWDB_FRONTIER_THRESHOLD 64', '#define SWDB_FRONTIER_THRESHOLD 0')


def pragma_operators(source):
    """Ticket 20's rewrite with both of its worksharing loops (in TDStep) written as _Pragma operators."""
    start = source.index('void TDStep(')
    end = source.index('\nint64_t TDStep2(', start)
    region = _replace(source[start:end], '#pragma omp for schedule(dynamic,1)', '_Pragma("omp for schedule(dynamic,1)")')
    region = _replace(region, '#pragma omp for nowait', '_Pragma("omp for nowait")')
    return source[:start] + region + source[end:]


def test_a_zero_threshold_is_refused_by_knob_range_under_1_6(tmp_path, monkeypatch, *, certification_store):
    record = _certify(tmp_path, monkeypatch, zero_threshold, certification_store=certification_store)
    # 2026-10-09 ET: the default is 1.7, which keeps 1.6's legality rules v2.
    assert record['command']['version'] == c.VERSION == '1.7' and record['verdict'] == 'failed'
    assert {x['reason'] for x in record['matrix']} == {'knob_range'}
    knob = {k['name']: k for k in record['matrix'][0]['legality_checks'][0]['knobs']}['frontier_threshold']
    assert (knob['value'], knob['source'], knob['macro']) == (0, 'assignment', 'SWDB_FRONTIER_THRESHOLD')


def test_a_pragma_operator_candidate_certifies_under_1_6(tmp_path, monkeypatch, *, certification_store):
    record = _certify(tmp_path, monkeypatch, pragma_operators, certification_store=certification_store)
    assert record['verdict'] == 'certified', _controls(record)
    schedule = [x for x in record['negative_controls'] if x['id'] == 'schedule_out_of_range']
    assert len(schedule) == 2 and all(x['status'] == 'rejected' and x['reason'] == 'schedule_range' for x in schedule)

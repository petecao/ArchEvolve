"""The strict layer's two wait rules: the old rule and the gem5 DX100 rule.

Created: 2026-10-09 ET (Yan-Ru's request). Research 14
(.scratch/formal-verification-2026-10-09/research/14-dx100-wait-rule.md) read gem5's DX100 device and
refuted the strict layer's old wait rule. The gem5 rule is compiled in with -DSWDB_STRICT_WAIT_RULE_GEM5
(candidate certify 1.7, lowering certify 1.2); without it the old rule runs unchanged (1.6 and earlier,
lowering 1.1). Every scenario here runs under both rules. Updated 2026-10-09 ET: rule 5, the dispatch
stall on tiles (IF.cc:193-212), is part of the gem5 rule.
"""
import subprocess
from pathlib import Path

import pytest

from swdb import certification as c
from swdb import certification_process as process
from swdb import certification_procedures as procedures

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'library'
SCENARIOS = Path(__file__).resolve().parent / 'fixtures/strict_wait_rule.cc'
GEM5 = '-DSWDB_STRICT_WAIT_RULE_GEM5'
SENTINEL = -1515870811          # 0xa5a5a5a5 as int32: what a CPU read sees before a covering wait
TILE = 1024


@pytest.fixture(scope='module', params=['old', 'gem5'])
def scenarios(request, tmp_path_factory):
    folder = tmp_path_factory.mktemp('strict-wait-' + request.param)
    executable = folder / 'strict_wait_rule'
    build = c.compile_cpp(SCENARIOS, executable, LIBRARY, tile_size=TILE, threads=4,
                          defines=[GEM5] if request.param == 'gem5' else [])
    assert build['returncode'] == 0, build['stderr']
    return request.param, executable


def run(executable, scenario):
    process = subprocess.run([str(executable), scenario], capture_output=True, text=True, timeout=60)
    values = dict(line.split('=', 1) for line in process.stdout.splitlines() if '=' in line)
    return process, {key: int(value) for key, value in values.items()}


def test_a_wait_on_a_stores_source_tile_covers_the_store_only_under_gem5(scenarios):
    """(a) The authors' unmodified TDStepMAA: store, wait_ready(tile3) (its source), read tile5."""
    rule, executable = scenarios
    result, values = run(executable, 'store_source_wait')
    assert result.returncode == 0, result.stderr
    if rule == 'gem5':
        assert values == {'ready5': 1, 'tile5_0': -1, 'tile4_0': 1}      # real old parent value
    else:
        assert values['ready5'] == 0 and values['tile5_0'] == SENTINEL     # the old rule: not covered


def test_a_wait_on_the_result_tile_covers_the_store_under_both_rules(scenarios):
    _, executable = scenarios
    result, values = run(executable, 'store_result_wait')
    assert result.returncode == 0 and values == {'ready5': 1, 'tile5_0': -1, 'tile4_0': 1}


def test_a_deleted_store_wait_is_caught_under_both_rules(scenarios):
    """(b) No wait at all: tile5 stays not ready, reads the sentinel, and its size is withheld."""
    _, executable = scenarios
    result, values = run(executable, 'store_no_wait')
    assert result.returncode == 0 and values == {'ready5': 0, 'tile5_0': SENTINEL, 'size5': 65535}


def test_a_stores_source_tile_is_not_ready_while_the_store_is_uncovered_under_gem5(scenarios):
    """Rule 3: get_tile_ready(t) is 1 only when no uncovered command names t (gem5's ready counter)."""
    rule, executable = scenarios
    result, values = run(executable, 'source_ready_before_wait')
    assert result.returncode == 0
    assert values == ({'ready3': 0, 'ready3_after': 1} if rule == 'gem5' else {'ready3': 1, 'ready3_after': 1})


def test_a_wait_on_a_condition_only_tile_does_not_cover_the_command(scenarios):
    """(c) A condition tile is not a counted role (MAA.cc:563-580): waiting on it covers nothing."""
    _, executable = scenarios
    result, values = run(executable, 'condition_only_wait')
    assert result.returncode == 0
    assert values == {'ready_dst': 0, 'ready_cond': 1, 'size_dst': 65535, 'ready_dst_after': 1}


def test_a_filled_range_loop_does_not_cover_its_tile_inputs_under_gem5(scenarios):
    """(d) RangeFuser.cc:166-168, 214-218: a range loop that fills its tile finishes without waiting for
    its min/max producers, so they stay uncovered; its register producer (loop A) is still covered."""
    rule, executable = scenarios
    result, values = run(executable, 'range_filled')
    assert result.returncode == 0, result.stderr
    assert values['size_b'] == TILE and values['ready_a'] == 1
    assert values['ready_min'] == (0 if rule == 'gem5' else 1)


def test_an_unfilled_range_loop_covers_its_tile_inputs_under_both_rules(scenarios):
    _, executable = scenarios
    result, values = run(executable, 'range_unfilled')
    assert result.returncode == 0 and values == {'size_b': 0, 'ready_min': 1, 'ready_a': 1}


def test_the_read_offload_chunk_reads_tile0_covered_after_a_filled_range_loop(scenarios):
    """Peter's read offload (library/dx100/bfs_read_offload.inc:30-44), one chunk. The filled range loop
    leaves the stream load and the row-bound gathers uncovered (rule 2), and both name tile0. Rule 5
    (IF.cc:193-212): the gather that overwrites tile0 is accepted only after they finish, so tile0 is
    ready when the CPU reads it. Without rule 5 this read failed read_before_wait (2026-10-09 finding)."""
    _, executable = scenarios
    result, values = run(executable, 'read_offload_chunk')
    assert result.returncode == 0, result.stderr
    assert values == {'ready0': 1, 'ready3': 1, 'ready5': 1}


@pytest.mark.parametrize('scenario', ['stall_source', 'stall_condition'])
def test_issuing_a_command_covers_the_users_of_its_destination_tile_under_gem5(scenarios, scenario):
    """Rule 5: a command that writes tile t covers every uncovered command naming t as a source,
    destination or condition (here a gather's index tile, or a stream load's condition tile). A wait on a
    condition-only tile still covers nothing (rule 1, test above)."""
    rule, executable = scenarios
    result, values = run(executable, scenario)
    assert result.returncode == 0, result.stderr
    expected = 101 if scenario == 'stall_source' else 100
    assert values == ({'ready1': 1, 'first1': expected} if rule == 'gem5' else {'ready1': 0, 'first1': SENTINEL})


def test_a_constant_write_waits_for_its_readers_under_gem5_and_fails_under_the_old_rule(scenarios):
    """(e) IF.cc:233-249, MAA.cc:510-538: the device holds the write until the register's readers finish."""
    rule, executable = scenarios
    result, values = run(executable, 'constant_hold')
    if rule == 'gem5':
        assert result.returncode == 0, result.stderr
        assert values == {'ready_dst': 1, 'size_dst': 4, 'dst_0': 100}   # loaded with the old bound
    else:
        assert result.returncode == 86 and 'SWDB_STRICT_ASSERT:constant_uncovered_register' in result.stderr


# --- lowering certify 1.2: the pinned differential driver under the gem5 rule ---------------------------

@pytest.fixture(scope='module', params=[1024, 16384])
def gem5_driver(request, tmp_path_factory):
    folder = tmp_path_factory.mktemp(f'strict-gem5-{request.param}')
    executable = folder / 'differential'
    build = c.compile_cpp(LIBRARY / 'dx100/drivers/differential.cc', executable, LIBRARY,
                          tile_size=request.param, threads=4, defines=[GEM5])
    assert build['returncode'] == 0, build['stderr']
    return executable


def _driver(executable, *args):
    process = subprocess.run([str(executable), *args], capture_output=True, text=True, timeout=60)
    return {'timeout': False, 'returncode': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr}


@pytest.mark.parametrize('operation', [*c.OPERATIONS, 'store'])
def test_gem5_rule_keeps_every_reference_semantics_match(gem5_driver, operation):
    result = _driver(gem5_driver, operation)
    assert result['returncode'] == 0 and f'SWDB_DIFFERENTIAL_PASS:{operation}' in result['stdout'], result['stderr']


GEM5_CONTROLS = [(operation, name, check) for operation, controls in c.CONTROLS_GEM5_WAIT.items()
                 for name, check in controls.items()]


@pytest.mark.parametrize('operation,control,expected', GEM5_CONTROLS)
def test_every_lowering_1_2_control_is_rejected_by_its_named_check(gem5_driver, operation, control, expected):
    driver_control = c.STORE_CONTROL['gem5'][1] if (operation, control) == ('store', 'dropped_store_wait') else control
    assert c.rejection(_driver(gem5_driver, operation, driver_control), expected) == ('rejected', expected)


@pytest.mark.parametrize('operation,control', [('store', 'wrong_store_wait'), ('const_i32', 'constant_uncovered'),
                                               ('wait', 'constant_uncovered'), ('stream_load', 'constant_uncovered')])
def test_the_replaced_lowering_controls_are_accepted_by_the_gem5_rule(gem5_driver, operation, control):
    """Why lowering 1.2 replaced them: gem5 accepts each, so they cannot be negative controls there."""
    assert control in c.CONTROLS[operation] and control not in c.CONTROLS_GEM5_WAIT[operation]
    result = _driver(gem5_driver, operation, control)
    assert result['returncode'] == 0 and f'SWDB_DIFFERENTIAL_PASS:{operation}' in result['stdout']


# --- calibration and the version table ---------------------------------------------------------------------

def test_dropped_store_wait_deletes_exactly_the_authors_store_wait():
    source = (ROOT / 'apps/dx100/benchmarks/gapbs/src/bfs.cc').read_text()
    assert source.count('wait_ready(tile3);') == 1
    mutant = c._rewrite_control(source, 'dropped_store_wait', calibrate=True)
    assert 'wait_ready(tile3);' not in mutant and len(mutant.splitlines()) == len(source.splitlines()) - 1
    with pytest.raises(Exception, match='authors store wait'):
        c._rewrite_control(mutant, 'dropped_store_wait', calibrate=True)


def test_new_versions_carry_the_gem5_rule_and_old_versions_do_not():
    get = procedures.procedure
    assert procedures.DEFAULTS['candidate'] == '1.7' and procedures.DEFAULTS['lowering_calibration'] == '1.2'
    for family, version in [('candidate', '1.7'), ('lowering_calibration', '1.2')]:
        proc = get(family, version)
        assert proc.wait_rule == 'gem5' and proc.strict_defines == (GEM5,)
        assert proc.definition()['wait_rule'] == 'gem5'
    for family, table in procedures.PROCEDURES.items():
        for version, proc in table.items():
            if (family, version) not in {('candidate', '1.7'), ('lowering_calibration', '1.2')}:
                assert proc.wait_rule is None and proc.strict_defines == () and 'wait_rule' not in proc.definition()
    # 1.7 is 1.6 except for the wait rule.
    old, new = get('candidate', '1.6').definition(), get('candidate', '1.7').definition()
    assert {k: v for k, v in new.items() if k not in ('version', 'wait_rule')} == \
        {k: v for k, v in old.items() if k != 'version'}


def test_only_candidate_1_7_builds_its_evaluator_with_the_gem5_rule():
    assert process._build_class(procedures.procedure('candidate', '1.7')) is process.Gem5WaitBuild
    for version in ('1.5', '1.6'):
        assert process._build_class(procedures.procedure('candidate', version)) is process.Build
    assert process.Build.evaluator_defines == () and process.Gem5WaitBuild.evaluator_defines == (GEM5,)

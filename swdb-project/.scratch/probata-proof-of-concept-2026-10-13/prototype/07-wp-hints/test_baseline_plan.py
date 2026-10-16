"""Method21 public shell/driver/report seams; controlled external tools only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

HERE = Path(__file__).resolve().parent


def test_diagnostic_baseline_keeps_full_inventory_and_final_timeout(tmp_path):
    tools = tmp_path / 'tools'
    tools.mkdir()
    opam = tools / 'opam'
    opam.write_text('#!/usr/bin/env python3\nimport json,sys,os\n'
                    'print(json.dumps({"argv":sys.argv[1:],"marker":os.getenv("SWDB_VERIFIER_RUN_TOKEN"),'
                    '"unrelated":os.getenv("SWDB_UNRELATED_TEST_VALUE")}))\n')
    opam.chmod(0o755)
    env = {**os.environ, 'PATH': str(tools) + os.pathsep + os.environ['PATH'],
           'SWDB_VERIFIER_RUN_TOKEN': 'nonsecret-test-marker', 'SWDB_UNRELATED_TEST_VALUE': 'dummy'}
    observed = {}
    for mode in ('baseline-smoke10', 'wp-smoke', 'wp-smoke-s'):
        directory = tmp_path / mode
        directory.mkdir()
        result = subprocess.run([str(HERE / 'wp_run.sh'), mode, str(directory), 'unit.c'],
                                env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        output = json.loads(result.stdout)
        assert output['marker'] == 'nonsecret-test-marker' and output['unrelated'] is None
        observed[mode] = output['argv']
    for mode, timeout in [('baseline-smoke10', '10'), ('wp-smoke', '30'), ('wp-smoke-s', '30')]:
        args = observed[mode]
        assert args[args.index('-wp-timeout') + 1] == timeout
        assert args[args.index('-wp-cache') + 1] == 'none'
        assert '-wp-smoke-tests' in args and '-wp-no-filter-init' in args
        assert '-machdep' in args and args[args.index('-machdep') + 1] == 'x86_64'
        assert '-wp-fct' not in args and not any(a.startswith('-wp-prop') for a in args)
        assert '-wp-par' in args and '-wp-report-json' in args and '-report-untried' in args


@pytest.mark.parametrize('seed_proven', [False, True])
def test_driver_records_diagnostic_baseline_and_preserves_final_acceptance(tmp_path, seed_proven):
    """Run the real driver/watchdog with controlled Codex and opam executables."""
    home = tmp_path / 'home'
    tools = tmp_path / 'tools'
    tools.mkdir()
    codex = home / '.local/bin/codex'
    codex.parent.mkdir(parents=True)
    codex.write_text('#!' + sys.executable + '\n' + '''import json,sys
if '--version' in sys.argv: print('controlled CLI');sys.exit(0)
path=sys.argv[sys.argv.index('--output-last-message')+1]
open(path,'w').write(json.dumps({'ops':[],'notes':'controlled external provider'}))
print(json.dumps({'type':'thread.started','thread_id':'controlled-same-run'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
''')
    codex.chmod(0o755)
    capture = tmp_path / 'invocations.jsonl'
    opam = tools / 'opam'
    opam.write_text('#!' + sys.executable + '\n' + f'''import json,pathlib,sys
args=sys.argv[1:]; directory=pathlib.Path.cwd()
with open({str(capture)!r},'a') as stream:stream.write(json.dumps({{'directory':directory.name,'args':args}})+'\\n')
if '-wp' not in args or '-wp-report-json' not in args:sys.exit(0)
baseline=directory.name=='round-0'
goals=[{{'goal':'typed_TDStep_ensures_fresh','function':'TDStep','smoke':False,'passed':True,'verdict':'valid'}},
       {{'goal':'typed_TDStep_ensures_unknown','function':'TDStep','smoke':False,'passed':False if baseline else {seed_proven!r},'verdict':'unknown'}}]
if '-wp-smoke-tests' in args:goals.append({{'goal':'typed_TDStep_wp_smoke','function':'TDStep','smoke':True,'passed':True,'verdict':'unknown'}})
pathlib.Path('goals.json').write_text(json.dumps(goals))
if '-wp-fct' in args:pathlib.Path('lemmas.json').write_text('[]')
print(f'[wp] {{len(goals)}} goals scheduled')
print("[report] Computing properties status...\\n--- Properties of Function 'TDStep'\\n[ Unknown ] Post-condition 'unknown'\\n--- Status Report Summary\\n    1 Total\\n------------------------")
''')
    opam.chmod(0o755)
    out = tmp_path / 'run'
    env = {**os.environ, 'HOME': str(home), 'PATH': str(tools) + os.pathsep + os.environ['PATH'],
           'PYTHONDONTWRITEBYTECODE': '1'}
    process = subprocess.run([sys.executable, str(HERE / 'edit_loop.py'), '--out', str(out),
                              '--monotone', '--seeds', '--staged-induction', '--design-probes',
                              '--diagnostic-baseline10', '--rounds', '1', '--final-reserve-min', '8'],
                             env=env, capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stdout + process.stderr
    meta = json.loads((out / 'meta.json').read_text())
    plan = meta['method21']
    assert plan['id'] == 'diagnostic-baseline10-v1'
    assert plan['baseline_timeout_s'] == 10 and plan['final_timeout_s'] == 30
    assert plan['diagnostic_only'] is True and meta['dev'] is False
    assert meta['budget_min'] == 60 and meta['final_reserve_min'] == 8
    history = json.loads((out / 'history.json').read_text())
    assert history[0]['diagnostic_baseline'] == {'mode': 'baseline-smoke10', 'timeout_s': 10}
    calls = [json.loads(line) for line in capture.read_text().splitlines()]
    baseline = next(c['args'] for c in calls if c['directory'] == 'round-0' and '-wp-report-json' in c['args'])
    assert baseline[baseline.index('-wp-timeout') + 1] == '10'
    assert '-wp-smoke-tests' in baseline and '-wp-fct' not in baseline
    summary = json.loads((out / 'summary.json').read_text())
    assert not summary['proven'] and not summary['within_budget']
    assert summary['attempt_counts']['recorded_proposal_requests'] == 0
    assert summary['attempt_counts']['candidate_wp_attempts_with_report'] == 0
    assert 'not completed' in summary['legacy_wp_attempts_meaning']
    if seed_proven:
        final = next(c['args'] for c in calls if c['directory'].startswith('final-') and '-wp-report-json' in c['args'])
        assert final[final.index('-wp-timeout') + 1] == '30'
        assert '-wp-smoke-tests' in final and '-wp-fct' not in final
        assert summary['final'] is not None  # the independent Unknown property still refuses acceptance
    else:
        config = json.loads((out / 'tool-r1/config.json').read_text())
        assert config['baseline_passed'] == ['typed_TDStep_ensures_fresh']
        assert summary['final'] is None


def test_run_report_separates_requests_complete_checks_and_censored_attempts(tmp_path):
    from run_report import attempt_counts
    reports = [
        ('attempt-a', 0, False, True),
        ('attempt-b', 137, True, False),
        ('attempt-c', 0, False, False),
    ]
    for name, code, timeout, complete in reports:
        directory = tmp_path / name
        directory.mkdir()
        goals = [{'goal': 'typed_TDStep_assert_open', 'function': 'TDStep', 'smoke': False,
                  'passed': False, 'verdict': 'unknown'}]
        (directory / 'goals.json').write_text(json.dumps(goals))
        (directory / 'lemmas.json').write_text('[]')
        log = directory / 'round-s.log'
        log.write_text("[wp] 1 goal scheduled\n[report] Computing properties status...\n"
                       "--- Properties of Function 'TDStep'\n[ Unknown ] Assertion 'open'\n" +
                       ('--- Status Report Summary\n    1 Total\n------------------------\n' if complete else ''))
        Path(str(log) + '.summary.json').write_text(json.dumps({
            'cmd': ['wp_run.sh', 'round-s', str(directory), 'unit.c'],
            'exit_code': code, 'timed_out': timeout, 'killed_by_watchdog': False,
            'queue_timed_out': False, 'unconfirmed_children': [], 'error': None}))
    history = [{'round': 1, 'tool': {'propose_calls': 4},
                'codex': {'usage': {'input_tokens': 17}, 'killed_at_deadline': False}},
               {'round': 2, 'final_answer_edit': {'result': 'rejected'},
                'codex': {'usage': {}, 'killed_at_deadline': True}}]
    report = attempt_counts(tmp_path, history)
    assert report == {
        'recorded_proposal_requests': 5,
        'candidate_wp_attempts_with_report': 3,
        'candidate_wp_completed_checks': 1,
        'candidate_wp_deadline_censored': 1,
        'candidate_wp_other_incomplete': 1,
        'provider_turns_with_usage': 1,
        'provider_turns_without_usage': 1,
        'token_totals_are_lower_bounds': True,
    }

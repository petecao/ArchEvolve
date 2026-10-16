"""METHOD23 public driver controls; tools are controlled external executables."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize('fault', [None, 'missing-smoke', 'failed-smoke', 'goals-changed', 'source-changed', 'receipt-changed', 'best-projection-changed', 'old-root-changed'])
def test_fresh_full_baseline_initializes_empty_diagnostic_without_second_wp_run(tmp_path, fault):
    home = tmp_path / 'home'; tools = tmp_path / 'tools'; tools.mkdir()
    out = tmp_path / 'run'
    cli = home / '.local/bin/codex'; cli.parent.mkdir(parents=True)
    cli.write_text('#!' + sys.executable + '\n' + '''import json,sys
if '--version' in sys.argv:print('controlled CLI');sys.exit(0)
open(sys.argv[sys.argv.index('--output-last-message')+1],'w').write(json.dumps({'ops':[],'notes':'controlled provider'}))
print(json.dumps({'type':'thread.started','thread_id':'fresh23'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
''')
    script = cli.read_text()
    clean_script = script
    if fault and fault.endswith('changed'):
        tamper = {'goals-changed': "p=out/'round-0/goals.json';rows=json.loads(p.read_text());rows[0]['passed']=True;p.write_text(json.dumps(rows))",
                  'source-changed': "p=out/'round-0/tdstep_standin.c';p.write_text(p.read_text()+'\\n/* changed */')",
                  'receipt-changed': "p=out/'baseline-initial.json';p.write_text(p.read_text()+' ')",
                  'best-projection-changed': "p=out/'best.json';b=json.loads(p.read_text());b['n_open']=0;b['failing_goals']=[];p.write_text(json.dumps(b))",
                  'old-root-changed': "old=out.parent/'older-owned-run';b=json.loads((old/'best.json').read_text());(out/'best.json').write_text(json.dumps(b))"}[fault]
        script = script.replace("open(sys.argv[sys.argv.index('--output-last-message')+1]", f"from pathlib import Path\nout=Path({str(out)!r})\n{tamper}\nopen(sys.argv[sys.argv.index('--output-last-message')+1]")
    cli.write_text(script); cli.chmod(0o755)
    capture = tmp_path / 'calls.jsonl'
    opam = tools / 'opam'
    opam.write_text('#!' + sys.executable + '\n' + f'''import json,pathlib,sys
args=sys.argv[1:];d=pathlib.Path.cwd()
with open({str(capture)!r},'a') as f:f.write(json.dumps({{'directory':d.name,'args':args}})+'\\n')
if '-wp' not in args or '-wp-report-json' not in args:sys.exit(0)
goals=[{{'goal':'typed_TDStep_ensures_open','function':'TDStep','smoke':False,'passed':False,'verdict':'unknown'}},
       {{'goal':'typed_lemma_FreshGenericLemma','function':'','smoke':False,'passed':True,'verdict':'valid'}},
       {{'goal':'typed_helper_ensures_other','function':'helper','smoke':False,'passed':True,'verdict':'valid'}},
       {{'goal':'typed_TDStep_wp_smoke','function':'TDStep','smoke':True,'passed':True,'verdict':'unknown'}}]
if d.name=='round-0' and {fault!r}=='missing-smoke':goals=[g for g in goals if not g['smoke']]
if d.name=='round-0' and {fault!r}=='failed-smoke':goals[-1]['passed']=False
pathlib.Path('goals.json').write_text(json.dumps(goals))
if '-wp-fct' in args:pathlib.Path('lemmas.json').write_text('[]')
print(f'[wp] {{len(goals)}} goals scheduled')
print("[report] Computing properties status...\\n--- Properties of Function 'TDStep'\\n[ Unknown ] Post-condition 'open'\\n--- Status Report Summary\\n    1 Total\\n------------------------")
'''); opam.chmod(0o755)
    command = [sys.executable, str(HERE / 'edit_loop.py'), '--out', str(out),
               '--monotone', '--staged-induction', '--design-probes',
               '--diagnostic-baseline10', '--terminal-full30', '--fresh-baseline-start',
               '--strategies', '--show-goal', '--budget-deadline', '--rounds', '1',
               '--final-reserve-min', '24']
    environment = {**os.environ, 'HOME': str(home),
                   'PATH': str(tools) + os.pathsep + os.environ['PATH'],
                   'PYTHONDONTWRITEBYTECODE': '1'}
    if fault == 'old-root-changed':
        # Produce a separate, genuine earlier synthetic run through the same CLI.
        # No snapshot field is fabricated to model freshness.
        cli.write_text(clean_script)
        earlier = subprocess.run([str(tmp_path/'older-owned-run') if a == str(out) else a for a in command],
                                 env=environment, capture_output=True, text=True, timeout=30)
        assert earlier.returncode == 0, earlier.stdout + earlier.stderr
        cli.write_text(script)
        capture.unlink()
    result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=30)
    if fault in {'missing-smoke','failed-smoke'}:
        assert result.returncode != 0 and 'smoke' in result.stderr.lower(), result.stdout + result.stderr
        assert not (out / 'tool-r1').exists() and not (out / 'baseline-initial.json').exists()
        return
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in capture.read_text().splitlines()]
    generated = [row for row in calls if '-wp-report-json' in row['args']]
    if fault and fault.endswith('changed'):
        assert [row['directory'] for row in generated] == ['round-0']
        summary = json.loads((out / 'summary.json').read_text())
        assert not summary['proven'] and not summary['within_budget']
        assert 'refus' in summary['final']['outcome'].lower()
        return
    assert [row['directory'] for row in generated] == ['round-0', 'final-r1']
    for row in generated:
        args = row['args']
        assert '-wp-smoke-tests' in args and '-wp-fct' not in args
        assert args[args.index('-wp-timeout') + 1] == ('10' if row['directory'] == 'round-0' else '30')
    best = json.loads((out / 'best.json').read_text())
    assert best['hints'] == [] and best['from'] == 'fresh-baseline'
    assert best['n_goals'] == 2 and best['n_open'] == 1
    assert [g['goal'] for g in best['failing_goals']] == ['typed_TDStep_ensures_open']
    assert not (out / 'seeds').exists() and not (out / 'round-0/lemmas.json').exists()
    initial = json.loads((out / 'baseline-initial.json').read_text())
    assert initial['source_mode'] == 'baseline-smoke10'
    assert initial['full_baseline_inventory'] == 4 and initial['diagnostic_subset_inventory'] == 2
    assert initial['cross_mode_formula_equivalence_claimed'] is False
    assert initial['source_sha256'] and initial['headers_sha256'] and initial['artifacts_sha256']
    config = json.loads((out / 'tool-r1/config.json').read_text())
    assert config['method23'] is True
    assert config['baseline_passed'] == ['typed_helper_ensures_other','typed_lemma_FreshGenericLemma']
    summary = json.loads((out / 'summary.json').read_text())
    assert summary['method23'] and not summary['proven'] and not summary['within_budget']
    assert summary['final'] is not None

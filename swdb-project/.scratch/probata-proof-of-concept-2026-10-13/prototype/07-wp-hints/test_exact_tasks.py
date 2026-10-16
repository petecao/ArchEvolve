"""METHOD23 public MCP reader controls with controlled external WP output.

Created: 2026-10-15 ET. Synthetic tasks have no theorem status.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
import select

HERE = Path(__file__).resolve().parent


def reader(tmp_path, tasks, goal='typed_TDStep_call_callee_requires', *, requests=None, raw_index=None, corrupt_after_first=None, search_remaining_s=None, corrupt_during_generation=None, debt_expiry=False):
    import loop as L
    import staged_search as S
    source = L.run_dir(tmp_path, 'initial', (L.STANDIN_DIR / L.UNIT).read_text())
    best = {'hints': [], 'dir': str(source), 'n_open': 1, 'n_goals': 1,
            'failing_goals': [{'goal': goal, 'function': 'TDStep', 'kind': 'requires', 'line': 999}]}
    (tmp_path / 'best.json').write_text(json.dumps(best))
    tools = tmp_path / 'tools'; tools.mkdir()
    capture = tmp_path / 'calls.jsonl'
    opam = tools / 'opam'
    generation_corruption = {None: '',
        'source': f"Path({L.UNIT!r}).write_text('changed source')\n",
        'header': f"Path({L.HEADERS[0]!r}).write_text('changed header')\n"}[corrupt_during_generation]
    encoded_index = raw_index if raw_index is not None else json.dumps(dict(schema='probata-wpo-tasks-v1', tasks=tasks))
    opam.write_text('#!' + sys.executable + '\nimport json,sys\nfrom pathlib import Path\n' +
                   f"with open({str(capture)!r},'a') as f:f.write(json.dumps(sys.argv[1:])+'\\n')\n" +
                   "if 'ocamlopt' in sys.argv:Path('task-export.cmxs').write_text('controlled compiler output');sys.exit(0)\n" +
                   ("import time;time.sleep(0.6)\n" if search_remaining_s is not None or debt_expiry else "") +
                   f"Path('wp-task-index.json').write_text({encoded_index!r})\n" +
                   generation_corruption +
                   "print('Goal misleading human header: \\nDo not select by ordinal.')\n")
    if debt_expiry:
        script = opam.read_text()
        rows = [{'goal': goal, 'function': 'TDStep', 'smoke': False, 'passed': False, 'verdict': 'unknown'},
                {'goal': 'typed_TDStep_ensures_extra_debt', 'function': 'TDStep', 'smoke': False, 'passed': False, 'verdict': 'unknown'}]
        report = ("[wp] 2 goals scheduled\n[report] Computing properties status...\n"
                  "--- Properties of Function 'TDStep'\n[ Unknown ] Post-condition 'extra_debt'\n"
                  "--- Status Report Summary\n    1 Total\n------------------------")
        controlled_round = ("if '-wp-report-json' in sys.argv:\n"
            + f" Path('goals.json').write_text(json.dumps({rows!r}))\n"
            + " Path('lemmas.json').write_text('[]')\n"
            + f" print({report!r})\n sys.exit(0)\n")
        opam.write_text(script.replace("if 'ocamlopt' in sys.argv:", controlled_round + "if 'ocamlopt' in sys.argv:"))
    opam.chmod(0o755)
    state = tmp_path / 'tool-r1'; state.mkdir()
    config = {'out': str(tmp_path), 'allowed_kinds': ['loop_assigns'], 'staged_search': None,
              'clock_kind': 'continuous_monotonic', 'clock_info': S.clock_info(),
              'method22': True, 'method23': True, 't0': S.clock(), 'budget_min': 60,
              'final_reserve_min': 24, 'round': 1, 'round_timeout': 10,
              'mode': 'round-s', 'show_goal': True}
    if debt_expiry:
        config.update(staged_search=S.schedule(0, 33 * 60), proof_search_stop_min=33)
    if search_remaining_s is not None:
        config.update(staged_search=S.schedule(0, 33 * 60), proof_search_stop_min=33,
                      t0=S.clock() - (33 * 60 - search_remaining_s))
    (state / 'config.json').write_text(json.dumps(config))
    args = requests or [{'goal': goal}]
    wire = [{'jsonrpc': '2.0', 'id': n, 'method': 'tools/call',
             'params': {'name': 'show_goal', 'arguments': a}} for n, a in enumerate(args, 1)]
    env = {**os.environ, 'PATH': str(tools) + os.pathsep + os.environ['PATH'],
           'PYTHONDONTWRITEBYTECODE': '1'}
    command = [sys.executable, str(HERE / 'edit_tool_mcp.py'), '--state', str(state)]
    if debt_expiry:
        proposal = {'jsonrpc': '2.0', 'id': 100, 'method': 'tools/call',
                    'params': {'name': 'propose_edit', 'arguments': {'ops': [
                        {'op': 'add', 'goal': goal, 'id': '', 'anchor': 'loop:k_loop',
                         'kind': 'loop_assigns', 'text': 'loop assigns k;'}]}}}
        staged = subprocess.run(command, input=json.dumps(proposal)+'\n', env=env,
                                capture_output=True, text=True, timeout=20)
        assert staged.returncode == 0 and (tmp_path/'debt.json').exists(), staged.stdout+staged.stderr
        debt = json.loads((tmp_path/'debt.json').read_text())
        # Resume the public retained session at a controlled near-expiry time.
        # The genuine MCP proposal created the state; no private helper is called.
        config['t0'] = S.clock() - (debt['started_s'] + 300 - 0.5)
        (state/'config.json').write_text(json.dumps(config))
        capture.unlink()
    if corrupt_after_first:
        process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            process.stdin.write(json.dumps(wire[0]) + '\n'); process.stdin.flush()
            assert select.select([process.stdout], [], [], 20)[0], 'no first MCP response'
            first = process.stdout.readline()
            index = next(tmp_path.glob('goal-*/wp-task-index.json'))
            if corrupt_after_first == 'delete-index':
                index.unlink()
            elif corrupt_after_first == 'change-index':
                index.write_text('{}')
            elif corrupt_after_first == 'change-exporter':
                (index.parent / 'task-export.cmxs').write_text('changed')
            elif corrupt_after_first == 'change-task-source':
                (index.parent / L.UNIT).write_text('changed source')
            elif corrupt_after_first == 'delete-task-header':
                (index.parent / L.HEADERS[0]).unlink()
            elif corrupt_after_first == 'delete-exporter-source':
                (index.parent / 'Probata_task_export.ml').unlink()
            elif corrupt_after_first == 'change-exporter-source':
                (index.parent / 'Probata_task_export.ml').write_text('changed exporter source')
            elif corrupt_after_first == 'delete-task':
                next((tmp_path / 'goal-pages').glob('*.task.txt')).unlink()
            process.stdin.write(''.join(json.dumps(r) + '\n' for r in wire[1:])); process.stdin.close(); process.stdin = None
            tail, errors = process.communicate(timeout=20)
            output = first + tail
            assert process.returncode == 0, output + errors
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
    else:
        result = subprocess.run(command, input=''.join(json.dumps(r) + '\n' for r in wire), env=env,
                                capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stdout + result.stderr
        output = result.stdout
    replies = [json.loads(line)['result']['content'][0]['text'] for line in output.splitlines()]
    records = [json.loads(line) for line in (state / 'submissions.jsonl').read_text().splitlines()]
    calls = [json.loads(line) for line in capture.read_text().splitlines()]
    return replies, records, calls


def test_exact_machine_id_selects_unsuffixed_call_without_human_ordinal(tmp_path):
    goal = 'typed_TDStep_call_callee_requires'
    exact = 'Goal Pre-condition ("generic.h", lines 2-3):\nAssume { ACTUAL PREMISE. }\nProve: EXACT CONCLUSION.'
    wrong = 'Goal misleading: WRONG TASK MUST STAY HIDDEN.'
    replies, records, calls = reader(tmp_path, {goal: exact, goal + '_2': wrong})
    assert 'ACTUAL PREMISE' in replies[0] and 'EXACT CONCLUSION' in replies[0]
    assert 'WRONG TASK MUST STAY HIDDEN' not in replies[0]
    assert records[0]['machine_goal_id'] == goal
    assert records[0]['full_task_sha256'] == hashlib.sha256(exact.encode()).hexdigest()
    assert records[0]['task_index_sha256'] and records[0]['exporter_source_sha256']
    assert len(calls) == 2  # pinned source compiled in this fresh task directory, then no-prover WP
    assert 'ocamlopt' in calls[0] and '-load-module' in calls[1]
    assert calls[1][calls[1].index('-wp-prover') + 1] == 'none'


@pytest.mark.parametrize('goal', ['typed_TDStep_call_callee_requires_8',
                                 'typed_TDStep_loop_invariant_named_preserved_part3',
                                 'typed_lemma_AxiomWithUnicode'])
def test_machine_id_preserves_range_and_split_identity_without_header_parsing(tmp_path, goal):
    task = 'Goal Instance ("generic.h", lines 116-117):\nAssume: α >= 0.\nProve: EXACT.'
    replies, records, calls = reader(tmp_path, {goal: task, goal + '_other': 'WRONG'}, goal)
    assert task in replies[0] and 'WRONG' not in replies[0]
    assert records[0]['machine_goal_id'] == goal


@pytest.mark.parametrize('raw', [
    '{"schema":"probata-wpo-tasks-v1","tasks":{}}',
    '{"schema":"probata-wpo-tasks-v1","tasks":{"different-id":"WRONG"}}',
    '{"schema":"wrong","tasks":{"typed_TDStep_call_callee_requires":"WRONG"}}',
    '{"schema":"probata-wpo-tasks-v1","tasks":{"typed_TDStep_call_callee_requires":""}}',
    '{"schema":"probata-wpo-tasks-v1","tasks":{"typed_TDStep_call_callee_requires":4}}',
    '{"schema":"probata-wpo-tasks-v1","tasks":{"typed_TDStep_call_callee_requires":"WRONG","typed_TDStep_call_callee_requires":"ALSO WRONG"}}',
    '{"schema":"wrong","schema":"probata-wpo-tasks-v1","tasks":{"typed_TDStep_call_callee_requires":"WRONG"}}',
    'not json',
])
def test_machine_index_refuses_missing_malformed_or_duplicate_identity(tmp_path, raw):
    replies, records, calls = reader(tmp_path, {}, raw_index=raw)
    assert 'refused' in replies[0].lower() and 'WRONG' not in replies[0]
    assert records[0]['result'].startswith('refused:')


def test_machine_task_pages_reuse_exact_index_and_expose_earliest_premises(tmp_path):
    goal = 'typed_TDStep_call_callee_requires'
    task = 'EARLY PREMISE\n' + 'x' * 18000 + '\nLAST CONCLUSION'
    digest = hashlib.sha256(task.encode()).hexdigest()
    replies, records, calls = reader(tmp_path, {goal: task}, requests=[
        {'goal': goal}, {'goal': goal, 'offset': 14000, 'task_sha256': digest},
        {'goal': goal, 'offset': 14000, 'task_sha256': '0' * 64}])
    assert 'EARLY PREMISE' in replies[0] and 'LAST CONCLUSION' not in replies[0]
    assert 'LAST CONCLUSION' in replies[1] and 'EARLY PREMISE' not in replies[1]
    assert records[0]['full_task_sha256'] == records[1]['full_task_sha256'] == digest
    assert records[0]['task_index_sha256'] == records[1]['task_index_sha256']
    assert records[0]['truncated'] is True and records[1]['truncated'] is False
    assert 'refused' in replies[2].lower() and len(calls) == 2


@pytest.mark.parametrize('fault', ['delete-index', 'change-index', 'change-exporter', 'delete-task',
                                  'change-task-source', 'delete-task-header', 'delete-exporter-source', 'change-exporter-source'])
def test_changed_or_missing_retained_task_is_refused_without_regeneration(tmp_path, fault):
    goal = 'typed_TDStep_call_callee_requires'
    task = 'EARLY PREMISE\n' + 'P' * 18000 + '\nCONCLUSION'
    digest = hashlib.sha256(task.encode()).hexdigest()
    replies, records, calls = reader(tmp_path, {goal: task}, requests=[{'goal': goal},
        {'goal': goal, 'offset': 14000, 'task_sha256': digest}], corrupt_after_first=fault)
    assert 'EARLY PREMISE' in replies[0]
    assert 'refused' in replies[1].lower() and 'CONCLUSION' not in replies[1]
    assert records[1]['result'].startswith('refused:') and len(calls) == 2



def test_task_completed_after_soft_stop_is_retained_but_not_disclosed(tmp_path):
    goal = 'typed_TDStep_call_callee_requires'
    task = 'Goal exact:\nAssume: LATE PREMISE.\nProve: LATE CONCLUSION.'
    replies, records, calls = reader(tmp_path, {goal: task}, search_remaining_s=0.4)
    assert 'LATE PREMISE' not in replies[0] and 'LATE CONCLUSION' not in replies[0]
    assert 'refused' in replies[0].lower()
    assert records[0]['deadline_censored'] is True
    assert records[0]['remaining_after_generation_s'] <= 0
    assert (tmp_path/'goal-r1c1/wp-task-index.json').exists()


@pytest.mark.parametrize('fault', ['source', 'header'])
def test_generated_task_input_changes_are_refused_before_first_page(tmp_path, fault):
    goal = 'typed_TDStep_call_callee_requires'
    task = 'Goal exact:\nAssume: SECRET PREMISE.\nProve: SECRET CONCLUSION.'
    replies, records, calls = reader(tmp_path, {goal: task}, corrupt_during_generation=fault)
    assert 'refused' in replies[0].lower() and 'SECRET PREMISE' not in replies[0]
    assert records[0]['result'].startswith('refused:') and len(calls) == 2



def test_task_of_expired_temporary_candidate_is_retained_but_not_disclosed(tmp_path):
    goal = 'typed_TDStep_call_callee_requires'
    task = 'Goal exact:\nAssume: EXPIRED TEMPORARY PREMISE.\nProve: EXPIRED TEMPORARY CONCLUSION.'
    replies, records, calls = reader(tmp_path, {goal: task}, debt_expiry=True)
    assert not (tmp_path/'debt.json').exists(), 'public task read must settle expired debt'
    assert 'EXPIRED TEMPORARY PREMISE' not in replies[0]
    assert 'EXPIRED TEMPORARY CONCLUSION' not in replies[0]
    assert 'refused' in replies[0].lower() and records[-1]['candidate_censored'] is True
    assert records[-1]['remaining_after_generation_s'] > 0  # global proof time remains
    assert len(calls) == 2 and (tmp_path/'goal-r1c2/wp-task-index.json').exists()

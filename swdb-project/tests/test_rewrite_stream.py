"""Stream-json provider capture: partial output survives a timeout. 2026-09-29 ET.

A local fake `claude` executable replays scripted stream-json events. No real
provider is called; these check SWDB's capture, parsing and retention only.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

from test_proposals import proposal_setup
from swdb import rewrite
from swdb.cli import Failure

RESPONSE = {'interpretation': 'Apply alpha 14.', 'patch': '', 'unresolved': ['fixture cannot rewrite']}


def delta(kind, text):
    field = 'partial_json' if kind == 'input_json_delta' else 'text'
    return {'type': 'stream_event', 'event': {'type': 'content_block_delta', 'index': 1,
                                              'delta': {'type': kind, field: text}}}


def events(result=True, error=False):
    body = json.dumps(RESPONSE)
    rows = [{'type': 'system', 'subtype': 'init', 'model': 'fake-model'},
            {'type': 'system', 'subtype': 'thinking_tokens', 'estimated_tokens': 120},
            delta('input_json_delta', body[:20]), delta('input_json_delta', body[20:])]
    if result:
        rows.append({'type': 'result', 'subtype': 'error_max_budget_usd' if error else 'success',
                     'is_error': error, 'structured_output': None if error else RESPONSE,
                     'result': '' if error else body, 'num_turns': 2, 'total_cost_usd': 0.01,
                     'usage': {'output_tokens': 42}})
    return rows


@pytest.fixture
def fake_claude(tmp_path):
    program = tmp_path / 'bin' / 'claude'
    program.parent.mkdir()
    program.write_text(f'#!{sys.executable}\n' + '\n'.join([
        'import json, sys, time', 'from pathlib import Path',
        'if "--version" in sys.argv: print("0.0-fake (Claude Code)"); raise SystemExit(0)',
        'sys.stdin.read()',
        'plan = json.loads(Path(__file__).with_name("plan.json").read_text())',
        'Path(__file__).with_name("argv.json").write_text(json.dumps(sys.argv[1:]))',
        'for row in plan["events"]:',
        '    sys.stdout.write(row + "\\n" if isinstance(row, str) else json.dumps(row) + "\\n"); sys.stdout.flush()',
        'time.sleep(plan.get("sleep", 0))',
        'raise SystemExit(plan.get("exit", 0))']))
    program.chmod(0o755)

    def make(rows, sleep=0, exit=0, **config):
        (program.parent / 'plan.json').write_text(json.dumps({'events': rows, 'sleep': sleep, 'exit': exit}))
        data = {'kind': 'external_fixture', 'emulates': 'claude', 'workspace': False, 'command': [str(program)], 'timeout_s': 5, 'max_repairs': 1,
                'total_seconds': 30, 'budget_usd': 5, 'output_format': 'stream-json', **config}
        path = tmp_path / 'provider.yaml'
        path.write_text(yaml.safe_dump(data))
        return path
    make.argv = lambda: json.loads((program.parent / 'argv.json').read_text())
    return make


def test_stream_capture_parses_final_result_event_and_records_progress(fake_claude, tmp_path):
    config = rewrite.configuration(fake_claude(events()))
    response, meta = rewrite.interpret(config, 'prompt', tmp_path / 'p1')
    assert response == RESPONSE
    argv = fake_claude.argv()
    assert argv[argv.index('--output-format') + 1] == 'stream-json'
    assert '--verbose' in argv and '--include-partial-messages' in argv and '--json-schema' in argv
    stream = meta['stream']
    assert stream['model'] == 'fake-model' and stream['estimated_thinking_tokens'] == 120
    assert stream['result']['subtype'] == 'success' and stream['result']['output_tokens'] == 42
    assert stream['delta_counts'] == {'input_json_delta': 2}
    assert (tmp_path / 'p1/partial_output.txt').read_text() == json.dumps(RESPONSE)
    assert stream['first_output_s'] is not None
    assert json.loads((tmp_path / 'p1/provider.json').read_text())['stream'] == stream


def test_timeout_retains_partial_stream_and_progress(fake_claude, tmp_path):
    config = rewrite.configuration(fake_claude(events(result=False), sleep=30, timeout_s=1))
    with pytest.raises(Exception) as caught:
        rewrite.interpret(config, 'prompt', tmp_path / 'p1')
    assert 'TimeoutExpired' in type(caught.value).__name__
    meta = json.loads((tmp_path / 'p1/provider.json').read_text())
    assert meta['state'] == 'interrupted_or_timeout' and meta['host_wall_s'] >= 1
    assert meta['stream']['events'] == 4 and meta['stream']['result'] is None
    assert meta['stream']['delta_chars']['input_json_delta'] == len(json.dumps(RESPONSE))
    assert (tmp_path / 'p1/partial_output.txt').read_text() == json.dumps(RESPONSE)
    assert (tmp_path / 'p1/stdout.txt').read_text().count('\n') == 4


@pytest.mark.parametrize('rows,message', [
    (events(result=False), 'without a result event'),
    (events(error=True), 'Claude returned an error'),
    (events(result=False) + ['{"type": "result", "truncated'], 'without a result event')])
def test_incomplete_or_error_stream_is_a_failure(fake_claude, tmp_path, rows, message):
    config = rewrite.configuration(fake_claude(rows))
    with pytest.raises(Failure, match=message):
        rewrite.interpret(config, 'prompt', tmp_path / 'p1')
    meta = json.loads((tmp_path / 'p1/provider.json').read_text())
    assert meta['state'] == 'completed'
    assert meta['stream']['unparsed_lines'] == (1 if isinstance(rows[-1], str) else 0)


def test_default_capture_is_unchanged_and_output_format_is_checked(fake_claude, tmp_path):
    path = fake_claude([json.dumps({'is_error': False, 'structured_output': RESPONSE})])
    data = yaml.safe_load(path.read_text())
    del data['output_format']
    path.write_text(yaml.safe_dump(data))
    config = rewrite.configuration(path)
    assert 'output_format' not in config
    response, meta = rewrite.interpret(config, 'prompt', tmp_path / 'p1')
    assert response == RESPONSE and 'stream' not in meta
    argv = fake_claude.argv()
    assert argv[argv.index('--output-format') + 1] == 'json' and '--verbose' not in argv
    for bad in ({'output_format': 'text'}, {'output_format': 'stream-json', 'kind': 'external_fixture', 'emulates': 'codex'}):
        path.write_text(yaml.safe_dump({**data, **bad}))
        with pytest.raises(Failure, match='output'):
            rewrite.configuration(path)


def test_public_submit_retains_stream_progress_after_timeout(proposal_setup, fake_claude):
    records, runs, _, request = proposal_setup
    config = fake_claude(events(result=False), sleep=30, timeout_s=1)
    result = records.swdb('submit', request(payload={'kind': 'natural_language', 'content': 'Adjust alpha to 14.'}),
                          '--provider-config', config, '--runs-dir', runs, '--format', 'json')
    assert result.returncode == 1, result.stderr
    data = json.loads(result.stdout)
    provider = data['attempts'][0]['provider']
    assert provider['state'] == 'interrupted_or_timeout'
    assert provider['stream']['events'] == 4 and provider['stream']['result'] is None
    assert Path(provider['stream']['partial_output']['path']).read_text() == json.dumps(RESPONSE)
    assert data['repair_budget']['used_seconds'] >= 1
    later = records.swdb('get', data['id'], '--format', 'json')
    assert later.returncode == 0
    assert json.loads(later.stdout)['attempts'][0]['provider']['stream'] == provider['stream']


def test_stream_capture_allows_amplified_output_above_the_json_cap(fake_claude, tmp_path):
    """2026-09-28: stream-json amplifies ~40x, so its stdout cap exceeds 10 MiB."""
    pad = delta('text_delta', 'x' * (1024 * 1024))
    config = rewrite.configuration(fake_claude([pad] * 11 + events()))
    response, meta = rewrite.interpret(config, 'prompt', tmp_path / 'p1')
    assert response == RESPONSE and (tmp_path / 'p1/stdout.txt').stat().st_size > rewrite.JSON_OUTPUT_LIMIT
    assert rewrite.STREAM_OUTPUT_LIMIT >= 64 * 1024 * 1024


def test_json_capture_keeps_the_10_mib_cap(fake_claude, tmp_path):
    path = fake_claude(['x' * (1024 * 1024)] * 11)
    data = yaml.safe_load(path.read_text())
    del data['output_format']
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(Failure, match='10 MiB'):
        rewrite.interpret(rewrite.configuration(path), 'prompt', tmp_path / 'p1')


def test_interpret_off_the_main_thread_skips_signal_handlers(fake_claude, tmp_path):
    """2026-09-28: signal.signal raises off the main thread; interpret still runs."""
    import threading
    config = rewrite.configuration(fake_claude(events()))
    outcome = {}

    def work():
        try:
            outcome['response'] = rewrite.interpret(config, 'prompt', tmp_path / 'p1')[0]
        except BaseException as exc:  # surfaced to the main thread below
            outcome['error'] = exc
    worker = threading.Thread(target=work)
    worker.start()
    worker.join(30)
    assert outcome.get('error') is None and outcome['response'] == RESPONSE

"""Host receipt contract fixtures; no remote observations. Updated: 2026-09-25."""
import json
import subprocess

from swdb import artifacts, host_observation


def test_host_receipt_retains_commands_failures_timeouts_and_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(host_observation, 'COMMANDS', [('ok',), ('missing',), ('slow',)])
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == 'slow':
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=b'partial', stderr=b'wait')
        return subprocess.CompletedProcess(command, 0 if command[0] == 'ok' else 1, 'value', 'unavailable')
    monkeypatch.setattr(host_observation.subprocess, 'run', run)
    receipt = host_observation.capture(tmp_path, tmp_path, evidence_kind='contract_fixture')
    assert receipt['sha256'] == artifacts.file_hash(tmp_path / 'host-observation.json')
    assert receipt['unavailable_commands'] == 2
    data = json.loads((tmp_path / 'host-observation.json').read_text())
    assert data['evidence_kind'] == 'contract_fixture'
    assert [row['state'] for row in data['commands']] == ['complete', 'unavailable', 'timed_out']
    assert data['commands'][1]['returncode'] == 1
    assert data['commands'][2]['stdout'] == 'partial'
    assert all(0 < kwargs['timeout'] <= 3 for _, kwargs in calls)


def test_exhausted_host_receipt_budget_does_not_start_commands(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('command ran after receipt budget expired')
    monkeypatch.setattr(host_observation.subprocess, 'run', forbidden)
    receipt = host_observation.capture(tmp_path, tmp_path, total_seconds=0, evidence_kind='contract_fixture')
    data = json.loads((tmp_path / 'host-observation.json').read_text())
    assert all(row['state'] == 'not_collected' for row in data['commands'])
    assert receipt['unavailable_commands'] == len(host_observation.COMMANDS)

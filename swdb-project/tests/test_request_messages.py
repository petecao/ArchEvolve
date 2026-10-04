"""Malformed public messages stay retrievable. Updated: 2026-09-26 ET."""
import json

import pytest


@pytest.mark.parametrize('command', ['submit', 'evaluate', 'bfs-profile', 'dx100-build',
                                    'dx100-compile', 'dx100-execute'])
@pytest.mark.parametrize('value', ['!!binary aGVsbG8=', '.nan', '!!set {item: null}',
                                  '{1: value}', '&cycle [*cycle]'])
def test_yaml_only_message_values_cannot_poison_durable_results(records, tmp_path, command, value):
    request = tmp_path / 'request.yaml'
    raw = 'message_version: "1.0"\nid: invalid-message\nextra: ' + value + '\n'
    request.write_text(raw)
    options = ['--lane', '0'] if command.startswith('dx100-') else []
    response = records.swdb(command, request, '--runs-dir', tmp_path / 'runs', '--format', 'json', *options)
    assert response.returncode == 1 and not response.stderr, response.stderr
    result = json.loads(response.stdout)
    assert result['outcome']['state'] not in {'submitted', 'complete', 'candidate_created'}
    assert result['request']['raw_text'] == raw
    assert 'JSON-compatible' in result['request']['parse_error']
    assert records.validate().returncode == 0
    rebuilt = records.swdb('build')
    assert rebuilt.returncode == 0, rebuilt.stderr
    later = records.swdb('get', result['id'], '--format', 'json')
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout) == result


@pytest.mark.parametrize('command', ['register-workload', 'freeze-protocol', 'compare-evaluations',
                                    'aggregate-evaluations', 'profile-package', 'dx100-profile'])
def test_shared_protocol_reader_rejects_yaml_only_values_before_publication(records, tmp_path, command):
    request = tmp_path / 'request.yaml'
    request.write_text('message_version: "1.0"\nid: bad-request\nextra: !!binary aGVsbG8=\n')
    options = ['--runs-dir', tmp_path / 'runs'] if command == 'dx100-profile' else []
    response = records.swdb(command, request, '--format', 'json', *options)
    assert response.returncode == 1 and 'JSON-compatible' in response.stderr
    assert 'Traceback' not in response.stderr
    assert not list(records.path.rglob('*.yaml'))
    assert records.validate().returncode == 0
    assert records.swdb('build').returncode == 0


@pytest.mark.parametrize('metadata', [{'value': b'bad'}, {1: 'number', '1': 'string'}],
                         ids=['binary', 'colliding-keys'])
def test_persistence_rejects_unserializable_metadata_before_writing(records, metadata):
    from swdb.cli import Failure
    from swdb.workflow import persist, record
    data = record('evaluation', 'bad-metadata', request=metadata)
    with pytest.raises(Failure, match='nothing was persisted'):
        persist(records.path, data, create=True)
    assert not list(records.path.rglob('*.yaml'))


@pytest.mark.parametrize('value', ['{? [a, b]: value}', '1' * 5000],
                         ids=['unhashable-key', 'oversized-integer'])
def test_yaml_construction_errors_retain_retrievable_failure(records, tmp_path, value):
    request = tmp_path / 'request.yaml'
    raw = 'message_version: "1.0"\nid: invalid-construction\nextra: ' + value + '\n'
    request.write_text(raw)
    response = records.swdb('evaluate', request, '--runs-dir', tmp_path / 'runs', '--format', 'json')
    assert response.returncode == 1 and not response.stderr, response.stderr
    result = json.loads(response.stdout)
    assert result['request']['raw_text'] == raw
    assert result['request']['parse_error']
    assert result['outcome']['state'] != 'complete'
    assert records.validate().returncode == 0
    assert records.swdb('build').returncode == 0
    later = records.swdb('get', result['id'], '--format', 'json')
    assert later.returncode == 0, later.stderr
    assert json.loads(later.stdout) == result

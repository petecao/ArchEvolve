"""Separate simulated syscall witness contracts; no execution evidence. Updated: 2026-09-26 ET."""

import copy
import hashlib
import json
from pathlib import Path
import runpy

import pytest

from swdb.dx100_witness import CHECKER, MAX_TRACE_BYTES, WitnessError, parse_trace, validate_completed_witness, validate_record_witness


CPUS = [f'system.switch_cpus{i}' for i in range(4)]


def line(tick, body, cpu=0, thread=0):
    return f'{tick}: SyscallBase: {CPUS[cpu]}: T{thread} : syscall {body}\n'


def trace(tmp_path, text=None, **kwargs):
    path = tmp_path / 'post-roi-syscalls.log'
    path.write_text(text if text is not None else (
        line(120, 'Calling exit_group(0)...') + line(120, 'Returned 0.')
        + line(130, 'Calling futex(195028, 128, 72, 0, 202, 1)...', 2)
        + line(130, 'Returned 0.', 2)))
    return path, parse_trace(path, enabled_tick=100, end_tick=150,
        expected_cpu=CPUS[0], allowed_cpus=CPUS, **kwargs)


def test_exact_exit_pair_retains_later_workers_without_claiming_termination(tmp_path):
    path, found = trace(tmp_path)
    assert found['completed'] is True
    assert found['trace']['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert found['caller'] == {'cpu': CPUS[0], 'thread': 0}
    assert found['exit_request'] == {'status': 0, 'tick': 120, 'call_line': 1,
                                    'return_line': 2, 'return_value': 0}
    assert found['events_after_exit'] == 2
    assert 'normal_exit_observed' not in found


@pytest.mark.parametrize('text,match', [
    ('Verification: PASS\n', 'format'),
    (line(120, 'Returned 0.'), 'orphan'),
    (line(120, 'Calling exit_group(1)...') + line(120, 'Returned 0.'), 'status'),
    (line(120, 'Calling exit_group(0)...') + line(120, 'Returned 1.'), 'return'),
    (line(120, 'Calling exit_group(0)...'), 'incomplete exit'),
    (line(120, 'Calling exit_group(0)...', 1) + line(120, 'Returned 0.', 1), 'caller'),
    (line(120, 'Calling exit_group(0)...', thread=1) + line(120, 'Returned 0.', thread=1), 'caller'),
    (line(99, 'Calling exit_group(0)...') + line(99, 'Returned 0.'), 'interval'),
    (line(151, 'Calling exit_group(0)...') + line(151, 'Returned 0.'), 'interval'),
    (line(120, 'Calling exit_group(0)...') + line(121, 'Returned 0.'), 'same tick'),
    (line(120, 'Calling exit_group(0)...') + line(119, 'Returned 0.'), 'order'),
    (line(120, 'Calling exit_group(0)...') + line(120, 'Calling getpid()...'), 'pending'),
    (line(120, 'Calling exit_group(0)...') + line(120, 'exit_group needs retry.'), 'retry'),
    (line(120, 'Calling exit_group(0)...') + line(120, 'No return value.'), 'return'),
    ((line(120, 'Calling exit_group(0)...') + line(120, 'Returned 0.')) * 2, 'duplicate'),
    (line(120, 'Calling exit_group(0)...').replace('SyscallBase: ', '') + line(120, 'Returned 0.'), 'format'),
    (line(120, 'Calling exit_group(0)...') + line(120, 'Returned 0.').rstrip(), 'truncated'),
])
def test_rejects_untrusted_or_conflicting_evidence(tmp_path, text, match):
    with pytest.raises(WitnessError, match=match):
        trace(tmp_path, text, allow_incomplete=True)


def test_chunk_without_exit_is_incomplete_but_valid_retries_are_retained(tmp_path):
    text = (line(110, 'Calling futex(1, 2, 3, 4, 5, 6)...', 1)
        + line(110, 'futex needs retry.', 1)
        + line(140, 'Retrying futex(1, 2, 3, 4, 5, 6)...', 1)
        + line(140, 'futex still needs retry.', 1))
    _, found = trace(tmp_path, text, allow_incomplete=True)
    assert found['completed'] is False and found['exit_request'] is None
    assert found['pending_calls'] == [{'cpu': CPUS[1], 'thread': 0, 'name': 'futex', 'state': 'retry'}]
    with pytest.raises(WitnessError, match='missing exit'):
        trace(tmp_path, text)


def test_trace_hash_identity_and_regular_bounded_file(tmp_path):
    path, _ = trace(tmp_path)
    with pytest.raises(WitnessError, match='hash'):
        parse_trace(path, enabled_tick=100, end_tick=150, expected_cpu=CPUS[0],
                    allowed_cpus=CPUS, expected_sha256='0' * 64)
    link = tmp_path / 'link'
    link.symlink_to(path)
    with pytest.raises(WitnessError, match='regular'):
        parse_trace(link, enabled_tick=100, end_tick=150, expected_cpu=CPUS[0])
    with path.open('wb') as out:
        out.truncate(MAX_TRACE_BYTES + 1)
    with pytest.raises(WitnessError, match='32 MiB'):
        parse_trace(path, enabled_tick=100, end_tick=150, expected_cpu=CPUS[0])


def test_unknown_cpu_invalid_encoding_and_unexpected_retry_are_rejected(tmp_path):
    with pytest.raises(WitnessError, match='CPU'):
        trace(tmp_path, line(120, 'Calling exit_group(0)...').replace(CPUS[0], 'other.cpu'))
    with pytest.raises(WitnessError, match='retry'):
        trace(tmp_path, line(120, 'Retrying exit_group(0)...'))
    path = tmp_path / 'bad'
    path.write_bytes(b'\xff\n')
    with pytest.raises(WitnessError, match='ASCII'):
        parse_trace(path, enabled_tick=100, end_tick=150, expected_cpu=CPUS[0])


def test_parser_can_load_standalone_in_gem5(tmp_path):
    module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'swdb/dx100_witness.py'))
    path, expected = trace(tmp_path)
    assert module['parse_trace'](path, enabled_tick=100, end_tick=150,
        expected_cpu=CPUS[0], allowed_cpus=CPUS) == expected


def test_initial_worker_retry_retains_partial_preseal_history(tmp_path):
    text = (line(105, 'Retrying futex(1, 2, 3, 4, 5, 6)...', 1)
        + line(105, 'futex still needs retry.', 1)
        + line(115, 'Retrying futex(1, 2, 3, 4, 5, 6)...', 1)
        + line(115, 'Returned 0.', 1)
        + line(120, 'Calling exit_group(0)...') + line(120, 'Returned 0.'))
    _, found = trace(tmp_path, text)
    assert found['completed'] is True
    assert found['initial_partial_calls'] == [{'cpu': CPUS[1], 'thread': 0, 'name': 'futex', 'tick': 105, 'line': 1}]
    assert found['pending_calls'] == []
    with pytest.raises(WitnessError, match='orphan'):
        trace(tmp_path, line(105, 'Returned 0.', 1) + text)
    with pytest.raises(WitnessError, match='unexpected syscall retry'):
        trace(tmp_path, text + line(140, 'Retrying futex(1, 2, 3, 4, 5, 6)...', 1))


def evaluation(tmp_path):
    path, found = trace(tmp_path)
    ref = found['trace']
    parser = Path(__file__).resolve().parents[1] / 'swdb/dx100_witness.py'
    binary = {'path': str(tmp_path / 'bfs'), 'sha256': 'b' * 64}
    simulator = {'path': str(tmp_path / 'gem5.opt'), 'sha256': 'c' * 64}
    workload = {'id': 'graph', 'source': 0, 'representation': {'path': str(tmp_path / 'graph.sg'), 'sha256': 'd' * 64}}
    binding = {'binary': binary, 'simulator': simulator, 'workload': workload, 'roi': 'bfs.dx100.traversal.v1'}
    def artifact(name):
        item = tmp_path / name
        item.write_text('// Explicit contract fixture.\n')
        return {'path': str(item), 'sha256': hashlib.sha256(item.read_bytes()).hexdigest()}
    driver, source, harness = artifact('driver.py'), artifact('bfs.cc'), artifact('benchmark.h')
    from swdb.artifacts import digest
    continuation = {'state': 'finished', 'checker': CHECKER, 'exit_tick': 150, 'exit_code': 0,
        'exit_cause': 'simulate() limit reached', 'stop_reason': 'exit_witness',
        'normal_exit_observed': False, 'chunk_ticks': 10**9, 'simulated_ticks': 50,
        'max_ticks': 10**10, 'exit_witness': found}
    treatment = {'flag': 'SyscallBase', 'format_flags': ['FmtFlag'],
        'scope': 'post-seal verifier continuation only', 'output': 'separate_simulator_trace',
        'disabled_format_flags': ['FmtTicksOff', 'FmtStackTrace'],
        'disabled_roi_flags': ['MAATrace', 'MAARangeFuser', 'MAAIndirect']}
    trace_ref = {**ref, **treatment, 'enabled_tick': 100}
    continuation['post_roi_trace'] = trace_ref
    continuation['parser_sha256'] = hashlib.sha256(parser.read_bytes()).hexdigest()
    seal = {'format': 'swdb.dx100.roi-seal.v1', 'roi_exit_tick': 100,
        'roi_exit_cause': 'm5_exit instruction encountered', 'execution_binding_sha256': digest(binding),
        'driver_sha256': driver['sha256'], 'verification': continuation,
        'verification_parser': {'path': str(parser), 'sha256': continuation['parser_sha256']}}
    seal_path = tmp_path / 'roi-seal.json'
    seal_path.write_text(json.dumps(seal))
    seal_ref = {'path': str(seal_path), 'sha256': hashlib.sha256(seal_path.read_bytes()).hexdigest(), **seal}
    log = tmp_path / 'simulation.log'
    log.write_text('SWDB_DX100_ROI_SEALED\nVerification: PASS\nVerification Time: 0.1\nAverage Time: 0.2\n')
    log_ref = {'path': str(log), 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
    check = {'checker': CHECKER, 'state': 'passed', 'passed': True, 'execution': 'new-v2',
        'binding': binding, 'source': 0, 'binary_sha256': binary['sha256'], 'continuation': continuation,
        'observed_verdicts': [{'verdict': 'PASS', 'line': 2, 'after_seal': True}],
        'sealed_roi': {k: seal_ref[k] for k in ('path', 'sha256')}, 'output': log_ref,
        'output_sha256': log_ref['sha256'], 'timed_source': source, 'verifier_source': {**source, 'harness': harness},
        'parent_results': [], 'completion_sequence': {'kind': 'pinned_author', 'observed': True, 'times': [
            {'kind': 'Verification Time', 'seconds': 0.1, 'line': 3, 'after_seal': True, 'finite': True},
            {'kind': 'Average Time', 'seconds': 0.2, 'line': 4, 'after_seal': True, 'finite': True}]}}
    return {'id': 'new-v2', 'outcome': {'state': 'complete'},
        'request': {'verification': {'checker': CHECKER, 'max_ticks': 10**10, 'post_roi_trace': 'SyscallBase'}, 'binary': binary,
                    'simulator': simulator, 'workload': workload},
        'build': {'binary': binary['path'], 'binary_sha256': binary['sha256'], 'simulator_sha256': simulator['sha256']},
        'context': {'verifier': CHECKER, 'source': 0, 'roi': binding['roi'],
            'instrumentation': {'post_roi_trace': {**treatment, 'chunk_ticks': 10**9}},
            'verification_driver': driver, 'timed_source': source, 'verifier_source': {**source, 'harness': harness},
            'verification_parser': {'path': str(parser), 'sha256': hashlib.sha256(parser.read_bytes()).hexdigest()},
            'post_roi_trace': trace_ref, 'execution_binding': binding,
            'execution_binding_sha256': digest(binding), 'sealed_roi': seal_ref},
        'correctness': {'state': 'passed', 'checks': [check]},
        'stages': [{'stage': 'simulation', 'state': 'complete', 'returncode': 0,
                    'log': str(log), 'log_sha256': log_ref['sha256']}]}


def test_completed_witness_does_not_require_normal_guest_exit(tmp_path):
    data = evaluation(tmp_path)
    original = copy.deepcopy(data)
    assert validate_completed_witness(data)['completed'] is True
    assert data == original
    data['outcome']['state'] = 'running'
    assert validate_completed_witness(data, require_complete_evaluation=False)['completed'] is True


@pytest.mark.parametrize('mutation', [
    lambda d: d['request']['verification'].update(checker='dx100.bfs.verifier.v1'),
    lambda d: d['context'].update(verifier='dx100.bfs.verifier.v1'),
    lambda d: d['correctness']['checks'][0].update(checker='dx100.bfs.verifier.v1'),
    lambda d: d['correctness']['checks'][0].update(execution='old-a6'),
    lambda d: d['correctness']['checks'][0].update(source=1),
    lambda d: d['correctness']['checks'][0].update(binary_sha256='f' * 64),
    lambda d: d['correctness']['checks'][0]['observed_verdicts'][0].update(verdict='FAIL'),
    lambda d: d['context']['post_roi_trace'].update(path=d['stages'][0]['log']),
    lambda d: d['context']['post_roi_trace'].update(format_flags=[]),
    lambda d: d['context']['verification_parser'].update(sha256='0' * 64),
    lambda d: d['outcome'].update(state='timed_out'),
    lambda d: d['stages'][0].update(state='failed', returncode=-15),
    lambda d: d['correctness']['checks'][0]['continuation'].update(normal_exit_observed=True),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness']['exit_request'].update(tick=99),
])
def test_completed_validator_rejects_wrong_identity_and_operational_failures(tmp_path, mutation):
    from swdb.cli import Failure
    data = evaluation(tmp_path)
    mutation(data)
    with pytest.raises(Failure):
        validate_completed_witness(data)


@pytest.mark.parametrize('mutation', [
    lambda d: d['correctness']['checks'][0].pop('completion_sequence'),
    lambda d: d['correctness']['checks'][0]['completion_sequence'].update(observed=False),
    lambda d: d['correctness']['checks'][0]['completion_sequence'].update(kind='protected_candidate'),
    lambda d: d['correctness']['checks'][0]['completion_sequence']['times'][0].update(line=1),
    lambda d: d['correctness']['checks'][0]['completion_sequence']['times'][0].update(seconds=float('inf')),
    lambda d: d['correctness']['checks'][0]['observed_verdicts'][0].update(line=True),
    lambda d: d['correctness']['checks'][0]['continuation'].update(exit_code=False),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness']['exit_request'].update(status=False),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness']['exit_request'].update(return_line=2.0),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness']['caller'].update(thread=False),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness'].update(events_after_exit=0),
    lambda d: d['correctness']['checks'][0]['continuation']['exit_witness'].update(pending_calls=[
        {'cpu': CPUS[0], 'thread': 0, 'name': 'exit_group', 'state': 'calling'}]),
    lambda d: d['correctness']['checks'][0].update(timed_source={'path': '/tmp/other', 'sha256': '0'*64}),
    lambda d: d['context']['verifier_source'].pop('harness'),
    lambda d: d['context']['verification_parser'].update(path='relative/path'),
    lambda d: d['context']['instrumentation']['post_roi_trace'].update(disabled_format_flags=[]),
])
def test_metadata_only_validation_still_requires_typed_and_bound_observations(tmp_path, mutation):
    from swdb.cli import Failure
    data = evaluation(tmp_path)
    mutation(data)
    with pytest.raises(Failure):
        validate_completed_witness(data, verify_artifacts=False)


def test_parser_rejects_control_characters_and_wrong_worker_thread(tmp_path):
    text = line(120, 'Calling exit_group(0)...') + line(120, 'Returned 0.')
    for invalid in (text.replace('\n', '\r\n'), text.replace('Calling', 'Call\x00ing'),
                    text + line(130, 'Calling futex(1)...', 1, 1)):
        with pytest.raises(WitnessError):
            trace(tmp_path, invalid)


def test_record_witness_rechecks_available_artifacts_without_changing_data(tmp_path):
    data = evaluation(tmp_path)
    original = copy.deepcopy(data)
    found = validate_record_witness(data)
    assert found['availability']['state'] == 'verified'
    assert len(found['availability']['artifacts']) == 8
    assert all(row['state'] == 'verified' for row in found['availability']['artifacts'])
    assert data == original


def remote_evaluation(tmp_path, monkeypatch):
    import swdb.dx100_witness as module
    monkeypatch.setattr(module.socket, 'gethostname', lambda: 'local-test.example')
    data = evaluation(tmp_path)
    data['context']['host'] = 'mbit10'
    data['context']['execution_environment'] = {'host': 'mbit10.eecs.umich.edu'}
    def replace(item):
        if isinstance(item, dict):
            return {key: replace(value) for key, value in item.items()}
        if isinstance(item, list):
            return [replace(value) for value in item]
        if isinstance(item, str) and item.startswith(str(tmp_path)):
            return '/data/swdb-witness-contract-fixture/' + item[len(str(tmp_path))+1:]
        return item
    data = replace(data)
    from swdb.artifacts import digest
    binding = data['context']['execution_binding']
    data['context']['execution_binding_sha256'] = digest(binding)
    data['context']['sealed_roi']['execution_binding_sha256'] = digest(binding)
    return data


def test_remote_metadata_explicitly_reports_unavailable_evidence(tmp_path, monkeypatch):
    data = remote_evaluation(tmp_path, monkeypatch)
    found = validate_record_witness(data)
    assert found['availability']['state'] == 'remote_unverified'
    rows = {row['kind']: row for row in found['availability']['artifacts']}
    assert rows['parser']['state'] == 'verified'
    assert rows['trace']['state'] == 'remote_unverified'


@pytest.mark.parametrize('host', ['local-test', None, ''])
def test_missing_local_artifacts_are_not_remote_evidence(tmp_path, monkeypatch, host):
    from swdb.cli import Failure
    data = remote_evaluation(tmp_path, monkeypatch)
    data['context']['host'] = host
    data['context'].pop('execution_environment')
    with pytest.raises(Failure):
        validate_record_witness(data)


def test_inconsistent_host_identities_are_rejected(tmp_path, monkeypatch):
    from swdb.cli import Failure
    data = remote_evaluation(tmp_path, monkeypatch)
    data['build']['execution_environment'] = {'host': 'other-host'}
    with pytest.raises(Failure, match='inconsistent execution host'):
        validate_record_witness(data)


def test_available_artifact_mismatch_rejects_even_if_others_are_remote(tmp_path, monkeypatch):
    from swdb.cli import Failure
    data = remote_evaluation(tmp_path, monkeypatch)
    parser = tmp_path / 'retained-parser.py'
    parser.write_text('changed parser bytes')
    data['context']['verification_parser']['path'] = str(parser)
    data['context']['sealed_roi']['verification_parser']['path'] = str(parser)
    with pytest.raises(Failure, match='parser bytes differ'):
        validate_record_witness(data)


@pytest.mark.parametrize('artifact', ['output', 'trace', 'timed_source', 'protected_wrapper', 'seal'])
def test_local_artifact_tampering_is_rejected(tmp_path, artifact):
    from swdb.cli import Failure
    data = evaluation(tmp_path)
    rows = validate_record_witness(data)['availability']['artifacts']
    path = Path(next(row['path'] for row in rows if row['kind'] == artifact))
    path.write_text(path.read_text() + '\nchanged\n')
    with pytest.raises(Failure):
        validate_record_witness(data)


def test_resealed_output_cannot_substitute_spoofed_completion_rows(tmp_path):
    from swdb.cli import Failure
    data = evaluation(tmp_path)
    check = data['correctness']['checks'][0]
    path = Path(check['output']['path'])
    path.write_text('SWDB_DX100_ROI_SEALED\nVerification: PASS\n')
    new_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    check['output']['sha256'] = check['output_sha256'] = data['stages'][0]['log_sha256'] = new_hash
    with pytest.raises(Failure, match='protected output observations'):
        validate_record_witness(data)


def test_dangling_symlink_does_not_count_as_remote_missing_file(tmp_path):
    from swdb.cli import Failure
    data = evaluation(tmp_path)
    path = Path(data['correctness']['checks'][0]['output']['path'])
    path.unlink()
    path.symlink_to(tmp_path / 'missing')
    with pytest.raises(Failure, match='symlink'):
        validate_record_witness(data)

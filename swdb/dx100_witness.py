"""Bounded DX100 v2 syscall evidence, not a normal-termination oracle.

Updated: 2026-09-27 ET. Parsing loads standalone inside pinned gem5 Python;
SWDB imports belong only in the downstream validator.
"""

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import socket


CHECKER = 'dx100.bfs.verifier.v2'
FORMAT = 'swdb.dx100.exit-witness.v1'
MAX_TRACE_BYTES = 32 * 1024 * 1024
# The seal embeds structured progress observations from the bounded trace.
# Give that serialized artifact its own explicit producer/consumer ceiling;
# it need not fit the former 64 KiB assumption. No trace allowance changes.
MAX_SEAL_BYTES = 32 * 1024 * 1024
MAX_LINE_BYTES = 8192
MAX_OUTPUT_BYTES = 2 * 1024**3
CPUS = tuple(f'system.switch_cpus{i}' for i in range(4))
_HASH = re.compile(r'[0-9a-f]{64}')
_LINE = re.compile(r' *(\d{1,24}): SyscallBase: ([A-Za-z_][A-Za-z0-9_.]*): T(\d{1,4}) : syscall (.+)')
_DECIMAL = r'[0-9]{1,24}(?:\.[0-9]{1,24})?(?:[eE][+-]?[0-9]{1,3})?'
# Pinned CPUProgressEvent::process uses DPRINTFN, which bypasses debug flags.
# Event::name supplies Event_<instance>; this is not a SyscallBase observation.
_PROGRESS = re.compile(r' *(\d{1,24}): Event_(\d{1,24}): ([A-Za-z_][A-Za-z0-9_.]*) '
    r'progress event, total committed:(\d{1,24}), progress insts committed: (\d{1,24}), IPC: (' + _DECIMAL + r')')
_CALL = re.compile(r'(Calling|Retrying) ([A-Za-z_][A-Za-z0-9_]*)\(([^\r\n]*)\)\.\.\.')
_RETURN = re.compile(r'Returned (-?\d{1,24})\.')
_RETRY = re.compile(r'([A-Za-z_][A-Za-z0-9_]*) (needs retry|still needs retry)\.')


class WitnessError(ValueError):
    """Missing or contradictory evidence; never a negative BFS verdict."""


def _need(condition, message):
    if not condition:
        raise WitnessError(message)


def graph_verification_contract(application):
    """Stable treatment identity shared by compilation, dispatch and evidence."""
    _need(application in {'gapbs', 'dx100-gapbs'}, 'unsupported original graph application')
    return {'contract': 'swdb.bfs.original-adjacency.v1',
            'input_format': 'gapbs.sg64' if application == 'gapbs' else 'gapbs.sg32',
            'byte_order': 'little',
            'adjacency': 'outgoing CSR from exact registered serialized input',
            'maximum_extra_bytes': 2147483648,
            'preload': 'before checkpoint and ROI',
            'verification': 'after ROI on exact returned parent buffer',
            'allocation': 'all oracle adjacency and checker work arrays allocated before ROI'}


def _integer(value, name, minimum=0):
    _need(type(value) is int and minimum <= value < 2**64, f'invalid {name}')
    return value


def _same(left, right):
    # JSON's Boolean and integer types are distinct even though Python's == is not.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _validate_progress(row, allowed, start, end):
    _need(isinstance(row, dict) and set(row) == {
        'line', 'tick', 'event', 'cpu', 'total_committed', 'interval_committed', 'ipc'},
        'invalid progress observation fields')
    _need(row['cpu'] in allowed, 'progress trace names an unexpected CPU')
    _need(start <= _integer(row['tick'], 'progress tick') <= end,
          'progress event lies outside enabled interval')
    _integer(row['line'], 'progress line', 1)
    _integer(row['event'], 'progress event')
    total = _integer(row['total_committed'], 'progress total committed')
    _need(_integer(row['interval_committed'], 'progress interval committed') <= total,
          'progress interval exceeds total committed instructions')
    _need(isinstance(row['ipc'], str) and re.fullmatch(_DECIMAL, row['ipc']) is not None
          and math.isfinite(float(row['ipc'])), 'invalid progress IPC')


def _reference(value, name):
    _need(isinstance(value, dict) and isinstance(value.get('path'), str)
          and Path(value['path']).is_absolute() and '..' not in Path(value['path']).parts
          and isinstance(value.get('sha256'), str) and _HASH.fullmatch(value['sha256']),
          f'invalid {name} artifact reference')
    return {key: value[key] for key in ('path', 'sha256')}


def seal_bytes(data):
    """Canonical producer bytes, bounded separately from the raw syscall trace."""
    raw = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode('utf-8')
    _need(len(raw) <= MAX_SEAL_BYTES, f"ROI seal exceeds {MAX_SEAL_BYTES}-byte read/write bound")
    return raw


def _read(path, limit, *, kind="evidence"):
    """Hash the same bounded regular-file bytes that the caller consumes."""
    path = Path(path)
    _need(path.is_absolute() and not path.is_symlink(), 'evidence requires an absolute regular file')
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            _need(stat.S_ISREG(before.st_mode), 'evidence requires a regular file')
            _need(before.st_size <= limit, f"{kind} exceeds {limit}-byte read bound")
            raw = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            _need(len(raw) <= limit, f"{kind} exceeds {limit}-byte read bound")
            _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                  (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                  and len(raw) == before.st_size, 'evidence changed while reading')
    except OSError as exc:
        raise WitnessError(f'regular evidence file unavailable: {path}: {exc}') from None
    return raw, hashlib.sha256(raw).hexdigest()


def parse_trace(path, *, enabled_tick, end_tick, expected_cpu, expected_thread=0,
                allowed_cpus=None, expected_sha256=None, allow_incomplete=False):
    """Parse only the separate simulator trace, including later worker activity.

    An incomplete result means no exit_group was observed yet. Contradictory,
    truncated, or half-written exit evidence always raises, even during polling.
    CPU object + hardware thread identify a trace stream, not a guest PID/TGID.
    """
    enabled_tick = _integer(enabled_tick, 'enabled_tick')
    end_tick = _integer(end_tick, 'end_tick')
    expected_thread = _integer(expected_thread, 'expected_thread')
    _need(end_tick >= enabled_tick, 'invalid trace interval')
    allowed = [expected_cpu] if allowed_cpus is None else list(allowed_cpus)
    _need(allowed and len(allowed) == len(set(allowed)) and expected_cpu in allowed
          and all(isinstance(cpu, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', cpu) for cpu in allowed),
          'invalid allowed CPU identity')
    _need(type(allow_incomplete) is bool, 'allow_incomplete must be Boolean')
    raw, digest = _read(path, MAX_TRACE_BYTES, kind="post-ROI syscall trace")
    _need(expected_sha256 is None or (_HASH.fullmatch(str(expected_sha256)) and digest == expected_sha256),
          'trace hash differs from retained identity')
    _need(not raw or raw.endswith(b'\n'), 'truncated trace line')
    try:
        text = raw.decode('ascii')
    except UnicodeDecodeError:
        raise WitnessError('trace must be ASCII') from None
    _need(all(character == '\n' or ' ' <= character <= '~' for character in text),
          'invalid control character in trace format')
    pending, exit_request, exit_count = {}, None, 0
    seen_streams, initial_partial, progress_rows = set(), [], []
    previous_tick, line_count, after_exit = enabled_tick, 0, 0
    for number, line in enumerate(text.splitlines(), 1):
        line_count = number
        _need(len(line) <= MAX_LINE_BYTES and '\r' not in line, 'trace line exceeds bound or format')
        match = _LINE.fullmatch(line)
        progress = _PROGRESS.fullmatch(line)
        _need(match is not None or progress is not None, f'invalid simulator trace format at line {number}')
        tick, cpu = (int(progress[1]), progress[3]) if progress else (int(match[1]), match[2])
        _need(cpu in allowed, 'trace names an unexpected CPU')
        _need(enabled_tick <= tick <= end_tick, 'trace event lies outside enabled interval')
        _need(tick >= previous_tick, 'trace ticks are out of order')
        previous_tick = tick
        if exit_request is not None:
            after_exit += 1
        if progress:
            row = {'line': number, 'tick': tick, 'event': int(progress[2]), 'cpu': cpu,
                'total_committed': int(progress[4]), 'interval_committed': int(progress[5]), 'ipc': progress[6]}
            _validate_progress(row, allowed, enabled_tick, end_tick)
            progress_rows.append(row)
            continue
        thread, body = int(match[3]), match[4]
        _need(thread == expected_thread, 'trace caller hardware thread differs')
        key = (cpu, thread)
        first_event = key not in seen_streams
        seen_streams.add(key)
        call, returned, retry = _CALL.fullmatch(body), _RETURN.fullmatch(body), _RETRY.fullmatch(body)
        if call:
            phase, name, args = call.groups()
            if phase == 'Retrying':
                current = pending.get(key)
                if current is None and first_event and name != 'exit_group':
                    # setupRetry may precede trace enable; the scheduled event
                    # emits Retrying before its synchronous result. Preserve
                    # this partial non-exit history rather than invent a call.
                    current = {'name': name, 'args': args, 'state': 'retry',
                               'tick': tick, 'line': number, 'retrying': True}
                    pending[key] = current
                    initial_partial.append({'cpu': cpu, 'thread': thread, 'name': name, 'tick': tick, 'line': number})
                _need(current is not None and current['state'] == 'retry'
                      and (current['name'], current['args']) == (name, args), 'unexpected syscall retry')
                _need(name != 'exit_group', 'exit_group cannot retry')
                current.update(state='calling', retrying=True, tick=tick)
                continue
            _need(key not in pending, 'new syscall replaces a pending call')
            if name == 'exit_group':
                exit_count += 1
                _need(exit_count == 1, 'duplicate exit_group witness')
                _need((cpu, thread) == (expected_cpu, expected_thread), 'exit_group caller identity differs')
                _need(args == '0', 'exit_group status must be exactly zero')
            pending[key] = {'name': name, 'args': args, 'state': 'calling',
                            'tick': tick, 'line': number, 'retrying': False}
        elif returned or body == 'No return value.':
            current = pending.get(key)
            _need(current is not None and current['state'] == 'calling', 'orphan syscall return')
            if current['name'] == 'exit_group':
                _need(returned is not None and int(returned[1]) == 0, 'exit_group return must be zero')
                _need(tick == current['tick'], 'exit_group call and return must have the same tick')
                exit_request = {'status': 0, 'tick': tick, 'call_line': current['line'],
                                'return_line': number, 'return_value': 0}
            pending.pop(key)
        elif retry:
            current = pending.get(key)
            _need(current is not None and current['state'] == 'calling' and current['name'] == retry[1],
                  'unexpected syscall retry notification')
            _need(current['name'] != 'exit_group', 'exit_group cannot retry')
            _need((retry[2] == 'still needs retry') == current['retrying'], 'inconsistent retry phase')
            current['state'] = 'retry'
        else:
            raise WitnessError(f'unrecognized syscall trace format at line {number}')
    _need(not any(row['name'] == 'exit_group' for row in pending.values()), 'incomplete exit_group call/return')
    _need(exit_request is not None or allow_incomplete, 'missing exit_group witness')
    result = {'format': FORMAT, 'completed': exit_request is not None,
        'trace': {'path': str(Path(path)), 'sha256': digest, 'bytes': len(raw)},
        'enabled_tick': enabled_tick, 'end_tick': end_tick,
        'caller': {'cpu': expected_cpu, 'thread': expected_thread}, 'allowed_cpus': allowed,
        'exit_request': exit_request, 'line_count': line_count, 'events_after_exit': after_exit,
        'initial_partial_calls': initial_partial,
        'pending_calls': [{'cpu': cpu, 'thread': thread, 'name': row['name'], 'state': row['state']}
                          for (cpu, thread), row in sorted(pending.items())]}
    if progress_rows:
        # Preserve the exact receipt shape of earlier traces without progress.
        result['progress_records'] = progress_rows
    return result


def _completion(check, context):
    sequence, verdicts = check['completion_sequence'], check['observed_verdicts']
    _need(sequence.get('observed') is True and len(verdicts) == 1,
          'protected completion sequence is missing')
    verdict_line = _integer(verdicts[0]['line'], 'verdict line', 1)
    candidate = bool(context.get('candidate_build'))
    _need(sequence['kind'] == ('protected_candidate' if candidate else 'pinned_author'),
          'protected completion kind differs from build treatment')
    if candidate:
        parents = check['parent_results']
        _need(len(parents) == 1, 'protected parent result is missing or ambiguous')
        parent = parents[0]
        _need(parent['after_seal'] is True and _integer(parent['source'], 'parent source') == context['source']
              and _integer(parent['vertices'], 'parent vertices', 1) == _integer(parent['parent_count'], 'parent count', 1)
              and _integer(parent['line'], 'parent line', 1) < verdict_line
              and re.fullmatch(r'[a-f0-9]{16}', parent['parent_fnv1a64']),
              'protected parent result does not precede and bind the structural verdict')
        if context.get('workload', {}).get('num_vertices') is not None:
            _need(parent['vertices'] == context['workload']['num_vertices'], 'protected parent result has another graph size')
        _reference(context['candidate_driver'], 'protected candidate wrapper')
    else:
        times = sequence['times']
        _need(len(times) == 2 and [row['kind'] for row in times] == ['Verification Time', 'Average Time'],
              'author benchmark completion sequence is missing')
        for row in times:
            _need(row['after_seal'] is True and row['finite'] is True
                  and type(row['seconds']) in (int, float) and math.isfinite(row['seconds']) and row['seconds'] >= 0,
                  'invalid author completion observation')
        _need(verdict_line < _integer(times[0]['line'], 'verification time line', 1)
              < _integer(times[1]['line'], 'average time line', 1), 'author completion sequence is reordered')
        _reference(context['verifier_source']['harness'], 'protected author harness')
    for field in ('timed_source', 'verifier_source'):
        _reference(context[field], field)
        _need(_same(check[field], context[field]), f'check {field} differs from executed source')


def _output_evidence(path):
    """Recompute completion rows and hash from the same bounded output bytes."""
    path = Path(path)
    _need(path.is_absolute() and not path.is_symlink(), 'output requires an absolute regular file')
    verdicts, parents, times, markers = [], [], [], 0
    digest, consumed = hashlib.sha256(), 0
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            _need(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_OUTPUT_BYTES, 'output exceeds regular-file bound')
            for number in range(1, MAX_OUTPUT_BYTES + 1):
                raw = stream.readline(1024*1024 + 1)
                if not raw:
                    break
                consumed += len(raw)
                _need(len(raw) <= 1024*1024 and consumed <= MAX_OUTPUT_BYTES, 'output exceeds line or byte bound')
                digest.update(raw)
                line = raw.decode('utf-8', errors='replace')
                if line.strip() == 'SWDB_DX100_ROI_SEALED':
                    markers += 1
                found = re.fullmatch(r'\s*Verification\s*:\s*(PASS|FAIL)\s*', line)
                if found:
                    verdicts.append({'verdict': found[1], 'line': number, 'after_seal': markers == 1})
                found = re.fullmatch(r'SWDB_BFS_RESULT source=(\d+) vertices=(\d+) parent_count=(\d+) parent_fnv1a64=([a-f0-9]{16})\s*', line)
                if found:
                    parents.append({'source': int(found[1]), 'vertices': int(found[2]), 'parent_count': int(found[3]),
                        'parent_fnv1a64': found[4], 'line': number, 'after_seal': markers == 1,
                        'fingerprint_kind': 'noncryptographic FNV-1a over little-endian signed32 parent values'})
                found = re.fullmatch(r'\s*(Verification Time|Average Time):\s*([0-9]+(?:\.[0-9]+)?(?:[eE][+-]?\d+)?)\s*', line)
                if found:
                    value = float(found[2])
                    times.append({'kind': found[1], 'seconds': value, 'line': number,
                                  'after_seal': markers == 1, 'finite': math.isfinite(value)})
            after = os.fstat(stream.fileno())
            _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                  (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and consumed == before.st_size,
                  'output changed while reading')
    except OSError as exc:
        raise WitnessError(f'protected output unavailable: {exc}') from None
    _need(markers == 1, 'protected output needs exactly one ROI seal marker')
    return digest.hexdigest(), verdicts, parents, times


def _witness_artifacts(data):
    context, check = data['context'], data['correctness']['checks'][0]
    rows = [('seal', context['sealed_roi']), ('parser', context['verification_parser']),
            ('trace', context['post_roi_trace']), ('output', check['output']),
            ('verification_driver', context['verification_driver']),
            ('host_memory_observer', context['host_memory_observer']),
            ('timed_source', context['timed_source']), ('verifier_source', context['verifier_source'])]
    rows.append(('protected_wrapper', context['candidate_driver'] if context.get('candidate_build')
                 else context['verifier_source']['harness']))
    return [(kind, _reference(reference, kind)) for kind, reference in rows]


def _verify_artifact(data, kind, reference):
    context, check = data['context'], data['correctness']['checks'][0]
    seal, witness = context['sealed_roi'], check['continuation']['exit_witness']
    if kind == 'trace':
        actual = parse_trace(reference['path'], enabled_tick=witness['enabled_tick'], end_tick=witness['end_tick'],
            expected_cpu=CPUS[0], expected_thread=0, allowed_cpus=CPUS, expected_sha256=reference['sha256'])
        _need(_same(actual, witness), 'retained witness differs from actual simulator trace')
    elif kind == 'output':
        digest, verdicts, parents, times = _output_evidence(reference['path'])
        _need(digest == reference['sha256'] and _same(verdicts, check['observed_verdicts'])
              and _same(parents, check['parent_results']) and _same(times, check['completion_sequence']['times']),
              'retained protected output observations differ from actual bytes')
    else:
        raw, digest = _read(reference['path'], MAX_SEAL_BYTES if kind == 'seal' else 8*1024*1024,
                            kind='ROI seal' if kind == 'seal' else kind)
        _need(digest == reference['sha256'], f'retained {kind} bytes differ')
        if kind == 'seal':
            _need(_same(json.loads(raw), {key: value for key, value in seal.items() if key not in {'path', 'sha256'}}),
                  'retained ROI seal bytes differ')


def validate_completed_witness(evaluation, *, verify_artifacts=True, require_complete_evaluation=True):
    """Validate one v2 execution's witness without imposing normal guest exit.

    The adapter independently checks protected BFS output. This boundary checks
    its retained verdict and exact execution/seal/parser/trace associations.
    Metadata-only inspection is explicit; qualification should verify artifacts.
    Aggregates must validate their actual component evaluations individually.
    """
    from swdb.artifacts import digest
    from swdb.cli import Failure

    try:
        data = evaluation
        request, context, build = data['request'], data['context'], data['build']
        checks = data['correctness']['checks']
        _need(data['correctness']['state'] == 'passed' and len(checks) == 1, 'v2 needs one passed structural check')
        check = checks[0]
        _need(request['verification']['checker'] == context['verifier'] == check['checker'] == CHECKER,
              'v2 request/context/checker identity differs')
        _need(request['verification'].get('post_roi_trace') == 'SyscallBase', 'v2 trace treatment was not requested')
        _need(check.get('passed') is True and check.get('state') == 'passed' and check['execution'] == data['id'],
              'v2 structural verdict or execution identity differs')
        _need(data['outcome']['state'] == 'complete' if require_complete_evaluation else
              data['outcome']['state'] in {'submitted', 'running', 'complete'}, 'evaluation has an operational failure or is incomplete')
        stages = [row for row in data['stages'] if row.get('stage') == 'simulation']
        _need(len(stages) == 1 and stages[0].get('state') == 'complete'
              and type(stages[0].get('returncode')) is int and stages[0]['returncode'] == 0,
              'simulator process did not finish cleanly')
        _need(not any(row.get('state') in {'failed', 'timed_out', 'interrupted', 'budget_exhausted', 'incompatible'}
                      for row in data['stages']), 'evaluation retains an operational failure')
        binding, seal = context['execution_binding'], context['sealed_roi']
        _need(digest(binding) == context['execution_binding_sha256'] == seal['execution_binding_sha256']
              and _same(check['binding'], binding), 'execution binding differs')
        _need(binding['binary'] == request['binary'] == {'path': build['binary'], 'sha256': build['binary_sha256']}
              and check['binary_sha256'] == build['binary_sha256'], 'timed binary identity differs')
        _need(binding['simulator'] == request['simulator'] and binding['simulator']['sha256'] == build['simulator_sha256'],
              'simulator identity differs')
        _need(binding['workload'] == request['workload'] and check['source'] == context['source'] == request['workload']['source']
              and binding['roi'] == context['roi'], 'workload/source/ROI identity differs')
        for source in (check['source'], context['source'], request['workload']['source']):
            _integer(source, 'BFS source')
        _need(seal['format'] == 'swdb.dx100.roi-seal.v1' and seal['roi_exit_cause'] == 'm5_exit instruction encountered'
              and seal['driver_sha256'] == context['verification_driver']['sha256'], 'ROI seal or driver identity differs')
        runtime = context['instrumentation']['verifier_runtime']
        expected_runtime = {
            'driver_sha256': context['verification_driver']['sha256'],
            'parser_sha256': context['verification_parser']['sha256'],
            'observer_sha256': context['host_memory_observer']['sha256']}
        _need(_same(runtime, expected_runtime)
              and all(isinstance(value, str) and _HASH.fullmatch(value) for value in expected_runtime.values()),
              'verifier runtime instrumentation differs from retained helper identities')
        _need(seal['host_memory_observer_sha256'] == expected_runtime['observer_sha256'],
              'sealed host memory observer identity differs')
        _need(check['sealed_roi'] == {key: seal[key] for key in ('path', 'sha256')}, 'check names another ROI seal')
        verdicts = check['observed_verdicts']
        _need(len(verdicts) == 1 and verdicts[0].get('verdict') == 'PASS' and verdicts[0].get('after_seal') is True,
              'protected structural verdict is missing or failed')
        if context.get('candidate_build') and context['roi'] == 'bfs.complete_call.v1':
            contract = graph_verification_contract(context.get('application'))
            _need(build.get('adapter') == 'dx100.complete_call.v2'
                  and _same(context.get('graph_verification'), contract)
                  and _same(context['instrumentation'].get('graph_verification'), contract),
                  'complete-call candidate lacks the original-adjacency checker treatment')
            _need(_same(_reference(context['verifier_source'], 'original graph oracle'),
                        _reference(context['candidate_driver'], 'candidate wrapper')),
                  'original graph oracle is not the protected compiled wrapper')
        _completion(check, context)
        continuation = check['continuation']
        _need(_same(continuation, seal['verification']), 'continuation differs from ROI seal')
        witness, trace_ref = continuation['exit_witness'], context['post_roi_trace']
        _need(continuation['state'] == 'finished' and continuation['checker'] == CHECKER
              and _integer(continuation['exit_code'], 'continuation exit code') == 0, 'continuation did not finish cleanly')
        normal = continuation['normal_exit_observed']
        _need(type(normal) is bool and (
            normal and continuation['exit_cause'] == 'exiting with last active thread context' and continuation['stop_reason'] == 'normal_exit'
            or not normal and continuation['exit_cause'] == 'simulate() limit reached' and continuation['stop_reason'] == 'exit_witness'),
            'termination receipt contradicts the actual event')
        start = _integer(seal['roi_exit_tick'], 'ROI exit tick')
        end = _integer(continuation['exit_tick'], 'continuation exit tick')
        maximum = _integer(request['verification']['max_ticks'], 'continuation maximum ticks', 1)
        _need(_integer(continuation['max_ticks'], 'retained maximum ticks') == maximum
              and _integer(continuation['simulated_ticks'], 'simulated ticks') == end-start
              and 0 < end-start <= maximum and _integer(continuation['chunk_ticks'], 'chunk ticks') == 10**9,
              'continuation tick accounting differs')
        parser_ref = context['verification_parser']
        _need(continuation['parser_sha256'] == parser_ref['sha256'] and _HASH.fullmatch(parser_ref['sha256']),
              'witness parser identity differs')
        _need(_same(seal['verification_parser'], parser_ref), 'sealed parser identity differs')
        _need(_same(continuation['post_roi_trace'], trace_ref) and trace_ref['flag'] == 'SyscallBase'
              and trace_ref['format_flags'] == ['FmtFlag'] and _integer(trace_ref['enabled_tick'], 'trace enable tick') == start,
              'trace instrumentation differs from the sealed treatment')
        treatment = context['instrumentation']['post_roi_trace']
        for key, expected in {
            'flag': 'SyscallBase', 'scope': 'post-seal verifier continuation only',
            'output': 'separate_simulator_trace', 'format_flags': ['FmtFlag'],
            'disabled_format_flags': ['FmtTicksOff', 'FmtStackTrace'],
            'disabled_roi_flags': ['MAATrace', 'MAARangeFuser', 'MAAIndirect']}.items():
            _need(_same(treatment.get(key), expected) and _same(trace_ref.get(key), expected),
                  f'trace {key} differs from declared post-seal treatment')
        _need(_integer(treatment['chunk_ticks'], 'instrumentation chunk ticks') == continuation['chunk_ticks'],
              'trace chunk treatment differs')
        _need(witness.get('format') == FORMAT and witness.get('completed') is True
              and _same(witness['caller'], {'cpu': CPUS[0], 'thread': 0}) and witness['allowed_cpus'] == list(CPUS)
              and _integer(witness['enabled_tick'], 'witness enable tick') == start
              and _integer(witness['end_tick'], 'witness end tick') == end,
              'completed witness identity or interval differs')
        _need(_same(witness['trace'], {key: trace_ref[key] for key in ('path', 'sha256', 'bytes')}), 'trace evidence identity differs')
        _need(_HASH.fullmatch(trace_ref['sha256']) and 0 < _integer(trace_ref['bytes'], 'trace byte count') <= MAX_TRACE_BYTES,
              'trace identity or size is invalid')
        exit_request = witness['exit_request']
        _need(_integer(exit_request['status'], 'exit status') == _integer(exit_request['return_value'], 'exit return') == 0
              and start <= _integer(exit_request['tick'], 'exit request tick') <= end
              and 0 < _integer(exit_request['call_line'], 'exit call line')
              < _integer(exit_request['return_line'], 'exit return line')
              <= _integer(witness['line_count'], 'trace line count') <= trace_ref['bytes'], 'exit request evidence is inconsistent')
        _need(_integer(witness['events_after_exit'], 'events after exit') == witness['line_count'] - exit_request['return_line'],
              'post-exit event accounting differs')
        progress_rows = witness.get('progress_records', [])
        _need(isinstance(progress_rows, list) and len(progress_rows) <= witness['line_count'],
              'invalid progress observation list')
        previous_line, previous_tick = 0, start
        for row in progress_rows:
            _validate_progress(row, CPUS, start, end)
            _need(previous_line < row['line'] <= witness['line_count']
                  and row['line'] not in {exit_request['call_line'], exit_request['return_line']}
                  and previous_tick <= row['tick'], 'invalid progress observation order or line')
            _need((row['line'] > exit_request['return_line'] or row['tick'] <= exit_request['tick'])
                  and (row['line'] < exit_request['call_line'] or row['tick'] >= exit_request['tick']),
                  'progress observation tick differs from exit ordering')
            previous_line, previous_tick = row['line'], row['tick']
        pending = witness['pending_calls']
        _need(isinstance(pending, list) and len(pending) <= len(CPUS), 'invalid pending syscall list')
        seen = set()
        for row in pending:
            key = (row['cpu'], _integer(row['thread'], 'pending thread'))
            _need(key not in seen and key[0] in CPUS and key[1] == 0 and row['name'] != 'exit_group'
                  and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', row['name']) and row['state'] in {'calling', 'retry'},
                  'invalid pending syscall identity')
            seen.add(key)
        initial = witness['initial_partial_calls']
        _need(isinstance(initial, list) and len(initial) <= len(CPUS), 'invalid initial partial syscall list')
        seen = set()
        for row in initial:
            key = (row['cpu'], _integer(row['thread'], 'initial partial thread'))
            _need(key not in seen and key[0] in CPUS and key[1] == 0 and row['name'] != 'exit_group'
                  and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', row['name'])
                  and start <= _integer(row['tick'], 'initial partial tick') <= end
                  and 1 <= _integer(row['line'], 'initial partial line') <= witness['line_count'],
                  'invalid initial partial syscall identity')
            seen.add(key)
        trace_path, seal_path, output_path = Path(trace_ref['path']), Path(seal['path']), Path(check['output']['path'])
        _need(trace_path.name == 'post-roi-syscalls.log' and trace_path.parent == seal_path.parent
              and trace_path != output_path and stages[0]['log'] == str(output_path)
              and stages[0]['log_sha256'] == check['output']['sha256'] == check['output_sha256'],
              'separate simulator trace or output identity differs')
        for kind, reference in _witness_artifacts(data):
            if verify_artifacts:
                _verify_artifact(data, kind, reference)
        return copy.deepcopy(witness)
    except (WitnessError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Failure(f'invalid completed DX100 v2 witness: {exc}') from None


def validate_record_witness(evaluation):
    """Qualify retained v2 metadata and report which raw evidence was rechecked.

    Only absent artifacts on another named host under /data or /data1 may be
    remote_unverified. Every present file is verified independently, even when
    another file is remote. This is not authority to dispatch from metadata.
    """
    from swdb.cli import Failure

    witness = validate_completed_witness(evaluation, verify_artifacts=False)
    try:
        context = evaluation['context']
        hosts = [context.get('host'), context.get('execution_environment', {}).get('host'),
                 evaluation.get('build', {}).get('execution_environment', {}).get('host')]
        hosts = [host for host in hosts if host is not None]
        _need(all(isinstance(host, str) and host and host == host.strip() for host in hosts), 'invalid execution host identity')
        _need(len({host.split('.')[0] for host in hosts}) <= 1, 'inconsistent execution host identities')
        host = hosts[0].split('.')[0] if hosts else None
        remote = host is not None and host != socket.gethostname().split('.')[0]
        rows = []
        for kind, reference in _witness_artifacts(evaluation):
            path = Path(reference['path'])
            _need(not path.is_symlink(), f'{kind} artifact is a symlink')
            if path.exists():
                _verify_artifact(evaluation, kind, reference)
                state = 'verified'
            else:
                _need(remote and str(path).startswith(('/data/', '/data1/')), f'{kind} raw artifact is unavailable locally')
                state = 'remote_unverified'
            rows.append({'kind': kind, **reference, 'state': state})
        state = 'remote_unverified' if any(row['state'] == 'remote_unverified' for row in rows) else 'verified'
        return {'witness': witness, 'availability': {'state': state, 'host': host, 'artifacts': rows}}
    except (WitnessError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Failure(f'invalid retained DX100 v2 witness: {exc}') from None

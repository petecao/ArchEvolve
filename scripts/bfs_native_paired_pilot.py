#!/usr/bin/env python3
"""One fixed unchanged native paired calibration. Created: 2026-09-26 ET.

This separately bounded study does not restart the expired pilot, retry a cell,
choose workloads, collect diagnostics, decide a gain, or publish a protocol.
"""
import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import socket
import signal
import sys
import threading
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_native_repeatability as previous
from scripts.bfs_freeze_pilot import native_lane, require, sample_grid, unchanged, workload_plan
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from swdb import artifacts, bfs_coverage, bfs_native, bfs_native_pair, bfs_protocol, profile, yamlio
from swdb.store import Store

RUN_ID = 'bfs-native-paired-pilot-20260926-a1'
PLAN = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-paired-pilot-20260926-a1.json'
LANE = 'mbit10-evaluation-node1'
DEADLINE = datetime(2026, 9, 26, 15, 0, tzinfo=ZoneInfo('America/New_York'))
SOURCES = [0, 1234, 7777]
REPETITIONS = 10
COLLECTION = {'method': bfs_native_pair.METHOD, 'order_seed': 20260926}
ANALYSIS = bfs_native_pair.ANALYSIS
RUNTIME_SETTINGS = ('OMP_THREAD_LIMIT', 'OMP_WAIT_POLICY', 'GOMP_SPINCOUNT', 'GOMP_CPU_AFFINITY')
POLICY = {'minimum_speedup': 1.05, 'confidence': 0.95, 'bootstrap_resamples': 2000,
          'bootstrap_seed': 20260925, 'maximum_relative_spread': 0.10}
BOUNDS = {'driver_seconds': 10800, 'outer_seconds': 10920, 'pair_seconds': 2400,
          'evaluation_seconds': 2400, 'evaluation_cli_seconds': 2460,
          'build_seconds': 180, 'run_seconds': 60, 'threads': 4, 'repetitions': 10,
          'warmups': 0, 'retries': 0, 'trials': 240,
          'batch_raw_bytes': 8 * 1024**3, 'sampled_rss_bytes': 16 * 1024**3,
          'resource_max_gap_seconds': 30}


def now():
    return datetime.now(DEADLINE.tzinfo).isoformat()


def validate_plan(plan):
    old = yamlio.load(previous.PLAN)
    previous.validate_plan(old)
    expected = []
    for cell in old['cells']:
        suffix = cell['id'].removeprefix(previous.RUN_ID + '.').removesuffix('.evaluation')
        prefix = RUN_ID + '.' + suffix
        expected.append({**cell, 'id': prefix + '.pair',
                         'baseline_evaluation': prefix + '.baseline', 'candidate_evaluation': prefix + '.candidate'})
    require(plan.get('message_version') == '1.0' and plan.get('id') == RUN_ID
            and plan.get('role') == 'paired_unchanged_native_calibration'
            and plan.get('lane') == LANE and plan.get('deadline_et') == DEADLINE.isoformat()
            and plan.get('bounds') == BOUNDS and all(type(value) is int for value in plan['bounds'].values())
            and plan.get('sources') == SOURCES and all(type(value) is int for value in plan['sources'])
            and plan.get('collection') == COLLECTION and type(plan['collection'].get('order_seed')) is int
            and plan.get('analysis') == ANALYSIS and plan.get('profitability') == POLICY
            and type(plan.get('maximum_relative_spread')) is float and plan['maximum_relative_spread'] == 0.10
            and all(plan.get(key) is False for key in ('candidate_assessment', 'protocol_freeze', 'profiling'))
            and plan.get('historical_expired_pilot_deadline_et') == previous.PILOT_DEADLINE.isoformat()
            and plan.get('cells') == expected,
            'paired plan changes fixed identities, ordering, collection, policy, or finite bounds')


def launch_budget(current):
    remaining = (DEADLINE - current).total_seconds()
    require(remaining >= BOUNDS['outer_seconds'],
            'the fixed paired deadline must leave the complete outer allowance (latest launch 11:58 ET)')
    return min(BOUNDS['driver_seconds'], remaining - (BOUNDS['outer_seconds'] - BOUNDS['driver_seconds']))


def pair_request(first, cell, machine):
    """Admit the exact old source record, then construct the new prospective grid."""
    base = previous.first_request(first, cell, machine)
    request = {'message_version': '1.0', 'id': cell['id'], 'collection': copy.deepcopy(COLLECTION),
               'budget': {'total_seconds': BOUNDS['pair_seconds']}}
    for role in bfs_native_pair.ROLES:
        member = copy.deepcopy(base)
        member.update(id=cell[role + '_evaluation'], repetitions=REPETITIONS)
        member['budget']['total_seconds'] = BOUNDS['evaluation_seconds']
        request[role] = member
    bfs_native_pair.validate_request(request)
    return request


def validate_pair_result(store, first, pair, machine, request):
    """Return full real source samples after request, binary, graph and raw checks."""
    require(pair.get('id') == request['id'] and pair.get('request') == request
            and pair.get('outcome', {}).get('state') == 'complete'
            and pair.get('evidence_kind') == 'execution' and pair.get('gain_claim') is False,
            'paired pilot lacks its exact completed real collection receipt')
    retained = store.get(pair['id'], 'evaluation_pair')
    require(retained is not None and artifacts.digest(retained) == artifacts.digest(pair),
            'public paired result differs from its retained record')
    candidate = store.get(first['candidate'], 'candidate')
    unchanged(store, candidate)
    workload = store.get(first['context']['workload']['id'], 'workload')
    bfs_protocol.verify_immutable(workload)
    workload_plan(workload, 18)
    pair_begin, pair_end = pair_interval(pair)
    evaluations, summaries = {}, {}
    outputs = {row['output'] for row in first['timing']}
    for role in bfs_native_pair.ROLES:
        evaluation = store.get(pair.get(role + '_evaluation'), 'evaluation')
        require(evaluation is not None and evaluation.get('id') == request[role]['id']
                and evaluation.get('request') == request[role]
                and bfs_coverage._real(evaluation) and evaluation.get('outcome', {}).get('state') == 'complete'
                and not bfs_coverage._correctness(evaluation, store), 'paired role lacks exact checked real evaluation evidence')
        require([(row.get('repetition'), row.get('source_position')) for row in evaluation['timing']]
                == [(repeat, position) for repeat in range(REPETITIONS) for position in range(len(SOURCES))]
                and len(evaluation['correctness']['checks']) == REPETITIONS * len(SOURCES)
                and all(check.get('passed') is True for check in evaluation['correctness']['checks']),
                'paired role changes the full repetition-major timing/check grid')
        summaries[role] = sample_grid(evaluation, SOURCES, REPETITIONS)
        require(native_lane(evaluation['context'], machine) == LANE, 'paired role ran in another lane')
        for field in ('candidate', 'implementation', 'machine', 'source_snapshot'):
            require(evaluation.get(field) == first.get(field), 'paired source identity changed: ' + field)
        for field in ('candidate_sha256', 'source_revision', 'application', 'adapter', 'target',
                      'machine_sha256', 'function', 'threads', 'sources', 'roi', 'protocol', 'basis',
                      'process_policy', 'verifier', 'backend_configuration', 'instrumentation'):
            require(evaluation['context'].get(field) == first['context'].get(field), 'paired context changed: ' + field)
        for field in ('id', 'canonical_sha256', 'adjacency_order_sha256', 'canonical_file_sha256', 'sources'):
            require(evaluation['context']['workload'].get(field) == first['context']['workload'].get(field),
                    'paired graph identity changed: ' + field)
        for field in ('compiler', 'compiler_version', 'flags', 'template_sha256', 'wrapper_sha256',
                      'binary_sha256', 'execution_environment'):
            require(evaluation['build'].get(field) == first['build'].get(field), 'paired build identity changed: ' + field)
        require(not outputs.intersection(row['output'] for row in evaluation['timing']), 'paired pilot reuses prior process output')
        validate_member_interval(evaluation, pair_begin, pair_end)
        outputs.update(row['output'] for row in evaluation['timing'])
        evaluations[role] = evaluation
    bfs_native_pair.validate_receipt(store, evaluations['baseline'], evaluations['candidate'],
        {'sampling': {'collection': COLLECTION, 'analysis': ANALYSIS, 'repetitions': REPETITIONS}})
    return summaries


def pair_interval(pair):
    begin, ready, end = (bfs_protocol._timestamp(pair.get(key)) for key in ('started', 'prepared_at', 'finished'))
    require(begin <= ready <= end and (end - begin).total_seconds() <= BOUNDS['pair_seconds'],
            'paired receipt exceeds its complete pair budget or has reversed timestamps')
    return begin, end


def validate_member_interval(evaluation, pair_begin, pair_end):
    for stage in evaluation['stages']:
        begin, end = bfs_protocol._timestamp(stage.get('started')), bfs_protocol._timestamp(stage.get('finished'))
        require(pair_begin <= begin <= end <= pair_end, 'paired member stage lies outside its pair interval')
        bound = {'build': BOUNDS['build_seconds'], 'build_reuse': BOUNDS['build_seconds'],
                 'execution': BOUNDS['run_seconds']}.get(stage['stage'])
        require(bound is None or (end - begin).total_seconds() <= bound,
                'paired member build/execution exceeded its finite stage allowance')


def _reference(ref, label, limit=32 * 1024**2):
    require(isinstance(ref, dict) and isinstance(ref.get('path'), str)
            and Path(ref['path']).is_absolute() and isinstance(ref.get('sha256'), str)
            and re.fullmatch(r'[a-f0-9]{64}', ref['sha256']), label + ' needs an absolute hashed artifact')
    try:
        raw, digest = bfs_native.observation_bytes(ref['path'], limit, label)
    except bfs_native.StageFailure as exc:
        raise ValueError(str(exc)) from None
    require(digest == ref['sha256'], label + ' content changed')
    return raw


def validate_driver_receipt(receipt, plan):
    """Reopen finite-study receipts; this validates collection, never profitability."""
    validate_plan(plan)
    stamp = bfs_protocol._timestamp
    require(receipt.get('id') == RUN_ID and receipt.get('state') == 'complete'
            and receipt.get('role') == 'paired_unchanged_native_calibration'
            and receipt.get('bounds') == BOUNDS
            and all(type(value) is int for value in receipt['bounds'].values())
            and all(receipt.get(key) is False for key in ('gain_claim', 'protocol_freeze', 'profiling'))
            and receipt.get('deadline_et') == DEADLINE.isoformat(), 'driver receipt changed its completed role or finite bounds')
    started, finished = stamp(receipt.get('started')), stamp(receipt.get('finished'))
    launch_budget(started)
    wall = receipt.get('host_wall_s')
    require(type(wall) in (int, float) and 0 <= wall <= BOUNDS['driver_seconds']
            and started <= finished <= DEADLINE
            and (finished - started).total_seconds() <= min(BOUNDS['driver_seconds'], wall + 1),
            'driver elapsed time or absolute deadline exceeds the fixed study')
    require(Path(receipt['plan']['path']).resolve() == PLAN.resolve()
            and json.loads(_reference(receipt['plan'], 'driver plan')) == plan
            and receipt['plan']['sha256'] == artifacts.file_hash(PLAN)
            and receipt['plan'].get('canonical_sha256') == artifacts.digest(plan), 'driver plan differs from the exact canonical plan')
    records = Path(receipt.get('records', '')).resolve()
    require(records == (ROOT / 'records').resolve(), 'driver records directory differs from its exact checkout')
    store = Store(records)
    machine = store.get('mbit10', 'machine')
    require(native_lane({'host': 'mbit10', 'target': 'mbit10', 'lane': receipt.get('lane'),
                         'backend_configuration': {'lane': LANE}}, machine) == LANE,
            'driver lacks the recorded verifier receipt for the fixed lane')
    runs = previous.raw_root(receipt.get('runs_dir', ''))
    folder = runs / (RUN_ID + '.driver')
    runtime = receipt.get('runtime', {})
    inherited = receipt.get('inherited_runtime_settings')
    require(isinstance(inherited, dict) and set(inherited) == set(RUNTIME_SETTINGS)
            and all(value is None or isinstance(value, str) for value in inherited.values()),
            'driver lacks the exact observed inherited OpenMP runtime settings')
    python = runtime.get('python_executable')
    require(isinstance(python, str) and Path(python).is_absolute()
            and runtime.get('python_sha256') == artifacts.file_hash(python), 'driver Python executable changed or is unavailable')
    from scripts import bfs_process
    modules = {'native': bfs_native.__file__, 'pair': bfs_native_pair.__file__, 'protocol': bfs_protocol.__file__,
               'driver': __file__, 'process': bfs_process.__file__}
    require(isinstance(runtime.get('modules'), dict) and set(runtime['modules']) == set(modules), 'runtime source snapshots are incomplete')
    reopened = [receipt['plan']]
    for name, source in modules.items():
        ref = runtime['modules'][name]
        require(ref.get('path') == str(folder / (name + '-runtime.py'))
                and ref.get('source_path') == str(Path(source).resolve())
                and ref.get('sha256') == artifacts.file_hash(source), 'runtime source differs from the reviewed collector: ' + name)
        _reference(ref, name + ' runtime source', 4 * 1024**2)
        reopened.append(ref)
    require(receipt.get('verifier_module_sha256') == runtime['modules']['native']['sha256']
            and receipt.get('paired_module_sha256') == runtime['modules']['pair']['sha256'], 'runtime module annotations disagree')
    rss = receipt.get('rss', {})
    require(rss.get('nominal_interval_seconds') == 5 and rss.get('true_peak') is False and rss.get('hard_kernel_cap') is False
            and rss.get('scope') == 'driver and observed owned descendants across sessions; PID/start-time bound',
            'RSS observations changed their sampled scope')
    require(rss.get('samples', {}).get('path') == str(folder / 'rss-samples.jsonl'), 'RSS sample artifact path differs')
    samples = [json.loads(line) for line in _reference(rss['samples'], 'RSS samples').splitlines()]
    require(len(samples) >= 2, 'RSS/space observations do not cover the collection')
    times, rss_values, raw_values, guard_durations = [], [], [], []
    known, driver_identity, previous_guard_end = set(), None, started
    require(type(receipt.get('driver_pid')) is int and receipt['driver_pid'] > 0, 'driver PID is invalid')
    for sample in samples:
        times.append(stamp(sample.get('sampled_at')))
        guard_start, guard_end = stamp(sample.get('guard_started')), stamp(sample.get('guard_finished'))
        guard_wall = sample.get('guard_wall_s')
        require(type(guard_wall) in (int, float) and 0 <= guard_wall <= BOUNDS['resource_max_gap_seconds']
                and previous_guard_end <= guard_start <= times[-1] <= guard_end <= finished
                and (guard_end - guard_start).total_seconds() <= guard_wall + 1,
                'resource guard duration or timestamps violate collection bounds')
        guard_durations.append(guard_wall)
        previous_guard_end = guard_end
        processes = sample.get('processes')
        require(isinstance(processes, list) and processes and all(isinstance(row, dict) for row in processes), 'RSS process sample is malformed')
        require(all(type(row.get(key)) is int and row[key] >= 0 for row in processes
                    for key in ('pid', 'parent_pid', 'start_ticks', 'rss_bytes'))
                and len({row['pid'] for row in processes}) == len(processes)
                and any(row['pid'] == receipt.get('driver_pid') for row in processes), 'RSS sample lacks distinct owned process identities')
        identities = {row['pid']: (row['pid'], row['start_ticks']) for row in processes}
        parents = {row['pid']: row['parent_pid'] for row in processes}
        for pid in parents:
            visited = set()
            while pid in parents:
                require(pid not in visited, 'RSS parent rows contain an ownership cycle')
                visited.add(pid)
                pid = parents[pid]
        current_driver = identities[receipt['driver_pid']]
        if driver_identity is None:
            driver_identity = current_driver
        require(current_driver == driver_identity, 'driver PID was reused during resource observation')
        owned = {pid for pid, identity in identities.items() if identity in known or identity == driver_identity}
        remaining = [row for row in processes if row['pid'] not in owned]
        while remaining:
            connected = [row for row in remaining if row['parent_pid'] in owned]
            require(bool(connected), 'new RSS process identity is not connected to an observed owned parent')
            owned.update(row['pid'] for row in connected)
            remaining = [row for row in remaining if row['pid'] not in owned]
        known.update(identities.values())
        require(type(sample.get('rss_bytes')) is int and sample['rss_bytes'] == sum(row['rss_bytes'] for row in processes)
                and sample['rss_bytes'] <= BOUNDS['sampled_rss_bytes'], 'sampled owned RSS is inconsistent or exceeded its ceiling')
        require(type(sample.get('batch_raw_bytes')) is int and 0 <= sample['batch_raw_bytes'] <= BOUNDS['batch_raw_bytes']
                and type(sample.get('raw_free_bytes')) is int and sample['raw_free_bytes'] >= 30 * 1024**3
                and type(sample.get('build_free_bytes')) is int and sample['build_free_bytes'] >= 10 * 1024**3
                and sample.get('lane') == receipt.get('lane'), 'sampled raw/build storage or lane violates the plan')
        rss_values.append(sample['rss_bytes']); raw_values.append(sample['batch_raw_bytes'])
    require(times == sorted(times) and started <= times[0] <= times[-1] <= finished,
            'resource sample timestamps contradict collection bounds')
    boundaries = [started, *times, finished]
    max_gap = max((right - left).total_seconds() for left, right in zip(boundaries, boundaries[1:]))
    require(max_gap <= BOUNDS['resource_max_gap_seconds']
            and type(rss.get('maximum_gap_seconds')) in (int, float) and rss['maximum_gap_seconds'] == max_gap
            and rss.get('maximum_guard_seconds') == max(guard_durations),
            'resource observations have an excessive or inconsistent gap/guard duration')
    require(type(rss.get('peak_sampled_bytes')) is int and rss['peak_sampled_bytes'] == max(rss_values)
            and rss.get('last_sampled_bytes') == rss_values[-1]
            and type(receipt.get('batch_raw_bytes_peak_sampled')) is int
            and receipt['batch_raw_bytes_peak_sampled'] == max(raw_values)
            and receipt.get('batch_raw_bytes_sampled') == raw_values[-1], 'retained resource peaks disagree with actual samples')
    reopened.append(rss['samples'])
    entries = receipt.get('cells', [])
    require([row.get('id') for row in entries] == [row['id'] for row in plan['cells']]
            and all(row.get('state') == 'complete' for row in entries), 'driver receipt lacks all four fixed ordered cells')
    stages = receipt.get('stages', [])
    require(len(stages) == 9 and all(row.get('state') == 'complete' and type(row.get('returncode')) is int
                                   and row['returncode'] == 0 for row in stages), 'driver stage history is incomplete or contains extra attempts')
    for index, stage in enumerate(stages):
        stderr = {'path': stage.get('stderr'), 'sha256': stage.get('stderr_sha256')}
        require(stderr['path'] == str(folder / (f'{index:02d}' + '.stderr')), 'driver stage stderr path differs')
        _reference(stderr, 'driver stage stderr')
        reopened.append(stderr)
        if index > 4:
            continue
        bound = 10 if index == 0 else 30
        require(type(stage.get('host_wall_s')) in (int, float) and 0 <= stage['host_wall_s'] <= bound
                and type(stage.get('timeout_s')) in (int, float) and 0 < stage['timeout_s'] <= bound,
                'driver preflight stage exceeded its finite bound')
        if index == 0:
            expected_command, output = ['git', 'rev-parse', 'HEAD'], folder / 'repository-commit.txt'
        else:
            entry, cell = entries[index - 1], plan['cells'][index - 1]
            first = store.get(cell['first_evaluation'], 'evaluation')
            compiler = entry.get('compiler_resolved')
            require(isinstance(compiler, str) and Path(compiler).is_absolute()
                    and compiler == str(Path(first['build']['compiler']).resolve(strict=True))
                    and entry.get('compiler_sha256') == artifacts.file_hash(compiler), 'compiler executable changed or is unavailable')
            expected_command, output = [compiler, '--version'], folder / (cell['id'] + '.compiler-version.txt')
        require(stage.get('command') == expected_command and stage.get('output') == str(output), 'driver preflight command/path differs')
        output_ref = {'path': str(output), 'sha256': stage.get('stdout_sha256')}
        raw = _reference(output_ref, 'driver preflight stdout').decode()
        if index == 0:
            require(re.fullmatch('[a-f0-9]{40}', receipt.get('repository_commit', ''))
                    and raw.strip() == receipt['repository_commit'], 'driver revision differs from its observed public git output')
        else:
            require(raw.splitlines()[:2] == store.get(cell['first_evaluation'], 'evaluation')['build']['compiler_version'],
                    'driver compiler version differs from its pinned historical first block')
        reopened.append(output_ref)
    public = stages[5:]
    previous_end = times[0]
    for cell, entry, stage in zip(plan['cells'], entries, public):
        require(entry.get('first_evaluation') == cell['first_evaluation']
                and entry.get('first_record_sha256') == cell['first_evaluation_sha256']
                and entry.get('pair') == cell['id']
                and all(entry.get(role + '_evaluation') == cell[role + '_evaluation'] for role in bfs_native_pair.ROLES),
                'driver cell identity differs from the prospective plan')
        begin, end = stamp(entry.get('started')), stamp(entry.get('finished'))
        require(previous_end <= begin <= end <= times[-1] and (end - begin).total_seconds() <= BOUNDS['evaluation_cli_seconds'],
                'paired cell exceeds its retained resource coverage or duration bound')
        previous_end = end
        ref = entry['request']
        require(ref.get('path') == str(folder / (cell['id'] + '.request.json')), 'public paired request path differs')
        request = json.loads(_reference(ref, 'public paired request'))
        require(request == pair_request(store.get(cell['first_evaluation'], 'evaluation'), cell, store.get('mbit10', 'machine')),
                'public paired request changed from the fixed source/grid/bounds')
        expected = [python, '-m', 'swdb', 'evaluate-pair', ref['path'], '--runs-dir', str(runs),
                    '--lane', LANE, '--records', str(records), '--format', 'json']
        require(stage.get('command') == expected and stage.get('output') == str(folder / (cell['id'] + '.result.json')),
                'public stage does not execute the exact admitted paired request')
        require(type(stage.get('host_wall_s')) in (int, float) and 0 <= stage['host_wall_s'] <= BOUNDS['evaluation_cli_seconds']
                and type(stage.get('timeout_s')) in (int, float) and 0 < stage['timeout_s'] <= BOUNDS['evaluation_cli_seconds'],
                'public paired stage exceeded its execution bound')
        result_ref = {'path': stage['output'], 'sha256': stage['stdout_sha256']}
        result = json.loads(_reference(result_ref, 'public paired result'))
        require(result.get('id') == cell['id'] and artifacts.digest(result) == entry.get('pair_sha256'),
                'public paired result differs from the retained pair identity')
        pair_begin, pair_end = pair_interval(result)
        require(begin <= pair_begin <= pair_end <= end
                and (pair_end - pair_begin).total_seconds() <= stage['host_wall_s'] + 1,
                'public paired result interval is not contained in its driver cell/stage')
        reopened.extend((ref, result_ref))
    return reopened


class DescendantRSS:
    """Sample live owned descendants across sessions, retaining observed PID identities."""
    def __init__(self, pid, proc=Path('/proc')):
        self.pid, self.proc, self.known = pid, Path(proc), {}

    def sample(self):
        pending = [(self.pid, self.known.get(self.pid), None),
                   *((pid, start, None) for pid, start in self.known.items())]
        seen, rows = set(), []
        while pending:
            pid, expected_start, discovered_parent = pending.pop()
            folder = self.proc / str(pid)
            try:
                fields = (folder / 'stat').read_text().rsplit(')', 1)[1].split()
                start, parent, state = int(fields[19]), int(fields[1]), fields[0]
                if expected_start is not None and start != expected_start:
                    continue  # An observed PID has been reused; this is not our process.
                require(discovered_parent is None or parent == discovered_parent or self.known.get(pid) == start,
                        'child PID no longer belongs to its discovering parent; RSS ownership is unavailable')
                if (pid, start) in seen:
                    continue
                seen.add((pid, start))
                status = (folder / 'status').read_text().splitlines()
                values = [line.split() for line in status if line.startswith('VmRSS:')]
                require(state == 'Z' or (len(values) == 1 and len(values[0]) == 3 and values[0][2] == 'kB'),
                        'owned process RSS is unavailable')
                rss = 0 if state == 'Z' else int(values[0][1]) * 1024
                require(rss >= 0, 'owned process RSS is invalid')
                children = []
                for task in (folder / 'task').iterdir():
                    if task.name.isdigit():
                        try:
                            children.extend(int(value) for value in (task / 'children').read_text().split())
                        except FileNotFoundError:
                            require(not task.exists(), 'live owned task child telemetry is unavailable')
                rows.append({'pid': pid, 'parent_pid': parent, 'start_ticks': start, 'rss_bytes': rss})
                self.known[pid] = start
                pending.extend((child, None, pid) for child in children)
            except FileNotFoundError:
                require(pid != self.pid and not folder.exists(), 'live owned process telemetry is unavailable')
            except (IndexError, TypeError) as exc:
                raise ValueError('owned process telemetry is malformed') from exc
        require(any(row['pid'] == self.pid for row in rows), 'driver RSS telemetry is unavailable')
        return {'sampled_at': now(), 'rss_bytes': sum(row['rss_bytes'] for row in rows), 'processes': rows}


class ResourceMonitor:
    """Nominal five-second observations also cover parent-side graph/checker work."""
    def __init__(self, sample):
        self.sample, self.error = sample, None
        self.done = threading.Event()
        self.signal_lock = threading.Lock()
        self.thread = None
        self.last_observation_started = None

    def _observe(self):
        before = time.monotonic()
        self.sample()
        # RSS may be read before storage/lane work. The successful guard's
        # start conservatively bounds that observation's age; its end does not.
        self.last_observation_started = before

    def start(self):
        self._observe()
        self.thread = threading.Thread(target=self._run, daemon=True, name='paired-pilot-resource-guard')
        self.thread.start()

    def _run(self):
        while not self.done.wait(5):
            try:
                self._observe()
            except BaseException as exc:
                self.error = exc
                with self.signal_lock:
                    if not self.done.is_set():
                        os.kill(os.getpid(), signal.SIGTERM)
                return

    def check(self):
        if self.error is not None:
            raise ValueError('paired resource monitor failed: ' + str(self.error))
        require(self.last_observation_started is not None
                and time.monotonic() - self.last_observation_started <= BOUNDS['resource_max_gap_seconds'],
                'resource telemetry is stale beyond its fixed ceiling')

    def stop(self):
        # A sample already in progress may fail while normal error cleanup joins
        # it. Once shutdown begins it must not interrupt final receipt saving.
        with self.signal_lock:
            self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=10)
            require(not self.thread.is_alive(), 'resource monitor failed to stop within cleanup allowance')


def main():
    start, started_at = time.monotonic(), now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=PLAN)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', choices=[LANE], required=True)
    args = parser.parse_args()
    plan = yamlio.load(args.plan)
    validate_plan(plan)
    require(args.plan.resolve() == PLAN.resolve(), 'paired pilot requires the exact canonical plan path')
    allowance = launch_budget(datetime.now(DEADLINE.tzinfo))
    require(socket.gethostname().split('.')[0] == 'mbit10', 'paired pilot requires mbit10')
    runs = previous.raw_root(args.runs_dir)
    records = args.records.resolve()
    require(records == (ROOT / 'records').resolve(), 'real paired pilot requires this exact checkout records directory')
    store = Store(records)
    machine = store.get('mbit10', 'machine')
    verified_lane = profile._verified_lane(machine, args.lane)
    ids = [cell[key] for cell in plan['cells'] for key in ('id', 'baseline_evaluation', 'candidate_evaluation')]
    require(not any(store.get(rid) for rid in ids), 'a planned paired ID already exists; retries are forbidden')
    require(not any((runs / rid).exists() or (Path('/data1/yanruj/EvolveSWDB_builds') / rid).exists() for rid in ids),
            'planned paired output/build directory already exists')
    previous.empty_run_directory(runs)
    folder = runs / (RUN_ID + '.driver')
    folder.mkdir(parents=True, exist_ok=False)
    deadline = start + allowance
    receipt = {'id': RUN_ID, 'created': '2026-09-26', 'started': started_at, 'state': 'running',
        'role': 'paired_unchanged_native_calibration', 'gain_claim': False, 'protocol_freeze': False,
        'profiling': False, 'lane': verified_lane, 'bounds': BOUNDS, 'deadline_et': DEADLINE.isoformat(),
        'plan': {'path': str(args.plan.resolve()), 'sha256': artifacts.file_hash(args.plan), 'canonical_sha256': artifacts.digest(plan)},
        'records': str(records), 'runs_dir': str(runs), 'driver_pid': os.getpid(),
        'batch_raw_bytes_sampled': 0, 'batch_raw_bytes_peak_sampled': 0,
        'stages': [], 'cells': [], 'rss': {'scope': 'driver and observed owned descendants across sessions; PID/start-time bound',
            'nominal_interval_seconds': 5, 'peak_sampled_bytes': 0, 'last_sampled_bytes': 0,
            'maximum_gap_seconds': 0, 'maximum_guard_seconds': 0,
            'true_peak': False, 'hard_kernel_cap': False},
        'limitations': plan['first_block_limitations'] + ['Expired serial controls remain unchanged and unqualified.',
            'Host interference remains uncontrolled; this collection does not establish statistical coverage or a gain.']}
    rss = DescendantRSS(os.getpid())
    rss_path = folder / 'rss-samples.jsonl'
    last_sample = receipt['started']
    save_receipt(folder, receipt)

    def observe_resources():
        nonlocal last_sample
        guard_start, guard_started = time.monotonic(), now()
        lane = profile._verified_lane(machine, args.lane)
        measured = rss.sample()
        measured['lane'] = lane
        measured['batch_raw_bytes'] = previous.batch_storage(runs, sys.maxsize)
        for key, directory in (('raw_free_bytes', runs), ('build_free_bytes', Path('/data1'))):
            usage = os.statvfs(directory)
            measured[key] = usage.f_bavail * usage.f_frsize
        measured.update(guard_started=guard_started, guard_finished=now(), guard_wall_s=time.monotonic() - guard_start)
        gap = (bfs_protocol._timestamp(measured['sampled_at']) - bfs_protocol._timestamp(last_sample)).total_seconds()
        last_sample = measured['sampled_at']
        receipt['rss']['maximum_gap_seconds'] = max(receipt['rss']['maximum_gap_seconds'], gap)
        receipt['rss']['maximum_guard_seconds'] = max(receipt['rss']['maximum_guard_seconds'], measured['guard_wall_s'])
        with rss_path.open('a') as stream:
            stream.write(json.dumps(measured) + '\n')
        receipt['rss']['peak_sampled_bytes'] = max(receipt['rss']['peak_sampled_bytes'], measured['rss_bytes'])
        receipt['rss']['last_sampled_bytes'] = measured['rss_bytes']
        receipt['batch_raw_bytes_sampled'] = measured['batch_raw_bytes']
        receipt['batch_raw_bytes_peak_sampled'] = max(receipt['batch_raw_bytes_peak_sampled'], measured['batch_raw_bytes'])
        require(0 <= gap <= BOUNDS['resource_max_gap_seconds']
                and measured['guard_wall_s'] <= BOUNDS['resource_max_gap_seconds'], 'resource telemetry gap/guard ceiling exceeded')
        require(measured['rss_bytes'] <= BOUNDS['sampled_rss_bytes'], 'sampled owned-descendant RSS ceiling exceeded')
        require(measured['batch_raw_bytes'] <= BOUNDS['batch_raw_bytes'], 'paired batch raw-storage ceiling exceeded')
        require(measured['raw_free_bytes'] >= 30 * 1024**3 and measured['build_free_bytes'] >= 10 * 1024**3,
                'paired raw/build free-space reserve violated')
        require(time.monotonic() < deadline and datetime.now(DEADLINE.tzinfo) < DEADLINE,
                'fixed paired pilot budget/deadline exhausted')

    monitor = ResourceMonitor(observe_resources)

    def resources():
        monitor.check()
        require(time.monotonic() < deadline and datetime.now(DEADLINE.tzinfo) < DEADLINE,
                'fixed paired pilot budget/deadline exhausted')

    def stage(command, timeout, output):
        resources()
        return run_stage(receipt, folder, command, timeout=timeout, deadline=deadline,
                         cwd=ROOT, output=output, monitor=resources)

    with interruption_signals():
        try:
            monitor.start()
            stage(['git', 'rev-parse', 'HEAD'], 10, folder / 'repository-commit.txt')
            receipt['repository_commit'] = (folder / 'repository-commit.txt').read_text().strip()
            receipt['verifier_module_sha256'] = artifacts.file_hash(bfs_native.__file__)
            receipt['paired_module_sha256'] = artifacts.file_hash(bfs_native_pair.__file__)
            receipt['inherited_runtime_settings'] = {name: os.environ.get(name) for name in RUNTIME_SETTINGS}
            from scripts import bfs_process
            receipt['runtime'] = {'python_executable': str(Path(sys.executable).resolve()),
                'python_sha256': artifacts.file_hash(Path(sys.executable).resolve()), 'modules': {}}
            for name, source_path in (('native', bfs_native.__file__), ('pair', bfs_native_pair.__file__),
                                      ('protocol', bfs_protocol.__file__), ('driver', __file__), ('process', bfs_process.__file__)):
                snapshot = folder / (name + '-runtime.py')
                snapshot.write_bytes(Path(source_path).read_bytes())
                receipt['runtime']['modules'][name] = {'path': str(snapshot), 'sha256': artifacts.file_hash(snapshot),
                                                     'source_path': str(Path(source_path).resolve())}
            prepared = []
            for cell in plan['cells']:
                resources()
                first = store.get(cell['first_evaluation'], 'evaluation')
                require(first is not None, 'missing original unchanged evaluation')
                request = pair_request(first, cell, machine)
                candidate = store.get(first['candidate'], 'candidate')
                implementation, source = unchanged(store, candidate)
                artifacts.verify(candidate['artifact'])
                workload = store.get(cell['workload'], 'workload')
                bfs_protocol.verify_immutable(workload)
                workload_plan(workload, 18)
                require(artifacts.file_hash(bfs_native.DRIVER) == cell['driver_template_sha256'], 'trusted timed driver changed')
                compiler = Path(first['build']['compiler']).resolve(strict=True)
                version = folder / (cell['id'] + '.compiler-version.txt')
                stage([str(compiler), '--version'], 30, version)
                require(version.read_text().splitlines()[:2] == first['build']['compiler_version'], 'compiler version changed')
                request_path = folder / (cell['id'] + '.request.json')
                request_path.write_text(json.dumps(request, indent=2) + '\n')
                entry = {'id': cell['id'], 'first_evaluation': first['id'], 'state': 'prepared',
                    'first_record_sha256': artifacts.digest(first), 'compiler_resolved': str(compiler),
                    'compiler_sha256': artifacts.file_hash(compiler),
                    'request': {'path': str(request_path), 'sha256': artifacts.file_hash(request_path)},
                    'availability': previous.verify_available([first, candidate, source, implementation, workload])}
                receipt['cells'].append(entry)
                prepared.append((first, request, request_path, entry))
                save_receipt(folder, receipt)
            # Resolve and retain all four cells before any primary trial.
            for first, request, request_path, entry in prepared:
                resources()
                require(deadline - time.monotonic() >= BOUNDS['evaluation_cli_seconds'], 'insufficient budget for another complete paired cell')
                require(artifacts.file_hash(entry['compiler_resolved']) == entry['compiler_sha256']
                        and artifacts.file_hash(bfs_native.DRIVER) == first['build']['template_sha256'], 'compiler or timed driver changed after preflight')
                require(all(artifacts.file_hash(ref['source_path']) == ref['sha256'] for ref in receipt['runtime']['modules'].values()),
                        'runtime source changed after preflight')
                entry.update(state='running', started=now())
                save_receipt(folder, receipt)
                output = folder / (entry['id'] + '.result.json')
                stage([receipt['runtime']['python_executable'], '-m', 'swdb', 'evaluate-pair', str(request_path), '--runs-dir', str(runs),
                       '--lane', args.lane, '--records', str(records), '--format', 'json'], BOUNDS['evaluation_cli_seconds'], output)
                pair = json.loads(output.read_text())
                current = Store(records)
                entry['timing_summary'] = validate_pair_result(current, first, pair, machine, request)
                entry.update(pair=pair['id'], pair_sha256=artifacts.digest(pair),
                    baseline_evaluation=pair['baseline_evaluation'], candidate_evaluation=pair['candidate_evaluation'])
                entry['availability_after'] = previous.verify_available([pair, *(current.get(pair[role + '_evaluation']) for role in bfs_native_pair.ROLES)])
                require(artifacts.file_hash(entry['compiler_resolved']) == entry['compiler_sha256'], 'compiler changed during paired cell')
                require(all(artifacts.file_hash(ref['source_path']) == ref['sha256'] for ref in receipt['runtime']['modules'].values()),
                        'runtime source changed during paired cell')
                entry.update(state='complete', finished=now())
                save_receipt(folder, receipt)
                resources()
            monitor.stop()
            resources()
            monitor._observe()
            receipt['state'] = 'complete'
        except BaseException as exc:
            receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
            for entry in receipt['cells']:
                if entry['state'] == 'running':
                    entry.update(state='failed', finished=now(), reason=receipt['reason'])
                elif entry['state'] == 'prepared':
                    entry.update(state='not_dispatched')
            raise
        finally:
            try:
                monitor.stop()
                monitor.check()
            except ValueError as exc:
                receipt.update(state='failed', reason=str(exc))
            if rss_path.is_file():
                receipt['rss']['samples'] = {'path': str(rss_path), 'sha256': artifacts.file_hash(rss_path)}
            receipt.update(finished=now(), host_wall_s=time.monotonic() - start)
            final_gap = (bfs_protocol._timestamp(receipt['finished']) - bfs_protocol._timestamp(last_sample)).total_seconds()
            receipt['rss']['maximum_gap_seconds'] = max(receipt['rss']['maximum_gap_seconds'], final_gap)
            if final_gap > BOUNDS['resource_max_gap_seconds']:
                receipt.update(state='failed', reason='final resource telemetry gap exceeded its ceiling')
            save_receipt(folder, receipt)
    require(receipt['state'] == 'complete', receipt.get('reason', 'paired pilot did not complete'))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

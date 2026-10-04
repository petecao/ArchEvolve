#!/usr/bin/env python3
"""Second and final unchanged native calibration block. Created: 2026-09-26 ET.

Only the four evaluations in the reviewed plan are admitted. This is not a
candidate assessment, protocol freeze, profiler, or automatic gain decision.
"""
import argparse
import copy
from datetime import datetime
import json
import os
from pathlib import Path
import socket
import stat
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_freeze_pilot import native_lane, require, sample_grid, unchanged, workload_plan
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from swdb import artifacts, bfs_coverage, bfs_native, bfs_protocol, profile, yamlio
from swdb.store import Store

RUN_ID = 'bfs-native-repeatability-20260926-a1'
LANE = 'mbit10-evaluation-node1'
PILOT_DEADLINE = datetime(2026, 9, 26, 5, 56, 38, tzinfo=ZoneInfo('America/New_York'))
SOURCES = [0, 1234, 7777]
ORDER = [('dx100', 'uniform-random', 'dx10018-a1'),
         ('upstream', 'uniform-random', 'upstream18-a2'),
         ('dx100', 'kronecker', 'dx10018-a1'),
         ('upstream', 'kronecker', 'upstream18-a2')]
BOUNDS = {'driver_seconds': 5400, 'outer_seconds': 5520,
          'evaluation_seconds': 1200, 'evaluation_cli_seconds': 1260,
          'build_seconds': 180, 'run_seconds': 60, 'trials': 60,
          'threads': 4, 'repetitions': 5, 'warmups': 0, 'retries': 0,
          'batch_raw_bytes': 4 * 1024**3}
ENVIRONMENT = {'OMP_NUM_THREADS': '4', 'OMP_DYNAMIC': 'FALSE',
               'OMP_PROC_BIND': 'close', 'OMP_PLACES': 'cores'}
PLAN = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-repeatability-20260926-a1.json'


def now():
    return datetime.now(ZoneInfo('America/New_York')).isoformat()


def validate_plan(plan):
    require(plan.get('id') == RUN_ID and plan.get('lane') == LANE
            and plan.get('pilot_deadline_et') == PILOT_DEADLINE.isoformat()
            and plan.get('bounds') == BOUNDS and plan.get('sources') == SOURCES
            and all(type(v) is int for v in plan['bounds'].values())
            and all(type(v) is int for v in plan['sources']),
            'repeatability plan changes the reviewed identity, lane, sources, or bounds')
    expected = [(f'{RUN_ID}.{impl}.{family}.evaluation',
                 f'bfs-native-pilot-20260925-{previous}.{family}.evaluation')
                for impl, family, previous in ORDER]
    require([(cell.get('id'), cell.get('first_evaluation')) for cell in plan.get('cells', [])] == expected,
            'repeatability plan changes the four admitted evaluation IDs or their order')
    for cell in plan['cells']:
        require(isinstance(cell.get('first_evaluation_sha256'), str)
                and len(cell['first_evaluation_sha256']) == 64, 'missing first-block record identity')


def raw_root(value):
    root = Path(value).resolve()
    require(any(base in root.parents for base in
                (Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))),
            'raw root must be below an authorized EvolveSWDB_runs directory')
    return root


def empty_run_directory(root):
    require(not root.exists() or (root.is_dir() and not any(root.iterdir())),
            'dedicated repeatability run directory must be empty before dispatch')


def pilot_budget(attested, current):
    remaining = int((PILOT_DEADLINE - current).total_seconds())
    require(type(attested) is int and 5400 <= attested <= 43200 and remaining >= 5400,
            'the original pilot deadline must have room for the complete bounded block')
    return min(attested, remaining)


def batch_storage(root, limit):
    """Sample retained apparent bytes without traversing directory symlinks."""
    retained = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            entry = (Path(directory) / name).lstat()
            if not stat.S_ISDIR(entry.st_mode):
                retained += entry.st_size
    require(retained <= limit,
            f'dedicated repeatability batch raw-storage ceiling exceeded: {retained} > {limit} bytes')
    return retained


def first_request(first, cell, machine):
    """Admission from persisted evidence; source bytes are checked separately."""
    require(first.get('id') == cell['first_evaluation']
            and artifacts.digest(first) == cell['first_evaluation_sha256'],
            'first-block evaluation metadata differs from the reviewed plan')
    expected = {'implementation': first['implementation'], 'candidate': first['candidate'],
                'workload': first['context']['workload']['id'],
                'source_sha256': first['context']['candidate_sha256'],
                'canonical_graph_sha256': first['context']['workload']['canonical_sha256'],
                'primary_binary_sha256': first['build']['binary_sha256'],
                'compiler': first['build']['compiler'], 'flags': first['build']['flags'],
                'driver_template_sha256': first['build']['template_sha256']}
    require(all(cell.get(key) == value for key, value in expected.items()),
            'reviewed cell fields differ from its first-block evaluation')
    require(bfs_coverage._real(first) and first.get('outcome', {}).get('state') == 'complete'
            and not bfs_coverage._correctness(first), 'first block lacks checked real native trials')
    context, build = first['context'], first['build']
    sample_grid(first, SOURCES, 5)
    require(native_lane(context, machine) == LANE and context.get('basis') == 'measured'
            and context.get('roi') == 'bfs.complete_call.v1' and context.get('threads') == 4
            and context.get('function') == 'DOBFS' and context.get('protocol') is None
            and context.get('machine_sha256') == artifacts.digest(machine)
            and build.get('execution_environment') == ENVIRONMENT,
            'first block target, ROI, source process, or recorded OpenMP environment differs')
    request = copy.deepcopy(first['request'])
    require(set(request) == {'message_version', 'id', 'candidate', 'machine', 'threads',
            'repetitions', 'sources', 'roi', 'target_configuration', 'workload',
            'comparison_baseline', 'budget'} and request['budget'] == {
                'build_seconds': 180, 'run_seconds': 60, 'total_seconds': 1200}
            and request['sources'] == SOURCES and request['repetitions'] == 5
            and request['threads'] == 4 and request['machine'] == 'mbit10'
            and request['roi'] == context['roi'] and request['candidate'] == first['candidate']
            and request['workload']['id'] == context['workload']['id']
            and request['target_configuration'] == {'lane': LANE},
            'first-block request is outside the fixed native calibration plan')
    request['id'] = cell['id']
    # Pin resolved settings instead of depending on possibly changed defaults.
    request['build'] = {key: copy.deepcopy(build[key]) for key in ('compiler', 'flags')}
    return request


def repeat_result(first, second, machine, request):
    """Validate a complete same-artifact second block; never assess a gain."""
    require(bfs_coverage._real(second) and second.get('outcome', {}).get('state') == 'complete'
            and not bfs_coverage._correctness(second), 'second block lacks complete checked native trials')
    require(second.get('id') == request['id'] and second.get('request') == request
            and second['id'] != first['id'], 'second block does not match its exact new public request')
    require(not ({row['output'] for row in first['timing']}
                 & {row['output'] for row in second['timing']}), 'second block reuses a first-block process output')
    require([(row.get('repetition'), row.get('source_position')) for row in second['timing']]
            == [(repeat, position) for repeat in range(5) for position in range(3)],
            'second block changed the admitted repetition-major trial order')
    summary = sample_grid(second, SOURCES, 5)
    require(native_lane(second['context'], machine) == LANE, 'second block ran in another lane')
    for field in ('candidate', 'implementation', 'machine'):
        require(second.get(field) == first.get(field), f'second-block {field} identity changed')
    for field in ('candidate_sha256', 'source_revision', 'application', 'adapter', 'target',
                  'machine_sha256', 'function', 'threads', 'sources', 'repetitions', 'roi',
                  'protocol', 'basis', 'process_policy', 'verifier', 'backend_configuration', 'instrumentation'):
        require(second['context'].get(field) == first['context'].get(field),
                f'second-block context changed: {field}')
    for field in ('id', 'canonical_sha256', 'adjacency_order_sha256', 'canonical_file_sha256', 'sources'):
        require(second['context']['workload'].get(field) == first['context']['workload'].get(field),
                f'second-block graph identity changed: {field}')
    for field in ('compiler', 'compiler_version', 'flags', 'template_sha256', 'wrapper_sha256',
                  'binary_sha256', 'execution_environment'):
        require(second['build'].get(field) == first['build'].get(field),
                f'second-block build identity changed: {field}')
    return summary


def verify_available(records):
    available = bfs_coverage._availability(records, 'mbit10')
    require(available and all(row['state'] == 'verified' for row in available),
            'retained source, graph, output, or binary is missing or changed')
    return available


def main():
    start = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=PLAN)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', choices=[LANE], required=True)
    parser.add_argument('--pilot-remaining-seconds', type=int, required=True,
                        help='coordinator-attested remaining part of the existing 12-hour pilot budget')
    args = parser.parse_args()
    plan = yamlio.load(args.plan)
    validate_plan(plan)
    runs = raw_root(args.runs_dir)
    require(socket.gethostname().split('.')[0] == 'mbit10', 'repeatability requires mbit10')
    remaining_pilot = pilot_budget(args.pilot_remaining_seconds, datetime.now(PILOT_DEADLINE.tzinfo))
    records = args.records.resolve()
    require(records == (ROOT / 'records').resolve(),
            'real calibration must use the exact checkout records directory')
    store = Store(records)
    machine = store.get('mbit10', 'machine')
    verified_lane = profile._verified_lane(machine, args.lane)
    require(not any(store.get(cell['id']) for cell in plan['cells']),
            'a planned second-block evaluation already exists; retries are forbidden')
    require(not any((runs / cell['id']).exists()
                    or (Path('/data1/yanruj/EvolveSWDB_builds') / cell['id']).exists()
                    for cell in plan['cells']), 'planned output or build directory already exists')
    empty_run_directory(runs)
    folder = runs / (RUN_ID + '.driver')
    folder.mkdir(parents=True, exist_ok=False)
    deadline = start + BOUNDS['driver_seconds']
    receipt = {'id': RUN_ID, 'created': '2026-09-26', 'started': now(), 'state': 'running',
               'role': 'second_unchanged_native_calibration_block', 'gain_claim': False,
               'protocol_freeze': False, 'profiling': False, 'lane': verified_lane,
               'bounds': BOUNDS, 'pilot_remaining_seconds_attested': args.pilot_remaining_seconds,
               'pilot_remaining_seconds_effective': remaining_pilot,
               'pilot_deadline_et': PILOT_DEADLINE.isoformat(),
               'plan': {'path': str(args.plan.resolve()), 'sha256': artifacts.file_hash(args.plan)},
               'stages': [], 'cells': [], 'limitations': [
                   'First-block compiler executable hashes and inherited runtime knobs were not retained.',
                   'Compiler version, source, primary binary, driver, and recorded OpenMP settings are checked.',
                   'Host interference remains uncontrolled; this is calibration, not a frozen gain comparison.']}
    save_receipt(folder, receipt)

    def resources():
        profile._verified_lane(machine, args.lane)
        retained = batch_storage(runs, BOUNDS['batch_raw_bytes'])
        receipt['batch_raw_bytes_sampled'] = retained
        receipt['batch_raw_bytes_peak_sampled'] = max(receipt.get('batch_raw_bytes_peak_sampled', 0), retained)
        for directory, reserve in ((runs, 30), (Path('/data1'), 10)):
            stat = os.statvfs(directory)
            require(stat.f_bavail * stat.f_frsize >= reserve * 1024**3,
                    f'free-space reserve below {reserve} GiB at {directory}')
        require(time.monotonic() < deadline, 'repeatability driver time budget exhausted')
        require(datetime.now(PILOT_DEADLINE.tzinfo) < PILOT_DEADLINE,
                'original global pilot deadline reached')

    def stage(command, timeout, output):
        resources()
        return run_stage(receipt, folder, command, timeout=timeout, deadline=deadline,
                         cwd=ROOT, output=output, monitor=resources)

    with interruption_signals():
        try:
            stage(['git', 'rev-parse', 'HEAD'], 10, folder / 'repository-commit.txt')
            receipt['repository_commit'] = (folder / 'repository-commit.txt').read_text().strip()
            receipt['verifier_module_sha256'] = artifacts.file_hash(bfs_native.__file__)
            receipt['inherited_runtime_settings'] = {name: os.environ.get(name) for name in
                ('OMP_THREAD_LIMIT', 'OMP_WAIT_POLICY', 'GOMP_SPINCOUNT', 'GOMP_CPU_AFFINITY')}
            prepared = []
            for cell in plan['cells']:
                first = store.get(cell['first_evaluation'], 'evaluation')
                require(first is not None, 'missing first-block evaluation')
                request = first_request(first, cell, machine)
                candidate = store.get(first['candidate'], 'candidate')
                implementation, source = unchanged(store, candidate)
                artifacts.verify(candidate['artifact'])
                workload = store.get(request['workload']['id'], 'workload')
                bfs_protocol.verify_immutable(workload)
                workload_plan(workload, 18)
                require(workload['definition']['canonical_sha256'] == first['context']['workload']['canonical_sha256'],
                        'registered canonical graph differs from the first block')
                require(artifacts.file_hash(bfs_native.DRIVER) == first['build']['template_sha256'],
                        'trusted native driver changed since the first block')
                compiler = Path(first['build']['compiler']).resolve(strict=True)
                version_path = folder / (cell['id'] + '.compiler-version.txt')
                stage([first['build']['compiler'], '--version'], 30, version_path)
                require(version_path.read_text().splitlines()[:2] == first['build']['compiler_version'],
                        'compiler version changed since the first block')
                entry = {'id': cell['id'], 'first_evaluation': first['id'], 'state': 'prepared',
                         'first_record_sha256': artifacts.digest(first),
                         'first_verifier_module_sha256': first['context']['verifier_sha256'],
                         'compiler_resolved': str(compiler), 'compiler_sha256': artifacts.file_hash(compiler),
                         'availability': verify_available([first, candidate, source, workload])}
                request_path = folder / (cell['id'] + '.request.json')
                request_path.write_text(json.dumps(request, indent=2) + '\n')
                entry['request'] = {'path': str(request_path), 'sha256': artifacts.file_hash(request_path)}
                receipt['cells'].append(entry)
                prepared.append((first, request_path, entry))
                save_receipt(folder, receipt)
            # Preflight all four before any trial, then use exactly the admitted order.
            for first, request_path, entry in prepared:
                resources()
                require(deadline - time.monotonic() >= BOUNDS['evaluation_cli_seconds'],
                        'remaining driver budget cannot cover another full evaluation')
                require(artifacts.file_hash(entry['compiler_resolved']) == entry['compiler_sha256']
                        and artifacts.file_hash(bfs_native.DRIVER) == first['build']['template_sha256'],
                        'compiler or driver changed after preflight')
                entry.update(state='running', started=now())
                save_receipt(folder, receipt)
                output = folder / (entry['id'] + '.result.json')
                stage([sys.executable, '-m', 'swdb', 'evaluate', str(request_path),
                       '--runs-dir', str(runs), '--lane', args.lane,
                       '--records', str(records), '--format', 'json'], 1260, output)
                second = json.loads(output.read_text())
                entry['evaluation'] = second['id']
                entry['timing_summary'] = repeat_result(first, second, machine, json.loads(request_path.read_text()))
                entry['availability_after'] = verify_available([second])
                require(artifacts.file_hash(entry['compiler_resolved']) == entry['compiler_sha256'],
                        'compiler changed during evaluation')
                entry.update(state='complete', finished=now(),
                             first_binary_sha256=first['build']['binary_sha256'],
                             second_binary_sha256=second['build']['binary_sha256'])
                save_receipt(folder, receipt)
                resources()
            receipt['state'] = 'complete'
        except BaseException as exc:
            receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
            for entry in receipt['cells']:
                if entry['state'] == 'running':
                    entry.update(state='failed', finished=now(), reason=receipt['reason'])
                elif entry['state'] == 'prepared':
                    entry['state'] = 'not_dispatched'
            raise
        finally:
            receipt.update(finished=now(), host_wall_s=time.monotonic() - start)
            save_receipt(folder, receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

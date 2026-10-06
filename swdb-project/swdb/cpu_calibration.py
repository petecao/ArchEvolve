"""Bounded native CPU calibration and immutable target-description import.

Created: 2026-10-06 ET. Effective source-work rates are not hardware issue rates.
"""
import json
import math
import statistics
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from swdb import access, artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store


def register_cli(commands):
    run = commands.add_parser('cpu-calibrate', help='bounded native CPU calibration inside a verified socket lane')
    run.add_argument('--records', type=Path, default=paths.RECORDS)
    run.add_argument('--output', type=Path, required=True, help='new raw folder outside the repository')
    run.add_argument('--machine', default='mbit10')
    run.add_argument('--lane')
    run.add_argument('--fixture', action='store_true', help='portable small fixture; never measured target evidence')
    run.add_argument('--compiler', default='c++')
    run.add_argument('--llvm-bin', type=Path, help='LLVM 22 folder, required for native source-normalized compute counts')
    run.add_argument('--toolchain-flag', action='append', default=[])
    run.add_argument('--build-flag', action='append', default=[])
    run.add_argument('--threads', default='1,2,4,8,16')
    run.add_argument('--chains', default='1,2,4,8,16,32')
    run.add_argument('--working-set-bytes', type=int, default=256 * 1024**2)
    run.add_argument('--cache-bytes', type=int, default=8 * 1024**2)
    run.add_argument('--repetitions', type=int, default=7)
    run.add_argument('--min-trial-s', type=float, default=.2)
    run.add_argument('--max-wall-s', type=float, default=1800)
    run.add_argument('--seed', type=int, default=20261006)
    run.add_argument('--format', choices=['yaml', 'json'], default='json')
    run.set_defaults(cpu_calibration_handler=calibrate)
    sub = commands.add_parser('import-cpu-calibration', help='import a native CPU calibration receipt as per-thread target descriptions')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--receipt', type=Path, required=True)
    sub.add_argument('--id-prefix', required=True)
    sub.add_argument('--fixture', action='store_true', help='explicitly admit a hand fixture; it never becomes measured evidence')
    sub.add_argument('--format', choices=['yaml', 'json'], default='json')
    sub.set_defaults(cpu_calibration_handler=import_receipt)


def stats(values):
    return {'values': values, 'median': statistics.median(values), 'min': min(values),
            'max': max(values), 'spread': max(values) - min(values), 'repetitions': len(values)}


def _fact(value, basis, source, unit):
    return {'value': value, 'basis': basis if value is not None else 'unknown', 'source': source, 'unit': unit}


def _validate_receipt(data, fixture):
    try:
        identity = data.get('identity_sha256')
        if identity != artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'}):
            raise Failure('calibration receipt identity differs from its content')
        if data['format'] != 'swdb.cpu-calibration.v1' or data['evidence_kind'] not in ('fixture', 'native'):
            raise Failure('unsupported calibration format or evidence kind')
        native = data['evidence_kind'] == 'native'
        if not native and not fixture:
            raise Failure('fixture calibration requires --fixture; it is not native measured evidence')
        settings, context = data['settings'], data['context']
        ts = settings['threads']
        if len(set(ts)) != len(ts) or not ts or not set(ts) <= {1, 2, 4, 8, 16}:
            raise Failure('invalid calibration thread configurations')
        if not 3 <= settings['repetitions'] <= 11:
            raise Failure('invalid calibration repetition count')
        if native:
            if not context.get('lane') or '(verified:' not in context['lane']:
                raise Failure('native calibration needs a verified socket-lane receipt')
            if context.get('dirty') is not False or len(context.get('commit', '')) != 40:
                raise Failure('native calibration needs clean committed source context')
            if context.get('host', '').split('.')[0] != data['machine'] or context.get('architecture') != 'x86_64':
                raise Failure('native receipt host/architecture differs from its CPU target')
            if not context.get('binary_sha256') or not context.get('source_sha256') or not context.get('compiler_version'):
                raise Failure('native calibration needs binary/source/compiler identities')
        seen = set()
        for cell in data['cells']:
            t = cell['threads']
            key = (t, cell['shape'], cell['chains'])
            if t not in ts or key in seen:
                raise Failure('unexpected or duplicate calibration cell')
            seen.add(key)
            if len(cell['trials']) != settings['repetitions']:
                raise Failure('calibration repetitions differ from their frozen settings')
            for trial in cell['trials']:
                if not math.isfinite(trial['seconds']) or trial['seconds'] <= 0:
                    raise Failure('trial elapsed time must be positive and finite')
                for name in ('iterations', 'accesses', 'useful_bytes', 'helper_bytes'):
                    value = trial[name]
                    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                        raise Failure('trial work counts must be nonnegative integers')
                workers = trial['worker_iterations']
                if len(workers) != t or len(set(workers)) != 1 or sum(workers) != trial['iterations']:
                    raise Failure('aggregate trial needs balanced, complete worker counts')
                if not math.isfinite(trial['checksum']):
                    raise Failure('trial checksum must be finite')
                if cell['shape'] == 'pointer_chase' and trial['accesses'] <= 0:
                    raise Failure('pointer latency needs positive completed load counts')
        for category, count in data['compute_counts'].items():
            if category not in ('integer', 'floating_point', 'branch', 'atomic') or count['level'] != 'source_normalized_ir':
                raise Failure('unsupported compute operation convention')
            slope, base = count['per_iteration'], count['per_invocation']
            if not isinstance(slope, int) or slope <= 0 or not isinstance(base, int):
                raise Failure('compute count coefficients must be positive integral work counts')
            if len(count['validation_points']) != 3 or any(n * slope + base != v for n, v in count['validation_points']):
                raise Failure('compute count extrapolation lacks three matching validation points')
            if native and count['source_sha256'] != context['source_sha256'].get('CpuWork.h'):
                raise Failure('compute numerator and timed kernel source differ')
        if native:
            for t in ts:
                required = {(t, shape, 1) for shape in SHAPES}
                required |= {(t, 'pointer_chase', c) for c in settings['chains']}
                if not required <= seen or set(data['compute_counts']) != {'integer', 'floating_point', 'branch', 'atomic'}:
                    raise Failure('native calibration matrix/counts are incomplete')
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise Failure(f'invalid calibration receipt: {exc}') from None
    return identity


def import_receipt(args):
    data = access.read_record(args.receipt)
    identity = _validate_receipt(data, args.fixture)
    basis = 'reported' if data['evidence_kind'] == 'fixture' else 'measured'
    descriptions = []
    for threads in data['settings']['threads']:
        cells = [c for c in data['cells'] if c['threads'] == threads]
        series = []
        for cell in cells:
            trials = cell['trials']
            summary = {'shape': cell['shape'], 'chains': cell['chains'],
                'seconds': stats([t['seconds'] for t in trials]),
                'useful_bytes_per_s': stats([t['useful_bytes'] / t['seconds'] for t in trials]),
                'helper_bytes_per_s': stats([t['helper_bytes'] / t['seconds'] for t in trials]),
                'footprint_bytes': cell.get('footprint_bytes'), 'scope': cell.get('scope'), 'trials': trials}
            category = cell['shape'].removeprefix('compute_')
            numerator = data['compute_counts'].get(category)
            if cell['shape'].startswith('compute_') and numerator:
                summary['operations_per_s'] = stats([
                    (numerator['per_iteration'] * t['iterations'] + numerator['per_invocation'] * threads) / t['seconds']
                    for t in trials])
            series.append(summary)
        def shape_series(shape):
            return next((s for s in series if s['shape'] == shape), None)
        stream = shape_series('stream')
        cache = shape_series('cache_stream')
        cold = shape_series('cache_cold_stream')
        dep = next((c for c in cells if c['shape'] == 'pointer_chase' and c['chains'] == 1), None)
        concurrent = sorted([c for c in cells if c['shape'] == 'pointer_chase'], key=lambda c: c['chains'])
        latency = concurrency = None
        curve = []
        plateau = {'state': 'not_established', 'criterion': 'last 3 distinct C medians within 15% relative range; <=25% elapsed spread; same footprint and balanced workers', 'points': [], 'relative_range': None}
        if dep and concurrent:
            latency_trials = [t['seconds'] * threads / t['accesses'] for t in dep['trials']]
            latency = statistics.median(latency_trials)
            for cell in concurrent:
                curve.append({'chains': cell['chains'], 'effective_requests_per_thread': stats([
                    trial['accesses'] / trial['seconds'] / threads * latency for trial in cell['trials']])})
            points = curve[-3:]
            medians = [p['effective_requests_per_thread']['median'] for p in points]
            relative = (max(medians) - min(medians)) / statistics.median(medians)
            spread = [(max(t['seconds'] for t in cell['trials']) - min(t['seconds'] for t in cell['trials'])) /
                      statistics.median(t['seconds'] for t in cell['trials']) for cell in [dep, *concurrent[-3:]]]
            footprints = {cell.get('footprint_bytes', data['settings']['working_set_bytes']) for cell in [dep, *concurrent[-3:]]}
            plateau.update({'points': points, 'relative_range': relative, 'elapsed_relative_spreads': spread,
                'same_footprint': len(footprints) == 1, 'balanced_workers': True})
            if len(points) == 3 and relative <= .15 and max(spread) <= .25 and len(footprints) == 1:
                plateau['state'] = 'established_for_constructed_work'
                concurrency = statistics.median(medians)
        source = f'CPU calibration {identity}; threads={threads}; useful source-element bytes'
        compute = {}
        for category in ('integer', 'floating_point', 'branch', 'atomic'):
            item = shape_series('compute_' + category)
            value = item.get('operations_per_s', {}).get('median') if item else None
            compute[category + '_ops_per_s'] = _fact(value, basis,
                source + '; ' + category + ' constructed work / uninstrumented elapsed; source_normalized_ir', 'operations/s')
        cache_info = data['context'].get('last_level_cache') or {}
        record = {'kind': 'target_description', 'schema_version': '0.4',
            'id': f'{args.id_prefix}.t{threads}', 'status': 'draft',
            'created': writer.today(), 'updated': writer.today(),
            'provenance': [{'id': 'cpu-calibration', 'kind': 'measurement' if basis == 'measured' else 'source_code',
                'description': source, 'uri': None}],
            'format': 'swdb.target-description.v1', 'version': identity,
            'target': data['machine'], 'threads': threads, 'estimator_variant': 'team',
            'calibration_sources': [source], 'dram_address_layout': None,
            'mechanisms': [
                {'model': 'compute_throughput', 'parameters': compute},
                {'model': 'streaming_bandwidth', 'parameters': {
                    'bytes_per_s': _fact(stream['useful_bytes_per_s']['median'] if stream else None, basis, source, 'bytes/s')}},
                {'model': 'requests_in_flight_latency', 'parameters': {
                    'dependent_latency_s': _fact(latency, basis, source + '; C=1 effective elapsed seconds/load', 'seconds/load'),
                    'effective_requests_per_thread': _fact(concurrency, 'inferred', source + '; plateau median of rate/thread * dependent seconds/load', 'requests/thread')}},
                {'model': 'cache_fit', 'parameters': {
                    'capacity_bytes': _fact(cache_info.get('capacity_bytes'), 'reported', source + '; live kernel-reported shared cache capacity', 'bytes'),
                    'bytes_per_s': _fact(cache['useful_bytes_per_s']['median'] if cache else None, basis, source + '; warm cache-resident stream footprint', 'bytes/s'),
                    'cold_bytes_per_s': _fact(cold['useful_bytes_per_s']['median'] if cold else None, basis, source + '; cache state after untimed eviction, bus/page-fault traffic unclaimed', 'bytes/s')}}],
            'extensions': {'cpu_calibration': {'receipt_sha256': identity, 'evidence_kind': data['evidence_kind'],
                'context': data['context'], 'settings': data['settings'], 'series': series,
                'compute_counts': data['compute_counts'], 'concurrency_curve': curve, 'plateau': plateau,
                'dependent_latency_s': stats(latency_trials) if dep else None,
                'effective_requests_per_thread': _fact(concurrency, 'inferred', source + '; rate/thread * dependent seconds/load', 'requests/thread'),
                'cache_scope': {'footprint_bytes': cache.get('footprint_bytes') if cache else None,
                    'level': cache_info.get('level'), 'sharing': cache_info.get('sharing'),
                    'access_shape': 'stream; partitioned read+write float',
                    'residency_basis': 'inferred from footprint and warmup; serving cache level not measured'},
                'notes': ['Concurrency is model-effective under this constructed work, not physical MSHR occupancy.',
                          'Rates are aggregate for this exact thread/compiler/runtime configuration.',
                          'Source-normalized constructed compute work is not physical instruction issue throughput.',
                          'Indirect payload rates include address/helper work in elapsed time; helper byte counts are separate.']}}}
        descriptions.append(record)
    writer.commit(args.records, new=descriptions)
    return {'descriptions': descriptions, 'receipt_sha256': identity}


SHAPES = ('stream', 'single_valued_indirect', 'ranged_indirect', 'data_dependent_merge',
          'cache_stream', 'cache_cold_stream', 'compute_integer', 'compute_floating_point', 'compute_branch', 'compute_atomic')


def _list(text, allowed, name):
    try:
        values = [int(v) for v in text.split(',')]
    except ValueError:
        raise Failure(f'{name} must be a comma-separated integer list') from None
    if not values or len(set(values)) != len(values) or not set(values) <= set(allowed):
        raise Failure(f'{name} must contain distinct values from {sorted(allowed)}')
    return values


def _optional_file(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def _host_state():
    return {'load': list(os.getloadavg()), 'time_ns': time.time_ns(),
        'available_memory': _optional_file('/proc/meminfo'),
        'governor': _optional_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
        'no_turbo': _optional_file('/sys/devices/system/cpu/intel_pstate/no_turbo')}


def _physical_cpus():
    if not hasattr(os, 'sched_getaffinity'):
        return []
    selected, seen = [], set()
    for cpu in sorted(os.sched_getaffinity(0)):
        root = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        core = (_optional_file(root / 'physical_package_id'), _optional_file(root / 'core_id'))
        if None in core:
            raise Failure('cannot establish one worker per physical core')
        if core not in seen:
            selected.append(cpu)
            seen.add(core)
    return selected


def _cache_info(cpus):
    entries = []
    if cpus and cpus[0] >= 0:
        for folder in sorted(Path(f'/sys/devices/system/cpu/cpu{cpus[0]}/cache').glob('index*')):
            size = _optional_file(folder / 'size')
            level = _optional_file(folder / 'level')
            kind = _optional_file(folder / 'type')
            if size and level and kind in ('Data', 'Unified'):
                multiplier = 1024 if size.endswith('K') else 1024**2 if size.endswith('M') else 1
                entries.append({'capacity_bytes': int(size.rstrip('KM')) * multiplier,
                    'level': int(level), 'sharing': _optional_file(folder / 'shared_cpu_list'), 'basis': 'reported'})
    return max(entries, key=lambda e: e['level']) if entries else None


class _CalibrationInterrupted(Exception):
    pass


def _command(command, timeout):
    import signal
    watched = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
    original = {sig: signal.getsignal(sig) for sig in watched}
    process, spawning, pending = None, True, None
    def interrupted(signum, frame):
        nonlocal pending
        pending = signum
        # Defer an interruption during Popen until its group identity is available.
        # Unlike blocking the signal, this does not give the child a blocked mask.
        if not spawning:
            raise _CalibrationInterrupted(signal.Signals(signum).name)
    try:
        for sig in watched:
            signal.signal(sig, interrupted)
        process = subprocess.Popen([str(x) for x in command], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        spawning = False
        if pending is not None:
            raise _CalibrationInterrupted(signal.Signals(pending).name)
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt, _CalibrationInterrupted):
        for sig in watched:
            signal.signal(sig, signal.SIG_IGN)
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.communicate()
        raise Failure('calibration subprocess exceeded its bounded timeout or was interrupted; child group terminated') from None
    finally:
        for sig, handler in original.items():
            signal.signal(sig, handler)
    if process.returncode:
        raise Failure(f'calibration command failed ({process.returncode}): {stderr[-4000:]}')
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _raw_budget(output):
    if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) > 50 * 1024**2:
        raise Failure('calibration reached its 50 MiB raw-output budget')


def _compute_counts(args, output, remaining):
    if not args.llvm_bin:
        return {}
    # Count the exact shared kernel functions separately from the uninstrumented timer.
    # A third point verifies the affine dynamic-count extrapolation, not a guessed ISA rate.
    count_records = output / 'count-records'
    # Only the immutable registration/reference closure is needed for count receipts.
    # Copying unrelated campaigns would consume the bounded raw-output budget.
    store = Store(args.records)
    selected, pending = {}, ['gapbs-bfs-do', 'kron-g16-k16']
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)
    while pending:
        identifier = pending.pop()
        if identifier in selected:
            continue
        record = store.get(identifier)
        if record is None:
            raise Failure(f'compute counting requires registration {identifier!r}')
        selected[identifier] = record
        pending.extend(x for x in strings(record) if store.get(x) is not None and x not in selected)
    count_records.mkdir()
    for identifier in selected:
        rel = store.path_of(identifier)
        destination = count_records / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(access.read_record_bytes(args.records / rel))
    source = Path(__file__).with_name('native') / 'CpuCount.cpp'
    result = {}
    for category in ('integer', 'floating_point', 'branch', 'atomic'):
        points, receipts = [], []
        for n in (32, 64, 96):
            command = [sys.executable, '-m', 'swdb', 'characterize', '--records', count_records,
                '--source', source, '--implementation', 'gapbs-bfs-do', '--input', 'kron-g16-k16',
                '--function', 'compute_' + category, '--threads', '1', '--fixture',
                '--id', f'calibration.count.{category}.{n}', '--roi', 'constructed-compute-function',
                '--llvm-bin', args.llvm_bin, '--output', output / f'count-{category}-{n}',
                '--run-arg', category, '--run-arg', str(n), '--format', 'json',
                '--timeout-s', str(min(180, remaining())), '--build-flag=-std=c++17', '--build-flag=-pthread']
            command += ['--toolchain-flag=' + f for f in args.toolchain_flag]
            command += ['--build-flag=' + f for f in args.build_flag]
            data = json.loads(_command(command, remaining()).stdout)
            count = sum(r['operation_counts'][category]['value'] for r in data['regions'])
            points.append([n, count]); receipts.append(artifacts.digest(data))
            _raw_budget(output)
        slope = (points[1][1] - points[0][1]) / 32
        intercept = points[0][1] - 32 * slope
        if slope <= 0 or slope != int(slope) or points[2][1] != 96 * slope + intercept:
            raise Failure(f'compute {category} source-normalized count is not a verified positive affine function')
        result[category] = {'level': 'source_normalized_ir', 'per_iteration': int(slope),
            'per_invocation': int(intercept), 'validation_points': points,
            'characterization_sha256': receipts,
            'source_sha256': artifacts.file_hash(source.with_name('CpuWork.h')),
            'basis': 'inferred', 'timing': 'separate uninstrumented binary',
            'scope': 'effective constructed work, not physical issue throughput'}
    return result


def calibrate(args):
    threads = _list(args.threads, (1, 2, 4, 8, 16), 'threads')
    chains = _list(args.chains, (1, 2, 4, 8, 16, 32), 'chains')
    if not 3 <= args.repetitions <= 11:
        raise Failure('repetitions must be in [3,11]')
    if not 1024 <= args.working_set_bytes <= 512 * 1024**2:
        raise Failure('working set must be in [1024,512 MiB]')
    if not 1024 <= args.cache_bytes <= 16 * 1024**2:
        raise Failure('cache footprint must be in [1024,16 MiB]')
    if not 0 < args.min_trial_s <= 1 or not 0 < args.max_wall_s <= 1800:
        raise Failure('trial duration must be in (0,1] seconds and wall budget in (0,1800] seconds')
    if not args.fixture and (args.working_set_bytes < 64 * 1024**2 or args.min_trial_s < .1 or not args.llvm_bin):
        raise Failure('native calibration requires >=64 MiB, >=0.1 s trials, and LLVM 22 source-normalized compute counts')
    output = args.output.resolve()
    if output.exists():
        raise Failure('output already exists; choose a new raw folder')
    ancestor = next(p for p in (output, *output.parents) if p.exists())
    free = shutil.disk_usage(ancestor).free
    if not args.fixture and free < 20 * 1024**3:
        raise Failure('raw output mount needs at least 20 GiB free')
    store = Store(args.records)
    lane = None
    if not args.fixture:
        machine = store.get(args.machine, 'machine')
        if not machine or socket.gethostname().split('.')[0] != machine['hostname']:
            raise Failure('native calibration must run on its registered machine')
        from swdb.profile import _verified_lane
        lane = _verified_lane(machine, args.lane)
    cpus = _physical_cpus() if platform.system() == 'Linux' else []
    if not args.fixture and len(cpus) < max(threads):
        raise Failure('insufficient physical cores inside this lane')
    cpus = cpus or [-1] * max(threads)
    started = time.monotonic()
    def remaining():
        left = args.max_wall_s - (time.monotonic() - started)
        if left <= 0:
            raise Failure('calibration reached its wall-time budget')
        return left
    artifacts.external_directory(output)
    native = Path(__file__).with_name('native')
    compiler = str(args.llvm_bin / 'clang++') if args.llvm_bin else args.compiler
    compiler = shutil.which(compiler)
    if not compiler:
        raise Failure('native C++ compiler is unavailable')
    flags = ['-O3', '-std=c++17', '-pthread', *args.build_flag, *args.toolchain_flag]
    if any(f.startswith(('-o', '-flto', '-fpass-plugin', '-emit-llvm', '-fsanitize', '-fprofile', '-finstrument', '-pg', '-Xclang', '-g0')) for f in args.build_flag):
        raise Failure('calibration build flags may not replace output or instrument timing')
    version = _command([compiler, '--version'], remaining()).stdout
    binary = output / 'cpu-calibration'
    _command([compiler, native / 'CpuCalibration.cpp', '-o', binary, *flags], remaining())
    context = {'compiler': compiler, 'compiler_version': version, 'flags': flags,
        'host': socket.gethostname(), 'architecture': platform.machine(), 'runtime': 'std::thread; physical-core pinning on Linux',
        'lane': lane, 'cpus': cpus[:max(threads)], 'commit': _command(['git', 'rev-parse', 'HEAD'], remaining()).stdout.strip(),
        'dirty': bool(_command(['git', 'status', '--porcelain'], remaining()).stdout),
        'source_sha256': {p.name: artifacts.file_hash(p) for p in native.iterdir() if p.is_file()},
        'binary_sha256': artifacts.file_hash(binary), 'start_state': _host_state(), 'free_disk_bytes': free}
    if not args.fixture and context['dirty']:
        raise Failure('native calibration source checkout must be clean')
    context['last_level_cache'] = _cache_info(cpus)
    capacity = (context['last_level_cache'] or {}).get('capacity_bytes')
    if not args.fixture and (not capacity or args.working_set_bytes < 8 * capacity or args.cache_bytes >= capacity):
        raise Failure('native large working set must exceed live LLC by 8x and cache footprint must fit below it')
    eviction = min(128 * 1024**2, 3 * (capacity or args.cache_bytes))
    counts = _compute_counts(args, output, remaining)
    cells = []
    for t in threads:
        matrix = [(s, 1) for s in SHAPES] + [('pointer_chase', c) for c in chains]
        for shape, c in matrix:
            footprint = args.cache_bytes if shape in ('cache_stream', 'cache_cold_stream') else args.working_set_bytes
            command = [binary, shape, t, footprint, c, args.repetitions, args.min_trial_s, args.seed,
                       ','.join(map(str, cpus[:t])), eviction]
            result = json.loads(_command(command, remaining()).stdout)
            cell = {'threads': t, 'shape': shape, 'chains': c, 'footprint_bytes': footprint,
                'scope': 'partitioned, first-touched on bound worker; useful payload bytes; helper bytes separate; compiler-only pass fence for repeated stores',
                'sampling_scope': 'single cold pass after untimed eviction; minimum-duration exemption' if shape == 'cache_cold_stream' else 'full-partition passes, frozen after pilot',
                'eviction_bytes': eviction if shape == 'cache_cold_stream' else 0, **result}
            cells.append(cell)
            (output / 'partial.json').write_text(json.dumps({'context': context, 'cells': cells}, indent=2, allow_nan=False))
            _raw_budget(output)
    context['end_state'] = _host_state()
    data = {'format': 'swdb.cpu-calibration.v1', 'evidence_kind': 'fixture' if args.fixture else 'native',
        'machine': args.machine, 'context': context, 'compute_counts': counts,
        'settings': {'threads': threads, 'chains': chains, 'repetitions': args.repetitions,
            'working_set_bytes': args.working_set_bytes, 'cache_bytes': args.cache_bytes,
            'min_trial_s': args.min_trial_s, 'max_wall_s': args.max_wall_s, 'seed': args.seed,
            'memory_cap_bytes': 1536 * 1024**2, 'raw_cap_bytes': 50 * 1024**2}, 'cells': cells}
    data['identity_sha256'] = artifacts.digest(data)
    _validate_receipt(data, args.fixture)
    _raw_budget(output)
    (output / 'receipt.json').write_text(json.dumps(data, indent=2, allow_nan=False))
    return {'receipt': str(output / 'receipt.json'), 'receipt_sha256': data['identity_sha256'],
            'cells': len(cells), 'evidence_kind': data['evidence_kind']}

"""Independent native service receipts. Created: 2026-10-06 ET.

Paired elapsed subtraction retains all inputs; unresolved service work stays unknown.
"""
import copy
import math
import json
import platform
import shutil
import socket
import time
from pathlib import Path

from yaml import YAMLError

from swdb import access, artifacts, paths, writer
from swdb.cli import Failure
from swdb.cpu_calibration import stats
from swdb.problems import Problem
from swdb.store import Record, Store, canonical_path


def identity(data):
    return artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})


def register_cli(commands):
    run = commands.add_parser('cpu-service-calibrate', help='bounded independent native service/driver timing, never application timing')
    run.add_argument('--records', type=Path, default=paths.RECORDS)
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--fixture', action='store_true')
    run.add_argument('--count-only', action='store_true', help='emit ABI/count proof only; no elapsed calibration')
    run.add_argument('--compiler', default='c++')
    run.add_argument('--machine', default='mbit10')
    run.add_argument('--lane')
    run.add_argument('--llvm-bin', type=Path, help='separate LLVM22 source-normalized-v2 service/driver count proof')
    run.add_argument('--toolchain-flag', action='append', default=[])
    run.add_argument('--repetitions', type=int, default=7)
    run.add_argument('--min-trial-s', type=float, default=.05)
    run.add_argument('--max-wall-s', type=float, default=900)
    run.add_argument('--format', choices=['yaml', 'json'], default='json')
    run.set_defaults(cpu_service_calibration_handler=calibrate)
    sub = commands.add_parser('import-cpu-service-calibration', help='retain independently timed native service costs and their paired driver inputs')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--receipt', type=Path, required=True)
    sub.add_argument('--id', required=True)
    sub.add_argument('--fixture', action='store_true')
    sub.add_argument('--format', choices=['yaml', 'json'], default='json')
    sub.set_defaults(cpu_service_calibration_handler=import_receipt)


def derive_service(service, record_id, evidence_kind, repetitions):
    trials = service['trials']
    if len(trials) != repetitions or not trials:
        raise Failure('service calibration repetitions differ')
    rates = []
    for trial in trials:
        n = trial['events']
        if type(n) is not int or n <= 0:
            raise Failure('service event denominator must be a positive integer')
        for key in ('gross_seconds', 'driver_seconds'):
            value = trial[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise Failure('paired service elapsed must be finite and nonnegative')
        rates.append((trial['gross_seconds'] - trial['driver_seconds']) / n)
    result = copy.deepcopy(service)
    result['seconds_per_event'] = stats(rates)
    resolved = all(value > 0 for value in rates)
    result['missing'] = [] if resolved else ['paired_driver_subtraction_resolution']
    result['parameter'] = {'value': result['seconds_per_event']['median'] if resolved else None,
        'basis': ('reported' if evidence_kind == 'fixture' else 'measured') if resolved else 'unknown',
        'source': f'Service calibration {record_id}; {service["id"]}; paired elapsed/work trials.',
        'unit': service['unit']}
    return result


def import_receipt(args):
    try:
        raw = access.read_record(args.receipt)
        if not isinstance(raw, dict) or raw.get('format') != 'swdb.cpu-service-calibration.v1' or raw.get('identity_sha256') != identity(raw):
            raise Failure('service calibration receipt identity/format differs')
        if raw['evidence_kind'] == 'native':
            from swdb.cpu_service_native import validate
            validate(raw)
        elif raw['evidence_kind'] != 'fixture' or not args.fixture:
            raise Failure('service fixture requires --fixture; it is not native measurement')
        repetitions = raw['settings']['repetitions']
        if type(repetitions) is not int or not 3 <= repetitions <= 11:
            raise Failure('service repetitions must be between 3 and 11')
        data = {'kind': 'cpu_service_calibration', 'schema_version': '0.4', 'id': args.id,
            'status': 'draft', 'created': writer.today(), 'updated': writer.today(),
            'provenance': [{'id': 'cpu-service', 'kind': 'measurement' if raw['evidence_kind'] == 'native' else 'source_code',
                'description': 'Independent service/driver elapsed and counted work; not application timing or CPU accuracy evidence.', 'uri': None}],
            'format': 'swdb.cpu-service-calibration-record.v1', 'backend': 'native',
            'evidence_kind': raw['evidence_kind'], 'receipt_sha256': raw['identity_sha256'],
            'target': raw['machine'], 'threads': raw['threads'],
            'context': copy.deepcopy(raw['context']), 'settings': copy.deepcopy(raw['settings']),
            'services': [derive_service(s, args.id, raw['evidence_kind'], repetitions) for s in raw['services']]}
        data['identity_sha256'] = identity(data)
        from swdb.archevolve import require_team_safe
        from swdb import workflow
        if workflow.CREATION_TAGS.get('mode') == 'extensa':
            raise Failure('CPU service calibration import requires team context')
        store = Store(args.records)
        store.add(Record(canonical_path(data['kind'], data['id']), data))
        require_team_safe(store, data, command='import-cpu-service-calibration')
        writer.commit(args.records, new=[data])
        return data
    except (OSError, ValueError, KeyError, TypeError, YAMLError) as exc:
        raise Failure(f'cannot import service calibration receipt: {exc}') from None


def validate_record(record, ctx):
    data = record.data
    if data.get('identity_sha256') != identity(data):
        yield Problem(record.rel, 'identity_sha256', 'service calibration content identity differs')
    try:
        for i, service in enumerate(data['services']):
            expected = derive_service(service, data['id'], data['evidence_kind'], data['settings']['repetitions'])
            if expected['seconds_per_event'] != service['seconds_per_event'] or expected['parameter'] != service['parameter'] or expected['missing'] != service.get('missing'):
                yield Problem(record.rel, f'services[{i}]', 'service cost/spread differs from paired elapsed/work inputs')
        if data['evidence_kind'] == 'native':
            from swdb.cpu_service_native import validate
            validate({'threads':data['threads'], 'machine':data['target'], 'context':data['context'], 'settings':data['settings'], 'services':data['services']})
    except (Failure, ValueError, KeyError, TypeError) as exc:
        yield Problem(record.rel, 'services', str(exc))


def calibrate(args):
    from swdb.cpu_calibration import _command
    if not 3 <= args.repetitions <= 11 or not math.isfinite(args.max_wall_s) or not 0 < args.max_wall_s <= 900 or not math.isfinite(args.min_trial_s) or not 0 < args.min_trial_s <= .2:
        raise Failure('service timing exceeds repetitions 3–11, wall 900s or per-trial 0.2s caps')
    output = args.output.resolve()
    if output.exists():
        raise Failure('service output must be a new external folder')
    if output.is_relative_to(paths.HOME.resolve()):
        raise Failure('service raw output must stay outside the project')
    if any(not flag.startswith(('--gcc-install-dir=', '--gcc-toolchain=', '--sysroot=', '-resource-dir=', '-stdlib=')) for flag in args.toolchain_flag):
        raise Failure('service toolchain flags may select headers/libraries, not alter or instrument work')
    from swdb.cpu_service_native import prepare
    if args.count_only and not args.llvm_bin:
        raise Failure('count-only service evidence requires LLVM22')
    native_context = prepare(args, output)
    output.mkdir(parents=True)
    deadline = time.monotonic() + args.max_wall_s
    def command(argv):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Failure('service timing reached its wall budget')
        return _command(argv, timeout=remaining)
    git = ['git', '-C', paths.HOME.parent]
    if native_context:
        native_context['commit'] = command([*git, 'rev-parse', 'HEAD']).stdout.strip()
        native_context['dirty'] = bool(command([*git, 'status', '--porcelain']).stdout)
        if native_context['dirty']:
            raise Failure('native service source checkout must be clean before counting or timing')
    source = Path(__file__).parent / 'native'
    for name in ('CpuServiceTimer.cpp', 'CpuServiceWork.h', 'CpuServiceCount.cpp'):
        shutil.copy2(source / name, output / name)
    binary = output / 'service-timer'
    flags = ['-O3', '-std=c++17', *args.toolchain_flag]
    compiler_path = args.llvm_bin / 'clang++' if args.llvm_bin else args.compiler
    compiler = command([compiler_path, '--version']).stdout.strip()
    build = command([compiler_path, *flags, output / 'CpuServiceTimer.cpp', '-o', binary])
    (output / 'build.stdout').write_text(build.stdout)
    (output / 'build.stderr').write_text(build.stderr)
    proof = None
    if args.llvm_bin:
        from swdb.cpu_service_counts import clock_proof
        proof = clock_proof(args.records, output, args.llvm_bin, args.toolchain_flag, command)
    if args.count_only:
        from swdb.cpu_service_native import loaded_libraries
        from swdb.cpu_calibration import _host_state
        context = {'compiler_version': compiler, 'flags': flags,
            'host': socket.gethostname(), 'architecture': platform.machine(),
            'source_sha256': {name: artifacts.file_hash(output / name) for name in ('CpuServiceTimer.cpp', 'CpuServiceWork.h', 'CpuServiceCount.cpp')},
            'binary_sha256': artifacts.file_hash(binary), 'binary_executed': False}
        if native_context:
            if command([*git, 'rev-parse', 'HEAD']).stdout.strip() != native_context['commit'] or command([*git, 'status', '--porcelain']).stdout:
                raise Failure('native service source changed during count proof')
            context.update(native_context)
            context.update(loaded_libraries=loaded_libraries(binary, command), end_state=_host_state())
        record = {'format': 'swdb.cpu-service-count-only.v1', 'evidence_kind': 'fixture' if args.fixture else 'native_count_only',
            'timings_collected': False, 'machine': args.machine, 'threads': 1, 'context': context, 'count_proof': proof}
        record['identity_sha256'] = identity(record)
        (output / 'count-proof.json').write_text(json.dumps(record, indent=2))
        return {'count_proof': str(output / 'count-proof.json'), 'identity_sha256': record['identity_sha256'], 'timings_collected': False}
    def timer(n, order):
        argv = [binary, n, order]
        if native_context:
            argv = ['taskset', '-c', native_context['cpus'][0], *argv]
        return json.loads(command(argv).stdout)
    n = 128
    while True:
        pilot = timer(n, 'service_first')
        (output / 'pilot.json').write_text(json.dumps(pilot))
        if min(pilot['gross_seconds'], pilot['driver_seconds']) >= args.min_trial_s:
            break
        if n >= 134217728:
            raise Failure('service pilot could not resolve both paired durations within its work cap')
        n = min(2 * n, 134217728)
    trials = []
    for i in range(args.repetitions):
        order = 'service_first' if i % 2 == 0 else 'driver_first'
        trial = timer(n, order)
        trials.append(trial)
        (output / 'partial-trials.json').write_text(json.dumps(trials))
    raw = {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'fixture' if args.fixture else 'native',
        'machine': args.machine, 'threads': 1,
        'context': {'compiler_version': compiler, 'flags': flags,
            'host': socket.gethostname(), 'architecture': platform.machine(),
            'source_sha256': {name: artifacts.file_hash(output / name) for name in ('CpuServiceTimer.cpp', 'CpuServiceWork.h', 'CpuServiceCount.cpp')},
            'binary_sha256': artifacts.file_hash(binary), 'instrumented_timer': False},
        'settings': {'repetitions': args.repetitions, 'min_trial_s': args.min_trial_s,
            'max_wall_s': args.max_wall_s, 'resident_payload_bytes': 0,
            'raw_output_cap_bytes': 25 * 1024**2, 'iteration_cap': 134217728},
        'services': [{'id': 'clock.now', 'unit': 'seconds/call',
            'event_definition': 'One system_clock::now per service iteration; matched conditional-loop driver, checksum consumption and return. Effective constructed service difference, not physical instruction latency.',
            'scope': {'worker_scope': 'serial', 'cache_state': 'warm',
                'runtime': 'current C++ standard library; portable contract only'},
            'denominator': {'level': 'source_normalized_work', 'basis': 'measured' if proof else 'reported',
                'proof': proof or 'Portable clock-loop construction; separate native counting proof is required.'},
            'trials': trials}]}
    if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) > 25 * 1024**2:
        raise Failure('service raw output reached its 25MiB cap')
    if native_context:
        from swdb.cpu_service_native import loaded_libraries, validate
        from swdb.cpu_calibration import _host_state
        raw['context'].update(native_context)
        if command([*git, 'rev-parse', 'HEAD']).stdout.strip() != native_context['commit'] or command([*git, 'status', '--porcelain']).stdout:
            raise Failure('native service source changed while collecting evidence')
        raw['context'].update(loaded_libraries=loaded_libraries(binary,command), end_state=_host_state())
        raw['services'][0]['scope'].update(cache_state='steady_repeated_calls', runtime='hash-bound loaded C/C++ libraries; exact counted clock ABI')
        validate(raw)
    raw['identity_sha256'] = identity(raw)
    (output / 'receipt.json').write_text(json.dumps(raw, indent=2))
    return {'receipt': str(output / 'receipt.json'), 'receipt_sha256': raw['identity_sha256'],
            'evidence_kind': raw['evidence_kind'], 'services': 1}

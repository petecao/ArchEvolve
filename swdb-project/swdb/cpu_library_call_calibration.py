"""Library-call service family: paired per-call receipts. Created: 2026-10-12 ET.

Spec C8/C9 of .scratch/cpu-description-t75-pricing-2026-10-12. Modeled on the clock
service: one shared source, a paired driver per service, a separate LLVM count proof with
one selected ABI per service. Calls without a resolved receipt stay unknown downstream.
"""
import copy
import json
import math
import platform
import re
import shutil
import socket
import sys
import time
from pathlib import Path

from swdb import access, artifacts, paths
from swdb.cli import Failure
from swdb.extensa_boundary import closure
from swdb.store import Store

GROUP = 'library_call_v1'
SOURCES = ('CpuLibraryCallWork.h', 'CpuLibraryCallTimer.cpp', 'CpuLibraryCallCount.cpp')
PIPELINE = {'version': 'source-normalized-v2', 'passes': ['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']}
FLAGS = ['-O3', '-std=c++17']
TOOLCHAIN_PREFIXES = ('--gcc-install-dir=', '--gcc-toolchain=', '--sysroot=', '-resource-dir=', '-stdlib=')
EVENT_CAP, BATCH_EVENTS, TIMED_CAP, COUNT_CAP = 134217728, 1024, 25 * 1024**2, 64 * 1024**2
COUNT_POINTS = (3, 5)
FUNCTION = 'service_library_call'
TEXT_BYTES = 16
SINK = 'regular_file'
COMMON = {'worker_scope': 'serial', 'transfer_basis': 'inferred', 'cache_state': 'steady_repeated_calls',
          'stdout_sink': SINK, 'stream': 'std::cout, sync_with_stdio(true), stdout reopened onto a regular file '
          '(fully buffered), flushed and truncated between untimed batches'}
# (id, exact libstdc++ ABI that the t75 characterizations name, event definition, extra scope)
SERVICES = [
    ('library.strlen', 'strlen',
     'One strlen of a constructed 16-byte string; driver uses the known length. Application string lengths are not measured.',
     {'length_bytes': TEXT_BYTES, 'length_transfer': 'inferred; application lengths unknown'}),
    ('library.ostream_put', '_ZNSo3putEc',
     'One ostream::put of one byte into the buffered stdout file; driver skips it. Buffer drain to the file happens outside the timed window.',
     {}),
    ('library.ostream_flush', '_ZNSo5flushEv',
     'One ostream::flush after a one-byte put (non-empty buffer, one write(2) to a regular file); driver does the put only. Cost depends on where stdout goes; measured to a file like the timed run.',
     {'pending_bytes': 1}),
    ('library.ostream_insert', '_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l',
     'One __ostream_insert of a constructed 16-byte string into the buffered stdout file; driver skips it.',
     {'length_bytes': TEXT_BYTES, 'length_transfer': 'inferred; application lengths unknown'}),
    ('library.ostream_insert_unsigned_long', '_ZNSo9_M_insertImEERSoT_',
     'One operator<<(unsigned long) (_M_insert<unsigned long>) of a 7-digit value into the buffered stdout file; driver skips it.',
     {'digits': 7}),
    ('library.ctype_widen_init', '_ZNKSt5ctypeIcE13_M_widen_initEv',
     'One uncached ctype<char>::_M_widen_init (cache flag cleared each iteration) plus its virtual do_widen; the driver makes one virtual do_widen(range) without it, so the dispatch is not in this rate.',
     {'facet_state': 'uncached each iteration; the application calls it once (first call), so warm-cache and first-call state differ (inferred)'}),
    ('library.indirect_call', 'indirect-call',
     'Call overhead only: one indirect call to a counted, trivially small callee; the driver inlines the same body, so the callee work stays where it is defined.',
     {'callee': 'counted trivially small body; the scalar selector prices every executed indirect site'}),
]
IDS = [s[0] for s in SERVICES]
NATIVE_ABIS = [s[1] for s in SERVICES]


def _command_runner(args):
    from swdb.cpu_calibration import _command
    deadline = time.monotonic() + args.max_wall_s

    def command(argv):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Failure('library-call service wall budget reached')
        return _command(argv, timeout=remaining)
    return command


def budget(output, *, addition=0):
    data, build = addition, 0
    for p in output.rglob('*'):
        if not p.is_file():
            continue
        if p.parent == output and (p.name in ('partial-trials.json', 'receipt.json', 'sink.out') or p.name.startswith('pilot-')):
            data += p.stat().st_size
        else:
            build += p.stat().st_size
    if build > COUNT_CAP or data > TIMED_CAP:
        raise Failure('library-call count-build/timed-data budget exceeded; partial artifacts retained')


def calibrate(args):
    from swdb.cpu_service_controls import snapshot
    from swdb.cpu_service_native import prepare, loaded_libraries
    from swdb.cpu_calibration import _host_state
    from swdb.cpu_service_calibration import identity
    if not args.llvm_bin:
        raise Failure('library-call services require LLVM22 and a separate count proof')
    if args.size or getattr(args, 'cell', None) or args.count_build_cap_mib != 64:
        raise Failure('--size, --cell and --count-build-cap-mib apply to the allocator service group')
    if (type(args.repetitions) is not int or not 3 <= args.repetitions <= 11 or not math.isfinite(args.min_trial_s)
            or not 0 < args.min_trial_s <= .2 or not math.isfinite(args.max_wall_s) or not 0 < args.max_wall_s <= 900):
        raise Failure('library-call caps are 3–11 repetitions, 0.2s trials and 900s wall')
    if any(not flag.startswith(TOOLCHAIN_PREFIXES) for flag in args.toolchain_flag):
        raise Failure('library-call toolchain flags may select headers/libraries, not alter or instrument work')
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):
        raise Failure('library-call raw output must be a new folder outside the project')
    native = prepare(args, output)
    command = _command_runner(args)
    git = ['git', '-C', paths.HOME.parent]
    if native:
        native.update(commit=command([*git, 'rev-parse', 'HEAD']).stdout.strip(),
                      dirty=bool(command([*git, 'status', '--porcelain']).stdout))
        if native['dirty']:
            raise Failure('native library-call source checkout must be clean before counting or timing')
    output.mkdir(parents=True)
    for name in SOURCES:
        shutil.copy2(Path(__file__).parent / 'native' / name, output / name)
    compiler = args.llvm_bin / 'clang++'
    flags = [*FLAGS, *args.toolchain_flag]
    binary = output / 'library-call-timer'
    built = command([compiler, *flags, output / SOURCES[1], '-o', binary])
    (output / 'build.stdout').write_text(built.stdout)
    (output / 'build.stderr').write_text(built.stderr)
    counted = proof(args.records, output, args.llvm_bin, args.toolchain_flag, command)
    context = {'compiler_version': command([compiler, '--version']).stdout.strip(),
        'compiler_sha256': artifacts.file_hash(compiler.resolve()), 'flags': flags,
        'host': socket.gethostname(), 'architecture': platform.machine(), 'instrumented_timer': False,
        'source_sha256': {n: artifacts.file_hash(output / n) for n in SOURCES},
        'binary_sha256': artifacts.file_hash(binary), **snapshot()}

    def unchanged():
        if command([*git, 'rev-parse', 'HEAD']).stdout.strip() != native['commit'] or command([*git, 'status', '--porcelain']).stdout:
            raise Failure('native library-call source changed during collection')
    if native:
        unchanged()
        context.update(native, loaded_libraries=loaded_libraries(binary, command))
    if args.count_only:
        raw = {'format': 'swdb.cpu-library-call-count-only.v1', 'evidence_kind': 'fixture' if args.fixture else 'native_count_only',
            'timings_collected': False, 'machine': args.machine, 'threads': 1, 'context': context, 'count_proof': counted}
        if native:
            context['end_state'] = _host_state()
        raw['identity_sha256'] = identity(raw)
        (output / 'count-proof.json').write_text(json.dumps(raw, indent=2))
        return {'count_proof': str(output / 'count-proof.json'), 'identity_sha256': raw['identity_sha256'], 'timings_collected': False}
    sink = output / 'sink.out'
    services = []
    for index, (service_id, _abi, definition, extra) in enumerate(SERVICES):
        def timer(batches, order):
            argv = [binary, index, BATCH_EVENTS, batches, order, sink]
            if native:
                argv = ['taskset', '-c', native['cpus'][0], *argv]
            trial = json.loads(command(argv).stdout)
            if trial.get('batch_events') != BATCH_EVENTS or trial.get('events') != BATCH_EVENTS * batches:
                raise Failure('library-call timer event denominator differs')
            return trial
        batches = 1
        while True:
            pilot = timer(batches, 'service_first')
            (output / f'pilot-library-{index}.json').write_text(json.dumps(pilot))
            if min(pilot['gross_seconds'], pilot['driver_seconds']) >= args.min_trial_s:
                break
            if batches * BATCH_EVENTS >= EVENT_CAP:
                raise Failure('library-call pilot could not resolve both paired durations within its event cap')
            batches = min(2 * batches, EVENT_CAP // BATCH_EVENTS)
        trials = [timer(batches, 'service_first' if i % 2 == 0 else 'driver_first') for i in range(args.repetitions)]
        abi = counted['cells'][index]['event_abi']
        services.append({'id': service_id, 'unit': 'seconds/call', 'event_definition': definition,
            'scope': {'event_abi': abi, **copy.deepcopy(COMMON), **copy.deepcopy(extra)},
            'denominator': {'level': 'selected_source_normalized_event', 'basis': 'measured', 'proof': counted},
            'trials': trials})
        (output / 'partial-trials.json').write_text(json.dumps(services, indent=2))
        budget(output)
    raw = {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'fixture' if args.fixture else 'native',
        'machine': args.machine, 'threads': 1, 'context': context,
        'settings': {'group': GROUP, 'repetitions': args.repetitions, 'min_trial_s': args.min_trial_s,
            'max_wall_s': args.max_wall_s, 'event_cap': EVENT_CAP, 'batch_events': BATCH_EVENTS,
            'timed_data_cap_bytes': TIMED_CAP, 'count_build_cap_bytes': COUNT_CAP, 'resident_payload_bytes': 0},
        'services': services}
    if native:
        unchanged()
        context['end_state'] = _host_state()
        validate(raw)
    raw['identity_sha256'] = identity(raw)
    payload = json.dumps(raw, indent=2)
    budget(output, addition=len(payload.encode()))
    (output / 'receipt.json').write_text(payload)
    return {'receipt': str(output / 'receipt.json'), 'receipt_sha256': raw['identity_sha256'],
            'evidence_kind': raw['evidence_kind'], 'services': len(services)}


def _uncovered(call):
    return not call.get('body_counted', False) and call.get('cost_accounting', 'opaque_callee') == 'opaque_callee'


def _rows(char):
    functions = {r['id']: r.get('source_location', {}).get('function') for r in char['regions']}
    return [c for c in char['unmodeled_calls'] if functions.get(c.get('region')) == FUNCTION and _uncovered(c)]


def select(service, driver, events):
    """Service and driver count runs at one `events` -> (cells, other counts by name per run).

    Op k ran (k + 1) * events iterations. Its selected site is the one uncovered call in the
    service function with that count in the service run and 0 in the driver run;
    indirect-call only for op 6. Every other uncovered call must match by name across runs.
    """
    service_rows, driver_rows = _rows(service), _rows(driver)
    driver_sites = {}
    for c in driver_rows:
        driver_sites[c['site']] = driver_sites.get(c['site'], 0) + c['execution_count']['value']
    cells, chosen = [], set()
    for k in range(len(SERVICES)):
        want = (k + 1) * events
        hits = [c for c in service_rows if c['execution_count']['value'] == want and driver_sites.get(c['site'], 0) == 0
                and (c['name'] == 'indirect-call') == (k == len(SERVICES) - 1) and c['site'] not in chosen]
        if len(hits) != 1:
            raise Failure(f'library-call selected event {k} needs exactly one counted site; found {len(hits)}')
        chosen.add(hits[0]['site'])
        cells.append({'index': k, 'event_abi': hits[0]['name'], 'executions': want, 'source_sites': [hits[0]['site']]})

    def others(rows):
        totals = {}
        for c in rows:
            if c['site'] not in chosen:
                totals[c['name']] = totals.get(c['name'], 0) + c['execution_count']['value']
        return totals
    service_others, driver_others = others(service_rows), others(driver_rows)
    if service_others != driver_others:
        raise Failure('library-call service and driver differ outside the selected events: '
                      + str({'service': service_others, 'driver': driver_others}))
    return cells, service_others, driver_others


def proof(records, output, llvm_bin, toolchain_flags, command):
    store = Store(records)
    seeds = ['gapbs-bfs-do', 'kron-g16-k16']
    if any(store.get(key) is None for key in seeds):
        raise Failure('library-call count proof requires the registered counting fixture carrier and input')
    copied = output / 'count-records'
    copied.mkdir()
    for key in closure(store, seeds):
        relative = store.path_of(key)
        destination = copied / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(records) / relative))
    points, abis = [], []
    for n in COUNT_POINTS:
        runs = {}
        for invoke in (True, False):
            key = f'{int(invoke)}.{n}'
            argv = [sys.executable, '-m', 'swdb', 'characterize', '--records', copied,
                '--source', output / SOURCES[2], '--implementation', seeds[0], '--input', seeds[1],
                '--function', FUNCTION, '--threads', '1', '--fixture', '--counting-pipeline', 'source-normalized-v2',
                '--id', 'calibration.library-call.' + key, '--roi', 'constructed-library-call-service',
                '--llvm-bin', llvm_bin, '--output', output / ('count-' + key), '--run-arg', str(n),
                '--run-arg', str(int(invoke)), '--format', 'json', '--timeout-s', '90', '--build-flag=-std=c++17']
            argv.extend('--toolchain-flag=' + flag for flag in toolchain_flags)
            char = json.loads(command(argv).stdout)
            if {'version': char['counting']['pipeline_version'], 'passes': char['counting']['passes']} != PIPELINE:
                raise Failure('library-call count recipe differs')
            runs[invoke] = char
            budget(output)
        cells, service_others, driver_others = select(runs[True], runs[False], n)
        abis.append([c['event_abi'] for c in cells])
        points.append({'events': n, 'invoke': True, 'cells': cells, 'other_uncovered_calls': service_others,
            'characterization_sha256': artifacts.digest(runs[True])})
        points.append({'events': n, 'invoke': False, 'other_uncovered_calls': driver_others,
            'cells': [{**c, 'executions': 0} for c in cells], 'characterization_sha256': artifacts.digest(runs[False])})
    if any(row != abis[0] for row in abis) or len(set(abis[0])) != len(SERVICES):
        raise Failure('library-call services need one distinct ABI each, stable across count points')
    root = Path(__file__).parent
    return {'format': 'swdb.cpu-library-call-count-proof.v1', 'pipeline': PIPELINE,
        'coefficients': 'op k runs (k + 1) * events iterations in the count driver; one selected event per iteration',
        'cells': [{'index': i, 'event_abi': abi} for i, abi in enumerate(abis[0])], 'points': points,
        'source_sha256': artifacts.file_hash(output / SOURCES[0]),
        'count_driver_sha256': artifacts.file_hash(output / SOURCES[2]),
        'plugin_source_sha256': artifacts.file_hash(root / 'llvm/Characterize.cpp'),
        'runtime_source_sha256': artifacts.file_hash(root / 'llvm/CountingRuntime.cpp')}


def validate(raw):
    """Native admission of a library-call receipt (Linux x86_64, libstdc++ ABIs)."""
    from swdb.cpu_service_controls import valid
    c, s = raw['context'], raw['settings']

    def require(condition, reason):
        if not condition:
            raise Failure('native library call: ' + reason)

    def hashed(value):
        return bool(re.fullmatch('[0-9a-f]{64}', str(value)))
    require(raw.get('format') == 'swdb.cpu-service-calibration.v1' and raw.get('evidence_kind') == 'native' and s.get('group') == GROUP, 'receipt classification differs')
    require(raw['threads'] == 1 and c.get('system') == 'Linux' and c.get('architecture') == 'x86_64', 'Linux/x86_64 serial T1 scope differs')
    require(c.get('host', '').split('.')[0] == raw['machine'] and c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}', str(c.get('commit'))), 'clean committed source/host identity missing')
    require('(verified:' in str(c.get('lane')) and isinstance(c.get('cpus'), list) and len(c['cpus']) == 1 and type(c['cpus'][0]) is int, 'verified lane/physical core missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.', c.get('compiler_version', '')), 'uninstrumented LLVM22 timing missing')
    require(c.get('flags', [])[:2] == FLAGS and all(f.startswith(TOOLCHAIN_PREFIXES) for f in c['flags'][2:]), 'compile recipe differs')
    require(7 <= s['repetitions'] <= 11 and .05 <= s['min_trial_s'] <= .2 and 0 < s['max_wall_s'] <= 900 and s.get('event_cap') == EVENT_CAP
            and s.get('batch_events') == BATCH_EVENTS and s.get('timed_data_cap_bytes') == TIMED_CAP and s.get('count_build_cap_bytes') == COUNT_CAP
            and s.get('resident_payload_bytes') == 0, 'caps/sampling differ')
    require(set(c.get('source_sha256', {})) == set(SOURCES) and all(hashed(v) for v in c['source_sha256'].values())
            and all(hashed(c.get(k)) for k in ('compiler_sha256', 'binary_sha256', 'machine_sha256')), 'source/compiler identities missing')
    libs = c.get('loaded_libraries', {})
    require(isinstance(libs, dict) and all(any(k.startswith(p) for k in libs) for p in ('libc.so', 'libstdc++'))
            and all(isinstance(v, dict) and hashed(v.get('sha256')) for v in libs.values()), 'C/C++ runtime hashes missing')
    require(valid(c), 'control environment declaration differs')
    require([x['id'] for x in raw['services']] == IDS, 'full library-call service list missing')
    for index, ((service_id, abi, definition, extra), service) in enumerate(zip(SERVICES, raw['services'])):
        proof = service['denominator'].get('proof')
        require(service['unit'] == 'seconds/call' and service['event_definition'] == definition
                and service['scope'] == {'event_abi': abi, **COMMON, **extra}, f'{service_id} ABI/scope differs')
        require(service['denominator']['level'] == 'selected_source_normalized_event' and service['denominator']['basis'] == 'measured'
                and isinstance(proof, dict) and proof.get('format') == 'swdb.cpu-library-call-count-proof.v1' and proof.get('pipeline') == PIPELINE,
                'separate count proof missing')
        require(proof['source_sha256'] == c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256'] == c['source_sha256'][SOURCES[2]]
                and all(hashed(proof.get(k)) for k in ('plugin_source_sha256', 'runtime_source_sha256')), 'timed/count shared source differs')
        require(proof['cells'] == [{'index': i, 'event_abi': a} for i, a in enumerate(NATIVE_ABIS)], 'counted exact ABI list differs')
        require({(p['events'], p['invoke']) for p in proof['points']} == {(n, b) for n in COUNT_POINTS for b in (True, False)}
                and len(proof['points']) == 2 * len(COUNT_POINTS), 'count points incomplete')
        by_events = {}
        for point in proof['points']:
            require(hashed(point.get('characterization_sha256')) and len(point['cells']) == len(SERVICES), 'count receipt identity missing')
            for k, cell in enumerate(point['cells']):
                expected = (k + 1) * point['events'] if point['invoke'] else 0
                require(cell['index'] == k and cell['event_abi'] == NATIVE_ABIS[k] and cell['executions'] == expected
                        and len(cell['source_sites']) == 1, 'selected event coefficient differs')
            by_events.setdefault(point['events'], []).append(point['other_uncovered_calls'])
        require(all(len(v) == 2 and v[0] == v[1] for v in by_events.values()), 'service and driver differ outside the selected events')
        require(len(service['trials']) == s['repetitions'], 'repetitions differ')
        for i, t in enumerate(service['trials']):
            require(type(t.get('events')) is int and 0 < t['events'] <= EVENT_CAP and t.get('batch_events') == BATCH_EVENTS
                    and t['events'] == BATCH_EVENTS * t.get('batches', 0), 'event denominator differs')
            require(t['order'] == ('service_first' if i % 2 == 0 else 'driver_first') and all(
                type(t[k]) in (int, float) and math.isfinite(t[k]) and t[k] >= s['min_trial_s'] for k in ('gross_seconds', 'driver_seconds')),
                'paired ordering/resolution differs')

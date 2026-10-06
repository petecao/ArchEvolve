"""LLVM characterization and composable analytic bounds. Updated: 2026-10-06 ET.

Commands are the public interface. Source counts use normalized pre-vectorization IR;
post-O3 facts are retained separately rather than guessing multiplicities after optimization.
Portable record-file inputs use the shared record access boundary (02/04 integration).
"""
import hashlib
import json
import math
import os
import platform
import re
import statistics
import copy
import shlex
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

from swdb import access, artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store

VERSION = 'swdb.analytic.v1'
CLASSES = ('integer', 'floating_point', 'branch', 'atomic')
PIPELINES = {'source-normalized-v1': 'mem2reg,loop-simplify',
             'source-normalized-v2': 'function(sroa,mem2reg),cgscc(inline),function(loop-simplify)'}


def register_cli(commands):
    sub = commands.add_parser('characterize', help='count source-normalized LLVM operations and accesses in one native run')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--source', type=Path, help='one buildable C/C++ translation unit with its protected driver')
    subject = sub.add_mutually_exclusive_group(required=True)
    subject.add_argument('--implementation')
    subject.add_argument('--candidate')
    sub.add_argument('--input', required=True)
    sub.add_argument('--adapter', choices=['registered-gapbs'], help='verify registered GAPBS source/input/trial-lambda binding')
    sub.add_argument('--counting-pipeline', choices=tuple(PIPELINES), help='fixed source normalization recipe; fixtures default v1, registered adapter requires v2')
    sub.add_argument('--trials', type=int, default=5, help='registered GAPBS trial count; preserve each invocation separately')
    sub.add_argument('--roi', help='declared timing ROI identity; recorded but not verified by this slice')
    sub.add_argument('--threads', type=int, default=1, help='explicit counted workload thread configuration')
    sub.add_argument('--id', required=True)
    sub.add_argument('--function', help='debug function name or LLVM symbol; absent counts every debug function in the translation unit')
    sub.add_argument('--region-map', type=Path, help='JSON: regions with id, function, line_start and line_end')
    sub.add_argument('--llvm-bin', type=Path, help='folder containing LLVM 22 clang++, opt and llvm-config')
    sub.add_argument('--toolchain-flag', action='append', default=[], help='compiler selection/header plumbing applied to pass, source and runtime builds (for example --toolchain-flag=--gcc-install-dir=/path)')
    sub.add_argument('--run-library-path', type=Path, action='append', default=[], help='native library folder, added to link/search paths and recorded (for example an installed libomp folder)')
    sub.add_argument('--build-flag', action='append', default=[], help='repeatable compiler/linker flag; use --build-flag=-I/path')
    sub.add_argument('--run-arg', action='append', default=[], help='repeatable argument to the counted native binary')
    sub.add_argument('--output', type=Path, help='new folder for compiled pass, IR, counts and run output (default a temporary folder)')
    sub.add_argument('--timeout-s', type=float, default=600)
    sub.add_argument('--fixture', action='store_true', help='label a hand-counted contract fixture, never application evidence')
    sub.add_argument('--target-description', help='reserved live counting input; target-specific stream counters follow in ticket 05')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=characterize)
    sub = commands.add_parser('estimate', help='compose mechanism bounds from a characterization and target description')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--characterization', required=True, help='record ID or YAML/JSON file')
    sub.add_argument('--target-description', required=True, help='record ID or YAML/JSON file')
    sub.add_argument('--protocol', required=True, help='estimate protocol identity; frozen protocol checks follow in ticket 06')
    sub.add_argument('--baseline', help='explicit baseline estimate record ID or YAML/JSON file')
    sub.add_argument('--id', required=True)
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=estimate)


def _run(command, *, env=None, timeout=600, cwd=None, check=True):
    try:
        result = subprocess.run([str(p) for p in command], capture_output=True, text=True,
                                env=env, timeout=timeout, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Failure(f'{Path(str(command[0])).name}: {exc}') from None
    if check and result.returncode:
        raise Failure(f'{Path(str(command[0])).name} failed ({result.returncode}): {result.stderr[-8000:]}')
    return result


def _llvm_bin(requested):
    configured = requested or os.environ.get('SWDB_LLVM_BIN')
    candidates = [Path(configured)] if configured else [Path('/opt/homebrew/opt/llvm/bin')]
    if not configured:
        found = shutil.which('llvm-config-22') or shutil.which('llvm-config')
        if found:
            candidates.insert(0, Path(found).resolve().parent)
    for candidate in candidates:
        if all((candidate / tool).is_file() for tool in ('llvm-config', 'opt', 'clang++')):
            version = _run([candidate / 'llvm-config', '--version']).stdout.strip()
            if version.startswith('22.'):
                return candidate, version
    raise Failure('LLVM 22 is required; set SWDB_LLVM_BIN or --llvm-bin to its bin folder')


def _envelope(kind, record_id, description):
    return {'kind': kind, 'schema_version': '0.4', 'id': record_id, 'status': 'draft',
            'created': writer.today(), 'updated': writer.today(),
            'provenance': [{'id': 'analytic', 'kind': 'measurement', 'description': description, 'uri': None}]}


def _fact(value, basis, **extra):
    return {'value': value, 'basis': 'unknown' if value is None else basis, **extra}


def _count(value, basis='measured', formula=None):
    return _fact(value, basis, formula=formula, scope='per_run')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(store, ref, kind):
    data = store.get(ref, kind)
    if data is None:
        try:
            data = access.read_record(Path(ref))
        except (OSError, ValueError) as exc:
            raise Failure(f'{kind} {ref!r} is neither an existing record nor a readable file: {exc}') from None
    if not isinstance(data, dict) or data.get('kind') != kind:
        raise Failure(f'{ref}: expected {kind} record')
    from swdb.schemas import SchemaSet
    from swdb import vocab
    vocabs, _ = vocab.load_all(paths.VOCAB)
    errors = sorted(SchemaSet(paths.SCHEMAS, vocabs).for_kind(kind).iter_errors(data), key=lambda e: str(e.path))
    if errors:
        raise Failure(f'{ref}: invalid {kind}: {errors[0].message}')
    problems = list(_payload_problems(data))
    if problems:
        raise Failure(f'{ref}: {problems[0][0]}: {problems[0][1]}')
    return data


def _counted_regions(static, counts):
    regions = []
    for r in static['regions']:
        ops = counts['operations'].get(str(r['index']), [0, 0, 0, 0])
        accesses = []
        for a in static['accesses']:
            if a['region_index'] != r['index']:
                continue
            dynamic = counts['accesses'].get(str(a['site']), {'elements': 0, 'bytes': 0, 'address_span_bytes': 0})
            accesses.append({'id': 'access.' + str(a['site']),
                'source_location': {'function': a['function'], 'line': a['line'], 'column': a['column'], 'path': a.get('path',''), 'llvm_function': a.get('llvm_function','')},
                'address_shape': _fact(None if a['address_shape'] == 'unknown' else a['address_shape'], 'code_reading'),
                'stride_bytes': _fact(a['stride_bytes'], 'code_reading'), 'element_bytes': a['element_bytes'],
                'update_kind': a['update_kind'], 'read_write': a.get('read_write',False), 'element_count': _count(dynamic['elements']),
                'bytes_accessed': _count(dynamic['bytes']),
                'observed_address_span_bytes': _fact(dynamic['address_span_bytes'], 'measured'),
                'observed_unique_bytes': _fact(dynamic.get('unique_bytes', 0), 'measured'),
                'address_expression': a['address_expression'], 'ir_lanes': a['ir_lanes']})
        regions.append({'id': r['id'], 'source_location': {'function': r['function'], 'line': r['line'], 'path': r.get('path',''), 'llvm_function': r.get('llvm_function','')},
            'active_workers': _fact(counts.get('active_workers',{}).get(str(r['index']),0), 'measured'),
            'mapped': r['mapped'], 'kind': 'loop' if r['is_loop'] else 'serial_remainder',
            'access_patterns': accesses, 'operation_counts': {name: _count(ops[i]) for i, name in enumerate(CLASSES)},
            'dynamic_counts': {'loop_iterations': _count(counts['trips'].get(str(r['index']), 0)) if r['is_loop'] else _count(None, 'unknown')},
            'footprint_bytes': _fact(counts.get('footprints', {}).get(str(r['index']), 0), 'measured', note='Live union of virtual byte ranges in this exclusive IR region; addresses are never persisted.'),
            'accelerator_calls': [], 'address_stream_counts': {}})
    # Several source loops may map to one existing region; aggregate their counters,
    # while static_analysis.loops retains each loop's identity and source location.
    combined = {}
    worker_tokens = {}
    team_sizes = {}
    for r in static['regions']:
        worker_tokens.setdefault(r['id'],set()).update(counts.get('worker_tokens',{}).get(str(r['index']),[]))
        team_sizes.setdefault(r['id'],set()).update(counts.get('team_sizes',{}).get(str(r['index']),[]))
    for region in regions:
        if region['id'] not in combined:
            combined[region['id']] = region
        else:
            previous = combined[region['id']]
            previous['access_patterns'].extend(region['access_patterns'])
            previous['footprint_bytes']['value'] = max(previous['footprint_bytes']['value'],region['footprint_bytes']['value'])
            previous['active_workers']['value'] = max(previous['active_workers']['value'],region['active_workers']['value'])
            for key in CLASSES:
                previous['operation_counts'][key]['value'] += region['operation_counts'][key]['value']
            previous['dynamic_counts']['loop_iterations'] = _count(None, 'unknown')
            previous['dynamic_counts']['loop_iterations']['note'] = 'Several lowered LLVM loops share this source region; unique source-loop iterations are not inferred by summing them.'
    regions = list(combined.values())
    for region in regions:
        if 'worker_tokens' in counts:
            region['active_workers']['value'] = len(worker_tokens[region['id']])
        region['worker_context'] = {'team_sizes': sorted(team_sizes[region['id']]),
            'measurement': 'Distinct executing workers per exclusive region within one trial; team sizes are context, not an active-worker multiplier.'}
    calls = []
    for original in static['unmodeled_calls']:
        called = dict(original)
        called['execution_count'] = _count(counts.get('calls', {}).get(str(called['site']), 0))
        called['size_bytes'] = _fact(counts.get('call_size_bytes', {}).get(str(called['site'])), 'measured')
        calls.append(called)
    return regions, calls



def characterize(args):
    store = Store(args.records)
    subject = args.candidate or args.implementation
    kind = 'candidate' if args.candidate else 'implementation'
    if store.get(subject, kind) is None:
        raise Failure(f'{kind} {subject!r} does not exist')
    if store.get(args.input, 'input') is None and store.get(args.input, 'workload') is None:
        raise Failure(f'input/workload {args.input!r} does not exist')
    subject_record = store.get(subject, kind)
    input_record = store.get(args.input, 'input') or store.get(args.input, 'workload')
    adapter = None
    if args.adapter:
        from swdb import analytic_binding
        adapter = analytic_binding.prepare(store, args, subject_record, input_record)
        args.source = adapter['source']
        args.roi = adapter['roi']
        args.build_flag = adapter['flags']
        args.run_arg = adapter['run']
    if args.source is None:
        raise Failure('--source is required without a registered adapter')
    source = args.source.resolve()
    if not source.is_file():
        raise Failure(f'source does not exist: {source}')
    if args.threads < 1:
        raise Failure('--threads must be positive')
    if args.timeout_s <= 0:
        raise Failure('--timeout-s must be positive')
    if args.target_description:
        raise Failure('this streaming slice has no target-specific address-stream mechanism; omit --target-description')
    # The counting command never mutates source or evaluator files. It only emits IR and
    # a separate counted binary. Flags governing the build still enter the recorded identity.
    forbidden = ('-o', '-emit-llvm', '-fpass-plugin', '-Xclang', '-flto', '-g0')
    if any(f == x or f.startswith(x + '=') for f in args.build_flag for x in forbidden):
        raise Failure('build flags may not replace output, debug mapping, LTO, or instrumentation stages')
    llvm, version = _llvm_bin(args.llvm_bin)
    output = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='swdb-characterize-'))
    if args.output:
        if output.exists():
            raise Failure(f'output already exists; choose a new folder: {output}')
        artifacts.external_directory(output)
    subject_record = store.get(subject, kind)
    source_identity = {'subject_record_sha256': artifacts.digest(subject_record)}
    if kind == 'candidate':
        source_identity.update({'source_snapshot': subject_record['source_snapshot'],
            'candidate_artifact_sha256': subject_record['artifact']['sha256'],
            'candidate_diff_sha256': subject_record.get('diff_sha256')})
        if not args.fixture:
            artifact_root = artifacts.verify(subject_record['artifact'])
            artifacts.check_protections(artifact_root, subject_record['protections'])
    else:
        context = store.source_context(subject_record)
        source_identity['registered_source'] = context['source']
        source_identity['registered_function'] = subject_record['function']
    input_record = store.get(args.input, 'input') or store.get(args.input, 'workload')
    flags = list(args.build_flag)
    toolchain_flags = list(args.toolchain_flag)
    if adapter:
        args.region_map = output / 'regions.json'
        args.region_map.write_text(json.dumps(adapter['mapping']))
        source_identity.update(adapter['identity'])
    plugin = output / 'Characterize.so'
    llvm_flags = shlex.split(_run([llvm / 'llvm-config', '--cxxflags', '--ldflags']).stdout)
    shared_probe = _run([llvm / 'llvm-config', '--link-shared', '--libs', 'core', 'passes', 'analysis', 'support', '--system-libs'], check=False)
    plugin_linkage = 'shared_llvm' if shared_probe.returncode == 0 else 'host_symbols'
    if plugin_linkage == 'shared_llvm':
        llvm_flags.extend(shlex.split(shared_probe.stdout))
    elif platform.system() == 'Darwin':
        # Linux shared objects resolve the host's exported LLVM symbols at opt load;
        # Mach-O requires explicit dynamic lookup for this same plugin convention.
        llvm_flags.extend(['-Wl,-undefined,dynamic_lookup'])
    # Never link a static libLLVM into the plugin: duplicate registries/LLVM globals
    # would conflict with opt. A static opt distribution must export its host symbols.
    run_library_paths = [str(p.resolve()) for p in args.run_library_path]
    llvm_src = Path(__file__).with_name('llvm')
    build = [llvm / 'clang++', '-shared', '-fPIC', llvm_src / 'Characterize.cpp', '-o', plugin,
             *llvm_flags, *toolchain_flags, '-Wl,-rpath,' + str(llvm.parent / 'lib')]
    _run(build, timeout=args.timeout_s)
    base = [llvm / 'clang++', '-O3', '-g', '-emit-llvm', '-c', source, *flags, *toolchain_flags]
    optimized = output / 'optimized.bc'
    raw = output / 'source.bc'
    normalized = output / 'normalized.bc'
    instrumented = output / 'instrumented.bc'
    _run([*base, '-o', optimized], timeout=args.timeout_s)
    _run([*base, '-Xclang', '-disable-llvm-passes', '-o', raw], timeout=args.timeout_s)
    # Adapter boundary hooks are inserted before helper inlining, preserving the exact source call.
    bound_ir = output / 'bound.bc'
    if adapter:
        gate_env = dict(os.environ, SWDB_ROI_PATH=adapter['roi_path'], SWDB_ROI_LINE=str(adapter['roi_line']))
        _run([llvm / 'opt', '-load-pass-plugin=' + str(plugin), '-passes=swdb-bind-roi', raw, '-o', bound_ir], env=gate_env, timeout=args.timeout_s)
    pipeline_version = args.counting_pipeline or ('source-normalized-v2' if adapter else 'source-normalized-v1')
    pipeline = PIPELINES[pipeline_version]
    _run([llvm / 'opt', '-passes=' + pipeline, bound_ir if adapter else raw, '-o', normalized], timeout=args.timeout_s)
    env = dict(os.environ)
    env['SWDB_SUBJECT'] = subject
    env['SWDB_COUNT_FUNCTION'] = args.function or ''
    env['SWDB_REGION_MAP'] = str(args.region_map.resolve()) if args.region_map else ''
    env['SWDB_ANALYSIS_OUTPUT'] = str(output / 'optimized.json')
    env['SWDB_INSTRUMENT'] = '0'
    _run([llvm / 'opt', '-load-pass-plugin=' + str(plugin), '-passes=swdb-characterize', optimized, '-disable-output'], env=env, timeout=args.timeout_s)
    env['SWDB_ANALYSIS_OUTPUT'] = str(output / 'source.json')
    env['SWDB_INSTRUMENT'] = '1'
    _run([llvm / 'opt', '-load-pass-plugin=' + str(plugin), '-passes=swdb-characterize', normalized, '-o', instrumented], env=env, timeout=args.timeout_s)
    binary = output / 'counted'
    native_library_flags = [flag for folder in run_library_paths for flag in ('-L' + folder, '-Wl,-rpath,' + folder)]
    _run([llvm / 'clang++', '-O3', instrumented, llvm_src / 'CountingRuntime.cpp', '-o', binary, *flags, *toolchain_flags, *native_library_flags], timeout=args.timeout_s)
    for name in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
        env[name] = os.pathsep.join(run_library_paths + ([env[name]] if env.get(name) else []))
    env['OMP_NUM_THREADS'] = str(args.threads)
    env['OMP_DYNAMIC'] = 'FALSE'
    env['SWDB_ROI_GATED'] = '1' if adapter else '0'
    env['SWDB_COUNTS_OUTPUT'] = str(output / 'counts.json')
    executed = _run([binary, *args.run_arg], env=env, timeout=args.timeout_s)
    (output / 'stdout.txt').write_text(executed.stdout)
    (output / 'stderr.txt').write_text(executed.stderr)
    try:
        static = json.loads((output / 'source.json').read_text())
        optimized_facts = json.loads((output / 'optimized.json').read_text())
        counts = json.loads((output / 'counts.json').read_text())
    except (OSError, ValueError) as exc:
        raise Failure(f'counted native run did not produce valid counts: {exc}') from None
    if not static['regions']:
        raise Failure('no source regions matched the requested function/debug information')
    regions, calls = _counted_regions(static, counts)
    trials = []
    if adapter:
        if len(counts.get('trials', [])) != args.trials:
            raise Failure('counted run lacks the registered trial sequence')
        for index, observed in enumerate(counts['trials']):
            trial_regions, trial_calls = _counted_regions(static, observed)
            called_regions = {c['region'] for c in trial_calls if c['execution_count']['value']}
            trials.append({'position': index, 'sources': observed.get('sources', []),
                'regions': [r for r in trial_regions if any(v['value'] for v in r['operation_counts'].values()) or any(a['element_count']['value'] for a in r['access_patterns']) or r['dynamic_counts']['loop_iterations']['value'] or r['id'] in called_regions],
                'unmodeled_calls': [c for c in trial_calls if c['execution_count']['value']]})
        if any(len(t['sources']) != 1 for t in trials):
            raise Failure('counted trial lacks its exact GAPBS source selection')
    record = _envelope('workload_characterization', args.id,
        'LLVM 22 static pass plus one IR-instrumented native count run; no timing measurement.')
    record.update({'format': 'swdb.workload-characterization.v1',
        'subject': {'kind': kind, 'id': subject}, 'input': args.input,
        'source': {'path': str(source), 'sha256': _sha(source), 'build_flags': flags,
                   'run_arguments': list(args.run_arg), 'protected_driver': 'unchanged; separately compiled instrumentation'},
        'binding': {'state': 'verified' if adapter else 'fixture' if args.fixture else 'unverified',
            'subject_source_identity': source_identity, 'input_record_sha256': artifacts.digest(input_record),
            'roi': args.roi, 'threads': args.threads,
            'run_arguments_sha256': artifacts.digest(list(args.run_arg)),
            'note': 'Source/input/ROI binding to a registered subject is not certified by an arbitrary supplied translation-unit SHA; application evidence needs the registered-source/protocol adapter.'},
        'host': {'machine': socket.gethostname(), 'architecture': platform.machine(), 'system': platform.platform()},
        'toolchain': {'llvm_version': version, 'llvm_bin': str(llvm), 'compiler_flags': toolchain_flags, 'plugin_linkage': plugin_linkage, 'run_library_paths': run_library_paths},
        'counting': {'level': 'source_normalized_ir', 'passes': [pipeline],
            'pipeline_version': pipeline_version,
            'summary': 'per_trial_then_median_time' if adapter else 'single_run',
            'native_runs': 1, 'basis': 'measured', 'vector_multiplicity': 'instrumented before vectorization and unrolling; existing fixed vectors counted by lane',
            'operation_definition': 'Normalized IR arithmetic/comparison operations; FMA counts two floating-point operations, branches count terminator executions; address and cast instructions excluded.',
            'loop_definition': 'Body entries when the header condition chooses inside/outside; header entries for other loop shapes.',
            'binary_sha256': _sha(binary), 'counts_sha256': _sha(output / 'counts.json'), 'output_directory': str(output)},
        'static_analysis': {'basis': 'code_reading', 'source_ir_sha256': _sha(normalized), 'optimized_ir_sha256': _sha(optimized),
            'loops': static['loops'], 'optimized_facts': optimized_facts,
            'mapping_note': 'Optimized loops/accesses are reported separately; optimized vector/unroll/call elimination is never used as a source count multiplier.'},
        'coverage': {'scope': 'registered_trial_lambda' if adapter else 'function' if args.function else 'translation_unit',
            'function': args.function, 'whole_timed_call': True if adapter else None,
            'count_coverage': 'normalized instructions in selected debug functions; indirect callees and other translation units are not claimed',
            'missing_costs': sorted({c['name'] for c in calls + [c for t in trials for c in t['unmodeled_calls']] if c['execution_count']['value'] and not c.get('body_counted', False)}),
            'missing_counts': ['callee bodies outside selected debug functions and other translation units'] if any(c['execution_count']['value'] and not c.get('body_counted', False) for c in calls + [c for t in trials for c in t['unmodeled_calls']]) else []},
        'regions': regions, 'unmapped_loops': [r['id'] for r in regions if r['kind'] == 'loop' and not r['mapped']],
        'unmodeled_calls': calls, 'evidence_kind': 'contract_fixture' if args.fixture else 'execution'})
    if adapter:
        record['trials'] = trials
        record['binding']['note'] = 'Registered source excerpts, input generator and original timed kernel lambda verified; each trial and SourcePicker selection retained.'
        record['coverage']['ambiguous_helper_loops'] = adapter['ambiguous_helper_loops']
        record['pattern_comparison'] = analytic_binding.compare_patterns(subject_record, regions, adapter['ambiguous_helper_loops'], adapter['mapping']['regions'])
        graph = re.search(r'Graph has ([0-9]+) nodes and ([0-9]+) (un)?directed edges', executed.stdout)
        if not graph:
            raise Failure('registered counting run lacks graph identity')
        observed_graph = {'num_nodes': int(graph[1]), 'reported_edges': int(graph[2]), 'directed': graph[3] is None}
        record['binding']['execution_receipt'] = analytic_binding.execution_receipt(record, observed_graph, llvm_src / 'Characterize.cpp', llvm_src / 'CountingRuntime.cpp')
        problems = analytic_binding.verify_binding(record, store, require_available=True)
        if problems:
            raise Failure('registered execution binding failed: ' + '; '.join(problems))
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record


def _estimate_regions(source_regions, source_calls, target):
    from swdb import analytic_models
    # Models are bounds, not a fitted timing. Preserve unknowns in composition.
    regions = []
    for region in source_regions:
        bounds = [analytic_models.evaluate(region, mechanism, [m['model'] for m in target['mechanisms']], target['threads']) for mechanism in target['mechanisms']]
        called = [c for c in source_calls
                  if c.get('region') == region['id'] and c.get('execution_count', {}).get('value') != 0 and not c.get('body_counted',False)]
        if called:
            bounds.append(analytic_models.bound('unmodeled_calls', None, 'sum(call execution count * call cost)',
                {'calls': called}, ['call_cost.' + c['name'] for c in called]))
        unknown = any(b['seconds'] is None for b in bounds)
        seconds = None if unknown else max((b['seconds'] for b in bounds), default=0.0)
        limiting = None if unknown else max(bounds, key=lambda b: b['seconds'])['model']
        regions.append({'id': region['id'], 'seconds': seconds, 'basis': 'estimated',
            'bounds': bounds, 'overheads': [], 'limiting_bound': limiting,
            'state': 'unknown' if unknown else 'known'})
    seconds = None if any(r['seconds'] is None for r in regions) else sum(r['seconds'] for r in regions)
    return regions, seconds


def estimate(args):
    from swdb import analytic_models
    store = Store(args.records)
    characterization = _load(store, args.characterization, 'workload_characterization')
    target = _load(store, args.target_description, 'target_description')
    if target['threads'] != characterization['binding']['threads']:
        raise Failure('target thread count differs from the counted workload thread identity')
    regions, seconds = _estimate_regions(characterization['regions'], characterization['unmodeled_calls'], target)
    trial_estimates=[]
    for trial in characterization.get('trials',[]):
        rows,total=_estimate_regions(trial['regions'],trial['unmodeled_calls'],target)
        trial_estimates.append({'position':trial['position'],'sources':trial['sources'],'regions':rows,'seconds':total})
    if trial_estimates:
        seconds=None if any(t['seconds'] is None for t in trial_estimates) else statistics.median(t['seconds'] for t in trial_estimates)
        lookups=[{r['id']:r for r in t['regions']} for t in trial_estimates]
        for row in regions:
            sequence=[index.get(row['id']) for index in lookups]
            values=[r['seconds'] if r else 0. for r in sequence]
            row['seconds']=None if any(v is None for v in values) else statistics.median(values)
            row['state']='unknown' if row['seconds'] is None else 'known'
            templates={b['model']:b for b in row['bounds']}
            for r in sequence:
                if r:
                    for b in r['bounds']:templates.setdefault(b['model'],copy.deepcopy(b))
            row['bounds']=list(templates.values())
            for bound in row['bounds']:
                bs=[next((b for b in r['bounds'] if b['model']==bound['model']),None) if r else None for r in sequence]
                values=[b['seconds'] if b else 0. for b in bs]
                bound['seconds']=None if any(v is None for v in values) else statistics.median(values)
                bound['state']='unknown' if bound['seconds'] is None else 'known'
                bound['missing']=sorted({m for b in bs if b for m in b['missing']})
                bound['notes']=list(bound.get('notes',[]))+['Per-region bound summary is the median across independent trial estimates.']
            row['limiting_bound']=None if row['seconds'] is None else max(row['bounds'],key=lambda b:b['seconds'])['model']
    record = _envelope('estimate', args.id, 'Analytic mechanism bounds from compiler/counting facts and frozen target parameters; no target timing.')
    record.update({'format': 'swdb.estimate.v1', 'basis': 'estimated', 'estimator_version': VERSION,
        'estimator_variant': target['estimator_variant'], 'calibration_sources': target['calibration_sources'],
        'characterization': characterization['id'], 'characterization_sha256': artifacts.digest(characterization),
        'target_description': target['id'], 'target_description_sha256': artifacts.digest(target),
        'target_description_snapshot': target, 'target': target['target'], 'threads': target['threads'],
        'subject': characterization['subject'], 'input': characterization['input'], 'protocol': args.protocol,
        'regions': regions, 'seconds': seconds, 'ratio': None, 'baseline': None,
        'verdict': 'within_error', 'error_band': None,
        'llm_parameters': [], 'evidence_kind': characterization['evidence_kind'],
        'binding': characterization['binding'],
        'scope': characterization.get('coverage', {'scope': 'counted source regions', 'unmapped_loops': characterization['unmapped_loops']}),
        'notes': ['No validated error band exists in this slice; the verdict remains within_error.',
                  'Total is the sum of region maxima and serial remainder. Any required unknown makes its region and total unknown.']})
    if trial_estimates:
        record['trials'] = trial_estimates
        record['summary'] = 'median_whole_call_seconds'
        record['notes'].append('Estimate each trial by summing exclusive region maxima; the reported total is the median whole-call trial time. Per-region medians are diagnostic and do not generally sum to that median.')
    if args.baseline:
        baseline = _load(store, args.baseline, 'estimate')
        required = ('input', 'target_description_sha256', 'protocol', 'threads', 'evidence_kind')
        if any(baseline.get(k) != record.get(k) for k in required):
            raise Failure('baseline estimate input, target description, protocol, threads or evidence kind differs')
        record['baseline'] = {'id': baseline['id'], 'sha256': artifacts.digest(baseline)}
        if seconds is not None and seconds > 0 and baseline['seconds'] is not None:
            record['ratio'] = baseline['seconds'] / seconds
    writer.commit(args.records, new=[record])
    return record


def _payload_problems(data):
    """Payload integrity and finite-number checks shared by CLI loading and validate."""
    kind = data['kind']
    if kind == 'workload_characterization':
        without_identity = {k: v for k, v in data.items() if k != 'identity_sha256'}
        try:
            expected = artifacts.digest(without_identity)
        except (ValueError, TypeError):
            yield 'identity_sha256', 'characterization contains non-finite or non-JSON values'
            return
        if data['identity_sha256'] != expected:
            yield 'identity_sha256', 'characterization content differs from its counted receipt identity'
        ids = [r['id'] for r in data['regions']]
        if len(set(ids)) != len(ids):
            yield 'regions', 'region IDs must be unique after loop aggregation'
        groups=[('regions',data['regions'])]+[(f'trials[{i}].regions',trial.get('regions',[])) for i,trial in enumerate(data.get('trials',[]))]
        for group, rows in groups:
          for i, region in enumerate(rows):
            counts = list(region['operation_counts'].values()) + list(region['dynamic_counts'].values())
            counts += [region['footprint_bytes']] + ([region['active_workers']] if 'active_workers' in region else [])
            counts += [a[k] for a in region['access_patterns'] for k in ('element_count', 'bytes_accessed', 'observed_address_span_bytes','observed_unique_bytes') if k in a]
            for count in counts:
                value = count.get('value')
                if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0):
                    yield f'{group}[{i}]', 'work counts must be finite nonnegative numbers or null'
    elif kind == 'target_description':
        for i, mechanism in enumerate(data['mechanisms']):
            for name, fact in mechanism['parameters'].items():
                value = fact['value']
                if value is not None and not math.isfinite(value):
                    yield f'mechanisms[{i}].parameters.{name}.value', 'target parameters must be finite or null'
    elif kind == 'estimate':
        try:
            expected = artifacts.digest(data['target_description_snapshot'])
        except (ValueError, TypeError):
            yield 'target_description_snapshot', 'target snapshot contains non-finite or non-JSON values'
            return
        if expected != data['target_description_sha256']:
            yield 'target_description_sha256', 'target snapshot differs from its recorded content hash'
        for key in ('seconds', 'ratio'):
            value = data[key]
            if value is not None and (not math.isfinite(value) or value < 0):
                yield key, 'estimate values must be finite nonnegative numbers or null'
        for i, region in enumerate(data['regions']):
            unknown = any(b['seconds'] is None for b in region['bounds'] + region['overheads'])
            if unknown and region['seconds'] is not None:
                yield f'regions[{i}].seconds', 'a required unknown bound makes region seconds unknown'
            for j, b in enumerate(region['bounds'] + region['overheads']):
                value = b['seconds']
                if value is not None and (not math.isfinite(value) or value < 0):
                    yield f'regions[{i}].bounds[{j}].seconds', 'bound values must be finite nonnegative numbers or null'
        if any(r['seconds'] is None for r in data['regions']) and data['seconds'] is not None:
            yield 'seconds', 'an unknown region makes total seconds unknown'
        if data['seconds'] is None and data['ratio'] is not None:
            yield 'ratio', 'ratio requires known total seconds'


def validate_record(record, ctx):
    from swdb.problems import Problem
    for field, reason in _payload_problems(record.data):
        yield Problem(record.rel, field, reason)
    if record.kind == 'workload_characterization' and record.data.get('binding', {}).get('state') == 'verified':
        from swdb import analytic_binding
        for reason in analytic_binding.verify_binding(record.data, ctx.store):
            yield Problem(record.rel, 'binding', reason)
    if record.kind == 'estimate':
        characterization = ctx.store.get(record.data['characterization'], 'workload_characterization')
        if characterization is not None and artifacts.digest(characterization) != record.data['characterization_sha256']:
            yield Problem(record.rel, 'characterization_sha256', 'characterization record differs from the estimate input hash')

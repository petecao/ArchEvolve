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
    sub.add_argument('--adapter', choices=['registered-gapbs','registered-functional'], help='verify registered GAPBS source/input/trial-lambda binding')
    sub.add_argument('--source-snapshot', help='immutable baseline snapshot for registered-functional; candidates pin their own snapshot')
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
    sub.add_argument('--object-scopes', action='store_true', help='observe bounded source objects and function-scoped ABI referent views; no residency claim')
    sub.add_argument('--state-budget', type=int, default=524288, help='maximum transient logical observation entries; overflow preserves named unknowns')
    sub.add_argument('--target-description', help='frozen description for generic functional-command and allocation-relative logical window counts')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=characterize)
    sub = commands.add_parser('estimate', help='compose mechanism bounds from a characterization and target description')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--characterization', required=True, help='record ID or YAML/JSON file')
    sub.add_argument('--target-description', required=True, help='record ID or YAML/JSON file')
    sub.add_argument('--protocol', required=True, help='persisted frozen estimate protocol ID')
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
    from swdb import workflow
    return {'kind': kind, 'schema_version': '0.4', 'id': record_id, 'status': 'draft',
            'created': writer.today(), 'updated': writer.today(), **workflow.CREATION_TAGS,
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


def _uncovered_call(call):
    return not call.get('body_counted', False) and call.get('cost_accounting', 'opaque_callee') not in (
        'no_runtime_operation', 'source_normalized_operations')


def _counted_regions(static, counts, count_scope="per_run", observation_contract=None):
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
    if 'memory_service_counts' in counts:
        updates=('read','write','add-update','compare-and-swap','min-max-update','arbitrary')
        for original,region in zip(static['regions'],regions):
            observed=counts['memory_service_counts'].get(str(original['index']),{})
            requests={kind:[] for kind in updates}
            for item in observed.get('requests',[]):
                requests[updates[item['update']]].append({'element_bytes':item['element_bytes'],
                    'requests':{'value':item['requests'],'basis':'unknown' if item['requests'] is None else 'measured','scope':count_scope}})
            missing=observed.get('missing',[])
            region['memory_service_counts']={'format':'swdb.memory-service-counts.v1',
                'scope':count_scope,'observation_method':'source_normalized_ir_allocation_relative',
                'state':'partial' if missing else 'known','requests_by_update_kind':requests,
                'useful_bytes':_fact(observed.get('useful_bytes',0),'measured'),
                **{name:_fact(observed.get(name,0),'measured') for name in
                    ('lifetime_line_union','logical_first_read_pages','logical_first_write_pages',
                     'pre_roi_allocation_pages','in_roi_allocation_pages','unknown_object_requests')},
                'missing':missing,'assumption_sha256':artifacts.digest({'line_bytes':64,'page_bytes':4096,
                    'placement':'allocation_relative','first_touch':'first_source_observer_access'})}
    if any('object_scope_counts' in row for row in counts.get('memory_service_counts',{}).values()):
        for original,region in zip(static['regions'],regions):
            observed=counts['memory_service_counts'].get(str(original['index']),{}).get('object_scope_counts',{})
            region['memory_service_counts']['object_scope_counts']={name:_fact(observed.get(name,0),'measured')
                for name in ('full_allocation_requests','bounded_view_requests','unresolved_requests','bounded_view_line_union')}
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
            previous['footprint_bytes']['value'] = (None if previous['footprint_bytes']['value'] is None or region['footprint_bytes']['value'] is None else max(previous['footprint_bytes']['value'],region['footprint_bytes']['value']))
            previous['footprint_bytes']['basis'] = 'unknown' if previous['footprint_bytes']['value'] is None else 'measured'
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
    if 'call_shapes' in counts:
        for region in regions:
            shaped=[]
            for call in calls:
                if call['region']!=region['id']:continue
                observed=counts['call_shapes'].get(str(call['site']),{})
                def bins(name):
                    return [{'bytes':item['bytes'],'execution_count':{'value':item['executions'],
                        'basis':'measured','scope':count_scope}} for item in observed.get(name,[])]
                unknown_lengths=observed.get('unknown_lengths',0)
                unknown_free=observed.get('unknown_free_lifetimes',0)
                shaped.append({'site':call['site'],'name':call['name'],'event':call.get('event','external_call'),
                    'execution_count':{'value':call['execution_count']['value'],'basis':'measured','scope':count_scope},
                    'body_counted':call.get('body_counted',False),'known_length_bins':bins('known_length_bins'),
                    'unknown_lengths':{'value':unknown_lengths,'basis':'measured','scope':count_scope},
                    'allocation_lifetime_size_bins':bins('allocation_lifetime_size_bins'),
                    'unknown_free_lifetimes':{'value':unknown_free,'basis':'measured','scope':count_scope},
                    'scope':count_scope,'missing':(['call_length'] if unknown_lengths else [])+
                        (['free_allocation_lifetime'] if unknown_free else [])})
            region['call_shape_counts']={'format':'swdb.call-shape-counts.v1','scope':count_scope,'calls':shaped}
    if observation_contract:
        from swdb.offload_observation import merge
        merge(regions,static,counts,observation_contract,count_scope)
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
    if args.source_snapshot and args.adapter!='registered-functional':
        raise Failure('--source-snapshot requires registered-functional')
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
    if args.state_budget < 1:
        raise Failure('--state-budget must be positive')
    if args.timeout_s <= 0:
        raise Failure('--timeout-s must be positive')
    live_contract=None
    if args.target_description:
        from swdb.offload_observation import prepare
        from swdb.archevolve import require_team_safe
        requested_target=_load(store,args.target_description,'target_description')
        require_team_safe(store,requested_target,command='characterize')
        live_contract=prepare(store,requested_target,source,fixture=args.fixture,compile_flags=args.build_flag+args.toolchain_flag)
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
            artifact_root = adapter['artifact_root'] if adapter and 'artifact_root' in adapter else artifacts.verify(subject_record['artifact'])
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
    command_contract=output/'functional-observation.json'
    if live_contract:command_contract.write_text(json.dumps(live_contract))
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
    analysis_input=bound_ir if adapter else raw
    if live_contract:
        command_ir=output/'commands.bc'
        command_env=dict(os.environ,SWDB_FUNCTIONAL_OBSERVATION=str(command_contract))
        _run([llvm/'opt','-load-pass-plugin='+str(plugin),'-passes=swdb-bind-commands',analysis_input,'-o',command_ir],env=command_env,timeout=args.timeout_s)
        analysis_input=command_ir
    pipeline_version = args.counting_pipeline or ('source-normalized-v2' if adapter else 'source-normalized-v1')
    pipeline = PIPELINES[pipeline_version]
    _run([llvm / 'opt', '-passes=' + pipeline, analysis_input, '-o', normalized], timeout=args.timeout_s)
    env = dict(os.environ)
    if live_contract:env['SWDB_FUNCTIONAL_OBSERVATION']=str(command_contract)
    env['SWDB_SUBJECT'] = subject
    env['SWDB_COUNT_FUNCTION'] = args.function or ''
    env['SWDB_REGION_MAP'] = str(args.region_map.resolve()) if args.region_map else ''
    env['SWDB_ANALYSIS_OUTPUT'] = str(output / 'optimized.json')
    env['SWDB_INSTRUMENT'] = '0'
    env.pop('SWDB_OBJECT_SCOPES',None)
    if args.object_scopes:env['SWDB_OBJECT_SCOPES']='1'
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
    env['SWDB_STATE_BUDGET'] = str(args.state_budget)
    env['SWDB_COUNTS_OUTPUT'] = str(output / 'counts.json')
    if live_contract:env.update(live_contract['environment'])
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
    regions, calls = _counted_regions(static, counts,observation_contract=live_contract)
    trials = []
    if counts.get('trials') or adapter:
        if adapter and len(counts.get('trials', [])) != args.trials:
            raise Failure('counted run lacks the registered trial sequence')
        for index, observed in enumerate(counts['trials']):
            trial_regions, trial_calls = _counted_regions(static, observed, count_scope='per_trial',observation_contract=live_contract)
            called_regions = {c['region'] for c in trial_calls if c['execution_count']['value']}
            trials.append({'position': index, 'sources': observed.get('sources', []),
                'regions': [r for r in trial_regions if any(v['value'] for v in r['operation_counts'].values()) or any(a['element_count']['value'] for a in r['access_patterns']) or r['dynamic_counts']['loop_iterations']['value'] or r['id'] in called_regions or any(c['execution_count']['value'] for c in r['accelerator_calls'])],
                'unmodeled_calls': [c for c in trial_calls if c['execution_count']['value']]})
        if adapter and adapter['identity'].get('source_selection','source_picker')=='source_picker' and any(len(t['sources']) != 1 for t in trials):
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
            'summary': 'per_trial_then_median_time' if trials else 'single_run',
            'native_runs': 1, 'basis': 'measured', 'vector_multiplicity': 'instrumented before vectorization and unrolling; existing fixed vectors counted by lane',
            'operation_definition': 'Normalized IR arithmetic/comparison operations; FMA counts two floating-point operations; checked integer arithmetic counts the result and overflow predicate (two per lane); branches count terminator executions; optimizer hints, address and cast instructions excluded.',
            'loop_definition': 'Body entries when the header condition chooses inside/outside; header entries for other loop shapes.',
            'binary_sha256': _sha(binary), 'counts_sha256': _sha(output / 'counts.json'), 'output_directory': str(output)},
        'static_analysis': {'basis': 'code_reading', 'source_ir_sha256': _sha(normalized), 'optimized_ir_sha256': _sha(optimized),
            'loops': static['loops'], 'optimized_facts': optimized_facts,
            'mapping_note': 'Optimized loops/accesses are reported separately; optimized vector/unroll/call elimination is never used as a source count multiplier.'},
        'coverage': {'scope': 'registered_trial_lambda' if adapter else 'function' if args.function else 'translation_unit',
            'function': args.function, 'whole_timed_call': True if adapter else None,
            'count_coverage': 'normalized instructions in selected debug functions; indirect callees and other translation units are not claimed',
            'missing_costs': sorted({c['name'] for c in calls + [c for t in trials for c in t['unmodeled_calls']] if c['execution_count']['value'] and _uncovered_call(c)}),
            'missing_counts': ['callee bodies outside selected debug functions and other translation units'] if any(c['execution_count']['value'] and _uncovered_call(c) for c in calls + [c for t in trials for c in t['unmodeled_calls']]) else []},
        'regions': regions, 'unmapped_loops': [r['id'] for r in regions if r['kind'] == 'loop' and not r['mapped']],
        'unmodeled_calls': calls, 'evidence_kind': 'contract_fixture' if args.fixture else 'execution'})
    native_libraries = {}
    native_missing = []
    for loaded_path in counts.get('loaded_images', []):
        library = Path(loaded_path).resolve()
        key = library.name
        if key in native_libraries and native_libraries[key]['path'] != str(library):
            native_missing.append('loaded_library_basename_collision:' + key)
            key = str(library)
        library_hash = _sha(library) if library.is_file() else None
        if library_hash is None:
            native_missing.append('loaded_library_hash:' + key)
        native_libraries[key] = {'path': str(library), 'sha256': library_hash}
    if not native_libraries:
        native_missing.append('process_loaded_images')
    environment_prefixes=['OMP_','KMP_','GOMP_','MALLOC_']
    environment_exact=['LD_LIBRARY_PATH','DYLD_LIBRARY_PATH','DYLD_INSERT_LIBRARIES',
        'LD_PRELOAD','LD_AUDIT','GLIBC_TUNABLES','MALLOC_ARENA_MAX','MALLOC_ARENA_TEST',
        'MALLOC_CHECK_','MALLOC_PERTURB_','MALLOC_MMAP_THRESHOLD_','MALLOC_TRIM_THRESHOLD_',
        'MALLOC_TOP_PAD_','MALLOC_MMAP_MAX_']
    native_environment={name:value for name,value in sorted(env.items())
        if name.startswith(tuple(environment_prefixes)) or name in environment_exact}
    for name in environment_exact:native_environment.setdefault(name,None)
    environment_scope={'format':'swdb.native-environment.v1','prefixes':environment_prefixes,
        'exact_variables':environment_exact,'absence_semantics':'null_or_absent_is_unset_under_declared_scope'}
    native_runtime = {'compiler_version': _run([llvm / 'clang++', '--version']).stdout.strip(),
        'compiler_sha256': _sha((llvm / 'clang++').resolve()),
        'environment': native_environment,'environment_scope':environment_scope, 'loaded_libraries': native_libraries,
        'observation_method': 'process_loaded_images', 'scope': 'counted_instrumented_binary',
        'missing': native_missing}
    if 'memory_service_counts' in counts:
        record['counting']['observation_format']='swdb.live-count-context.v1'
        record['observation_contract']={'format':'swdb.live-count-context.v1',
            'level':'source_normalized_ir','abi':'swdb.access.v2','call_abi':'swdb.call.v2',
            'line_bytes':64,'page_bytes':4096,'state_budget':args.state_budget,
            'object_scope':'translation_unit_allocator_calls',
            'first_access_scope':'first observed access in selected normalized source functions; opaque initialization is not observed',
            'physical_residency_known':False,'native_runtime':native_runtime,
            'observer_isolation':'thread_local_reentrancy_guard',
            'runtime_bundle_sha256':artifacts.digest({name:_sha(llvm_src/name)
                for name in ('CountingRuntime.cpp','LiveObjects.hpp','LogicalCommands.hpp')})}
    if args.object_scopes:
        record['observation_contract']['object_scope_contract']={
            'format':'swdb.object-scopes.v1','abi':'swdb.object-scope.v1',
            'full_objects':['heap','source_alloca','defined_global_non_tls'],'bounded_views':['openmp_microtask_int32_referent'],
            'retirement':'frame_exit_lifetime_end_stackrestore',
            'observer_sha256':_sha(llvm_src/'ObjectScopes.hpp'),
            'runtime_sha256':_sha(llvm_src/'ObjectScopeRuntime.hpp')}
    if live_contract:
        from swdb.analytic_count_reuse import policy_sha256,POLICY_FORMAT
        command_specs=live_contract['functional_observation']['commands']
        observed_descriptors={site['descriptor'] for site in static.get('semantic_sites',[])}
        semantic_missing=counts.get('semantic_missing',[])
        if observed_descriptors!=set(range(len(command_specs))):semantic_missing=semantic_missing+['semantic_command_binding']
        if live_contract.get('normative_bindings') is not None:
            record['observation_contract']['normative_bindings']=live_contract['normative_bindings']
        record['observation_contract'].update(level='functional_semantic_access',
            functional_observation=live_contract['functional_observation'],
            counted_target_description_snapshot=live_contract['counted_target_description_snapshot'],
            target_observation_policy_format=POLICY_FORMAT,
            target_observation_policy_sha256=policy_sha256(live_contract['counted_target_description_snapshot']),
            requested_target_description_sha256=live_contract['target_description_sha256'],
            dram_address_layout=live_contract['dram_address_layout'],
            host_counting_policy='exclusive_host_outside_guarded_functional_commands',
            observer_bundle_sha256=artifacts.digest({name:_sha(llvm_src/name) for name in ('Characterize.cpp','SemanticCommands.hpp')}),
            semantic_commands={'complete':not semantic_missing,'event_ids':[command['event'] for command in command_specs],'missing':semantic_missing})
    if trials:
        record['trials'] = trials
    if adapter:
        record['binding']['note'] = 'Registered source excerpts, input generator and original timed kernel lambda verified; each trial and SourcePicker selection retained.'
        record['coverage']['ambiguous_helper_loops'] = adapter['ambiguous_helper_loops']
        record['pattern_comparison'] = [] if args.adapter=='registered-functional' else analytic_binding.compare_patterns(subject_record, regions, adapter['ambiguous_helper_loops'], adapter['mapping']['regions'])
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


def _estimate_regions(source_regions, source_calls, target, observation_contract=None, *, characterization=None,count_reuse=None):
    from swdb import analytic_models

    characterization_sha256=artifacts.digest(characterization) if characterization else None
    regions = []
    for region in source_regions:
        called = [c for c in source_calls if c.get('region') == region['id']]
        context = {'target_description_sha256': artifacts.digest(target),
            'logical_count_target_description_sha256':count_reuse['counted_target_description_sha256'] if count_reuse else artifacts.digest(target),
            'configured_threads': target['threads'], 'observation_contract': observation_contract,
            'characterization_id': characterization['id'] if characterization else None,
            'characterization_sha256': characterization_sha256,
            'selected_domain': None, 'composition_contract': target.get('composition_contract'),
            'source_calls': called}
        bounds, overheads = [], []
        covered = set()
        for mechanism in target['mechanisms']:
            result = analytic_models.evaluate(region, mechanism,
                [m['model'] for m in target['mechanisms']], target['threads'], context=context)
            (overheads if mechanism.get('accounting', 'resource_bound') == 'additive_overhead' else bounds).append(result)
            if result['seconds'] is not None:
                for claim in result['inputs'].get('covered_calls', []):
                    for call in called:
                        count = call.get('execution_count', {}).get('value')
                        if (claim.get('site') == call.get('site') and type(count) is int
                            and count >= 0 and claim.get('execution_count') == count):
                            covered.add(call['site'])
        uncovered = [c for c in called if c.get('execution_count', {}).get('value') != 0
                     and _uncovered_call(c) and c.get('site') not in covered]
        if uncovered:
            bounds.append(analytic_models.bound('unmodeled_calls', None,
                'sum(call execution count * call cost)', {'calls': uncovered},
                ['call_cost.' + c['name'] for c in uncovered]))
        unknown = any(b['seconds'] is None for b in bounds + overheads)
        seconds = None if unknown else max((b['seconds'] for b in bounds), default=0.) + sum(b['seconds'] for b in overheads)
        limiting = None if unknown or not bounds else max(bounds, key=lambda b: b['seconds'])['model']
        regions.append({'id': region['id'], 'seconds': seconds, 'basis': 'estimated',
            'bounds': bounds, 'overheads': overheads, 'limiting_bound': limiting,
            'state': 'unknown' if unknown else 'known'})
    seconds = None if any(r['seconds'] is None for r in regions) else sum(r['seconds'] for r in regions)
    return regions, seconds


def estimate(args):
    from swdb import analytic_models
    store = Store(args.records)
    characterization = _load(store, args.characterization, 'workload_characterization')
    target = _load(store, args.target_description, 'target_description')
    from swdb.offload_observation import binding_problems
    issues=binding_problems(characterization,store)
    if issues:raise Failure('functional source binding: '+'; '.join(issues))
    from swdb.archevolve import require_team_safe
    from swdb.estimate_protocol import bind
    require_team_safe(store, characterization, target, args.protocol, command='estimate')
    protocol = bind(store, args.protocol, characterization, target)
    if target['threads'] != characterization['binding']['threads']:
        raise Failure('target thread count differs from the counted workload thread identity')
    from swdb.analytic_count_reuse import resolve
    count_reuse=resolve(characterization,target)
    regions, seconds = _estimate_regions(characterization['regions'], characterization['unmodeled_calls'], target, characterization.get('observation_contract'),characterization=characterization,count_reuse=count_reuse)
    trial_estimates=[]
    for trial in characterization.get('trials',[]):
        rows,total=_estimate_regions(trial['regions'],trial['unmodeled_calls'],target,characterization.get('observation_contract'),characterization=characterization,count_reuse=count_reuse)
        trial_estimates.append({'position':trial['position'],'sources':trial['sources'],'regions':rows,'seconds':total})
    if trial_estimates:
        seconds=None if any(t['seconds'] is None for t in trial_estimates) else statistics.median(t['seconds'] for t in trial_estimates)
        lookups=[{r['id']:r for r in t['regions']} for t in trial_estimates]
        for row in regions:
            sequence=[index.get(row['id']) for index in lookups]
            values=[r['seconds'] if r else 0. for r in sequence]
            row['seconds']=None if any(v is None for v in values) else statistics.median(values)
            row['state']='unknown' if row['seconds'] is None else 'known'
            for field in ('bounds', 'overheads'):
                templates={b['model']:b for b in row[field]}
                for r in sequence:
                    if r:
                        for b in r[field]:templates.setdefault(b['model'],copy.deepcopy(b))
                row[field]=list(templates.values())
                for bound in row[field]:
                    bs=[next((b for b in r[field] if b['model']==bound['model']),None) if r else None for r in sequence]
                    values=[b['seconds'] if b else 0. for b in bs]
                    bound['seconds']=None if any(v is None for v in values) else statistics.median(values)
                    bound['state']='unknown' if bound['seconds'] is None else 'known'
                    bound['missing']=sorted({m for b in bs if b for m in b['missing']})
                    bound['notes']=list(bound.get('notes',[]))+['Per-region component summary is the median across independent trial estimates.']
            row['limiting_bound']=None if row['seconds'] is None or not row['bounds'] else max(row['bounds'],key=lambda b:b['seconds'])['model']
    record = _envelope('estimate', args.id, 'Analytic mechanism bounds from compiler/counting facts and frozen target parameters; no target timing.')
    record.update({'format': 'swdb.estimate.v1', 'basis': 'estimated', 'estimator_version': VERSION,
        'estimator_sha256': protocol['settings']['estimator_sha256'],
        'protocol_sha256': protocol['identity_sha256'],
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
                  'Total sums exclusive region resource maxima plus declared additive overheads. Any required unknown makes its region and total unknown.']})
    if trial_estimates:
        record['trials'] = trial_estimates
        record['summary'] = 'median_whole_call_seconds'
        record['notes'].append('Estimate each trial by summing exclusive region maxima; the reported total is the median whole-call trial time. Per-region medians are diagnostic and do not generally sum to that median.')
    if count_reuse is not None:record['count_reuse']=count_reuse
    if args.baseline:
        baseline = _load(store, args.baseline, 'estimate')
        require_team_safe(store, baseline, command='estimate')
        required = ('input', 'target_description_sha256', 'protocol', 'protocol_sha256', 'estimator_version', 'estimator_sha256', 'threads', 'evidence_kind')
        if any(baseline.get(k) != record.get(k) for k in required):
            raise Failure('baseline estimate input, target description, protocol, threads or evidence kind differs')
        record['baseline'] = {'id': baseline['id'], 'sha256': artifacts.digest(baseline)}
        if seconds is not None and seconds > 0 and baseline['seconds'] is not None:
            record['ratio'] = baseline['seconds'] / seconds
    from swdb.analytic_extensions import finalize_estimate
    record = finalize_estimate(record, store=store, protocol=protocol,
        characterization=characterization, target_description=target)
    writer.commit(args.records, new=[record])
    return record


def _payload_problems(data):
    """Payload integrity and finite-number checks shared by CLI loading and validate."""
    kind = data['kind']
    if kind == 'workload_characterization':
        from swdb.feature_reports import payload_problems
        yield from payload_problems(data)
        from swdb.offload_observation import count_problems
        yield from count_problems(data)
        from swdb.analytic_count_reuse import snapshot_problems
        yield from snapshot_problems(data)
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
            if 'memory_service_counts' in region:
                memory=region['memory_service_counts']
                counts += [memory[name] for name in ('useful_bytes','lifetime_line_union',
                    'logical_first_read_pages','logical_first_write_pages','pre_roi_allocation_pages',
                    'in_roi_allocation_pages','unknown_object_requests')]
                scope_facts=memory.get('object_scope_counts')
                if scope_facts is not None:
                    field=f'{group}[{i}].memory_service_counts.object_scope_counts'
                    if not data.get('observation_contract',{}).get('object_scope_contract'):
                        yield field,'object scope facts require their sealed optional observation contract'
                    values={name:fact.get('value') for name,fact in scope_facts.items()}
                    if any(value is not None and (not isinstance(value,int) or isinstance(value,bool) or value<0) for value in values.values()):
                        yield field,'object scope counts must be nonnegative integers or null'
                    partition=[values.get(name) for name in ('full_allocation_requests','bounded_view_requests','unresolved_requests')]
                    requests=[item['requests'].get('value') for items in memory['requests_by_update_kind'].values() for item in items]
                    if all(isinstance(value,int) and not isinstance(value,bool) for value in partition+requests):
                        if sum(partition)!=sum(requests):yield field,'scope coverage partition must match executed requests'
                    if values.get('unresolved_requests')!=memory['unknown_object_requests'].get('value'):
                        yield field,'unresolved scope requests must match unknown object requests'
                    if isinstance(values.get('bounded_view_requests'),int) and values['bounded_view_requests']>0:
                        if 'bounded_view_not_full_allocation' not in memory['missing']:
                            yield field,'bounded views must state that full allocation facts remain unknown'
                        if any(memory[name].get('value') is not None for name in ('lifetime_line_union','logical_first_read_pages',
                            'logical_first_write_pages','pre_roi_allocation_pages','in_roi_allocation_pages')):
                            yield field,'bounded views cannot establish full allocation lifetime or page facts'
                counts += list(memory.get('object_scope_counts',{}).values())
                counts += [item['requests'] for items in memory['requests_by_update_kind'].values() for item in items]
            for call in region.get('call_shape_counts',{}).get('calls',[]):
                counts += [call[name] for name in ('execution_count','unknown_lengths','unknown_free_lifetimes')]
                counts += [item['execution_count'] for name in ('known_length_bins','allocation_lifetime_size_bins') for item in call[name]]
            for count in counts:
                value = count.get('value')
                if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0):
                    yield f'{group}[{i}]', 'work counts must be finite nonnegative numbers or null'
    elif kind == 'target_description':
        from swdb.offload_observation import payload_problems
        for message in payload_problems(data):yield 'functional_observation',message
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
    if record.kind == 'workload_characterization':
        from swdb.offload_observation import binding_problems
        for reason in binding_problems(record.data,ctx.store):yield Problem(record.rel,'observation_contract.normative_bindings',reason)
    if record.kind == 'workload_characterization' and record.data.get('binding', {}).get('state') == 'verified':
        from swdb import analytic_binding
        for reason in analytic_binding.verify_binding(record.data, ctx.store):
            yield Problem(record.rel, 'binding', reason)
    if record.kind == 'estimate':
        characterization = ctx.store.get(record.data['characterization'], 'workload_characterization')
        if characterization is not None and artifacts.digest(characterization) != record.data['characterization_sha256']:
            yield Problem(record.rel, 'characterization_sha256', 'characterization record differs from the estimate input hash')

        protocol = ctx.store.get(record.data['protocol'], 'protocol')
        if protocol is None:
            yield Problem(record.rel, 'protocol', 'frozen estimate protocol is missing')
        elif (record.data['protocol_sha256'] != protocol['identity_sha256']
              or record.data['estimator_version'] != protocol['settings'].get('estimator_version')
              or record.data['estimator_sha256'] != protocol['settings'].get('estimator_sha256')
              or record.data['target_description_sha256'] != protocol['settings'].get('target_description', {}).get('sha256')):
            yield Problem(record.rel, 'protocol_sha256', 'estimate identities differ from their frozen protocol')

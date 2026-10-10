"""Functional counting shadow of the protected DX100 BFS call. 2026-10-09 ET.

This closes the invocation/input scope only. It does not register a numerical
adapter or equate software functional execution with MMIO execution. Production
Extensa estimates remain unknown until those separate premises are supported.
"""
import hashlib
import json
import os
import platform
import re
from pathlib import Path
from types import SimpleNamespace

from swdb import artifacts
from swdb.cli import Failure

FORMAT = 'swdb.dx100-functional-call-shadow.v1'
MARKERS = '''extern "C" void __swdb_begin();
extern "C" void __swdb_end();
extern "C" void __swdb_source(unsigned long long);
'''


def _registered(store, value, kind):
    try:
        registered = store.get(value['id'], kind)
        if value.get('kind') != kind or registered is None or artifacts.digest(value) != artifacts.digest(registered):
            raise Failure('functional call shadow ' + kind + ' differs from its registered record')
    except (KeyError, TypeError, ValueError):
        raise Failure('functional call shadow requires a canonical registered ' + kind) from None
    return registered


def driver(source, function, *, sg_offset_bytes):
    """Derive the counting window from the existing evaluator, including its check.

    Remove simulator events rather than executing them on the counting host.
    Graph loading and the independent original-CSR check stay outside the sole
    marked call; the returned parent object stays alive across the end marker.
    """
    from swdb.dx100_candidate import driver as evaluator_driver
    if not isinstance(function, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', function):
        raise Failure('functional call shadow requires one C++ function identifier')
    model = Path('/__swdb_unused_model__')
    text = evaluator_driver(Path(source), model, function, sg_offset_bytes=sg_offset_bytes)
    header = '#include ' + json.dumps(str(model / 'include/gem5/m5ops.h'))
    replacements = {
        header: '#if !defined(FUNC) || defined(GEM5) || defined(GEM5_MAGIC)\n'
                '#error "counting shadow requires the functional backend only"\n#endif\n' + MARKERS,
        '  m5_checkpoint(0, 0);': '',
        '  m5_work_begin(0, 0);': '',
        '  m5_reset_stats(0, 0);': '  __swdb_begin();\n  __swdb_source(static_cast<unsigned long long>(source));',
        '  m5_dump_stats(0, 0);': '  __swdb_end();',
        '  m5_work_end(0, 0);': '',
        '  m5_exit(0);': '',
    }
    for original, replacement in replacements.items():
        # A changed evaluator boundary needs review, never a best-effort match.
        if text.count(original) != 1:
            raise Failure('protected DX100 evaluator boundary changed: ' + original)
        text = text.replace(original, replacement, 1)
    return text


def prepare(store, candidate, workload, source, selected_source):
    """Bind one count-only plan to immutable candidate and registered SG bytes.

    No output is written and no candidate is executed by preparation. Build and
    runtime observations belong to a later count execution; neither this plan
    nor its digest is an execution/certification/admission receipt.
    """
    from swdb.analytic_functional_binding import selected, build_flags
    from swdb.bfs_native import _protect_driver_macros
    from swdb.bfs_native_scalable import resolve_workload
    candidate = _registered(store, candidate, 'candidate')
    workload = _registered(store, workload, 'workload')
    snapshot, context, artifact, protections, relative = selected(store, candidate)
    if artifacts.digest(candidate['context']) != artifacts.digest(context):
        raise Failure('functional call shadow candidate context differs from its source snapshot')
    if (context.get('application') != 'dx100-gapbs' or context.get('function') != 'DOBFS'
            or relative != 'benchmarks/gapbs/src/bfs.cc'):
        raise Failure('functional call shadow supports the registered DX100 DOBFS candidate only')
    observed = resolve_workload(store, {'id': workload['id']}, context['application'])
    if (observed['representation'].get('application') != 'dx100-gapbs'
            or observed['graph_input']['format'] != 'gapbs_sg32le'):
        raise Failure('functional call shadow requires the DX100 SG32 representation')
    if type(selected_source) is not int or not 0 <= selected_source < observed['num_vertices']:
        raise Failure('functional call shadow source is outside the registered graph')
    source = Path(source).resolve()
    if not source.as_posix().endswith('/' + relative):
        raise Failure('functional call shadow source path differs from the registered translation unit')
    root = source.parents[len(Path(relative).parts) - 1]
    actual = artifacts.identify(root)
    if actual['sha256'] != artifact['sha256'] or artifacts.digest(actual['files']) != artifacts.digest(artifact['files']):
        raise Failure('functional call shadow candidate artifact differs')
    artifacts.check_protections(root, protections)
    graph = observed['graph_input']
    text = driver(source, context['function'], sg_offset_bytes=graph['offset_bytes'])
    _protect_driver_macros(candidate, root, extra_text=text)
    flags = build_flags(context, root)
    allowed = {'-std=c++11', '-O3', '-Wall', '-fopenmp', '-pthread', '-DFUNC',
        '-I' + str((root / 'benchmarks/API').resolve()),
        '-I' + str((root / 'benchmarks/gapbs/src').resolve())}
    if '-DFUNC' not in flags or any(flag not in allowed for flag in flags):
        raise Failure('functional call shadow build flags cannot substitute source, headers or protected markers')
    arguments = ['-f', graph['path'], '-r', str(selected_source)]
    scope = {'format': FORMAT, 'candidate': candidate['id'],
        'candidate_record_sha256': artifacts.digest(candidate), 'source_snapshot': snapshot['id'],
        'source_snapshot_record_sha256': artifacts.digest(snapshot),
        'candidate_artifact_sha256': artifact['sha256'], 'application': context['application'],
        'function': context['function'], 'translation_unit_sha256': artifacts.file_hash(source),
        'workload': workload['id'], 'workload_record_sha256': artifacts.digest(workload),
        'canonical_graph_sha256': observed['canonical_sha256'], 'graph_input': graph,
        'num_vertices': observed['num_vertices'],
        'source': selected_source, 'threads': 4, 'roi': 'bfs.complete_call.v1',
        'environment': {'OMP_NUM_THREADS': '4', 'OMP_DYNAMIC': 'FALSE', 'SWDB_ROI_GATED': '1'},
        'run_arguments': arguments, 'functional_build_flags': flags,
        'counting_driver_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'timer_values_used': False, 'mmio_correspondence': 'unknown',
        'numeric_admission': False, 'execution_observed': False}
    return {'source': source, 'driver': text, 'flags': flags, 'run': arguments,
            'scope': scope, 'scope_sha256': artifacts.digest(scope)}


def _counted_result(observed, scope):
    """Admit one observed source window and the evaluator-owned result check."""
    from swdb.analytic import _counted_regions
    counts, static = observed['counts'], observed['static']
    trials = counts.get('trials', [])
    if (not isinstance(trials, list) or len(trials) != 1 or not isinstance(trials[0], dict)
            or artifacts.digest(trials[0].get('sources')) != artifacts.digest([scope['source']])):
        raise Failure('functional call shadow requires exactly one counted source window')
    stdout = observed['executed'].stdout
    results = re.findall(r'^SWDB_BFS_RESULT source=(\d+) vertices=(\d+) parent_count=(\d+) parent_fnv1a64=([0-9a-f]{16})$', stdout, re.M)
    vertices = scope['num_vertices']
    if (len(results) != 1 or tuple(map(int, results[0][:3])) != (scope['source'], vertices, vertices)
            or re.findall(r'^Verification: (PASS|FAIL)$', stdout, re.M) != ['PASS']):
        raise Failure('functional call shadow independent original-graph check failed')
    if not static.get('regions'):
        raise Failure('functional call shadow has no counted source regions')
    regions, calls = _counted_regions(static, trials[0], count_scope='per_trial')
    return {'sources': trials[0]['sources'], 'regions': regions, 'unmodeled_calls': calls,
            'parent_fnv1a64': results[0][3]}


def execute(store, candidate, workload, source, selected_source, output, *, llvm_bin=None,
            timeout_s=120, state_budget=524288):
    """Run the existing protected LLVM pipeline; return count-only observations.

    This internal path writes external raw artifacts and a compact receipt. It
    does not register a characterization, certify a candidate, consume outcome
    timings or establish functional/MMIO or numerical correspondence.
    """
    from swdb import analytic
    from swdb.analytic_cpu_binding import controls
    if (type(timeout_s) not in (int, float) or not 0 < timeout_s <= 600
            or type(state_budget) is not int or not 0 < state_budget <= 524288):
        raise Failure('functional call shadow requires bounded timeout and state budget')
    plan = prepare(store, candidate, workload, source, selected_source)
    injection = ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'OBJC_INCLUDE_PATH',
                 'COMPILER_PATH', 'GCC_EXEC_PREFIX', 'LIBRARY_PATH', 'CCC_OVERRIDE_OPTIONS',
                 'LD_PRELOAD', 'LD_AUDIT', 'DYLD_INSERT_LIBRARIES', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH')
    if (any(os.environ.get(name) for name in injection)
            or any(name.startswith('SWDB_') and name != 'SWDB_LLVM_BIN' for name in os.environ)):
        raise Failure('functional call shadow refuses ambient compiler/observer/library substitutions')
    llvm, version = analytic._llvm_bin(llvm_bin)
    llvm = llvm.resolve()
    output = Path(output).resolve()
    root = plan['source'].parents[3]
    if output.exists() or output.is_relative_to(root) or Path(plan['scope']['graph_input']['path']).is_relative_to(output):
        raise Failure('functional call shadow requires a new output outside candidate and graph input')
    observer = Path(analytic.__file__).with_name('llvm')
    inputs = [plan['source'], Path(plan['scope']['graph_input']['path']), Path(__file__), Path(analytic.__file__),
              Path(__file__).with_name('analytic_llvm_support.py'),
              *(observer.glob('*.cpp')), *(observer.glob('*.hpp')),
              *(llvm / name for name in ('clang++', 'opt', 'llvm-config'))]
    pinned = {str(path.resolve()): artifacts.file_hash(path) for path in inputs}
    artifacts.external_directory(output)
    wrapper = output / 'counting_driver.cc'; wrapper.write_text(plan['driver'])
    # Runtime control comes only from this exact plan. Stale observer controls
    # never enter a fresh execution; shared stages retain their original recipe.
    env = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR', 'TEMP', 'TMP') if key in os.environ}
    env.update(plan['scope']['environment'])
    env['LD_LIBRARY_PATH' if platform.system() != 'Darwin' else 'DYLD_LIBRARY_PATH'] = str(llvm.parent / 'lib')
    args = SimpleNamespace(run_library_path=[llvm.parent / 'lib'], timeout_s=timeout_s,
        function=None, region_map=None, object_scopes=False, counting_pipeline='source-normalized-v2',
        threads=4, state_budget=state_budget, run_arg=plan['run'])
    build_env = {'PATH': '/usr/bin:/bin', 'TMPDIR': str(output)}
    toolchain_flags = ['--no-default-config']
    sdk = None
    if platform.system() == 'Darwin':
        sdk = Path(analytic._run(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=build_env).stdout.strip()).resolve()
        if not sdk.is_dir() or not (sdk / 'SDKSettings.json').is_file():
            raise Failure('functional call shadow requires an explicit installed macOS SDK')
        toolchain_flags.extend(['-isysroot', str(sdk)])
        pinned[str(sdk / 'SDKSettings.json')] = artifacts.file_hash(sdk / 'SDKSettings.json')
    observed = analytic._execute_counts(args, adapter={'explicit_roi': True, 'environment': env,
        'build_environment': build_env},
        output=output, live_contract=None, llvm=llvm, source=wrapper, flags=plan['flags'],
        toolchain_flags=toolchain_flags, subject=candidate['id'])
    payload = _counted_result(observed, plan['scope'])
    # Paths are observed by the child, but these hashes are from after exit.
    # They cannot prove loaded byte continuity, even when all files still exist.
    libraries, missing = {}, ['runtime_library_byte_continuity']
    for path in observed['counts'].get('loaded_images', []):
        library = Path(path).resolve()
        digest = artifacts.file_hash(library) if library.is_file() else None
        libraries[str(library)] = digest
        if digest is None:
            missing.append('loaded_library_hash:' + str(library))
    if not libraries:
        missing.append('process_loaded_images')
    files = {name: {'sha256': artifacts.file_hash(output / name), 'bytes': (output / name).stat().st_size}
        for name in ('counting_driver.cc', 'Characterize.so', 'optimized.bc', 'source.bc',
                     'normalized.bc', 'instrumented.bc', 'counted', 'source.json', 'optimized.json',
                     'counts.json', 'stdout.txt', 'stderr.txt')}
    receipt = {'format': 'swdb.dx100-functional-count-execution.v1', 'scope': plan['scope'],
        'scope_sha256': plan['scope_sha256'], 'execution_observed': True, 'numeric_admission': False,
        'mmio_correspondence': 'unknown', 'timer_values_used': False,
        'host': {'architecture': platform.machine(), 'system': platform.platform()},
        'llvm_version': version, 'compiler_version': analytic._run([llvm / 'clang++', '--no-default-config', '--version'], env=build_env).stdout.strip(),
        'build_environment': build_env, 'toolchain_flags': toolchain_flags,
        'macos_sdk': str(sdk) if sdk else None,
        'pinned_inputs': pinned, 'pipeline': args.counting_pipeline,
        'passes': analytic.PIPELINES[args.counting_pipeline], 'state_budget': state_budget,
        'environment': controls(observed['env']),
        'observed_loaded_image_paths': sorted(libraries),
        'post_run_library_file_hashes': libraries, 'runtime_missing': missing,
        'plugin_linkage': observed['plugin_linkage'], 'plugin_support_objects': observed['plugin_support_objects'],
        'artifacts': files, 'counted_payload_sha256': artifacts.digest(payload),
        'coverage': 'selected normalized source functions; opaque callees remain unmodeled',
        'correctness': 'evaluator-owned independent original-CSR check passed; not certification'}
    fresh = prepare(store, candidate, workload, source, selected_source)
    if (fresh['scope_sha256'] != plan['scope_sha256']
            or any(artifacts.file_hash(Path(path)) != digest for path, digest in pinned.items())
            or artifacts.file_hash(wrapper) != plan['scope']['counting_driver_sha256']
            or any(artifacts.file_hash(output / name) != descriptor['sha256']
                   or (output / name).stat().st_size != descriptor['bytes'] for name, descriptor in files.items())):
        raise Failure('functional call shadow source/input/compiler/observer/artifacts changed during counting')
    receipt['identity_sha256'] = artifacts.digest(receipt)
    (output / 'receipt.json').write_text(json.dumps(receipt, sort_keys=True) + '\n')
    return {'receipt': receipt, 'payload': payload}

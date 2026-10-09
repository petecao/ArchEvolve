"""Functional counting shadow of the protected DX100 BFS call. 2026-10-09 ET.

This closes the invocation/input scope only. It does not register a numerical
adapter or equate software functional execution with MMIO execution. Production
Extensa estimates remain unknown until those separate premises are supported.
"""
import hashlib
import json
import re
from pathlib import Path

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
        'source': selected_source, 'threads': 4, 'roi': 'bfs.complete_call.v1',
        'environment': {'OMP_NUM_THREADS': '4', 'OMP_DYNAMIC': 'FALSE', 'SWDB_ROI_GATED': '1'},
        'run_arguments': arguments, 'functional_build_flags': flags,
        'counting_driver_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'timer_values_used': False, 'mmio_correspondence': 'unknown',
        'numeric_admission': False, 'execution_observed': False}
    return {'source': source, 'driver': text, 'flags': flags, 'run': arguments,
            'scope': scope, 'scope_sha256': artifacts.digest(scope)}

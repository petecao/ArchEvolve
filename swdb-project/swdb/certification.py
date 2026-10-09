"""Executable DX100 library and kernel candidate certification (2026-10-03 ET).

This is finite strict-functional evidence, never target timing or a formal proof.
Controls count only after compilation and a named runtime rejection.
Updated: 2026-10-06 ET (record reads use the shared access layer).

Ticket 42 (2026-10-03 ET): a candidate's matrix instance and pass rule come from
the kernel plug-in named by its rewrite contract's correctness check
(``swdb.kernels``). BFS keeps the functions below; BC adds its own.

Ticket 70 (2026-10-04 ET, certify 1.3): candidate artifacts are certified by
:func:`certify_candidate` with the isolation of ``swdb.certification_isolation``; no candidate
verdict is read from printed output.

Updated 2026-10-05 ET (code-review fixes F1-F5, F10, C10; agent-decided under Yan-Ru's delegation,
revisable): every certify path takes its version's behavior from one frozen table per command family
(``swdb.certification_procedures``), records the per-version source manifest, the git commit, the
command family and the evidence basis of its path (ADR 0008: ``measured`` for native-CPU runs), and
raises on an unknown version. Lowerings and calibration are their own family (version 1.1).
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import struct
import subprocess
import uuid
import tempfile
import time
from collections import deque

from swdb import artifacts, paths, workflow
from swdb import certification_common as common
from swdb import certification_procedures as procedures
from swdb.cli import Failure, UsageError
from swdb.store import Store

# 1.1 (2026-10-04 ET, ticket 67): forged_frontier control version 2 (control records carry
# `fault.version`). Records with command version 1.0 used forged_frontier version 1.
# 1.2 (2026-10-04 ET, ticket 68): knob_range and schedule_range checks and their controls
# (swdb.certification_legality); records before 1.2 report neither.
# 1.3 (2026-10-04 ET, ticket 70): candidate-artifact certification is isolated
# (swdb.certification_isolation): every named check is computed out of process from evaluator
# records on an evaluator-opened descriptor, the kernel's result comes from an evaluator-owned main,
# faults live in a separately compiled object linked to one unchanged candidate object, and a
# evaluator scan refuses candidate text naming evaluator symbols. Records before 1.3 read named checks
# from stdout/stderr and selected faults with a macro in the candidate's translation unit; they
# keep that meaning. Lowering certification and calibration are unchanged.
# 1.4 (2026-10-05 ET, ticket 76; agent-decided under Yan-Ru's delegation, revisable): candidate
# artifacts are certified by swdb.certification_blinding. Per tile size the positive matrix and every
# library-fault control run one binary; the fault arrives in a blinded run plan; all runs take a
# random order; a library-fault control is rejected only when its check is attributable to the
# fault's own action; windows are read from the queue at each slide; positive runs must pass the
# seam witness (contract clause L4). Records of 1.3 and earlier keep their meaning, and
# `certify(..., version='1.3')` (CLI `--command-version 1.3`) still runs 1.3 unchanged.
# Lowering certification and calibration certify only evaluator-pinned trusted code (ticket 76) and
# are unchanged.
# Ticket 75 (2026-10-05 ET, merged after ticket 76): native-CPU candidate certification for a rewrite
# contract that pins a native candidate profile (swdb.certification_native, library/native/). Under
# version 1.3 it uses 1.3's isolation (one candidate object per build, one seam object per fault, a
# frontier hook before DOBFS's protected print); under 1.4 it uses 1.4's blinding (one binary, a
# blinded plan, random order, attributed rejections, the slide-window events and the seam witness).
# certification.b7954f4df9dd4e228fb12437b845f190 was written on the ticket 75 branch before this merge,
# when that branch numbered its 1.3-isolation native path "1.4"; its sources_sha256 06fe4cc5... names
# that code. `--candidate-record` binds a snapshot-plus-patch certification to an Extensa candidate
# record whose artifact sha256 equals the patched tree.
# 1.5 (2026-10-05 ET, ticket 78; scope decided by Yan-Ru 2026-10-05, engineering refactor): candidate
# artifacts are certified by swdb.certification_process. The record writer, the run plan, the fault
# logic, the seam-witness events and the strict model's state run in a trusted evaluator process; the
# candidate runs as its child, with its C++ heap in a shared arena, and reaches every seam and
# strict-layer call by a request to the evaluator. Procedure, record format, judge, attribution and
# scan are 1.4's. Records of 1.4 and earlier keep their meaning; 1.3 and 1.4 stay selectable.
# 1.6 (2026-10-05 ET, code-review fixes C4, C24; agent-decided under Yan-Ru's delegation, revisable):
# 1.5 with knob_range reading every declared spelling of a knob that the candidate uses (SWDB_KNOB_<NAME>
# and SWDB_<NAME>; "unverified", never the contract default, when none is used) and the
# schedule_out_of_range control also mutating _Pragma forms. 1.3-1.5 keep the ticket 68 rules.
# The version table (one per command family, with each version's files and frozen digest) is
# swdb.certification_procedures; VERSION and VERSIONS name the candidate family's default and versions.
VERSION = procedures.DEFAULTS[procedures.CANDIDATE]
VERSIONS = tuple(procedures.PROCEDURES[procedures.CANDIDATE])
ROOT = paths.HOME
BFS = 'benchmarks/gapbs/src/bfs.cc'
HEADER = 'benchmarks/gapbs/src/swdb_dxc_lowering.hpp'
DEFAULT_SNAPSHOT = 'bfs-dx100-scalar-only-20260929-a1.source'
OPERATIONS = ('gather', 'session_begin', 'thread_context', 'const_i32', 'wait',
              'range_loop', 'stream_load', 'tile_size', 'tile_pointer', 'alu_scalar')
COMMON_CONTROLS = {'shared_context': 'thread_ownership_tile',
                   'other_thread_register': 'thread_ownership_register',
                   'second_session_begin': 'session_begin_twice',
                   'dropped_wait': 'read_before_wait', 'read_before_wait': 'reference_semantics'}
CONTROLS = {
    'gather': {**COMMON_CONTROLS, 'index_wrap': 'byte_offset_overflow', 'memory_region': 'memory_region'},
    'session_begin': {'second_session_begin': 'session_begin_twice'},
    'thread_context': {'shared_context': 'thread_ownership_tile', 'other_thread_register': 'thread_ownership_register'},
    'const_i32': {'other_thread_register': 'thread_ownership_register', 'constant_uncovered': 'constant_uncovered_register'},
    'wait': {'dropped_wait': 'read_before_wait', 'read_before_wait': 'reference_semantics', 'constant_uncovered': 'constant_uncovered_register'},
    'range_loop': {'dropped_continuation': 'range_continuation', 'index_wrap': 'byte_offset_overflow', 'dropped_wait': 'read_before_wait'},
    'stream_load': {'truncation': 'tile_truncation', 'memory_region': 'memory_region', 'constant_uncovered': 'constant_uncovered_register'},
    'tile_size': {'dropped_wait': 'read_before_wait'},
    'tile_pointer': {'read_before_wait': 'reference_semantics'},
    'alu_scalar': {'dropped_wait': 'read_before_wait'},
    'store': {'wrong_store_wait': 'read_before_wait'},
}
FRONTIER_TEXT = 'std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;'
AUTHOR_FRONTIER_TEXT = 'std::cout << "Starting TDStepMAA: " << queue.size() << " elements" << std::endl;'
TRUSTED_FRONTIER = r'''
// Evaluator-owned preservation check, inserted into a private build copy (calibration only since
// certify 1.3; candidates record the window through library/dx100/certification/record.cc).
template<class Queue> void swdb_certification_frontier(const Queue& queue) {
 std::set<int32_t> unique;
 for(size_t i=queue.shared_out_start;i<queue.shared_out_end;++i)
  if(!unique.insert(queue.shared[i]).second){
   std::fprintf(stderr,"SWDB_PRESERVATION_FAIL:duplicate_frontier\n");std::_Exit(88);
  }
 std::printf("SWDB trusted_frontier=%llu\n",(unsigned long long)queue.size());
}
'''


def compiler():
    selected = os.environ.get('SWDB_CERTIFY_CXX')
    if selected:
        found = shutil.which(selected)
        if not found:
            raise Failure('SWDB_CERTIFY_CXX does not name an available compiler')
        return found
    for name in ('g++-16', 'g++-15', 'g++-14', 'g++'):
        found = shutil.which(name)
        if found and ('homebrew' in found or platform.system() != 'Darwin'):
            return found
    raise Failure('certification requires GCC with OpenMP (set SWDB_CERTIFY_CXX)')


def execute(command, log, *, cwd=None, threads=4, timeout=180, extra_env=None, pass_fds=()):
    environment = {**os.environ, 'OMP_NUM_THREADS': str(threads), 'OMP_DYNAMIC': 'FALSE', **(extra_env or {})}
    started = time.monotonic()   # ticket 78: wall time of every command (overhead measurement)
    try:
        process = subprocess.run([str(x) for x in command], cwd=cwd, env=environment,
                                 capture_output=True, text=True, timeout=timeout, pass_fds=tuple(pass_fds))
        result = {'command': [str(x) for x in command], 'returncode': process.returncode,
                  'stdout': process.stdout, 'stderr': process.stderr, 'timeout': False}
    except subprocess.TimeoutExpired as exc:
        result = {'command': [str(x) for x in command], 'returncode': None,
                  'stdout': (exc.stdout or b'').decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ''),
                  'stderr': (exc.stderr or b'').decode() if isinstance(exc.stderr, bytes) else (exc.stderr or ''), 'timeout': True}
    result['seconds'] = round(time.monotonic() - started, 4)
    Path(log).write_text(json.dumps(result, indent=2) + '\n')
    result['log'] = str(Path(log).resolve())
    return result


def rejection(result, expected):
    if result['timeout']:
        return 'invalid', 'timeout'
    named = re.findall(r'SWDB_(?:STRICT_ASSERT|DIFFERENTIAL_MISMATCH|PRESERVATION_FAIL):([a-z_]+)',
                       result['stdout'] + result['stderr'])
    if result['returncode'] != 0 and expected in named:
        return 'rejected', expected
    if result['returncode'] == 0:
        return 'survived', 'all checks passed'
    return 'invalid', 'process failed without expected named check'


def compile_cpp(source, output, library, *, tile_size, threads, tree=None, defines=()):
    model = tree or ROOT / 'apps/dx100'
    command = [compiler(), '-std=c++11', '-O1', '-g', '-fopenmp', '-DFUNC', '-DGEM5',
               f'-DTILE_SIZE={tile_size}', f'-DNUM_CORES={threads}',
               '-I' + str(library / 'dx100/strict'), '-I' + str(library / 'dx100'),
               '-I' + str(model / 'benchmarks/API'), '-I' + str(model / 'include'),
               *defines, str(source), '-o', str(output)]
    return execute(command, output.with_suffix('.build.json'), timeout=180)


def preprocess_cpp(source, output, library, *, tile_size, threads, tree=None, defines=(), quote_dir=None):
    """The compile_cpp command with -E: the preprocessed text the build would compile (ticket 68)."""
    model = tree or ROOT / 'apps/dx100'
    command = [compiler(), '-std=c++11', '-E', '-fopenmp', '-DFUNC', '-DGEM5',
               f'-DTILE_SIZE={tile_size}', f'-DNUM_CORES={threads}',
               *(['-iquote', str(quote_dir)] if quote_dir else []),
               '-I' + str(library / 'dx100/strict'), '-I' + str(library / 'dx100'),
               '-I' + str(model / 'benchmarks/API'), '-I' + str(model / 'include'),
               *defines, str(source), '-o', str(output)]
    return execute(command, Path(str(output) + '.json'), timeout=180)


def legality_checks(text, source_path, label, library, entry, folder, *, tile_size, threads, tree, defines,
                    rules='v1'):
    """knob_range and schedule_range on one private build copy (ticket 68, 2026-10-04 ET).

    The text is preprocessed exactly as its build would be, from a probe copy outside the tree
    (quoted includes resolve from the source's own directory), so the tree identity is untouched.
    ``rules`` is the procedure's legality rule set (v2 from certify 1.6: every declared knob spelling).
    """
    from swdb import certification_legality as legality
    candidate_text = text
    probe = (folder / f'{label}.legality.cc').resolve()
    probe.write_text(legality.probe_source(text, entry, rules=rules))
    output = folder / f'{label}.legality.ii'
    result = preprocess_cpp(probe, output, library, tile_size=tile_size, threads=threads, tree=tree,
                            defines=defines, quote_dir=source_path.parent)
    if result['returncode']:
        return [{'check': name, 'status': 'invalid', 'problems': ['preprocessing failed'], 'log': result['log']}
                for name in legality.CHECKS]
    text = output.read_text()
    knobs_ok, knob_problems, knobs = legality.knob_check(text, entry, tile_size, rules=rules, source=candidate_text)
    schedule_ok, schedule_problems, schedules = legality.schedule_check(text, entry, tile_size, str(probe))
    output.unlink()  # large; the probe source and the command log stay
    return [{'check': legality.KNOB_RANGE, 'status': 'passed' if knobs_ok else 'failed',
             'problems': knob_problems, 'knobs': knobs},
            {'check': legality.SCHEDULE_RANGE, 'status': 'passed' if schedule_ok else 'failed',
             'problems': schedule_problems, 'schedules': schedules}]


def _legality_failures(static):
    """(failed check names, any invalid) of one build's legality checks."""
    static = static or []
    return ([s['check'] for s in static if s['status'] == 'failed'],
            any(s['status'] == 'invalid' for s in static))


def operation_of(entry_id):
    for op in sorted(OPERATIONS, key=len, reverse=True):
        if f'dxc_{op}.' in entry_id or entry_id == f'intrinsic.dxc_{op}':
            return op
    raise Failure('entry has no supported DX100 differential-test operation: ' + entry_id)


def lowering_build(entry_id, library, tile_sizes, threads):
    """Bind a supported driver invocation to this lowering's normative pins."""
    from swdb.library import Library
    catalog = Library(library)
    entry = catalog.get(entry_id)
    if not entry or entry.get('kind') != 'lowering':
        raise UsageError('DX100 differential certification requires a lowering entry; certify each intrinsic lowering')
    try:
        operation = operation_of(entry['intrinsic'])
        intrinsic = catalog.get(entry['intrinsic'])
        header = catalog.resolve(entry['location'])
        driver = catalog.resolve(entry['differential_test'])
        reference = catalog.resolve(intrinsic['reference_semantics'])
    except (ValueError, KeyError, TypeError, Failure) as exc:
        raise UsageError('unsupported or unresolved DX100 lowering inputs: ' + str(exc)) from None
    if entry['location'].get('symbol') != '__dxc_' + operation:
        raise UsageError('lowering symbol does not match the supported differential operation')
    if intrinsic['reference_semantics'].get('symbol') != operation:
        raise UsageError('reference symbol does not match the supported differential operation')
    for path, digest in ((header, entry['code_sha256']), (driver, entry['differential_test']['sha256']),
                         (reference, intrinsic['reference_semantics']['sha256'])):
        if artifacts.file_hash(path) != digest:
            raise UsageError('lowering certification source pin differs from bytes: ' + str(path))
    driver_text = driver.read_text()
    if any(driver_text.count('#include ' + seam) != 1
           for seam in ('SWDB_DXC_LOWERING_HEADER', 'SWDB_DXC_REFERENCE_HEADER')):
        raise UsageError('unsupported differential driver: requires the pinned lowering/reference include seams')
    expected_inputs = {'operation': operation, 'seeds': [0], 'tile_sizes': list(tile_sizes),
                       'threads': threads, 'indices': ['repeated', 'zero', 'tail'],
                       'long_rows': operation == 'range_loop'}
    declared_inputs = entry['differential_test'].get('input_set')
    if not isinstance(declared_inputs, dict):
        raise UsageError('unsupported differential input_set')
    normalized_inputs = dict(declared_inputs)
    declared_sizes = normalized_inputs.get('tile_sizes')
    if not isinstance(declared_sizes, list) or any(type(s) is not int for s in declared_sizes):
        raise UsageError('unsupported differential input_set tile_sizes')
    normalized_inputs['tile_sizes'] = sorted(declared_sizes)
    expected_inputs['tile_sizes'] = sorted(expected_inputs['tile_sizes'])
    if (normalized_inputs != expected_inputs or
            type(normalized_inputs.get('threads')) is not int or
            type(normalized_inputs.get('long_rows')) is not bool or
            any(type(seed) is not int for seed in normalized_inputs.get('seeds', []))):
        raise UsageError('unsupported differential input_set; the driver supports only its declared deterministic DX100 cases')
    definitions = entry['build_defines']
    if not isinstance(definitions, dict) or set(definitions) - {'strict', 'tile_sizes', 'core_count', 'defines'}:
        raise UsageError('unsupported lowering build_defines')
    strict = definitions.get('strict')
    if (not isinstance(strict, list) or
            any(not isinstance(flag, str) or not re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', flag) for flag in strict) or
            not {'FUNC', 'GEM5', 'SWDB_STRICT'} <= set(strict) or
            {'NUM_CORES', 'TILE_SIZE', 'SWDB_DXC_LOWERING_HEADER', 'SWDB_DXC_REFERENCE_HEADER'} & set(strict)):
        raise UsageError('lowering build_defines must enable FUNC, GEM5 and SWDB_STRICT')
    build_sizes = definitions.get('tile_sizes')
    if (type(definitions.get('core_count')) is not int or definitions.get('core_count') != threads or
            not isinstance(build_sizes, list) or any(type(s) is not int for s in build_sizes) or
            sorted(build_sizes) != sorted(tile_sizes)):
        raise UsageError('lowering build_defines matrix differs from the requested full tile/core matrix')
    extra = definitions.get('defines', {})
    reserved = {'FUNC', 'GEM5', 'SWDB_STRICT', 'NUM_CORES', 'TILE_SIZE',
                'SWDB_DXC_LOWERING_HEADER', 'SWDB_DXC_REFERENCE_HEADER'}
    if not isinstance(extra, dict):
        raise UsageError('lowering build_defines.defines must be a macro mapping')
    flags = ['-D' + name for name in strict]
    for name, value in sorted(extra.items(), key=lambda item: str(item[0])):
        if (not isinstance(name, str) or not re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', name) or
                name in reserved or type(value) not in (int, str, bool) or
                isinstance(value, str) and any(ch in value for ch in ('\n', '\r', '\0'))):
            raise UsageError('unsupported or reserved lowering macro definition: ' + str(name))
        flags.append('-D' + name + '=' + (str(int(value)) if isinstance(value, bool) else str(value)))
    flags.extend(['-DSWDB_DXC_LOWERING_HEADER=' + json.dumps(str(header)),
                  '-DSWDB_DXC_REFERENCE_HEADER=' + json.dumps(str(reference))])
    return operation, driver, flags, {'lowering': str(header), 'driver': str(driver),
                                     'reference': str(reference), 'input_set': declared_inputs,
                                     'build_defines': definitions,
                                     'source_pins': [{'path': str(header), 'sha256': entry['code_sha256']},
                                                     {'path': str(driver), 'sha256': entry['differential_test']['sha256']},
                                                     {'path': str(reference), 'sha256': intrinsic['reference_semantics']['sha256']}]}


def certify_lowering(entry_id, library, folder, tile_sizes, threads):
    """Differential certification of one lowering entry against its reference semantics.

    Ticket 76 (2026-10-05 ET): this reads verdict lines (`SWDB_DIFFERENTIAL_PASS`, named checks)
    from the driver's output. That is sound only because every byte it runs is evaluator-trusted:
    the lowering header, the differential driver and the reference are library files whose sha256
    the entry pins (checked before and after the run), and no candidate artifact, patch or
    provider output reaches this path (`certify` routes candidates to the rewrite-contract path).
    """
    operation, driver, defines, inputs = lowering_build(entry_id, library, tile_sizes, threads)
    matrix, controls = [], []
    for size in tile_sizes:
        output = folder / f'{operation}-{size}'
        build = compile_cpp(driver, output, library, tile_size=size, threads=threads, defines=defines)
        if build['returncode'] != 0:
            matrix.append({'operation': operation, 'tile_size': size, 'status': 'failed', 'reason': 'build failed',
                           'build': build, 'certification_inputs': inputs})
            continue
        positive = execute([output, operation], output.with_suffix('.positive.json'), threads=threads)
        passed = positive['returncode'] == 0 and f'SWDB_DIFFERENTIAL_PASS:{operation}' in positive['stdout']
        matrix.append({'operation': operation, 'tile_size': size, 'threads': threads,
                       'status': 'passed' if passed else 'failed', 'run': positive, 'build': build,
                       'certification_inputs': inputs})
        for name, expected in CONTROLS[operation].items():
            # Each control gets its own built executable. A build failure can never reject a control.
            control_binary = folder / f'{operation}-{size}-{name}'
            control_build = compile_cpp(driver, control_binary, library, tile_size=size, threads=threads, defines=defines)
            if control_build['returncode'] != 0:
                controls.append({'id': name, 'tile_size': size, 'status': 'invalid', 'reason': 'build failed', 'build': control_build})
                continue
            run = execute([control_binary, operation, name], control_binary.with_suffix('.run.json'), threads=threads)
            status, reason = rejection(run, expected)
            controls.append({'id': name, 'tile_size': size, 'status': status, 'reason': reason,
                             'expected_check': expected, 'build': control_build, 'run': run})
    # The strict store is required by calibration even though Peter's rewrite is read only.
    if operation == 'wait':
        for size in tile_sizes:
            output = folder / f'store-{size}'
            build = compile_cpp(driver, output, library, tile_size=size, threads=threads, defines=defines)
            if build['returncode'] != 0:
                controls.append({'id': 'wrong_store_wait', 'tile_size': size, 'status': 'invalid', 'reason': 'build failed', 'build': build})
                continue
            positive = execute([output, 'store'], output.with_suffix('.positive.json'), threads=threads)
            passed = positive['returncode'] == 0 and 'SWDB_DIFFERENTIAL_PASS:store' in positive['stdout']
            matrix.append({'operation': 'store', 'tile_size': size, 'status': 'passed' if passed else 'failed',
                           'run': positive, 'build': build, 'certification_inputs': inputs})
            run = execute([output, 'store', 'wrong_store_wait'], output.with_suffix('.negative.json'), threads=threads)
            status, reason = rejection(run, 'read_before_wait')
            controls.append({'id': 'wrong_store_wait', 'tile_size': size, 'status': status, 'reason': reason, 'run': run, 'build': build})
    for source in inputs['source_pins']:
        if artifacts.file_hash(Path(source['path'])) != source['sha256']:
            raise Failure('pinned source changed during lowering certification: ' + source['path'])
    return matrix, controls


def materialize_snapshot(store, snapshot_id, destination):
    snapshot = store.get(snapshot_id, 'source_snapshot')
    if not snapshot:
        raise Failure('unknown source snapshot: ' + snapshot_id)
    source = destination / 'source'
    derivation = snapshot.get('context', {}).get('source_derivation')
    if derivation:
        # Ticket 42: each scalar-only derivation names its own script (BFS's predates the field).
        script = (ROOT / derivation.get('script', 'scripts/prepare_dx100_scalar_snapshot.py')).resolve()
        # 2026-10-04 ET (final code review): a record field names code that is executed, so it
        # must be a snapshot-preparation script of this checkout.
        scripts = (ROOT / 'scripts').resolve()
        if (script.parent != scripts or not re.fullmatch(r'prepare_[a-z0-9_]+_snapshot\.py', script.name)
                or not script.is_file()):
            raise Failure('source derivation script must be a scripts/prepare_*_snapshot.py of this checkout')
        spec = importlib.util.spec_from_file_location('swdb_scalar_snapshot', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.materialize(destination, store.dir)
        current = data['artifact']
    else:
        current = artifacts.copy_snapshot(ROOT / 'apps/dx100', source)
    if current['sha256'] != snapshot['artifact']['sha256'] or current['files'] != snapshot['artifact']['files']:
        raise Failure('reconstructed snapshot manifest differs from registered source identity')
    return source, snapshot


def apply_patch(tree, patch):
    patch = Path(patch).resolve()
    if not patch.is_file():
        raise Failure('candidate patch is unavailable')
    # Git applies a patch without a repository. It refuses absolute paths and traversal.
    command = ['git', 'apply', '--check', str(patch)]
    check = subprocess.run(command, cwd=tree, capture_output=True, text=True)
    if check.returncode:
        raise Failure('candidate patch cannot be applied: ' + check.stderr.strip())
    process = subprocess.run(['git', 'apply', str(patch)], cwd=tree, capture_output=True, text=True)
    if process.returncode:
        raise Failure('candidate patch apply failed: ' + process.stderr.strip())


def peter_source(scalar):
    start = scalar.index('void TDStep(')
    end = scalar.index('\nint64_t TDStep2(', start)
    source = scalar[:start] + (ROOT / 'library/dx100/bfs_read_offload.inc').read_text() + scalar[end:]
    source = source.replace('#include <MAA_utility.hpp>', '#include <MAA_utility.hpp>\n#include "swdb_dxc_lowering.hpp"', 1)
    setup = '''    init_MAA();\n    t.Start();'''
    guarded = '''    init_MAA();
    // E3: guards and setup run once per BFS call after the existing allocation.
    swdb_dxc::chunks() = 0; swdb_dxc::races() = 0; swdb_dxc::violations() = 0;
    swdb_acceleration_enabled = uint64_t(g.num_nodes()) <= UINT64_C(1073741823) &&
        uint64_t(g.num_edges_directed()) <= UINT64_C(1073741823) && omp_get_max_threads() <= NUM_CORES;
    if (swdb_acceleration_enabled) {
        __dxc_session_begin();
#pragma omp parallel
        { swdb_contexts[omp_get_thread_num()] = __dxc_thread_context(); }
    }
    t.Start();'''
    if source.count(setup) != 1:
        raise Failure('scalar DOBFS setup differs from pinned source')
    source = source.replace(setup, guarded, 1)
    return source.replace('    return parent;\n}\n\n\nvoid PrintBFSStats', '    __dxc_report();\n    return parent;\n}\n\n\nvoid PrintBFSStats', 1)


def create_peter_patch(store, output, library=None, plugin=None, temporary_root=None):
    """Produce the deliverable patch without changing a vendored source byte.

    Ticket 42: ``plugin`` selects the kernel (default BFS: Peter section 5); its
    snapshot, rewritten translation unit and source rewrite come from the plug-in.
    """
    from swdb import kernels
    plugin = plugin or kernels.BFS
    library = Path(library or ROOT / 'library')
    import difflib
    rewritten = plugin.certification_source
    with tempfile.TemporaryDirectory(prefix='swdb-peter-patch-', dir=temporary_root) as temporary:
        tree, _ = materialize_snapshot(store, plugin.certification_snapshot, Path(temporary))
        original = (tree / rewritten).read_text()
        source = plugin.certification_rewrite(original)
        header = (library / 'dx100/dxc_lowering.hpp').read_text()
        diff = ''.join(difflib.unified_diff(original.splitlines(True), source.splitlines(True),
                                          fromfile='a/' + rewritten, tofile='b/' + rewritten))
        diff += ''.join(difflib.unified_diff([], header.splitlines(True), fromfile='/dev/null', tofile='b/' + HEADER))
        Path(output).write_text(diff)
    return {'patch': str(Path(output).resolve()), 'header_sha256': artifacts.file_hash(library / 'dx100/dxc_lowering.hpp')}


def graph_oracle(path, source):
    """Independent exact-depth counts from immutable normalized serialized CSR: the reference
    per-level frontier counts every candidate run is compared with."""
    data = Path(path).read_bytes()
    if len(data) < 9 or data[0] not in (0, 1):
        raise Failure('invalid certification graph')
    directed = data[0]
    edges, nodes = struct.unpack_from('<ii', data, 1)
    if nodes <= 0 or edges < 0 or not 0 <= source < nodes:
        raise Failure('invalid graph size or source')
    expected = 9 + (1 + directed) * ((nodes + 1) * 4 + edges * 4)
    if len(data) != expected:
        raise Failure('serialized graph size differs from CSR')
    offsets = struct.unpack_from(f'<{nodes+1}i', data, 9)
    neighbors = struct.unpack_from(f'<{edges}i', data, 9 + (nodes+1)*4)
    if offsets[0] != 0 or offsets[-1] != edges or any(a > b or a < 0 for a, b in zip(offsets, offsets[1:])):
        raise Failure('invalid graph offsets')
    if any(v < 0 or v >= nodes for v in neighbors):
        raise Failure('invalid graph neighbors')
    depth = [-1] * nodes
    depth[source] = 0
    frontier = deque([source])
    counts = []
    while frontier:
        u = frontier.popleft()
        d = depth[u]
        if d == len(counts):
            counts.append(0)
        counts[d] += 1
        for v in neighbors[offsets[u]:offsets[u+1]]:
            if depth[v] == -1:
                depth[v] = d + 1
                frontier.append(v)
    return counts


def two_level_graph(path):
    # First frontier has 4,200 vertices; vertex 1 then emits >16,384 arcs.
    # Spare isolated nodes allow duplicate-enqueue controls to reach the guard.
    width, leaves = 4200, 17000
    nodes = width + leaves + 17
    rows = [list(range(1, width+1)), list(range(width+1, width+leaves+1)),
            list(range(width+leaves-511, width+leaves+1))]
    rows += [[] for _ in range(nodes-3)]
    inverse = [[] for _ in range(nodes)]
    for u, row in enumerate(rows):
        for v in row:
            inverse[v].append(u)
    edges = sum(map(len, rows))
    with Path(path).open('wb') as stream:
        stream.write(struct.pack('<Bii', 1, edges, nodes))
        for adjacency in (rows, inverse):
            offset = 0
            stream.write(struct.pack('<i', offset))
            for row in adjacency:
                offset += len(row)
                stream.write(struct.pack('<i', offset))
            for row in adjacency:
                if row:
                    stream.write(struct.pack('<' + 'i'*len(row), *row))


def matrix_graphs(folder, library, threads):
    converter = folder / 'converter'
    build = compile_cpp(ROOT / 'apps/dx100/benchmarks/gapbs/src/converter.cc', converter,
                        library, tile_size=1024, threads=threads)
    if build['returncode']:
        raise Failure('certification graph converter failed to build; see ' + build['log'])
    graphs = []
    for name, option, scale in [('kronecker-10', '-g', 10), ('kronecker-14', '-g', 14), ('kronecker-16', '-g', 16), ('uniform-14', '-u', 14)]:
        graph = folder / (name + '.sg')
        run = execute([converter, option, scale, '-k', '16', '-s', '-b', graph], folder / (name+'.generation.json'), threads=threads)
        if run['returncode']:
            raise Failure('certification graph generation failed; see ' + run['log'])
        graphs.append((name, graph))
    graph = folder / 'two-level-degree-17000.sg'
    two_level_graph(graph)
    graphs.append(('two-level-degree-17000', graph))
    return graphs


def instrument_source(source, *, calibrate=False, frontier_hook=True):
    """Insert the evaluator's frontier inspection before the protected frontier print.

    Ticket 70 (certify 1.3): for a candidate the inspection only records the window
    (``candidate_prelude.hpp``, forced in by the build); calibration keeps the 1.2 in-source check.
    Ticket 76 (certify 1.4): ``frontier_hook=False`` inserts nothing into the candidate's function
    (the forced 1.4 prelude records each window at the queue's slide); the checks stay.
    """
    statement = AUTHOR_FRONTIER_TEXT if calibrate else FRONTIER_TEXT
    if source.count(statement) != 1:
        raise Failure('BFS frontier logging statement differs from the protected exact text')
    # Protect the source kernel verifier and the standard benchmark driver's PASS rendering.
    if source.count('bool BFSVerifier(') != 1:
        raise Failure('BFS correctness check is missing or ambiguous')
    if frontier_hook or calibrate:
        source = source.replace(statement, 'swdb_certification_frontier(queue);\n        ' + statement)
    if not calibrate:
        return source
    if calibrate:
        consume = '#pragma omp simd aligned(tile4Ptr, tile0Ptr, tile5Ptr : 16) simdlen(4)'
        if len(re.findall('^' + re.escape(consume) + '$', source, re.MULTILINE)) != 1:
            raise Failure('authors tile-read site differs from pinned source')
        source = re.sub('^' + re.escape(consume) + '$', lambda _: 'swdb_strict::check(get_tile_ready(tile5)!=0, "read_before_wait");\n' + consume, source, flags=re.MULTILINE)
    return '#include <set>\n#include <cstdio>\n#include <cstdlib>\n#include <cstdint>\n' + TRUSTED_FRONTIER + source


def judge_bfs(result, counts, *, calibrate=False, threshold=64):
    output = result['stdout']
    if result['timeout']:
        return False, 'timeout'
    if 'SWDB_STRICT_ASSERT:' in output + result['stderr']:
        return False, 'strict_layer_assertion'
    if 'SWDB_PRESERVATION_FAIL:' in output + result['stderr']:
        return False, 'frontier_size_equality'
    if result['returncode'] != 0:
        return False, 'process_failure'
    if not re.search(r'Verification\s*:?\s*PASS', output):
        return False, 'verifier'
    observed = [int(n) for n in re.findall(r'Starting TDStep(?:MAA)?: (\d+) elements', output)]
    trusted = [int(n) for n in re.findall(r'SWDB trusted_frontier=(\d+)', output)]
    if observed != counts or trusted != counts:
        return False, 'frontier_size_equality'
    witnesses = re.findall(r'SWDB (?:strict_operations|accelerated_chunks)=(\d+)', output)
    needed = max(counts) > 4096 if calibrate else max(counts) >= threshold
    if needed and (len(witnesses) != 1 or int(witnesses[0]) == 0):
        return False, 'execution_witness'
    return True, 'all_checks_passed'


def _rewrite_control(source, name, *, calibrate=False):
    """Mutate actual candidate code; no fabricated runtime result fixtures."""
    if calibrate:
        if name == 'wrong_store_wait':
            return source.replace('wait_ready(tile5);', 'wait_ready(tile3);', 1)
        if name == 'shared_context':
            return source.replace('int tid = omp_get_thread_num();', 'int tid = 0;', 1)
        if name == 'dropped_continuation':
            return source.replace('} while (curr_tile7_size > 0);', '} while (false);', 1)
        if name == 'oversized_chunk':
            # Retain real compilation and intentionally exceed strict capacity.
            return source.replace('if (tile_size != -1) {', 'if (tile_size != -1) {', 1).replace('int max = min + tile_size;', 'int max = min + 16384;', 1)
    # Ticket 62 (2026-10-04 ET): candidate controls act at the library seam, never on
    # the candidate's spelling (swdb.certification_faults).
    from swdb.certification_faults import library_control
    return library_control(source, name)


def certify_bfs(tree, library, folder, tile_sizes, threads, sources, *, calibrate=False, threshold=64, plugin=None,
                contract=None, version=None):
    """Run the matrix and its controls; the kernel plug-in supplies the instance.

    Calibration is the BFS authors' reference and always uses the BFS functions and the 1.2
    in-process checks (it certifies the authors' code, not a candidate). A candidate artifact is
    certified by the evaluator entry point of its version in the candidate version table
    (``swdb.certification_procedures``; the default version when ``version`` is None).
    """
    from swdb import kernels
    if not calibrate:
        procedure = procedures.procedure(procedures.CANDIDATE, version)
        matrix, controls, _schedule = procedure.entry_point()(
            tree, library, folder, tile_sizes, threads, sources, threshold=threshold, plugin=plugin or kernels.BFS,
            contract=contract, procedure=procedure)
        return matrix, controls
    if plugin not in (None, kernels.BFS):
        raise Failure('calibration exists only for the BFS authors reference')
    plugin = kernels.BFS
    judge = lambda run, counts: judge_bfs(run, counts, calibrate=True, threshold=threshold)
    graphs = matrix_graphs(folder, library, threads)
    source = (tree / plugin.certification_source).read_text()
    source = source.replace('wait_ready(tile3);', 'wait_ready(tile5);', 1)
    source = source.replace('    return parent;\n}\n\nvoid PrintBFSStats', '    std::printf("SWDB strict_operations=%llu\\n",(unsigned long long)swdb_strict::operation_count());\n    return parent;\n}\n\nvoid PrintBFSStats', 1)
    if 'SWDB strict_operations=' not in source:
        # Exact authors code has a separate blank-line count across pinned ranges.
        begin = source.index('pvector<NodeID> DOBFSMAA(')
        end = source.index('void PrintBFSStats', begin)
        section = source[begin:end]
        section = section.replace('    return parent;', '    std::printf("SWDB strict_operations=%llu\\n",(unsigned long long)swdb_strict::operation_count());\n    return parent;', 1)
        source = source[:begin] + section + source[end:]
    matrix, controls = [], []
    source_path = tree / plugin.certification_source
    stem = plugin.binary_stem
    expected = {'shared_context': {'thread_ownership_tile', 'thread_ownership_register'}, 'dropped_continuation': set(),
                'oversized_chunk': {'tile_truncation'}, 'wrong_store_wait': {'read_before_wait'}}
    for size in tile_sizes:
        source_path.write_text(instrument_source(source, calibrate=True))
        output = folder / f'{stem}-{size}'
        build = compile_cpp(source_path, output, library, tile_size=size, threads=threads, tree=tree, defines=['-DMAA'])
        if build['returncode'] != 0:
            matrix.append({'tile_size': size, 'status': 'failed', 'reason': 'build failed', 'build': build})
            continue
        for graph_name, graph in graphs:
            for source_vertex in sources:
                counts = plugin.certification_oracle(graph, source_vertex)
                run = execute([output, '-f', graph, '-r', source_vertex, '-n', '1', '-v'], folder / f'{graph_name}-{size}-{source_vertex}.json', threads=threads)
                passed, reason = judge(run, counts)
                matrix.append({'graph': graph_name, 'graph_sha256': artifacts.file_hash(graph), 'source': source_vertex,
                               'oracle_frontier_counts': counts, 'tile_size': size, 'threads': threads,
                               'status': 'passed' if passed else 'failed', 'reason': reason, 'build': build, 'run': run})
        graph_name, graph = graphs[-1]
        counts = plugin.certification_oracle(graph, plugin.control_source(sources))
        for name in ('shared_context', 'dropped_continuation', 'oversized_chunk', 'wrong_store_wait'):
            # Oversized chunk is specifically a 1,024-element build control.
            if name == 'oversized_chunk' and size != 1024:
                continue
            source_path.write_text(_rewrite_control(instrument_source(source, calibrate=True), name, calibrate=True))
            output_control = folder / f'{stem}-{size}-{name}'
            control_build = compile_cpp(source_path, output_control, library, tile_size=size, threads=threads, tree=tree,
                                        defines=['-DMAA'])
            fault = {'site': 'calibration_source'}
            if control_build['returncode']:
                controls.append({'id': name, 'tile_size': size, 'status': 'invalid', 'reason': 'build failed',
                                 'observed_checks': [], 'fault': fault, 'build': control_build})
                continue
            run = execute([output_control, '-f', graph, '-r', plugin.control_source(sources), '-n', '1', '-v'], folder / f'control-{size}-{name}.json', threads=threads)
            passed, reason = judge(run, counts)
            named = re.findall(r'SWDB_(?:STRICT_ASSERT|DIFFERENTIAL_MISMATCH|PRESERVATION_FAIL):([a-z_]+)', run['stdout'] + run['stderr'])
            observed = observed_checks(run, counts, judge, named)
            controls.append({'id': name, 'tile_size': size, 'status': control_status(expected[name], observed, run, passed),
                             'reason': reason, 'named_checks': named, 'observed_checks': observed, 'graph': graph_name,
                             'fault': fault, 'build': control_build, 'run': run})
    source_path.write_text(source)  # This is a private build copy, never a vendored tree.
    return matrix, controls


def graph_adjacency(path):
    """Out-neighbor lists of a serialized certification graph (the result checks' input, ticket 70)."""
    data = Path(path).read_bytes()
    if len(data) < 9 or data[0] not in (0, 1):
        raise Failure('invalid certification graph')
    edges, nodes = struct.unpack_from('<ii', data, 1)
    if nodes <= 0 or edges < 0 or len(data) != 9 + (1 + data[0]) * ((nodes + 1) * 4 + edges * 4):
        raise Failure('serialized graph size differs from CSR')
    offsets = struct.unpack_from(f'<{nodes+1}i', data, 9)
    neighbors = struct.unpack_from(f'<{edges}i', data, 9 + (nodes + 1) * 4)
    if offsets[0] != 0 or offsets[-1] != edges or any(a > b for a, b in zip(offsets, offsets[1:])):
        raise Failure('invalid graph offsets')
    if any(v < 0 or v >= nodes for v in neighbors):
        raise Failure('invalid graph neighbors')
    return [list(neighbors[offsets[u]:offsets[u + 1]]) for u in range(nodes)]


def judge_run(plugin, run, graph, vertex, counts, *, threshold=64, adjacency=None):
    """Every check of one certify 1.3 run, from its evaluator records and the trusted reference counts."""
    from swdb import certification_isolation as isolation
    from swdb.certification_feedback import STRICT_MESSAGES
    adjacency = {} if adjacency is None else adjacency
    if graph not in adjacency:
        adjacency[graph] = graph_adjacency(graph)
    parsed = isolation.parse_records(run['record'], set(STRICT_MESSAGES))
    check = lambda values: plugin.certification_check_result(adjacency[graph], vertex, values)
    return isolation.judge(run, parsed, counts, check_result=check, result_kind=plugin.certification_result_kind,
                           threshold=threshold)


def certify_candidate(tree, library, folder, tile_sizes, threads, sources, *, threshold=64, plugin, contract=None,
                      procedure=None):
    """Certify one candidate tree with certify 1.3's isolation (ticket 70, 2026-10-04 ET).

    Per tile size, the instrumented candidate plus the evaluator's driver is compiled once into
    one object with the evaluator prelude. The positive matrix and every library-fault control
    link that same object with record.cc and seams.cc (no fault, or exactly one). Token and
    legality controls change candidate text and get their own object, linked with no fault.
    Every check comes from :func:`swdb.certification_isolation.judge` on the run's records.
    Ticket 68's legality checks run as before. ``procedure`` is the version table's entry (candidate
    1.3 when omitted); it names the driver and the legality rules. Returns (matrix, controls, None).
    """
    from swdb import certification_isolation as isolation
    from swdb import certification_legality as legality
    from swdb.certification_faults import FAULT_VERSIONS, SEAM_FILE
    procedure = procedure or procedures.procedure(procedures.CANDIDATE, '1.3')
    rules = procedure.legality
    legal = bool(contract) and legality.applies(contract)
    graphs = matrix_graphs(folder, library, threads)
    by_name = dict(graphs)
    source_path = tree / plugin.certification_source
    source = source_path.read_text()
    driver = procedure.driver_path(library, plugin).read_text()
    stem = plugin.binary_stem
    adjacency = {}
    judged = lambda run, graph, vertex, counts: judge_run(plugin, run, graph, vertex, counts, threshold=threshold,
                                                          adjacency=adjacency)

    def legality_of(text, label, size):
        return (legality_checks(text, source_path, label, library, contract, folder, tile_size=size, threads=threads,
                                tree=tree, defines=[], rules=rules) if legal else None)

    matrix, controls = [], []
    for size in tile_sizes:
        build = isolation.CandidateBuild(folder / f'{stem}-{size}.objects', library, tree, source_path, size, threads)
        instrumented = common.candidate_check(plugin.certification_instrument, source) + driver
        static = legality_of(instrumented, f'{stem}-{size}', size)
        static_failed, static_invalid = _legality_failures(static)
        legality_field = {'legality_checks': static} if legal else {}
        output = folder / f'{stem}-{size}'
        positive = build.candidate_object(instrumented, 'positive')
        link = build.link(positive, None, output) if positive['returncode'] == 0 else positive
        if link['returncode'] != 0:
            matrix.append({'tile_size': size, 'status': 'failed', 'reason': 'build failed', 'build': positive,
                           'link': link, **legality_field})
            continue
        for graph_name, graph in graphs:
            for source_vertex in sources:
                counts = plugin.certification_oracle(graph, source_vertex)
                run = isolation.run(output, graph, source_vertex, folder / f'{graph_name}-{size}-{source_vertex}.json',
                                    threads)
                verdict = judged(run, graph, source_vertex, counts)
                passed, reason = verdict['passed'], verdict['reason']
                if static_failed or static_invalid:
                    # Ticket 68: an evaluator legality check names the failure before any run check.
                    passed, reason = False, static_failed[0] if static_failed else 'legality_check_invalid'
                matrix.append({'graph': graph_name, 'graph_sha256': artifacts.file_hash(graph), 'source': source_vertex,
                               'oracle_frontier_counts': counts, 'tile_size': size, 'threads': threads,
                               'status': 'passed' if passed else 'failed', 'reason': reason, 'build': positive,
                               'link': link, 'run': run, **common.evidence(link, verdict), **legality_field})
        names = list(plugin.certification_controls) + (list(legality.CONTROLS) if legal else [])
        # A control runs on the last (two-level) graph unless its plug-in names another matrix
        # graph (2026-10-04 ET: BC's L4 path-count control needs unequal path counts).
        control_graphs = getattr(plugin, 'certification_control_graphs', None) or {}
        reference_counts = {}
        vertex = plugin.control_source(sources)
        for name in names:
            graph_name = control_graphs.get(name, graphs[-1][0])
            graph = by_name[graph_name]
            if graph_name not in reference_counts:
                reference_counts[graph_name] = plugin.certification_oracle(graph, vertex)
            counts = reference_counts[graph_name]
            if name in legality.CONTROLS and legal:
                # Ticket 68: the knob assignment or schedule clause of the candidate's own source.
                control = legality.control(source, name, contract, rules=rules)
                control['source'] = plugin.certification_instrument(control['source']) + driver
            else:
                control = plugin.certification_control(plugin.certification_instrument(source), name)
                if isinstance(control, str):
                    control = {'source': control + driver, 'fault': None, 'site': 'candidate_tokens'}
                else:
                    control = {**control, 'source': control['source'] + driver}
            fault = {'site': control['site']}
            if control['fault']:
                # A library fault never changes the candidate's text: the control links the positive
                # object itself, and the fault macro reaches only the seam object.
                if control['source'] != instrumented:
                    raise Failure('library-fault control changed candidate text: ' + name)
                candidate_object, control_static = positive, static
                fault.update(macro=control['fault'], version=control.get('version', FAULT_VERSIONS.get(name, 1)),
                             delivery='separate_object', seam_source_sha256=artifacts.file_hash(library / SEAM_FILE))
            else:
                control_static = legality_of(control['source'], f'{stem}-{size}-{name}', size)
                candidate_object = build.candidate_object(control['source'], name)
            expected_checks = plugin.certification_controls.get(name) or legality.CONTROLS.get(name, set())
            static_failed, _ = _legality_failures(control_static)
            legality_field = {'legality_checks': control_static} if legal else {}
            output_control = folder / f'{stem}-{size}-{name}'
            control_link = (build.link(candidate_object, control['fault'], output_control)
                            if candidate_object['returncode'] == 0 else candidate_object)
            if control_link['returncode']:
                # Ticket 68: a build failure never rejects a control; an evaluator legality check that
                # names the control's expected check does (e.g. a candidate static_assert on a knob
                # also stops the build).
                named_static = sorted(set(static_failed) & set(expected_checks))
                controls.append({'id': name, 'tile_size': size, 'status': 'rejected' if named_static else 'invalid',
                                 'reason': named_static[0] if named_static else 'build failed',
                                 'observed_checks': sorted(set(static_failed)), 'fault': fault,
                                 'build': candidate_object, 'link': control_link, **legality_field})
                continue
            run = isolation.run(output_control, graph, vertex, folder / f'control-{size}-{name}.json', threads)
            verdict = judged(run, graph, vertex, counts)
            passed, reason = verdict['passed'], verdict['reason']
            record = common.evidence(control_link, verdict)
            if static_failed:
                record['observed_checks'] = sorted(set(record['observed_checks']) | set(static_failed))
                passed, reason = False, static_failed[0]
            controls.append({'id': name, 'tile_size': size,
                             'status': control_status(expected_checks, record['observed_checks'], run, passed),
                             'reason': reason, 'graph': graph_name, 'fault': fault, 'build': candidate_object,
                             'link': control_link, 'run': run, **record, **legality_field})
    source_path.write_text(source)  # This is a private build copy, never a vendored tree.
    return matrix, controls, None


def evaluate_trusted(*, calibrate, entry_id, tree, library, folder, tile_sizes, threads, sources):
    """The lowering-and-calibration family's evaluator entry point: (matrix, controls, None)."""
    if calibrate:
        matrix, controls = certify_bfs(tree, library, folder, tile_sizes, threads, sources, calibrate=True)
    else:
        matrix, controls = certify_lowering(entry_id, library, folder, tile_sizes, threads)
    return matrix, controls, None


SEMANTIC_CHECKS = {'verifier', 'frontier_size_equality', 'execution_witness'}
# Ticket 76 (certify 1.4): the seam witness of contract clause L4, from the trusted slide-window events.
SEAM_WITNESS = 'seam_witness'


def observed_checks(run, counts, judge, named):
    """Every check a control run failed, not only the judge's first reason.

    Created 2026-10-04 ET (final code review, ticket 43). Named checks come from the run's
    own SWDB_* lines; a preservation failure is a frontier-size failure. With a clean exit,
    a missing verifier PASS is `verifier`, and the judge's later checks (frontier sizes,
    execution witness) are evaluated as if the verifier had passed, so a clause that names
    `frontier_size_equality` is not hidden behind an earlier verifier failure.
    """
    observed = set(named)
    text = run['stdout'] + run['stderr']
    if 'SWDB_PRESERVATION_FAIL:' in text:
        observed.add('frontier_size_equality')
    if not run['timeout'] and run['returncode'] == 0 and 'SWDB_STRICT_ASSERT:' not in text:
        if not re.search(r'Verification\s*:?\s*PASS', run['stdout']):
            observed.add('verifier')
            run = {**run, 'stdout': run['stdout'] + '\nVerification: PASS\n'}
        passed, reason = judge(run, counts)
        if not passed and reason in SEMANTIC_CHECKS:
            observed.add(reason)
    return sorted(observed)


def control_status(expected_checks, observed, run, passed):
    """`rejected`, `survived` or `invalid` for one negative-control run.

    2026-10-04 ET (final code review, ticket 43): a control with expected named checks is
    rejected only by one of them; a semantic failure no longer stands in for it. A semantic
    control (empty set) needs a semantic failure with a clean exit.
    """
    if expected_checks:
        rejected = bool(set(expected_checks) & set(observed))
    else:
        rejected = run['returncode'] == 0 and bool(SEMANTIC_CHECKS & set(observed))
    if rejected and not passed and not run['timeout']:
        return 'rejected'
    return 'survived' if passed else 'invalid'


def producible_checks():
    """Check names a certification run can report (named SWDB_* checks and semantic checks).

    Ticket 68 (2026-10-04 ET): plus the evaluator's legality checks knob_range and schedule_range.
    """
    from swdb.certification_feedback import STRICT_MESSAGES
    from swdb.certification_legality import CHECKS
    return set(STRICT_MESSAGES) | SEMANTIC_CHECKS | {'duplicate_frontier', SEAM_WITNESS} | set(CHECKS)


def clause_controls(entry, controls, plugin=None):
    """Compare each contract clause's negative control with the check the clause names.

    Created 2026-10-04 ET (final code review, ticket 43). A clause is `matched` when every run
    of its control was rejected and observed the clause's named check. A check name that no
    run can report is recorded as not `enforceable` (a contract wording defect to fix in the
    contract, not here) and does not change the verdict; an enforceable mismatch does.
    A plug-in may add controls to a clause (`certification_clause_controls`, source `plugin`),
    e.g. BC's L4 parts that the contract's single control does not exercise.
    """
    from swdb import certification_legality as legality
    producible = producible_checks()
    extra = getattr(plugin, 'certification_clause_controls', None) or {}
    legal = legality.applies(entry)
    rows = []
    for clause in entry.get('clauses') or []:
        control = clause.get('negative_control') or {}
        pairs = []
        if control.get('id') not in (None, 'none') and control.get('check'):
            pairs.append((control['id'], control['check'], 'contract'))
        pairs += [(cid, check, 'plugin') for cid, check in extra.get(clause.get('id'), ())]
        # Ticket 68 (2026-10-04 ET): knob_range and schedule_range are exercised by the certifier's
        # own legality controls; the contract's control for them changes no knob assignment or
        # schedule clause, so that pair cannot be matched (a contract wording issue for Yan-Ru).
        if legal and control.get('check') in legality.CHECKS:
            pairs.append((legality.CHECK_CONTROL[control['check']], control['check'], 'certifier'))
        for cid, check, origin in pairs:
            runs = [c for c in controls if c['id'] == cid]
            seen = sorted(set().union(*(c.get('observed_checks') or [] for c in runs))) if runs else []
            matched = bool(runs) and all(c['status'] == 'rejected' and check in (c.get('observed_checks') or [])
                                         for c in runs)
            row = {'clause': clause.get('id'), 'control': cid, 'check': check, 'source': origin,
                   'observed_checks': seen, 'matched': matched, 'enforceable': check in producible}
            if check in legality.CHECKS and cid != legality.CHECK_CONTROL[check]:
                row.update(enforceable=False, reason='control_cannot_exercise_check')
            elif not row['enforceable']:
                row['reason'] = 'no_run_reports_check'
            rows.append(row)
    return rows


_CONTROL_EXPECTED = {
    'shared_context': {'thread_ownership_tile', 'thread_ownership_register'},
    'skipped_cas_recheck': {'duplicate_frontier'}, 'dropped_continuation': set(),
    'chunk_off_by_one': {'tile_truncation'}, 'dropped_wait': {'byte_offset_overflow', 'read_before_wait'},
    'read_before_wait': {'read_before_wait'}, 'index_wrap': {'stream_bounds', 'byte_offset_overflow'},
    'forged_frontier': {'duplicate_frontier'},
}


def check_candidate_scope(tree, snapshot, plugin=None):
    """Every changed source byte belongs to this kernel rewrite's declared files."""
    from swdb import kernels
    plugin = plugin or kernels.BFS
    rewritten = plugin.certification_source
    original = {item['path']: item for item in snapshot['artifact']['files']}
    current = {item['path']: item for item in artifacts.manifest(tree)}
    changed = {path for path in set(original) | set(current) if original.get(path) != current.get(path)}
    if changed - {rewritten, HEADER} or rewritten not in changed:
        raise common.CandidateUsageError(f'{plugin.name} contract permits only the {plugin.name} rewrite and canonical lowering header; '
                         'changed files: ' + ', '.join(sorted(changed)))
    return sorted(changed)


def bind_candidate_record(path, snapshot_id, tree):
    """Ticket 75: the Extensa candidate record a snapshot-plus-patch tree reproduces, or a refusal.

    The record is read only (it stays in its campaign store); it binds only when its source snapshot
    is the one certified and its artifact sha256 equals the patched tree's identity.
    """
    from swdb import access
    data = access.read_record(Path(path))
    if not isinstance(data, dict) or data.get('kind') != 'candidate' or not data.get('id'):
        raise UsageError('--candidate-record must be a candidate record')
    if data.get('source_snapshot') != snapshot_id:
        raise UsageError('candidate record names another source snapshot: ' + str(data.get('source_snapshot')))
    tree_sha256 = artifacts.identify(tree)['sha256']
    if (data.get('artifact') or {}).get('sha256') != tree_sha256:
        raise UsageError('patched tree differs from the candidate record artifact '
                         f"({tree_sha256} != {(data.get('artifact') or {}).get('sha256')})")
    bound = {'id': data['id'], 'record_sha256': access.record_hash(Path(path))}
    for key in ('mode', 'campaign'):
        if data.get(key):
            bound[key] = data[key]
    return bound


def _materialize_candidate(store, folder, *, candidate, snapshot, patch, rewritten):
    """(tree, snapshot record, snapshot ID, snapshot text of the rewritten file) of a candidate input:
    a registered candidate artifact, or a registered snapshot with a patch applied."""
    if candidate:
        data = store.get(candidate, 'candidate')
        if not data:
            raise UsageError('unknown candidate artifact')
        original = artifacts.verify(data['artifact'])
        tree = folder / 'source'
        artifacts.copy_snapshot(original, tree)
        snapshot_id = data.get('source_snapshot')
        original_snapshot = store.get(snapshot_id, 'source_snapshot')
        if not original_snapshot:
            raise Failure('candidate has no registered source snapshot')
        (folder / 'snapshot').mkdir()
        snapshot_tree, _ = materialize_snapshot(store, snapshot_id, folder / 'snapshot')
        snapshot_text = (snapshot_tree / rewritten).read_text()
    else:
        tree, original_snapshot = materialize_snapshot(store, snapshot, folder)
        snapshot_id = snapshot
        snapshot_text = (tree / rewritten).read_text()
        apply_patch(tree, patch)
    if not original_snapshot:
        raise Failure('candidate has no registered source snapshot')
    return tree, original_snapshot, snapshot_id, snapshot_text


def _candidate_identity(entry_id, content_sha256, tree, snapshot_id, changed_files, *, candidate, candidate_record,
                        **extra):
    identity = {'contract': entry_id, 'contract_sha256': content_sha256,
                'tree_sha256': artifacts.identify(tree)['sha256'], 'snapshot': snapshot_id,
                'changed_files': changed_files, **extra}
    if candidate:
        identity['id'] = candidate
    if candidate_record:
        bound = bind_candidate_record(candidate_record, snapshot_id, tree)
        identity.update(id=bound.pop('id'), candidate_record=bound)
    return identity


def certify(store, entry_id=None, *, runs_dir=None, library=None, candidate=None,
            snapshot=None, patch=None, calibrate=False, tile_sizes=(16384, 1024), threads=4, sources=(0,),
            candidate_record=None, version=None):
    from swdb.library import Library
    from swdb import certification_native as native
    from swdb import kernels
    library_root = Path(library or ROOT / 'library').resolve()
    catalog = Library(library_root, store=store)
    problems = catalog.validate()
    if problems:
        raise UsageError('typed library is invalid: ' + str(problems[0]))
    native_entry = None if calibrate or not entry_id else catalog.get(entry_id)
    native_entry = native_entry if native.is_native(native_entry) else None
    if candidate_record and not (snapshot and patch):
        raise UsageError('--candidate-record binds a --snapshot/--patch certification')
    if native_entry is None and (threads != 4 or tuple(sorted(set(tile_sizes))) != (1024, 16384)):
        raise UsageError('DX100 certification requires the full matrix: tile sizes 16384,1024 and four threads')
    if not sources or any(type(s) is not int or s < 0 for s in sources):
        raise UsageError('sources must be nonnegative vertex IDs')
    if bool(snapshot) != bool(patch) or (candidate and snapshot):
        raise UsageError('use --candidate or the paired --snapshot/--patch input')
    if not calibrate and not entry_id:
        raise UsageError('certification requires an entry ID')
    # One frozen version table per command family (swdb.certification_procedures); an unknown or
    # historic version raises here. Ticket 76: calibration and lowering certification read printed
    # lines, so they only ever run trusted code: the pinned authors' tree (calibration) or hash-pinned
    # library files (lowerings). Neither takes candidate input.
    if calibrate and (candidate or snapshot or patch):
        raise UsageError('calibration certifies only the pinned authors source; it takes no candidate input')
    family = (procedures.LOWERING if calibrate else procedures.NATIVE if native_entry is not None
              else procedures.CANDIDATE if candidate or snapshot else procedures.LOWERING)
    procedure = procedures.procedure(family, version)
    plugin = None
    if calibrate:
        entry_id = entry_id or 'calibration.dx100_authors_t17'
        content_sha256 = artifacts.digest({'source_tree': artifacts.identify(ROOT / 'apps/dx100')['sha256'], 'fix': 'wait_ready(tile3) -> wait_ready(tile5)', 'strict_layer': artifacts.identify(library_root / 'dx100/strict')['sha256']})
        dependencies = []
    else:
        entry = catalog.get(entry_id)
        if not entry:
            raise UsageError('unknown library entry: ' + entry_id)
        content_sha256 = catalog.content_sha256(entry_id)
        dependencies = catalog.dependency_pins(entry_id)
        if family == procedures.NATIVE:
            if not (candidate or snapshot):
                raise UsageError('a native-CPU rewrite contract certifies a candidate artifact')
            plugin = kernels.get(entry.get('correctness_check', {}).get('kernel'))
            if plugin is None or plugin.certification_result_kind is None:
                raise UsageError('rewrite contract correctness check names no kernel with a certification plug-in')
        elif family == procedures.CANDIDATE:
            if entry.get('kind') != 'rewrite_contract':
                raise UsageError('candidate-artifact certification requires a rewrite contract')
            plugin = kernels.get(entry.get('correctness_check', {}).get('kernel'))
            if plugin is None or plugin.certification_source is None:
                raise UsageError('rewrite contract correctness check names no kernel with a certification plug-in')
        elif entry.get('kind') not in {'lowering', 'intrinsic', 'library_operation'}:
            raise UsageError('entry requires a candidate artifact or a differential-test driver')
    base = artifacts.external_directory(runs_dir or Path(tempfile.gettempdir()) / 'swdb-certification')
    folder = base / ('certify-' + uuid.uuid4().hex)
    folder.mkdir()
    before = artifacts.identify(ROOT / 'apps/dx100')
    command, sources_before = procedures.command_fields(procedure, library_root, plugin)
    identity = None
    native_schedule = None
    if calibrate:
        tree = folder / 'source'
        artifacts.copy_snapshot(ROOT / 'apps/dx100', tree)
        matrix, controls, _ = procedure.entry_point()(calibrate=True, entry_id=entry_id, tree=tree, library=library_root,
                                                      folder=folder, tile_sizes=tile_sizes, threads=threads,
                                                      sources=sources)
    elif family == procedures.NATIVE:
        # Ticket 75: a native-CPU contract; its pinned profile is the matrix.
        profile = native.load_profile(catalog, entry)
        tree, original_snapshot, snapshot_id, snapshot_text = _materialize_candidate(
            store, folder, candidate=candidate, snapshot=snapshot, patch=patch, rewritten=profile['scope']['file'])
        common.candidate_check(artifacts.check_protections, tree, original_snapshot['protections'])
        changed_files = native.check_scope(profile, tree, original_snapshot, snapshot_text)
        from swdb.certification_isolation import refuse_scan_findings, scan
        candidate_text = (tree / profile['scope']['file']).read_text()
        directives = procedure.directives == 'pragma_omp_only'
        refuse_scan_findings(snapshot_text, candidate_text, version=procedure.version, directives=directives,
                             primitives=procedure.scan_primitives)
        identity = _candidate_identity(
            entry_id, content_sha256, tree, snapshot_id, changed_files, candidate=candidate,
            candidate_record=candidate_record,
            scan={'findings': len(scan(snapshot_text, candidate_text, procedure.version, directives=directives,
                                       primitives=procedure.scan_primitives)),
                  'directives': 'only #pragma omp may be authored'},
            rewrite_scope={'file': profile['scope']['file'], 'function': profile['scope']['begin']})
        if tuple(sources) != (0,):
            raise UsageError('a native-CPU profile pins its sources; --sources cannot override them')
        matrix, controls, native_schedule = procedure.entry_point()(tree, library_root, folder, profile, plugin,
                                                                    procedure=procedure)
        native_profile = {'id': profile['data']['id'], 'path': str(profile['path'].relative_to(library_root)),
                          'sha256': profile['sha256'], 'target': 'native_cpu',
                          # Ticket 75 review: pre-check on the certifying host, not on the target machine.
                          'target_scope': f'pre-check executed on {platform.system()} {platform.machine()}; '
                                          'the target check is the evaluator compiled verifier on every timed '
                                          'trial on mbit10 (x86_64)'}
    elif family == procedures.CANDIDATE:
        tree, original_snapshot, snapshot_id, snapshot_text = _materialize_candidate(
            store, folder, candidate=candidate, snapshot=snapshot, patch=patch, rewritten=plugin.certification_source)
        common.candidate_check(artifacts.check_protections, tree, original_snapshot['protections'])
        changed_files = check_candidate_scope(tree, original_snapshot, plugin)
        header = tree / HEADER
        if not header.is_file() or artifacts.file_hash(header) != artifacts.file_hash(library_root / 'dx100/dxc_lowering.hpp'):
            raise common.CandidateFailure('candidate must ship the byte-identical canonical lowering header')
        # Ticket 70 (certify 1.3): candidate-authored text may not name evaluator symbols. Ticket 76:
        # 1.4 also refuses descriptor reads, temporary files and frame introspection.
        from swdb.certification_isolation import refuse_scan_findings
        candidate_text = (tree / plugin.certification_source).read_text()
        refuse_scan_findings(snapshot_text, candidate_text, version=procedure.version, primitives=procedure.scan_primitives)
        if procedure.directives == 'dx100_knob_defaults':
            # Ticket 78 (from ticket 75's review): authored code may not depend on whether it is a
            # certification build (knob defaults and the diagnostic block excepted).
            from swdb.certification_process import refuse_directives
            refuse_directives(snapshot_text, candidate_text, entry, procedure.version)
        identity = _candidate_identity(entry_id, content_sha256, tree, snapshot_id, changed_files,
                                       candidate=candidate, candidate_record=candidate_record)
        matrix, controls, _schedule = procedure.entry_point()(
            tree, library_root, folder, tile_sizes, threads, sources, threshold=64, plugin=plugin, contract=entry,
            procedure=procedure)
    else:
        matrix, controls, _ = procedure.entry_point()(calibrate=False, entry_id=entry_id, tree=None,
                                                      library=library_root, folder=folder, tile_sizes=tile_sizes,
                                                      threads=threads, sources=sources)
    if artifacts.identify(ROOT / 'apps/dx100') != before:
        raise Failure('vendored DX100 source changed during certification')
    if identity and artifacts.identify(tree)['sha256'] != identity['tree_sha256']:
        raise Failure('candidate source tree changed during certification; results are not bound to the patched identity')
    verdict = 'certified' if matrix and all(c['status'] == 'passed' for c in matrix) and controls and all(c['status'] == 'rejected' for c in controls) else 'failed'
    clauses = clause_controls(entry, controls, plugin) if identity else None
    if clauses and any(row['enforceable'] and not row['matched'] for row in clauses):
        verdict = 'failed'
    if not procedures.unchanged(sources_before, procedures.manifest(procedure, library_root, plugin)):
        raise Failure('certification source files changed during execution; results are not bound to one source identity')
    if not calibrate:
        current_catalog = Library(library_root, store=store)
        try:
            current_content_sha256 = current_catalog.content_sha256(entry_id)
            current_dependencies = current_catalog.dependency_pins(entry_id)
        except ValueError as exc:
            raise Failure('normative library dependency identity disappeared during execution: ' + str(exc)) from None
        if content_sha256 != current_content_sha256:
            raise Failure('normative library entry changed during execution; results are not bound to one content identity')
        if dependencies != current_dependencies:
            raise Failure('normative library dependencies changed during execution; results are not bound to one dependency identity')
    record = workflow.record('certification', 'certification.' + uuid.uuid4().hex,
        entry={'id': entry_id, 'content_sha256': content_sha256},
        dependencies=dependencies,
        command=command,
        host={'hostname': socket.gethostname(), 'system': platform.system(), 'architecture': platform.machine(), 'compiler': compiler()},
        matrix=matrix, negative_controls=controls, verdict=verdict, evidence_basis=procedure.evidence_basis,
        evidence_kind='execution', created_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if identity:
        record['candidate'] = identity
        record['clause_controls'] = clauses
    if native_entry is not None:
        record['profile'] = native_profile  # ticket 75
        if native_schedule is not None:
            record['profile']['schedule'] = native_schedule   # certify 1.4 and later: the random run order
    (folder / 'certification.json').write_text(json.dumps(record, indent=2) + '\n')
    workflow.persist(store.dir, record, create=True)
    return record


def register_cli(commands):
    sub = commands.add_parser('certify', help='Certify a typed-library lowering, a library operation (--profile) or a '
                                              'candidate artifact of a rewrite contract (DX100 or native-CPU)')
    sub.add_argument('entry_id', nargs='?')
    group = sub.add_mutually_exclusive_group()
    group.add_argument('--candidate')
    group.add_argument('--snapshot')
    sub.add_argument('--patch')
    sub.add_argument('--calibrate', action='store_true')
    sub.add_argument('--tile-sizes', default='16384,1024')
    sub.add_argument('--threads', type=int, default=4)
    sub.add_argument('--sources', default='0')
    sub.add_argument('--runs-dir', type=Path)
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--library', type=Path, default=ROOT / 'library')
    # Ticket 49 (2026-10-03 ET): library operations certify against a profile.
    sub.add_argument('--profile', help='certification profile (library operations)')
    sub.add_argument('--seed', type=int, help='fixed case seed (default: chosen after the candidate exists)')
    # Ticket 75 (2026-10-05 ET): bind a --snapshot/--patch run to an Extensa candidate record (read only).
    sub.add_argument('--candidate-record', type=Path,
                     help='candidate record file whose artifact the patched tree must reproduce')
    # 2026-10-05 ET (code-review fixes F3, F4): each command family has its own version table
    # (swdb.certification_procedures); the help text is generated from it.
    families = ', '.join(f"{family.replace('_', ' ')} {'/'.join(table)} (default {procedures.DEFAULTS[family]})"
                         for family, table in procedures.PROCEDURES.items())
    sub.add_argument('--command-version', choices=procedures.all_versions(), default=None,
                     help='certify command version of the entry\'s command family: ' + families)
    return sub


def run_cli(args):
    if getattr(args, 'profile', None):
        from swdb.library_operations import certify_cli
        return certify_cli(args)
    try:
        sizes = tuple(int(x) for x in args.tile_sizes.split(','))
        sources = tuple(int(x) for x in args.sources.split(','))
    except ValueError:
        raise UsageError('tile sizes and sources must be comma-separated integers') from None
    record = certify(Store(Path(args.records)), args.entry_id, runs_dir=args.runs_dir, library=args.library,
                     candidate=args.candidate, snapshot=args.snapshot, patch=args.patch, calibrate=args.calibrate,
                     tile_sizes=sizes, threads=args.threads, sources=sources,
                     candidate_record=getattr(args, 'candidate_record', None),
                     version=getattr(args, 'command_version', None))
    print(json.dumps({'id': record['id'], 'verdict': record['verdict'], 'matrix_cells': len(record['matrix']),
                      'negative_controls': len(record['negative_controls'])}, indent=2))
    return 0 if record['verdict'] == 'certified' else 1

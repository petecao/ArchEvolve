"""Executable DX100 library and BFS candidate certification (2026-10-03 ET).

This is finite strict-functional evidence, never target timing or a formal proof.
Controls count only after compilation and a named runtime rejection.
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
from collections import deque

from swdb import artifacts, paths, workflow
from swdb.cli import Failure, UsageError
from swdb.store import Store

VERSION = '1.0'
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
// Evaluator-owned preservation check, inserted into a private build copy.
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


def execute(command, log, *, cwd=None, threads=4, timeout=180):
    environment = {**os.environ, 'OMP_NUM_THREADS': str(threads), 'OMP_DYNAMIC': 'FALSE'}
    try:
        process = subprocess.run([str(x) for x in command], cwd=cwd, env=environment,
                                 capture_output=True, text=True, timeout=timeout)
        result = {'command': [str(x) for x in command], 'returncode': process.returncode,
                  'stdout': process.stdout, 'stderr': process.stderr, 'timeout': False}
    except subprocess.TimeoutExpired as exc:
        result = {'command': [str(x) for x in command], 'returncode': None,
                  'stdout': (exc.stdout or b'').decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ''),
                  'stderr': (exc.stderr or b'').decode() if isinstance(exc.stderr, bytes) else (exc.stderr or ''), 'timeout': True}
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
            mutant = folder / f'{operation}-{size}-{name}'
            control_build = compile_cpp(driver, mutant, library, tile_size=size, threads=threads, defines=defines)
            if control_build['returncode'] != 0:
                controls.append({'id': name, 'tile_size': size, 'status': 'invalid', 'reason': 'build failed', 'build': control_build})
                continue
            run = execute([mutant, operation, name], mutant.with_suffix('.run.json'), threads=threads)
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
    if snapshot.get('context', {}).get('source_derivation'):
        script = ROOT / 'scripts/prepare_dx100_scalar_snapshot.py'
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


def create_peter_patch(store, output, library=None):
    """Produce the deliverable patch without changing a vendored source byte."""
    library = Path(library or ROOT / 'library')
    import difflib
    with tempfile.TemporaryDirectory(prefix='swdb-peter-patch-', dir='/private/tmp') as temporary:
        tree, _ = materialize_snapshot(store, DEFAULT_SNAPSHOT, Path(temporary))
        original = (tree / BFS).read_text()
        source = peter_source(original)
        header = (library / 'dx100/dxc_lowering.hpp').read_text()
        diff = ''.join(difflib.unified_diff(original.splitlines(True), source.splitlines(True),
                                          fromfile='a/' + BFS, tofile='b/' + BFS))
        diff += ''.join(difflib.unified_diff([], header.splitlines(True), fromfile='/dev/null', tofile='b/' + HEADER))
        Path(output).write_text(diff)
    return {'patch': str(Path(output).resolve()), 'header_sha256': artifacts.file_hash(library / 'dx100/dxc_lowering.hpp')}


def graph_oracle(path, source):
    """Independent exact-depth counts from immutable normalized serialized CSR."""
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


def instrument_source(source, *, calibrate=False):
    statement = AUTHOR_FRONTIER_TEXT if calibrate else FRONTIER_TEXT
    if source.count(statement) != 1:
        raise Failure('BFS frontier logging statement differs from the protected exact text')
    # Protect the source kernel verifier and the standard harness's PASS rendering.
    if source.count('bool BFSVerifier(') != 1:
        raise Failure('BFS correctness check is missing or ambiguous')
    source = source.replace(statement, 'swdb_certification_frontier(queue);\n        ' + statement)
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
    mutations = {
        'shared_context': ('dxc_context c=swdb_contexts[omp_get_thread_num()];', 'dxc_context c=swdb_contexts[0];'),
        'skipped_cas_recheck': ('if(claimed){parent[v]=u;lqueue.push_back(v);}', 'if(hint<0){parent[v]=u;lqueue.push_back(v);}'),
        'dropped_continuation': ('for(;;){', 'for(int swdb_once=0;swdb_once<1;++swdb_once){'),
        'chunk_off_by_one': ('std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end))', 'std::min(begin+size_t(SWDB_CHUNK_SIZE)+1,size_t(queue.shared_out_end))'),
        'dropped_wait': ('__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);', '/* negative control: omitted result waits */'),
        'read_before_wait': ('__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);', 'if(__dxc_tile_pointer<int>(c.tile[5])[0]==int32_t(0xa5a5a5a5)){std::fprintf(stderr,"SWDB_DIFFERENTIAL_MISMATCH:read_before_wait\\n");std::_Exit(87);} __dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);'),
        'index_wrap': ('__dxc_const_i32(begin,c.reg[0]);', '__dxc_const_i32(INT32_MAX,c.reg[0]);'),
        'forged_frontier': ('if(claimed){parent[v]=u;lqueue.push_back(v);}', 'if(claimed){parent[v]=u;lqueue.push_back(v); static std::atomic<bool> swdb_forged(false); if(!swdb_forged.exchange(true))lqueue.push_back(v);}'),
    }
    if name not in mutations:
        raise Failure('unknown rewrite control')
    before, after = mutations[name]
    if source.count(before) != 1:
        raise Failure('candidate source lacks a unique negative-control mutation site: ' + name)
    mutated = source.replace(before, after, 1)
    if name == 'forged_frontier':
        # This control deliberately prints the oracle's true counts at every depth,
        # even though it double-enqueues. Only trusted queue inspection can reject it.
        forged = 'static unsigned swdb_forged_level=0; static const unsigned swdb_forged_counts[]={1,4200,17000};\n'
        mutated = forged + mutated.replace('<< queue.size() << " elements"', '<< swdb_forged_counts[swdb_forged_level++] << " elements"', 1)
    return mutated


def certify_bfs(tree, library, folder, tile_sizes, threads, sources, *, calibrate=False, threshold=64):
    graphs = matrix_graphs(folder, library, threads)
    source = (tree / BFS).read_text()
    if calibrate:
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
    source_path = tree / BFS
    for size in tile_sizes:
        source_path.write_text(instrument_source(source, calibrate=calibrate))
        output = folder / f'bfs-{size}'
        build = compile_cpp(source_path, output, library, tile_size=size, threads=threads, tree=tree,
                            defines=['-DMAA'] if calibrate else [])
        if build['returncode'] != 0:
            matrix.append({'tile_size': size, 'status': 'failed', 'reason': 'build failed', 'build': build})
            continue
        for graph_name, graph in graphs:
            for source_vertex in sources:
                counts = graph_oracle(graph, source_vertex)
                run = execute([output, '-f', graph, '-r', source_vertex, '-n', '1', '-v'], folder / f'{graph_name}-{size}-{source_vertex}.json', threads=threads)
                passed, reason = judge_bfs(run, counts, calibrate=calibrate, threshold=threshold)
                matrix.append({'graph': graph_name, 'graph_sha256': artifacts.file_hash(graph), 'source': source_vertex,
                               'oracle_frontier_counts': counts, 'tile_size': size, 'threads': threads,
                               'status': 'passed' if passed else 'failed', 'reason': reason, 'build': build, 'run': run})
        names = ['shared_context', 'dropped_continuation', 'oversized_chunk', 'wrong_store_wait'] if calibrate else list(_CONTROL_EXPECTED)
        graph = graphs[-1][1]
        counts = graph_oracle(graph, sources[0])
        for name in names:
            # Oversized chunk is specifically a 1,024-element build control.
            if name == 'oversized_chunk' and size != 1024:
                continue
            mutant = _rewrite_control(instrument_source(source, calibrate=calibrate), name, calibrate=calibrate)
            source_path.write_text(mutant)
            output_mutant = folder / f'bfs-{size}-{name}'
            control_build = compile_cpp(source_path, output_mutant, library, tile_size=size, threads=threads, tree=tree,
                                        defines=['-DMAA'] if calibrate else [])
            if control_build['returncode']:
                controls.append({'id': name, 'tile_size': size, 'status': 'invalid', 'reason': 'build failed', 'build': control_build})
                continue
            run = execute([output_mutant, '-f', graph, '-r', sources[0], '-n', '1', '-v'], folder / f'control-{size}-{name}.json', threads=threads)
            passed, reason = judge_bfs(run, counts, calibrate=calibrate, threshold=threshold)
            named = re.findall(r'SWDB_(?:STRICT_ASSERT|DIFFERENTIAL_MISMATCH|PRESERVATION_FAIL):([a-z_]+)', run['stdout'] + run['stderr'])
            semantic_rejection = reason in {'verifier', 'frontier_size_equality', 'execution_witness'} and run['returncode'] == 0
            expected_checks = _CONTROL_EXPECTED.get(name, set())
            if calibrate:
                expected_checks = {'shared_context': {'thread_ownership_tile', 'thread_ownership_register'}, 'dropped_continuation': set(),
                                   'oversized_chunk': {'tile_truncation'}, 'wrong_store_wait': {'read_before_wait'}}[name]
            asserted = bool(expected_checks.intersection(named))
            # Runtime preservation guards are a named semantic check, including duplicate enqueue.
            semantic_rejection = semantic_rejection or ('duplicate_frontier' in named and reason == 'frontier_size_equality')
            rejected = not passed and not run['timeout'] and (semantic_rejection or asserted)
            status = 'rejected' if rejected else 'survived' if passed else 'invalid'
            controls.append({'id': name, 'tile_size': size, 'status': status, 'reason': reason,
                             'named_checks': named, 'build': control_build, 'run': run})
    source_path.write_text(source)  # This is a private build copy, never a vendored tree.
    return matrix, controls


_CONTROL_EXPECTED = {
    'shared_context': {'thread_ownership_tile', 'thread_ownership_register'},
    'skipped_cas_recheck': {'duplicate_frontier'}, 'dropped_continuation': set(),
    'chunk_off_by_one': {'tile_truncation'}, 'dropped_wait': {'byte_offset_overflow', 'read_before_wait'},
    'read_before_wait': {'read_before_wait'}, 'index_wrap': {'stream_bounds', 'byte_offset_overflow'},
    'forged_frontier': {'duplicate_frontier'},
}


def check_candidate_scope(tree, snapshot):
    """Every changed source byte belongs to this BFS rewrite's declared files."""
    original = {item['path']: item for item in snapshot['artifact']['files']}
    current = {item['path']: item for item in artifacts.manifest(tree)}
    changed = {path for path in set(original) | set(current) if original.get(path) != current.get(path)}
    if changed - {BFS, HEADER} or BFS not in changed:
        raise UsageError('BFS contract permits only the BFS rewrite and canonical lowering header; '
                         'changed files: ' + ', '.join(sorted(changed)))
    return sorted(changed)


def source_digest(library_root):
    files = sorted(p for p in (library_root / 'dx100').rglob('*') if p.is_file()) + [Path(__file__)]
    return artifacts.digest([{'path': p.relative_to(library_root).as_posix() if library_root in p.parents else 'swdb/certification.py',
                              'sha256': artifacts.file_hash(p)} for p in files])


def certify(store, entry_id=None, *, runs_dir=None, library=None, candidate=None,
            snapshot=None, patch=None, calibrate=False, tile_sizes=(16384, 1024), threads=4, sources=(0,)):
    from swdb.library import Library
    library_root = Path(library or ROOT / 'library').resolve()
    catalog = Library(library_root, store=store)
    problems = catalog.validate()
    if problems:
        raise UsageError('typed library is invalid: ' + str(problems[0]))
    if threads != 4 or tuple(sorted(set(tile_sizes))) != (1024, 16384):
        raise UsageError('DX100 certification requires the full matrix: tile sizes 16384,1024 and four threads')
    if not sources or any(type(s) is not int or s < 0 for s in sources):
        raise UsageError('sources must be nonnegative vertex IDs')
    if bool(snapshot) != bool(patch) or (candidate and snapshot):
        raise UsageError('use --candidate or the paired --snapshot/--patch input')
    if not calibrate and not entry_id:
        raise UsageError('certification requires an entry ID')
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
    base = artifacts.external_directory(runs_dir or '/private/tmp/swdb-certification')
    folder = base / ('certify-' + uuid.uuid4().hex)
    folder.mkdir()
    before = artifacts.identify(ROOT / 'apps/dx100')
    command_hash = source_digest(library_root)
    identity = None
    if calibrate:
        tree = folder / 'source'
        artifacts.copy_snapshot(ROOT / 'apps/dx100', tree)
        matrix, controls = certify_bfs(tree, library_root, folder, tile_sizes, threads, sources, calibrate=True)
    elif candidate or snapshot:
        if entry.get('kind') != 'rewrite_contract':
            raise UsageError('candidate-artifact certification requires a rewrite contract')
        if candidate:
            data = store.get(candidate, 'candidate')
            if not data:
                raise UsageError('unknown candidate artifact')
            original = artifacts.verify(data['artifact'])
            tree = folder / 'source'
            artifacts.copy_snapshot(original, tree)
            snapshot_id = data.get('source_snapshot')
            original_snapshot = store.get(snapshot_id, 'source_snapshot')
        else:
            tree, original_snapshot = materialize_snapshot(store, snapshot, folder)
            snapshot_id = snapshot
            apply_patch(tree, patch)
        if not original_snapshot:
            raise Failure('candidate has no registered source snapshot')
        artifacts.check_protections(tree, original_snapshot['protections'])
        changed_files = check_candidate_scope(tree, original_snapshot)
        header = tree / HEADER
        if not header.is_file() or artifacts.file_hash(header) != artifacts.file_hash(library_root / 'dx100/dxc_lowering.hpp'):
            raise Failure('candidate must ship the byte-identical canonical lowering header')
        identity = {'contract': entry_id, 'contract_sha256': content_sha256,
                    'tree_sha256': artifacts.identify(tree)['sha256'], 'snapshot': snapshot_id, 'changed_files': changed_files}
        if candidate:
            identity['id'] = candidate
        threshold = 64
        matrix, controls = certify_bfs(tree, library_root, folder, tile_sizes, threads, sources, threshold=threshold)
    else:
        if entry.get('kind') not in {'lowering', 'intrinsic', 'library_operation'}:
            raise UsageError('entry requires a candidate artifact or a differential-test driver')
        matrix, controls = certify_lowering(entry_id, library_root, folder, tile_sizes, threads)
    if artifacts.identify(ROOT / 'apps/dx100') != before:
        raise Failure('vendored DX100 source changed during certification')
    if identity and artifacts.identify(tree)['sha256'] != identity['tree_sha256']:
        raise Failure('candidate source tree changed during certification; results are not bound to the patched identity')
    verdict = 'certified' if matrix and all(c['status'] == 'passed' for c in matrix) and controls and all(c['status'] == 'rejected' for c in controls) else 'failed'
    if source_digest(library_root) != command_hash:
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
        command={'version': VERSION, 'sources_sha256': command_hash},
        host={'hostname': socket.gethostname(), 'system': platform.system(), 'architecture': platform.machine(), 'compiler': compiler()},
        matrix=matrix, negative_controls=controls, verdict=verdict, evidence_basis='simulated',
        evidence_kind='execution', created_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if identity:
        record['candidate'] = identity
    (folder / 'certification.json').write_text(json.dumps(record, indent=2) + '\n')
    workflow.persist(store.dir, record, create=True)
    return record


def register_cli(commands):
    sub = commands.add_parser('certify', help='Certify typed DX100 lowerings or BFS candidate artifacts')
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
                     tile_sizes=sizes, threads=args.threads, sources=sources)
    print(json.dumps({'id': record['id'], 'verdict': record['verdict'], 'matrix_cells': len(record['matrix']),
                      'negative_controls': len(record['negative_controls'])}, indent=2))
    return 0 if record['verdict'] == 'certified' else 1

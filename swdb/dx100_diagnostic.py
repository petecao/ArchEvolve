"""Exact-preprocessor simulated source-region diagnostics. Updated: 2026-09-25."""

import json
import hashlib
from pathlib import Path
import sys

from swdb import artifacts, bfs_discovery, paths
from swdb.bfs_native import _protect_driver_macros
from swdb.bfs_profiling import _discovery_settings
from swdb.cli import Failure
from swdb.dx100 import _bounded_process


def prepare(session, request, candidate, root, source, compiler, flags, includes, build_directory):
    """Discover and instrument candidate scopes without modifying its artifact."""
    settings = request.get('discovery', {})
    if not isinstance(settings, dict) or settings.keys() - {'library', 'resource_dir'}:
        raise Failure('DX100 discovery permits library/resource_dir only; preprocessor flags come from the real build')
    limits = request['budget']
    def run(name, argv, seconds):
        return _bounded_process(session, name, argv, seconds, limits['memory_gib'], limits['storage_gib'])
    macro = run('diagnostic_preprocessor', [str(compiler), *flags, '-dM', '-E', '-v', '-x', 'c++', '/dev/null'], 30)
    library, arguments = _discovery_settings(request, compiler, flags, includes, macro)
    definition = session.folder / 'discovery-request.json'
    definition.write_text(json.dumps({'source': str(source), 'arguments': arguments, 'library': str(library)}))
    output = session.folder / 'discovery.json'
    run('diagnostic_discovery', [sys.executable, str(Path(bfs_discovery.__file__)), str(definition), str(output)], 120)
    found = json.loads(output.read_text())
    rows = found.pop('regions')
    if not rows or len(rows) > 10000:
        raise Failure('diagnostic discovery requires between 1 and 10000 supported source scopes')
    original_runtime = paths.HOME / 'tools/bfs_profile/gem5_runtime.hpp'
    _protect_driver_macros(candidate, root, extra_text=original_runtime.read_text())
    runtime = build_directory / 'gem5_runtime.hpp'
    runtime.write_bytes(original_runtime.read_bytes())
    rewritten = build_directory / 'instrumented_bfs.cc'
    rewritten.write_bytes(bfs_discovery.instrument(source, rows))
    for row in rows:
        row['path'] = source.relative_to(root).as_posix()
        row['source_artifact_sha256'] = candidate['artifact']['sha256']
    for row in rows:
        enclosing = [item for item in rows if item['kind'] == 'function'
                     and item['byte_range'][0] <= row['byte_range'][0]
                     and item['byte_range'][1] >= row['byte_range'][1]]
        if enclosing:
            function = min(enclosing, key=lambda item: item['byte_range'][1] - item['byte_range'][0])
            row['function_region'] = function['id']
            row['referenced_types'] = list(function.get('referenced_types', []))
    found.update(library_sha256=artifacts.file_hash(library.resolve()),
                 pass_sha256=artifacts.file_hash(bfs_discovery.__file__),
                 actual_build_flags=flags, collector='dx100.m5_rpns.source_scopes.v1')
    return {'instrumented_source': {'path': str(rewritten), 'sha256': artifacts.file_hash(rewritten)},
            'runtime': {'path': str(runtime), 'sha256': artifacts.file_hash(runtime)},
            'discovery': found, 'regions': rows,
            'quantity': 'per-thread simulated elapsed intervals summed across threads; includes waiting and overlap',
            'attribution': 'inclusive includes nested guarded work; exclusive subtracts nested guarded intervals on the same thread',
            'difference': 'scope guards, m5_rpns reads, thread-local stacks and atomic counters; diagnostic times cannot replace primary timing'}


def counters(log, count, *, return_sha256=False):
    """Read exactly one post-seal diagnostic report with bounded integer data."""
    found, sealed = [], 0
    digest = hashlib.sha256()
    with Path(log).open('rb') as stream:
        for raw in stream:
            digest.update(raw)
            line = raw.decode(errors='replace')
            if line.strip() == 'SWDB_DX100_ROI_SEALED':
                sealed += 1
            if line.startswith('SWDB_DX100_REGIONS '):
                if sealed != 1 or len(line) > count * 256 + 4096:
                    raise Failure('diagnostic region output is unsealed or exceeds its bound')
                found.append(json.loads(line.split(' ', 1)[1]))
    if sealed != 1 or len(found) != 1:
        raise Failure('diagnostic requires exactly one post-seal region report')
    value = found[0]
    if (not isinstance(value, dict) or value.get('format') != 'swdb.dx100.regions.v1'
            or value.get('clock') != 'm5_rpns' or type(value.get('errors')) is not int or value['errors'] != 0):
        raise Failure('simulated region clock or nested accounting failed')
    rows = value.get('regions')
    if not isinstance(rows, list) or len(rows) != count:
        raise Failure('simulated region counter inventory differs from compiler discovery')
    for index, row in enumerate(rows):
        if (not isinstance(row, dict) or type(row.get('index')) is not int or row['index'] != index
                or any(type(row.get(key)) is not int or not 0 <= row[key] < 2**64
                       for key in ('inclusive_ns', 'exclusive_ns', 'invocations'))
                or row['exclusive_ns'] > row['inclusive_ns']):
            raise Failure('invalid simulated region counter')
    return (rows, digest.hexdigest()) if return_sha256 else rows

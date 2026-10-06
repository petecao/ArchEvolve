"""Observed MAA coverage inside an exact statistics tick interval. Updated: 2026-09-27.

Updated 2026-10-05 ET (ticket 80, spec review C16): a new execution record whose kernel plug-in names its result
otherwise than "parent" (BC: "score") takes its competing-update labels from the plug-in and records
`context.coverage_labels` (`LABELS_V2`). Records without that field keep the BFS labels, so every existing
record, BFS or BC, revalidates unchanged.
"""

import gzip
import hashlib
from pathlib import Path
import re
import time
import zlib

from swdb import artifacts
from swdb.cli import Failure

TRANSPORT = 'gem5-gzip.v1'
TRACE_NAME = 'roi-debug.trace.gz'
TRACE_FORMAT = 'swdb.dx100.debug-trace.v1'
#: Ticket 80 (C16): the label version a new non-BFS execution record carries in `context.coverage_labels`.
LABELS_V2 = 'swdb.dx100.coverage-labels.v2'


def labels(plugin=None, version=None):
    """The competing-update case key, storage key and result noun of a coverage result.

    Without a version (every record before ticket 80, and every BFS record) these are BFS's labels. Under
    `LABELS_V2` they come from the kernel plug-in's `result_noun`."""
    noun = 'parent'
    if version == LABELS_V2:
        noun = getattr(plugin, 'result_noun', None) or 'parent'
    elif version is not None:
        raise Failure(f'unknown coverage label version {version!r}')
    return {'case': f'competing_{noun}_updates', 'storage': f'{noun}_storage', 'noun': noun}


def labels_version(plugin):
    """The label version a NEW execution record of this plug-in records: None for a result named "parent"
    (BFS records stay unchanged), `LABELS_V2` for any other result noun."""
    return None if (getattr(plugin, 'result_noun', None) or 'parent') == 'parent' else LABELS_V2


def _deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise Failure('debug trace read exceeded the existing caller deadline')


def _hash(path, deadline):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            _deadline(deadline)
            digest.update(block)
    _deadline(deadline)
    return digest.hexdigest()


def trace_lines(trace, identity, deadline=None):
    """Hash every decoded byte, require complete gzip, and never expand to disk."""
    expected = trace if isinstance(trace, dict) else None
    path = Path(expected['path'] if expected else trace)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise Failure('debug trace must be an absolute regular file')
    with path.open('rb') as stream:
        if path.stat().st_size < 18 or stream.read(2) != b'\x1f\x8b':
            raise Failure('incomplete or corrupt gzip debug trace: missing gzip header/trailer')
    compressed = _hash(path, deadline)
    if expected and expected.get('sha256') != compressed:
        raise Failure('compressed debug trace differs from retained identity')
    decoded, size, lines = hashlib.sha256(), 0, 0
    try:
        with gzip.open(path, 'rb') as stream:
            while True:
                _deadline(deadline)
                line = stream.readline(1024 * 1024 + 1)
                if not line:
                    break
                if len(line) > 1024 * 1024:
                    raise Failure('debug trace line exceeds the 1 MiB reader bound')
                decoded.update(line); size += len(line); lines += 1
                yield lines, line.decode('utf-8', errors='strict')
    except (OSError, EOFError, UnicodeError, zlib.error) as exc:
        raise Failure('incomplete or corrupt gzip debug trace: ' + str(exc)) from exc
    if _hash(path, deadline) != compressed:
        raise Failure('debug trace changed during streaming read')
    identity.update(format=TRACE_FORMAT, transport=TRANSPORT, path=str(path), sha256=compressed,
                    bytes=path.stat().st_size, uncompressed_sha256=decoded.hexdigest(),
                    uncompressed_bytes=size, lines=lines)
    if expected and artifacts.digest(identity) != artifacts.digest(expected):
        raise Failure('decoded debug stream differs from retained identity')


def trace_reference(evaluation):
    """Reopen only an explicitly declared, exact-execution compressed treatment."""
    context = evaluation.get('context', {})
    verification = evaluation.get('request', {}).get('verification') or {}
    requested = verification.get('trace_transport')
    declared = context.get('trace_transport')
    reference = context.get('debug_trace')
    checks = evaluation.get('correctness', {}).get('checks', [])
    retained = [check.get('coverage', {}).get('debug_trace') for check in checks]
    if 'trace_transport' not in verification:
        explicit_files = [arg for stage in evaluation.get('stages', []) if stage.get('stage') == 'simulation'
                          for arg in stage.get('command', [])
                          if isinstance(arg, str) and arg.startswith('--debug-file')]
        if explicit_files or declared is not None or reference is not None or any(item is not None for item in retained):
            raise Failure('legacy execution cannot be relabeled with compressed debug evidence')
        return None
    stages = [stage for stage in evaluation.get('stages', []) if stage.get('stage') == 'simulation']
    if (requested != TRANSPORT or declared != TRANSPORT or not isinstance(reference, dict)
            or len(stages) != 1 or reference.get('format') != TRACE_FORMAT
            or reference.get('transport') != TRANSPORT
            or reference.get('path') != str(Path(stages[0]['log']).parent / 'simulation' / TRACE_NAME)
            or any(artifacts.digest(item) != artifacts.digest(reference) for item in retained)):
        raise Failure('compressed debug trace is not bound to this exact execution and coverage')
    command = stages[0].get('command', [])
    expected_flags = 'MAATrace,MAARangeFuser,MAAIndirect' if verification.get('coverage') else 'MAATrace'
    if (not isinstance(command, list) or any(not isinstance(arg, str) for arg in command)
            or [arg for arg in command if arg.startswith('--debug-file')] != ['--debug-file=' + reference['path']]
            or [arg for arg in command if arg.startswith('--debug-flags')] != ['--debug-flags=' + expected_flags]
            or context.get('debug_flags') != expected_flags
            or context.get('instrumentation', {}).get('debug_flags') != expected_flags):
        raise Failure('compressed trace command or unchanged debug flags differ from the request')
    return reference


def validate_trace(evaluation, deadline=None, store=None):
    reference = trace_reference(evaluation)
    if reference is not None:
        if not Path(reference['path']).exists():
            from swdb.retention import retained
            receipt = retained(store, reference, evaluation['id'])
            if receipt:
                # Coverage counters were decoded and frozen before pruning.
                # Return the exact original identity; callers compare it by digest.
                return reference
        from swdb.dx100 import _file
        from swdb.dx100_profile import statistics
        context = evaluation['context']
        stats = _file(context['statistics'], 'compressed-trace ROI statistics')
        intervals = statistics(stats, deadline if deadline is not None else float('inf'))
        if len(intervals) != 1:
            raise Failure('compressed trace needs exactly one sealed statistics interval')
        stage = next(stage for stage in evaluation['stages'] if stage['stage'] == 'simulation')
        log = _file({'path': stage['log'], 'sha256': stage['log_sha256']}, 'compressed-trace stdout')
        from swdb import kernels
        actual = observe(log, intervals[0]['values'], context['configuration']['tile_elements'],
                         trace=reference, deadline=deadline,
                         read_only=evaluation.get('request', {}).get('verification', {}).get('read_only', False),
                         plugin=kernels.by_gem5_checker(context.get('verifier')),
                         label_version=context.get('coverage_labels'))
        checks = evaluation.get('correctness', {}).get('checks', [])
        if len(checks) != 1 or any(artifacts.digest(value) != artifacts.digest(checks[0].get('coverage', {}).get(key))
                                   for key, value in actual.items()):
            raise Failure('retained coverage differs from the complete compressed debug stream')
    return reference


def observe(log, values, tile_elements, *, trace=None, deadline=None, read_only=False, plugin=None,
            label_version=None):
    # Ticket 39 (2026-10-03 ET): the result-storage marker and the read-only
    # instruction-mix rule come from the checker's kernel plug-in (BFS default).
    # Ticket 80 (C16): `label_version` selects the result labels (absent: BFS's, as recorded before).
    from swdb import kernels
    plugin = plugin or kernels.BFS
    marker = plugin.gem5_storage_marker
    names = labels(plugin, label_version)
    try:
        end = int(values["finalTick"])
        start = end - int(values["simTicks"])
        if start < 0 or end <= start:
            raise ValueError()
    except (KeyError, ValueError):
        return {"state": "unobserved", "reason": "exact finalTick/simTicks interval is unavailable",
                "completed_trace_units": {}, "full_tiles": "unobserved", "tail_tiles": "unobserved",
                names['case']: "unobserved"}
    units, tile_sizes, current, blocks, stores, collisions = {}, {}, {}, {}, {}, {}
    parent_storage = None
    truncated = False
    trace_identity = {}
    opcode_counts, pending_opcodes = {}, {}
    def lines():
        with log.open(errors="replace") as stream:
            for number, line in enumerate(stream, 1):
                _deadline(deadline)
                yield number, line, 'stdout'
        if trace is not None:
            for number, line in trace_lines(trace, trace_identity, deadline):
                yield number, line, 'debug_trace'
    for number, line, origin in lines():
        storage = (re.fullmatch(re.escape(marker) + r" address=([a-f0-9]+) count=(\d+) element_bytes=4\s*", line)
                   if marker and origin == 'stdout' and line.startswith(marker + " ") else None)
        if storage and origin == 'stdout':
            parent_storage = {"virtual_address": int(storage[1], 16), "count": int(storage[2]), "line": number}
            if trace is not None:
                parent_storage['stream'] = 'stdout'
        if trace is not None and origin != 'debug_trace':
            continue
        match = re.match(r"\s*(\d+):", line)
        if not match or not start <= int(match[1]) <= end:
            continue
        tick = int(match[1])
        if read_only:
            started = re.search(r'\b([SIAR])\[(\d+)\] Start \[.*\bopcode\(([A-Z0-9_]+)\)', line)
            ended = re.search(r'\b([SIAR])\[(\d+)\] End \[', line)
            if started:
                pending_opcodes[(started[1], started[2])] = started[3]
            if ended:
                opcode = pending_opcodes.pop((ended[1], ended[2]), None)
                if opcode is not None:
                    opcode_counts[opcode] = opcode_counts.get(opcode, 0) + 1
        # Necessary literal prefixes avoid five full regex scans on unrelated
        # debug messages. Patterns remain the authority; lines are never skipped
        # from decoding, hashing, numbering, deadline checks, or other matches.
        finished = re.search(r"\b([SIAR])\[\d+\] End \[", line) if ' End [' in line else None
        if finished:
            units[finished[1]] = units.get(finished[1], 0) + 1
        size = re.search(r"\bR\[\d+\] executeInstruction: .*tile size: (\d+)", line) if 'tile size: ' in line else None
        if size:
            n = int(size[1]); tile_sizes[n] = tile_sizes.get(n, 0) + 1
        issued = re.search(r"\bI\[(\d+)\] Start \[(.*)", line) if ' Start [' in line else None
        if issued:
            instruction = issued[2]
            base = re.search(r"baseAddr\(0x([a-f0-9]+)\)", instruction)
            current[int(issued[1])] = (int(base[1], 16) if base and "opcode(INDIR_ST_VECTOR)" in instruction
                and "datatype(INT32)" in instruction else None)
            blocks.pop(int(issued[1]), None)
        received = re.search(r"\bI\[(\d+)\] \w+: \d+ entries received for addr\(0x([a-f0-9]+)\)", line) if ' entries received for addr(0x' in line else None
        if received:
            blocks[int(received[1])] = int(received[2], 16)
        stored = re.search(r"\bI\[(\d+)\] \w+: new_data\[(\d+)\] = SPD\[\d+\]\[\d+\] = \d+/(-?\d+)/", line) if 'new_data[' in line else None
        if stored:
            unit, word, value = map(int, stored.groups())
            base = current.get(unit)
            if base is None or unit not in blocks:
                continue
            address = blocks[unit] + 4 * word
            key = (base, address)
            if key not in stores and len(stores) >= 500000:
                truncated = True
                continue
            previous = stores.get(key)
            if previous is not None and previous != value:
                record = collisions.setdefault(base, {"count": 0, "samples": []})
                record["count"] += 1
                if len(record["samples"]) < 8:
                    record["samples"].append({"physical_word_address": address, "prior_value": previous,
                                              "new_value": value, "tick": tick, "line": number})
                    if trace is not None:
                        record['samples'][-1]['stream'] = 'debug_trace'
            stores[key] = value
    parent_collisions = collisions.get(parent_storage["virtual_address"], {}) if parent_storage else {}
    full = tile_sizes.get(tile_elements, 0)
    tail = sum(count for size, count in tile_sizes.items() if 0 < size < tile_elements)
    result = {"state": "observed", "tick_interval": [start, end], "completed_trace_units": units,
        "address_space_contract": {"model_revision": "e4fc4afdf894f295442cef3604667a469fab8e62",
            "instruction_baseAddr": f"guest virtual; compared only with returned {names['noun']}.data()",
            "recvData_addr": "translated physical cache line; compared only with other physical words",
            "source_evidence": [
                {"path": "src/mem/MAA/IF.cc", "sha256": "fd7dd67f35f63ff6ed9ef0b8ce36cb60cc6d63b20fe9c0796e648bff82da6561", "lines": [38, 63]},
                {"path": "src/mem/MAA/IndirectAccess.cc", "sha256": "7e238a370f25ff5a7a1211548630a291d6358c32d8a199fc58bfacd37d1d35db", "lines": [494, 505]}]},
        "range_output_tile_sizes": {str(size): count for size, count in tile_sizes.items()},
        "full_tiles": {"state": "observed" if full else "unobserved", "count": full, "capacity": tile_elements},
        "tail_tiles": {"state": "observed" if tail else "unobserved", "count": tail, "capacity": tile_elements},
        names['case']: {"state": "observed" if parent_collisions.get("count", 0) else "unobserved",
            "count": parent_collisions.get("count", 0), "samples": parent_collisions.get("samples", []),
            names['storage']: parent_storage, "target_tracking_truncated": truncated,
            "definition": "Different signed32 vector-store values observed at the same physical word, from "
                          f"instructions whose virtual base is the returned {names['noun']} array."},
        "limits": "Positive counts prove these finite observed cases only. Graph topology is not substituted for executed updates; traces outside the selected ROI are excluded."}
    if trace is not None:
        result['debug_trace'] = trace_identity
    if read_only:
        result['completed_trace_opcodes'] = opcode_counts
        result['unmatched_trace_opcodes'] = len(pending_opcodes)
        # Count completion opcodes rather than graph topology or unit activity.
        stream = sum(value for key, value in opcode_counts.items() if key.startswith('STREAM_LD'))
        indirect = sum(value for key, value in opcode_counts.items() if key.startswith('INDIR_LD'))
        ranges = sum(value for key, value in opcode_counts.items() if key.startswith('RANGE'))
        alu = sum(value for key, value in opcode_counts.items() if key.startswith('ALU'))
        stores = sum(value for key, value in opcode_counts.items() if key.startswith('INDIR_ST'))
        observed = (plugin.read_only_rule(stream, indirect, ranges, alu, stores) and not pending_opcodes
            and sum(opcode_counts.values()) == sum(units.values())
            and units.get('S', 0) == stream and units.get('I', 0) == indirect
            and units.get('R', 0) == ranges and units.get('A', 0) == 0)
        result['read_only_executed'] = {'state': 'observed' if observed else 'unobserved',
            'count': int(observed), 'stream': stream, 'indirect': indirect, 'range': ranges,
            'alu': alu, 'indirect_stores': stores,
            'rule': plugin.read_only_rule_text}
    return result

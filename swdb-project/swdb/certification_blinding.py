"""Candidate certification with blinded controls and attributed rejections (certify 1.4).

Created: 2026-10-05 ET (ticket 76). Agent-decided under Yan-Ru's delegation; revisable.
Certify 1.3 (``swdb.certification_isolation``) stays available unchanged.

Certify 1.3 took every verdict from evaluator records and moved faults out of the candidate's
translation unit, but left four holes open (ticket 70). This module closes what can be closed in
one process and names what cannot:

1. **One binary, a blinded run plan.** Per tile size the candidate object, the record object and
   one seam object holding every fault are linked once. The positive matrix and every
   library-fault control run that same file with the same arguments, the same environment
   variable names and the same descriptor layout. The fault (or none) arrives on a pipe that
   trusted code drains before ``main``; a positive run's plan has the same length. All runs of a
   tile size, positive cells and controls, run in a fresh random order, so state carried between
   runs (for example a file the candidate writes) cannot tell a control from a positive run either.
2. **Attributed rejections.** The trusted seams record where a fault acted. A library-fault control
   counts as rejected only when its named check is attributable to that action on the candidate's
   own data (:data:`ATTRIBUTION`): a duplicate frontier vertex whose push is paired with a forged
   claim, or is the forged push copy; a strict failure inside the stream load the fault modified,
   or on a thread the fault acted on; a missing frontier vertex reached only through an edge the
   dropped continuation removed. A candidate that probes a seam and then misbehaves on purpose
   gains nothing: its deliberate failure is not the fault's, and the fault's own effect, if it
   amplifies it, is exactly what an honest candidate shows.
3. **Seam witness, frontier ledger.** Windows are read by trusted code from the queue object at each
   slide (the frontier inspection no longer runs in the candidate's function). Every positive run
   must show, from the same records, contract clause L4 directly: one frontier queue; each window
   equals the pushes made into it since the previous slide; every pushed vertex but the source was
   claimed by the pushing thread through the claim seam at ``base + 4 * vertex`` with one ``base``
   per run (for BFS, the returned parent array); and the DX100 gathered from that array whenever a
   frontier reached the threshold. Bypassing the claim or push seam therefore fails the positive
   matrix (``seam_witness``), whatever the controls do.

Residual threats are stated in ticket 76 (in-process memory introspection; data flow from DX100
tiles into claims is not traced).
"""
from __future__ import annotations

import os
import random
import re
import secrets
import struct
from collections import Counter, defaultdict, deque
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

VERSION = '1.4'
CHANNEL_ENV, PLAN_ENV = 'SWDB_CERT_RECORD_FD', 'SWDB_CERT_PLAN_FD'
FOLDER = 'dx100/certification/v1_4'
PRELUDE = FOLDER + '/prelude.hpp'
RECORD_SOURCE = FOLDER + '/record.cc'
SEAM_SOURCE = FOLDER + '/seams.cc'
RECORD_LIMIT = 512 * 1024 * 1024
# The seam object's fault indices (seams.cc `enum Fault`); 0 is no fault.
FAULT_INDEX = {None: 0, 'shared_context': 1, 'skipped_cas_recheck': 2, 'dropped_continuation': 3,
               'chunk_off_by_one': 4, 'dropped_wait': 5, 'read_before_wait': 6, 'index_wrap': 7,
               'forged_frontier': 8}
# How each library fault's rejection is attributed to the fault's own action.
ATTRIBUTION = {
    'skipped_cas_recheck': 'duplicate_after_forged_claim',
    'forged_frontier': 'duplicate_is_forged_push',
    'chunk_off_by_one': 'strict_inside_faulted_call',
    'index_wrap': 'strict_inside_faulted_call',
    'shared_context': 'strict_on_faulted_thread',
    'dropped_wait': 'strict_on_faulted_thread',
    'read_before_wait': 'strict_on_faulted_thread',
    'dropped_continuation': 'missing_vertex_behind_lost_edge',
}


# --- build and run -----------------------------------------------------------------------------------

class Build:
    """Objects and binaries of one candidate tree at one tile size (certify 1.4)."""

    def __init__(self, folder, library, tree, source_path, tile_size, threads):
        from swdb.certification import compiler
        from swdb.certification_isolation import _flags
        self.folder, self.library, self.tree = Path(folder), Path(library), Path(tree)
        self.source_path, self.tile_size, self.threads = Path(source_path), tile_size, threads
        self.folder.mkdir(parents=True, exist_ok=True)
        self.compiler = compiler()
        self.flags = _flags(self.library, self.tree, tile_size, threads)
        self._trusted = {}

    def _compile(self, source, output, extra=()):
        from swdb.certification import execute
        command = [self.compiler, *self.flags, *extra, '-c', str(source), '-o', str(output)]
        result = execute(command, Path(str(output) + '.build.json'), timeout=180)
        if result['returncode'] == 0:
            result['object_sha256'] = artifacts.file_hash(output)
        result['object'] = str(output)
        return result

    def candidate_object(self, text, label):
        self.source_path.write_text(text)
        extra = ['-Dmain=swdb_candidate_main', '-iquote', str(self.source_path.parent),
                 '-include', str(self.library / PRELUDE)]
        result = self._compile(self.source_path, self.folder / f'candidate-{label}.o', extra)
        result['source_sha256'] = artifacts.digest(text)
        return result

    def trusted_object(self, kind):
        if kind not in self._trusted:
            source = self.library / (RECORD_SOURCE if kind == 'record' else SEAM_SOURCE)
            result = self._compile(source, self.folder / f'{kind}-v14.o')
            if result['returncode']:
                raise Failure(f'trusted certification object failed to build ({kind}); see ' + result['log'])
            self._trusted[kind] = result
        return self._trusted[kind]

    def link(self, candidate, output):
        from swdb.certification import execute
        record, seams = self.trusted_object('record'), self.trusted_object('seams')
        command = [self.compiler, '-fopenmp', candidate['object'], record['object'], seams['object'],
                   '-o', str(output)]
        result = execute(command, Path(str(output) + '.link.json'), timeout=180)
        result.update(candidate_object_sha256=candidate.get('object_sha256'),
                      record_object_sha256=record['object_sha256'], seam_object_sha256=seams['object_sha256'],
                      binary=str(output), binary_sha256=artifacts.file_hash(output) if result['returncode'] == 0 else None)
        return result


def plan_line(fault, nonce):
    """The fixed-length plan line record.cc reads (43 bytes)."""
    line = f'plan 2 {FAULT_INDEX[fault]:02d} {nonce}\n'.encode('ascii')
    assert len(line) == 43
    return line


def run(binary, graph, source, log, threads, fault=None):
    """One run: a fresh record file and a plan pipe; stdout and stderr are only logged."""
    from swdb.certification import execute
    record = Path(str(log) + '.record')
    nonce = secrets.token_hex(16)
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    plan_read, plan_write = os.pipe()
    try:
        os.write(plan_write, plan_line(fault, nonce))
        os.close(plan_write)
        plan_write = None
        result = execute([binary, '-f', graph, '-r', source, '-n', '1', '-v'], log, threads=threads,
                         extra_env={CHANNEL_ENV: str(descriptor), PLAN_ENV: str(plan_read)},
                         pass_fds=(descriptor, plan_read))
    finally:
        os.close(descriptor)
        os.close(plan_read)
        if plan_write is not None:
            os.close(plan_write)
    result.update(record=str(record.resolve()), record_sha256=artifacts.file_hash(record),
                  plan={'fault': fault, 'nonce': nonce})
    return result


# --- records -------------------------------------------------------------------------------------------

_HEX = re.compile(r'[0-9a-f]{1,16}')
_EVENT = re.compile(r'([cC])(\d+):([0-9a-f]{1,16})|([pPd])(\d+):(\d+):(-?\d+)|r(\d+):(\d+)|g:([0-9a-f]{1,16}):(\d+)')
_STRICT_NAME = re.compile(r'[a-z_]+')


def _events(fields):
    out = []
    for token in fields:
        match = _EVENT.fullmatch(token)
        if not match:
            raise ValueError(token)
        if match.group(1):
            out.append(('claim', int(match.group(2)), int(match.group(3), 16), match.group(1) == 'C'))
        elif match.group(4):
            kind = {'p': 'push', 'P': 'forged_push', 'd': 'direct_push'}[match.group(4)]
            out.append((kind, int(match.group(5)), int(match.group(6)), int(match.group(7))))
        elif match.group(8):
            out.append(('reset', int(match.group(8)), int(match.group(9))))
        else:
            out.append(('gather', int(match.group(10), 16), int(match.group(11))))
    return out


def parse_records(path, strict_names):
    """The certify 1.4 records of one run. Anything malformed or unknown makes the run invalid."""
    parsed = {'begin': False, 'end': False, 'nonce': None, 'source': None, 'strict': [], 'faults': [],
              'continuation_lost': [], 'queues': {}, 'epochs': [], 'windows': [], 'result': None,
              'result_base': None, 'chunks': None, 'operations': None, 'invalid': []}
    path = Path(path)
    if not path.is_file() or path.stat().st_size > RECORD_LIMIT:
        parsed['invalid'].append('record file missing or too large')
        return parsed
    lines = path.read_bytes().split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    pending_epoch = None
    for number, raw in enumerate(lines, 1):
        try:
            line = raw.decode('ascii')
        except UnicodeDecodeError:
            parsed['invalid'].append(f'line {number}: not ASCII')
            continue
        fields = line.split(' ')
        kind = fields[0]
        try:
            if line == 'begin 2' and number == 1:
                parsed['begin'] = True
            elif kind == 'plan' and len(fields) == 2 and parsed['nonce'] is None and re.fullmatch(r'[0-9a-f]{32}', fields[1]):
                parsed['nonce'] = fields[1]
            elif kind == 'source' and len(fields) == 2 and parsed['source'] is None:
                parsed['source'] = int(fields[1])
            elif kind == 'strict' and len(fields) == 3 and _STRICT_NAME.fullmatch(fields[1]) \
                    and fields[1] in strict_names and fields[2] in ('0', '1', '2'):
                parsed['strict'].append((fields[1], int(fields[2])))
            elif kind == 'fault' and len(fields) == 3 and fields[1] in ('context', 'wait', 'stream'):
                parsed['faults'].append((fields[1], int(fields[2])))
            elif kind == 'fault' and len(fields) >= 4 and fields[1] == 'continuation' \
                    and int(fields[3]) == len(fields) - 4:
                parsed['faults'].append(('continuation', int(fields[2])))
                parsed['continuation_lost'].extend(int(v) for v in fields[4:])
            elif kind == 'queue' and len(fields) == 3 and int(fields[1]) == len(parsed['queues']) \
                    and _HEX.fullmatch(fields[2]):
                parsed['queues'][int(fields[1])] = int(fields[2], 16)
            elif kind == 'epoch' and len(fields) >= 3 and pending_epoch is None and int(fields[2]) == len(fields) - 3:
                pending_epoch = (int(fields[1]), _events(fields[3:]))
            elif kind == 'window' and len(fields) >= 3 and pending_epoch is not None \
                    and int(fields[1]) == pending_epoch[0] and int(fields[2]) == len(fields) - 3:
                parsed['epochs'].append(pending_epoch[1])
                parsed['windows'].append((pending_epoch[0], [int(v) for v in fields[3:]]))
                pending_epoch = None
            elif kind == 'result' and len(fields) >= 3 and parsed['result'] is None \
                    and int(fields[2]) == len(fields) - 3 and fields[1] in ('i32', 'f32'):
                if fields[1] == 'i32':
                    values = [int(v) for v in fields[3:]]
                else:
                    values = [struct.unpack('<f', struct.pack('<I', int(v, 16)))[0] for v in fields[3:]]
                parsed['result'] = {'kind': fields[1], 'values': values}
            elif kind == 'result_base' and len(fields) == 3 and parsed['result_base'] is None and _HEX.fullmatch(fields[1]):
                parsed['result_base'] = (int(fields[1], 16), int(fields[2]))
            elif kind == 'witness' and len(fields) == 3 and parsed['chunks'] is None \
                    and fields[1].startswith('chunks=') and fields[2].startswith('operations='):
                parsed['chunks'] = int(fields[1][7:])
                parsed['operations'] = int(fields[2][11:])
            elif line == 'end' and not parsed['end'] and pending_epoch is None:
                parsed['end'] = True
            else:
                parsed['invalid'].append(f'line {number}: unexpected record {kind[:20]!r}')
        except (ValueError, struct.error):
            parsed['invalid'].append(f'line {number}: malformed {kind[:20]!r} record')
    if pending_epoch is not None and parsed['end']:
        parsed['invalid'].append('epoch without its window')
    referenced = {q for q, _ in parsed['windows']}
    for events in parsed['epochs']:
        referenced |= {e[2] for e in events if e[0] in ('push', 'forged_push', 'direct_push', 'reset')}
    if referenced - set(parsed['queues']):
        parsed['invalid'].append('event names an unannounced queue')
    return parsed


# --- seam witness (contract clause L4) ---------------------------------------------------------------

def ledger(parsed, source, *, result_base=None):
    """Pair pushes with claims and windows with pushes, from the records alone.

    Returns {'problems', 'base', 'queue', 'paired_forged', 'forged_pushes'}. ``paired_forged`` lists
    (window index, vertex) for pushes paired with a forged claim; ``forged_pushes`` (window index,
    vertex) for forged push copies. ``base`` is the claim array base the pairing found (or None).
    """
    problems = []
    windows, epochs = parsed['windows'], parsed['epochs']
    slid = sorted({q for q, _ in windows})
    if len(slid) != 1:
        problems.append(f'{len(slid)} queues were slid; the frontier must be one queue')
    queue = slid[0] if slid else None
    # The claim array base: the most common (claim address - 4 * vertex) over each push and the
    # pushing thread's latest claim before it.
    deltas = Counter()
    for events in epochs:
        latest = {}
        for event in events:
            if event[0] == 'claim':
                latest[event[1]] = event[2]
            elif event[0] == 'push' and event[1] in latest:
                deltas[latest.pop(event[1]) - 4 * event[3]] += 1
    base = deltas.most_common(1)[0][0] if deltas else None
    if result_base is not None and base is not None and base != result_base:
        problems.append('claims do not address the returned parent array')
        base = result_base
    elif result_base is not None:
        base = result_base
    paired_forged, forged_pushes, unpaired, direct_bad, mismatched = [], [], 0, 0, 0
    for index, ((window_queue, window), events) in enumerate(zip(windows, epochs)):
        claims = defaultdict(deque)          # (thread, address) -> forged flags, oldest first
        pushed = []
        for event in events:
            kind = event[0]
            if kind == 'claim':
                claims[(event[1], event[2])].append(event[3])
            elif kind in ('push', 'forged_push', 'direct_push'):
                thread, target, vertex = event[1], event[2], event[3]
                if target != window_queue:
                    problems.append(f'window {index}: a push went into a queue that was not slid')
                    continue
                pushed.append(vertex)
                if kind == 'forged_push':
                    forged_pushes.append((index, vertex))
                elif kind == 'direct_push':
                    if not (index == 0 and vertex == source and pushed.count(vertex) == 1):
                        direct_bad += 1
                else:
                    slot = claims.get((thread, base + 4 * vertex)) if base is not None else None
                    if slot:
                        if slot.popleft():
                            paired_forged.append((index, vertex))
                    else:
                        unpaired += 1
        if sorted(pushed) != sorted(window):
            mismatched += 1
    if unpaired:
        problems.append(f'{unpaired} pushes have no claim by the pushing thread at base + 4 * vertex')
    if direct_bad:
        problems.append(f'{direct_bad} direct queue pushes other than the source')
    if mismatched:
        problems.append(f'{mismatched} windows differ from the pushes made into them')
    return {'problems': problems, 'base': base, 'queue': queue, 'paired_forged': paired_forged,
            'forged_pushes': forged_pushes}


def gathers_from(parsed, base, counts_threshold):
    """Epochs that processed a window at or above the threshold and gathered from ``base``."""
    windows, epochs = parsed['windows'], parsed['epochs']
    hits = 0
    for index in range(1, len(epochs)):
        if len(windows[index - 1][1]) >= counts_threshold and base is not None and any(
                e[0] == 'gather' and e[1] == base and e[2] > 0 for e in epochs[index]):
            hits += 1
    return hits


# --- attribution ----------------------------------------------------------------------------------------

def level_sets(adjacency, source):
    depth = {source: 0}
    frontier, levels = [source], []
    while frontier:
        levels.append(set(frontier))
        following = []
        for u in frontier:
            for v in adjacency[u]:
                if v not in depth:
                    depth[v] = depth[u] + 1
                    following.append(v)
        frontier = following
    return levels


def attributed(fault, parsed, verdict, book, expected, *, adjacency=None, source=None):
    """(attributed, evidence) for one library-fault control run."""
    rule = ATTRIBUTION[fault]
    windows = [w for _, w in parsed['windows']]
    duplicated = {i: {v for v, n in Counter(w).items() if n > 1} for i, w in enumerate(windows)}
    if rule == 'duplicate_after_forged_claim':
        hits = sorted({(i, v) for i, v in book['paired_forged'] if v in duplicated.get(i, ())})
        return bool(hits), {'rule': rule, 'duplicates_after_forged_claims': hits[:5]}
    if rule == 'duplicate_is_forged_push':
        hits = sorted({(i, v) for i, v in book['forged_pushes'] if v in duplicated.get(i, ())})
        return bool(hits), {'rule': rule, 'forged_duplicates': hits[:5]}
    if rule in ('strict_inside_faulted_call', 'strict_on_faulted_thread'):
        floor = 2 if rule == 'strict_inside_faulted_call' else 1
        hits = [name for name, attribution in parsed['strict'] if attribution >= floor and name in expected]
        return bool(hits), {'rule': rule, 'strict': parsed['strict'][:5]}
    # missing_vertex_behind_lost_edge: the first level whose window differs from the oracle's level
    # misses a vertex that is the head of an edge the dropped continuation removed.
    lost = set(parsed['continuation_lost'])
    if not lost or adjacency is None:
        return False, {'rule': rule, 'lost_edges': len(lost)}
    flat = [v for row in adjacency for v in row]
    heads = {flat[j] for j in lost if 0 <= j < len(flat)}
    levels = level_sets(adjacency, source)
    observed = [set(w) for w in windows if w]
    for depth, expected_level in enumerate(levels):
        seen = observed[depth] if depth < len(observed) else set()
        if seen != expected_level:
            missing = expected_level - seen
            hits = sorted(missing & heads)
            return bool(hits), {'rule': rule, 'level': depth, 'missing': len(missing),
                                'missing_behind_lost_edges': hits[:5], 'lost_edges': len(lost)}
    return False, {'rule': rule, 'lost_edges': len(lost), 'levels_equal': True}


# --- judge ------------------------------------------------------------------------------------------------

SEMANTIC_CHECKS = ('verifier', 'frontier_size_equality', 'seam_witness', 'execution_witness')


def judge(run_result, parsed, counts, *, check_result, result_kind, source, threshold=64,
          claims_address_result=False):
    """Every check of one certify 1.4 run, from its records and the trusted oracles.

    The order of reasons is 1.3's (timeout, strict layer, duplicate frontier, invalid record,
    process failure, verifier, frontier sizes, execution witness) with ``seam_witness`` before the
    execution witness. A run whose plan nonce is missing or different is ``record_invalid``; so is a
    run without a fault whose records show one.
    """
    plan = run_result.get('plan') or {}
    invalid = list(parsed['invalid'])
    if parsed['nonce'] != plan.get('nonce'):
        invalid.append('plan nonce missing or different')
    if parsed['source'] not in (None, source):
        invalid.append('source record differs from the run')
    if plan.get('fault') is None and (parsed['faults'] or any(
            e[0] in ('forged_push',) or (e[0] == 'claim' and e[3]) for events in parsed['epochs'] for e in events)):
        invalid.append('fault records in a run without a fault')
    strict = list(dict.fromkeys(name for name, _ in parsed['strict']))
    windows = [w for _, w in parsed['windows']]
    duplicate = any(len(set(w)) != len(w) for w in windows)
    named = strict + (['duplicate_frontier'] if duplicate else [])
    observed = set(named) | ({'frontier_size_equality'} if duplicate else set())
    clean = (not run_result['timeout'] and run_result['returncode'] == 0 and parsed['begin'] and parsed['end']
             and not strict and not invalid)
    result_check, book = None, None
    result_base = parsed['result_base'][0] if claims_address_result and parsed['result_base'] else None
    book = ledger(parsed, source, result_base=result_base)
    if clean:
        result = parsed['result']
        if result is None or result['kind'] != result_kind:
            result_check = {'passed': False, 'reason': 'no result record of kind ' + result_kind}
        else:
            result_check = check_result(result['values'])
        if not result_check['passed']:
            observed.add('verifier')
        sizes = [len(w) for w in windows]
        if sizes and sizes[-1] == 0:
            sizes.pop()                      # the slide that ends the search leaves an empty window
        if sizes != list(counts):
            observed.add('frontier_size_equality')
        if claims_address_result and parsed['result_base'] is None:
            book['problems'].append('no result_base record')
        if book['problems']:
            observed.add('seam_witness')
        if max(counts) >= threshold and not (parsed['chunks'] and parsed['operations']
                                             and gathers_from(parsed, book['base'], threshold)):
            observed.add('execution_witness')
    if run_result['timeout']:
        reason = 'timeout'
    elif strict:
        reason = 'strict_layer_assertion'
    elif duplicate:
        reason = 'frontier_size_equality'
    elif invalid:
        reason = 'record_invalid'
    elif not clean:
        reason = 'process_failure'
    else:
        reason = next((name for name in SEMANTIC_CHECKS if name in observed), 'all_checks_passed')
    return {'passed': reason == 'all_checks_passed', 'reason': reason, 'observed_checks': sorted(observed),
            'named_checks': named, 'result_check': result_check, 'record_problems': invalid[:5],
            'seam_witness': {'problems': book['problems'][:5], 'claim_base': hex(book['base']) if book['base'] is not None else None},
            '_book': book}


# --- certification ------------------------------------------------------------------------------------------

def certify_candidate(tree, library, folder, tile_sizes, threads, sources, *, threshold=64, plugin, contract=None,
                      rng=None, build_class=None, runner=None, driver_attribute='certification_driver_v14',
                      build_suffix='v14'):
    """Certify one candidate tree with certify 1.4 (ticket 76, 2026-10-05 ET).

    Per tile size: one candidate object (prelude 1.4) linked once with record.cc and seams.cc; the
    positive matrix and every library-fault control run that binary with a blinded plan, in a random
    order shared with the token and legality controls. Every check comes from :func:`judge`; a
    library-fault control is rejected only when its check is attributable (:func:`attributed`).

    Ticket 78 (certify 1.5): ``build_class``, ``runner``, ``driver_attribute`` and ``build_suffix``
    select the 1.5 process split (``swdb.certification_process``); their defaults are 1.4's.
    """
    build_class = build_class or Build
    runner = runner or run_one
    from swdb import certification as base
    from swdb import certification_legality as legality
    from swdb.certification_faults import FAULT_VERSIONS, LIBRARY_FAULTS
    from swdb.certification_feedback import STRICT_MESSAGES
    rng = rng or random.SystemRandom()
    legal = bool(contract) and legality.applies(contract)
    graphs = base.matrix_graphs(folder, library, threads)
    by_name = dict(graphs)
    source_path = tree / plugin.certification_source
    source = source_path.read_text()
    driver = (library / getattr(plugin, driver_attribute)).read_text()
    stem = plugin.binary_stem
    claims_address_result = bool(getattr(plugin, 'certification_claims_address_result', False))
    adjacency = {}
    strict_names = set(STRICT_MESSAGES)
    instrument = lambda text: plugin.certification_instrument(text, frontier_hook=False) + driver

    def graph_rows(graph):
        if graph not in adjacency:
            adjacency[graph] = base.graph_adjacency(graph)
        return adjacency[graph]

    def judged(run, graph, vertex, counts):
        parsed = parse_records(run['record'], strict_names)
        rows = graph_rows(graph)
        check = lambda values: plugin.certification_check_result(rows, vertex, values)
        verdict = judge(run, parsed, counts, check_result=check, result_kind=plugin.certification_result_kind,
                        source=vertex, threshold=threshold, claims_address_result=claims_address_result)
        return parsed, verdict

    def evidence(link, run, verdict):
        return {'candidate_object_sha256': link['candidate_object_sha256'], 'binary_sha256': link['binary_sha256'],
                'seam_object_sha256': link['seam_object_sha256'], 'record_object_sha256': link['record_object_sha256'],
                'plan': run['plan'], 'named_checks': verdict['named_checks'],
                'observed_checks': verdict['observed_checks'], 'result_check': verdict['result_check'],
                'record_problems': verdict['record_problems'], 'seam_witness': verdict['seam_witness'],
                **{key: link[key] for key in ('client_object_sha256', 'evaluator_sha256', 'process_split') if key in link}}

    matrix, controls, schedule = [], [], []
    for size in tile_sizes:
        build = build_class(folder / f'{stem}-{size}.{build_suffix}', library, tree, source_path, size, threads)
        instrumented = instrument(source)
        static = (base.legality_checks(instrumented, source_path, f'{stem}-{size}', library, contract, folder,
                                       tile_size=size, threads=threads, tree=tree, defines=[]) if legal else None)
        static_failed, static_invalid = base._legality_failures(static)
        legality_field = {'legality_checks': static} if legal else {}
        output = folder / f'{stem}-{size}'
        positive = build.candidate_object(instrumented, 'positive')
        link = build.link(positive, output) if positive['returncode'] == 0 else positive
        if link['returncode'] != 0:
            matrix.append({'tile_size': size, 'status': 'failed', 'reason': 'build failed', 'build': positive,
                           'link': link, **legality_field})
            continue
        jobs = []      # (kind, name or (graph, vertex), binary link, fault, graph name, graph, vertex)
        for graph_name, graph in graphs:
            for vertex in sources:
                jobs.append({'kind': 'matrix', 'graph_name': graph_name, 'graph': graph, 'vertex': vertex,
                             'link': link, 'fault': None})
        names = list(plugin.certification_controls) + (list(legality.CONTROLS) if legal else [])
        control_graphs = getattr(plugin, 'certification_control_graphs', None) or {}
        vertex = plugin.control_source(sources)
        for name in names:
            graph_name = control_graphs.get(name, graphs[-1][0])
            job = {'kind': 'control', 'name': name, 'graph_name': graph_name, 'graph': by_name[graph_name],
                   'vertex': vertex}
            if name in legality.CONTROLS and legal:
                mutant = legality.control(source, name, contract)
                mutant['source'] = instrument(mutant['source'])
            else:
                mutant = plugin.certification_control(plugin.certification_instrument(source, frontier_hook=False), name)
                if isinstance(mutant, str):
                    mutant = {'source': mutant + driver, 'fault': None, 'site': 'candidate_tokens'}
                else:
                    mutant = {**mutant, 'source': mutant['source'] + driver}
            fault = {'site': mutant['site']}
            if mutant['fault']:
                if mutant['source'] != instrumented or name not in LIBRARY_FAULTS:
                    raise Failure('library-fault control changed candidate text: ' + name)
                fault.update(macro=None, plan=name, version=mutant.get('version', FAULT_VERSIONS.get(name, 1)),
                             delivery='run_plan', attribution=ATTRIBUTION[name])
                job.update(link=link, fault=name, candidate=positive, static=static)
            else:
                control_static = (base.legality_checks(mutant['source'], source_path, f'{stem}-{size}-{name}', library,
                                                       contract, folder, tile_size=size, threads=threads, tree=tree,
                                                       defines=[]) if legal else None)
                candidate_object = build.candidate_object(mutant['source'], name)
                mutant_link = (build.link(candidate_object, folder / f'{stem}-{size}-{name}')
                               if candidate_object['returncode'] == 0 else candidate_object)
                job.update(link=mutant_link, fault=None, candidate=candidate_object, static=control_static)
            job['fault_record'] = fault
            jobs.append(job)
        for canonical, job in enumerate(jobs):
            job['canonical'] = canonical
        rng.shuffle(jobs)
        done_matrix, done_controls = [], []
        for order, job in enumerate(jobs):
            schedule.append({'tile_size': size, 'order': order, 'kind': job['kind'],
                             'name': job.get('name') or f"{job['graph_name']}/{job['vertex']}"})
            if job['kind'] == 'matrix':
                counts = plugin.certification_oracle(job['graph'], job['vertex'])
                run = runner(job, folder / f"{job['graph_name']}-{size}-{job['vertex']}.json", threads)
                parsed, verdict = judged(run, job['graph'], job['vertex'], counts)
                passed, reason = verdict['passed'], verdict['reason']
                if static_failed or static_invalid:
                    passed, reason = False, static_failed[0] if static_failed else 'legality_check_invalid'
                done_matrix.append((job['canonical'], {'graph': job['graph_name'], 'graph_sha256': artifacts.file_hash(job['graph']),
                               'source': job['vertex'], 'oracle_frontier_counts': counts, 'tile_size': size,
                               'threads': threads, 'status': 'passed' if passed else 'failed', 'reason': reason,
                               'build': positive, 'link': link, 'run': run, 'schedule_order': order,
                               **evidence(link, run, verdict), **legality_field}))
                continue
            name, counts = job['name'], plugin.certification_oracle(job['graph'], job['vertex'])
            expected_checks = plugin.certification_controls.get(name) or legality.CONTROLS.get(name, set())
            control_failed, _ = base._legality_failures(job['static'])
            control_legality = {'legality_checks': job['static']} if legal else {}
            if job['link']['returncode']:
                named_static = sorted(set(control_failed) & set(expected_checks))
                done_controls.append((job['canonical'], {'id': name, 'tile_size': size, 'status': 'rejected' if named_static else 'invalid',
                                 'reason': named_static[0] if named_static else 'build failed',
                                 'observed_checks': sorted(set(control_failed)), 'fault': job['fault_record'],
                                 'build': job['candidate'], 'link': job['link'], 'schedule_order': order,
                                 **control_legality}))
                continue
            run = runner(job, folder / f'control-{size}-{name}.json', threads)
            parsed, verdict = judged(run, job['graph'], job['vertex'], counts)
            passed, reason = verdict['passed'], verdict['reason']
            record = evidence(job['link'], run, verdict)
            if control_failed:
                record['observed_checks'] = sorted(set(record['observed_checks']) | set(control_failed))
                passed, reason = False, control_failed[0]
            status = base.control_status(expected_checks, record['observed_checks'], run, passed)
            if job['fault']:
                ok, attribution = attributed(job['fault'], parsed, verdict, verdict['_book'],
                                             set(expected_checks) or set(SEMANTIC_CHECKS),
                                             adjacency=graph_rows(job['graph']), source=job['vertex'])
                record['attribution'] = {'attributed': ok, **attribution}
                if status == 'rejected' and not ok:
                    status, reason = 'invalid', 'check_not_attributed_to_fault'
            done_controls.append((job['canonical'], {
                'id': name, 'tile_size': size, 'status': status, 'reason': reason, 'graph': job['graph_name'],
                'fault': job['fault_record'], 'build': job['candidate'], 'link': job['link'], 'run': run,
                'schedule_order': order, **record, **control_legality}))
        # Records keep the canonical order (graphs, then controls), whatever order the runs took.
        matrix.extend(cell for _, cell in sorted(done_matrix, key=lambda pair: pair[0]))
        controls.extend(cell for _, cell in sorted(done_controls, key=lambda pair: pair[0]))
    source_path.write_text(source)  # This is a private build copy, never a vendored tree.
    return matrix, controls, schedule


def run_one(job, log, threads):
    return run(job['link']['binary'], job['graph'], job['vertex'], log, threads, fault=job['fault'])

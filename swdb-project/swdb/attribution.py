"""Fine-grained estimate attribution: `swdb attribute`. Created: 2026-10-11 ET.

Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md` (ticket 02, the narrowest path).
The command is the public interface; everything below it may change.

What it reads: two saved `estimate` records, the `workload_characterization` each one pins,
and the two source trees (a `source_snapshot` or `candidate` record's `artifact`) that were
counted. It never re-estimates and never binds a protocol, so it runs on old estimates
after the estimator code changed.

Rules used by this version (ticket 04 widens the matching rules):

1. Diff (F17). SWDB diffs the two verified artifact trees itself, file by file, line by line
   (`difflib`, no junk heuristic). A stored candidate diff is never read. Each changed run of
   lines (one non-equal opcode) is one rewrite site. A site's `baseline_lines` and
   `candidate_lines` are `[first, last]`; an empty side (pure insertion or deletion) is
   written `[p, p - 1]`, the insertion point before line `p`.
2. Paths. A region's `source_location.path` is made relative to its side's tree: strip the
   artifact root, else take the one manifest file the path ends with. A path in neither tree
   (for example a system header) cannot have changed, so its region is untouched.
3. Span. A region covers `[min, max]` of its own start line and the lines of its access
   patterns in the same file. Region IDs are never matched across sides.
4. Label. A region with no path or no line is `unattributed`. A region whose span overlaps a
   site on its own side is `agent_rewritten`; an insertion point overlaps a span only when it
   lies strictly inside it. Every other region is `untouched`. Ticket 05: a region inside a
   site becomes `offload_command`, `intrinsic` or `library_call` when it executes one (see
   `_Catalog`); its group stays `agent_rewritten`, which lists per-origin seconds.
5. Groups (F4). Each side's group seconds are summed per estimate trial (a region absent from
   a trial counts 0 s), then the median is taken per group; a single-run estimate is one
   trial. Group medians are never rescaled to the estimate's total. Whole-program totals are
   the estimates' own `seconds`.
6. Unknowns (F8). An unknown region makes its group's seconds unknown and lists the region
   with its bounds' `missing` reasons; every ratio that depends on an unknown is null.
7. Identity (F43, F44). The record pins both estimates, both source records and the target
   description by content hash. Its dates are the latest `updated` date of those inputs and
   dicts are built in a fixed order, so the same inputs give a byte-identical record.
8. Iterations (F13, ticket 06). Given the previous accepted candidate (`--previous-estimate`,
   `--previous-source`), the top-level comparison stays cumulative (original baseline ->
   candidate) and a `this_iteration` block repeats it against the previous candidate. The
   candidate is iteration 2 + the number of `--earlier-source` trees (accepted candidates
   before the previous one, oldest first). Each region row records `last_changed_iteration`:
   the newest iteration whose diff into that region's version labels it rewritten (0 = never,
   null = no source location). Without a previous candidate the record is the ticket 02 one.
9. Resource floor (ticket 07, F6). Each region's floor is max(compute bound, useful-bytes
   bandwidth bound) from the unchanged mechanism models at the pinned description's own
   rates, per trial then median. A missing rate gives an unknown floor naming it; no other
   description's rate is borrowed. Headroom = region seconds ÷ named limit. `this_iteration`
   region rows carry floors too (same row shape; the previous candidate's from its own estimate).
10. Ranking (F7, floor-only tier). Candidate regions by floor headroom, largest first;
    unknown headrooms follow and are never ranked against known ones. One top-level ranking:
    the candidate is the same in both comparisons, so its floors are too.
"""
import copy
import difflib
import statistics
from pathlib import Path, PurePosixPath

from swdb import artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store

FORMAT = 'swdb.attribution.v1'
ORIGINS = ('untouched', 'agent_rewritten', 'unattributed')
# Ticket 05 (F2): origins a region inside a rewrite site can take, highest precedence first.
# All of them belong to the `agent_rewritten` group; the group lists them under `origins`.
REWRITE_ORIGINS = ('offload_command', 'intrinsic', 'library_call', 'agent_rewritten')
REWRITE_REASONS = {'offload_command': 'offload_command_in_site', 'intrinsic': 'intrinsic_in_site',
                   'library_call': 'library_operation_in_site', 'agent_rewritten': 'overlaps_rewrite_site'}
SOURCE_KINDS = ('source_snapshot', 'candidate')
SAME = ('input', 'target_description_sha256', 'threads', 'evidence_kind')


def register_cli(commands):
    sub = commands.add_parser('attribute', help='split two saved estimates by code origin from their source trees')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--baseline-estimate', required=True, help='saved baseline estimate record ID')
    sub.add_argument('--candidate-estimate', required=True, help='saved candidate estimate record ID')
    sub.add_argument('--baseline-source', required=True, help='source_snapshot or candidate record the baseline counted')
    sub.add_argument('--candidate-source', required=True, help='source_snapshot or candidate record the candidate counted')
    sub.add_argument('--id', required=True)
    sub.add_argument('--library', type=Path, default=None,
                     help='typed library whose operations label library calls (default: beside the records folder)')
    sub.add_argument('--previous-estimate', help='iteration 2 on: saved estimate of the previous accepted candidate')
    sub.add_argument('--previous-source', help='iteration 2 on: source record the previous accepted candidate counted')
    sub.add_argument('--earlier-source', action='append', default=[],
                     help='source record of an accepted candidate before the previous one, oldest first (repeatable)')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=attribute)


def _require(condition, message):
    if not condition:
        raise Failure(message)


def _record(store, rid, kinds):
    data = store.get(rid)
    _require(data is not None and data['kind'] in kinds, f'{rid!r} is not a saved {" or ".join(kinds)} record')
    return data


def _subject_matches(source, subject):
    if source['kind'] == 'candidate':
        return subject == {'kind': 'candidate', 'id': source['id']}
    return subject == {'kind': 'implementation', 'id': source['implementation']}


class _Side:
    """One estimate with its counted characterization and verified source tree."""

    def __init__(self, store, name, estimate_id, source_id):
        self.name = name
        self.estimate = _record(store, estimate_id, ('estimate',))
        self.source = _record(store, source_id, SOURCE_KINDS)
        _require(_subject_matches(self.source, self.estimate['subject']),
                 f'{name} estimate subject {self.estimate["subject"]} did not count source {source_id!r}')
        self.characterization = _record(store, self.estimate['characterization'], ('workload_characterization',))
        _require(artifacts.digest(self.characterization) == self.estimate['characterization_sha256'],
                 f'{name} characterization differs from the hash its estimate pins')
        self.root = artifacts.verify(self.source['artifact'])
        self.files = {f['path'] for f in self.source['artifact']['files']}
        self.locations = {}
        for row in self.characterization['regions'] + [r for t in self.characterization.get('trials', []) for r in t['regions']]:
            self.locations.setdefault(row['id'], row)
        self.calls = _executed_calls(self.characterization)

    def relative(self, text):
        if not text:
            return None
        path = PurePosixPath(text)
        root = PurePosixPath(self.root.as_posix())
        if path.is_absolute() and root in path.parents:
            rel = path.relative_to(root).as_posix()
            return rel if rel in self.files else None
        if not path.is_absolute() and path.as_posix() in self.files:
            return path.as_posix()
        matches = [f for f in self.files if text.endswith('/' + f)]
        return matches[0] if len(matches) == 1 else None

    def text(self, rel):
        if rel not in self.files:
            return []
        return (self.root / rel).read_text(errors='replace').splitlines()

    def place(self, region_id):
        """(relative path or None, [first, last], located); located is False without path or line."""
        row = self.locations.get(region_id)
        where = (row or {}).get('source_location', {})
        line = where.get('line')
        if not where.get('path') or not isinstance(line, int) or line < 1:
            return None, None, False
        rel = self.relative(where['path'])
        lines = [line] + [a['source_location']['line'] for a in row.get('access_patterns', [])
                          if a['source_location'].get('path') == where['path'] and a['source_location'].get('line', 0) >= 1]
        return rel, [min(lines), max(lines)], True

    def trials(self):
        if self.estimate.get('trials'):
            return [t['regions'] for t in self.estimate['trials']]
        return [self.estimate['regions']]


def _sites(baseline, candidate):
    sites = []
    for rel in sorted(baseline.files | candidate.files):
        before, after = baseline.text(rel), candidate.text(rel)
        if rel in baseline.files and rel in candidate.files and before == after:
            continue
        matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op != 'equal':
                sites.append({'id': f'site.{len(sites) + 1}', 'path': rel,
                              'baseline_lines': [i1 + 1, i2], 'candidate_lines': [j1 + 1, j2],
                              'baseline_regions': [], 'candidate_regions': []})
    return sites


def _overlaps(span, lines):
    first, last = lines
    if first <= last:
        return span[0] <= last and first <= span[1]
    return span[0] < first <= span[1]


def _label(side, sites, catalog=None):
    rows = {}
    for region in side.estimate['regions']:
        rel, span, located = side.place(region['id'])
        touched = [s for s in sites if located and rel is not None and s['path'] == rel
                   and _overlaps(span, s[side.name + '_lines'])]
        if not located:
            origin, reason = 'unattributed', 'no_source_location'
        elif rel is None:
            origin, reason = 'untouched', 'outside_source_tree'
        elif touched:
            origin, reason = 'agent_rewritten', 'overlaps_rewrite_site'
        else:
            origin, reason = 'untouched', 'no_changed_line'
        evidence = catalog.evidence(side, region['id']) if touched and catalog is not None else []
        if evidence:
            origin = evidence[0]['origin']
            reason = REWRITE_REASONS[origin]
        for site in touched:
            site[side.name + '_regions'].append(region['id'])
        rows[region['id']] = {'side': side.name, 'region': region['id'], 'origin': origin, 'reason': reason,
                              'path': rel, 'lines': span, 'sites': [s['id'] for s in touched],
                              'seconds': region['seconds'], 'evidence': evidence}
    return rows


# --- Ticket 05: library, intrinsic and offload labels (F2) -------------------------------------
#
# Only a region inside a rewrite site is relabeled, so a baseline libc or C++ standard library
# call outside every site stays untouched. Signals, read from the counted characterization:
#   offload_command  the region issued a command bound by the functional observation contract
#                    (`accelerator_calls[]` with a nonzero `execution_count`), named by its event;
#   intrinsic        an executed call (`unmodeled_calls[]`, top level or any trial) whose name is
#                    a saved `intrinsic` record's C `name`, plain or as an Itanium source name;
#   library_call     an executed call naming a typed-library operation's `location.symbol` the
#                    same way, or the region or one of its accesses located in that operation's
#                    `location.path` (inlined library code keeps its header's file and line).
# The highest-precedence signal names the origin; `evidence` lists every signal found.

def _executed(fact):
    return (fact or {}).get('value') != 0


def _executed_calls(characterization):
    """{region ID: sorted executed call names}, over the aggregate and every trial."""
    calls = {}
    for row in characterization.get('unmodeled_calls', []) + [
            c for t in characterization.get('trials', []) for c in t.get('unmodeled_calls', [])]:
        if _executed(row.get('execution_count')) and row.get('region') and row.get('name'):
            calls.setdefault(row['region'], set()).add(row['name'])
    return {region: sorted(names) for region, names in calls.items()}


def _names(call, symbol):
    """The call is `symbol` itself or carries it as an Itanium source name (`<length><symbol>`)."""
    import re
    return call == symbol or re.search(f'(?<![0-9]){len(symbol)}{re.escape(symbol)}', call) is not None


class _Catalog:
    """Saved intrinsic records and the typed library's operations, pinned when they label a region."""

    def __init__(self, store, root):
        from swdb.library import Library
        self.intrinsics = sorted((r.data['name'], r.data['id'], artifacts.digest(r.data))
                                 for r in store.of_kind('intrinsic') if r.data.get('name'))
        library = Library(root) if root.exists() else None
        self.operations = sorted((rid, data.get('location') or {}, artifacts.digest(data))
                                 for rid, data in (library.entries.items() if library else ())
                                 if data.get('kind') == 'library_operation')
        self.used = {}

    def _operation_located(self, side, region_id, path):
        row = side.locations.get(region_id) or {}
        paths = [(row.get('source_location') or {}).get('path')] + [
            (a.get('source_location') or {}).get('path') for a in row.get('access_patterns', [])]
        return any(p and (p == path or p.endswith('/' + path)) for p in paths)

    def evidence(self, side, region_id):
        found = set()
        for row in [r for r in [side.locations.get(region_id)] if r] + [
                r for t in side.characterization.get('trials', []) for r in t['regions'] if r['id'] == region_id]:
            for command in row.get('accelerator_calls', []):
                if _executed(command.get('execution_count')):
                    found.add(('offload_command', command['event'], None))
        calls = side.calls.get(region_id, [])
        for name, rid, sha in self.intrinsics:
            if any(_names(c, name) for c in calls):
                found.add(('intrinsic', rid, ('intrinsic', sha)))
        for rid, location, sha in self.operations:
            symbol, path = location.get('symbol'), location.get('path')
            if (symbol and any(_names(c, symbol) for c in calls)) or (
                    path and self._operation_located(side, region_id, path)):
                found.add(('library_call', rid, ('library_operation', sha)))
        for _, rid, pin in found:
            if pin:
                self.used[rid] = {'kind': pin[0], 'id': rid, 'sha256': pin[1]}
        return [{'origin': origin, 'name': name}
                for origin, name, _ in sorted(found, key=lambda f: (REWRITE_ORIGINS.index(f[0]), f[1]))]

    def pins(self):
        return [self.used[rid] for rid in sorted(self.used)]


def _missing(region):
    return sorted({m for b in region['bounds'] + region['overheads'] for m in b['missing']})


def _group_seconds(side, labels, origins=ORIGINS):
    """{origin: (median seconds or None, [unknown region reasons])} from per-trial sums.

    A region whose label is not one of `origins` is left out (ticket 05's per-origin split)."""
    sums = {origin: [] for origin in origins}
    unknown = {origin: {} for origin in origins}
    for rows in side.trials():
        totals = {origin: 0. for origin in origins}
        for region in rows:
            origin = labels[region['id']]['origin'] if region['id'] in labels else 'unattributed'
            if origin not in totals:
                continue
            if region['seconds'] is None:
                totals[origin] = None
                unknown[origin].setdefault(region['id'], set()).update(_missing(region))
            elif totals[origin] is not None:
                totals[origin] += region['seconds']
        for origin in origins:
            sums[origin].append(totals[origin])
    result = {}
    for origin in origins:
        values = sums[origin]
        seconds = None if any(v is None for v in values) else statistics.median(values)
        reasons = [{'side': side.name, 'region': rid, 'missing': sorted(missing)}
                   for rid, missing in sorted(unknown[origin].items())]
        result[origin] = (seconds, reasons)
    return result


def _ratio(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _grouped(labels):
    """Labels with every rewrite-site origin folded into the `agent_rewritten` group."""
    return {rid: {**row, 'origin': 'agent_rewritten' if row['origin'] in REWRITE_ORIGINS else row['origin']}
            for rid, row in labels.items()}


def _rewrite_origins(baseline, candidate, labels):
    """Ticket 05: per-origin seconds and shares inside the rewritten group, in precedence order."""
    base = _group_seconds(baseline, labels['baseline'], REWRITE_ORIGINS)
    cand = _group_seconds(candidate, labels['candidate'], REWRITE_ORIGINS)
    rows = []
    for origin in REWRITE_ORIGINS:
        (b, b_unknown), (c, c_unknown) = base[origin], cand[origin]
        rows.append({'origin': origin, 'baseline_seconds': b, 'candidate_seconds': c,
                     'baseline_share': _ratio(b, baseline.estimate['seconds']),
                     'candidate_share': _ratio(c, candidate.estimate['seconds']), 'unknown': b_unknown + c_unknown})
    return rows


def _groups(baseline, candidate, labels):
    base = _group_seconds(baseline, _grouped(labels['baseline']))
    cand = _group_seconds(candidate, _grouped(labels['candidate']))
    base_total, cand_total = baseline.estimate['seconds'], candidate.estimate['seconds']
    groups = []
    for origin in ORIGINS:
        (b, b_unknown), (c, c_unknown) = base[origin], cand[origin]
        row = {'origin': origin, 'baseline_seconds': b, 'candidate_seconds': c,
               'baseline_share': _ratio(b, base_total), 'candidate_share': _ratio(c, cand_total),
               'realized_speedup': _ratio(b, c)}
        if origin == 'untouched':
            row['drift'] = _ratio(c, b)
        row['unknown'] = b_unknown + c_unknown
        if origin == 'agent_rewritten':
            row['origins'] = _rewrite_origins(baseline, candidate, labels)
        groups.append(row)
    return groups


def _whole(baseline, candidate, groups):
    base_total, cand_total = baseline.estimate['seconds'], candidate.estimate['seconds']
    untouched = next(g for g in groups if g['origin'] == 'untouched')
    return {'baseline_seconds': base_total, 'candidate_seconds': cand_total,
            'total_speedup': _ratio(base_total, cand_total),
            'amdahl_ceiling': _ratio(base_total, untouched['candidate_seconds']),
            'unknown': [reason for g in groups for reason in g['unknown']]}


FLOOR_MODELS = ('compute_throughput', 'streaming_bandwidth')


def _floor_terms(region, target):
    """The two floor terms of one counted region, from the description's own mechanisms only (F6).

    The unchanged mechanism models are called exactly as the estimator calls them, so each term
    equals that model's bound in the estimate. A model the description lacks is run with no
    rates: zero work gives 0 s, any work gives an unknown term naming the missing rate. No other
    description's rate and no latency, row, queue or overhead mechanism is read.
    """
    from swdb import analytic_models
    models = [m['model'] for m in target['mechanisms']]
    terms = []
    for model in FLOOR_MODELS:
        own = [m for m in target['mechanisms']
               if m['model'] == model and m.get('accounting', 'resource_bound') == 'resource_bound']
        results = [analytic_models.evaluate(region, m, models, target['threads']) for m in own or [{'model': model, 'parameters': {}}]]
        seconds = None if any(r['seconds'] is None for r in results) else max(r['seconds'] for r in results)
        terms.append({'model': model, 'in_description': bool(own), 'seconds': seconds,
                      'missing': sorted({m for r in results for m in r['missing']})})
    return terms


def _counted_trials(side, store):
    """Per-trial counted regions by ID, reconciled the way the estimator reconciles them."""
    from swdb.analytic_trial_scope import reconcile_trial
    trials = side.characterization.get('trials') or []
    if not trials:
        return [{r['id']: r for r in side.characterization['regions']}]
    return [{r['id']: r for r in reconcile_trial(side.characterization, trial, store)[0]['regions']} for trial in trials]


def _median(values):
    return None if any(v is None for v in values) else statistics.median(values)


def _resource_floor(region_id, counted, target):
    """Median over trials of max(terms) (a region absent from a trial counts 0 s), like the estimate."""
    per_trial = [_floor_terms(t[region_id], target) if region_id in t else None for t in counted]
    terms = []
    for i, model in enumerate(FLOOR_MODELS):
        rows = [t[i] for t in per_trial if t is not None]
        terms.append({'model': model, 'in_description': all(r['in_description'] for r in rows) if rows else True,
                      'seconds': _median([t[i]['seconds'] if t else 0. for t in per_trial]),
                      'missing': sorted({m for r in rows for m in r['missing']})})
    floors = [None if t and any(x['seconds'] is None for x in t) else max((x['seconds'] for x in t), default=0.) if t else 0.
              for t in per_trial]
    seconds = _median(floors)
    limiting = None if seconds is None else max(terms, key=lambda t: t['seconds'])['model']
    return {'seconds': seconds, 'limiting_term': limiting, 'terms': terms,
            'missing': sorted({m for t in terms for m in t['missing']})}


def _headroom(limit, estimate, bound):
    """Estimate ÷ the named limit; null with a reason when it cannot be a number."""
    reason = ('unknown_estimate' if estimate is None else 'unknown_limit' if bound is None
              else 'zero_limit' if bound == 0 else None)
    return {'limit': limit, 'value': None if reason else estimate / bound, 'reason': reason}


def _add_floors(side, labels, store):
    """Annotate each region row of one side with its resource floor and floor headroom."""
    counted = _counted_trials(side, store)
    target = side.estimate['target_description_snapshot']
    _require(artifacts.digest(target) == side.estimate['target_description_sha256'],
             f'{side.name} estimate target description snapshot differs from the hash it pins')
    for row in labels.values():
        floor = _resource_floor(row['region'], counted, target)
        row['resource_floor'] = floor
        row['headroom'] = [_headroom('resource_floor', row['seconds'], floor['seconds'])]


def _ranking(labels):
    """Candidate regions for the next iteration, by floor headroom (F7, floor-only tier).

    Known headrooms come first, largest first (ties by region ID); unknown ones follow in
    region-ID order and are never ranked against known ones. A later tier (the remaining gain
    bound of ticket 08) goes before the floor tier; positions are 1-based over the whole list.
    """
    def floor(row):
        return next(h for h in row['headroom'] if h['limit'] == 'resource_floor')
    rows = list(labels.values())
    known = sorted((r for r in rows if floor(r)['value'] is not None), key=lambda r: (-floor(r)['value'], r['region']))
    unknown = sorted((r for r in rows if floor(r)['value'] is None), key=lambda r: r['region'])
    entries = [('floor_headroom', r) for r in known] + [('unknown', r) for r in unknown]
    return [{'position': i, 'side': row['side'], 'region': row['region'], 'tier': tier, 'limit': 'resource_floor',
             'value': floor(row)['value'], 'reason': floor(row)['reason']}
            for i, (tier, row) in enumerate(entries, start=1)]


def _pin(data):
    return {'id': data['id'], 'sha256': artifacts.digest(data)}


def _source_pin(data):
    return {'kind': data['kind'], 'id': data['id'], 'sha256': artifacts.digest(data),
            'artifact_sha256': data['artifact']['sha256']}


def _floor_problems(record):
    """A resource floor is a lower limit: never above its region's known estimate (ticket 07)."""
    from swdb.problems import Problem
    blocks = [('regions', record.data['regions'])]
    if 'this_iteration' in record.data:
        blocks.append(('this_iteration.regions', record.data['this_iteration']['regions']))
    for field, rows in blocks:
        for i, row in enumerate(rows):
            floor, seconds = row['resource_floor']['seconds'], row['seconds']
            if floor is not None and seconds is not None and floor > seconds * (1 + 1e-9) + 1e-12:
                yield Problem(record.rel, f'{field}[{i}].resource_floor',
                              f'resource floor {floor} s exceeds the region estimate {seconds} s')


def validate_record(record, ctx):
    """`swdb validate`: the report is unedited and every pinned input is unchanged."""
    from swdb.problems import Problem
    data = record.data
    try:
        expected = artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})
    except (TypeError, ValueError):
        expected = None
    if data['identity_sha256'] != expected:
        yield Problem(record.rel, 'identity_sha256', 'attribution report differs from its content identity')
    for field in ('baseline_estimate', 'candidate_estimate', 'baseline_source', 'candidate_source'):
        pin = data[field]
        current = ctx.store.get(pin['id'])
        if current is None or artifacts.digest(current) != pin['sha256']:
            yield Problem(record.rel, field, f'pinned record {pin["id"]!r} is missing or changed')
    # Ticket 05: a saved intrinsic that labeled a region must be unchanged. Library operations
    # live outside the records folder (`--library`), so their pins are kept for replay only.
    for pin in data.get('catalog', []):
        if pin['kind'] == 'intrinsic':
            current = ctx.store.get(pin['id'], 'intrinsic')
            if current is None or artifacts.digest(current) != pin['sha256']:
                yield Problem(record.rel, 'catalog', f'pinned intrinsic {pin["id"]!r} is missing or changed')
    yield from _floor_problems(record)
    for field in ('baseline_estimate', 'candidate_estimate'):
        current = ctx.store.get(data[field]['id'], 'estimate')
        if current is not None and current['target_description_sha256'] != data['target_description']['sha256']:
            yield Problem(record.rel, 'target_description', 'pinned estimate used a different target description')
    yield from _validate_iteration(record, ctx)


def _validate_iteration(record, ctx):
    """Ticket 06: the previous accepted candidate's estimate and every source it pins are unchanged."""
    from swdb.problems import Problem
    this = record.data.get('this_iteration')
    if this is None:
        return
    pins = [('this_iteration.previous_estimate', this['previous_estimate']),
            ('this_iteration.previous_source', this['previous_source'])]
    pins += [(f'this_iteration.earlier_sources[{i}]', pin) for i, pin in enumerate(this['earlier_sources'])]
    for field, pin in pins:
        current = ctx.store.get(pin['id'])
        if current is None or artifacts.digest(current) != pin['sha256']:
            yield Problem(record.rel, field, f'pinned record {pin["id"]!r} is missing or changed')
    current = ctx.store.get(this['previous_estimate']['id'], 'estimate')
    if current is not None and current['target_description_sha256'] != record.data['target_description']['sha256']:
        yield Problem(record.rel, 'this_iteration.previous_estimate', 'pinned estimate used a different target description')


class _Tree:
    """A verified source tree with no estimate: an accepted candidate before the previous one."""

    def __init__(self, store, source_id):
        self.source = _record(store, source_id, SOURCE_KINDS)
        self.root = artifacts.verify(self.source['artifact'])
        self.files = {f['path'] for f in self.source['artifact']['files']}

    text = _Side.text


def _as(side, name):
    """The same side under another role name (the role picks the site line field)."""
    renamed = copy.copy(side)
    renamed.name = name
    return renamed


def _last_changed(side, chain, catalog=None):
    """{region ID: iteration that last changed it}. `chain[k]` is iteration k's tree; `side` is
    iteration len(chain). A region last changed in iteration k + 1 overlaps a site of the diff
    from chain[k] but none from chain[k + 1]; one that overlaps none is 0, one without a source
    location is None. Uses the labeling rules of `_label`, so it follows whatever they are."""
    current = _as(side, 'candidate')
    found, pending = {}, [r['id'] for r in side.estimate['regions']]
    for k in reversed(range(len(chain))):
        labels = _label(current, _sites(chain[k], current), catalog)
        for rid in list(pending):
            origin = labels[rid]['origin']
            if origin != 'untouched':
                found[rid] = None if origin == 'unattributed' else k + 1
                pending.remove(rid)
    return {**found, **{rid: 0 for rid in pending}}


def _iteration(store, args, baseline, candidate, labels, catalog=None):
    """F13: the `this_iteration` block (previous accepted candidate -> candidate), and every
    region row's `last_changed_iteration`. None without a previous candidate."""
    if args.previous_estimate is None and args.previous_source is None:
        _require(not args.earlier_source, '--earlier-source needs --previous-estimate and --previous-source')
        return None, []
    _require(args.previous_estimate is not None and args.previous_source is not None,
             '--previous-estimate and --previous-source go together')
    previous = _Side(store, 'previous', args.previous_estimate, args.previous_source)
    differ = [key for key in SAME if previous.estimate[key] != candidate.estimate[key]]
    _require(not differ, 'previous and candidate estimates differ in ' + ', '.join(differ) + '; refusing to compare')
    earlier = [_Tree(store, rid) for rid in args.earlier_source]
    chain = [baseline, *earlier, previous]
    before = _as(previous, 'baseline')
    sites = _sites(before, candidate)
    rows = {'baseline': _label(before, sites, catalog), 'candidate': _label(candidate, sites, catalog)}
    changed = {'previous': _last_changed(previous, chain[:-1], catalog),
               'candidate': _last_changed(candidate, chain, catalog)}
    for row in labels['baseline'].values():
        row['last_changed_iteration'] = 0
    for row in list(labels['candidate'].values()) + list(rows['candidate'].values()):
        row['last_changed_iteration'] = changed['candidate'][row['region']]
    for row in rows['baseline'].values():
        row['last_changed_iteration'] = changed['previous'][row['region']]
    _add_floors(before, rows['baseline'], store)
    _add_floors(candidate, rows['candidate'], store)
    groups = _groups(before, candidate, rows)
    block = {'iteration': len(chain), 'previous_estimate': _pin(previous.estimate),
             'previous_source': _source_pin(previous.source),
             'earlier_sources': [_source_pin(tree.source) for tree in earlier],
             'rewrite_sites': sites, 'regions': list(rows['baseline'].values()) + list(rows['candidate'].values()),
             'groups': groups, 'whole_program': _whole(before, candidate, groups)}
    return block, [previous.estimate, previous.source] + [tree.source for tree in earlier]


def attribute(args):
    from swdb import workflow
    store = Store(args.records)
    baseline = _Side(store, 'baseline', args.baseline_estimate, args.baseline_source)
    candidate = _Side(store, 'candidate', args.candidate_estimate, args.candidate_source)
    differ = [key for key in SAME if baseline.estimate[key] != candidate.estimate[key]]
    _require(not differ, 'baseline and candidate estimates differ in ' + ', '.join(differ) + '; refusing to compare')
    sites = _sites(baseline, candidate)
    from swdb.library import default_root
    catalog = _Catalog(store, Path(args.library) if args.library else default_root(args.records))
    labels = {'baseline': _label(baseline, sites, catalog), 'candidate': _label(candidate, sites, catalog)}
    _add_floors(baseline, labels['baseline'], store)
    _add_floors(candidate, labels['candidate'], store)
    groups = _groups(baseline, candidate, labels)
    this_iteration, previous_inputs = _iteration(store, args, baseline, candidate, labels, catalog)
    inputs = [baseline.estimate, candidate.estimate, baseline.source, candidate.source] + previous_inputs
    date = max(str(data['updated']) for data in inputs)
    record = {'kind': 'attribution', 'schema_version': '0.4', 'id': args.id, 'status': 'draft',
              'created': date, 'updated': date, **workflow.CREATION_TAGS,
              'provenance': [{'id': 'attribution', 'kind': 'source_code', 'uri': None,
                              'description': 'Saved estimates split by code origin from a diff of their counted source trees; no timing, no re-estimation.'}],
              'format': FORMAT,
              'baseline_estimate': _pin(baseline.estimate), 'candidate_estimate': _pin(candidate.estimate),
              'baseline_source': _source_pin(baseline.source), 'candidate_source': _source_pin(candidate.source),
              'target_description': {'id': baseline.estimate['target_description'],
                                     'sha256': baseline.estimate['target_description_sha256']},
              'input': baseline.estimate['input'], 'threads': baseline.estimate['threads'],
              'evidence_kind': baseline.estimate['evidence_kind'],
              'catalog': catalog.pins(),
              'rewrite_sites': sites,
              'regions': list(labels['baseline'].values()) + list(labels['candidate'].values()),
              'groups': groups, 'whole_program': _whole(baseline, candidate, groups),
              'ranking': _ranking(labels['candidate'])}
    if this_iteration is not None:
        record['this_iteration'] = this_iteration
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

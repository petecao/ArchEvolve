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
   lies strictly inside it. Every other region is `untouched`.
5. Groups (F4). Each side's group seconds are summed per estimate trial (a region absent from
   a trial counts 0 s), then the median is taken per group; a single-run estimate is one
   trial. Group medians are never rescaled to the estimate's total. Whole-program totals are
   the estimates' own `seconds`.
6. Unknowns (F8). An unknown region makes its group's seconds unknown and lists the region
   with its bounds' `missing` reasons; every ratio that depends on an unknown is null.
7. Identity (F43, F44). The record pins both estimates, both source records and the target
   description by content hash. Its dates are the latest `updated` date of those inputs and
   dicts are built in a fixed order, so the same inputs give a byte-identical record.
8. Resource floor (ticket 07, F6). Each region's floor is max(compute bound, useful-bytes
   bandwidth bound) from the unchanged mechanism models at the pinned description's own
   rates, per trial then median. A missing rate gives an unknown floor naming it; no other
   description's rate is borrowed. Headroom = region seconds ÷ named limit.
9. Ranking (F7, floor-only tier). Candidate regions by floor headroom, largest first;
   unknown headrooms follow and are never ranked against known ones.
"""
import difflib
import statistics
from pathlib import Path, PurePosixPath

from swdb import artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store

FORMAT = 'swdb.attribution.v1'
ORIGINS = ('untouched', 'agent_rewritten', 'unattributed')
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


def _label(side, sites):
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
        for site in touched:
            site[side.name + '_regions'].append(region['id'])
        rows[region['id']] = {'side': side.name, 'region': region['id'], 'origin': origin, 'reason': reason,
                              'path': rel, 'lines': span, 'sites': [s['id'] for s in touched],
                              'seconds': region['seconds']}
    return rows


def _missing(region):
    return sorted({m for b in region['bounds'] + region['overheads'] for m in b['missing']})


def _group_seconds(side, labels):
    """{origin: (median seconds or None, [unknown region reasons])} from per-trial sums."""
    sums = {origin: [] for origin in ORIGINS}
    unknown = {origin: {} for origin in ORIGINS}
    for rows in side.trials():
        totals = {origin: 0. for origin in ORIGINS}
        for region in rows:
            origin = labels[region['id']]['origin'] if region['id'] in labels else 'unattributed'
            if region['seconds'] is None:
                totals[origin] = None
                unknown[origin].setdefault(region['id'], set()).update(_missing(region))
            elif totals[origin] is not None:
                totals[origin] += region['seconds']
        for origin in ORIGINS:
            sums[origin].append(totals[origin])
    result = {}
    for origin in ORIGINS:
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


def _groups(baseline, candidate, labels):
    base, cand = _group_seconds(baseline, labels['baseline']), _group_seconds(candidate, labels['candidate'])
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
    for i, row in enumerate(record.data['regions']):
        floor, seconds = row['resource_floor']['seconds'], row['seconds']
        if floor is not None and seconds is not None and floor > seconds * (1 + 1e-9) + 1e-12:
            yield Problem(record.rel, f'regions[{i}].resource_floor', f'resource floor {floor} s exceeds the region estimate {seconds} s')


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
    yield from _floor_problems(record)
    for field in ('baseline_estimate', 'candidate_estimate'):
        current = ctx.store.get(data[field]['id'], 'estimate')
        if current is not None and current['target_description_sha256'] != data['target_description']['sha256']:
            yield Problem(record.rel, 'target_description', 'pinned estimate used a different target description')


def attribute(args):
    from swdb import workflow
    store = Store(args.records)
    baseline = _Side(store, 'baseline', args.baseline_estimate, args.baseline_source)
    candidate = _Side(store, 'candidate', args.candidate_estimate, args.candidate_source)
    differ = [key for key in SAME if baseline.estimate[key] != candidate.estimate[key]]
    _require(not differ, 'baseline and candidate estimates differ in ' + ', '.join(differ) + '; refusing to compare')
    sites = _sites(baseline, candidate)
    labels = {'baseline': _label(baseline, sites), 'candidate': _label(candidate, sites)}
    _add_floors(baseline, labels['baseline'], store)
    _add_floors(candidate, labels['candidate'], store)
    groups = _groups(baseline, candidate, labels)
    inputs = [baseline.estimate, candidate.estimate, baseline.source, candidate.source]
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
              'rewrite_sites': sites,
              'regions': list(labels['baseline'].values()) + list(labels['candidate'].values()),
              'groups': groups, 'whole_program': _whole(baseline, candidate, groups),
              'ranking': _ranking(labels['candidate'])}
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

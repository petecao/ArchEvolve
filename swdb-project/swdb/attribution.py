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


def _pin(data):
    return {'id': data['id'], 'sha256': artifacts.digest(data)}


def _source_pin(data):
    return {'kind': data['kind'], 'id': data['id'], 'sha256': artifacts.digest(data),
            'artifact_sha256': data['artifact']['sha256']}


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
              'groups': groups, 'whole_program': _whole(baseline, candidate, groups)}
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

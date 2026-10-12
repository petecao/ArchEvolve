"""Fine-grained estimate attribution: `swdb attribute`. Created: 2026-10-11 ET.

Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md` (ticket 02, the narrowest path).
The command is the public interface; everything below it may change.

What it reads: two saved `estimate` records, the `workload_characterization` each one pins,
and the two source trees (a `source_snapshot` or `candidate` record's `artifact`) that were
counted. It never re-estimates and never binds a protocol, so it runs on old estimates
after the estimator code changed.

Rules used by this version (ticket 04 added the rewrite-site edge cases):

1. Diff (F17). SWDB diffs the two verified artifact trees itself, file by file, line by line
   (`difflib`, no junk heuristic). A stored candidate diff is never read. Each changed run of
   lines (one non-equal opcode) is one span, `[first, last]` per side; an empty side (pure
   insertion or deletion) is written `[p, p - 1]`, the insertion point before line `p`.
2. Paths. A region's `source_location.path` is made relative to its side's tree: strip the
   artifact root, else take the one manifest file the path ends with. A path in neither tree
   (for example a system header) cannot have changed.
3. Pieces. A region's home span is `[min, max]` of its start line and its accesses inside its
   own lexical function in the same file. Accesses elsewhere (another file or function) are
   inlined code, kept as `inlined` pieces by their own file and line (story 15).
4. Label. A region with no path or no line is `unattributed`. A region with a piece that
   overlaps a span on its own side is `agent_rewritten`; an insertion point overlaps a piece
   only when it lies strictly inside it. It is `mixed` when some line of its pieces is
   unchanged (F14). Every other region is `untouched`. Ticket 05: a region inside a site
   becomes `offload_command`, `intrinsic` or `library_call` when it executes one (see
   `_Catalog`); its group stays `agent_rewritten`, which lists per-origin seconds.
5. Sites (F1). Spans that one region overlaps, on either side, merge into one rewrite site,
   so no region's time is in two sites. Untouched regions are paired across sides through the
   line diff (`matched_region`, story 14); region IDs are never compared.
6. Groups (F4). Each side's group seconds are summed per estimate trial (a region absent from
   a trial counts 0 s), then the median is taken per group; a single-run estimate is one
   trial. Group medians are never rescaled to the estimate's total. Whole-program totals are
   the estimates' own `seconds`.
7. Unknowns (F8). An unknown region makes its group's seconds unknown and lists the region
   with its bounds' `missing` reasons; every ratio that depends on an unknown is null.
   Unattributed time above 10% of either total sets `unattributed_flagged` (F24).
8. Identity (F43, F44). The record pins both estimates, both source records and the target
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
10. Ranking (F7). Candidate regions with a known catalog bound first, by remaining gain bound
    (an upper limit, never an expected gain); then regions without one, by floor headroom;
    then every null value. Tiers are never ranked against each other. One top-level ranking:
    the candidate is the same in both comparisons, so its limits are too.
11. Catalog bound (ticket 08, F6, F21, F25). Given a saved campaign summary's site-finder
    regions (`--site-finder`), each region joins the site-finder regions whose function it
    overlaps (the function's span in that side's own tree, found by name: site-finder lines
    name the full-source revision; partial overlap is `mixed`). Each joined entry's mechanism
    models are the pinned description's offload mechanisms reached from the entry's
    `uses_intrinsics` through their `hardware_operations` and the description's functional
    observation commands. They run unchanged on the region's own counts, per trial then
    median. The bound is the lowest known entry; otherwise `needs_rewritten_counts` (a model
    lacks offload counts only a rewrite produces), `unknown_catalog_entry` or
    `no_catalog_match`; `no_site_finder` when none was given.
12. Split check (ticket 09, F15, F18, F19, F23). Given one `region_profile` per side
    (`--baseline-profile`, `--candidate-profile`), each measured source scope's exclusive
    thread-CPU seconds go to a group by file and line with the report's own rewrite sites: a
    scope's exclusive lines are its lines minus those of scopes nested inside it, and the
    labeling rules of `_label` apply to them. Measured share = group seconds / all measured
    scopes' seconds on that side. The fixed rule `SPLIT_RULE` passes when every group of both
    sides is within 0.1 of its estimated share; otherwise, or when a share is unknown, the
    report is `split_unverified`. A profile of another tree, input or thread count, or one
    dated before an estimate, is refused.
"""
import copy
import difflib
import statistics
from pathlib import Path, PurePosixPath

from swdb import artifacts, cpp_lexical, paths, writer
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
UNATTRIBUTED_THRESHOLD = 0.1   # F24: share of an estimate's total above which the split is flagged weak


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
    sub.add_argument('--site-finder', help='saved campaign_summary whose site-finder regions give catalog bounds (ticket 08)')
    sub.add_argument('--site-finder-iteration', type=int, default=None,
                     help='campaign iteration index whose site-finder regions to use (default: the last one that has them)')
    sub.add_argument('--baseline-profile', help='ticket 09: saved region_profile (`swdb bfs-profile`) timing the baseline tree')
    sub.add_argument('--candidate-profile', help='ticket 09: saved region_profile (`swdb bfs-profile`) timing the candidate tree')
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
        self._functions = {}
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
        lines = [line] + [a['source_location']['line'] for a in self._accesses(row) if self._at_home(where, a)]
        return rel, [min(lines), max(lines)], True

    def inlined(self, region_id):
        """Ticket 04: `[{path, lines}]` pieces of code inlined into the region from elsewhere.

        An access outside the region's own function (another file, or a line outside the
        enclosing function's lexical span) is inlined code: the LLVM pass keeps its own file and
        line but gives it the caller's region. Accesses are grouped by file and enclosing
        function, each group spanning `[min, max]` of its lines. A file outside the source tree
        cannot change, so its accesses add no piece."""
        row = self.locations.get(region_id) or {}
        where = row.get('source_location', {})
        groups = {}
        for access in self._accesses(row):
            if self._at_home(where, access):
                continue
            rel = self.relative(access['source_location']['path'])
            if rel is None:
                continue
            line = access['source_location']['line']
            groups.setdefault((rel, self._function(rel, line) or (line, line)), []).append(line)
        return [{'path': rel, 'lines': [min(lines), max(lines)]} for (rel, _), lines in sorted(groups.items())]

    @staticmethod
    def _accesses(row):
        return [a for a in (row or {}).get('access_patterns', [])
                if a['source_location'].get('path') and a['source_location'].get('line', 0) >= 1]

    def _at_home(self, where, access):
        """True when the access is in the region's own file and inside its own function's lines.
        Without a recognizable enclosing function, every access in the same file counts as home."""
        place = access['source_location']
        if place['path'] != where.get('path'):
            return False
        rel = self.relative(where['path'])
        home = self._function(rel, where['line']) if rel is not None else None
        return home is None or home[0] <= place['line'] <= home[1]

    def _function(self, rel, line):
        """1-based `(first, last)` lines of the top-level function lexically enclosing `line`, or None."""
        if rel not in self._functions:
            self._functions[rel] = cpp_lexical.function_spans('\n'.join(self.text(rel)))
        return next((span for span in self._functions[rel] if span[0] <= line <= span[1]), None)

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


def _line_maps(baseline, candidate):
    """{relative path: {baseline line: candidate line}} over the unchanged lines of files in both trees."""
    maps = {}
    for rel in sorted(baseline.files & candidate.files):
        matcher = difflib.SequenceMatcher(None, baseline.text(rel), candidate.text(rel), autojunk=False)
        maps[rel] = {i + 1 + k: j + 1 + k for i, j, size in matcher.get_matching_blocks() for k in range(size)}
    return maps


def _match_untouched(baseline, candidate, labels):
    """Story 14 (ticket 04): pair each untouched region with the other side's region at the same code.

    A baseline region's lines and inlined pieces are carried through the line diff (so inserted
    or deleted lines above them do not matter) and must equal a candidate region's, file by
    file, with the same region kind. A region outside both trees keeps its own path and lines. Only a one-to-one
    pairing is recorded; otherwise `matched_region` is null. Region IDs are never compared."""
    maps = _line_maps(baseline, candidate)

    def carried(side, path, lines):
        if side.name == 'baseline':
            lines = [maps.get(path, {}).get(line) for line in lines]
        return None if None in lines else (path, tuple(lines))

    def key(side, row):
        where = side.locations[row['region']]
        pieces = [carried(side, p['path'], p['lines']) for p in row['inlined']]
        if row['reason'] == 'outside_source_tree':
            home = ('outside', where['source_location']['path'], tuple(row['lines']))
        else:
            home = carried(side, row['path'], row['lines'])
        return None if home is None or None in pieces else (home, tuple(pieces), where.get('kind'))

    keyed = {}
    for side in (baseline, candidate):
        found = keyed.setdefault(side.name, {})
        for row in labels[side.name].values():
            row['matched_region'] = None
            if row['origin'] == 'untouched' and (k := key(side, row)) is not None:
                found.setdefault(k, []).append(row)
    for k, rows in keyed['baseline'].items():
        others = keyed['candidate'].get(k, [])
        if len(rows) == 1 and len(others) == 1:
            rows[0]['matched_region'], others[0]['matched_region'] = others[0]['region'], rows[0]['region']


def _merge_sites(raw, labels):
    """F1 (ticket 04): changed runs that one region overlaps, on either side, become one site.

    `raw` are the one-run sites of `_sites`; each label row lists the raw sites it overlaps.
    Merging is transitive, keeps the runs as `spans`, and numbers sites by their first run, so a
    region ends in at most one site and no region's time is counted in two. A site's `path` and
    line envelopes are null when its runs lie in several files (an inlined helper elsewhere)."""
    order = {s['id']: i for i, s in enumerate(raw)}
    root = {s['id']: s['id'] for s in raw}

    def find(sid):
        while root[sid] != sid:
            sid = root[sid]
        return sid

    for rows in labels.values():
        for row in rows.values():
            for sid in row['sites'][1:]:
                a, b = find(row['sites'][0]), find(sid)
                if a != b:
                    keep, drop = (a, b) if order[a] < order[b] else (b, a)
                    root[drop] = keep
    members = {}
    for site in raw:
        members.setdefault(find(site['id']), []).append(site)
    renamed, sites = {}, []
    for group in members.values():
        paths = list(dict.fromkeys(s['path'] for s in group))
        one_file = len(paths) == 1
        site = {'id': f'site.{len(sites) + 1}', 'path': paths[0] if one_file else None,
                'baseline_lines': _envelope(group, 'baseline_lines') if one_file else None,
                'candidate_lines': _envelope(group, 'candidate_lines') if one_file else None,
                'spans': [{'path': s['path'], 'baseline_lines': s['baseline_lines'], 'candidate_lines': s['candidate_lines']}
                          for s in group],
                'baseline_regions': [], 'candidate_regions': []}
        for member in group:
            renamed[member['id']] = site
        sites.append(site)
    for side, rows in labels.items():
        for row in rows.values():
            merged = renamed[row['sites'][0]] if row['sites'] else None
            row['sites'] = [merged['id']] if merged else []
            if merged:
                merged[side + '_regions'].append(row['region'])
    return sites


def _envelope(spans, key):
    return [min(s[key][0] for s in spans), max(s[key][1] for s in spans)]


def _overlaps(span, lines):
    first, last = lines
    if first <= last:
        return span[0] <= last and first <= span[1]
    return span[0] < first <= span[1]


def _label(side, sites, catalog=None):
    rows = {}
    for region in side.estimate['regions']:
        rel, span, located = side.place(region['id'])
        inlined = side.inlined(region['id']) if located else []
        pieces = ([(rel, span)] if located and rel is not None else []) + [(p['path'], p['lines']) for p in inlined]
        touched = [s for s in sites if any(s['path'] == path and _overlaps(lines, s[side.name + '_lines'])
                                           for path, lines in pieces)]
        if not located:
            origin, reason = 'unattributed', 'no_source_location'
        elif touched:
            origin, reason = 'agent_rewritten', 'overlaps_rewrite_site'
        elif rel is None:
            origin, reason = 'untouched', 'outside_source_tree'
        else:
            origin, reason = 'untouched', 'no_changed_line'
        evidence = catalog.evidence(side, region['id']) if touched and catalog is not None else []
        if evidence:
            origin = evidence[0]['origin']
            reason = REWRITE_REASONS[origin]
        mixed = bool(touched) and (rel is None or any(_partly_changed(path, lines, side.name, sites) for path, lines in pieces))
        rows[region['id']] = {'side': side.name, 'region': region['id'], 'origin': origin, 'reason': reason,
                              'mixed': mixed, 'path': rel, 'lines': span, 'inlined': inlined,
                              'sites': [s['id'] for s in touched], 'seconds': region['seconds'], 'evidence': evidence}
    return rows


def _partly_changed(rel, lines, side_name, sites):
    """F14 (ticket 04): True when some line of `lines` in file `rel` is not a changed line on this side."""
    changed = set()
    for site in sites:
        first, last = site[side_name + '_lines']
        if site['path'] == rel:
            changed.update(range(first, last + 1))
    return any(line not in changed for line in range(lines[0], lines[1] + 1))


def _split(before, after, catalog=None):
    """Ticket 04: (merged rewrite sites, labels) for one diff, `before` as baseline, `after` as candidate."""
    raw = _sites(before, after)
    labels = {'baseline': _label(before, raw, catalog), 'candidate': _label(after, raw, catalog)}
    sites = _merge_sites(raw, labels)
    _match_untouched(before, after, labels)
    return sites, labels


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
        self.library = library
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
            'unattributed_threshold': UNATTRIBUTED_THRESHOLD,
            'unattributed_flagged': _unattributed_flagged(groups),
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


def _headroom(limit, estimate, bound, unknown_limit='unknown_limit'):
    """Estimate ÷ the named limit; null with a reason when it cannot be a number.
    `unknown_limit` names why the limit is unknown (ticket 08: the catalog bound's own reason)."""
    reason = ('unknown_estimate' if estimate is None else unknown_limit if bound is None
              else 'zero_limit' if bound == 0 else None)
    return {'limit': limit, 'value': None if reason else estimate / bound, 'reason': reason}


# --- Ticket 08: catalog bound (F6, F21, F25) ---------------------------------------------------
#
# Site-finder regions come from a saved campaign summary: one iteration's chosen `regions`
# rows, each with `why.source` (path, full-source revision and lines) and `why.applications`
# (the entries that apply). Their lines name the full-source revision, not either tree
# attributed here (risks C1, C2), so a site-finder region is placed in each side's own tree by
# the function its ID names (`<implementation>/<function>:<first>-<last>`), as ticket 73's
# `workspace_region_lines` does. An estimate region joins it when one of its pieces (home span
# or inlined piece) overlaps that function's span; `mixed` when some piece lies outside (F21).

COUNT_GAPS = ('address_stream_counts', 'accelerator_calls')   # offload counts only a rewrite produces
UNKNOWN_ENTRY = ('missing_inputs', 'entry_changed', 'not_in_library')
SITE_FINDER_REGION = r'^.+/(?P<function>[A-Za-z_]\w*):[0-9]+-[0-9]+$'
RANKING_RULE = {
    'remaining_gain_bound': 'Upper limit, never an expected gain: share x max(0, 1 - catalog bound / estimate), '
                            'share = region seconds / candidate total seconds. Regions with a known catalog bound only; '
                            'largest first.',
    'floor_headroom': 'Regions without a known catalog bound: estimate / resource floor, largest first. Never ranked '
                      'against the remaining_gain_bound tier.',
    'unknown': 'Regions whose ranking value is null, in region-ID order, after every known value.'}


class _SiteFinder:
    """One iteration's site-finder regions from a saved campaign summary."""

    def __init__(self, store, summary_id, iteration=None):
        import re
        self.summary = _record(store, summary_id, ('campaign_summary',))
        with_why = [it for it in self.summary.get('iterations', [])
                    if any(isinstance(r.get('why'), dict) for r in it.get('regions', []))]
        if iteration is None:
            _require(with_why, f'campaign summary {summary_id!r} records no site-finder region with its why')
            chosen = with_why[-1]
        else:
            chosen = next((it for it in with_why if it.get('index') == iteration), None)
            _require(chosen is not None, f'campaign summary {summary_id!r} iteration {iteration} records no site-finder region')
        self.iteration = chosen['index']
        self.query_sha256 = (chosen.get('site_finder') or {}).get('query_sha256')
        # Ticket 10: the kernel and target the site finder ran under, so it can find this report again.
        params = ((chosen.get('site_finder') or {}).get('parameters')
                  or (self.summary.get('site_finder') or {}).get('parameters') or {})
        self.kernel, self.target = params.get('kernel'), params.get('target')
        self.regions = []
        for row in sorted((r for r in chosen['regions'] if isinstance(r.get('why'), dict)), key=lambda r: r['id']):
            match = re.match(SITE_FINDER_REGION, row['id'])
            source = row['why'].get('source') or {}
            self.regions.append({
                'id': row['id'], 'function': match['function'] if match else None, 'path': source.get('path'),
                'revision': source.get('revision'), 'lines': source.get('lines'),
                'applications': sorted(({'entry': a['entry'], 'kind': a.get('kind'), 'content_sha256': a.get('content_sha256')}
                                        for a in row['why'].get('applications', [])), key=lambda a: a['entry'])})

    def block(self):
        return {'campaign_summary': _pin(self.summary), 'iteration': self.iteration, 'query_sha256': self.query_sha256,
                'kernel': self.kernel, 'target': self.target,
                'regions': [{k: r[k] for k in ('id', 'function', 'path', 'revision', 'lines')}
                            | {'entries': [a['entry'] for a in r['applications']]} for r in self.regions]}


def _tree_file(side, path):
    """The one file of the side's tree that is `path`, or ends with it, or that `path` ends with."""
    if not path:
        return None
    if path in side.files:
        return path
    matches = sorted(f for f in side.files if f.endswith('/' + path) or path.endswith('/' + f))
    return matches[0] if len(matches) == 1 else None


def _joins(side, labels, finder):
    """{region ID: [(site-finder region, mixed)]} for one side (F21, risks C1/C2)."""
    placed = []
    for sf in finder.regions:
        rel = _tree_file(side, sf['path'])
        span = cpp_lexical.function_span('\n'.join(side.text(rel)), sf['function']) if rel and sf['function'] else None
        if span:
            placed.append((sf, rel, span))
    joins = {}
    for row in labels.values():
        pieces = ([(row['path'], row['lines'])] if row['path'] and row['lines'] else []) + [
            (p['path'], p['lines']) for p in row['inlined']]
        for sf, rel, span in placed:
            if any(path == rel and _overlaps(span, lines) for path, lines in pieces):
                inside = all(path == rel and span[0] <= lines[0] and lines[1] <= span[1] for path, lines in pieces)
                joins.setdefault(row['region'], []).append((sf, not inside))
    return joins


class _Bounds:
    """Catalog bounds of one attribution: the site finder, the typed library and per-entry models."""

    def __init__(self, finder, library):
        self.finder, self.library = finder, library

    def _hardware_operations(self, entry_id):
        """Hardware operations of every intrinsic the entry uses, directly or through library operations."""
        seen, pending, found = set(), [entry_id], set()
        while pending:
            data = self.library.get(pending.pop()) if self.library else None
            if data is None:
                continue
            if data.get('kind') == 'intrinsic':
                found.update(data.get('hardware_operations', []))
                continue
            for ref in data.get('uses_intrinsics', []) + data.get('uses_library_operations', []):
                if ref not in seen:
                    seen.add(ref)
                    pending.append(ref)
        return found

    def mechanisms(self, application, target):
        """(the entry's mechanisms in the description, reason when there are none or the entry cannot be read).

        F25: the entry's intrinsics' hardware operations select the description's functional
        observation commands whose operations they all provide; those commands' events select
        the offload mechanisms (`selector.domain: offload`, or `selector.event_ids` naming one)."""
        entry = self.library.get(application['entry']) if self.library else None
        if entry is None:
            return [], 'not_in_library'
        if application.get('content_sha256') and artifacts.digest(entry) != application['content_sha256']:
            return [], 'entry_changed'
        operations = self._hardware_operations(application['entry'])
        commands = (target.get('functional_observation') or {}).get('commands', [])
        events = {c['event'] for c in commands if c.get('hardware_operations') and set(c['hardware_operations']) <= operations}
        own = [m for m in target['mechanisms'] if events and (
            (m.get('selector') or {}).get('domain') == 'offload' or set((m.get('selector') or {}).get('event_ids') or []) & events)]
        return own, None if own else 'no_offload_mechanism'


def _entry_trial(region, calls, mechanisms, side, target):
    """One trial: (seconds, per-mechanism results) composed as the estimator composes a region."""
    from swdb import analytic_composition, analytic_models
    target_sha = side.estimate['target_description_sha256']
    context = {'target_description_sha256': target_sha,
               'logical_count_target_description_sha256': (side.estimate.get('count_reuse') or {}).get(
                   'counted_target_description_sha256') or target_sha,
               'configured_threads': target['threads'],
               'observation_contract': side.characterization.get('observation_contract'),
               'characterization_id': side.characterization['id'],
               'characterization_sha256': side.estimate['characterization_sha256'],
               'composition_contract': target.get('composition_contract'),
               'source_calls': calls, 'source_accesses': region['access_patterns']}
    models = [m['model'] for m in target['mechanisms']]
    results = [analytic_models.evaluate(region, m, models, target['threads'],
                                        context={**context, 'selected_domain': analytic_composition.domain(m)})
               for m in mechanisms]
    bounds = [r for r, m in zip(results, mechanisms) if m.get('accounting', 'resource_bound') != 'additive_overhead']
    overheads = [r for r, m in zip(results, mechanisms) if m.get('accounting', 'resource_bound') == 'additive_overhead']
    if any(r['seconds'] is None for r in results):
        return None, results
    return max((r['seconds'] for r in bounds), default=0.) + sum(r['seconds'] for r in overheads), results


def _entry_bound(region_id, counted, calls, mechanisms, side, target):
    """Median over trials of the entry's composed seconds on the region's own counts (absent = 0 s)."""
    per_trial = [_entry_trial(t[region_id], calls.get(region_id, []), mechanisms, side, target) if region_id in t else None
                 for t in counted]
    rows = []
    for i, mechanism in enumerate(mechanisms):
        results = [t[1][i] for t in per_trial if t is not None]
        rows.append({'model': mechanism['model'], 'accounting': mechanism.get('accounting', 'resource_bound'),
                     'seconds': _median([t[1][i]['seconds'] if t else 0. for t in per_trial]),
                     'missing': sorted({m for r in results for m in r['missing']})})
    seconds = _median([t[0] if t else 0. for t in per_trial])
    missing = sorted({m for r in rows for m in r['missing']})
    reason = None
    if seconds is None:
        reason = 'needs_rewritten_counts' if any(m.startswith(COUNT_GAPS) for m in missing) else 'missing_inputs'
    return {'seconds': seconds, 'reason': reason, 'mechanisms': rows, 'missing': missing}


def _add_catalog(side, labels, store, bounds, counted, target):
    """Annotate each region row of one side with its catalog bound and catalog headroom."""
    if bounds is None or bounds.finder is None:
        for row in labels.values():
            row['catalog_bound'] = {'seconds': None, 'entry': None, 'reason': 'no_site_finder', 'mixed': False,
                                    'site_finder_regions': [], 'entries': [], 'missing': []}
            row['headroom'].append(_headroom('catalog_bound', row['seconds'], None, 'no_site_finder'))
        return
    joins = _joins(side, labels, bounds.finder)
    calls = {}
    for call in side.characterization.get('unmodeled_calls', []):
        calls.setdefault(call.get('region'), []).append(call)
    for row in labels.values():
        joined = joins.get(row['region'], [])
        entries = {}
        for sf, _ in joined:
            for application in sf['applications']:
                entries.setdefault(application['entry'], (application, []))[1].append(sf['id'])
        evaluated = []
        for entry_id in sorted(entries):
            application, regions = entries[entry_id]
            mechanisms, reason = bounds.mechanisms(application, target)
            result = (_entry_bound(row['region'], counted, calls, mechanisms, side, target) if mechanisms
                      else {'seconds': None, 'reason': reason, 'mechanisms': [], 'missing': []})
            evaluated.append({'entry': entry_id, 'kind': application.get('kind'),
                              'content_sha256': application.get('content_sha256'),
                              'site_finder_regions': sorted(set(regions)), **result})
        known = [e for e in evaluated if e['seconds'] is not None]
        best = min(known, key=lambda e: (e['seconds'], e['entry'])) if known else None
        reasons = {e['reason'] for e in evaluated}
        reason = (None if best else 'needs_rewritten_counts' if 'needs_rewritten_counts' in reasons
                  else 'unknown_catalog_entry' if reasons & set(UNKNOWN_ENTRY) else 'no_catalog_match')
        row['catalog_bound'] = {'seconds': best['seconds'] if best else None, 'entry': best['entry'] if best else None,
                                'reason': reason, 'mixed': any(mixed for _, mixed in joined),
                                'site_finder_regions': sorted({sf['id'] for sf, _ in joined}), 'entries': evaluated,
                                'missing': sorted({m for e in evaluated for m in e['missing']})}
        row['headroom'].append(_headroom('catalog_bound', row['seconds'], row['catalog_bound']['seconds'], reason))


def _add_limits(side, labels, store, bounds=None):
    """Annotate each region row of one side with its resource floor, catalog bound and both headrooms."""
    counted = _counted_trials(side, store)
    target = side.estimate['target_description_snapshot']
    _require(artifacts.digest(target) == side.estimate['target_description_sha256'],
             f'{side.name} estimate target description snapshot differs from the hash it pins')
    for row in labels.values():
        floor = _resource_floor(row['region'], counted, target)
        row['resource_floor'] = floor
        row['headroom'] = [_headroom('resource_floor', row['seconds'], floor['seconds'])]
    _add_catalog(side, labels, store, bounds, counted, target)


def _remaining_gain_bound(estimate, bound, total):
    """F7: share x max(0, 1 - bound / estimate), or (None, reason). An upper limit, never an expected gain."""
    if estimate is None:
        return None, 'unknown_estimate'
    if total is None:
        return None, 'unknown_share'
    if total == 0:
        return None, 'zero_total'
    if estimate == 0:
        return 0., None
    return estimate / total * max(0., 1 - bound / estimate), None


def _ranking(labels, total):
    """Candidate regions for the next iteration (F7), in three tiers never ranked against each other.

    1. `remaining_gain_bound`: regions with a known catalog bound, largest first.
    2. `floor_headroom`: regions without one (floor-only), by floor headroom, largest first.
    3. `unknown`: every null value, in region-ID order: a known catalog bound whose remaining
       gain bound is null (limit `catalog_bound`), or a floor-only region with a null floor
       headroom (limit `resource_floor`).
    Ties go by region ID; positions are 1-based over the whole list.
    """
    def limit(row, name):
        return next(h for h in row['headroom'] if h['limit'] == name)
    gains, floors, unknown = [], [], []
    for row in labels.values():
        if row['catalog_bound']['seconds'] is not None:
            value, reason = _remaining_gain_bound(row['seconds'], row['catalog_bound']['seconds'], total)
            (gains if value is not None else unknown).append((row, 'catalog_bound', value, reason))
        else:
            floor = limit(row, 'resource_floor')
            (floors if floor['value'] is not None else unknown).append((row, 'resource_floor', floor['value'], floor['reason']))
    entries = ([('remaining_gain_bound', *e) for e in sorted(gains, key=lambda e: (-e[2], e[0]['region']))]
               + [('floor_headroom', *e) for e in sorted(floors, key=lambda e: (-e[2], e[0]['region']))]
               + [('unknown', *e) for e in sorted(unknown, key=lambda e: e[0]['region'])])
    return [{'position': i, 'side': row['side'], 'region': row['region'], 'tier': tier, 'limit': name,
             'value': value, 'reason': reason}
            for i, (tier, row, name, value, reason) in enumerate(entries, start=1)]


def _unattributed_flagged(groups):
    """F24: True when either side's unattributed share is above the threshold; null when no known
    share is above it but one is unknown; otherwise False. A flag never stops the report."""
    unattributed = next(g for g in groups if g['origin'] == 'unattributed')
    shares = [unattributed['baseline_share'], unattributed['candidate_share']]
    if any(share is not None and share > UNATTRIBUTED_THRESHOLD for share in shares):
        return True
    return None if None in shares else False


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
    finder = data.get('site_finder')
    if finder is not None:   # ticket 08: the site-finder regions that gave catalog bounds are unchanged
        current = ctx.store.get(finder['campaign_summary']['id'], 'campaign_summary')
        if current is None or artifacts.digest(current) != finder['campaign_summary']['sha256']:
            yield Problem(record.rel, 'site_finder', f'pinned campaign summary {finder["campaign_summary"]["id"]!r} is missing or changed')
    for field in ('baseline_estimate', 'candidate_estimate'):
        current = ctx.store.get(data[field]['id'], 'estimate')
        if current is not None and current['target_description_sha256'] != data['target_description']['sha256']:
            yield Problem(record.rel, 'target_description', 'pinned estimate used a different target description')
    yield from _validate_iteration(record, ctx)
    yield from _validate_split_check(record, ctx)


def _validate_split_check(record, ctx):
    """Ticket 09: both timed profiles are unchanged and the verdict follows the gaps under the fixed rule."""
    from swdb.problems import Problem
    check = record.data.get('split_check')
    if check is None:
        return
    for side, pin in sorted(check['profiles'].items()):
        current = ctx.store.get(pin['id'], 'region_profile')
        if current is None or artifacts.digest(current) != pin['sha256']:
            yield Problem(record.rel, f'split_check.profiles.{side}', f'pinned region profile {pin["id"]!r} is missing or changed')
    if check['rule'] != SPLIT_RULE:
        yield Problem(record.rel, 'split_check.rule', 'split-check rule differs from the fixed rule')
    passed = not check['reasons'] and all(g['within_rule'] is True for g in check['gaps'])
    if check['verdict'] != ('passed' if passed else 'split_unverified'):
        yield Problem(record.rel, 'split_check.verdict', 'split-check verdict does not follow its gaps and reasons')


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


# --- Ticket 09: split check (F15, F18, F19, F23) -------------------------------------------------
#
# The rule is fixed before any timing and recorded in every checked report. A measured scope is
# one `swdb bfs-profile` source region (function or loop of the timed translation unit) with its
# accumulated exclusive thread-CPU seconds. Exclusive time lies on the scope's own lines, so
# lines of scopes nested inside it are removed before it is labeled.

SPLIT_RULE = {
    'id': 'swdb.split_check.v1',
    'max_abs_share_gap': 0.1,
    'tolerance': 1e-9,
    'statement': 'Passed when, for every group (untouched, agent_rewritten, unattributed) on both sides, '
                 '|measured share - estimated share| <= 0.1 (10 percentage points, compared with a 1e-9 float '
                 'tolerance). Otherwise, or when a share is unknown, split_unverified. Fixed before timing (F19).',
    'estimated_share': "the report's group share: group seconds / that estimate's total seconds",
    'measured_share': "group exclusive thread-CPU seconds / the sum of every measured scope's exclusive "
                      "thread-CPU seconds in that side's region_profile"}
PROFILE_DONE = ('partial', 'complete')   # `swdb bfs-profile` ends a successful run as `partial`


def _runs(lines):
    """Sorted line numbers as contiguous `[first, last]` runs."""
    runs = []
    for line in lines:
        if runs and line == runs[-1][1] + 1:
            runs[-1][1] = line
        else:
            runs.append([line, line])
    return runs


def _nested(inner, outer):
    if inner is outer or inner.get('path') != outer.get('path'):
        return False
    a, b = inner.get('byte_range'), outer.get('byte_range')
    if a and b:
        return b[0] <= a[0] and a[1] <= b[1] and a != b
    return outer['lines'][0] <= inner['lines'][0] and inner['lines'][1] <= outer['lines'][1] and inner['lines'] != outer['lines']


class _Profile:
    """One side's saved region profile, checked against the attributed estimate and tree (F18)."""

    def __init__(self, store, rid, side, estimates):
        self.data = data = _record(store, rid, ('region_profile',))
        name = side.name
        state = data['outcome']['state']
        _require(state in PROFILE_DONE, f'{name} profile {rid!r} did not finish (outcome {state!r}); refusing to compare')
        context = data.get('context') or {}
        _require(context.get('candidate_sha256') == side.source['artifact']['sha256'],
                 f'{name} profile {rid!r} timed another source tree than the {name} source; refusing to compare')
        self.workload = (context.get('workload') or {}).get('id')
        _require(self.workload == side.estimate['input'],
                 f'{name} profile {rid!r} timed input {self.workload!r}, not the estimates\' input '
                 f'{side.estimate["input"]!r}; refusing to compare')
        _require(context.get('threads') == side.estimate['threads'],
                 f'{name} profile {rid!r} ran {context.get("threads")!r} threads, not the estimates\' '
                 f'{side.estimate["threads"]}; refusing to compare')
        latest = max(str(e['created']) for e in estimates)
        _require(str(data['created']) >= latest,
                 f'{name} profile {rid!r} is dated {data["created"]}, before an estimate ({latest}): the split '
                 'check must be prospective (LR-02); refusing to compare')
        self.rows = [r for r in data['regions'] if r.get('basis') == 'measured']
        _require(self.rows and len(self.rows) == len(data['regions']) and all(
            isinstance((r.get('metrics') or {}).get('exclusive_thread_cpu_seconds'), (int, float)) for r in self.rows),
                 f'{name} profile {rid!r} has no measured exclusive thread-CPU seconds for every region')
        self.context = context

    def pin(self):
        context = self.context
        return {'id': self.data['id'], 'sha256': artifacts.digest(self.data), 'evaluation': self.data.get('evaluation'),
                'machine': self.data.get('machine'), 'workload': self.workload, 'threads': context['threads'],
                'lane': context.get('lane'), 'load_average': context.get('load_average'),
                'primary_load_average': context.get('primary_load_average')}


def _scope_label(side, row, rows, sites):
    """The `_label` rules on one measured scope's exclusive lines."""
    lines = row.get('lines')
    if not row.get('path') or not lines:
        return {'origin': 'unattributed', 'reason': 'no_source_location', 'mixed': False, 'exclusive_lines': [], 'sites': []}
    own = set(range(lines[0], lines[1] + 1))
    for other in rows:
        if other.get('lines') and _nested(other, row):
            own -= set(range(other['lines'][0], other['lines'][1] + 1))
    runs = _runs(sorted(own)) or [list(lines)]
    rel = side.relative(row['path'])
    key = side.name + '_lines'
    touched = [s for s in sites if any(span['path'] == rel and _overlaps(run, span[key])
                                       for span in s['spans'] for run in runs)] if rel else []
    if touched:
        origin, reason = 'agent_rewritten', 'overlaps_rewrite_site'
    else:
        origin, reason = 'untouched', 'outside_source_tree' if rel is None else 'no_changed_line'
    changed = {line for s in touched for span in s['spans'] if span['path'] == rel
               for line in range(span[key][0], span[key][1] + 1)}
    mixed = bool(touched) and any(line not in changed for run in runs for line in range(run[0], run[1] + 1))
    return {'origin': origin, 'reason': reason, 'mixed': mixed, 'exclusive_lines': runs, 'sites': [s['id'] for s in touched]}


def _split_check(sides, profiles, sites, groups):
    """F19: the split_check block; `sides` and `profiles` are in baseline, candidate order."""
    regions, measured, gaps, reasons = [], [], [], []
    estimated = {g['origin']: g for g in groups}
    for side, profile in zip(sides, profiles):
        seconds = {origin: 0. for origin in ORIGINS}
        for row in profile.rows:
            label = _scope_label(side, row, profile.rows, sites)
            value = row['metrics']['exclusive_thread_cpu_seconds']
            seconds[label['origin']] += value
            regions.append({'side': side.name, 'region': row['id'], 'kind': row.get('kind'), 'path': row.get('path'),
                            'lines': row.get('lines'), **label, 'seconds': value})
        total = sum(seconds.values())
        if total <= 0:
            reasons.append({'side': side.name, 'origin': None, 'reason': 'no_measured_time'})
        for origin in ORIGINS:
            share = seconds[origin] / total if total > 0 else None
            measured.append({'side': side.name, 'origin': origin, 'seconds': seconds[origin], 'share': share})
            expected = estimated[origin][side.name + '_share']
            if expected is None:
                reasons.append({'side': side.name, 'origin': origin, 'reason': 'unknown_estimated_share'})
            gap = None if share is None or expected is None else share - expected
            within = None if gap is None else abs(gap) <= SPLIT_RULE['max_abs_share_gap'] + SPLIT_RULE['tolerance']
            if within is False:
                reasons.append({'side': side.name, 'origin': origin, 'reason': 'gap_above_rule'})
            gaps.append({'side': side.name, 'origin': origin, 'estimated_share': expected, 'measured_share': share,
                         'gap': gap, 'within_rule': within})
    return {'verdict': 'split_unverified' if reasons else 'passed', 'rule': dict(SPLIT_RULE), 'reasons': reasons,
            'profiles': {side.name: profile.pin() for side, profile in zip(sides, profiles)},
            'measured_shares': measured, 'gaps': gaps, 'regions': regions}


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


def _iteration(store, args, baseline, candidate, labels, catalog=None, bounds=None):
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
    sites, rows = _split(before, candidate, catalog)
    changed = {'previous': _last_changed(previous, chain[:-1], catalog),
               'candidate': _last_changed(candidate, chain, catalog)}
    for row in labels['baseline'].values():
        row['last_changed_iteration'] = 0
    for row in list(labels['candidate'].values()) + list(rows['candidate'].values()):
        row['last_changed_iteration'] = changed['candidate'][row['region']]
    for row in rows['baseline'].values():
        row['last_changed_iteration'] = changed['previous'][row['region']]
    _add_limits(before, rows['baseline'], store, bounds)
    _add_limits(candidate, rows['candidate'], store, bounds)
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
    _require((args.baseline_profile is None) == (args.candidate_profile is None),
             '--baseline-profile and --candidate-profile go together')
    profiles = [_Profile(store, rid, side, [baseline.estimate, candidate.estimate])
                for rid, side in ((args.baseline_profile, baseline), (args.candidate_profile, candidate))] if args.baseline_profile else []
    from swdb.library import default_root
    catalog = _Catalog(store, Path(args.library) if args.library else default_root(args.records))
    finder = _SiteFinder(store, args.site_finder, args.site_finder_iteration) if args.site_finder else None
    _require(finder is not None or args.site_finder_iteration is None, '--site-finder-iteration needs --site-finder')
    bounds = _Bounds(finder, catalog.library)
    sites, labels = _split(baseline, candidate, catalog)
    _add_limits(baseline, labels['baseline'], store, bounds)
    _add_limits(candidate, labels['candidate'], store, bounds)
    groups = _groups(baseline, candidate, labels)
    this_iteration, previous_inputs = _iteration(store, args, baseline, candidate, labels, catalog, bounds)
    inputs = [baseline.estimate, candidate.estimate, baseline.source, candidate.source] + previous_inputs + (
        [finder.summary] if finder else []) + [p.data for p in profiles]
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
              **({'site_finder': finder.block()} if finder else {}),
              'rewrite_sites': sites,
              'regions': list(labels['baseline'].values()) + list(labels['candidate'].values()),
              'groups': groups, 'whole_program': _whole(baseline, candidate, groups),
              'ranking': _ranking(labels['candidate'], candidate.estimate['seconds']),
              'ranking_rule': dict(RANKING_RULE)}
    if this_iteration is not None:
        record['this_iteration'] = this_iteration
    if profiles:
        record['split_check'] = _split_check((baseline, candidate), profiles, sites, groups)
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

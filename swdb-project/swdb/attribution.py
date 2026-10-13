"""Fine-grained estimate attribution: `swdb attribute`. Created: 2026-10-11 ET. Updated: 2026-10-12 ET (cpu-description review F1: floor-only memory coverage;
final review fixes F40-F47: split-check shares, profile order and identity, comparable estimators,
one ranking).

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
   `_OriginSignals`); its group stays `agent_rewritten`, which lists per-origin seconds. Review fix
   F34: `offload_command` needs a command the pinned description's functional observation
   contract names; a region inside a site that executes any other command is `unattributed`
   (`unbound_offload_command`).
5. Sites (F1). Spans that one region overlaps, on either side, merge into one rewrite site,
   so no region's time is in two sites. Untouched regions are paired across sides through the
   line diff (`matched_region`, story 14); region IDs are never compared.
6. Groups (F4). Each side's group seconds are summed per estimate trial (a region absent from
   a trial counts 0 s), then the median is taken per group; a single-run estimate is one
   trial. Group medians are never rescaled to the estimate's total. Whole-program totals are
   the estimates' own `seconds`. Review fix F33 (F2): a region's seconds inside calls (its
   `unmodeled_calls` or call-covering estimate rows) go to `unattributed` per trial; the
   region's group keeps the seconds recomposed without those rows. The split check alone keeps
   them in the region's group (F40, rule 13).
7. Unknowns (F8). An unknown region makes its group's seconds unknown and lists the region
   with its bounds' `missing` reasons; every ratio that depends on an unknown is null.
   Unattributed time above 10% of either total sets `unattributed_flagged` (F24).
8. Identity (stories 43, 44). The record pins both estimates, both source records and the target
   description by content hash. Its dates are the latest `updated` date of those inputs (so
   `created` is the newest input's date, not the day the report was made) and dicts are built
   in a fixed order, so the same inputs give a byte-identical record. One caveat: under
   `SWDB_EXTENSA_CAMPAIGN` the record carries `workflow.CREATION_TAGS` (`mode`, `campaign`),
   which enter `identity_sha256`, so the same inputs give other bytes inside an Extensa
   campaign than outside one.
9. Iterations (F13, ticket 06). Given the previous accepted candidate (`--previous-estimate`,
   `--previous-source`), the top-level comparison stays cumulative (original baseline ->
   candidate) and a `this_iteration` block repeats it against the previous candidate. The
   candidate is iteration 2 + the number of `--earlier-source` trees (accepted candidates
   before the previous one, oldest first). Each region row records `last_changed_iteration`:
   the newest iteration whose diff into that region's version labels it rewritten (0 = never,
   null = no source location). Without a previous candidate the record is the ticket 02 one.
10. Resource floor (ticket 07, F6). Each region's floor is max(compute bound, useful-bytes
   bandwidth bound) from the unchanged mechanism models at the pinned description's own
   rates, per trial then median. A missing rate gives an unknown floor naming it; no other
   description's rate is borrowed. Headroom = region seconds ÷ named limit. `this_iteration`
   region rows carry floors too (same row shape; the previous candidate's from its own estimate).
11. Ranking (F7). Candidate regions with a known catalog bound first, by remaining gain bound
    (an upper limit, never an expected gain; clamped at 0, ties by floor headroom, F29); then
    regions whose bound is `no_catalog_match` or `no_site_finder`, by floor headroom; then
    every null value, including every unknown catalog bound with its reason (F36). Tiers are
    never ranked against each other. One top-level ranking, over the cumulative comparison's
    candidate regions (F45). A candidate row's catalog bound runs on its matched region's counts
    (F35), and the match differs per comparison, so the `this_iteration` bounds can differ from
    the ranked ones; they are informational (`ranking_rule.comparison`).
12. Catalog bound (ticket 08, F6, F21, F25; review fixes F30-F32, F35). Given a saved
    Extensa campaign summary's site-finder regions (`--site-finder`), each site-finder region's
    lines are moved from the full-source revision (`--site-finder-source`) into each tree by
    their offset inside the named function; a region joins when one of its pieces overlaps the
    moved lines, `mixed` when some line of its pieces lies outside every joined span. Without
    a way to move them, the whole function joins (`join: function`, with the reason); a
    site-finder region that cannot be placed makes the bounds it could reach
    `site_finder_unplaced`. Each joined entry's mechanism models are the pinned description's
    offload mechanisms reached from the entry's `uses_intrinsics` through their
    `hardware_operations` and the description's functional observation commands. They run
    unchanged on the region's baseline counts (a candidate row reads its `matched_region`'s;
    none gives `no_baseline_counts`), per trial with that trial's calls, then median. The bound
    is the lowest known entry; otherwise `needs_rewritten_counts` (a model lacks offload counts
    only a rewrite produces), `unknown_catalog_entry` (also an entry with no hash,
    `entry_unhashed`), `no_baseline_counts`, `site_finder_unplaced` or `no_catalog_match`;
    `no_site_finder` when none was given.
13. Split check (ticket 09, F15, F18, F19, F23). Given one `region_profile` per side
    (`--baseline-profile`, `--candidate-profile`), each measured source scope's exclusive
    thread-CPU seconds go to a group by file and line with the report's own rewrite sites: a
    scope's exclusive lines are its lines minus those of scopes nested inside it, and the
    labeling rules of `_label` apply to them. Measured share = group seconds / all measured
    scopes' seconds on that side. Estimated share (F40): group seconds with every region's full
    seconds, call time included, under its own label, / that estimate's total, because measured
    exclusive time holds the scope's uninstrumented callees. The fixed rule `SPLIT_RULE`
    (`swdb.split_check.v2`) passes when every group of both sides is within 0.1 of its estimated
    share; otherwise, or when a share is unknown, the report is `split_unverified`. Refused: a
    profile of another tree, input, thread count, machine, counted BFS sources or input seed
    (F18, F44), or one not dated strictly after both estimates (F43: estimates carry only a date).
"""
import copy
import difflib
import re
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
# Fields two compared estimates must share. F47 (final review M8): `estimator_sha256` too, so drift and
# realized speedup never mix an estimator change with the code change (F27).
COMPARABLE = ('input', 'target_description_sha256', 'threads', 'evidence_kind', 'estimator_sha256')
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
    sub.add_argument('--site-finder', help='saved Extensa campaign summary whose site-finder regions give catalog bounds (ticket 08)')
    sub.add_argument('--site-finder-source', default=None,
                     help='source_snapshot or candidate record of the full-source revision the site-finder lines name; '
                          'without it a site-finder region joins its whole function (join: function)')
    sub.add_argument('--site-finder-iteration', type=int, default=None,
                     help='Extensa campaign summary iteration index whose site-finder regions to use (default: the last one that has them)')
    sub.add_argument('--baseline-profile', help='ticket 09: saved region_profile (`swdb bfs-profile`) timing the baseline tree')
    sub.add_argument('--candidate-profile', help='ticket 09: saved region_profile (`swdb bfs-profile`) timing the candidate tree')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=attribute)


def _require(condition, message):
    if not condition:
        raise Failure(message)


def _require_comparable(first, second, names):
    """Refuse two estimates that differ in any `COMPARABLE` field; `names` is how the message calls them."""
    differ = [key for key in COMPARABLE if first.get(key) != second.get(key)]
    _require(not differ, f'{names} estimates differ in ' + ', '.join(differ) + '; refusing to compare')


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
        if touched and catalog is not None and catalog.unbound_commands(side, region['id']):
            origin, reason = 'unattributed', 'unbound_offload_command'   # F34: beats every other signal
        mixed = bool(touched) and (rel is None or any(_partly_changed(path, lines, side.name, sites) for path, lines in pieces))
        rows[region['id']] = {'side': side.name, 'region': region['id'], 'origin': origin, 'reason': reason,
                              'mixed': mixed, 'path': rel, 'lines': span, 'inlined': inlined,
                              'sites': [s['id'] for s in touched], 'seconds': region['seconds'],
                              'unmodeled_calls': _unmodeled_calls(side, region['id']), 'evidence': evidence}
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


def _calls_symbol(call, symbol):
    """The call is `symbol` itself or carries it as an Itanium source name (`<length><symbol>`)."""
    return call == symbol or re.search(f'(?<![0-9]){len(symbol)}{re.escape(symbol)}', call) is not None


def _observation_commands(target):
    """The pinned description's functional observation commands (F2, F25)."""
    return (target.get('functional_observation') or {}).get('commands', [])


def _bound_events(target):
    """Events of the commands the description's functional observation contract binds (F34)."""
    return {c.get('event') for c in _observation_commands(target)}


def _region_commands(side, region_id):
    """The region's executed `accelerator_calls`, over the aggregate and every trial."""
    rows = [r for r in [side.locations.get(region_id)] if r] + [
        r for t in side.characterization.get('trials', []) for r in t['regions'] if r['id'] == region_id]
    return [c for row in rows for c in row.get('accelerator_calls', []) if _executed(c.get('execution_count'))]


class _OriginSignals:
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

    @staticmethod
    def unbound_commands(side, region_id):
        """F2 (review fix F34): executed commands whose event no functional observation command of
        the side's pinned description names. Their time cannot be placed in any origin."""
        bound = _bound_events(side.estimate['target_description_snapshot'])
        return sorted({c['event'] for c in _region_commands(side, region_id) if c['event'] not in bound})

    def evidence(self, side, region_id):
        found = set()
        bound = _bound_events(side.estimate['target_description_snapshot'])
        for command in _region_commands(side, region_id):
            if command['event'] in bound:
                found.add(('offload_command', command['event'], None))
        calls = side.calls.get(region_id, [])
        for name, rid, sha in self.intrinsics:
            if any(_calls_symbol(c, name) for c in calls):
                found.add(('intrinsic', rid, ('intrinsic', sha)))
        for rid, location, sha in self.operations:
            symbol, path = location.get('symbol'), location.get('path')
            if (symbol and any(_calls_symbol(c, symbol) for c in calls)) or (
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


def _is_call_row(row):
    """A bound or overhead that prices executed calls: uncovered ones, or ones a model covered."""
    return row['model'] == 'unmodeled_calls' or bool((row.get('inputs') or {}).get('covered_calls'))


def _call_part(region, target):
    """F2 (review fix F33): (own seconds, own missing inputs, seconds inside calls, their missing
    inputs) of one estimated region row, or None when no row prices a call.

    Own seconds recompose the region as the estimator does without its call rows (max of the
    resource bounds, domain composition, plus additive overheads); the calls hold the rest. An
    unknown call row leaves the call time unknown and the region's own time known. The call time
    is the region minus its own time, so an unknown own time leaves it unknown too, and its
    missing inputs then name the own-time items as well (final review L1)."""
    calls = [b for b in region['bounds'] + region['overheads'] if _is_call_row(b)]
    if not calls:
        return None
    from swdb import analytic_composition
    bounds = [b for b in region['bounds'] if not _is_call_row(b) and b['model'] != 'domain_composition']
    bounds += analytic_composition.resource_composition(bounds, target)
    overheads = [o for o in region['overheads'] if not _is_call_row(o)]
    own = (None if any(b['seconds'] is None for b in bounds + overheads)
           else max((b['seconds'] for b in bounds), default=0.) + sum(o['seconds'] for o in overheads))
    own_missing = {m for b in region['bounds'] + region['overheads'] if not _is_call_row(b) for m in b['missing']}
    inside = None if region['seconds'] is None or own is None else max(0., region['seconds'] - own)
    inside_missing = {m for b in calls for m in b['missing']} | (own_missing if own is None else set())
    return own, sorted(own_missing), inside, sorted(inside_missing)


def _unmodeled_calls(side, region_id):
    """The region row's `unmodeled_calls`: median seconds inside calls over trials (a trial without
    call rows counts 0 s) with their missing inputs, or None when no trial prices a call."""
    target = side.estimate['target_description_snapshot']
    parts = [_call_part(r, target) if r else None
             for r in (next((x for x in rows if x['id'] == region_id), None) for rows in side.trials())]
    if all(p is None for p in parts):
        return None
    return {'seconds': _median([p[2] if p else 0. for p in parts]),
            'missing': sorted({m for p in parts if p for m in p[3]})}


def _group_seconds(side, labels, origins=ORIGINS, calls_apart=True):
    """{origin: (median seconds or None, [unknown region reasons])} from per-trial sums.

    A region whose label is not one of `origins` is left out (ticket 05's per-origin split).
    F33: a region's seconds inside calls go to `unattributed` (when it is one of `origins`); the
    region's group keeps its own seconds. With `calls_apart` False (the split check, F40) every
    region keeps its full seconds, calls included, under its own label."""
    target = side.estimate['target_description_snapshot']
    sums = {origin: [] for origin in origins}
    unknown = {origin: {} for origin in origins}

    def add(totals, origin, rid, seconds, missing):
        if origin not in totals:
            return
        if seconds is None:
            totals[origin] = None
            unknown[origin].setdefault(rid, set()).update(missing)
        elif totals[origin] is not None:
            totals[origin] += seconds
    for rows in side.trials():
        totals = {origin: 0. for origin in origins}
        for region in rows:
            origin = labels[region['id']]['origin'] if region['id'] in labels else 'unattributed'
            part = _call_part(region, target) if calls_apart else None
            if part is None:
                add(totals, origin, region['id'], region['seconds'], _missing(region))
                continue
            own, own_missing, inside, inside_missing = part
            add(totals, origin, region['id'], own, own_missing)
            add(totals, 'unattributed', region['id'], inside, inside_missing)
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
    """The two floor terms of one counted region, from the description's own rates only (F6).

    The unchanged mechanism models are called exactly as the estimator calls them, so each term
    equals that model's bound in the estimate. A model the description lacks is run with no
    rates: zero work gives 0 s, any work gives an unknown term naming the missing rate. No other
    description's rate and no latency, row, queue or overhead mechanism is read.

    The description's own rates are its `resource_bound` mechanisms plus its
    `resource_floor_mechanisms` (2026-10-12 ET, cpu-description ticket 03, C11): rates the
    estimator never reads, so a term from one is a floor term only, not a bound in the estimate.

    Review F1 (2026-10-12 ET): a floor-only rate also treats `memory_service_scenario` as covering
    non-stream bytes. The services binder strips every other memory model, so without this every
    indirect access left the bandwidth term unknown. As in the estimator, covered non-stream bytes
    are left out of the streamed bytes (the scenario prices them), so the term only gets smaller and
    the floor stays a lower bound.
    """
    from swdb import analytic_models
    models = [m['model'] for m in target['mechanisms']]
    floor_only = target.get('resource_floor_mechanisms') or []
    floor_covering = analytic_models.NONSTREAM_COVERING | {'memory_service_scenario'}
    terms = []
    for model in FLOOR_MODELS:
        own = [m for m in target['mechanisms']
               if m['model'] == model and m.get('accounting', 'resource_bound') == 'resource_bound']
        own = [(m, analytic_models.NONSTREAM_COVERING) for m in own]
        own += [(m, floor_covering) for m in floor_only if m['model'] == model]
        results = [analytic_models.evaluate(region, m, models, target['threads'], covering=covering)
                   for m, covering in own or [({'model': model, 'parameters': {}}, analytic_models.NONSTREAM_COVERING)]]
        seconds = None if any(r['seconds'] is None for r in results) else max(r['seconds'] for r in results)
        terms.append({'model': model, 'in_description': bool(own), 'seconds': seconds,
                      'missing': sorted({m for r in results for m in r['missing']})})
    return terms


def _calls_by_region(calls):
    found = {}
    for call in calls:
        found.setdefault(call.get('region'), []).append(call)
    return found


def _counted_trials(side, store):
    """(per-trial counted regions by ID, per-trial executed calls by region ID), reconciled the way
    the estimator reconciles them: each trial's regions are estimated with that trial's own
    `unmodeled_calls` (review fix F38), a single-run characterization with its aggregate ones."""
    from swdb.analytic_trial_scope import reconcile_trial
    trials = side.characterization.get('trials') or []
    if not trials:
        return ([{r['id']: r for r in side.characterization['regions']}],
                [_calls_by_region(side.characterization.get('unmodeled_calls', []))])
    reconciled = [reconcile_trial(side.characterization, trial, store)[0] for trial in trials]
    return ([{r['id']: r for r in t['regions']} for t in reconciled],
            [_calls_by_region(t.get('unmodeled_calls', [])) for t in reconciled])


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


# --- Ticket 08: catalog bound (F6, F21, F25; review fixes F30-F36) ------------------------------
#
# Site-finder regions come from a saved Extensa campaign summary: one iteration's chosen `regions`
# rows, each with `why.source` (path, full-source revision and lines) and `why.applications`
# (the entries that apply). Their lines name the full-source revision, not either tree
# attributed here (risks C1, C2). F21 (review fix F30): each site-finder region's lines are
# moved into each tree by their offset inside the function the region ID names
# (`<implementation>/<function>:<first>-<last>`): offset from the function's first line in the
# revision tree (`--site-finder-source`), added to the same definition's first line in the tree.
# The moved lines are kept when the function's text is the same in both trees or they stay
# inside the tree's definition. An estimate region joins a site-finder region when one of its
# pieces (home span or inlined piece) overlaps the moved lines; `mixed` when some line of its
# pieces lies outside every joined span. When the lines cannot be moved (no revision tree, or it
# lacks the file or function), the whole function joins, recorded as `join: function` with the
# reason. A site-finder region that cannot be placed at all is listed with its reason and makes
# the bound of every region it could have joined unknown (`site_finder_unplaced`, F31).

COUNT_GAPS = ('address_stream_counts', 'accelerator_calls')   # offload counts only a rewrite produces
UNKNOWN_ENTRY = ('missing_inputs', 'entry_changed', 'entry_unhashed', 'not_in_library')
FLOOR_TIER_REASONS = ('no_catalog_match', 'no_site_finder')   # F36: the only null bounds ranked by floor headroom
SITE_FINDER_REGION = r'^.+/(?P<function>[A-Za-z_]\w*):[0-9]+-[0-9]+$'
RANKING_RULE = {
    'remaining_gain_bound': 'Upper limit, never an expected gain: share x max(0, 1 - catalog bound / estimate), '
                            'share = region seconds / candidate total seconds. Regions with a known catalog bound only; '
                            'largest first. Clamped at 0 (F29): an entry slower than the region\'s estimate offers no '
                            'gain, the same as a region already at its bound. Ties (for example at 0) go by floor '
                            'headroom, largest first and null last, then by region ID.',
    'floor_headroom': 'Regions whose catalog bound is no_catalog_match or no_site_finder: estimate / resource floor, '
                      'largest first. Never ranked against the remaining_gain_bound tier. The floor\'s bandwidth term '
                      'is the streaming_bandwidth model\'s own bound, which leaves out bytes a cache_fit or latency model '
                      'of the description covers, so the floor is a looser but still valid lower limit (F6).',
    'unknown': 'Regions whose ranking value is null, in region-ID order, after every known value: an unknown catalog '
               'bound (its reason, for example needs_rewritten_counts, unknown_catalog_entry, no_baseline_counts or '
               'site_finder_unplaced), or a null remaining gain bound or floor headroom.',
    'comparison': 'One ranking over the candidate regions of the cumulative comparison (original baseline -> '
                  'candidate), whose catalog bounds run on the original baseline\'s counts (F35). The this_iteration '
                  'catalog bounds and floors run on the previous candidate\'s counts; they are informational and never '
                  'ranked (F45).'}


class _SiteFinder:
    """One iteration's site-finder regions from a saved campaign summary, and where each one lies
    in every attributed tree."""

    def __init__(self, store, summary_id, iteration=None, revision_id=None):
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
        self.revision = _Tree(store, revision_id) if revision_id else None
        self.placements = {}
        self.regions = []
        for row in sorted((r for r in chosen['regions'] if isinstance(r.get('why'), dict)), key=lambda r: r['id']):
            match = re.match(SITE_FINDER_REGION, row['id'])
            source = row['why'].get('source') or {}
            self.regions.append({
                'id': row['id'], 'function': match['function'] if match else None, 'path': source.get('path'),
                'revision': source.get('revision'), 'lines': source.get('lines'),
                'applications': sorted(({'entry': a['entry'], 'kind': a.get('kind'), 'content_sha256': a.get('content_sha256')}
                                        for a in row['why'].get('applications', [])), key=lambda a: a['entry'])})

    def place(self, side):
        """[(site-finder region, placement)] in one tree, computed once per source record."""
        key = side.source['id']
        if key not in self.placements:
            self.placements[key] = {sf['id']: _placement(sf, side, self.revision) for sf in self.regions}
        return [(sf, self.placements[key][sf['id']]) for sf in self.regions]

    def block(self):
        block = {'campaign_summary': _pin(self.summary), 'iteration': self.iteration, 'query_sha256': self.query_sha256,
                 'kernel': self.kernel, 'target': self.target,
                 'regions': [{k: r[k] for k in ('id', 'function', 'path', 'revision', 'lines')}
                             | {'entries': [a['entry'] for a in r['applications']],
                                'placements': [{'source': source, **self.placements[source][r['id']]}
                                               for source in sorted(self.placements)]}
                             for r in self.regions]}
        if self.revision is not None:
            block['revision_source'] = _source_pin(self.revision.source)
        return block


def _tree_file(side, path):
    """The one file of the tree that `path` names (`_Side.relative`: the file itself, or the one file
    `path` ends with), else the one file that ends with `path` (a site-finder path relative to a
    deeper root)."""
    if not path:
        return None
    rel = _Side.relative(side, path)
    if rel is not None:
        return rel
    matches = [f for f in side.files if f.endswith('/' + path)]
    return matches[0] if len(matches) == 1 else None


def _moved_lines(sf, rel, definitions, lines, revision):
    """(the site-finder lines moved into the tree by function-relative offset, None) or (None, reason)."""
    if revision is None:
        return None, 'no_revision_tree'
    if revision.source.get('revision') != sf['revision']:
        return None, 'revision_mismatch'
    rev_rel = _tree_file(revision, sf['path'])
    if rev_rel is None:
        return None, 'file_not_in_revision_tree'
    span = sf['lines']
    if not (isinstance(span, list) and len(span) == 2 and all(isinstance(x, int) for x in span) and 1 <= span[0] <= span[1]):
        return None, 'no_site_finder_lines'
    rev_lines = revision.text(rev_rel)
    rev_definitions = cpp_lexical.definition_spans('\n'.join(rev_lines), sf['function'])
    inside = [i for i, d in enumerate(rev_definitions) if d[0] <= span[0] and span[1] <= d[1]]
    if not inside:
        return None, 'lines_outside_function_in_revision'
    if len(rev_definitions) != len(definitions):
        return None, 'definitions_differ'
    i = max(inside, key=lambda k: rev_definitions[k][0])   # the innermost definition holding the lines
    source, target = rev_definitions[i], definitions[i]
    moved = [target[0] + span[0] - source[0], target[0] + span[1] - source[0]]
    same_text = rev_lines[source[0] - 1:source[1]] == lines[target[0] - 1:target[1]]
    if not same_text and not (target[0] <= moved[0] and moved[1] <= target[1]):
        return None, 'moved_lines_outside_function'
    return moved, None


def _placement(sf, side, revision):
    """Where one site-finder region lies in one tree: `{join, path, lines, reason}`.

    `join` is `lines` (moved lines), `function` (the whole definition; `reason` says why the lines
    could not be moved) or null (unplaced; `reason` says why)."""
    unplaced = {'join': None, 'path': None, 'lines': None}
    if sf['function'] is None:
        return {**unplaced, 'reason': 'unrecognized_region_id'}
    rel = _tree_file(side, sf['path'])
    if rel is None:
        return {**unplaced, 'reason': 'file_not_in_tree'}
    lines = side.text(rel)
    definitions = cpp_lexical.definition_spans('\n'.join(lines), sf['function'])
    if not definitions:
        return {**unplaced, 'path': rel, 'reason': 'function_not_in_tree'}
    moved, reason = _moved_lines(sf, rel, definitions, lines, revision)
    if moved is not None:
        return {'join': 'lines', 'path': rel, 'lines': moved, 'reason': None}
    if len(definitions) != 1:
        return {**unplaced, 'path': rel, 'reason': 'ambiguous_function'}
    return {'join': 'function', 'path': rel, 'lines': list(definitions[0]), 'reason': reason}


def _pieces(row):
    return ([(row['path'], row['lines'])] if row['path'] and row['lines'] else []) + [
        (p['path'], p['lines']) for p in row['inlined']]


def _joins(side, labels, finder):
    """({region ID: [(site-finder region, placement)]}, {region ID: [unplaced site-finder region IDs]},
    {region ID: mixed}) for one side (F21, F30, F31)."""
    placed = finder.place(side)
    joins, unplaced, mixed = {}, {}, {}
    for row in labels.values():
        pieces = _pieces(row)
        for sf, where in placed:
            if where['join'] is None:
                if any(path is not None and (where['path'] is None or path == where['path']) for path, _ in pieces):
                    unplaced.setdefault(row['region'], []).append(sf['id'])
            elif any(path == where['path'] and _overlaps(where['lines'], lines) for path, lines in pieces):
                joins.setdefault(row['region'], []).append((sf, where))
        spans = [(where['path'], where['lines']) for _, where in joins.get(row['region'], [])]
        mixed[row['region']] = bool(spans) and any(
            not any(path == p and s[0] <= line <= s[1] for p, s in spans)
            for path, lines in pieces for line in range(lines[0], lines[1] + 1))
    return joins, unplaced, mixed


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
        the offload mechanisms (`selector.domain: offload`, or `selector.event_ids` naming one).
        F28: operation families are never mapped onto each other (an `dx100.mmio.v1.*` entry
        reaches no `dx100.functional.v1.*` command). F32: an application without the
        `content_sha256` the site finder saw is `entry_unhashed`, never evaluated."""
        entry = self.library.get(application['entry']) if self.library else None
        if entry is None:
            return [], 'not_in_library'
        if not application.get('content_sha256'):
            return [], 'entry_unhashed'
        if artifacts.digest(entry) != application['content_sha256']:
            return [], 'entry_changed'
        operations = self._hardware_operations(application['entry'])
        events = {c['event'] for c in _observation_commands(target)
                  if c.get('hardware_operations') and set(c['hardware_operations']) <= operations}
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


def _entry_bound(region_id, counts, mechanisms, side, target):
    """Median over trials of the entry's composed seconds on the region's baseline counts (F35; absent = 0 s).
    `counts` is `_counted_trials(side)`: each trial's regions and that trial's own calls (F38)."""
    trials, calls = counts
    per_trial = [_entry_trial(t[region_id], c.get(region_id, []), mechanisms, side, target) if region_id in t else None
                 for t, c in zip(trials, calls)]
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


def _catalog_reason(evaluated, unplaced):
    """The null bound's reason (F6, F31, F35): an unknown before a missing match."""
    reasons = {e['reason'] for e in evaluated}
    if 'needs_rewritten_counts' in reasons:
        return 'needs_rewritten_counts'
    if reasons & set(UNKNOWN_ENTRY):
        return 'unknown_catalog_entry'
    if 'no_baseline_counts' in reasons:
        return 'no_baseline_counts'
    return 'site_finder_unplaced' if unplaced else 'no_catalog_match'


def _add_catalog(side, labels, bounds, counts, target, baseline=None):
    """Annotate each region row of one side with its catalog bound and catalog headroom.

    F35 (spec F6): an entry runs on the region's baseline counts. A baseline row
    uses its own; a candidate row uses those of its `matched_region` on the baseline side
    (`baseline` = (that side, its counts)); a candidate row with no matched region has none, so
    an entry with mechanisms gives `no_baseline_counts`."""
    if bounds is None or bounds.finder is None:
        for row in labels.values():
            row['catalog_bound'] = {'seconds': None, 'entry': None, 'reason': 'no_site_finder', 'mixed': False,
                                    'site_finder_regions': [], 'joins': [], 'unplaced_site_finder_regions': [],
                                    'entries': [], 'missing': []}
            row['headroom'].append(_headroom('catalog_bound', row['seconds'], None, 'no_site_finder'))
        return
    joins, unplaced, mixed = _joins(side, labels, bounds.finder)
    for row in labels.values():
        joined = joins.get(row['region'], [])
        source_side, source_counts = (side, counts) if baseline is None else baseline
        region_id = row['region'] if baseline is None else row['matched_region']
        entries = {}
        for sf, _ in joined:
            for application in sf['applications']:
                entries.setdefault(application['entry'], (application, []))[1].append(sf['id'])
        evaluated = []
        for entry_id in sorted(entries):
            application, regions = entries[entry_id]
            mechanisms, reason = bounds.mechanisms(application, target)
            if mechanisms and region_id is None:
                result = {'seconds': None, 'reason': 'no_baseline_counts', 'mechanisms': [], 'missing': []}
            elif mechanisms:
                result = _entry_bound(region_id, source_counts, mechanisms, source_side, target)
            else:
                result = {'seconds': None, 'reason': reason, 'mechanisms': [], 'missing': []}
            evaluated.append({'entry': entry_id, 'kind': application.get('kind'),
                              'content_sha256': application.get('content_sha256'),
                              'site_finder_regions': sorted(set(regions)), **result})
        known = [e for e in evaluated if e['seconds'] is not None]
        best = min(known, key=lambda e: (e['seconds'], e['entry'])) if known else None
        reason = None if best else _catalog_reason(evaluated, unplaced.get(row['region']))
        row['catalog_bound'] = {'seconds': best['seconds'] if best else None, 'entry': best['entry'] if best else None,
                                'reason': reason, 'mixed': mixed[row['region']],
                                'site_finder_regions': sorted({sf['id'] for sf, _ in joined}),
                                'joins': [{'site_finder_region': sf['id'], 'join': where['join'], 'path': where['path'],
                                           'lines': where['lines'], 'reason': where['reason']}
                                          for sf, where in sorted(joined, key=lambda j: j[0]['id'])],
                                'unplaced_site_finder_regions': sorted(unplaced.get(row['region'], [])),
                                'entries': evaluated,
                                'missing': sorted({m for e in evaluated for m in e['missing']})}
        row['headroom'].append(_headroom('catalog_bound', row['seconds'], row['catalog_bound']['seconds'], reason))


def _add_limits(side, labels, store, bounds=None, baseline=None):
    """Annotate each region row of one side with its resource floor, catalog bound and both
    headrooms; returns the side's per-trial counts, which the other side's rows read (F35)."""
    counts = _counted_trials(side, store)
    target = side.estimate['target_description_snapshot']
    _require(artifacts.digest(target) == side.estimate['target_description_sha256'],
             f'{side.name} estimate target description snapshot differs from the hash it pins')
    for row in labels.values():
        floor = _resource_floor(row['region'], counts[0], target)
        row['resource_floor'] = floor
        row['headroom'] = [_headroom('resource_floor', row['seconds'], floor['seconds'])]
    _add_catalog(side, labels, bounds, counts, target, baseline)
    return counts


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

    1. `remaining_gain_bound`: regions with a known catalog bound, largest first; ties (for
       example at the 0 clamp, F29) by floor headroom, largest first and null last.
    2. `floor_headroom`: regions whose bound is `no_catalog_match` or `no_site_finder`
       (floor-only), by floor headroom, largest first.
    3. `unknown`: every null value, in region-ID order: an unknown catalog bound (limit
       `catalog_bound`, its reason, F36), a known one whose remaining gain bound is null, or a
       floor-only region with a null floor headroom (limit `resource_floor`).
    Remaining ties go by region ID; positions are 1-based over the whole list.
    """
    def limit(row, name):
        return next(h for h in row['headroom'] if h['limit'] == name)
    def tie(row):   # F29: equal remaining gain bounds (for example 0) go by floor headroom, null last
        value = limit(row, 'resource_floor')['value']
        return (value is None, -(value or 0.))
    gains, floors, unknown = [], [], []
    for row in labels.values():
        bound = row['catalog_bound']
        if bound['seconds'] is not None:
            value, reason = _remaining_gain_bound(row['seconds'], bound['seconds'], total)
            (gains if value is not None else unknown).append((row, 'catalog_bound', value, reason))
        elif bound['reason'] not in FLOOR_TIER_REASONS:   # F36: an unknown bound is never floor-only
            unknown.append((row, 'catalog_bound', None, bound['reason']))
        else:
            floor = limit(row, 'resource_floor')
            (floors if floor['value'] is not None else unknown).append((row, 'resource_floor', floor['value'], floor['reason']))
    entries = ([('remaining_gain_bound', *e) for e in sorted(gains, key=lambda e: (-e[2], *tie(e[0]), e[0]['region']))]
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


def _pin_problems(record, ctx, field, pin, kind=None, what='record'):
    """A problem when the record `pin` names is missing or no longer has the pinned content hash."""
    from swdb.problems import Problem
    current = ctx.store.get(pin['id'], kind) if kind else ctx.store.get(pin['id'])
    if current is None or artifacts.digest(current) != pin['sha256']:
        yield Problem(record.rel, field, f'pinned {what} {pin["id"]!r} is missing or changed')


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
        yield from _pin_problems(record, ctx, field, data[field])
    # Ticket 05: a saved intrinsic that labeled a region must be unchanged. Library operations
    # live outside the records folder (`--library`), so their pins are kept for replay only.
    for pin in data.get('catalog', []):
        if pin['kind'] == 'intrinsic':
            yield from _pin_problems(record, ctx, 'catalog', pin, 'intrinsic', 'intrinsic')
    yield from _floor_problems(record)
    finder = data.get('site_finder')
    if finder is not None:   # ticket 08: the site-finder regions that gave catalog bounds are unchanged
        yield from _pin_problems(record, ctx, 'site_finder', finder['campaign_summary'], 'campaign_summary', 'campaign summary')
        if finder.get('revision_source') is not None:   # review fix F30: the revision tree that moved the lines
            yield from _pin_problems(record, ctx, 'site_finder.revision_source', finder['revision_source'],
                                     what='revision source')
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
        yield from _pin_problems(record, ctx, f'split_check.profiles.{side}', pin, 'region_profile', 'region profile')
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
        yield from _pin_problems(record, ctx, field, pin)
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
    'id': 'swdb.split_check.v2',
    'max_abs_share_gap': 0.1,
    'tolerance': 1e-9,
    'statement': 'Passed when, for every group (untouched, agent_rewritten, unattributed) on both sides, '
                 '|measured share - estimated share| <= 0.1 (10 percentage points, compared with a 1e-9 float '
                 'tolerance). Otherwise, or when a share is unknown, split_unverified. Fixed before timing (F19).',
    'estimated_share': "group seconds / that estimate's total seconds, where each estimated region keeps its full "
                       "seconds, time inside its calls included, under its own group label (F40). Measured "
                       "exclusive time holds the scope's uninstrumented callees, so the report's F33 move of call "
                       "time to unattributed is not applied here; the report's groups keep it",
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


def _seed(workload):
    """The input generator's seed in a workload definition (or a profile's copy of it), or None."""
    return (((workload or {}).get('generator') or {}).get('parameters') or {}).get('seed')


def _check_identity(store, rid, side, data):
    """F44 (final review M3, F18): the profile ran on the machine that counted its estimate, timed
    exactly the BFS sources the characterization counted, and used the counted input's generator seed."""
    name, characterization, context = side.name, side.characterization, data.get('context') or {}
    counted_on = (characterization.get('host') or {}).get('machine')
    _require(data.get('machine') == counted_on,
             f'{name} profile {rid!r} ran on machine {data.get("machine")!r}, not {counted_on!r} where its estimate '
             'was counted; refusing to compare')
    trials = characterization.get('trials') or []
    _require(trials, f'{name} estimate\'s characterization records no counted sources (a single-run count); '
                     'refusing to compare')
    counted = sorted({source for trial in trials for source in trial['sources']})
    timed = sorted(set(context.get('sources') or []))
    _require(timed == counted, f'{name} profile {rid!r} timed sources {timed}, not the counted sources {counted}; '
                               'refusing to compare')
    expected = _seed((store.get(characterization['input']) or {}).get('definition'))
    found = _seed(context.get('workload'))
    _require(found == expected, f'{name} profile {rid!r} timed input seed {found!r}, not the counted input\'s seed '
                                f'{expected!r}; refusing to compare')


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
        _check_identity(store, rid, side, data)
        # F43 (final review M2): estimate records carry only a date (the envelope's `created`), so
        # no full-timestamp order exists; the profile must be dated strictly after every estimate.
        latest = max(str(e['created']) for e in estimates)
        _require(str(data['created']) > latest,
                 f'{name} profile {rid!r} is dated {data["created"]}, not after every estimate ({latest}): '
                 'estimates carry only a date, so the split check is prospective (LR-02) only for a profile '
                 'dated a later day; refusing to compare')
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


def _split_shares(side, labels):
    """F40 (final review H1): {origin: estimated share} for the split check. Every region keeps its
    full seconds, calls included, under its own group, as a measured scope's exclusive time does."""
    seconds = _group_seconds(side, _grouped(labels), calls_apart=False)
    return {origin: _ratio(seconds[origin][0], side.estimate['seconds']) for origin in ORIGINS}


def _split_check(sides, profiles, sites, labels):
    """F19: the split_check block; `sides` and `profiles` are in baseline, candidate order."""
    regions, measured, gaps, reasons = [], [], [], []
    for side, profile in zip(sides, profiles):
        estimated = _split_shares(side, labels[side.name])
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
            expected = estimated[origin]
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


def _last_changed(side, chain, known=None):
    """{region ID: iteration that last changed it}. `chain[k]` is iteration k's tree; `side` is
    iteration len(chain). A region last changed in iteration k + 1 overlaps a site of the diff
    from chain[k] but none from chain[k + 1]; one that overlaps none is 0, one without a source
    location is None. Uses the labeling rules of `_label`, so it follows whatever they are.

    Review fix F39: labels here never read the catalog, so a call seen only in an earlier
    diff pins nothing in the report. `known[k]` are labels the caller already made for the diff
    chain[k] -> side (any catalog origin only changes the name of a touched origin), so no diff is
    labeled twice."""
    current = _as(side, 'candidate')
    found, pending = {}, [r['id'] for r in side.estimate['regions']]
    for k in reversed(range(len(chain))):
        labels = (known or {}).get(k) or _label(current, _sites(chain[k], current))
        for rid in list(pending):
            row = labels[rid]
            if row['reason'] == 'no_source_location':
                found[rid] = None
                pending.remove(rid)
            elif row['sites']:
                found[rid] = k + 1
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
    _require_comparable(previous.estimate, candidate.estimate, 'previous and candidate')
    earlier = [_Tree(store, rid) for rid in args.earlier_source]
    chain = [baseline, *earlier, previous]
    before = _as(previous, 'baseline')
    sites, rows = _split(before, candidate, catalog)
    changed = {'previous': _last_changed(previous, chain[:-1]),
               'candidate': _last_changed(candidate, chain, {0: labels['candidate'], len(chain) - 1: rows['candidate']})}
    for row in labels['baseline'].values():
        row['last_changed_iteration'] = 0
    for row in list(labels['candidate'].values()) + list(rows['candidate'].values()):
        row['last_changed_iteration'] = changed['candidate'][row['region']]
    for row in rows['baseline'].values():
        row['last_changed_iteration'] = changed['previous'][row['region']]
    counts = _add_limits(before, rows['baseline'], store, bounds)
    _add_limits(candidate, rows['candidate'], store, bounds, (before, counts))
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
    _require_comparable(baseline.estimate, candidate.estimate, 'baseline and candidate')
    _require((args.baseline_profile is None) == (args.candidate_profile is None),
             '--baseline-profile and --candidate-profile go together')
    profiles = [_Profile(store, rid, side, [baseline.estimate, candidate.estimate])
                for rid, side in ((args.baseline_profile, baseline), (args.candidate_profile, candidate))] if args.baseline_profile else []
    from swdb.library import default_root
    catalog = _OriginSignals(store, Path(args.library) if args.library else default_root(args.records))
    finder = (_SiteFinder(store, args.site_finder, args.site_finder_iteration, args.site_finder_source)
              if args.site_finder else None)
    _require(finder is not None or args.site_finder_iteration is None, '--site-finder-iteration needs --site-finder')
    _require(finder is not None or args.site_finder_source is None, '--site-finder-source needs --site-finder')
    bounds = _Bounds(finder, catalog.library)
    sites, labels = _split(baseline, candidate, catalog)
    counts = _add_limits(baseline, labels['baseline'], store, bounds)
    _add_limits(candidate, labels['candidate'], store, bounds, (baseline, counts))
    groups = _groups(baseline, candidate, labels)
    this_iteration, previous_inputs = _iteration(store, args, baseline, candidate, labels, catalog, bounds)
    inputs = [baseline.estimate, candidate.estimate, baseline.source, candidate.source] + previous_inputs + (
        [finder.summary] if finder else []) + ([finder.revision.source] if finder and finder.revision else []) + [
        p.data for p in profiles]
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
        record['split_check'] = _split_check((baseline, candidate), profiles, sites, labels)
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

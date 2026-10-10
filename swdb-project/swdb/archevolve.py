"""New-operation gem5 provenance boundary (ADR 0013). Updated: 2026-10-10 ET
(code review of tickets 06/12: every Extensa campaign record outside the promotable
candidate lineage, nested `{id: ...}` reference pins, generic simulator markers and
simulated target-description facts are refused); 2026-10-06 ET.

Historical validation never calls this guard. Source/configuration facts marked
code_reading can cite pinned simulator source; execution/calibration cannot.
"""
from contextlib import contextmanager

from swdb import workflow
from swdb.cli import Failure
from swdb.store import Store

EVIDENCE_COMMANDS = {'fill-target-parameters', 'characterize', 'estimate', 'freeze-protocol', 'dx100-build', 'dx100-compile',
    'dx100-execute', 'dx100-profile', 'evaluate', 'evaluate-functional', 'evaluate-pair', 'compare', 'compare-evaluations',
    'aggregate-evaluations', 'bfs-profile', 'bfs-hotspots', 'profile-package', 'profile-strategies',
    'strategy-regions', 'bfs-coverage', 'handoff-message', 'submit', 'repair', 'profile', 'annotate',
    'claim', 'add', 'annotate-score', 'certify', 'synthesize', 'recompute-cachegrind', 'agreement-freeze', 'agreement-report'}


def register_cli(commands):
    for name, parser in commands.choices.items():
        if name not in EVIDENCE_COMMANDS:
            continue
        existing = {option for action in parser._actions for option in action.option_strings}
        if '--mode' not in existing:
            parser.add_argument('--mode', choices=['archevolve', 'extensa'], default=None,
                help='evaluation policy (default ArchEvolve, or inherited Extensa campaign)')
        if '--campaign' not in existing:
            parser.add_argument('--campaign', help='explicit Extensa mode requires its campaign ID')


@contextmanager
def command_mode(args):
    previous = dict(workflow.CREATION_TAGS)
    mode = getattr(args, 'mode', None)
    try:
        if mode == 'archevolve':
            workflow.CREATION_TAGS.clear()
        elif mode == 'extensa':
            import re
            from swdb.schemas import campaign_id_pattern
            campaign = getattr(args, 'campaign', None) or previous.get('campaign')
            if not isinstance(campaign, str) or not re.fullmatch(campaign_id_pattern(), campaign):
                raise Failure('explicit Extensa mode requires a valid --campaign ID')
            workflow.CREATION_TAGS.clear()
            workflow.CREATION_TAGS.update(mode='extensa', campaign=campaign)
        yield
    finally:
        workflow.CREATION_TAGS.clear()
        workflow.CREATION_TAGS.update(previous)


#: Generic simulator marker (2026-10-09 ET code review): matched case-insensitively in
#: identity fields only, never in embedded source text, and never inside a record ID
#: (a referenced record is walked instead). No accelerator-specific names.
SIMULATOR_MARKER = 'gem5'
IDENTITY_FIELDS = ('backend', 'simulator', 'model', 'target', 'hardware_target')


def _simulator_named(store, value):
    """The identity text naming the simulator, or None (a string, or a dict's string values)."""
    texts = [value] if isinstance(value, str) else [v for v in value.values() if isinstance(v, str)] if isinstance(value, dict) else []
    return next((text for text in texts if SIMULATOR_MARKER in text.lower() and store.get(text) is None), None)


def _simulated_facts(value, path=''):
    """Paths of value/basis facts with basis `simulated` inside one target description."""
    if isinstance(value, dict):
        if value.get('basis') == 'simulated' and 'value' in value:
            yield path or '.'
        for key, child in value.items():
            yield from _simulated_facts(child, f'{path}.{key}' if path else str(key))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from _simulated_facts(child, f'{path}[{i}]')


def require_team_safe(store, *values, command):
    if workflow.CREATION_TAGS.get('mode') == 'extensa':
        return
    from swdb.extensa_boundary import OWNED_KINDS
    visited, objects, trail = set(), set(), []
    # 2026-10-10 ET: the whole lineage is walked and every offending record is named
    # (first reason per record), so a refused relay also names what it pins.
    refused = {}

    def refuse(owner, reason):
        refused.setdefault(owner, (reason, list(trail)))

    def walk(value, owner='request', source_read=False, root=False):
        if isinstance(value, str):
            record = store.get(value)
            if record is not None and value not in visited:
                # D18 permits source configuration reading from this pinned model;
                # it never admits an execution record labeled as source reading.
                if source_read and record['kind'] in {'hardware_target', 'implementation', 'application'}:
                    return
                visited.add(value)
                trail.append(value)
                try:
                    walk(record, value, root=True)
                finally:
                    trail.pop()
            return
        if not isinstance(value, (dict, list)) or id(value) in objects:
            return
        objects.add(id(value))
        if isinstance(value, list):
            for child in value:
                walk(child, owner, source_read=source_read)
            return
        rid = value.get('id')
        if isinstance(rid, str) and (root or store.get(rid) is not None):
            owner = rid
        if not root and isinstance(rid, str):
            # A nested `{id: ...}` pin is a reference like a bare ID string (the
            # frozen dependency closure follows it too); only a record's own ID is not.
            walk(rid, owner, source_read=source_read)
        kind = value.get('kind')
        if value.get('mode') == 'extensa' and isinstance(kind, str) and kind not in OWNED_KINDS:
            # Only the promotable candidate lineage may appear; extensa_boundary
            # still requires its promotion and team re-evaluation (ADR 0009).
            refuse(owner, f'Extensa campaign {kind} records never enter team results or protocols')
        if value.get('estimator_variant') == 'research':
            refuse(owner, 'research estimator variants never enter team protocols')
        for field in IDENTITY_FIELDS:
            named = _simulator_named(store, value.get(field))
            if named is not None:
                refuse(owner, f'{SIMULATOR_MARKER} {field} {named!r}')
        if kind == 'target_description':
            simulated = next(_simulated_facts({k: v for k, v in value.items() if k != 'parameter_estimation'}), None)
            if simulated is not None:
                refuse(owner, f'simulated target-description fact {simulated}: simulator-derived numbers never calibrate a team estimator')
        source = value.get('source')
        if isinstance(source, str) and SIMULATOR_MARKER in source.lower() and value.get('basis') not in {None, 'code_reading'}:
            refuse(owner, f'{SIMULATOR_MARKER} numeric source {source!r}')
        promotion = kind == 'review' and isinstance(value.get('origin'), dict) and value['origin'].get('mode') == 'extensa'
        for key, child in value.items():
            if key in {'id', 'kind'}:
                continue
            if promotion and key == 'evidence':
                # Yan-Ru's promotion review cites the campaign evidence it read (ADR 0009);
                # the team re-evaluation, not that evidence, enters team results.
                continue
            if key == 'provenance':
                # Source-code provenance describes inspection, not a simulation.
                for row in child if isinstance(child, list) else []:
                    if isinstance(row, dict):
                        reference = store.get(row.get('id'))
                        if row.get('kind') != 'source_code' or (reference and reference['kind'] not in {'hardware_target', 'implementation', 'application'}):
                            walk(row.get('id'), owner)
                            walk(row, owner)
                continue
            if key == 'calibration_sources' and isinstance(child, list):
                for source_id in child:
                    if not isinstance(source_id, str) or store.get(source_id) is None:
                        refuse(owner, f'unverifiable calibration dependency {source_id!r}')
            walk(child, owner, source_read=key == 'source_evidence' or (key == 'source' and value.get('basis') == 'code_reading'))

    for value in values:
        walk(value, root=True)
    if refused:
        rows = [f'record {owner!r}: {reason}; dependency records: {chain}' for owner, (reason, chain) in refused.items()]
        more = f'; and {len(rows) - 10} more refused records' if len(rows) > 10 else ''
        raise Failure(f'ADR 0013: ArchEvolve {command} refuses ' + '; also refuses '.join(rows[:10]) + more)


def guard_cli(args):
    if args.command not in EVIDENCE_COMMANDS or workflow.CREATION_TAGS.get('mode') == 'extensa':
        return
    if not args.records.is_dir():
        return  # Dispatch retains the established missing-records usage diagnostic.
    store = Store(args.records)
    values = [value for name, value in vars(args).items() if name not in {'mode', 'campaign', 'command', 'records', 'db', 'format'}]
    file = getattr(args, 'file', None)
    if file is not None:
        try:
            values.append(workflow.message_from_text(file.read_text()))
        except OSError:
            pass  # The command reports its own malformed/missing request.
    require_team_safe(store, *values, command=args.command)
    if args.command.startswith('dx100-'):
        raise Failure(f'ADR 0013: ArchEvolve {args.command} refuses record {getattr(args, "file", "request")!s}: gem5 backend command')

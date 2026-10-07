"""New-operation gem5 provenance boundary (ADR 0013). Updated: 2026-10-06 ET.

Historical validation never calls this guard. Source/configuration facts marked
code_reading can cite pinned simulator source; execution/calibration cannot.
"""
from contextlib import contextmanager

from swdb import workflow
from swdb.cli import Failure
from swdb.store import Store

EVIDENCE_COMMANDS = {'characterize', 'estimate', 'freeze-protocol', 'dx100-build', 'dx100-compile',
    'dx100-execute', 'dx100-profile', 'evaluate', 'evaluate-functional', 'evaluate-pair', 'compare', 'compare-evaluations',
    'aggregate-evaluations', 'bfs-profile', 'bfs-hotspots', 'profile-package', 'profile-strategies',
    'strategy-regions', 'bfs-coverage', 'handoff-message', 'submit', 'repair', 'profile', 'annotate',
    'claim', 'add', 'annotate-score', 'certify', 'synthesize', 'recompute-cachegrind'}


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


def require_team_safe(store, *values, command):
    if workflow.CREATION_TAGS.get('mode') == 'extensa':
        return
    visited, objects, trail = set(), set(), []

    def refuse(owner, reason):
        raise Failure(f'ADR 0013: ArchEvolve {command} refuses record {owner!r}: {reason}; dependency records: {trail}')

    def walk(value, owner='request', source_read=False):
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
                    walk(record, value)
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
        owner = value.get('id', owner) if isinstance(value.get('id', owner), str) else owner
        if value.get('mode') == 'extensa' and value.get('kind') in {'protocol', 'target_description', 'estimate', 'workload_characterization'}:
            refuse(owner, 'Extensa research evidence never enters team protocols')
        if value.get('estimator_variant') == 'research':
            refuse(owner, 'research estimator variants never enter team protocols')
        backend = value.get('backend')
        backend = backend.get('id') if isinstance(backend, dict) else backend
        if isinstance(backend, str) and 'gem5' in backend.lower():
            refuse(owner, f'gem5 backend {backend}')
        simulator = value.get('simulator')
        if isinstance(simulator, str) and 'gem5' in simulator.lower():
            refuse(owner, 'gem5 execution or simulator artifact')
        source = value.get('source')
        if isinstance(source, str) and 'gem5' in source.lower() and value.get('basis') not in {None, 'code_reading'}:
            refuse(owner, f'gem5 numeric source {source!r}')
        for key, child in value.items():
            if key in {'id', 'kind'}:
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
                for rid in child:
                    if not isinstance(rid, str) or store.get(rid) is None:
                        refuse(owner, f'unverifiable calibration dependency {rid!r}')
            walk(child, owner, source_read=key == 'source_evidence' or (key == 'source' and value.get('basis') == 'code_reading'))

    for value in values:
        walk(value)


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

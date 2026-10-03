"""Immutable raw-output custody and conservative pruning. Updated: 2026-10-03 ET.

Listings are exact, hashed approvals. A path's name alone never overrides evidence
roles recorded by a workload, build, witness, correctness check, or region report.
"""
import datetime
import fcntl
import json
from pathlib import Path
import socket
import uuid
from contextlib import contextmanager

from swdb import artifacts, paths, workflow
from swdb.cli import Failure, _require_valid

RUN_ROOTS = ('/data1/yanruj/EvolveSWDB_runs', '/data/yanruj/EvolveSWDB_runs')
INPUT_KINDS = {'workload', 'source_snapshot', 'protocol'}
PROTECTED_KEYS = {'correctness', 'sealed_roi', 'post_roi_trace', 'verification_runtime',
                  'verification_driver', 'verification_parser', 'host_memory_observer',
                  'region_output', 'raw_report', 'companion_acceptance', 'companion_cases',
                  'parent_gather_race', 'frontier_sizes', 'coverage_report'}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@contextmanager
def _custody_lock(records):
    """Claim/prune serialization uses a different lock from the record writer."""
    with (Path(records) / '.retention.lock').open('a') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _strings(value, prefix=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, prefix + (key,))
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item, prefix)
    elif isinstance(value, str) and value.startswith('/'):
        yield value, prefix


def _under(name, path):
    return name == str(path) or str(path).startswith(name.rstrip('/') + '/')


def references(store, path):
    """Return every path reference, including references to containing folders."""
    result = []
    for record in store.records:
        if record.kind in {'retention', 'team_claim'}:
            continue
        for name, fields in _strings(record.data):
            if _under(name, path):
                result.append({'record': record.id, 'kind': record.kind, 'field': '.'.join(fields),
                               'path': name})
    return result


def classify(path, refs):
    # Source/build/model inputs outrank output names, including ancestor paths.
    if any(ref['kind'] in INPUT_KINDS or ref['field'].startswith('build.')
           or ref['field'].startswith('context.verification_runtime')
           or (ref['kind'] == 'evaluation' and ref['field'].startswith('build'))
           or 'build_receipt' in ref['field'] or 'checkpoint_manifest' in ref['field']
           for ref in refs):
        return 'input'
    # A raw_artifacts directory identifies storage, not a claim that every child
    # is compact; exact correctness/witness paths always protect their children.
    if any(any(field in PROTECTED_KEYS for field in ref['field'].split('.'))
           and 'debug_trace' not in ref['field'].split('.') for ref in refs):
        return 'compact'
    if path.name in {'roi-debug.trace.gz', 'debug.trace.gz'} or any(
            component.startswith('cpt.') for component in path.parts):
        return 'bulky'
    return 'compact'


def listing(store, roots):
    roots = [Path(root).absolute() for root in roots]
    rows = []
    seen = set()
    for root in roots:
        if root.is_symlink() or '..' in root.parts or not root.is_dir():
            raise Failure(f'run root must be an existing absolute directory: {root}')
        for path in sorted(root.rglob('*')):
            if path.is_symlink():
                raise Failure(f'prune listing refuses symlink: {path}')
            if not path.is_file():
                continue
            if path in seen:
                continue
            seen.add(path)
            refs = references(store, path)
            category = classify(path, refs)
            owners = sorted({ref['record'] for ref in refs if ref['kind'] == 'evaluation'})
            rows.append({'path': str(path), 'bytes': path.stat().st_size, 'class': category,
                         'references': refs, 'evaluations': owners,
                         'sha256': artifacts.file_hash(path) if category == 'bulky' else None,
                         'proposed': category == 'bulky' and len(owners) == 1 and team_state(store, owners[0]) != 'claimed'})
    return {'format': 'swdb.prune-listing.v1', 'created_at': _now(),
            'host': socket.gethostname().split('.')[0], 'roots': list(map(str, roots)), 'files': rows}


def retained(store, reference, evaluation_id=None):
    """Only a matching path AND digest AND evaluation may excuse absent bytes."""
    if store is None or not callable(getattr(store, 'of_kind', None)) or not isinstance(reference, dict):
        return None
    matches = []
    for record in store.of_kind('retention'):
        data = record.data
        if data.get('event') != 'prune' or (evaluation_id and data.get('evaluation') != evaluation_id):
            continue
        for item in data.get('deleted', []):
            if item.get('path') == reference.get('path') and item.get('sha256') == reference.get('sha256'):
                matches.append({'state': 'pruned, sha256 retained', 'retention': record.id, **item})
    return matches[-1] if matches else None


def retained_directory(store, artifact):
    """Reconcile each original directory member; pruning cannot excuse new files."""
    root = Path(artifact['path'])
    if not root.is_dir() or root.is_symlink() or not isinstance(artifact.get('files'), list):
        return None
    expected = artifact['files']
    if artifacts.digest(expected) != artifact.get('sha256'):
        return None
    actual = artifacts.manifest(root)
    current = {item['path']: item for item in actual}
    removed = []
    for item in expected:
        if item['path'] in current:
            if current.pop(item['path']) != item:
                return None
        else:
            receipt = retained(store, {'path': str(root / item['path']), 'sha256': item['sha256']})
            if not receipt or receipt['bytes'] != item['bytes']:
                return None
            removed.append(receipt)
    if current or not removed:
        return None
    return {'state': 'pruned, sha256 retained', 'artifacts': removed}


def _closure(store, ids):
    seen, pending = set(), list(ids)
    while pending:
        rid = pending.pop()
        if rid in seen:
            continue
        seen.add(rid)
        record = store.get(rid)
        if record:
            def links(value):
                if isinstance(value, dict):
                    for item in value.values():
                        yield from links(item)
                elif isinstance(value, list):
                    for item in value:
                        yield from links(item)
                elif isinstance(value, str) and value in store.by_id:
                    yield value
            pending.extend(links(record))
    return seen


def team_state(store, evaluation_id):
    claims = [record.data for record in store.of_kind('team_claim') if record.data.get('action') == 'claim']
    if any(evaluation_id in _closure(store, claim['records']) for claim in claims):
        return 'claimed'
    if any(record.data.get('action') == 'release' and evaluation_id in execution_ids(store, record.data.get('evaluation'))
           for record in store.of_kind('team_claim')):
        return 'released'
    return 'pending'


def execution_ids(store, evaluation_id):
    """A release of an aggregate covers its explicitly identified executions."""
    ids, pending = set(), [evaluation_id]
    while pending:
        rid = pending.pop()
        if rid in ids:
            continue
        evaluation = store.get(rid, 'evaluation')
        if evaluation is None:
            continue
        ids.add(rid)
        pending.extend(item.get('evaluation') for item in evaluation.get('component_evaluations', []))
    return ids


def _delete(records, evaluation_id, entries, reason, *, db=None, approval=None):
    with _custody_lock(records):
        return _delete_locked(records, evaluation_id, entries, reason, db=db, approval=approval)


def _delete_locked(records, evaluation_id, entries, reason, *, db=None, approval=None):
    """Validate the complete event before mutation, then record each actual deletion."""
    store = _require_valid(records)
    if not store.get(evaluation_id, 'evaluation'):
        raise Failure('retention requires an existing evaluation')
    if team_state(store, evaluation_id) == 'claimed':
        raise Failure('prune refuses output retained by a team claim')
    if len({entry['path'] for entry in entries}) != len(entries):
        raise Failure('prune refuses duplicate listed paths')
    checked = []
    for entry in entries:
        path = Path(entry['path'])
        if not path.is_absolute() or '..' in path.parts or any(parent.is_symlink() for parent in (path, *path.parents)):
            raise Failure('prune refuses relative or symlinked paths')
        if entry.get('class') != 'bulky' or classify(path, references(store, path)) != 'bulky':
            raise Failure(f'prune refuses non-bulky evidence: {path}')
        if not path.is_file() or path.stat().st_size != entry['bytes'] or artifacts.file_hash(path) != entry['sha256']:
            raise Failure(f'approved prune file changed or is missing: {path}')
        checked.append((path, dict(entry)))
    intent = None
    if checked:
        intent = workflow.record('retention', 'prune-intent-' + uuid.uuid4().hex,
            event='prune_intent', evaluation=evaluation_id, deleted=[],
            planned=[{key: entry[key] for key in ('path', 'sha256', 'bytes')} for _, entry in checked],
            reason=reason, occurred_at=_now(), host=socket.gethostname().split('.')[0], approval=approval)
        # Failure here leaves every byte intact; interrupted deletion still has
        # durable intended identities. Readers never count intent as deletion.
        workflow.persist(records, intent, db, create=True)
    deleted = []
    try:
        for path, entry in checked:
            # Recheck immediately before unlink; an approved path grants no
            # authority to delete replacement bytes.
            if team_state(_require_valid(records), evaluation_id) == 'claimed':
                raise Failure('prune refuses output retained by a new team claim')
            before = path.lstat()
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise Failure('prune path became a symlink')
            if before.st_size != entry['bytes'] or artifacts.file_hash(path) != entry['sha256']:
                raise Failure(f'prune file changed during apply: {path}')
            after = path.lstat()
            stamp = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
            if stamp(before) != stamp(after):
                raise Failure(f'prune file changed during hashing: {path}')
            path.unlink()
            deleted.append({key: entry[key] for key in ('path', 'sha256', 'bytes')})
    finally:
        if deleted:
            data = workflow.record('retention', 'retention-' + uuid.uuid4().hex,
                event='prune', evaluation=evaluation_id, deleted=deleted, reason=reason,
                occurred_at=_now(), host=socket.gethostname().split('.')[0], approval=approval, intent=intent['id'])
            workflow.persist(records, data, db, create=True)
    return deleted


def claim(args):
    with _custody_lock(args.records):
        result = _claim_locked(args)
    release = getattr(args, 'release', None)
    if release:
        automatic(args.records, execution_ids(_require_valid(args.records), release), 'comparison', db=getattr(args, 'db', None))
    return result


def _claim_locked(args):
    store = _require_valid(args.records)
    release = getattr(args, 'release', None)
    ids = getattr(args, 'record_ids', [])
    if release:
        if ids or getattr(args, 'audience', None) or not store.get(release, 'evaluation'):
            raise Failure('claim --release requires one existing evaluation and no records/audience')
        if team_state(store, release) == 'claimed':
            raise Failure('an evaluation cited by a team claim cannot be released')
        data = workflow.record('team_claim', 'team-release-' + uuid.uuid4().hex,
            action='release', records=[], audience=[], evaluation=release, recorded_at=_now())
    else:
        audience = [name.strip() for name in (getattr(args, 'audience', '') or '').split(',') if name.strip()]
        if not ids or not audience or any(not store.get(rid) for rid in ids):
            raise Failure('claim requires existing records and --audience NAMES (comma separated)')
        evaluations = [rid for rid in _closure(store, ids) if store.get(rid, 'evaluation')]
        for rid in evaluations:
            if team_state(store, rid) == 'released' or any(record.data.get('evaluation') == rid
                    and record.data.get('event') == 'prune' and any(Path(item['path']).name in {'roi-debug.trace.gz', 'debug.trace.gz'}
                    for item in record.data.get('deleted', [])) for record in store.of_kind('retention')):
                raise Failure(f'cannot claim released or pruned evaluation {rid}')
        data = workflow.record('team_claim', 'team-claim-' + uuid.uuid4().hex,
            action='claim', records=list(dict.fromkeys(ids)), audience=audience, recorded_at=_now())
    return workflow.persist(args.records, data, getattr(args, 'db', None), create=True)


def prune(args):
    store = _require_valid(args.records)
    if getattr(args, 'dry_run', False):
        data = listing(store, getattr(args, 'run_roots', None) or RUN_ROOTS)
        destination = Path(args.output)
        with destination.open('x') as stream:
            stream.write(json.dumps(data, indent=2, sort_keys=True) + '\n')
        return {'listing': str(destination.absolute()), 'sha256': artifacts.file_hash(destination),
                'files': data['files'], 'deleted': []}
    source = Path(getattr(args, 'approve', None) or args.apply)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 64 * 1024 ** 2:
        raise Failure('prune listing must be a regular file of at most 64 MiB')
    raw = source.read_bytes()
    import hashlib
    digest = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    if data.get('format') != 'swdb.prune-listing.v1' or data.get('host') != socket.gethostname().split('.')[0]:
        raise Failure('prune listing format or host differs')
    if getattr(args, 'approve', None):
        approval = workflow.record('retention', 'prune-approval-' + uuid.uuid4().hex,
            event='approval', deleted=[], reason='Yan-Ru approved this exact cleanup listing.',
            occurred_at=_now(), host=data['host'], listing={'path': str(source.absolute()), 'sha256': digest},
            approved_by='yanrujhou')
        return workflow.persist(args.records, approval, getattr(args, 'db', None), create=True)
    approvals = [record for record in store.of_kind('retention') if record.data.get('event') == 'approval'
                 and record.data.get('listing', {}).get('sha256') == digest
                 and record.data.get('approved_by') == 'yanrujhou' and record.data.get('host') == data['host']]
    if not approvals:
        raise Failure('prune --apply refuses a listing without recorded Yan-Ru approval')
    roots = [Path(root) for root in data['roots']]
    events = {}
    seen = set()
    for entry in data['files']:
        if not entry.get('proposed'):
            continue
        path = Path(entry['path'])
        if entry.get('class') != 'bulky' or len(entry.get('evaluations', [])) != 1 or not any(path.is_relative_to(root) for root in roots):
            raise Failure('approved listing proposes a non-bulky, unowned, or out-of-root file')
        if path in seen:
            raise Failure('approved listing repeats a proposed path')
        seen.add(path)
        events.setdefault(entry['evaluations'][0], []).append(entry)
    # Prevalidate all events before deleting the first one.
    for entries in events.values():
        for entry in entries:
            path = Path(entry['path'])
            if path.is_symlink() or not path.is_file() or classify(path, references(store, path)) != 'bulky' or path.stat().st_size != entry['bytes'] or artifacts.file_hash(path) != entry['sha256']:
                raise Failure('approved listing changed or now contains protected evidence')
            if team_state(store, entry['evaluations'][0]) == 'claimed':
                raise Failure('approved listing cannot override a team claim')
    deleted = []
    for rid, entries in events.items():
        deleted.extend(_delete(args.records, rid, entries, 'Approved cleanup listing',
                               db=getattr(args, 'db', None), approval=approvals[-1].id))
    return {'deleted': deleted, 'listing_sha256': digest}


def automatic(records, evaluation_ids, trigger, *, db=None):
    store = _require_valid(records)
    deleted = []
    for rid in evaluation_ids:
        evaluation = store.get(rid, 'evaluation')
        if not evaluation or evaluation.get('outcome', {}).get('state') != 'complete' or evaluation.get('correctness', {}).get('state') != 'passed':
            continue
        if team_state(store, rid) == 'claimed':
            continue
        if trigger == 'comparison':
            if team_state(store, rid) != 'released':
                continue
            aggregates = [record for record in store.of_kind('evaluation') if any(
                item.get('evaluation') == rid for item in record.data.get('component_evaluations', []))]
            comparisons = [record for record in store.of_kind('comparison_result')
                if record.data.get('decision', {}).get('state') != 'rejected']
            packages = [record for record in store.of_kind('profile_package') if rid in _closure(store, [record.id])
                        and record.data.get('completeness') in {'complete', 'fixture'}]
            coverage_reference = evaluation.get('context', {}).get('coverage_report')
            coverage_report = (evaluation.get('request', {}).get('protocol_companion') == 'parent_gather_race'
                and isinstance(coverage_reference, dict) and Path(coverage_reference.get('path', '')).is_file()
                and artifacts.file_hash(coverage_reference['path']) == coverage_reference.get('sha256')
                and all(check.get('coverage', {}).get('state') == 'observed'
                        and check.get('frontier_sizes', {}).get('state') == 'passed'
                        and check.get('parent_gather_race', {}).get('outcome') in {'observed', 'inconclusive', 'refuted'}
                        for check in evaluation.get('correctness', {}).get('checks', []))
                and bool(evaluation.get('correctness', {}).get('checks')))
            is_profile = bool(evaluation.get('context', {}).get('diagnostic')) or (bool(packages) and not evaluation.get('request', {}).get('protocol'))
            ready = coverage_report or bool(packages if is_profile else aggregates)
            if coverage_report:
                comparisons = [record for record in comparisons if rid in record.data.get('request', {}).get('companion_evaluations', {}).values()]
            elif is_profile:
                package_ids = {record.id for record in packages}
                comparisons = [record for record in comparisons if package_ids & set(record.data.get('request', {}).get('region_packages', {}).values())]
            else:
                aggregate_ids = {record.id for record in aggregates}
                comparisons = [record for record in comparisons if any(record.data.get(key) in aggregate_ids
                    for key in ('baseline_evaluation', 'candidate_evaluation'))]
            if not comparisons or not ready:
                continue
        folder_refs = [Path(row['path']) for row in evaluation.get('raw_artifacts', [])
                       if row.get('kind') == 'dx100_execute' and isinstance(row.get('path'), str)]
        for folder in folder_refs:
            if not folder.is_dir() or folder.is_symlink():
                continue
            entries = []
            for path in folder.rglob('*'):
                if not path.is_file() or path.is_symlink():
                    continue
                is_checkpoint = any(part.startswith('cpt.') for part in path.parts)
                if (trigger == 'execute') != is_checkpoint:
                    continue
                refs = references(store, path)
                if classify(path, refs) == 'bulky':
                    entries.append({'path': str(path), 'sha256': artifacts.file_hash(path),
                                    'bytes': path.stat().st_size, 'class': 'bulky'})
            if entries:
                deleted.extend(_delete(records, rid, entries, f'Automatic {trigger} pruning', db=db))
    return deleted


def validate_record(record, ctx):
    from swdb.problems import Problem
    data = record.data
    if record.kind == 'team_claim' and data.get('action') == 'claim':
        for index, rid in enumerate(data['records']):
            if not ctx.store.get(rid):
                yield Problem(record.rel, f'records[{index}]', 'team claim cites a missing record')
    if record.kind == 'retention' and data.get('event') == 'prune':
        if len({item['path'] for item in data['deleted']}) != len(data['deleted']):
            yield Problem(record.rel, 'deleted', 'retention event repeats a deleted path')
        if data.get('approval') is not None:
            approval = ctx.store.get(data['approval'], 'retention')
            if not approval or approval.get('event') != 'approval':
                yield Problem(record.rel, 'approval', 'prune approval does not name a listing approval record')
        if data.get('intent') is not None:
            intent = ctx.store.get(data['intent'], 'retention')
            if not intent or intent.get('event') != 'prune_intent' or intent.get('evaluation') != data['evaluation']:
                yield Problem(record.rel, 'intent', 'prune intent must identify this evaluation and planned event')
            elif any(item not in intent['planned'] for item in data['deleted']):
                yield Problem(record.rel, 'deleted', 'deleted identities differ from the durable intent')


def register_cli(commands):
    for name, handler in (('claim', claim), ('prune', prune)):
        sub = commands.add_parser(name, help='record team evidence claims' if name == 'claim' else 'inspect and apply exact approved raw-output cleanup')
        sub.add_argument('--records', type=Path, default=paths.RECORDS)
        sub.add_argument('--db', type=Path)
        sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
        sub.set_defaults(retention_handler=handler)
        if name == 'claim':
            sub.add_argument('record_ids', nargs='*')
            sub.add_argument('--audience')
            sub.add_argument('--release')
        else:
            action = sub.add_mutually_exclusive_group(required=True)
            action.add_argument('--dry-run', action='store_true')
            action.add_argument('--approve', type=Path)
            action.add_argument('--apply', type=Path)
            sub.add_argument('--run-root', dest='run_roots', action='append', type=Path)
            sub.add_argument('--output', type=Path, default=Path('prune-listing.json'))

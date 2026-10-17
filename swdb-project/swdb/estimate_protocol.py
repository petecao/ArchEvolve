"""Immutable analytic protocol and counted-input binding. Updated: 2026-10-06 ET."""
import copy
import re

from swdb import artifacts
from swdb.cli import Failure


def _require(condition, reason):
    if not condition:
        raise Failure(reason)


def _input(store, rid):
    data = store.get(rid)
    _require(data is not None and data.get('kind') in {'input', 'workload'}, f'input/workload {rid!r} does not exist')
    if data['kind'] == 'workload':
        from swdb.bfs_protocol import verify_immutable
        verify_immutable(data)
    return data


def estimator_identity():
    # Freeze the portable SWDB implementation bundle, including all mechanism
    # modules. Counts separately retain their LLVM pass/runtime/source hashes.
    from pathlib import Path
    root = Path(__file__).parent
    return artifacts.digest({path.relative_to(root).as_posix(): artifacts.file_hash(path)
                             for path in sorted(root.rglob('*.py'))})


def _dependency_identities(store, target):
    from swdb.extensa_boundary import _references, closure
    return {rid: artifacts.digest(store.get(rid))
            for rid in sorted(closure(store, _references(store, target)))}


def freeze(args, request, store):
    from swdb import analytic, bfs_protocol
    settings = copy.deepcopy(request['settings'])
    _require(settings.get('estimator_version') == analytic.VERSION, 'unsupported frozen estimator version')
    settings['estimator_sha256'] = estimator_identity()
    _require(isinstance(settings.get("target_description"), str), "estimated protocol needs a target-description record ID or YAML path")
    target = analytic._load(store, settings["target_description"], "target_description")
    from swdb.archevolve import require_team_safe
    require_team_safe(store, settings, target, command="freeze-protocol")
    settings['target_description'] = {'id': target['id'], 'sha256': artifacts.digest(target), 'snapshot': target}
    settings['dependency_identities'] = _dependency_identities(store, target)
    if 'cpu_error_band' in settings:
        from swdb.cpu_error_band import freeze_pin
        freeze_pin(settings, store)
    validate_settings(settings, store)
    inputs = {rid: artifacts.digest(_input(store, rid)) for rid in settings['inputs']}
    sources = {}
    for rid in settings.get('sources', []):
        data = store.get(rid)
        _require(data is not None and data['kind'] in {'implementation', 'candidate', 'source_snapshot'},
                 f'source record {rid!r} does not exist')
        sources[rid] = artifacts.digest(data)
    return bfs_protocol._save_immutable(args, request, 'protocol', settings=settings,
        workload_identities={}, input_identities=inputs, source_identities=sources,
        frozen_at=bfs_protocol._now(), state='frozen')


def validate_settings(settings, store):
    _require(settings.get('mode') == 'estimated', 'not an estimated protocol')
    _require(isinstance(settings.get('estimator_version'), str) and bool(settings['estimator_version']), 'frozen estimator version is required')
    _require(re.fullmatch(r'[0-9a-f]{64}', str(settings.get('estimator_sha256'))), 'frozen estimator bundle hash is required')
    _require(type(settings.get('threads')) is int and settings['threads'] >= 1, 'estimated protocol threads must be a positive integer')
    _require(isinstance(settings.get('roi'), str) and bool(settings['roi'].strip()), 'estimated protocol needs its counted ROI identity')
    inputs = settings.get('inputs')
    _require(isinstance(inputs, list) and inputs and all(isinstance(rid, str) for rid in inputs)
             and len(inputs) == len(set(inputs)), 'estimated protocol needs unique input IDs')
    for rid in inputs:
        _input(store, rid)
    arguments = settings.get('input_run_arguments')
    if arguments is not None:
        _require(isinstance(arguments, dict) and set(arguments) == set(inputs)
                 and all(isinstance(values, list) and all(isinstance(arg, str) for arg in values)
                         for values in arguments.values()), 'input_run_arguments must freeze an argument list for every protocol input')
    sources = settings.get('sources', [])
    _require(isinstance(sources, list) and all(isinstance(rid, str) for rid in sources)
             and len(sources) == len(set(sources)), 'estimated protocol sources must be unique record IDs')
    pin = settings.get('target_description')
    _require(isinstance(pin, dict) and set(pin) == {'id', 'sha256', 'snapshot'}, 'estimated protocol needs a frozen target-description snapshot/hash')
    snapshot = pin['snapshot']
    _require(isinstance(snapshot, dict) and snapshot.get('kind') == 'target_description'
             and pin['id'] == snapshot.get('id') and re.fullmatch(r'[0-9a-f]{64}', str(pin['sha256']))
             and pin['sha256'] == artifacts.digest(snapshot), 'frozen target-description snapshot/hash differs')
    _require(snapshot['threads'] == settings['threads'], 'estimated protocol and target thread counts differ')
    if 'cpu_error_band' in settings:
        from swdb.cpu_error_band import validate_pin
        validate_pin(settings, store)
    dependencies = settings.get('dependency_identities')
    _require(isinstance(dependencies, dict) and all(isinstance(rid, str)
             and re.fullmatch(r'[0-9a-f]{64}', str(digest)) for rid, digest in dependencies.items()),
             'frozen target dependency identities are required')
    current = store.get(pin['id'], 'target_description')
    _require(current is None or artifacts.digest(current) == pin['sha256'], 'frozen target-description record changed')


def validate_frozen(data, store):
    settings = data['settings']
    validate_settings(settings, store)
    for rid, digest in settings['dependency_identities'].items():
        current = store.get(rid)
        _require(current is not None and artifacts.digest(current) == digest, f'frozen target dependency record {rid!r} changed')
    _require(settings['dependency_identities'] == _dependency_identities(store, settings['target_description']['snapshot']),
             'frozen target dependency closure differs')
    _require(set(data.get('input_identities', {})) == set(settings['inputs']), 'frozen input identities do not match protocol inputs')
    for rid, digest in data['input_identities'].items():
        _require(artifacts.digest(_input(store, rid)) == digest, f'frozen input record {rid!r} changed')
    _require(set(data.get('source_identities', {})) == set(settings.get('sources', [])), 'frozen source identities do not match protocol sources')
    for rid, digest in data.get('source_identities', {}).items():
        current = store.get(rid)
        _require(current is not None and artifacts.digest(current) == digest, f'frozen source record {rid!r} changed')


def bind(store, rid, characterization, target):
    from swdb import bfs_protocol
    protocol = store.get(rid, 'protocol')
    _require(protocol is not None, f'frozen estimate protocol {rid!r} does not exist')
    bfs_protocol.verify_immutable(protocol)
    validate_frozen(protocol, store)
    settings = protocol['settings']
    from swdb.analytic import VERSION
    _require(settings['estimator_version'] == VERSION and settings['estimator_sha256'] == estimator_identity(),
             'estimator implementation changed after freeze; freeze a fresh protocol')
    _require(artifacts.digest(target) == settings['target_description']['sha256'], 'estimate target description differs from frozen protocol')
    binding = characterization['binding']
    _require((binding['state'] == 'fixture' and characterization['evidence_kind'] == 'contract_fixture')
             or (binding['state'] == 'verified' and characterization['evidence_kind'] == 'execution'),
             'application estimate requires verified registered-source/input binding')
    iid = characterization['input']
    _require(iid in protocol['input_identities'] and binding['input_record_sha256'] == protocol['input_identities'][iid],
             'counted input record differs from frozen protocol')
    _require(binding['roi'] == settings['roi'] and binding['threads'] == settings['threads'], 'counted ROI or threads differ from frozen protocol')
    _require(binding['run_arguments_sha256'] == artifacts.digest(characterization['source']['run_arguments']),
             'counted run arguments differ from their binding receipt')
    arguments = settings.get('input_run_arguments')
    _require(binding['state'] == 'fixture' or arguments is not None, 'application estimate requires frozen per-input run arguments')
    if arguments is not None:
        _require(binding['run_arguments_sha256'] == artifacts.digest(arguments[iid]), 'counted run arguments differ from frozen protocol')
    subject = characterization['subject']['id']
    current = store.get(subject, characterization['subject']['kind'])
    identity = binding['subject_source_identity']
    _require(current is not None and artifacts.digest(current) == identity.get('subject_record_sha256'), 'counted source subject record changed')
    if current['kind'] == 'candidate':
        _require(current['source_snapshot'] == identity.get('source_snapshot')
                 and current['artifact']['sha256'] == identity.get('candidate_artifact_sha256')
                 and current.get('diff_sha256') == identity.get('candidate_diff_sha256'), 'counted candidate source identity changed')
    if protocol.get('source_identities'):
        _require(subject in protocol['source_identities'] or identity.get('source_snapshot') in protocol['source_identities'],
                 'counted source is absent from frozen protocol sources')
    if binding['state'] != 'fixture':
        try:
            from swdb.analytic_binding import verify_binding
        except ModuleNotFoundError:
            raise Failure('application estimate requires the registered-source binding verifier') from None
        problems = verify_binding(characterization, store, require_available=False)
        _require(not problems, f'registered-source/input binding proof failed: {problems}')
    return protocol

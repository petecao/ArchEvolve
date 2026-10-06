"""Immutable CPU error evidence; missing whole-call costs stay failed. Created: 2026-10-06 ET."""
import copy
import math
import time
from pathlib import Path

from swdb import artifacts, paths, writer, workflow
from swdb.cli import Failure
from swdb.cpu_service_calibration import identity
from swdb.problems import Problem
from swdb.store import Store


def register_cli(commands):
    p = commands.add_parser('freeze-cpu-error-band', help='freeze development error width or explicit whole-call failure')
    p.add_argument('--records', type=Path, default=paths.RECORDS)
    p.add_argument('--estimate', action='append', required=True)
    p.add_argument('--validation', action='append', default=[], help='matched original-driver validation IDs in estimate order')
    p.add_argument('--id', required=True)
    p.add_argument('--fixture', action='store_true')
    p.add_argument('--format', choices=['yaml', 'json'], default='json')
    p.set_defaults(cpu_error_band_handler=freeze)


def _load(store, rid, kind):
    from swdb.analytic import _load as load
    return load(store, rid, kind)


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _pair(store, estimate, validation, fixture):
    from swdb.archevolve import require_team_safe
    require_team_safe(store, estimate, validation or {}, command='freeze-cpu-error-band')
    missing = []
    predicted = estimate['seconds']
    if not _positive(predicted):
        missing.append('complete_positive_whole_call_estimate')
    native = None
    if validation is None:
        missing.append('matched_native_validation')
    else:
        if not fixture and (validation['evidence_kind'] != 'native' or estimate['evidence_kind'] != 'execution'):
            missing.append('actual_native_execution')
        if (estimate['characterization'] != validation['characterization']
                or estimate['characterization_sha256'] != validation['characterization_sha256']
                or estimate['threads'] != validation['threads'] or estimate['target'] != validation['target']
                or estimate['subject']['id'] != validation['implementation'] or estimate['input'] != validation['input']):
            missing.append('exact_counted_source_input_thread_target_pair')
        native = validation['summary']['median_whole_call_s']
        if not _positive(native):
            missing.append('positive_resolved_native_time')
    log_error = None
    worst_error = None
    if not missing:
        half = validation['summary']['rounding_half_width_s']
        if not _positive(native - half):
            missing.append('printed_time_resolution')
        else:
            log_error = math.log(predicted) - math.log(native)
            worst_error = max(abs(math.log(predicted) - math.log(native-half)), abs(math.log(predicted) - math.log(native+half)))
    return {'estimate': estimate['id'], 'estimate_sha256': artifacts.digest(estimate),
        'validation': None if validation is None else validation['id'],
        'validation_sha256': None if validation is None else artifacts.digest(validation),
        'input': estimate['input'], 'predicted_seconds': predicted, 'native_seconds': native,
        'log_error': log_error, 'rounding_aware_absolute_log_error': worst_error,
        'missing': sorted(set(missing)), 'regions': copy.deepcopy(estimate['regions'])}


def freeze(args):
    if workflow.CREATION_TAGS.get('mode') == 'extensa':
        raise Failure('CPU error bands require ArchEvolve mode')
    if len(set(args.estimate)) != len(args.estimate):
        raise Failure('development estimates must be unique independent workload pairs')
    if args.validation and len(args.validation) != len(args.estimate):
        raise Failure('validation IDs must match estimate IDs in order')
    store = Store(args.records)
    estimates = [_load(store, rid, 'estimate') for rid in args.estimate]
    validations = [_load(store, rid, 'cpu_native_validation') for rid in args.validation] if args.validation else [None] * len(estimates)
    pairs = [_pair(store, e, v, args.fixture) for e, v in zip(estimates, validations)]
    # Trial samples share graph/process state; the unit here is an independently
    # scoped workload pair, never five purported independent error observations.
    values = [p['rounding_aware_absolute_log_error'] for p in pairs]
    known = all(value is not None for value in values)
    state = ('fixture' if args.fixture else 'development') if known else 'failed'
    first = estimates[0]
    record = {'kind': 'cpu_error_band', 'schema_version': '0.4', 'id': args.id,
        'status': 'draft', 'created': writer.today(), 'updated': writer.today(),
        'provenance': [{'id': 'error-band', 'kind': 'source_code' if args.fixture else 'measurement',
            'description': 'Empirical whole-call development envelope with printed-time rounding; held-out validation is separate. No missing cost or timing is filled.', 'uri': None}],
        'format': 'swdb.cpu-error-band.v1', 'backend': 'native', 'evidence_kind': 'fixture' if args.fixture else 'native',
        'state': state, 'width_log': max(values) if known else None, 'frozen_ns': time.time_ns(),
        'target_description_sha256': first['target_description_sha256'], 'estimator_sha256': first['estimator_sha256'],
        'threads': first['threads'], 'pairs': pairs, 'development_band': None,
        'admission': {'generalization': 'none; no unseen implementation, kernel, workload, thread or target confidence',
            'validated': False, 'unit': 'independent workload pair; five original-driver trials are retained within the pair',
            'missing': sorted({m for p in pairs for m in p['missing']}),
            'large_error_threshold_log': math.log(1.25)},
        'notes': ['A failed or development-only band never enables a gain verdict.',
            'Region bounds and missing costs are diagnostic estimates, not measured region timings.']}
    record['identity_sha256'] = identity(record)
    writer.commit(args.records, new=[record])
    return record


def require_holdout(store, rid, characterization, *, protocol):
    band = _load(store, rid, 'cpu_error_band')
    if band['state'] != 'development' or band['evidence_kind'] != 'native' or band['width_log'] is None:
        raise Failure('held-out timing requires a known frozen native development width')
    if protocol is None or protocol['settings']['estimator_sha256'] != band['estimator_sha256'] or protocol['settings']['target_description']['sha256'] != band['target_description_sha256']:
        raise Failure('held-out model/calibration identity differs from frozen development')
    if characterization['input'] in {p['input'] for p in band['pairs']}:
        raise Failure('held-out input was already used in development')
    return band


def freeze_pin(settings, store):
    rid = settings['cpu_error_band']
    if not isinstance(rid, str):
        raise Failure('cpu_error_band must name a persisted band record before freeze')
    band = _load(store, rid, 'cpu_error_band')
    from swdb.archevolve import require_team_safe
    require_team_safe(store, band, command='freeze-protocol CPU error band')
    from swdb.extensa_boundary import closure
    settings['cpu_error_band'] = {'id':band['id'], 'sha256':artifacts.digest(band), 'snapshot':copy.deepcopy(band)}
    settings['cpu_error_band_dependencies'] = {key:artifacts.digest(store.get(key)) for key in sorted(closure(store,[rid]))}
    validate_pin(settings, store)


def validate_pin(settings, store):
    pin = settings['cpu_error_band']
    if not isinstance(pin, dict) or set(pin) != {'id','sha256','snapshot'}:
        raise Failure('CPU error band requires a frozen ID/hash/snapshot')
    band = pin['snapshot']
    current = store.get(pin['id'],'cpu_error_band')
    if not isinstance(band,dict) or band.get('kind')!='cpu_error_band' or band.get('id')!=pin['id'] or current is None or artifacts.digest(band)!=pin['sha256'] or artifacts.digest(current)!=pin['sha256'] or band.get('identity_sha256')!=identity(band):
        raise Failure('CPU error band snapshot or persisted record changed')
    from swdb.archevolve import require_team_safe
    require_team_safe(store, band, command='frozen CPU error band')
    if band['estimator_sha256']!=settings['estimator_sha256'] or band['target_description_sha256']!=settings['target_description']['sha256'] or band['threads']!=settings['threads']:
        raise Failure('CPU error band model/calibration/threads differ from protocol')
    from swdb.extensa_boundary import closure
    expected={key:artifacts.digest(store.get(key)) for key in sorted(closure(store,[pin['id']]))}
    if settings.get('cpu_error_band_dependencies')!=expected:
        raise Failure('CPU error band dependency closure changed')
    return band


def finalize_estimate(result, *, store, protocol, characterization, target_description):
    settings = protocol['settings']
    if 'cpu_error_band' not in settings:
        return result
    band = validate_pin(settings,store)
    result['error_band'] = {'id':band['id'],'sha256':artifacts.digest(band),'state':band['state'],
        'width_log':band['width_log'],'validated':False,
        'missing':copy.deepcopy(band['admission']['missing']),
        'admission_reason':'Failed, fixture or development-only band; prospective scoped holdout admission unavailable.'}
    result['verdict']='within_error'
    result['notes'].append('The frozen CPU band is retained beside this verdict; it grants no validated confidence.')
    return result


def validate_record(record, ctx):
    data = record.data
    try:
        if data['identity_sha256'] != identity(data):
            raise Failure('CPU error-band content identity differs')
        expected = []
        for pair in data['pairs']:
            estimate = ctx.passed(pair['estimate'], 'estimate')
            validation = ctx.passed(pair['validation'], 'cpu_native_validation') if pair['validation'] else None
            if estimate is None or (pair['validation'] and validation is None):
                raise Failure('CPU error-band pair dependency is unavailable or invalid')
            expected.append(_pair(ctx.store, estimate, validation, data['evidence_kind'] == 'fixture'))
        if expected != data['pairs']:
            raise Failure('CPU error-band inputs or per-region explanations changed')
        values = [p['rounding_aware_absolute_log_error'] for p in expected]
        width = max(values) if all(v is not None for v in values) else None
        state = ('fixture' if data['evidence_kind'] == 'fixture' else 'development') if width is not None else 'failed'
        if data['width_log'] != width or data['state'] != state or data['admission']['validated'] is not False:
            raise Failure('CPU error-band state/width differs from admitted development evidence')
    except (Failure, KeyError, TypeError, ValueError) as exc:
        yield Problem(record.rel, 'identity_sha256', str(exc))

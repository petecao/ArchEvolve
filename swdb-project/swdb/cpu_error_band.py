"""Immutable CPU error evidence; missing whole-call costs stay failed. Created: 2026-10-06 ET."""
import copy
import math
import time
from pathlib import Path

from swdb import artifacts, paths, writer, workflow
from swdb.cli import Failure
from swdb.cpu_service_calibration import identity
from swdb.problems import Problem
from swdb.store import Store, Record


def register_cli(commands):
    p = commands.add_parser('freeze-cpu-error-band', help='freeze development error width or explicit whole-call failure')
    p.add_argument('--records', type=Path, default=paths.RECORDS)
    p.add_argument('--estimate', action='append', required=True)
    p.add_argument('--validation', action='append', default=[], help='matched original-driver validation IDs in estimate order')
    p.add_argument('--id', required=True)
    p.add_argument('--fixture', action='store_true')
    p.add_argument('--format', choices=['yaml', 'json'], default='json')
    p.set_defaults(cpu_error_band_handler=freeze)
    p = commands.add_parser('validate-cpu-error-band', help='retain prospective held-out error against an unchanged frozen development width')
    p.add_argument('--records', type=Path, default=paths.RECORDS)
    p.add_argument('--development-band', required=True)
    p.add_argument('--estimate', action='append', required=True)
    p.add_argument('--validation', action='append', required=True)
    p.add_argument('--id', required=True)
    p.add_argument('--fixture', action='store_true')
    p.add_argument('--format', choices=['yaml','json'], default='json')
    p.set_defaults(cpu_error_band_handler=holdout)


def _load(store, rid, kind):
    from swdb.analytic import _load as load
    return load(store, rid, kind)


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


class _Context:
    def __init__(self,store):self.store=store
    def passed(self,rid,kind):
        try:return _load(self.store,rid,kind)
        except Failure:return None


def _source_scope(char):
    si=char['binding']['subject_source_identity']
    arguments=list(char['source']['run_arguments'])
    for flag in ('-g','-u'):
        if flag in arguments:
            i=arguments.index(flag)
            if i+1<len(arguments) and arguments[i+1].isdigit():arguments[i+1]='prospective_scale'
    native=char.get('observation_contract',{}).get('native_runtime')
    return {'implementation':char['subject']['id'],'source_root_sha256':si.get('source_root_sha256'),
        'translation_unit_sha256':char['source']['sha256'],'timed_wrapper_sha256':si.get('timed_wrapper_sha256'),
        'source_policy':si.get('source_policy'),'trial_count':si.get('trial_count'),
        'roi':char['binding']['roi'],'threads':char['binding']['threads'],
        'input_generation_shape':arguments,'flags':char['source']['build_flags']+char['toolchain']['compiler_flags'],
        'llvm_version':char['toolchain']['llvm_version'],'run_library_paths':char['toolchain']['run_library_paths'],
        'native_runtime':None if native is None else {k:copy.deepcopy(native.get(k)) for k in ('compiler_version','compiler_sha256','environment','environment_scope','loaded_libraries')}}


def _checked_band(store,rid):
    band=_load(store,rid,'cpu_error_band')
    problems=list(validate_record(Record(Path(rid),band),_Context(store)))
    if problems:raise Failure('invalid frozen CPU band: '+str(problems[0]))
    return band


def _common(estimates):
    fields=('target_description_sha256','estimator_sha256','threads','target','evidence_kind')
    if any(any(e.get(k)!=estimates[0].get(k) for k in fields) for e in estimates[1:]):
        raise Failure('CPU band cannot pool different model/calibration/bundle/thread/target/evidence identities')

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
        pin=validation.get('estimate_protocol')
        protocol=_load(store,estimate['protocol'],'protocol')
        if protocol.get('identity_sha256')!=estimate['protocol_sha256'] or not pin or any(pin.get(k)!=v for k,v in {'id':estimate['protocol'],'sha256':artifacts.digest(protocol),
            'estimator_sha256':estimate['estimator_sha256'],'target_description_sha256':estimate['target_description_sha256']}.items()):
            missing.append('exact_prior_frozen_estimate_protocol')
        from swdb.cpu_native_validation import validate_record as validate_native
        if list(validate_native(Record(Path(validation['id']),validation),_Context(store))):
            missing.append('valid_native_validation_scope')
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
        'characterization':estimate['characterization'],'characterization_sha256':estimate['characterization_sha256'],
        'input': estimate['input'], 'predicted_seconds': predicted, 'native_seconds': native,
        'log_error': log_error, 'rounding_aware_absolute_log_error': worst_error,
        'missing': sorted(set(missing)), 'regions': copy.deepcopy(estimate['regions']),
        'scope':None if validation is None else _source_scope(_load(store,estimate['characterization'],'workload_characterization'))}


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
    _common(estimates)
    if any(v is not None and v.get('development_band') is not None for v in validations):
        raise Failure('development width cannot be retuned from a heldout validation')
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


def _holdout_pairs(store,band,estimates,validations,fixture):
    _common(estimates)
    pairs=[]
    for estimate,validation in zip(estimates,validations):
        pair=_pair(store,estimate,validation,fixture)
        for field in ('target_description_sha256','estimator_sha256','threads'):
            if estimate[field]!=band[field]:pair['missing'].append('unchanged_development.'+field)
        if estimate['input'] in {p['input'] for p in band['pairs']}:pair['missing'].append('independent_heldout_input')
        if pair['scope'] not in [p.get('scope') for p in band['pairs']]:pair['missing'].append('exact_development_source_runtime_scope')
        if validation.get('development_band')!=band['id']:pair['missing'].append('prior_development_band_binding')
        if validation['context']['timing_started_ns']<=band['frozen_ns']:pair['missing'].append('holdout_timing_after_frozen_development_width')
        if not fixture:
            try:require_holdout(store,band['id'],_load(store,estimate['characterization'],'workload_characterization'),protocol=_load(store,estimate['protocol'],'protocol'))
            except Failure as exc:pair['missing'].append('prospective_holdout_admission: '+str(exc))
        if pair['rounding_aware_absolute_log_error'] is not None and pair['rounding_aware_absolute_log_error']>band['width_log']:
            pair['missing'].append('empirical_holdout_outside_frozen_width')
        pair['missing']=sorted(set(pair['missing']));pairs.append(pair)
    return pairs


def holdout(args):
    if workflow.CREATION_TAGS.get('mode')=='extensa':raise Failure('CPU error validation requires ArchEvolve mode')
    if len(args.estimate)!=len(args.validation) or len(set(args.estimate))!=len(args.estimate):
        raise Failure('heldout validation IDs must match unique estimate IDs in order')
    store=Store(args.records);band=_checked_band(store,args.development_band)
    if band['development_band'] is not None or band['width_log'] is None or band['state'] not in ('development','fixture'):
        raise Failure('holdout requires a known frozen development width, never a failed or heldout band')
    if not args.fixture and band['evidence_kind']!='native':raise Failure('native holdout requires actual native development evidence')
    estimates=[_load(store,rid,'estimate') for rid in args.estimate]
    validations=[_load(store,rid,'cpu_native_validation') for rid in args.validation]
    pairs=_holdout_pairs(store,band,estimates,validations,args.fixture)
    missing=sorted({reason for pair in pairs for reason in pair['missing']})
    passed=not missing
    record=copy.deepcopy(band)
    record.update(id=args.id,created=writer.today(),updated=writer.today(),frozen_ns=time.time_ns(),pairs=pairs,
        development_band=band['id'],state=('fixture' if args.fixture else 'validated') if passed else 'failed',
        evidence_kind='fixture' if args.fixture else 'native')
    record['admission'].update(validated=passed and not args.fixture,holdout_passed=passed,missing=missing,
        generalization='Only the exact held-out characterization identities; no unseen implementation, kernel, workload, thread or target confidence.')
    record['notes']=['Unchanged frozen development width tested against prospective held-out whole-call observations.',
        'An empirical scoped envelope is not a statistical confidence interval or a proven application upper bound; no outcome retuning.']
    record['identity_sha256']=identity(record)
    writer.commit(args.records,new=[record])
    return record


def require_holdout(store, rid, characterization, *, protocol):
    band = _checked_band(store,rid)
    if band['state'] != 'development' or band['evidence_kind'] != 'native' or band['width_log'] is None:
        raise Failure('held-out timing requires a known frozen native development width')
    if protocol is None or protocol['settings']['estimator_sha256'] != band['estimator_sha256'] or protocol['settings']['target_description']['sha256'] != band['target_description_sha256']:
        raise Failure('held-out model/calibration identity differs from frozen development')
    if characterization['input'] in {p['input'] for p in band['pairs']}:
        raise Failure('held-out input was already used in development')
    if _source_scope(characterization) not in [p.get('scope') for p in band['pairs']]:
        raise Failure('held-out source/ROI/runtime/compiler/process/input-generation scope differs from development')
    allowlist=protocol['settings']['target_description']['snapshot'].get('extensions',{}).get('cpu_services_binding',{}).get('characterization_allowlist',[])
    if {'id':characterization['id'],'sha256':artifacts.digest(characterization)} not in allowlist:
        raise Failure('held-out characterization was not frozen prospectively in the common model allowlist')
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
    _checked_band(store,pin['id'])
    from swdb.archevolve import require_team_safe
    require_team_safe(store, band, command='frozen CPU error band')
    if band['estimator_sha256']!=settings['estimator_sha256'] or band['target_description_sha256']!=settings['target_description']['sha256'] or band['threads']!=settings['threads']:
        raise Failure('CPU error band model/calibration/threads differ from protocol')
    from swdb.extensa_boundary import closure
    expected={key:artifacts.digest(store.get(key)) for key in sorted(closure(store,[pin['id']]))}
    if settings.get('cpu_error_band_dependencies')!=expected:
        raise Failure('CPU error band dependency closure changed')
    return band


def _admitted_estimate(band,result):
    return (band['state']=='validated' and band['evidence_kind']=='native' and band['admission']['validated'] is True
        and any(p['estimate']==result['id'] or
            (p.get('scope',{}).get('implementation')==result['subject']['id'] and p['input']==result['input']
             and not p['missing'] and p['estimate_sha256'] and p.get('characterization')==result['characterization']
             and p.get('characterization_sha256')==result['characterization_sha256']) for p in band['pairs']))


def finalize_estimate(result, *, store, protocol, characterization, target_description):
    settings=protocol['settings']
    if 'cpu_error_band' not in settings:return result
    band=validate_pin(settings,store)
    admitted=_admitted_estimate(band,result)
    reason='Exact held-out native scope admitted; empirical envelope only.' if admitted else 'Failed, fixture, development-only or unmatched held-out scope grants no validated confidence.'
    result['error_band']={'id':band['id'],'sha256':artifacts.digest(band),'state':band['state'],
        'width_log':band['width_log'],'validated':admitted,'missing':copy.deepcopy(band['admission']['missing']),
        'admission_reason':reason}
    result['verdict']='within_error'
    baseline=None if result.get('baseline') is None else store.get(result['baseline']['id'],'estimate')
    if admitted and baseline is not None and _admitted_estimate(band,baseline) and _positive(result.get('ratio')):
        log_ratio=math.log(result['ratio']);radius=2*band['width_log'];threshold=math.log(1.05)
        if log_ratio-radius>threshold:result['verdict']='estimated_gain'
        elif log_ratio+radius<threshold:result['verdict']='estimated_no_gain'
        result['error_band']['ratio_log_interval']=[log_ratio-radius,log_ratio+radius]
        result['error_band']['gain_threshold']=1.05
    result['notes'].append(reason+' Unseen implementations, kernels, inputs, threads or targets receive no envelope transfer; native CPU timing selection remains separate.')
    return result


def validate_record(record, ctx):
    data = record.data
    try:
        if data['identity_sha256'] != identity(data):
            raise Failure('CPU error-band content identity differs')
        expected = []
        estimates=[];validations=[]
        for pair in data['pairs']:
            estimate = ctx.passed(pair['estimate'], 'estimate')
            validation = ctx.passed(pair['validation'], 'cpu_native_validation') if pair['validation'] else None
            if estimate is None or (pair['validation'] and validation is None):
                raise Failure('CPU error-band pair dependency is unavailable or invalid')
            estimates.append(estimate);validations.append(validation)
            expected.append(_pair(ctx.store, estimate, validation, data['evidence_kind'] == 'fixture'))
        _common(estimates)
        if any(v is not None and v['context']['finished_ns']>data['frozen_ns'] for v in validations):
            raise Failure('CPU band must freeze after its retained validation finishes')
        if data['development_band'] is None and any(v is not None and v.get('development_band') is not None for v in validations):
            raise Failure('development width cannot reuse heldout timing')
        if data['development_band'] is not None:
            band=_checked_band(ctx.store,data['development_band'])
            if band['development_band'] is not None or band['width_log'] is None:
                raise Failure('heldout source is not a known development band')
            expected=_holdout_pairs(ctx.store,band,estimates,validations,data['evidence_kind']=='fixture')
            passed=not any(p['missing'] for p in expected)
            state=('fixture' if data['evidence_kind']=='fixture' else 'validated') if passed else 'failed'
            if data['width_log']!=band['width_log'] or data['state']!=state or data['admission']['validated']!=(passed and data['evidence_kind']=='native') or data['admission'].get('holdout_passed')!=passed:
                raise Failure('heldout width/state differs from unchanged development evidence')
        if data['admission']['missing']!=sorted({reason for pair in expected for reason in pair['missing']}):
            raise Failure('CPU band admission explanations differ from retained evidence')
        if expected != data['pairs']:
            raise Failure('CPU error-band inputs or per-region explanations changed')
        values = [p['rounding_aware_absolute_log_error'] for p in expected]
        width = max(values) if all(v is not None for v in values) else None
        state = ('fixture' if data['evidence_kind'] == 'fixture' else 'development') if width is not None else 'failed'
        if data['development_band'] is None and (data['width_log'] != width or data['state'] != state or data['admission']['validated'] is not False):
            raise Failure('CPU error-band state/width differs from admitted development evidence')
    except (Failure, KeyError, TypeError, ValueError) as exc:
        yield Problem(record.rel, 'identity_sha256', str(exc))

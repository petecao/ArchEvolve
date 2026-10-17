"""Typed, hash-bound CPU calibration provenance. Created: 2026-10-06 ET.

Legacy targets stay immutable. A fresh binding carries compact measured inputs,
not a new timing observation; source-count corrections retain their lineage.
"""
import copy

from yaml import YAMLError

from swdb import access, artifacts, writer
from swdb.cli import Failure
from swdb.store import Record, Store, canonical_path


def _identity(data):
    return artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})


def _evidence(target, identifier, lineage=None, equivalence=None):
    data = target['extensions']['cpu_calibration']
    record = {'kind': 'cpu_calibration', 'schema_version': '0.4', 'id': identifier,
        'status': 'draft', 'created': writer.today(), 'updated': writer.today(),
        'provenance': [{'id': 'cpu-calibration', 'kind': 'measurement' if data['evidence_kind'] == 'native' else 'source_code',
            'description': f"Compact CPU calibration receipt {data['receipt_sha256']}; exact elapsed/work trials retained; raw remains external.", 'uri': None}],
        'format': 'swdb.cpu-calibration-record.v1', 'backend': 'native',
        'evidence_kind': data['evidence_kind'], 'receipt_sha256': data['receipt_sha256'],
        'target': target['target'], 'threads': target['threads'],
        'context': copy.deepcopy(data['context']), 'settings': copy.deepcopy(data['settings']),
        'compute_counts': copy.deepcopy(data['compute_counts']), 'series': copy.deepcopy(data['series']),
        'concurrency_curve': copy.deepcopy(data['concurrency_curve']), 'plateau': copy.deepcopy(data['plateau']),
        'dependent_latency_s': copy.deepcopy(data['dependent_latency_s']),
        'lineage': lineage, 'source_count_equivalence': equivalence}
    record['identity_sha256'] = _identity(record)
    return record


def attach(target, prefix, lineage=None, equivalence=None):
    """Bind an existing compact native/fixture snapshot without promoting its basis."""
    evidence = _evidence(target, f'{prefix}.calibration.t{target["threads"]}', lineage, equivalence)
    target['calibration_sources'] = [evidence['id']]
    target['extensions']['cpu_calibration']['calibration_record_sha256'] = artifacts.digest(evidence)
    target['version'] = artifacts.digest({'receipt_sha256': evidence['receipt_sha256'],
        'calibration_record_sha256': artifacts.digest(evidence), 'format': 'swdb.cpu-calibration-binding.v1'})
    return evidence


def commit(records, targets, evidence, command):
    from swdb.archevolve import require_team_safe
    from swdb import workflow
    if workflow.CREATION_TAGS.get('mode') == 'extensa':
        raise Failure('CPU calibration import/binding produces team evidence; leave the inherited Extensa context')
    store = Store(records)
    for data in [*evidence, *targets]:
        store.add(Record(canonical_path(data['kind'], data['id']), data))
    require_team_safe(store, *targets, *evidence, command=command)
    writer.commit(records, new=[*evidence, *targets])


def _apply_equivalence(target, equivalence):
    from swdb.cpu_calibration import stats
    data = target['extensions']['cpu_calibration']
    if equivalence.get('identity_sha256') != _identity(equivalence) or equivalence.get('format') != 'swdb.cpu-calibration-pipeline-equivalence.v1':
        raise Failure('count equivalence identity/format differs')
    # Count-only proof transfers between receipts only under identical source/compiler
    # identities and old coefficients, checked below; native timings are never pooled.
    if equivalence.get('source_sha256') != data['context']['source_sha256']['CpuWork.h']:
        raise Failure('count equivalence and timed shared source differ')
    if equivalence.get('architecture') != data['context']['architecture'] or equivalence.get('compiler_version', '').strip() != data['context']['compiler_version'].strip():
        raise Failure('count equivalence mixes compiler/architecture contexts')
    if data['context']['flags'] != ['-O3', *equivalence['build_flags'], *equivalence['toolchain_flags']]:
        raise Failure('count equivalence mixes build/toolchain flags')
    if equivalence.get('timings_rerun') is not False or equivalence.get('runtime_dirty') is not False:
        raise Failure('count equivalence requires clean count-only context')
    old_counts = copy.deepcopy(data['compute_counts'])
    for category, old in data['compute_counts'].items():
        new = equivalence['compute_counts'][category]
        if new['old_validation_points'] != old['validation_points'] or (new['old_per_iteration'], new['old_per_invocation']) != (old['per_iteration'], old['per_invocation']):
            raise Failure('count equivalence old coefficients differ from the native receipt')
        slope, base = new['per_iteration'], new['per_invocation']
        points = new['validation_points']
        if type(slope) is not int or slope <= 0 or type(base) is not int or len(points) != 3 or [p[0] for p in points] != [p[0] for p in old['validation_points']] or any(n * slope + base != v for n, v in points):
            raise Failure('new compute numerator lacks a valid affine three-point proof')
        if new['new_pipeline']['version'] != 'source-normalized-v2' or new['source_sha256'] != old['source_sha256']:
            raise Failure('new numerator pipeline/shared source differs')
        old.update(per_iteration=slope, per_invocation=base, pipeline=new['new_pipeline'],
            validation_points=points, characterization_sha256=new['characterization_sha256'])
        item = next(s for s in data['series'] if s['shape'] == 'compute_' + category)
        item['operations_per_s'] = stats([(slope * t['iterations'] + base * target['threads']) / t['seconds'] for t in item['trials']])
        mechanism = next(m for m in target['mechanisms'] if m['model'] == 'compute_throughput')
        fact = mechanism['parameters'][category + '_ops_per_s']
        fact['value'] = item['operations_per_s']['median']
        fact['source'] += '; source-normalized-v2 numerator proof ' + equivalence['identity_sha256']
    data['source_count_equivalence_sha256'] = equivalence['identity_sha256']
    return old_counts


def bind(args):
    store = Store(args.records)
    equivalence = None
    if args.count_equivalence:
        try:
            equivalence = access.read_record(args.count_equivalence)
            if not isinstance(equivalence, dict) or not equivalence:
                raise Failure('count equivalence must be a nonempty mapping')
            if isinstance(equivalence, dict) and equivalence.get('format') == 'swdb.cpu-calibration-pipeline-equivalence-compact-receipt.v1':
                if equivalence.get('identity_sha256') != _identity(equivalence):
                    raise Failure('compact count-equivalence wrapper identity differs')
                equivalence = equivalence['equivalence']
            if not isinstance(equivalence, dict) or equivalence.get('format') != 'swdb.cpu-calibration-pipeline-equivalence.v1':
                raise Failure('unsupported count equivalence format')
        except (OSError, ValueError, KeyError, YAMLError) as exc:
            raise Failure(f'cannot read count equivalence: {exc}') from None
    targets, evidence, seen = [], [], set()
    for identifier in args.target_description:
        original = store.get(identifier, 'target_description')
        if original is None or original.get('estimator_variant') != 'team' or original.get('mode') == 'extensa':
            raise Failure('CPU binding needs an existing team target description')
        try:
            compact = original['extensions']['cpu_calibration']
            if compact['evidence_kind'] not in ('native', 'fixture'):
                raise Failure('CPU binding needs native or explicit fixture evidence')
            if compact['evidence_kind'] == 'fixture' and not args.fixture:
                raise Failure('fixture CPU binding requires --fixture')
            from swdb.archevolve import require_team_safe
            from swdb import workflow
            if workflow.CREATION_TAGS.get('mode') == 'extensa':
                raise Failure('CPU binding produces team evidence; leave the inherited Extensa context')
            legacy_source = f"CPU calibration {compact['receipt_sha256']}; threads={original['threads']}; useful source-element bytes"
            resolved = []
            for source in original['calibration_sources']:
                if store.get(source) is not None:
                    require_team_safe(store, source, command='bind-cpu-calibration')
                    resolved.append(source)
                elif source != legacy_source:
                    raise Failure('ADR 0013: unverifiable calibration dependency cannot be discarded: ' + repr(source))
            key = original['threads']
            if key in seen:
                raise Failure('binding prefix needs one source per thread configuration')
            seen.add(key)
            target = copy.deepcopy(original)
            target['id'] = f'{args.id_prefix}.t{key}'
            target['created'] = target['updated'] = writer.today()
            lineage = {'description': 'Derived from immutable target description ' + identifier,
                'target_description_sha256': artifacts.digest(original),
                'original_receipt_sha256': compact['receipt_sha256'], 'original_resolved_calibration_sources': resolved, 'timings_rerun': False}
            corrections = []
            for series in target['extensions']['cpu_calibration']['series']:
                if series['shape'].startswith('compute_'):
                    corrections.append({'shape': series['shape'], 'original_footprint_bytes': series.get('footprint_bytes'),
                        'original_scope': series.get('scope')})
                    series['requested_working_set_bytes'] = series.get('requested_working_set_bytes', series.get('footprint_bytes'))
                    series['footprint_bytes'] = 8 * key if series['shape'] == 'compute_atomic' else 0
                    series['scope'] = 'scalar state; no payload arrays; uncontended atomic uses one private 8-byte word per worker; logical footprint from shared source'
            lineage['compute_metadata_corrections'] = corrections
            if equivalence:
                lineage['original_compute_counts'] = _apply_equivalence(target, equivalence)
            source = attach(target, args.id_prefix, lineage, equivalence)
            targets.append(target); evidence.append(source)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
            raise Failure(f'invalid CPU calibration snapshot: {exc}') from None
    commit(args.records, targets, evidence, args.command)
    return {'descriptions': targets, 'calibrations': evidence}


def validate_record(record, ctx):
    from swdb.cpu_calibration import _validate_receipt, stats
    from swdb.problems import Problem
    data = record.data
    try:
        if data['identity_sha256'] != _identity(data):
            raise Failure('CPU calibration content differs from its immutable identity')
        if data['threads'] not in data['settings']['threads']:
            raise Failure('CPU calibration threads differ from its recorded matrix')
        receipt = {'format': 'swdb.cpu-calibration.v1', 'evidence_kind': data['evidence_kind'],
            'machine': data['target'], 'context': data['context'], 'compute_counts': data['compute_counts'],
            'settings': {**data['settings'], 'threads': [data['threads']]},
            'cells': [{**s, 'threads': data['threads']} for s in data['series']]}
        receipt['identity_sha256'] = artifacts.digest(receipt)
        _validate_receipt(receipt, fixture=data['evidence_kind'] == 'fixture')
        for series in data['series']:
            trials = series['trials']
            if series['seconds'] != stats([t['seconds'] for t in trials]):
                raise Failure('CPU calibration elapsed summary differs from its retained trials')
            for name in ('useful_bytes', 'helper_bytes'):
                if series[name + '_per_s'] != stats([t[name] / t['seconds'] for t in trials]):
                    raise Failure('CPU calibration byte-rate summary differs from its retained trials')
            category = series['shape'].removeprefix('compute_')
            count = data['compute_counts'].get(category)
            if series['shape'].startswith('compute_') and count:
                expected = stats([(count['per_iteration'] * t['iterations'] + count['per_invocation'] * data['threads']) / t['seconds'] for t in trials])
                if series['operations_per_s'] != expected:
                    raise Failure('CPU calibration compute-rate summary differs from its retained trials/counts')
    except (Failure, KeyError, TypeError, ValueError, OverflowError, AttributeError, IndexError) as exc:
        yield Problem(record.rel, 'identity_sha256', str(exc))

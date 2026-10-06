"""Independent native service receipts. Created: 2026-10-06 ET.

Paired elapsed subtraction retains all inputs; unresolved service work stays unknown.
"""
import copy
import math
from pathlib import Path

from yaml import YAMLError

from swdb import access, artifacts, paths, writer
from swdb.cli import Failure
from swdb.cpu_calibration import stats
from swdb.problems import Problem
from swdb.store import Record, Store, canonical_path


def identity(data):
    return artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})


def register_cli(commands):
    sub = commands.add_parser('import-cpu-service-calibration', help='retain independently timed native service costs and their paired driver inputs')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--receipt', type=Path, required=True)
    sub.add_argument('--id', required=True)
    sub.add_argument('--fixture', action='store_true')
    sub.add_argument('--format', choices=['yaml', 'json'], default='json')
    sub.set_defaults(cpu_service_calibration_handler=import_receipt)


def derive_service(service, record_id, evidence_kind, repetitions):
    trials = service['trials']
    if len(trials) != repetitions or not trials:
        raise Failure('service calibration repetitions differ')
    rates = []
    for trial in trials:
        n = trial['events']
        if type(n) is not int or n <= 0:
            raise Failure('service event denominator must be a positive integer')
        for key in ('gross_seconds', 'driver_seconds'):
            value = trial[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise Failure('paired service elapsed must be finite and nonnegative')
        rates.append((trial['gross_seconds'] - trial['driver_seconds']) / n)
    result = copy.deepcopy(service)
    result['seconds_per_event'] = stats(rates)
    resolved = all(value > 0 for value in rates)
    result['missing'] = [] if resolved else ['paired_driver_subtraction_resolution']
    result['parameter'] = {'value': result['seconds_per_event']['median'] if resolved else None,
        'basis': ('reported' if evidence_kind == 'fixture' else 'measured') if resolved else 'unknown',
        'source': f'Service calibration {record_id}; {service["id"]}; paired elapsed/work trials.',
        'unit': service['unit']}
    return result


def import_receipt(args):
    try:
        raw = access.read_record(args.receipt)
        if not isinstance(raw, dict) or raw.get('format') != 'swdb.cpu-service-calibration.v1' or raw.get('identity_sha256') != identity(raw):
            raise Failure('service calibration receipt identity/format differs')
        if raw['evidence_kind'] != 'fixture':
            raise Failure('native service import requires counted matching ABI/runtime evidence')
        if not args.fixture:
            raise Failure('service fixture requires --fixture; it is not native measurement')
        repetitions = raw['settings']['repetitions']
        if type(repetitions) is not int or not 3 <= repetitions <= 11:
            raise Failure('service repetitions must be between 3 and 11')
        data = {'kind': 'cpu_service_calibration', 'schema_version': '0.4', 'id': args.id,
            'status': 'draft', 'created': writer.today(), 'updated': writer.today(),
            'provenance': [{'id': 'cpu-service', 'kind': 'source_code',
                'description': 'Independent service/driver elapsed fixture; not application timing or CPU accuracy evidence.', 'uri': None}],
            'format': 'swdb.cpu-service-calibration-record.v1', 'backend': 'native',
            'evidence_kind': raw['evidence_kind'], 'receipt_sha256': raw['identity_sha256'],
            'target': raw['machine'], 'threads': raw['threads'],
            'context': copy.deepcopy(raw['context']), 'settings': copy.deepcopy(raw['settings']),
            'services': [derive_service(s, args.id, raw['evidence_kind'], repetitions) for s in raw['services']]}
        data['identity_sha256'] = identity(data)
        from swdb.archevolve import require_team_safe
        from swdb import workflow
        if workflow.CREATION_TAGS.get('mode') == 'extensa':
            raise Failure('CPU service calibration import requires team context')
        store = Store(args.records)
        store.add(Record(canonical_path(data['kind'], data['id']), data))
        require_team_safe(store, data, command='import-cpu-service-calibration')
        writer.commit(args.records, new=[data])
        return data
    except (OSError, ValueError, KeyError, TypeError, YAMLError) as exc:
        raise Failure(f'cannot import service calibration receipt: {exc}') from None


def validate_record(record, ctx):
    data = record.data
    if data.get('identity_sha256') != identity(data):
        yield Problem(record.rel, 'identity_sha256', 'service calibration content identity differs')
    try:
        for i, service in enumerate(data['services']):
            expected = derive_service(service, data['id'], data['evidence_kind'], data['settings']['repetitions'])
            if expected['seconds_per_event'] != service['seconds_per_event'] or expected['parameter'] != service['parameter'] or expected['missing'] != service.get('missing'):
                yield Problem(record.rel, f'services[{i}]', 'service cost/spread differs from paired elapsed/work inputs')
        if data['evidence_kind'] != 'fixture':
            yield Problem(record.rel, 'evidence_kind', 'native service import requires counted matching ABI/runtime evidence')
    except (Failure, ValueError, KeyError, TypeError) as exc:
        yield Problem(record.rel, 'services', str(exc))

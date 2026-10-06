"""Additional reported workload inputs; preserve counted facts. Created: 2026-10-06 ET."""
import copy
import re
from pathlib import Path

from swdb import access, analytic, artifacts, paths, writer
from swdb.cli import Failure
from swdb.store import Store


def register_cli(commands):
    sub = commands.add_parser('import-feature-report', help='attach a sanitized reported input to a new characterization; counted facts stay unchanged')
    sub.add_argument('--records', type=Path, default=paths.RECORDS)
    sub.add_argument('--report', type=Path, required=True)
    sub.add_argument('--characterization', required=True, help='existing characterization ID or YAML/JSON file')
    sub.add_argument('--id', required=True, help='new immutable characterization ID')
    sub.add_argument('--format', choices=['yaml', 'json'], default='yaml')
    sub.set_defaults(analytic_handler=import_report)


def _read(path):
    try:
        data = access.read_record(path)
    except (OSError, ValueError) as exc:
        raise Failure(f'cannot read feature input {path}: {exc}') from None
    if not isinstance(data, dict):
        raise Failure('feature input must be an object')
    try:
        artifacts.digest(data)
    except (ValueError, TypeError):
        raise Failure('feature input must contain finite JSON-compatible values') from None
    return data


def import_report(args):
    store = Store(args.records)
    original = analytic._load(store, args.characterization, 'workload_characterization')
    report = _read(args.report)
    if not isinstance(report.get('schema_version'), str) or not isinstance(report.get('kernel'), dict):
        raise Failure('feature report needs explicit schema_version and kernel scope')
    features = copy.deepcopy(report)
    redactions = []
    if 'hardware_performance_profile' in features:
        del features['hardware_performance_profile']
        redactions.append({'path': '/hardware_performance_profile', 'reason': 'PMU/performance outcomes are withheld from estimation inputs'})
    match = re.search(r'\.v([0-9]+\.[0-9]+)\.', args.report.name)
    filename_version = match.group(1) if match else None
    conflicts = []
    if filename_version and filename_version != report['schema_version']:
        conflicts.append({'kind': 'version_mismatch', 'path': '/schema_version',
            'reported': report['schema_version'], 'other': filename_version,
            'reason': 'Report content and filename declare different versions; neither is rewritten.'})
    supplied = {'basis': 'reported',
        'source_report': {'path': str(args.report.resolve()), 'sha256': access.record_hash(args.report),
            'filename_version': filename_version, 'schema_version': report['schema_version'],
            'sanitized_sha256': artifacts.digest(features)},
        'base_characterization': {'id': original['id'], 'sha256': artifacts.digest(original)},
        'features': features, 'conflicts': conflicts, 'redactions': redactions}
    record = copy.deepcopy(original)
    record['id'] = args.id
    record['created'] = record['updated'] = writer.today()
    record.setdefault('reported_inputs', []).append(supplied)
    record['provenance'].append({'id': 'feature-report.' + str(len(record['reported_inputs'])),
        'kind': 'human_report', 'description': 'Additional reported feature input; counted evidence retained unchanged.', 'uri': None})
    record.pop('identity_sha256', None)
    record['identity_sha256'] = artifacts.digest(record)
    writer.commit(args.records, new=[record])
    return record

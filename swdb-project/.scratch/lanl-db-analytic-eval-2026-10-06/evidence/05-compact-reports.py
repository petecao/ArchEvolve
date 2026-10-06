#!/usr/bin/env python3
"""Read-only compact application reports; keep null unknowns. Updated: 2026-10-06 ET."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from swdb import access


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counted(region):
    return any(fact['value'] for fact in region['operation_counts'].values()) or any(
        access['element_count']['value'] for access in region['access_patterns']) or bool(
        region['dynamic_counts']['loop_iterations']['value'])


def inventory(calls):
    groups = defaultdict(list)
    for call in calls:
        if call['execution_count']['value'] == 0:
            continue
        groups[(call['name'], call.get('event', 'external_call'), call.get('body_counted', False), call.get('cost_accounting','opaque_callee'), call['region'])].append(call)
    result = []
    for (name, event, body_counted, accounting, region), rows in sorted(groups.items()):
        counts = [row['execution_count']['value'] for row in rows]
        sizes = [row['size_bytes']['value'] for row in rows]
        result.append({'name': name, 'event': event, 'body_counted': body_counted, 'cost_accounting': accounting,
            'execution_count': None if any(n is None for n in counts) else sum(counts),
            'size_bytes': None if any(n is None for n in sizes) else sum(sizes),
            'known_size_bytes_partial': sum(n for n in sizes if n is not None),
            'unknown_size_sites': sum(n is None for n in sizes),
            'region': region, 'sites': [{'site': row.get('site'), 'line': row.get('line'), 'cost_accounting': row.get('cost_accounting','opaque_callee'),
                'execution_count': row['execution_count']['value'], 'size_bytes': row['size_bytes']['value']} for row in rows]})
    return result


def compact(value):
    if isinstance(value, dict):
        if 'value' in value and 'basis' in value:
            return {key: value[key] for key in ('value', 'basis', 'unit', 'scope', 'formula') if key in value}
        return {key: compact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [compact(item) for item in value]
    return value


def region_report(region):
    return {'id': region['id'], 'seconds': region['seconds'], 'state': region['state'],
        'limiting_bound': region['limiting_bound'], 'bounds': [
            {'model': bound['model'], 'seconds': bound['seconds'], 'state': bound['state'],
                'formula': bound['formula'], 'inputs': compact(bound['inputs']),
                'missing': bound['missing'], 'notes': bound.get('notes', [])}
            for bound in region['bounds']]}


def read_record(path):
    # JSON scientific notation has JSON numeric semantics, even where YAML 1.1
    # would parse a coefficient such as 1e-09 as text. All reads use the boundary.
    return json.loads(access.read_record_bytes(path)) if path.suffix == '.json' else access.read_record(path)


def application(characterization_path, estimate_path):
    source = read_record(characterization_path)
    estimated = read_record(estimate_path)
    if estimated['characterization'] != source['id']:
        raise ValueError('estimate refers to a different characterization')
    if source['binding']['state'] != 'verified' or source['evidence_kind'] != 'execution':
        raise ValueError('receipt requires registered application execution evidence')
    # Full static inventories remain at the raw path. Every observed region and every
    # zero-only ID is represented, with unmapped loops retained independently.
    observed = {region['id'] for region in source['regions'] if counted(region)}
    trials = source.get('trials', [])
    for trial in trials:
        observed.update(region['id'] for region in trial['regions'])
        observed.update(call['region'] for call in trial['unmodeled_calls'])
    rows = []
    for region in estimated['regions']:
        if region['id'] not in observed and region['seconds'] == 0:
            continue
        rows.append(region_report(region))
    selected = {row['id'] for row in rows}
    return {'subject': source['subject'], 'input': source['input'],
        'characterization': {'id': source['id'], 'file_sha256': digest(characterization_path),
            'identity_sha256': source['identity_sha256'], 'host': source['host'],
            'binding': source['binding'], 'counting': source['counting'],
            'coverage': source['coverage'], 'pattern_comparison': source['pattern_comparison'],
            'unmapped_loops': source['unmapped_loops'], 'static_region_count': len(source['regions']),
            'trials': [{'position': trial['position'], 'sources': trial['sources'],
                'region_count': len(trial['regions']), 'executed_calls': inventory(trial['unmodeled_calls']),
                'workers': [{'id': region['id'], 'active_workers': region.get('active_workers'),
                    'worker_context': region.get('worker_context')} for region in trial['regions']]}
                for trial in trials]},
        'estimate': {'id': estimated['id'], 'file_sha256': digest(estimate_path),
            'protocol': estimated['protocol'], 'protocol_sha256': estimated.get('protocol_sha256'),
            'target_description': estimated['target_description'],
            'target_description_sha256': estimated['target_description_sha256'],
            'estimator_version': estimated['estimator_version'], 'estimator_sha256': estimated.get('estimator_sha256'),
            'threads': estimated['threads'],
            'seconds': estimated['seconds'], 'ratio': estimated['ratio'], 'summary': estimated.get('summary'),
            'regions': rows, 'zero_only_region_ids': [region['id'] for region in estimated['regions']
                if region['id'] not in selected],
            'trials': [{'position': trial['position'], 'sources': trial['sources'], 'seconds': trial['seconds'],
                'regions': [region_report(region) for region in trial['regions']]}
                for trial in estimated.get('trials', [])], 'notes': estimated['notes']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--characterization', action='append', required=True, type=Path)
    parser.add_argument('--estimate', action='append', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--validate-log', type=Path)
    args = parser.parse_args()
    if len(args.characterization) != len(args.estimate):
        parser.error('give one estimate path for each characterization path, in matching order')
    report = {'format': 'swdb.registered-application-reports.v1', 'updated': '2026-10-06 ET',
        'source_commit': args.source_commit, 'evidence_kind': 'native_counts_plus_analytic_estimates',
        'applications': [application(c, e) for c, e in zip(args.characterization, args.estimate)]}
    if args.validate_log:
        report['validation'] = {'file_sha256': digest(args.validate_log), 'output': args.validate_log.read_text()}
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()

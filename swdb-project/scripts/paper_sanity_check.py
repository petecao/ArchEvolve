#!/usr/bin/env python3
"""Read-only, reported-paper comparison. Created: 2026-10-06 ET.
Updated: 2026-10-09 ET (code review): the estimate's subject must resolve to the
cited kernel; input/configuration differences are required; a non-null ratio needs
a declared baseline-system difference, because estimator ratios compare two codes
on one target description, not the paper's baseline system.
"""
import argparse
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import access, artifacts

SUBJECT_FOLDERS = {'implementation': 'implementations', 'candidate': 'candidates'}
REQUIRED_DIFFERENCES = ('input', 'configuration')


def _subject_record(records, kind, rid):
    folder = SUBJECT_FOLDERS.get(kind)
    if folder is None or not isinstance(rid, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', rid):
        raise ValueError('estimate subject must be a registered implementation or candidate')
    path = records / folder / (rid + '.yaml')
    data = access.read_record(path) if path.is_file() else None
    if not isinstance(data, dict) or data.get('kind') != kind or data.get('id') != rid:
        raise ValueError('estimate subject record is unavailable: ' + kind + '/' + rid)
    return data


def subject_kernel(records, subject):
    """The kernel ID of an estimate's subject, through its implementation record."""
    data = _subject_record(records, subject.get('kind'), subject.get('id'))
    if data['kind'] == 'candidate':
        data = _subject_record(records, 'implementation', data.get('implementation'))
    return data.get('kernel')


def _differences(comparison, ratio):
    rows = comparison['differences']
    if not isinstance(rows, list) or any(not isinstance(row, dict) or any(
            not isinstance(row.get(field), str) or not row[field].strip() for field in ('dimension', 'paper', 'estimate'))
            for row in rows):
        raise ValueError('scope differences require dimension, paper and estimate text')
    required = REQUIRED_DIFFERENCES + (('baseline_system',) if ratio is not None else ())
    absent = [name for name in required if name not in {row['dimension'] for row in rows}]
    if absent:
        raise ValueError('comparison must list scope differences: ' + ', '.join(absent))
    return rows


def create_report(records, request):
    if request.get('identity_sha256') != artifacts.digest({key: value for key, value in request.items() if key != 'identity_sha256'}):
        raise ValueError('request seal changed')
    if request.get('format') != 'swdb.paper-sanity-request.v1':
        raise ValueError('unsupported paper request format')
    source = request['source']
    if not source.get('uri', '').startswith('https://') or not re.fullmatch('[0-9a-f]{64}', source.get('sha256', '')):
        raise ValueError('paper source requires an HTTPS citation and PDF hash')
    observations = request['observations']
    if not observations or len({row['kernel'] for row in observations}) != len(observations):
        raise ValueError('paper observations must be nonempty and unique by kernel')
    for observation in observations:
        if observation.get('basis') != 'reported' or observation.get('unit') != 'ratio':
            raise ValueError('paper number requires reported basis and ratio unit')
        if not isinstance(observation.get('locator'), str) or not observation['locator'].strip():
            raise ValueError('paper number requires a page/figure/table locator')
        if observation.get('approximate') is not True:
            raise ValueError('plot readings must be explicitly approximate')
        for field, positive in [('ratio', True), ('reading_uncertainty', False)]:
            number = observation.get(field)
            if type(number) not in (int, float) or not math.isfinite(number) or number < 0 or (positive and number == 0):
                raise ValueError('paper number requires finite ratio and explicit reading uncertainty')
        scope = observation['scope']
        if any(not scope.get(field) for field in ('input', 'cores', 'algorithm', 'configuration')):
            raise ValueError('paper number requires input, core count, algorithm, and configuration scope')
    comparisons = request['comparisons']
    if len({row['kernel'] for row in comparisons}) != len(comparisons) or any(row['kernel'] not in {observation['kernel'] for observation in observations} for row in comparisons):
        raise ValueError('comparison kernel must have exactly one cited observation')
    rows = []
    for observation in request['observations']:
        comparison = next((row for row in request['comparisons']
                           if row['kernel'] == observation['kernel']), None)
        estimate = None
        if comparison is not None:
            ref = comparison['estimate']
            candidates = [access.read_record(path) for path, _ in access.record_files(records / 'estimates')]
            matches = [data for data in candidates if data.get('id') == ref['id']]
            if len(matches) != 1 or artifacts.digest(matches[0]) != ref['sha256']:
                raise ValueError('estimate identity or content pin changed')
            estimate = matches[0]
            if estimate.get('kind') != 'estimate' or estimate.get('basis') != 'estimated':
                raise ValueError('comparison requires a canonical estimated record')
            if estimate.get('evidence_kind') != 'execution':
                raise ValueError('comparison requires an execution estimate, not fixture evidence')
            if subject_kernel(records, estimate['subject']) != observation['kernel']:
                raise ValueError('estimate subject kernel differs from the cited paper kernel')
        ratio = estimate.get('ratio') if estimate else None
        differences = _differences(comparison, ratio) if comparison else []
        rows.append({**observation, 'reported_ratio': observation['ratio'],
                     'paper_basis': observation['basis'], 'estimated_ratio': ratio,
                     'estimated_threads': estimate['target_description_snapshot']['threads'] if estimate else None,
                     'estimate': comparison['estimate'] if comparison else None,
                     'estimate_scope': {'subject': estimate['subject'], 'kernel': observation['kernel'],
                         'input': estimate['input'], 'target': estimate['target'],
                         'target_description': estimate['target_description'],
                         'baseline': estimate.get('baseline'),
                         'baseline_scope': None if ratio is None else 'same_target_description'} if estimate else None,
                     'comparison_state': 'incomparable' if ratio is None else 'weak_comparison',
                     'differences': differences,
                     'reason': 'Estimated ratio is unknown.' if estimate and ratio is None else
                               'No estimate supplied.' if estimate is None else
                               'Scopes differ, and the estimated ratio compares two codes on one target description; this is a weak comparison only.'})
    report = {'format': 'swdb.paper-sanity-report.v1', 'updated': request['updated'],
              'mode': 'weak_sanity_check', 'accuracy_validation': False,
              'request_sha256': request['identity_sha256'], 'source': request['source'], 'rows': rows}
    report['identity_sha256'] = artifacts.digest(report)
    return report


def markdown(report):
    lines = ['# Weak paper sanity check', '', 'Updated: ' + report['updated'], '',
             'This reported-paper comparison is a sanity check. It does not establish estimator accuracy.', '',
             '| Kernel | Reported ratio | Estimated ratio | Paper input | Paper cores / estimated software threads | Paper configuration | Scope / state |', '|---|---:|---:|---|---|---|---|']
    for row in report['rows']:
        ratio = 'unknown' if row['estimated_ratio'] is None else str(row['estimated_ratio'])
        threads = 'unknown' if row['estimated_threads'] is None else str(row['estimated_threads'])
        lines.append(f"| {row['label']} | {row['reported_ratio']} ± {row['reading_uncertainty']} (reported, approximate) | {ratio} | {row['scope']['input']} | {row['scope']['cores']} / {threads} | {row['scope']['configuration']} | {row['locator']}; {row['comparison_state']} |")
    for row in report['rows']:
        lines += ['', '## ' + row['label'], '', row['reason'], '',
                  'Paper scope: ' + json.dumps(row['scope'], ensure_ascii=False) + '.',
                  'Estimated software threads: ' + ('unknown' if row['estimated_threads'] is None else str(row['estimated_threads'])) + '.']
        scope = row.get('estimate_scope')
        if scope:
            lines.append(f"Estimate scope: subject {scope['subject']['kind']}/{scope['subject']['id']} (kernel {scope['kernel']}), "
                         f"input {scope['input']}, target {scope['target']}, description {scope['target_description']}.")
            if scope['baseline_scope']:
                lines.append('Estimated ratio baseline: ' + json.dumps(scope['baseline'], ensure_ascii=False)
                             + ' on the same target description, not the paper\'s baseline system.')
        for difference in row['differences']:
            lines.append(f"- {difference['dimension']}: paper {difference['paper']}; estimate {difference['estimate']}.")
    lines += ['', f"Source: [{report['source']['uri']}]({report['source']['uri']}); PDF SHA-256 `{report['source']['sha256']}`.",
              '', 'Bar-reading uncertainty describes manual plot resolution, not a statistical interval.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text())
        report = create_report(args.records, request)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
        (args.output / 'report.md').write_text(markdown(report))
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

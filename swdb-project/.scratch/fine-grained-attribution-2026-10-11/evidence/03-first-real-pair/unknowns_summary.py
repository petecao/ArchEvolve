"""Every missing piece of the two saved ticket 03 estimates. Created: 2026-10-12 ET (final review H2).

Deterministic: reads only the two saved estimate records and writes `unknowns-summary.json` beside
this file. Run from `swdb-project/`:

    python3 .scratch/fine-grained-attribution-2026-10-11/evidence/03-first-real-pair/unknowns_summary.py

Rule. An unknown region is one whose `seconds` is null. `missing_counts[item]` is the number of
unknown regions whose bounds or overheads name `item` in their `missing` list (top-level
`regions`; the script checks that every trial gives the same set and that the estimate's own
`parameter_report.structural_missing` lists the same items with the same region counts). Items
are grouped by prefix (`GROUPS`); groups are ordered by the most regions they reach on a side.
"""
import collections
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT))
from swdb import artifacts  # noqa: E402

ESTIMATES = {'baseline': 'fga03.t75-baseline.uniform22.t1.estimate.a2',
             'candidate': 'fga03.t75-candidate.uniform22.t1.estimate.a2'}
# (group, what it is, item prefixes or suffixes); the first match wins.
GROUPS = [
    ('characterization_allowlist', 'the description accepts only the four gapbs g16/g17 counts (risk B1)',
     ('suffix', '.characterization_allowlist')),
    ('openmp_projection', 'no exact OpenMP characterization/static-site projection for these counts',
     ('prefix', 'openmp.')),
    ('call_costs', 'opaque calls with no service rate in the description', ('prefix', 'call_cost.')),
    ('call_shape_bins', 'allocation and bulk-copy size bins with no constructed rate', ('prefix', 'call_shape.')),
    ('memory_scenario_cells', 'memory-scenario cells and access primitives with no constructed rate',
     ('prefix', 'memory_scenario.')),
]


def group_of(item):
    for name, _, (kind, text) in GROUPS:
        if (item.endswith(text) if kind == 'suffix' else item.startswith(text)):
            return name
    return 'other'


def unknown_missing(rows):
    """{region ID: set of missing items} over the unknown rows, in row order."""
    return {r['id']: {m for b in r['bounds'] + r['overheads'] for m in b['missing']}
            for r in rows if r['seconds'] is None}


def side_summary(data):
    unknown = unknown_missing(data['regions'])
    for trial in data.get('trials') or []:
        if unknown_missing(trial['regions']) != unknown:
            raise SystemExit(f'{data["id"]}: trial {trial["position"]} has other unknown regions or items')
    counts = collections.Counter(m for items in unknown.values() for m in items)
    structural = {row['missing']: len(row['regions']) for row in data['parameter_report']['structural_missing']}
    if structural != dict(counts):
        raise SystemExit(f'{data["id"]}: parameter_report.structural_missing differs from the regions\' missing items')
    groups = {}
    for region, items in unknown.items():
        for item in items:
            groups.setdefault(group_of(item), {'regions': set(), 'items': set()})
            groups[group_of(item)]['regions'].add(region)
            groups[group_of(item)]['items'].add(item)
    return {'estimate': data['id'], 'estimate_sha256': artifacts.digest(data), 'created': str(data['created']),
            'seconds': data['seconds'], 'input': data['input'], 'threads': data['threads'],
            'target_description_sha256': data['target_description_sha256'], 'protocol': data['protocol'],
            'estimator_sha256': data['estimator_sha256'],
            'regions': len(data['regions']), 'unknown_regions': len(unknown),
            'known_region_seconds_sum': sum(r['seconds'] for r in data['regions'] if r['seconds'] is not None),
            'unknown_region_ids': list(unknown),
            'missing_counts': dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            'groups': {name: {'regions': len(g['regions']), 'items': len(g['items'])} for name, g in sorted(groups.items())},
            'agrees_with_parameter_report': True, 'trials_agree': True}


def main():
    sides = {}
    for side, rid in ESTIMATES.items():
        with open(PROJECT / 'records' / 'estimates' / f'{rid}.yaml') as handle:
            data = yaml.load(handle, Loader=yaml.CSafeLoader)
        sides[side] = side_summary(data)
        del data
    reach = {name: max(s['groups'].get(name, {}).get('regions', 0) for s in sides.values())
             for name in {n for s in sides.values() for n in s['groups']}}
    described = {name: what for name, what, _ in GROUPS} | {'other': 'any other missing item'}
    items = {name: sorted({m for s in sides.values() for m in s['missing_counts'] if group_of(m) == name}) for name in reach}
    summary = {'format': 'fga03.unknowns-summary.v2',
               'generated_by': 'unknowns_summary.py beside this file (reads only the two saved estimate records)',
               'rule': ('missing_counts[item] = unknown regions (seconds null) whose bounds or overheads name the item; '
                        'checked against every trial and against parameter_report.structural_missing'),
               'groups': [{'group': name, 'what': described[name], 'max_regions_on_a_side': reach[name],
                           'items': items[name]} for name in sorted(reach, key=lambda n: (-reach[n], n))],
               'sides': sides}
    (HERE / 'unknowns-summary.json').write_text(json.dumps(summary, indent=1) + '\n')


if __name__ == '__main__':
    main()

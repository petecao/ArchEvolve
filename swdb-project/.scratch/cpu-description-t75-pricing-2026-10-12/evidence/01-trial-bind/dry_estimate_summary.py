"""C4 trial estimates without persisting them, then the unknowns summary. Created: 2026-10-12 ET.

Fallback for cpud ticket 01 when the scratch disk cannot hold two more committed estimates and
their sqlite rebuild (/data reached 0 bytes free at 03:38 ET, filled by another session). Runs the
exact `swdb estimate` code path (`swdb.analytic.estimate`: team-safe gate, protocol bind,
compose_estimate, finalize_estimate) and replaces only the final `writer.commit` with a capture,
so nothing is written to the store. The summary is the parameterized `unknowns_summary.py` rule,
including its trial and `parameter_report.structural_missing` cross-checks. Run from `swdb-project/`:

    python3 <this file> --records <scratch store> --target-description <id> \
      --side baseline=<characterization>,<protocol> --side candidate=<characterization>,<protocol> \
      --output <summary.json>
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT))
from swdb import analytic, artifacts, writer  # noqa: E402

spec = importlib.util.spec_from_file_location('cpud01_unknowns_summary', HERE / 'unknowns_summary.py')
summary_rule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary_rule)


def dry_estimate(records, characterization, target, protocol, estimate_id):
    captured = []
    real_commit = writer.commit
    writer.commit = lambda records_dir, new=(), replace=(), upsert=(): captured.extend(new) or []
    try:
        analytic.estimate(argparse.Namespace(records=records, characterization=characterization,
                                             target_description=target, protocol=protocol, id=estimate_id,
                                             baseline=None))
    finally:
        writer.commit = real_commit
    if len(captured) != 1:
        raise SystemExit(f'{estimate_id}: expected one captured estimate record, got {len(captured)}')
    return captured[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--target-description', required=True)
    parser.add_argument('--side', action='append', required=True, metavar='SIDE=CHARACTERIZATION,PROTOCOL')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--detail', type=Path, help='optional: unknown regions with each term that names a missing item')
    args = parser.parse_args()
    sides, timing, details = {}, {}, {}
    for item in args.side:
        side, rest = item.split('=', 1)
        characterization, protocol = rest.split(',', 1)
        start = time.monotonic()
        record = dry_estimate(args.records, characterization, args.target_description, protocol,
                              f'cpud01.t75-{side}.uniform22.t1.estimate.trial-dry-a1')
        sides[side] = summary_rule.side_summary(record)
        sides[side]['persisted'] = False
        details[side] = [{'region': r['id'], 'terms': [
            {'model': b.get('model'), 'state': b.get('state'), 'missing': b['missing'],
             'inputs': json.dumps(b.get('inputs'), default=str)[:20000]}
            for b in r['bounds'] + r['overheads'] if b['missing']]}
            for r in record['regions'] if r['seconds'] is None]
        timing[side] = round(time.monotonic() - start, 1)
        print(f'{side}: seconds={record["seconds"]} unknown={sides[side]["unknown_regions"]}/{sides[side]["regions"]} '
              f'in {timing[side]} s', file=sys.stderr, flush=True)
        del record
    reach = {name: max(s['groups'].get(name, {}).get('regions', 0) for s in sides.values())
             for name in {n for s in sides.values() for n in s['groups']}}
    described = {name: what for name, what, _ in summary_rule.GROUPS} | {'other': 'any other missing item'}
    items = {name: sorted({m for s in sides.values() for m in s['missing_counts'] if summary_rule.group_of(m) == name})
             for name in reach}
    summary = {'format': 'fga03.unknowns-summary.v2',
               'generated_by': ('cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind/dry_estimate_summary.py '
                                '(swdb estimate code path, writer.commit captured; estimates not persisted)'),
               'records': str(args.records), 'target_description': args.target_description,
               'note': 'C4 trial; scratch store, not committed; estimates computed in memory because /data was full',
               'rule': ('missing_counts[item] = unknown regions (seconds null) whose bounds or overheads name the item; '
                        'checked against every trial and against parameter_report.structural_missing'),
               'estimate_wall_s': timing,
               'groups': [{'group': name, 'what': described[name], 'max_regions_on_a_side': reach[name],
                           'items': items[name]} for name in sorted(reach, key=lambda n: (-reach[n], n))],
               'sides': sides}
    args.output.write_text(json.dumps(summary, indent=1) + '\n')
    if args.detail:
        args.detail.write_text(json.dumps(details, indent=1) + '\n')


if __name__ == '__main__':
    main()

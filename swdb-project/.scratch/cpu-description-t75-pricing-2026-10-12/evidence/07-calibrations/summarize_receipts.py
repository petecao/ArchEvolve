"""Compact per-service summary of ticket-07 receipts (raw output stays on mbit10).
Written 2026-10-12 ET. Usage: python3 summarize_receipts.py <raw root> <out.json>

Per service: trial count, events per trial, gross/event and paired (gross - driver)/event in ns
(median, min, max) and the paired spread (max - min) / median. Diagnostic only; the imported
records hold the authoritative derived values.
"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

RECEIPTS = ['memory-v2.elapsed', 'allocator-v2.elapsed', 'openmp-a2.elapsed', 'library-call-2.elapsed', 'bulk.a3.elapsed']


def stats(values):
    if not values:
        return None
    med = statistics.median(values)
    return {'median_ns': med * 1e9, 'min_ns': min(values) * 1e9, 'max_ns': max(values) * 1e9,
            'spread_over_median': (max(values) - min(values)) / med if med else None}


def main(root, out):
    root = Path(root)
    result = {'format': 'cpud07.receipt-summary.v1', 'raw_root': str(root), 'receipts': {}}
    for name in RECEIPTS:
        path = root / name / 'receipt.json'
        if not path.exists():
            result['receipts'][name] = None
            continue
        raw = json.loads(path.read_text())
        services = []
        for s in raw['services']:
            trials = s['trials']
            gross, paired = [], []
            for t in trials:
                events = t.get('events') or t.get('requests') or t.get('calls')
                if not events or 'gross_seconds' not in t:
                    continue
                gross.append(t['gross_seconds'] / events)
                if 'driver_seconds' in t:
                    paired.append((t['gross_seconds'] - t['driver_seconds']) / events)
            services.append({'id': s['id'], 'event_abi': s.get('scope', {}).get('event_abi'), 'trials': len(trials),
                             'events_per_trial': sorted({t.get('events') for t in trials if t.get('events')}),
                             'gross_per_event': stats(gross), 'paired_per_event': stats(paired),
                             'nonpositive_paired_trials': sum(1 for p in paired if p <= 0)})
        ctx = raw.get('context', {})
        result['receipts'][name] = {
            'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'identity_sha256': raw.get('identity_sha256'),
            'group': raw.get('settings', {}).get('group'), 'commit': ctx.get('commit'), 'dirty': ctx.get('dirty'),
            'lane': ctx.get('lane'), 'cpus': ctx.get('cpus'), 'start_load': (ctx.get('start_state') or {}).get('load'),
            'end_load': (ctx.get('end_state') or {}).get('load'), 'services': services}
    Path(out).write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

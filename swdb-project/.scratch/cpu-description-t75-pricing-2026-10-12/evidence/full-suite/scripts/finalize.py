"""finalize.py: merge rounds into one outcome per test id per side; classify head failures against base."""
import json, importlib.util, collections
R = '/data/yanruj/EvolveSWDB_runs/cpud-fullsuite-20261013'
spec = importlib.util.spec_from_file_location('st', f'{R}/status.py'); st = importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
hcol = [l.strip() for l in open(f'{R}/head/collected.txt') if l.strip()]
bcol = set(l.strip() for l in open(f'{R}/base/collected.txt') if l.strip())
def first(m):
    lines = [x for x in (m or '').strip().splitlines() if x.strip()]
    return lines[0][:200] if lines else ''
rows = {}
for t in hcol:
    rows[t] = {'head': st.h.get(t, 'not_run'), 'base': st.b.get(t, 'not_run') if t in bcol else 'absent_at_base',
               'head_message': first(st.hm.get(t)) if st.h.get(t) in ('failed', 'error') else ''}
cls = collections.defaultdict(list)
for t, r in rows.items():
    if r['head'] not in ('failed', 'error'): continue
    if r['base'] == 'passed': cls['introduced_candidate'].append(t)
    elif r['base'] in ('failed', 'error'): cls['pre_existing'].append(t)
    elif r['base'] == 'absent_at_base': cls['new_test_failing'].append(t)
    else: cls['base_' + r['base']].append(t)
counts = collections.Counter(r['head'] for r in rows.values())
bcounts = collections.Counter(st.b.get(t, 'not_run') for t in bcol)
out = {'head_commit': '07b63e3ef018f623aa5549e2b833f2f07cb68d87', 'base_commit': 'e954e93846e8388a58c1294081b3d1deac78eb27',
       'head_counts': dict(counts), 'head_collected': len(hcol), 'base_counts': dict(bcounts), 'base_collected': len(bcol),
       'classification_counts': {k: len(v) for k, v in cls.items()}, 'classification': {k: sorted(v) for k, v in cls.items()},
       'tests': rows}
json.dump(out, open(f'{R}/classification.json', 'w'), indent=1, sort_keys=True)
print(json.dumps({k: out[k] for k in ('head_counts', 'head_collected', 'base_counts', 'base_collected', 'classification_counts')}))
for k in ('introduced_candidate', 'new_test_failing') + tuple(k for k in cls if k.startswith('base_')):
    for t in cls.get(k, []): print(k, t, '|', rows[t]['head_message'][:160])

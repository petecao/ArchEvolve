"""status.py [x]: per-side outcomes merged over rounds (later rounds win), and head-fail/base-pass candidates.
A candidate whose head failure is a FileExistsError under /data1/yanruj/EvolveSWDB_sources is a
snapshot-namespace collision (harness artifact) and is listed as COLL instead of CAND."""
import json, sys, os
R = '/data/yanruj/EvolveSWDB_runs/cpud-fullsuite-20261013'
def load1(p):
    out, msg = {}, {}
    for line in open(p):
        try: d = json.loads(line)
        except Exception: continue
        if d.get('$report_type') != 'TestReport': continue
        nid, when, oc = d['nodeid'], d['when'], d['outcome']
        prev = out.get(nid)
        if oc == 'failed':
            out[nid] = 'failed' if when == 'call' else 'error'
            lr = d.get('longrepr')
            msg[nid] = lr.get('reprcrash', {}).get('message', '') if isinstance(lr, dict) else str(lr)
        elif oc == 'skipped' and prev is None:
            out[nid] = 'skipped'
        elif oc == 'passed' and when == 'call' and prev is None:
            out[nid] = 'passed'
    return out, msg
def load(side):
    out, msg = {}, {}
    for rnd in (side, side + '-r2', side + '-r3', side + '-r4'):
        p = f'{R}/{rnd}/report.jsonl'
        if os.path.exists(p):
            o, m = load1(p)
            for k in o:
                out[k] = o[k]; msg.pop(k, None)
            msg.update(m)
    return out, msg
def coll(m):
    return 'FileExistsError' in m and 'EvolveSWDB_sources' in m
h, hm = load('head'); b, bm = load('base')
def cnt(d):
    c = {}
    for v in d.values(): c[v] = c.get(v, 0) + 1
    return c
if __name__ == '__main__':
    print('head', len(h), cnt(h), '| base', len(b), cnt(b))
    bad = sorted(k for k, v in h.items() if v in ('failed', 'error'))
    cand = [k for k in bad if b.get(k) == 'passed']
    real = [k for k in cand if not coll(hm.get(k, ''))]
    unk = [k for k in bad if k not in b]
    print('head bad', len(bad), 'head-coll', sum(coll(hm.get(k, '')) for k in bad), 'base-pass', len(real), 'coll-cand', len(cand) - len(real), 'base-unknown', len(unk))
    if len(sys.argv) > 1:
        for k in cand: print('COLL' if k not in real else 'CAND', k, '|', hm.get(k, '').strip().splitlines()[-1][:150] if hm.get(k) else '')

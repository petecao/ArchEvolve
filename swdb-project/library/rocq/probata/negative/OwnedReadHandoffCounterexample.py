"""2026-10-15 ET: finite witness for the superseded ffb5bda7 composition statement.
This is an executable model audit, not a Rocq proof of the universal negation.
The approved e23f3715 ownership-lifetime repair rejects this witness.
"""
from itertools import combinations
from collections import defaultdict
from dataclasses import dataclass
@dataclass(frozen=True)
class E:
    k:str
    l:int|None=None
    v:int|None=None
    c:int|None=None
A,B,T=0,1,2
tr0=[E('Barrier'),E('Own',A),E('DeviceRead',B,1,7),E('Enter'),E('Read',A,0),E('Write',A,1),E('Covered',c=7),E('Exit')]
tr1=[E('Own',A),E('Own',T),E('Enter'),E('DeviceRead',A,1,8),E('Read',T,0),E('DeviceWrite',T,1,8),E('Exit'),E('Barrier'),E('Covered',c=8),E('Shared',B,0)]
tr=[tr0,tr1]
X=[(0,tr0[0])]+[(1,e) for e in tr1[:8]]+[(0,e) for e in tr0[1:6]]+[(1,e) for e in tr1[8:]]+[(0,e) for e in tr0[6:]]
assert len(X)==18
cls=lambda interval,l:'shared' if l==B else 'owned'
def read(e):return (e.l,e.v) if e.k in ('Read','DeviceRead','Shared') else None
def written(e):
    if e.k in ('Write','DeviceWrite'):return e.l,e.v
    if e.k=='Shared':return e.l,e.v+1
    return None
def states(Y):
    intervals=[0,0];inside=[False,False];owned=[set(),set()];states=[]
    for t,e in Y:
        states.append((intervals.copy(),inside.copy(),[s.copy() for s in owned]))
        if e.k=='Own':owned[t].add(e.l)
        if e.k=='Barrier':intervals[t]+=1;owned[t]=set()
        if e.k=='Enter':inside[t]=True
        if e.k=='Exit':inside[t]=False
    return states
S=states(X)
assert [[e for t,e in X if t==u] for u in (0,1)]==tr
# All program prefixes fit. Thus class_fit holds for every program run, including
# every global prefix, independent of its rely premise.
for t,trace in enumerate(tr):
    for n in range(len(trace)+1):
        local=states([(t,e) for e in trace[:n]])
        for i,e in enumerate(trace[:n]):
            ints,ins,owns=local[i]
            if e.l is None or e.k=='Own':continue
            c=cls(ints[t],e.l)
            if c=='owned':assert e.l in owns[t]
            else:assert e.k in ('DeviceRead','Shared') and not ins[t]
# Own sites in different threads have disjoint intervals (the only common loc A).
ownsites=defaultdict(list)
for i,(t,e) in enumerate(X):
    if e.k=='Own':ownsites[e.l].append((t,S[i][0][t]))
for sites in ownsites.values():
    for t,k in sites:
        for u,h in sites:
            assert t==u or k!=h
# Both exact critical blocks implement the increment shared action on one loc.
for trace in tr:
    block=trace[trace.index(E('Enter'))+1:trace.index(E('Exit'))]
    writes=[written(e) for e in block if written(e) is not None]
    assert len(writes)==1
    l,v=writes[0]
    first=next(e for e in block if e.l==l)
    assert read(first)==(l,v-1) and all(e.k!='Barrier' for e in block)
# Same synchronization/control list, no worksharing iterations (chunk cover vacuous).
assert [[e for e in trace if e.k=='Barrier'] for trace in tr]==[[E('Barrier')],[E('Barrier')]]
# Full quiet_ok checks: conflict, dead tile outputs, protected-read exclusion,
# class stability. Commands 7 and 8 are distinct and all classes are constant.
for t,trace in enumerate(tr):
    local=states([(t,e) for e in trace])
    for p,d in enumerate(trace):
        if d.k not in ('DeviceRead','DeviceWrite'):continue
        for q,e in enumerate(trace[p+1:],p+1):
            conflict=(d.l==e.l and ((d.k=='DeviceRead' and e.k in ('Write','Shared')) or (d.k=='DeviceWrite' and e.k in ('Read','Write','Shared'))))
            if conflict:assert any(v.k=='Covered' and v.c==d.c for v in trace[p+1:q])
            if d.k=='DeviceRead' and not any(v.k=='Covered' and v.c==d.c for v in trace[p+1:q]):
                assert cls(local[p][0][t],d.l)==cls(local[q][0][t],d.l)
    for c in (7,8):
        crosses=False
        for p,d in enumerate(trace):
            if d.k not in ('DeviceRead','DeviceWrite') or d.c!=c:continue
            for q,e in enumerate(trace[p+1:],p+1):
                sync=e.k=='Barrier' or (e.k=='Exit' and local[p][1][t])
                crosses |= sync and not any(v.k=='Covered' and v.c==c for v in trace[p+1:q])
        if crosses:
            outs=[(p,d) for p,d in enumerate(trace) if d.k=='DeviceWrite' and d.c==c]
            assert outs
            for p,d in outs:
                assert d.l==T
                for q,e in enumerate(trace[p+1:],p+1):
                    if read(e) is not None and e.l==d.l:
                        assert any(v.k=='DeviceWrite' and v.l==d.l and v.c!=c for v in trace[p+1:q])
            assert all(cls(local[p][0][t],d.l)!='locked' for p,d in enumerate(trace) if d.k=='DeviceRead' and d.c==c)
# Current X satisfies omp bracket, mutual exclusion, barrier waiting and ids.
active=None
for i,(t,e) in enumerate(X):
    if e.k=='Enter':assert active is None;active=t
    if e.k=='Exit':assert active==t;active=None
    for u in (0,1):
        for k in range(S[i][0][t]):
            assert any(j<i and v==u and d.k=='Barrier' and S[j][0][u]==k for j,(v,d) in enumerate(X))
# Exact source map, memory/hb read ages, device source and covering constraints.
W={i:written(e) for i,(t,e) in enumerate(X) if written(e) is not None}
rf={i:next((s for s,w in W.items() if w==read(e)),None) for i,(t,e) in enumerate(X) if read(e) is not None}
# Value0 always initial; the unique value1 sources are after issue, before cover.
hb={(i,j) for i,(t,e) in enumerate(X) for j,(u,d) in enumerate(X) if i<j and (t==u or (e.k=='Exit' and d.k=='Enter') or (e.k=='Barrier' and S[i][0][t]<S[j][0][u]))}
for _ in X:
    hb|={(i,k) for i,j in hb for h,k in hb if j==h}
for j,(t,e) in enumerate(X):
    if read(e) is None:continue
    s=rf[j]
    if s is None:assert e.v==0
    else:assert W[s]==read(e)
    if e.k in ('Read','Shared'):
        assert s is None or s<j
    if e.k=='Shared':
        assert not any(i<j and w[0]==e.l and (s is None or i>s) for i,w in W.items())
    else:
        for i,w in W.items():
            if w[0]!=e.l:continue
            seen=(i,j) in hb
            for r,(u,d) in enumerate(X[:j]):
                seen |= u==t and read(d) is not None and d.l==e.l and rf.get(r) is not None and i<=rf[r]
            if seen:assert s is not None and i<=s
    if e.k=='DeviceRead' and s is not None and j<s:
        assert X[s][0]!=t
        assert not any(u==t and d.k=='Covered' and d.c==e.c for u,d in X[j+1:s+1])
# Every full shuffle preserves the exact per-thread traces. Since each desired
# value1 has a unique source, rf' cannot evade the source/cover cycle.
serial=0;with_device=0;total=0
for zeroes in combinations(range(18),8):
    total+=1;zeroes=set(zeroes);idx=[0,0];Y=[]
    for i in range(18):
        t=0 if i in zeroes else 1;Y.append((t,tr[t][idx[t]]));idx[t]+=1
    contiguous=True
    for t in (0,1):
        ent=next(i for i,(u,e) in enumerate(Y) if u==t and e.k=='Enter')
        ex=next(i for i,(u,e) in enumerate(Y) if u==t and e.k=='Exit')
        contiguous &= all(u==t for u,e in Y[ent+1:ex])
    if not contiguous:continue
    serial+=1;valid=True
    for j,(t,e) in enumerate(Y):
        if e.k!='DeviceRead':continue
        ss=[i for i,(u,d) in enumerate(Y) if written(d)==read(e)]
        assert len(ss)==1;s=ss[0]
        if j<s:
            valid &= Y[s][0]!=t and not any(u==t and d.k=='Covered' and d.c==e.c for u,d in Y[j+1:s+1])
    with_device+=valid
assert total==43758 and with_device==0
# The repaired global ownership-lifetime predicate rejects exactly the old
# owner's uncovered read at 4 followed by the new owner's Own A at 9.
handoff_violations=[]
for i,(t,e) in enumerate(X):
    if e.k!='DeviceRead' or cls(S[i][0][t],e.l)!='owned':continue
    for j,(u,d) in enumerate(X[i+1:],i+1):
        if u!=t and d.k=='Own' and d.l==e.l:
            if not any(v==t and f.k=='Covered' and f.c==e.c for v,f in X[i+1:j]):
                handoff_violations.append((i,j))
assert handoff_violations==[(4,9)]
print({'checked_shuffles':total,'critical_contiguous_shuffles':serial,'device_valid_contiguous_shuffles':with_device,'repaired_handoff_violations':handoff_violations,'rf':rf,'X':X})

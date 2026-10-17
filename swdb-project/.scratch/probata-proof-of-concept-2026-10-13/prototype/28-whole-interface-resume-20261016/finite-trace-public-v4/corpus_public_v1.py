"""2026-10-16 ET. Closed finite public selectors; predictions are never proof inputs."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASIS=HERE.parent/'finite-event-plan-v1/corpus_v1.py'

def cases():
    raw=BASIS.read_bytes()
    expected=(HERE/'corpus-basis.sha256').read_text().strip()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('frozen corpus basis changed')
    spec=importlib.util.spec_from_file_location('_finite_literal_corpus',BASIS)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    out=m.cases();event=m.event;common=m.common;regs=m.regs;stream=m.stream
    def add(plan,context,prediction,reason,pair):
        out.append(dict(plan=plan,context=context,prediction=prediction,reason=reason,pair=pair))
    for bad in (False,True):
        p,c=common('pair_wrong_owner_negative' if bad else 'pair_owned_positive')
        if bad:c['tile_owners'][1]=1
        p['events']=[event('tile_write',tile='pair0',lane=0,value=9),event('tile_read',tile='pair0',lane=0,out='x'),event('assert_eq',result='x',value=9)]
        add(p,c,'predicted_invalid' if bad else 'predicted_valid','Both physical halves require the same issuing owner.','pair_ownership')
    p,c=common('command_wrong_owner_negative')
    p['events']=[event('cpu_write',1,object='a',lane=0,value=7),*regs(1),stream('stream_load','load',1,'a','t0')]
    add(p,c,'predicted_invalid','An issued command retains the destination tile owner check.','command_ownership')
    for command in (True,False):
        for wide in (True,False):
            name=('pair' if wide else 'u32')+('_command_half_' if command else '_cpu_half_read_')+('negative' if wide else 'positive')
            p,c=common(name,dtype=3 if wide else 0)
            p['events']=[event('tile_write',tile='half1',lane=0,value=11),event('cpu_write',object='a',lane=0,value=7),*regs(),stream('stream_load','first',tile='pair0' if wide else 't0')]
            if command:
                p['events'] += [stream('stream_load','second',0,'a','half1'),event('wait_tile',tile='half1')]
            else:p['events'] += [event('tile_read',tile='half1',lane=0,out='half'),event('assert_eq',result='half',value=11)]
            p['events'] += [event('wait_tile',tile='pair0' if wide else 't0')]
            # The second command is a4-byte operation on a second4-byte object.
            if command and wide:
                p['objects'][1]['dtype']=0
                p['events']=[e if not(e['kind']=='stream_load' and e.get('command')=='second') else stream('stream_load','second',0,'b','half1') for e in p['events']]
                p['events'].insert(1,event('cpu_write',object='b',lane=0,value=11))
            add(p,c,'predicted_invalid' if wide else 'predicted_valid','Second-half hazard and its exact4-byte counterpart; no cover is inserted.','pair_command' if command else 'pair_cpu_read')
    for suffix in ('relation_positive','always_one_negative','always_zero_negative','cpu_read_negative'):
        p,c=common('ready_'+suffix);p['schema']='owned-finite-dx100-event-plan-2'
        p['events']=[event('tile_write',tile='t0',lane=0,value=7),*regs(),stream('stream_store','store'),event('logical_ready_query',tile='t0',out='ready')]
        if suffix=='relation_positive':p['events'].append(event('observe_ready_store',ready='ready',command='store',object='a',lane=0,value=7))
        elif suffix=='cpu_read_negative':p['events'] += [event('cpu_read',object='a',lane=0,out='x'),event('assert_eq',result='x',value=7)]
        else:p['events'].append(event('assert_eq',result='ready',value=1 if suffix=='always_one_negative' else 0))
        p['events'].append(event('wait_tile',tile='t0'))
        add(p,c,'predicted_valid' if suffix=='relation_positive' else 'predicted_invalid','Logical readiness may choose0pending or1cover; this is absent the original header and has no fairness claim.','finite_ready')
    row=deepcopy(next(row for row in out if row['plan']['id']=='prior_cpu_store_visible_positive'))
    row['plan']['id']='prior_cpu_store_old_value_negative'
    next(e for e in row['plan']['events'] if e['kind']=='assert_eq')['value']=1
    row.update(prediction='predicted_invalid',reason='An older value before the completed pre-issue CPU write is excluded.',pair='visibility')
    out.append(row)
    assert len(out)==30 and len({row['plan']['id'] for row in out})==30
    return out

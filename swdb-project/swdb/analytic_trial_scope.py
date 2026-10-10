"""Infer legacy labels only inside a sealed registered trial window. 2026-10-06 ET.

The native ROI resets counters at begin and snapshots them at end. Older Python
producers put per_run labels on those per-trial source facts. This module copies
only a proved window; it never edits the observation or relaxes a service guard.
"""
import copy
from collections import defaultdict

from swdb import artifacts
from swdb.analytic_binding import verify_binding


def _number(fact, scope):
    value=fact.get('value')
    return type(value) is int and value>=0 and fact.get('scope')==scope


def _counts(trial):
    for region in trial['regions']:
        yield from region['operation_counts'].values()
        yield from region['dynamic_counts'].values()
        for access in region['access_patterns']:
            yield access['element_count']
            yield access['bytes_accessed']
    for call in trial['unmodeled_calls']:
        yield call['execution_count']


def _window(trial):
    """Exact scoped site/bin and source-access partition proof, without costs."""
    calls=trial['unmodeled_calls']
    if len({c['site'] for c in calls})!=len(calls):return None
    source={c['site']:c for c in calls}
    matched=set();site_totals=[]
    for region in trial['regions']:
        shape=region.get('call_shape_counts',{})
        memory=region.get('memory_service_counts',{})
        if shape.get('format')!='swdb.call-shape-counts.v1' or shape.get('scope')!='per_trial':return None
        if memory.get('format')!='swdb.memory-service-counts.v1' or memory.get('scope')!='per_trial':return None
        expected=defaultdict(int);observed=defaultdict(int)
        for access in region['access_patterns']:
            n=access['element_count']['value'];moved=access['bytes_accessed']['value'];width=access['element_bytes']
            if type(n) is not int or n<0 or type(moved) is not int or moved!=n*width:return None
            expected[access['update_kind'],width]+=n
        for kind,rows in memory['requests_by_update_kind'].items():
            for row in rows:
                if not _number(row['requests'],'per_trial'):return None
                observed[kind,row['element_bytes']]+=row['requests']['value']
        if {k:v for k,v in expected.items() if v}!={k:v for k,v in observed.items() if v}:return None
        seen=set()
        for row in shape['calls']:
            site=row['site'];count=row['execution_count']
            if site in seen or row.get('scope')!='per_trial' or not _number(count,'per_trial'):return None
            seen.add(site);n=count['value'];length_total=0
            for bins,unknown in [('known_length_bins','unknown_lengths'),('allocation_lifetime_size_bins','unknown_free_lifetimes')]:
                if not _number(row[unknown],'per_trial'):return None
                total=row[unknown]['value'];sizes=set()
                for item in row[bins]:
                    size=item['bytes'];fact=item['execution_count']
                    if type(size) is not int or size<0 or size in sizes or not _number(fact,'per_trial'):return None
                    sizes.add(size);total+=fact['value']
                    if bins=='known_length_bins':length_total+=size*fact['value']
                # Empty dimensions have no shape observation (e.g. scalar clock
                # calls). Nonempty dimensions must partition every execution.
                if total and total!=n:return None
            if not n:continue
            call=source.get(site)
            if call is None or site in matched or call['region']!=region['id']:return None
            if any(row.get(k,d)!=call.get(k,d) for k,d in [('name',None),('event','external_call'),('body_counted',False)]):return None
            if call['execution_count']['value']!=n:return None
            size=call.get('size_bytes',{}).get('value')
            if row['known_length_bins'] and row['unknown_lengths']['value']==0 and size!=length_total:return None
            matched.add(site);site_totals.append({'site':site,'execution_count':n,'shape_sha256':artifacts.digest(row)})
    return sorted(site_totals,key=lambda row:row['site']) if matched==set(source) else None


def reconcile_trial(characterization,trial,store):
    """Return (copied trial, inferred proof), or the untouched trial and None."""
    try:
        facts=list(_counts(trial))
        if not any(f.get('scope')=='per_run' for f in facts):return trial,None
        if any(f.get('scope') not in {'per_run','per_trial'} for f in facts):return trial,None
        if any(c.get('size_bytes',{}).get('scope') not in {None,'per_run','per_trial'} for c in trial['unmodeled_calls']):return trial,None
        binding=characterization['binding'];counting=characterization['counting']
        if binding.get('state')!='verified' or characterization.get('evidence_kind')!='execution':return trial,None
        receipt=binding.get('execution_receipt',{})
        if receipt.get('format')!='swdb.registered-count-receipt.v1' or counting.get('summary')!='per_trial_then_median_time' or counting.get('native_runs')!=1:return trial,None
        sequence=characterization['trials'];position=trial['position']
        if type(position) is not int or not 0<=position<len(sequence) or trial!=sequence[position]:return trial,None
        if verify_binding(characterization,store):return trial,None
        totals=_window(trial)
        if totals is None:return trial,None
        normalized=copy.deepcopy(trial)
        for fact in _counts(normalized):fact['scope']='per_trial'
        for call in normalized['unmodeled_calls']:call['size_bytes']['scope']='per_trial'
        proof={'format':'swdb.legacy-trial-scope-reconciliation.v1','basis':'inferred',
            'position':position,'roi':binding['roi'],'characterization_sha256':artifacts.digest(characterization),
            'counted_payload_sha256':receipt['counted_payload_sha256'],
            'runtime_source_sha256':receipt['runtime_source_sha256'],'scope':'per_trial',
            'fields':['operation_counts','dynamic_counts','access_element_count','access_bytes','call_execution_count','call_size_bytes'],
            'site_totals':totals,'source_access_partition':'exact_update_kind_and_element_width',
            'note':'Registered begin/reset/end trial window and exact scoped partitions establish scope; source values, original labels and immutable receipt remain unchanged.'}
        return normalized,proof
    except (KeyError,TypeError,ValueError,AttributeError):
        return trial,None

"""Exact static OpenMP ABI classes with explicit inferred legal T1 transfer.2026-10-06 ET."""
import math
from swdb.cpu_openmp_calibration import check_signature
from swdb.cpu_openmp_profiles import PROFILES, STATE, PROBE
from swdb.cpu_service_calibration import identity
from swdb.cli import Failure

ASSUMPTION={'regime':STATE,'transfer_basis':'inferred','probe_kind':PROBE,'dynamic_bounds':'unverified',
    'runtime_internal_state':'unverified','next_outcome_policy':'max_constructed_success_failure_median',
    'physical_instruction_latency':False,'physical_upper_bound':False}


def profile_indexes(signature):
    """Only supported literal ABI classes and source outlined/caller context."""
    if not isinstance(signature,dict) or not isinstance(signature.get('llvm_function'),str):return []
    result=[]
    outlined='.omp_outlined' in signature.get('llvm_function','')
    for profile in PROFILES:
        try:check_signature(signature,profile)
        except (Failure,KeyError,TypeError,ValueError,AttributeError):continue
        if (profile['context']=='serialized_team')!=outlined:continue
        result.append(profile['index'])
    return result


def cost(region,call,selection,mechanism,context):
    def unknown(reason):return None,['openmp.'+reason]
    if selection.get('scope_assumption')!=ASSUMPTION:return unknown('explicit_legal_probe_transfer')
    documents=mechanism.get('selector',{}).get('openmp_projections')
    if not isinstance(documents,list) or not documents:return unknown('exact_projection')
    selected=[d for d in documents if isinstance(d,dict) and isinstance(d.get('characterization'),dict) and d['characterization'].get('id')==context.get('characterization_id') and d['characterization'].get('sha256')==context.get('characterization_sha256')]
    if len(selected)!=1:return unknown('exact_characterization_projection')
    document=selected[0]
    if (document.get('format')!='swdb.openmp-call-projection.v1' or document.get('identity_sha256')!=identity(document) or
        document.get('all_source_json_sites_cross_checked') is not True):return unknown('sealed_projection')
    signatures=[c for c in document.get('calls',[]) if isinstance(c,dict) and c.get('site')==call.get('site') and c.get('region')==region['id'] and c.get('name')==call['name']]
    if len(signatures)!=1:return unknown('exact_static_site')
    indexes=profile_indexes(signatures[0])
    if not indexes:return unknown('unsupported_abi_class')
    rows=selection.get('abi_sites')
    if not isinstance(rows,list):return unknown('site_classes')
    selected=[r for r in rows if isinstance(r,dict) and r.get('characterization_sha256')==context.get('characterization_sha256') and r.get('site')==call.get('site') and r.get('region')==region['id']]
    if len(selected)!=1:return unknown('full_exact_site_class')
    row=selected[0]
    if set(row)!={'characterization_sha256','site','region','profile_indexes','parameter','source_parameters'} or row['profile_indexes']!=indexes:
        return unknown('exact_constructed_profiles')
    source=row['source_parameters']
    if not isinstance(source,list) or len(source)!=len(indexes) or any(not isinstance(p,dict) or set(p)!={'profile_index','parameter'} for p in source) or [p['profile_index'] for p in source]!=indexes:
        return unknown('exact_source_parameters')
    def rate(name):
        if not isinstance(name,str) or not name:return None
        from swdb.analytic_cpu_service import _rate
        return _rate(mechanism,name,'seconds/call')
    rates=[rate(p['parameter']) for p in source]
    if any(v is None or not math.isfinite(v) or v<=0 for v in rates):return unknown('all_constructed_return_costs')
    expected=max(rates);actual=rate(row['parameter'])
    if actual!=expected or (len(indexes)==1 and row['parameter']!=source[0]['parameter']) or (len(indexes)>1 and mechanism['parameters'].get(row['parameter'],{}).get('basis')!='inferred'):
        return unknown('exact_return_profile_maximum')
    value=call['execution_count']['value']*actual
    return (value,[]) if math.isfinite(value) else unknown('finite_full_site_cost')

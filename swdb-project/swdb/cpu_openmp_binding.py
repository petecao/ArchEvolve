"""Exact outcome-free ABI projection and typed probe binding.2026-10-06 ET."""
import copy,math
from swdb import access,artifacts
from swdb.cli import Failure
from swdb.cpu_service_calibration import identity
from swdb.cpu_openmp_profiles import PROFILES
from swdb.analytic_cpu_openmp import ASSUMPTION,profile_indexes


def _executed(char):
    return {(c['site'],c['name'],c['region']) for part in [char,*char.get('trials',[])] for c in part.get('unmodeled_calls',[])
        if c.get('name','').startswith('__kmpc_') and c.get('body_counted') is not True and type(c.get('execution_count',{}).get('value')) is int and c['execution_count']['value']>0}


def binding(args,target,char,scopes,cells):
    from swdb.cpu_service_binding import _scope_compatibility
    if args.openmp_next_policy!='max_constructed_success_failure_median':raise Failure('OpenMP needs explicit constructed return-profile policy')
    documents=[access.read_record(p) for p in args.openmp_projection]
    if len(documents)!=len(scopes):raise Failure('OpenMP requires one exact projection per frozen characterization')
    paired={}
    for document in documents:
        if (document.get('format')!='swdb.openmp-call-projection.v1' or document.get('identity_sha256')!=identity(document) or
            document.get('all_source_json_sites_cross_checked') is not True):raise Failure('OpenMP sealed static projection missing')
        matching=[c for c in scopes if document.get('characterization',{}).get('id')==c['id'] and document['characterization'].get('sha256')==artifacts.digest(c)]
        if len(matching)!=1 or matching[0]['id'] in paired:raise Failure('OpenMP projection full characterization binding differs')
        selected=matching[0]
        if document.get('source_ir_sha256')!=selected.get('static_analysis',{}).get('source_ir_sha256'):raise Failure('OpenMP projection/count normalized source IR differs')
        signatures=document.get('calls',[])
        if (not isinstance(signatures,list) or len({(c['site'],c['name'],c['region']) for c in signatures})!=len(signatures) or
            {(c['site'],c['name'],c['region']) for c in signatures}!=_executed(selected)):
            raise Failure('OpenMP exact all-trial executed site union differs')
        if selected.get('evidence_kind')!='contract_fixture':
            receipt=document.get('receipt',{});native=selected.get('observation_contract',{}).get('native_runtime',{})
            if (receipt.get('compiler_sha256')!=native.get('compiler_sha256') or receipt.get('inputs_byte_identical_after_projection') is not True or
                receipt.get('application_execution') is not False):raise Failure('OpenMP projection native compiler/input scope differs')
        paired[selected['id']]=document
    parameters={};rows=[];profiles={}
    for calibration,service in cells:
        profile=service.get('scope',{}).get('abi_profile',{});index=profile.get('index')
        if type(index) is not int or not 0<=index<len(PROFILES) or profile!=PROFILES[index] or service['id']!=profile['id'] or index in profiles:
            raise Failure('OpenMP exact independent profile matrix differs or is duplicated')
        missing,scope_rows=_scope_compatibility(target,char,calibration,service,args.fixture,scopes)
        name='openmp_raw_'+str(index);fact=copy.deepcopy(service['parameter'])
        fact['source']+='; exact static ABI/ident class, explicitly inferred legal warmed serialized T1 transfer; application bounds/pointer/runtime internal state unverified'
        if missing:fact.update(value=None,basis='unknown')
        parameters[name]=fact;profiles[index]=name
        rows.append({'calibration':calibration['id'],'service':service['id'],'parameter':name,'missing':missing,'scopes':scope_rows})
    if set(profiles)!=set(range(22)):raise Failure('OpenMP full22-class independent matrix required')
    selectors={}
    for selected in scopes:
        document=paired[selected['id']];sha=document['characterization']['sha256']
        for signature in document['calls']:
            indexes=profile_indexes(signature)
            sources=[{'profile_index':index,'parameter':profiles[index]} for index in indexes]
            if len(indexes)==1:name=profiles[indexes[0]]
            else:
                name='openmp_envelope_'+str(len(parameters))
                facts=[parameters[profiles[index]] for index in indexes]
                known=bool(facts) and all(p['basis']!='unknown' and type(p['value']) in (int,float) and math.isfinite(p['value']) and p['value']>0 for p in facts)
                parameters[name]={'value':max(p['value'] for p in facts) if known else None,'basis':'inferred' if known else 'unknown','unit':'seconds/call',
                    'source':'Prospective maximum of separately retained constructed successful/terminal dispatch medians; actual return/state mix unverified, no physical upper bound.'}
            item=selectors.setdefault(signature['name'],{'name':signature['name'],'unit':'seconds/call','scope_assumption':copy.deepcopy(ASSUMPTION),'abi_sites':[]})
            item['abi_sites'].append({'characterization_sha256':sha,'site':signature['site'],'region':signature['region'],
                'profile_indexes':indexes,'parameter':name,'source_parameters':sources})
    return selectors,parameters,rows,documents

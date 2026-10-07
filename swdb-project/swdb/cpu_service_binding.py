"""Fresh typed CPU service bindings. Created: 2026-10-06 ET.

Standalone public module CLI keeps an active calibration runner immutable.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

from swdb import artifacts, paths, writer
from swdb.analytic import _load
from swdb.cli import Failure
from swdb.cpu_service_calibration import identity, validate_record
from swdb.store import Store, Record

ALLOCATOR_FIELDS={'_Znam':'known_length_bins','_Znwm':'known_length_bins',
                  '_ZdaPv':'allocation_lifetime_size_bins','_ZdlPv':'allocation_lifetime_size_bins'}


def _library_hashes(libraries, prefix):
    return {v.get('sha256') for k,v in libraries.items() if k.startswith(prefix)}


def _compatibility(target, char, calibration, service, fixture):
    missing=[]
    if target['target']!=calibration['target']:missing.append('service_target')
    if target['threads']!=1 or calibration['threads']!=1 or char.get('binding',{}).get('threads')!=1:
        missing.append('service_serial_T1')
    if calibration['evidence_kind']=='fixture':
        if not fixture:raise Failure('fixture service binding requires --fixture')
        if char.get('evidence_kind')!='contract_fixture':missing.append('fixture_native_mixing')
        return missing
    if char.get('evidence_kind')=='contract_fixture' and not fixture:
        raise Failure('fixture workload binding requires --fixture')
    native=char.get('observation_contract',{}).get('native_runtime',{})
    context=calibration['context']
    if native.get('compiler_version','').strip()!=context.get('compiler_version','').strip():
        missing.append('service_compiler_identity')
    if context.get('compiler_sha256') is not None and native.get('compiler_sha256')!=context['compiler_sha256']:
        missing.append('service_compiler_sha256')
    for prefix in ('libc.so','libstdc++'):
        observed=_library_hashes(native.get('loaded_libraries',{}),prefix)
        measured=_library_hashes(context.get('loaded_libraries',{}),prefix)
        if not observed or None in observed or observed!=measured:missing.append('service_runtime.'+prefix)
    declaration=native.get('environment_scope',{})
    actual=native.get('environment',{})
    measured=context.get('control_environment',context.get('allocator_environment',{}))
    from swdb.cpu_service_controls import valid
    measured_scope=valid(context) or context.get('allocator_environment_scope')=='GLIBC_TUNABLES,MALLOC_*,LD_PRELOAD,LD_AUDIT,library_search'
    interposers=('LD_PRELOAD','LD_AUDIT')
    if not measured_scope or not set(interposers)<=set(declaration.get('exact_variables',[])):
        missing.append('service_interposer_control_absence_scope')
    elif any(actual.get(k)!=measured.get(k) or actual.get(k) is not None for k in interposers):
        missing.append('service_interposer_controls_unsupported')
    if service.get('scope',{}).get('allocator_regime'):
        exact_controls=('GLIBC_TUNABLES','LD_PRELOAD','LD_AUDIT')
        declared=native.get('environment_scope',{})
        actual=native.get('environment',{})
        if 'MALLOC_' not in declared.get('prefixes',[]) or 'GLIBC_TUNABLES' not in declared.get('exact_variables',[]):
            missing.append('service_allocator_control_absence_scope')
        else:
            controls={k:v for k,v in actual.items() if k.startswith('MALLOC_') or k in exact_controls}
            measured={k:v for k,v in context.get('allocator_environment',{}).items() if k.startswith('MALLOC_') or k in exact_controls}
            if any(controls.get(k)!=v for k,v in measured.items()) or any(measured.get(k)!=v for k,v in controls.items()):
                missing.append('service_allocator_controls')
    return missing




def _scope_compatibility(target,char,calibration,service,fixture,scopes):
    values=[{'characterization':c['id'],'missing':_compatibility(target,c,calibration,service,fixture)} for c in scopes]
    missing=[reason if len(scopes)==1 else 'scope.'+row['characterization']+'.'+reason for row in values for reason in row['missing']]
    return missing,values

MEMORY_KINDS={'read':'read','write':'write','add-update':'add-update',
    'cas-success':'compare-and-swap','cas-failure':'compare-and-swap'}
CAS_POLICY='max_constructed_success_failure_median'
MEMORY_MODELS={'streaming_bandwidth','requests_in_flight_latency','cache_fit','memory_service_scenario'}


def _memory_binding(args,target,char,cells,scopes):
    footprint=args.memory_footprint_bytes
    if type(footprint) is not int or not 64<=footprint<=8388608 or footprint&(footprint-1):
        raise Failure('memory binding requires an explicit memory footprint power-of-two bin from64B to8MiB')
    if args.memory_cas_policy!=CAS_POLICY:
        raise Failure('memory binding requires the explicit constructed CAS success/failure median policy')
    selected={};parameters={};compatibility=[]
    for calibration,service in cells:
        scope=service.get('scope',{});op=scope.get('operation');width=scope.get('element_bytes');size=scope.get('footprint_bytes')
        if op not in MEMORY_KINDS or type(width) is not int or width not in (1,4,8) or type(size) is not int:
            raise Failure('unsupported constructed memory service cell')
        small=width==1
        regime='fixed_small_byte_read_constructed_requests' if small else 'resident_serial_constructed_requests'
        if scope.get('update_kind')!=MEMORY_KINDS[op] or scope.get('memory_regime')!=regime or scope.get('worker_scope')!='serial' or scope.get('transfer_basis')!='inferred' or (small and (op!='read' or size!=256)):
            raise Failure('unsupported memory construction regime/primitive/width')
        if not small and size!=footprint:continue
        key=(op,width)
        if key in selected:raise Failure('ambiguous duplicate constructed memory cell')
        missing,scope_rows=_scope_compatibility(target,char,calibration,service,args.fixture,scopes)
        name='memory_'+str(len(parameters));parameter=copy.deepcopy(service['parameter'])
        parameter['source']+='; context binding '+char['id']+'; constructed request transfer is inferred'
        if missing:parameter.update(value=None,basis='unknown')
        parameters[name]=parameter
        selected[key]={'parameter':name,'calibration':calibration['id'],'service':service['id'],'footprint_bytes':size,'regime':regime,
            'cost_basis':service.get('cost_basis','paired_driver_subtraction')}
        compatibility.append({'calibration':calibration['id'],'service':service['id'],'parameter':name,'missing':missing,'scopes':scope_rows})
    if not selected:raise Failure('selected memory footprint has no measured/reported cells')
    requests=[]
    for (op,width),cell in sorted(selected.items()):
        if op=='cas-failure':continue
        source_services=[{k:cell[k] for k in ('calibration','service','parameter')}]
        parameter=cell['parameter'];construction={'regime':cell['regime'],'footprint_bytes':cell['footprint_bytes'],
            'transfer_basis':'inferred','source_services':source_services,'physical_cache_level':'unverified','cost_basis':cell['cost_basis']}
        if op=='cas-success':
            other=selected.get(('cas-failure',width))
            if not other:raise Failure('constructed CAS binding needs both independent success and failure cells')
            if other['cost_basis']!=cell['cost_basis']:raise Failure('constructed CAS cells must share a resource recipe')
            source_services.append({k:other[k] for k in ('calibration','service','parameter')})
            rates=[parameters[x['parameter']] for x in (cell,other)]
            known=all(r.get('basis')!='unknown' and type(r.get('value')) in (int,float) and math.isfinite(r['value']) and r['value']>0 for r in rates)
            parameter='memory_cas_envelope_'+str(width)
            parameters[parameter]={'value':max(r['value'] for r in rates) if known else None,'basis':'inferred' if known else 'unknown',
                'unit':'seconds/request','source':'Maximum of the separately retained constructed success/failure medians; no application outcome mix or physical upper bound is established.'}
            construction['outcome_policy']=CAS_POLICY
            construction['primitive']='integer_strong_seq_cst_compare_exchange'
        else:construction['primitive']={'read':'ordinary_read','write':'ordinary_write','add-update':'integer_seq_cst_add'}[op]
        requests.append({'update_kind':MEMORY_KINDS[op],'element_bytes':width,'parameter':parameter,'construction':construction})
    if any(op=='cas-failure' and ('cas-success',width) not in selected for op,width in selected):
        raise Failure('constructed CAS binding needs both independent success and failure cells')
    mechanism={'model':'memory_service_scenario','accounting':'resource_bound','parameters':parameters,
        'selector':{'domain':'host','worker_scope':'serial_T1','scenario':'resident_serial_constructed_requests',
            'transfer_basis':'inferred','object_scope':'logical_requests_and_bounded_referent_views',
            'characterization_sha256':artifacts.digest(char),'requests':requests}}
    return mechanism,compatibility


def bind(args):
    from swdb.archevolve import require_team_safe
    from swdb import workflow
    if workflow.CREATION_TAGS.get('mode')=='extensa':raise Failure('CPU service binding requires team context')
    store=Store(args.records)
    target=_load(store,args.target_description,'target_description')
    char=_load(store,args.characterization,'workload_characterization')
    scope_ids=list(dict.fromkeys([args.characterization,*args.scope_characterization]))
    scopes=[char if identifier==args.characterization else _load(store,identifier,'workload_characterization') for identifier in scope_ids]
    allowlist=[{'id':c['id'],'sha256':artifacts.digest(c)} for c in scopes]
    if target.get('estimator_variant')!='team':raise Failure('CPU service binding requires team target description')
    require_team_safe(store,target,*scopes,*args.calibration,command='bind-cpu-services')
    result=copy.deepcopy(target)
    result.update(id=args.id,created=writer.today(),updated=writer.today())
    parameters={}; selectors={}; proofs=[]; rows=[]; memory_cells=[]
    for identifier in args.calibration:
        found=store.by_id.get(identifier)
        if found is None:
            from swdb import access
            kind=access.read_record(Path(identifier)).get('kind')
        else:kind=found.kind
        if kind not in ('cpu_service_calibration','cpu_memory_resource_calibration'):
            raise Failure('unsupported typed CPU service/resource calibration kind')
        calibration=_load(store,identifier,kind)
        if kind=='cpu_memory_resource_calibration':
            from swdb.cpu_memory_resource import validate_record as validate_resource
            problems=list(validate_resource(Record(Path(identifier),calibration),store))
        else:problems=list(validate_record(Record(Path(identifier),calibration),None))
        if problems:raise Failure('invalid service calibration: '+str(problems[0]))
        proofs.append({'id':identifier,'sha256':artifacts.digest(calibration)})
        for service in calibration['services']:
            missing,scope_rows=_scope_compatibility(target,char,calibration,service,args.fixture,scopes)
            scope=service.get('scope',{})
            if service.get('unit')=='seconds/request':
                memory_cells.append((calibration,service));continue
            proof=service.get('denominator',{}).get('proof',{})
            abi=scope.get('event_abi') or (proof.get('event_abi') if isinstance(proof,dict) else None)
            if service.get('unit')!='seconds/call':raise Failure('unsupported service binding unit')
            if not isinstance(abi,str) or not abi:raise Failure('service lacks an exact counted event ABI')
            param='service_'+str(len(parameters))
            value=copy.deepcopy(service['parameter'])
            value['source']+='; context binding '+char['id']+'; constructed work transfer, no physical issue-latency claim'
            if missing:value.update(value=None,basis='unknown')
            parameters[param]=value
            rows.append({'calibration':identifier,'service':service['id'],'parameter':param,'missing':missing,'scopes':scope_rows})
            if scope.get('allocator_regime'):
                if abi not in ALLOCATOR_FIELDS or type(scope.get('size_bytes')) is not int:
                    raise Failure('unsupported allocator service ABI/size')
                selection=selectors.setdefault(abi,{'name':abi,'unit':'seconds/call','bin_kind':ALLOCATOR_FIELDS[abi],
                    'bins':[],'scope_assumption':{'regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred'}})
                size=scope['size_bytes']
                if 'bins' not in selection or any(b['bytes']==size for b in selection['bins']):
                    raise Failure('ambiguous duplicate service ABI/size')
                selection['bins'].append({'bytes':size,'parameter':param})
            else:
                if abi in selectors:raise Failure('ambiguous duplicate scalar service ABI')
                selectors[abi]={'name':abi,'parameter':param,'unit':'seconds/call'}
    if not selectors and not memory_cells:raise Failure('binding needs at least one independently scoped service')
    removed=[]
    if memory_cells:
        if target.get('extensions',{}).get('cpu_services_binding'):raise Failure('bind memory services from an unbound immutable base description')
        memory,memory_rows=_memory_binding(args,target,char,memory_cells,scopes);rows.extend(memory_rows)
        removed=[m['model'] for m in result['mechanisms'] if m['model'] in MEMORY_MODELS]
        result['mechanisms']=[m for m in result['mechanisms'] if m['model'] not in MEMORY_MODELS]
    if selectors:result['mechanisms'].append({'model':'native_service_costs','accounting':'additive_overhead',
        'selector':{'domain':'host','worker_scope':'serial_T1','characterization_sha256':artifacts.digest(char),'calls':list(selectors.values())},'parameters':parameters})
    if memory_cells:result['mechanisms'].append(memory)
    if len(scopes)>1:
        for mechanism in result['mechanisms']:
            if mechanism['model'] in ('native_service_costs','memory_service_scenario'):
                mechanism['selector'].pop('characterization_sha256',None)
                mechanism['selector']['characterization_allowlist']=allowlist
    result['calibration_sources']=list(dict.fromkeys([*target['calibration_sources'],*args.calibration,*scope_ids]))
    evidence={'format':'swdb.cpu-services-binding.v1','base':{'id':target['id'],'sha256':artifacts.digest(target)},
        'characterization':{'id':char['id'],'sha256':artifacts.digest(char)},'characterization_allowlist':allowlist,'calibrations':proofs,'compatibility':rows,
        'models':[m['model'] for m in result['mechanisms'] if m['model'] in ('native_service_costs','memory_service_scenario')],
        'memory_selection':{'footprint_bytes':args.memory_footprint_bytes,'cas_policy':args.memory_cas_policy,'superseded_memory_models':removed} if memory_cells else None,
        'model':'native_service_costs','transfer_basis':'inferred','timings_rerun':False}
    result.setdefault('extensions',{})['cpu_services_binding']=evidence
    result['version']=artifacts.digest(evidence)
    writer.commit(args.records,new=[result])
    return result


def main():
    parser=argparse.ArgumentParser(description='derive fresh descriptions with typed independent CPU service dependencies')
    parser.add_argument('--records',type=Path,default=paths.RECORDS)
    parser.add_argument('--target-description',required=True)
    parser.add_argument('--characterization',required=True)
    parser.add_argument('--scope-characterization',action='append',default=[],help='additional immutable outcome-free count scope to freeze before any application timing')
    parser.add_argument('--calibration',action='append',required=True)
    parser.add_argument('--id',required=True)
    parser.add_argument('--fixture',action='store_true')
    parser.add_argument('--memory-footprint-bytes',type=int,help='explicit constructed 4/8B memory footprint; byte reads retain their separate256B scope')
    parser.add_argument('--memory-cas-policy',choices=[CAS_POLICY],help='explicit inferred transfer of the larger independent constructed success/failure median')
    parser.add_argument('--format',choices=['yaml','json'],default='json')
    args=parser.parse_args()
    try:
        result=bind(args)
        from swdb.cli import _emit
        _emit(result,args.format)
    except (Failure,KeyError,TypeError,ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())

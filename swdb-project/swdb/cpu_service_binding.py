"""Fresh typed CPU service bindings. Created: 2026-10-06 ET.

Standalone public module CLI keeps an active calibration runner immutable.
"""
import argparse
import copy
import json
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
        exact_controls=('GLIBC_TUNABLES','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH','DYLD_LIBRARY_PATH')
        declared=native.get('environment_scope',{})
        actual=native.get('environment',{})
        if 'MALLOC_' not in declared.get('prefixes',[]) or 'GLIBC_TUNABLES' not in declared.get('exact_variables',[]):
            missing.append('service_allocator_control_absence_scope')
        else:
            controls={k:v for k,v in actual.items() if k.startswith('MALLOC_') or k in exact_controls}
            measured=context.get('allocator_environment',{})
            if any(controls.get(k)!=v for k,v in measured.items()) or any(measured.get(k)!=v for k,v in controls.items()):
                missing.append('service_allocator_controls')
    return missing


def bind(args):
    from swdb.archevolve import require_team_safe
    from swdb import workflow
    if workflow.CREATION_TAGS.get('mode')=='extensa':raise Failure('CPU service binding requires team context')
    store=Store(args.records)
    target=_load(store,args.target_description,'target_description')
    char=_load(store,args.characterization,'workload_characterization')
    if target.get('estimator_variant')!='team':raise Failure('CPU service binding requires team target description')
    require_team_safe(store,target,char,*args.calibration,command='bind-cpu-services')
    result=copy.deepcopy(target)
    result.update(id=args.id,created=writer.today(),updated=writer.today())
    parameters={}; selectors={}; proofs=[]; rows=[]
    for identifier in args.calibration:
        calibration=_load(store,identifier,'cpu_service_calibration')
        problems=list(validate_record(Record(Path(identifier),calibration),None))
        if problems:raise Failure('invalid service calibration: '+str(problems[0]))
        proofs.append({'id':identifier,'sha256':artifacts.digest(calibration)})
        for service in calibration['services']:
            missing=_compatibility(target,char,calibration,service,args.fixture)
            scope=service.get('scope',{})
            proof=service.get('denominator',{}).get('proof',{})
            abi=scope.get('event_abi') or (proof.get('event_abi') if isinstance(proof,dict) else None)
            if service.get('unit')!='seconds/call':raise Failure('unsupported service binding unit')
            if not isinstance(abi,str) or not abi:raise Failure('service lacks an exact counted event ABI')
            param='service_'+str(len(parameters))
            value=copy.deepcopy(service['parameter'])
            value['source']+='; context binding '+char['id']+'; constructed work transfer, no physical issue-latency claim'
            if missing:value.update(value=None,basis='unknown')
            parameters[param]=value
            rows.append({'calibration':identifier,'service':service['id'],'parameter':param,'missing':missing})
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
    if not selectors:raise Failure('binding needs at least one independently scoped service')
    result['mechanisms'].append({'model':'native_service_costs','accounting':'additive_overhead',
        'selector':{'domain':'host','worker_scope':'serial_T1','characterization_sha256':artifacts.digest(char),'calls':list(selectors.values())},'parameters':parameters})
    result['calibration_sources']=list(dict.fromkeys([*target['calibration_sources'],*args.calibration,char['id']]))
    evidence={'format':'swdb.cpu-services-binding.v1','base':{'id':target['id'],'sha256':artifacts.digest(target)},
        'characterization':{'id':char['id'],'sha256':artifacts.digest(char)},'calibrations':proofs,'compatibility':rows,
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
    parser.add_argument('--calibration',action='append',required=True)
    parser.add_argument('--id',required=True)
    parser.add_argument('--fixture',action='store_true')
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

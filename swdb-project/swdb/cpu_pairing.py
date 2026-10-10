"""Prospective source-slot estimates beside native timing. Updated 2026-10-09 ET.

Updated 2026-10-09 23:10 ET (code review F9): unpaired states are validated too.

The native timer and correctness selector are unchanged. Admission is completed
before the first native invocation. Original advancing-driver error bands do not
transfer to the protected fresh-process driver.
"""
import copy
import math
import platform
import subprocess
import statistics

from swdb import artifacts
from swdb.cli import Failure


def unavailable():
    return {'format':'swdb.cpu-paired-estimate.v1','basis':'estimated','state':'unavailable',
        'seconds':None,'estimate':None,'native_timing_decides':True,
        'missing':['matched_counted_evaluator_scope'],
        'reason':'No counted source/input/runtime/protocol binding for this established native evaluator scope.'}


def paired_estimate(store,evaluation,request):
    if 'paired_estimate' in evaluation:
        return copy.deepcopy(evaluation['paired_estimate'])
    result=unavailable()
    if evaluation.get('mode')=='extensa':
        result.update(state='excluded',missing=['ArchEvolve_mode'],reason='Extensa timing is excluded from the team CPU error check.')
    elif request.get('analytic_estimate') is not None or request.get('analytic_estimates') is not None:
        result.update(state='excluded',missing=['requested_estimate_admission'],reason='Prospective matched estimate admission did not complete before native execution.')
    return result


def validate_record(record, ctx):
    """Check archived pairing pins without requiring today's estimator bundle.

    Fresh preparation checks the current executable/runtime. Archived validation
    checks recorded identities, so future model changes do not rewrite evidence.
    """
    from swdb.problems import Problem
    data=record.data;pair=data.get('paired_estimate',{})
    if not pair:return
    if pair.get('state')!='paired':
        # Code review 2026-10-09 ET (F9): an unpaired slot carries no prediction.
        if (pair.get('state') not in ('unavailable','excluded') or pair.get('seconds') is not None
                or pair.get('kernel_seconds') is not None or pair.get('estimate') is not None or 'slots' in pair):
            yield Problem(record.rel,'paired_estimate','an unavailable or excluded CPU paired estimate must carry no prediction')
        return
    try:
        context=data['context']['analytic_evaluator_scope']
        if pair['evaluation_scope_sha256']!=artifacts.digest(context):
            raise Failure('paired protected evaluator context differs')
        native=data['context'];request=data['request'];build=data['build']
        candidate=ctx.passed(data['candidate'],'candidate')
        if candidate is None or context['candidate']!=candidate['id'] or context['candidate_sha256']!=artifacts.digest(candidate) or context['source_root_sha256']!=candidate['artifact']['sha256'] or native['candidate_sha256']!=context['source_root_sha256']:
            raise Failure('paired actual evaluator candidate differs')
        for name in ('sources','repetitions','roi','threads','process_policy'):
            if native[name]!=context[name] or (name in request and request[name]!=context[name]):
                raise Failure('paired actual evaluator '+name+' differs')
        if data['machine']!=context['machine'] or request['machine']!=context['machine'] or request['candidate']!=context['candidate']:
            raise Failure('paired actual evaluator machine/source differs')
        if build['wrapper_sha256']!=context['timed_wrapper_sha256'] or build['template_sha256']!=context['driver_template_sha256'] or build['flags']!=context['build_flags'] or build.get('toolchain_flags',[])!=context['toolchain_flags'] or build.get('run_library_paths',[])!=context['run_library_paths']:
            raise Failure('paired actual evaluator build/driver differs')
        graph=native['workload']
        if graph['canonical_sha256']!=context['canonical_graph_sha256'] or any(graph[name]!=value for name,value in context['canonical_graph'].items()):
            raise Failure('paired actual evaluator graph differs')
        if context.get('format')=='swdb.protected-cpu-sg-scope.v1' and (graph.get('graph_input')!=context.get('graph_input') or native.get('evaluator')!=context.get('evaluator')):
            raise Failure('paired actual evaluator SG representation differs')
        expected={(r,p,s) for r in range(context['repetitions']) for p,s in enumerate(context['sources'])}
        observed=set();values=[];all_missing=set()
        for slot in pair['slots']:
            key=(slot['repetition'],slot['source_position'],slot['source'])
            if key in observed:raise Failure('paired duplicate source slot')
            observed.add(key);refs={}
            for field,kind in [('estimate','estimate'),('characterization','workload_characterization'),('protocol','protocol')]:
                pin=slot[field];dependency=ctx.passed(pin['id'],kind)
                if dependency is None or artifacts.digest(dependency)!=pin['sha256']:
                    raise Failure('paired immutable '+field+' reference differs')
                refs[field]=dependency
            char=refs['characterization'];estimate=refs['estimate'];protocol=refs['protocol']
            from swdb.analytic_cpu_binding import verify
            issues=verify(char,ctx.store)
            if issues:raise Failure('paired counted evaluator binding differs: '+'; '.join(issues))
            identity=char['binding']['subject_source_identity']
            if identity['evaluation_scope']!=context or identity['slot']!={'repetition':key[0],'source_position':key[1],'source':key[2]} or char['evidence_kind']!=data['evidence_kind']:
                raise Failure('paired counted source context differs')
            if slot['counted_payload_sha256']!=char['binding']['execution_receipt']['counted_payload_sha256'] or estimate['characterization']!=char['id'] or estimate['characterization_sha256']!=artifacts.digest(char):
                raise Failure('paired counted payload/estimate identity differs')
            target=protocol['settings']['target_description']['snapshot']
            if slot['target_description']!={'id':target['id'],'sha256':artifacts.digest(target)} or estimate['protocol']!=protocol['id'] or estimate['protocol_sha256']!=protocol['identity_sha256'] or estimate['target_description_sha256']!=artifacts.digest(target) or estimate['estimator_sha256']!=protocol['settings']['estimator_sha256'] or target['target']!=context['machine']:
                raise Failure('paired frozen target/protocol identity differs')
            runtime=slot['runtime_admission'];missing=runtime['missing']
            if not isinstance(missing,list) or any(not isinstance(reason,str) for reason in missing):
                raise Failure('paired runtime admission is malformed')
            if request.get('fixture') is True:
                if runtime.get('scope')!='contract_fixture_only' or runtime.get('accuracy_claim') is not False or runtime.get('counted')!=char.get('observation_contract',{}).get('native_runtime',{}) or missing:
                    raise Failure('paired fixture runtime admission differs')
            else:
                loaded=char.get('observation_contract',{}).get('native_runtime',{}).get('loaded_libraries',{})
                selected=lambda name:name.startswith(('libomp','libgomp','libstdc++','libc.so','libgcc_s','libm.so','libpthread','librt.'))
                counted={name:fact['sha256'] for name,fact in loaded.items() if selected(name)}
                if runtime.get('scope')!='protected_binary_preflight' or runtime.get('counted')!=counted:
                    raise Failure('paired archived runtime identity differs')
                required=not counted or counted!=runtime.get('resolved') or bool(char.get('observation_contract',{}).get('native_runtime',{}).get('missing'))
                if ('actual_native_runtime_identity' in missing)!=required:
                    raise Failure('paired archived runtime admission differs')
            value=None if missing else estimate['seconds'];values.append(value)
            if slot['kernel_seconds']!=value:raise Failure('paired semantic kernel prediction differs')
            expected_missing=set(missing)|{'uncalibrated_steady_clock_measurement_boundary'}
            if estimate['seconds'] is None:expected_missing.add('required_model_costs')
            if set(slot['missing'])!=expected_missing:raise Failure('paired prediction uncertainty differs')
            all_missing.update(expected_missing)
        if observed!=expected:raise Failure('paired prospective source-slot coverage differs')
        prediction=None if not values or any(value is None for value in values) else statistics.median(values)
        if pair['kernel_seconds']!=prediction or pair['missing']!=sorted(all_missing) or pair['estimate']!=(pair['slots'][0]['estimate'] if len(pair['slots'])==1 else None):
            raise Failure('paired aggregate semantic prediction differs')
    except (Failure,KeyError,TypeError,ValueError,AttributeError,OSError) as exc:
        yield Problem(record.rel,'paired_estimate',str(exc))


def runtime_admission(char,binary,fixture=False):
    """Retain counted facts while admitting only a proved current runtime relation."""
    native=char.get('observation_contract',{}).get('native_runtime',{})
    if fixture:
        return {'scope':'contract_fixture_only','observation_method':'counted_process_loaded_images',
            'counted':copy.deepcopy(native),'missing':[],'accuracy_claim':False}
    counted=native.get('loaded_libraries',{})
    selected=lambda name:name.startswith(('libomp','libgomp','libstdc++','libc.so','libgcc_s','libm.so','libpthread','librt.'))
    left={k:v['sha256'] for k,v in counted.items() if selected(k)}
    if platform.system()!='Linux':
        return {'scope':'protected_binary_preflight','observation_method':'unavailable_on_host_platform',
            'counted':left,'resolved':None,'missing':['actual_native_runtime_identity'],'accuracy_claim':False}
    from swdb.cpu_service_native import loaded_libraries
    def command(argv):
        completed=subprocess.run(list(map(str,argv)),capture_output=True,text=True,timeout=15)
        if completed.returncode:raise Failure('protected CPU runtime preflight failed')
        return completed
    try:
        observed=loaded_libraries(binary,command)
    except (Failure,OSError,subprocess.SubprocessError) as exc:
        return {'scope':'protected_binary_preflight','observation_method':'runtime_query_unavailable',
            'counted':left,'resolved':None,'missing':['actual_native_runtime_identity'],
            'accuracy_claim':False,'query_error':type(exc).__name__}
    right={k:v['sha256'] for k,v in observed.items() if selected(k)}
    missing=[]
    if not left or left!=right or native.get('missing'):
        missing.append('actual_native_runtime_identity')
    return {'scope':'protected_binary_preflight','observation_method':'Linux_ldd_resolved_current_file_hashes',
        'counted':left,'resolved':right,'missing':missing,
        'assumption':'Resolved library paths are unchanged when the already built protected binary executes.'}


def prepare(store,evaluation,request,context,binary):
    result=paired_estimate(store,evaluation,request)
    if evaluation.get('mode')=='extensa':return result
    from swdb import analytic_cpu_binding, analytic_estimate_binding, estimate_protocol
    from swdb.archevolve import require_team_safe
    from swdb.analytic import _payload_problems
    explicit=request.get('analytic_estimate') is not None or request.get('analytic_estimates') is not None
    try:
        rows=request.get('analytic_estimates')
        one=request.get('analytic_estimate')
        if rows is not None and one is not None:raise Failure('use one analytic_estimate or exact analytic_estimates slot table')
        expected=[(r,p,s) for r in range(request['repetitions']) for p,s in enumerate(request['sources'])]
        selected={}
        if one is not None:
            if len(expected)!=1 or not isinstance(one,str):raise Failure('analytic_estimate requires exactly one prospective source/repetition slot')
            selected[(0,0)]=one
        elif rows is not None:
            if not isinstance(rows,list) or any(not isinstance(row,dict) or set(row)!={'source_position','repetition','estimate'} for row in rows):
                raise Failure('analytic_estimates requires exact source_position/repetition/estimate rows')
            for row in rows:
                key=(row['repetition'],row['source_position'])
                if any(type(n) is not int for n in key) or key in selected or not isinstance(row['estimate'],str):
                    raise Failure('analytic_estimates contains duplicate or malformed slots')
                selected[key]=row['estimate']
            if set(selected)!={(r,p) for r,p,_ in expected}:raise Failure('analytic_estimates does not cover every prospective slot')
        else:
            for rec in store.of_kind('estimate'):
                estimate=rec.data;char=store.get(estimate['characterization'],'workload_characterization')
                identity=(char or {}).get('binding',{}).get('subject_source_identity',{})
                if identity.get('adapter') not in analytic_cpu_binding.ADAPTERS or identity.get('evaluation_scope_sha256')!=artifacts.digest(context):continue
                slot=identity.get('slot',{});key=(slot.get('repetition'),slot.get('source_position'))
                if key in selected:raise Failure('multiple persisted matched estimates require an explicit prospective selection')
                selected[key]=rec.id
            if not selected:return result
            if set(selected)!={(r,p) for r,p,_ in expected}:raise Failure('persisted matched estimates do not cover every prospective source slot')
        slots=[]
        for repetition,position,source in expected:
            rid=selected[(repetition,position)];estimate=store.get(rid,'estimate')
            if estimate is None:raise Failure('requested analytic estimate record is unavailable')
            require_team_safe(store,estimate,command='CPU paired estimate')
            char=store.get(estimate['characterization'],'workload_characterization')
            if char is None or artifacts.digest(char)!=estimate['characterization_sha256']:
                raise Failure('paired characterization identity differs')
            problems=list(_payload_problems(char))+list(_payload_problems(estimate))
            if problems:raise Failure('paired immutable estimate/count payload differs')
            problems=analytic_cpu_binding.verify(char,store)
            if problems:raise Failure('paired counted evaluator scope: '+'; '.join(problems))
            identity=char['binding']['subject_source_identity']
            if identity['evaluation_scope']!=context or identity['slot']!={'repetition':repetition,'source_position':position,'source':source}:
                raise Failure('paired protected evaluator source/input/process/build scope differs')
            if char['evidence_kind']!=evaluation['evidence_kind']:
                raise Failure('paired estimate execution/fixture evidence differs')
            protocol=store.get(estimate['protocol'],'protocol')
            if protocol is None:raise Failure('paired frozen estimate protocol is unavailable')
            target=protocol['settings']['target_description']['snapshot']
            if target['target']!=context['machine']:raise Failure('paired target machine differs from the protected evaluator')
            analytic_estimate_binding.admit(store,estimate,char,target)
            if estimate['protocol_sha256']!=protocol['identity_sha256'] or estimate['target_description_sha256']!=artifacts.digest(target) or estimate['estimator_sha256']!=estimate_protocol.estimator_identity():
                raise Failure('paired frozen model/protocol identity differs')
            runtime=runtime_admission(char,binary,request.get('fixture') is True)
            seconds=estimate['seconds'];missing=list(runtime['missing'])
            if seconds is None:missing.append('required_model_costs')
            elif type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
                raise Failure('paired estimate seconds are malformed')
            if missing:seconds=None
            kernel_seconds=seconds
            missing.append('uncalibrated_steady_clock_measurement_boundary')
            slots.append({'source_position':position,'repetition':repetition,'source':source,
                'estimate':{'id':rid,'sha256':artifacts.digest(estimate)},
                'characterization':{'id':char['id'],'sha256':artifacts.digest(char)},
                'counted_payload_sha256':char['binding']['execution_receipt']['counted_payload_sha256'],
                'protocol':{'id':protocol['id'],'sha256':artifacts.digest(protocol)},
                'target_description':{'id':target['id'],'sha256':artifacts.digest(target)},
                'seconds':None,'kernel_seconds':kernel_seconds,'missing':missing,'runtime_admission':runtime,
                'prediction_quantity':'semantic_kernel_call_seconds',
                'elapsed_interval_uncertainty':{'state':'unknown','seconds':None,'reason':'steady_clock boundary work is not independently calibrated; system_clock cost is not transferable.'},
                'error_band':None,'error_band_reason':'Original advancing-driver bands do not transfer to the protected fresh-process ROI.'})
        missing=sorted({name for slot in slots for name in slot['missing']})
        result.update(state='paired',seconds=None,
            kernel_seconds=None if any(s['kernel_seconds'] is None for s in slots) else statistics.median(s['kernel_seconds'] for s in slots),
            estimate=slots[0]['estimate'] if len(slots)==1 else None,slots=slots,missing=missing,
            evaluation_scope_sha256=artifacts.digest(context),prepared_before_native_timing=True,
            error_band=None,agreement_claim=False,
            reason='Prospective persisted estimates match every exact protected source slot; unsupported costs remain null and native timing decides.')
    except (Failure,KeyError,TypeError,ValueError,OSError) as exc:
        result.update(state='excluded' if explicit else 'unavailable',seconds=None,
            missing=['requested_estimate_admission' if explicit else 'matched_counted_evaluator_scope'],reason=str(exc))
    return result

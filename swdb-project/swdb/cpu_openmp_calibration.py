"""Bounded independently counted legal OpenMP event probes.2026-10-06 ET."""
import argparse
import copy
import json
import math
import os
import platform
import re
import shutil
import socket
import sys
import time
from pathlib import Path
from swdb import access, artifacts, paths
from swdb.cli import Failure
from swdb.cpu_calibration import _command, _host_state
from swdb.cpu_service_calibration import identity
from swdb.cpu_service_controls import snapshot
from swdb.cpu_service_native import prepare, loaded_libraries
from swdb.cpu_memory_calibration import budget, COUNT_CAP, TIMED_CAP, PIPELINE
from swdb.cpu_openmp_profiles import PROFILES, PROBE, STATE, EVENT_CAP
from swdb.extensa_boundary import closure
from swdb.store import Store

SOURCES=('CpuOpenmpWork.h','CpuOpenmpTimer.cpp','CpuOpenmpCount.cpp')
OMP_SCOPE={'prefixes':['OMP_','KMP_','GOMP_'],'absence_semantics':'null_or_absent_is_unset_under_declared_prefix_scope'}
REQUIRED={'OMP_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','OMP_PROC_BIND':'close','OMP_PLACES':'cores'}


def calibrate(args):
    if not args.llvm_bin:raise Failure('OpenMP event probes requireLLVM22 and an independent count matrix')
    if type(args.repetitions) is not int or not 3<=args.repetitions<=11 or not math.isfinite(args.min_trial_s) or not 0<args.min_trial_s<=.2 or not math.isfinite(args.max_wall_s) or not 0<args.max_wall_s<=900:
        raise Failure('OpenMP probe caps are3–11reps,.2s gross trials and900s wall')
    if any(not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in args.toolchain_flag):raise Failure('OpenMP flags may select headers/libraries only')
    environment={k:v for k,v in os.environ.items() if k.startswith(tuple(OMP_SCOPE['prefixes']))}
    if any(environment.get(k)!=v for k,v in REQUIRED.items()):raise Failure('OpenMP probes require exact serial controls '+str(REQUIRED))
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):raise Failure('OpenMP probes need a new external raw folder')
    native=prepare(args,output);deadline=time.monotonic()+args.max_wall_s
    def command(argv):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Failure('OpenMP probe wall budget reached')
        return _command(argv,timeout=remaining)
    git=['git','-C',paths.HOME.parent]
    if native:
        native.update(commit=command([*git,'rev-parse','HEAD']).stdout.strip(),dirty=bool(command([*git,'status','--porcelain']).stdout))
        if native['dirty']:raise Failure('native OpenMP source must be clean/committed')
    output.mkdir(parents=True)
    for name in SOURCES:shutil.copy2(Path(__file__).parent/'native'/name,output/name)
    compiler=args.llvm_bin/'clang++';flags=['-O3','-std=c++11','-fopenmp',*args.toolchain_flag];binary=output/'openmp-timer'
    built=command([compiler,*flags,output/SOURCES[1],'-o',binary]);(output/'build.stdout').write_text(built.stdout);(output/'build.stderr').write_text(built.stderr)
    command([compiler,*flags,'-S','-emit-llvm',output/SOURCES[1],'-o',output/'openmp-optimized.ll'])
    ir=(output/'openmp-optimized.ll').read_text();abis=sorted({p['name'] for p in PROFILES})
    if any(not re.search(r'call[^\n]*@'+abi+r'\(',ir) for abi in abis):raise Failure('optimized OpenMP ABI event elided')
    context={'compiler_version':command([compiler,'--version']).stdout.strip(),'compiler_sha256':artifacts.file_hash(compiler.resolve()),
        'flags':flags,'host':socket.gethostname(),'architecture':platform.machine(),'instrumented_timer':False,
        'source_sha256':{n:artifacts.file_hash(output/n) for n in SOURCES},'binary_sha256':artifacts.file_hash(binary),
        'optimized_work':{'ir_sha256':artifacts.file_hash(output/'openmp-optimized.ll'),'retained_abis':abis},
        'openmp_environment':environment,'openmp_environment_scope':copy.deepcopy(OMP_SCOPE),**snapshot()}
    counted=proof(args,output,command)
    def unchanged():
        if command([*git,'rev-parse','HEAD']).stdout.strip()!=native['commit'] or command([*git,'status','--porcelain']).stdout:raise Failure('native OpenMP source changed during collection')
    if native:unchanged();context.update(native,loaded_libraries=loaded_libraries(binary,command),end_state=_host_state())
    if args.count_only:
        raw={'format':'swdb.cpu-openmp-count-only.v1','evidence_kind':'fixture' if args.fixture else 'native_count_only',
            'timings_collected':False,'machine':args.machine,'threads':1,'context':context,'count_proof':counted,
            'budgets':{'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP}}
        raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()),timed=False)
        (output/'count-proof.json').write_text(payload)
        return {'count_proof':str(output/'count-proof.json'),'identity_sha256':raw['identity_sha256'],'timings_collected':False}
    services=[]
    for profile in PROFILES:
        op=profile['index']
        def timer(n,first):
            argv=[binary,op,n,int(first)]
            if native:argv=['taskset','-c',native['cpus'][0],*argv]
            trial=json.loads(command(argv).stdout)
            if trial['team_size']!=1 or trial['omp_active_level']!=0 or trial['omp_level']!=(0 if op<6 else 1):raise Failure('OpenMP live serialized-team context differs')
            if trial.get('event_return_sum')!=(n if profile['constructed_outcome']==1 else 0) or trial.get('driver_event_return_sum')!=trial.get('event_return_sum'):raise Failure('OpenMP event return outcome differs')
            if trial['checked_legal_sequences']!=n or trial['driver_checked_legal_sequences']!=n or trial['probe_kind']!=PROBE:raise Failure('OpenMP legal sequence/probe check differs')
            return trial
        n=1024
        while True:
            trial=timer(n,True);(output/f'pilot-openmp-{op}.json').write_text(json.dumps(trial))
            if min(trial['gross_seconds'],trial['driver_seconds'])>=args.min_trial_s*1.25:break
            if n==EVENT_CAP:raise Failure('OpenMP empty-window resolution unmet at event cap')
            n=min(n*2,EVENT_CAP)
        trials=[timer(n,i%2==0) for i in range(args.repetitions)]
        services.append({'id':profile['id'],'unit':'seconds/call',
            'event_definition':'One selected legal OpenMP ABI event; empty-window probe subtraction, setup/cleanup excluded; no physical latency or application-state proof.',
            'scope':{'event_abi':profile['name'],'worker_scope':'serial','openmp_regime':STATE,'abi_profile':copy.deepcopy(profile),
                'probe_kind':PROBE,'warm_sequences':16,'transfer_basis':'inferred','dynamic_bounds':'constructed0..31; application bounds unverified'},
            'denominator':{'level':'selected_source_normalized_event','basis':'measured','proof':counted},'trials':trials})
        (output/'partial-trials.json').write_text(json.dumps(services,indent=2));budget(output)
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture' if args.fixture else 'native','machine':args.machine,'threads':1,'context':context,
        'settings':{'group':'openmp_v1','repetitions':args.repetitions,'min_trial_s':args.min_trial_s,'max_wall_s':args.max_wall_s,
            'event_cap':EVENT_CAP,'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP,'requested_helper_payload_cap_bytes':4096},'services':services}
    if native:unchanged();context['end_state']=_host_state();validate(raw)
    raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()));(output/'receipt.json').write_text(payload)
    return {'receipt':str(output/'receipt.json'),'receipt_sha256':raw['identity_sha256'],'services':len(services),'evidence_kind':raw['evidence_kind']}


def proof(args,output,command):
    store=Store(args.records);seeds=['gapbs-bfs-do','kron-g16-k16'];copied=output/'count-records';copied.mkdir()
    for key in closure(store,seeds):
        relative=store.path_of(key);destination=copied/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(args.records)/relative))
    lines={i+1:int(m.group(1)) for i,line in enumerate((output/SOURCES[0]).read_text().splitlines()) if (m:=re.search(r'SWDB_OMP_EVENT (\d+)$',line))}
    if set(lines.values())!=set(range(22)):raise Failure('OpenMP source profile markers differ')
    points=[];static_projection=None
    for invoke in (True,False):
        for n in (3,5):
            key=str(int(invoke))+'.'+str(n);directory=output/('count-'+key)
            argv=[sys.executable,'-m','swdb','characterize','--records',copied,'--source',output/SOURCES[2],
                '--implementation',seeds[0],'--input',seeds[1],'--function','service_openmp_matrix','--threads','1','--fixture',
                '--counting-pipeline','source-normalized-v2','--id','calibration.openmp.'+key,'--roi','constructed-openmp-selected-event',
                '--llvm-bin',args.llvm_bin,'--output',directory,'--format','json','--timeout-s','90','--build-flag=-std=c++11','--build-flag=-fopenmp',
                '--run-arg='+str(n),'--run-arg='+str(int(invoke))]+['--toolchain-flag='+f for f in args.toolchain_flag]
            char=json.loads(command(argv).stdout)
            if {'version':char['counting']['pipeline_version'],'passes':char['counting']['passes']}!=PIPELINE:raise Failure('OpenMP count recipe differs')
            cells={i:0 for i in range(22)};sites={i:[] for i in cells};diagnostics=[]
            regions={r['id']:r['source_location'] for r in char['regions']}
            if static_projection is None:
                projection_output=directory/'abi-projection'
                projected=command([sys.executable,'-m','scripts.openmp_call_projection','--characterization',
                    copied/'workload_characterizations'/('calibration.openmp.'+key+'.yaml'),'--source-ir',directory/'normalized.bc',
                    '--source-map',directory/'source.json','--llvm-bin',args.llvm_bin,'--function','service_openmp_matrix','--output-directory',projection_output,
                    *['--toolchain-flag='+f for f in args.toolchain_flag]])
                static_projection=json.loads((projection_output/'projection.json').read_text())
            if static_projection['source_ir_sha256']!=artifacts.file_hash(directory/'normalized.bc'):
                raise Failure('OpenMP service/driver normalized event IR differs')
            projected_sites={c['site']:c for c in static_projection['calls']}
            for call in char['unmodeled_calls']:
                count=call['execution_count']['value'];index=lines.get(call.get('line'))
                location=regions.get(call.get('region'),{})
                if (index is not None and Path(location.get('path',''))==output/SOURCES[2] and location.get('function')=='service_openmp_matrix'):
                    if call['name']!=PROFILES[index]['name'] or type(count) is not int or count<0:raise Failure('selected OpenMP exact ABI/site differs')
                    signature=projected_sites.get(call['site'],{})
                    check_signature(signature,PROFILES[index])
                    if signature.get('source_location',{}).get('path')!=str(output/SOURCES[0]) or signature.get('llvm_function')!='service_openmp_matrix':raise Failure('OpenMP projected shared source path/context differs')
                    cells[index]+=count;sites[index].append(call['site'])
                elif count:diagnostics.append({'site':call['site'],'name':call['name'],'executions':count,'scope':'outside selected event; retained diagnostic'})
            rows=[{'index':i,'event_abi':p['name'],'executions':cells[i],'source_sites':sites[i]} for i,p in enumerate(PROFILES)]
            if any(c['executions']!=(n if invoke else 0) or len(c['source_sites'])!=1 for c in rows):raise Failure('OpenMP selected-event matrix differs: '+str(rows))
            points.append({'events':n,'invoke':invoke,'cells':rows,'outside_scope_diagnostics':diagnostics,
                'characterization_sha256':artifacts.digest(char),'normalized_ir_sha256':artifacts.file_hash(directory/'normalized.bc'),
                'source_map_sha256':artifacts.file_hash(directory/'source.json'),
                'operation_counts':{k:sum(r['operation_counts'][k]['value'] for r in char['regions']) for k in ('integer','floating_point','branch','atomic')}})
            budget(output)
    root=Path(__file__).parent
    return {'format':'swdb.cpu-openmp-count-proof.v1','pipeline':PIPELINE,'profiles':copy.deepcopy(PROFILES),'points':points,'static_projection':static_projection,
        'event_scope':'Only the shared selected event is in the counted ROI; legal prepare/cleanup and driver event remain outside, explicitly retained diagnostics.',
        'source_sha256':artifacts.file_hash(output/SOURCES[0]),'count_driver_sha256':artifacts.file_hash(output/SOURCES[2]),
        'plugin_source_sha256':artifacts.file_hash(root/'llvm/Characterize.cpp'),'runtime_source_sha256':artifacts.file_hash(root/'llvm/CountingRuntime.cpp')}


def check_signature(call,profile):
    if (call.get('name')!=profile['name'] or call.get('argument_count')!=profile['argument_count'] or
        call.get('ident_flags',{}).get('state')!='constant' or call['ident_flags'].get('bits')!=32 or
        call['ident_flags'].get('signed_decimal')!=str(profile['ident_flags'])):
        raise Failure('OpenMP exact ABI/ident class differs')
    operands={o['index']:o for o in call.get('operands',[])}
    for expected in profile['integer_constants']:
        observed=operands.get(expected['index'],{})
        if observed.get('kind')!='integer' or observed.get('state')!='constant' or any(observed.get(k)!=v for k,v in expected.items()):
            raise Failure('OpenMP literal ABI argument differs')
    return True


def validate(raw):
    from swdb.cpu_service_controls import valid
    c,s=raw['context'],raw['settings']
    def require(condition,reason):
        if not condition:raise Failure('native OpenMP: '+reason)
    def hashed(value):return bool(re.fullmatch('[0-9a-f]{64}',str(value)))
    require(raw.get('format')=='swdb.cpu-service-calibration.v1' and raw.get('evidence_kind')=='native' and s.get('group')=='openmp_v1','native receipt classification differs')
    require(raw['threads']==1 and c.get('system')=='Linux' and c.get('architecture')=='x86_64','Linux/x86 serial context differs')
    require(c.get('host','').split('.')[0]==raw['machine'] and c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}',str(c.get('commit'))),'clean source/host identity missing')
    require('(verified:' in str(c.get('lane')) and len(c.get('cpus',[]))==1 and type(c['cpus'][0]) is int,'verified physical core missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.',c.get('compiler_version','')),'uninstrumented LLVM22 missing')
    require(c['flags'][:3]==['-O3','-std=c++11','-fopenmp'] and all(f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in c['flags'][3:]),'compile recipe differs')
    require(7<=s['repetitions']<=11 and .05<=s['min_trial_s']<=.2 and 0<s['max_wall_s']<=900 and s['event_cap']==EVENT_CAP and s['count_build_cap_bytes']==COUNT_CAP and s['timed_data_cap_bytes']==TIMED_CAP and s['requested_helper_payload_cap_bytes']==4096,'caps/sampling differ')
    require(set(c['source_sha256'])==set(SOURCES) and all(hashed(v) for v in c['source_sha256'].values()) and all(hashed(c.get(k)) for k in ('compiler_sha256','binary_sha256','machine_sha256')),'source/compiler identities missing')
    libs=c.get('loaded_libraries',{})
    require(all(any(k.startswith(prefix) for k in libs) for prefix in ('libc.so','libstdc++','libomp')) and all(hashed(v.get('sha256')) for v in libs.values()),'actual C/C++/libomp hashes missing')
    require(valid(c) and c.get('openmp_environment_scope')==OMP_SCOPE and all(c.get('openmp_environment',{}).get(k)==v for k,v in REQUIRED.items()),'control/environment scope differs')
    require(c.get('optimized_work',{}).get('retained_abis')==sorted({p['name'] for p in PROFILES}) and hashed(c['optimized_work'].get('ir_sha256')),'optimized events elided')
    require(len(raw['services'])==22,'full prospective matrix missing')
    for profile,service in zip(PROFILES,raw['services']):
        scope=service['scope'];proof=service['denominator']['proof']
        require(service['id']==profile['id'] and service['unit']=='seconds/call' and scope=={'event_abi':profile['name'],'worker_scope':'serial','openmp_regime':STATE,'abi_profile':profile,'probe_kind':PROBE,'warm_sequences':16,'transfer_basis':'inferred','dynamic_bounds':'constructed0..31; application bounds unverified'},'ABI/probe/state construction differs')
        require(service['denominator']['level']=='selected_source_normalized_event' and service['denominator']['basis']=='measured' and proof['format']=='swdb.cpu-openmp-count-proof.v1' and proof['pipeline']==PIPELINE and proof['profiles']==PROFILES and proof['source_sha256']==c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256']==c['source_sha256'][SOURCES[2]],'count/timed event source differs')
        require(all(hashed(proof.get(k)) for k in ('plugin_source_sha256','runtime_source_sha256')) and len(proof['points'])==4 and {(p['events'],p['invoke']) for p in proof['points']}=={(n,b) for n in (3,5) for b in (True,False)},'numerator proof incomplete')
        projection=proof['static_projection']
        require(projection.get('format')=='swdb.openmp-call-projection.v1' and projection.get('identity_sha256')==identity(projection) and projection['characterization']['sha256']==proof['points'][0]['characterization_sha256'] and hashed(projection.get('source_ir_sha256')) and hashed(projection.get('source_json_sha256')),'static ABI projection identity differs')
        projected={call['site']:call for call in projection['calls']}
        require(len(projected)==22,'static exact event projection incomplete')
        for point in proof['points']:
            require(point['normalized_ir_sha256']==projection['source_ir_sha256'] and point['source_map_sha256']==projection['source_json_sha256'],'service/driver event IR or source map differs')
            require(all(hashed(point.get(k)) for k in ('characterization_sha256','normalized_ir_sha256','source_map_sha256')) and len(point['cells'])==22,'count artifact identity missing')
            for i,cell in enumerate(point['cells']):
                require(cell['index']==i and cell['event_abi']==PROFILES[i]['name'] and type(cell['executions']) is int and cell['executions']==(point['events'] if point['invoke'] else 0) and len(cell['source_sites'])==1,'selected event coefficient differs')
                signature=projected.get(cell['source_sites'][0],{})
                check_signature(signature,PROFILES[i])
                require(signature.get('llvm_function')=='service_openmp_matrix' and Path(signature.get('source_location',{}).get('path','')).name==SOURCES[0],'shared target source projection differs')
        require(len(service['trials'])==s['repetitions'],'repetitions differ')
        for i,t in enumerate(service['trials']):
            require(type(t['events']) is int and 0<t['events']<=EVENT_CAP and t['checked_legal_sequences']==t['events'] and t['driver_checked_legal_sequences']==t['events'] and t['team_size']==1 and t['omp_active_level']==0 and t['omp_level']==(0 if profile['index']<6 else 1) and t['probe_kind']==PROBE,'live event/sequence scope differs')
            require(t.get('event_return_sum')==(t['events'] if profile['constructed_outcome']==1 else 0) and t.get('driver_event_return_sum')==t.get('event_return_sum'),'live target/driver return outcome differs')
            require(t['order']==('service_first' if i%2==0 else 'driver_first') and all(type(t[k]) in (int,float) and math.isfinite(t[k]) and t[k]>=s['min_trial_s'] for k in ('gross_seconds','driver_seconds')),'paired ordering/resolution differs')


def main():
    p=argparse.ArgumentParser(description='legal OpenMP selected-event probes, no application timing')
    p.add_argument('--records',type=Path,default=paths.RECORDS);p.add_argument('--output',type=Path);p.add_argument('--validate-receipt',type=Path,help='check native classification, ABI count/probe/runtime admission without importing or timing')
    p.add_argument('--llvm-bin',type=Path);p.add_argument('--toolchain-flag',action='append',default=[])
    p.add_argument('--fixture',action='store_true');p.add_argument('--count-only',action='store_true')
    p.add_argument('--machine',default='mbit10');p.add_argument('--lane')
    p.add_argument('--repetitions',type=int,default=7);p.add_argument('--min-trial-s',type=float,default=.05);p.add_argument('--max-wall-s',type=float,default=900)
    args=p.parse_args()
    try:
        if args.validate_receipt:
            raw=access.read_record(args.validate_receipt)
            if raw.get('identity_sha256')!=identity(raw):raise Failure('OpenMP receipt identity differs')
            validate(raw);print(json.dumps({'valid':True,'identity_sha256':raw['identity_sha256'],'timings_collected':False}));return 0
        if args.output is None:raise Failure('--output is required for collection')
        print(json.dumps(calibrate(args)));return 0
    except (Failure,KeyError,TypeError,ValueError,OSError) as exc:print(str(exc),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

"""Independent floating64 monotonic atomic cells. Created:2026-10-06 ET.

Existing memory/byte/integer helpers and immutable receipts are untouched.
"""
import argparse,json,math,platform,re,shutil,socket,sys,time
from pathlib import Path
from swdb import access,artifacts,paths
from swdb.cli import Failure
from swdb.cpu_calibration import _command,_host_state
from swdb.cpu_memory_calibration import budget,COUNT_CAP,TIMED_CAP,EVENT_CAP,PIPELINE
from swdb.cpu_service_calibration import identity
from swdb.cpu_service_controls import snapshot,valid
from swdb.cpu_service_native import prepare,loaded_libraries
from swdb.extensa_boundary import closure
from swdb.store import Store

SOURCES=('CpuFloatMemoryWork.h','CpuFloatMemoryTimer.cpp','CpuFloatMemoryCount.cpp')
PRIMITIVE={'opcode':'atomicrmw','value_kind':'floating','element_bits':64,'update_opcode':'fadd','atomic_ordering':'monotonic'}


def proof(args,output,command):
    store=Store(args.records);seeds=['gapbs-bfs-do','kron-g16-k16']
    if any(store.get(k) is None for k in seeds):raise Failure('float count needs registered carrier/input')
    copied=output/'count-records';copied.mkdir()
    for key in closure(store,seeds):
        relative=store.path_of(key);destination=copied/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(args.records)/relative))
    points=[]
    for invoke in (True,False):
        for n in (3,5):
            key=f'{int(invoke)}.{n}'
            argv=[sys.executable,'-m','swdb','characterize','--records',copied,'--source',output/SOURCES[2],
                '--implementation',seeds[0],'--input',seeds[1],'--function','service_float_memory','--threads','1',
                '--fixture','--counting-pipeline','source-normalized-v2','--id','calibration.float.'+key,
                '--roi','constructed-floating-memory-service','--llvm-bin',args.llvm_bin,'--output',output/('count-'+key),
                '--format','json','--timeout-s','60','--build-flag=-std=c++11','--build-flag=-fopenmp',
                '--run-arg='+str(n),'--run-arg='+str(int(invoke))]
            argv+=['--toolchain-flag='+f for f in args.toolchain_flag]
            char=json.loads(command(argv).stdout);active=[];requests=0;atomic=0
            for region in char['regions']:
                atomic+=region['operation_counts']['atomic']['value']
                for access_row in region['access_patterns']:
                    count=access_row['element_count']['value']
                    if count:
                        p=access_row.get('primitive_semantics',{})
                        if ({k:p.get(k) for k in PRIMITIVE}!=PRIMITIVE or p.get('vector') is not False or p.get('volatile') is not False or p.get('weak') is not None or p.get('failure_ordering') is not None or access_row['element_bytes']!=8 or access_row['update_kind']!='add-update' or access_row['read_write'] is not True):raise Failure('float exact source primitive differs')
                        active.append(access_row['id']);requests+=count
            opaque=sum(c['execution_count']['value'] for c in char['unmodeled_calls'] if not c.get('body_counted') and c.get('cost_accounting')=='opaque_callee')
            recipe={'version':char['counting']['pipeline_version'],'passes':char['counting']['passes']}
            if requests!=(n if invoke else 0) or atomic!=requests or opaque or recipe!=PIPELINE:raise Failure('float source numerator/driver/recipe differs')
            points.append({'invoke':invoke,'events':n,'requests':requests,'atomic_events':atomic,'opaque_events':opaque,
                'primitive':dict(PRIMITIVE),'active_sites':active,'characterization_sha256':artifacts.digest(char)})
            budget(output)
    root=Path(__file__).parent
    return {'format':'swdb.cpu-float-memory-count-proof.v1','pipeline':PIPELINE,'points':points,
        'source_sha256':artifacts.file_hash(output/SOURCES[0]),'count_driver_sha256':artifacts.file_hash(output/SOURCES[2]),
        'plugin_source_sha256':artifacts.file_hash(root/'llvm/Characterize.cpp'),'runtime_source_sha256':artifacts.file_hash(root/'llvm/CountingRuntime.cpp')}


def calibrate(args):
    footprints=sorted(set(args.footprint_bytes or (32768,8388608)))
    if not footprints or len(footprints)>2 or any(type(f) is not int or not 64<=f<=8388608 or f&(f-1) for f in footprints):raise Failure('float footprints require at most2 power-of-two64B–8MiB bins')
    if not 3<=args.repetitions<=11 or not math.isfinite(args.max_wall_s) or not 0<args.max_wall_s<=900 or not math.isfinite(args.min_trial_s) or not 0<args.min_trial_s<=.2:raise Failure('float sampling caps differ')
    if not args.llvm_bin:raise Failure('float proof and elapsed require LLVM22')
    if any(not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in args.toolchain_flag):raise Failure('float flags may select headers/libraries only')
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):raise Failure('float needs new external output')
    native=prepare(args,output);deadline=time.monotonic()+args.max_wall_s
    def command(argv):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Failure('float wall budget reached')
        return _command(argv,timeout=remaining)
    git=['git','-C',paths.HOME.parent]
    if native:
        native.update(commit=command([*git,'rev-parse','HEAD']).stdout.strip(),dirty=bool(command([*git,'status','--porcelain']).stdout))
        if native['dirty']:raise Failure('float source must be committed clean')
    output.mkdir(parents=True)
    for name in SOURCES:shutil.copy2(Path(__file__).parent/'native'/name,output/name)
    compiler=args.llvm_bin/'clang++';flags=['-O3','-std=c++11','-fopenmp',*args.toolchain_flag]
    version=command([compiler,'--version']).stdout.strip()
    if not re.search(r'clang version 22\.',version):raise Failure('float requires LLVM22')
    binary=output/'float-timer';built=command([compiler,*flags,output/SOURCES[1],'-o',binary])
    (output/'build.stdout').write_text(built.stdout);(output/'build.stderr').write_text(built.stderr)
    ir=output/'float-optimized.ll';command([compiler,*flags,'-S','-emit-llvm',output/SOURCES[1],'-o',ir])
    body=re.search(r'define[^\n]*@service_float_memory\([^\n]*\).*?\n}',ir.read_text(),re.S)
    if not body or not re.search(r'atomicrmw fadd [^\n]*double 1\.000000e\+00 monotonic',body.group(0)):raise Failure('optimized float atomic primitive absent')
    counted=proof(args,output,command)
    context={'compiler_version':version,'flags':flags,'host':socket.gethostname(),'architecture':platform.machine(),
        'source_sha256':{name:artifacts.file_hash(output/name) for name in SOURCES},'binary_sha256':artifacts.file_hash(binary),
        'compiler_sha256':artifacts.file_hash(compiler.resolve()),'instrumented_timer':False,
        'optimized_work':{'ir_sha256':artifacts.file_hash(ir),'primitive':dict(PRIMITIVE)},**snapshot()}
    def unchanged():
        if native and (command([*git,'rev-parse','HEAD']).stdout.strip()!=native['commit'] or command([*git,'status','--porcelain']).stdout):raise Failure('float evidence source changed')
    unchanged()
    if native:context.update(native,loaded_libraries=loaded_libraries(binary,command),end_state=_host_state())
    if args.count_only:
        raw={'format':'swdb.cpu-float-memory-count-only.v1','evidence_kind':'fixture' if args.fixture else 'native_count_only',
            'timings_collected':False,'machine':args.machine,'threads':1,'context':context,'count_proof':counted,
            'budgets':{'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP}}
        raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()),timed=False)
        (output/'count-proof.json').write_text(payload);return {'count_proof':str(output/'count-proof.json'),'identity_sha256':raw['identity_sha256'],'timings_collected':False}
    def timer(elements,batches,order):
        argv=[binary,elements,batches,order]
        if native:argv=['taskset','-c',native['cpus'][0],*argv]
        return json.loads(command(argv).stdout)
    services=[]
    for footprint in footprints:
        elements=footprint//8;batches=1
        while True:
            trial=timer(elements,batches,'service_first');(output/f'pilot-{footprint}.json').write_text(json.dumps(trial))
            if trial['gross_seconds']>=args.min_trial_s*1.25:break
            if elements*batches>=EVENT_CAP:raise Failure('float gross pilot unresolved at event cap')
            batches=min(2*batches,EVENT_CAP//elements)
        trials=[timer(elements,batches,'service_first' if r%2==0 else 'driver_first') for r in range(args.repetitions)]
        services.append({'id':f'memory.floating-add-update.8.{footprint}','unit':'seconds/request',
            'event_definition':'One exactly proved floating64 monotonic fadd logical source request. Preparation/checks untimed; physical instruction latency/application residency unknown.',
            'scope':{'worker_scope':'serial','memory_regime':'resident_serial_constructed_requests','operation':'floating-add-update',
                'update_kind':'add-update','element_bytes':8,'footprint_bytes':footprint,'transfer_basis':'inferred','source_primitive':dict(PRIMITIVE),
                'construction':'sequential uncontended floating64 monotonic atomic add; prepared zero buffer',
                'cache_state':'prepared buffers and repeated calls; physical cache level unverified','first_touch':'preparation excluded'},
            'denominator':{'level':'source_normalized_work','basis':'measured','proof':counted},'trials':trials})
        (output/'partial-trials.json').write_text(json.dumps(services,indent=2));budget(output)
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture' if args.fixture else 'native','machine':args.machine,'threads':1,
        'context':context,'settings':{'group':'memory_float_v1','repetitions':args.repetitions,'min_trial_s':args.min_trial_s,'max_wall_s':args.max_wall_s,
            'event_cap':EVENT_CAP,'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP,'live_payload_cap_bytes':8388608,'footprint_bytes':footprints,
            'trial_resolution_scope':'gross_aggregate_only; paired driver retained'},'services':services}
    unchanged()
    if native:context['end_state']=_host_state();validate(raw)
    raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()))
    (output/'receipt.json').write_text(payload);return {'receipt':str(output/'receipt.json'),'receipt_sha256':raw['identity_sha256'],'services':len(services),'evidence_kind':raw['evidence_kind']}


def validate(raw):
    c,s=raw['context'],raw['settings']
    def require(ok,why):
        if not ok:raise Failure('native floating memory: '+why)
    def hashed(v):return bool(re.fullmatch('[0-9a-f]{64}',str(v)))
    def finite(v):return type(v) in (int,float) and math.isfinite(v)
    require(raw['threads']==1 and c.get('system')=='Linux' and c.get('architecture')=='x86_64' and c.get('host','').split('.')[0]==raw['machine'],'native target differs')
    require(c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}',str(c.get('commit'))) and '(verified:' in str(c.get('lane')) and isinstance(c.get('cpus'),list) and len(c['cpus'])==1 and type(c['cpus'][0]) is int and c['cpus'][0]>=0,'clean source/verified worker missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.',c.get('compiler_version','')) and c['flags'][:3]==['-O3','-std=c++11','-fopenmp'] and all(f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in c['flags'][3:]),'compiler/work flags differ')
    require(s['group']=='memory_float_v1' and type(s['repetitions']) is int and 7<=s['repetitions']<=11 and finite(s['min_trial_s']) and .05<=s['min_trial_s']<=.2 and finite(s['max_wall_s']) and 0<s['max_wall_s']<=900,'sampling differs')
    require(s['event_cap']==EVENT_CAP and s['count_build_cap_bytes']==COUNT_CAP and s['timed_data_cap_bytes']==TIMED_CAP and s['live_payload_cap_bytes']==8388608,'caps differ')
    require(set(c['source_sha256'])==set(SOURCES) and all(hashed(v) for v in c['source_sha256'].values()) and all(hashed(c.get(k)) for k in ('compiler_sha256','binary_sha256','machine_sha256')) and valid(c),'context identities/control scope missing')
    libs=c.get('loaded_libraries',{});require(all(any(k.startswith(p) for k in libs) for p in ('libstdc++','libc.so','libomp')) and all(hashed(v.get('sha256')) for v in libs.values()),'runtime identities missing')
    require(c['optimized_work']['primitive']==PRIMITIVE and hashed(c['optimized_work']['ir_sha256']),'optimized primitive proof missing')
    footprints=s['footprint_bytes'];require(isinstance(footprints,list) and footprints==sorted(set(footprints)) and 0<len(footprints)<=2 and all(type(f) is int and 64<=f<=8388608 and not f&(f-1) for f in footprints),'footprints differ')
    require(len(raw['services'])==len(footprints),'cell matrix differs');seen=set()
    for service in raw['services']:
        scope=service['scope'];footprint=scope['footprint_bytes'];require(footprint in footprints and footprint not in seen,'duplicate/unsupported footprint');seen.add(footprint)
        require(service['id']==f'memory.floating-add-update.8.{footprint}' and service['unit']=='seconds/request' and all(scope.get(k)==v for k,v in {'worker_scope':'serial','memory_regime':'resident_serial_constructed_requests','operation':'floating-add-update','update_kind':'add-update','element_bytes':8,'transfer_basis':'inferred','source_primitive':PRIMITIVE,'first_touch':'preparation excluded','cache_state':'prepared buffers and repeated calls; physical cache level unverified'}.items()),'exact floating cell scope differs')
        denominator=service['denominator'];proof=denominator['proof'];require(denominator['level']=='source_normalized_work' and denominator['basis']=='measured' and proof['format']=='swdb.cpu-float-memory-count-proof.v1' and proof['pipeline']==PIPELINE and proof['source_sha256']==c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256']==c['source_sha256'][SOURCES[2]] and all(hashed(proof.get(k)) for k in ('plugin_source_sha256','runtime_source_sha256')),'count/timing identity differs')
        points=proof['points'];require(len(points)==4 and {(p['invoke'],p['events']) for p in points}=={(invoke,n) for invoke in (True,False) for n in (3,5)},'full count matrix absent')
        for p in points:
            n=p['events'] if p['invoke'] else 0
            require(type(p['invoke']) is bool and type(p['events']) is int and type(p['requests']) is int and p['requests']==n and p['atomic_events']==n and p['opaque_events']==0 and p['primitive']==PRIMITIVE and hashed(p['characterization_sha256']),'primitive/numerator differs')
        require(len(service['trials'])==s['repetitions'],'trial count differs')
        for i,t in enumerate(service['trials']):
            require(all(type(t[k]) is int and t[k]>0 for k in ('events','batch_events','batches')) and t['events']<=EVENT_CAP and t['events']==t['batch_events']*t['batches'] and t['batch_events']==footprint//8 and t.get('verified_updates')==t['events'],'exact bounded updated-element count differs')
            require(finite(t['gross_seconds']) and t['gross_seconds']>=s['min_trial_s'] and finite(t['driver_seconds']) and t['driver_seconds']>0 and t['order']==('service_first' if i%2==0 else 'driver_first'),'elapsed/order differs')


def main():
    p=argparse.ArgumentParser(description='bounded independent floating64 monotonic atomic proof/elapsed; no application timing')
    p.add_argument('--records',type=Path,default=paths.RECORDS);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture',action='store_true');p.add_argument('--count-only',action='store_true')
    p.add_argument('--llvm-bin',type=Path);p.add_argument('--toolchain-flag',action='append',default=[]);p.add_argument('--footprint-bytes',type=int,action='append')
    p.add_argument('--machine',default='mbit10');p.add_argument('--lane');p.add_argument('--repetitions',type=int,default=7);p.add_argument('--min-trial-s',type=float,default=.05);p.add_argument('--max-wall-s',type=float,default=900)
    args=p.parse_args()
    try:print(json.dumps(calibrate(args)));return 0
    except (Failure,OSError,KeyError,ValueError,TypeError) as exc:print(str(exc),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())

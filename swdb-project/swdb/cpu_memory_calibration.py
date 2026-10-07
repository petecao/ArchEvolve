"""Independent conditional memory request cells. Created: 2026-10-06 ET."""
import argparse
import json
import math
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
from swdb.cpu_service_native import loaded_libraries, prepare
from swdb.extensa_boundary import closure
from swdb.store import Store

NAMES=('read','write','add-update','cas-success','cas-failure')
KINDS=('read','write','add-update','compare-and-swap','compare-and-swap')
SOURCES=('CpuMemoryWork.h','CpuMemoryTimer.cpp','CpuMemoryCount.cpp')
PIPELINE={'version':'source-normalized-v2','passes':['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']}
COUNT_CAP,TIMED_CAP,EVENT_CAP=64*1024**2,25*1024**2,134217728
PRIMITIVES=['volatile_read','volatile_write','seq_cst_add','seq_cst_compare_exchange']


def budget(output,*,addition=0,timed=True):
    build=0;data=addition if timed else 0
    for p in output.rglob('*'):
        if not p.is_file():continue
        if p.parent==output and (p.name in ('partial-trials.json','receipt.json') or p.name.startswith('pilot-')):data+=p.stat().st_size
        else:build+=p.stat().st_size
    if not timed:build+=addition
    if build>COUNT_CAP or data>TIMED_CAP:raise Failure('memory count-build/timed-data budget exceeded; partial sealed artifacts retained')


def proof(args,output,command,operations,widths):
    store=Store(args.records);seeds=['gapbs-bfs-do','kron-g16-k16']
    if any(store.get(k) is None for k in seeds):raise Failure('memory count proof needs registered carrier/input')
    copied=output/'count-records';copied.mkdir()
    for key in closure(store,seeds):
        relative=store.path_of(key);destination=copied/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(args.records)/relative))
    points=[]
    for name in operations:
        op=NAMES.index(name)
        for width in widths:
            for invoke in (True,False):
                for n in (3,5):
                    key=f'{name}.{width}.{int(invoke)}.{n}'
                    argv=[sys.executable,'-m','swdb','characterize','--records',copied,'--source',output/SOURCES[2],
                        '--implementation',seeds[0],'--input',seeds[1],'--function','service_memory'+str(width*8),'--threads','1',
                        '--fixture','--counting-pipeline','source-normalized-v2','--id','calibration.memory.'+key,
                        '--roi','constructed-memory-service','--llvm-bin',args.llvm_bin,'--output',output/('count-'+key),
                        '--format','json','--timeout-s','60','--build-flag=-std=c++11']
                    argv+=['--run-arg='+str(v) for v in (n,width,op,int(invoke))]
                    argv+=['--toolchain-flag='+f for f in args.toolchain_flag]
                    char=json.loads(command(argv).stdout)
                    counts={k:0 for k in set(KINDS)};by_width=[]
                    for region in char['regions']:
                        for kind,rows in region.get('memory_service_counts',{}).get('requests_by_update_kind',{}).items():
                            for row in rows:
                                value=row['requests']['value']
                                if value:by_width.append({'update_kind':kind,'element_bytes':row['element_bytes'],'requests':value})
                                counts[kind]=counts.get(kind,0)+value
                    if counts.get(KINDS[op])!=(n if invoke else 0) or sum(counts.values())!=(n if invoke else 0) or any(r['element_bytes']!=width for r in by_width):
                        raise Failure('memory exact source request coefficient/width differs: '+str(by_width))
                    recipe={'version':char['counting']['pipeline_version'],'passes':char['counting']['passes']}
                    if recipe!=PIPELINE:raise Failure('memory source-normalized recipe differs')
                    if any(c['execution_count']['value'] and not c.get('body_counted') and c.get('cost_accounting')=='opaque_callee' for c in char['unmodeled_calls']):
                        raise Failure('memory constructed body has an executed opaque helper')
                    points.append({'operation':name,'element_bytes':width,'invoke':invoke,'events':n,
                        'requests':sum(counts.values()),'opaque_events':0,'requests_by_kind_width':by_width,
                        'checked_success_events':n if invoke and op==3 else 0 if invoke and op==4 else None,'characterization_sha256':artifacts.digest(char),
                        'operation_counts':{k:sum(r['operation_counts'][k]['value'] for r in char['regions']) for k in ('integer','floating_point','branch','atomic')}})
                    budget(output)
    root=Path(__file__).parent
    return {'format':'swdb.cpu-memory-count-proof.v1','pipeline':PIPELINE,'points':points,
        'source_sha256':artifacts.file_hash(output/SOURCES[0]),'count_driver_sha256':artifacts.file_hash(output/SOURCES[2]),
        'plugin_source_sha256':artifacts.file_hash(root/'llvm/Characterize.cpp'),
        'runtime_source_sha256':artifacts.file_hash(root/'llvm/CountingRuntime.cpp')}


def calibrate(args):
    operations=list(dict.fromkeys(args.operation or NAMES));widths=sorted(set(args.element_bytes or (4,8)))
    footprints=sorted(set(args.footprint_bytes or (32768,8388608)))
    if any(f<64 or f>8388608 or f&(f-1) for f in footprints) or len(footprints)>2:
        raise Failure('memory footprints require at most2 power-of-two bins from64B to8MiB')
    if 1 in widths and (operations!=['read'] or any(f>256 for f in footprints)):
        raise Failure('one-byte reads require a separate read-only fixed-small ring <=256B')
    if not 3<=args.repetitions<=11 or not math.isfinite(args.max_wall_s) or not 0<args.max_wall_s<=900 or not math.isfinite(args.min_trial_s) or not 0<args.min_trial_s<=.2:
        raise Failure('memory caps are3–11reps,900s wall and0.2s gross trial')
    if any(not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in args.toolchain_flag):
        raise Failure('memory toolchain flags may select headers/libraries only')
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):raise Failure('memory output requires a new external folder')
    if args.count_only and not args.llvm_bin:raise Failure('memory count-only requires LLVM22')
    native=prepare(args,output);deadline=time.monotonic()+args.max_wall_s
    def command(argv):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Failure('memory wall budget reached')
        return _command(argv,timeout=remaining)
    git=['git','-C',paths.HOME.parent]
    if native:
        native.update(commit=command([*git,'rev-parse','HEAD']).stdout.strip(),dirty=bool(command([*git,'status','--porcelain']).stdout))
        if native['dirty']:raise Failure('native memory source must be clean and committed')
    output.mkdir(parents=True)
    for name in SOURCES:shutil.copy2(Path(__file__).parent/'native'/name,output/name)
    compiler=args.llvm_bin/'clang++' if args.llvm_bin else args.compiler;flags=['-O3','-std=c++11',*args.toolchain_flag]
    binary=output/'memory-timer';version=command([compiler,'--version']).stdout.strip()
    built=command([compiler,*flags,output/SOURCES[1],'-o',binary])
    (output/'build.stdout').write_text(built.stdout);(output/'build.stderr').write_text(built.stderr)
    optimized=None
    if args.llvm_bin:
        command([compiler,*flags,'-S','-emit-llvm',output/SOURCES[1],'-o',output/'memory-optimized.ll'])
        optimized=optimized_proof(output/'memory-optimized.ll')
    counted=proof(args,output,command,operations,widths) if args.llvm_bin else None
    context={'compiler_version':version,'flags':flags,'host':socket.gethostname(),'architecture':platform.machine(),
        'source_sha256':{name:artifacts.file_hash(output/name) for name in SOURCES},'binary_sha256':artifacts.file_hash(binary),
        'compiler_sha256':artifacts.file_hash(Path(shutil.which(str(compiler)) or compiler).resolve()),
        'instrumented_timer':False,'optimized_work':optimized,**snapshot()}
    def unchanged():
        if command([*git,'rev-parse','HEAD']).stdout.strip()!=native['commit'] or command([*git,'status','--porcelain']).stdout:
            raise Failure('native memory source changed during evidence collection')
    if native:unchanged();context.update(native,loaded_libraries=loaded_libraries(binary,command),end_state=_host_state())
    if args.count_only:
        raw={'format':'swdb.cpu-memory-count-only.v1','evidence_kind':'fixture' if args.fixture else 'native_count_only',
            'budgets':{'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP},
            'timings_collected':False,'machine':args.machine,'threads':1,'context':context,'count_proof':counted}
        raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()),timed=False)
        (output/'count-proof.json').write_text(payload)
        return {'count_proof':str(output/'count-proof.json'),'identity_sha256':raw['identity_sha256'],'timings_collected':False}
    def timer(width,elements,batches,op,order):
        argv=[binary,width,elements,batches,op,order]
        if native:argv=['taskset','-c',native['cpus'][0],*argv]
        return json.loads(command(argv).stdout)
    services=[]
    for name in operations:
        op=NAMES.index(name)
        for width in widths:
            for footprint in footprints:
                elements=footprint//width;batches=1
                while True:
                    trial=timer(width,elements,batches,op,'service_first')
                    (output/f'pilot-{name}-{width}-{footprint}.json').write_text(json.dumps(trial))
                    if trial['gross_seconds']>=args.min_trial_s*1.25:break
                    if elements*batches>=EVENT_CAP:raise Failure('memory gross pilot unresolved at event cap')
                    batches=min(2*batches,EVENT_CAP//elements)
                trials=[timer(width,elements,batches,op,'service_first' if r%2==0 else 'driver_first') for r in range(args.repetitions)]
                services.append({'id':f'memory.{name}.{width}.{footprint}','unit':'seconds/request',
                    'event_definition':'One exact logical source request; shared body gross minus conditional-loop driver. Preparation is untimed; no application residency or physical latency claim.',
                    'scope':{'worker_scope':'serial','memory_regime':'fixed_small_byte_read_constructed_requests' if width==1 else 'resident_serial_constructed_requests','operation':name,
                        'update_kind':KINDS[op],'element_bytes':width,'footprint_bytes':footprint,'transfer_basis':'inferred',
                        'construction':'dependent permuted-ring read; sequential volatile write; uncontended seq_cst add/CAS; deterministic success/failure cells',
                        'cache_state':'prepared buffers and repeated calls; physical cache level unverified','first_touch':'preparation excluded'},
                    'denominator':{'level':'source_normalized_work','basis':'measured' if counted else 'reported',
                        'proof':counted or 'Portable shared-source construction only; no native counting proof.'},'trials':trials})
                (output/'partial-trials.json').write_text(json.dumps(services,indent=2));budget(output)
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture' if args.fixture else 'native','machine':args.machine,
        'threads':1,'context':context,'settings':{'group':'memory_v1','repetitions':args.repetitions,'min_trial_s':args.min_trial_s,
        'max_wall_s':args.max_wall_s,'event_cap':EVENT_CAP,'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP,
        'live_payload_cap_bytes':16*1024**2,'operations':operations,'element_bytes':widths,'footprint_bytes':footprints,
        'trial_resolution_scope':'gross_aggregate_only; paired driver retained'},'services':services}
    if native:unchanged();context['end_state']=_host_state();validate(raw)
    raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()))
    (output/'receipt.json').write_text(payload)
    return {'receipt':str(output/'receipt.json'),'receipt_sha256':raw['identity_sha256'],'services':len(services),'evidence_kind':raw['evidence_kind']}


def optimized_proof(ir_path):
    text=ir_path.read_text();retained={}
    for width,bits in ((1,8),(4,32),(8,64)):
        body=re.search(r'define[^\n]*@service_memory'+str(bits)+r'\([^\n]*\).*?\n}',text,re.S)
        if not body:raise Failure('optimized memory typed wrapper missing')
        patterns=(r'load volatile i'+str(bits)+r',',r'store volatile i'+str(bits)+r' ',
            r'atomicrmw add [^\n]*i'+str(bits)+r' 1 seq_cst',r'cmpxchg [^\n]*i'+str(bits)+r' [^\n]*seq_cst seq_cst')
        if any(not re.search(pattern,body.group(0)) for pattern in (patterns[:1] if width==1 else patterns)):
            raise Failure('optimized memory did not retain every typed primitive')
        retained[str(width)]=['volatile_read'] if width==1 else list(PRIMITIVES)
    return {'ir_sha256':artifacts.file_hash(ir_path),'retained_primitives':retained,
        'scope':'Actual O3 typed wrapper lowering; normalized request numerator proof is independent.'}


def validate(raw):
    from swdb.cpu_service_controls import valid
    c,s=raw['context'],raw['settings']
    def require(ok,reason):
        if not ok:raise Failure('native memory: '+reason)
    def hashed(value):return bool(re.fullmatch('[0-9a-f]{64}',str(value)))
    def finite(value):return type(value) in (int,float) and math.isfinite(value)
    require(raw['threads']==1 and c.get('system')=='Linux' and c.get('architecture')=='x86_64','Linux/x86 serial scope differs')
    require(c.get('host','').split('.')[0]==raw['machine'] and c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}',str(c.get('commit'))),'clean target/source missing')
    require('(verified:' in str(c.get('lane')) and isinstance(c.get('cpus'),list) and len(c['cpus'])==1 and type(c['cpus'][0]) is int and c['cpus'][0]>=0,'verified one-core lane missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.',c.get('compiler_version','')),'uninstrumented LLVM22 missing')
    require(c['flags'][:2]==['-O3','-std=c++11'] and all(f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in c['flags'][2:]),'work flags differ')
    require(type(s['repetitions']) is int and 7<=s['repetitions']<=11 and finite(s['min_trial_s']) and .05<=s['min_trial_s']<=.2 and finite(s['max_wall_s']) and 0<s['max_wall_s']<=900,'sampling/budget differs')
    require(s['event_cap']==EVENT_CAP and s['count_build_cap_bytes']==COUNT_CAP and s['timed_data_cap_bytes']==TIMED_CAP and s['live_payload_cap_bytes']==16*1024**2,'construction caps differ')
    require(set(c['source_sha256'])==set(SOURCES) and all(hashed(v) for v in c['source_sha256'].values()) and all(hashed(c.get(k)) for k in ('compiler_sha256','binary_sha256','machine_sha256')),'compiler/shared source/target identities missing')
    libs=c.get('loaded_libraries',{})
    require(any(k.startswith('libstdc++') for k in libs) and any(k.startswith('libc.so') for k in libs) and all(hashed(v.get('sha256')) for v in libs.values()),'C/C++ identities missing')
    require(valid(c),'control declaration missing')
    optimized=c.get('optimized_work',{})
    require(hashed(optimized.get('ir_sha256')) and optimized.get('retained_primitives')=={'1':['volatile_read'],'4':PRIMITIVES,'8':PRIMITIVES},'optimized typed primitive proof missing')
    operations,widths,footprints=s['operations'],s['element_bytes'],s['footprint_bytes']
    require(isinstance(operations,list) and 0<len(operations)<=5 and len(set(operations))==len(operations) and all(o in NAMES for o in operations),'operation matrix differs')
    require(isinstance(widths,list) and widths==sorted(set(widths)) and widths and all(type(w) is int and w in (1,4,8) for w in widths),'width matrix differs')
    require(isinstance(footprints,list) and footprints==sorted(set(footprints)) and 0<len(footprints)<=2 and all(type(f) is int and 64<=f<=8388608 and not f&(f-1) for f in footprints),'footprint matrix differs')
    require(1 not in widths or (operations==['read'] and max(footprints)<=256),'one-byte construction cannot cover a larger footprint or other primitive')
    expected={(o,w,f) for o in operations for w in widths for f in footprints};seen=set()
    require(len(raw['services'])==len(expected),'service matrix incomplete')
    expected_points={(o,w,invoke,n) for o in operations for w in widths for invoke in (True,False) for n in (3,5)}
    for service in raw['services']:
        scope=service['scope'];op,width,footprint=scope['operation'],scope['element_bytes'],scope['footprint_bytes']
        require((op,width,footprint) in expected and (op,width,footprint) not in seen,'duplicate/unsupported cell')
        seen.add((op,width,footprint));kind=KINDS[NAMES.index(op)]
        require(service['id']==f'memory.{op}.{width}.{footprint}' and service['unit']=='seconds/request' and scope['update_kind']==kind and scope['worker_scope']=='serial' and scope['memory_regime']==('fixed_small_byte_read_constructed_requests' if width==1 else 'resident_serial_constructed_requests') and scope['transfer_basis']=='inferred' and scope['cache_state']=='prepared buffers and repeated calls; physical cache level unverified' and scope['first_touch']=='preparation excluded','cell service scope differs')
        denominator=service['denominator'];proof=denominator['proof']
        require(denominator['level']=='source_normalized_work' and denominator['basis']=='measured' and proof['format']=='swdb.cpu-memory-count-proof.v1','counted denominator missing')
        require(proof['source_sha256']==c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256']==c['source_sha256'][SOURCES[2]] and proof['pipeline']==PIPELINE and all(hashed(proof.get(k)) for k in ('plugin_source_sha256','runtime_source_sha256')),'count/timing source or recipe differs')
        points=proof['points']
        require(len(points)==len(expected_points) and {(p['operation'],p['element_bytes'],p['invoke'],p['events']) for p in points}==expected_points,'full typed count matrix incomplete')
        for p in points:
            n=p['events'] if p['invoke'] else 0
            require(type(p['invoke']) is bool and type(p['events']) is int and type(p['requests']) is int and p['requests']==n and p['opaque_events']==0 and hashed(p['characterization_sha256']),'request coefficient/opaque count differs')
            require(p['requests_by_kind_width']==([{'update_kind':KINDS[NAMES.index(p['operation'])],'element_bytes':p['element_bytes'],'requests':n}] if n else []),'request kind/width differs')
            expected_count_success=p['events'] if p['invoke'] and p['operation']=='cas-success' else 0 if p['invoke'] and p['operation']=='cas-failure' else None
            require(p.get('checked_success_events')==expected_count_success and (expected_count_success is None or type(p['checked_success_events']) is int),'counted CAS outcome check differs')
            counts=p['operation_counts']
            require(set(counts)=={'integer','floating_point','branch','atomic'} and all(type(v) is int and v>=0 for v in counts.values()) and counts['floating_point']==0 and counts['atomic']==(n if p['operation'] in ('add-update','cas-success','cas-failure') else 0),'source operation inventory differs')
        trials=service['trials']
        require(len(trials)==s['repetitions'],'paired repetitions differ')
        for i,t in enumerate(trials):
            require(all(type(t[k]) is int and t[k]>0 for k in ('events','batch_events','batches')) and t['events']<=EVENT_CAP and t['events']==t['batch_events']*t['batches'] and t['batch_events']==footprint//width,'bounded full-footprint event workload differs')
            require(finite(t['gross_seconds']) and t['gross_seconds']>=s['min_trial_s'] and finite(t['driver_seconds']) and t['driver_seconds']>0 and t['order']==('service_first' if i%2==0 else 'driver_first'),'paired elapsed/order differs')
            require(t.get('cycle_verified_elements')==(footprint//width if op=='read' else None),'read cycle extent proof differs')
            expected_success=t['events'] if op=='cas-success' else 0 if op=='cas-failure' else None
            require(t.get('success_events')==expected_success and (expected_success is None or type(t['success_events']) is int),'CAS outcome proof differs')
    # Finite nonpositive paired residuals remain admissible inputs with unknown costs.
    # Neither physical residency nor whole-application accuracy follows from these cells.


def main():
    parser=argparse.ArgumentParser(description='bounded independent logical memory service/driver cells; no application timing')
    parser.add_argument('--records',type=Path,default=paths.RECORDS);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fixture',action='store_true');parser.add_argument('--count-only',action='store_true')
    parser.add_argument('--operation',choices=NAMES,action='append');parser.add_argument('--element-bytes',choices=(1,4,8),type=int,action='append')
    parser.add_argument('--footprint-bytes',type=int,action='append');parser.add_argument('--compiler',default='c++')
    parser.add_argument('--machine',default='mbit10');parser.add_argument('--lane');parser.add_argument('--llvm-bin',type=Path)
    parser.add_argument('--toolchain-flag',action='append',default=[]);parser.add_argument('--repetitions',type=int,default=7)
    parser.add_argument('--min-trial-s',type=float,default=.05);parser.add_argument('--max-wall-s',type=float,default=900)
    args=parser.parse_args()
    try:print(json.dumps(calibrate(args)));return 0
    except (Failure,OSError,ValueError,KeyError,TypeError) as exc:print(str(exc),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())

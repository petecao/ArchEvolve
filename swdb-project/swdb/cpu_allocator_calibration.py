"""Exact-size constructed allocator costs. Created: 2026-10-06 ET.

Application allocator-state transfer remains inferred, never measured by this runner.
"""
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
from swdb.cpu_service_native import loaded_libraries, prepare
from swdb.extensa_boundary import closure
from swdb.store import Store

NAMES = ('new_array', 'delete_array', 'new_scalar', 'delete_scalar')
ABI = ('_Znam', '_ZdaPv', '_Znwm', '_ZdlPv')
SOURCES = ('CpuAllocatorWork.h', 'CpuAllocatorTimer.cpp', 'CpuAllocatorCount.cpp')
SIZES = (8,16,32,64,128,8192,65536,227416,262144,524288)
PAYLOAD_CAP, EVENT_CAP, RAW_CAP = 64 * 1024**2, 16777216, 25 * 1024**2
COUNT_CAP = 64 * 1024**2
REGIME = 'fresh_process_repeated_allocate_free_batches'
CONTROL_SCOPE = 'GLIBC_TUNABLES,MALLOC_*,LD_PRELOAD,LD_AUDIT,library_search'
PIPELINE = {'version':'source-normalized-v2', 'passes':['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']}


def controls():
    return {k:v for k,v in os.environ.items() if k.startswith('MALLOC_') or
        k in {'GLIBC_TUNABLES','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH','DYLD_LIBRARY_PATH'}}


def raw_budget(output, count_cap, *, add_build=0, add_timed=0):
    build, timed = add_build, add_timed
    for p in output.rglob('*'):
        if not p.is_file(): continue
        size = p.stat().st_size
        if p.parent==output and (p.name in {'partial-trials.json','receipt.json'} or p.name.startswith('pilot-')):
            timed += size
        else:
            build += size
    if build > count_cap:
        raise Failure('allocator count-build artifacts exceed their explicit budget; partial sealed artifacts retained')
    if timed > RAW_CAP:
        raise Failure('allocator timed data exceeds25MiB; partial evidence retained')


def count_proof(args, output, command):
    store = Store(args.records)
    seeds = ['gapbs-bfs-do','kron-g16-k16']
    if any(store.get(k) is None for k in seeds):
        raise Failure('allocator counting requires its registered carrier/input')
    copied = output / 'count-records'
    copied.mkdir()
    for key in closure(store,seeds):
        relative = store.path_of(key)
        destination = copied / relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(args.records) / relative))
    rows=[]
    for op,name in enumerate(NAMES):
        for size in sorted({min(args.size or SIZES), max(args.size or SIZES)}):
            for invoke in (True,False):
                for n in (3,5):
                    key=f'{name}.{size}.{int(invoke)}.{n}'
                    argv=[sys.executable,'-m','swdb','characterize','--records',copied,
                        '--source',output/SOURCES[2],'--implementation',seeds[0],'--input',seeds[1],
                        '--function','service_allocator','--threads','1','--fixture',
                        '--counting-pipeline','source-normalized-v2','--id','calibration.allocator.'+key,
                        '--roi','constructed-allocator-service','--llvm-bin',args.llvm_bin,
                        '--output',output/('count-'+key),'--format','json','--timeout-s','60','--build-flag=-std=c++11']
                    argv += ['--run-arg='+str(v) for v in (n,size,op,int(invoke))]
                    argv += ['--toolchain-flag='+f for f in args.toolchain_flag]
                    data=json.loads(command(argv).stdout)
                    calls=[c for c in data['unmodeled_calls'] if c.get('cost_accounting')=='opaque_callee' and
                        not c.get('body_counted') and c['execution_count']['value']]
                    observed=sum(c['execution_count']['value'] for c in calls)
                    pipeline={'version':data['counting']['pipeline_version'],'passes':data['counting']['passes']}
                    if observed != (n if invoke else 0) or any(c['name'] != ABI[op] for c in calls) or pipeline != PIPELINE:
                        raise Failure('allocator exact ABI/event coefficient or count recipe differs')
                    shape_rows = [c for r in data['regions'] for c in r.get('call_shape_counts',{}).get('calls',[]) if c['name']==ABI[op]]
                    hist = {}
                    field = 'allocation_lifetime_size_bins' if op % 2 else 'known_length_bins'
                    unknown = 'unknown_free_lifetimes' if op % 2 else 'unknown_lengths'
                    for c in shape_rows:
                        if c[unknown]['value'] != 0:
                            raise Failure('allocator counted size/lifetime is unresolved')
                        for item in c[field]:
                            hist[item['bytes']] = hist.get(item['bytes'],0) + item['execution_count']['value']
                    bins = [{'bytes':b,'events':count} for b,count in sorted(hist.items())]
                    if bins != ([{'bytes':size,'events':n}] if invoke else []):
                        raise Failure('allocator observed size/lifetime bins differ from the constructed event')
                    rows.append({'event_size_bins':bins, 'operation':name,'size_bytes':size,'invoke':invoke,'events':n,
                        'opaque_events':observed,'event_abi':ABI[op],'characterization_sha256':artifacts.digest(data)})
                    raw_budget(output, args.count_build_cap_mib * 1024**2)
    root=Path(__file__).parent
    return {'format':'swdb.cpu-allocator-count-proof.v1','pipeline':PIPELINE,'points':rows,
        'source_sha256':artifacts.file_hash(output/SOURCES[0]),'count_driver_sha256':artifacts.file_hash(output/SOURCES[2]),
        'plugin_source_sha256':artifacts.file_hash(root/'llvm/Characterize.cpp'),
        'runtime_source_sha256':artifacts.file_hash(root/'llvm/CountingRuntime.cpp')}


def calibrate(args):
    if type(args.count_build_cap_mib) is not int or not 1<=args.count_build_cap_mib<=64:
        raise Failure('allocator count-build cap must be1–64MiB; timed data cap stays25MiB')
    sizes=sorted(set(args.size or SIZES))
    if not sizes or len(sizes)>10 or any(type(s) is not int or not 0<s<=1048576 for s in sizes):
        raise Failure('allocator sizes require at most10 positive exact bins <=1MiB')
    if not 3<=args.repetitions<=11 or not math.isfinite(args.max_wall_s) or not 0<args.max_wall_s<=900 or not math.isfinite(args.min_trial_s) or not 0<args.min_trial_s<=.2:
        raise Failure('allocator caps are3–11reps,900s wall and0.2s gross trial')
    if any(not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in args.toolchain_flag):
        raise Failure('allocator toolchain flags may select headers/libraries only')
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):
        raise Failure('allocator output requires a new external folder')
    if args.count_only and not args.llvm_bin:
        raise Failure('allocator count-only evidence requires LLVM22')
    native=prepare(args,output)
    deadline=time.monotonic()+args.max_wall_s
    def command(argv):
        remaining=deadline-time.monotonic()
        if remaining<=0: raise Failure('allocator wall budget reached')
        return _command(argv,timeout=remaining)
    git=['git','-C',paths.HOME.parent]
    if native:
        native.update(commit=command([*git,'rev-parse','HEAD']).stdout.strip(),
            dirty=bool(command([*git,'status','--porcelain']).stdout))
        if native['dirty']: raise Failure('native allocator source must be clean and committed')
    output.mkdir(parents=True)
    for name in SOURCES: shutil.copy2(Path(__file__).parent/'native'/name,output/name)
    compiler=args.llvm_bin/'clang++' if args.llvm_bin else args.compiler
    flags=['-O3','-std=c++11',*args.toolchain_flag]
    binary=output/'allocator-timer'
    version=command([compiler,'--version']).stdout.strip()
    built=command([compiler,*flags,output/SOURCES[1],'-o',binary])
    (output/'build.stdout').write_text(built.stdout)
    (output/'build.stderr').write_text(built.stderr)
    optimized=None
    if args.llvm_bin:
        command([compiler,*flags,'-S','-emit-llvm',output/SOURCES[2],'-o',output/'allocator-optimized.ll'])
        body=re.search(r'define[^\n]*@service_allocator\([^\n]*\).*?\n}',(output/'allocator-optimized.ll').read_text(),re.S)
        if not body or any(not re.search(r'(?:call|invoke)[^\n]*@'+name+r'\(',body.group(0)) for name in ABI):
            raise Failure('optimized allocator did not retain all four exact ABI calls')
        optimized={'ir_sha256':artifacts.file_hash(output/'allocator-optimized.ll'),'retained_event_abis':list(ABI)}
    proof=count_proof(args,output,command) if args.llvm_bin else None
    context={'compiler_version':version,'flags':flags,'host':socket.gethostname(),'architecture':platform.machine(),
        'source_sha256':{n:artifacts.file_hash(output/n) for n in SOURCES},'binary_sha256':artifacts.file_hash(binary),
        'instrumented_timer':False,'allocator_environment':controls(),'allocator_environment_scope':CONTROL_SCOPE,
        'runtime_identity_method':'dynamic_linker_resolution_preexecution','optimized_event_proof':optimized}
    if native:
        context.update(native)
        context['loaded_libraries']=loaded_libraries(binary,command)
    def unchanged():
        if native and (command([*git,'rev-parse','HEAD']).stdout.strip()!=native['commit'] or command([*git,'status','--porcelain']).stdout):
            raise Failure('native allocator source changed during collection')
    if args.count_only:
        unchanged()
        raw={'format':'swdb.cpu-allocator-count-only.v1','evidence_kind':'fixture' if args.fixture else 'native_count_only',
            'budgets':{'count_build_cap_bytes':args.count_build_cap_mib * 1024**2,'timed_data_cap_bytes':RAW_CAP},
            'timings_collected':False,'machine':args.machine,'threads':1,'context':context,'count_proof':proof,'sizes':sizes}
        raw['identity_sha256']=identity(raw)
        payload=json.dumps(raw,indent=2)
        raw_budget(output,args.count_build_cap_mib * 1024**2,add_build=len(payload.encode()))
        (output/'count-proof.json').write_text(payload)
        return {'count_proof':str(output/'count-proof.json'),'timings_collected':False,'identity_sha256':raw['identity_sha256']}
    def timer(size,n,batches,op,order):
        argv=[binary,size,n,batches,op,order]
        if native: argv=['taskset','-c',native['cpus'][0],*argv]
        return json.loads(command(argv).stdout)
    services=[]
    cells=[(op,size) for op in range(4) for size in sizes if args.size or (size>=8192 if op<2 else size<=128)]
    for op,size in cells:
            name=NAMES[op]
            n=min(65536,PAYLOAD_CAP//size)
            batches=1
            while True:
                pilot=timer(size,n,batches,op,'service_first')
                (output/f'pilot-{name}-{size}.json').write_text(json.dumps(pilot))
                if pilot['gross_seconds']>=args.min_trial_s*1.25: break
                if n*batches>=EVENT_CAP: raise Failure('allocator gross pilot unresolved at event cap')
                batches=min(2*batches,EVENT_CAP//n)
            trials=[timer(size,n,batches,op,'service_first' if r%2==0 else 'driver_first') for r in range(args.repetitions)]
            services.append({'id':f'allocator.{name}.{size}','unit':'seconds/call',
                'event_definition':f'One {ABI[op]} opaque call of {size} bytes/lifetime; gross minus conditional driver. Untimed preparations/cleanup, payload touch excluded.',
                'scope':{'worker_scope':'serial','operation':name,'event_abi':ABI[op],'size_bytes':size,
                    'allocator_regime':REGIME,'transfer_basis':'inferred','cache_state':'unobserved','payload_touch':False,
                    'runtime':'hash-bound C/C++ allocator libraries'},
                'denominator':{'level':'source_normalized_work','basis':'measured' if proof else 'reported',
                    'proof':proof or 'Portable shared-source construction only; no native count proof.'},'trials':trials})
            (output/'partial-trials.json').write_text(json.dumps(services,indent=2))
            raw_budget(output, args.count_build_cap_mib * 1024**2)
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture' if args.fixture else 'native',
        'machine':args.machine,'threads':1,'context':context,'settings':{'group':'allocator_v1',
            'repetitions':args.repetitions,'min_trial_s':args.min_trial_s,'trial_resolution_scope':'gross_aggregate_only; paired driver retained',
            'max_wall_s':args.max_wall_s,'live_payload_cap_bytes':PAYLOAD_CAP,'batch_event_cap':65536,
            'event_cap':EVENT_CAP,'timed_data_cap_bytes':RAW_CAP,'count_build_cap_bytes':args.count_build_cap_mib * 1024**2,'sizes':sizes,
            'cells':[{'operation':NAMES[op],'size_bytes':size} for op,size in cells]},'services':services}
    if native:
        unchanged()
        context['end_state']=_host_state()
        validate(raw)
    raw_budget(output, args.count_build_cap_mib * 1024**2)
    raw['identity_sha256']=identity(raw)
    payload=json.dumps(raw,indent=2)
    raw_budget(output,args.count_build_cap_mib * 1024**2,add_timed=len(payload.encode()))
    (output/'receipt.json').write_text(payload)
    return {'receipt':str(output/'receipt.json'),'receipt_sha256':raw['identity_sha256'],'evidence_kind':raw['evidence_kind'],'services':len(services)}


def validate(raw):
    c,s=raw['context'],raw['settings']
    def require(ok,reason):
        if not ok: raise Failure('native allocator: '+reason)
    require(raw['threads']==1 and c.get('system')=='Linux' and c.get('architecture')=='x86_64','Linux/x86 serial scope differs')
    require(c.get('host','').split('.')[0]==raw['machine'] and c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}',str(c.get('commit'))),'clean target/source missing')
    require('(verified:' in str(c.get('lane')) and len(c.get('cpus',[]))==1,'verified pinned lane missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.',c.get('compiler_version','')),'uninstrumented LLVM22 missing')
    require(c['flags'][:2]==['-O3','-std=c++11'] and all(f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in c['flags'][2:]),'work flags differ')
    require(7<=s['repetitions']<=11 and .05<=s['min_trial_s']<=.2 and 0<s['max_wall_s']<=900,'sampling/budget differs')
    require(s['live_payload_cap_bytes']==PAYLOAD_CAP and s['event_cap']==EVENT_CAP and s['batch_event_cap']==65536 and s['timed_data_cap_bytes']==RAW_CAP and 1024**2<=s['count_build_cap_bytes']<=COUNT_CAP,'construction caps differ')
    require(set(c['source_sha256'])==set(SOURCES) and all(re.fullmatch('[0-9a-f]{64}',str(v)) for v in c['source_sha256'].values()),'shared source identities missing')
    require(all(re.fullmatch('[0-9a-f]{64}',str(c.get(k))) for k in ('binary_sha256','machine_sha256')),'machine/binary identity missing')
    libs=c.get('loaded_libraries',{})
    require(any(k.startswith('libstdc++') for k in libs) and any(k.startswith('libc.so') for k in libs) and all(re.fullmatch('[0-9a-f]{64}',str(v.get('sha256'))) for v in libs.values()),'C/C++ identities missing')
    require(isinstance(c.get('allocator_environment'),dict) and c.get('allocator_environment_scope')==CONTROL_SCOPE,'allocator controls scope missing')
    optimized=c.get('optimized_event_proof',{})
    require(optimized.get('retained_event_abis')==list(ABI) and re.fullmatch('[0-9a-f]{64}',str(optimized.get('ir_sha256'))),'optimized ABI proof missing')
    sizes=s['sizes']
    require(0<len(sizes)<=10 and sizes==sorted(set(sizes)) and all(type(n) is int and 0<n<=1048576 for n in sizes),'size matrix differs')
    cells=s['cells']
    require(isinstance(cells,list) and 0<len(cells)<=40 and all(p.get('operation') in NAMES and p.get('size_bytes') in sizes for p in cells) and
        len({(p['operation'],p['size_bytes']) for p in cells})==len(cells) and len(raw['services'])==len(cells),'split matrix incomplete')
    seen=set()
    for service in raw['services']:
        scope=service['scope']; op,size=scope['operation'],scope['size_bytes']
        require({'operation':op,'size_bytes':size} in cells and (op,size) not in seen,'duplicate/unsupported cell')
        seen.add((op,size))
        require(service['id']==f'allocator.{op}.{size}' and service['unit']=='seconds/call' and scope['event_abi']==ABI[NAMES.index(op)] and
            scope['allocator_regime']==REGIME and scope['transfer_basis']=='inferred' and scope['payload_touch'] is False,'cell scope differs')
        proof=service['denominator']['proof']
        require(service['denominator']['level']=='source_normalized_work' and service['denominator']['basis']=='measured' and
            proof['format']=='swdb.cpu-allocator-count-proof.v1','counted denominator missing')
        require(proof['source_sha256']==c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256']==c['source_sha256'][SOURCES[2]] and proof['pipeline']==PIPELINE,'count/timing source or recipe differs')
        points=proof['points']
        expected={(o,z,invoke,n) for o in NAMES for z in {min(sizes),max(sizes)} for invoke in (True,False) for n in (3,5)}
        require({(p['operation'],p['size_bytes'],p['invoke'],p['events']) for p in points}==expected and len(points)==len(expected),'count matrix incomplete')
        require(all(p['opaque_events']==(p['events'] if p['invoke'] else 0) and p['event_size_bins']==([{'bytes':p['size_bytes'],'events':p['events']}] if p['invoke'] else []) and p['event_abi']==ABI[NAMES.index(p['operation'])] and re.fullmatch('[0-9a-f]{64}',str(p['characterization_sha256'])) for p in points),'event coefficient differs')
        require(all(re.fullmatch('[0-9a-f]{64}',str(proof.get(k))) for k in ('plugin_source_sha256','runtime_source_sha256')),'observer identity missing')
        trials=service['trials']
        require(len(trials)==s['repetitions'] and all(type(t['events']) is int and 0<t['events']<=EVENT_CAP and
            t['events']==t['batches']*t['batch_events'] and 0<t['batch_events']<=65536 and t['batch_events']*size<=PAYLOAD_CAP and
            t['gross_seconds']>=s['min_trial_s'] and t['driver_seconds']>0 and t['order']==('service_first' if i%2==0 else 'driver_first') for i,t in enumerate(trials)), 'paired trials differ')

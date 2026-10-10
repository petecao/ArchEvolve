"""Bounded independent exact-length bulk cells. Created2026-10-06 ET."""
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
from swdb.cpu_memory_calibration import budget, COUNT_CAP, TIMED_CAP, EVENT_CAP, PIPELINE
from swdb.extensa_boundary import closure
from swdb.store import Store

from swdb.cpu_bulk_calibration import SOURCES, REGIMES, FUNCTIONS, proof, optimized_proof


def calibrate(args):
    sizes=sorted(set(args.size or (8,)))
    if not sizes or len(sizes)>32 or any(type(n) is not int or not 8<=n<=1048576 for n in sizes):
        raise Failure('bulk exact bins require1–32 sizes from8B to1MiB; overlap shift is4B')
    if type(args.repetitions) is not int or not 3<=args.repetitions<=11 or not math.isfinite(args.min_trial_s) or not 0<args.min_trial_s<=.2 or not math.isfinite(args.max_wall_s) or not 0<args.max_wall_s<=900:
        raise Failure('bulk caps are3–11reps,.2s gross trials and900s wall')
    if any(not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in args.toolchain_flag):raise Failure('bulk flags may select headers/libraries only')
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):raise Failure('bulk output needs a new external folder')
    if args.count_only and not args.llvm_bin:raise Failure('bulk count-only requiresLLVM22')
    native=prepare(args,output);deadline=time.monotonic()+args.max_wall_s
    def command(argv):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Failure('bulk wall budget reached')
        return _command(argv,timeout=remaining)
    git=['git','-C',paths.HOME.parent]
    if native:
        native.update(commit=command([*git,'rev-parse','HEAD']).stdout.strip(),dirty=bool(command([*git,'status','--porcelain']).stdout))
        if native['dirty']:raise Failure('native bulk source must be clean/committed')
    output.mkdir(parents=True)
    for name in SOURCES:shutil.copy2(Path(__file__).parent/'native'/name,output/name)
    compiler=args.llvm_bin/'clang++' if args.llvm_bin else args.compiler
    flags=['-O3','-std=c++11',*args.toolchain_flag];binary=output/'bulk-timer'
    version=command([compiler,'--version']).stdout.strip()
    built=command([compiler,*flags,output/SOURCES[1],'-o',binary])
    (output/'build.stdout').write_text(built.stdout);(output/'build.stderr').write_text(built.stderr)
    context={'compiler_version':version,'flags':flags,'host':socket.gethostname(),'architecture':platform.machine(),
        'source_sha256':{n:artifacts.file_hash(output/n) for n in SOURCES},'binary_sha256':artifacts.file_hash(binary),
        'compiler_sha256':artifacts.file_hash(Path(shutil.which(str(compiler)) or compiler).resolve()),
        'instrumented_timer':False,'collection_recipe':'gross_loop_window_with_retained_driver_v2',**snapshot()}
    if args.llvm_bin:
        command([compiler,*flags,'-S','-emit-llvm',output/SOURCES[1],'-o',output/'bulk-optimized.ll'])
        context['optimized_work']=optimized_proof(output/'bulk-optimized.ll')
    counted=proof(args,output,command,sizes) if args.llvm_bin else None
    def unchanged():
        if command([*git,'rev-parse','HEAD']).stdout.strip()!=native['commit'] or command([*git,'status','--porcelain']).stdout:
            raise Failure('native bulk source changed during collection')
    if native:unchanged();context.update(native,loaded_libraries=loaded_libraries(binary,command),end_state=_host_state())
    if args.count_only:
        raw={'format':'swdb.cpu-bulk-count-only.v2','evidence_kind':'fixture' if args.fixture else 'native_count_only',
            'timings_collected':False,'machine':args.machine,'threads':1,'context':context,'count_proof':counted,
            'budgets':{'count_build_cap_bytes':COUNT_CAP,'timed_data_cap_bytes':TIMED_CAP}}
        raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()),timed=False)
        (output/'count-proof.json').write_text(payload)
        return {'count_proof':str(output/'count-proof.json'),'identity_sha256':raw['identity_sha256'],'timings_collected':False}
    services=[]
    for op,regime in enumerate(REGIMES):
        for size in ([8] if op==0 else sizes):
            def timer(n,order):
                argv=[binary,op,size,n,int(order=='service_first')]
                if native:argv=['taskset','-c',native['cpus'][0],*argv]
                return json.loads(command(argv).stdout)
            n=1024
            while True:
                trial=timer(n,'service_first')
                (output/f'pilot-bulk-{op}-{size}.json').write_text(json.dumps(trial))
                if trial['gross_seconds']>=args.min_trial_s*1.25:break
                if n==EVENT_CAP:raise Failure('bulk gross loop pilot unresolved at event cap')
                n=min(n*2,EVENT_CAP)
            trials=[timer(n,'service_first' if i%2==0 else 'driver_first') for i in range(args.repetitions)]
            services.append({'id':f'bulk.{op}.{size}','unit':'seconds/call',
                'event_definition':'One exact logical source bulk copy; shared-helper paired elapsed, no physical traffic or application overlap/first-touch claim.',
                'scope':{'event_abi':'memcpy' if op==0 else 'memmove','worker_scope':'serial','bulk_regime':regime,
                    'size_bytes':size,'alignment_min_bytes':8 if op==0 else 4,'transfer_basis':'inferred',
                    'first_touch':'preparation excluded','cache_state':'prepared reused buffers; physical cache level unverified',
                    'residual_policy':{'id':'both_windows_meet_declared_threshold','minimum_window_s':args.min_trial_s}},
                'denominator':{'level':'source_normalized_work','basis':'measured' if counted else 'reported',
                    'proof':counted or 'Portable shared source only; no native counting proof.'},'trials':trials})
            (output/'partial-trials.json').write_text(json.dumps(services,indent=2));budget(output)
    raw={'format':'swdb.cpu-service-calibration.v1','evidence_kind':'fixture' if args.fixture else 'native',
        'machine':args.machine,'threads':1,'context':context,
        'settings':{'group':'bulk_total_v2','sizes':sizes,'repetitions':args.repetitions,'min_trial_s':args.min_trial_s,
            'max_wall_s':args.max_wall_s,'event_cap':EVENT_CAP,'count_build_cap_bytes':COUNT_CAP,
            'timed_data_cap_bytes':TIMED_CAP,'live_payload_cap_bytes':3*1048576+320},'services':services}
    if native:unchanged();context['end_state']=_host_state();validate(raw)
    raw['identity_sha256']=identity(raw);payload=json.dumps(raw,indent=2);budget(output,addition=len(payload.encode()))
    (output/'receipt.json').write_text(payload)
    return {'receipt':str(output/'receipt.json'),'receipt_sha256':raw['identity_sha256'],'services':len(services),'evidence_kind':raw['evidence_kind']}


def validate(raw):
    from swdb.cpu_service_controls import valid
    c,s=raw['context'],raw['settings']
    def require(ok,reason):
        if not ok:raise Failure('native bulk: '+reason)
    def hashed(v):return bool(re.fullmatch('[0-9a-f]{64}',str(v)))
    def finite(v):return type(v) in (int,float) and math.isfinite(v)
    require(s.get('group')=='bulk_total_v2' and c.get('collection_recipe')=='gross_loop_window_with_retained_driver_v2','distinct gross recipe identity missing')
    require(raw['threads']==1 and c.get('system')=='Linux' and c.get('architecture')=='x86_64','Linux/x86 serial scope differs')
    require(c.get('host','').split('.')[0]==raw['machine'] and c.get('dirty') is False and re.fullmatch('[0-9a-f]{40}',str(c.get('commit'))),'clean source/target missing')
    require('(verified:' in str(c.get('lane')) and isinstance(c.get('cpus'),list) and len(c['cpus'])==1 and type(c['cpus'][0]) is int and c['cpus'][0]>=0,'verified one-core lane missing')
    require(c.get('instrumented_timer') is False and re.search(r'clang version 22\.',c.get('compiler_version','')),'uninstrumented LLVM22 missing')
    require(c['flags'][:2]==['-O3','-std=c++11'] and all(f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in c['flags'][2:]),'work flags differ')
    require(type(s['repetitions']) is int and 7<=s['repetitions']<=11 and finite(s['min_trial_s']) and .05<=s['min_trial_s']<=.2 and finite(s['max_wall_s']) and 0<s['max_wall_s']<=900,'sampling/budget differs')
    require(s['event_cap']==EVENT_CAP and s['count_build_cap_bytes']==COUNT_CAP and s['timed_data_cap_bytes']==TIMED_CAP and s['live_payload_cap_bytes']==3*1048576+320,'construction caps differ')
    require(set(c['source_sha256'])==set(SOURCES) and all(hashed(v) for v in c['source_sha256'].values()) and all(hashed(c.get(k)) for k in ('compiler_sha256','binary_sha256','machine_sha256')),'compiler/shared source/target identities missing')
    libs=c.get('loaded_libraries',{})
    require(any(k.startswith('libstdc++') for k in libs) and any(k.startswith('libc.so') for k in libs) and all(hashed(v.get('sha256')) for v in libs.values()),'C/C++ identities missing')
    require(valid(c),'control declaration missing')
    optimized=c.get('optimized_work',{})
    require(hashed(optimized.get('ir_sha256')) and optimized.get('retained')==dict(zip(FUNCTIONS,('constant8_word_load_store',*(['dynamic_length_memmove']*3)))),'optimized bulk work elided or unsupported')
    sizes=s['sizes']
    require(isinstance(sizes,list) and sizes==sorted(set(sizes)) and 0<len(sizes)<=32 and all(type(n) is int and 8<=n<=1048576 for n in sizes),'exact byte matrix differs')
    matrix=[('memcpy',FUNCTIONS[0],8)]+[('memmove',f,n) for f in FUNCTIONS[1:] for n in sizes]
    expected={(op,n) for op in range(4) for n in ([8] if op==0 else sizes)};seen=set()
    require(len(raw['services'])==len(expected),'service matrix incomplete')
    for service in raw['services']:
        scope=service['scope'];regime=scope['bulk_regime'];op=REGIMES.index(regime);n=scope['size_bytes'];alignment=8 if op==0 else 4
        require((op,n) in expected and (op,n) not in seen,'duplicate/unsupported cell');seen.add((op,n))
        require(service['id']==f'bulk.{op}.{n}' and service['unit']=='seconds/call' and scope['event_abi']==('memcpy' if op==0 else 'memmove') and scope['worker_scope']=='serial' and scope['alignment_min_bytes']==alignment and scope['transfer_basis']=='inferred' and scope['first_touch']=='preparation excluded' and scope['cache_state']=='prepared reused buffers; physical cache level unverified','cell construction scope differs')
        denominator=service['denominator'];proof=denominator['proof']
        require(denominator['level']=='source_normalized_work' and denominator['basis']=='measured' and proof['format']=='swdb.cpu-bulk-count-proof.v1','counted numerator missing')
        require(proof['source_sha256']==c['source_sha256'][SOURCES[0]] and proof['count_driver_sha256']==c['source_sha256'][SOURCES[2]] and proof['pipeline']==PIPELINE and proof['sizes']==sizes and all(hashed(proof.get(k)) for k in ('plugin_source_sha256','runtime_source_sha256')),'count/timing source or recipe differs')
        require(proof['visibility']=='Count-only always-inline exposes the identical shared loop; native elapsed wrappers remain noinline.' and proof['retention']=='Empty inline asm retains source memory work; counted indirect-call diagnostics are not ABI events.','count/native visibility or retention premise missing')
        points=proof['points']
        require(len(points)==4 and {(p['events'],p['invoke']) for p in points}=={(v,b) for v in (3,5) for b in (True,False)},'full service/driver count matrix missing')
        for point in points:
            require(type(point['events']) is int and type(point['invoke']) is bool and all(hashed(point.get(k)) for k in ('characterization_sha256','normalized_ir_sha256','source_map_sha256')),'count receipt identity missing')
            require(len(point['cells'])==len(matrix) and [(r['event_abi'],r['helper_function'],r['size_bytes']) for r in point['cells']]==matrix,'exact ABI/size/profile count matrix differs')
            sites=point['source_sites'];require(len(sites)==4 and {r['helper_function'] for r in sites}==set(FUNCTIONS) and len({r['site'] for r in sites})==4 and all(type(r['site']) is int and r['site']>=0 and type(r['line']) is int and r['line']>0 and r['normalized_name']=='llvm.'+('memcpy' if r['helper_function']==FUNCTIONS[0] else 'memmove')+'.p0.p0.i64' for r in sites),'exact source site projection missing')
            by_helper={r['helper_function']:r['site'] for r in sites}
            for cell in point['cells']:
                require(type(cell['executions']) is int and cell['executions']==(point['events'] if point['invoke'] else 0) and cell['source_sites']==[by_helper[cell['helper_function']]],'bulk source coefficient or site differs')
            counts=point['operation_counts'];require(set(counts)=={'integer','floating_point','branch','atomic'} and all(type(v) is int and v>=0 for v in counts.values()) and counts['floating_point']==0 and counts['atomic']==0,'constructed compute diagnostics differ')
        require(scope.get('residual_policy')=={'id':'both_windows_meet_declared_threshold','minimum_window_s':s['min_trial_s']},'paired residual resolution policy differs')
        trials=service['trials'];require(len(trials)==s['repetitions'],'paired repetitions differ')
        delta=((n+63)//64)*64+64 if op in (0,1) else 4 if op==2 else -4
        overlap=0 if op in (0,1) else n-4
        for i,t in enumerate(trials):
            require(type(t['events']) is int and 0<t['events']<=EVENT_CAP and finite(t['gross_seconds']) and t['gross_seconds']>=s['min_trial_s'] and finite(t['driver_seconds']) and t['driver_seconds']>=0 and t['order']==('service_first' if i%2==0 else 'driver_first'),'paired elapsed/work/order differs')
            require(t.get('checked_one_copy') is True and type(t.get('copied_size_bytes')) is int and t['copied_size_bytes']==n and type(t.get('source_destination_delta_bytes')) is int and t['source_destination_delta_bytes']==delta and type(t.get('overlap_bytes')) is int and t['overlap_bytes']==overlap and t.get('destination_alignment_min_bytes')==alignment and t.get('source_alignment_min_bytes')==alignment,'actual copy correctness/size/alias regime differs')
    # Finite unresolved residuals remain retained inputs with unknown service cost.



def main():
    p=argparse.ArgumentParser(description='distinct gross bulk-loop collection with retained short-driver diagnostics, no application timing')
    p.add_argument('--records',type=Path,default=paths.RECORDS);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixture',action='store_true');p.add_argument('--count-only',action='store_true')
    p.add_argument('--size',type=int,action='append');p.add_argument('--compiler',default='c++')
    p.add_argument('--llvm-bin',type=Path);p.add_argument('--toolchain-flag',action='append',default=[])
    p.add_argument('--machine',default='mbit10');p.add_argument('--lane')
    p.add_argument('--repetitions',type=int,default=7);p.add_argument('--min-trial-s',type=float,default=.05)
    p.add_argument('--max-wall-s',type=float,default=900);args=p.parse_args()
    try:print(json.dumps(calibrate(args)));return 0
    except (Failure,KeyError,TypeError,ValueError,OSError) as exc:print(str(exc),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())

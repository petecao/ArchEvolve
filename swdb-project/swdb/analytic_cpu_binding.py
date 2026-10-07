"""Prospective counts for the evaluator-owned fresh-process CPU driver. 2026-10-07 ET.

Only the canonical v1 driver is supported. Original advancing-lambda counts never
qualify. Markers are inserted into a derived counting wrapper, never the source
artifact or the uninstrumented native driver. Counted timer output is discarded.
"""
import copy
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

from swdb import access, artifacts, kernels
from swdb.cli import Failure

ADAPTER = 'registered-cpu.v1'
PROCESS_POLICY = 'one fresh process per source and repetition; graph construction before ROI'
CONTROL_PREFIXES = ('OMP_', 'KMP_', 'GOMP_', 'MALLOC_')
CONTROL_EXACT = ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES', 'LD_PRELOAD', 'LD_AUDIT', 'GLIBC_TUNABLES')
MARKER_DECLARATIONS = '\nextern "C" void __swdb_begin();\nextern "C" void __swdb_end();\nextern "C" void __swdb_source(unsigned long long);\n'


def controls(environment):
    return {**{k:v for k,v in environment.items() if k.startswith(CONTROL_PREFIXES) and v is not None},
            **{k:environment.get(k) for k in CONTROL_EXACT}}


def build_extensions(request):
    build = request.get('build', {})
    flags = build.get('toolchain_flags', [])
    if not isinstance(flags, list) or any(not isinstance(f,str) or not f.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for f in flags):
        raise Failure('protected CPU toolchain flags may only select installed headers/libraries')
    directories = build.get('run_library_paths', [])
    if not isinstance(directories,list) or any(not isinstance(p,str) or not Path(p).is_absolute() or not Path(p).is_dir() for p in directories):
        raise Failure('protected CPU runtime paths require available absolute library directories')
    return list(flags), [str(Path(p).resolve()) for p in directories]


def runtime_environment(store, request, threads):
    from swdb.bfs_native import runtime_environment as environment
    protocol = store.get(request.get('protocol'), 'protocol')
    policy = None if protocol is None else protocol['settings'].get('native_runtime')
    env, actual = environment(threads,policy,required=bool(protocol) and request.get('fixture') is not True)
    selections, directories = build_extensions(request)
    if protocol and (selections or directories):
        frozen=protocol['settings'].get('build',{})
        if frozen.get('toolchain_flags')!=selections or frozen.get('run_library_paths')!=directories:
            raise Failure('protected CPU toolchain/runtime selection differs from frozen native protocol')
    for name in ('LD_LIBRARY_PATH','DYLD_LIBRARY_PATH'):
        if directories:env[name]=os.pathsep.join(directories+([env[name]] if env.get(name) else []))
    return env, actual


def scope(store,request,candidate,plugin,compiler,flags,includes,source,workload,env):
    toolchain, directories = build_extensions(request)
    completed = subprocess.run([compiler,'--version'],capture_output=True,text=True,timeout=30)
    if completed.returncode:raise Failure('protected CPU compiler identity is unavailable')
    root = Path(candidate['artifact']['path']).resolve()
    return {'format':'swdb.protected-cpu-scope.v1','candidate':candidate['id'],
        'candidate_sha256':artifacts.digest(candidate),'source_snapshot':candidate['source_snapshot'],
        'source_root_sha256':candidate['artifact']['sha256'],'translation_unit_relative_path':source.relative_to(root).as_posix(),
        'translation_unit_sha256':artifacts.file_hash(source),'driver_template_sha256':artifacts.file_hash(plugin.native_driver),
        'timed_wrapper_sha256':hashlib.sha256(Path(plugin.native_driver).read_text().replace('#include SWDB_SOURCE_INCLUDE','#include '+json.dumps(str(source))).encode()).hexdigest(),
        'input':workload.get('id') or (request.get('analytic_input') if request.get('fixture') is True else None),'canonical_graph_sha256':workload['canonical_sha256'],
        'canonical_graph':{key:workload[key] for key in ('num_vertices','num_directed_edges','directed')},
        'machine':request['machine'],'roi':request['roi'],'threads':request['threads'],
        'sources':list(request['sources']),'repetitions':request['repetitions'],'process_policy':PROCESS_POLICY,
        'compiler_sha256':artifacts.file_hash(Path(compiler).resolve()),'compiler_version':completed.stdout.strip(),
        'build_flags':list(flags),'toolchain_flags':toolchain,'run_library_paths':directories,
        'include_relative_paths':[Path(p).relative_to(root).as_posix() for p in includes],
        'control_environment':controls(env),'control_scope':{'prefixes':list(CONTROL_PREFIXES),'exact_variables':list(CONTROL_EXACT),
          'absence_semantics':'null_or_absent_is_unset_under_declared_scope'},
        'timer_scope':'protected kernel invocation between steady_clock timestamps; counting observer and timer values are excluded'}


def prepare(store,args,subject,input_record):
    from swdb import bfs_native as native
    from swdb import bfs_native_scalable as scalable
    if subject['kind']!='candidate' or not args.evaluation_request:
        raise Failure('registered-cpu requires a candidate and a prospective --evaluation-request')
    request=access.read_record(args.evaluation_request)
    threads,repetitions,sources,_=native._request(request)
    if request['candidate']!=subject['id'] or threads!=args.threads:
        raise Failure('prospective CPU candidate or threads differ from characterize')
    if request.get('fixture') is not args.fixture and bool(request.get('fixture'))!=args.fixture:
        raise Failure('protected CPU fixture state must match the prospective evaluator request')
    if args.trials!=1 or args.function or args.build_flag or args.run_arg or args.region_map or args.source:
        raise Failure('registered-cpu derives one exact fresh-process source slot, wrapper, flags and ROI')
    if args.counting_pipeline not in (None,'source-normalized-v2'):
        raise Failure('registered-cpu requires source-normalized-v2')
    if scalable.is_scalable(scalable.request_evaluator(store,request)):
        raise Failure('registered-cpu currently supports only the canonical v1 protected driver; SG scopes remain unknown')
    implementation=store.get(subject['implementation'],'implementation')
    plugin=kernels.get(implementation['kernel'])
    if plugin is None or not plugin.native_entry_supported(implementation,subject) or request['roi']!=plugin.native_roi:
        raise Failure('prospective protected CPU kernel/ROI is unsupported')
    if not 0<=args.source_position<len(sources) or not 0<=args.repetition<repetitions:
        raise Failure('protected CPU source position/repetition is outside the prospective request')
    root=artifacts.verify(subject['artifact']);artifacts.check_protections(root,subject['protections'])
    native._protect_driver_macros(subject,root,driver=plugin.native_driver,extra_text=MARKER_DECLARATIONS)
    compiler,flags,includes,source,_=native._compile_settings(request,subject,root,plugin)
    from swdb.analytic import _llvm_bin
    llvm,_=_llvm_bin(args.llvm_bin)
    if Path(compiler).resolve()!= (llvm/'clang++').resolve():
        raise Failure('protected CPU counts require the same LLVM22 compiler as the prospective native evaluator')
    toolchain,libraries=build_extensions(request)
    if args.toolchain_flag and args.toolchain_flag!=toolchain:raise Failure('protected CPU toolchain selection differs from prospective evaluator')
    if args.run_library_path and [str(p.resolve()) for p in args.run_library_path]!=libraries:raise Failure('protected CPU runtime library selection differs from prospective evaluator')
    args.toolchain_flag=toolchain;args.run_library_path=[Path(p) for p in libraries]
    supplied=request['workload']
    if isinstance(supplied,dict) and set(supplied)=={'id'}:
        from swdb.bfs_protocol import materialize_workload
        if supplied['id']!=input_record['id']:raise Failure('protected CPU registered workload differs from --input')
        supplied=materialize_workload(store,supplied['id'])
    elif not args.fixture:
        raise Failure('native protected CPU counting requires an immutable registered workload ID')
    canonical,workload=native.canonical_graph(supplied)
    workload['id']=input_record['id']
    if any(s>=canonical['num_vertices'] for s in sources):raise Failure('protected CPU source exceeds canonical graph')
    env,actual=runtime_environment(store,request,threads)
    context=scope(store,request,subject,plugin,compiler,flags,includes,source,workload,env)
    parent=Path(args.output).resolve().parent if args.output else Path(tempfile.gettempdir())
    parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='swdb-protected-cpu-wrapper-',dir=parent))
    graph=work/'graph.swdb'
    with graph.open('w') as out:
        out.write(f"SWDBGRAPH1 {canonical['num_vertices']} {workload['num_directed_edges']} {int(canonical['directed'])}\n")
        for u,row in enumerate(canonical['adjacency']):
            for v in row:out.write(f'{u} {v}\n')
    template=Path(plugin.native_driver).read_text()
    wrapper=template.replace('#include SWDB_SOURCE_INCLUDE','#include '+json.dumps(str(source)))
    matches=list(re.finditer(r'^        auto (parent|scores) = (DOBFS|Brandes)\([^\n]+;\s*$',wrapper,re.M))
    if len(matches)!=1:raise Failure('protected CPU kernel invocation is not exactly one declared driver site')
    match=matches[0]
    instrumented=wrapper[:match.start()]+'        __swdb_begin();\n        __swdb_source(static_cast<unsigned long long>(source));\n'+match.group()+'\n        __swdb_end();'+wrapper[match.end():]
    instrumented=instrumented.replace('#undef main','#undef main'+MARKER_DECLARATIONS,1)
    derived=work/'counting_driver.cc';derived.write_text(instrumented)
    output=work/'counted-result.json';slot={'source_position':args.source_position,'repetition':args.repetition,'source':sources[args.source_position]}
    run=[str(graph),str(slot['source']),str(output)]
    identity={'adapter':ADAPTER,'application':subject['context']['application'],'source_snapshot':subject['source_snapshot'],
        'candidate_artifact_sha256':subject['artifact']['sha256'],'candidate_diff_sha256':subject.get('diff_sha256'),
        'source_root_sha256':subject['artifact']['sha256'],'translation_unit_sha256':artifacts.file_hash(derived),
        'protected_source_sha256':artifacts.file_hash(source),'driver_template_sha256':artifacts.file_hash(plugin.native_driver),
        'timed_wrapper_sha256':context['timed_wrapper_sha256'],'trial_count':1,'source_selection':'fixed_protected_source_slot',
        'source_policy':PROCESS_POLICY,'process_policy':PROCESS_POLICY,'slot':slot,'evaluation_scope':context,
        'evaluation_scope_sha256':artifacts.digest(context),'counting_wrapper_sha256':artifacts.file_hash(derived),
        'marker_derivation':'existing __swdb_source/begin/end only around the exact protected kernel invocation',
        'timer_outputs_used_for_counts':False,'region_bindings':[]}
    return {'source':derived,'artifact_root':root,'flags':[*flags,*('-I'+str(p) for p in includes)],'run':run,
        'roi':plugin.native_roi,'mapping':{'regions':[]},'identity':identity,'explicit_roi':True,
        'environment':env,'canonical':canonical,'plugin':plugin,'graph':{**context['canonical_graph'],'num_nodes':canonical['num_vertices'],
            'canonical_sha256':workload['canonical_sha256']},'ambiguous_helper_loops':[]}


def verify(record,store,require_available=False):
    from swdb.analytic_binding import counted_payload
    binding=record['binding'];si=binding['subject_source_identity'];receipt=binding.get('execution_receipt',{});problems=[]
    subject=store.get(record['subject']['id'],'candidate');inp=store.get(record['input'])
    if subject is None or inp is None:return ['protected CPU candidate/input unavailable']
    context=si.get('evaluation_scope',{});slot=si.get('slot',{})
    expected_state='fixture' if record.get('evidence_kind')=='contract_fixture' else 'verified'
    if binding.get('state')!=expected_state:
        problems.append('protected CPU evidence state differs')
    manifest={row['path']:row['sha256'] for row in subject['artifact']['files']}
    source_relative=context.get('translation_unit_relative_path')
    if manifest.get(source_relative)!=context.get('translation_unit_sha256') or si.get('protected_source_sha256')!=context.get('translation_unit_sha256'):
        problems.append('protected CPU source manifest differs')
    if si.get('source_snapshot')!=subject['source_snapshot'] or si.get('candidate_artifact_sha256')!=subject['artifact']['sha256'] or si.get('candidate_diff_sha256')!=subject.get('diff_sha256'):
        problems.append('protected CPU candidate lineage differs')
    if si.get('timed_wrapper_sha256')!=context.get('timed_wrapper_sha256') or si.get('source_selection')!='fixed_protected_source_slot':
        problems.append('protected CPU wrapper/source-slot derivation differs')
    if si.get('marker_derivation')!='existing __swdb_source/begin/end only around the exact protected kernel invocation':
        problems.append('protected CPU marker contract differs')
    root=Path(subject['artifact']['path']).resolve()
    expected_flags=context.get('build_flags',[])+['-I'+str(root/p) for p in context.get('include_relative_paths',[])]
    if record['source'].get('build_flags')!=expected_flags or record['toolchain'].get('compiler_flags')!=context.get('toolchain_flags') or record['toolchain'].get('run_library_paths')!=context.get('run_library_paths'):
        problems.append('protected CPU build/runtime selection differs')
    if si.get('adapter')!=ADAPTER or receipt.get('adapter')!=ADAPTER:return ['protected CPU adapter identity differs']
    if context.get('format')!='swdb.protected-cpu-scope.v1' or artifacts.digest(context)!=si.get('evaluation_scope_sha256'):
        problems.append('protected CPU prospective context differs')
    if context.get('candidate')!=subject['id'] or context.get('candidate_sha256')!=artifacts.digest(subject) or context.get('source_root_sha256')!=subject['artifact']['sha256']:
        problems.append('protected CPU source/candidate identity differs')
    if binding['input_record_sha256']!=artifacts.digest(inp) or context.get('input')!=record['input']:
        problems.append('protected CPU input identity differs')
    native=record.get('observation_contract',{}).get('native_runtime',{})
    if native.get('compiler_sha256')!=context.get('compiler_sha256') or native.get('compiler_version')!=context.get('compiler_version') or controls(native.get('environment',{}))!=context.get('control_environment'):
        problems.append('protected CPU counted compiler/control observation differs')
    if context.get('process_policy')!=PROCESS_POLICY or binding['roi']!=context.get('roi') or binding['threads']!=context.get('threads'):
        problems.append('protected CPU process/ROI/thread scope differs')
    sources=context.get('sources',[]);position=slot.get('source_position');repetition=slot.get('repetition')
    if type(position) is not int or not 0<=position<len(sources) or type(repetition) is not int or not 0<=repetition<context.get('repetitions',0) or slot.get('source')!=sources[position]:
        problems.append('protected CPU source slot differs')
    if record['source']['run_arguments'][1:2]!=[str(slot.get('source'))] or len(record.get('trials',[]))!=1 or record['trials'][0]['sources']!=[slot.get('source')] or record['trials'][0]['position']!=0:
        problems.append('protected CPU counted source window differs')
    if si.get('counted_correctness',{}).get('passed') is not True or si.get('counted_correctness',{}).get('timer_outputs_used') is not False:
        problems.append('protected CPU counted correctness evidence differs')
    if record['source']['sha256']!=si.get('counting_wrapper_sha256') or si.get('timer_outputs_used_for_counts') is not False:
        problems.append('protected CPU marker derivation differs')
    expected={'format':'swdb.registered-count-receipt.v1','subject_record_sha256':artifacts.digest(subject),
        'source_root_sha256':subject['artifact']['sha256'],'source_sha256':record['source']['sha256'],
        'input_record_sha256':binding['input_record_sha256'],'run_arguments_sha256':binding['run_arguments_sha256'],
        'roi':binding['roi'],'threads':binding['threads'],'trial_count':1,'pipeline_version':'source-normalized-v2',
        'passes':['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)'],
        'llvm_version':record['toolchain']['llvm_version'],'binary_sha256':record['counting']['binary_sha256'],
        'counts_sha256':record['counting']['counts_sha256'],'source_ir_sha256':record['static_analysis']['source_ir_sha256'],
        'optimized_ir_sha256':record['static_analysis']['optimized_ir_sha256'],'counted_payload_sha256':artifacts.digest(counted_payload(record))}
    for name,value in expected.items():
        if receipt.get(name)!=value:problems.append('protected CPU execution receipt differs: '+name)
    if receipt.get('graph',{}).get('canonical_sha256')!=context.get('canonical_graph_sha256') or any(receipt.get('graph',{}).get(key)!=value for key,value in context.get('canonical_graph',{}).items()) or record['coverage'].get('whole_timed_call') is not True:
        problems.append('protected CPU whole-call graph/ROI differs')
    if require_available:
        root=artifacts.verify(subject['artifact']);source=root/context['translation_unit_relative_path']
        plugin=kernels.get(store.get(subject['implementation'],'implementation')['kernel'])
        if artifacts.file_hash(source)!=context['translation_unit_sha256'] or artifacts.file_hash(plugin.native_driver)!=context['driver_template_sha256']:
            problems.append('protected CPU source/driver changed during counting')
        folder=Path(record['counting']['output_directory'])
        for name,key in [('counts.json','counts_sha256'),('counted','binary_sha256')]:
            if artifacts.file_hash(folder/name)!=record['counting'][key]:problems.append('protected CPU counted artifact changed: '+name)
    return problems


def finish(adapter,record,store):
    from swdb import analytic_binding
    # Read source/ROI/output identity only. Instrumented duration is not admitted.
    from swdb.bfs_native import json_observation
    observed,_=json_observation(Path(adapter['run'][2]),adapter['plugin'].native_output_limit(adapter['canonical']['num_vertices']),'protected counted driver output')
    slot=adapter['identity']['slot']
    if observed.get('source')!=slot['source'] or observed.get('roi')!=adapter['roi'] or observed.get('configured_threads')!=record['binding']['threads']:
        raise Failure('protected counted driver source/ROI/thread output differs')
    check=adapter['plugin'].check_native_trial(adapter['canonical']['adjacency'],slot['source'],observed,application=adapter['identity']['application'])
    if not check['passed']:raise Failure('protected counted driver independent correctness failed: '+str(check['reason']))
    adapter['identity']['counted_correctness']={'passed':True,'verifier':adapter['plugin'].native_verifier,'timer_outputs_used':False}
    # source_identity has already copied adapter fields; retain the new correctness check there too.
    record['binding']['subject_source_identity']['counted_correctness']=adapter['identity']['counted_correctness']
    record['coverage']['scope']='protected_cpu_kernel_invocation'
    record['binding']['note']='Exact prospective canonical graph/source slot and fresh protected evaluator process. Derived markers only; counted timer output is unused. No original-driver error-band transfer.'
    record['binding']['execution_receipt']=analytic_binding.execution_receipt(record,adapter['graph'],
        Path(__file__).with_name('llvm')/'Characterize.cpp',Path(__file__).with_name('llvm')/'CountingRuntime.cpp')
    issues=verify(record,store,require_available=True)
    if issues:raise Failure('protected CPU execution binding failed: '+'; '.join(issues))

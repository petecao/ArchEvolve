"""Prepare/read validation evidence for the pinned DX100 16K reference.

No build, benchmark, simulator or scheduler commands are executed by this module.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import configparser
import json
import math
import re
import subprocess

from archevolve.dx100_parameter_adapter import SOURCE,read_handoff
from archevolve.evolution_store import digest
from tools.render_mermaid import RequestError

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT/'docs/designs/dx100-parameter-domain'
EXTRA_SOURCES=['benchmarks/gapbs/Makefile','benchmarks/gapbs/src/benchmark.h','benchmarks/gapbs/src/command_line.h',
    'benchmarks/gapbs/src/converter.cc','benchmarks/gapbs/src/util.h','benchmarks/gapbs/src/generator.h',
    'benchmarks/gapbs/src/builder.h','benchmarks/gapbs/src/writer.h','benchmarks/API/MAA_functional.hpp',
    'configs/common/Simulation.py','configs/common/MemConfig.py','src/mem/ramulator2.cc','configs/deprecated/example/se.py','scripts/sim.py','ext/ramulator2/SConscript','ext/ramulator2/ramulator2/CMakeLists.txt']
BINARY_NAMES=('converter','functional-baseline','functional-dx100','gem5-baseline','gem5-dx100')


def require(ok,message):
    if not ok: raise RequestError('DX100 validation: '+message)


def file_hash(path):
    h=sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def prepare(source_root):
    require((Path(source_root)/'.git').exists(),'A local pinned DX100 Git checkout is required.')
    contract,ch,verification,_,ph=read_handoff(DOMAIN/'contract.yaml',DOMAIN/'verification.json',DOMAIN/'published-dx100-calibration.json')
    # Reading pinned Git blobs is independent of local sparse-checkout population.
    files={s['path']:s['sha256'] for s in contract['source_files']}
    for name in list(files)+EXTRA_SOURCES:
        blob=subprocess.check_output(['git','-C',str(source_root),'show',SOURCE+':'+name])
        h=sha256(blob).hexdigest()
        if name in files: require(h==files[name],'Pinned Git object differs from contract: '+name)
        files[name]=h
    # Include all public API/GAP headers in the build-source closure, not just the files cited in the handoff.
    names=subprocess.check_output(['git','-C',str(source_root),'ls-tree','-r','--name-only',SOURCE,
        'benchmarks/gapbs/src','benchmarks/API'],text=True).splitlines()
    for name in names:
        if name.endswith(('.h','.hpp')) and name not in files:
            files[name]=sha256(subprocess.check_output(['git','-C',str(source_root),'show',SOURCE+':'+name])).hexdigest()
    defaults={p['id']:p['reference_default'] for p in contract['parameters']}
    require(defaults['num_tile_elements']==16384 and defaults['num_cores']==4 and defaults['num_maas']==1,'Unexpected reference profile.')
    effective={**defaults,'max_outstanding_cache_side_packets':32768,'max_outstanding_cpu_side_packets':32768}
    workflows=[]
    for kind,flag in [('kronecker','-g'),('uniform','-u')]:
        workflows.append({'id':kind+'18-root0','generator_argv':['{converter}',flag,'18','-k','16','-b','{graph}'],
            'generator_seed':27491095,'root':0,'trials':1,
            'benchmark_options':['-f','{graph}','-r','0','-n','1','-v','-l','-a'],
            'input_binding':'Generate once, hash the serialized .sg, and use the identical file in baseline and DX100 runs.'})
    plan={'format':'dx100-reference-validation-v0.1','source_commit':SOURCE,'domain_contract_sha256':ch,
        'published_evidence_sha256':ph,'source_files':files,'tile_elements':16384,
        'tool_sha256':{n:file_hash(ROOT/n) for n in ('archevolve/dx100_validation.py','archevolve/dx100_validation_cli.py')},
        'scope':'Pinned authors standalone TDStepMAA and TDStep control; not the hybrid or proposed CPU-CAS read-offload rewrite.',
        'declared_model_defaults':defaults,'expected_effective_model_parameters':effective,
        'effective_override_basis':{'source':'configs/common/MAAConfig.py:143-156',
            'formula':'max(512, 2 * num_maas * num_tile_elements)',
            'note':'Stock launcher overrides both packet capacities. Do not blindly freeze the SimObject default 512.'},
        'compile_constants':{'TILE_SIZE':16384,'NUM_CORES':4,'NUM_TILES_PER_CORE':8,'NUM_REGS_PER_CORE':8,'MEM_SIZE':0x400000000},
        'guest_environment':{'OMP_NUM_THREADS':'4','OMP_DYNAMIC':'FALSE','OMP_PROC_BIND':'false'},
        'workloads':workflows,
        'required_target_counters':['system.maa.numInst_INDRD','system.maa.numInst_RANGE'],
        'stats_policy':'Select one complete ROI stats block explicitly; never silently use the final block or divide ticks by 313.',
        'verifier_exit_issue':'Both GEM5 kernels call m5_exit before returning to BenchmarkKernel/BFSVerifier. Stock benchCheckpoints stops on non-checkpoint exit. A separately reviewed continuation/verification method is required for target correctness.',
        'baseline_issue':'Stock DOBFS also allocates/initializes MAA before ROI. Target CPU control needs the same MAA memory mapping, with read/range instruction counters zero inside ROI; a no-MAA baseline requires a separately reviewed source change.',
        'timing_validation':'Independent timing/model validation remains outstanding even if correctness and intended-path checks pass.',
        'execution_performed':False,'target_validated':False,'speedup':None}
    env={'format':'dx100-validation-environment-v0.1','workflow_sha256':digest(plan),
        'source_root':None,'platform':{'host':None,'os':None,'architecture':None,'toolchain_version':None},
        'tools':{'cxx':None,'cc':None,'cmake':None,'make':None,'scons':None,'gem5':None},
        'build_root':None,'run_root':None,'build_jobs':None,
        'great_lakes':{'account':None,'partition':None,'cpus_per_task':None,'memory':None,'walltime':None},
        'target':{'memory_size_bytes':None,'cpu_model':None,'cpu_clock':None,'cache_configuration':None,
                  'ramulator_config':None,'ramulator_config_sha256':None,'dram_topology':None,
                  'guest_env_file':None,'guest_env_sha256':sha256(guest_env_text(plan).encode()).hexdigest(),
                  'system_argv':None,'launcher':None,'launcher_sha256':None,'checkpoint_policy':None,
                  'verifier_continuation_review':None,'resource_address_review':None},
        'note':'Unbound site/target settings are blockers, not inferred defaults. No job submission is implemented.'}
    common=['-std=c++11','-O3','-Wall','-g3','-fopenmp','-DNUM_CORES=4','-DTILE_SIZE=16384','-I{source}/benchmarks/API']
    build={'format':'dx100-reference-build-recipes-v0.1','workflow_sha256':digest(plan),'execute':False,
        'recipes':[
            {'id':'ramulator-configure','cwd':'{source}/ext/ramulator2/ramulator2','argv':['{cmake}','-S','.','-B','{source}/ext/ramulator2/ramulator2/build','-DCMAKE_C_COMPILER={cc}','-DCMAKE_CXX_COMPILER={cxx}'],'status':'template_requires_linkage_review'},
            {'id':'ramulator-build','cwd':'{source}','argv':['{cmake}','--build','{source}/ext/ramulator2/ramulator2/build','-j','{jobs}'],'status':'template_requires_linkage_review'},
            {'id':'m5ops-build','cwd':'{source}/util/m5','argv':['{scons}','build/x86/out/m5','-j{jobs}']},
            {'id':'gem5-build','cwd':'{source}','argv':['{scons}','build/X86/gem5.opt','-j{jobs}']},
            {'id':'converter','cwd':'{build}','argv':['{cxx}','-std=c++11','-O3','-fopenmp','{source}/benchmarks/gapbs/src/converter.cc','-o','{build}/converter']},
            {'id':'fresh-m5op-object','cwd':'{build}','argv':['{cxx}','-I{source}/include','-I{source}/util/m5/src','-c','{source}/util/m5/build/x86/abi/x86/m5op.S','-o','{build}/m5op.o']}],
        'notes':['Recipes are unexecuted argv templates, not shell strings. Bind paths and toolchain on Great Lakes.',
                 'Ramulator uses its source-local build directory per the artifact; ext/ramulator2/SConscript links from the Ramulator source root. Confirm the produced library location and archive its hash.',
                 'Use fresh output names/object files; do not reuse the repository-shipped m5op.o or binaries.',
                 'Capture command argv, cwd, allowlisted environment, compiler version, exit status, stdout/stderr, macro dump and binary/object hashes.',
                 'Native FUNC binaries provide only functional-model evidence. Never execute a GEM5/MMIO binary natively.']}
    for mode,define in [('functional','-DFUNC'),('gem5','-DGEM5')]:
        for variant in ('baseline','dx100'):
            argv=['{cxx}',*common,define]+(['-DMAA'] if variant=='dx100' else [])
            if mode=='gem5':argv+=['-I{source}/include','-I{source}/util/m5/src']
            argv+=['{source}/benchmarks/gapbs/src/bfs.cc']
            if mode=='gem5':argv+=['{build}/m5op.o']
            argv+=['-o','{build}/bfs-'+mode+'-'+variant]
            build['recipes'].append({'id':mode+'-'+variant,'cwd':'{build}','argv':argv})
    run={'format':'dx100-reference-run-plan-v0.1','workflow_sha256':digest(plan),'execute':False,
        'sequence':['Bind environment/source/build provenance','Build and pin converter/functional/target artifacts',
                    'Generate and hash each .sg once','Run functional baseline and functional DX100 on identical graphs',
                    'Resolve target topology/config and verifier exit handling','Run target baseline and target DX100 separately',
                    'Collect raw evidence and compare frontiers','Request independent timing review before performance claims'],
        'guest_environment':plan['guest_environment'],'workloads':workflows,
        'target_argv':None,'target_argv_status':'Requires reviewed complete CPU/cache/clock/Ramulator/MAA and exit/checkpoint launcher settings.',
        'required_target_settings':{'maa_enabled_for_both_variants':True,'num_cpus':4,'mem_channels':2,'mem_size_bytes':0x400000000,
            'maa_num_maas':1,'maa_num_tile_elements':16384,'maa_num_initial_row_table_slices':32,
            'maa_reconfigure_row_table':False,'maa_no_reorder':False,'maa_force_cache_access':False,
            'guest_environment_option':'--env {guest_env_file}'},
        'note':'Simulated cores/workers are not a Slurm CPU allocation. Resource requests stay unbound.'}
    receipt={'format':'dx100-validation-receipt-v0.1','workflow_sha256':digest(plan),'environment_sha256':None,
        'workload_id':None,'mode':None,'variant':None,'completion':'not_run','exit_code':None,
        'benchmark_argv':None,'command_argv':None,'guest_environment':None,'stats_block_index':None,
        'artifacts':{k:None for k in ('stdout','stderr','binary','graph','graph_receipt','build_receipt','macro_dump','config_ini','stats','launcher','exit_events','simulator','ramulator_config','ramulator_library','guest_env_file')},
        'note':'Each artifact is {path, sha256}; use absolute paths or paths relative to this receipt. Native and gem5 runs use separate receipts.'}
    return plan,env,build,run,receipt


def geometry(topology,initial=32):
    if topology is None:return {'status':'unresolved','reason':'Actual DRAM topology is unbound.'}
    fields=('channels','ranks','bankgroups','banks')
    if not isinstance(topology,dict) or set(topology)!=set(fields) or not all(type(topology[k]) is int and topology[k]>0 for k in fields):
        return {'status':'rejected','reason':'Four positive integral topology dimensions required.'}
    dims=[topology[k] for k in fields];total=math.prod(dims);minimum=2*dims[0]*dims[1]
    if dims[0]!=2 or total%minimum or total//minimum & (total//minimum-1) or total<minimum:
        return {'status':'rejected','reason':'Two reference channels and integral power-of-two slice ratio required.'}
    family=[];slices=minimum
    while slices<=total:
        remaining=slices;organization=[]
        for dim in dims:
            if remaining>dim:
                if remaining%dim:return {'status':'rejected','reason':'Source slice-factor divisibility guard fails.'}
                organization.append(dim);remaining//=dim
            elif remaining:
                if dim%remaining:return {'status':'rejected','reason':'Uniform bank coverage/divisibility unresolved.'}
                organization.append(remaining);remaining=0
            else:organization.append(1)
        if remaining or math.prod(organization)!=slices:return {'status':'rejected','reason':'Slice index coverage fails.'}
        family.append(slices);slices*=2
    return {'status':'necessary_geometry_pass' if initial in family else 'rejected','slice_family':family,
            'initial_slices':initial,'reason':'Necessary arithmetic only; not a hardware correctness/timing proof.'}


def preflight(plan,env):
    require(env.get('workflow_sha256')==digest(plan),'Environment refers to a different workflow.')
    missing=[];failures=[];verified={}
    for key in ('source_root','build_root','run_root','build_jobs'):
        if env.get(key) is None:missing.append(key)
    root=env.get('source_root')
    if root:
        try:
            head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
            dirty=subprocess.check_output(['git','-C',str(root),'diff','--name-only','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
            if head!=SOURCE:failures.append('checkout_revision_mismatch')
            if dirty:failures.append('tracked_checkout_changes_require_review')
        except (OSError,subprocess.CalledProcessError):failures.append('source_git_identity_unavailable')
        for name,expected in plan['source_files'].items():
            path=Path(root)/name
            if not path.is_file():missing.append('source:'+name)
            elif file_hash(path)!=expected:failures.append('source_hash:'+name)
            else:verified[name]=expected
    sections={'platform':('host','os','architecture','toolchain_version'),
              'tools':('cxx','cc','cmake','make','scons','gem5'),
              'great_lakes':('account','partition','cpus_per_task','memory','walltime')}
    for section,keys in sections.items():
        for key in keys:
            value=env.get(section,{}).get(key)
            if value is None or value=='':missing.append(section+'.'+key)
            elif section=='tools' and (not isinstance(value,str) or not Path(value).is_file()):failures.append('tool_path:'+key)
    if env.get('build_jobs') is not None and (type(env['build_jobs']) is not int or env['build_jobs']<=0):failures.append('build_jobs_must_be_positive_integer')
    platform=env.get('platform',{})
    if platform.get('os') not in (None,'Linux'):failures.append('requires_Linux_execution_environment')
    if platform.get('architecture') not in (None,'x86_64'):failures.append('requires_x86_64_target_toolchain_environment')
    for key in ('memory_size_bytes','cpu_model','cpu_clock','cache_configuration','ramulator_config',
                'ramulator_config_sha256','dram_topology','system_argv','launcher','launcher_sha256',
                'checkpoint_policy','verifier_continuation_review','resource_address_review','guest_env_file','guest_env_sha256'):
        if env.get('target',{}).get(key) is None:missing.append('target.'+key)
    target=env.get('target',{})
    if target.get('memory_size_bytes') not in (None,0x400000000):failures.append('memory_size_must_match_compiled_16GiB_API')
    for key in ('verifier_continuation_review','resource_address_review'):
        review=target.get(key)
        if review is not None and (not isinstance(review,dict) or not all(review.get(k) for k in ('reviewer','description','evidence_refs'))):
            failures.append('invalid_review:'+key)
    if target.get('system_argv') is not None and (not isinstance(target['system_argv'],list) or not target['system_argv'] or not all(isinstance(x,str) and x for x in target['system_argv'])):
        failures.append('system_argv_requires_explicit_argument_list')
    geo=geometry(target.get('dram_topology'))
    if geo['status']=='rejected':failures.append('dram_slice_geometry')
    for key in ('ramulator_config','launcher'):
        path=target.get(key);expected=target.get(key+'_sha256')
        if path and expected:
            if not Path(path).is_file() or file_hash(path)!=expected:failures.append(key+'_hash')
    guest_path=target.get('guest_env_file')
    if guest_path:
        if not Path(guest_path).is_file() or Path(guest_path).read_text()!=guest_env_text(plan):failures.append('guest_environment_file_mismatch')
        elif file_hash(guest_path)!=target.get('guest_env_sha256'):failures.append('guest_environment_hash_mismatch')
        args=target.get('system_argv') or []
        env_values=[a.split('=',1)[1] for a in args if isinstance(a,str) and a.startswith('--env=')]
        env_values += [args[i+1] for i,a in enumerate(args[:-1]) if a=='--env']
        if env_values!=[guest_path]:failures.append('explicit_guest_env_option_required')
    return {'format':'dx100-validation-preflight-v0.1','workflow_sha256':digest(plan),'environment_sha256':digest(env),
        'status':'rejected' if failures else 'blocked_unbound_environment' if missing else 'inputs_present_pending_manual_review',
        'missing':missing,'failures':failures,'verified_source_files':verified,'geometry':geo,
        'ready_to_execute':False,'target_validated':False,'note':'This preparatory checker never submits jobs or certifies a target.'}


def check_config(text,expected):
    parser=configparser.ConfigParser(interpolation=None,strict=True)
    try:parser.read_string(text)
    except configparser.Error as exc:return {'status':'rejected','errors':[str(exc)]}
    sections=[s for s in parser.sections() if parser.has_option(s,'num_tile_elements') and parser.has_option(s,'num_maas')]
    if len(sections)!=1:return {'status':'unresolved','errors':['Need exactly one identified MAA SimObject section.']}
    section=sections[0];missing=[];mismatches=[]
    for key,value in expected.items():
        raw=parser.get(section,key,fallback=None)
        if raw is None:missing.append(key);continue
        try:
            actual={'true':True,'false':False}[raw.lower()] if type(value) is bool else int(raw)
        except (ValueError,KeyError):mismatches.append(key);continue
        if actual!=value:mismatches.append(key)
    return {'status':'rejected' if mismatches else 'unresolved' if missing else 'reference_parameters_observed',
        'section':section,'missing':missing,'mismatches':mismatches,
        'note':'MAA scalar parameters only; CPU/cache/clock/MMIO/Ramulator/launcher configuration also requires review.'}


def stats_blocks(text):
    blocks=[];current=None
    for line in text.splitlines():
        if 'Begin Simulation Statistics' in line:
            if current is not None:raise RequestError('Nested/incomplete stats blocks.')
            current={}
        elif 'End Simulation Statistics' in line:
            if current is None:raise RequestError('Unmatched stats block end.')
            blocks.append(current);current=None
        elif current is not None:
            tokens=line.split()
            if len(tokens)>=2 and not tokens[0].startswith('#'):
                if tokens[0] in current:raise RequestError('Duplicate stat key in one block.')
                try:v=float(tokens[1])
                except ValueError:continue
                current[tokens[0]]=v if math.isfinite(v) else None
    if current is not None:raise RequestError('Incomplete stats block.')
    return blocks


def analyze_logs(stdout,stderr,mode,variant,completion,exit_code,stats=None,block_index=None,counters=None):
    require(mode in {'functional','gem5'} and variant in {'baseline','dx100'},'Specify mode and variant.')
    failures=[];missing=[]
    tokens=re.findall(r'^\s*Verification:\s*(PASS|FAIL)\s*$',stdout,re.M)
    if 'FAIL' in tokens:failures.append('BFSVerifier_FAIL')
    elif tokens!=['PASS']:missing.append('exactly_one_BFSVerifier_PASS_required')
    if re.search(r'(panic:|fatal:|assertion.*failed|segmentation fault|SIGSEGV)',stdout+'\n'+stderr,re.I):failures.append('runtime_failure_diagnostic')
    if completion!='completed':missing.append('run_not_completed')
    if exit_code is None:missing.append('exit_code_unbound')
    elif type(exit_code) is not int:failures.append('invalid_exit_code')
    elif exit_code!=0:
        if completion=='completed':failures.append('nonzero_exit_code')
        else:missing.append('interrupted_or_incomplete_exit')
    prefix='TDStepMAA' if variant=='dx100' else 'TDStep'
    frontier=[int(x) for x in re.findall(r'^Starting '+prefix+r':\s*(\d+) elements\s*$',stdout,re.M)]
    if not frontier:missing.append('per_level_frontier_log_missing')
    witness='not_applicable_functional_model';raw_stats=None
    if mode=='gem5':
        if stdout.count('ROI started:')!=1 or stdout.count('ROI End!!!')!=1:missing.append('unambiguous_ROI_markers_required')
        if stats is None or type(block_index) is not int or block_index<0:missing.append('explicit_complete_ROI_stats_block_required');witness='unresolved'
        else:
            try:
                blocks=stats_blocks(stats)
                require(block_index<len(blocks),'Stats block index out of bounds.')
                raw_stats=blocks[block_index]
                values=[raw_stats.get(k) for k in counters]
                if any(v is None for v in values):missing.append('required_counter_missing');witness='unresolved'
                elif any(v<0 or v!=int(v) for v in values):failures.append('invalid_instruction_counter');witness='refuted'
                elif (variant=='dx100' and all(v>0 for v in values)) or (variant=='baseline' and all(v==0 for v in values)):
                    witness='required_activity_observed' if variant=='dx100' else 'idle_accelerator_observed'
                elif completion=='completed':failures.append('required_execution_witness_failed');witness='refuted'
                else:missing.append('execution_witness_incomplete_run');witness='unresolved'
            except RequestError as exc:missing.append(str(exc));witness='unresolved'
    return {'status':'refuted' if failures else 'inconclusive' if missing else 'log_checks_passed_pending_provenance_and_review',
        'failures':failures,'missing':missing,'verifier_tokens':tokens,'frontier_sizes':frontier,
        'intended_path_observation':witness,'selected_stats_block':block_index,'raw_roi_stats':raw_stats,
        'target_timing_validated':False,'latency_ms':None,'speedup':None}


def check_macros(text,plan,mode,variant):
    definitions=dict(re.findall(r'^#define[ \t]+(\w+)(?:[ \t]+([^\r\n]*))?$',text,re.M))
    missing=[];errors=[]
    constants=plan['compile_constants'] if mode=='gem5' else {k:v for k,v in plan['compile_constants'].items() if k!='MEM_SIZE'}
    for key,wanted in constants.items():
        if key not in definitions:missing.append(key);continue
        try:actual=int(definitions[key].split()[0],0)
        except (ValueError,IndexError):errors.append(key);continue
        if actual!=wanted:errors.append(key)
    if ('MAA' in definitions)!=(variant=='dx100'):errors.append('MAA_definition')
    if ('FUNC' in definitions)!=(mode=='functional') or ('GEM5' in definitions)!=(mode=='gem5'):errors.append('execution_mode_definitions')
    return {'status':'rejected' if errors else 'unresolved' if missing else 'expected_definitions_observed','missing':missing,'mismatches':errors}


def collect(plan,env,receipt,base):
    require(receipt.get('format')=='dx100-validation-receipt-v0.1','Unsupported receipt format.')
    require(receipt.get('workflow_sha256')==digest(plan),'Receipt workflow mismatch.')
    if receipt.get('environment_sha256') is not None:
        require(receipt['environment_sha256']==digest(env),'Receipt environment mismatch.')
    missing=[];errors=[];evidence={};loaded={}
    if receipt.get('environment_sha256') is None:missing.append('environment_hash_unbound')
    mode,variant=receipt.get('mode'),receipt.get('variant')
    common={'stdout','stderr','binary','graph','graph_receipt','build_receipt','macro_dump'}
    required=common|({'config_ini','stats','launcher','exit_events','simulator','ramulator_config','ramulator_library','guest_env_file'} if mode=='gem5' else set())
    for name in sorted(required):
        entry=receipt.get('artifacts',{}).get(name)
        if entry is None:missing.append('artifact:'+name);continue
        require(isinstance(entry,dict) and set(entry)=={'path','sha256'},'Artifact entry requires path and sha256.')
        if not entry['path'] or not entry['sha256']:missing.append('artifact_binding:'+name);continue
        path=Path(entry['path']);path=path if path.is_absolute() else base/path
        if not path.is_file():missing.append('artifact_file:'+name);continue
        actual=file_hash(path)
        if actual!=entry['sha256']:errors.append('artifact_hash:'+name);continue
        evidence[name]={'path':str(path.resolve()),'sha256':actual,'bytes':path.stat().st_size}
        if name not in {'binary','graph','simulator','ramulator_library'}:
            if path.stat().st_size>64*1024*1024:missing.append('text_artifact_exceeds_reader_budget:'+name);continue
            loaded[name]=path.read_text(errors='replace')
    workloads={w['id']:w for w in plan['workloads']}
    workload=workloads.get(receipt.get('workload_id'))
    if workload is None:missing.append('workload_id_unbound')
    if receipt.get('guest_environment') is None:missing.append('guest_environment_unbound')
    elif receipt['guest_environment']!=plan['guest_environment']:errors.append('guest_environment_mismatch')
    if not isinstance(receipt.get('command_argv'),list) or not receipt['command_argv']:missing.append('command_argv_unbound')
    if workload and 'graph' in evidence and 'binary' in evidence:
        # Receipt argv records original paths; normalize only the recorded graph/binary operand positions.
        args=receipt.get('benchmark_argv')
        if not isinstance(args,list) or len(args)!=10:errors.append('benchmark_argv_mismatch')
        else:
            expected=['-f',args[2],'-r','0','-n','1','-v','-l','-a']
            if args[1:]!=expected:errors.append('benchmark_argv_mismatch')
            for value,name in ((args[0],'binary'),(args[2],'graph')):
                path=Path(value);path=path if path.is_absolute() else base/path
                if str(path.resolve())!=evidence[name]['path']:errors.append('benchmark_'+name+'_path_mismatch')
    def document(name):
        if name not in loaded:return None
        try:return json.loads(loaded[name])
        except (ValueError,TypeError):errors.append(name+'_invalid_JSON');return None
    build=document('build_receipt')
    if build is not None:
        if not isinstance(build,dict):errors.append('invalid_build_receipt')
        else:
            if build.get('workflow_sha256')!=digest(plan) or build.get('source_commit')!=SOURCE or build.get('source_files')!=plan['source_files']:
                errors.append('build_source_binding')
            if build.get('binary_sha256')!=evidence.get('binary',{}).get('sha256') or build.get('macro_dump_sha256')!=evidence.get('macro_dump',{}).get('sha256'):
                errors.append('build_output_binding')
            if type(build.get('exit_code')) is not int or build['exit_code']!=0:errors.append('build_not_successful')
            if not build.get('compiler_version') or not build.get('argv'):missing.append('build_command_or_toolchain')
    graph=document('graph_receipt')
    if graph is not None:
        if not isinstance(graph,dict):errors.append('invalid_graph_receipt')
        elif graph.get('graph_sha256')!=evidence.get('graph',{}).get('sha256') or graph.get('source_commit')!=SOURCE or graph.get('workload_id')!=receipt.get('workload_id'):
            errors.append('graph_provenance_binding')
        elif workload:
            opts=graph.get('generator_options')
            if not isinstance(opts,list) or len(opts)!=6 or graph.get('generator_seed')!=workload['generator_seed']:
                errors.append('graph_generator_identity')
            else:
                expected=[v if v!='{graph}' else opts[-1] for v in workload['generator_argv'][1:]]
                path=Path(opts[-1]);path=path if path.is_absolute() else base/path
                if opts!=expected or str(path.resolve())!=evidence['graph']['path']:errors.append('graph_generator_identity')
    macros=check_macros(loaded['macro_dump'],plan,mode,variant) if 'macro_dump' in loaded and mode in {'functional','gem5'} and variant in {'baseline','dx100'} else None
    if macros and macros['status']=='rejected':errors.append('compiled_constants_mismatch')
    if macros and macros['status']=='unresolved':missing.append('compiled_constants_unbound')
    config=check_config(loaded['config_ini'],plan['expected_effective_model_parameters']) if 'config_ini' in loaded else None
    if config and config['status']=='rejected':errors.append('effective_model_parameters_mismatch')
    if config and config['status']=='unresolved':missing.append('effective_model_parameters_unbound')
    if mode=='gem5':
        if loaded.get('guest_env_file')!=guest_env_text(plan):errors.append('guest_environment_file_binding')
        for name in ('launcher','ramulator_config'):
            if evidence.get(name,{}).get('sha256')!=env.get('target',{}).get(name+'_sha256'):errors.append(name+'_environment_binding')
        exits=document('exit_events')
        if exits is not None and (not isinstance(exits,dict) or exits.get('guest_completed') is not True or not exits.get('events')):
            missing.append('guest_completion_or_exit_event_chain')
    checks=analyze_logs(loaded.get('stdout',''),loaded.get('stderr',''),mode,variant,receipt.get('completion'),receipt.get('exit_code'),
        loaded.get('stats'),receipt.get('stats_block_index'),plan['required_target_counters']) if mode in {'functional','gem5'} and variant in {'baseline','dx100'} else None
    if checks is None:missing.append('mode_or_variant_unbound')
    pre=preflight(plan,env)
    if pre['failures']:errors+=['preflight:'+v for v in pre['failures']]
    missing+=['preflight:'+v for v in pre['missing']]
    status='rejected_receipt' if errors else 'refuted_checks' if checks and checks['failures'] else 'inconclusive' if missing or not checks or checks['missing'] else 'evidence_consistent_pending_review'
    return {'format':'dx100-validation-collection-v0.1','workflow_sha256':digest(plan),'environment_sha256':digest(env),
        'receipt_sha256':digest(receipt),'mode':mode,'variant':variant,'workload_id':receipt.get('workload_id'),
        'status':status,'provenance_errors':errors,'missing':missing,'artifacts':evidence,'log_checks':checks,
        'macro_checks':macros,'configuration_checks':config,'preflight':pre,
        'target_validated':False,'target_timing_validated':False,'parameter_admission':None,'speedup':None,
        'scope':'Read-only consistency checks on supplied artifacts. Receipt authorship and model accuracy require independent review; no parameter tuple is promoted.'}


def compare_collections(baseline,accelerated):
    require(baseline.get('variant')=='baseline' and accelerated.get('variant')=='dx100','Expected baseline and DX100 collections.')
    required=('workflow_sha256','environment_sha256','workload_id','mode')
    mismatches=[k for k in required if baseline.get(k)!=accelerated.get(k) or baseline.get(k) is None]
    bgraph=baseline.get('artifacts',{}).get('graph',{}).get('sha256')
    agraph=accelerated.get('artifacts',{}).get('graph',{}).get('sha256')
    if not bgraph or bgraph!=agraph:mismatches.append('graph_sha256')
    b=(baseline.get('log_checks') or {}).get('frontier_sizes',[]);a=(accelerated.get('log_checks') or {}).get('frontier_sizes',[])
    equal=bool(b and a and b==a)
    states={baseline.get('status'),accelerated.get('status')}
    status=('not_comparable' if mismatches else 'rejected_evidence' if 'rejected_receipt' in states
            else 'refuted_checks' if 'refuted_checks' in states else 'inconclusive' if not b or not a
            else 'frontier_mismatch' if not equal else 'frontiers_match_pending_full_review'
            if states=={'evidence_consistent_pending_review'} else 'frontiers_match_other_checks_inconclusive')
    return {'status':status,'binding_mismatches':mismatches,'frontier_sizes_equal':equal,
        'baseline_status':baseline.get('status'),'accelerated_status':accelerated.get('status'),
        'target_validated':False,'timing_validated':False,'speedup':None,
        'note':'Parent arrays may differ. Equal frontier sizes do not override a failed verifier or missing execution/provenance evidence.'}


def guest_env_text(plan):
    return ''.join(k+'='+v+'\n' for k,v in plan['guest_environment'].items())

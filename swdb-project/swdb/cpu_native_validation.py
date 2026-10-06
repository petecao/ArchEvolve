"""Separate original-driver CPU validation collector. Created: 2026-10-06 ET.

Existing native evaluators and timing selection retain their established scope.
"""
import copy
import json
import math
import os
import platform
import re
import socket
import statistics
import time
from pathlib import Path

from swdb import access, artifacts, paths, writer, workflow
from swdb.cli import Failure
from swdb.cpu_service_calibration import identity
from swdb.problems import Problem
from swdb.store import Record, Store, canonical_path

PROCESS = 'five original GAPBS calls in one fresh process; no verification between timed calls'


def register_cli(commands):
    p = commands.add_parser('collect-cpu-native-validation', help='separate matched original GAPBS five-call validation; never changes CPU selection')
    p.add_argument('--records', type=Path, default=paths.RECORDS)
    p.add_argument('--characterization', required=True)
    p.add_argument('--id', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--machine', default='mbit10')
    p.add_argument('--lane', help='exact verified socket lease name')
    p.add_argument('--llvm-bin', type=Path, required=True)
    p.add_argument('--run-library-path', type=Path, action='append', default=[])
    p.add_argument('--estimate-protocol', help='frozen model/calibration/input protocol required before native development timing')
    p.add_argument('--development-band', help='frozen development record required before held-out timing')
    p.add_argument('--fixture', action='store_true')
    p.add_argument('--max-wall-s', type=float, default=900)
    p.add_argument('--format', choices=['yaml','json'], default='json')
    p.set_defaults(cpu_native_validation_handler=collect)


def _graph(stdout):
    m = re.search(r'Graph has ([0-9]+) nodes and ([0-9]+) (un)?directed edges', stdout)
    if not m:
        raise Failure('original-driver run lacks observed graph metadata')
    return {'num_nodes': int(m[1]), 'reported_edges': int(m[2]), 'directed': m[3] is None}


def collect(args):
    from swdb import analytic, analytic_binding
    from swdb.archevolve import require_team_safe
    from swdb.cpu_calibration import _command, _host_state
    from swdb.cpu_service_native import environment, loaded_libraries
    if workflow.CREATION_TAGS.get('mode') == 'extensa':
        raise Failure('CPU error validation admits ArchEvolve-mode evidence only')
    if not math.isfinite(args.max_wall_s) or not 0 < args.max_wall_s <= 900:
        raise Failure('CPU validation wall budget must be in (0,900] seconds')
    store = Store(args.records)
    char = analytic._load(store, args.characterization, 'workload_characterization')
    require_team_safe(store, char, command='collect-cpu-native-validation')
    errors = analytic_binding.verify_binding(char, store, require_available=True)
    if errors:
        raise Failure('CPU validation requires registered-source counts: ' + '; '.join(errors))
    binding = char['binding']; source_identity = binding['subject_source_identity']
    if binding['threads'] != 1 or binding['roi'] != analytic_binding.ROI or source_identity['trial_count'] != 5 or len(char['trials']) != 5:
        raise Failure('CPU validation requires the registered serialT1 original five-call scope')
    protocol = None
    if not args.fixture and not args.estimate_protocol:
        raise Failure('native validation requires a frozen estimate protocol before application timing')
    if args.estimate_protocol:
        from swdb import estimate_protocol
        protocol = store.get(args.estimate_protocol, 'protocol')
        if not protocol:
            raise Failure('frozen estimate protocol does not exist')
        target = protocol['settings']['target_description']['snapshot']
        protocol = estimate_protocol.bind(store, args.estimate_protocol, char, target)
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(paths.HOME.resolve()):
        raise Failure('CPU validation needs a new external raw folder')
    native_context = environment(args, output)
    if native_context and (char['host']['machine'].split('.')[0] != args.machine or char['host']['architecture'] != 'x86_64'):
        raise Failure('counting and native timing machine/architecture differ')
    if args.development_band:
        from swdb.cpu_error_band import require_holdout
        require_holdout(store, args.development_band, char, protocol=protocol)
    output.mkdir(parents=True)
    deadline = time.monotonic() + args.max_wall_s
    def command(argv):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Failure('CPU validation reached its wall budget')
        return _command(argv, remaining)
    git = ['git','-C',paths.HOME.parent]
    commit = command([*git,'rev-parse','HEAD']).stdout.strip()
    dirty = bool(command([*git,'status','--porcelain']).stdout)
    if native_context and dirty:
        raise Failure('native CPU validation requires clean committed source')
    version = command([args.llvm_bin/'llvm-config','--version']).stdout.strip()
    if version != char['toolchain']['llvm_version'] or not version.startswith('22.'):
        raise Failure('counting and timing LLVM toolchain version differs')
    subject = store.get(char['subject']['id'], 'implementation')
    source = Path(char['source']['path'])
    root = artifacts.source_root(store, subject)
    tree = artifacts.identify(root)['sha256']
    if tree != source_identity['source_root_sha256']:
        raise Failure('registered original source tree changed before timing')
    libraries = [Path(p).resolve() for p in args.run_library_path]
    if [str(p) for p in libraries] != char['toolchain']['run_library_paths']:
        raise Failure('counting and timing runtime library search paths differ')
    flags = char['source']['build_flags'] + char['toolchain']['compiler_flags']
    if any(flag.startswith(('-flto','-fpass-plugin','-fsanitize','-fprofile','-finstrument','-pg')) for flag in flags):
        raise Failure('CPU validation timing must be uninstrumented and without LTO')
    compiler = args.llvm_bin/'clang++'
    compiler_version = command([compiler,'--version']).stdout.strip()
    binary = output/'original-driver'
    library_flags = [flag for path in libraries for flag in ('-L'+str(path),'-Wl,-rpath,'+str(path))]
    built = command([compiler, source, '-o', binary, *flags, *library_flags])
    (output/'build.stdout').write_text(built.stdout); (output/'build.stderr').write_text(built.stderr)
    counted_runtime = char.get('observation_contract', {}).get('native_runtime')
    if native_context and (not counted_runtime or counted_runtime.get('missing')):
        raise Failure('native timing requires complete actual counted compiler/runtime context')
    runtime = copy.deepcopy(counted_runtime.get('environment', {})) if counted_runtime else {
        'OMP_NUM_THREADS': '1', 'OMP_DYNAMIC': 'FALSE'}
    declaration = (counted_runtime or {}).get('environment_scope', {})
    prefixes = tuple(declaration.get('prefixes', ['OMP_', 'KMP_', 'GOMP_']))
    exact = declaration.get('exact_variables', [])
    if not all(isinstance(k, str) for k in (*prefixes, *exact)) or any(not isinstance(k,str) or (v is not None and not isinstance(v,str)) for k,v in runtime.items()):
        raise Failure('counted runtime environment scope/values are invalid')
    keys = {key for key in os.environ if key.startswith(prefixes)}
    keys.update(exact)
    keys.update(runtime)
    keys.update(('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'))
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        os.environ.update({key:value for key,value in runtime.items() if value is not None})
        if not counted_runtime:
            for key in ('LD_LIBRARY_PATH','DYLD_LIBRARY_PATH'):
                os.environ[key] = os.pathsep.join(str(p) for p in libraries)
        loaded = loaded_libraries(binary, command) if native_context else {}
        if native_context:
            if counted_runtime['compiler_sha256'] != artifacts.file_hash(compiler) or counted_runtime['compiler_version'] != compiler_version:
                raise Failure('counted and timed compiler identities differ')
            critical = {k:v for k,v in counted_runtime['loaded_libraries'].items()
                        if k.startswith(('libc.so', 'libstdc++', 'libomp'))}
            if not any(k.startswith('libomp') for k in critical) or any(
                    not v.get('sha256') or loaded.get(k) != v for k,v in critical.items()):
                raise Failure('counted and timed loaded C/C++/OpenMP runtime identities differ')
        arguments = list(char['source']['run_arguments'])
        if '-v' in arguments or '-n' not in arguments or arguments[arguments.index('-n')+1] != '5':
            raise Failure('counted arguments must preserve no-v original five-call policy')
        started = time.time_ns()
        prefix = ['taskset', '-c', native_context['cpus'][0]] if native_context else []
        verification = command([*prefix,binary,*arguments,'-v'])
        (output/'verification.stdout').write_text(verification.stdout)
        (output/'verification.stderr').write_text(verification.stderr)
        checks = re.findall(r'^Verification:\s*(PASS|FAIL)\s*$', verification.stdout, re.M)
        if checks != ['PASS']*5:
            raise Failure('separate original reference verifier did not pass all five calls')
        timing_started = time.time_ns()
        timed = command([*prefix,binary,*arguments])
        finished = time.time_ns()
    finally:
        for key, value in previous.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key]=value
    (output/'timing.stdout').write_text(timed.stdout); (output/'timing.stderr').write_text(timed.stderr)
    printed = re.findall(r'^Trial Time:\s*([0-9]+\.[0-9]{5})\s*$', timed.stdout, re.M)
    if len(printed) != 5:
        raise Failure('original timed driver lacks exactly five quantized TrialTime values')
    graph = _graph(timed.stdout)
    if graph != binding['execution_receipt']['graph'] or _graph(verification.stdout) != graph:
        raise Failure('counted/correctness/timed observed graph metadata differ')
    if artifacts.identify(root)['sha256'] != tree or artifacts.file_hash(source) != char['source']['sha256']:
        raise Failure('registered source changed during timing')
    if native_context and (command([*git,'rev-parse','HEAD']).stdout.strip() != commit or command([*git,'status','--porcelain']).stdout):
        raise Failure('CPU validation runtime source changed during timing')
    values = [float(v) for v in printed]
    record = {'kind':'cpu_native_validation','schema_version':'0.4','id':args.id,'status':'draft','created':writer.today(),'updated':writer.today(),
        'provenance':[{'id':'native-validation','kind':'measurement' if native_context else 'source_code','description':'Separate original-driver validation scope; timing does not decide or alter existing CPU evaluation.', 'uri':None}],
        'format':'swdb.cpu-native-validation.v1','backend':'native','evidence_kind':'native' if native_context else 'fixture',
        'characterization':char['id'],'characterization_sha256':artifacts.digest(char),'implementation':subject['id'],'input':char['input'],'target':args.machine,'threads':1,
        'timing_arguments':arguments,'development_band':args.development_band,
        'estimate_protocol': None if protocol is None else {'id':protocol['id'],'sha256':artifacts.digest(protocol),
            'estimator_sha256':protocol['settings']['estimator_sha256'],
            'target_description_sha256':protocol['settings']['target_description']['sha256']},
        'scope':{'roi':binding['roi'],'process_policy':PROCESS,'source_policy':source_identity['source_policy'],'trial_count':5,
            'input_sha256':binding['input_record_sha256'],'source_root_sha256':tree,'translation_unit_sha256':char['source']['sha256'],
            'timed_wrapper_sha256':source_identity['timed_wrapper_sha256'],'graph_generation_contract_sha256':artifacts.digest({'input':binding['input_record_sha256'],'source_tree':tree,'arguments':arguments,'threads':1}),
            'observed_graph':graph,'observed_graph_metadata_sha256':artifacts.digest(graph),'graph_content_digest':None,
            'graph_identity_note':'Deterministic registered source/input/thread generation contract plus observed metadata; no CSR-content checksum is claimed.'},
        'context':{'host':socket.gethostname(),'architecture':platform.machine(),'compiler_version':compiler_version,'llvm_version':version,
            'flags':flags,'run_library_paths':[str(p) for p in libraries],'loaded_libraries':loaded,
            'binary_sha256':artifacts.file_hash(binary),'compiler_sha256':artifacts.file_hash(compiler),'commit':commit,'dirty':dirty,'instrumented_timer':False,'native_runtime':runtime,'counted_native_runtime_sha256':None if counted_runtime is None else artifacts.digest(counted_runtime),
            'runtime_match':'known' if native_context else 'fixture',
            'started_ns':started,'timing_started_ns':timing_started,'finished_ns':finished,'end_state':_host_state(),**(native_context or {})},
        'correctness':{'state':'passed','separate_process':True,'arguments':arguments+['-v'],'checks':checks,'stdout_sha256':artifacts.file_hash(output/'verification.stdout')},
        'trials':[{'position':i,'source':char['trials'][i]['sources'][0],'printed_duration_s':value,'printed_text':printed[i],
            'interval_s':[max(0.,value-.000005),value+.000005],'basis':'measured' if native_context else 'reported'} for i,value in enumerate(values)],
        'summary':{'median_whole_call_s':statistics.median(values),'rounding_half_width_s':.000005,'basis':'measured' if native_context else 'reported'},
        'raw_artifacts':[{'path':str(output/name),'sha256':artifacts.file_hash(output/name)} for name in ('timing.stdout','timing.stderr','verification.stdout','verification.stderr')]}
    record['identity_sha256']=identity(record)
    store.add(Record(canonical_path(record['kind'],record['id']),record))
    require_team_safe(store, record, command='collect-cpu-native-validation')
    writer.commit(args.records,new=[record])
    (output/'validation.json').write_text(json.dumps(record,indent=2))
    return record


def validate_record(record, ctx):
    data=record.data
    try:
        if data['identity_sha256'] != identity(data):
            raise Failure('CPU validation content identity differs')
        values=[row['printed_duration_s'] for row in data['trials']]
        if len(values)!=5 or [t['position'] for t in data['trials']]!=list(range(5)) or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values):
            raise Failure('CPU validation needs exactly five finite quantized trials')
        for trial in data['trials']:
            value=trial['printed_duration_s']
            if not re.fullmatch(r'[0-9]+\.[0-9]{5}',trial['printed_text']) or float(trial['printed_text'])!=value or trial['interval_s']!=[max(0.,value-.000005),value+.000005]:
                raise Failure('CPU validation printed-time rounding interval differs')
        basis='measured' if data['evidence_kind']=='native' else 'reported'
        if any(t['basis']!=basis for t in data['trials']) or data['summary']['basis']!=basis:
            raise Failure('fixture and native timing classifications differ')
        if data['summary']['median_whole_call_s']!=statistics.median(values) or data['summary']['rounding_half_width_s']!=.000005:
            raise Failure('CPU validation summary differs from retained printed trials')
        if data['scope']['process_policy']!=PROCESS or '-v' in data['timing_arguments'] or data['correctness']['arguments']!=data['timing_arguments']+['-v'] or data['correctness']['checks']!=['PASS']*5 or data['correctness']['state']!='passed' or data['correctness']['separate_process'] is not True:
            raise Failure('CPU validation timing/correctness scope differs')
        if data['scope']['graph_content_digest'] is not None or data['scope']['observed_graph_metadata_sha256']!=artifacts.digest(data['scope']['observed_graph']):
            raise Failure('CPU validation graph metadata identity differs; CSR content is unavailable')
        char=ctx.passed(data['characterization'],'workload_characterization')
        if char is None or artifacts.digest(char)!=data['characterization_sha256']:
            raise Failure('CPU validation counted characterization identity differs')
        binding=char['binding']; si=binding['subject_source_identity']
        if data['implementation']!=char['subject']['id'] or data['input']!=char['input'] or data['threads']!=binding['threads'] or data['timing_arguments']!=char['source']['run_arguments']:
            raise Failure('CPU validation counted implementation/input/T/arguments differ')
        scope=data['scope']
        if (scope['roi']!=binding['roi'] or scope['input_sha256']!=binding['input_record_sha256']
            or scope['source_policy']!=si['source_policy'] or scope['source_root_sha256']!=si['source_root_sha256']
            or scope['translation_unit_sha256']!=char['source']['sha256'] or scope['timed_wrapper_sha256']!=si['timed_wrapper_sha256']
            or scope['observed_graph']!=binding['execution_receipt']['graph']
            or [t['source'] for t in data['trials']]!=[t['sources'][0] for t in char['trials']]):
            raise Failure('CPU validation original-driver count/timing scope differs')
        context=data['context']
        if context['instrumented_timer'] is not False or context['flags']!=char['source']['build_flags']+char['toolchain']['compiler_flags']:
            raise Failure('CPU validation compiler/measurement flags differ')
        if not context['started_ns']<=context['timing_started_ns']<=context['finished_ns']:
            raise Failure('CPU validation timing chronology differs')
        if data['evidence_kind']=='native':
            if (context['dirty'] is not False or '(verified:' not in str(context.get('lane'))
                or context['architecture']!='x86_64' or context['system']!='Linux' or context['runtime_match']!='known'):
                raise Failure('native CPU validation requires clean actual Linux/x86_64 leased runtime')
            runtime=char.get('observation_contract',{}).get('native_runtime')
            if not runtime or runtime['missing'] or context['counted_native_runtime_sha256']!=artifacts.digest(runtime) or context['native_runtime']!=runtime['environment'] or context['compiler_sha256']!=runtime['compiler_sha256'] or context['compiler_version']!=runtime['compiler_version']:
                raise Failure('native CPU validation counted runtime/compiler identity differs')
            critical={k:v for k,v in runtime['loaded_libraries'].items() if k.startswith(('libc.so','libstdc++','libomp'))}
            if not any(k.startswith('libomp') for k in critical) or any(not v.get('sha256') or context['loaded_libraries'].get(k)!=v for k,v in critical.items()):
                raise Failure('native CPU validation loaded C/C++/OpenMP identities differ')
            pin=data.get('estimate_protocol')
            protocol=ctx.passed(pin['id'],'protocol') if pin else None
            if (not protocol or pin['sha256']!=artifacts.digest(protocol)
                or pin['estimator_sha256']!=protocol['settings']['estimator_sha256']
                or pin['target_description_sha256']!=protocol['settings']['target_description']['sha256']):
                raise Failure('native application timing lacks its prior frozen model/calibration protocol')
            if len(context.get('cpus',[]))!=1:
                raise Failure('native CPU validation needs its pinned physical T1 core')
    except (Failure,KeyError,TypeError,ValueError,IndexError) as exc:
        yield Problem(record.rel,'identity_sha256',str(exc))

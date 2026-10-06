"""Immutable source-artifact adapter for protected GAPBS timed-call drivers. 2026-10-06 ET.

Fixture packaging remains fixture packaging. This adapter proves a new count
execution's source/input/ROI identity; it does not promote its source or candidate.
"""
import re
import shlex
from pathlib import Path
from swdb import artifacts
from swdb.cli import Failure

ADAPTER='registered-functional.v1'
ROI='gapbs.functional_trial_lambda.v1'


def selected(store,subject,snapshot_id=None):
    rid=subject.get('source_snapshot') if subject['kind']=='candidate' else snapshot_id
    snapshot=store.get(rid,'source_snapshot')
    if snapshot is None:raise Failure('registered-functional requires an immutable source snapshot')
    context=snapshot['context']
    if subject['kind']=='candidate':
        if subject.get('context')!=context:raise Failure('candidate context differs from its registered source snapshot')
        artifact=subject['artifact'];protections=subject['protections']
    else:
        if context.get('source_baseline')!=subject['id']:raise Failure('snapshot does not bind this registered baseline')
        artifact=snapshot['artifact'];protections=snapshot['protections']
    primary=[c['path'] for c in context['code'] if Path(c['path']).suffix in ('.c','.cc','.cpp')]
    if len(primary)!=1:raise Failure('registered source translation unit is ambiguous')
    return snapshot,context,artifact,protections,artifacts.relative_path(primary[0])


def run_arguments(context,input_record,trials):
    generator=input_record.get('generator',{})
    if generator.get('application')!=context['application']:raise Failure('registered input generator application differs from source context')
    raw=shlex.split(generator.get('arguments',''))
    if not re.fullmatch(r'-(?:g|u) [0-9]+ -k [0-9]+',' '.join(raw)):
        raise Failure('registered source requires explicit built-in graph scale and degree')
    for name,value in (('scale',int(raw[1])),('requested_degree',int(raw[3]))):
        declared=input_record.get('properties',{}).get(name,{}).get('value')
        if declared is not None and declared!=value:raise Failure('registered input '+name+' differs from generator arguments')
    command=context['run']['command']
    if not command.startswith('{binary} ') or '{input_args}' not in command or '{trials}' not in command:
        raise Failure('registered timed driver argument contract is unresolved')
    rendered=command.replace('{binary}','__binary__').replace('{input_args}',shlex.join(raw)).replace('{trials}',str(trials))
    if '{' in rendered or '}' in rendered:raise Failure('unsupported registered run placeholder')
    result=shlex.split(rendered)
    if result[0]!='__binary__' or '-v' in result:raise Failure('counted timed call must use the registered original driver without verification')
    return result[1:]


def build_flags(context,root,*,require_available=True):
    tokens=shlex.split(context['build']['command'])
    if tokens.count('{cxx}')!=1 or tokens.count('{flags}')!=1 or tokens.count('{source}')!=1 or tokens.count('{binary}')!=1:
        raise Failure('registered source compiler contract is unresolved')
    flags=shlex.split(context['build']['flags'])
    allowed={'{cxx}','{flags}','{source}','-o','{binary}'}
    for token in tokens:
        if token in allowed:continue
        if not token.startswith('-I{app}/'):raise Failure('unsupported registered build template token: '+token)
        relative=artifacts.relative_path(token[len('-I{app}/'):])
        directory=(root/relative).resolve()
        if not directory.is_relative_to(root.resolve()) or (require_available and not directory.is_dir()):raise Failure('registered include path unavailable')
        flags.append('-I'+str(directory))
    return flags


def prepare(store,args,subject,input_record):
    if args.fixture:raise Failure('registered-functional counts actual source artifacts; fixture packaging state is retained separately')
    if args.counting_pipeline not in (None,'source-normalized-v2'):raise Failure('registered-functional requires source-normalized-v2')
    if args.function or args.build_flag or args.run_arg or args.region_map:raise Failure('registered-functional derives source, flags, arguments and scope from immutable records')
    if any(not flag.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for flag in args.toolchain_flag):
        raise Failure('registered toolchain flags may select headers/libraries, not change source semantics')
    if args.roi and args.roi!=ROI:raise Failure('registered-functional ROI is '+ROI)
    if not 1<=args.trials<=100:raise Failure('registered trial count must be between 1 and 100')
    snapshot,context,artifact,protections,relative=selected(store,subject,args.source_snapshot)
    if context['run'].get('timer')!='gapbs_trial_time':raise Failure('registered timed source requires a GAPBS trial-lambda driver')
    if args.source:
        source=args.source.resolve()
        if not source.as_posix().endswith('/'+relative):raise Failure('source is not the registered translation-unit relative path')
        root=source.parents[len(Path(relative).parts)-1]
        actual=artifacts.identify(root)
        if actual['sha256']!=artifact['sha256'] or actual['files']!=artifact['files']:raise Failure('relocated source artifact differs from immutable registered identity')
    else:root=artifacts.verify(artifact);source=root/relative
    artifacts.check_protections(root,protections)
    benchmark=source.parent/'benchmark.h'
    lines=benchmark.read_text().splitlines()
    sites=[i+1 for i,line in enumerate(lines) if line.strip()=='auto result = kernel(g);']
    if len(sites)!=1:raise Failure('registered timed kernel lambda is unresolved')
    source_policy='source_picker' if re.search(r'\.PickNext\s*\(',source.read_text()) else 'none'
    return {'source':source,'artifact_root':root,'flags':build_flags(context,root),'run':run_arguments(context,input_record,args.trials),
        'roi':ROI,'roi_path':str(benchmark),'roi_line':sites[0],'mapping':{'regions':[]},'ambiguous_helper_loops':[],
        'identity':{'adapter':ADAPTER,'application':context['application'],'source_snapshot':snapshot['id'],
            'source_snapshot_record_sha256':artifacts.digest(snapshot),'source_context_sha256':artifacts.digest(context),
            'source_commit':context['source']['commit'],'source_root_sha256':artifact['sha256'],
            'translation_unit_sha256':artifacts.file_hash(source),'translation_unit_relative_path':relative,
            'timed_wrapper_relative_path':benchmark.relative_to(root).as_posix(),'timed_wrapper_sha256':artifacts.file_hash(benchmark),
            'trial_count':args.trials,'source_selection':source_policy,
            'source_policy':'Original registered source selection; '+source_policy,
            'summary':'per-trial exclusive counts, median whole-call estimate',
            'region_bindings':[], 'packaging_evidence':'Source/candidate/profile states are retained; count binding is independent execution evidence.'}}


def verify(record,store,require_available=False):
    from swdb.analytic_binding import counted_payload
    binding=record['binding'];identity=binding['subject_source_identity'];receipt=binding.get('execution_receipt',{});issues=[]
    subject=store.get(record['subject']['id'],record['subject']['kind']);input_record=store.get(record['input'],'input')
    if subject is None or input_record is None:return ['registered functional subject/input unavailable']
    snapshot,context,artifact,protections,relative=selected(store,subject,identity.get('source_snapshot'))
    expected={'adapter':ADAPTER,'source_snapshot_record_sha256':artifacts.digest(snapshot),
        'source_context_sha256':artifacts.digest(context),'source_root_sha256':artifact['sha256'],
        'subject_record_sha256':artifacts.digest(subject),'translation_unit_relative_path':relative}
    for name,value in expected.items():
        if identity.get(name)!=value:issues.append('registered functional source identity differs: '+name)
    manifest={f['path']:f for f in artifact['files']}
    if record['source']['sha256']!=manifest[relative]['sha256'] or identity.get('translation_unit_sha256')!=record['source']['sha256']:
        issues.append('registered functional translation-unit hash differs')
    wrapper=identity.get('timed_wrapper_relative_path')
    if wrapper not in manifest or identity.get('timed_wrapper_sha256')!=manifest[wrapper]['sha256']:
        issues.append('registered functional timed wrapper hash differs')
    n=identity.get('trial_count')
    if type(n) is not int or not 1<=n<=100:return issues+['registered functional trial count is invalid']
    arguments=run_arguments(context,input_record,n)
    if record['source']['run_arguments']!=arguments or binding['run_arguments_sha256']!=artifacts.digest(arguments):issues.append('registered functional run arguments differ')
    if binding['input_record_sha256']!=artifacts.digest(input_record):issues.append('registered functional input identity differs')
    if binding['roi']!=ROI or record['coverage'].get('whole_timed_call') is not True:issues.append('registered functional whole-call ROI differs')
    if record['counting'].get('pipeline_version')!='source-normalized-v2' or record['counting']['passes']!=['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']:
        issues.append('registered functional source pipeline differs')
    trials=record.get('trials',[])
    if len(trials)!=n or [t['position'] for t in trials]!=list(range(n)):issues.append('registered functional trial sequence differs')
    nodes=receipt.get('graph',{}).get('num_nodes');selection=identity.get('source_selection')
    if type(nodes) is not int or nodes<1:issues.append('registered counted graph size unavailable')
    elif selection=='source_picker':
        if any(len(t['sources'])!=1 or type(t['sources'][0]) is not int or not 0<=t['sources'][0]<nodes for t in trials):issues.append('registered source-picker trial selection differs')
    elif selection=='none':
        if any(t['sources'] for t in trials):issues.append('source-free driver unexpectedly selected a source')
    else:issues.append('registered source-selection scope is unresolved')
    fields={'format':'swdb.registered-count-receipt.v1','adapter':ADAPTER,
        'subject_record_sha256':identity['subject_record_sha256'],'source_root_sha256':identity['source_root_sha256'],
        'source_sha256':record['source']['sha256'],'input_record_sha256':binding['input_record_sha256'],
        'run_arguments_sha256':binding['run_arguments_sha256'],'roi':binding['roi'],'threads':binding['threads'],
        'trial_count':n,'pipeline_version':record['counting']['pipeline_version'],'passes':record['counting']['passes'],
        'llvm_version':record['toolchain']['llvm_version'],'binary_sha256':record['counting']['binary_sha256'],
        'counts_sha256':record['counting']['counts_sha256'],'source_ir_sha256':record['static_analysis']['source_ir_sha256'],
        'optimized_ir_sha256':record['static_analysis']['optimized_ir_sha256'],'counted_payload_sha256':artifacts.digest(counted_payload(record))}
    for name,value in fields.items():
        if receipt.get(name)!=value:issues.append('registered functional execution receipt differs: '+name)
    path=Path(record['source']['path'])
    if not path.as_posix().endswith('/'+relative):issues.append('registered functional source path differs')
    root=path.parents[len(Path(relative).parts)-1]
    if record['source']['build_flags']!=build_flags(context,root,require_available=False):issues.append('registered functional build flags differ')
    declared_nodes=input_record.get('properties',{}).get('num_nodes',{}).get('value')
    if declared_nodes is not None and declared_nodes!=nodes:issues.append('counted graph differs from registered input node count')
    if require_available or path.is_file():
        root=path.parents[len(Path(relative).parts)-1];actual=artifacts.identify(root)
        if actual['sha256']!=artifact['sha256'] or actual['files']!=artifact['files']:issues.append('registered functional source tree changed')
        artifacts.check_protections(root,protections)
        if record['source']['build_flags']!=build_flags(context,root):issues.append('registered functional build flags differ')
        selected_policy='source_picker' if re.search(r'\.PickNext\s*\(',path.read_text()) else 'none'
        if selected_policy!=selection:issues.append('registered functional source-selection policy differs')
    if require_available:
        folder=Path(record['counting']['output_directory'])
        for name,key in [('counts.json','counts_sha256'),('counted','binary_sha256')]:
            if not (folder/name).is_file() or artifacts.file_hash(folder/name)!=record['counting'][key]:issues.append('registered execution artifact differs: '+name)
    return issues

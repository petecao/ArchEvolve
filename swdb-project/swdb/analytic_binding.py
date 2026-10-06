"""Registered source/input/ROI binding for GAPBS. Updated: 2026-10-06 ET.

An arbitrary translation unit can still be counted, but never gains this adapter's
binding by naming an implementation. Source/evaluator files are read, never edited.
"""
import hashlib
import re
import shlex
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

ROI='gapbs.trial_lambda.v1'
ADAPTER='registered-gapbs.v1'


def prepare(store,args,subject,input_record):
    if args.adapter=='registered-functional':
        from swdb.analytic_functional_binding import prepare as functional_prepare
        return functional_prepare(store,args,subject,input_record)
    if args.candidate or args.fixture:
        raise Failure('registered-gapbs requires a registered baseline implementation, not a candidate/fixture')
    if args.counting_pipeline not in (None,'source-normalized-v2'):
        raise Failure('registered-gapbs requires source-normalized-v2 counting pipeline')
    context=store.source_context(subject)
    if context['application']!='gapbs' or subject['function'] not in ('DOBFS','Brandes'):
        raise Failure('registered-gapbs currently supports the registered GAPBS DOBFS and Brandes baselines')
    root=artifacts.source_root(store,subject)
    primary=next((c for c in subject['code'] if c['path'].endswith('.cc')),None)
    if not primary:
        raise Failure('implementation lacks its registered translation unit')
    source=(root/primary['path']).resolve()
    if args.source and args.source.resolve()!=source:
        raise Failure('source differs from the registered translation unit')
    if any(not flag.startswith(('--gcc-install-dir=','--gcc-toolchain=','--sysroot=','-resource-dir=','-stdlib=')) for flag in args.toolchain_flag):
        raise Failure('registered adapter toolchain flags may select installed headers/libraries, not alter source macros or code')
    if args.function or args.build_flag or args.run_arg or args.region_map:
        raise Failure('registered-gapbs derives source scope, flags, run arguments and region mapping from registered records')
    if args.roi and args.roi!=ROI:
        raise Failure('registered-gapbs ROI is '+ROI)
    if not 1<=args.trials<=100:
        raise Failure('registered-gapbs trials must be between 1 and 100')
    for code in subject['code']:
        path=root/code['path']
        lo,hi=code['lines']
        excerpt=''.join(path.read_text().splitlines(keepends=True)[lo-1:hi]).strip()
        if code.get('excerpt') and excerpt!=code['excerpt'].strip():
            raise Failure('registered source differs from authoritative implementation excerpt: '+code['path'])
    generator=input_record.get('generator',{})
    if generator.get('application')!=context['application']:
        raise Failure('registered GAPBS input must use the same registered application generator')
    run=shlex.split(generator.get('arguments',''))
    if not re.fullmatch(r'-(?:g|u) [0-9]+ -k [0-9]+',' '.join(run)):
        raise Failure('registered GAPBS adapter requires an explicit built-in graph scale and degree')
    run+=['-n',str(args.trials)]
    if subject['function']=='Brandes':run+=['-i','1']
    benchmark=root/'src/benchmark.h'
    lines=benchmark.read_text().splitlines()
    sites=[i+1 for i,line in enumerate(lines) if line.strip()=='auto result = kernel(g);']
    if len(sites)!=1:
        raise Failure('registered BenchmarkKernel timed call boundary is unresolved')
    rows=[]
    for loop in subject['loops']:
        code=loop['code'];lo,hi=code['lines'];path=root/code['path']
        owners=[]
        if code['path']==primary['path']:
            for c in subject['code']:
                if c['path']==code['path'] and c['lines'][0]<=lo and hi<=c['lines'][1]:
                    text=c.get('excerpt','');match=re.search(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\([^;]*?\)\s*\{',text,re.S)
                    if match:owners.append(match.group(1))
        owner=min(owners,key=len) if owners else ('fill' if path.name=='pvector.h' else 'reset' if path.name=='bitmap.h' else None)
        if owner:
            rows.append({'id':subject['id']+'/'+loop['id'],'function':owner,'path':str(path.resolve()),
                'line_start':lo,'line_end':hi,'catalog_loop':loop['id']})
    # Reuse current-source profile IDs, never stale candidate/profile line labels.
    profile_regions={}
    for package in store.of_kind('profile_package'):
        if package.data.get('implementation')!=subject['id']:continue
        for region in package.data.get('regions',[]):
            if region.get('kind')!='loop' or not region.get('byte_range') or not region.get('source_sha256'):continue
            path=root/region.get('path','')
            if not path.is_file():continue
            begin,end=region['byte_range']
            if hashlib.sha256(path.read_bytes()[begin:end]).hexdigest()!=region['source_sha256']:continue
            profile_regions.setdefault(region['id'],region)
    for row in rows:
        candidates=[r for r in profile_regions.values() if (root/r['path']).resolve()==Path(row['path'])
            and r.get('function')==row['function'] and row['line_start']<=r['lines'][0]<=row['line_start']+2
            and r['lines'][1]==row['line_end']]
        if candidates:
            selected=min(candidates,key=lambda r:(r['lines'][1]-r['lines'][0],r['id']))
            row['id']=selected['id']
            row['profile_source_sha256']=selected['source_sha256']
    # A shared helper definition cannot distinguish multiple logical call sites.
    groups={}
    for row in rows:groups.setdefault((row['path'],row['function'],row['line_start'],row['line_end']),[]).append(row)
    unique=[group[0] for group in groups.values() if len(group)==1]
    identity=artifacts.identify(root)
    return {'source':source,'flags':shlex.split(subject['build']['flags']),'run':run,'roi':ROI,
        'roi_path':str(benchmark.resolve()),'roi_line':sites[0],'mapping':{'regions':unique},
        'identity':{'adapter':ADAPTER,'application':context['application'],'source_commit':context['source']['commit'],
            'source_root_sha256':identity['sha256'],'translation_unit_sha256':artifacts.file_hash(source),
            'timed_wrapper_sha256':artifacts.file_hash(benchmark),'trial_count':args.trials,
            'source_policy':'original deterministic SourcePicker, advancing between kernel invocations',
            'summary':'estimate each invocation, then median whole-call seconds; never sum trial counts',
            'region_bindings':unique},
        'ambiguous_helper_loops':[r['catalog_loop'] for g in groups.values() if len(g)>1 for r in g]}


def compare_patterns(subject,regions,ambiguous=(),mapping=()):
    result=[]
    ids={r['catalog_loop']:r['id'] for r in mapping}
    for pattern in subject.get('access_patterns',[]):
        expected=[s['address_shape'] for s in pattern['steps']]
        region_id=ids.get(pattern['loop'],subject['id']+'/'+pattern['loop'])
        rows=[r for r in regions if r['id']==region_id]
        observed=sorted({a['address_shape']['value'] or 'unknown' for r in rows for a in r['access_patterns']})
        updates=sorted({a['update_kind'] for r in rows for a in r['access_patterns']})
        wanted_update={'compare_and_swap':'compare-and-swap','add_update':'add-update','min_max_update':'min-max-update'}.get(pattern['update_kind'],pattern['update_kind'])
        matched=len(expected)==1 and expected[0] in observed and wanted_update in updates
        if pattern['loop'] in ambiguous:reason='Shared header helper has several logical call sites; instance binding remains unresolved.'
        elif not rows:reason='No LLVM loop matched this source extent; loop/callee observations remain in the unmapped inventory.'
        elif len(expected)>1:reason='LLVM reports individual SSA address sites; the complete handwritten multi-step chain is not yet proven across helpers.'
        elif not matched:reason='Expected '+expected[0]+' / '+wanted_update+'; observed shapes '+(', '.join(observed) or 'none')+' and updates '+(', '.join(updates) or 'none')+'.'
        else:reason='Source-bound loop contains the expected individual address shape; update semantics remain the handwritten contract.'
        result.append({'pattern':pattern['id'],'loop':pattern['loop'],'region':region_id if rows else None,'expected_shapes':expected,
            'observed_shapes':observed,'observed_update_kinds':updates,'expected_update_kind':pattern['update_kind'],'matched':matched,'reason':reason})
    return result


def counted_payload(record):
    payload={'regions':record['regions'],'trials':record.get('trials',[]),
        'unmodeled_calls':record['unmodeled_calls']}
    if 'observation_contract' in record:
        payload['observation_contract']=record['observation_contract']
        payload['observation_format']=record['counting'].get('observation_format')
    return payload


def execution_receipt(record,graph,plugin_source,runtime_source):
    binding=record['binding'];identity=binding['subject_source_identity'];counting=record['counting']
    return {'format':'swdb.registered-count-receipt.v1','adapter':identity.get('adapter',ADAPTER),
        'subject_record_sha256':identity['subject_record_sha256'],
        'source_root_sha256':identity['source_root_sha256'],'source_sha256':record['source']['sha256'],
        'input_record_sha256':binding['input_record_sha256'],'run_arguments_sha256':binding['run_arguments_sha256'],
        'roi':binding['roi'],'threads':binding['threads'],'trial_count':identity['trial_count'],
        'pipeline_version':counting['pipeline_version'],'passes':counting['passes'],
        'llvm_version':record['toolchain']['llvm_version'],'binary_sha256':counting['binary_sha256'],
        'counts_sha256':counting['counts_sha256'],'source_ir_sha256':record['static_analysis']['source_ir_sha256'],
        'optimized_ir_sha256':record['static_analysis']['optimized_ir_sha256'],
        'plugin_source_sha256':artifacts.file_hash(plugin_source),'runtime_source_sha256':artifacts.file_hash(runtime_source),
        'counted_payload_sha256':artifacts.digest(counted_payload(record)),'graph':graph}


def _verify_binding(record,store,require_available=False):
    """Semantic proof hook; return problems without requiring historical remote raw files.

    The receipt binds compact observed facts to the source/arguments/pipeline checked
    at execution. A label alone has no receipt and cannot establish application binding.
    New executions also verify the available registered source tree and raw counts.
    """
    problems=[];binding=record.get('binding',{});identity=binding.get('subject_source_identity',{})
    if identity.get('adapter')=='registered-functional.v1':
        from swdb.analytic_functional_binding import verify
        return verify(record,store,require_available)
    receipt=binding.get('execution_receipt')
    if not isinstance(receipt,dict) or receipt.get('format')!='swdb.registered-count-receipt.v1':
        return ['verified binding requires a registered counted execution receipt']
    if identity.get('adapter')!=ADAPTER or receipt.get('adapter')!=ADAPTER:
        problems.append('registered adapter identity differs')
    subject=store.get(record.get('subject',{}).get('id'),'implementation')
    input_record=store.get(record.get('input'),'input')
    if not subject or not input_record:return problems+['registered subject/input is unavailable']
    if artifacts.digest(subject)!=identity.get('subject_record_sha256'):
        problems.append('registered subject record identity differs')
    if artifacts.digest(input_record)!=binding.get('input_record_sha256'):
        problems.append('registered input record identity differs')
    trial_count=identity.get('trial_count')
    if type(trial_count) is not int or not 1<=trial_count<=100:
        return problems+['registered trial count is invalid']
    args=shlex.split(input_record.get('generator',{}).get('arguments',''))+['-n',str(trial_count)]
    if subject.get('function')=='Brandes':args+=['-i','1']
    if record['source']['run_arguments']!=args or binding.get('run_arguments_sha256')!=artifacts.digest(args):
        problems.append('registered input run arguments differ')
    if binding.get('roi')!=ROI or record.get('coverage',{}).get('whole_timed_call') is not True:
        problems.append('registered timed trial-lambda ROI is not established')
    if record['counting'].get('pipeline_version')!='source-normalized-v2' or record['counting'].get('passes')!=['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']:
        problems.append('registered source-counting pipeline differs')
    trials=record.get('trials',[])
    if len(trials)!=trial_count or [t.get('position') for t in trials]!=list(range(trial_count)):
        problems.append('registered trial positions/count differ')
    nodes=receipt.get('graph',{}).get('num_nodes')
    if type(nodes) is not int or nodes<1:problems.append('registered counted graph size is unavailable')
    elif any(len(t.get('sources',[]))!=1 or type(t['sources'][0]) is not int or not 0<=t['sources'][0]<nodes for t in trials):
        problems.append('registered trial source selection is invalid')
    expected={'subject_record_sha256':identity.get('subject_record_sha256'),'source_root_sha256':identity.get('source_root_sha256'),
        'source_sha256':record['source']['sha256'],'input_record_sha256':binding.get('input_record_sha256'),
        'run_arguments_sha256':binding.get('run_arguments_sha256'),'roi':binding.get('roi'),'threads':binding.get('threads'),
        'trial_count':trial_count,'pipeline_version':record['counting'].get('pipeline_version'),'passes':record['counting'].get('passes'),
        'llvm_version':record['toolchain']['llvm_version'],'binary_sha256':record['counting']['binary_sha256'],
        'counts_sha256':record['counting']['counts_sha256'],'source_ir_sha256':record['static_analysis']['source_ir_sha256'],
        'optimized_ir_sha256':record['static_analysis']['optimized_ir_sha256'],
        'counted_payload_sha256':artifacts.digest(counted_payload(record))}
    for key,value in expected.items():
        if receipt.get(key)!=value:problems.append('registered execution receipt differs: '+key)
    # Git-synced registered sources are checked when available on this host. A saved
    # remote output path is optional for ordinary validation and never causes a fetch.
    try:
        root=artifacts.source_root(store,subject)
        source=root/next(c['path'] for c in subject['code'] if c['path'].endswith('.cc'))
        if artifacts.file_hash(source)!=record['source']['sha256']:problems.append('registered source file hash differs')
        if require_available and artifacts.identify(root)['sha256']!=identity.get('source_root_sha256'):
            problems.append('registered source tree changed during counting')
        if artifacts.file_hash(root/'src/benchmark.h')!=identity.get('timed_wrapper_sha256'):
            problems.append('registered timed wrapper hash differs')
    except (Failure,OSError,StopIteration):
        if require_available:problems.append('registered source files are unavailable at execution')
    if require_available:
        folder=Path(record['counting']['output_directory'])
        for name,key in [('counts.json','counts_sha256'),('counted','binary_sha256')]:
            if not (folder/name).is_file() or artifacts.file_hash(folder/name)!=record['counting'][key]:
                problems.append('registered execution artifact differs: '+name)
    return problems


def verify_binding(record,store,require_available=False):
    try:return _verify_binding(record,store,require_available)
    except (KeyError,TypeError,ValueError,AttributeError,Failure,OSError) as exc:
        return ['malformed registered execution binding: '+str(exc)]

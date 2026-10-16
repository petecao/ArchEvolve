"""2026-10-16 ET. Inert independent six-glue cold auditor.

Run only after root confirms the exact producer has settled. Stdlib and read-only
Git only; no project import, tool probe, compiler, verifier, solver or raw transfer.
"""
import argparse
import ast
import csv
import hashlib
import io
import itertools
import json
import re
import resource
import signal
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1')
PROFILE = RAW/'closed-lifetime6-public-v1-profile'
SOURCE = Path('/data1/yanruj/probata-resume-20261016-fb197c5d')
COMMIT = 'fb197c5ddd173065ca781766886c6a797684a838'
ENTRY_SHA = '76a687229c3d28e504102aad1bdd2c3efc47b1992cf1703c94a2291ec6f7c263'
EXPECTED_SHA = 'a10f2ee5864b8c39c22e72b29f34e3195b59839e0fdc9a6ae9e5c6c5f7ecd4b2'
COMMAND_SHA = '__COMMAND_SHA__'
PRIOR_SUPPORT_HASHES = __PRIOR_SUPPORT_HASHES__
PRIOR_SUPPORT_PINS = __PRIOR_SUPPORT_PINS__
CHECKS = []

# __REVIEWED_PARSER_HELPERS__

# __INDEPENDENT_GOALS_AND_DEFINITIONS__


def git(*args, input=None):
    return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
        '-c','core.preloadIndex=false','-c','core.fsmonitor=false','-c','index.threads=1',
        '-C',str(SOURCE),*args], input=input, timeout=45)


def lineage(anchors):
    direct = ('tool','function','c_lowering_sha256','anchors','models','std_models','allocation')
    keys = ('count','receiver','alias','reserve_request','observation','guard','entry_obligations',
            'call_obligations','scalar_read_obligation','lowered_lifetime','source_sha256','lowered_sha256')
    return {**{k:anchors[k] for k in direct},
            'candidate_source_events':{k:anchors['vector_reallocation_candidate'][k] for k in keys}}


def normal_flags(flags):
    for name in ('-wp','-wp-rte','-wp-no-filter-init','-wp-smoke-tests','-wp-status-all'):
        require(name in flags,'mandatory complete normal flag '+name)
    for name,wanted in [('-wp-cache','none'),('-wp-model','+real'),('-machdep','x86_64'),
                        ('-rte-initialized','@all'),('-wp-par','1'),('-wp-timeout','30'),
                        ('-wp-prover','alt-ergo,z3,cvc5')]:
        values=[flags[i+1] for i,x in enumerate(flags[:-1]) if x==name]
        values += [x[len(name)+1:] for x in flags if x.startswith(name+'=')]
        require(values and all(x==wanted for x in values),'exact normal flag values '+name)
    require(not any(x.startswith(('-wp-prop','-wp-fct','-wp-session','-wp-script','-wp-cache-dir')) or
                    x in {'-wp-gen','-wp-no-why3-detect','-wp-filter-init','-wp-no-rte'} for x in flags),
            'no selective/generation/weakening/session flags')


def source_false_map(assertion, tree):
    """Recognize only Heap's original new-identity false initialization lambda."""
    value = assertion
    if not (isinstance(value,list) and len(value)==3 and value[0]=='forall' and len(value[1])==1):
        return None
    variable, sort = value[1][0]
    body = value[2]
    if sort!='Int' or not (isinstance(body,list) and len(body)==3 and body[0]=='='):
        return None
    left,right=body[1:]
    if left=='false':left,right=right,left
    if right!='false' or not (isinstance(left,list) and len(left)==3 and left[0]=='select' and left[2]==variable and isinstance(left[1],str)):
        return None
    name=left[1]
    declared=[x for x in tree if x[:2]==['declare-fun',name]]
    if declared!=[['declare-fun',name,[],['Array','Int','Bool']]]:
        return None
    def uses(value):
        return int(value==name) if isinstance(value,str) else sum(uses(x) for x in value)
    owners=[x for x in tree if x and x[0]=='define-fun' and uses(x)]
    if not owners or any(x[1] not in {'begin_automatic','allocate'} for x in owners):
        return None
    expected_uses=forms('(store (initialized h) (next h) '+name+')')[0]
    def contains(value,wanted):
        return value==wanted or isinstance(value,list) and any(contains(x,wanted) for x in value)
    if any(uses(x)!=1 or not contains(expand(x[-1]),expected_uses) for x in owners):
        return None
    all_uses=[x for x in tree if uses(x)]
    if len(all_uses)!=len(owners)+2:
        return None
    return {'classification':'Definitional lifting of unchanged Heap initialization lambda; not a theorem premise',
            'source':'theory/heap_reallocation.mlw','source_transitions':[x[1] for x in owners],
            'exact_array_type':True,'sole_source_initialization_use':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',type=int,choices=(0,1),required=True)
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--ended-utc',required=True)
    args=parser.parse_args()
    require(args.generation>0 and bool(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',args.ended_utc)),
            'root-confirmed settlement arguments')
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    started=time.monotonic()
    def audit(event,values):
        if event=='subprocess.Popen':
            require(values[0]=='/usr/bin/git','read-only Git is the sole allowed child')
        elif event in {'os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            raise RuntimeError('project/native/external execution forbidden')
        elif event=='open' and len(values)>1 and isinstance(values[1],str) and any(x in values[1] for x in 'wax+'):
            raise RuntimeError('remote writes forbidden')
    sys.addaudithook(audit)
    initial=snapshot(RAW)
    expected=read(PROFILE/'expected.json');policy=expected['resource_policy']
    require(pin(PROFILE/'expected.json')['sha256']==EXPECTED_SHA,'exact frozen expected')
    for path in (RAW/'closed-lifetime6-public-v1-entry.py',PROFILE/'entry.py'):
        require(pin(path)['sha256']==ENTRY_SHA,'exact frozen entry '+str(path))
    require(expected['source_commit']==COMMIT and expected['remote_project']==str(SOURCE/'swdb-project'),'exact source/context')
    require(git('rev-parse','HEAD').decode().strip()==COMMIT and not git('status','--porcelain','--untracked-files=all'),'current source exact and clean')
    for row in expected['source_blobs']+expected['test_helper_pins']:
        require(pin(SOURCE/'swdb-project'/row['relative'])['sha256']==row['sha256'],'source/helper '+row['relative'])
    consumers=[]
    for path in sorted(PROFILE.glob('source-consumers-*.json')):
        closure=read(path)
        for relative,row in closure['trees'].items():
            require(git('rev-parse',COMMIT+':swdb-project/'+relative).decode().strip()==row['oid'],'consumer Git tree '+relative)
        for row in closure['files']:
            got=pin(row['path']);require(got['sha256']==row['sha256'] and got['bytes']==row['bytes'],'physical consumer '+row['relative'])
        oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n' for r in closure['files']).encode()).decode().splitlines()
        require(oids==[r['git_blob'] for r in closure['files']],'physical consumer Git blobs')
        consumers.append({'receipt':pin(path),'count':closure['count'],'total_bytes':closure['total_bytes']})
    require(len(consumers)==2 and read(PROFILE/'source-consumers-0.json')==read(PROFILE/'source-consumers-1.json'),'source before/after consumers exact')
    runtime=[]
    for row in [*expected['tools'].values(),*expected['wp_artifacts'],expected['why3_config']]:
        got=pin(row['path']);require(got['sha256']==row['sha256'],'physical selected tool/artifact/config');runtime.append(got)
    prefix=Path(expected['linux_prefix'])
    for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
        actual=[]
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink() and (path.is_file() or path.is_dir()),'regular support input')
            if path.is_file():
                got=pin(path);runtime.append(got);actual.append({'relative':str(path.relative_to(root)),'sha256':got['sha256']})
        require(actual==expected['portable_import_surfaces'][key],'complete support membership '+key)
    for row in expected['runtime_sources']:
        require(pin(prefix/'lib/frama-c-wp/core'/row['name'])['sha256']==row['sha256'],'runtime source '+row['name'])
    compiler=read(PROFILE/'compiler-runtime.json')
    require(compiler=={'runtime':expected['linux_project_identity_derivation']['runtime'],'identity':expected['linux_project_identity_derivation']['predicted_identity']},'actual current compiler/source context')
    for row in [expected['linux_clang_components']['command_executable'],expected['linux_clang_components']['driver']]:
        require(pin(row['path'])['sha256']==row['sha256'],'physical compiler component')
    compiler_root=Path(expected['linux_clang_components']['driver']['path']).parent.parent
    require(pin((compiler_root/'lib/libclang.so').resolve())['sha256']==expected['linux_clang_components']['parser']['sha256'],'physical libclang')
    headers=hashlib.sha256();count=0
    for label,root in [('libc++',compiler_root/'include/c++/v1'),('clang-resource',compiler_root/'lib/clang/22/include')]:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                got=pin(path);headers.update(label.encode()+b'\0'+str(path.relative_to(root)).encode()+b'\0');headers.update(bytes.fromhex(got['sha256']));count+=1
    require({'id':'llvm-standard-resource-headers','sha256':headers.hexdigest(),'files':count}==expected['linux_clang_components']['headers'],'complete compiler/header context')
    foundation=read(PROFILE/'foundation.json')
    for row in foundation['sources']:
        require(pin(row['path'])['sha256']==row['sha256'],'selected foundation source')
    require(pin(foundation['metadata_executable'])['sha256']==foundation['metadata_executable_sha256'],'retained foundation executable')
    anchors=read(PROFILE/'anchors.fresh.json')
    require(lineage(anchors)==expected['cached_anchor_lineage'],'fresh original anchor/source lineage')
    provenance=anchors['stdlib_provenance'];candidate=anchors['vector_reallocation_candidate']
    require(provenance['verdict']=='passed' and provenance['library']['id']=='libc++-22.1.8','full original-TU provenance retained')
    require(candidate['stdlib_binding_sha256']==hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest(),'candidate full provenance binding')
    require(candidate['known_origins_granted']==[] and candidate['original_caller_premises_added']==[],'no source origin or caller premise granted')
    manifest=read(PROFILE/'canonical-inputs/manifest.json')
    portable=json.loads(json.dumps(manifest));host=portable['source_view']['library_allocator_binding'].pop('certificate_sha256')
    require(host==digest(provenance) and portable==expected['canonical_manifest_portable'],'single host leaf omitted; full provenance rebound')
    physical=[{'path':str(p.relative_to(PROFILE/'canonical-inputs')),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted((PROFILE/'canonical-inputs').rglob('*')) if p.is_file() and p.name!='manifest.json']
    require(physical==expected['canonical_files'] and len(physical)==15,'all canonical nonmanifest bytes')
    require(pin(PROFILE/'canonical-inputs/sources/original.cc')['sha256']==expected['source_sha256'] and pin(SOURCE/'swdb-project'/expected['source_relative'])['sha256']==expected['source_sha256'],'original C++ source byte lineage')
    require(pin(PROFILE/'canonical-inputs/sources/original-caller.c')['sha256']==expected['lowered_sha256'],'original lowered caller lineage')
    launch=read(RAW/'launch.json')
    require(digest(launch['command'])==COMMAND_SHA and launch['source_commit']==COMMIT and Path(launch['source'])==SOURCE,'exact actual launch argv/source')
    require(launch['timeout_seconds']==policy['root_whole_seconds'] and launch['rss_cap_bytes']==policy['cap_bytes'] and launch['workers']==1,'exact actual launch limits')
    for name,wanted in expected['linux_launch_binding']['wrappers'].items():
        require(pin(RAW/name)['sha256']==wanted==launch['reviewed_wrapper_reuse'][name],'reviewed outer wrapper '+name)
    guards={name:read(RAW/name) for name in ('resources.json','outer-resources.json')}
    for name,value in guards.items():
        require(value['exit_code']==0 and not value['out_of_memory'] and not value['timed_out'] and value['peak_rss_bytes']<=policy['cap_bytes'],'settled guard '+name)
    lane=read(RAW/'lane.json')['socket_lane']
    require(lane['node']==args.node and lane['lease_generation']==args.generation and lane['ended_utc']==args.ended_utc and lane['exit_code']==0 and lane['numa_memory_policy']=='bind:'+str(args.node),'root-confirmed actual lane settlement')
    require(read(RAW/'source-after.json')=={'commit':COMMIT,'source_unchanged':True,'tracked_changes':''},'exact source after')
    require('PYTHONPATH' not in read(RAW/'dispatch-environment.json'),'outer PYTHONPATH removed')
    result=read(PROFILE/'result.json')
    require(result['producer_complete'] and result['within_profile_budget'] and result['source_after_clean'] and not result['unexecuted'] and not result.get('error'),'all six producer outcomes retained')
    require([r['id'] for r in result['runs']]==expected['target_ids'] and len(result['runs'])==6,'all six distinct source identities')
    for name in ('proof_acceptance','source_typed_bridge_established','body_acceptance','caller_acceptance','public_proof_record_created','universal_proof_setup_attested'):
        require(result[name] is False,'larger admission remains false '+name)
    require(not list((PROFILE/'workspace/records/proofs').glob('*.yaml')),'no public proof record')
    names=[]
    for node in ast.parse((SOURCE/'swdb-project/swdb/proof_setup.py').read_bytes()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in node.targets):names+=ast.literal_eval(node.value)
        elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES':names+=ast.literal_eval(node.value)
    identity=[{'path':'swdb/'+n,'sha256':pin(SOURCE/'swdb-project/swdb'/n)['sha256']} for n in names]
    identity += [{'path':'vocab/'+n,'sha256':pin(SOURCE/'swdb-project/vocab'/n)['sha256']} for n in ('proof_failure_classes.yaml','proof_subject_kinds.yaml')]
    reading={'version':'1','sha256':digest(identity)}
    require(pin(PROFILE/'reader/proof_report.ml')['sha256']==pin(SOURCE/'swdb-project/swdb/proof_report.ml')['sha256'],'actual native reader source')
    method=read(PROFILE/'method.json')
    require(method['tools']['seconds']==30 and method['tools']['provers']==['alt-ergo','z3','cvc5'],'complete unchanged portfolio')
    normal_flags(method['flags'])
    leaves=[];tasks=[];roots=set();unmatched=[]
    for run in result['runs']:
        ident=run['id'];row=next(x for x in manifest['obligations'] if x['id']==ident);directory=PROFILE/('leaf-'+ident)
        require(run['cwd']==str(directory) and pin(directory/'wp_input.c')['sha256']==row['sha256'],'actual leaf source '+ident)
        outcome=read(directory/'outcome.json');require(outcome==run['outcome'] and not outcome['assumptions'],'unchanged normal reader; no opaque premise '+ident)
        if outcome.get('reading'):
            require(outcome['reading']['check']==reading,'current ordinary reader identity '+ident)
        require(run['resources']==read(directory/'resources.json') and run['resources']['exit_code']==0 and not any(run['resources'][k] for k in ('timed_out','out_of_memory','output_limit')),'actual leaf resources '+ident)
        invocation=read(directory/'command.json')['argv']
        require(invocation[0]==expected['tools']['frama-c']['path'] and all(f in invocation for f in method['flags']),'normal complete command '+ident)
        normal_flags(invocation)
        native=read(directory/'wp-inventory.json');ordinary=read(directory/'wp-goals.json');prop='check_lemma_'+row['goal']
        require(native['complete'] is True and len(native['goals'])==len(ordinary)==len(outcome['goals'])==1,'complete single source-owned ordinary goal '+ident)
        goal=native['goals'][0];peer=ordinary[0]
        require(goal['property']==prop and goal['smoke'] is False and goal['targets']==[],'sole native source owner '+ident)
        require(all(goal.get(k)==peer.get(k) for k in ('goal','property','function','line','smoke','passed')),'native/ordinary peer '+ident)
        require(len(native['properties'])==2 and [p['property'] for p in native['properties'] if p['kind']=='lemma']==[prop] and all(not p['dependencies'] and p['origin'] is None and not p['extern'] and not p.get('generated_smoke_failure') for p in native['properties']),'complete dependency-free source property closure '+ident)
        closure=native['property_closure'];require(closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==2 and not any(closure[k] for k in ('unregistered_status_lookup_performed','unregistered_wp_smoke_properties','unregistered_wp_call_instances')),'registered source property census '+ident)
        with (directory/'wp-properties.csv').open() as stream:
            csvrows=list(csv.reader(stream,delimiter='\t'))
        require(csvrows==[['directory','file','line','function','property kind','status','property']],'legitimate complete global-lemma CSV '+ident)
        log=(directory/'frama-c.log').read_text();roots.update(re.findall(r'\(\* use ([\w.]+) \*\)',log));roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log))
        printed=re.findall(r'(?m)^  theory WP[0-9]*\s*\n(.*?)^  end\s*$',log,re.S)
        require(printed,'actual printed theory retained '+ident)
        wanted=required_definitions(ident)
        for index,body in enumerate(printed):
            declarations=re.findall(r'^\s*(predicate|function|goal|axiom|lemma|constant|val)\s+(\w+)',strip_comments(body),re.M)
            suffix='' if index==0 else str(index)
            require(set(declarations)=={('function' if name.startswith('L_') else 'predicate',name+suffix) for name in wanted}|{('goal','wp_goal')},'only source definitions and sole goal '+ident)
        census=read(directory/'task-census.json');require(not census['missing_noninternal_tasks'] and len(census['common_exports'])==len(printed),'all printed exports retained '+ident)
        for export in census['common_exports']:
            with (directory/'frama-c.log').open('rb') as stream:
                stream.seek(export['begin_byte']);segment=stream.read(export['end_byte']-export['begin_byte'])
            require(hashlib.sha256(segment).hexdigest()==export['sha256'] and export['goal']==goal['goal'],'common range/native identity '+ident)
        files=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'));require(files,'actual materialized tasks retained '+ident)
        for path in files:
            tree=forms(path.read_text());assertions=[x[1] for x in tree if x[0]=='assert'];checks=[n for n,x in enumerate(tree) if x[0]=='check-sat']
            require(assertions and len(checks)==1 and all(x==['get-info',':reason-unknown'] for x in tree[checks[0]+1:]),'sole SMT query/epilogue '+path.name)
            actual=canon(assertions[-1]);variants=[('literal_source',source_goal(ident))]
            if ident=='positive.cleanup':variants.append(('positive_antecedent_dominates_scalar_branch',source_goal(ident,positive_branch=True)))
            equal=[name for name,value in variants if actual==canon(value)]
            require(equal,'independent complete source goal '+ident+' '+path.name+' actual='+digest(actual))
            defs=check_source_definitions([x for x in tree if x[0]=='define-fun'],ident)
            attribution=[]
            for value in assertions[:-1]:
                require(not any(name in json.dumps(value) for name in ['check_lemma_','wp_goal','P_t25','L_t25']),'no desired/sibling theorem premise '+ident)
                key=digest(value)
                if key in PRIOR_SUPPORT_HASHES:
                    attribution.append({'sha256':key,'classification':'exact previously primary-source-attributed standard/Heap definitional support; old goals/proofs excluded'})
                else:
                    lifted=source_false_map(value,tree)
                    if lifted:attribution.append({'sha256':key,**lifted})
                    else:unmatched.append({'id':ident,'task':str(path),'assertion_sha256':key})
            tasks.append({'id':ident,**pin(path),'source_goal_equivalent':True,'normalization':equal,'goal_form_sha256':digest(assertions[-1]),'source_definitions':defs,'support_attribution':attribution,'non_goal_assertions':len(assertions)-1,'actual_submission_attested':False})
        leaves.append({'id':ident,'goal':goal['goal'],'property':prop,'native_results':goal['results'],'passed':goal['passed'],'normal_verdict':outcome['verdict'],'failure_class':outcome['failure_class'],'ordinary':1,'smoke':0,'properties':2,'CSV_rows':0,'input':pin(directory/'wp_input.c')})
    graph={};visiting=set()
    def visit(name):
        if name in graph:return
        require(name not in visiting,'acyclic selected import '+name);visiting.add(name)
        if name=='why3.BuiltIn.BuiltIn':graph[name]={'classification':'selected Why3 intrinsic core'}
        else:
            filename=name.rsplit('.',1)[0].replace('.','/')+'.mlw'
            candidates=[PROFILE/'canonical-inputs/theory/heap_reallocation.mlw'] if name=='heap_reallocation.Heap' else [prefix/'share/why3/stdlib'/filename,prefix/'share/frama-c/share/wp/why3'/filename]
            found=[p for p in candidates if p.is_file()];require(len(found)==1,'unambiguous actual import '+name)
            text=strip_comments(found[0].read_text());module=name.rsplit('.',1)[1]
            bodies=list(re.finditer(r'^(?:module|theory) '+re.escape(module)+r'\b[^\n]*\n(.*?)^end\s*$',text,re.M|re.S));require(len(bodies)==1,'complete actual import body '+name)
            body=bodies[0][1];edges=[]
            for match in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b',body,re.M):
                kind,target=match.groups();full=target if '.' in target else name.rsplit('.',1)[0]+'.'+target;edges.append({'kind':kind,'target':full});visit(full)
            propositions=re.findall(r'^\s*(axiom|lemma|goal)\s+(\w+)',body,re.M)
            if name=='heap_reallocation.Heap':require(not propositions,'source Heap definitions only; no desired axiom')
            graph[name]={'source':pin(found[0]),'module_body_sha256':hashlib.sha256(body.encode()).hexdigest(),'dependencies':edges,'proposition_declarations':propositions,'classification':'project definitions only' if name=='heap_reallocation.Heap' else 'selected standard arithmetic/maps/Qed TCB'}
        visiting.remove(name)
    for name in sorted(roots):visit(name)
    for row in read(PROFILE/'artifact-manifest.json'):
        require(pin(row['path'])['sha256']==row['sha256'],'producer artifact bytes '+row['relative'])
    require(snapshot(RAW)==initial,'entire raw unchanged before/after')
    require(not unmatched,'all actual support assertions source-attributed '+digest(unmatched))
    all_proven=all(x['normal_verdict']=='proven' and x['passed'] and 'valid' in x['native_results'] for x in leaves)
    require(result['all_six_producer_proven']==all_proven,'producer aggregate matches all actual leaves')
    output={'created':'2026-10-16 ET','classification':'PASS_CONDITIONAL_SIX_SOURCE_MATH_COLD' if all_proven else 'COMPLETE_SIX_SOURCE_COLD_NOT_PROVEN',
        'checks':len(CHECKS),'elapsed_seconds':time.monotonic()-started,'source_commit':COMMIT,'raw_root':str(RAW),
        'entry_sha256':ENTRY_SHA,'expected_sha256':EXPECTED_SHA,'actual_command_sha256':COMMAND_SHA,
        'result_pin':pin(PROFILE/'result.json'),'raw_files':len(initial),'raw_bytes':sum(x['bytes'] for x in initial),'raw_manifest':initial,'raw_pre_post_equal':True,
        'leaves':leaves,'materialized_tasks':tasks,'unmatched_supports':unmatched,'prior_support_source_attribution_pins':PRIOR_SUPPORT_PINS,
        'source_consumers':consumers,'source_and_helper_count':len(expected['source_blobs'])+len(expected['test_helper_pins']),
        'runtime_pins':runtime,'selected_runtime_sources':expected['runtime_sources'],'reader_check':reading,'guard':guards,'lane':lane,
        'full_fresh_host_certificate_sha256':host,'only_portable_host_digest_leaf_omitted':True,'sourceafter_clean':True,
        'direct_import_roots':sorted(roots),'import_source_closure':graph,'all_six_normal_producer_proven':all_proven,
        'old_ctor_dtor_math_imported_as_premise':False,'current_constructor_body_record_admitted':False,
        'source_typed_bridge_established':False,'body_acceptance':False,'caller_acceptance':False,'public_proof_record_created':False,
        'universal_proof_setup_attested':False,'actual_submission_count':None,'submitted_byte_attestation':False,
        'scope':'Six independent conditional mathematical source duties only under declared translation/standard support/solver TCB; no source allocation/Typed/lifetime/body/caller/public/ticket admission.'}
    encoded=(json.dumps(output,sort_keys=True,indent=2)+'\n').encode();require(len(encoded)<4*1024**2,'compact metadata output bound')
    signal.alarm(0);sys.stdout.buffer.write(encoded)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'classification':'REFUSED_PASSIVE_SIX_COLD','error_type':type(error).__name__,'error':str(error),'checks_before_refusal':len(CHECKS),'acceptance':False}))
        raise SystemExit(1)

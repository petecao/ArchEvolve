"""2026-10-16 ET. Passive default4 complete raw/native/task/context audit.
No project import, compiler, verifier, solver, native helper or tool execution.
Normal WP/Qed/CFG/driver/standard-theory/solver soundness remains explicit TCB.
"""
import ast
import collections
import csv
import hashlib
import io
import json
import os
import re
import shlex
import signal
import stat
import sys
import time
from pathlib import Path
import yaml

PROJECT=Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project')
POC=PROJECT/'.scratch/probata-proof-of-concept-2026-10-13'
RAW=Path('/private/tmp/probata-vector-default4-public-20261016-v2')
OUT=POC/'evidence/t25-default4-public-v2-independent-cold-v1-20261016.json'
MEMBERS=['std_vector_int_ctor','std_vector_float_ctor','std_vector_double_ctor','std_vector_int_ptr_ctor']
ATTEMPTS=[]
CHECKS=0

def need(value,label):
    global CHECKS
    CHECKS+=1
    if not value:raise ValueError(label)

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def read(path):return json.loads(path.read_bytes())
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
def stable(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def census():
    need(RAW.resolve(strict=True)==RAW and stat.S_ISDIR(RAW.lstat().st_mode),'physical raw root')
    rows=[]
    for path in sorted(RAW.rglob('*')):
        before=path.lstat()
        need(path.resolve(strict=True)==path and (stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode)),'no raw aliases or specials')
        row={'relative':str(path.relative_to(RAW)),'kind':'directory' if stat.S_ISDIR(before.st_mode) else 'regular','identity':stable(before)}
        if row['kind']=='regular':
            data=path.read_bytes();need(stable(path.lstat())==stable(before) and len(data)==before.st_size,'finite stable raw read')
            row.update(bytes=len(data),sha256=sha(data))
        rows.append(row)
    return rows

def audit(event,args):
    if event.startswith(('subprocess.','socket.')) or event in {'os.system','os.posix_spawn','os.exec','os.fork','os.forkpty','ctypes.dlopen'}:
        ATTEMPTS.append(event);raise RuntimeError('child/native/network prohibited')
    if event=='open':
        path,mode,flags=args
        writable=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and (flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writable:need(isinstance(path,str) and Path(path)==OUT,'only independent compact decision write permitted')
    if event in {'os.remove','os.rename','os.rmdir','os.mkdir','os.link','os.symlink','os.chmod','os.truncate','os.utime'}:
        ATTEMPTS.append(event);raise RuntimeError('filesystem mutation prohibited')

def literal(name,path):
    found=[node.value for node in ast.parse(path.read_bytes()).body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id==name for target in node.targets)]
    need(len(found)==1,'one literal '+name);return ast.literal_eval(found[0])

def source_check():
    names=[]
    for node in ast.parse((PROJECT/'swdb/proof_setup.py').read_bytes()).body:
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='CHECK_SOURCES' for target in node.targets):names+=ast.literal_eval(node.value)
        elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES':names+=ast.literal_eval(node.value)
    return {'version':'1','sha256':digest([{'path':'swdb/'+name,'sha256':pin(PROJECT/'swdb'/name)['sha256']} for name in names]+[{'path':'vocab/'+name,'sha256':pin(PROJECT/'vocab'/name)['sha256']} for name in ('proof_failure_classes.yaml','proof_subject_kinds.yaml')])},names

def main():
    started=time.monotonic();signal.alarm(110);sys.dont_write_bytecode=True;sys.addaudithook(audit)
    before=census();regular=[{key:row[key] for key in ('relative','bytes','sha256')} for row in before if row['kind']=='regular']
    root_manifest_path=POC/'evidence/t25-default4-public-v2-root-raw-manifest-20261016.json';root_manifest=read(root_manifest_path)
    need(regular==root_manifest['files'] and len(regular)==root_manifest['file_count']==85 and sum(row['bytes'] for row in regular)==root_manifest['bytes']==708621,'complete independently matched root raw manifest')
    need(sum(row['kind']=='directory' for row in before)>0 and not (RAW/'native-working').exists(),'settled relocated native source')
    root_execution_path=POC/'evidence/t25-default4-public-v2-root-execution-20261016.json';root_execution=read(root_execution_path)
    need(root_execution['resources']['exit_code']==0 and root_execution['resources']['out_of_memory'] is False and root_execution['resources']['timed_out'] is False and root_execution['entry_unchanged'] is True,'settled root controller healthy')
    need(root_execution['resources']['wall_seconds']<=900 and root_execution['resources']['peak_rss_bytes']<=8*1024**3,'root actual resource budgets')
    need(pin(Path(root_execution['log']['path']))==root_execution['log'],'original root stdout resource log pin')
    root_stdout_path=POC/'evidence/t25-default4-public-v2-root-stdout-20261016.json';root_stdout=read(root_stdout_path)
    need(read(Path(root_execution['log']['path']))==root_stdout,'entire physical root stdout')
    entry=POC/'prototype/25-default-ctors-20261016/public_default4_v2.py';need(pin(entry)['sha256']=='3af3ee7559e4c15d4f7e429ab96f4b83b12a3ddd40a16e521083df98b6f7fec0','frozen reviewed controller bytes')
    plan=read(RAW/'plan.json');progress=read(RAW/'incremental.json')
    need(plan['members']==MEMBERS==[row['member'] for row in progress['results']]==[row['member'] for row in root_stdout['results']],'exact ordered four complete results')
    need(plan['source_commit']=='a102e275cd23352aea8c268be3761d8a330b9be0' and plan['workers']==1 and plan['RSS_cap_bytes']==8*1024**3 and plan['job_seconds']==180 and plan['leaf_outer_seconds']==240 and plan['whole_seconds']==900 and plan['output_budget_bytes']==128*1024**2,'exact source and profile')
    need(progress['results']==root_stdout['results'] and root_stdout['retained_bytes']==708621 and root_stdout['all_four_proven'] is True and root_stdout['caller_admission'] is False,'controller final JSON/complete extent')
    source_pins=[]
    for row in plan['source_pins']:
        current=pin(PROJECT/row['relative']);need(current['sha256']==row['sha256'],'all nine original selected source consumers still match');source_pins.append(current)
    need(len(source_pins)==9,'nine use-time original source checks')
    checker,checker_names=source_check()
    parser=POC/'prototype/25-owned-source-view-20261016/source9-cold/semantic_terms.py';need(pin(parser)['sha256']=='eb0265a44d147f062292bd32c299edd58dd3045cec252cfbe0369eb4726948fa','reviewed complete syntax parser')
    forms_node=next(node for node in ast.parse(parser.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name=='forms')
    namespace={'re':re,'need':need};exec(compile(ast.Module(body=[forms_node],type_ignores=[]),'<syntax-only-forms>','exec'),namespace);forms=namespace['forms']
    method_path=RAW/'library/methods/wp-vector-default-constructors-v1.yaml';need(pin(method_path)['sha256']==plan['method_sha256'],'actual method pin')
    method=yaml.safe_load(method_path.read_bytes());need(method['id']=='method.wp-vector-default-constructors-v1' and method['sequence']==4 and method['evidence_kind']=='contract_fixture','ordinary normal fixture method')
    need(len(method['c_lowering']['translators'])==1 and method['c_lowering']['translators'][0]['id']=='swdb-c-lowering-9','no qualified source/body checker translator')
    wp=next(row for row in method['lineup'] if row['tool']=='frama-c-wp');wp_flags=['-wp','-wp-rte','-wp-cache','none','-wp-model','+real','-wp-par','1','-machdep','x86_64','-rte-initialized','@all','-wp-no-filter-init','-wp-out',str(RAW/'native-working'),'-wp-print','-wp-proof-trace']
    need(wp['flags']==wp_flags,'complete unchanged normal WP flags')
    fixture_method=RAW/'library/methods/contract-fixture-1.yaml';need(fixture_method.read_bytes()==(PROJECT/'tests/fixtures/proof/methods/contract-fixture-1.yaml').read_bytes(),'complete fixture policy copy')
    originals=read(POC/'evidence/t25-default4-public-preparation-v1-20261016.json')['canonical_originals'];originals={row['name']:row for row in originals}
    headers=literal('HEADERS',PROJECT/'swdb/c_lowering.py')
    totals=collections.Counter();members=[];support={};definitions={};declarations={};all_commands={};runtime_records=[]
    for item in progress['results']:
        name=item['member'];leaf=RAW/name;resource=read(leaf/'resources.json')
        need(resource==item['resources'] and type(resource['exit_code']) is int and resource['exit_code']==0 and resource['out_of_memory'] is False and resource['timed_out'] is False and resource['peak_rss_bytes']<=8*1024**3 and resource['wall_seconds']<=240,'exact clean final-row and per-leaf outcomes')
        public=read(leaf/'public.log');record=public['record'];yaml_path=RAW/'records'/public['path']
        need(public['path']=='proofs/'+record['id']+'.yaml' and digest(yaml.safe_load(yaml_path.read_bytes()))==digest(record),'entire authoritative YAML equals type-sensitive public JSON')
        need(record['id']==item['record_id'] and record['subject']=={'kind':'c_model','id':name} and record['verdict']==item['verdict']=='proven' and record['evidence_kind']=='contract_fixture' and record['pins']['summaries']==[],'exact independent C model record without caller dependencies')
        need(record['proof_setup_check']['verdict']=='passed' and record['proof_setup_check']['check']==checker and record['verdict_reading']=={'check':checker,'verdict':'proven'},'complete setup and reader source identity')
        need(record['bounds']=={'threads':1,'input_size':'unbounded'},'unbounded original receiver contract')
        original=(leaf/'original-model.c').read_bytes();want=originals[name]
        need(len(original)==want['bytes'] and sha(original)==want['sha256'] and original==Path(want['path']).read_bytes(),'whole unchanged original source unit')
        need(record['pins']['code']==record['pins']['contract']=={'id':name,'sha256':sha(original)},'complete original code and contract pins')
        need(record['pins']['std_models']==method['models']['std_vector']=={'id':'swdb-std-models-2','sha256':pin(PROJECT/'swdb/std_models.py')['sha256']},'unchanged complete model source identity')
        text=original.decode();body=re.search(r'static void '+re.escape(name)+r'\([^)]*\)\s*\{([^{}]*)\}\s*$',text);need(body is not None and re.sub(r'\s+','',body[1])=='this->data=NULL;this->size=0;this->capacity=0;','exact complete three-store default body')
        need('requires \\valid(this);' in text and 'assigns *this;' in text and 'ensures '+name[:-5]+'_valid(this) && this->size == 0;' in text,'original valid-receiver, assigns and empty representation contract')
        settings=record['settings'];flags=wp_flags+['-machdep','x86_64','-wp-prover','alt-ergo,z3,cvc5','-wp-timeout','30','-wp-par','1','-wp-smoke-tests','-wp-fct='+name]
        need(settings['flags']==flags and settings['session']=='fresh' and settings['environment_removed']==[] and settings['rss_cap_bytes']==8*1024**3 and settings['verifier_launched'] is True and settings['hint_count']==0 and settings['build_constants']==[],'actual full normal flags and no additional premise selectors')
        need(record['pins']['method_version']==record['proof_setup_check']['method_version']=={'id':method['id'],'sha256':plan['method_sha256']},'actual selected ordinary method')
        run=RAW/'runs'/record['id'];reports={row['name']:Path(row['path']) for row in record['evidence']['reports']}
        need(set(reports)=={'wp_input','wp_log','wp_goals','wp_properties','wp_inventory','wp_normalized'},'complete six raw reports')
        for report in [record['evidence']['adapter_log'],*record['evidence']['reports']]:need(Path(report['path']).is_relative_to(run) and pin(Path(report['path']))['sha256']==report['sha256'],'each record report physical content pin')
        generated=('\n'.join([*headers,text])+'\n').encode();need(generated==reports['wp_input'].read_bytes(),'whole WP input only standard headers plus unchanged source')
        pointer=settings['pointer_bounds'];need(pointer['kind']=='generated_c_model' and pointer['functions']==[name] and pointer['sites']==[] and pointer['source_sha256']==sha(generated),'no hidden pointer/domain insertions')
        native=read(reports['wp_inventory']);json_goals=read(reports['wp_goals']);native_goals={row['goal']:row for row in native['goals']};jg={row['goal']:row for row in json_goals};rg={row['goal']:row for row in record['goals']};props={row['property']:row for row in native['properties']};closure=native['property_closure']
        need(len(native_goals)==len(native['goals'])==10 and set(native_goals)==set(rg) and len(json_goals)==len(jg)==8 and set(jg)<set(native_goals),'complete unique native/JSON/record census')
        need(native['complete'] is True and len(props)==len(native['properties'])==closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==10 and closure['registration_membership_refreshed_after_consolidation'] is True and closure['unregistered_status_lookup_performed'] is False and closure['unregistered_wp_smoke_properties']==closure['unregistered_wp_call_instances']==[],'complete closed registered properties')
        for prop in props.values():
            need(prop['function']==name and prop['origin'] is None and prop['extern'] is False and prop['generated_smoke_failure'] is False and set(prop['dependencies'])<=set(props) and prop['status_registered'] is True and prop['property_export_origin']=='registered' and prop['call_context'] is None,'all properties and dependencies source-local without Extern/opaque calls')
        for gid,goal in native_goals.items():
            peer=rg[gid];need(goal['function']==name and goal['property'] in props and goal['passed'] is True and peer['property']==goal['property'] and peer['function']==name and peer['status']=='valid' and peer['smoke']==goal['smoke'],'every record/native goal identity')
            if goal['smoke']:
                need(goal['property']==name+'_wp_smoke_default_requires' and goal['targets']==[] and goal['results']==['timeout','unknown','timeout'] and jg[gid]['verdict']=='timeout' and jg[gid]['passed'] is True,'healthy nonproof default-requires smoke retained exactly')
                need(any(row['prover']=='Alt-Ergo:2.6.4' and row['success']==1 for row in jg[gid]['provers']),'WP nonproof smoke health normalization')
            else:need(goal['results']==['valid'],'every ordinary native goal Valid')
            if gid not in jg:need(not goal['smoke'] and goal['property'] in {name+'_terminates',name+'_exits'} and peer['source']=='wp_inventory','only inventory CFG termination/exit goals')
            else:need(jg[gid]['property']==goal['property'] and jg[gid]['line']==goal['line'] and jg[gid]['function']==name and jg[gid]['smoke']==goal['smoke'],'full WP JSON native point binding')
        csv_rows=list(csv.reader(io.StringIO(reports['wp_properties'].read_text()),delimiter='\t'));need(csv_rows[0]==['directory','file','line','function','property kind','status','property'] and len(csv_rows)==9 and all(row[3]==name and row[5] in {'Valid','Ignored'} for row in csv_rows[1:]) and sum(row[5]=='Ignored' for row in csv_rows[1:])==1,'complete eight CSV rows and sole assumed requires')
        need([row[6] for row in csv_rows[1:] if row[5]=='Ignored']==['\\valid(this)'],'original requires is explicit incoming premise')
        log=reports['wp_log'].read_text();printed=re.findall(r'(?m)^Goal (.*?)\n(.*?)(?=^Goal |\Z)',log,re.S);need(len(printed)==8 and 'Proved goals:   10 / 10' in log and 'Smoke Tests:       1 / 1' in log,'all printed ordinary/smoke contexts and native counts')
        need(sum('Prover Qed returns Valid' in body for _,body in printed)==3 and sum('Prover Alt-Ergo 2.6.4 returns Valid' in body for _,body in printed)==4 and sum('Prove: false.' in body for _,body in printed)==1,'all printed external/internal/smoke outcomes retained')
        relocation=read(leaf/'native-relocation.json');archive=leaf/'retained-native';actual_files=sorted(q for q in archive.rglob('*') if q.is_file())
        need(relocation['actual_original_WP_output']==str(RAW/'native-working') and relocation['retained_archive']==str(archive) and relocation['exact_bytes_before_after_move'] is True and [str(q.relative_to(archive)) for q in actual_files]==[row['relative'] for row in relocation['files']] and len(actual_files)==item['native_files_preserved']==7,'entire settled normal WP output relocation')
        task_rows=[];by_goal=collections.Counter()
        for task,want_task in zip(actual_files,relocation['files']):
            data=task.read_bytes();need(len(data)==want_task['bytes'] and sha(data)==want_task['sha256'] and task.suffix in {'.smt2','.psmt2'},'each original archived task byte identity')
            gid='typed_real_'+task.name.split('_Why3_')[0];need(gid in native_goals,'task exact native goal');by_goal[gid]+=1
            commands=forms(data.decode());need(commands and all(isinstance(command,list) and command for command in commands),'complete syntax command coverage')
            allowed={'set-logic','set-info','set-option','declare-sort','declare-fun','declare-const','declare-datatype','declare-datatypes','define-fun','assert','check-sat','get-info'};need(all(command[0] in allowed for command in commands),'no hidden SMT import/command')
            queries=[i for i,c in enumerate(commands) if c==['check-sat']];asserts=[(i,c) for i,c in enumerate(commands) if c[0]=='assert'];need(len(queries)==1 and asserts and all(len(c)==2 for _,c in asserts) and asserts[-1][0]<queries[0] and all(c==['get-info',':reason-unknown'] for c in commands[queries[0]+1:]),'all hypotheses precede sole final goal query and closed epilogue')
            command_rows=[]
            for index,command in enumerate(commands):
                key=digest(command);all_commands.setdefault(key,{'kind':command[0],'occurrences':0})['occurrences']+=1
                command_rows.append({'index':index,'kind':command[0],'sha256':key})
                if command[0]=='define-fun':definitions.setdefault(key,{'name':command[1],'occurrences':0})['occurrences']+=1
                if command[0].startswith('declare-'):declarations.setdefault(key,{'kind':command[0],'name':command[1] if isinstance(command[1],str) else None,'occurrences':0})['occurrences']+=1
            for _,command in asserts[:-1]:support.setdefault(digest(command),{'occurrences':0,'formula_sha256':digest(command[1])})['occurrences']+=1
            task_rows.append({'relative':str(task.relative_to(RAW)),'bytes':len(data),'sha256':sha(data),'native_goal':gid,'smoke':native_goals[gid]['smoke'],'commands':command_rows,'support_assertions':[digest(c) for _,c in asserts[:-1]],'sole_final_negated_goal_assertion_sha256':digest(asserts[-1][1]),'source_driver_formula_equivalence_independently_established':False})
        for goal in json_goals:
            external=[row for row in goal['provers'] if row['prover']!='qed'];need(by_goal[goal['goal']]==(3 if goal['smoke'] else 1 if external else 0),'no missing portfolio or ordinary task and no invented internal task')
        setup=record['proof_setup_check'];need(setup['hashes']['contract']==sha(original) and setup['hashes']['run_plan']==digest({'bounds':None,'budget_seconds':180.0,'defines':[],'function':name,'contract':'c_model.'+name,'contract_sha256':sha(original)}),'full type-sensitive public source/job plan hash')
        adapter=(run/'adapter.log').read_text();invocation=shlex.split(next(line[9:] for line in adapter.splitlines() if line.startswith('command: ')))
        expected=['opam','exec','--switch=framac-33','--','frama-c','-machdep','x86_64','wp_input.c','-print','-ocode','wp-normalized.c','-then',*flags,'-wp-report-json','wp-goals.json','-then','-load-module',str(run/'scratch/proof_report.cmxs'),'-report','-report-untried','-report-csv','wp-properties.csv']
        need(invocation==expected and len(setup['runs'])==1,'entire recorded normal verifier invocation')
        srun=setup['runs'][0];need(srun['tool']=='wp' and srun['verdict']=='passed' and srun['hashes']['wp_input.c']==setup['hashes']['wp_input.c']==sha(generated) and srun['hashes']['compiler_runtime']==digest(settings['compiler_runtime']) and srun['run_plan_sha256']==digest({'command':invocation,'flags':flags,'inputs':srun['hashes'],'bounds':None,'method_version':record['pins']['method_version']}),'complete generated-input launch/runtime context and run-plan hash')
        need('out of memory False, timed out False' in adapter and 'outcome: proven' in adapter,'retained actual native child resource and reader outcome')
        runtime_records.append({'member':name,'compiler_runtime':settings['compiler_runtime'],'assumptions':record['assumptions']})
        members.append({'member':name,'record_id':record['id'],'record_yaml':pin(yaml_path),'original_model':pin(leaf/'original-model.c'),'input':pin(reports['wp_input']),'normalized_source':pin(reports['wp_normalized']),'native_goals':native['goals'],'native_properties':native['properties'],'CSV_rows':csv_rows[1:],'printed_contexts':[{'heading':heading,'body_sha256':sha(body.encode())} for heading,body in printed],'native_tasks':task_rows,'resources':resource,'full_record_sha256':digest(record),'assumptions':record['assumptions'],'compiler_runtime':settings['compiler_runtime']})
        totals.update(records=1,ordinary=9,smokes=1,properties=10,CSV_rows=8,printed_contexts=8,tasks=7,external_ordinary_Valid=4,internal_Qed_Valid=3,inventory_only_CFG_Valid=2)
    prior_runtime_path=POC/'evidence/t25-member-all32-independent-current-why3-pins-20261016.json';prior_runtime=read(prior_runtime_path);runtime_now=[]
    need(pin(Path(prior_runtime['config']['path']))==prior_runtime['config'],'current Why3 configuration still exact retained selected mapping')
    for label,row in prior_runtime['selected'].items():
        current=pin(Path(row['physical_path']));need(current['sha256']==row['record_sha256'] and all(any(a['reference']['id']==label+'-'+row['version'] and a['reference']['sha256']==current['sha256'] for a in item['assumptions']) for item in runtime_records),'current selected solver bytes match all four historical record pins')
        runtime_now.append({'label':label,'configured_path':row['path'],'current':current,'historical_use_time_or_continuous_identity_attested':False})
    after=census();need(before==after and not ATTEMPTS,'complete raw content/nine-stat pre/post equality and zero external attempts')
    need(totals['records']==4 and totals['ordinary']==36 and totals['smokes']==4 and totals['tasks']==28,'full exact four-record cold census')
    return {'date':'2026-10-16 ET','classification':'PASS_FOUR_ORIGINAL_DEFAULT_CONSTRUCTOR_PUBLIC_RECORD_CONTEXT_CENSUS','scope':'Four unchanged standalone C model constructors under their original valid(this), assigns *this, empty-valid-result contracts and the normal installed WP/Qed/CFG/driver/standard-theory/solver TCB. No source C++/caller or general model dependency admission.','source_commit_at_execution':plan['source_commit'],'entry':pin(entry),'root_execution':pin(root_execution_path),'root_stdout':pin(root_stdout_path),'root_manifest':pin(root_manifest_path),'raw_root':str(RAW),'raw_manifest':before,'raw_pre_post_content_and_nine_stat_equal':True,'raw_regular_files':len(regular),'raw_regular_bytes':sum(row['bytes'] for row in regular),'source_pins':source_pins,'current_setup_reader':checker,'setup_reader_source_files':checker_names,'method':pin(method_path),'syntax_parser_source':pin(parser),'only_forms_function_executed':True,'totals':dict(totals),'members':members,'complete_task_command_index':all_commands,'complete_task_support_assertions':support,'complete_task_definitions':definitions,'complete_task_declarations':declarations,'current_Why3_reference':pin(prior_runtime_path),'current_selected_solver_pins':runtime_now,'checks':CHECKS,'external_attempts':ATTEMPTS,'wall_seconds':time.monotonic()-started,'scoped_original_C_model_body_evidence_eligible':True,'source_driver_full_formula_reconstruction_complete':False,'all_standard_assertions_primary_source_attribution_complete':False,'historical_full_runtime_loader_or_solver_consumed_bytes_attested':False,'Cxx_source_caller_admission':False,'Heap_Typed_ownership_lifetime_admission':False,'default_catalog_dependency_admission':False,'full_ticket25_acceptance':False,'normal_TCB_and_limits':['Every original archived task and all commands/hypotheses/definitions/declarations are indexed; no assertion or alternative solver task is dropped. Source-to-driver formula equivalence and primary-source attribution of every standard theory assertion remain normal WP/compiler/driver/foundation TCB, matching the accepted32 audit policy.','All36 ordinary native goals are directly Valid; four default-requires smoke attempts retain Timeout/Unknown/Timeout. Smoke health normalization does not prove consistency, source-state satisfiability or an ordinary theorem.','All three original header stores and original full contracts are unchanged. Constructor writes initialize only the receiver header and do not allocate/free/access payload. Typed WP layout/machdep correspondence, fresh receiver creation and C++ source correspondence are separate obligations.','Printed internal-Qed contexts and inventory-only termination/exit goals remain trusted WP/Qed/CFG outputs rather than independent SMT proofs.','The record compiler driver/parser and1982-header aggregate are retained; this audit does not reproduce historical full header/SDK/package/Python/native loader closure or independently establish source-to-binary correctness.','Current selected solver/config file hashes match the historical records at this finite observation. Actual historical resolution, generated-report-reader binary/runtime identity, solver-consumed bytes, original runtime immutability and continuous use-time closure remain explicit TCB.','The actual source was a102. A later HEAD does not relabel its historical identity; all nine selected source consumers and the current complete setup/reader aggregate were checked separately. No general construction, source ownership, move/swap/reallocation/destruction or full ticket25 result is implied.']}

if __name__=='__main__':
    try:
        result=main()
    except Exception as error:
        result={'date':'2026-10-16 ET','classification':'REFUSED_DEFAULT4_INDEPENDENT_COLD_V1','error':type(error).__name__+': '+str(error),'checks':CHECKS,'external_attempts':ATTEMPTS,'scientific_adoption':False}
    with OUT.open('x') as stream:json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
    print(json.dumps({'decision':pin(OUT),'classification':result['classification'],'totals':result.get('totals'),'checks':CHECKS},sort_keys=True))
    raise SystemExit(0 if result['classification'].startswith('PASS_') else 2)

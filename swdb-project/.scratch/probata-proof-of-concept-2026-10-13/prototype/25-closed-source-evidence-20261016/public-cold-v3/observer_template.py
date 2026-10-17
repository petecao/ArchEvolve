"""2026-10-16 ET. INERT independent public5 V3 cold metadata observer.
Root settlement plus exact-source review required before any remote execution.
No project/package imports, children, filesystem writes, C/AST/SMT transfer.
"""
import argparse
import ast
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import time
import xml.etree.ElementTree as ET

EXPECTED_BYTES = base64.b64decode('__EXPECTED_BASE64__')
EXPECTED_SHA = '__EXPECTED_SHA__'
YAML_BYTES = base64.b64decode('__YAML_BASE64__')
YAML_SHA = '__YAML_SHA__'
MAX_JSON = 8*1024**2
MAX_OUTPUT = 4*1024**2
CASE_IDS = ('safe','missing_bundle','stale_method','wrong_result','default_method')
METHOD = 'method.wp-vector-closed-source-v1'
CONTRACT = 'contract.fixture_vector_closed_no_growth'
PREFIX = 'test_public_closed_source_proo'
SELECTION = 'test_public_closed_source_proof_and_exact_opt_in_controls'


def need(ok, reason):
    if not ok: raise ValueError(reason)
def H(raw): return hashlib.sha256(raw).hexdigest()
def digest(value): return H(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def strict_json(raw):
    def pairs(rows):
        value={}
        for key,item in rows:
            need(key not in value,'duplicate JSON key');value[key]=item
        return value
    def bad(value): raise ValueError('nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def stable(s):
    return tuple(getattr(s,n) for n in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))


class Physical:
    def __init__(self): self.rows={}
    def pin(self,path,expected=None,git_blob=None):
        path=Path(path);need(path.is_absolute() and path.resolve(strict=True)==path,'canonical physical path')
        before=path.lstat();need(stat.S_ISREG(before.st_mode),'regular physical input')
        sha=hashlib.sha256();git=hashlib.sha1(b'blob '+str(before.st_size).encode()+b'\0')
        descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        with os.fdopen(descriptor,'rb') as stream:
            need(stable(os.fstat(stream.fileno()))==stable(before),'file replaced while opening')
            for block in iter(lambda:stream.read(1048576),b''): sha.update(block);git.update(block)
            need(stable(os.fstat(stream.fileno()))==stable(before),'file changed during read')
        need(stable(path.lstat())==stable(before),'file changed after read')
        row={'path':str(path),'bytes':before.st_size,'sha256':sha.hexdigest()}
        if expected:
            for k in ('bytes','sha256'):
                if k in expected: need(row[k]==expected[k],'physical '+k+' differs: '+str(path))
        if git_blob: need(git.hexdigest()==git_blob,'physical content differs from selected Git blob')
        previous=self.rows.get(str(path));value=(row,stable(before))
        need(previous is None or previous==value,'input changed across observations')
        self.rows[str(path)]=value
        return row
    def read(self,path,maximum=MAX_JSON):
        row=self.pin(path);need(row['bytes']<=maximum,'metadata size budget')
        raw=Path(path).read_bytes();need(len(raw)==row['bytes'] and H(raw)==row['sha256'],'metadata bytes changed')
        return raw
    def json(self,path): return strict_json(self.read(path))
    def unchanged(self):
        for path,(row,attributes) in list(self.rows.items()):
            need(stable(Path(path).lstat())==attributes,'physical metadata changed at final check')
            self.pin(path,row)


P=Physical()

def plain_tree(root):
    root=Path(root);need(root.resolve(strict=True)==root and root.is_dir(),'physical directory')
    files=[];pending=[root]
    while pending:
        parent=pending.pop()
        with os.scandir(parent) as entries:
            for item in entries:
                path=Path(item.path);mode=item.stat(follow_symlinks=False).st_mode
                need(not stat.S_ISLNK(mode),'unexpected physical input symlink')
                if stat.S_ISDIR(mode):pending.append(path)
                else:need(stat.S_ISREG(mode),'special file');files.append(path)
    return sorted(files)


def raw_snapshot(raw):
    base=raw/'closed-source-profile/pytest';alias=base/(PREFIX+'current');target=base/(PREFIX+'4')
    files=[];links=[];pending=[raw]
    while pending:
        parent=pending.pop()
        with os.scandir(parent) as entries:
            for item in entries:
                path=Path(item.path);s=item.stat(follow_symlinks=False)
                if stat.S_ISLNK(s.st_mode):
                    need(path==alias and os.readlink(path)==str(target),'unknown or rebound raw alias')
                    need(target.resolve(strict=True)==target and stat.S_ISDIR(target.lstat().st_mode),'alias target not physical')
                    links.append({'relative':str(path.relative_to(raw)),'literal_target':os.readlink(path),'bytes':s.st_size})
                elif stat.S_ISDIR(s.st_mode):pending.append(path)
                else:
                    need(stat.S_ISREG(s.st_mode) and s.st_size<=134217728,'raw special/oversized file')
                    row=P.pin(path);files.append({'relative':str(path.relative_to(raw)),**row})
    need(len(links)==1,'exact one pytest alias')
    need({p.name for p in base.iterdir()}=={PREFIX+str(i) for i in range(5)}|{PREFIX+'current'},'five exact physical test roots')
    files.sort(key=lambda r:r['relative']);links.sort(key=lambda r:r['relative'])
    total=sum(r['bytes'] for r in files)+sum(r['bytes'] for r in links)
    need(total<=536870912,'settled raw extent exceeded')
    return {'files':files,'aliases':links,'bytes':total}


def safe_module(path,expected_sha):
    raw=P.read(path,1024**2);need(H(raw)==expected_sha,'pure metadata helper pin')
    tree=ast.parse(raw)
    allowed={'hashlib','json','os','pathlib','re','stat','contextlib','shlex','shutil','subprocess','sys','types'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):need(all(a.name in allowed for a in n.names),'metadata helper import')
        elif isinstance(n,ast.ImportFrom):need(n.module=='pathlib','metadata helper from import')
    need(not any(isinstance(n,ast.If) for n in tree.body),'metadata helper must have no entry main')
    ns={'__name__':'independent_passive_metadata','__file__':str(path)}
    exec(compile(tree,str(path),'exec'),ns)
    return ns


def runtime_check(policy,control,raw):
    closed=safe_module(control/'closed_python_surface.py',policy['controller_files']['closed_python_surface.py']['sha256'])
    wp=safe_module(control/'reviewed_wp_gates.py',policy['controller_files']['reviewed_wp_gates.py']['sha256'])
    native=safe_module(control/'reviewed_native_gates.py',policy['controller_files']['reviewed_native_gates.py']['sha256'])
    python=closed['verify_python_metadata'](policy['python_surface_binding'])
    native['physical_runtime'](policy,type('Closed',(),closed))
    for path,sha in policy['runtime_files'].items():P.pin(path,{'sha256':sha})
    for label,root in policy['ocaml_packages'].items():
        rp=Path(root);wanted=sorted([{'relative':str(Path(path).relative_to(rp)),'sha256':sha} for path,sha in policy['runtime_files'].items() if Path(path).is_relative_to(rp)],key=lambda r:Path(r['relative']).parts)
        wp['import_surface'](root,wanted)
    prefix=Path(policy['tools']['frama-c']['path']).parent.parent
    for name,path in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
        wp['import_surface'](path,policy['portable_import_surfaces'][name])
    wp['header_surface_check_v4'](policy['linux_header_surfaces'],policy['linux_clang_components']['headers'],type('Closed',(),closed))
    for row in policy['tools'].values():P.pin(Path(row['path']).resolve(strict=True),{'sha256':row['sha256']})
    P.pin(policy['config']['path'],policy['config'])
    for path,sha in policy['wp_artifacts'].items():P.pin(path,{'sha256':sha})
    need(P.json(raw/'closed-native-runtime-before.json')==P.json(raw/'closed-native-runtime-after.json'),'native before/after metadata differs')
    roles=safe_module(control/'python_startup_roles_v2.py',policy['controller_files']['python_startup_roles_v2.py']['sha256'])
    startup={}
    for role in ('entry-isolated','pytest-child'):
        observed=P.json(raw/('initialized-python-'+role+'.json'))
        need(observed['exit_code']==0 and not observed['stderr'],'startup observer failed')
        actual=roles['check_role_observation_v2'](observed['request'],strict_json(observed['stdout']))
        need(actual==P.json(raw/('initialized-python-'+role+'-accepted.json')),'startup evidence differs from exact role check')
        startup[role]={'observation':P.pin(raw/('initialized-python-'+role+'.json')),'accepted':P.pin(raw/('initialized-python-'+role+'-accepted.json'))}
    return {'python':python,'runtime_files':len(policy['runtime_files']),'startup':startup,
            'native_pins':len(policy['native_runtime']['pins']),'native_trees':len(policy['native_runtime']['trees'])}


def consumer_check(expected,project,raw):
    before=P.json(raw/'closed-source-before.json');after=P.json(raw/'closed-source-after.json')
    need(before==after and before['source_commit']==expected['source_commit'],'source before/after closure differs')
    need(before['trees']==expected['consumer_roots'],'source consumer root identities')
    wanted={r['relative']:r for r in expected['consumer_files']};found=set()
    for name in expected['consumer_roots']:
        root=project/name
        for path in ([root] if root.is_file() else plain_tree(root)):found.add(str(path.relative_to(project)))
    need(found==set(wanted),'source consumer physical membership')
    observed={r['relative']:r for r in before['files']};need(set(observed)==set(wanted),'producer consumer census')
    for name,row in wanted.items():
        actual=P.pin(project/name,row,git_blob=row['git_blob']);primary=observed[name]
        need(primary['git_blob']==row['git_blob'] and primary['path']==str(project/name)
             and primary['sha256']==actual['sha256'] and primary['bytes']==actual['bytes'],'source consumer primary/physical mismatch')
    for name,sha in expected['source_files'].items():P.pin(project/name,{'sha256':sha})
    return {'before':P.pin(raw/'closed-source-before.json'),'after':P.pin(raw/'closed-source-after.json'),
            'files':len(wanted),'bytes':sum(r['bytes'] for r in wanted.values()),'git_blob_and_SHA256_equal':True}


def yaml_load(path):
    need(H(YAML_BYTES)==YAML_SHA,'frozen YAML reader changed')
    ns={'__name__':'independent_yaml_subset'};exec(compile(YAML_BYTES,'record_yaml_subset.py','exec'),ns)
    return ns['loads'](P.read(path))


def bundle_check(root,expected):
    catalog=P.json(root/'catalog.json');P.pin(root/'catalog.json',expected['catalog'])
    need(catalog['required_target_count']==82 and not catalog['source_admission'] and not catalog['caller_acceptance'],'historical catalog scope')
    wanted={'catalog.json',*(r['path'] for r in expected['catalog_documents'])}
    need({str(p.relative_to(root)) for p in plain_tree(root)}==wanted,'complete scientific bundle membership')
    documents={}
    for row in expected['catalog_documents']:
        path=root/row['path'];P.pin(path,row);documents[row['path']]=P.json(path)
    def resolve(location):
        row=location['document'];need(row in expected['catalog_documents'],'unregistered historical evidence document')
        value=documents[row['path']]
        for piece in location['pointer'].split('/')[1:]:
            key=piece.replace('~1','/').replace('~0','~');value=value[int(key)] if isinstance(value,list) else value[key]
        return value
    def visit(value):
        if isinstance(value,dict):
            if set(value)=={'document','pointer'}:resolve(value)
            for child in value.values():visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    visit(catalog)
    for component in catalog['components']:
        for target in component['targets']:
            old=resolve(target['canonical_obligation'])
            need(all(old[k]==target[k] for k in ('id','goal','kind','statement')) and old['sha256']==target['input_sha256'],'historical complete target/source input')
            primary=resolve(target['observation']['evidence'])
            need(primary['id']==target['id'] and primary.get('input_sha256',primary.get('input',{}).get('sha256'))==target['input_sha256'],'historical primary observation input')
    return {'catalog':P.pin(root/'catalog.json'),'objects':len(documents),'targets':82,'full_pointer_closure':True}


def source_result_check(record,reports,case_root,expected,policy):
    result_path=reports['closed_source_manifest.json'];result=P.json(result_path)
    need(result['method']==METHOD and result['proof_basis']=='checked closed source observation rule and exact conditional mathematical evidence','source proof basis')
    need(result['original_contract']==expected['expected_contract'] and result['caller_premises_added']==[],'source contract/premises')
    need(result['pins']==expected['source_pins'] and result['scientific_target_count']==82,'current source/result pins')
    rule=result['source_rule'];portable=copy.deepcopy(rule)
    certificate=portable['source_view']['library_allocator_binding'].pop('certificate_sha256')
    need(portable==expected['source_rule_portable'],'complete original source-rule derivation changed')
    provenance=record['settings']['stdlib_provenance']['unit']
    need(provenance['verdict']=='passed' and provenance['library']['id']=='libc++-22.1.8' and digest(provenance)==certificate,'complete current compiler certificate binding')
    need(P.json(reports['stdlib_provenance_unit'])==provenance,'retained original-TU certificate differs')
    binding=result['scientific_binding']
    need(binding['source_rule']==rule and binding['components']==expected['components'],'all82 exact targets/full historical contexts')
    need(binding['scientific_dependencies_bound'] is True and binding['complete_source_target_count']==82
         and binding['scientific_catalog_sha256']==expected['catalog']['sha256'] and binding['evidence_object_count']==91
         and binding['original_two_timeout_results_preserved'] is True
         and binding['original_native_reader_not_proven_preserved'] is True,'scientific evidence census/boundary')
    for key in ('historical_records_rewritten','source_typed_bridge_established','source_admission','public_proof_record_created','caller_acceptance'):
        need(binding[key] is False,'scientific preparation admission flag changed')
    need(binding['current_model_records_created']==[],'new model record adoption')
    original=rule['original_source_obligation_ledger']
    need(original['ordinary_count']==24 and original['smoke_count']==9 and original['frame_partitions']==13,'complete24/9/13 original census')
    goals=[{'goal':r['goal'],'property':r['goal'],'function':rule['function'],'status':'valid',
            'solver':expected['source_pins']['vector_closed_source_rule']['id'],'seconds':None,'source':'source_rule','smoke':False} for r in original['ordinary']]
    need(record['goals']==goals==result['source_obligations'],'full original ordinary goal ledger')
    for name,row in expected['source_rule_files'].items():
        key='closed_source_scientific-binding/source-rule/'+name
        P.pin(reports[key],row)
    need(record['pins']['c_lowering']['sha256']==rule['source_view']['original_lowering_sha256'],'original lowering source identity')
    P.pin(reports['c_lowering'],{'sha256':record['pins']['c_lowering']['sha256']})
    need(P.json(reports['closed_source_scientific-binding/manifest.json'])==binding,'binding primary manifest')
    need(P.json(reports['closed_source_scientific-binding/source-rule/manifest.json'])==rule,'source rule primary manifest')
    bundle=bundle_check(case_root/'library/proof_evidence/vector_closed_scientific_bundle',expected)
    return result,{'manifest':P.pin(result_path),'source_rule_digest':digest(rule),'bundle':bundle,
        'components':[{'id':c['id'],'targets':len(c['targets']),'historical_source_commit':c['historical_source_commit'],
                       'accepted_decision':c['accepted_decision'],'cold_evidence':c['cold_evidence']} for c in binding['components']]}


def expected_contract_entry(expected,control):
    clauses=list(expected['expected_contract'])
    if control=='wrong_result':clauses[-1]=r'ensures \result == 123;'
    return {'kind':'rewrite_contract','id':CONTRACT,'formal_frame':1,'version':'1.0',
        'provenance':{'origin':{'intrinsic_specification':'vector-closed-source-fixture-20261016'}},
        'proof_unit':{'function':'vector_realloc_v3_no_growth','source':{'root':'library',
            'path':'proof_units/vector_reallocation_v3.cc','sha256':expected['source_rule_files']['sources/original.cc']['sha256']}},
        'concurrency_frame':[],
        'clauses':[{'id':name,'role':role,'statement':'Closed source '+name,
            'discharge_mode':'runtime_guard','negative_control':{'id':name+'-control','check':name},
            'acsl':{'text':text,'uses':[]},'proof_placement':{'once':'self'}}
            for (name,role),text in zip((('pre','legality'),('frame','postcondition'),('post','postcondition')),clauses)],
        'pattern_key':[{'roles':['index','target'],'address_shapes':['stream','single_valued_indirect'],'update_kind':'read'}],
        'strategies':[],'uses_intrinsics':[],'uses_library_operations':[],'runtime_guards':[],
        'knobs':[],'preservation_obligations':[],'correctness_check':{'kernel':'fixture','check':'fixture'},
        'execution_witness':{'check':'fixture'},
        'negative_controls':[{'id':kind,'kind':kind,'check':'fixture'}
            for kind in ('overlapping_pointer','double_claim','dropped_operand')],'requirement_map':[]}


def record_check(case_root,control,expected,policy,project_runtime):
    retained=case_root/'retained-public-record.json';record=P.json(retained)
    proofs=list((case_root/'records/proofs').glob('*.yaml'))
    need(len(proofs)==1,'one physical proof YAML per case')
    physical=yaml_load(proofs[0]);need(digest(physical)==digest(record),'physical YAML differs from retained JSON semantics')
    method_id=METHOD if control!='default_method' else 'method.wp-vector-closed-default-v1'
    method_path=case_root/'library/methods'/(method_id.removeprefix('method.')+'.yaml')
    method=yaml_load(method_path);method_pin={'id':method_id,'sha256':P.pin(method_path)['sha256']}
    need(method['id']==method_id and method['status']=='draft' and method['evidence_kind']=='contract_fixture','explicit fixture method lifecycle')
    need(record['pins']['method_version']==method_pin==record['proof_setup_check']['method_version'],'selected method/file/setup pin')
    need(method['checks']['proof_setup_check']==expected['proof_setup_identity']
         and method['checks']['verdict_reading']==expected['proof_setup_identity'],'current method checker pins')
    translators=method['c_lowering']['translators']
    need(translators[0]==project_runtime['lowering_identity']['c_lowering'],'fresh selected compiler/lowering identity in method')
    required=[expected['source_pins'][name] for name in ('vector_closed_source_rule',
        'vector_closed_scientific_binding','vector_closed_scientific_bundle','vector_closed_source_route')]
    if control=='stale_method':
        changed=copy.deepcopy(required);changed[-1]['sha256']='0'*64
        need(translators[1:]==changed,'stale method mutation not exact')
    elif control=='default_method':need(len(translators)==1,'default control retained opt-in pins')
    else:need(translators[1:]==required,'all four current source checker/bundle/method pins')
    bundle=case_root/'library/proof_evidence/vector_closed_scientific_bundle'
    need(bundle.exists()==(control!='missing_bundle'),'missing-bundle control changed')
    unit=case_root/'library/proof_units/vector_reallocation_v3.cc'
    P.pin(unit,expected['source_rule_files']['sources/original.cc'])
    need(record['evidence_kind']=='contract_fixture' and record['subject']=={'kind':'library_summary','id':CONTRACT}
         and record['job']['adapter']=='wp' and record['settings']['verifier_launched'] is False,'record subject/admission boundary')
    setup=record['proof_setup_check']
    need(setup['check']==expected['proof_setup_identity'] and setup['verdict']=='passed','fresh universal setup report')
    for field in ('code','contract'):
        need(record['pins'][field]['id']==CONTRACT and re.fullmatch('[a-f0-9]{64}',record['pins'][field]['sha256']),'source/contract record pin')
    need(record['pins']['code']==record['pins']['contract'],'source summary content pins differ')
    entry=yaml_load(case_root/'library/rewrite_contracts/fixture_vector_closed_no_growth.yaml')
    need(entry==expected_contract_entry(expected,control) and digest(entry)==record['pins']['contract']['sha256'],
         'complete original summary/control content or content hash differs')
    plan={'bounds':None,'budget_seconds':300,'defines':[],'function':'vector_realloc_v3_no_growth',
          'contract':CONTRACT,'contract_sha256':record['pins']['contract']['sha256']}
    need(setup['hashes']['run_plan']==digest(plan) and setup['hashes']['contract']==plan['contract_sha256'],'current frozen job plan/contract')
    reports={}
    for row in record['evidence'].get('reports',[]):
        need(row['name'] not in reports and row['name'] not in ('wp_log','wp_goals','wp_properties','wp_inventory'),'native proof report boundary')
        path=Path(row['path']);need(path.is_relative_to(case_root/'runs'),'report escapes exact case run')
        P.pin(path,row);reports[row['name']]=path
    adapter_log=record['evidence']['adapter_log'];need(Path(adapter_log['path']).is_relative_to(case_root/'runs'),'adapter log path')
    P.pin(adapter_log['path'],adapter_log)
    detail=None
    if control=='safe':
        need(record['verdict']=='proven' and not record.get('unproven_properties') and 'failure_class' not in record,'safe source verdict')
        settings=record['settings'];need(settings['tool']=='checked-vector-source-rule' and settings['framework_source_rule_evaluated'] is True
            and settings['source_typed_bridge_established'] is False and settings['current_model_records_created']==[],'safe source/Typed/current model boundary')
        need(record['bounds']=={'threads':1,'input_size':'unbounded'},'source proof bounds')
        for name,wanted in expected['source_pins'].items():need(record['pins'][name]==wanted,'record current source checker pin')
        need('models' not in record['pins'],'historical model records relabeled current')
        expected_reports={'stdlib_provenance_unit','c_lowering','anchors','closed_source_manifest.json',
            'closed_source_scientific-binding/manifest.json','closed_source_scientific-binding/source-rule/manifest.json',
            *('closed_source_scientific-binding/source-rule/'+n for n in expected['source_rule_files'])}
        need(set(reports)==expected_reports,'complete exact source-result report census')
        result,detail=source_result_check(record,reports,case_root,expected,policy)
        for name in ('proof_basis','original_diagnostic','native_projected_diagnostic'):
            need(settings[name]==result[name],'source proof basis/native diagnostic changed')
        need(settings['original_diagnostic']['normal_verdict']=='not_proven' and settings['original_diagnostic']['ordinary']==24
             and settings['native_projected_diagnostic']['normal_verdict']=='not_proven'
             and settings['native_projected_diagnostic']['ordinary']==17,'original/projected native outcomes promoted')
        need(settings['historical_scientific_components']==[{'id':c['id'],'historical_identity':c['historical_identity'],
            'targets':len(c['targets'])} for c in expected['components']],'complete historical method/domain/source identities')
        assumptions=record['assumptions'];standard=[r for r in assumptions if r['reference']==record['pins']['std_models']]
        need(any(r['sentence']=='Allocation succeeds: every malloc (std::vector growth, new[]) returns usable memory, never null.' for r in standard)
             and any(r['sentence'].startswith('The pinned standard library ') for r in standard),'both original plain assumptions')
        for required in result['assumptions']:need(required in assumptions,'explicit source/library/allocator/historical TCB omitted')
        need(record['pins']['std_models']=={'id':'swdb-std-models-2','sha256':'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'},'pinned original library/allocator model')
        need(record['verdict_reading']=={'check':expected['proof_setup_identity'],'verdict':'proven'},'current source verdict reading')
        need(len(setup['runs'])==1,'exact one current source-rule preflight')
        run=setup['runs'][0];need(run['verdict']=='passed' and run['tool']=='wp' and run['invocation']=='checked-source-rule-evaluation'
             and run['native_verifier_launched'] is False and run['proof_basis']==result['proof_basis'],'current preflight basis')
        hashes=run['hashes'];need(hashes['vector_closed_source']==digest(result),'current result preflight hash')
        runtime=settings['compiler_runtime'];need(runtime==project_runtime['runtime'],'fresh compiler/runtime changed')
        for key,value in policy['linux_clang_components'].items():need(runtime[key]==value,'actual compiler physical component')
        need(hashes['compiler_runtime']==digest(runtime),'current preflight compiler binding')
        provenance=settings['stdlib_provenance']['unit'];need(hashes['stdlib_provenance']==digest({'unit':H(json.dumps(provenance,sort_keys=True).encode())}),'current original-TU preflight')
        inputs={str(path):P.pin(path)['sha256'] for name,path in reports.items() if name=='c_lowering' or name.startswith('closed_source_')}
        absolute={k:v for k,v in hashes.items() if Path(k).is_absolute()}
        need(absolute==inputs,'complete current absolute generated-input census')
        need(hashes['lowering']==record['pins']['c_lowering']['sha256'],'current original lowering hash')
        need(run['run_plan_sha256']==digest({'command':[],'flags':[],'inputs':hashes,'bounds':None,'method_version':method_pin}),'current native-free evaluation plan')
        need(all(setup['hashes'][k]==v for k,v in hashes.items()),'full setup/run hash agreement')
        anchors=P.json(reports['anchors']);need(anchors['function']=='vector_realloc_v3_no_growth'
             and anchors['c_lowering_sha256']==record['pins']['c_lowering']['sha256']
             and anchors['stdlib_provenance']==provenance
             and anchors['stdlib_substitutions']==result['source_rule']['source_view']['library_allocator_binding']['original_substitutions'],'original complete lowering anchors/certificate lineage')
    else:
        need(record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct','named unsupported control unexpectedly proved')
        need(setup['runs']==[],'unsupported control reached generated/native invocation')
    return {'control':control,'record':P.pin(retained),'physical_yaml':P.pin(proofs[0]),'id':record['id'],
            'subject':record['subject'],'verdict':record['verdict'],'failure_class':record.get('failure_class'),
            'method':method_pin,'setup_check':setup['check'],'setup_runs':len(setup['runs']),
            'complete_evidence_reports':[{'name':n,**P.pin(path)} for n,path in reports.items()],
            'conditional_source_science':detail,'native_verifier_launched':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--ended-utc',required=True)
    args=parser.parse_args();need(args.generation>0 and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',args.ended_utc),'root settlement arguments')
    need(__debug__ and not sys.flags.optimize and sys.flags.isolated and sys.dont_write_bytecode,'isolated -I -B cold observer')
    signal.alarm(180);resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    def audit(event,values):
        if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
            raise RuntimeError('cold observer forbids child/native/network execution')
        if event=='import' and values[0].split('.')[0] in ('swdb','yaml','pytest','clang','psutil'):
            raise RuntimeError('cold observer forbids target/project package import')
        if event=='open':
            path,mode,flags=values
            writable=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags & os.O_ACCMODE != os.O_RDONLY or bool(flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writable:raise RuntimeError('cold observer forbids every writable open')
        if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.truncate','os.chmod','os.chown','os.utime'):
            raise RuntimeError('cold observer forbids filesystem mutation')
    sys.addaudithook(audit)
    need(H(EXPECTED_BYTES)==EXPECTED_SHA,'exact expected context')
    expected=strict_json(EXPECTED_BYTES);raw=Path(expected['raw_root']);project=Path(expected['project'])
    need(raw.resolve(strict=True)==raw and project.resolve(strict=True)==project,'canonical raw/project')
    started=time.monotonic();initial=raw_snapshot(raw)
    launch=P.json(raw/'launch.json');need(launch['command']==expected['command']['argv']
        and launch['source_commit']==expected['source_commit'] and launch['source']==str(project.parent)
        and launch['node']==0 and launch['workers']==1 and launch['rss_cap_bytes']==8589934592
        and launch['timeout_seconds']==1200,'exact root launch/source/lane/resource plan')
    policy=P.json(raw/'control/policy.json');P.pin(raw/'control/policy.json',expected['policy']);P.pin(raw/'control/entry.py',expected['entry'])
    need(policy['linux_launch_binding']['node']==0,'exact selected node')
    for row in expected['command']['controller_inputs']:P.pin(raw/'control'/row['name'],row)
    for name,sha in policy['linux_launch_binding']['wrappers'].items():
        need(launch['reviewed_wrapper_reuse'][name]==sha,'root wrapper lineage');P.pin(raw/name,{'sha256':sha})
    resources={name:P.json(raw/name) for name in ('resources.json','outer-resources.json')}
    for row in resources.values():
        need(row['exit_code']==0 and not row['out_of_memory'] and not row['timed_out']
             and not row.get('output_limit',False) and row['peak_rss_bytes']<=8589934592
             and row['wall_seconds']<1200,'healthy settled producer whole-tree resource evidence required')
    lane=P.json(raw/'lane.json')['socket_lane']
    need(lane['node']==0 and lane['lease_generation']==args.generation and lane['ended_utc']==args.ended_utc
         and lane['exit_code']==0 and lane['numa_memory_policy']=='bind:0','root-confirmed settled lane generation')
    need(P.json(raw/'source-after.json')=={'commit':expected['source_commit'],'source_unchanged':True,'tracked_changes':''},'root final source integrity')
    producer=P.json(raw/'closed-result.json')
    need(producer['status']=='PRODUCER_WORKFLOW_COMPLETE' and producer['source_commit']==expected['source_commit']
         and producer['exit_code']==0 and producer['tests']==5 and producer['records']==5
         and producer['independent_cold_acceptance'] is False,'complete original producer required; incomplete V3 cannot be promoted')
    extent=producer['finalization'];need(extent['reserve_bytes']==65536 and extent['result_byte_cap']==16384
         and extent['margin_seconds']==1.0 and extent['whole_seconds']==1200
         and extent['elapsed_seconds_before']<1199 and extent['result_bytes']==P.pin(raw/'closed-result.json')['bytes']
         and extent['projected_total_bytes']==extent['before']['bytes']+extent['result_bytes']<=536870912,'bounded exact finalization evidence')
    source=consumer_check(expected,project,raw)
    runtime=runtime_check(policy,raw/'control',raw)
    project_runtime=P.json(raw/'closed-project-runtime.json')
    for key,value in policy['linux_clang_components'].items():need(project_runtime['runtime'][key]==value,'actual compiler plan')
    root=ET.fromstring(P.read(raw/'closed-source-profile/junit.xml'))
    suites=list(root.iter('testsuite'));cases=list(root.iter('testcase'))
    need(root.tag=='testsuites' and len(suites)==1 and len(cases)==5 and suites[0].get('tests')=='5'
         and all(suites[0].get(n)=='0' for n in ('errors','failures','skipped'))
         and not any(list(root.iter(n)) for n in ('error','failure','skipped')),'complete actual five-case JUnit')
    need([c.get('name') for c in cases]==[SELECTION+'['+name+']' for name in CASE_IDS]
         and all(c.get('classname')=='tests.test_vector_reallocation_closed_public_workflow' for c in cases),'exact ordered JUnit identities')
    base=raw/'closed-source-profile/pytest'
    records=[record_check(base/(PREFIX+str(i)),name,expected,policy,project_runtime) for i,name in enumerate(CASE_IDS)]
    need(len({r['id'] for r in records})==5 and [r['verdict'] for r in records]==['proven']+['not_proven']*4,'all five distinct expected outcomes')
    census=P.json(raw/'closed-record-census.json')
    need(census['records']==5 and census['source_rule_proven']==1 and census['unsupported_controls']==4
         and census['original_native_results_preserved'] is True and census['independent_cold_acceptance'] is False,'producer record census')
    need(census['physical_records']==[{'path':str(Path(r['record']['path']).relative_to(raw)),'sha256':r['record']['sha256']} for r in records],'producer retained record hashes')
    proofpaths=[r for r in initial['files'] if '/records/proofs/' in '/'+r['relative'] and r['relative'].endswith('.yaml')]
    need(len(proofpaths)==5,'extra current model/proof records')
    need(not any(Path(r['relative']).name in ('frama-c.log','wp_goals.json','wp_properties.csv','wp_inventory.json') for r in initial['files']),'new native WP proof artifact')
    final=raw_snapshot(raw);need(initial==final,'complete raw pre/post immutability')
    P.unchanged()
    result={'created':'2026-10-16 ET','classification':'complete conditional source-rule public fixture integrity; root acceptance remains separate',
        'source_commit':expected['source_commit'],'raw_root':str(raw),'lane':lane,'resources':resources,
        'entry_sha256':expected['entry']['sha256'],'policy_sha256':expected['policy']['sha256'],
        'expected_sha256':EXPECTED_SHA,'source':source,'runtime':runtime,'records':records,
        'JUnit':{'cases':5,'failed':0,'errors':0,'skipped':0},'historical_mathematical_targets':82,
        'original_census':{'ordinary':24,'smokes':9,'frame_partitions':13},
        'native_original_and_projected_outcomes_preserved':'not_proven; no native caller theorem',
        'new_WP_solver_job_requested_by_exact_source':False,'new_model_records':[],
        'raw_manifest':final,'raw_pre_post_equal':True,'observed_file_pins':len(P.rows),
        'elapsed_seconds':time.monotonic()-started,'actual_partial_or_refused_run_promoted':False,
        'source_typed_bridge_established':False,'default_or_caller_admission':False,'full_ticket25':False,
        'prior_public_V2_failure_preserved':True,'continuous_source_runtime_immutability_claimed':False,
        'scope':'All82 accepted conditional theorem contexts and exact current source rule remain under their reviewed historical/compiler/library/allocator/source TCB; no solver/proof rerun, raw C/AST/SMT transfer or arbitrary method adoption.'}
    encoded=json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)
    need(len(encoded.encode())<=MAX_OUTPUT,'compact metadata output budget')
    print(encoded)


if __name__=='__main__':
    try:main()
    except (Exception,SystemExit) as error:
        print(json.dumps({'classification':'REFUSED_OR_INCOMPLETE_COLD_OBSERVER','error':type(error).__name__,
            'reason':str(error)[:4096],'actual_partial_or_refused_run_promoted':False,
            'source_typed_bridge_established':False,'default_or_caller_admission':False,'full_ticket25':False},sort_keys=True))
        raise SystemExit(1)

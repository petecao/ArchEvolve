"""2026-10-16 ET. Author inert complete record-predicate diagnostic, no execution."""
import ast
import base64
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'record-metadata-probe-v2'
OUT.mkdir(exist_ok=True)
SOURCE=(HERE/'full-observer-v3/observer-v3.py').read_bytes()
assert hashlib.sha256(SOURCE).hexdigest()=='6e51a0f12b9d535d3827d1d717a410203d2bb4554533de65fd1d35024f491666'
TREE=ast.parse(SOURCE)
WANTED={'need','H','digest','strict_json','stable','Physical','plain_tree','raw_snapshot','yaml_load','bundle_check','source_result_check','expected_contract_entry','record_check'}
SEMANTIC={'bundle_check','source_result_check','record_check'}
HARD={'one physical proof YAML per case','report escapes exact case run','adapter log path','unregistered historical evidence document'}
class Trace(ast.NodeTransformer):
    def __init__(self,function):self.function=function;self.observations=0;self.comparisons=0
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='need':
            assert len(node.args)==2 and not node.keywords
            reason=node.args[1];assert isinstance(reason,ast.Constant) and isinstance(reason.value,str)
            if reason.value not in HARD:
                self.observations+=1;node.func.id='observe';node.args.extend([ast.Constant(self.function),ast.Constant(node.lineno)])
        return node
    def visit_Compare(self,node):
        self.generic_visit(node)
        if all(isinstance(op,(ast.Eq,ast.NotEq)) for op in node.ops):
            self.comparisons+=1
            thunks=[ast.Lambda(args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=value) for value in [node.left,*node.comparators]]
            return ast.copy_location(ast.Call(func=ast.Name(id='compare_trace',ctx=ast.Load()),args=[ast.List(elts=thunks,ctx=ast.Load()),ast.Constant([type(op).__name__ for op in node.ops]),ast.Constant(self.function),ast.Constant(node.lineno)],keywords=[]),node)
        return node
nodes=[];census=[]
for node in TREE.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in WANTED:
        if node.name in SEMANTIC:
            transform=Trace(node.name);node=transform.visit(node);census.append({'function':node.name,'semantic_need_sites':transform.observations,'typed_equality_sites':transform.comparisons})
        nodes.append(node)
assert len(nodes)==len(WANTED)
main=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='main')
def named_assign(node,name):return isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.For) and ast.unparse(n.iter)=="expected['settlement']['metadata_pins']")
end=next(i for i,n in enumerate(main.body) if named_assign(n,'source'))
project_start=next(i for i,n in enumerate(main.body) if named_assign(n,'project_runtime'))
records_start=next(i for i,n in enumerate(main.body) if named_assign(n,'records'))
final_start=next(i for i,n in enumerate(main.body) if named_assign(n,'final'))
segments=[('root_before',main.body[start:end],['expected'],"return policy"),
          ('root_junit',main.body[project_start:records_start],['policy'],"return project_runtime"),
          ('root_after',main.body[records_start+1:final_start],['records','initial'],"return True")]
for name,body,args,ending in segments:
    prefix=ast.parse("raw=ROOT\nproject=Path(expected['project'])\nargs=types.SimpleNamespace(generation=619,ended_utc='2026-10-16T21:28:57Z')").body if name=='root_before' else ast.parse('raw=ROOT').body
    wrapper=ast.FunctionDef(name=name,args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=a) for a in args],kwonlyargs=[],kw_defaults=[],defaults=[]),body=prefix+body+ast.parse(ending).body,decorator_list=[])
    transform=Trace(name);wrapper=transform.visit(wrapper);nodes.append(wrapper);census.append({'function':name,'semantic_need_sites':transform.observations,'typed_equality_sites':transform.comparisons})
FUNCTION_BYTES=ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))).encode()
EXPECTED=(HERE/'expected.json').read_bytes();READER=(HERE/'strict-yaml-repair-v1/record_yaml_subset_v3.py').read_bytes()
root_observation=HERE.parents[2]/'evidence/t25-public-v4-root-observation-20261016t2130z.json'
RECORDS=json.loads(root_observation.read_bytes())['actual']['closed-record-census.json']['physical_records']
def literal(name,raw):return name+'=base64.b64decode('+repr(base64.b64encode(raw).decode())+')\n'+name+'_SHA='+repr(hashlib.sha256(raw).hexdigest())+'\n'
header='''"""2026-10-16 ET. INERT complete five-case record/job metadata diagnostic only."""
import base64, copy, hashlib, json, math, os, re, resource, signal, stat, sys, time, types
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-1433b8f5-t25-closed-source-public-v4')
PREFIX='test_public_closed_source_proo'
CASES=('safe','missing_bundle','stale_method','wrong_result','default_method')
CASE_IDS=CASES
SELECTION='test_public_closed_source_proof_and_exact_opt_in_controls'
METHOD='method.wp-vector-closed-source-v1'
CONTRACT='contract.fixture_vector_closed_no_growth'
MAX_JSON=8*1024**2
'''
header+=literal('FUNCTION_BYTES',FUNCTION_BYTES)+literal('EXPECTED_BYTES',EXPECTED)+literal('YAML_BYTES',READER)
header+='YAML_SHA=YAML_BYTES_SHA\nRECORD_PINS='+repr(RECORDS)+'\n'
body='''
def hard(ok,reason):
    if not ok:raise ValueError(reason)

CASE=None
GROUPS={}
FAILURES=[]
PREDICATE_COUNT=0
PREDICATE_HASH=hashlib.sha256()
EQUALITY_COUNT=0
EQUALITY_HASH=hashlib.sha256()
TYPE_CONFUSIONS=[]
TYPE_CONFUSION_COUNT=0
UNCLASSIFIED_EQUALITY_COUNT=0

def framed(target,value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    target.update(len(raw).to_bytes(8,'big')+raw)

def observe(ok,reason,function,line):
    global PREDICATE_COUNT
    row={'case':CASE,'function':function,'line':line,'reason':reason,'passed':bool(ok)}
    PREDICATE_COUNT+=1;framed(PREDICATE_HASH,row)
    key=json.dumps([CASE,function,line,reason]);group=GROUPS.setdefault(key,{'case':CASE,'function':function,'line':line,'reason':reason,'passed':0,'failed':0})
    group['passed' if ok else 'failed']+=1
    if not ok and len(FAILURES)<64:FAILURES.append(row)

def canonical(value):
    if type(value) is set and all(type(item) is str for item in value):
        return json.dumps({'text_set':sorted(value)},sort_keys=True,separators=(',',':')).encode()
    def valid(item):
        if type(item) in (str,int,bool,type(None)):return True
        if type(item) is float:return math.isfinite(item)
        if type(item) is list:return all(valid(child) for child in item)
        if type(item) is dict:return all(type(k) is str and valid(v) for k,v in item.items())
        return False
    if valid(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return None

def compare_trace(thunks,ops,function,line):
    global EQUALITY_COUNT,TYPE_CONFUSION_COUNT,UNCLASSIFIED_EQUALITY_COUNT
    left=thunks[0]()
    for op,thunk in zip(ops,thunks[1:]):
        right=thunk();python_equal=left==right;a,b=canonical(left),canonical(right)
        strict_equal=None if a is None or b is None else type(left) is type(right) and a==b
        row={'case':CASE,'function':function,'line':line,'operation':op,'left_type':type(left).__name__,'right_type':type(right).__name__,
            'python_equal':bool(python_equal),'strict_JSON_equal':strict_equal,
            'left_sha256':None if a is None else hashlib.sha256(a).hexdigest(),'right_sha256':None if b is None else hashlib.sha256(b).hexdigest()}
        EQUALITY_COUNT+=1;framed(EQUALITY_HASH,row)
        if strict_equal is None:UNCLASSIFIED_EQUALITY_COUNT+=1
        elif bool(python_equal)!=strict_equal:
            TYPE_CONFUSION_COUNT+=1
            if len(TYPE_CONFUSIONS)<16:TYPE_CONFUSIONS.append(row)
        outcome=python_equal if op=='Eq' else not python_equal
        if not outcome:return outcome
        left=right
    return True

def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        raise RuntimeError('record diagnostic forbids tools/children/network/native libraries')
    if event=='open':
        hard(not (isinstance(args[1],str) and any(c in args[1] for c in 'wax+')) and not args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND),'diagnostic writable open refused')
    if event in ('os.remove','os.rmdir','os.mkdir','os.rename','os.link','os.symlink','os.chmod','os.chown','os.truncate','os.utime','resource.setrlimit'):
        raise RuntimeError('diagnostic mutation/cap-change refused')
    if event=='import' and args[0].split('.')[0] in ('swdb','yaml','pytest','clang','ctypes','psutil'):
        raise RuntimeError('diagnostic project/third-party/native import refused')

def main():
    global P,CASE
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024));resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('record diagnostic alarm')));signal.alarm(45)
    sys.addaudithook(audit)
    hard(__debug__ and sys.flags.isolated and sys.dont_write_bytecode,'isolated no-bytecode diagnostic required')
    for value,sha in ((FUNCTION_BYTES,FUNCTION_BYTES_SHA),(EXPECTED_BYTES,EXPECTED_BYTES_SHA),(YAML_BYTES,YAML_BYTES_SHA)):
        hard(hashlib.sha256(value).hexdigest()==sha,'frozen diagnostic dependency differs')
    exec(compile(FUNCTION_BYTES,'reviewed-record-metadata-functions','exec'),globals())
    class RawPhysical(Physical):
        def pin(self,path,expected=None,git_blob=None):
            path=Path(path);hard(path.is_absolute() and ROOT in path.parents,'metadata input escapes original raw')
            return super().pin(path,expected,git_blob)
    P=RawPhysical();started=time.monotonic();expected=strict_json(EXPECTED_BYTES)
    initial=raw_snapshot(ROOT);CASE='root';policy=root_before(expected);runtime=root_junit(policy);rows=[];summaries=[]
    for index,case in enumerate(CASES):
        CASE=case;base=ROOT/'closed-source-profile/pytest'/(PREFIX+str(index));record_path=base/'retained-public-record.json'
        P.pin(record_path,{'sha256':RECORD_PINS[index]['sha256']});hard(str(record_path.relative_to(ROOT))==RECORD_PINS[index]['path'],'exact root-observed record path')
        record=P.json(record_path);before=PREDICATE_COUNT;failures_before=sum(g['failed'] for g in GROUPS.values());complete=True;exception=None
        try:summaries.append(record_check(base,case,expected,policy,runtime))
        except (ValueError,TypeError,IndexError,KeyError,UnicodeError,RecursionError) as error:
            complete=False;exception={'class':type(error).__name__,'reason':'hard physical/path/shape gate refused; no acceptance'}
        plan={'bounds':None,'budget_seconds':300,'defines':[],'function':'vector_realloc_v3_no_growth','contract':CONTRACT,'contract_sha256':record['pins']['contract']['sha256']}
        float_plan=dict(plan,budget_seconds=300.0)
        setup=record['proof_setup_check'];matrix={'integer_budget_type':type(plan['budget_seconds']).__name__,'float_budget_type':type(float_plan['budget_seconds']).__name__,
            'integer_plan_sha256':digest(plan),'source_float_plan_sha256':digest(float_plan),'actual_plan_sha256':setup['hashes']['run_plan'],
            'integer_plan_matches':digest(plan)==setup['hashes']['run_plan'],'source_float_plan_matches':digest(float_plan)==setup['hashes']['run_plan'],
            'contract_materialization_matches':setup['hashes']['contract']==record['pins']['contract']['sha256'],
            'bounds_null_preserved_in_both_plans':plan['bounds'] is None and float_plan['bounds'] is None}
        rows.append({'case':case,'record':P.pin(record_path),'all_record_predicates_reached':complete,'exception':exception,'predicate_count':PREDICATE_COUNT-before,
            'failed_predicates':sum(g['failed'] for g in GROUPS.values())-failures_before,'exact_plan_matrix':matrix,
            'safe_bounds_strict_JSON_matches':digest(record['bounds'])==digest({'threads':1,'input_size':'unbounded'}) if case=='safe' else None})
    CASE='root';root_post_complete=False;root_post_exception=None
    try:root_after(summaries,initial);root_post_complete=True
    except (ValueError,TypeError,IndexError,KeyError,UnicodeError,RecursionError) as error:root_post_exception={'class':type(error).__name__,'reason':'root post-record shape gate refused'}
    final=raw_snapshot(ROOT);hard(digest(initial)==digest(final),'complete raw pre/post census differs')
    P.unchanged();pins=[dict(row,stable=list(attributes)) for _,(row,attributes) in sorted(P.rows.items())]
    failed=sum(g['failed'] for g in GROUPS.values());result={'date':'2026-10-16 ET','classification':'complete record-predicate diagnostic only; no acceptance','raw_root':str(ROOT),
        'function_bytes_sha256':FUNCTION_BYTES_SHA,'expected_sha256':EXPECTED_BYTES_SHA,'reader_sha256':YAML_SHA,
        'cases':rows,'root_post_metadata_complete':root_post_complete,'root_post_exception':root_post_exception,'raw_pre_post_equal':True,'raw_manifest_files':len(final['files']),'raw_manifest_bytes':final['bytes'],'all_five_record_checks_complete':all(r['all_record_predicates_reached'] for r in rows),'predicate_count':PREDICATE_COUNT,
        'predicate_sequence_sha256':PREDICATE_HASH.hexdigest(),'predicate_groups':list(GROUPS.values()),'failed_predicate_count':failed,'failure_samples':FAILURES,'failure_sample_limit':64,
        'equality_checks':EQUALITY_COUNT,'equality_sequence_sha256':EQUALITY_HASH.hexdigest(),'type_conflation_count':TYPE_CONFUSION_COUNT,'type_conflation_samples':TYPE_CONFUSIONS,
        'unclassified_equality_count':UNCLASSIFIED_EQUALITY_COUNT,'all_physical_input_final_checks_equal':True,'physical_inputs':pins,
        'seconds':time.monotonic()-started,'original_integer_budget_predicate_preserved':True,'scientific_or_source_or_caller_admission':False,
        'full_runtime_and_project_source_rehash_performed':False,'complete_original_raw_census_rehash_performed':True,'compiler_native_solver_project_or_full_observer_executed':False,'raw_C_AST_SMT_or_scalar_payload_transferred':False}
    text=json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False);hard(len(text.encode())+1<=4194304,'bounded diagnostic complete publication');print(text)

if __name__=='__main__':main()
'''
script=(header+body).encode();ast.parse(script)
path=OUT/'record-probe-v2.py';path.write_bytes(script)
def pin(p):r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
command=json.loads((HERE/'strict-yaml-repair-v1/semantic-probe-command-v1.json').read_bytes());command['stdin']=pin(path);command['kind']='INERT complete remaining record/job metadata diagnostic only; fresh review/root admission required';command['stdout_maximum_bytes']=4194304
(OUT/'command.json').write_text(json.dumps(command,indent=2,sort_keys=True)+'\n')
(OUT/'function-lineage.json').write_text(json.dumps({'date':'2026-10-16 ET','source':pin(HERE/'full-observer-v3/observer-v3.py'),'exact_extracted_names':sorted(WANTED),'diagnostic_only_semantic_functions':census,'hard_literal_reasons':sorted(HARD),'preserved_original_integer_budget_plan':True,'all_other_extracted_function_class_AST_exact':True,'function_bytes_sha256':hashlib.sha256(FUNCTION_BYTES).hexdigest()},indent=2,sort_keys=True)+'\n')
print(json.dumps({'probe':pin(path),'command':pin(OUT/'command.json'),'lineage':pin(OUT/'function-lineage.json')}))

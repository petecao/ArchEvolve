"""2026-10-16 ET. Author an inert complete15 semantic probe; never execute it."""
import ast
import base64
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
POC=HERE.parents[3]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
original=PARENT/'yaml-diagnostic-v3/diagnostic-v3.py'
source=original.read_text();tree=ast.parse(source)
helpers='\n\n'.join(ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','stable','read','audit'))
assert len([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','stable','read','audit')])==4
reader=(HERE/'record_yaml_subset_v3.py').read_bytes();expected=json.loads((HERE/'semantic-expected.json').read_bytes())
root_observation=POC/'evidence/t25-public-v4-root-observation-20261016t2130z.json'
expected['record_json_pins']=json.loads(root_observation.read_bytes())['actual']['closed-record-census.json']['physical_records']
expected['root_observation']=pin(root_observation)
expected_bytes=(json.dumps(expected,sort_keys=True,indent=2)+'\n').encode()
(HERE/'probe-expected.json').write_bytes(expected_bytes)
header='''"""2026-10-16 ET. INERT complete15 YAML semantic comparison, no scientific audit."""
import base64, copy, hashlib, json, os, re, resource, signal, stat, sys, time
from pathlib import Path
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-1433b8f5-t25-closed-source-public-v4')
PREFIX='test_public_closed_source_proo'
CASES=('safe','missing_bundle','stale_method','wrong_result','default_method')
LIMIT=8*1024*1024
'''
header+='READER_BYTES=base64.b64decode('+repr(base64.b64encode(reader).decode())+')\nREADER_SHA='+repr(sha(reader))+'\n'
header+='EXPECTED_BYTES=base64.b64decode('+repr(base64.b64encode(expected_bytes).decode())+')\nEXPECTED_SHA='+repr(sha(expected_bytes))+'\n'
body='''
def strict_json(raw):
    def pairs(rows):
        result={}
        for key,value in rows:need(key not in result,'duplicate JSON key');result[key]=value
        return result
    def bad(_):raise ValueError('nonfinite JSON value')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def expected_method(expected,case,runtime):
    result=copy.deepcopy(expected['method_template'])
    translator=runtime['lowering_identity']['c_lowering']
    need(isinstance(translator,dict) and set(translator)=={'id','sha256'} and isinstance(translator['id'],str)
         and re.fullmatch('[0-9a-f]{64}',translator['sha256']),'current lowering identity shape')
    result['c_lowering']['translators'][0]=translator
    if case=='stale_method':result['c_lowering']['translators'][-1]['sha256']='0'*64
    elif case=='default_method':
        result['id']='method.wp-vector-closed-default-v1'
        result['c_lowering']['translators']=result['c_lowering']['translators'][:1]
    return result

def counts(value):
    result={'objects':0,'arrays':0,'strings':0,'integers':0,'reals':0,'booleans':0,'nulls':0}
    def visit(item):
        if isinstance(item,dict):
            result['objects']+=1
            for key,child in item.items():need(isinstance(key,str),'JSON-shaped mapping key');visit(child)
        elif isinstance(item,list):
            result['arrays']+=1
            for child in item:visit(child)
        elif item is None:result['nulls']+=1
        elif type(item) is bool:result['booleans']+=1
        elif type(item) is int:result['integers']+=1
        elif type(item) is float:result['reals']+=1
        elif isinstance(item,str):result['strings']+=1
        else:raise ValueError('non JSON-shaped YAML value')
    visit(value);return result

def compare(data,wanted,reader):
    try:
        value=reader['loads'](data)
        return {'parsed':True,'complete_semantic_equality':digest(value)==digest(wanted),
            'actual_semantic_sha256':digest(value),'expected_semantic_sha256':digest(wanted),
            'counts':counts(value)},value
    except (ValueError,TypeError,IndexError,UnicodeError,RecursionError) as error:
        line=None;tb=error.__traceback__
        while tb:
            instance=tb.tb_frame.f_locals.get('self')
            if isinstance(instance,reader['Reader']):line=instance.at
            tb=tb.tb_next
        return {'parsed':False,'complete_semantic_equality':False,'exception':type(error).__name__,
            'candidate_line':line,'reason':'strict parser or JSON-shape refusal; no scalar content returned'},None

def main():
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('probe alarm')));signal.alarm(45)
    sys.addaudithook(audit)
    need(__debug__ and sys.flags.isolated and sys.dont_write_bytecode,'isolated no-bytecode probe required')
    need(hashlib.sha256(READER_BYTES).hexdigest()==READER_SHA and hashlib.sha256(EXPECTED_BYTES).hexdigest()==EXPECTED_SHA,'frozen probe inputs differ')
    reader={'__name__':'independent_strict_yaml'};exec(compile(READER_BYTES,'frozen-strict-yaml','exec'),reader)
    expected=strict_json(EXPECTED_BYTES);observed=[];rows=[];started=time.monotonic()
    runtime_path=ROOT/'closed-project-runtime.json';runtime_raw,runtime_pin=read(runtime_path);observed.append((runtime_path,runtime_pin));runtime=strict_json(runtime_raw)
    for i,case in enumerate(CASES):
        base=ROOT/'closed-source-profile/pytest'/(PREFIX+str(i))
        record_path=base/'retained-public-record.json';record_raw,record_pin=read(record_path);observed.append((record_path,record_pin))
        selected=expected['record_json_pins'][i]
        need(record_pin['relative']==selected['path'] and record_pin['sha256']==selected['sha256'],'root-observed retained JSON identity changed')
        record=strict_json(record_raw);identifier=record['id']
        need(isinstance(identifier,str) and re.fullmatch(r'proof\\.[A-Za-z0-9_.-]+',identifier),'safe exact proof filename required')
        method_name='wp-vector-closed-default-v1' if case=='default_method' else 'wp-vector-closed-source-v1'
        expected_method_value=expected_method(expected,case,runtime)
        work=(('proof',base/'records/proofs'/(identifier+'.yaml'),record),
              ('method',base/'library/methods'/(method_name+'.yaml'),expected_method_value),
              ('contract',base/'library/rewrite_contracts/fixture_vector_closed_no_growth.yaml',expected['contracts'][case]))
        for phase,path,wanted in work:
            raw,pin=read(path);observed.append((path,pin));result,value=compare(raw,wanted,reader)
            if phase=='method':
                result['retained_record_content_pin_equal']=(record['pins']['method_version']=={'id':expected_method_value['id'],'sha256':pin['sha256']})
            elif phase=='contract':
                result['retained_record_content_pin_equal']=(record['pins']['contract']=={'id':wanted['id'],'sha256':digest(wanted)} and record['pins']['code']==record['pins']['contract'])
            rows.append({'case':case,'phase':phase,'input':pin,'comparison':result})
    for path,pin in observed:
        _,after=read(path);need(after==pin,'probe final input identity changed')
    need(len(observed)==21 and len(rows)==15,'complete five-case comparison census')
    complete=all(r['comparison']['parsed'] and r['comparison']['complete_semantic_equality'] and r['comparison'].get('retained_record_content_pin_equal',True) for r in rows)
    result={'date':'2026-10-16 ET','kind':'complete15 strict YAML semantic comparison only','raw_root':str(ROOT),
        'reader_sha256':READER_SHA,'expected_sha256':EXPECTED_SHA,'inputs':len(observed),'yaml_files':len(rows),
        'root_runtime_input':runtime_pin,'record_json_inputs':[pin for path,pin in observed if path.name=='retained-public-record.json'],
        'rows':rows,'all15_complete_semantic_equal':complete,'all21_input_content_and_nine_stat_rechecks_equal':True,
        'seconds':time.monotonic()-started,'scalar_values_or_raw_payload_transferred':False,
        'compiler_native_solver_project_or_full_observer_executed':False,'scientific_source_or_caller_admission':False}
    output=json.dumps(result,sort_keys=True);need(len(output.encode())<32768,'probe output budget');print(output)

if __name__=='__main__':main()
'''
script=(header+'\n'+helpers+'\n'+body).encode();ast.parse(script)
(HERE/'semantic-probe-v1.py').write_bytes(script)
command=json.loads((PARENT/'yaml-diagnostic-v3/command.json').read_bytes());command['stdin']=pin(HERE/'semantic-probe-v1.py');command['kind']='INERT complete15 semantic comparison only; new root once-only admission required'
(HERE/'semantic-probe-command-v1.json').write_text(json.dumps(command,sort_keys=True,indent=2)+'\n')
print(json.dumps({'probe':pin(HERE/'semantic-probe-v1.py'),'command':pin(HERE/'semantic-probe-command-v1.json'),'expected':pin(HERE/'probe-expected.json'),'reader':pin(HERE/'record_yaml_subset_v3.py')}))

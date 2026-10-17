"""2026-10-16 ET. Mechanical V6→V7 preparation, no entry/main/tool execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys


def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('mechanical capture preparation refuses '+event)


sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
OLD=WHOLE/'compiler-capture-v6'
POC=WHOLE.parent.parent
OLD_RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v6'
NEW_RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v7'
BINDER='217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'
PASSIVE={'source_dispatch_v3.py':'d05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703',
         'source_argument_staging_v2.py':'79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178'}
ENTRY_EDITS=[
    {'old':'RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v6"',
     'new':'RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v7"'}]


def pin(path,expected=None):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    value={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    assert expected is None or value['sha256']==expected,(path,value['sha256'])
    return value


def write(name,value):
    (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def transform(value):
    if isinstance(value,str):
        for before,after in ((OLD_RAW,NEW_RAW),(str(OLD),str(HERE)),
            ('linux_compiler_capture_v6.py','linux_compiler_capture_v7.py'),
            ('linux_compiler_capture_policy_v6.json','linux_compiler_capture_policy_v7.json'),
            ('whole_interface_v4.py','whole_interface_v4.py')):
            value=value.replace(before,after)
        return value
    if isinstance(value,list):return [transform(item) for item in value]
    if isinstance(value,dict):return {transform(key):transform(item) for key,item in value.items()}
    return value


def json_edits(before,after,path=()):
    if before==after:return []
    if isinstance(before,dict) and isinstance(after,dict) and set(before)==set(after):
        return [edit for key in sorted(before) for edit in json_edits(before[key],after[key],path+(key,))]
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return [edit for index in range(len(before)) for edit in json_edits(before[index],after[index],path+(index,))]
    return [{'path':list(path),'old':before,'new':after}]


def main():
    previous=pin(OLD/'compiler-capture-source-packet-v6.json','c473101fcd5880aea35b8751e780cf475407cbae062dd62e54040f4a8804de33')
    old_packet=json.loads(Path(previous['path']).read_bytes())
    for row in old_packet['controller_inputs']:
        assert pin(row['path'])==row
    old_entry=pin(OLD/'linux_compiler_capture_v6.py','3818dc8c776194b2cbdb1a5d1d13e4857f6059e2396270aad96c08fb9e3bb426')
    text=Path(old_entry['path']).read_bytes().decode()
    for edit in ENTRY_EDITS:
        assert text.count(edit['old'])==1
        text=text.replace(edit['old'],edit['new'],1)
    (HERE/'linux_compiler_capture_v7.py').write_text(text)
    entry=pin(HERE/'linux_compiler_capture_v7.py')
    inverse=text
    for edit in reversed(ENTRY_EDITS):
        assert inverse.count(edit['new'])==1
        inverse=inverse.replace(edit['new'],edit['old'],1)
    assert inverse.encode()==Path(old_entry['path']).read_bytes()
    assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(Path(old_entry['path']).read_bytes()),include_attributes=False)
    pin(WHOLE/'whole_interface_v4.py',BINDER)
    for name,sha in PASSIVE.items():pin(WHOLE/name,sha)
    old_policy_path=OLD/'linux_compiler_capture_policy_v6.json'
    old_policy=json.loads(old_policy_path.read_bytes());policy=transform(old_policy)
    policy['schema']='t28-whole-source-compiler-capture-7'
    policy['node']=1
    policy['raw_name']=Path(NEW_RAW).name
    policy['entry_sha256']=entry['sha256']
    old_command=json.loads((OLD/'linux_compiler_capture_command_v6.json').read_bytes())
    staged=[]
    for row in old_command['controller_inputs']:
        if Path(row['path']).name==old_policy_path.name:continue
        new_pin=pin(transform(row['path']))
        staged.append(new_pin)
        policy['controller_files'][Path(new_pin['path']).name]={key:new_pin[key] for key in ('bytes','sha256')}
    assert len(staged)==len(old_policy['controller_files'])==len(policy['controller_files'])
    assert set(policy['controller_files'])==(set(old_policy['controller_files'])-{'linux_compiler_capture_v6.py'})|{'linux_compiler_capture_v7.py'}
    assert not set(PASSIVE)&set(policy['controller_files'])
    for key in old_policy:
        if key not in {'schema','raw_name','entry_sha256','controller_files','capture_recipe','node'}:assert policy[key]==old_policy[key]
    assert policy['capture_recipe']==transform(old_policy['capture_recipe'])
    assert policy['budgets']=={'whole_seconds':180,'entry_seconds':165,'rss_bytes':4294967296,'stage_bytes':134217728,'total_bytes':268435456}
    write('linux_compiler_capture_policy_v7.json',policy)
    policy_pin=pin(HERE/'linux_compiler_capture_policy_v7.json')
    staged.append(policy_pin)
    command=transform(old_command);command['node']=1;command['controller_inputs']=staged;command['argv'][-1]=policy_pin['sha256']
    assert command['root_guard']==old_command['root_guard']
    assert command['root_reviewed_wrapper_hashes']==old_command['root_reviewed_wrapper_hashes']
    assert command['recipe']==policy['capture_recipe']
    write('linux_compiler_capture_command_v7.json',command)
    command_pin=pin(HERE/'linux_compiler_capture_command_v7.json')
    inverse={'date':'2026-10-16 ET','status':'SOURCE ONLY: exact lane/namespace rebind; all other finalization/runtime/source logic preserved',
        'predecessor':old_entry,'successor':entry,'edits':ENTRY_EDITS,'textual_inverse_exact':True,'AST_inverse_exact':True,
        'policy':{'predecessor':pin(old_policy_path),'successor':policy_pin,'json_edits':json_edits(old_policy,policy)},
        'command':{'predecessor':pin(OLD/'linux_compiler_capture_command_v6.json'),'successor':command_pin,'json_edits':json_edits(old_command,command)},
        'recipe_adapter_unchanged':pin(WHOLE/'compiler_unit_adapter_v2.py','1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317'),
        'passive_not_staged_or_imported':[pin(WHOLE/name,sha) for name,sha in PASSIVE.items()],
        'scientific_execution':False,'actual_capture_admitted':False,'public_admission':False}
    for key in ('policy','command'):
        value=copy.deepcopy(policy if key=='policy' else command)
        for edit in reversed(inverse[key]['json_edits']):
            cursor=value
            for part in edit['path'][:-1]:cursor=cursor[part]
            assert cursor[edit['path'][-1]]==edit['new']
            cursor[edit['path'][-1]]=edit['old']
        assert value==(old_policy if key=='policy' else old_command)
    write('compiler-capture-v7-inverse.json',inverse)
    review=pin(POC/'evidence/resume-20261016-lane-coordination/t28-unrelated-macro-call-v1-independent-static-review-20261016.json')
    assert review['sha256'].startswith('2b9ab436')
    controls_log=HERE/'pure-capture-v7-controls.log'
    validation={'pure_tests':16,'actual_main_or_child_invoked':False,'executed':False}
    if controls_log.exists():
        lines=controls_log.read_text().splitlines();report=json.loads(lines[-1])
        assert report['tests']==16 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
        assert report['controller_sha256']==entry['sha256'] and report['policy_sha256']==policy_pin['sha256'] and report['command_sha256']==command_pin['sha256']
        assert report['controls_sha256']==pin(HERE/'test_capture_v7.py')['sha256']
        validation.update(executed=True,failures=0,errors=0,skips=0,log=pin(controls_log))
    packet={'date':'2026-10-16 ET','status':'SOURCE PREPARATION ONLY; V7 actual capture not admitted',
        'controller_inputs':staged,'command':command_pin,'preparation':pin(Path(__file__)),'pure_controls':pin(HERE/'test_capture_v7.py'),
        'readme':pin(HERE/'README.md'),'validation':validation,'predecessor_packet':previous,
        'source_basis':old_packet['source_basis'],
        'consumed_binder':pin(WHOLE/'whole_interface_v4.py',BINDER),
        'reviewed_passive_consumers':[pin(WHOLE/name,sha) for name,sha in PASSIVE.items()],
        'reviewed_macro_repair':review,
        'preserved_V6_review':pin(POC/'evidence/resume-20261016-lane-coordination/t28-compiler-capture-v6-independent-static-review-20261016.json'),
        'inherited_policy':old_packet['inherited_policy'],'controls_bytes':sum(row['bytes'] for row in staged),
        'original_recipe_unchanged_except_raw_namespace':True,'lane_rebind':{'predecessor':0,'successor':1},'runtime_role_resource_finalization_logic_unchanged':True,
        'derived_stub':old_packet['derived_stub'],'inverse':pin(HERE/'compiler-capture-v7-inverse.json'),
        'finalization_reserve_bytes':1048576,'final_entry_deadline_seconds':165,
        'scientific_execution':False,'source_call_admission':False,'public_admission':False,'current_0_2':False,'full_ticket28':False}
    if (HERE/'pure-capture-v7-controls-red.log').exists():packet['retained_controls_red']=pin(HERE/'pure-capture-v7-controls-red.log')
    assert packet['controls_bytes']<1048576
    write('compiler-capture-source-packet-v7.json',packet)
    print(json.dumps(pin(HERE/'compiler-capture-source-packet-v7.json'),sort_keys=True))


if __name__=='__main__':main()

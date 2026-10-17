"""2026-10-16 ET. Source-only narrow minifier write bound successor."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('inert assembly refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-capture-v9';INGRESS=WHOLE/'streaming-minify-v1'
PREP={'__name__':'inert_predecessor','__file__':str(OLD/'prepare_capture_v9.py')};exec(compile((OLD/'prepare_capture_v9.py').read_bytes(),'inert_predecessor','exec'),PREP)
pin=PREP['pin'];changes=PREP['changes']
def write(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def main():
    old_mini=pin(INGRESS/'strict_minify_v1.py');text=Path(old_mini['path']).read_text()
    before='''        self.output_bytes+=len(value);self.output_hash.update(value);self.output.extend(value)
        if len(self.output)>=CHUNK:self.flush()'''
    after='''        self.output_bytes+=len(value);self.output_hash.update(value)
        # Never combine a maximum string token with the existing buffer into a
        # write larger than the final metadata reserve. Every write <=64 KiB.
        at=0
        while at<len(value):
            amount=min(CHUNK-len(self.output),len(value)-at)
            self.output.extend(value[at:at+amount]);at+=amount
            if len(self.output)==CHUNK:self.flush()'''
    assert text.count(before)==1;text=text.replace(before,after,1);(INGRESS/'strict_minify_v2.py').write_text(text);mini=pin(INGRESS/'strict_minify_v2.py')
    assert text.replace(after,before,1)==Path(old_mini['path']).read_text()
    old_entry=pin(OLD/'linux_compiler_capture_v9.py','a25a623e4e10376919c2d51ea800466d69262b6e354b7ba23ffae113e04694d9')
    old_text=Path(old_entry['path']).read_text();entry_text=old_text;edits=[]
    for before_e,after_e in [('RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v9"','RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v10"'),
        ('MINIFIER_SHA = "'+old_mini['sha256']+'"','MINIFIER_SHA = "'+mini['sha256']+'"'),
        ('module("strict_minify_v1.py", MINIFIER_SHA)','module("strict_minify_v2.py", MINIFIER_SHA)')]:
        assert entry_text.count(before_e)==1;entry_text=entry_text.replace(before_e,after_e,1);edits.append({'old':before_e,'new':after_e})
    (HERE/'linux_compiler_capture_v10.py').write_text(entry_text);entry=pin(HERE/'linux_compiler_capture_v10.py')
    restored=entry_text
    for edit in reversed(edits):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'],1)
    assert restored==old_text and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old_text))
    def transform(value):
        if isinstance(value,str):
            for old,new in ((str(OLD),str(HERE)),('full-tu-2baf722f-v9','full-tu-2baf722f-v10'),('linux_compiler_capture_v9.py','linux_compiler_capture_v10.py'),
                ('linux_compiler_capture_policy_v9.json','linux_compiler_capture_policy_v10.json'),('strict_minify_v1.py','strict_minify_v2.py')):value=value.replace(old,new)
            return value
        if isinstance(value,list):return [transform(v) for v in value]
        if isinstance(value,dict):return {transform(k):transform(v) for k,v in value.items()}
        return value
    old_policy=json.loads((OLD/'linux_compiler_capture_policy_v9.json').read_bytes());policy=transform(old_policy)
    policy['schema']='t28-whole-source-compiler-capture-10';policy['entry_sha256']=entry['sha256']
    old_command=json.loads((OLD/'linux_compiler_capture_command_v9.json').read_bytes());command=transform(old_command)
    staged=[pin(transform(row['path'])) for row in old_command['controller_inputs'] if Path(row['path']).name!='linux_compiler_capture_policy_v9.json']
    policy['controller_files']={Path(r['path']).name:{k:r[k] for k in ('bytes','sha256')} for r in staged}
    write('linux_compiler_capture_policy_v10.json',policy);policy_pin=pin(HERE/'linux_compiler_capture_policy_v10.json');staged.append(policy_pin)
    command['controller_inputs']=staged;command['argv'][-1]=policy_pin['sha256'];write('linux_compiler_capture_command_v10.json',command);command_pin=pin(HERE/'linux_compiler_capture_command_v10.json')
    for key in old_policy:
        if key not in {'schema','raw_name','entry_sha256','controller_files','capture_recipe'}:assert policy[key]==old_policy[key]
    assert command['root_guard']==old_command['root_guard']
    write('compiler-capture-v10-inverse.json',{'date':'2026-10-16 ET','predecessor':old_entry,'successor':entry,'entry_edits':edits,
        'minifier_predecessor':old_mini,'minifier_successor':mini,'minifier_edits':[{'old':before,'new':after}],
        'policy_edits':changes(old_policy,policy),'command_edits':changes(old_command,command),
        'old_policy':pin(OLD/'linux_compiler_capture_policy_v9.json'),'old_command':pin(OLD/'linux_compiler_capture_command_v9.json'),
        'entry_and_minifier_text_AST_inverse_exact':True,'policy':policy_pin,'command':command_pin,'max_minifier_write_bytes':65536,
        'semantic_and_resource_profile_unchanged':True,'actual_admission':False})
    log=HERE/'pure-capture-v10-controls.log';validation={'executed':False}
    if log.exists():
        report=json.loads(log.read_text().splitlines()[-1]);assert report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
        assert report['entry_sha256']==entry['sha256'] and report['minifier_sha256']==mini['sha256'] and report['controls_sha256']==pin(HERE/'test_capture_v10.py')['sha256']
        validation={'executed':True,'report':report,'log':pin(log)}
    packet={'date':'2026-10-16 ET','status':'SOURCE ONLY: bounded writes repair, predecessor preserved; no actual capture',
        'controller_inputs':staged,'command':command_pin,'inverse':pin(HERE/'compiler-capture-v10-inverse.json'),'preparation':pin(Path(__file__)),
        'controls':pin(HERE/'test_capture_v10.py'),'validation':validation,'predecessor_packet':pin(OLD/'compiler-capture-source-packet-v9.json','81d32b208c2b18c42dda5123ba2bbb7910a00af40d98fad5e4414b4e7694bc97'),
        'design':pin(INGRESS/'design.md'),'controls_bytes':sum(row['bytes'] for row in staged),'max_minifier_write_bytes':65536,
        'expanded_original_bytes':2147483648,'caller_ast_phase_seconds':120,'other_phase_seconds':45,
        'retained_per_file_bytes':134217728,'retained_total_bytes':268435456,'finalization_reserve_bytes':1048576,'guard_seconds':180,'entry_seconds':165,'rss_bytes':4294967296,
        'complete_original_TU_tokens_preserved':True,'raw_full_DOM_materialized':False,'all_other_source_runtime_resource_criteria_unchanged':True,
        'actual_capture':False,'public_proof':False,'current_0_2':False,'full_ticket28':False}
    assert packet['controls_bytes']<1048576 and not EVENTS;write('compiler-capture-source-packet-v10.json',packet)
    print(json.dumps(pin(HERE/'compiler-capture-source-packet-v10.json'),sort_keys=True))
if __name__=='__main__':main()

"""Root-delegated once-only V3 read-only census transport; no compiler job.

The remote census command and stdin are the exact reviewed frozen bytes. Local
SSH/timeout/env transport is root-owned TCB. Original V10 artifacts stay read-only.
"""
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import subprocess
import time
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;POC=WHOLE.parents[1];V3=WHOLE/'compiler-duplicate-census-v3';FIRST=WHOLE/'compiler-duplicate-diagnostic-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value,exclusive=False):
    with (HERE/name).open('x' if exclusive else 'w') as handle:handle.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
def bounded(remote,stdin,seconds):
    started=time.monotonic();command=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10',remote]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc.stdin.write(stdin);proc.stdin.close();selector=selectors.DefaultSelector()
    for name,pipe in [('stdout',proc.stdout),('stderr',proc.stderr)]:selector.register(pipe,selectors.EVENT_READ,name)
    values={'stdout':bytearray(),'stderr':bytearray()};refusal=None
    try:
        while selector.get_map():
            if time.monotonic()-started>=seconds:refusal='local transport timeout';proc.kill();break
            for key,_ in selector.select(0.5):
                name=key.data;remaining=32768-len(values[name]);chunk=os.read(key.fileobj.fileno(),min(65536,remaining+1))
                if not chunk:selector.unregister(key.fileobj);continue
                if len(chunk)>remaining:refusal='bounded '+name+' overflow';proc.kill();break
                values[name].extend(chunk)
            if refusal:break
        proc.wait(timeout=10)
    finally:
        selector.close()
        for pipe in (proc.stdout,proc.stderr):pipe.close()
    return {'returncode':proc.returncode,'local_wall_seconds':time.monotonic()-started,'local_refusal':refusal,
        'local_ssh_argv_prefix':command[:-1]},bytes(values['stdout']),bytes(values['stderr'])
command_path=V3/'complete-census-command-v3.json';assert pin(command_path)['sha256']=='8835f7ae59c6ba5f9c93e2c5cbbc856d76625d7a8f0733a8528817293479beb3'
command=json.loads(command_path.read_bytes());payload_path=V3/'complete_duplicate_census_v3.py';payload=payload_path.read_bytes()
assert pin(payload_path)==command['stdin'] and pin(V3/'readonly_bootstrap_v4.py')==command['bootstrap']
admission=POC/'evidence/t28-complete-census-v3-root-admission-20261016.json';assert pin(admission)['sha256']=='cf2b711d3584433379153b35cbec5c1728f881e4d90555bb0e64ccc4bd9013f3'
preflight=(FIRST/'preflight_source_v1.py').read_text();assert hashlib.sha256(preflight.encode()).hexdigest()=='fae00ab5f1a71d51093d94f6b014414aa59e35d92b2c5943a4031d47255c54f4'
line=next(line for line in preflight.splitlines() if line.startswith('print(json.dumps('));assert preflight.count(line)==1
preflight=preflight.replace(line,line.replace('print(json.dumps(','observation=').removesuffix(',sort_keys=True))'),1)
preflight+='''\npolicy=json.loads((raw/'control/linux_compiler_capture_policy_v10.json').read_bytes())
extra={}
for row in policy['source_inputs']:
 path=Path(policy['source_project'])/row['relative'];actual=pin(path)
 need(actual=={k:row[k] for k in ('bytes','sha256')},'current selected source/header input differs')
 extra[str(path)]=actual
for name,row in policy['controller_files'].items():
 path=raw/'control'/name;actual=pin(path);need(actual==row,'current control/input differs');extra[str(path)]=actual
runtime=[policy['zlib_binding']['physical_interpreter'],*policy['zlib_binding']['mapped_compression_objects']]
for row in runtime:
 path=Path(row['path']);actual=pin(path);need(actual=={k:row[k] for k in ('bytes','sha256')},'selected passive decoder runtime differs');extra[str(path)]=actual
observation['current_physical_source_control_decoder_pins']=extra
observation['runtime_scope']='exact physical selected interpreter and mapped compression object; full bind_zlib startup is also required by census'
print(json.dumps(observation,sort_keys=True))
'''
(HERE/'preflight_source_v3.py').write_text(preflight)
argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','25s','/usr/bin/env','-i',*[k+'='+v for k,v in command['closed_environment'].items()],command['python_argv'][0],'-I','-B','-c',preflight]
def flight(name):
    result,stdout,stderr=bounded(shlex.join(argv),b'',35)
    (HERE/(name+'-stdout.json')).write_bytes(stdout);(HERE/(name+'-stderr.log')).write_bytes(stderr)
    result.update(stdout=pin(HERE/(name+'-stdout.json')),stderr=pin(HERE/(name+'-stderr.log')),preflight_source=pin(HERE/'preflight_source_v3.py'))
    save(name+'.json',result)
    assert result['returncode']==0 and result['local_refusal'] is None and stderr==b'',result
    return json.loads(stdout)
before=flight('actual-preflight-v3')
save('actual-census-launch-v3.json',{'date':'2026-10-16 ET','admission':pin(admission),'command':pin(command_path),'stdin':pin(payload_path),
    'local_driver':pin(Path(__file__)),'preflight_source':pin(HERE/'preflight_source_v3.py'),
    'started_unix_seconds':time.time(),'original_raw':command['python_argv'][-1],'once_only':True,'normalized_writes_or_compiler':False},exclusive=True)
print('Fresh preflight passed; exact reviewed complete census V3 dispatched once.',flush=True)
result,stdout,stderr=bounded(command['remote_shell_command'],payload,command['local_transport_timeout_seconds'])
(HERE/'actual-census-stdout-v3.json').write_bytes(stdout);(HERE/'actual-census-stderr-v3.log').write_bytes(stderr)
result.update(stdout=pin(HERE/'actual-census-stdout-v3.json'),stderr=pin(HERE/'actual-census-stderr-v3.log'),stdin=pin(payload_path),command=pin(command_path),
    original_V10_status_rewritten=False,normalized_AST_written=False,scientific_execution=False)
save('actual-census-result-v3.json',result)
print(json.dumps(result),flush=True)
after=flight('actual-postflight-v3')
assert before['pins']==after['pins'] and before['current_physical_source_control_decoder_pins']==after['current_physical_source_control_decoder_pins'] and before['original_metadata']==after['original_metadata']
save('actual-census-immutability-v3.json',{'before':pin(HERE/'actual-preflight-v3.json'),'after':pin(HERE/'actual-postflight-v3.json'),
    'all_selected_physical_pins_equal':True,'original_G639_metadata_equal':True,'original_V10_duplicate_refusal_preserved':True,
    'all_host_empty_required':False,'current_source_Git_command_executed':False,'original_source_after_receipt_rehashed':True,
    'actual_capture_or_source_call_ABI_or_proof_admission':False})
print('Postflight selected pins and original G639 metadata are unchanged.',flush=True)

"""2026-10-16 ET: root-delegated once-only passive V2 transform transport.

SSH, timeout/env, and inherited current SSH/OS/PAM service ancestry are the
explicit root transport TCB. This does not execute a compiler or proof engine.
"""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
POC=WHOLE.parents[1]
V2=WHOLE/'role-normalization-controller-v2'

def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(name,value):
    with (HERE/name).open('x') as handle:
        handle.write(json.dumps(value,sort_keys=True,indent=2)+'\n')

def bounded(remote,stdin,seconds):
    started=time.monotonic()
    argv=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10',remote]
    proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc.stdin.write(stdin)
    proc.stdin.close()
    selector=selectors.DefaultSelector()
    for name,pipe in [('stdout',proc.stdout),('stderr',proc.stderr)]:
        selector.register(pipe,selectors.EVENT_READ,name)
    values={'stdout':bytearray(),'stderr':bytearray()}
    refusal=None
    try:
        while selector.get_map():
            if time.monotonic()-started>=seconds:
                refusal='local transport timeout';proc.kill();break
            for key,_ in selector.select(0.5):
                name=key.data
                remaining=32768-len(values[name])
                chunk=os.read(key.fileobj.fileno(),min(65536,remaining+1))
                if not chunk:
                    selector.unregister(key.fileobj);continue
                if len(chunk)>remaining:
                    refusal='bounded '+name+' overflow';proc.kill();break
                values[name].extend(chunk)
            if refusal:break
        proc.wait(timeout=10)
    finally:
        selector.close()
        for pipe in (proc.stdout,proc.stderr):pipe.close()
    return {'returncode':proc.returncode,'local_wall_seconds':time.monotonic()-started,
        'local_refusal':refusal,'local_ssh_argv_prefix':argv[:-1]},bytes(values['stdout']),bytes(values['stderr'])

command_path=V2/'command_v2.json'
assert pin(command_path)['sha256']=='d8b6d6815412273c40c00c3cd456c4635d355d25d96c42099869b77616e00c03'
command=json.loads(command_path.read_bytes())
payload_path=V2/'normalization_controller_v2.py'
assert pin(payload_path)==command['stdin']
assert pin(V2/'bootstrap_v2.py')==command['bootstrap']
assert pin(V2/'source_policy_v2.json')==command['source_policy']
packet_path=V2/'source-packet-v2.json'
assert pin(packet_path)['sha256']=='826d1df8c33ccf50be4bc9b0232937851f1f201d4bbd95573cd5ae35c7babfce'
admission=POC/'evidence/t28-role-normalization-controller-v2-root-admission-20261016.json'
assert pin(admission)['sha256']=='d98178902c209b05408590b3c976e34f4e2115a25fb839037f9bb44396a6de6b'
assert command['remote_shell_command']==shlex.join(command['remote_argv'])
assert command['python_argv'][4]==(V2/'bootstrap_v2.py').read_text()
payload=payload_path.read_bytes()
policy=json.loads((V2/'source_policy_v2.json').read_bytes())
template=(HERE/'preflight_template.py').read_text()
assert template.count('__POLICY__')==1 and template.count('__POST__')==1
encoded=base64.b64encode((V2/'source_policy_v2.json').read_bytes()).decode()
sources={}
for post,name in [(False,'preflight_source_v2.py'),(True,'postflight_source_v2.py')]:
    source=template.replace('__POLICY__',encoded).replace('__POST__',str(post))
    ast.parse(source)
    with (HERE/name).open('x') as handle:handle.write(source)
    sources[post]=(source,HERE/name)

def flight(post,name):
    source,path=sources[post]
    argv=['/usr/bin/timeout','--signal=TERM','--kill-after=3s','25s','/usr/bin/env','-i',
        *[key+'='+value for key,value in command['closed_environment'].items()],
        command['python_argv'][0],'-I','-B','-c',source]
    result,stdout,stderr=bounded(shlex.join(argv),b'',35)
    for suffix,data in [('stdout.json',stdout),('stderr.log',stderr)]:
        with (HERE/(name+'-'+suffix)).open('xb') as handle:handle.write(data)
    result.update(stdout=pin(HERE/(name+'-stdout.json')),stderr=pin(HERE/(name+'-stderr.log')),source=pin(path))
    save(name+'.json',result)
    assert result['returncode']==0 and result['local_refusal'] is None and stderr==b'',result
    return json.loads(stdout)

before=flight(False,'actual-preflight-v2')
save('actual-transform-launch-v2.json',{'date':'2026-10-16 ET','admission':pin(admission),'source_packet':pin(packet_path),
    'command':pin(command_path),'stdin':pin(payload_path),'bootstrap':command['bootstrap'],'driver':pin(Path(__file__)),
    'preflight':pin(HERE/'actual-preflight-v2.json'),'started_unix_seconds':time.time(),
    'output_root':policy['output_root'],'once_only':True,'compiler_native_solver_or_proof':False})
print('Fresh preflight passed; exact reviewed passive role transform V2 dispatched once.',flush=True)
result,stdout,stderr=bounded(command['remote_shell_command'],payload,command['limits']['local_seconds'])
for name,data in [('actual-transform-stdout-v2.json',stdout),('actual-transform-stderr-v2.log',stderr)]:
    with (HERE/name).open('xb') as handle:handle.write(data)
result.update(stdout=pin(HERE/'actual-transform-stdout-v2.json'),stderr=pin(HERE/'actual-transform-stderr-v2.log'),
    stdin=pin(payload_path),command=pin(command_path),bootstrap=command['bootstrap'],original_V10_status_rewritten=False,
    source_call_ABI_public_or_full28_admission=False,scientific_execution=False)
save('actual-transform-result-v2.json',result)
print(json.dumps(result,sort_keys=True),flush=True)
assert result['returncode']==0 and result['local_refusal'] is None and stderr==b'',result
after=flight(True,'actual-postflight-v2')
assert before['pins']==after['pins'] and before['original_refusal']==after['original_refusal']
message=json.loads(stdout)
assert message['normalization_complete'] is True
assert message['result']==after['output_pins'][policy['output_root']+'/result.json'] | {'path':policy['output_root']+'/result.json'}
save('actual-transform-immutability-v2.json',{'date':'2026-10-16 ET','before':pin(HERE/'actual-preflight-v2.json'),
    'after':pin(HERE/'actual-postflight-v2.json'),'all_selected_physical_pins_equal':True,
    'original_V10_duplicate_refusal_preserved':True,'zero_exit_and_settled_output_reconciliation':True,
    'output_files':len(after['output_pins']),'aggregate_output_bytes':sum(row['bytes'] for row in after['output_pins'].values()),
    'all_host_empty_required':False,'source_call_ABI_public_or_full28_admission':False})
save('root-observed-execution-v2.json',{'schema':'passive-transform-root-execution-1','controller':pin(payload_path),
    'command':pin(command_path),'bootstrap':command['bootstrap'],'stdin_sha256':pin(payload_path)['sha256'],
    'output_root':policy['output_root'],'returncode':0,'local_refusal':None,'timed_out':False,'out_of_memory':False,
    'wall_seconds':result['local_wall_seconds'],'stdout':result['stdout'],'stderr':result['stderr']})
print('Postflight input identity and all settled output pins reconciled; original V10 refusal is unchanged.',flush=True)

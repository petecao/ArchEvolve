"""Author pinned controller/policy/bootstrap/command; no remote/main invocation."""
import base64
import hashlib
import json
from pathlib import Path
import shlex
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;POC=WHOLE.parents[1]
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def encode(raw):return base64.b64encode(raw).decode('ascii')
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
actual=WHOLE/'compiler-duplicate-census-v3-actual';before=json.loads((actual/'actual-preflight-v3-stdout.json').read_bytes())
normalizer=WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py';census=actual/'actual-census-stdout-v3.json'
assert pin(normalizer)['sha256']=='6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'
assert pin(census)['sha256']=='df800e08c89abd76ef0ea7e713af9fd52315ae873accc8ea54ab5a760fa8a41b'
raw_root=before['raw'];physical={raw_root+'/'+name:row for name,row in before['pins'].items()};physical.update(before['current_physical_source_control_decoder_pins'])
settled=json.loads((POC/'evidence/t28-capture-v10-root-settled-observation-20261016.json').read_bytes())
commands=settled['runs']['capture-v10']['metadata']['component/commands.json']
for row in commands:
    for key in ('stdout','stderr'):
        value=row[key];expected={k:value[k] for k in ('bytes','sha256')}
        assert value['path'] not in physical or physical[value['path']]==expected;physical[value['path']]=expected
policy={'schema':'passive-paired-type-normalization-policy-1','date':'2026-10-16 ET','original_raw':raw_root,
    'output_root':'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1',
    'normalizer':pin(normalizer),'census':pin(census),'physical_inputs':physical,'original_commands':commands,
    'limits':{'AS_bytes':536870912,'CPU_seconds':950,'work_seconds':885,'internal_seconds':900,'outer_seconds':960,'local_seconds':1000,
        'expanded_normalized_bytes':201326592,'physical_file_bytes':134217728,'aggregate_bytes':268435456,'reserve_bytes':1048576,'disk_floor_bytes':53687091200},
    'scope':'byte-transform certificate only; exact original compiler provenance/source/dependency/public consumer admission remains separate',
    'original_capture_status_preserved':True,'actual_normalized_writes_admitted':False,'compiler_or_proof_or_public_admission':False}
policy_raw=json.dumps(policy,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
(HERE/'source_policy_v1.json').write_bytes(policy_raw)
entry=(HERE/'controller_template.py').read_text()
for name,raw in [('POLICY',policy_raw),('NORMALIZER',normalizer.read_bytes()),('CENSUS',census.read_bytes())]:
    token='__'+name+'_B64__';assert entry.count(token)==1;entry=entry.replace(token,encode(raw),1)
(HERE/'normalization_controller_v1.py').write_text(entry);payload=pin(HERE/'normalization_controller_v1.py')
out=policy['output_root'];names=['control/controller.py','control/normalizer.py','control/census.json','control/policy.json',
    'component/inputs-before.json','component/inputs-after.json','component/caller.normalized.json.gz','component/rename-manifest.jsonl',
    'component/transport.json','component/inverse.json','result.json']
boot='''# Source-only selected Python bootstrap; no execution during authoring.
import resource
import sys
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(950,950))
OUTPUT_ROOT=__OUT__
OUTPUT_PATHS=__PATHS__
def bootstrap_audit(event,args):
    if event=='open':
        path,mode,flags=args
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(1|2|64|512|1024):
            if type(path) is not str or path not in OUTPUT_PATHS or not flags&64 or not flags&128:
                raise PermissionError('only exclusive fixed new-root output allowed')
    if event=='os.mkdir':
        if args[0] not in (OUTPUT_ROOT,OUTPUT_ROOT+'/control',OUTPUT_ROOT+'/component'):
            raise PermissionError('only fixed new-root directories allowed')
        return
    if event in {'os.system','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate',
        'os.utime','os.chdir','os.putenv','os.unsetenv','ctypes.dlopen','resource.setrlimit'} or event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')):
        raise PermissionError('passive transform mutation/child/network refused: '+event)
sys.addaudithook(bootstrap_audit)
import hashlib
payload=sys.stdin.buffer.read(__SIZE_PLUS_ONE__)
if len(payload)!=__SIZE__ or hashlib.sha256(payload).hexdigest()!=__SHA__:
    raise ValueError('exact reviewed transform stdin required')
if len(sys.argv)!=2 or sys.argv[1]!=OUTPUT_ROOT:
    raise ValueError('exact fresh output argument required')
exec(compile(payload,'<reviewed-passive-role-transform-stdin>','exec'),{'__name__':'__main__','SOURCE_BYTES':payload,'__builtins__':__builtins__})
'''
for old,new in [('__OUT__',repr(out)),('__PATHS__',repr(tuple(out+'/'+name for name in names))),('__SIZE_PLUS_ONE__',str(payload['bytes']+1)),('__SIZE__',str(payload['bytes'])),('__SHA__',repr(payload['sha256']))]:
    assert boot.count(old)==1;boot=boot.replace(old,new,1)
(HERE/'bootstrap_v1.py').write_text(boot)
prior=json.loads((WHOLE/'compiler-duplicate-census-v3/complete-census-command-v3.json').read_bytes());env=prior['closed_environment']
argv=[prior['python_argv'][0],'-I','-B','-c',boot,out]
remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','960s','/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],*argv]
save('command_v1.json',{'date':'2026-10-16 ET','scope':'INERT passive byte transform; independent review and root actual-write admission required',
    'stdin':payload,'bootstrap':pin(HERE/'bootstrap_v1.py'),'source_policy':pin(HERE/'source_policy_v1.json'),
    'python_argv':argv,'remote_argv':remote,'remote_shell_command':shlex.join(remote),'closed_environment':env,
    'selected_python_physical_pin':prior['selected_python_physical_pin'],'selected_libz_physical_pins':prior['selected_libz_physical_pins'],
    'limits':policy['limits'],'stdout_limit_bytes':32768,'stderr_limit_bytes':32768,'actual_executed':False,
    'prior_once_only_census_admission_reused':False,'root_transport_TCB':['SSH','/usr/bin/timeout','/usr/bin/env']})
print(json.dumps({'entry':payload,'policy':pin(HERE/'source_policy_v1.json'),'command':pin(HERE/'command_v1.json')}))

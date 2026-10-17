"""Reviewer control: actual27 staging payloads, root-only path rebinding.

Pure stdlib copy/metadata validators only. No observer, project, child or tools.
"""
from pathlib import Path
import ast,hashlib,json,os,stat,sys,tempfile,types
HERE=Path(__file__).resolve().parent

def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('reviewer layout control forbids child/native/network')
sys.addaudithook(audit)
source=HERE/'linux_observation_envelope_v2.py';tree=ast.parse(source.read_bytes())
namespace={'Path':Path,'ast':ast,'hashlib':hashlib,'json':json,'os':os,'stat':stat,'sys':sys,'types':types}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef))],type_ignores=[]),'<exact-frozen-envelope-layout-control>','exec'),namespace)
command=json.loads((HERE/'command-v2.json').read_bytes());original=json.loads((HERE/'envelope-policy-v2.json').read_bytes())
def rebased(value,old,new):
    if type(value) is dict:return {k:rebased(v,old,new) for k,v in value.items()}
    if type(value) is list:return [rebased(v,old,new) for v in value]
    if type(value) is str:return value.replace(old,new)
    return value
with tempfile.TemporaryDirectory(prefix='t28-observer-actual-layout-') as directory:
    raw=Path(directory).resolve()/original['raw_name'];(raw/'control').mkdir(parents=True)
    old=command['raw'];policy=rebased(original,old,str(raw))
    for name,row in command['stage_sources'].items():
        payload=Path(row['path']).read_bytes()
        assert (len(payload),hashlib.sha256(payload).hexdigest())==(row['bytes'],row['sha256'])
        (raw/'control'/name).write_bytes(payload)
    obs_path=raw/'control/observation-policy-v1.json';observer=rebased(json.loads(obs_path.read_bytes()),old,str(raw))
    obs_path.write_text(json.dumps(observer,sort_keys=True,separators=(',',':')))
    observed_pin=namespace['pin'](obs_path);policy['controls'][obs_path.name]=observed_pin
    policy['observer_policy']={**observed_pin,'path':str(raw/'observer/control'/obs_path.name)}
    runtime=Path(original['runtime_policy']['path']);runtime_local=Path(directory).resolve()/'exact-runtime-policy.json'
    basis=HERE.parent/'compiler-capture-v10/linux_compiler_capture_policy_v10.json';runtime_local.write_bytes(basis.read_bytes())
    policy['runtime_policy']=namespace['pin'](runtime_local)
    policy_path=raw/'control/envelope-policy-v2.json';policy_path.write_text(json.dumps(policy,sort_keys=True,separators=(',',':')))
    namespace['stage_layout'](raw,policy)
    values=namespace['input_check'](raw,policy,namespace['pin'](policy_path))
    assert set(values)==set(original['controls']) and len(values)==27
    assert len(list((raw/'observer/control').iterdir()))==14
    assert (raw/'library_fixture/proof_units/source.cpp').read_bytes()==(raw/'control/source_call_fixture_v2.cpp').read_bytes()
    (raw/'observer/control/extra').write_bytes(b'unknown')
    try:namespace['input_check'](raw,policy,namespace['pin'](policy_path))
    except ValueError:pass
    else:raise AssertionError('unknown copied control accepted')
print(json.dumps({'schema':'actual-staged-layout-review-control-1','pass':True,'fixed_actual_payloads':27,'copied_observer_controls_including_policy':14,'source_buffer_bytes':4524,'extra_member_refused':True,'path_rebinding':'Only selected RAW root and copied local runtime-policy location; scientific observer and capture are never invoked.','compiler_native_solver_child_SSH_or_project_import':False},sort_keys=True))

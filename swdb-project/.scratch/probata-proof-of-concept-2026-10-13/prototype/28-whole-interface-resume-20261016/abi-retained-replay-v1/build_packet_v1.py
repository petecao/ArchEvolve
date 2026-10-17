"""2026-10-16 ET. Source-only retained ABI replay packet author; no runtime/main."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1')
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10')
MEMORY=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1')
OBSERVER=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3')
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
    raw=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(raw),sha256=sha(raw))
def save(name,v):(HERE/name).write_bytes(canonical(v)+b'\n')

def build():
    old=WHOLE/'abi-role-diagnostic-v1/read_abi_census_v1.py';raw=old.read_text();tree=ast.parse(raw)
    assert sha(old.read_bytes())=='dda8d74a9fd02c6d193e99f4947aa830b11f5e1461ac13cb5fcfda6d6d909787'
    wanted=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WANTED_PAM' for t in n.targets))
    pam=ast.get_source_segment(raw,wanted)
    functions={n.name:ast.get_source_segment(raw,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'pam_identity','transport_identity','scan'}}
    old_transport=functions['transport_identity'];assert old_transport.count("'35s'")==1
    functions['transport_identity']=old_transport.replace("'35s'","'185s'")
    assert functions['transport_identity'].replace("'185s'","'35s'")==old_transport
    known=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='known' for t in n.targets)))
    memory=json.loads((WHOLE/'compiler-memory-capture-v1-actual/closure-stdout-v1.json').read_bytes())
    for row in memory['rows']:
        value={k:row[k] for k in ('bytes','sha256')};assert row['path'] not in known or known[row['path']]==value;known[row['path']]=value
    status=json.loads((WHOLE/'normalized-unit-envelope-v3-actual/status-stdout-v3.json').read_bytes())
    for name in ('lane.json','resources.json','outer-resources.json','envelope-result.json','observer/unit-observation-result.json','source-after.json'):
        row=status['raw_files'][name];known[str(OBSERVER/name)]={k:row[k] for k in ('bytes','sha256')}
    selected={
      'helper':WHOLE/'abi-role-transport-v2/abi_role_transport_v1.py',
      'legacy':WHOLE/'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py',
      'binder':WHOLE/'whole_interface_v4.py',
      'normalizer':WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py',
      'tokens':WHOLE/'streaming-minify-v1/strict_minify_v2.py',
      'python_surface':WHOLE/'normalized-unit-observation-v1/modules/closed_python_surface.py'}
    expected={'helper':'ea2e7e26ae154ccb9bd40204f75571ddca8fe50591a862d36abb140ec0893f8e','legacy':'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c',
       'binder':'217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8','normalizer':'6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941',
       'tokens':'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897','python_surface':'748423c27ac8c1f9810c08d3f0ffc71548da703b4b4f95cedc31d4f8bc0418af'}
    controls={};staging=[]
    for role,path in selected.items():
        assert pin(path)['sha256']==expected[role]
        output=HERE/'controls'/path.name;output.write_bytes(path.read_bytes());row=pin(output);remote=dict(row,path=str(ROOT/'control'/path.name));controls[role]=remote;staging.append(dict(source=row,destination=remote))
    runtime=json.loads((WHOLE/'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json').read_bytes())
    artifacts=[dict(family=family,ABI=dict(path=str(root/'component/abi.ast.json'),bytes=count,sha256=digest),probe=dict(path=str(root/'control/compiler_abi_probe_v1.cpp'),bytes=1588,sha256='c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34'))
        for family,root,count,digest in [('first-source-v10',RAW,127394,'0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'),('three-memory-g642',MEMORY,127541,'493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c')]]
    policy=dict(schema='retained-ABI-replay-policy-1',date='2026-10-16 ET',controls=controls,known=known,artifacts=artifacts,
        runtime_hashes=runtime['runtime_files'],python_binding=runtime['python_surface_binding'],
        control_membership=sorted([Path(row['path']).name for row in controls.values()]+['policy.json','replay_entry_v1.py']),
        resource=dict(wall_seconds=180,outer_seconds=185,RLIMIT_AS=536870912,CPU_soft=170,CPU_hard=175,stdout_bytes=65536),
        original_refusals_and_G642_observation_only_preserved=True,fresh_compiler_source_or_public_admission=False)
    save('controls/policy.json',policy);policy_pin=pin(HERE/'controls/policy.json');staging.append(dict(source=policy_pin,destination=dict(policy_pin,path=str(ROOT/'control/policy.json'))))
    # These are the exact old selected roots plus the memory raw and this new audit context.
    old_needles=(str(RAW),'/data1/yanruj/probata-resume-20261016-2baf722f','/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v2',
        '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v2',str(OBSERVER))
    prefix="""import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(170,175))
import os,json,hashlib,stat,subprocess,signal,time,ast,sys,types,re,copy,io,shutil,zlib
from pathlib import Path
signal.alarm(180)
started=time.monotonic()
"""
    prefix+='ROOT=Path('+repr(str(ROOT))+')\nRAW=Path('+repr(str(RAW))+')\nMEMORY=Path('+repr(str(MEMORY))+')\nOBSERVER=Path('+repr(str(OBSERVER))+')\nSOURCE=Path("/data1/yanruj/probata-resume-20261016-2baf722f")\nCOMMIT="2baf722fdaa6cba24b859eae3172a6f597417d72"\nPOLICY_SHA='+repr(policy_pin['sha256'])+'\nREADS={}\nTRANSPORT=None\n'
    prefix+=pam+'\n'+'\n\n'.join(functions.values())+'\nneedles='+repr((*old_needles,str(MEMORY),str(ROOT)))+'\n'
    entry=prefix+(HERE/'replay_body_v1.py.txt').read_text();ast.parse(entry);(HERE/'replay_entry_v1.py').write_text(entry)
    entry_pin=pin(HERE/'replay_entry_v1.py');staging.append(dict(source=entry_pin,destination=dict(entry_pin,path=str(ROOT/'control/replay_entry_v1.py'))))
    save('staging-manifest-v1.json',dict(date='2026-10-16 ET',schema='prospective-readonly-ABI-replay-staging-1',fresh_root=str(ROOT),files=staging,
        root_must_exclusively_create_root_and_control_before_launch=True,measurement_raw_and_source_writes=False,staging_execution_authorized=False))
    command="/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/timeout --signal=TERM --kill-after=5s 185s /usr/bin/python3 -I -B -"
    save('command-v1.json',dict(date='2026-10-16 ET',schema='retained-ABI-replay-command-1',remote_shell_command=command,stdin=entry_pin,
        argv=['ssh','mbit10',command],local_timeout_seconds=200,max_stdout_bytes=65536,max_stderr_bytes=65536,root_once_admission_required=True,actual_execution=False,
        root_preflight='Verify complete staging manifest, exact stdin bytes, fresh canonical audit context, original source/raw/lease and selected runtime. Only two exact metadata Git children occur before replay audit.',
        root_postflight='Require zero exit, bounded complete JSON stdout, current selected context controls/raw/source/runtime closure and fresh whole source Git status. No private/public producer adoption inferred.'))
    save('scanner-inverse-v1.json',dict(date='2026-10-16 ET',basis=pin(old),source_functions=['pam_identity','transport_identity','scan'],
        pam_and_scan_source_and_AST_exact=True,transport_replacements=[dict(old="'35s'",new="'185s'")],transport_byte_inverse_exact=True,
        all_PAM_UID_birth_ancestry_and_unknown_unreadable_refusals_preserved=True,original_needles=list(old_needles),added_needles=[str(MEMORY),str(ROOT)],
        complete_module_bytes_unchanged={role:dict(basis=pin(selected[role]),staged=pin(HERE/'controls'/selected[role].name)) for role in selected},
        legacy_complete_module_and_validator_AST_unchanged=True,old_diagnostic_program_not_relabelled_as_new_replay=True))
    return entry_pin
if __name__=='__main__':print(json.dumps(build(),sort_keys=True))

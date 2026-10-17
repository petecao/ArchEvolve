"""2026-10-16 ET. Compiler-free V4 controller authoring; never dispatches.

The published initialized proof source, original partial caller, both answers,
native health gates and frozen runner remain unchanged. This versions only the
Linux runtime admission and retains complete before/after physical evidence.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
TRACE = HERE.parent / '28-public-memory-trace-resume-20261016'
EVIDENCE = HERE.parents[1] / 'evidence/resume-20261016-lane-coordination'
BASE_ENTRY_SHA = '9d8753cdc21899c95b37d51544429355067e7b1ff76ffc3755adae405fd8f0fa'
BASE_POLICY_SHA = '22448884a92a7154db776ab570383dc5889e142236964614479e86a3cbb526bf'
RAW_NAME = 'probata-resume-20261016-t28-initialized-pair-2baf722f-v4'
HELPERS = ('closed_python_surface.py', 'python_startup_roles_v2.py', 'python_role_observer_v2.py')
OBSERVER_NAME = 't28-linux-runtime-observer-v2-actual-20261016.json'
FRAMAC_META_PIN = {
    'path': '/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c/META',
    'bytes': 2318,
    'sha256': '1d41605b5220bc71779ffac319ff9b06950245f5eab9f61894e865ddd9658002',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path, expected=None):
    data = path.read_bytes()
    if expected is not None and sha(data) != expected:
        raise ValueError('exact reviewed authoring basis differs: ' + str(path))
    return data


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('exact V3 source anchor differs: ' + old[:80])
    return text.replace(old, new, 1)


RUNTIME_FUNCTIONS = '''
# V4 controller-only runtime closure. No project import or tool execution here.
def load_controller_module_v4(name):
 import types
 if name not in EXPECTED['controller_files']:raise ValueError('unlisted controller input')
 path=policy_path.parent/name
 if path.is_symlink()or not path.is_file()or path.parent!=output/'control':raise ValueError('regular raw/control input required')
 data=path.read_bytes();wanted=EXPECTED['controller_files'][name]
 if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('controller input bytes differ: '+name)
 module=types.ModuleType('t28_reviewed_'+name.removesuffix('.py'))
 module.__file__=str(path)
 exec(compile(data,str(path),'exec'),module.__dict__)
 return module,data

def controller_root_observer_v4():
 if EXPECTED['root_observer_file']!='t28-linux-runtime-observer-v2-actual-20261016.json':raise ValueError('exact root observation metadata name required')
 path=policy_path.parent/EXPECTED['root_observer_file']
 wanted=EXPECTED['controller_files'][path.name]
 if path.is_symlink()or not path.is_file():raise ValueError('regular root observation metadata required')
 data=path.read_bytes()
 if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('root observation metadata bytes differ')
 return data

def runtime_surface_check_v4(label):
 controls={}
 names={Path(__file__).name,policy_path.name,*EXPECTED['controller_files']}
 if {path.name for path in policy_path.parent.iterdir()}!=names:raise ValueError('exact staged controller membership differs')
 if hashlib.sha256(policy_path.read_bytes()).hexdigest()!=sys.argv[4]or pin(__file__)['sha256']!=EXPECTED['linux_launch_binding']['entry_sha256']:raise ValueError('entry/policy bytes changed')
 for name,wanted in EXPECTED['controller_files'].items():
  path=policy_path.parent/name
  if path.name!=name or path.parent!=output/'control'or path.is_symlink()or not path.is_file():raise ValueError('regular closed controller basename required')
  data=path.read_bytes()
  if len(data)!=wanted['bytes']or hashlib.sha256(data).hexdigest()!=wanted['sha256']:raise ValueError('staged controller input changed: '+name)
  controls[name]=wanted
 python=closed_v4.verify_python_metadata(EXPECTED['python_surface_binding'])
 files={}
 for name,digest in EXPECTED['runtime_files'].items():
  row=pin(name)
  if row['sha256']!=digest:raise ValueError('complete physical runtime component differs: '+name)
  files[name]=row['sha256']
 meta=EXPECTED['framac_kernel_meta_origin']['pin']
 if Path(meta['path']).stat().st_size!=meta['bytes']or files.get(meta['path'])!=meta['sha256']:raise ValueError('fresh Frama kernel META physical pin differs')
 packages={}
 for name,root in EXPECTED['ocaml_packages'].items():
  root_path=Path(root)
  wanted=[{'relative':str(Path(path).relative_to(root_path)),'sha256':digest}for path,digest in EXPECTED['runtime_files'].items()if Path(path).is_relative_to(root_path)]
  wanted.sort(key=lambda row:Path(row['relative']).parts)
  if not wanted:raise ValueError('complete package file inventory is empty: '+name)
  packages[name]=import_surface(root_path,wanted)
 prefix=Path(EXPECTED['tools']['frama-c']['path']).parent.parent
 portable={name:import_surface(root,EXPECTED['portable_import_surfaces'][name])for name,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]}
 headers=header_surface_check_v4(EXPECTED['linux_header_surfaces'],EXPECTED['linux_clang_components']['headers'],closed_v4)
 receipt={'controller_files':controls,'python':python,'runtime_files':files,'ocaml_packages':packages,'portable_import_surfaces':portable,'linux_headers':headers,'scope':'Physical content/membership closure only; no solver or theorem result'}
 (output/('initialized-runtime-'+label+'.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\\n')
 return receipt

def header_surface_check_v4(surfaces,wanted,closed):
 if set(surfaces)!={'libc++','clang-resource'}:raise ValueError('exact two LLVM header roots required')
 aggregate=hashlib.sha256();count=0;receipts={}
 for label in ('libc++','clang-resource'):
  expected=surfaces[label];root=Path(expected['path'])
  if closed._resolution(root,[])!=root or root.is_symlink()or not root.is_dir():raise ValueError('canonical physical LLVM header root required')
  rows=[]
  for path in sorted(root.rglob('*')):
   mode=path.lstat().st_mode
   if stat.S_ISLNK(mode)or not(stat.S_ISREG(mode)or stat.S_ISDIR(mode)):raise ValueError('LLVM header symlink/special input')
   if stat.S_ISDIR(mode):continue
   row,_unused=closed._regular(path)
   row={'relative':str(path.relative_to(root)),'bytes':row['bytes'],'sha256':row['sha256']}
   rows.append(row);aggregate.update(label.encode()+b'\\0'+row['relative'].encode()+b'\\0'+bytes.fromhex(row['sha256']));count+=1
  digest=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
  if len(rows)!=expected['count']or digest!=expected['inventory_sha256']:raise ValueError('complete LLVM header membership/content differs')
  receipts[label]={'path':str(root),'count':len(rows),'inventory_sha256':digest}
 identity={'id':'llvm-standard-resource-headers','sha256':aggregate.hexdigest(),'files':count}
 if identity!=wanted:raise ValueError('selected LLVM production header aggregate differs')
 return {'surfaces':receipts,'aggregate':identity}

def observe_startup_role_v4(plan,role,environment,cache):
 request=roles_v4.role_request_v2(plan,role=role,environment=environment,cache=cache)
 command=[EXPECTED['linux_launch_binding']['python']]
 if role=='entry-isolated':command+=['-I']
 command+=['-B','-X','pycache_prefix='+str(cache),'-c',observer_source_v4.decode(),json.dumps(request,sort_keys=True)]
 done=subprocess.run(command,cwd=project,env=environment,capture_output=True,text=True,timeout=30)
 evidence={'role':role,'argv_prefix':command[:command.index('-c')+1],'request':request,'exit_code':done.returncode,'stdout':done.stdout,'stderr':done.stderr,'observer_source_sha256':hashlib.sha256(observer_source_v4).hexdigest()}
 (output/('initialized-python-'+role+'.json')).write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\\n')
 if done.returncode or done.stderr:raise ValueError('actual guarded Python startup role refused: '+role)
 observed=json.loads(done.stdout)
 receipt=roles_v4.check_role_observation_v2(request,observed)
 (output/('initialized-python-'+role+'-accepted.json')).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\\n')
 return receipt

def runner_child_environment_v4(base,project,output,roles):
 profile=output/'initialized-profile'
 environment=roles.child_environment_v2(base,project=project,raw=profile,cache=profile/'source-cache')
 environment.update(PROBATA_PYTHON=sys.executable,TMPDIR=str(profile/'tmp'),XDG_CACHE_HOME=str(profile/'cache'))
 return environment
'''


def prepare():
    base = load(HERE / 'linux_pair_entry_v3.py', BASE_ENTRY_SHA).decode()
    policy = json.loads(load(HERE / 'linux_pair_policy_2baf722f_v3.json', BASE_POLICY_SHA))
    policy['linux_launch_binding']['node'] = 0
    candidate = json.loads(load(EVIDENCE / 't28-abstract25-linux-runtime-candidate-policy-fields.json'))
    candidate['runtime_files'][FRAMAC_META_PIN['path']] = FRAMAC_META_PIN['sha256']
    prior_components = json.loads(load(EVIDENCE / 't28-abstract25-linux-prior-frama-clang-fresh-rehash.json'))
    parser_path = '/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/libclang.so.22.1.8'
    if candidate['runtime_files'].get(parser_path) != policy['linux_clang_components']['parser']['sha256']:
        raise ValueError('exact physical libclang parser pin is absent from the runtime closure')
    observer_path = EVIDENCE / OBSERVER_NAME
    root_bytes = load(observer_path)
    root = json.loads(root_bytes)['observation']
    if root['cbmc_version_observation']['stdout'] != '6.11.0 (cbmc-6.11.0)\n':
        raise ValueError('actual root version observation differs')
    control = {}
    for path in [*(TRACE / name for name in HELPERS), observer_path]:
        data = load(path)
        control[path.name] = {'bytes': len(data), 'sha256': sha(data)}
    physical = candidate['python_surface_binding']
    physical_fields = {key: physical[key] for key in ('schema', 'surfaces', 'startup_pins', 'pth', 'interpreter', 'absence')}
    canonical = lambda value: sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
    covered = []
    for path in root['sys_path']:
        if path in physical['absence'] or path in physical['surfaces']:
            continue
        parents = [name for name in physical['surfaces'] if Path(name) in Path(path).parents]
        if len(parents) != 1:
            raise ValueError('root observed path lacks one exact physical root')
        covered.append({'path': path, 'root': parents[0]})
    policy.update(runtime_files=candidate['runtime_files'],
                  python_surface_binding=physical, ocaml_packages=candidate['ocaml_packages'],
                  linux_header_surfaces={label: {key: value for key, value in row.items() if key != 'files'}
                                         for label, row in prior_components['header_surfaces'].items()},
                  framac_kernel_meta_origin={'pin': FRAMAC_META_PIN,
                      'source': 'Root fresh passive mbit10 physical hash/size reported directly on 2026-10-16 ET; no native query executed'},
                  controller_files=control, root_observer_file=OBSERVER_NAME,
                  raw_name=RAW_NAME,
                  startup_roles={'schema': 'python-startup-roles-plan-2', 'admitted': True,
                      'root_observer_sha256': sha(root_bytes), 'root_observer_selection': 'observation',
                      'physical_metadata_sha256': canonical(physical_fields),
                      'package_sys_path': root['sys_path'], 'covered_descendants': covered,
                      'packages': root['selected_packages'],
                      'module_origins': {name: root['loaded_module_origins'][name] for name in
                                         ('site', 'sitecustomize', '_distutils_hack', 'pytest', 'yaml', 'jsonschema', 'psutil')},
                      'executable': root['executable'], 'prefix': root['prefix'],
                      'base_prefix': root['base_prefix'],
                      'source_project': '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project'})
    text = replace_once(base, 'os.chdir(project);sys.path.insert(0,str(project))', 'os.chdir(project)')
    text = replace_once(text, 'ambient=ambient_check(os.environ,EXPECTED[\'config\'][\'path\'],project)',
                        RUNTIME_FUNCTIONS + '\nambient=ambient_check(os.environ,EXPECTED[\'config\'][\'path\'],project)')
    anchor = "(output/'initialized-source-consumer-closure-before.json').write_text(json.dumps(closure,indent=2,sort_keys=True)+'\\n')\n"
    bootstrap = '''
if output.name!=EXPECTED['raw_name']or output.is_symlink():raise ValueError('exact fresh V4 raw namespace required')
closed_v4,_closed_source_v4=load_controller_module_v4('closed_python_surface.py')
roles_v4,_roles_source_v4=load_controller_module_v4('python_startup_roles_v2.py')
_observer_module_v4,observer_source_v4=load_controller_module_v4('python_role_observer_v2.py')
runtime_surface_check_v4('before')
role_plan_v4=EXPECTED['startup_roles']
plan_receipt_v4=roles_v4.validate_role_plan_v2(role_plan_v4,metadata=EXPECTED['python_surface_binding'],source_project=project,root_observer_bytes=controller_root_observer_v4(),closed=closed_v4)
(output/'initialized-python-role-plan.json').write_text(json.dumps(plan_receipt_v4,indent=2,sort_keys=True)+'\\n')
observe_startup_role_v4(role_plan_v4,'entry-isolated',dict(os.environ),bootstrap_cache)
child_environment_v4=runner_child_environment_v4(os.environ,project,output,roles_v4)
observe_startup_role_v4(role_plan_v4,'pytest-child',child_environment_v4,output/'initialized-profile/source-cache')
runtime_surface_check_v4('after-startup')
'''
    text = replace_once(text, anchor, anchor + bootstrap)
    text = replace_once(text, 'from swdb import c_lowering,stdlib_provenance\n',
                        "sys.path.insert(0,str(project))\nfrom swdb import c_lowering,stdlib_provenance\n")
    text = replace_once(text,
                        "valid=done.returncode==0 and path.is_dir() and path.is_relative_to((prefix/'lib').resolve())",
                        "valid=done.returncode==0 and path.is_dir() and path.is_relative_to((prefix/'lib').resolve())and path==Path(EXPECTED['ocaml_packages'][name]).resolve()")
    # Use the finalized compiler/tool markers in the exact runner environment.
    text = replace_once(text, "os.environ.update(PROBATA_OUTPUT=str(profile),PROBATA_PYTHON=sys.executable)\n",
                        "child_environment_v4=runner_child_environment_v4(os.environ,project,output,roles_v4)\n")
    text = replace_once(text, 'os.execv(command[0],command)\n', '''
result_v4=None
try:
 result_v4=subprocess.run(command,env=child_environment_v4,cwd=project,timeout=1180).returncode
 (output/'initialized-runner-exit-code.txt').write_text(str(result_v4)+'\\n')
finally:
 source_check()
 closure=consumer_closure(project,repo,EXPECTED)
 (output/'initialized-source-consumer-closure-after.json').write_text(json.dumps(closure,indent=2,sort_keys=True)+'\\n')
 runtime_surface_check_v4('after')
 if bootstrap_cache.exists()or bootstrap_cache.is_symlink():raise ValueError('unexpected entry bytecode cache output')
 if (profile/'source-cache').exists()or(profile/'source-cache').is_symlink():raise ValueError('unexpected child bytecode cache output')
raise SystemExit(result_v4)
''')
    ast.parse(text)
    entry_path = HERE / 'linux_pair_entry_v4.py'
    entry_path.write_text(text)
    policy['linux_launch_binding']['entry_sha256'] = sha(text.encode())
    policy['runtime_controller_version'] = 4
    policy_path = HERE / 'linux_pair_policy_2baf722f_v4.json'
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
    command = json.loads((HERE / 'linux_pair_command_2baf722f_v3.json').read_text())
    old_raw = command['raw_root']
    new_raw = old_raw.removesuffix('-v3') + '-v4'
    command = json.loads(json.dumps(command).replace(old_raw, new_raw).replace('linux_pair_entry_v3.py', 'linux_pair_entry_v4.py').replace('linux_pair_policy_2baf722f_v3.json', 'linux_pair_policy_2baf722f_v4.json'))
    command['argv'][-1] = sha(policy_path.read_bytes())
    command['controller_inputs'] = [{'path': str(path), 'bytes': len(load(path)), 'sha256': sha(load(path))}
                                    for path in (entry_path, policy_path, *(TRACE / name for name in HELPERS), observer_path)]
    command['status'] = 'INERT/UNLAUNCHED V4; reviewed exact-role startup and complete physical runtime closure; root review/admission required'
    command['runtime_controller_version'] = 4
    command['node'] = 0
    command['runtime_scope'] = 'Entry-I and final runner child-role states independently checked before project imports; raw root V2 provenance retained; all proof criteria unchanged'
    command['proof_acceptance'] = False
    command['independent_review_pending'] = True
    (HERE / 'linux_pair_command_2baf722f_v4.json').write_text(json.dumps(command, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    prepare()

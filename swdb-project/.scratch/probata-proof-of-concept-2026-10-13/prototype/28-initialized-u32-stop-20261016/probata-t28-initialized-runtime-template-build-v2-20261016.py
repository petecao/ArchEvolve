"""2026-10-16 ET. INERT runtime policy from cached observations + read-only hashes.

No project import, identity/version call, subprocess, compiler or formal tool.
The companion inventory explicitly leaves native loader/compiler correctness TCB.
"""
import hashlib,json,shlex,sys
from pathlib import Path
def refuse(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure runtime template reader refused execution: '+event)
sys.addaudithook(refuse)
ROOT=Path('/private/tmp');PROJECT=ROOT/'probata-resume-t25-pair/swdb-project'
EXPECTED=ROOT/'probata-t07-device-diagnostic-proof-v2-20261016-expected.json'
BASE=ROOT/'probata-t28-initialized-u32-compiler-observe-v1-20261016/component'
def pin(path):
 p=Path(path).resolve()
 with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
def save(path,data):
 path=Path(path);assert not path.exists();path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
expected=json.loads(EXPECTED.read_text());cached=expected['runtime'];allpins={};origins={};trees=[]
def add(path,origin,prior=None):
 row=pin(path)
 if prior is not None:
  assert row['sha256']==prior['sha256'],('cached physical hash changed',str(path))
  assert 'bytes'not in prior or row['bytes']==prior['bytes'],('cached physical bytes changed',str(path))
 if row['path']in allpins:assert allpins[row['path']]==row
 allpins[row['path']]=row;origins.setdefault(row['path'],[]).append(origin)
 return row
for row in cached['configuration_files']:add(row.get('resolved',row['path']),'cached OCaml/package configuration',row)
for row in cached['native_closure']:add(row.get('resolved',row['path']),'cached selected OCaml/WP native closure',row)
for name in ['ocamlfind','ocamlopt','gcc']:
 row=cached['tools'][name];add(row.get('resolved',row['path']),'cached selected compiler '+name,row)
add(cached['python']['path'],'cached selected Python',cached['python'])
for row in cached['toolchain_artifacts']:add(row.get('resolved',row['path']),'cached WP compiler artifacts',row)
for surface in cached['package_surfaces']:
 for row in surface['files']:add(row.get('resolved',row['path']),'cached package '+surface['path'],row)
 root=Path(surface['path']);assert root.is_dir()
 # Conservatively include every present physical member, including ML/native
 # interfaces and metadata. This is a new filesystem inventory, not a probe.
 members=[]
 for path in sorted(root.rglob('*')):
  if path.is_file():members.append({'relative':str(path.relative_to(root)),**add(path,'complete selected package tree')})
 trees.append({'role':'selected package','root':str(root),'files':len(members),'membership_sha256':hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
for path in [Path('/Users/yanrujhou/.opam/framac-33/lib/frama-c/META'),Path('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/META')]:add(path,'selected package META')
context=(BASE/'driver-context.stderr').read_text()
line=next(line for line in context.splitlines()if '"-cc1"'in line);argv=shlex.split(line)
def argument(flag):
 assert argv.count(flag)==1,flag
 return argv[argv.index(flag)+1]
driver=Path(argv[0]).resolve();assert pin(driver)['sha256']=='305697d3868243dca6e4aabf4f628df7de135d701eb4fd78f6a5d7528fef4395'
add(driver,'root original8c3 selected driver')
resource=Path(argument('-resource-dir')).resolve();llvm=resource.parents[2];sdk=Path(argument('-isysroot')).resolve()
clang_config=Path(next(line.split(': ',1)[1]for line in context.splitlines()if line.startswith('Configuration file: '))).resolve()
add(clang_config,'retained actual driver configuration')
libclang=Path('/opt/homebrew/opt/llvm/lib/libclang.dylib');assert libclang.is_file()
add(libclang,'selected own ctypes Clang-C API library')
for role,root in [('libc++',llvm/'include/c++/v1'),('clang-resource',resource/'include')]:
 assert root.is_dir();members=[]
 for path in sorted(root.rglob('*')):
  if path.is_file():members.append({'relative':str(path.relative_to(root)),**add(path,'complete observed '+role+' header tree')})
 trees.append({'role':role,'root':str(root),'files':len(members),'membership_sha256':hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
inputs=json.loads((BASE/'compiler-inputs.json').read_text());sdkpins=[]
for row in inputs:
 if Path(row['path']).is_relative_to(sdk):sdkpins.append(add(row['path'],'retained original actually used SDK input',row))
assert sdkpins
pythonroot=Path('/Users/yanrujhou/.pyenv/versions/3.12.6/lib/python3.12')
ctypes_members=[]
for path in sorted((pythonroot/'ctypes').rglob('*')):
 if path.is_file()and '__pycache__'not in path.parts and path.suffix!='.pyc':ctypes_members.append(add(path,'selected Python stdlib ctypes own-binding support'))
extensions=[pythonroot/'lib-dynload/_ctypes.cpython-312-darwin.so'];assert extensions[0].is_file()
add(extensions[0],'selected Python ctypes native extension')
for path in [Path('/usr/bin/clang'),Path('/usr/bin/cc'),Path('/usr/bin/ld'),Path('/usr/bin/as')]:
 if path.is_file():add(path,'selected system OCaml C/assembler/linker path; native implementation remains TCB')
policy={'pins':[allpins[key]for key in sorted(allpins)],'clang_command':'/opt/homebrew/opt/llvm/bin/clang++',
 'ocamlfind_command':'/Users/yanrujhou/.opam/framac-33/bin/ocamlfind',
 'path':'/Users/yanrujhou/.opam/framac-33/bin:/opt/homebrew/opt/llvm/bin:/usr/bin:/bin:/usr/sbin:/sbin',
 'opam_switch_prefix':'/Users/yanrujhou/.opam/framac-33'}
out=ROOT/'probata-t28-initialized-u32-public-runtime-policy-template-v1-20261016.json'
save(out,policy)
inventory={'date':'2026-10-16 ET','status':'INERT TEMPLATE; root independently rechecks and admits before any workflow',
 'published_source_commit':'188a478eaf29089050b70adfbc4a546d20440cb4','runtime_policy':pin(out),'cached_expected':pin(EXPECTED),
 'actual_driver_context':pin(BASE/'driver-context.stderr'),'actual_original_used_inputs':pin(BASE/'compiler-inputs.json'),
 'expected_package_roots':cached['package_bindings'],'trees':trees,'sdk_root':str(sdk),'actually_used_sdk_inputs':sdkpins,
 'pin_count':len(allpins),'physical_bytes':sum(p['bytes']for p in allpins.values()),'pin_origins':origins,
 'python_binding':{'kind':'owned ctypes binding, no clang.cindex or cffi import in selected source','source':pin(PROJECT/'swdb/stdlib_provenance.py'),
  'support_files':ctypes_members,'native_extension':pin(extensions[0]),'selected_libclang':pin(libclang)},
 'explicit_boundaries':['No complete LLVM transitive dynamic-loader closure is claimed; OS loader/dyld shared cache/native compiler correctness remain TCB',
  'LLVM/libc++ trees are fully inventoried; SDK pins are exactly the retained original actually used inputs, not all possible SDK/framework headers',
  'Original source constructor first records used-header pins after preprocessing and rechecks afterward; full source/header correspondence remains owned TCB',
  'The real profile must freshly calculate and match context-specific method/setup/lowerer identities; no historical composite substitutes',
  'Root wrapper separately freezes complete package/consumer tracked source and current config; ignored caches are outside scientific acceptance',
  'Runtime-policy pins do not authorize actual Frama/WP/Why3/solver or caller execution; only root-reviewed compiler plus scripted persistence'],
 'actual_workflow_launched':False,'tool_or_version_probe':False,'source_body_proof':False,'formal_acceptance':False}
meta=ROOT/'probata-t28-initialized-u32-public-runtime-template-context-v1-20261016.json'
save(meta,inventory)
print(json.dumps({'policy':pin(out),'context':pin(meta),'pins':len(allpins),'trees':trees},sort_keys=True))

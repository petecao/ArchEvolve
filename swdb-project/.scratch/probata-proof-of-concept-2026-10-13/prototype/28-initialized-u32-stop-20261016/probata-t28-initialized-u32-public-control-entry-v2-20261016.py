"""INERT root-only compiler/scripted-persistence profile, 2026-10-16 ET.

Root must supply a concrete reviewed published HEAD and physical runtime policy.
The only selector uses named formal-tool stand-ins. No proof result is accepted.
"""
import argparse,hashlib,json,os,re,shlex,shutil,subprocess,sys,time
from pathlib import Path

SELECTOR='tests/test_dx100_initialized_register.py::test_public_initialized_u32_has_ordinary_prewrite_capacity_and_original_partial_frame'
PY='/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12'
ORIGINAL=Path('/private/tmp/probata-resume-t25-pair/swdb-project')
SOURCE_POLICY_SHA='7b1dc8c6eb4f4cf8f57051b0699fa34f744fa379f753fa85e28dc110c4ffb3e3'
LIMIT=256*1024**2
def sha(path):
 with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pin(path):
 p=Path(path).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def save(path,value):Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def main():
 profile_started=time.monotonic();deadline=profile_started+220
 parser=argparse.ArgumentParser()
 for key in ['project','output','source-policy','runtime-policy']:parser.add_argument('--'+key,type=Path,required=True)
 parser.add_argument('--expected-commit',required=True);parser.add_argument('--runtime-sha256',required=True)
 args=parser.parse_args();project=args.project.resolve();out=args.output.resolve()
 if sys.executable!=PY or sys.flags.optimize:raise ValueError('exact selected nonoptimized Python required')
 if not re.fullmatch('[a-f0-9]{40}',args.expected_commit):raise ValueError('root must bind a concrete reviewed published HEAD')
 if not re.fullmatch('[a-f0-9]{64}',args.runtime_sha256)or sha(args.runtime_policy)!=args.runtime_sha256:raise ValueError('root selected runtime policy bytes changed')
 if sha(args.source_policy)!=SOURCE_POLICY_SHA:raise ValueError('explicit successor source-policy metadata changed')
 if out.exists()or args.output.is_symlink()or out.is_relative_to(project.parent):raise ValueError('fresh raw component outside full checkout required')
 if shutil.disk_usage(out.parent).free<50*1024**3+LIMIT:raise ValueError('50GiB free floor plus256MiB raw allowance required')
 if not os.environ.get('SWDB_VERIFIER_RUN_TOKEN'):raise ValueError('root admitted B+c6 marker required')
 if any(os.environ.get(k)for k in ['CPATH','CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','OBJC_INCLUDE_PATH','INCLUDE','SDKROOT','PYTEST_ADDOPTS','OCAMLPATH']):
  raise ValueError('ambient include/SDK/pytest/OCaml overrides need separate review')
 def git(*argv):
  remaining=deadline-time.monotonic()-2
  if remaining<=0:raise TimeoutError('public profile remaining budget exhausted')
  result=subprocess.run(['/usr/bin/git','-C',str(project),*argv],capture_output=True,text=True,timeout=min(10,remaining),check=True)
  return result.stdout.strip()
 if git('rev-parse','HEAD')!=args.expected_commit or git('status','--porcelain','--untracked-files=all'):raise ValueError('exact clean source HEAD required')
 expected=json.loads(args.source_policy.read_text());runtime=json.loads(args.runtime_policy.read_text())
 if set(runtime)!={'pins','clang_command','ocamlfind_command','path','opam_switch_prefix'}:raise ValueError('closed root runtime-policy shape required')
 if shlex.split(runtime['clang_command'])!=['/opt/homebrew/opt/llvm/bin/clang++']:raise ValueError('only previously selected Clang argv allowed')
 compiler=shlex.split(runtime['ocamlfind_command'])
 if compiler!=['/Users/yanrujhou/.opam/framac-33/bin/ocamlfind']:raise ValueError('root must bind selected direct Frama33 OCamlfind')
 if runtime['path']!='/Users/yanrujhou/.opam/framac-33/bin:/opt/homebrew/opt/llvm/bin:/usr/bin:/bin:/usr/sbin:/sbin' or runtime['opam_switch_prefix']!='/Users/yanrujhou/.opam/framac-33':
  raise ValueError('selected compiler switch/PATH context differs')
 if not isinstance(runtime['pins'],list)or not runtime['pins']:raise ValueError('complete selected compiler/runtime/package physical pins required')
 required={str(Path(p).resolve())for p in [PY,'/opt/homebrew/opt/llvm/bin/clang++',compiler[0],'/Users/yanrujhou/.opam/framac-33/bin/ocamlopt']}
 if not required.issubset({p['path']for p in runtime['pins']}):raise ValueError('selected Python/Clang/OCamlfind/OCamlopt binary omitted')
 if sha('/opt/homebrew/opt/llvm/bin/clang++')!='305697d3868243dca6e4aabf4f628df7de135d701eb4fd78f6a5d7528fef4395':raise ValueError('original observed Clang bytes changed')
 for row in runtime['pins']:
  if pin(row['path'])!=row:raise ValueError('selected root runtime pin changed')
 before=[]
 for row in expected['source_paths']:
  path=project/Path(row['path']).relative_to(ORIGINAL);actual=pin(path)
  if actual['bytes']!=row['bytes']or actual['sha256']!=row['sha256']:raise ValueError('successor selected source byte changed: '+str(path))
  before.append(actual)
 out.mkdir();save(out/'source-before.json',before);save(out/'runtime-before.json',runtime)
 pycache=out/'source-cache'
 if pycache.exists()or pycache.is_symlink():raise ValueError('fresh nonexistent private bytecode cache prefix required')
 command=[PY,'-B','-m','pytest','-q','-x','-p','no:cacheprovider',SELECTOR,'--basetemp',str(out/'pytest'),'--junitxml',str(out/'junit.xml')]
 environment={'PATH':runtime['path'],'HOME':'/Users/yanrujhou','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
  'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','SWDB_CLANG':runtime['clang_command'],'SWDB_OCAMLFIND':runtime['ocamlfind_command'],
  'OPAM_SWITCH_PREFIX':runtime['opam_switch_prefix'],'TMPDIR':str(out/'tmp'),'PYTHONPYCACHEPREFIX':str(pycache)}
 (out/'tmp').mkdir()
 for key in ['SWDB_VERIFIER_RUN_TOKEN','SWDB_WATCHDOG_TAG','SWDB_VERIFIER_LOCK','SWDB_VERIFIER_RSS_CAP_BYTES']:
  if key in os.environ:environment[key]=os.environ[key]
 save(out/'command.json',{'argv':command,'cwd':str(project),'scope':'real compiler plus scripted persistence only; no real formal or native caller program',
  'expected_head':args.expected_commit,'entry':pin(__file__),'source_policy':pin(args.source_policy),'runtime_policy':pin(args.runtime_policy)})
 code=None;error=None
 try:
  remaining=min(200,deadline-time.monotonic()-10)
  if remaining<=0:raise TimeoutError('profile preparation exhausted remaining budget')
  with (out/'pytest.log').open('wb')as log:
   result=subprocess.run(command,cwd=project,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=remaining,check=False)
  code=result.returncode
 except subprocess.TimeoutExpired:error='pytest whole profile timeout; stdout retained'
 finally:
  after=[pin(p['path'])for p in before];save(out/'source-after.json',after)
  runtime_equal=all(pin(p['path'])==p for p in runtime['pins'])
  clean=git('rev-parse','HEAD')==args.expected_commit and not git('status','--porcelain','--untracked-files=all')
  total=sum(p.stat().st_size for p in out.rglob('*')if p.is_file())
  save(out/'result.json',{'test_exit_code':code,'error':error,'wall_s':time.monotonic()-profile_started,'source_unchanged':after==before and clean,
   'python_bytecode_cache':{'prefix':str(pycache),'fresh_nonexistent_before_child':True,'exists_after':pycache.exists(),'policy':'-B and PYTHONDONTWRITEBYTECODE plus fresh prefix; no ignored author pyc consumption'},
   'runtime_pins_unchanged':runtime_equal,'raw_bytes_before_receipt':total,'scope':'compiler/scripted-persistence observation only',
   'actual_formal_acceptance':False,'native_caller_execution':False,'source_body_proof':False,'current_0_2':False,'full_ticket28':False})
  save(out/'artifact-manifest.json',[{'relative':str(p.relative_to(out)),**pin(p)}for p in sorted(out.rglob('*'))if p.is_file()and p.name!='artifact-manifest.json'])
 if code!=0 or error or after!=before or not runtime_equal or not clean or total>LIMIT or pycache.exists():return 1
 return 0
if __name__=='__main__':raise SystemExit(main())

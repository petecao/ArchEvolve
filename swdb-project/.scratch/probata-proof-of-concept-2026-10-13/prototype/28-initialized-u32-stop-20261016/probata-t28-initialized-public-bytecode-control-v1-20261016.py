"""Pure Python import-cache boundary control, 2026-10-16 ET; no tools."""
import ast,hashlib,importlib.util,importlib.machinery,importlib._bootstrap_external,json,sys
from pathlib import Path
def nochild(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure cache control refuses '+event)
sys.addaudithook(nochild)
R=Path('/private/tmp');out=R/'probata-t28-initialized-public-bytecode-control-v1-20261016'
assert not out.exists();out.mkdir()
source=out/'isolated_fixture.py';source.write_text('VALUE = "CURRENT_SOURCE"\n')
oldprefix=sys.pycache_prefix;oldwrite=sys.dont_write_bytecode
try:
 sys.pycache_prefix=None;sys.dont_write_bytecode=True
 cache=Path(importlib.util.cache_from_source(str(source)));cache.parent.mkdir()
 code=compile('VALUE = "STALE_IGNORED_CACHE"\n',str(source),'exec')
 cache.write_bytes(importlib._bootstrap_external._code_to_hash_pyc(code,importlib.util.source_hash(source.read_bytes()),checked=False))
 loader=importlib.machinery.SourceFileLoader('isolated_fixture',str(source))
 before={};exec(loader.get_code('isolated_fixture'),before)
 assert before['VALUE']=='STALE_IGNORED_CACHE','-B alone unexpectedly prevented valid existing pyc consumption'
 fresh=out/'fresh-source-cache';assert not fresh.exists()
 sys.pycache_prefix=str(fresh)
 assert Path(importlib.util.cache_from_source(str(source))).is_relative_to(fresh)
 after={};exec(loader.get_code('isolated_fixture'),after)
 assert after['VALUE']=='CURRENT_SOURCE'and not fresh.exists()
finally:
 sys.pycache_prefix=oldprefix;sys.dont_write_bytecode=oldwrite
entry=R/'probata-t28-initialized-u32-public-control-entry-v2-20261016.py'
tree=ast.parse(entry.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
environment=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='environment'for t in n.targets))
values={k.value:v for k,v in zip(environment.keys,environment.values)}
assert ast.unparse(values['PYTHONPYCACHEPREFIX'])=='str(pycache)'
assert values['PYTHONDONTWRITEBYTECODE'].value=='1'
command=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='command'for t in n.targets))
assert '-B'in [n.value for n in command.elts if isinstance(n,ast.Constant)]
conftest=R/'probata-resume-t25-pair/swdb-project/tests/conftest.py'
tree=ast.parse(conftest.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run_swdb')
assert ast.unparse(run.body[1])=='full_env = dict(os.environ)'
assert ast.unparse(run.body[2])=='full_env.update(env or {})'
call=run.body[3].value;assert ast.unparse(next(k.value for k in call.keywords if k.arg=='env'))=='full_env'
result={'status':'PASS','old_B_only_consumes_existing_valid_pyc':True,'fresh_private_prefix_reads_source_without_writing_cache':True,
 'entry_environment_pins_prefix_and_B':True,'public_helper_preserves_prefix_from_os_environ':True,
 'tools_project_imports_native_or_formal_executed':False,'source':str(source),'cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),
 'entry_sha256':hashlib.sha256(entry.read_bytes()).hexdigest(),'conftest_sha256':hashlib.sha256(conftest.read_bytes()).hexdigest()}
(out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))

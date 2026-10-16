"""Pure retained-WP assertion control; no fixture/tool/compiler execution."""
import ast,hashlib,json,re,sys
from pathlib import Path
def refuse(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('pure frame control refused '+event)
sys.addaudithook(refuse)
project=Path('/private/tmp/probata-resume-t25-pair/swdb-project')
source=project/'tests/test_dx100_initialized_register.py'
raw=Path('/private/tmp/probata-t28-initialized-u32-public-compiler-standin-v1-188a478e-20261016/component/pytest/test_public_initialized_u32_ha0/runs/proof.contract.dx100_initialized_register_partial_fixture.v1.20261016t152357z.84353b9a/wp/wp_input.c')
text=raw.read_text();tree=ast.parse(source.read_text())
helper=next((n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='assert_original_initialized_register_frame'),None)
if helper is None:
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name.startswith('test_public_'))
 node=next(n for n in fn.body if isinstance(n,ast.Assert)and isinstance(n.test,ast.Compare)and isinstance(n.test.left,ast.Constant)and n.test.left.value=='REG_count, SPD_count, region_count, __swdb_dx_reg_words[0..1]')
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),{'text':text})
 raise AssertionError('old predicate unexpectedly accepted actual retained WP input')
sys.path.insert(0,str(project))
from swdb.acsl_subset import tokens
ns={'re':re,'tokens':tokens}
exec(compile(ast.fix_missing_locations(ast.Module(body=[helper],type_ignores=[])),str(source),'exec'),ns)
check=ns['assert_original_initialized_register_frame'];check(text)
marker='/* swdb-anchor trust_fixture.contract */'
prefix,unit=text.split(marker)
changes={
 'widened-cell':('__swdb_dx_reg_words [ 0 .. 1 ]','__swdb_dx_reg_words [ 0 .. 2 ]'),
 'omitted-counter':('REG_count , SPD_count , region_count ,','REG_count , SPD_count ,'),
 'changed-counter':('REG_count , SPD_count , region_count ,','REG_count , SPD_count , foreign_count ,'),
 'omitted-cell':(' , __swdb_dx_reg_words [ 0 .. 1 ]',''),
 'extra-location':('__swdb_dx_reg_words [ 0 .. 1 ] ;','__swdb_dx_reg_words [ 0 .. 1 ] , RF_other ;'),
 'duplicate-assigns':('ensures \\result','assigns RF_other; ensures \\result'),
 'misleading-helper-same-frame':('__swdb_dx_reg_words [ 0 .. 1 ]','__swdb_dx_reg_words [ 1 .. 2 ]'),
}
refused=[]
for name,(old,new)in changes.items():
 assert unit.count(old)==1,(name,old)
 changed=prefix+marker+unit.replace(old,new)
 if name=='misleading-helper-same-frame':changed='/*@ assigns REG_count, SPD_count, region_count, __swdb_dx_reg_words[0..1]; */\n'+changed
 try:check(changed)
 except AssertionError:refused.append(name)
 else:raise AssertionError('frame predicate accepted changed target: '+name)
assert len(refused)==7
print(json.dumps({'status':'GREEN','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'retained_wp_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'actual_spacing_accepted':True,'changed_target_refusals':refused,'external_tools_or_tests_executed':False},sort_keys=True))

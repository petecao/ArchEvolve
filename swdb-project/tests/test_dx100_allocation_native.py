"""2026-10-16 ET. Defined software-counter domains and source capacity aborts."""
import json,resource,subprocess
import pytest
from swdb import c_lowering
from testkit.dx100_allocation import STATE,MODEL
from testkit.dx100_allocation_native import counter_source

@pytest.mark.parametrize('initial,width,expected',[(31,1,'31 31 32 32\n'),(30,2,'30 30 32 32\n'),(1,2,'1 1 3 3\n')],ids=['u32-last','u64-last','u64-odd'])
def test_native_allocator_source_and_model_preserve_ids_pairs_and_last_capacity(tmp_path,initial,width,expected):
 outputs=[];commands=[];tool=c_lowering.locate()
 typ='unsigned int'if width==1 else'unsigned long long'
 for language,prefix,tile,reg,tcall,rcall in [
  ('c++',counter_source(),'SPD_count','REG_count','get_new_tile<'+typ+'>()','get_new_reg<'+typ+'>()'),
  ('c','#include <assert.h>\n#define DX_ASSERT(c) assert(c)\n'+STATE+MODEL,'SPD_count','REG_count','get_new_tile_'+typ.replace(' ','_')+'()','get_new_reg_'+typ.replace(' ','_')+'_args0()')]:
  path=tmp_path/('counter.cc'if language=='c++'else'counter.c');exe=tmp_path/('counter-cxx'if language=='c++'else'counter-c')
  path.write_text(prefix+'\n#include <stdio.h>\nint main(void) { init_MAA(); '+tile+'='+str(initial)+'; '+reg+'='+str(initial)+'; int t='+tcall+'; int r='+rcall+'; printf("%d %d %d %d\\n",t,r,'+tile+','+reg+'); return 0; }\n')
  command=[*tool.command,'-x',language,'-std='+('c++17'if language=='c++'else'c11'),'-fsanitize=address,undefined','-fno-sanitize-recover=all',str(path),'-o',str(exe)];commands.append(command)
  build=subprocess.run(command,capture_output=True,text=True);(tmp_path/(language+'.compile.stderr')).write_text(build.stderr)
  assert build.returncode==0,build.stdout+build.stderr
  run=subprocess.run([str(exe)],capture_output=True,text=True)
  (tmp_path/(language+'.stdout')).write_text(run.stdout);(tmp_path/(language+'.stderr')).write_text(run.stderr)
  assert run.returncode==0,run.stdout+run.stderr;outputs.append(run.stdout)
 (tmp_path/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert outputs==[expected,expected]

@pytest.mark.parametrize('family',['tile','reg'])
def test_native_source_capacity33_is_assertion_failure_not_normal_result_or_ub(tmp_path,family):
 source=tmp_path/'capacity.cc';exe=tmp_path/'capacity'
 counter='SPD_count'if family=='tile'else'REG_count'
 source.write_text(counter_source()+'\nint main() { init_MAA(); '+counter+'=32; return get_new_'+family+'<unsigned int>(); }\n')
 command=[*c_lowering.locate().command,'-std=c++17','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(source),'-o',str(exe)]
 build=subprocess.run(command,capture_output=True,text=True);(tmp_path/'compile.stderr').write_text(build.stderr)
 assert build.returncode==0,build.stdout+build.stderr
 def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 run=subprocess.run([str(exe)],capture_output=True,text=True,preexec_fn=no_core)
 (tmp_path/'command.json').write_text(json.dumps(command,indent=2)+'\n');(tmp_path/'stdout').write_text(run.stdout);(tmp_path/'stderr').write_text(run.stderr)
 assert run.returncode!=0 and 'Assertion failed' in run.stderr
 assert 'runtime error:'not in run.stderr and not run.stdout

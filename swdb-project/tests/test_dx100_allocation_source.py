"""2026-10-16 ET. Public original-total software allocator gate, no actual WP."""
import json
from pathlib import Path
import yaml
from testkit.dx100_allocation import prove_allocation,STATEMENT

def test_public_allocator_binds_original_counter_calls_without_hardware_entry_premises(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102)
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert record['verdict']=='not_proven'and record['failure_class']=='tool_crash'
 assert marker.exists(),'explicit exit99 stand-in, no actual formal proof'
 assert record['subject']=={'kind':'library_summary','id':'contract.dx100_software_allocation_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[] and settings['unit_ensures']==[]
 assert settings['correctness_scope']=='original total software-counter unit; no hardware progress premise'
 assert settings['original_assigns_frame']==['REG_count','SPD_count','region_count']
 assert {c['call']for c in settings['source_definitions']}=={'init_MAA','get_new_tile','get_new_reg'}
 assert STATEMENT in [a['sentence']for a in record['assumptions']]
 assert not any('as if it finished at issue'in a['sentence']or 'fresh-SPD'in a['sentence']for a in record['assumptions'])
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 assert r'terminates \false'not in Path(wp['path']).read_text()
 # Compile and execute exact public generated C with its declared model bodies;
 # the independent original C++ source/header supplies the expected behavior.
 import subprocess
 from swdb import c_lowering
 from testkit.dx100_allocation import MODEL
 from conftest import REPO
 tool=c_lowering.locate();commands=[];outputs=[]
 from testkit.dx100_allocation_native import counter_source
 from testkit.dx100_allocation import CANONICAL_CALLER
 original=counter_source()+CANONICAL_CALLER
 for language,body,counters in [('c++',original,'SPD_count,REG_count,(int)region_count'),('c',Path(wp['path']).read_text()+'\n#include <assert.h>\n#define DX_ASSERT(c) assert(c)\n'+MODEL,'SPD_count,REG_count,region_count')]:
  source=tmp_path/('native.cc'if language=='c++'else'native.c');exe=tmp_path/('native-cxx'if language=='c++'else'native-c')
  source.write_text(body+'\n#include <stdio.h>\nint main(void) { int result=trust_fixture(); printf("%d %d %d %d\\n",result,'+counters+'); return 0; }\n')
  command=[*tool.command,'-x',language,'-std='+('c++17'if language=='c++'else'c11'),'-I'+str(tmp_path/'library/proof_units'),'-fsanitize=address,undefined','-fno-sanitize-recover=all',str(source),'-o',str(exe)]
  commands.append(command);compiled=subprocess.run(command,capture_output=True,text=True)
  (tmp_path/(language+'.compile.stderr')).write_text(compiled.stderr)
  assert compiled.returncode==0,compiled.stdout+compiled.stderr
  run=subprocess.run([str(exe)],capture_output=True,text=True)
  (tmp_path/(language+'.stdout')).write_text(run.stdout);(tmp_path/(language+'.stderr')).write_text(run.stderr)
  assert run.returncode==0,run.stdout+run.stderr
  outputs.append(run.stdout)
 (tmp_path/'native-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 assert outputs==['102 3 3 6\n']*2

import pytest
@pytest.mark.parametrize('change',['removed-reset','assertions-disabled','initialized-overload','changed-model','changed-contract'],ids=str)
def test_allocator_refuses_unbound_source_assertions_overload_or_model_before_adapter(tmp_path,change):
 from testkit.dx100_allocation import CANONICAL_CALLER
 from conftest import REPO
 source='#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+CANONICAL_CALLER
 if change=='removed-reset':source=source.replace('init_MAA();','')
 elif change=='assertions-disabled':source='#define NDEBUG\n'+source
 elif change=='initialized-overload':source=source.replace('get_new_reg<unsigned int>()','get_new_reg<unsigned int>(7U)')
 def mutate(data,library):
  if change=='changed-model':
   import hashlib
   pin=data['model']['c'];p=library/pin['path'];p.write_text(p.read_text().replace(' += width;',' += 0;',1));pin['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  elif change=='changed-contract':
   v=next(r for r in data['calls']if r['call']=='get_new_tile')['instances'][0]
   v['contract']=v['contract'].replace('<= 31','<= 32')
 result,records,entry,marker=prove_allocation(tmp_path,102,source=source,mutate=mutate)
 (tmp_path/'refusal.stdout').write_text(result.stdout);(tmp_path/'refusal.stderr').write_text(result.stderr)
 assert result.returncode!=0,result.stdout+result.stderr
 assert not marker.exists()
 assert not list((tmp_path/'runs').glob('**/wp_input.c'))


def test_allocator_original_assigns_nothing_is_refused_instead_of_silently_widened(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102,frame=r'\nothing')
 assert result.returncode!=0,result.stdout+result.stderr
 assert 'explicit original software-counter assigns frame'in result.stdout+result.stderr
 assert not marker.exists()

def test_correct_and_wrong_counter_contracts_keep_original_source_and_model_unchanged(tmp_path):
 sources=[];models=[]
 for expected in [102,101]:
  root=tmp_path/str(expected);root.mkdir()
  result,records,entry,marker=prove_allocation(root,expected)
  assert result.returncode==0,result.stdout+result.stderr
  record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
  assert record['verdict']=='not_proven'and record['failure_class']=='tool_crash'and marker.exists()
  sources.append((root/'library/proof_units/trust.cc').read_bytes())
  models.append((root/'library/proof_semantics/software-allocation/model.h').read_bytes())
  wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
  assert 'ensures \\result == '+str(expected)+';'in Path(wp['path']).read_text()
 assert sources[0]==sources[1]and models[0]==models[1]


def test_closed_allocator_cbmc_route_refuses_before_any_formal_adapter_invocation(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102,adapter='cbmc')
 assert result.returncode!=0,result.stdout+result.stderr
 assert 'software allocator fixture is admitted only through its WP route'in result.stdout+result.stderr
 assert not marker.exists()

"""2026-10-16 ET. Public original-partial register source/record controls."""
import json
from pathlib import Path
import yaml
from testkit.dx100_register import prove_register,STATEMENT

def test_public_source_register_roundtrip_uses_original_partial_policy_and_frame(tmp_path):
 result,records,entry,marker=prove_register(tmp_path,711)
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert marker.exists()and record['verdict']=='not_proven'and record['failure_class']=='tool_crash'
 assert record['subject']=={'kind':'partial_library_summary','id':'contract.dx100_register_partial_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 assert settings['original_assigns_frame']==['__swdb_dx_reg_words[0..1]']
 assert {c['call']for c in settings['source_definitions']}=={'get_reg','set_reg'}
 assert STATEMENT in [a['sentence']for a in record['assumptions']]
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 text=Path(wp['path']).read_text()
 compact=''.join(text.split())
 assert r'terminates\false;'in compact and r'ensures\result==711;'in compact
 assert 'assigns__swdb_dx_reg_words[0..1];'in compact
 from conftest import REPO
 bundle=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-register-parser/inputs/wp-correct.c'
 assert Path(wp['path']).read_bytes()==bundle.read_bytes(),'current normal public input must exactly match the inert parser bundle'

 # Independent exact RF class/constructor excerpt and ordinary public C model.
 # This checks finite scalar value projection, not CPU/device transport/fences.
 import subprocess
 from conftest import REPO
 from swdb import c_lowering,stdlib_provenance
 from testkit.dx100_register import MODEL
 from testkit.dx100_size_native import pin
 excerpt=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics/checks/rf-source-excerpt.hpp'
 reference='#include <cstdint>\n#include <cstdlib>\n#include <cassert>\n'+excerpt.read_text()+'\nint trust_fixture() { gem5::RF rf(32); rf.setData<uint32_t>(0,7U); rf.setData<uint32_t>(1,11U); return (int)(100U*rf.getData<uint32_t>(0)+rf.getData<uint32_t>(1)); }\n'
 tool=c_lowering.locate();commands=[];outputs=[];units=[]
 for language,body in [('c++',reference),('c',text+'\n#include <assert.h>\n#define DX_ASSERT(c) assert(c)\n'+MODEL)]:
  src=tmp_path/('reference.cc'if language=='c++'else'public.c');exe=tmp_path/('reference-cxx'if language=='c++'else'public-c');dep=src.with_suffix('.d')
  src.write_text(body+'\n#include <stdio.h>\nint main(void) { printf("%d\\n",trust_fixture()); return 0; }\n')
  cmd=[*tool.command,'-x',language,'-std='+('c++17'if language=='c++'else'c11'),'-fsanitize=address,undefined','-fno-sanitize-recover=all','-MD','-MF',str(dep),str(src),'-o',str(exe)]
  commands.append(cmd);build=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
  (tmp_path/(language+'.compile.stderr')).write_text(build.stderr)
  assert build.returncode==0,build.stdout+build.stderr
  ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
  (tmp_path/(language+'.stdout')).write_text(ran.stdout);(tmp_path/(language+'.stderr')).write_text(ran.stderr)
  assert ran.returncode==0,ran.stdout+ran.stderr
  outputs.append(ran.stdout);units.extend([pin(src),pin(exe),pin(dep)])
 (tmp_path/'native-scalar-receipt.json').write_text(json.dumps({'commands':commands,'outputs':outputs,'units':units,'RF_excerpt':pin(excerpt),'runtime':stdlib_provenance.runtime_identity(tool),'scope':'Finite source RF scalar effects versus public C; no actual MMIO/fence/transport/proof'},indent=2)+'\n')
 assert outputs==['711\n','711\n']

import pytest
@pytest.mark.parametrize('change',['missing-certificate','interference','model','u64','source-fence','caller-index','original-total','frame'])
def test_register_refuses_unbound_entry_source_type_model_or_original_unit_policy(tmp_path,change):
 from testkit.dx100_register import CALLER
 from conftest import REPO
 source='#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+CALLER
 if change=='u64':source=source.replace('unsigned int','unsigned long long')
 if change=='source-fence':source='#define __volatile__\n'+source
 if change=='caller-index':source=source.replace('(1,11U)','(32,11U)')
 def mutate(data,library):
  import hashlib
  if change=='interference':
   for row in data['calls']:
    for variant in row.get('instances',[]):variant['definition']['entry']['interference']='other-core writes allowed'
  if change=='model':
   pin=data['model']['c'];p=library/pin['path'];p.write_text(p.read_text().replace('[reg_id]=data','[0]=data'));pin['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 result,records,entry,marker=prove_register(tmp_path,711,source=source,mutate=mutate,certificate=change!='missing-certificate',partial=change!='original-total',frame=r'\nothing'if change=='frame'else'__swdb_dx_reg_words[0..1]')
 (tmp_path/'refusal.stdout').write_text(result.stdout);(tmp_path/'refusal.stderr').write_text(result.stderr)
 assert result.returncode!=0,result.stdout+result.stderr
 assert not marker.exists(),'refusal must precede any verifier stand-in'


def test_wrong_crossregister_result_keeps_source_model_and_frame_identical(tmp_path):
 sources=[];models=[];contracts=[]
 for expected in [711,1107]:
  root=tmp_path/str(expected);root.mkdir()
  result,records,entry,marker=prove_register(root,expected)
  assert result.returncode==0,result.stdout+result.stderr
  record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
  assert marker.exists()and record['failure_class']=='tool_crash'and record['verdict']=='not_proven'
  sources.append((root/'library/proof_units/trust.cc').read_bytes())
  models.append((root/'library/proof_semantics/u32-register/model.h').read_bytes())
  contracts.append((root/'library/rewrite_contracts/trust.yaml').read_text())
  assert record['settings']['proof_semantics']['original_assigns_frame']==['__swdb_dx_reg_words[0..1]']
 assert sources[0]==sources[1]and models[0]==models[1]
 assert contracts[0].replace('711','1107')==contracts[1]


def test_rehashed_register_llvm_fence_mutation_is_rechecked_before_use(tmp_path):
 import copy,hashlib
 from types import SimpleNamespace
 from swdb import dx100_register_source
 result,records,entry,marker=prove_register(tmp_path,711)
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 for change in ('fence','missing-operation'):
  certificate=copy.deepcopy(record['settings']['proof_semantics']['source_definitions'][0])
  function=certificate['operations']['set']['source']
  replacement=function.replace('mfence;','nop;',1)if change=='fence'else''
  certificate['llvm_module']=certificate['llvm_module'].replace(function,replacement,1)
  certificate['llvm_module_sha256']=hashlib.sha256(certificate['llvm_module'].encode()).hexdigest()
  with pytest.raises(dx100_register_source.Refused):
   dx100_register_source.recheck(SimpleNamespace(summaries=[{'semantic_source':certificate}]))


@pytest.mark.parametrize('malformed',[None,[],True])
def test_malformed_original_partial_policy_refuses_without_validation_traceback(tmp_path,malformed):
 def change(contract):contract['proof_unit']['correctness_policy']=malformed
 result,records,entry,marker=prove_register(tmp_path,711,contract_mutate=change)
 diagnostic=result.stdout+result.stderr
 assert result.returncode!=0 and not marker.exists()
 assert 'Traceback'not in diagnostic,diagnostic
 assert 'correctness_policy'in diagnostic,diagnostic

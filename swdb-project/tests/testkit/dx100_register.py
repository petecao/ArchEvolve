"""2026-10-16 ET. Original partial, isolated u32 register observation fixture."""
import hashlib,json,shutil
from conftest import FIXTURES,REPO
from testkit.dx100_selector import pure_selector,read_actual_lineup,bind_actual_lineup
from testkit.dx100_trust import run_semantics_fixture

from swdb.dx100_register_model import OWNER,ENTRY,STATEMENT,CALLER,STATE,PROTOTYPES,CONTRACTS,MODEL

def register_semantics(data,library,*,certificate=True):
 pure_selector(data,library)
 data.update(id='semantics.dx100_register_fixture_0_2',description='One original-partial u32 register roundtrip, no current0.2.')
 data['rules']=[r for r in data['rules']if r['id']not in ('selector_value','selector_scope')]
 data['rules'] += [{'id':'register_scope','statement':STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True},
 {'id':'register_source','statement':'Typed CPU scalar writes are queued; dispatch updates RF before its response. A scalar read copies the selected RF bytes. IF stalls register writes only on matching explicit IDs.',
 'cites':{'gem5_commit':'e4fc4afdf894f295442cef3604667a469fab8e62','path':'src/mem/MAA/CpuSidePort.cc','lines':'112-150,317-332'}}]
 folder=library/'proof_semantics/u32-register';folder.mkdir()
 sources=[]
 from swdb.dx100_size_source import SOURCE_PINS
 from swdb.dx100_interface import HEADERS
 for name,digest in SOURCE_PINS.items():
  if name in HEADERS:
   sources.append({'root':'project','path':'apps/dx100/benchmarks/API/'+name,'sha256':digest});continue
  p=folder/name;shutil.copyfile(FIXTURES/'proof/dx100/gem5-e4fc4af'/name,p)
  sources.append({'root':'library','path':str(p.relative_to(library)),'sha256':digest})
 for row in data['calls']:
  name=row['call'];overloads=row.get('overloads');row.clear();row.update(call=name,rules=['register_scope','register_source'])
  if name in PROTOTYPES:
   definition={'kind':'dx100-u32-register-v1','call':name,'sources':sources}
   if certificate:definition['entry']=json.loads(json.dumps(ENTRY))
   row.update(supported=True,instances=[{'arguments':['unsigned int'],'arity':2 if name=='set_reg'else 1,'prototype':PROTOTYPES[name],'contract':CONTRACTS[name],'definition':definition}])
  else:
   row.update(supported=False,prototype='int '+name+'(void)',contract=r'requires \false; assigns \nothing;')
   if overloads:row['overloads']=overloads
 def pin(name,text):
  p=folder/name;p.write_text(text)
  return {'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 data['model']={'layout':'dx100-u32-register-partial-v1','state':pin('state.h',STATE),'logic':pin('logic.acsl','/* No added axioms. */\n'),'c':pin('model.h',MODEL)}
 data['ghost']={'acsl':pin('ghost.acsl','/* Ordinary register-word projection. */\n')}

def prove_register(tmp_path,expected,*,certificate=True,source=None,mutate=None,actual=False,partial=True,frame='__swdb_dx_reg_words[0..1]',contract_mutate=None):
 lineup=read_actual_lineup()if actual else None
 source=source or '#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+CALLER
 def build(data,library):
  register_semantics(data,library,certificate=certificate)
  if mutate is not None:mutate(data,library)
 def contract_only(contract):
  contract['proof_unit'].pop('array_domains',None);contract['concurrency_frame']=[]
  if partial:
   entry=tmp_path/'library/proof_semantics/dx100_trust_fixture.yaml'
   contract.update(id='contract.dx100_register_partial_fixture.v1',version='0.1')
   contract['proof_unit']['correctness_policy']={'kind':'partial-normal-return-v1','source_policy':'dx100-u32-register-v1','semantics':{'id':'semantics.dx100_register_fixture_0_2','sha256':hashlib.sha256(entry.read_bytes()).hexdigest()}}
  if contract_mutate is not None:contract_mutate(contract)
 def method_only(method):
  method['id']='method.dx100-register-partial-fixture-v1'if partial else'method.dx100-register-total-refusal-v1'
  if actual:bind_actual_lineup(method,lineup)
 return run_semantics_fixture(tmp_path,'wp',source=source,semantics_transform=build,contract_transform=contract_only,method_transform=method_only,tool_environment={}if actual else None,
  source_files={'gem5/m5ops.h':'#pragma once\n#include <stdint.h>\nextern "C" void m5_add_mem_region(void*,void*,uint64_t);\nextern "C" void m5_clear_mem_region(void);\n'},
  postcondition='assigns '+frame+r'; ensures \result == '+str(expected)+';')

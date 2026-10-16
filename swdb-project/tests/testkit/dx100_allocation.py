"""2026-10-16 ET. Closed pure software-counter allocation fixture, no MMIO."""
import hashlib,json
from conftest import REPO
from testkit.dx100_selector import pure_selector
from testkit.dx100_trust import run_semantics_fixture

from swdb.dx100_allocation_source import (KIND,LAYOUT,OWNER,STATEMENT,STATE,CONTRACTS,PROTOTYPES,MODEL,CANONICAL_CALLER)


def allocation_semantics(data,library):
 pure_selector(data,library)
 data.update(id='semantics.dx100_allocation_fixture_0_2',description='Closed original-total software allocation caller; all hardware operations unsupported.')
 data['rules']=[r for r in data['rules']if r['id']not in ('selector_value','selector_scope')]
 data['rules'] += [{'id':'software_allocation_source','statement':'init_MAA resets only allocation counters; each source allocator returns the current counter, adds sizeof(T)/sizeof(uint32_t), and asserts the source bound.',
  'cites':{'gem5_commit':'e4fc4afdf894f295442cef3604667a469fab8e62','path':'benchmarks/API/MAA_gem5.hpp','lines':'93-144'}},
  {'id':'software_allocation_scope','statement':STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True}]
 from swdb.dx100_interface import HEADERS
 sources=[{'root':'project','path':'apps/dx100/benchmarks/API/'+name,'sha256':digest}for name,digest in HEADERS.items()]
 def definition(call):return {'kind':KIND,'call':call,'sources':sources}
 for row in data['calls']:
  name=row['call'];old_overloads=row.get('overloads');row.clear()
  row.update(call=name,rules=['software_allocation_source','software_allocation_scope'])
  if name=='init_MAA':row.update(supported=True,prototype=PROTOTYPES[name],contract=CONTRACTS[name],definition=definition(name))
  elif name in ('get_new_tile','get_new_reg'):
   instances=[]
   for argument,suffix in [('unsigned int','unsigned_int'),('unsigned long long','unsigned_long_long')]:
    symbol=name+'_'+suffix+('_args0'if name=='get_new_reg'else '')
    variant={'arguments':[argument],'arity':0,'prototype':PROTOTYPES[symbol],'contract':CONTRACTS[symbol],'definition':definition(name)}
    if name=='get_new_reg':variant['declaration']='inline int get_new_reg()'
    instances.append(variant)
   if name=='get_new_reg':
    instances.append({'arguments':['unsigned int'],'arity':1,'declaration':'inline int get_new_reg(T1 data)',
     'prototype':'int get_new_reg_unsigned_int_args1(unsigned int data)','contract':r'requires \false; assigns \nothing;'})
   row.update(supported=True,instances=instances)
  else:
   row.update(supported=False,prototype='int '+name+'(void)',contract=r'requires \false; assigns \nothing;')
   if old_overloads:row['overloads']=old_overloads
 folder=library/'proof_semantics/software-allocation';folder.mkdir()
 def pin(name,text):
  p=folder/name;p.write_text(text)
  return {'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 data['model']={'layout':LAYOUT,'state':pin('state.h',STATE),'logic':pin('logic.acsl','/* No added axioms. */\n'),'c':pin('model.h',MODEL)}
 data['ghost']={'acsl':pin('ghost.acsl','/* Only ordinary software counters, no hardware state. */\n')}

def prove_allocation(tmp_path,expected,*,source=None,mutate=None,frame="REG_count, SPD_count, region_count",actual=False,adapter="wp"):
 from testkit.dx100_selector import read_actual_lineup,bind_actual_lineup
 lineup=read_actual_lineup()if actual else None
 source=source or ('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+CANONICAL_CALLER)
 def transform(data,library):
  allocation_semantics(data,library)
  if mutate is not None:mutate(data,library)
 def contract_only(contract):
  contract.update(id='contract.dx100_software_allocation_fixture.v1',version='0.1')
  contract['proof_unit'].pop('array_domains',None);contract['concurrency_frame']=[]
 def method_only(method):
  method['id']='method.dx100-software-allocation-fixture-v1'
  if actual:bind_actual_lineup(method,lineup)
 return run_semantics_fixture(tmp_path,adapter,source=source,semantics_transform=transform,
  contract_transform=contract_only,method_transform=method_only,tool_environment={}if actual else None,
  source_files={'gem5/m5ops.h':'#pragma once\n#include <stdint.h>\nextern "C" void m5_add_mem_region(void*,void*,uint64_t);\nextern "C" void m5_clear_mem_region(void);\n'},
  postcondition='assigns '+frame+r'; ensures \result == '+str(expected)+';')

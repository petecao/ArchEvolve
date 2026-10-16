"""2026-10-16 ET. Closed partial-return stream fixture; no current0.2."""
import hashlib,json,shutil
from conftest import FIXTURES,REPO
from testkit.dx100_selector import pure_selector
from testkit.dx100_trust import run_semantics_fixture

OWNER='Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
ENTRY={'kind':'isolated-one-u32-stream-core0-v1','core':0,'tiles':32,'tile_words':16384,'register_words':32,
 'guest_address_bits':64,'byte_order':'little','rf_i32':{'0':0,'1':1,'2':1},
 'epoch':'after-constructor-and-configured-quiescent-RF-before-one-command',
 'input':{'symbol':'stream_input','bytes':64,'alignment':64,'storage':'initialized C static array',
          'region':'registered normal-memory line disjoint from MMIO','translation':'stable synchronous fault-free64-byte mapping',
          'visibility':'coherent stable full physical line; no competing CPU/device writes from any core through return'},
 'commands':'exactly one u32 stream load, no condition or competing command'}
BOOT_STATEMENT=('This synthetic core0 unit starts with the pinned32-tile/16384-word SPD constructor state and configured4-core MMIO mapping, '
 'quiescent initialized signed-int32 RF values0/1/1 at registers0/1/2, and one registered initialized64-byte aligned normal-memory input line '
 'with stable synchronous fault-free translation and coherent no-interference visibility through normal return. '
 'These are conditional environment/source-model premises owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59); '
 'alloc/init do not establish them and arbitrary callers or physical boot are not established.')
NORMAL_RETURN_STATEMENT=('All three MMIO helpers and this source unit are interpreted only on normal return; no termination, fairness or hardware-liveness theorem is claimed.')
COMPRESSION_STATEMENT=('An acknowledgement establishes dispatch, not completion or still-unfinished hardware. In this isolated no-observation/no-interference caller, '
 'unobserved device events may be represented by a logically uncovered command and settled only at the returned real ready read; '
 'this source-model correspondence is owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59). All-schedule event refinement and contract/body agreement remain unverified owned TCB duties, not conclusions of finite native prefixes.')


def stream_semantics(data,library,*,certificate=True):
    from swdb.dx100_stream_model import normal_return_model
    pure_selector(data,library);model=normal_return_model()
    data.update(id='semantics.dx100_stream_fixture_0_2',description='One source-bound u32 stream metadata observation on conditional normal return.')
    data['rules']=[r for r in data['rules'] if r['id'] not in ('selector_value','selector_scope')]
    data['rules'] += [
      {'id':'stream_epoch','statement':BOOT_STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True},
      {'id':'stream_normal_return','statement':NORMAL_RETURN_STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True},
      {'id':'stream_event_compression','statement':COMPRESSION_STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True},
      {'id':'stream_count_response','statement':'For defined signed-int RF0/1/1, the nonempty u32 stream has one lane; a matched completed response sets starting-tile size1 before Finished/ready restoration.',
       'cites':{'gem5_commit':'e4fc4afdf894f295442cef3604667a469fab8e62','path':'src/mem/MAA/StreamAccess.cc','lines':'138-342'}},
      {'id':'stream_scope','statement':'Only the unchanged one-command stream/wait/size synthetic caller is admitted; no payload CPU read or full interface acceptance.', 'assumed':{'owner':OWNER}}]
    folder=library/'proof_semantics/one-u32-stream';folder.mkdir()
    sources=[]
    for sub in ('gem5-e4fc4af','gem5-e4fc4af-stream'):
      for source in sorted((FIXTURES/'proof/dx100'/sub).glob('*')):
        if source.suffix not in ('.cc','.hh'):continue
        p=folder/source.name;shutil.copyfile(source,p)
        sources.append({'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    from swdb.dx100_interface import HEADERS
    sources += [{'root':'project','path':'apps/dx100/benchmarks/API/'+name,'sha256':digest} for name,digest in HEADERS.items()]
    def definition(role):
      result={'kind':'dx100-one-u32-stream-v1','call':role,'sources':sources}
      if certificate:result['entry']=json.loads(json.dumps(ENTRY))
      return result
    for row in data['calls']:
      name=row['call'];overloads=row.get('overloads');row.clear()
      rules=['stream_epoch','stream_normal_return','stream_event_compression','stream_count_response']
      if name=='maa_stream_load':
        row.update(call=name,supported=True,instances=[{'arguments':['unsigned int'],'arity':6,
            'prototype':'void maa_stream_load_unsigned_int(unsigned int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile)',
            'contract':model['contracts']['maa_stream_load_unsigned_int'],'definition':definition(name)}],rules=rules)
      elif name in ('wait_ready','get_tile_size'):
        row.update(call=name,supported=True,prototype=('void wait_ready(int SPD_id)' if name=='wait_ready' else 'volatile unsigned short get_tile_size(int SPD_id)'),
            contract=model['contracts'][name],rules=rules,definition=definition(name))
      else:
        row.update(call=name,supported=False,prototype='int '+name+'(void)',contract=r'requires \false; assigns \nothing;',rules=['stream_scope'])
        if overloads:row['overloads']=overloads
    def pin(name,text):
      p=folder/name;p.write_text(text)
      return {'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    data['model']={'layout':'dx100-one-u32-stream-partial-v1','state':pin('state.h',model['state']),
        'logic':pin('logic.acsl','/* No added axioms. */\n'),'c':pin('model.h',model['c'])}
    data['ghost']={'acsl':pin('ghost.acsl','/* Ordinary private metadata projection only. */\n')}


def prove_stream(tmp_path,expected,*,certificate=True,source=None,mutate=None,actual=False,partial=True,contract_mutate=None,method_mutate=None):
    from testkit.dx100_selector import read_actual_lineup,bind_actual_lineup
    lineup=read_actual_lineup() if actual else None
    source=source or ('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'
        'alignas(64) uint32_t stream_input[16]={7};\n'
        'int trust_fixture() { maa_stream_load<uint32_t>(stream_input,0,1,2,0,-1); wait_ready(0); int observed=(int)get_tile_size(0); return observed; }\n')
    def contract_only(contract):
      contract['proof_unit'].pop('array_domains',None);contract['concurrency_frame']=[]
      if partial:
        entry=tmp_path/'library/proof_semantics/dx100_trust_fixture.yaml'
        contract.update(id='contract.dx100_stream_partial_fixture.v1',version='0.1')
        contract['proof_unit']['correctness_policy']={'kind':'partial-normal-return-v1',
            'source_policy':'dx100-one-u32-stream-v1',
            'semantics':{'id':'semantics.dx100_stream_fixture_0_2','sha256':hashlib.sha256(entry.read_bytes()).hexdigest()}}
      if contract_mutate is not None:contract_mutate(contract)
    def build(data,library):
      stream_semantics(data,library,certificate=certificate)
      if mutate is not None:mutate(data,library)
    def method_only(method):
      method['id']='method.dx100-stream-partial-fixture-v1' if partial else 'method.dx100-stream-total-refusal-v1'
      if actual:bind_actual_lineup(method,lineup)
      if method_mutate is not None:method_mutate(method)
    return run_semantics_fixture(tmp_path,'wp',source=source,semantics_transform=build,
      tool_environment={} if actual else None,method_transform=method_only,contract_transform=contract_only,
      source_files={'gem5/m5ops.h':'#pragma once\n#include <stdint.h>\nextern "C" void m5_add_mem_region(void*,void*,uint64_t);\nextern "C" void m5_clear_mem_region(void);\n'},
      postcondition=r'assigns \nothing; ensures \result == '+str(expected)+';')

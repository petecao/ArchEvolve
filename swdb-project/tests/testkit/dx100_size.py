"""2026-10-16 ET. Closed synthetic-boot source getter fixture, not current0.2."""
import hashlib
import json
import shutil

from conftest import FIXTURES,REPO
from testkit.dx100_selector import pure_selector
from testkit.dx100_trust import run_semantics_fixture

BOOT={'kind':'synthetic-fresh-spd-core0-v1','core':0,'tiles':32,'tile_words':16384,
      'guest_address_bits':64,'byte_order':'little','epoch':'after-constructor-and-address-setup-before-any-command'}
OWNER='Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
BOOT_STATEMENT=('This synthetic fixture begins on core0 immediately after one pinned SPD constructor has completed '
    'with 32 tiles and 16,384 words per tile, and pinned 4-core MMIO-address setup has configured its globals, before commands or other accesses modify '
    'that instance. This is a conditional environment/source-model premise owned by the Probata '
    'proof-semantics maintainer, pending Yan-Ru freeze review (59); arbitrary callers and physical boot '
    'are not established. alloc_MAA/init_MAA do not establish freshness.')
PROTOTYPE='volatile unsigned short get_tile_size(int SPD_id)'
CONTRACT=(r'requires 0 <= SPD_id < 32; assigns \nothing; ensures \result == '
          r'__swdb_dx_size_bytes[2*SPD_id] + 256*__swdb_dx_size_bytes[2*SPD_id+1];')
STATE='static unsigned char __swdb_dx_size_bytes[64];\n'
MODEL=('volatile unsigned short get_tile_size(int SPD_id) {\n'
       '  DX_ASSERT(0 <= SPD_id && SPD_id < 32);\n'
       '  return (unsigned short)(__swdb_dx_size_bytes[2*SPD_id] + 256U*__swdb_dx_size_bytes[2*SPD_id+1]);\n}\n')


def size_semantics(data,library,*,certificate=True):
    pure_selector(data,library)
    data.update(id='semantics.dx100_size_fixture_0_2',description='Synthetic fresh-SPD size getter only; conditional boot epoch.')
    data['rules']=[r for r in data['rules'] if r['id'] not in ('selector_value','selector_scope')]
    data['rules'] += [
        {'id':'fresh_spd_epoch','statement':BOOT_STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True},
        {'id':'size_response','statement':'The core0 aligneduint16 size-range read returns the Finished tile size without covering commands.',
         'cites':{'gem5_commit':'e4fc4afdf894f295442cef3604667a469fab8e62','path':'src/mem/MAA/CpuSidePort.cc','lines':'278-294'}},
        {'id':'size_scope','statement':'Only the source-bound fresh-SPD size getter is supported in this synthetic boot epoch.',
         'assumed':{'owner':OWNER}}]
    folder=library/'proof_semantics/fresh-spd-size';folder.mkdir()
    sources=[]
    for source in sorted(p for p in (FIXTURES/'proof/dx100/gem5-e4fc4af').glob('*') if p.suffix in ('.cc','.hh')):
        p=folder/source.name;shutil.copyfile(source,p)
        sources.append({'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    from swdb.dx100_interface import HEADERS
    sources += [{'root':'project','path':'apps/dx100/benchmarks/API/'+name,'sha256':digest} for name,digest in HEADERS.items()]
    definition={'kind':'dx100-get-tile-size-v1','sources':sources}
    if certificate:definition['entry']=dict(BOOT)
    for row in data['calls']:
        if row['call']=='get_tile_size':
            row.clear();row.update(call='get_tile_size',supported=True,prototype=PROTOTYPE,contract=CONTRACT,
                                   rules=['fresh_spd_epoch','size_response'],definition=definition)
        else:
            name=row['call'];overloads=row.get('overloads');row.clear()
            row.update(call=name,supported=False,prototype='int '+name+'(void)',contract=r'requires \false; assigns \nothing;',rules=['size_scope'])
            if overloads:row['overloads']=overloads
    def pin(name,text):
        p=folder/name;p.write_text(text)
        return {'root':'library','path':str(p.relative_to(library)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    data['model']={'layout':'dx100-fresh-spd-size-v1','state':pin('state.h',STATE),
                   'logic':pin('logic.acsl','/* No added axioms. */\n'),'c':pin('model.h',MODEL)}
    data['ghost']={'acsl':pin('ghost.acsl','/* Ordinary private model state only. */\n')}


def prove_size(tmp_path,expected,*,certificate=True,source=None,mutate=None,actual=False):
    from testkit.dx100_selector import read_actual_lineup,bind_actual_lineup
    lineup=read_actual_lineup() if actual else None
    source=source or ('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+
                      '\nint trust_fixture() { int observed=(int)get_tile_size(0); return observed; }\n')
    def contract_only(contract):
        contract['proof_unit'].pop('array_domains',None);contract['concurrency_frame']=[]
    def build(data,library):
        size_semantics(data,library,certificate=certificate)
        if mutate is not None:mutate(data,library)
    def method_only(method):
        method['id']='method.dx100-size-fixture-0-2'
        if actual:bind_actual_lineup(method,lineup)
    return run_semantics_fixture(tmp_path,'wp',source=source,
        semantics_transform=build,tool_environment={} if actual else None,
        method_transform=method_only,
        contract_transform=contract_only,
        source_files={'gem5/m5ops.h':'#pragma once\n#include <stdint.h>\nextern "C" void m5_add_mem_region(void*,void*,uint64_t);\nextern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == '+str(expected)+';')

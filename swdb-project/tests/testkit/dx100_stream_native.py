"""2026-10-16 ET. Independent exact-SPD excerpt/stream metadata finite controls.

C11 transition kernel and C++17 source excerpts compile separately. No simulator,
MMIO/coherence/RT/event scheduler or object-lifetime theorem is established.
"""
import hashlib,json,os,shlex,subprocess
from pathlib import Path
from conftest import FIXTURES
from swdb import c_lowering,dx100_size_source,stdlib_provenance
from testkit.dx100_size_native import function,pin


def run_spd_transitions(tmp_path,kernel):
    folder=FIXTURES/'proof/dx100/gem5-e4fc4af'
    for name in ('SPD.cc','SPD.hh'):
        assert pin(folder/name)['sha256']==dx100_size_source.SOURCE_PINS[name]
    source=(folder/'SPD.cc').read_text();header=(folder/'SPD.hh').read_text()
    start=source.index('    tiles_data = new uint8_t[num_tiles * num_tile_elements * sizeof(uint32_t)];')
    stop=source.index('    waiting_units_funcs = new std::vector<uint8_t>[num_tiles];',start)
    constructor=source[start:stop]+'    memset(tiles_data, 0, num_tiles * num_tile_elements * sizeof(uint32_t));\n'
    methods=[function(source,s) for s in ('SPD::TileStatus SPD::getTileStatus(int tile_id)',
       'void SPD::setTileIdle(int tile_id, int word_size)','void SPD::setTileService(int tile_id, int word_size)',
       'void SPD::setTileFinished(int tile_id, int word_size)','void SPD::setTileReady(int tile_id, int word_size)',
       'void SPD::setTileNotReady(int tile_id, int word_size)','bool SPD::getTileReady(int tile_id)',
       'uint16_t SPD::getSize(int tile_id)','void SPD::setSize(int tile_id, uint16_t size)')]
    checks=[function(header,s) for s in ('void check_tile_id(int tile_id, int word_size)',
        'void check_tile_element_id(int tile_id, int element_id, int word_size)',
        'void setData(int tile_id, int element_id, T _data)')]
    observation='struct Obs { unsigned status,ready,size,lane0,others,initialized; uint32_t word; };\n'
    c=tmp_path/'kernel.c';obj=tmp_path/'kernel.o';cpp=tmp_path/'reference.cpp';exe=tmp_path/'reference.bin'
    c.write_text(kernel+'\n'+observation+r'''
int projected_trace(unsigned step,struct Obs *out) {
 struct dxl_state s;uint32_t input[16]={7};
 if(dxl_fresh(&s,UINT64_C(0x1000),UINT64_C(0x2000)) || dxl_bind_input(&s,input,16)) return 1;
 if(step>=1 && (dxl_packet(&s,0,UINT64_C(0x00ff00ff)) || dxl_packet(&s,1,UINT64_C(0xffffffff000102ff)) ||
    dxl_packet(&s,2,UINT64_C(0x1000)) || dxl_dispatch(&s))) return 2;
 if(step>=2 && dxl_start(&s,0,1,1)) return 3;
 if(step>=3 && dxl_request(&s,UINT64_C(0x2000),64,0,0)) return 4;
 if(step>=4 && dxl_response(&s,UINT64_C(0x2000),64,0,0,7)) return 5;
 if(step>=5 && dxl_finish(&s,1,1)) return 6;
 *out=(struct Obs){s.tile_status,s.ready,s.size,s.lane0_finished,s.other_lanes_finished,s.payload_initialized,s.payload0};
 return 0;
}
''')
    cpp.write_text('''#include <cstdint>
#include <cassert>
#include <cstring>
#include <algorithm>
#define panic_if(c,...) assert(!(c))
#define DPRINTF(...) ((void)0)
'''+observation+'''
extern "C" int projected_trace(unsigned,Obs*);
struct SPD {
 enum class TileStatus : uint8_t { Idle=0,Service=1,Finished=2,MAX };
 unsigned num_tiles=32,num_tile_elements=16384;
 uint8_t *tiles_data,*tiles_ready;TileStatus *tiles_status;
 bool *tiles_dirty,*element_finished;uint16_t *tiles_size;
 SPD() {\n'''+constructor+'''
 }
 ~SPD(){delete[] tiles_data;delete[] tiles_ready;delete[] tiles_status;delete[] tiles_dirty;delete[] tiles_size;delete[] element_finished;}
 void wakeup_waiting_units(int) {} // Scheduler side effects omitted; metadata comparison only.
'''+checks[0]+'\n'+checks[1]+'\ntemplate<typename T>\n'+checks[2]+'''
 TileStatus getTileStatus(int);
 void setTileIdle(int,int);void setTileService(int,int);void setTileFinished(int,int);
 void setTileReady(int,int);void setTileNotReady(int,int);bool getTileReady(int);
 uint16_t getSize(int);void setSize(int,uint16_t);
};
'''+ '\n'.join(methods)+r'''
int main() {
 static_assert(sizeof(uint32_t)==4 && sizeof(uint16_t)==2 && sizeof(void*)==8);
 SPD reference;
 for(unsigned step=0;step<6;++step) {
  if(step==1) {reference.setTileIdle(0,4);reference.setTileNotReady(0,4);}
  if(step==2) reference.setTileService(0,4);
  if(step==4) reference.setData<uint32_t>(0,0,7);
  if(step==5) {
   // Exact selected signed source recurrence from StreamAccess.cc146:0/1/1.
   int min=0,max=1,stride=1;
   int size=(max==min)?0:std::min((int)reference.num_tile_elements,((int)((max-min-1)/stride))+1);
   assert(size==1);
   reference.setSize(0,(uint16_t)size);reference.setTileFinished(0,4);reference.setTileReady(0,4);
  }
  Obs actual{};assert(projected_trace(step,&actual)==0);
  uint32_t word=0;std::memcpy(&word,reference.tiles_data,4);
  bool other=true;for(unsigned i=1;i<reference.num_tile_elements;++i) other=other&&reference.element_finished[i];
  assert(actual.status==(unsigned)reference.getTileStatus(0));
  assert(actual.ready==reference.tiles_ready[0] && actual.size==reference.tiles_size[0]);
  assert(actual.lane0==reference.element_finished[0] && actual.others==other);
  assert(actual.word==word && actual.initialized==1);
  assert(reference.getTileReady(0)==(actual.ready==0));
  if(step==0 || step==5) assert(reference.getSize(0)==actual.size);
 }
 assert(reference.getSize(0)==1 && !reference.element_finished[1]);
 return 0;
}
''')
    tool=c_lowering.locate();commands=[];outputs=[];deps=[]
    for unit,tail,dialect in ((c,['-c','-o',str(obj)],['-x','c','-std=c11']),
                              (cpp,[str(obj),'-o',str(exe)],['-x','c++','-std=c++17'])):
        dep=unit.with_suffix('.d');deps.append(dep)
        command=[*tool.command,*dialect,'-O1','-Wall','-Werror','-Wno-unused-function','-Wno-sign-compare',
                 '-fsanitize=address,undefined','-MD','-MF',str(dep),str(unit),*tail]
        # Object input must not inherit the preceding explicit C++ language.
        if unit==cpp:command[command.index(str(obj)):command.index(str(obj))]=['-x','none']
        built=subprocess.run(command,capture_output=True,text=True,timeout=60)
        commands.append(command);outputs.append({'exit':built.returncode,'stdout':built.stdout,'stderr':built.stderr})
        if built.returncode:break
    env={'ASAN_OPTIONS':'detect_leaks=0:abort_on_error=0','UBSAN_OPTIONS':'halt_on_error=1:exitcode=1'}
    ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30,env={**os.environ,**env}) if exe.exists() else None
    headers=set()
    for dep in deps:
        if dep.exists():headers.update(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1]))
    receipt={'compile_commands':commands,'compile_outputs':outputs,'native_command':[str(exe)],
        'native_exit':ran.returncode if ran else None,'stdout':ran.stdout if ran else None,'stderr':ran.stderr if ran else None,
        'units':[pin(c),pin(cpp)],'executable':pin(exe) if exe.exists() else None,'headers':[pin(p) for p in sorted(headers)],
        'runtime':stdlib_provenance.runtime_identity(tool),'upstream':[pin(folder/'SPD.cc'),pin(folder/'SPD.hh')],
        'constructor_excerpt':constructor,'source_methods':methods,'scope':__doc__}
    (tmp_path/'spd-source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert len(outputs)==2 and all(row['exit']==0 for row in outputs),outputs
    assert ran.returncode==0,ran.stdout+ran.stderr

"""2026-10-16 ET. Exact pinned constructor/getter excerpts in a finite native harness."""
import hashlib,json,os,shlex,subprocess
from pathlib import Path

from conftest import FIXTURES
from swdb import c_lowering,dx100_size_source,stdlib_provenance


def pin(path):
    path=Path(path).resolve()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def function(text,signature):
    start=text.index(signature);opening=text.index('{',start);depth=0
    for pos in range(opening,len(text)):
        depth+=(text[pos]=='{')-(text[pos]=='}')
        if depth==0:return text[start:pos+1]
    raise AssertionError('incomplete pinned source excerpt')


def run_constructor_projection(tmp_path):
    folder=FIXTURES/'proof/dx100/gem5-e4fc4af'
    for name in ('SPD.cc','SPD.hh'):
        assert pin(folder/name)['sha256']==dx100_size_source.SOURCE_PINS[name]
    source=(folder/'SPD.cc').read_text();header=(folder/'SPD.hh').read_text()
    begin=source.index('    tiles_data = new uint8_t[num_tiles * num_tile_elements * sizeof(uint32_t)];')
    end=source.index('    element_finished = new bool[num_tiles * num_tile_elements];',begin)
    excerpt=source[begin:end]
    check=function(header,'void check_tile_id(int tile_id, int word_size)')
    status=function(source,'SPD::TileStatus SPD::getTileStatus(int tile_id)')
    getsize=function(source,'uint16_t SPD::getSize(int tile_id)')
    projection=dx100_size_source.constructor_projection(dict(dx100_size_source.BOOT_CERTIFICATE))
    unit=tmp_path/'constructor.cpp'
    unit.write_text('''#include <cstdint>
#include <cassert>
#include <cstring>
#define panic_if(c,...) assert(!(c))
#define DX_ASSERT(c) assert(c)
struct SPD {
 enum class TileStatus : uint8_t { Idle=0,Service=1,Finished=2,MAX };
 unsigned num_tiles=32,num_tile_elements=16384;
 uint8_t *tiles_data,*tiles_ready;
 TileStatus *tiles_status;
 bool *tiles_dirty;
 uint16_t *tiles_size;
 SPD() {
'''+excerpt+'''
 }
 ~SPD() { delete[] tiles_data;delete[] tiles_ready;delete[] tiles_status;delete[] tiles_dirty;delete[] tiles_size; }
'''+check+'''
 TileStatus getTileStatus(int tile_id);
 uint16_t getSize(int tile_id);
};
'''+status+'\n'+getsize+'\n'+dx100_size_source.STATE+dx100_size_source.MODEL+'''
int main() {
 static_assert(sizeof(uint16_t)==2 && sizeof(uint32_t)==4 && sizeof(void*)==8);
 SPD source;
'''+ '\n'.join(projection['entry_assignments'])+'''
 unsigned char encoded[64];std::memcpy(encoded,source.tiles_size,64);
 for(unsigned t=0;t<32;++t) {
  assert(source.tiles_status[t]==SPD::TileStatus::Finished && source.tiles_ready[t]==0);
  assert(source.getSize(t)==0 && get_tile_size(t)==source.getSize(t));
 }
 assert(std::memcmp(encoded,__swdb_dx_size_bytes,64)==0);
 // Independent finite decode controls after the certified epoch; not public fresh-state admission.
 for(unsigned t=0;t<32;++t) {
  source.tiles_size[t]=static_cast<uint16_t>(t*257+7);
  std::memcpy(__swdb_dx_size_bytes,source.tiles_size,64);
  assert(get_tile_size(t)==source.getSize(t));
 }
 return 0;
}
''')
    tool=c_lowering.locate();assert not tool.missing
    exe=tmp_path/'constructor.bin';dep=tmp_path/'constructor.d'
    command=[*tool.command,'-x','c++','-std=c++17','-O1','-Wall','-Werror','-Wno-ignored-qualifiers',
             '-fsanitize=address,undefined','-MD','-MF',str(dep),str(unit),'-o',str(exe)]
    built=subprocess.run(command,capture_output=True,text=True,timeout=60)
    env={'ASAN_OPTIONS':'detect_leaks=0:abort_on_error=0','UBSAN_OPTIONS':'halt_on_error=1:abort_on_error=0:exitcode=1'}
    ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30,env={**os.environ,**env}) if built.returncode==0 else None
    dependencies=shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1]) if dep.exists() else []
    receipt={'compile_command':command,'compile_returncode':built.returncode,'compile_stdout':built.stdout,'compile_stderr':built.stderr,
             'compiler_version':tool.version,'runtime_context':stdlib_provenance.runtime_identity(tool),'native_environment':env,
             'native_command':[str(exe)],'native_returncode':ran.returncode if ran else None,'native_stdout':ran.stdout if ran else None,'native_stderr':ran.stderr if ran else None,
             'source':pin(unit),'executable':pin(exe) if exe.exists() else None,'headers':[pin(p) for p in sorted(set(dependencies))],
             'upstream':[pin(folder/'SPD.cc'),pin(folder/'SPD.hh')],'constructor_excerpt':excerpt,
             'constructor_excerpt_sha256':hashlib.sha256(excerpt.encode()).hexdigest(),'scope':'Finite exact source excerpt/projection and defined metadata decode controls; no full simulator/boot theorem.'}
    (tmp_path/'native-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert built.returncode==0,built.stderr
    assert ran.returncode==0,ran.stdout+ran.stderr

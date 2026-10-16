"""2026-10-16 ET. Exact pure counter source excerpts, no ARM MMIO assembly."""
import hashlib,re
from conftest import REPO
from swdb.dx100_interface import HEADERS

def counter_source():
 folder=REPO/'apps/dx100/benchmarks/API';texts={}
 for name,digest in HEADERS.items():
  text=(folder/name).read_bytes();assert hashlib.sha256(text).hexdigest()==digest;texts[name]=text.decode()
 header=texts['MAA_gem5.hpp'];base=texts['MAA.hpp']
 def function(signature):
  start=header.index(signature);begin=header.index('{',start);depth=0
  for end in range(begin,len(header)):
   depth+=(header[end]=='{')-(header[end]=='}')
   if depth==0:return header[start:end+1]
  raise AssertionError('pinned source body is not closed')
 declarations=[]
 for name in ['NUM_TILES_PER_CORE','NUM_REGS_PER_CORE','NUM_TILES','NUM_SCALAR_REGS']:
  declarations.append(re.search(r'^#define '+re.escape(name)+r'[ \t]+[^\n]*',base,re.M)[0])
 # Exact conventional4-core geometry; changing source macros is tested by the
 # full original-TU compiler certificate, not inferred by this native excerpt.
 return ('#include <cassert>\n#include <cstdint>\n#define NUM_CORES 4\n'+'\n'.join(declarations)+'\n'
  +'int REG_count;\nint SPD_count;\nint8_t region_count;\n'+function('inline void init_MAA()')+'\n'
  +'template<class T1>\n'+function('inline int get_new_tile()')+'\n'
  +'template<class T1>\n'+function('inline int get_new_reg()')+'\n')

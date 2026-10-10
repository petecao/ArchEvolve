// One source-normalized matrix proof; setup stays outside its ROI.2026-10-06 ET.
#define SWDB_BULK_COUNT_INLINE
#include "CpuBulkWork.h"
#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>
extern "C" __attribute__((noinline)) void service_bulk_matrix(unsigned char *base,const std::size_t *sizes,std::size_t count,std::uint64_t n,bool invoke){
  bulk_copy8(base+8+64,base+8,8,n,invoke);
  for(std::size_t i=0;i<count;++i){
    std::size_t bytes=sizes[i];unsigned char *src=base+4;
    bulk_move_disjoint(src+((bytes+63)&~std::size_t(63))+64,src,bytes,n,invoke);
    bulk_move_forward(src+4,src,bytes,n,invoke);
    bulk_move_backward(src,src+4,bytes,n,invoke);
  }
}
int main(int argc,char **argv){
  if(argc!=4)return 2;std::uint64_t n=std::strtoull(argv[1],0,10);bool invoke=std::atoi(argv[2])!=0;
  std::vector<std::size_t> sizes;std::stringstream input(argv[3]);std::string item;
  while(std::getline(input,item,','))sizes.push_back(std::strtoull(item.c_str(),0,10));
  std::vector<unsigned char> storage(2*1048576+320,1);
  auto ptr=(reinterpret_cast<std::uintptr_t>(storage.data())+63)&~std::uintptr_t(63);
  service_bulk_matrix(reinterpret_cast<unsigned char *>(ptr),sizes.data(),sizes.size(),n,invoke);
}

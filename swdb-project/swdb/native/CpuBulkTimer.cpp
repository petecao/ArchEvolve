// Uninstrumented paired helper timing; no application execution.2026-10-06 ET.
#include "CpuBulkWork.h"
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <vector>
using Work=void(*)(unsigned char *,const unsigned char *,std::size_t,std::uint64_t,bool);
static Work choose(int operation){return operation==0?bulk_copy8:operation==1?bulk_move_disjoint:operation==2?bulk_move_forward:bulk_move_backward;}
int main(int argc,char **argv){
  if(argc!=5)return 2;
  int operation=std::atoi(argv[1]);std::size_t bytes=std::strtoull(argv[2],0,10);
  std::uint64_t n=std::strtoull(argv[3],0,10);bool service_first=std::atoi(argv[4])!=0;
  if(operation<0||operation>3||bytes<8||bytes>1048576||!n||n>134217728||(operation==0&&bytes!=8))return 3;
  std::vector<unsigned char> storage(2*bytes+320);
  auto base=reinterpret_cast<std::uintptr_t>(storage.data());base=(base+63)&~std::uintptr_t(63);
  unsigned char *src=reinterpret_cast<unsigned char *>(base)+(operation==0?8:4);
  unsigned char *dst=src+((bytes+63)&~std::size_t(63))+64;
  if(operation==2)dst=src+4;
  if(operation==3){dst=src;src+=4;}
  for(std::size_t i=0;i<storage.size();++i)storage[i]=static_cast<unsigned char>(i*13+7);
  Work work=choose(operation);
  std::vector<unsigned char> expected(src,src+bytes);
  work(dst,src,bytes,1,true);
  bool checked=std::equal(expected.begin(),expected.end(),dst);
  if(!checked)return 4;
  work(dst,src,bytes,16,true);
  auto timed=[&](bool invoke){auto start=std::chrono::steady_clock::now();work(dst,src,bytes,n,invoke);return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
  double gross,driver;if(service_first){gross=timed(true);driver=timed(false);}else{driver=timed(false);gross=timed(true);}
  std::ptrdiff_t delta=dst-src;std::size_t separation=delta<0?-delta:delta;
  std::printf("{\"events\":%llu,\"gross_seconds\":%.17g,\"driver_seconds\":%.17g,\"order\":\"%s\",\"checked_one_copy\":true,\"copied_size_bytes\":%llu,\"source_destination_delta_bytes\":%lld,\"overlap_bytes\":%llu,\"destination_alignment_min_bytes\":%d,\"source_alignment_min_bytes\":%d}\n",static_cast<unsigned long long>(n),gross,driver,service_first?"service_first":"driver_first",static_cast<unsigned long long>(bytes),static_cast<long long>(delta),static_cast<unsigned long long>(separation>=bytes?0:bytes-separation),operation==0?8:4,operation==0?8:4);
}

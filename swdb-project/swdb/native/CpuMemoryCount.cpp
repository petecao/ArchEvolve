// Created: 2026-10-06 ET. One shared body invocation, untimed preparation.
// Updated: 2026-10-12 ET: 1/2-byte writes (memory_v2).
#include "CpuMemoryWork.h"
#include <cstdlib>
template<class T> int count(std::size_t n,int operation,bool invoke) {
  T data[16];
  for (std::size_t i=0;i<16;++i) data[i]=operation==0 ? static_cast<T>((i+1)%16) : T(0);
  volatile auto result=service_memory(data,16,n,operation,invoke);
  if (invoke && (operation==3 || operation==4) && (result^n)!=(operation==3 ? n : 0)) return 3;
  return 0;
}
int main(int argc,char **argv) {
  if (argc!=5) return 2;
  const auto n=std::strtoull(argv[1],nullptr,10);const int width=std::atoi(argv[2]);
  const int operation=std::atoi(argv[3]);const bool invoke=std::atoi(argv[4])!=0;
  const bool narrow_store=(width==1 || width==2) && operation==1;
  if (!n || n>5 || (width!=1 && width!=2 && width!=4 && width!=8) || operation<0 || operation>4 ||
      (!narrow_store && (width==2 || (width==1 && operation!=0)))) return 2;
  return width==1 ? count<std::uint8_t>(n,operation,invoke) : width==2 ? count<std::uint16_t>(n,operation,invoke) : width==4 ? count<std::uint32_t>(n,operation,invoke) : count<std::uint64_t>(n,operation,invoke);
}

// Created:2026-10-06 ET. Untimed preparation/checks outside the selected work function.
#include "CpuFloatMemoryWork.h"
#include <cstdlib>
int main(int argc,char**argv) {
  if(argc!=3)return 2;
  const auto n=std::strtoull(argv[1],nullptr,10);const bool invoke=std::atoi(argv[2])!=0;
  if(n!=3 && n!=5)return 2;
  double data[16]={};volatile auto result=service_float_memory(data,16,n,invoke);(void)result;
  for(std::size_t i=0;i<16;++i)if(data[i]!=(invoke && i<n ? 1.0 : 0.0))return 3;
  return 0;
}

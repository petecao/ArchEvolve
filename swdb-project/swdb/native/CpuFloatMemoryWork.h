// Created:2026-10-06 ET. Exact floating64 monotonic source request, serial construction.
#pragma once
#include <cstddef>
extern "C" __attribute__((noinline)) std::size_t service_float_memory(double* data,std::size_t elements,std::size_t n,bool invoke) {
  std::size_t index=0;
  for(std::size_t i=0;i<n;++i) {
    if(invoke) {
#pragma omp atomic update relaxed
      data[index]+=1.0;
    }
    index=(index+1)&(elements-1);
    asm volatile("" : "+r"(index) :: "memory");
  }
  return index;
}

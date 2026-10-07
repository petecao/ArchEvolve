// Created:2026-10-06 ET. Sequential uncontended double atomic updates; no app timing.
#include "CpuFloatMemoryWork.h"
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
volatile std::size_t float_memory_sink=0;
int main(int argc,char**argv) {
  if(argc!=4)return 2;
  const auto elements=std::strtoull(argv[1],nullptr,10),batches=std::strtoull(argv[2],nullptr,10);
  const std::string order=argv[3];
  if(elements<8 || elements>1048576 || (elements&(elements-1)) || !batches || batches>134217728/elements || (order!="service_first" && order!="driver_first"))return 2;
  std::vector<double> data(elements,0.0);
  float_memory_sink^=service_float_memory(data.data(),elements,elements,true);
  double gross=0.,driver=0.;std::size_t verified=0;
  auto one=[&](bool invoke) {
    double elapsed=0.;
    for(std::size_t b=0;b<batches;++b) {
      std::fill(data.begin(),data.end(),0.0);
      const auto start=std::chrono::steady_clock::now();
      const auto result=service_float_memory(data.data(),elements,elements,invoke);
      const auto end=std::chrono::steady_clock::now();
      elapsed+=std::chrono::duration<double>(end-start).count();float_memory_sink^=result;
      for(const double value:data)if(value!=(invoke ? 1.0 : 0.0))return false;
      if(invoke)verified+=elements;
    }
    if(invoke)gross=elapsed;else driver=elapsed;return true;
  };
  const bool first=order=="service_first";
  if(!one(first) || !one(!first))return 3;
  std::cout<<std::setprecision(17)<<"{\"events\":"<<elements*batches<<",\"batch_events\":"<<elements<<",\"batches\":"<<batches
    <<",\"gross_seconds\":"<<gross<<",\"driver_seconds\":"<<driver<<",\"verified_updates\":"<<verified<<",\"order\":\""<<order<<"\"}\n";
}

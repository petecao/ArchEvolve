// Created: 2026-10-06 ET. Prepared resident-cell/driver pairs, no application timing.
#include "CpuMemoryWork.h"
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>
volatile std::uint64_t memory_sink=0;
template<class T> int timed(std::size_t elements,std::size_t batches,int operation,const std::string& order) {
  std::vector<T> data(elements), permutation(elements);
  std::iota(permutation.begin(),permutation.end(),T(0));
  std::mt19937_64 random(20261006);std::shuffle(permutation.begin(),permutation.end(),random);
  auto prepare=[&]() {
    if (operation==0) for (std::size_t i=0;i<elements;++i) data[permutation[i]]=permutation[(i+1)%elements];
    else std::fill(data.begin(),data.end(),T(0));
  };
  prepare();
  if (operation==0) {
    T index=0;
    for (std::size_t i=0;i<elements;++i) {
      index=data[index];
      if (static_cast<std::size_t>(index)>=elements || (index==0 && i+1!=elements)) return 3;
    }
    if (index!=0) return 3;
  }
  memory_sink^=service_memory(data.data(),elements,elements,operation,true);
  double gross=0., driver=0.;std::size_t success_events=0;
  auto one=[&](bool invoke) {
    double elapsed=0.;
    for (std::size_t j=0;j<batches;++j) {
      prepare();
      auto start=std::chrono::steady_clock::now();
      auto result=service_memory(data.data(),elements,elements,operation,invoke);
      auto end=std::chrono::steady_clock::now();
      elapsed+=std::chrono::duration<double>(end-start).count();memory_sink^=result;
      if (invoke && operation==3 && result!=elements) return -1.;
      if (invoke && operation==4 && result!=0) return -1.;
      if (invoke && (operation==3 || operation==4)) success_events+=result;
    }
    if (invoke) gross=elapsed;else driver=elapsed;return elapsed;
  };
  const bool first=order=="service_first";
  if (one(first)<0 || one(!first)<0) return 3;
  std::cout<<std::setprecision(17)<<"{\"events\":"<<elements*batches<<",\"batch_events\":"<<elements
      <<",\"batches\":"<<batches<<",\"gross_seconds\":"<<gross<<",\"driver_seconds\":"<<driver
      <<",\"order\":\""<<order<<"\",\"checksum\":"<<memory_sink
      <<",\"success_events\":";
  if (operation==3 || operation==4) std::cout<<success_events;else std::cout<<"null";
  std::cout<<",\"cycle_verified_elements\":";
  if (operation==0) std::cout<<elements;else std::cout<<"null";
  std::cout<<"}\n";return 0;
}
int main(int argc,char **argv) {
  if (argc!=6) return 2;
  const int width=std::atoi(argv[1]);const auto elements=std::strtoull(argv[2],nullptr,10);
  const auto batches=std::strtoull(argv[3],nullptr,10);const int operation=std::atoi(argv[4]);
  const std::string order=argv[5];
  if ((width!=1 && width!=4 && width!=8) || elements<8 || (elements&(elements-1)) || elements*width>8388608 ||
      !batches || elements*batches>134217728 || operation<0 || operation>4 || (width==1 && (operation!=0 || elements>256)) ||
      (order!="service_first" && order!="driver_first")) return 2;
  return width==1 ? timed<std::uint8_t>(elements,batches,operation,order) : width==4 ? timed<std::uint32_t>(elements,batches,operation,order) : timed<std::uint64_t>(elements,batches,operation,order);
}

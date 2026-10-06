// One live native counting run; never records an address trace or a timing.
// Updated: 2026-10-06 ET. Thread-safe counts support outlined OpenMP functions.
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <map>
#include <array>
#include <mutex>
#include <limits>
struct AccessCount { uint64_t elements=0,bytes=0,lo=UINT64_MAX,hi=0; };
struct Counts {
  std::mutex mutex;
  std::map<uint32_t,uint64_t> trips, calls;
  std::map<uint32_t,std::array<uint64_t,4>> ops;
  std::map<uint32_t,AccessCount> accesses;
  ~Counts() {
    const char *path=std::getenv("SWDB_COUNTS_OUTPUT"); if (!path) return;
    std::ofstream out(path); out<<"{\"trips\":{"; bool first=true;
    for(auto &p:trips) {if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second;}
    out<<"},\"operations\":{";first=true;
    for(auto &p:ops) {if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":["<<p.second[0]<<','<<p.second[1]<<','<<p.second[2]<<','<<p.second[3]<<']';}
    out<<"},\"accesses\":{";first=true;
    for(auto &p:accesses) {if(!first)out<<',';first=false;auto &a=p.second;out<<'"'<<p.first<<"\":{\"elements\":"<<a.elements<<",\"bytes\":"<<a.bytes<<",\"address_span_bytes\":"<<(a.elements?a.hi-a.lo:0)<<'}';}
    out<<"},\"calls\":{";first=true;
    for(auto &p:calls) {if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second;}
    out<<"}}\n";
  }
};
Counts &counts() { static Counts value; return value; }
extern "C" void __swdb_trip(uint32_t region,uint64_t n) { auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.trips[region]+=n; }
extern "C" void __swdb_op(uint32_t region,uint32_t kind,uint64_t n) { auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.ops[region][kind]+=n; }
extern "C" void __swdb_access(uint32_t site,uint64_t address,uint64_t n,uint64_t bytes) {
  auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);auto &a=c.accesses[site];a.elements+=n;a.bytes+=n*bytes;
  if(address<a.lo)a.lo=address;if(address+n*bytes>a.hi)a.hi=address+n*bytes;
}

extern "C" void __swdb_call(uint32_t site) { auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.calls[site]++; }

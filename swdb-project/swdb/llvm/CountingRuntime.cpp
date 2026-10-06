// Live compact counts; virtual addresses never leave this process. Updated: 2026-10-06 ET.
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <map>
#include <array>
#include <mutex>
#include <limits>
#include <set>
#include <algorithm>
#include <atomic>
#include <vector>
#include <thread>
#include "LiveObjects.hpp"
#ifdef _OPENMP
#include <omp.h>
#endif
uint64_t workers(){
#ifdef _OPENMP
return omp_get_num_threads();
#else
return 1;
#endif
}
struct Footprint {
  std::set<std::pair<uint64_t,uint64_t>> ranges;
  bool complete=true;
  void add(uint64_t lo,uint64_t hi){
    if(!complete)return;
    if(hi<lo){complete=false;ranges.clear();return;}
    auto it=ranges.lower_bound({lo,0});
    if(it!=ranges.begin()){auto previous=std::prev(it);if(previous->second>=lo)it=previous;}
    while(it!=ranges.end() && it->first<=hi){lo=std::min(lo,it->first);hi=std::max(hi,it->second);it=ranges.erase(it);}
    if(ranges.size()>=swdb_live::budget()){complete=false;ranges.clear();return;}
    ranges.emplace(lo,hi);
  }
  std::string json_bytes()const{return complete?std::to_string(bytes()):"null";}
  uint64_t bytes() const {
    uint64_t total=0,lo=0,hi=0;bool first=true;
    for(auto r:ranges){if(first){lo=r.first;hi=r.second;first=false;}else if(r.first>hi){total+=hi-lo;lo=r.first;hi=r.second;}else hi=std::max(hi,r.second);}
    return first?0:total+hi-lo;
  }
};
struct AccessCount { uint64_t elements=0,bytes=0,lo=UINT64_MAX,hi=0;Footprint footprint; };
struct CallShape {
  uint64_t unknown_lengths=0,unknown_free_lifetimes=0;
  std::map<uint64_t,uint64_t> lengths,lifetimes;
};
struct Counts {
  std::mutex mutex;
  swdb_live::Registry registry;
  std::atomic<bool> active;
  std::map<uint32_t,uint64_t> trips,calls,sizes;
  std::map<uint32_t,CallShape> call_shapes;
  uint64_t call_shape_entries=0;
  std::map<std::thread::id,uint64_t> thread_ids;
  std::map<uint32_t,std::set<uint64_t>> active_workers,team_sizes;
  std::map<uint32_t,std::array<uint64_t,4>> ops;
  std::map<uint32_t,AccessCount> accesses;
  std::map<uint32_t,Footprint> footprints;
  std::vector<uint64_t> sources;
  std::vector<std::string> trials;
  Counts():active(!(std::getenv("SWDB_ROI_GATED") && std::string(std::getenv("SWDB_ROI_GATED"))=="1")){}
  void clear(){registry.begin();call_shapes.clear();call_shape_entries=0;trips.clear();calls.clear();sizes.clear();ops.clear();accesses.clear();footprints.clear();sources.clear();active_workers.clear();team_sizes.clear();thread_ids.clear();}
  void observe(uint32_t region){
    auto token=thread_ids.emplace(std::this_thread::get_id(),thread_ids.size()).first->second;
    active_workers[region].insert(token);team_sizes[region].insert(workers());
  }
  std::string snapshot() {
    std::ostringstream out;out<<"{\"trips\":{";bool first=true;
    for(auto &p:trips){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second;}
    out<<"},\"operations\":{";first=true;
    for(auto &p:ops){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":["<<p.second[0]<<','<<p.second[1]<<','<<p.second[2]<<','<<p.second[3]<<']';}
    out<<"},\"accesses\":{";first=true;
    for(auto &p:accesses){if(!first)out<<',';first=false;auto &a=p.second;out<<'"'<<p.first<<"\":{\"elements\":"<<a.elements<<",\"bytes\":"<<a.bytes<<",\"address_span_bytes\":"<<(a.elements?a.hi-a.lo:0)<<",\"unique_bytes\":"<<a.footprint.json_bytes()<<'}';}
    out<<"},\"footprints\":{";first=true;
    for(auto &p:footprints){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second.json_bytes();}
    out<<"},\"calls\":{";first=true;
    for(auto &p:calls){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second;}
    out<<"},\"call_size_bytes\":{";first=true;
    for(auto &p:sizes){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second;}
    out<<"},\"active_workers\":{";first=true;for(auto &p:active_workers){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":"<<p.second.size();}
    for(auto item:{std::make_pair("worker_tokens",&active_workers),std::make_pair("team_sizes",&team_sizes)}){
      out<<"},\""<<item.first<<"\":{";first=true;for(auto &p:*item.second){if(!first)out<<',';first=false;out<<'"'<<p.first<<"\":[";bool sep=false;for(auto token:p.second){if(sep)out<<',';sep=true;out<<token;}out<<']';}
    }
    out<<"},\"sources\":[";first=true;for(auto s:sources){if(!first)out<<',';first=false;out<<s;}
    out<<"],\"memory_service_counts\":"<<registry.snapshot()<<",\"call_shapes\":{";first=true;
    for(auto &p:call_shapes){if(!first)out<<',';first=false;auto &shape=p.second;
      out<<'"'<<p.first<<"\":{\"unknown_lengths\":"<<shape.unknown_lengths<<",\"unknown_free_lifetimes\":"<<shape.unknown_free_lifetimes;
      for(auto item:{std::make_pair("known_length_bins",&shape.lengths),std::make_pair("allocation_lifetime_size_bins",&shape.lifetimes)}){
        out<<",\""<<item.first<<"\":[";bool sep=false;for(auto &bin:*item.second){if(sep)out<<',';sep=true;out<<"{\"bytes\":"<<bin.first<<",\"executions\":"<<bin.second<<'}';}out<<']';
      }out<<'}';
    }out<<"}}";return out.str();
  }
  ~Counts(){const char *path=std::getenv("SWDB_COUNTS_OUTPUT");if(!path)return;
    std::ofstream out(path);std::string root=trials.empty()?snapshot():trials.front();root.pop_back();out<<root<<",\"trials\":[";
    bool first=true;for(auto &trial:trials){if(!first)out<<',';first=false;out<<trial;}out<<"]}\n";
  }
};
Counts &counts(){static Counts value;return value;}
extern "C" void __swdb_begin(){auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.clear();c.active=true;}
extern "C" void __swdb_end(){auto &c=counts();c.active=false;std::lock_guard<std::mutex> lock(c.mutex);c.trials.push_back(c.snapshot());}
extern "C" void __swdb_source(uint64_t source){auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);c.sources.push_back(source);}
extern "C" void __swdb_trip(uint32_t region,uint64_t n){auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);c.trips[region]+=n;if(n)c.observe(region);}
extern "C" void __swdb_op(uint32_t region,uint32_t kind,uint64_t n){auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);c.ops[region][kind]+=n;c.observe(region);}
extern "C" void __swdb_access(uint32_t site,uint32_t region,uint64_t address,uint64_t n,uint64_t bytes){
  auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);c.observe(region);auto &a=c.accesses[site];a.elements+=n;a.bytes+=n*bytes;
  a.footprint.add(address,address+n*bytes);c.footprints[region].add(address,address+n*bytes);
  if(address<a.lo)a.lo=address;if(address+n*bytes>a.hi)a.hi=address+n*bytes;
}
extern "C" void __swdb_call(uint32_t site,uint64_t size,uint32_t known,uint32_t region){auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);c.calls[site]++;c.observe(region);if(known)c.sizes[site]+=size;}

extern "C" void __swdb_allocate(uint64_t address,uint64_t size,uint32_t known){auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.registry.allocate(address,size,known);}
extern "C" void __swdb_release(uint64_t address){auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.registry.release(address);}
extern "C" void __swdb_reallocate(uint64_t old,uint64_t address,uint64_t size,uint32_t known){auto &c=counts();std::lock_guard<std::mutex> lock(c.mutex);c.registry.reallocate(old,address,size,known);}
extern "C" void __swdb_access_v2(uint32_t site,uint32_t region,uint64_t address,uint64_t n,uint64_t width,uint32_t update){
  auto &c=counts();{std::lock_guard<std::mutex> lock(c.mutex);c.registry.observe(region,address,n,width,update,c.active);}
  __swdb_access(site,region,address,n,width);
}

extern "C" void __swdb_call_v2(uint32_t site,uint64_t size,uint32_t known,uint32_t region,uint64_t pointer,uint32_t action){
  auto &c=counts();if(!c.active)return;std::lock_guard<std::mutex> lock(c.mutex);
  c.calls[site]++;c.observe(region);if(known)c.sizes[site]+=size;
  auto &shape=c.call_shapes[site];
  auto add=[&](std::map<uint64_t,uint64_t> &bins,uint64_t bytes,uint64_t &unknown){
    auto it=bins.find(bytes);if(it!=bins.end())++it->second;
    else if(c.call_shape_entries<swdb_live::budget()){bins[bytes]=1;++c.call_shape_entries;}
    else ++unknown;
  };
  if(action==2){
    auto it=c.registry.objects.find(pointer);
    if(it==c.registry.objects.end())++shape.unknown_free_lifetimes;
    else add(shape.lifetimes,it->second.size,shape.unknown_free_lifetimes);
  } else if(known)add(shape.lengths,size,shape.unknown_lengths);
  else ++shape.unknown_lengths;
}

// Compact logical object observations; no pointer/trace serialization. Updated: 2026-10-06 ET.
#pragma once
#include <map>
#include <set>
#include <cstdint>
#include <limits>
#include <sstream>
#include <cstdlib>

namespace swdb_live {
inline uint64_t budget(){const char *v=std::getenv("SWDB_STATE_BUDGET");return v?std::strtoull(v,nullptr,10):524288;}
struct Object {
  uint64_t base,size,id,born;std::set<uint64_t> touched_pages;bool touches_complete;
  Object(uint64_t b,uint64_t s,uint64_t i,uint64_t e):base(b),size(s),id(i),born(e),touches_complete(true){}
};
struct Service {
  std::map<std::pair<uint32_t,uint64_t>,uint64_t> requests;
  uint64_t useful_bytes=0,unknown_requests=0,first_read=0,first_write=0;
  std::set<std::pair<uint64_t,uint64_t>> lines,pre_pages,in_pages;
  bool lines_complete=true,pages_complete=true,first_complete=true,bytes_complete=true;
};
struct Registry {
  std::map<uint64_t,Object> objects;
  std::map<uint32_t,Service> services;
  uint64_t next_id=1,epoch=0,touch_entries=0,service_entries=0;
  bool object_budget_exhausted=false;
  void begin(){++epoch;services.clear();service_entries=0;}
  Object *resolve(uint64_t address,uint64_t size){
    auto it=objects.upper_bound(address);if(it==objects.begin())return nullptr;--it;
    auto &o=it->second;
    return address>=o.base && address-o.base<=o.size && size<=o.size-(address-o.base)?&o:nullptr;
  }
  void allocate(uint64_t base,uint64_t size,bool known){
    if(!base)return;
    release(base);
    if(!known || !size || size>UINT64_MAX-base)return;
    if(objects.size()>=budget()){object_budget_exhausted=true;return;}
    objects.emplace(base,Object(base,size,next_id++,epoch));
  }
  void release(uint64_t base){auto it=objects.find(base);if(it!=objects.end()){touch_entries-=it->second.touched_pages.size();objects.erase(it);}}
  void reallocate(uint64_t old,uint64_t result,uint64_t size,bool known){
    if(!result && size)return; // failure preserves the old lifetime
    release(old); // zero-size semantics cannot retain a provably live old object
    allocate(result,size,known);
  }
  bool add(std::set<std::pair<uint64_t,uint64_t>> &set,uint64_t id,uint64_t key){
    if(set.count({id,key}))return true;
    if(service_entries>=budget())return false;
    set.emplace(id,key);++service_entries;return true;
  }
  void observe(uint32_t region,uint64_t address,uint64_t n,uint64_t width,uint32_t update,bool active){
    bool range_known=width && n<=UINT64_MAX/width;
    uint64_t bytes=range_known?n*width:0;
    auto *object=range_known?resolve(address,bytes):nullptr;
    Service *s=active?&services[region]:nullptr;
    if(s){s->requests[{update,width}]+=n;
      if(!range_known || s->useful_bytes>UINT64_MAX-bytes)s->bytes_complete=false;
      else s->useful_bytes+=bytes;
      if(!object)s->unknown_requests+=n;
    }
    if(!object || !bytes)return;
    uint64_t offset=address-object->base,hi=offset+bytes-1;
    if(s && s->lines_complete){
      for(uint64_t line=offset/64;line<=hi/64;++line)
        if(!add(s->lines,object->id,line)){s->lines_complete=false;s->lines.clear();break;}
    }
    // These are first accesses observed by this source observer, never native page faults.
    for(uint64_t page=offset/4096;page<=hi/4096;++page){
      bool first=!object->touched_pages.count(page);
      if(first && touch_entries>=budget())object->touches_complete=false;
      else if(first){object->touched_pages.insert(page);++touch_entries;}
      if(!s)continue;
      if(!object->touches_complete)s->first_complete=false;
      if(first && object->touches_complete){if(update==0)++s->first_read;else if(update==1)++s->first_write;else s->first_complete=false;}
      auto &pages=object->born<epoch?s->pre_pages:s->in_pages;
      if(s->pages_complete && !add(pages,object->id,page)){s->pages_complete=false;s->pre_pages.clear();s->in_pages.clear();}
    }
  }
  std::string snapshot()const{
    std::ostringstream out;out<<'{';bool sep=false;
    for(auto &p:services){if(sep)out<<',';sep=true;auto &s=p.second;
      out<<'"'<<p.first<<"\":{\"requests\":[";bool entry=false;
      for(auto &r:s.requests){if(entry)out<<',';entry=true;out<<"{\"update\":"<<r.first.first<<",\"element_bytes\":"<<r.first.second<<",\"requests\":"<<r.second<<'}';}
      out<<"],\"useful_bytes\":"<<(s.bytes_complete?std::to_string(s.useful_bytes):"null")
        <<",\"lifetime_line_union\":"<<(s.lines_complete && !s.unknown_requests?std::to_string(s.lines.size()):"null")
        <<",\"logical_first_read_pages\":"<<(s.first_complete && !s.unknown_requests?std::to_string(s.first_read):"null")
        <<",\"logical_first_write_pages\":"<<(s.first_complete && !s.unknown_requests?std::to_string(s.first_write):"null")
        <<",\"pre_roi_allocation_pages\":"<<(s.pages_complete && !s.unknown_requests?std::to_string(s.pre_pages.size()):"null")
        <<",\"in_roi_allocation_pages\":"<<(s.pages_complete && !s.unknown_requests?std::to_string(s.in_pages.size()):"null")
        <<",\"unknown_object_requests\":"<<s.unknown_requests<<",\"missing\":[";
      bool missing=false;auto emit=[&](const char *name){if(missing)out<<',';missing=true;out<<'"'<<name<<'"';};
      if(s.unknown_requests)emit("object_identity_or_extent");
      if(!s.lines_complete)emit("state_budget.lifetime_line_union");
      if(!s.pages_complete)emit("state_budget.allocation_pages");
      if(!s.first_complete)emit("first_access_scope_or_state_budget");
      if(!s.bytes_complete)emit("byte_range_overflow");
      if(object_budget_exhausted)emit("state_budget.object_registry");
      out<<"]}";
    }out<<'}';return out.str();
  }
};
}

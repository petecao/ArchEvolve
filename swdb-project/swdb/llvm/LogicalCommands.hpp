// Bounded in-memory logical windows; never serialize pointers/rows/sequences.
// Created: 2026-10-06 ET. Allocation placement is a declared inferred scenario.
#pragma once
namespace swdb_logical {
inline uint64_t setting(const char *name){const char *v=std::getenv(name);return v?std::strtoull(v,nullptr,10):0;}
struct Config {
  uint64_t transaction,window;bool coalesce,layout,placement;
  std::array<std::vector<std::pair<unsigned,unsigned>>,5> fields;
  Config():transaction(setting("SWDB_LOGICAL_TRANSACTION_BYTES")),window(setting("SWDB_LOGICAL_WINDOW_REQUESTS")),
    coalesce(std::getenv("SWDB_LOGICAL_COALESCING") && std::string(std::getenv("SWDB_LOGICAL_COALESCING"))=="window_unique_lines"),
    layout(setting("SWDB_LOGICAL_LAYOUT_KNOWN")),placement(setting("SWDB_LOGICAL_PLACEMENT_KNOWN")){
    unsigned i=0;for(auto name:{"CHANNEL","RANK","BANK_GROUP","BANK","ROW"}){
      std::string key=std::string("SWDB_LOGICAL_FIELD_")+name;const char *v=std::getenv(key.c_str());
      if(v){std::istringstream items(v);std::string field;while(std::getline(items,field,',')){auto colon=field.find(':');fields[i].push_back({std::stoul(field.substr(0,colon)),std::stoul(field.substr(colon+1))});}}++i;
    }
  }
  uint64_t decode(uint64_t address,unsigned index)const{
    uint64_t result=0;unsigned output=0;for(auto field:fields[index]){
      unsigned lo=field.first,width=field.second;uint64_t mask=width==64?UINT64_MAX:(uint64_t(1)<<width)-1;
      result|=((address>>lo)&mask)<<output;output+=width;
    }return result;
  }
  std::array<uint64_t,6> row(uint64_t object,uint64_t address)const{
    return {{object,decode(address,0),decode(address,1),
      decode(address,2),decode(address,3),decode(address,4)}};
  }
};
struct Totals {
  uint32_t descriptor=0,region=0;uint64_t executions=0,active_elements=0,active_unknown=0,useful_accesses=0,useful_bytes=0;
  uint64_t line_requests=0,row_groups=0,windows=0,bookkeeping_accesses=0;
  std::array<uint64_t,4> bookkeeping_ops{{0,0,0,0}};
  bool requests_complete=true,rows_complete=true,unknown_target=false;
  std::set<std::string> missing;
  std::map<uint32_t,uint64_t> opaque_calls;
  std::string json()const{
    std::ostringstream out;out<<"{\"descriptor\":"<<descriptor<<",\"region\":"<<region<<",\"executions\":"<<executions
      <<",\"active_elements\":"<<active_elements<<",\"active_unknown\":"<<active_unknown<<",\"useful_accesses\":"<<useful_accesses
      <<",\"useful_bytes\":"<<useful_bytes<<",\"unknown_target\":"<<(unknown_target?"true":"false")
      <<",\"line_requests\":"<<(requests_complete?std::to_string(line_requests):"null")
      <<",\"row_groups\":"<<(rows_complete && requests_complete?std::to_string(row_groups):"null")<<",\"windows\":"<<windows
      <<",\"bookkeeping_accesses\":"<<bookkeeping_accesses<<",\"bookkeeping_ops\":[";
    for(unsigned i=0;i<4;++i){if(i)out<<',';out<<bookkeeping_ops[i];}out<<"],\"opaque_calls\":{";bool sep=false;
    for(auto &call:opaque_calls){if(sep)out<<',';sep=true;out<<'"'<<call.first<<"\":"<<call.second;}out<<"},\"missing\":[";sep=false;
    for(auto &name:missing){if(sep)out<<',';sep=true;out<<'"'<<name<<'"';}out<<"]}";return out.str();
  }
};
struct Frame {
  uint32_t site=0,descriptor=0,region=0;uint64_t object=0,pointer=0,base=0,extent=0,expanded=0;bool alias=false;
  std::set<std::pair<uint64_t,uint64_t>> lines;
  std::set<std::array<uint64_t,6>> rows;
};
thread_local std::vector<Frame> frames;
thread_local uint64_t suppressed_depth=0;
inline Frame *current(){for(auto it=frames.rbegin();it!=frames.rend();++it)if(!it->alias)return &*it;return nullptr;}
inline void add(uint64_t &count,uint64_t n,Totals &total){if(count>UINT64_MAX-n){total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("logical_count_overflow");}else count+=n;}
inline void close(Frame &frame,Totals &total,uint64_t &entries,const Config &config){
  if(!frame.expanded)return;
  add(total.line_requests,config.coalesce?frame.lines.size():frame.expanded,total);add(total.row_groups,frame.rows.size(),total);++total.windows;
  entries-=frame.lines.size()+frame.rows.size();frame.lines.clear();frame.rows.clear();frame.expanded=0;
}
inline void observe(Frame &frame,Totals &total,uint64_t address,uint64_t n,uint64_t width,uint32_t update,
                    swdb_live::Registry &registry,uint64_t &entries,const Config &config,uint64_t target_roles,uint64_t bookkeeping_roles){
  uint64_t bit=uint64_t(1)<<frame.descriptor;
  if(bookkeeping_roles&bit){total.bookkeeping_accesses+=n;return;}
  if(!(target_roles&bit)){
    if(frame.object && address>=frame.base && address-frame.base<frame.extent){total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("target_access_source_role");}
    else total.bookkeeping_accesses+=n;return;
  }
  if(!frame.object){total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("semantic_target_object_identity");return;}
  bool within=address>=frame.base && address-frame.base<frame.extent;
  if(!within){total.bookkeeping_accesses+=n;return;}
  if(update!=0){total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("unsupported_target_update_policy");return;}
  if(!width || n>UINT64_MAX/width || n*width>frame.extent-(address-frame.base)){
    total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("semantic_target_byte_extent");return;
  }
  auto *object=registry.resolve(address,n*width);
  if(!object || object->id!=frame.object){total.unknown_target=true;total.requests_complete=false;total.rows_complete=false;total.missing.insert("semantic_target_lifetime");return;}
  add(total.useful_accesses,n,total);add(total.useful_bytes,n*width,total);
  if(!n)return;
  if(!config.transaction || !config.placement){total.requests_complete=false;total.rows_complete=false;total.missing.insert("transaction_or_placement_policy");return;}
  if(!config.layout){total.rows_complete=false;total.missing.insert("address_layout");}
  if(!config.window){total.rows_complete=false;total.missing.insert("logical_window_policy");if(config.coalesce)total.requests_complete=false;}
  uint64_t offset=address-frame.base,hi=offset+n*width-1;
  for(uint64_t line=offset/config.transaction;line<=hi/config.transaction;++line){
    if(!config.window){if(!config.coalesce)add(total.line_requests,1,total);continue;}
    ++frame.expanded;
    std::pair<uint64_t,uint64_t> key(frame.object,line);
    if(config.coalesce && !frame.lines.count(key)){
      if(entries>=swdb_live::budget()){total.requests_complete=false;total.missing.insert("state_budget.window_lines");}
      else {frame.lines.insert(key);++entries;}
    }
    if(config.layout){auto row=config.row(frame.object,line*config.transaction);
      if(!frame.rows.count(row)){
        if(entries>=swdb_live::budget()){total.rows_complete=false;total.missing.insert("state_budget.window_rows");}
        else {frame.rows.insert(row);++entries;}
      }
    }
    if(frame.expanded==config.window)close(frame,total,entries,config);
  }
}
}

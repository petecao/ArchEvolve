// Optional scope callbacks. Included after Counts/ObserverScope; no address serialization.
// Updated: 2026-10-06 ET.
#pragma once
namespace swdb_scopes {
std::atomic<bool> finished(false);
struct Shutdown {
  ~Shutdown(){observerEntered=true;finished=true;}
};
// Construct after the lazy Counts instance, so the gate closes before Counts
// finalization and later application destructors cannot re-enter dead state.
Counts &observed(){auto &value=counts();static Shutdown gate;return value;}
struct Entry {uint64_t id,serial;};
struct Frame {uint64_t token,next_serial;std::map<uint64_t,Entry> objects;};
// POD thread pointer avoids observer STL destruction re-entering source weak ODR helpers.
// States are bounded, process-lifetime metadata; an empty state's vector releases capacity.
struct State {std::vector<Frame> frames;};
thread_local State *state=nullptr;
uint64_t next_token=1,state_entries=0,frame_entries=0;
State *get(bool create=false){
  if(!state && create){
    if(state_entries>=swdb_live::budget()){swdb_scopes::observed().registry.scope_missing.insert("state_budget.object_scope_threads");return nullptr;}
    state=new State;++state_entries;
  }return state;
}
void release(uint64_t base,uint64_t id) {
  auto it=swdb_scopes::observed().registry.objects.find(base);
  if(it!=swdb_scopes::observed().registry.objects.end() && it->second.id==id)swdb_scopes::observed().registry.release(base);
}
void retire(Frame &frame,uint64_t mark=0) {
  for(auto it=frame.objects.begin();it!=frame.objects.end();) {
    if(it->second.serial>=mark){release(it->first,it->second.id);it=frame.objects.erase(it);}else ++it;
  }
}
Frame *find(uint64_t token){auto *s=get();return s && !s->frames.empty() && s->frames.back().token==token?&s->frames.back():nullptr;}
void pop(State &s){auto token=s.frames.back().token;retire(s.frames.back());swdb_scopes::observed().registry.retire_views(token);s.frames.pop_back();--frame_entries;
  if(s.frames.empty())std::vector<Frame>().swap(s.frames);
}
bool unwind(uint64_t token,bool include){
  auto *s=get();if(!s)return false;
  auto found=std::find_if(s->frames.rbegin(),s->frames.rend(),[&](const Frame &f){return f.token==token;});
  if(found==s->frames.rend()){swdb_scopes::observed().registry.scope_missing.insert("frame_control_flow_unknown");return false;}
  while(s->frames.back().token!=token)pop(*s);
  if(include)pop(*s);return true;
}
}
extern "C" uint64_t __swdb_object_scope_enter() {
  if(observerEntered || swdb_scopes::finished)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::observed().registry.scope_enabled=true;
  auto *state=swdb_scopes::get(true);if(!state)return 0;
  if(swdb_scopes::frame_entries>=swdb_live::budget() || swdb_scopes::next_token==UINT64_MAX){swdb_scopes::observed().registry.scope_missing.insert("state_budget.object_scope_frames");return 0;}
  uint64_t token=swdb_scopes::next_token++;
  state->frames.push_back({token,1,{}});++swdb_scopes::frame_entries;return token;
}
extern "C" uint64_t __swdb_object_scope_storage(uint64_t token) {
  if(observerEntered || swdb_scopes::finished || !token)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);auto *frame=swdb_scopes::find(token);
  if(!frame || frame->next_serial==UINT64_MAX){swdb_scopes::observed().registry.scope_missing.insert("source_storage_order_unknown");return 0;}
  return frame->next_serial++;
}
extern "C" void __swdb_object_scope_alloc_at(uint64_t token,uint64_t base,uint64_t bytes,uint32_t known,uint64_t storage) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  auto *frame=swdb_scopes::find(token);if(!frame)return;
  if(!storage || storage>=frame->next_serial){swdb_scopes::observed().registry.scope_missing.insert("source_storage_order_unknown");return;}
  auto previous=frame->objects.find(base);auto existing=swdb_scopes::observed().registry.objects.find(base);
  if(existing!=swdb_scopes::observed().registry.objects.end()){
    bool owned=previous!=frame->objects.end() && previous->second.id==existing->second.id;
    if(owned && known && bytes==existing->second.size)return;
    if(known){existing->second.ambiguous=true;swdb_scopes::observed().registry.scope_missing.insert("overlapping_full_object_extents");return;}
    if(owned){swdb_scopes::release(base,previous->second.id);frame->objects.erase(previous);}
  }
  swdb_scopes::observed().registry.allocate(base,bytes,known,1);
  auto it=swdb_scopes::observed().registry.objects.find(base);
  if(it!=swdb_scopes::observed().registry.objects.end())frame->objects[base]={it->second.id,storage};
}
extern "C" void __swdb_object_scope_alloc(uint64_t token,uint64_t base,uint64_t bytes,uint32_t known) {
  auto storage=__swdb_object_scope_storage(token);
  __swdb_object_scope_alloc_at(token,base,bytes,known,storage);
}
extern "C" void __swdb_object_scope_retire(uint64_t token,uint64_t base) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  auto *frame=swdb_scopes::find(token);if(!frame)return;
  auto it=frame->objects.find(base);
  if(it!=frame->objects.end()){swdb_scopes::release(base,it->second.id);frame->objects.erase(it);}
}
extern "C" uint64_t __swdb_object_scope_mark(uint64_t token) {
  if(observerEntered || swdb_scopes::finished || !token)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  auto *frame=swdb_scopes::find(token);return frame?frame->next_serial:0;
}
extern "C" void __swdb_object_scope_restore(uint64_t token,uint64_t mark) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  auto *frame=swdb_scopes::find(token);if(frame){if(!mark)swdb_scopes::observed().registry.scope_missing.insert("stackrestore_checkpoint_unknown");swdb_scopes::retire(*frame,mark);}
}
extern "C" void __swdb_object_scope_leave(uint64_t token) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::unwind(token,true);
}

extern "C" void __swdb_object_scope_view(uint64_t token,uint64_t base,uint64_t bytes) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  if(swdb_scopes::find(token))swdb_scopes::observed().registry.view(token,base,bytes);
}

extern "C" void __swdb_object_scope_unwind(uint64_t token) {
  if(observerEntered || swdb_scopes::finished || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::unwind(token,false);
}

extern "C" void __swdb_object_scope_global(uint64_t base,uint64_t bytes,uint32_t known) {
  if(observerEntered || swdb_scopes::finished)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::observed().registry.global(base,bytes,known);
}

extern "C" void __swdb_object_scope_abandon() {
  if(observerEntered || swdb_scopes::finished)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::observed().registry.scope_missing.insert("nonlocal_control_flow");
  auto *state=swdb_scopes::get();if(state)while(!state->frames.empty())swdb_scopes::pop(*state);
}
extern "C" void __swdb_object_scope_problem() {
  if(observerEntered || swdb_scopes::finished)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(swdb_scopes::observed().mutex);
  swdb_scopes::observed().registry.scope_enabled=true;swdb_scopes::observed().registry.scope_missing.insert("unsupported_function_lifetime_contract");
}

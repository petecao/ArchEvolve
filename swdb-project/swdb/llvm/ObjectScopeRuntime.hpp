// Optional scope callbacks. Included after Counts/ObserverScope; no address serialization.
// Updated: 2026-10-06 ET.
#pragma once
namespace swdb_scopes {
struct Entry {uint64_t id,serial;};
struct Frame {uint64_t token,next_serial;std::map<uint64_t,Entry> objects;};
thread_local std::vector<Frame> frames;
uint64_t next_token=1;
void release(uint64_t base,uint64_t id) {
  auto it=counts().registry.objects.find(base);
  if(it!=counts().registry.objects.end() && it->second.id==id)counts().registry.release(base);
}
void retire(Frame &frame,uint64_t mark=0) {
  for(auto it=frame.objects.begin();it!=frame.objects.end();) {
    if(it->second.serial>=mark){release(it->first,it->second.id);it=frame.objects.erase(it);}else ++it;
  }
}
Frame *find(uint64_t token){auto &state=frames;return !state.empty() && state.back().token==token?&state.back():nullptr;}
}
extern "C" uint64_t __swdb_object_scope_enter() {
  if(observerEntered)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  if(swdb_scopes::frames.size()>=swdb_live::budget()){counts().registry.object_budget_exhausted=true;return 0;}
  uint64_t token=swdb_scopes::next_token++;
  swdb_scopes::frames.push_back({token,1,{}});return token;
}
extern "C" void __swdb_object_scope_alloc(uint64_t token,uint64_t base,uint64_t bytes,uint32_t known) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto *frame=swdb_scopes::find(token);if(!frame)return;
  counts().registry.allocate(base,bytes,known);
  auto it=counts().registry.objects.find(base);
  if(it!=counts().registry.objects.end())frame->objects[base]={it->second.id,frame->next_serial++};
}
extern "C" void __swdb_object_scope_retire(uint64_t token,uint64_t base) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto *frame=swdb_scopes::find(token);if(!frame)return;
  auto it=frame->objects.find(base);
  if(it!=frame->objects.end()){swdb_scopes::release(base,it->second.id);frame->objects.erase(it);}
}
extern "C" uint64_t __swdb_object_scope_mark(uint64_t token) {
  if(observerEntered || !token)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto *frame=swdb_scopes::find(token);return frame?frame->next_serial:0;
}
extern "C" void __swdb_object_scope_restore(uint64_t token,uint64_t mark) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto *frame=swdb_scopes::find(token);if(frame)swdb_scopes::retire(*frame,mark);
}
extern "C" void __swdb_object_scope_leave(uint64_t token) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto &frames=swdb_scopes::frames;
  if(frames.empty() || frames.back().token!=token)return;
  swdb_scopes::retire(frames.back());frames.pop_back();
}

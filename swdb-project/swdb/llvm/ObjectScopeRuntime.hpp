// Optional scope callbacks. Included after Counts/ObserverScope; no address serialization.
// Updated: 2026-10-06 ET.
#pragma once
namespace swdb_scopes {
struct Frame {uint64_t token;std::map<uint64_t,uint64_t> objects;};
thread_local std::vector<Frame> frames;
uint64_t next_token=1;
void retire(Frame &frame) {
  for(auto &item:frame.objects) {
    auto it=counts().registry.objects.find(item.first);
    if(it!=counts().registry.objects.end() && it->second.id==item.second)counts().registry.release(item.first);
  }
}
}
extern "C" uint64_t __swdb_object_scope_enter() {
  if(observerEntered)return 0;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  if(swdb_scopes::frames.size()>=swdb_live::budget())return 0;
  uint64_t token=swdb_scopes::next_token++;
  swdb_scopes::frames.push_back({token,{}});return token;
}
extern "C" void __swdb_object_scope_alloc(uint64_t token,uint64_t base,uint64_t bytes,uint32_t known) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto &frames=swdb_scopes::frames;if(frames.empty() || frames.back().token!=token)return;
  counts().registry.allocate(base,bytes,known);
  auto it=counts().registry.objects.find(base);
  if(it!=counts().registry.objects.end())frames.back().objects[base]=it->second.id;
}
extern "C" void __swdb_object_scope_leave(uint64_t token) {
  if(observerEntered || !token)return;ObserverScope observer;
  std::lock_guard<std::mutex> lock(counts().mutex);
  auto &frames=swdb_scopes::frames;
  if(frames.empty() || frames.back().token!=token)return;
  swdb_scopes::retire(frames.back());frames.pop_back();
}

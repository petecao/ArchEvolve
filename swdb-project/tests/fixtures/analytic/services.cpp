// Created: 2026-10-06 ET. Native allocator shape fixture, not application evidence.
#include <cstdlib>
extern "C" __attribute__((noinline)) int services() {
  const size_t sizes[]={64,128,64};
  for(int i=0;i<3;++i){
    void *p=std::malloc(sizes[i]);
    if(!p)return 2;
    std::free(p);
  }
  return 0;
}
int main(){return services();}

// Created: 2026-10-06 ET. Logical lifetime fixture, not application evidence.
#include <cstdlib>
#include <cstring>
__attribute__((noinline)) void *operator new(size_t,void *p) noexcept {return p;}
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
volatile int sink;
extern "C" __attribute__((noinline)) int observe(const int *p) {
  int sum=0;
  for(int i=0;i<2;++i) sum+=p[i*16];
  return sum;
}
int main(int argc,char** argv) {
  int *a=(int*)std::calloc(48,sizeof(int));
  int *b=(int*)std::calloc(48,sizeof(int));
  if(!a || !b)return 2;
  if(argc>1 && std::strcmp(argv[1],"placement")==0)::operator new(sizeof(int),a+16);
  __swdb_begin();
  sink=observe(a)+observe(a+16)+observe(b);
  if(argc>1 && std::strcmp(argv[1],"reuse")==0){
    std::free(a);a=(int*)std::calloc(48,sizeof(int));
    if(!a)return 2;
    sink+=observe(a);
  }
  __swdb_end();
  if(argc>2){__swdb_begin();sink=observe(b);__swdb_end();}
  std::free(a);std::free(b);
  return sink;
}

#include <csetjmp>
#include <cstdlib>
#include <cstring>
// Bounded source-object contract fixture; no application evidence. Updated: 2026-10-06 ET.
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
extern "C" __attribute__((noinline)) int scope_reads(const volatile char *parent) {
  volatile char local[129] = {};
  int sum=0;
  for(int i=0;i<3;++i)sum+=parent[i*64]+local[i*64];
  return sum;
}
extern "C" __attribute__((noinline)) int scope_dynamic(int n) {
  volatile char local[n];
  int sum=0;
  for(int i=0;i<3;++i)local[i*64]=0;
  for(int i=0;i<3;++i)sum+=local[i*64];
  return sum;
}
extern "C" __attribute__((noinline)) void scope_thrower() {
  volatile char local[129]={};
  if(local[0]==0)throw 1;
}
extern "C" __attribute__((noinline)) int scope_recover() {
  try {scope_thrower();} catch(int) {}
  volatile char post[129]={};
  int sum=0;
  for(int i=0;i<3;++i)sum+=post[i*64];
  return sum;
}
volatile char declared_global[129]={};
extern "C" __attribute__((noinline)) int scope_global() {
  int sum=0;
  for(int i=0;i<3;++i)sum+=declared_global[i*64];
  return sum;
}
std::jmp_buf jump_target;
extern "C" __attribute__((noinline)) void scope_escape(){std::longjmp(jump_target,1);}
extern "C" __attribute__((noinline)) int scope_nonlocal(){
  if(setjmp(jump_target)==0)scope_escape();
  volatile char post[129]={};int sum=0;
  for(int i=0;i<3;++i)sum+=post[i*64];
  return sum;
}
int main(int argc,char **argv) {
  volatile char parent[129] = {};
  __swdb_begin();
  int result=argc>1 && std::strcmp(argv[1],"nonlocal")==0?scope_nonlocal():argc>1 && std::strcmp(argv[1],"global")==0?scope_global():argc>1 && std::strcmp(argv[1],"recover")==0?scope_recover():argc>1 && std::strcmp(argv[1],"dynamic")==0?scope_dynamic(std::atoi(argv[2])):scope_reads(parent);
  __swdb_end();
  return result;
}

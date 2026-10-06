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
int main(int argc,char **argv) {
  volatile char parent[129] = {};
  __swdb_begin();
  int result=argc>1 && std::strcmp(argv[1],"dynamic")==0?scope_dynamic(std::atoi(argv[2])):scope_reads(parent);
  __swdb_end();
  return result;
}

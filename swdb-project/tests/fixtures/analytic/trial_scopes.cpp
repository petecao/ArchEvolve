// Independent source-count fixture; no application timing. Updated: 2026-10-06 ET.
#include <cstdlib>
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
__attribute__((noinline)) void scoped_kernel(int n) {
  volatile int *data = static_cast<int *>(std::malloc(n * sizeof(int)));
  for (int i=0;i<n;++i) data[i]=i;
  std::free(const_cast<int *>(data));
}
int main(){for(int trial=0;trial<2;++trial){__swdb_begin();scoped_kernel(4*(trial+1));__swdb_end();}}

// Actual libomp ABI referent fixture; no application evidence. Updated: 2026-10-06 ET.
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
extern "C" __attribute__((noinline)) void scope_worker(int *parent) {
#pragma omp parallel for num_threads(1)
  for(int i=0;i<3;++i)parent[i*16]+=1;
}
int main() {
  int parent[33]={};
  __swdb_begin();scope_worker(parent);__swdb_end();
  return parent[0]!=1;
}

// Selected-event proof; all state preparation/cleanup stays outside its ROI.2026-10-06 ET.
#define SWDB_OPENMP_COUNT_INLINE
#include "CpuOpenmpWork.h"
extern "C" __attribute__((noinline)) void service_openmp_matrix(int p,std::int32_t gtid,std::uint64_t n,bool invoke) {
  SwdbOmpState s(gtid);
  for(std::uint64_t i=0;i<n;++i) {
    swdb_openmp_prepare(p,s);
    s.result=invoke ? swdb_openmp_event(p,s) : swdb_openmp_outside(p,s);
    swdb_openmp_cleanup(p,s);
  }
}
struct Task { std::uint64_t n;bool invoke; };
static void team(std::int32_t *gtid,std::int32_t *,Task *t) {
  if(omp_get_num_threads()!=1 || omp_get_level()!=1 || omp_get_active_level()!=0)std::abort();
  for(int p=6;p<22;++p)service_openmp_matrix(p,*gtid,t->n,t->invoke);
}
int main(int argc,char **argv) {
  if(argc!=3)return 2;Task t={std::strtoull(argv[1],0,10),std::atoi(argv[2])!=0};
  for(int p=0;p<6;++p)service_openmp_matrix(p,0,t.n,t.invoke);
  __kmpc_fork_call(&swdb_loc2,1,reinterpret_cast<SwdbMicrotask>(team),&t);
}

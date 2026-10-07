// Uninstrumented per-event probes and empty-window drivers. Created2026-10-06 ET.
#include "CpuOpenmpWork.h"
#include <chrono>
#include <iomanip>
#include <iostream>
#include <string>
struct Task { int p;std::uint64_t n;bool invoke;double seconds;int team_size,level,active_level;std::uint64_t checked,return_sum; };
static void measure(Task &t,std::int32_t gtid) {
  t.team_size=omp_get_num_threads();t.level=omp_get_level();t.active_level=omp_get_active_level();
  if(t.team_size!=1 || (t.p>=6 && (t.level!=1 || t.active_level!=0)))std::abort();
  SwdbOmpState s(gtid);double sum=0.;std::uint64_t checked=0,return_sum=0;
  for(std::uint64_t i=0;i<t.n;++i) {
    swdb_openmp_prepare(t.p,s);
    auto begin=std::chrono::steady_clock::now();
    if(t.invoke)s.result=swdb_openmp_event(t.p,s);
    auto end=std::chrono::steady_clock::now();
    if(!t.invoke)s.result=swdb_openmp_outside(t.p,s);
    swdb_openmp_cleanup(t.p,s);++checked;return_sum+=static_cast<std::uint64_t>(s.result);
    sum+=std::chrono::duration<double>(end-begin).count();
  }
  t.seconds=sum;t.checked=checked;t.return_sum=return_sum;
}
static void team(std::int32_t *gtid,std::int32_t *,Task *t) { measure(*t,*gtid); }
static void run(Task &t) {
  if(t.p<6)measure(t,0);
  else __kmpc_fork_call(&swdb_loc2,1,reinterpret_cast<SwdbMicrotask>(team),&t);
}
int main(int argc,char **argv) {
  if(argc!=4)return 2;int p=std::atoi(argv[1]);std::uint64_t n=std::strtoull(argv[2],0,10);bool first=std::atoi(argv[3])!=0;
  if(p<0 || p>=22 || n==0 || n>16777216)return 2;
  Task warm={p,16,true,0.,0,0,0,0};run(warm);warm.invoke=false;run(warm);
  Task a={p,n,true,0.,0,0,0,0},b={p,n,false,0.,0,0,0,0};
  if(first){run(a);run(b);}else{run(b);run(a);}
  std::cout<<std::setprecision(17)<<"{\"events\":"<<n<<",\"gross_seconds\":"<<a.seconds<<",\"driver_seconds\":"<<b.seconds
    <<",\"order\":\""<<(first?"service_first":"driver_first")<<"\",\"checked_legal_sequences\":"<<a.checked
    <<",\"driver_checked_legal_sequences\":"<<b.checked<<",\"event_return_sum\":"<<a.return_sum<<",\"driver_event_return_sum\":"<<b.return_sum<<",\"team_size\":"<<a.team_size<<",\"omp_level\":"<<a.level
    <<",\"omp_active_level\":"<<a.active_level<<",\"probe_kind\":\"per_event_steady_clock_empty_window\"}\n";
}

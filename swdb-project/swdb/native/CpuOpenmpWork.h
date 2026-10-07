// Legal serialized-team OpenMP event probes. Created2026-10-06 ET.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdlib>
struct SwdbIdent { std::int32_t reserved1,flags,reserved2,reserved3; const char *source; };
typedef void (*SwdbMicrotask)(std::int32_t *,std::int32_t *,...);
extern "C" {
void __kmpc_fork_call(const SwdbIdent *,std::int32_t,SwdbMicrotask,...);
void __kmpc_barrier(const SwdbIdent *,std::int32_t);
void __kmpc_for_static_init_4(const SwdbIdent *,std::int32_t,std::int32_t,std::int32_t *,std::int32_t *,std::int32_t *,std::int32_t *,std::int32_t,std::int32_t);
void __kmpc_for_static_init_8(const SwdbIdent *,std::int32_t,std::int32_t,std::int32_t *,std::int64_t *,std::int64_t *,std::int64_t *,std::int64_t,std::int64_t);
void __kmpc_for_static_fini(const SwdbIdent *,std::int32_t);
std::int32_t __kmpc_reduce_nowait(const SwdbIdent *,std::int32_t,std::int32_t,std::size_t,void *,void (*)(void *,void *),std::int32_t *);
void __kmpc_end_reduce_nowait(const SwdbIdent *,std::int32_t,std::int32_t *);
std::int32_t __kmpc_single(const SwdbIdent *,std::int32_t);
void __kmpc_end_single(const SwdbIdent *,std::int32_t);
void __kmpc_dispatch_init_4(const SwdbIdent *,std::int32_t,std::int32_t,std::int32_t,std::int32_t,std::int32_t,std::int32_t);
void __kmpc_dispatch_init_8(const SwdbIdent *,std::int32_t,std::int32_t,std::int64_t,std::int64_t,std::int64_t,std::int64_t);
std::int32_t __kmpc_dispatch_next_4(const SwdbIdent *,std::int32_t,std::int32_t *,std::int32_t *,std::int32_t *,std::int32_t *);
std::int32_t __kmpc_dispatch_next_8(const SwdbIdent *,std::int32_t,std::int32_t *,std::int64_t *,std::int64_t *,std::int64_t *);
void __kmpc_dispatch_deinit(const SwdbIdent *,std::int32_t);
int omp_get_num_threads(); int omp_get_level(); int omp_get_active_level();
}
static const SwdbIdent swdb_loc2={0,2,0,0,";swdb;event;1;1;;"};
static const SwdbIdent swdb_loc18={0,18,0,0,";swdb;event;1;1;;"};
static const SwdbIdent swdb_loc34={0,34,0,0,";swdb;event;1;1;;"};
static const SwdbIdent swdb_loc322={0,322,0,0,";swdb;event;1;1;;"};
static const SwdbIdent swdb_loc514={0,514,0,0,";swdb;event;1;1;;"};
struct SwdbOmpState {
  std::int32_t gtid,last,lo4,hi4,stride4,result;
  std::int64_t lo8,hi8,stride8,reduced;
  void *reduction[1]; std::int32_t lock[8];
  explicit SwdbOmpState(std::int32_t g):gtid(g),last(0),lo4(0),hi4(31),stride4(1),result(0),lo8(0),hi8(31),stride8(1),reduced(1),reduction{&reduced},lock{} {}
};
static void swdb_empty_task(std::int32_t *,std::int32_t *,...) { asm volatile("" ::: "memory"); }
static void swdb_reduce(void *lhs,void *rhs) {
  auto a=static_cast<void **>(lhs),b=static_cast<void **>(rhs);
  *static_cast<std::int64_t *>(a[0])+=*static_cast<std::int64_t *>(b[0]);
}
#if defined(SWDB_OPENMP_COUNT_INLINE)
#define SWDB_OMP_VIS __attribute__((always_inline)) inline
#else
#define SWDB_OMP_VIS __attribute__((noinline))
#endif
static SWDB_OMP_VIS std::int32_t swdb_openmp_event(int p,SwdbOmpState &s) {
  void *a=&s.reduced;
  switch(p) {
    case 0: __kmpc_fork_call(&swdb_loc2,2,swdb_empty_task,a,a);break; // SWDB_OMP_EVENT 0
    case 1: __kmpc_fork_call(&swdb_loc2,3,swdb_empty_task,a,a,a);break; // SWDB_OMP_EVENT 1
    case 2: __kmpc_fork_call(&swdb_loc2,4,swdb_empty_task,a,a,a,a);break; // SWDB_OMP_EVENT 2
    case 3: __kmpc_fork_call(&swdb_loc2,5,swdb_empty_task,a,a,a,a,a);break; // SWDB_OMP_EVENT 3
    case 4: __kmpc_fork_call(&swdb_loc2,7,swdb_empty_task,a,a,a,a,a,a,a);break; // SWDB_OMP_EVENT 4
    case 5: __kmpc_fork_call(&swdb_loc2,8,swdb_empty_task,a,a,a,a,a,a,a,a);break; // SWDB_OMP_EVENT 5
    case 6: __kmpc_barrier(&swdb_loc34,s.gtid);break; // SWDB_OMP_EVENT 6
    case 7: __kmpc_barrier(&swdb_loc322,s.gtid);break; // SWDB_OMP_EVENT 7
    case 8: __kmpc_for_static_init_4(&swdb_loc514,s.gtid,34,&s.last,&s.lo4,&s.hi4,&s.stride4,1,1);break; // SWDB_OMP_EVENT 8
    case 9: __kmpc_for_static_init_8(&swdb_loc514,s.gtid,34,&s.last,&s.lo8,&s.hi8,&s.stride8,1,1);break; // SWDB_OMP_EVENT 9
    case 10: __kmpc_for_static_fini(&swdb_loc514,s.gtid);break; // SWDB_OMP_EVENT 10
    case 11: return __kmpc_reduce_nowait(&swdb_loc18,s.gtid,1,8,s.reduction,swdb_reduce,s.lock); // SWDB_OMP_EVENT 11
    case 12: __kmpc_end_reduce_nowait(&swdb_loc18,s.gtid,s.lock);break; // SWDB_OMP_EVENT 12
    case 13: return __kmpc_single(&swdb_loc2,s.gtid); // SWDB_OMP_EVENT 13
    case 14: __kmpc_end_single(&swdb_loc2,s.gtid);break; // SWDB_OMP_EVENT 14
    case 15: __kmpc_dispatch_init_4(&swdb_loc2,s.gtid,1073741859,0,31,1,1024);break; // SWDB_OMP_EVENT 15
    case 16: __kmpc_dispatch_init_8(&swdb_loc2,s.gtid,1073741859,0,31,1,64);break; // SWDB_OMP_EVENT 16
    case 17: return __kmpc_dispatch_next_4(&swdb_loc2,s.gtid,&s.last,&s.lo4,&s.hi4,&s.stride4); // SWDB_OMP_EVENT 17
    case 18: return __kmpc_dispatch_next_4(&swdb_loc2,s.gtid,&s.last,&s.lo4,&s.hi4,&s.stride4); // SWDB_OMP_EVENT 18
    case 19: return __kmpc_dispatch_next_8(&swdb_loc2,s.gtid,&s.last,&s.lo8,&s.hi8,&s.stride8); // SWDB_OMP_EVENT 19
    case 20: return __kmpc_dispatch_next_8(&swdb_loc2,s.gtid,&s.last,&s.lo8,&s.hi8,&s.stride8); // SWDB_OMP_EVENT 20
    case 21: __kmpc_dispatch_deinit(&swdb_loc2,s.gtid);break; // SWDB_OMP_EVENT 21
    default:std::abort();
  }
  return 0;
}
#undef SWDB_OMP_VIS
static __attribute__((noinline)) void swdb_openmp_prepare(int p,SwdbOmpState &s) {
  s.lo4=0;s.hi4=31;s.stride4=1;s.lo8=0;s.hi8=31;s.stride8=1;s.last=0;
  if(p==10)swdb_openmp_event(9,s);
  if(p==12 && swdb_openmp_event(11,s)!=1)std::abort();
  if(p==14 && swdb_openmp_event(13,s)!=1)std::abort();
  if(p==17 || p==18 || p==21)swdb_openmp_event(15,s);
  if(p==19 || p==20)swdb_openmp_event(16,s);
  if(p==18 && swdb_openmp_event(17,s)!=1)std::abort();
  if(p==20 && swdb_openmp_event(19,s)!=1)std::abort();
  if(p==21)while(swdb_openmp_event(17,s)){}
}
static __attribute__((noinline)) void swdb_openmp_cleanup(int p,SwdbOmpState &s) {
  if(p==8 || p==9)swdb_openmp_event(10,s);
  if(p==11) { if(s.result!=1)std::abort();swdb_openmp_event(12,s); }
  if(p==13) { if(s.result!=1)std::abort();swdb_openmp_event(14,s); }
  if(p==15 || p==17) { while(swdb_openmp_event(17,s)){};swdb_openmp_event(21,s); }
  if(p==16 || p==19) { while(swdb_openmp_event(19,s)){};swdb_openmp_event(21,s); }
  if(p==18 || p==20)swdb_openmp_event(21,s);
  if((p==17 || p==19) && s.result!=1)std::abort();
  if((p==18 || p==20) && s.result!=0)std::abort();
}
// Driver executes the same legal event outside the selected count/timing window.
static __attribute__((noinline)) std::int32_t swdb_openmp_outside(int p,SwdbOmpState &s) { return swdb_openmp_event(p,s); }

// Static ABI projection fixture with pure LLVM intrinsics between OpenMP calls; never linked
// or run. Created: 2026-10-12 ET (cpud ticket 01). Characterize counts llvm.ctlz/ctpop/fabs
// as operations, not call sites, so the projector must skip them too.
struct Ident { int reserved, flags, reserved2, reserved3; const char *source; };
static const Ident ident = {0, 514, 0, 0, "fixture"};
extern "C" {
void __kmpc_fork_call(const void *, int, void *, ...);
void __kmpc_for_static_init_8(const void *, int, int, void *, void *, void *, void *, long, long);
void __kmpc_dispatch_init_4(const void *, int, int, int, int, int, int);
int __kmpc_reduce_nowait(const void *, int, int, unsigned long, void *, void *, void *);
void __kmpc_barrier(const void *, int);
int __kmpc_global_thread_num(const void *);
}
void fixture_openmp(int schedule, int tid, long chunk, unsigned long bits, double x) {
  __kmpc_fork_call(&ident, 2, nullptr, nullptr, nullptr);
  long width = __builtin_clzll(bits) + __builtin_popcountll(bits);
  __kmpc_for_static_init_8(&ident, tid, 34, nullptr, nullptr, nullptr, nullptr, 1, chunk + width);
  int scaled = (int)__builtin_fabs(x);
  __kmpc_dispatch_init_4(&ident, tid, schedule, 0, 63, 1, 7);
  __kmpc_reduce_nowait(&ident, tid, 1, 128, nullptr, nullptr, nullptr);
  __kmpc_barrier(&ident, tid + scaled);
  __kmpc_global_thread_num(&ident);
  __kmpc_barrier(&ident, tid); // Hand fixture marks this distinct site unexecuted.
}

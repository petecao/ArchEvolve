// Selected-root fixture with an excluded opaque helper. Updated: 2026-10-06 ET.
#include "openmp_abi.cpp"
__attribute__((noinline)) void excluded_prepare(int *sink) {
  *sink = __kmpc_global_thread_num(&ident);
}

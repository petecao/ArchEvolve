// PROTOTYPE (ticket 08), first test: does crux-llvm accept the strict layer as written?
// One stream load + wait + CPU read; nothing about BFS.
#include <MAA_functional.hpp>
#include <crucible.h>
#undef check  // crucible.h defines check(e); the strict layer has its own swdb_strict::check

static int32_t mem[4] = {5, 6, 7, 8};
int main() {
  alloc_MAA(); init_MAA();
  add_mem_region(mem, mem + 4);
  int t = get_new_tile<int>(), lo = get_new_reg<int>(), hi = get_new_reg<int>(), one = get_new_reg<int>();
  maa_const<int>(0, lo); maa_const<int>(2, hi); maa_const<int>(1, one);
  maa_stream_load<int>(mem, lo, hi, one, t);
  wait_ready(t);
  crucible_assert(get_cacheable_tile_pointer<int>(t)[1] == 6, __FILE__, __LINE__);
  return 0;
}

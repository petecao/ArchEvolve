// Producer-side harness (2026-09-27 ET), NOT a candidate and NOT DX100 evidence.
// Builds the HW test client's reference helper against the pinned DX100 functional
// model (MAA_functional.hpp, selected by MAA_utility.hpp without GEM5). The functional
// model names its region call m5_add_mem_region, so this harness supplies the gem5
// API's add_mem_region/clear_mem_region region numbering (first user region 6).
#include <MAA_utility.hpp>
static int func_region_count = 6;
static void add_mem_region(void *s, void *e) { m5_add_mem_region(s, e, func_region_count++); }
#define clear_mem_region() (clear_mem_region(), func_region_count = 6, (void)0)
#include "reference-bfs.cc"

// Ticket 06 spike (b), 2026-10-14 ET. THROWAWAY. Tests of the per-call summaries themselves
// (test_summaries.saw), on shape 95 with concrete inputs: frontier {0, 1}, offsets [0, 1, 3, 3]
// (edges 0->2, 1->2, 1->0). The range loop must return 2, 1, 0 lanes on three calls (210):
//   a: range loops only;  b: with TDStepMAA's loop body between them (gathers, alu, store, waits).
#include "unit_common.hpp"

// Never verified: makes every summarized symbol present in the module (make_overrides needs them).
void swdb_test_symbols() { swdb_probe_tile_read(0); swdb_probe_cpu(0, 0); }

static void setup() {
  maa_const<int>(1, 2); maa_const<int>(0, 3); maa_const<int>(0, 0); maa_const<int>(2, 1);
  maa_stream_load(g_queue, 0, 1, 2, 0);
  maa_indirect_load<int>(g_offsets, 0, 1);
  maa_indirect_load<int>(g_offsets + 1, 0, 2);
  maa_const<int>(0, 6); maa_const<int>(-1, 7);
}

int swdb_test_range_only() {
  setup();
  int c[3];
  for (int k = 0; k < 3; ++k) { maa_range_loop<int>(6, 7, 1, 2, 2, 6, 7); wait_ready(7); c[k] = get_tile_size(7); }
  return c[0] * 100 + c[1] * 10 + c[2];
}

int swdb_test_range_body() {
  setup();
  int c[3];
  for (int k = 0; k < 3; ++k) {
    maa_range_loop<int>(6, 7, 1, 2, 2, 6, 7);
    maa_indirect_load<int>(g_neighbors, 7, 0);
    maa_indirect_load<int>(g_queue, 6, 3);
    wait_ready(7);
    c[k] = get_tile_size(7);
    if (c[k] == 0) continue;
    maa_indirect_load<int>(g_parent, 0, 7);
    maa_alu_scalar<int>(7, 3, 4, Operation_t::LT_OP);
    maa_indirect_store_vector<int>(g_parent, 0, 3, 4, 5);
    wait_ready(3);
  }
  return c[0] * 100 + c[1] * 10 + c[2];
}

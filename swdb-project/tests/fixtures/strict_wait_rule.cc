// Strict-layer wait-rule scenarios. Created: 2026-10-09 ET (gem5 wait rule, research 14).
// Built twice by tests/test_strict_wait_rule.py: without and with -DSWDB_STRICT_WAIT_RULE_GEM5.
// Usage: strict_wait_rule <scenario>; prints "key=value" lines; a strict check exits 86.
#include <MAA_functional.hpp>
#include <cstdio>
#include <string>
#include <vector>

static std::vector<int32_t> memory(TILE_SIZE * 8, 0);
static void put(int tile, const std::vector<int32_t> &values) {
  int32_t *p = get_cacheable_tile_pointer<int32_t>(tile);
  for (size_t k = 0; k < values.size(); ++k) p[k] = values[k];
  set_tile_size(tile, uint16_t(values.size()));
}
static void show(const char *key, long value) { std::printf("%s=%ld\n", key, value); }
static long first(int tile) { return long(get_cacheable_tile_pointer<int32_t>(tile)[0]); }

int main(int argc, char **argv) {
  const std::string scenario = argc > 1 ? argv[1] : "";
  alloc_MAA(); init_MAA();
  add_mem_region(memory.data(), memory.data() + memory.size());
  int t[8], r[8];
  for (int &x : t) x = get_new_tile<int>();
  for (int &x : r) x = get_new_reg<int>();
  // The authors' TDStepMAA critical section (bfs.cc:170-181): tile7 = parent[tile0]; tile4 = tile7 < 0;
  // if tile4: tile5 = parent[tile0], parent[tile0] = tile3; then a wait (or none) and CPU reads.
  auto store_section = [&]() {
    for (int k = 0; k < 4; ++k) memory[k] = k == 2 ? 7 : -1 - k;        // parent[]: vertex 2 visited
    put(t[0], {0, 1, 2, 3});                                             // v
    put(t[3], {10, 11, 12, 13});                                         // inner u
    maa_const<int>(0, r[0]);
    maa_indirect_load<int>(memory.data(), t[0], t[7]);
    maa_alu_scalar<int>(t[7], r[0], t[4], Operation_t::LT_OP);
    maa_indirect_store_vector<int>(memory.data(), t[0], t[3], t[4], t[5]);
  };
  if (scenario == "store_source_wait") {           // (a) the authors' unmodified wait_ready(tile3)
    store_section();
    wait_ready(t[3]);
    show("ready5", get_tile_ready(t[5])); show("tile5_0", first(t[5])); show("tile4_0", first(t[4]));
  } else if (scenario == "store_result_wait") {    // calibration 1.1's patched wait_ready(tile5)
    store_section();
    wait_ready(t[5]);
    show("ready5", get_tile_ready(t[5])); show("tile5_0", first(t[5])); show("tile4_0", first(t[4]));
  } else if (scenario == "store_no_wait") {        // (b) the wait deleted
    store_section();
    show("ready5", get_tile_ready(t[5])); show("tile5_0", first(t[5])); show("size5", get_tile_size(t[5]));
  } else if (scenario == "source_ready_before_wait") {  // a store's source tile is not ready while it runs
    store_section();
    show("ready3", get_tile_ready(t[3]));
    wait_ready(t[3]);
    show("ready3_after", get_tile_ready(t[3]));
  } else if (scenario == "condition_only_wait") {  // (c) a wait on a tile named only as a condition
    put(t[1], {1, 0, 1, 1});                                             // condition, CPU-written
    maa_const<int>(0, r[1]); maa_const<int>(4, r[2]); maa_const<int>(1, r[3]);
    maa_stream_load<int>(memory.data(), r[1], r[2], r[3], t[2], t[1]);
    wait_ready(t[1]);
    show("ready_dst", get_tile_ready(t[2])); show("ready_cond", get_tile_ready(t[1]));
    show("size_dst", get_tile_size(t[2]));
    wait_ready(t[2]);
    show("ready_dst_after", get_tile_ready(t[2]));
  } else if (scenario == "range_filled" || scenario == "range_unfilled") {  // (d)
    const int32_t end = scenario == "range_filled" ? 3 * TILE_SIZE : 10;
    memory[0] = 0; memory[1] = end;                                      // one row [0, end)
    put(t[0], {0});
    maa_indirect_load<int>(memory.data(), t[0], t[1]);                   // min = memory[0]
    maa_indirect_load<int>(memory.data() + 1, t[0], t[2]);               // max = memory[1]
    maa_const<int>(0, r[4]); maa_const<int>(-1, r[5]); maa_const<int>(1, r[2]);
    maa_range_loop<int>(r[4], r[5], t[1], t[2], r[2], t[6], t[7]);       // A: rows t6, columns t7
    maa_range_loop<int>(r[4], r[5], t[1], t[2], r[2], t[4], t[5]);       // B: reads A's continuation
    wait_ready(t[5]);
    show("size_b", get_tile_size(t[5]));
    show("ready_min", get_tile_ready(t[1]));      // its gather is followed only through an unfilled loop
    show("ready_a", get_tile_ready(t[7]));        // A is B's register producer: always followed
  } else if (scenario == "read_offload_chunk") {   // library/dx100/bfs_read_offload.inc:30-44, one chunk
    int32_t *queue = memory.data() + 4 * TILE_SIZE, *neighbors = memory.data() + TILE_SIZE;
    memory[0] = 0; memory[1] = 3 * TILE_SIZE; queue[0] = 0;              // vertex 0: 3 tiles of edges
    maa_const<int>(0, r[0]); maa_const<int>(1, r[1]); maa_const<int>(1, r[2]);
    maa_stream_load<int>(queue, r[0], r[1], r[2], t[0]);
    maa_indirect_load<int>(memory.data(), t[0], t[1]);
    maa_indirect_load<int>(memory.data() + 1, t[0], t[2]);
    maa_const<int>(0, r[4]); maa_const<int>(-1, r[5]);
    maa_range_loop<int>(r[4], r[5], t[1], t[2], r[2], t[6], t[7]);       // fills its tile
    wait_ready(t[7]);
    maa_indirect_load<int>(neighbors, t[7], t[0]);                       // overwrites t0 (WAR on the gathers)
    maa_indirect_load<int>(queue, t[6], t[3]);
    maa_indirect_load<int>(memory.data(), t[0], t[5]);
    wait_ready(t[3]); wait_ready(t[5]);
    show("ready0", get_tile_ready(t[0])); show("ready3", get_tile_ready(t[3])); show("ready5", get_tile_ready(t[5]));
  } else if (scenario == "stall_source" || scenario == "stall_condition") {  // rule 5 (IF.cc:193-212)
    for (int k = 0; k < 8; ++k) memory[k] = 100 + k;
    put(t[0], {1, 2, 3});
    maa_const<int>(0, r[1]); maa_const<int>(3, r[2]); maa_const<int>(1, r[3]);
    if (scenario == "stall_source") {
      maa_indirect_load<int>(memory.data(), t[0], t[1]);                 // reads t0 as its index
      maa_stream_load<int>(memory.data(), r[1], r[2], r[3], t[0]);       // then overwrites t0
    } else {
      put(t[3], {1, 0, 1});
      maa_stream_load<int>(memory.data(), r[1], r[2], r[3], t[1], t[3]); // reads t3 as its condition
      maa_alu_scalar<int>(t[0], r[1], t[3], Operation_t::ADD_OP);        // then overwrites t3
    }
    show("ready1", get_tile_ready(t[1])); show("first1", first(t[1]));
  } else if (scenario == "constant_hold") {        // (e) a constant write to a register a command reads
    for (int k = 0; k < 8; ++k) memory[k] = 100 + k;
    maa_const<int>(0, r[1]); maa_const<int>(4, r[2]); maa_const<int>(1, r[3]);
    maa_stream_load<int>(memory.data(), r[1], r[2], r[3], t[2]);
    maa_const<int>(8, r[2]);                                             // no wait in between
    show("ready_dst", get_tile_ready(t[2])); show("size_dst", get_tile_size(t[2]));
    show("dst_0", first(t[2]));
  } else {
    std::fprintf(stderr, "unknown scenario\n");
    return 2;
  }
  return 0;
}

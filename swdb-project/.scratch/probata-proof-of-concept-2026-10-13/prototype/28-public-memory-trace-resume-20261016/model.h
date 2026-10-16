/* 2026-10-16 ET. CBMC synthetic trace model, deliberately no real API body.
 * Abstract cells 0/1 are disjoint physical lines; their registered region IDs
 * are respectively 0/1. A trace is one fixed sequential event order over two
 * thread IDs, four physical tiles, at most two commands and one later CPU
 * write per unfinished gather. Four independent initialized harness cells supply
 * at most four fresh nondeterministic choices. Values are int in 0..31, never FP
 * or bit images. The choice budget is checked, never silently recycled.
 * No completion is inferred from a known value. Ready is a LOGICAL ghost query:
 * the pinned header's wait_ready blocks, and has no get_tile_ready operation.
 * All domains/capacities use checked obligations; only choice-bit selection is
 * nondeterministic. No source entry precondition or desired result is assumed.
 */
#define TR_CHECK(c, r) SWDB_CHECK((c), DX_RULE(r))
static void tr_thread(int thread) { TR_CHECK(thread == 0 || thread == 1,"thread_domain"); }
static void tr_cell(int cell) { TR_CHECK(cell == 0 || cell == 1,"cell_domain"); }
static void tr_value(int value) { TR_CHECK(0 <= value && value <= 31,"value_domain"); }
static int tr_mask(int tile, int bytes) {
  TR_CHECK(0 <= tile && tile < 4,"tile_domain");
  TR_CHECK(bytes == 4 || bytes == 8,"width_domain");
  TR_CHECK(bytes == 4 || tile < 3,"pair_domain");
  return (bytes == 4 ? 1 : 3) << tile;
}
static int tr_owner(int tile) {
  return tile == 0 ? tr_owner0 : tile == 1 ? tr_owner1 : tile == 2 ? tr_owner2 : tr_owner3;
}
static void tr_owned(int thread, int mask) {
  tr_thread(thread);

  if (mask & 1) TR_CHECK(tr_owner0 == thread,"tile_ownership");
  if (mask & 2) TR_CHECK(tr_owner1 == thread,"tile_ownership");
  if (mask & 4) TR_CHECK(tr_owner2 == thread,"tile_ownership");
  if (mask & 8) TR_CHECK(tr_owner3 == thread,"tile_ownership");
}
static int tr_pick(void) {
  SWDB_CHECK(0 <= tr_picks && tr_picks < 4,"swdb.ghost_capacity");
  int draw = tr_picks == 0 ? dx_tile_data[0][0] : tr_picks == 1 ? dx_tile_data[1][0] :
             tr_picks == 2 ? dx_tile_data[2][0] : dx_tile_data[3][0];
  tr_picks = tr_picks + 1; return (int)((unsigned int)draw % 2u);
}
static int tr_memory(int cell) { return cell == 0 ? tr_mem0 : tr_mem1; }
static void tr_set_memory(int cell, int value) { if (cell == 0) tr_mem0 = value; else tr_mem1 = value; }
static void tr_cover0(void) {
  if (tr_c0_pending) {
    if (tr_c0_access == 1) {
      int pick = tr_c0_writes ? tr_pick() : 0;
      tr_c0_result = pick ? tr_c0_later : tr_c0_issue;
    } else {
      tr_set_memory(tr_c0_cell, tr_c0_value);
    }
    tr_c0_pending = 0;
  }
}
static void tr_cover1(void) {
  if (tr_c1_pending) {
    if (tr_c1_access == 1) {
      int pick = tr_c1_writes ? tr_pick() : 0;
      tr_c1_result = pick ? tr_c1_later : tr_c1_issue;
    } else {
      tr_set_memory(tr_c1_cell, tr_c1_value);
    }
    tr_c1_pending = 0;
  }
}
static void swdb_dx_init(void) {
  tr_count = 0; tr_picks = 0; tr_mem0 = 0; tr_mem1 = 0;
  tr_owner0 = -1;
  tr_owner1 = -1;
  tr_owner2 = -1;
  tr_owner3 = -1;
  tr_c0_pending = 0;
  tr_c0_thread = 0;
  tr_c0_access = 0;
  tr_c0_region = 0;
  tr_c0_cell = 0;
  tr_c0_tile = 0;
  tr_c0_mask = 0;
  tr_c0_value = 0;
  tr_c0_issue = 0;
  tr_c0_later = 0;
  tr_c0_writes = 0;
  tr_c0_result = 0;
  tr_c1_pending = 0;
  tr_c1_thread = 0;
  tr_c1_access = 0;
  tr_c1_region = 0;
  tr_c1_cell = 0;
  tr_c1_tile = 0;
  tr_c1_mask = 0;
  tr_c1_value = 0;
  tr_c1_issue = 0;
  tr_c1_later = 0;
  tr_c1_writes = 0;
  tr_c1_result = 0;
}
static void swdb_dx_check_exit(void) {
  SWDB_CHECK(!tr_c0_pending && !tr_c1_pending,"swdb.dx100_memory_domain");
}
int swdb_t28_claim(int thread, int tile, int bytes) {
  tr_thread(thread);
  int mask = tr_mask(tile, bytes);
  if (mask & 1) TR_CHECK(tr_owner0 == -1,"tile_already_owned");
  if (mask & 2) TR_CHECK(tr_owner1 == -1,"tile_already_owned");
  if (mask & 4) TR_CHECK(tr_owner2 == -1,"tile_already_owned");
  if (mask & 8) TR_CHECK(tr_owner3 == -1,"tile_already_owned");
  if (mask & 1) tr_owner0 = thread;
  if (mask & 2) tr_owner1 = thread;
  if (mask & 4) tr_owner2 = thread;
  if (mask & 8) tr_owner3 = thread;
  return 0;
}
static void tr_cpu_access(int thread, int cell, int write) {
  tr_thread(thread); tr_cell(cell);
  if (tr_c0_pending && tr_c0_cell == cell) {
    TR_CHECK(tr_c0_access != 2,"store_footprint_cpu_access");
    if (write) TR_CHECK(tr_c0_thread != thread,"same_thread_read_footprint_write");
  }
  if (tr_c1_pending && tr_c1_cell == cell) {
    TR_CHECK(tr_c1_access != 2,"store_footprint_cpu_access");
    if (write) TR_CHECK(tr_c1_thread != thread,"same_thread_read_footprint_write");
  }
}
int swdb_t28_cpu_read(int thread, int cell) {
  tr_cpu_access(thread, cell, 0); return tr_memory(cell);
}
int swdb_t28_cpu_write(int thread, int cell, int value) {
  tr_cpu_access(thread, cell, 1); tr_value(value);
  if (tr_c0_pending && tr_c0_access == 1 && tr_c0_cell == cell) {
    SWDB_CHECK(tr_c0_writes == 0,"swdb.ghost_capacity");
    tr_c0_later = value; tr_c0_writes = 1;
  }
  if (tr_c1_pending && tr_c1_access == 1 && tr_c1_cell == cell) {
    SWDB_CHECK(tr_c1_writes == 0,"swdb.ghost_capacity");
    tr_c1_later = value; tr_c1_writes = 1;
  }
  tr_set_memory(cell, value); return 0;
}
int swdb_t28_cpu_cas(int thread, int cell, int expected, int desired) {
  tr_value(expected); tr_value(desired);
  int actual = swdb_t28_cpu_read(thread, cell);
  if (actual == expected) { swdb_t28_cpu_write(thread, cell, desired); return 1; }
  return 0;
}
int swdb_t28_issue(int thread, int access, int region, int cell, int tile, int bytes, int value) {
  tr_thread(thread); tr_cell(cell); tr_value(value);
  TR_CHECK(access == 1 || access == 2,"access_domain");
  TR_CHECK(region == cell,"region_footprint_correspondence");
  int mask = tr_mask(tile, bytes); tr_owned(thread, mask);
  SWDB_CHECK(tr_count < 2,"swdb.ghost_capacity");
  if (tr_c0_pending && ((access == 1 && tile == tr_c0_tile) ||
      (tr_c0_region == region && (access == 2 || tr_c0_access == 2)))) tr_cover0();
  if (tr_c1_pending && ((access == 1 && tile == tr_c1_tile) ||
      (tr_c1_region == region && (access == 2 || tr_c1_access == 2)))) tr_cover1();
  if (tr_c0_pending) {
    TR_CHECK(!(mask & tr_c0_mask) || (access == 2 && tr_c0_access == 2),"pending_tile_write");
    TR_CHECK(cell != tr_c0_cell || (access == 1 && tr_c0_access == 1),"device_memory_conflict");
  }
  if (tr_c1_pending) {
    TR_CHECK(!(mask & tr_c1_mask) || (access == 2 && tr_c1_access == 2),"pending_tile_write");
    TR_CHECK(cell != tr_c1_cell || (access == 1 && tr_c1_access == 1),"device_memory_conflict");
  }
  int command = tr_count;
  if (command == 0) {
    tr_c0_pending = 1;
    tr_c0_thread = thread;
    tr_c0_access = access;
    tr_c0_region = region;
    tr_c0_cell = cell;
    tr_c0_tile = tile;
    tr_c0_mask = mask;
    tr_c0_value = value;
    tr_c0_issue = tr_memory(cell);
    tr_c0_later = 0;
    tr_c0_writes = 0;
    tr_c0_result = 0;
  } else {
    tr_c1_pending = 1;
    tr_c1_thread = thread;
    tr_c1_access = access;
    tr_c1_region = region;
    tr_c1_cell = cell;
    tr_c1_tile = tile;
    tr_c1_mask = mask;
    tr_c1_value = value;
    tr_c1_issue = tr_memory(cell);
    tr_c1_later = 0;
    tr_c1_writes = 0;
    tr_c1_result = 0;
  }
  tr_count = tr_count + 1; return command;
}
int swdb_t28_wait(int tile) {
  int mask = tr_mask(tile, 4);
  if (tr_c0_pending && (tr_c0_mask & mask)) tr_cover0();
  if (tr_c1_pending && (tr_c1_mask & mask)) tr_cover1();
  return 0;
}
int swdb_t28_tile_read(int thread, int tile, int bytes) {
  int mask = tr_mask(tile, bytes); tr_owned(thread, mask);
  TR_CHECK(!tr_c0_pending || tr_c0_access != 1 || !(tr_c0_mask & mask),"pending_tile_write");
  TR_CHECK(!tr_c1_pending || tr_c1_access != 1 || !(tr_c1_mask & mask),"pending_tile_write");
  return 0;
}
int swdb_t28_pending(int command) {
  TR_CHECK(0 <= command && command < tr_count,"command_domain");
  return command == 0 ? tr_c0_pending : tr_c1_pending;
}
int swdb_t28_result(int command) {
  TR_CHECK(0 <= command && command < tr_count,"command_domain");
  TR_CHECK(!swdb_t28_pending(command),"pending_tile_write");
  TR_CHECK((command == 0 ? tr_c0_access : tr_c1_access) == 1,"result_domain");
  return command == 0 ? tr_c0_result : tr_c1_result;
}
int swdb_t28_ready(int tile) {
  int mask = tr_mask(tile, 4);
  int pending = (tr_c0_pending && (tr_c0_mask & mask)) || (tr_c1_pending && (tr_c1_mask & mask));
  int ready = pending ? tr_pick() : 1;
  if (ready) swdb_t28_wait(tile);
  return ready;
}

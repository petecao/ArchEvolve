// 2026-10-16 ET. Formal-only device initializedness diagnostics.
// No unsafe negative may be executed natively. No Init/reset/havoc premise.
#include "dxc_summaries.h"

/*@ requires TILE_SIZE == 2;
    requires \valid(out);
    requires \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. 1));
    requires \forall integer t, u; 0 <= t < u < DXC_NUM_TILES ==>
      \separated(dxc_tile_data[t] + (0 .. 1), dxc_tile_data[u] + (0 .. 1));
    requires \separated(out, dxc_tile_data + (0 .. DXC_NUM_TILES - 1),
      dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_reg + (0 .. DXC_NUM_REGS - 1),
      dxc_pending + (0 .. DXC_NUM_TILES - 1),
      dxc_dep + (0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1));
    requires dxc_idle;
    assigns *out, dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. 1],
      dxc_tile_len[0 .. DXC_NUM_TILES - 1], dxc_reg[0 .. DXC_NUM_REGS - 1],
      dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures *out == 0;
*/
void swdb_device_pipeline_safe(int *out) {
  int source[2];
  source[0] = 0;
  source[1] = 1;
  int upper[2]; upper[0] = 1; upper[1] = 1;
  __dxc_const_i32(0, 0);
  __dxc_const_i32(1, 1);
  __dxc_const_i32(1, 2);
  __dxc_stream_load(source, 0, 1, 2, 0);
  __dxc_gather(upper, 0, 1);
  __dxc_const_i32(0, 4);
  __dxc_const_i32(-1, 5);
  __dxc_range_loop(4, 5, 0, 1, 2, 2, 3);
  __dxc_wait(3);
  int *produced;
  __dxc_tile_pointer_out(3, &produced);
  /*@ check fixture_read_ready: dxc_cpu_may_read(produced + 0); */
  *out = produced[0];
}

/*@ requires TILE_SIZE == 2;
    requires \valid(out);
    requires \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. 1));
    requires \forall integer t, u; 0 <= t < u < DXC_NUM_TILES ==>
      \separated(dxc_tile_data[t] + (0 .. 1), dxc_tile_data[u] + (0 .. 1));
    requires \separated(out, dxc_tile_data + (0 .. DXC_NUM_TILES - 1),
      dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_reg + (0 .. DXC_NUM_REGS - 1),
      dxc_pending + (0 .. DXC_NUM_TILES - 1),
      dxc_dep + (0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1));
    requires dxc_idle;
    assigns *out, dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. 1],
      dxc_tile_len[0 .. DXC_NUM_TILES - 1], dxc_reg[0 .. DXC_NUM_REGS - 1],
      dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
*/
void swdb_device_missing_source(int *out) {
  int source[2];
  /* source[0] deliberately has no store */
  source[1] = 1;
  int upper[2]; upper[0] = 1; upper[1] = 1;
  __dxc_const_i32(0, 0);
  __dxc_const_i32(1, 1);
  __dxc_const_i32(1, 2);
  __dxc_stream_load(source, 0, 1, 2, 0);
  __dxc_gather(upper, 0, 1);
  __dxc_const_i32(0, 4);
  __dxc_const_i32(-1, 5);
  __dxc_range_loop(4, 5, 0, 1, 2, 2, 3);
  __dxc_wait(3);
  int *produced;
  __dxc_tile_pointer_out(3, &produced);
  /*@ check fixture_read_ready: dxc_cpu_may_read(produced + 0); */
  *out = produced[0];
}

/*@ requires TILE_SIZE == 2;
    requires \valid(out);
    requires \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. 1));
    requires \forall integer t, u; 0 <= t < u < DXC_NUM_TILES ==>
      \separated(dxc_tile_data[t] + (0 .. 1), dxc_tile_data[u] + (0 .. 1));
    requires \separated(out, dxc_tile_data + (0 .. DXC_NUM_TILES - 1),
      dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_reg + (0 .. DXC_NUM_REGS - 1),
      dxc_pending + (0 .. DXC_NUM_TILES - 1),
      dxc_dep + (0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1));
    requires dxc_idle;
    assigns *out, dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. 1],
      dxc_tile_len[0 .. DXC_NUM_TILES - 1], dxc_reg[0 .. DXC_NUM_REGS - 1],
      dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
*/
void swdb_device_wrong_prefix(int *out) {
  int source[2];
  source[0] = 0;
  source[1] = 1;
  int upper[2]; upper[0] = 1; upper[1] = 1;
  __dxc_const_i32(0, 0);
  __dxc_const_i32(1, 1);
  __dxc_const_i32(1, 2);
  __dxc_stream_load(source, 0, 1, 2, 0);
  __dxc_gather(upper, 0, 1);
  __dxc_const_i32(0, 4);
  __dxc_const_i32(-1, 5);
  __dxc_range_loop(4, 5, 0, 1, 2, 2, 3);
  __dxc_wait(3);
  int *produced;
  __dxc_tile_pointer_out(3, &produced);
  /*@ check fixture_read_ready: dxc_cpu_may_read(produced + 1); */
  *out = produced[1];
}

/*@ requires TILE_SIZE == 2;
    requires \valid(out);
    requires \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. 1));
    requires \forall integer t, u; 0 <= t < u < DXC_NUM_TILES ==>
      \separated(dxc_tile_data[t] + (0 .. 1), dxc_tile_data[u] + (0 .. 1));
    requires \separated(out, dxc_tile_data + (0 .. DXC_NUM_TILES - 1),
      dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_reg + (0 .. DXC_NUM_REGS - 1),
      dxc_pending + (0 .. DXC_NUM_TILES - 1),
      dxc_dep + (0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1));
    requires dxc_idle;
    requires dxc_tile_len[0] == 1;
    assigns *out, dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. 1],
      dxc_tile_len[0 .. DXC_NUM_TILES - 1], dxc_reg[0 .. DXC_NUM_REGS - 1],
      dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures *out == 17;
*/
void swdb_device_index_safe(int *out) {
  int base[2]; base[0] = 17; base[1] = 19;
  dxc_tile_data[0][0] = 0;
  __dxc_gather(base, 0, 1);
  __dxc_wait(1);
  int *produced;
  __dxc_tile_pointer_out(1, &produced);
  /*@ check fixture_read_ready: dxc_cpu_may_read(produced); */
  *out = produced[0];
}

/*@ requires TILE_SIZE == 2;
    requires \valid(out);
    requires \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \valid(dxc_tile_data[t] + (0 .. 1));
    requires \forall integer t, u; 0 <= t < u < DXC_NUM_TILES ==>
      \separated(dxc_tile_data[t] + (0 .. 1), dxc_tile_data[u] + (0 .. 1));
    requires \separated(out, dxc_tile_data + (0 .. DXC_NUM_TILES - 1),
      dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_reg + (0 .. DXC_NUM_REGS - 1),
      dxc_pending + (0 .. DXC_NUM_TILES - 1),
      dxc_dep + (0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1));
    requires dxc_idle;
    requires dxc_tile_len[0] == 1;
    assigns *out, dxc_tile_data[0 .. DXC_NUM_TILES - 1][0 .. 1],
      dxc_tile_len[0 .. DXC_NUM_TILES - 1], dxc_reg[0 .. DXC_NUM_REGS - 1],
      dxc_pending[0 .. DXC_NUM_TILES - 1],
      dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
*/
void swdb_device_missing_index(int *out) {
  int base[2]; base[0] = 17; base[1] = 19;
  /* no store to the incoming index cell */
  __dxc_gather(base, 0, 1);
  __dxc_wait(1);
  int *produced;
  __dxc_tile_pointer_out(1, &produced);
  /*@ check fixture_read_ready: dxc_cpu_may_read(produced); */
  *out = produced[0];
}

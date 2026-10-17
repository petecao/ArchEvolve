// Prospective lexical private-array refinement; source/formal acceptance pending.
// Prospective private out-slot ABI, 2026-10-16 ET. Not a proof record.
// PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
// Throwaway ACSL summaries of the DX100 calls Peter's read offload uses (dxc_* and maa_* region
// calls), standing in for tickets 27/30. Body-less: WP prints their contracts as Extern, and each
// is an assumption entry of kind "summary".
// Semantics (map 12): values as if each command finished at issue; hazards tracked apart in
// ghost state. Wait rule: the library's (library/intrinsics/dxc_range_loop.yaml completion
// assumptions) "a tile wait covers its producer and transitive dependencies". This is
// conservative against gem5 (research 14: gem5 also covers commands naming the tile as a
// source), so a hazard proven absent here is absent under gem5 too.
// Narrowing: range loop stride register must hold 1 (the only stride the unit uses).
#ifndef DXC_SUMMARIES_H
#define DXC_SUMMARIES_H
#include <stdint.h>

#define DXC_NUM_TILES 8   /* NUM_CORES (1, threads = 1 build) * NUM_TILES_PER_CORE (8) */
#define DXC_NUM_REGS 8    /* NUM_CORES (1) * NUM_REGS_PER_CORE (8) */

struct dxc_context { int tile[8], reg[8]; };  /* dxc_lowering.hpp:14 */
typedef struct dxc_context dxc_context;

/* Symbolic build constant (map 19 item 2): tile capacity, 1..65535 (dxc_lowering.hpp:13). */
extern const unsigned TILE_SIZE;

/* SPD tile memory as get_cacheable_tile_pointer exposes it; one block per tile. */
int *dxc_tile_data[DXC_NUM_TILES];

/* Ghost device state (map 16 item 10, reduced): tile sizes, scalar registers, and per tile
   whether an uncovered command writes it plus the tiles its writer depends on. */
//@ ghost int dxc_tile_len[DXC_NUM_TILES];
//@ ghost int dxc_reg[DXC_NUM_REGS];
//@ ghost int dxc_pending[DXC_NUM_TILES];
//@ ghost int dxc_dep[DXC_NUM_TILES * DXC_NUM_TILES];  /* row-major: dxc_dep[x * DXC_NUM_TILES + y] */

/*@
  predicate dxc_tile_ok(integer t) = 0 <= t < DXC_NUM_TILES;
  predicate dxc_reg_ok(integer r) = 0 <= r < DXC_NUM_REGS;
  predicate dxc_in2(integer x, integer a, integer b) = x == a || x == b;

  // The CPU may read through p only if no uncovered command writes the tile p points into.
  predicate dxc_cpu_may_read{L}(int *p) =
    \forall integer t; 0 <= t < DXC_NUM_TILES ==>
      \base_addr(p) == \base_addr(\at(dxc_tile_data[t], L)) ==> \at(dxc_pending[t], L) == 0;

  predicate dxc_idle{L} = \forall integer t; 0 <= t < DXC_NUM_TILES ==> \at(dxc_pending[t], L) == 0;

  // Effect of issuing one command with source tiles s1, s2 and destination tiles d1, d2 (-1: none).
  predicate dxc_issued{L1, L2}(integer s1, integer s2, integer d1, integer d2) =
    \forall integer x; 0 <= x < DXC_NUM_TILES ==>
      (dxc_in2(x, d1, d2) ==> \at(dxc_pending[x], L2) == 1) &&
      (!dxc_in2(x, d1, d2) ==> \at(dxc_pending[x], L2) == \at(dxc_pending[x], L1)) &&
      (\forall integer y; 0 <= y < DXC_NUM_TILES ==>
        (dxc_in2(x, d1, d2) ==>
          (\at(dxc_dep[x * DXC_NUM_TILES + y], L2) != 0 <==>
            ((dxc_in2(y, d1, d2) && y != x) ||
             (dxc_in2(y, s1, s2) && \at(dxc_pending[y], L1) != 0) ||
             (s1 >= 0 && \at(dxc_pending[s1], L1) != 0 && \at(dxc_dep[s1 * DXC_NUM_TILES + y], L1) != 0) ||
             (s2 >= 0 && \at(dxc_pending[s2], L1) != 0 && \at(dxc_dep[s2 * DXC_NUM_TILES + y], L1) != 0)))) &&
        (!dxc_in2(x, d1, d2) ==>
          (\at(dxc_dep[x * DXC_NUM_TILES + y], L2) != 0 <==> (!dxc_in2(y, d1, d2) && \at(dxc_dep[x * DXC_NUM_TILES + y], L1) != 0))));

  // A wait on tile t covers t's uncovered writer and everything that writer depends on.
  predicate dxc_covers{L}(integer t, integer x) =
    \at(dxc_pending[t], L) != 0 && (x == t || \at(dxc_dep[t * DXC_NUM_TILES + x], L) != 0);

  // Range loop (stride 1): pairs (i, j) with 0 <= i < n and lo[i] <= j < hi[i], in
  // lexicographic order; continuation state (i, j): j == -1 means "before row i".
  predicate dxc_lex_lt(integer i1, integer j1, integer i2, integer j2) = i1 < i2 || (i1 == i2 && j1 < j2);
  predicate dxc_lex_le(integer i1, integer j1, integer i2, integer j2) = i1 < i2 || (i1 == i2 && j1 <= j2);
  predicate dxc_rl_pair{L}(int *lo, int *hi, integer n, integer i, integer j) =
    0 <= i < n && \at(lo[i], L) <= j < \at(hi[i], L);
  predicate dxc_rl_state{L}(int *lo, int *hi, integer n, integer i, integer j) =
    0 <= i <= n && (j == -1 || (i < n && \at(lo[i], L) <= j < \at(hi[i], L)));
*/

/*@ requires dxc_reg_ok(reg);
    terminates \true;
    assigns dxc_reg[reg];
    ensures dxc_reg[reg] == value;
    exits \false; */
void __dxc_const_i32(int32_t value, int reg);

/*@ requires dxc_reg_ok(minimum) && dxc_reg_ok(maximum) && dxc_reg_ok(stride) && dxc_tile_ok(dst);
    requires dxc_reg[stride] == 1;
    requires 0 <= dxc_reg[minimum];
    requires dxc_reg[maximum] - dxc_reg[minimum] <= TILE_SIZE;
    requires \valid_read(base + (dxc_reg[minimum] .. dxc_reg[maximum] - 1));
    requires \initialized(base + (dxc_reg[minimum] .. dxc_reg[maximum] - 1));
    requires \valid(dxc_tile_data[dst] + (0 .. TILE_SIZE - 1));
    terminates \true;
    assigns dxc_tile_data[dst][0 .. TILE_SIZE - 1], dxc_tile_len[dst],
            dxc_pending[0 .. DXC_NUM_TILES - 1], dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures dxc_tile_len[dst] == (dxc_reg[maximum] > dxc_reg[minimum] ? dxc_reg[maximum] - dxc_reg[minimum] : 0);
    ensures \forall integer i; 0 <= i < dxc_tile_len[dst] ==>
              dxc_tile_data[dst][i] == \old(base[dxc_reg[minimum] + i]);
    ensures dxc_issued{Pre, Post}(-1, -1, dst, -1);
    ensures \initialized(dxc_tile_data[dst] + (0 .. dxc_tile_len[dst] - 1));
    exits \false; */
void __dxc_stream_load(const int *base, int minimum, int maximum, int stride, int dst);

/*@ requires dxc_tile_ok(index) && dxc_tile_ok(dst) && index != dst;
    requires 0 <= dxc_tile_len[index] <= TILE_SIZE;
    requires \forall integer i; 0 <= i < dxc_tile_len[index] ==> \valid_read(base + dxc_tile_data[index][i]);
    requires \valid_read(dxc_tile_data[index] + (0 .. dxc_tile_len[index] - 1));
    requires \initialized(dxc_tile_data[index] + (0 .. dxc_tile_len[index] - 1));
    requires \forall integer i; 0 <= i < dxc_tile_len[index] ==>
      \initialized(base + dxc_tile_data[index][i]);
    requires \valid(dxc_tile_data[dst] + (0 .. TILE_SIZE - 1));
    terminates \true;
    assigns dxc_tile_data[dst][0 .. TILE_SIZE - 1], dxc_tile_len[dst],
            dxc_pending[0 .. DXC_NUM_TILES - 1], dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures dxc_tile_len[dst] == dxc_tile_len[index];
    ensures \forall integer i; 0 <= i < dxc_tile_len[dst] ==>
              dxc_tile_data[dst][i] == \old(base[dxc_tile_data[index][i]]);
    ensures dxc_issued{Pre, Post}(index, -1, dst, -1);
    ensures \initialized(dxc_tile_data[dst] + (0 .. dxc_tile_len[dst] - 1));
    exits \false; */
void __dxc_gather(const int *base, int index, int dst);

/*@ requires dxc_reg_ok(last_i) && dxc_reg_ok(last_j) && dxc_reg_ok(stride) && last_i != last_j;
    requires dxc_tile_ok(lower) && dxc_tile_ok(upper) && dxc_tile_ok(rows) && dxc_tile_ok(columns);
    requires lower != upper && rows != columns;
    requires !dxc_in2(rows, lower, upper) && !dxc_in2(columns, lower, upper);
    requires dxc_reg[stride] == 1;
    requires dxc_tile_len[lower] == dxc_tile_len[upper] && 0 <= dxc_tile_len[lower] <= TILE_SIZE;
    requires \forall integer i; 0 <= i < dxc_tile_len[lower] ==>
               0 <= dxc_tile_data[lower][i] <= dxc_tile_data[upper][i] <= 1073741823;
    requires dxc_rl_state{Here}(dxc_tile_data[lower], dxc_tile_data[upper], dxc_tile_len[lower],
                                dxc_reg[last_i], dxc_reg[last_j]);
    requires \valid_read(dxc_tile_data[lower] + (0 .. dxc_tile_len[lower] - 1));
    requires \valid_read(dxc_tile_data[upper] + (0 .. dxc_tile_len[upper] - 1));
    requires \initialized(dxc_tile_data[lower] + (0 .. dxc_tile_len[lower] - 1));
    requires \initialized(dxc_tile_data[upper] + (0 .. dxc_tile_len[upper] - 1));
    requires \valid(dxc_tile_data[rows] + (0 .. TILE_SIZE - 1));
    requires \valid(dxc_tile_data[columns] + (0 .. TILE_SIZE - 1));
    terminates \true;
    assigns dxc_tile_data[rows][0 .. TILE_SIZE - 1], dxc_tile_data[columns][0 .. TILE_SIZE - 1],
            dxc_tile_len[rows], dxc_tile_len[columns], dxc_reg[last_i], dxc_reg[last_j],
            dxc_pending[0 .. DXC_NUM_TILES - 1], dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures dxc_tile_len[rows] == dxc_tile_len[columns] && 0 <= dxc_tile_len[columns] <= TILE_SIZE;
    ensures \forall integer k; 0 <= k < dxc_tile_len[columns] ==>
              dxc_rl_pair{Pre}(dxc_tile_data[lower], dxc_tile_data[upper], \old(dxc_tile_len[lower]),
                               dxc_tile_data[rows][k], dxc_tile_data[columns][k]) &&
              dxc_lex_lt(\old(dxc_reg[last_i]), \old(dxc_reg[last_j]), dxc_tile_data[rows][k], dxc_tile_data[columns][k]) &&
              dxc_lex_le(dxc_tile_data[rows][k], dxc_tile_data[columns][k], dxc_reg[last_i], dxc_reg[last_j]);
    ensures \forall integer k1, k2; 0 <= k1 < k2 < dxc_tile_len[columns] ==>
              dxc_lex_lt(dxc_tile_data[rows][k1], dxc_tile_data[columns][k1],
                         dxc_tile_data[rows][k2], dxc_tile_data[columns][k2]);
    ensures \forall integer i, j;
              dxc_rl_pair{Pre}(dxc_tile_data[lower], dxc_tile_data[upper], \old(dxc_tile_len[lower]), i, j) &&
              dxc_lex_lt(\old(dxc_reg[last_i]), \old(dxc_reg[last_j]), i, j) &&
              dxc_lex_le(i, j, dxc_reg[last_i], dxc_reg[last_j]) ==>
              \exists integer k; 0 <= k < dxc_tile_len[columns] &&
                dxc_tile_data[rows][k] == i && dxc_tile_data[columns][k] == j;
    ensures dxc_tile_len[columns] < TILE_SIZE ==>
              dxc_reg[last_i] == \old(dxc_tile_len[lower]) && dxc_reg[last_j] == -1;
    ensures dxc_tile_len[columns] == TILE_SIZE ==>
              dxc_reg[last_i] == dxc_tile_data[rows][TILE_SIZE - 1] &&
              dxc_reg[last_j] == dxc_tile_data[columns][TILE_SIZE - 1];
    ensures dxc_rl_state{Pre}(dxc_tile_data[lower], dxc_tile_data[upper], \old(dxc_tile_len[lower]),
                              dxc_reg[last_i], dxc_reg[last_j]);
    ensures dxc_lex_le(\old(dxc_reg[last_i]), \old(dxc_reg[last_j]), dxc_reg[last_i], dxc_reg[last_j]);
    ensures dxc_issued{Pre, Post}(lower, upper, rows, columns);
    ensures \initialized(dxc_tile_data[rows] + (0 .. dxc_tile_len[rows] - 1));
    ensures \initialized(dxc_tile_data[columns] + (0 .. dxc_tile_len[columns] - 1));
    exits \false; */
void __dxc_range_loop(int last_i, int last_j, int lower, int upper, int stride, int rows, int columns);

/*@ requires dxc_tile_ok(tile);
    terminates \true;
    assigns dxc_pending[0 .. DXC_NUM_TILES - 1], dxc_dep[0 .. DXC_NUM_TILES * DXC_NUM_TILES - 1];
    ensures \forall integer x; 0 <= x < DXC_NUM_TILES ==>
              (dxc_covers{Pre}(tile, x) ==> dxc_pending[x] == 0) &&
              (!dxc_covers{Pre}(tile, x) ==> dxc_pending[x] == \old(dxc_pending[x])) &&
              (\forall integer y; 0 <= y < DXC_NUM_TILES ==>
                 (dxc_dep[x * DXC_NUM_TILES + y] != 0 <==> (!dxc_covers{Pre}(tile, x) && \old(dxc_dep[x * DXC_NUM_TILES + y]) != 0)));
    exits \false; */
void __dxc_wait(int tile);

/*@ requires \valid(swdb_out); requires \separated(swdb_out, dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_tile_data + (0 .. DXC_NUM_TILES - 1), dxc_pending + (0 .. DXC_NUM_TILES - 1));
 requires dxc_tile_ok(tile);
    requires hazard_tile_size_ready: dxc_pending[tile] == 0;
    requires 0 <= dxc_tile_len[tile] <= TILE_SIZE;
    terminates \true;
    assigns *swdb_out;
    ensures (*swdb_out) == dxc_tile_len[tile];
    exits \false;
    ensures \initialized(swdb_out); */
void __dxc_tile_size_out(int tile, uint16_t *swdb_out);

/*@ requires \valid(swdb_out); requires \separated(swdb_out, dxc_tile_len + (0 .. DXC_NUM_TILES - 1), dxc_tile_data + (0 .. DXC_NUM_TILES - 1), dxc_pending + (0 .. DXC_NUM_TILES - 1));
 requires dxc_tile_ok(tile);
    terminates \true;
    assigns *swdb_out;
    ensures (*swdb_out) == dxc_tile_data[tile];
    exits \false;
    ensures \initialized(swdb_out); */
void __dxc_tile_pointer_out(int tile, int * *swdb_out);

/*@ terminates \true;
    assigns \nothing;
    exits \false; */
void __dxc_accelerated_chunk(void);

/* MAA API region registration (GEM5 build). The region stall is not modeled here. */
/*@ terminates \true;
    assigns \nothing;
    exits \false; */
void clear_mem_region(void);
/*@ terminates \true;
    assigns \nothing;
    exits \false; */
void add_mem_region(void *start, void *end);

#endif

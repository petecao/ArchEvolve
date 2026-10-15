/* DX100 proof semantics 0.1 (semantics.dx100_bfs_0_1): command kinds and the device state (not ghost).
   Created: 2026-10-14 ET (Probata proof of concept ticket 27). Read by the C model (model.h, the CBMC form)
   and by the ACSL contracts (the WP form). Sizes (DX_K, DX_NT, DX_NR, DX_NM, DX_TS) come from the entry's
   build-constant defaults or --define. */
#define DX_STREAM_LOAD 1
#define DX_GATHER 2
#define DX_RANGE_LOOP 3
#define DX_ALU_SCALAR 4
#define DX_STORE_VECTOR 5
#define DX_LT_OP 13

int dx_tile_data[DX_NT][DX_TS];   /* tile elements, CPU-visible through get_cacheable_tile_pointer */
int dx_tile_size[DX_NT];          /* tile sizes, read by get_tile_size */
int dx_reg_value[DX_NR];          /* scalar registers */
int dx_next_tile;                 /* allocation counters (get_new_tile, get_new_reg) */
int dx_next_reg;
int dx_regions;                   /* registered memory regions (add_mem_region; region rules: ticket 28) */

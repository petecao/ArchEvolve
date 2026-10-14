// Probata PoC 24 fixture, construct group "__dxc_* and maa_* calls through summaries". Created: 2026-10-14 ET.
// The DX100 calls are declared only: a summary stands for each (map 16 item 6). Without one, the
// lowering refuses the call (unsupported construct) until tickets 27, 28 and 30 supply real ones.
void maa_const_i32(int value, int reg);
template <class T>
void maa_indirect_load(T *base, int idx_tile, int dst_tile, int cond_tile = -1);
unsigned short __dxc_tile_size(int tile);

int swdb_dxc_unit(int tile) { return __dxc_tile_size(tile) + 1; }

int swdb_maa_unit(int *base, int n) {
  maa_const_i32(n, 0);
  maa_indirect_load(base, 0, 1);
  return n;
}

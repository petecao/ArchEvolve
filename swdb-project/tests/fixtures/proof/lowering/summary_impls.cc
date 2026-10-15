// Probata PoC 24: stand-in definitions of the fixture summaries' calls (summaries.cc), the code each fixture
// summary entry is proven on (`swdb prove --summary ENTRY --adapter wp`). Not DX100 semantics: real
// per-call summaries come with tickets 27, 28 and 30. Created: 2026-10-14 ET.
void maa_const_i32(int value, int reg) {
  (void)value;
  (void)reg;
}

void maa_indirect_load_i32(int *base, int idx_tile, int dst_tile, int cond_tile) {
  (void)base;
  (void)idx_tile;
  (void)dst_tile;
  (void)cond_tile;
}

unsigned short __dxc_tile_size(int tile) { return (unsigned short)(tile & 1); }

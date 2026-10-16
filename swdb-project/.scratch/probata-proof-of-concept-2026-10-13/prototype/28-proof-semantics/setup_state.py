"""2026-10-16 ET. Exact source-shaped alloc/init/region wrapper prototype.

Source physical stride is distinct from the value prefix. Host counters reset
without clearing payloads or pending device commands. Source/ABI admission and
full public proof contracts remain separate work.
"""


def render_header(command_header, *, source_tile_words, source_cores):
    if type(source_cores) is not int or source_cores not in (4, 8):
        raise ValueError('source4/8-core geometries fit this64-bit role-mask prototype;16-core not yet modeled')
    if type(source_tile_words) is not int or not 1 <= source_tile_words <= 65535:
        raise ValueError('source tile size must fit the16-bit tile size interface')
    tiles = source_cores * 8
    if tiles * source_tile_words > 2147483647:
        raise ValueError('source signed-int tile geometry intermediate overflows')
    prefix = ('static void dxs_reset_state(void);\n#define DXS_ON_RESET() dxs_reset_state()\n'
              f'#define DXS_SOURCE_TILES {tiles}\n#define DXS_SOURCE_REGS {tiles}\n'
              f'#define DXS_SOURCE_WORDS {source_tile_words}\n'
              f'#define DXS_SOURCE_MEMORY UINT64_C({source_cores * 0x100000000})\n')
    return prefix + command_header + r'''
#ifndef SWDB_DX_SETUP_STATE_H
#define SWDB_DX_SETUP_STATE_H
#ifdef __cplusplus
#define DXS_ABI(c) static_assert(c,"source setup geometry/ABI")
#else
#define DXS_ABI(c) _Static_assert(c,"source setup geometry/ABI")
#endif
DXS_ABI(DXM_TILES == DXS_SOURCE_TILES && DXG_REGS == DXS_SOURCE_REGS);
DXS_ABI(DXP_TILE_WORDS == DXS_SOURCE_WORDS && DXC_REGIONS == 256);
/* The pinned conventional int8 conversion profile, not signed overflow UB.
   Native compiler evaluation binds the narrowing; formal/source admission
   must retain the same implementation-defined conversion profile. */
DXS_ABI(INT8_MIN == -128 && INT8_MAX == 127 && (int8_t)128 == -128);
static uint64_t dxs_mmio[7];
static unsigned dxs_allocated,dxs_tile_next;
static int dxs_region_next;
static void dxs_reset_state(void) {
  dxs_allocated=0; dxs_tile_next=0; dxs_region_next=0;
  for (unsigned i=0; i<7; ++i) dxs_mmio[i]=0;
}
static void dxs_clear_regions(void) {
  DXM_CHECK(!dxc_constructing,"unbound-command");
  DXM_CHECK(dxs_allocated,"mmio-setup-domain");
  dxr_reset_state();
  for (int i=0; i<6; ++i) dxr_add(i,dxs_mmio[i],dxs_mmio[i+1]);
  dxs_region_next=6;
}
/* MAA_gem5.hpp:71-91, BASE_ADDR0, source NUM_TILES/REGS=NUM_CORES*8.
   No allocation counter or device payload reset is hidden in this call. */
static void dxs_alloc(void) {
  DXM_CHECK(!dxc_constructing,"unbound-command");
  dxs_mmio[0]=DXS_SOURCE_MEMORY;
  dxs_mmio[1]=dxs_mmio[0]+UINT64_C(4)*DXS_SOURCE_TILES*DXS_SOURCE_WORDS;
  dxs_mmio[2]=dxs_mmio[1]+UINT64_C(4)*DXS_SOURCE_TILES*DXS_SOURCE_WORDS;
  dxs_mmio[3]=dxs_mmio[2]+UINT64_C(2)*DXS_SOURCE_TILES;
  dxs_mmio[4]=dxs_mmio[3]+UINT64_C(2)*DXS_SOURCE_TILES;
  dxs_mmio[5]=dxs_mmio[4]+UINT64_C(4)*DXS_SOURCE_REGS;
  dxs_mmio[6]=dxs_mmio[5]+24;
  dxs_allocated=1;
  dxs_clear_regions();
}
/* MAA_gem5.hpp:93-97 resets only host allocation/next-region counters. */
static void dxs_init(void) {
  DXM_CHECK(!dxc_constructing,"unbound-command");
  dxg_init_counters(); dxs_tile_next=0; dxs_region_next=6;
}
static void dxs_add_region(uint64_t begin,uint64_t end) {
  DXM_CHECK(!dxc_constructing,"unbound-command");
  DXM_CHECK(dxs_region_next >= 0 && dxs_region_next < DXC_REGIONS,"region-capacity");
  dxr_add(dxs_region_next,begin,end);
  dxs_region_next=dxs_region_next == 127 ? -128 : dxs_region_next+1;
}
static unsigned dxs_new_tile(unsigned thread,unsigned dtype) {
  DXM_CHECK(thread < 2,"thread-domain");
  unsigned halves=dxm_tile_halves(dxs_tile_next,dxp_width(dtype)), tile=dxs_tile_next;
  for (unsigned j=0; j<halves; ++j)
    DXM_CHECK(dxm_tile_owner[tile+j] == -1 || dxm_tile_owner[tile+j] == (int)thread,"tile-ownership");
  for (unsigned j=0; j<halves; ++j) dxm_tile_owner[tile+j]=(int)thread;
  dxs_tile_next += halves;
  return tile;
}
#endif
'''

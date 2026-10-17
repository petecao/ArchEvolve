"""2026-10-16 ET. Immutable starting-tile size versions, not readiness waits.

Unknown quiescent entry sizes are overapproximated rather than reset to zero by
alloc/init. A fresh-constructor zero certificate is a separate admission.
"""


def render_header(image_header):
    prefix = 'static void dxz_reset_state(void);\n#define DXZ_ON_RESET() dxz_reset_state()\n'
    return prefix + image_header + r'''
#ifndef SWDB_DX_SIZE_STATE_H
#define SWDB_DX_SIZE_STATE_H
static unsigned dxz_sizes[DXM_TILES];
static void dxz_reset_state(void) {
  DXM_CHECK(DXP_TILE_WORDS <= UINT16_MAX,"tile-size-source-domain");
  for (unsigned t=0; t<DXM_TILES; ++t) dxz_sizes[t]=UINT_MAX;
}
/* This captures metadata, never waits or settles a pending producer version.
   Native arbitrary-entry controls enumerate selected possible initial sizes.
   Source integration must justify the valid/quiescent entry-state invariant. */
static unsigned dxz_capture_size(unsigned tile) {
  dxm_tile_halves(tile,4);
  if (dxz_sizes[tile] == UINT_MAX) {
    unsigned size=DXM_CHOOSE(DXP_TILE_WORDS+1);
    DXM_CHECK(size <= DXP_TILE_WORDS,"nondeterministic-choice-domain");
    dxz_sizes[tile]=dxm_constant(size);
  }
  return dxz_sizes[tile];
}
static void dxz_bind_size(unsigned command,unsigned tile,unsigned root) {
  dxp_check_output(command,tile,0);
  DXM_CHECK(root < dxm_count,"producer-version-domain");
  /* SPD::setSize updates the explicitly named starting tile only, even for
     an8-byte data role; do not copy metadata into the second physical half. */
  dxz_sizes[tile]=root;
}
static uint16_t dxz_get_size(unsigned tile) {
  DXM_CHECK(!dxc_constructing,"unbound-command");
  uint64_t mask=dxc_tile_mask(tile,4);
  /* SPD::getSize requires Finished status. Conservatively refuse an unfinished
     physical writer; a size load supplies no covering event or ownership grant. */
  for (unsigned i=0; i<dxc_count; ++i)
    if (dxc_commands[i].pending)
      DXM_CHECK(!(dxc_commands[i].physical_write & mask),"tile-size-before-finish");
  unsigned root=dxz_capture_size(tile); dxm_cover(root);
  uint64_t size=dxm_value(root);
  DXM_CHECK(size <= UINT16_MAX && size <= DXP_TILE_WORDS,"tile-size-source-domain");
  return (uint16_t)size;
}
#endif
'''

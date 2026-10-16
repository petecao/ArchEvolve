"""2026-10-15 ET. Source region assignment and checked F2 correspondence.

Models MAA.cc:200-241 at e4fc4af. Registration rejection is intentionally
one-sided like the source; lookup uses the first containing ID, not any region.
Addresses remain explicit source/device-domain values, not inferred C pointers.
"""


def render_header(command_header):
    prefix = r'''
static void dxr_reset_state(void);
#define DXR_ON_RESET() dxr_reset_state()
'''
    regions = r'''
#ifndef SWDB_DX_REGION_STATE_H
#define SWDB_DX_REGION_STATE_H
struct dxr_region { uint64_t begin,end; };
static struct dxr_region dxr_regions[DXC_REGIONS];
static void dxr_reset_state(void) {
  for (unsigned i=0; i<DXC_REGIONS; ++i) dxr_regions[i].begin=dxr_regions[i].end=0;
}
static void dxr_add(int id,uint64_t begin,uint64_t end) {
  DXM_CHECK(id >= 0 && id < DXC_REGIONS, "region-capacity");
  DXM_CHECK(begin < end && end != 0, "region-domain");
  for (unsigned i=0; i<DXC_REGIONS; ++i)
    DXM_CHECK(!(begin <= dxr_regions[i].begin && dxr_regions[i].begin < end), "region-registration-overlap");
  dxr_regions[id].begin=begin; dxr_regions[id].end=end;
}
static int dxr_find(uint64_t address) {
  for (unsigned i=0; i<DXC_REGIONS; ++i)
    if (dxr_regions[i].begin <= address && address < dxr_regions[i].end) return (int)i;
  return -1;
}
static int dxr_assign(uint64_t base) {
  int region=dxr_find(base);
  DXM_CHECK(region >= 0, "unregistered-command-base");
  return region;
}
/* F2 is a call-site obligation, not a replacement original-unit precondition.
   A containing later region cannot replace the ID selected for the base. */
static void dxr_check_span(int assigned,uint64_t begin,uint64_t end) {
  DXM_CHECK(assigned >= 0 && assigned < DXC_REGIONS, "assigned-region-domain");
  DXM_CHECK(begin <= end, "memory-footprint-domain");
  if (begin == end) return;
  DXM_CHECK(dxr_regions[assigned].begin <= begin && end <= dxr_regions[assigned].end,
            "region-footprint-correspondence");
  for (int i=0; i<assigned; ++i)
    DXM_CHECK(!(begin < dxr_regions[i].end && dxr_regions[i].begin < end),
              "region-footprint-correspondence");
}
/* IndirectAccess.cc:492-494, IndirectAccess.hh:113: int word size times
   uint32 index is a uint32 product on the pinned int32 ABI, then Addr addition.
   Both unsigned wraps are defined source behavior, not signed arithmetic UB. */
static uint64_t dxr_device_address(uint64_t base,uint32_t index,unsigned word_bytes) {
  DXM_CHECK(word_bytes == 4 || word_bytes == 8, "device-word-domain");
  DXM_CHECK(sizeof(int) == 4 && UINT_MAX == UINT32_MAX, "device-index-abi");
  uint32_t offset=(uint32_t)(word_bytes*index);
  return base+(uint64_t)offset;
}
/* Narrow ordinary-array correspondence only. Source callers must discharge
   it where that view is used; the raw address function remains wrapped.
   Object validity, Addr addition and physical mapping are separate checks. */
static void dxr_array_offset_correspondence(uint32_t index,unsigned word_bytes) {
  DXM_CHECK(word_bytes == 4 || word_bytes == 8, "device-word-domain");
  DXM_CHECK(index <= UINT32_MAX/word_bytes, "index-offset-correspondence");
}
/* Region membership is in the source/device address domain; hazards are in
   the physical domain supplied separately. No equality between these address
   spaces is inferred. Source/translation correspondence remains a caller check. */
static unsigned dxr_prepare(unsigned thread,unsigned access,uint64_t base,
    uint64_t logical_begin,uint64_t logical_end,uint64_t explicit_read,uint64_t explicit_write,
    uint64_t physical_read,uint64_t physical_write,uint64_t hazard_begin,uint64_t hazard_end) {
  DXM_CHECK(access == 1 || access == 2, "access-kind-domain");
  int assigned=dxr_assign(base);
  dxr_check_span(assigned,logical_begin,logical_end);
  return dxc_prepare(thread,assigned,access,explicit_read,explicit_write,
                     physical_read,physical_write,hazard_begin,hazard_end);
}
#endif
'''
    return prefix + command_header + regions

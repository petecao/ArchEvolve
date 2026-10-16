"""2026-10-16 ET. Sparse physical tile bytes backed by immutable producer IDs.

Explicit source tile stride is independent of the value-prefix encoding bound.
This is not a source/ABI certificate or permission for an unchecked pointer cast.
"""


def render_header(command_header, *, source_tile_words, value_bound, byte_order):
    if type(source_tile_words) is not int or not 1 <= source_tile_words <= 2147483647:
        raise ValueError('source tile word count must be a positive int32')
    if type(value_bound) is not int or not 1 <= value_bound <= source_tile_words:
        raise ValueError('value prefix must fit the source tile element count')
    if byte_order != 'little':
        raise ValueError('only the explicit little-endian source profile is modeled')
    prefix = ('static void dxp_reset_state(void);\n#define DXP_ON_RESET() dxp_reset_state()\n'
              f'#define DXP_TILE_WORDS {source_tile_words}\n#define DXP_VALUE_BOUND {value_bound}\n')
    image = r'''
#ifndef SWDB_DX_TILE_IMAGE_H
#define SWDB_DX_TILE_IMAGE_H
#include <string.h>
#ifdef __cplusplus
static_assert(CHAR_BIT == 8 && sizeof(int) == 4 && sizeof(float) == 4 && sizeof(double) == 8,"tile scalar ABI");
static_assert(INT32_MIN == -INT32_MAX-1 && INT64_MIN == -INT64_MAX-1,"two's complement scalar ABI");
#else
_Static_assert(CHAR_BIT == 8 && sizeof(int) == 4 && sizeof(float) == 4 && sizeof(double) == 8,"tile scalar ABI");
_Static_assert(INT32_MIN == -INT32_MAX-1 && INT64_MIN == -INT64_MAX-1,"two's complement scalar ABI");
#endif
#ifndef DXP_IMAGE_BYTES
#define DXP_IMAGE_BYTES (DXM_TILES*DXP_VALUE_BOUND*8)
#endif
struct dxp_byte { uint64_t offset; unsigned parent,shift; };
static struct dxp_byte dxp_image[DXP_IMAGE_BYTES];
static unsigned dxp_count;
static void dxp_reset_state(void) {
  DXM_CHECK(DXP_IMAGE_BYTES > 0 && DXP_IMAGE_BYTES <= INT_MAX,"tile-image-capacity-domain");
  dxp_count=0;
}
static unsigned dxp_width(unsigned dtype) {
  DXM_CHECK(dtype < 6, "numeric-type-domain");
  return dtype < 3 ? 4 : 8;
}
static uint64_t dxp_offset(unsigned tile,unsigned lane,unsigned dtype) {
  unsigned bytes=dxp_width(dtype);
  dxm_tile_halves(tile,bytes);
  DXM_CHECK(lane < DXP_VALUE_BOUND && lane < DXP_TILE_WORDS, "tile-element-domain");
  /* Preserve the actual int intermediates in MAA.hpp/SPD.hh before widening. */
  DXM_CHECK(tile <= INT_MAX/DXP_TILE_WORDS && lane <= INT_MAX/bytes, "tile-source-index-domain");
  unsigned base=tile*DXP_TILE_WORDS, words=lane*bytes/4;
  DXM_CHECK(words <= INT_MAX-base, "tile-source-index-domain");
  return ((uint64_t)base+words)*4;
}
static int dxp_find(uint64_t offset) {
  for (unsigned i=0; i<dxp_count; ++i) if (dxp_image[i].offset == offset) return (int)i;
  return -1;
}
static void dxp_set_bytes(uint64_t offset,unsigned bytes,const unsigned *parents,const unsigned *shifts) {
  unsigned extra=0;
  for (unsigned j=0; j<bytes; ++j) if (dxp_find(offset+j) < 0) ++extra;
  DXM_CHECK(dxp_count <= DXP_IMAGE_BYTES && extra <= DXP_IMAGE_BYTES-dxp_count, "tile-image-capacity");
  for (unsigned j=0; j<bytes; ++j) {
    int slot=dxp_find(offset+j);
    if (slot < 0) { slot=(int)dxp_count++; dxp_image[slot].offset=offset+j; }
    DXM_CHECK(parents[j] < dxm_count && shifts[j] < 8, "image-producer-version-domain");
    dxp_image[slot].parent=parents[j]; dxp_image[slot].shift=shifts[j];
  }
}
/* Each byte points to an immutable value version, not a mutable row object. */
static void dxp_set_version(unsigned tile,unsigned lane,unsigned dtype,unsigned root) {
  DXM_CHECK(root < dxm_count, "image-producer-version-domain");
  unsigned bytes=dxp_width(dtype), parents[8]={0}, shifts[8]={0};
  uint64_t offset=dxp_offset(tile,lane,dtype);
  for (unsigned j=0; j<bytes; ++j) { parents[j]=root; shifts[j]=j; }
  dxp_set_bytes(offset,bytes,parents,shifts);
}
static unsigned dxp_capture_bits(unsigned tile,unsigned lane,unsigned dtype) {
  unsigned bytes=dxp_width(dtype), parents[8]={0}, shifts[8]={0};
  unsigned missing=UINT_MAX;
  uint64_t offset=dxp_offset(tile,lane,dtype);
  for (unsigned j=0; j<bytes; ++j) {
    int slot=dxp_find(offset+j);
    if (slot < 0) {
      if (missing == UINT_MAX) missing=dxm_uninitialized();
      parents[j]=missing; shifts[j]=0;
    } else { parents[j]=dxp_image[slot].parent; shifts[j]=dxp_image[slot].shift; }
  }
  return dxm_bytes(parents,shifts,bytes);
}
/* Install a deferred version while constructing its owning command.  A device
   consumer captures these immutable IDs; CPU observations still require cover. */
static void dxp_check_output(unsigned command,unsigned tile,unsigned dtype) {
  DXM_CHECK(command < dxc_count && dxc_constructing == command+1, "command-binding");
  struct dxc_command *c=&dxc_commands[command];
  unsigned bytes=dxp_width(dtype);
  dxm_use_tile(c->thread,tile,bytes);
  uint64_t needed=dxc_tile_mask(tile,bytes);
  DXM_CHECK((c->physical_write & needed) == needed && (c->explicit_write & (UINT64_C(1)<<tile)),
            "image-command-output-domain");
}
static void dxp_bind_output(unsigned command,unsigned tile,unsigned lane,unsigned dtype,unsigned root) {
  dxp_check_output(command,tile,dtype);
  dxp_set_version(tile,lane,dtype,root);
}
/* Fake/inactive data preserves each prior byte, including its initializedness;
   preserving an8-byte view must not force an uninitialized neighboring byte. */
static void dxp_bind_conditional_output(unsigned command,unsigned tile,unsigned lane,unsigned dtype,
    unsigned condition,unsigned active_root) {
  dxp_check_output(command,tile,dtype);
  unsigned bytes=dxp_width(dtype), parents[8]={0}, shifts[8]={0}, missing=UINT_MAX;
  uint64_t offset=dxp_offset(tile,lane,dtype);
  for (unsigned j=0; j<bytes; ++j) {
    int slot=dxp_find(offset+j);
    unsigned old,shift;
    if (slot < 0) {
      if (missing == UINT_MAX) missing=dxm_uninitialized();
      old=missing; shift=0;
    } else { old=dxp_image[slot].parent; shift=dxp_image[slot].shift; }
    parents[j]=dxm_byte_select(condition,active_root,j,old,shift);
  }
  dxp_set_bytes(offset,bytes,parents,shifts);
}
static void dxp_cpu_write_bits(unsigned thread,unsigned tile,unsigned lane,unsigned dtype,uint64_t value) {
  unsigned bytes=dxp_width(dtype);
  dxc_cpu_tile_access(thread,tile,bytes,1);
  if (bytes == 4) value &= UINT32_MAX;
  dxp_set_version(tile,lane,dtype,dxm_constant(value));
}
static uint64_t dxp_cpu_read_bits(unsigned thread,unsigned tile,unsigned lane,unsigned dtype) {
  dxc_cpu_tile_access(thread,tile,dxp_width(dtype),0);
  unsigned root=dxp_capture_bits(tile,lane,dtype);
  dxm_cover(root);
  return dxm_value(root);
}
'''
    typed = []
    for dtype, name, ctype, width in [(0, 'u32', 'uint32_t', 32), (1, 'i32', 'int32_t', 32),
                                      (2, 'f32', 'float', 32), (3, 'u64', 'uint64_t', 64),
                                      (4, 'i64', 'int64_t', 64), (5, 'f64', 'double', 64)]:
        typed += [f'static {ctype} dxp_load_{name}(unsigned thread,unsigned tile,unsigned lane) {{',
                  f'  uint{width}_t bits=(uint{width}_t)dxp_cpu_read_bits(thread,tile,lane,{dtype});',
                  f'  {ctype} value; memcpy(&value,&bits,sizeof(value)); return value;', '}',
                  f'static void dxp_store_{name}(unsigned thread,unsigned tile,unsigned lane,{ctype} value) {{',
                  f'  uint{width}_t bits=0; memcpy(&bits,&value,sizeof(value));',
                  f'  dxp_cpu_write_bits(thread,tile,lane,{dtype},bits);', '}']
    return prefix + command_header + image + '\n'.join(typed) + '\n#endif\n'

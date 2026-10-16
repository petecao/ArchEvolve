"""2026-10-16 ET. Source-shaped register bytes and global allocation counters.

Explicit ABI alignment is a source C++ access obligation, not a hardware even-ID
allocation rule. Explicit-ID CPU write stalls remain separate from pair guards.
"""


def render_header(command_header, *, register_words, alignment_by_dtype):
    if type(register_words) is not int or not 1 <= register_words <= 64:
        raise ValueError('register words must fit the explicit64-bit role mask')
    if (type(alignment_by_dtype) not in (list, tuple) or len(alignment_by_dtype) != 6
            or any(type(a) is not int or a not in (1, 2, 4, 8) for a in alignment_by_dtype)):
        raise ValueError('six explicit source scalar alignments required')
    prefix = ('static void dxg_reset_state(void);\n#define DXG_ON_RESET() dxg_reset_state()\n'
              f'#define DXG_REGS {register_words}\n')
    aligns = ','.join(str(a) for a in alignment_by_dtype)
    header = r'''
#ifndef SWDB_DX_REGISTER_STATE_H
#define SWDB_DX_REGISTER_STATE_H
#ifdef __cplusplus
#define DXG_ALIGN(T) alignof(T)
#define DXG_ABI(c) static_assert(c,"register source ABI")
#else
#define DXG_ALIGN(T) _Alignof(T)
#define DXG_ABI(c) _Static_assert(c,"register source ABI")
#endif
'''
    for dtype, ctype in enumerate(['uint32_t', 'int32_t', 'float', 'uint64_t', 'int64_t', 'double']):
        header += f'DXG_ABI(DXG_ALIGN({ctype}) == {alignment_by_dtype[dtype]});\n'
    header += f'static const unsigned dxg_alignment[6]={{{aligns}}};\n'
    header += r'''
struct dxg_byte { unsigned initialized,parent,shift; };
static struct dxg_byte dxg_image[DXG_REGS*4];
static int dxg_owner[DXG_REGS];
static unsigned dxg_next;
struct dxg_role { unsigned bound; uint64_t explicit_read,explicit_write,physical_read,physical_write; };
static struct dxg_role dxg_roles[DXC_COMMANDS];
static void dxg_reset_state(void) {
  dxg_next=0;
  for (unsigned i=0; i<DXG_REGS; ++i) dxg_owner[i]=-1;
  for (unsigned i=0; i<DXG_REGS*4; ++i) dxg_image[i].initialized=0;
  for (unsigned i=0; i<DXC_COMMANDS; ++i) dxg_roles[i].bound=0;
}
static unsigned dxg_width(unsigned dtype) {
  DXM_CHECK(dtype < 6,"numeric-type-domain"); return dtype < 3 ? 4 : 8;
}
static unsigned dxg_halves(unsigned reg,unsigned dtype) {
  unsigned halves=dxg_width(dtype)/4;
  DXM_CHECK(reg < DXG_REGS && halves <= DXG_REGS-reg,"register-pair-domain");
  return halves;
}
static void dxg_init_counters(void) { dxg_next=0; }
/* MAA_gem5.hpp:129-145: allocation changes counters, not payload or pending
   commands. An8-byte allocation may have an odd ID; it is not a dereference. */
static unsigned dxg_new(unsigned thread,unsigned dtype) {
  DXM_CHECK(thread < 2,"thread-domain");
  unsigned halves=dxg_halves(dxg_next,dtype), reg=dxg_next;
  for (unsigned j=0; j<halves; ++j)
    DXM_CHECK(dxg_owner[reg+j] == -1 || dxg_owner[reg+j] == (int)thread,"register-ownership");
  for (unsigned j=0; j<halves; ++j) dxg_owner[reg+j]=(int)thread;
  dxg_next += halves;
  return reg;
}
static void dxg_use(unsigned thread,unsigned reg,unsigned dtype) {
  DXM_CHECK(thread < 2,"thread-domain");
  unsigned halves=dxg_halves(reg,dtype);
  /* Actual source RF::getData/setData and MMIO T* dereferences at reg*4. */
  DXM_CHECK((reg*4)%dxg_alignment[dtype] == 0,"register-source-alignment");
  for (unsigned j=0; j<halves; ++j)
    DXM_CHECK(dxg_owner[reg+j] == (int)thread,"register-ownership");
}
static uint64_t dxg_mask(unsigned reg,unsigned dtype) {
  unsigned halves=dxg_halves(reg,dtype);
  uint64_t mask=0;
  for (unsigned j=0; j<halves; ++j) mask |= UINT64_C(1) << (reg+j);
  return mask;
}
static void dxg_bind_roles(unsigned command,uint64_t explicit_read,uint64_t explicit_write,
    uint64_t physical_read,uint64_t physical_write) {
  DXM_CHECK(command < dxc_count && dxc_constructing == command+1,"command-binding");
  DXM_CHECK(!dxg_roles[command].bound,"register-role-binding");
  DXM_CHECK(!(explicit_read & ~physical_read) && !(explicit_write & ~physical_write),"register-role-domain");
  unsigned thread=dxc_commands[command].thread;
  for (unsigned r=0; r<64; ++r) {
    if (((physical_read | physical_write) >> r) & 1) {
      DXM_CHECK(r < DXG_REGS,"register-pair-domain");
      DXM_CHECK(dxg_owner[r] == (int)thread,"register-ownership");
    }
  }
  /* pushInstruction has no register dependency stall. Ambiguous RF races are
     software refusals, not invented command ordering or second-half stalls. */
  for (unsigned i=0; i<command; ++i) {
    struct dxg_role *old=&dxg_roles[i];
    if (dxc_commands[i].pending && old->bound)
      DXM_CHECK(!(old->physical_write & (physical_read | physical_write))
                && !(old->physical_read & physical_write),"pending-register-pair");
  }
  struct dxg_role *r=&dxg_roles[command];
  r->bound=1; r->explicit_read=explicit_read; r->explicit_write=explicit_write;
  r->physical_read=physical_read; r->physical_write=physical_write;
}
static unsigned dxg_capture_bits(unsigned reg,unsigned dtype) {
  unsigned bytes=dxg_width(dtype), parents[8]={0}, shifts[8]={0}, missing=UINT_MAX;
  dxg_halves(reg,dtype);
  for (unsigned j=0; j<bytes; ++j) {
    struct dxg_byte *b=&dxg_image[reg*4+j];
    if (b->initialized) { parents[j]=b->parent; shifts[j]=b->shift; }
    else {
      if (missing == UINT_MAX) missing=dxm_uninitialized_with_rule(1);
      parents[j]=missing;
    }
  }
  return dxm_bytes(parents,shifts,bytes);
}
static void dxg_set_version(unsigned reg,unsigned dtype,unsigned root) {
  unsigned bytes=dxg_width(dtype);
  dxg_halves(reg,dtype);
  DXM_CHECK(root < dxm_count,"producer-version-domain");
  for (unsigned j=0; j<bytes; ++j) {
    struct dxg_byte *b=&dxg_image[reg*4+j];
    b->initialized=1; b->parent=root; b->shift=j;
  }
}
static void dxg_bind_output(unsigned command,unsigned reg,unsigned dtype,unsigned root) {
  DXM_CHECK(command < dxc_count && dxc_constructing == command+1,"command-binding");
  dxg_use(dxc_commands[command].thread,reg,dtype);
  uint64_t mask=dxg_mask(reg,dtype);
  struct dxg_role *r=&dxg_roles[command];
  DXM_CHECK(r->bound && (r->physical_write & mask) == mask
            && (r->explicit_write & (UINT64_C(1)<<reg)),"register-command-output-domain");
  dxg_set_version(reg,dtype,root);
}
static void dxg_cpu_access(unsigned thread,unsigned reg,unsigned dtype,unsigned write) {
  DXM_CHECK(!dxc_constructing,"unbound-command"); dxg_use(thread,reg,dtype);
  uint64_t mask=dxg_mask(reg,dtype), start=UINT64_C(1)<<reg;
  /* IF.cc:233-249 compares the CPU write's starting ID to explicit register
     operands. It does not expand either operand's8-byte pair. */
  if (write) {
    for (unsigned i=0; i<dxc_count; ++i) {
      struct dxg_role *r=&dxg_roles[i];
      if (dxc_commands[i].pending && r->bound && ((r->explicit_read | r->explicit_write) & start)) dxc_cover(i);
    }
  }
  for (unsigned i=0; i<dxc_count; ++i) {
    struct dxg_role *r=&dxg_roles[i];
    if (dxc_commands[i].pending && r->bound) {
      if (write) DXM_CHECK(!((r->physical_read | r->physical_write) & mask),"pending-register-pair");
      else DXM_CHECK(!(r->physical_write & mask),"pending-register-write");
    }
  }
}
static void dxg_cpu_write_bits(unsigned thread,unsigned reg,unsigned dtype,uint64_t value) {
  dxg_cpu_access(thread,reg,dtype,1);
  if (dxg_width(dtype) == 4) value &= UINT32_MAX;
  dxg_set_version(reg,dtype,dxm_constant(value));
}
static unsigned dxg_new_initialized(unsigned thread,unsigned dtype,uint64_t value) {
  /* Capacity is a call-site obligation before the source overload's MMIO
     write, which occurs before its final capacity assertion. */
  unsigned reg=dxg_new(thread,dtype);
  dxg_cpu_write_bits(thread,reg,dtype,value);
  return reg;
}
static uint64_t dxg_cpu_read_bits(unsigned thread,unsigned reg,unsigned dtype) {
  dxg_cpu_access(thread,reg,dtype,0);
  unsigned root=dxg_capture_bits(reg,dtype); dxm_cover(root); return dxm_value(root);
}
#endif
'''
    return prefix + command_header + header

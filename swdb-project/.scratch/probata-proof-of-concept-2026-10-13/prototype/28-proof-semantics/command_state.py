"""2026-10-15 ET. Command completion is distinct from knowing output values.

Physical tile halves and explicit hardware tile IDs remain separate masks.
Region IDs are checked assignments supplied by the call wrapper; registration,
physical-line correspondence and deferred write actions are not supplied here.
"""


def render_header(values_header):
    return values_header + r'''
#ifndef SWDB_DX_COMMAND_STATE_H
#define SWDB_DX_COMMAND_STATE_H
#ifndef DXC_COMMANDS
#define DXC_COMMANDS 64
#endif
#ifndef DXC_REGIONS
#define DXC_REGIONS 8
#endif
#ifndef DXC_ON_RESET
#define DXC_ON_RESET() ((void)0)
#endif
#ifndef DXC_ON_COMPLETE
#define DXC_ON_COMPLETE(id) ((void)(id))
#endif
#ifndef DXR_ON_RESET
#define DXR_ON_RESET() ((void)0)
#endif
#ifndef DXP_ON_RESET
#define DXP_ON_RESET() ((void)0)
#endif
struct dxc_command {
  unsigned thread, pending, bound, root, access;
  int region;
  uint64_t explicit_read, explicit_write, physical_read, physical_write, begin, end, dependencies;
};
static struct dxc_command dxc_commands[DXC_COMMANDS];
static unsigned dxc_count, dxc_constructing;
static void dxc_cover(unsigned id);
struct dxc_span { uint64_t begin, end; };
/* Addresses are in a supplied physical byte domain. Neither C pointer
   validity nor distinct allocation objects establish this correspondence.
   line_bytes must be pinned to the configured gem5 block size by integration. */
static struct dxc_span dxc_store_span(uint64_t address, uint64_t bytes, uint64_t line_bytes) {
  DXM_CHECK(bytes > 0 && line_bytes > 0, "physical-footprint-domain");
  DXM_CHECK(address <= UINT64_MAX-(bytes-1), "physical-address-overflow");
  uint64_t last=address+(bytes-1);
  uint64_t last_line=last-last%line_bytes;
  DXM_CHECK(last_line <= UINT64_MAX-line_bytes, "physical-address-overflow");
  struct dxc_span span={address-address%line_bytes,last_line+line_bytes};
  return span;
}
static void dxc_reset(void) {
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  DXM_CHECK(DXC_COMMANDS <= 64, "command-mask-capacity");
  dxm_reset(); dxc_count=0; dxc_constructing=0;
  DXC_ON_RESET();
  DXR_ON_RESET();
  DXP_ON_RESET();
}
static uint64_t dxc_tile_mask(unsigned tile, unsigned bytes) {
  unsigned halves=dxm_tile_halves(tile,bytes);
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  uint64_t mask=0;
  for (unsigned i=0; i<halves; ++i) mask |= UINT64_C(1) << (tile+i);
  return mask;
}
static void dxc_check_mask(unsigned thread, uint64_t mask) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  for (unsigned i=0; i<64; ++i) {
    if ((mask >> i) & 1) {
      DXM_CHECK(i < DXM_TILES, "tile-domain");
      DXM_CHECK(dxm_tile_owner[i] == (int)thread, "tile-ownership");
    }
  }
}
/* Preparation is before issue-time memory snapshots. Binding follows without
   an intervening source action; wrappers must use this pair as one call. */
static unsigned dxc_prepare(unsigned thread, int region, unsigned access,
    uint64_t explicit_read, uint64_t explicit_write,
    uint64_t physical_read, uint64_t physical_write, uint64_t begin, uint64_t end) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(DXC_COMMANDS <= 64, "command-mask-capacity");
  DXM_CHECK(access <= 2, "access-kind-domain");
  if (access == 0) {
    DXM_CHECK(region == -1 && begin == 0 && end == 0, "compute-memory-footprint");
  } else {
    DXM_CHECK(region >= 0 && region < DXC_REGIONS, "assigned-region-domain");
    DXM_CHECK(begin < end, "memory-footprint-domain");
  }
  dxc_check_mask(thread,physical_write | physical_read);
  /* Software pair-disjointness obligation; distinct hardware starting IDs
     alone do not exclude a destination's second-half alias with an input. */
  DXM_CHECK(!(physical_read & physical_write), "intra-command-physical-alias");
  DXM_CHECK((explicit_write & ~physical_write) == 0 && (explicit_read & ~physical_read) == 0,
            "explicit-tile-footprint");
  /* IF.cc:193-218: new explicit destinations stall matching old operands;
     region conflicts span one global instance. Read/read does not stall. */
  for (unsigned i=0; i<dxc_count; ++i) {
    struct dxc_command *old=&dxc_commands[i];
    if (old->pending && ((explicit_write & (old->explicit_read | old->explicit_write))
        || (access != 0 && old->access != 0 && old->region == region
            && (access == 2 || old->access == 2)))) dxc_cover(i);
  }
  uint64_t dependencies=0;
  for (unsigned i=0; i<dxc_count; ++i) {
    struct dxc_command *old=&dxc_commands[i];
    if (old->pending) {
      if (access != 0 && old->access != 0 && begin < old->end && old->begin < end)
        DXM_CHECK(access != 2 && old->access != 2, "device-memory-footprint-conflict");
      unsigned dependent=(explicit_read & old->explicit_write) != 0;
      DXM_CHECK(!(old->physical_write & physical_write) && !(old->physical_read & physical_write)
                && (!(old->physical_write & physical_read) || dependent), "pending-tile-write");
      if (dependent) dependencies |= UINT64_C(1) << i;
    }
  }
  DXM_CHECK(dxc_count < DXC_COMMANDS, "command-history-capacity");
  unsigned id=dxc_count++;
  struct dxc_command *c=&dxc_commands[id];
  c->thread=thread; c->pending=1; c->bound=0;
  c->region=region; c->access=access; c->begin=begin; c->end=end;
  c->dependencies=dependencies;
  c->explicit_read=explicit_read; c->physical_read=physical_read;
  c->explicit_write=explicit_write; c->physical_write=physical_write;
  dxc_constructing=id+1;
  return id;
}
static void dxc_bind(unsigned id, unsigned root) {
  DXM_CHECK(dxc_constructing == id+1 && id < dxc_count, "command-binding");
  DXM_CHECK(root < dxm_count, "producer-version-domain");
  dxc_commands[id].root=root; dxc_commands[id].bound=1;
  dxc_constructing=0;
}
static void dxc_cover(unsigned id) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  DXM_CHECK(id < dxc_count && dxc_commands[id].bound, "command-domain");
  unsigned needed[DXC_COMMANDS]={0}; needed[id]=1;
  for (unsigned cursor=id+1; cursor>0; --cursor) {
    unsigned i=cursor-1;
    if (needed[i]) {
      for (unsigned parent=0; parent<i; ++parent)
        if ((dxc_commands[i].dependencies >> parent) & 1) needed[parent]=1;
    }
  }
  for (unsigned i=0; i<=id; ++i) {
    if (needed[i] && dxc_commands[i].pending) {
      DXM_CHECK(dxc_commands[i].bound, "command-binding");
      dxm_cover(dxc_commands[i].root);
      DXC_ON_COMPLETE(i);
      dxc_commands[i].pending=0;
    }
  }
}
/* gem5 compares explicit starting IDs. No thread-owner check: this is one
   global instance and a wait observes matching commands from either thread. */
static void dxc_wait_tile(unsigned tile) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  DXM_CHECK(tile < DXM_TILES, "tile-domain");
  uint64_t mask=UINT64_C(1) << tile;
  for (unsigned i=0; i<dxc_count; ++i)
    if (dxc_commands[i].pending && ((dxc_commands[i].explicit_read | dxc_commands[i].explicit_write) & mask)) dxc_cover(i);
}
/* Logical query absent from the pinned source header. Both pending answers
   are permitted; returning one has exactly the covering-wait effect. This
   gives no termination or fairness premise to a polling loop. */
static unsigned dxc_get_tile_ready(unsigned tile) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  DXM_CHECK(tile < DXM_TILES, "tile-domain");
  uint64_t mask=UINT64_C(1) << tile;
  unsigned pending=0;
  for (unsigned i=0; i<dxc_count; ++i)
    if (dxc_commands[i].pending && ((dxc_commands[i].explicit_read | dxc_commands[i].explicit_write) & mask)) pending=1;
  if (!pending) return 1;
  unsigned ready=DXM_CHOOSE(2);
  DXM_CHECK(ready < 2, "nondeterministic-choice-domain");
  if (ready) dxc_wait_tile(tile);
  return ready;
}
static void dxc_cpu_tile_access(unsigned thread, unsigned tile, unsigned bytes, unsigned write) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(write <= 1, "access-kind-domain");
  dxm_use_tile(thread,tile,bytes);
  uint64_t mask=dxc_tile_mask(tile,bytes);
  for (unsigned i=0; i<dxc_count; ++i)
    if (dxc_commands[i].pending) {
      DXM_CHECK(!(dxc_commands[i].physical_write & mask), "pending-tile-write");
      if (write) DXM_CHECK(!(dxc_commands[i].physical_read & mask), "pending-tile-read");
    }
}
static void dxc_cpu_memory_access(unsigned thread, uint64_t begin, uint64_t end, unsigned write) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(begin < end, "memory-footprint-domain");
  DXM_CHECK(write <= 1, "access-kind-domain");
  for (unsigned i=0; i<dxc_count; ++i) {
    struct dxc_command *c=&dxc_commands[i];
    if (c->pending && begin < c->end && c->begin < end) {
      DXM_CHECK(c->access != 2, "store-footprint-cpu-access");
      if (write && c->access == 1)
        DXM_CHECK(c->thread != thread, "same-thread-read-footprint-write");
    }
  }
}
/* The call-site audit must bind cell and physical span to the same actual
   source access. These functions do not infer addresses from a C object. */
static uint64_t dxc_cpu_read(unsigned thread, unsigned cell, uint64_t begin, uint64_t end) {
  dxc_cpu_memory_access(thread,begin,end,0);
  return dxm_cpu_read(thread,cell);
}
static void dxc_cpu_write(unsigned thread, unsigned cell, uint64_t begin, uint64_t end, uint64_t value) {
  dxc_cpu_memory_access(thread,begin,end,1);
  dxm_cpu_write(thread,cell,value);
}
static unsigned dxc_cpu_cas(unsigned thread, unsigned cell, uint64_t begin, uint64_t end,
    uint64_t *expected, uint64_t desired) {
  uint64_t actual=dxc_cpu_read(thread,cell,begin,end);
  if (actual == *expected) {
    dxc_cpu_write(thread,cell,begin,end,desired);
    return 1;
  }
  *expected=actual;
  return 0;
}
#endif
'''

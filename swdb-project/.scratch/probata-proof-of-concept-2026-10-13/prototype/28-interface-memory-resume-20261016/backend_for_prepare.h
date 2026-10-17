
static void dxr_reset_state(void);
#define DXR_ON_RESET() dxr_reset_state()

#ifndef SWDB_DX_DEFERRED_STATE_H
#define SWDB_DX_DEFERRED_STATE_H
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#ifndef DXM_CELLS
#define DXM_CELLS 64
#endif
#ifndef DXM_NODES
#define DXM_NODES 128
#endif
#ifndef DXM_HISTORY
#define DXM_HISTORY 64
#endif
#ifndef DXM_EVENTS
#define DXM_EVENTS 128
#endif
#ifndef DXM_TILES
#define DXM_TILES 8
#endif
#ifndef DXM_CHECK
#define DXM_CHECK(c, rule) assert(c)
#endif
#ifndef DXM_EVAL
static uint64_t dxm_missing_numeric_binding(unsigned dtype, unsigned op, uint64_t a, uint64_t b) {
  (void)dtype; (void)op; (void)a; (void)b;
  DXM_CHECK(0, "numeric-runtime-binding"); return 0;
}
#define DXM_EVAL(dtype,op,a,b) dxm_missing_numeric_binding(dtype,op,a,b)
#endif
/* DXM_CHOOSE(n) is the model's bounded nondeterministic primitive: 0 <= result < n.
   Native controls enumerate it. It is not a candidate entry precondition. */
struct dxm_node {
  unsigned kind, issuer, cell, count, settled, dtype, op, left, right, otherwise, extent, event_start;
  unsigned byte_count, byte_parent[8], byte_shift[8];
  uint64_t value, history[DXM_HISTORY];
  uint64_t issue_values[DXM_CELLS];
  unsigned issue_initialized[DXM_CELLS];
};
struct dxm_write_event { unsigned cell; uint64_t value; };
static struct dxm_write_event dxm_events[DXM_EVENTS];
static unsigned dxm_event_count;
static struct dxm_node dxm_nodes[DXM_NODES];
static unsigned dxm_count;
static uint64_t dxm_memory[DXM_CELLS];
static unsigned dxm_initialized[DXM_CELLS];
/* Software ownership, not an assertion that gem5 enforces thread isolation. */
static int dxm_tile_owner[DXM_TILES];
static void dxm_reset(void) {
  dxm_count=0; dxm_event_count=0;
  for (unsigned i=0; i<DXM_CELLS; ++i) {
    dxm_memory[i]=0; dxm_initialized[i]=0;
  }
  for (unsigned i=0; i<DXM_TILES; ++i) dxm_tile_owner[i]=-1;
}
static unsigned dxm_tile_halves(unsigned tile, unsigned bytes) {
  DXM_CHECK(bytes == 4 || bytes == 8, "tile-width-domain");
  DXM_CHECK(tile < DXM_TILES, "tile-domain");
  unsigned halves=bytes/4;
  DXM_CHECK(halves <= DXM_TILES-tile, "tile-pair-domain");
  return halves;
}
static void dxm_claim_tile(unsigned thread, unsigned tile, unsigned bytes) {
  DXM_CHECK(thread < 2, "thread-domain");
  unsigned halves=dxm_tile_halves(tile,bytes);
  for (unsigned i=0; i<halves; ++i)
    DXM_CHECK(dxm_tile_owner[tile+i] == -1, "tile-already-owned");
  for (unsigned i=0; i<halves; ++i) dxm_tile_owner[tile+i]=(int)thread;
}
static void dxm_use_tile(unsigned thread, unsigned tile, unsigned bytes) {
  DXM_CHECK(thread < 2, "thread-domain");
  unsigned halves=dxm_tile_halves(tile,bytes);
  for (unsigned i=0; i<halves; ++i)
    DXM_CHECK(dxm_tile_owner[tile+i] == (int)thread, "tile-ownership");
}
static void dxm_cpu_write(unsigned thread, unsigned cell, uint64_t value) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(cell < DXM_CELLS, "cell-domain");
  DXM_CHECK(dxm_event_count < DXM_EVENTS, "memory-event-capacity");
  for (unsigned i=0; i<dxm_count; ++i) {
    struct dxm_node *n=&dxm_nodes[i];
    if (!n->settled && n->kind == 0 && n->cell == cell) {
      DXM_CHECK(n->issuer != thread, "same-thread-read-footprint-write");
      DXM_CHECK(n->count < DXM_HISTORY, "history-capacity");
    }
    if (!n->settled && n->kind == 3 && cell >= n->cell && cell-n->cell < n->extent)
      DXM_CHECK(n->issuer != thread, "same-thread-read-footprint-write");
  }
  dxm_memory[cell]=value; dxm_initialized[cell]=1;
  dxm_events[dxm_event_count].cell=cell;
  dxm_events[dxm_event_count++].value=value;
  for (unsigned i=0; i<dxm_count; ++i) {
    struct dxm_node *n=&dxm_nodes[i];
    if (!n->settled && n->kind == 0 && n->cell == cell) {
      n->history[n->count++]=value;
    }
  }
}
/* Actual device event, after command-level physical conflicts are discharged.
   It extends other unfinished read intervals without pretending to be a CPU. */
static void dxm_device_write(unsigned cell, uint64_t value) {
  DXM_CHECK(cell < DXM_CELLS, "cell-domain");
  DXM_CHECK(dxm_event_count < DXM_EVENTS, "memory-event-capacity");
  for (unsigned i=0; i<dxm_count; ++i) {
    struct dxm_node *n=&dxm_nodes[i];
    if (!n->settled && n->kind == 0 && n->cell == cell)
      DXM_CHECK(n->count < DXM_HISTORY, "history-capacity");
  }
  dxm_memory[cell]=value; dxm_initialized[cell]=1;
  dxm_events[dxm_event_count].cell=cell;
  dxm_events[dxm_event_count++].value=value;
  for (unsigned i=0; i<dxm_count; ++i) {
    struct dxm_node *n=&dxm_nodes[i];
    if (!n->settled && n->kind == 0 && n->cell == cell) n->history[n->count++]=value;
  }
}
static uint64_t dxm_cpu_read(unsigned thread, unsigned cell) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(cell < DXM_CELLS, "cell-domain");
  DXM_CHECK(dxm_initialized[cell], "read-initialized");
  return dxm_memory[cell];
}
/* One fixed sequential event. Failed CAS performs a read and expected update,
   never a write of desired and never a new history candidate. */
static unsigned dxm_cpu_cas(unsigned thread, unsigned cell, uint64_t *expected, uint64_t desired) {
  uint64_t actual=dxm_cpu_read(thread,cell);
  if (actual == *expected) {
    dxm_cpu_write(thread,cell,desired);
    return 1;
  }
  *expected=actual;
  return 0;
}
static unsigned dxm_issue_read(unsigned thread, unsigned cell) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(cell < DXM_CELLS, "cell-domain");
  DXM_CHECK(dxm_initialized[cell], "read-initialized");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=0; n->issuer=thread; n->cell=cell; n->count=1; n->settled=0;
  n->history[0]=dxm_memory[cell]; n->value=0;
  return id;
}
static unsigned dxm_constant(uint64_t value) {
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  dxm_nodes[id].kind=1; dxm_nodes[id].settled=1; dxm_nodes[id].value=value;
  return id;
}
/* A deferred index is a captured producer version. Candidate-cell snapshots
   are logical shadow values, never speculative C pointer dereferences. A
   checked caller mapping must justify base/extent and its uint32 index view. */
static unsigned dxm_issue_indexed_read(unsigned thread, unsigned index, unsigned base, unsigned extent) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(index < dxm_count, "producer-version-domain");
  DXM_CHECK(base < DXM_CELLS && extent > 0 && extent <= DXM_CELLS-base, "cell-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=3; n->issuer=thread; n->left=index; n->cell=base; n->extent=extent; n->settled=0;
  n->event_start=dxm_event_count;
  for (unsigned i=0; i<DXM_CELLS; ++i) {
    n->issue_values[i]=dxm_memory[i]; n->issue_initialized[i]=dxm_initialized[i];
  }
  return id;
}
static unsigned dxm_issue_binary(unsigned thread, unsigned dtype, unsigned op, unsigned left, unsigned right) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(left < dxm_count && right < dxm_count, "producer-version-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=2; n->issuer=thread; n->dtype=dtype; n->op=op;
  n->left=left; n->right=right; n->settled=0;
  return id;
}
/* A value expression, not cancellation of an independently issued command.
   The command wrapper must separately track every issued memory action. */
static unsigned dxm_select(unsigned thread, unsigned condition, unsigned yes, unsigned no) {
  DXM_CHECK(thread < 2, "thread-domain");
  DXM_CHECK(condition < dxm_count && yes < dxm_count && no < dxm_count, "producer-version-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=4; n->issuer=thread; n->left=condition; n->right=yes; n->otherwise=no; n->settled=0;
  return id;
}
static unsigned dxm_join(unsigned left,unsigned right) {
  DXM_CHECK(left < dxm_count && right < dxm_count, "producer-version-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=5; n->left=left; n->right=right; n->settled=0;
  return id;
}
static unsigned dxm_result(void) {
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  dxm_nodes[id].kind=6; dxm_nodes[id].settled=0;
  return id;
}
static unsigned dxm_uninitialized_with_rule(unsigned is_register) {
  DXM_CHECK(is_register <= 1, "initializedness-rule-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  dxm_nodes[id].kind=8; dxm_nodes[id].settled=0; dxm_nodes[id].op=is_register;
  return id;
}
static unsigned dxm_uninitialized(void) { return dxm_uninitialized_with_rule(0); }
static void dxm_publish(unsigned id,uint64_t value) {
  DXM_CHECK(id < dxm_count && dxm_nodes[id].kind == 6, "action-result-domain");
  DXM_CHECK(!dxm_nodes[id].settled, "immutable-action-result");
  dxm_nodes[id].value=value; dxm_nodes[id].settled=1;
}
/* Inactive old-result lanes retain the captured version without evaluating it.
   The edge must descend even when its target is uninitialized. */
static void dxm_publish_alias(unsigned id,unsigned parent) {
  DXM_CHECK(id < dxm_count && dxm_nodes[id].kind == 6, "action-result-domain");
  DXM_CHECK(!dxm_nodes[id].settled, "immutable-action-result");
  DXM_CHECK(parent < id, "acyclic-producer-version");
  if (dxm_nodes[parent].settled) dxm_publish(id,dxm_nodes[parent].value);
  else { dxm_nodes[id].kind=9; dxm_nodes[id].left=parent; }
}
static unsigned dxm_bytes(const unsigned *parents,const unsigned *shifts,unsigned count) {
  DXM_CHECK(count == 4 || count == 8, "image-width-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=7; n->byte_count=count; n->settled=0;
  for (unsigned i=0; i<count; ++i) {
    DXM_CHECK(parents[i] < id && shifts[i] < 8, "image-producer-version-domain");
    n->byte_parent[i]=parents[i]; n->byte_shift[i]=shifts[i];
  }
  return id;
}
static unsigned dxm_byte_select(unsigned condition,unsigned yes,unsigned yes_shift,unsigned no,unsigned no_shift) {
  DXM_CHECK(condition < dxm_count && yes < dxm_count && no < dxm_count, "producer-version-domain");
  DXM_CHECK(yes_shift < 8 && no_shift < 8, "image-byte-domain");
  DXM_CHECK(dxm_count < DXM_NODES, "node-capacity");
  unsigned id=dxm_count++;
  struct dxm_node *n=&dxm_nodes[id];
  n->kind=10; n->left=condition; n->right=yes; n->otherwise=no; n->settled=0;
  n->byte_shift[0]=yes_shift; n->byte_shift[1]=no_shift;
  return id;
}
static void dxm_cover(unsigned id) {
  DXM_CHECK(id < dxm_count, "node-domain");
  DXM_CHECK(DXM_NODES > 0 && DXM_NODES <= UINT_MAX/20, "node-capacity-domain");
  unsigned stack[DXM_NODES], phase[DXM_NODES], depth=1, steps=0;
  stack[0]=id; phase[0]=0;
  /* Explicit DFS: immutable parent IDs strictly decrease. Conditions settle
     before choosing a branch; unused operands have no evaluation side effect. */
  while (depth) {
    DXM_CHECK(steps++ < 20*DXM_NODES, "evaluation-step-capacity");
    unsigned frame=depth-1, i=stack[frame];
    struct dxm_node *n=&dxm_nodes[i];
    if (n->settled) { --depth; continue; }
    if (n->kind == 6) { DXM_CHECK(0, "action-result-before-completion"); return; }
    if (n->kind == 8) { DXM_CHECK(0, n->op ? "register-value-initialized" : "tile-value-initialized"); return; }
    unsigned parent=0, visit=0;
    if ((n->kind == 2 || n->kind == 5) && phase[frame] < 2) {
      parent=phase[frame] == 0 ? n->left : n->right;
      ++phase[frame]; visit=1;
    } else if ((n->kind == 3 || n->kind == 9) && phase[frame] == 0) {
      parent=n->left; ++phase[frame]; visit=1;
    } else if ((n->kind == 4 || n->kind == 10) && phase[frame] < 2) {
      parent=phase[frame] == 0 ? n->left : (dxm_nodes[n->left].value ? n->right : n->otherwise);
      ++phase[frame]; visit=1;
    } else if (n->kind == 7 && phase[frame] < n->byte_count) {
      parent=n->byte_parent[phase[frame]++]; visit=1;
    }
    if (visit) {
      DXM_CHECK(parent < i, "acyclic-producer-version");
      DXM_CHECK(depth < DXM_NODES, "evaluation-stack-capacity");
      stack[depth]=parent; phase[depth]=0; ++depth; continue;
    }
      if (n->kind == 0) {
        unsigned pick=DXM_CHOOSE(n->count);
        DXM_CHECK(pick < n->count, "nondeterministic-choice-domain");
        n->value=n->history[pick];
      } else if (n->kind == 2) {
        n->value=DXM_EVAL(n->dtype,n->op,dxm_nodes[n->left].value,dxm_nodes[n->right].value);
      } else if (n->kind == 3) {
        uint64_t index=dxm_nodes[n->left].value;
        DXM_CHECK(index <= UINT32_MAX, "index-type-domain");
        DXM_CHECK(index < n->extent, "index-cell-domain");
        unsigned cell=n->cell+(unsigned)index;
        DXM_CHECK(n->issue_initialized[cell], "read-initialized");
        uint64_t candidates[DXM_HISTORY];
        unsigned count=1; candidates[0]=n->issue_values[cell];
        for (unsigned e=n->event_start; e<dxm_event_count; ++e) {
          if (dxm_events[e].cell == cell) {
            DXM_CHECK(count < DXM_HISTORY, "history-capacity");
            candidates[count++]=dxm_events[e].value;
          }
        }
        unsigned pick=DXM_CHOOSE(count);
        DXM_CHECK(pick < count, "nondeterministic-choice-domain");
        n->value=candidates[pick];
      } else if (n->kind == 5) {
        n->value=0;
      } else if (n->kind == 9) {
        n->value=dxm_nodes[n->left].value;
      } else if (n->kind == 10) {
        unsigned yes=dxm_nodes[n->left].value != 0;
        unsigned parent=yes ? n->right : n->otherwise;
        unsigned shift=n->byte_shift[yes ? 0 : 1];
        n->value=(dxm_nodes[parent].value >> (8*shift)) & UINT64_C(255);
      } else if (n->kind == 7) {
        n->value=0;
        for (unsigned j=0; j<n->byte_count; ++j) {
          uint64_t byte=(dxm_nodes[n->byte_parent[j]].value >> (8*n->byte_shift[j])) & UINT64_C(255);
          n->value |= byte << (8*j);
        }
      } else {
        DXM_CHECK(n->kind == 4, "value-node-kind-domain");
        n->value=dxm_nodes[dxm_nodes[n->left].value ? n->right : n->otherwise].value;
      }
      n->settled=1;
      --depth;
  }
}
static uint64_t dxm_value(unsigned id) {
  DXM_CHECK(id < dxm_count, "node-domain");
  DXM_CHECK(dxm_nodes[id].settled, "value-before-cover");
  return dxm_nodes[id].value;
}
#endif

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
#ifndef DXG_ON_RESET
#define DXG_ON_RESET() ((void)0)
#endif
#ifndef DXS_ON_RESET
#define DXS_ON_RESET() ((void)0)
#endif
#ifndef DXZ_ON_RESET
#define DXZ_ON_RESET() ((void)0)
#endif
struct dxc_command {
  unsigned thread, pending, bound, root, access;
  int region;
  uint64_t explicit_read, explicit_write, physical_read, physical_write, ready_roles, begin, end, dependencies;
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
  DXG_ON_RESET();
  DXS_ON_RESET();
  DXZ_ON_RESET();
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
static unsigned dxc_prepare_counted(unsigned thread, int region, unsigned access,
    uint64_t explicit_read, uint64_t explicit_write,
    uint64_t physical_read, uint64_t physical_write, uint64_t begin, uint64_t end,
    uint64_t ready_roles) {
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
  /* MAA.cc:563-580 counts src1/src2/dst1/dst2, not condition-only
     roles; SPD.cc:120-137 counts both physical halves for 8-byte roles.
     A checked call wrapper must derive this mask from resolved role widths.
     These subset checks alone cannot distinguish a condition from a source. */
  DXM_CHECK(!(ready_roles & ~(physical_read | physical_write))
            && !(physical_write & ~ready_roles), "ready-role-footprint");
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
  c->ready_roles=ready_roles;
  dxc_constructing=id+1;
  return id;
}
/* Condition-free native prototype convenience only. Callers with a condition
   operand must use the precise counted-role entry; no production call admission
   or source-role inference is provided by this convenience wrapper. */
static unsigned dxc_prepare(unsigned thread, int region, unsigned access,
    uint64_t explicit_read, uint64_t explicit_write,
    uint64_t physical_read, uint64_t physical_write, uint64_t begin, uint64_t end) {
  return dxc_prepare_counted(thread,region,access,explicit_read,explicit_write,
      physical_read,physical_write,begin,end,physical_read | physical_write);
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
/* A source ready-range MMIO read waits for the per-physical-tile counter.
   This differs from IF dispatch starting-ID matching. No thread-owner filter:
   one global instance observes counted commands from either thread. */
static void dxc_wait_tile(unsigned tile) {
  DXM_CHECK(!dxc_constructing, "unbound-command");
  DXM_CHECK(DXM_TILES <= 64, "tile-mask-capacity");
  DXM_CHECK(tile < DXM_TILES, "tile-domain");
  uint64_t mask=UINT64_C(1) << tile;
  for (unsigned i=0; i<dxc_count; ++i)
    if (dxc_commands[i].pending && (dxc_commands[i].ready_roles & mask)) dxc_cover(i);
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
    if (dxc_commands[i].pending && (dxc_commands[i].ready_roles & mask)) pending=1;
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

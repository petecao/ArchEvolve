"""2026-10-15 ET. Bounded deferred value engine for synthetic DX100 callers.

Cell identifiers here denote an already checked typed memory cell, not a C
pointer or inferred physical address. Integration must establish that mapping.
Each read chooses an actual value from its issue-to-cover interval exactly once.
Independent choices overapproximate correlations between reads; they do not
describe a packet schedule. Exhausting a bound is a checked domain obligation.
"""


def render_header():
    return r'''
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
static void dxm_cover(unsigned id) {
  DXM_CHECK(id < dxm_count, "node-domain");
  DXM_CHECK(DXM_NODES > 0 && DXM_NODES <= UINT_MAX/8, "node-capacity-domain");
  unsigned stack[DXM_NODES], phase[DXM_NODES], depth=1, steps=0;
  stack[0]=id; phase[0]=0;
  /* Explicit DFS: immutable parent IDs strictly decrease. Conditions settle
     before choosing a branch; unused operands have no evaluation side effect. */
  while (depth) {
    DXM_CHECK(steps++ < 8*DXM_NODES, "evaluation-step-capacity");
    unsigned frame=depth-1, i=stack[frame];
    struct dxm_node *n=&dxm_nodes[i];
    if (n->settled) { --depth; continue; }
    unsigned parent=0, visit=0;
    if (n->kind == 2 && phase[frame] < 2) {
      parent=phase[frame] == 0 ? n->left : n->right;
      ++phase[frame]; visit=1;
    } else if (n->kind == 3 && phase[frame] == 0) {
      parent=n->left; ++phase[frame]; visit=1;
    } else if (n->kind == 4 && phase[frame] < 2) {
      parent=phase[frame] == 0 ? n->left : (dxm_nodes[n->left].value ? n->right : n->otherwise);
      ++phase[frame]; visit=1;
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
'''

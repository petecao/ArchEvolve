"""2026-10-15 ET. Deferred logical-cell store effects, prototype only.

Physical-line hazards, source-to-cell/type correspondence and registration/F2
must be established by integration. Entry order is conservatively arbitrary;
no global packet/lane schedule is claimed. Conflicting full physical-line
accesses must be excluded before using these logical completion effects.
"""


def render_header(command_header):
    prefix = r'''
static void dxa_reset_state(void);
static void dxa_complete(unsigned id);
#define DXC_ON_RESET() dxa_reset_state()
#define DXC_ON_COMPLETE(id) dxa_complete(id)
'''
    actions = r'''
#ifndef SWDB_DX_ACTION_STATE_H
#define SWDB_DX_ACTION_STATE_H
#ifndef DXA_ACTIONS
#define DXA_ACTIONS 128
#endif
struct dxa_action {
  unsigned command,dtype,base,extent,index,value,active,done,kind,op,old_result,preserved;
};
static struct dxa_action dxa_actions[DXA_ACTIONS];
static unsigned dxa_count;
static void dxa_reset_state(void) { dxa_count=0; }
static unsigned dxa_store(unsigned command,unsigned dtype,unsigned base,unsigned extent,
    unsigned index,unsigned value,unsigned active) {
  DXM_CHECK(command < dxc_count && dxc_constructing == command+1, "action-command-binding");
  DXM_CHECK(dxc_commands[command].access == 2, "action-write-command");
  DXM_CHECK(dtype < 6, "numeric-type-domain");
  DXM_CHECK(base < DXM_CELLS && extent > 0 && extent <= DXM_CELLS-base, "cell-domain");
  DXM_CHECK(index < dxm_count && value < dxm_count && active < dxm_count, "producer-version-domain");
  DXM_CHECK(dxa_count < DXA_ACTIONS, "action-capacity");
  struct dxa_action *a=&dxa_actions[dxa_count++];
  a->command=command; a->dtype=dtype; a->base=base; a->extent=extent;
  a->index=index; a->value=value; a->active=active; a->done=0;
  a->kind=0; a->op=0; a->old_result=UINT_MAX;
  unsigned zero=dxm_constant(0);
  unsigned selected_index=dxm_select(dxc_commands[command].thread,active,index,zero);
  unsigned selected_value=dxm_select(dxc_commands[command].thread,active,value,zero);
  return dxm_join(selected_index,selected_value);
}
static unsigned dxa_rmw(unsigned command,unsigned dtype,unsigned op,unsigned base,unsigned extent,
    unsigned index,unsigned value,unsigned active,unsigned old_result,unsigned preserved) {
  DXM_CHECK(op == 0 || op == 4 || op == 5, "numeric-rmw-opcode-domain");
  DXM_CHECK(old_result < dxm_count && dxm_nodes[old_result].kind == 6 && !dxm_nodes[old_result].settled,
            "action-result-domain");
  DXM_CHECK(preserved < dxm_count, "producer-version-domain");
  unsigned root=dxa_store(command,dtype,base,extent,index,value,active);
  struct dxa_action *a=&dxa_actions[dxa_count-1];
  a->kind=1; a->op=op; a->old_result=old_result; a->preserved=preserved;
  unsigned zero=dxm_constant(0);
  unsigned inactive_old=dxm_select(dxc_commands[command].thread,active,zero,preserved);
  return dxm_join(root,inactive_old);
}
static void dxa_complete(unsigned command) {
  unsigned candidates[DXA_ACTIONS], count=0;
  for (unsigned i=0; i<dxa_count; ++i) {
    if (dxa_actions[i].command == command && !dxa_actions[i].done) candidates[count++]=i;
  }
  /* IndirectAccess.cc:898-940: old values alias the progressively modified
     copied line. No source establishes one global ascending lane order.
     Logical writes here are observational completion effects only under the
     command layer's full-line no-interference checks, not packet events. */
  while (count) {
    unsigned pick=count == 1 ? 0 : DXM_CHOOSE(count);
    DXM_CHECK(pick < count, "nondeterministic-choice-domain");
    unsigned i=candidates[pick]; candidates[pick]=candidates[--count];
    struct dxa_action *a=&dxa_actions[i];
      if (dxm_value(a->active)) {
        uint64_t index=dxm_value(a->index);
        DXM_CHECK(index <= UINT32_MAX && index < a->extent, "index-cell-domain");
        uint64_t value=dxm_value(a->value);
        if (a->dtype < 3) value &= UINT32_MAX;
        unsigned cell=a->base+(unsigned)index;
        if (a->kind == 1) {
          DXM_CHECK(dxm_initialized[cell], "read-initialized");
          uint64_t old=dxm_memory[cell];
          if (a->dtype < 3) old &= UINT32_MAX;
          value=dxt_evaluate_family(a->dtype,a->op,old,value,1);
          dxm_publish(a->old_result,old);
        }
        dxm_device_write(cell,value);
      } else if (a->kind == 1) {
        dxm_publish(a->old_result,dxm_value(a->preserved));
      }
      a->done=1;
  }
}
#endif
'''
    return prefix + command_header + actions

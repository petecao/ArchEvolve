"""2026-10-15 ET. Compose raw-bit numeric helpers with deferred value nodes.

This does not infer a source dtype, bind a runtime policy, or supply IEEE logic.
The caller supplies a provenance-bound runtime; a missing policy stays refused.
"""


def render_header(values_header, numeric_header):
    prefix = r'''
#include <assert.h>
#ifndef DXM_CHECK
#define DXM_CHECK(c,rule) assert(c)
#endif
#ifndef DX_NUM_CHECK
#define DX_NUM_CHECK(c,rule) DXM_CHECK(c,rule)
#endif
#ifndef DX_NUM_REFUSE
#define DX_NUM_REFUSE(rule) DXM_CHECK(0,rule)
#endif
'''
    bridge = r'''
static struct dx_num_runtime dxt_runtime;
/* Native test configuration only until source/runtime admission pins these
   flags. An arbitrary candidate must never gain this private entry point. */
static void dxt_set_runtime(struct dx_num_runtime runtime) { dxt_runtime=runtime; }
static uint64_t dxt_evaluate_family(unsigned dtype,unsigned op,uint64_t lhs,uint64_t rhs,unsigned family) {
  uint64_t value=0;
  enum dx_num_status status=dxv_eval_bits(dtype,op,lhs,rhs,family,&dxt_runtime,&value);
  DXM_CHECK(status != DX_NUM_UNSUPPORTED,"numeric-unsupported-domain");
  DXM_CHECK(status != DX_NUM_ARITHMETIC,"numeric-arithmetic-domain");
  DXM_CHECK(status != DX_NUM_RUNTIME,"numeric-runtime-binding");
  DXM_CHECK(status == DX_NUM_OK,"numeric-status-domain");
  return value;
}
#ifdef DXM_EVAL
#error "typed model must bind its own raw numeric evaluator"
#endif
#define DXM_EVAL(dtype,op,lhs,rhs) dxt_evaluate_family(dtype,op,lhs,rhs,0)
'''
    constructors = r'''
/* Structural source domains hold even when a condition disables evaluation.
   Arithmetic domains are checked only for the selected active expression. */
static unsigned dxt_binary(unsigned thread,unsigned dtype,unsigned op,unsigned lhs,unsigned rhs) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(op <= 15 && !((dtype == 2 || dtype == 5) && op >= 6 && op <= 10),"numeric-opcode-domain");
  return dxm_issue_binary(thread,dtype,op,lhs,rhs);
}
'''
    return prefix + numeric_header + bridge + values_header + constructors

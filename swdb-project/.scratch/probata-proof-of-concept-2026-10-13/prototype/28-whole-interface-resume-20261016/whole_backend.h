/*2026-10-16 ET. Source-only private composition; fatal hooks required. */
#ifndef DXM_CHECK
#error "bind classified fatal DXM_CHECK before inclusion"
#endif
#ifndef DXM_CHOOSE
#error "bind bounded independent DXM_CHOOSE before inclusion"
#endif
#define DXM_TILES 32
#define DXC_REGIONS 256
static void dxs_reset_state(void);
#define DXS_ON_RESET() dxs_reset_state()
#define DXS_SOURCE_TILES 32
#define DXS_SOURCE_REGS 32
#define DXS_SOURCE_WORDS 16384
#define DXS_SOURCE_MEMORY UINT64_C(17179869184)
static void dxz_reset_state(void);
#define DXZ_ON_RESET() dxz_reset_state()
static void dxp_reset_state(void);
#define DXP_ON_RESET() dxp_reset_state()
#define DXP_TILE_WORDS 16384
#define DXP_VALUE_BOUND 2
static void dxg_reset_state(void);
#define DXG_ON_RESET() dxg_reset_state()
#define DXG_REGS 32

static void dxr_reset_state(void);
#define DXR_ON_RESET() dxr_reset_state()

static void dxa_reset_state(void);
static void dxa_complete(unsigned id);
#define DXC_ON_RESET() dxa_reset_state()
#define DXC_ON_COMPLETE(id) dxa_complete(id)

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
/* Created2026-10-15 ET. Prototype numeric values; no device/refinement claim. */
#ifndef SWDB_DX_NUMERIC_VALUES_H
#define SWDB_DX_NUMERIC_VALUES_H
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <fenv.h>
#if defined(__cplusplus)
static_assert(CHAR_BIT==8 && sizeof(uint32_t)==4 && sizeof(uint64_t)==8 && sizeof(int)==4,"numeric ABI");
#else
_Static_assert(CHAR_BIT==8 && sizeof(uint32_t)==4 && sizeof(uint64_t)==8 && sizeof(int)==4,"numeric ABI");
#endif
#ifndef DX_NUM_CHECK
#error "DX_NUM_CHECK(condition, rule) must report a program arithmetic failure"
#endif
#ifndef DX_NUM_REFUSE
#error "DX_NUM_REFUSE(rule) must report an unsupported model/runtime domain"
#endif
/* Flags represent provenance-bound policies, never inferred from operand values.
   signed_shift=1 means C++17 left shift and arithmetic negative right shift;
   ieee=1 and unordered_first=1 will be used only by the floating slice. */
struct dx_num_runtime {
  unsigned signed_shift_cpp17_arithmetic;
  unsigned ieee_binary_rn;
  unsigned alu_minmax_unordered_first;
};
enum dx_num_status { DX_NUM_OK=0, DX_NUM_UNSUPPORTED=1, DX_NUM_ARITHMETIC=2, DX_NUM_RUNTIME=3 };
static inline int dx_num_guard(int valid,const char *rule) {
  DX_NUM_CHECK(valid,rule); return valid;
}
static inline enum dx_num_status dx_num_refusal(enum dx_num_status status,const char *rule) {
  DX_NUM_REFUSE(rule); return status;
}
static inline int dx_num_float_runtime(const struct dx_num_runtime *runtime) {
  int valid=runtime && runtime->ieee_binary_rn==1 && FLT_RADIX==2 &&
    sizeof(float)==4 && sizeof(double)==8 && FLT_MANT_DIG==24 && DBL_MANT_DIG==53 &&
    FLT_MAX_EXP==128 && DBL_MAX_EXP==1024 && FLT_EVAL_METHOD==0 && fegetround()==FE_TONEAREST;
#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__>0)
  valid=0;
#endif
  return valid;
}
static inline enum dx_num_status dxv_eval_bits(unsigned dtype,unsigned op,uint64_t lhs,uint64_t rhs,
              unsigned family,const struct dx_num_runtime *runtime,uint64_t *out) {
  if (!out || family>1 || op>15 || (family==1 && op!=0 && op!=4 && op!=5))
    return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.type_or_opcode");
  switch(dtype) {
case 0: {
  uint32_t ua=(uint32_t)lhs,ub=(uint32_t)rhs;
  uint32_t a=ua,b=ub,z;
  switch(op) {
  case 0:
    z=(uint32_t)(a+b); break;
  case 1:
    z=(uint32_t)(a-b); break;
  case 2:
    z=(uint32_t)(a*b); break;
  case 3:
    if (!dx_num_guard(b!=0,"numeric.3.i0")) return DX_NUM_ARITHMETIC;
    z=(uint32_t)(a/b); break;
  case 4: z=a<b?a:b; break;
  case 5: z=a>b?a:b; break;
  case 6: *out=(uint32_t)(ua&ub); return DX_NUM_OK;
  case 7: *out=(uint32_t)(ua|ub); return DX_NUM_OK;
  case 8: *out=(uint32_t)(ua^ub); return DX_NUM_OK;
  case 9:
    if (!dx_num_guard(b<32,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=(uint32_t)(ua<<b); return DX_NUM_OK;
  case 10:
    if (!dx_num_guard(b<32,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=(uint32_t)(ua>>b); return DX_NUM_OK;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  *out=z; return DX_NUM_OK;
}
case 1: {
  uint32_t ua=(uint32_t)lhs,ub=(uint32_t)rhs;
  int32_t a,b,z;
  memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));
  switch(op) {
  case 0:
    if (!dx_num_guard(!((b>0 && a>INT32_MAX-b)||(b<0 && a<INT32_MIN-b)),"numeric.0.i32")) return DX_NUM_ARITHMETIC;
    z=(int32_t)(a+b); break;
  case 1:
    if (!dx_num_guard(!((b<0 && a>INT32_MAX+b)||(b>0 && a<INT32_MIN+b)),"numeric.1.i32")) return DX_NUM_ARITHMETIC;
    z=(int32_t)(a-b); break;
  case 2:
    if (!dx_num_guard((a==0 || b==0 || (a>0 ? (b>0 ? a<=INT32_MAX/b : b>=INT32_MIN/a) : (b>0 ? a>=INT32_MIN/b : a>=INT32_MAX/b))),"numeric.2.i32")) return DX_NUM_ARITHMETIC;
    z=(int32_t)(a*b); break;
  case 3:
    if (!dx_num_guard(b!=0 && !(a==INT32_MIN && b==-1),"numeric.3.i32")) return DX_NUM_ARITHMETIC;
    z=(int32_t)(a/b); break;
  case 4: z=a<b?a:b; break;
  case 5: z=a>b?a:b; break;
  case 6: *out=(uint32_t)(ua&ub); return DX_NUM_OK;
  case 7: *out=(uint32_t)(ua|ub); return DX_NUM_OK;
  case 8: *out=(uint32_t)(ua^ub); return DX_NUM_OK;
  case 9:
    if (!runtime || runtime->signed_shift_cpp17_arithmetic!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.signed_shift_runtime");
    if (!dx_num_guard(b>=0 && b<32,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    if (!dx_num_guard(a>=0 && ua<=(UINT32_MAX>>b),"numeric.signed_left")) return DX_NUM_ARITHMETIC;
    *out=(uint32_t)(ua<<b); return DX_NUM_OK;
  case 10:
    if (!runtime || runtime->signed_shift_cpp17_arithmetic!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.signed_shift_runtime");
    if (!dx_num_guard(b>=0 && b<32,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=b==0?ua:(uint32_t)((ua>>b)|(a<0?(uint32_t)(UINT32_MAX<<(32-b)):0)); return DX_NUM_OK;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;
}
case 3: {
  uint64_t ua=(uint64_t)lhs,ub=(uint64_t)rhs;
  uint64_t a=ua,b=ub,z;
  switch(op) {
  case 0:
    z=(uint64_t)(a+b); break;
  case 1:
    z=(uint64_t)(a-b); break;
  case 2:
    z=(uint64_t)(a*b); break;
  case 3:
    if (!dx_num_guard(b!=0,"numeric.3.i0")) return DX_NUM_ARITHMETIC;
    z=(uint64_t)(a/b); break;
  case 4: z=a<b?a:b; break;
  case 5: z=a>b?a:b; break;
  case 6: *out=(uint64_t)(ua&ub); return DX_NUM_OK;
  case 7: *out=(uint64_t)(ua|ub); return DX_NUM_OK;
  case 8: *out=(uint64_t)(ua^ub); return DX_NUM_OK;
  case 9:
    if (!dx_num_guard(b<64,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=(uint64_t)(ua<<b); return DX_NUM_OK;
  case 10:
    if (!dx_num_guard(b<64,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=(uint64_t)(ua>>b); return DX_NUM_OK;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  *out=z; return DX_NUM_OK;
}
case 4: {
  uint64_t ua=(uint64_t)lhs,ub=(uint64_t)rhs;
  int64_t a,b,z;
  memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));
  switch(op) {
  case 0:
    if (!dx_num_guard(!((b>0 && a>INT64_MAX-b)||(b<0 && a<INT64_MIN-b)),"numeric.0.i64")) return DX_NUM_ARITHMETIC;
    z=(int64_t)(a+b); break;
  case 1:
    if (!dx_num_guard(!((b<0 && a>INT64_MAX+b)||(b>0 && a<INT64_MIN+b)),"numeric.1.i64")) return DX_NUM_ARITHMETIC;
    z=(int64_t)(a-b); break;
  case 2:
    if (!dx_num_guard((a==0 || b==0 || (a>0 ? (b>0 ? a<=INT64_MAX/b : b>=INT64_MIN/a) : (b>0 ? a>=INT64_MIN/b : a>=INT64_MAX/b))),"numeric.2.i64")) return DX_NUM_ARITHMETIC;
    z=(int64_t)(a*b); break;
  case 3:
    if (!dx_num_guard(b!=0 && !(a==INT64_MIN && b==-1),"numeric.3.i64")) return DX_NUM_ARITHMETIC;
    z=(int64_t)(a/b); break;
  case 4: z=a<b?a:b; break;
  case 5: z=a>b?a:b; break;
  case 6: *out=(uint64_t)(ua&ub); return DX_NUM_OK;
  case 7: *out=(uint64_t)(ua|ub); return DX_NUM_OK;
  case 8: *out=(uint64_t)(ua^ub); return DX_NUM_OK;
  case 9:
    if (!runtime || runtime->signed_shift_cpp17_arithmetic!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.signed_shift_runtime");
    if (!dx_num_guard(b>=0 && b<64,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    if (!dx_num_guard(a>=0 && ua<=(UINT64_MAX>>b),"numeric.signed_left")) return DX_NUM_ARITHMETIC;
    *out=(uint64_t)(ua<<b); return DX_NUM_OK;
  case 10:
    if (!runtime || runtime->signed_shift_cpp17_arithmetic!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.signed_shift_runtime");
    if (!dx_num_guard(b>=0 && b<64,"numeric.shift_count")) return DX_NUM_ARITHMETIC;
    *out=b==0?ua:(uint64_t)((ua>>b)|(a<0?(uint64_t)(UINT64_MAX<<(64-b)):0)); return DX_NUM_OK;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;
}
case 2: {
  if (op>=6 && op<=10) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_opcode");
  if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");
  uint32_t ua=(uint32_t)lhs,ub=(uint32_t)rhs;
  float a,b,z; memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));
  switch(op) {
  case 0: z=a+b; break;
  case 1: z=a-b; break;
  case 2: z=a*b; break;
  case 3: z=a/b; break;
  case 4:
    if (family==0 && (isnan(a)||isnan(b)) && runtime->alu_minmax_unordered_first!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.alu_minmax_nan_runtime");
    z=family==1?(a<b?a:b):(b<a?b:a); break;
  case 5:
    if (family==0 && (isnan(a)||isnan(b)) && runtime->alu_minmax_unordered_first!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.alu_minmax_nan_runtime");
    z=family==1?(a>b?a:b):(a<b?b:a); break;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;
}
case 5: {
  if (op>=6 && op<=10) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_opcode");
  if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");
  uint64_t ua=(uint64_t)lhs,ub=(uint64_t)rhs;
  double a,b,z; memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));
  switch(op) {
  case 0: z=a+b; break;
  case 1: z=a-b; break;
  case 2: z=a*b; break;
  case 3: z=a/b; break;
  case 4:
    if (family==0 && (isnan(a)||isnan(b)) && runtime->alu_minmax_unordered_first!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.alu_minmax_nan_runtime");
    z=family==1?(a<b?a:b):(b<a?b:a); break;
  case 5:
    if (family==0 && (isnan(a)||isnan(b)) && runtime->alu_minmax_unordered_first!=1)
      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.alu_minmax_nan_runtime");
    z=family==1?(a>b?a:b):(a<b?b:a); break;
  case 11: *out=(uint32_t)(a>b); return DX_NUM_OK;
  case 12: *out=(uint32_t)(a>=b); return DX_NUM_OK;
  case 13: *out=(uint32_t)(a<b); return DX_NUM_OK;
  case 14: *out=(uint32_t)(a<=b); return DX_NUM_OK;
  case 15: *out=(uint32_t)(a==b); return DX_NUM_OK;
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");
  }
  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;
}
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.dtype");
  }
}
static inline enum dx_num_status dxv_initializer_bits(unsigned dtype,unsigned op,
              const struct dx_num_runtime *runtime,uint64_t *out) {
  if (!out || op>7) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.reduction_opcode");
  switch(dtype) {
  case 0:
    switch(op) {
    case 0: case 1: case 7: *out=0; break;
    case 2: case 3: *out=1; break;
    case 4: *out=UINT32_MAX; break;
    case 5: *out=0; break;
    case 6: *out=UINT32_MAX; break;
    } return DX_NUM_OK;
  case 1:
    switch(op) {
    case 0: case 1: case 7: *out=0; break;
    case 2: case 3: *out=1; break;
    case 4: *out=INT32_MAX; break;
    case 5: *out=(UINT32_C(1)<<31); break;
    case 6: *out=UINT32_MAX; break;
    } return DX_NUM_OK;
  case 3:
    switch(op) {
    case 0: case 1: case 7: *out=0; break;
    case 2: case 3: *out=1; break;
    case 4: *out=UINT64_MAX; break;
    case 5: *out=0; break;
    case 6: *out=UINT64_MAX; break;
    } return DX_NUM_OK;
  case 4:
    switch(op) {
    case 0: case 1: case 7: *out=0; break;
    case 2: case 3: *out=1; break;
    case 4: *out=INT64_MAX; break;
    case 5: *out=(UINT64_C(1)<<63); break;
    case 6: *out=UINT64_MAX; break;
    } return DX_NUM_OK;
  case 2: {
    if (op>5) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_reduction_opcode");
    if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");
    float z; uint32_t bits;
    switch(op) {
    case 0: case 1: z=0; break;
    case 2: case 3: z=1; break;
    case 4: z=FLT_MAX; break;
    default: z=FLT_MIN; break;
    } memcpy(&bits,&z,sizeof(z)); *out=bits; return DX_NUM_OK;
  }
  case 5: {
    if (op>5) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_reduction_opcode");
    if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");
    double z; uint64_t bits;
    switch(op) {
    case 0: case 1: z=0; break;
    case 2: case 3: z=1; break;
    case 4: z=DBL_MAX; break;
    default: z=DBL_MIN; break;
    } memcpy(&bits,&z,sizeof(z)); *out=bits; return DX_NUM_OK;
  }
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.dtype");
  }
}
static inline enum dx_num_status dxv_reduce_bits(unsigned dtype,unsigned op,
       const uint64_t *values,const uint32_t *active,size_t count,
       const struct dx_num_runtime *runtime,uint64_t *out) {
  if (!out || (count && !values)) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.reduction_storage");
  uint64_t acc,next; enum dx_num_status status=dxv_initializer_bits(dtype,op,runtime,&acc);
  if (status!=DX_NUM_OK) return status;
  for (size_t i=0;i<count;i++) if (!active || active[i]!=0) {
    status=dxv_eval_bits(dtype,op,values[i],acc,0,runtime,&next);
    if (status!=DX_NUM_OK) return status;
    acc=next;
  }
  *out=acc; return DX_NUM_OK;
}
/* Source-faithful ordinary-array domain: reject uint32 intermediate wrap first.
   Object validity, address-space/line correspondence and Addr addition remain caller obligations. */
static inline enum dx_num_status dxv_indirect_offset_bits(unsigned word_size,uint32_t index,uint64_t *out) {
  if (!out || (word_size!=4 && word_size!=8))
    return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.word_size");
  if (!dx_num_guard(index<=UINT32_MAX/word_size,"numeric.indirect_offset_wrap")) return DX_NUM_ARITHMETIC;
  *out=(uint64_t)word_size*index; return DX_NUM_OK;
}
#endif

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

/* Structural source domains hold even when a condition disables evaluation.
   Arithmetic domains are checked only for the selected active expression. */
static unsigned dxt_binary(unsigned thread,unsigned dtype,unsigned op,unsigned lhs,unsigned rhs) {
  DXM_CHECK(dtype < 6,"numeric-type-domain");
  DXM_CHECK(op <= 15 && !((dtype == 2 || dtype == 5) && op >= 6 && op <= 10),"numeric-opcode-domain");
  return dxm_issue_binary(thread,dtype,op,lhs,rhs);
}

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
  DXM_CHECK(preserved < old_result, "acyclic-producer-version");
  unsigned root=dxa_store(command,dtype,base,extent,index,value,active);
  struct dxa_action *a=&dxa_actions[dxa_count-1];
  a->kind=1; a->op=op; a->old_result=old_result; a->preserved=preserved;
  return root;
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
        dxm_publish_alias(a->old_result,a->preserved);
      }
      a->done=1;
  }
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

#ifndef SWDB_DX_REGISTER_STATE_H
#define SWDB_DX_REGISTER_STATE_H
#ifdef __cplusplus
#define DXG_ALIGN(T) alignof(T)
#define DXG_ABI(c) static_assert(c,"register source ABI")
#else
#define DXG_ALIGN(T) _Alignof(T)
#define DXG_ABI(c) _Static_assert(c,"register source ABI")
#endif
DXG_ABI(DXG_ALIGN(uint32_t) == 4);
DXG_ABI(DXG_ALIGN(int32_t) == 4);
DXG_ABI(DXG_ALIGN(float) == 4);
DXG_ABI(DXG_ALIGN(uint64_t) == 8);
DXG_ABI(DXG_ALIGN(int64_t) == 8);
DXG_ABI(DXG_ALIGN(double) == 8);
static const unsigned dxg_alignment[6]={4,4,4,8,8,8};

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
static uint32_t dxp_load_u32(unsigned thread,unsigned tile,unsigned lane) {
  uint32_t bits=(uint32_t)dxp_cpu_read_bits(thread,tile,lane,0);
  uint32_t value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_u32(unsigned thread,unsigned tile,unsigned lane,uint32_t value) {
  uint32_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,0,bits);
}
static int32_t dxp_load_i32(unsigned thread,unsigned tile,unsigned lane) {
  uint32_t bits=(uint32_t)dxp_cpu_read_bits(thread,tile,lane,1);
  int32_t value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_i32(unsigned thread,unsigned tile,unsigned lane,int32_t value) {
  uint32_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,1,bits);
}
static float dxp_load_f32(unsigned thread,unsigned tile,unsigned lane) {
  uint32_t bits=(uint32_t)dxp_cpu_read_bits(thread,tile,lane,2);
  float value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_f32(unsigned thread,unsigned tile,unsigned lane,float value) {
  uint32_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,2,bits);
}
static uint64_t dxp_load_u64(unsigned thread,unsigned tile,unsigned lane) {
  uint64_t bits=(uint64_t)dxp_cpu_read_bits(thread,tile,lane,3);
  uint64_t value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_u64(unsigned thread,unsigned tile,unsigned lane,uint64_t value) {
  uint64_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,3,bits);
}
static int64_t dxp_load_i64(unsigned thread,unsigned tile,unsigned lane) {
  uint64_t bits=(uint64_t)dxp_cpu_read_bits(thread,tile,lane,4);
  int64_t value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_i64(unsigned thread,unsigned tile,unsigned lane,int64_t value) {
  uint64_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,4,bits);
}
static double dxp_load_f64(unsigned thread,unsigned tile,unsigned lane) {
  uint64_t bits=(uint64_t)dxp_cpu_read_bits(thread,tile,lane,5);
  double value; memcpy(&value,&bits,sizeof(value)); return value;
}
static void dxp_store_f64(unsigned thread,unsigned tile,unsigned lane,double value) {
  uint64_t bits=0; memcpy(&bits,&value,sizeof(value));
  dxp_cpu_write_bits(thread,tile,lane,5,bits);
}
#endif

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

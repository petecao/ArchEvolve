/* Checked-body hooks: preserve every ordinary property. */
#include <stdint.h>
#include <stddef.h>
#ifndef SWDB_CHECK
#error "public checked-property hooks must precede model assembly"
#endif
static uint32_t dws_choice_table[128];
static unsigned dws_choice_used;
static unsigned dws_model_choose(unsigned alternatives) {
  SWDB_CHECK(alternatives>0 && alternatives<=256,"whole-choice-domain");
  SWDB_CHECK(dws_choice_used<128u,"whole-choice-capacity");
  return dws_choice_table[dws_choice_used++] % alternatives;
}
#define DXM_CHECK(condition,rule) SWDB_CHECK((condition),rule)
#define DXM_CHOOSE(alternatives) dws_model_choose(alternatives)

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
  const char *guard_rule;
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
    if (n->kind == 11 && phase[frame] < 2) {
      if (phase[frame] == 0) parent=n->left;
      else {DXM_CHECK(dxm_nodes[n->left].value,n->guard_rule);parent=n->right;}
      ++phase[frame];visit=1;
    } else if ((n->kind == 2 || n->kind == 5) && phase[frame] < 2) {
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
      } else if (n->kind == 11) {
        n->value=dxm_nodes[n->right].value;
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
        if (a->kind == 1 || a->kind == 2) {
          DXM_CHECK(dxm_initialized[cell], "read-initialized");
          uint64_t old=dxm_memory[cell];
          if (a->dtype < 3) old &= UINT32_MAX;
          if(a->kind == 1) value=dxt_evaluate_family(a->dtype,a->op,old,value,1);
          dxm_publish(a->old_result,old);
        }
        dxm_device_write(cell,value);
      } else if (a->kind == 1 || a->kind == 2) {
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

/*2026-10-16 ET. PRIVATE preparation adapters, no public admission.
 * Include after the frozen backend. Never hand candidate code access to these
 * entry points or to a value-builder callback. Owned source/MMIO/ABI premises,
 * source replay and checked per-call value recipes are mandatory integration.
 */
#ifndef SWDB_DX_WHOLE_INTERFACE_PREPARATION_H
#define SWDB_DX_WHOLE_INTERFACE_PREPARATION_H
struct dwi_packet { int src1,src2,dst1,dst2,rdst1,rdst2,rsrc1,rsrc2,rsrc3,condition; };
struct dwi_footprint {
  uint64_t source_base,logical_begin,logical_end,physical_begin,physical_end,line_bytes;
};
struct dwi_roles {
  uint64_t er,ew,pr,pw,ready,re, we,rp,wp;
  unsigned tile_width[64],register_width[64];
};
static void dwi_add_tile(struct dwi_roles *r,int id,unsigned bytes,unsigned write,unsigned counted) {
  if(id==-1) return;
  DXM_CHECK(id>=0,"tile-domain");
  uint64_t mask=dxc_tile_mask((unsigned)id,bytes);
  DXM_CHECK(!r->tile_width[id] || r->tile_width[id]==bytes,"source-role-width-conflict");
  r->tile_width[id]=bytes;
  if(write) {r->ew|=UINT64_C(1)<<id;r->pw|=mask;}
  else {r->er|=UINT64_C(1)<<id;r->pr|=mask;}
  if(counted) r->ready|=mask;
}
static void dwi_add_register(struct dwi_roles *r,unsigned thread,int id,unsigned dtype,unsigned write,unsigned read) {
  if(id==-1) return;
  DXM_CHECK(id>=0,"register-pair-domain");
  dxg_use(thread,(unsigned)id,dtype);
  unsigned bytes=dxg_width(dtype);uint64_t mask=dxg_mask((unsigned)id,dtype);
  DXM_CHECK(!r->register_width[id] || r->register_width[id]==bytes,"source-register-width-conflict");
  r->register_width[id]=bytes;
  if(write) {r->we|=UINT64_C(1)<<id;r->wp|=mask;}
  if(read) {r->re|=UINT64_C(1)<<id;r->rp|=mask;}
}
static void dwi_operation(unsigned opcode,unsigned dtype,unsigned op) {
  DXM_CHECK(opcode<=10 && dtype<6,"source-type-opcode-domain");
  if(opcode==5 || opcode==6) DXM_CHECK(op==0 || op==4 || op==5,"numeric-rmw-opcode-domain");
  else if(opcode==10) DXM_CHECK(op<=(dtype==2 || dtype==5 ? 5u:7u),"numeric-reduction-opcode-domain");
  else if(opcode==8 || opcode==9) DXM_CHECK(op<=15,"numeric-opcode-domain");
  else DXM_CHECK(op==255,"source-unused-opcode");
  DXM_CHECK(!(dtype==2 || dtype==5) || !(6<=op && op<=10),"numeric-float-opcode-domain");
}
static unsigned dwi_prepare_packet(unsigned thread,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *f) {
  DXM_CHECK(p!=0,"source-packet-domain");
  if(opcode==7) dtype=1;
  dwi_operation(opcode,dtype,op);
  unsigned bytes=dxp_width(dtype), source1=bytes,source2=bytes,destination=bytes;
  if(opcode>=2 && opcode<=7) source1=4;
  if(opcode==7) source2=destination=4;
  if((opcode==8 || opcode==9) && op>=11) destination=4;
  struct dwi_roles r={0};
  dwi_add_tile(&r,p->src1,source1,0,1);dwi_add_tile(&r,p->src2,source2,0,1);
  dwi_add_tile(&r,p->dst1,destination,1,1);dwi_add_tile(&r,p->dst2,destination,1,1);
  dwi_add_tile(&r,p->condition,4,0,0);
  unsigned rdtype=(opcode==0 || opcode==1 || opcode==7)?1:dtype;
  dwi_add_register(&r,thread,p->rsrc1,rdtype,0,1);
  dwi_add_register(&r,thread,p->rsrc2,rdtype,0,1);
  dwi_add_register(&r,thread,p->rsrc3,rdtype,0,1);
  dwi_add_register(&r,thread,p->rdst1,rdtype,1,opcode==7);
  dwi_add_register(&r,thread,p->rdst2,rdtype,1,opcode==7);
  unsigned access=opcode==0 || opcode==2 ? 1 : opcode<=6 ? 2:0;
  int region=-1;uint64_t begin=0,end=0;
  if(access) {
    DXM_CHECK(f && f->logical_begin<f->logical_end && f->physical_begin<f->physical_end,"nonempty-source-footprint");
    region=dxr_assign(f->source_base);dxr_check_span(region,f->logical_begin,f->logical_end);
    begin=f->physical_begin;end=f->physical_end;
    if(access==2) {struct dxc_span span=dxc_store_span(begin,end-begin,f->line_bytes);begin=span.begin;end=span.end;}
  } else DXM_CHECK(f==0,"compute-memory-footprint");
  unsigned command=dxc_prepare_counted(thread,region,access,r.er,r.ew,r.pr,r.pw,begin,end,r.ready);
  dxg_bind_roles(command,r.re,r.we,r.rp,r.wp);
  return command;
}
/* A source-owned builder captures IMMUTABLE input/size versions, installs
 * deferred typed outputs/actions, and returns one root covering every active
 * effect. It may not invoke a CPU/source action, settle history or add premises.
 * This seam alone is not a completed value model or public support certificate.
 */
typedef unsigned (*dwi_value_builder)(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *,const struct dwi_footprint *,void *context);
static unsigned dwi_atomic_packet(unsigned thread,unsigned opcode,unsigned dtype,unsigned op,
    struct dwi_packet packet,const struct dwi_footprint *footprint,dwi_value_builder build,void *context) {
  DXM_CHECK(build!=0,"source-bound-value-builder-required");
  unsigned command=dwi_prepare_packet(thread,opcode,dtype,op,&packet,footprint);
  unsigned root=build(command,opcode,opcode==7?1:dtype,op,&packet,footprint,context);
  DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");
  dxc_bind(command,root);
  return command;
}
static void dwi_alloc_MAA(void) {dxs_alloc();}
static void dwi_init_MAA(void) {dxs_init();}
static void dwi_add_mem_region(uint64_t begin,uint64_t end) {dxs_add_region(begin,end);}
static void dwi_clear_mem_region(void) {dxs_clear_regions();}
static void dwi_wait_ready(unsigned tile) {dxc_wait_tile(tile);}
static uint16_t dwi_get_tile_size(unsigned tile) {return dxz_get_size(tile);}
static unsigned dwi_get_data_type(unsigned actual_type_identity) {
  DXM_CHECK(actual_type_identity<=6,"source-type-identity-domain");return actual_type_identity;
}
static unsigned dwi_get_new_tile(unsigned thread,unsigned dtype) {return dxs_new_tile(thread,dtype);}
static unsigned dwi_get_new_reg(unsigned thread,unsigned dtype) {return dxg_new(thread,dtype);}
static unsigned dwi_get_new_reg_initialized(unsigned thread,unsigned dtype,uint64_t value) {return dxg_new_initialized(thread,dtype,value);}
static uint64_t dwi_get_reg(unsigned thread,unsigned dtype,unsigned reg) {return dxg_cpu_read_bits(thread,reg,dtype);}
static void dwi_set_reg(unsigned thread,unsigned dtype,unsigned reg,uint64_t value) {dxg_cpu_write_bits(thread,reg,dtype,value);}
static void dwi_maa_const(unsigned thread,unsigned dtype,uint64_t value,unsigned reg) {dxg_cpu_write_bits(thread,reg,dtype,value);}
/* Address identity only. Never cast this modeled address to a host pointer or
 * infer that the noncacheable range supports the same CPU dereference policy.
 */
static uint64_t dwi_tile_address(unsigned dtype,unsigned tile,unsigned noncacheable) {
  DXM_CHECK(!dxc_constructing && dxs_allocated && noncacheable<=1,"mmio-setup-domain");
  dxm_tile_halves(tile,dxp_width(dtype));
  DXM_CHECK(tile<=INT_MAX/DXP_TILE_WORDS,"tile-source-index-domain");
  return dxs_mmio[noncacheable]+(uint64_t)(tile*DXP_TILE_WORDS)*4;
}
static uint64_t dwi_get_cacheable_tile_pointer(unsigned dtype,unsigned tile) {return dwi_tile_address(dtype,tile,0);}
static uint64_t dwi_get_noncacheable_tile_pointer(unsigned dtype,unsigned tile) {return dwi_tile_address(dtype,tile,1);}
typedef void (*dwi_print_observer)(unsigned tile,unsigned lane,unsigned dtype,uint64_t bits,void *context);
static void dwi_print_tile(unsigned thread,unsigned dtype,unsigned tile,dwi_print_observer observe,void *context) {
  DXM_CHECK(observe!=0,"source-owned-io-projection-required");
  uint16_t size=dxz_get_size(tile);
  DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");
  for(unsigned lane=0;lane<size;++lane) observe(tile,lane,dtype,dxp_cpu_read_bits(thread,tile,lane,dtype),context);
}

/* MAA_gem5.hpp:175-192; exact packed operand map. */
static unsigned dwi_maa_alu_scalar(unsigned thread, unsigned dtype, int src1_tile, int src2_reg, int dst_tile, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src2_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={src1_tile,-1,dst_tile,-1,-1,-1,src2_reg,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,8,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:194-211; exact packed operand map. */
static unsigned dwi_maa_alu_vector(unsigned thread, unsigned dtype, int src1_tile, int src2_tile, int dst_tile, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src2_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={src1_tile,src2_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,9,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:213-230; exact packed operand map. */
static unsigned dwi_maa_alu_reduce(unsigned thread, unsigned dtype, int src1_tile, int dst_reg, int op, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(dst_reg>=0,"source-rdst1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  struct dwi_packet packet={src1_tile,-1,-1,-1,dst_reg,-1,-1,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,10,dtype,op,packet,footprint,build,context);
}
/* MAA_gem5.hpp:232-249; exact packed operand map. */
static unsigned dwi_maa_stream_load(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={-1,-1,dst_tile,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,0,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:251-268; exact packed operand map. */
static unsigned dwi_maa_stream_store(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int src_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(src_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  struct dwi_packet packet={src_tile,-1,-1,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,1,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:270-287; exact packed operand map. */
static unsigned dwi_maa_indirect_load(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,2,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:289-306; exact packed operand map. */
static unsigned dwi_maa_indirect_store_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,4,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:308-325; exact packed operand map. */
static unsigned dwi_maa_indirect_store_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,3,dtype,255,packet,footprint,build,context);
}
/* MAA_gem5.hpp:327-344; exact packed operand map. */
static unsigned dwi_maa_indirect_rmw_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,6,dtype,o_type,packet,footprint,build,context);
}
/* MAA_gem5.hpp:346-363; exact packed operand map. */
static unsigned dwi_maa_indirect_rmw_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");
  struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};
  DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");
  return dwi_atomic_packet(thread,5,dtype,o_type,packet,footprint,build,context);
}
/* MAA_gem5.hpp:366-383; exact packed operand map. */
static unsigned dwi_maa_range_loop(unsigned thread, unsigned dtype, int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile, const struct dwi_footprint *footprint, dwi_value_builder build, void *context) {
  DXM_CHECK(min_tile>=0,"source-src1-operand-domain");
  DXM_CHECK(max_tile>=0,"source-src2-operand-domain");
  DXM_CHECK(last_i_reg>=0,"source-rdst1-operand-domain");
  DXM_CHECK(last_j_reg>=0,"source-rdst2-operand-domain");
  DXM_CHECK(stride_reg>=0,"source-rsrc1-operand-domain");
  DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");
  DXM_CHECK(dst_i_tile>=0,"source-dst1-operand-domain");
  DXM_CHECK(dst_j_tile>=0,"source-dst2-operand-domain");
  struct dwi_packet packet={min_tile,max_tile,dst_i_tile,dst_j_tile,last_i_reg,last_j_reg,stride_reg,-1,-1,cond_tile};
  return dwi_atomic_packet(thread,7,dtype,255,packet,footprint,build,context);
}
#endif

/*2026-10-16 ET. PRIVATE typed deferred family builders.
 * Include extended whole backend and exact source packet adapters first.
 * Source/MMIO effects are owned premises. No source/pointer/ABI admission is
 * granted by calling these private functions. Candidate callbacks are forbidden.
 */
#ifndef SWDB_DX_WHOLE_VALUE_BUILDERS_H
#define SWDB_DX_WHOLE_VALUE_BUILDERS_H
static unsigned dxw_require(unsigned predicate,unsigned value,const char *rule) {
  DXM_CHECK(predicate<dxm_count && value<dxm_count && rule,"producer-version-domain");
  DXM_CHECK(dxm_count<DXM_NODES,"node-capacity");
  unsigned id=dxm_count++;struct dxm_node *n=&dxm_nodes[id];
  n->kind=11;n->left=predicate;n->right=value;n->guard_rule=rule;n->settled=0;
  return id;
}
static unsigned dxw_cmp(unsigned thread,unsigned op,unsigned left,unsigned right) {
  return dxt_binary(thread,0,op,left,right);
}
static unsigned dxw_bound_size(unsigned thread,unsigned size) {
  return dxw_require(dxw_cmp(thread,14,size,dxm_constant(DXP_VALUE_BOUND)),size,"value-prefix-capacity");
}
static unsigned dxw_same_size(unsigned thread,unsigned size,unsigned other) {
  return dxw_require(dxw_cmp(thread,15,size,other),size,"source-size-agreement");
}
static unsigned dxw_active(unsigned thread,unsigned size,int condition,unsigned lane) {
  unsigned inside=dxw_cmp(thread,13,dxm_constant(lane),size);
  if(condition<0) return inside;
  /* Outside the source size, do not observe even a condition's initializedness. */
  return dxm_select(thread,inside,dxp_capture_bits((unsigned)condition,lane,0),dxm_constant(0));
}
static unsigned dxw_work_root(unsigned thread,unsigned active,unsigned value) {
  return dxm_select(thread,active,value,dxm_constant(0));
}
static unsigned dxw_alu(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *unused) {
  (void)unused;DXM_CHECK(!footprint && opcode>=8 && opcode<=10,"alu-family-binding");
  unsigned thread=dxc_commands[command].thread;
  unsigned size=dxz_capture_size((unsigned)p->src1);
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  if(opcode==9) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->src2));
  size=dxw_bound_size(thread,size);
  unsigned root=size,scalar=UINT_MAX,acc=UINT_MAX;
  if(opcode==8) scalar=dxg_capture_bits((unsigned)p->rsrc1,dtype);
  if(opcode==10) {
    uint64_t bits=0;enum dx_num_status status=dxv_initializer_bits(dtype,op,&dxt_runtime,&bits);
    DXM_CHECK(status==DX_NUM_OK,"source-reduction-initializer-domain");acc=dxm_constant(bits);
  }
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned left=dxp_capture_bits((unsigned)p->src1,lane,dtype);
    unsigned right=opcode==8?scalar:opcode==9?dxp_capture_bits((unsigned)p->src2,lane,dtype):acc;
    /* ALU.cc folds src OP accumulator, including SUB and DIV. */
    unsigned value=dxt_binary(thread,dtype,op,left,right);
    if(opcode==10) acc=dxm_select(thread,active,value,acc);
    else {
      unsigned output_dtype=op>=11?0:dtype;
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,output_dtype,active,value);
      root=dxm_join(root,dxw_work_root(thread,active,value));
    }
  }
  if(opcode==10) {dxg_bind_output(command,(unsigned)p->rdst1,dtype,acc);root=dxm_join(root,acc);}
  else dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}

/* This describes an already established typed ordinary-array mapping. An actual
 * compiler/source access certificate must justify C object, guest addresses,
 * physical envelopes, cell identity, endianness and alias consistency together.
 */
struct dxw_memory {unsigned base_cell,extent;uint64_t source_base;unsigned source_page_bytes;};
static void dxw_memory_domain(unsigned dtype,const struct dwi_footprint *f,const struct dxw_memory *m) {
  DXM_CHECK(f && m && m->base_cell<DXM_CELLS && m->extent>0 && m->extent<=DXM_CELLS-m->base_cell,"cell-domain");
  unsigned bytes=dxp_width(dtype);
  DXM_CHECK(m->source_base==f->source_base,"source-address-binding");
  DXM_CHECK(m->extent-1<=UINT32_MAX/bytes,"numeric-indirect-offset-wrap");
  uint64_t span=(uint64_t)m->extent*bytes;
  DXM_CHECK(m->source_base<=UINT64_MAX-span,"source-address-overflow");
  DXM_CHECK(f->logical_begin<=m->source_base && m->source_base+span<=f->logical_end,"logical-object-envelope");
}
static unsigned dxw_store_old(unsigned command,unsigned dtype,unsigned base,unsigned extent,
    unsigned index,unsigned value,unsigned active,unsigned result,unsigned preserved) {
  DXM_CHECK(result<dxm_count && dxm_nodes[result].kind==6 && !dxm_nodes[result].settled,"action-result-domain");
  DXM_CHECK(preserved<result,"acyclic-producer-version");
  unsigned root=dxa_store(command,dtype,base,extent,index,value,active);
  struct dxa_action *a=&dxa_actions[dxa_count-1];
  a->kind=2;a->old_result=result;a->preserved=preserved;return root;
}
static unsigned dxw_indirect(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *context) {
  DXM_CHECK(opcode>=2 && opcode<=6,"indirect-family-binding");
  const struct dxw_memory *m=(const struct dxw_memory *)context;
  dxw_memory_domain(dtype,footprint,m);
  unsigned thread=dxc_commands[command].thread;
  unsigned size=dxz_capture_size((unsigned)p->src1);
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  size=dxw_bound_size(thread,size);
  unsigned root=size,scalar=UINT_MAX;
  if(opcode==3 || opcode==5) scalar=dxg_capture_bits((unsigned)p->rsrc1,dtype);
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned index=dxp_capture_bits((unsigned)p->src1,lane,0);
    if(opcode==2) {
      unsigned read=dxm_issue_indexed_read(thread,index,m->base_cell,m->extent);
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,dtype,active,read);
      root=dxm_join(root,dxw_work_root(thread,active,read));
    } else {
      unsigned value=opcode==3 || opcode==5?scalar:dxp_capture_bits((unsigned)p->src2,lane,dtype);
      unsigned action;
      if(opcode==5 || opcode==6 || p->dst1>=0) {
        unsigned preserved=p->dst1>=0?dxp_capture_bits((unsigned)p->dst1,lane,dtype):dxm_constant(0);
        unsigned old=dxm_result();
        if(opcode==5 || opcode==6) action=dxa_rmw(command,dtype,op,m->base_cell,m->extent,index,value,active,old,preserved);
        else action=dxw_store_old(command,dtype,m->base_cell,m->extent,index,value,active,old,preserved);
        if(p->dst1>=0) dxp_bind_output(command,(unsigned)p->dst1,lane,dtype,old);
      } else action=dxa_store(command,dtype,m->base_cell,m->extent,index,value,active);
      root=dxm_join(root,action);
    }
  }
  if(p->dst1>=0) dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}
static unsigned dxw_stream(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *context) {
  DXM_CHECK(opcode<=1 && op==255,"stream-family-binding");
  const struct dxw_memory *m=(const struct dxw_memory *)context;
  dxw_memory_domain(dtype,footprint,m);
  unsigned thread=dxc_commands[command].thread,bytes=dxp_width(dtype);
  DXM_CHECK(m->source_page_bytes>=bytes && m->source_page_bytes%bytes==0
            && m->source_page_bytes/bytes<INT_MAX,"source-page-geometry-domain");
  unsigned zero=dxm_constant(0),one=dxm_constant(1);
  unsigned min=dxg_capture_bits((unsigned)p->rsrc1,1);
  unsigned max=dxg_capture_bits((unsigned)p->rsrc2,1);
  unsigned stride=dxg_capture_bits((unsigned)p->rsrc3,1);
  min=dxw_require(dxt_binary(thread,1,12,min,zero),min,"stream-nonnegative-min");
  stride=dxw_require(dxt_binary(thread,1,11,stride,zero),stride,"stream-positive-stride");
  max=dxw_require(dxt_binary(thread,1,11,max,min),max,"stream-nonempty-range");
  /* Preserve source signed multiplication, page-loop increment and final
   * stride increment domains. These checked restrictions are not assumptions. */
  max=dxw_require(dxt_binary(thread,1,14,max,dxm_constant(INT_MAX/bytes)),max,"stream-byte-offset-domain");
  max=dxw_require(dxt_binary(thread,1,14,max,dxm_constant(INT_MAX-m->source_page_bytes/bytes)),max,"stream-page-increment-domain");
  unsigned stride_limit=dxt_binary(thread,1,1,dxm_constant(INT_MAX),stride);
  max=dxw_require(dxt_binary(thread,1,14,max,stride_limit),max,"stream-stride-increment-domain");
  unsigned difference=dxt_binary(thread,1,1,max,min);
  unsigned minus_one=dxt_binary(thread,1,1,difference,one);
  unsigned quotient=dxt_binary(thread,1,3,minus_one,stride);
  unsigned size=dxt_binary(thread,1,4,dxt_binary(thread,1,0,quotient,one),dxm_constant(DXP_TILE_WORDS));
  size=dxw_bound_size(thread,size);
  unsigned root=size;
  for(unsigned lane=0;lane<DXP_VALUE_BOUND;++lane) {
    unsigned active=dxw_active(thread,size,p->condition,lane);
    unsigned index=dxt_binary(thread,1,0,min,dxt_binary(thread,1,2,dxm_constant(lane),stride));
    if(opcode==0) {
      unsigned read=dxm_issue_indexed_read(thread,index,m->base_cell,m->extent);
      dxp_bind_conditional_output(command,(unsigned)p->dst1,lane,dtype,active,read);
      root=dxm_join(root,dxw_work_root(thread,active,read));
    } else {
      unsigned value=dxp_capture_bits((unsigned)p->src1,lane,dtype);
      unsigned action=dxa_store(command,dtype,m->base_cell,m->extent,index,value,active);
      root=dxm_join(root,action);
    }
  }
  if(opcode==0) dxz_bind_size(command,(unsigned)p->dst1,size);
  return root;
}
static unsigned dxw_range(unsigned command,unsigned opcode,unsigned dtype,unsigned op,
    const struct dwi_packet *p,const struct dwi_footprint *footprint,void *unused) {
  (void)unused;
  DXM_CHECK(opcode==7 && dtype==1 && op==255 && !footprint,"range-family-binding");
  /* This slice accepts a call only when its complete output fits the private
   * prefix, strictly below source capacity. Thus it reaches the end of its
   * input rows; source mid-row capacity continuation is a checked refusal. */
  DXM_CHECK(DXP_VALUE_BOUND<DXP_TILE_WORDS,"range-source-capacity-profile");
  unsigned thread=dxc_commands[command].thread,zero=dxm_constant(0),one=dxm_constant(1);
  unsigned size=dxz_capture_size((unsigned)p->src1);
  size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->src2));
  if(p->condition>=0) size=dxw_same_size(thread,size,dxz_capture_size((unsigned)p->condition));
  size=dxw_bound_size(thread,size);
  unsigned initial_i=dxg_capture_bits((unsigned)p->rdst1,1);
  unsigned initial_j=dxg_capture_bits((unsigned)p->rdst2,1);
  unsigned stride=dxg_capture_bits((unsigned)p->rsrc1,1);
  initial_i=dxw_require(dxt_binary(thread,1,12,initial_i,zero),initial_i,"range-nonnegative-row");
  initial_j=dxw_require(dxt_binary(thread,1,12,initial_j,dxm_constant(UINT32_MAX)),initial_j,"range-continuation-domain");
  stride=dxw_require(dxt_binary(thread,1,11,stride,zero),stride,"range-positive-stride");
  unsigned root=dxm_join(size,dxm_join(initial_i,dxm_join(initial_j,stride)));
  unsigned last_j=initial_j,total=zero;
  for(unsigned row=0;row<DXP_VALUE_BOUND;++row) {
    unsigned eligible=dxw_cmp(thread,12,dxm_constant(row),initial_i);
    unsigned active=dxm_select(thread,eligible,dxw_active(thread,size,p->condition,row),zero);
    unsigned min=dxp_capture_bits((unsigned)p->src1,row,0);
    unsigned max=dxp_capture_bits((unsigned)p->src2,row,0);
    min=dxw_require(dxw_cmp(thread,14,min,dxm_constant(INT_MAX)),min,"range-signed-min-conversion");
    max=dxw_require(dxw_cmp(thread,14,max,dxm_constant(INT_MAX)),max,"range-signed-max-domain");
    unsigned start=dxm_select(thread,dxw_cmp(thread,15,last_j,dxm_constant(UINT32_MAX)),min,last_j);
    unsigned less=dxt_binary(thread,1,13,start,max);
    unsigned difference=dxt_binary(thread,1,1,max,start);
    unsigned count=dxt_binary(thread,1,0,dxt_binary(thread,1,3,dxt_binary(thread,1,1,difference,one),stride),one);
    count=dxm_select(thread,less,count,zero);
    /* RangeFuser.cc:211 increments signed my_last_j even after the last
     * emitted item; retain that source overflow obligation at cover. */
    unsigned after=dxt_binary(thread,3,0,start,dxt_binary(thread,3,2,count,stride));
    count=dxw_require(dxt_binary(thread,3,14,after,dxm_constant(INT_MAX)),count,"range-stride-increment-domain");
    unsigned row_checks=dxm_join(min,dxm_join(max,count));
    root=dxm_join(root,dxw_work_root(thread,active,row_checks));
    count=dxm_select(thread,active,count,zero);
    unsigned previous=total;
    total=dxw_bound_size(thread,dxt_binary(thread,0,0,previous,count));
    root=dxm_join(root,total);
    for(unsigned slot=0;slot<DXP_VALUE_BOUND;++slot) {
      unsigned at=dxm_constant(slot);
      unsigned belongs=dxm_select(thread,dxw_cmp(thread,12,at,previous),dxw_cmp(thread,13,at,total),zero);
      unsigned offset=dxt_binary(thread,0,1,at,previous);
      unsigned j=dxt_binary(thread,1,0,start,dxt_binary(thread,1,2,offset,stride));
      dxp_bind_conditional_output(command,(unsigned)p->dst1,slot,1,belongs,dxm_constant(row));
      dxp_bind_conditional_output(command,(unsigned)p->dst2,slot,1,belongs,j);
      root=dxm_join(root,dxw_work_root(thread,belongs,j));
    }
    last_j=dxm_select(thread,active,dxm_constant(UINT32_MAX),last_j);
  }
  unsigned last_i=dxm_select(thread,dxw_cmp(thread,13,initial_i,size),size,initial_i);
  dxg_bind_output(command,(unsigned)p->rdst1,1,last_i);
  dxg_bind_output(command,(unsigned)p->rdst2,1,last_j);
  dxz_bind_size(command,(unsigned)p->dst1,total);dxz_bind_size(command,(unsigned)p->dst2,total);
  return dxm_join(root,dxm_join(last_i,last_j));
}
#endif

/*2026-10-16 ET. Closed private routes; source/ABI/access admission required. */
#ifndef SWDB_DX_WHOLE_CLOSED_VALUE_ROUTES_H
#define SWDB_DX_WHOLE_CLOSED_VALUE_ROUTES_H
static unsigned dxw_call_maa_alu_scalar(unsigned thread, unsigned dtype, int src1_tile, int src2_reg, int dst_tile, int op, int cond_tile) {
  return dwi_maa_alu_scalar(thread, dtype, src1_tile, src2_reg, dst_tile, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_alu_vector(unsigned thread, unsigned dtype, int src1_tile, int src2_tile, int dst_tile, int op, int cond_tile) {
  return dwi_maa_alu_vector(thread, dtype, src1_tile, src2_tile, dst_tile, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_alu_reduce(unsigned thread, unsigned dtype, int src1_tile, int dst_reg, int op, int cond_tile) {
  return dwi_maa_alu_reduce(thread, dtype, src1_tile, dst_reg, op, cond_tile, 0, dxw_alu, 0);
}
static unsigned dxw_call_maa_stream_load(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_stream_load(thread, dtype, data, min_reg, max_reg, stride_reg, dst_tile, cond_tile, footprint, dxw_stream, (void *)mapping);
}
static unsigned dxw_call_maa_stream_store(unsigned thread, unsigned dtype, uint64_t data, int min_reg, int max_reg, int stride_reg, int src_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_stream_store(thread, dtype, data, min_reg, max_reg, stride_reg, src_tile, cond_tile, footprint, dxw_stream, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_load(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int dst_tile, int cond_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_load(thread, dtype, data, idx_tile, dst_tile, cond_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_store_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_store_vector(thread, dtype, data, idx_tile, src_tile, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_store_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_store_scalar(thread, dtype, data, idx_tile, src_reg, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_rmw_vector(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_tile, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_rmw_vector(thread, dtype, data, idx_tile, src_tile, o_type, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_indirect_rmw_scalar(unsigned thread, unsigned dtype, uint64_t data, int idx_tile, int src_reg, int o_type, int cond_tile, int dst_tile, const struct dwi_footprint *footprint, const struct dxw_memory *mapping) {
  return dwi_maa_indirect_rmw_scalar(thread, dtype, data, idx_tile, src_reg, o_type, cond_tile, dst_tile, footprint, dxw_indirect, (void *)mapping);
}
static unsigned dxw_call_maa_range_loop(unsigned thread, unsigned dtype, int last_i_reg, int last_j_reg, int min_tile, int max_tile, int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile) {
  return dwi_maa_range_loop(thread, dtype, last_i_reg, last_j_reg, min_tile, max_tile, stride_reg, dst_i_tile, dst_j_tile, cond_tile, 0, dxw_range, 0);
}
#endif

/*2026-10-16 ET. PRIVATE direct family specializations, no callback ABI. */
#ifndef SWDB_DX_SOURCE_DIRECT_FAMILIES_V1_H
#define SWDB_DX_SOURCE_DIRECT_FAMILIES_V1_H
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static unsigned dws_fixed_maa_alu_scalar(unsigned thread,unsigned dtype,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");DXM_CHECK(src2_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");struct dwi_packet packet={src1_tile,-1,dst_tile,-1,-1,-1,src2_reg,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,8u,dtype,op,&packet,0);unsigned root=dxw_alu(command,8u,dtype,op,&packet,0,0);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static unsigned dws_fixed_maa_alu_vector(unsigned thread,unsigned dtype,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");DXM_CHECK(src2_tile>=0,"source-src2-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");struct dwi_packet packet={src1_tile,src2_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,9u,dtype,op,&packet,0);unsigned root=dxw_alu(command,9u,dtype,op,&packet,0,0);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static unsigned dws_fixed_maa_alu_reduce(unsigned thread,unsigned dtype,int src1_tile,int dst_reg,int op,int cond_tile) {DXM_CHECK(src1_tile>=0,"source-src1-operand-domain");DXM_CHECK(dst_reg>=0,"source-rdst1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");struct dwi_packet packet={src1_tile,-1,-1,-1,dst_reg,-1,-1,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,10u,dtype,op,&packet,0);unsigned root=dxw_alu(command,10u,dtype,op,&packet,0,0);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static unsigned dws_fixed_maa_stream_load(unsigned thread,unsigned dtype,uint64_t data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={-1,-1,dst_tile,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};unsigned command=dwi_prepare_packet(thread,0u,dtype,255,&packet,footprint);unsigned root=dxw_stream(command,0u,dtype,255,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static unsigned dws_fixed_maa_stream_store(unsigned thread,unsigned dtype,uint64_t data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(src_tile>=0,"source-src1-operand-domain");DXM_CHECK(min_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(max_reg>=0,"source-rsrc2-operand-domain");DXM_CHECK(stride_reg>=0,"source-rsrc3-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={src_tile,-1,-1,-1,-1,-1,min_reg,max_reg,stride_reg,cond_tile};unsigned command=dwi_prepare_packet(thread,1u,dtype,255,&packet,footprint);unsigned root=dxw_stream(command,1u,dtype,255,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static unsigned dws_fixed_maa_indirect_load(unsigned thread,unsigned dtype,uint64_t data,int idx_tile,int dst_tile,int cond_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=0,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,2u,dtype,255,&packet,footprint);unsigned root=dxw_indirect(command,2u,dtype,255,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static unsigned dws_fixed_maa_indirect_store_vector(unsigned thread,unsigned dtype,uint64_t data,int idx_tile,int src_tile,int cond_tile,int dst_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");DXM_CHECK(src_tile>=0,"source-src2-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,4u,dtype,255,&packet,footprint);unsigned root=dxw_indirect(command,4u,dtype,255,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static unsigned dws_fixed_maa_indirect_store_scalar(unsigned thread,unsigned dtype,uint64_t data,int idx_tile,int src_reg,int cond_tile,int dst_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,3u,dtype,255,&packet,footprint);unsigned root=dxw_indirect(command,3u,dtype,255,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static unsigned dws_fixed_maa_indirect_rmw_vector(unsigned thread,unsigned dtype,uint64_t data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");DXM_CHECK(src_tile>=0,"source-src2-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={idx_tile,src_tile,dst_tile,-1,-1,-1,-1,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,6u,dtype,o_type,&packet,footprint);unsigned root=dxw_indirect(command,6u,dtype,o_type,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static unsigned dws_fixed_maa_indirect_rmw_scalar(unsigned thread,unsigned dtype,uint64_t data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile,const struct dwi_footprint *footprint,const struct dxw_memory *mapping) {DXM_CHECK(idx_tile>=0,"source-src1-operand-domain");DXM_CHECK(src_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_tile>=-1,"source-dst1-operand-domain");DXM_CHECK(footprint && footprint->source_base==data,"source-address-binding");struct dwi_packet packet={idx_tile,-1,dst_tile,-1,-1,-1,src_reg,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,5u,dtype,o_type,&packet,footprint);unsigned root=dxw_indirect(command,5u,dtype,o_type,&packet,footprint,(void *)mapping);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static unsigned dws_fixed_maa_range_loop(unsigned thread,unsigned dtype,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {DXM_CHECK(min_tile>=0,"source-src1-operand-domain");DXM_CHECK(max_tile>=0,"source-src2-operand-domain");DXM_CHECK(last_i_reg>=0,"source-rdst1-operand-domain");DXM_CHECK(last_j_reg>=0,"source-rdst2-operand-domain");DXM_CHECK(stride_reg>=0,"source-rsrc1-operand-domain");DXM_CHECK(cond_tile>=-1,"source-condition-operand-domain");DXM_CHECK(dst_i_tile>=0,"source-dst1-operand-domain");DXM_CHECK(dst_j_tile>=0,"source-dst2-operand-domain");dtype=1;struct dwi_packet packet={min_tile,max_tile,dst_i_tile,dst_j_tile,last_i_reg,last_j_reg,stride_reg,-1,-1,cond_tile};unsigned command=dwi_prepare_packet(thread,7u,dtype,255,&packet,0);unsigned root=dxw_range(command,7u,dtype,255,&packet,0,0);DXM_CHECK(dxc_constructing==command+1,"atomic-call-binding");dxc_bind(command,root);return command;}
#endif

/*2026-10-16 ET. PRIVATE source pointer bridge; no host pointer casts.
 * Include exact value backend/adapters/builders/closed routes first.
 * Only the compiler-owned lowering may construct or inspect these descriptors.
 * Object/source/provenance/geometry and complete access instrumentation are TCB.
 */
#ifndef SWDB_DX_SOURCE_POINTER_BRIDGE_V1_H
#define SWDB_DX_SOURCE_POINTER_BRIDGE_V1_H
#if defined(__cplusplus)
static_assert(sizeof(float)==4 && sizeof(double)==8,"source scalar representation ABI");
#else
_Static_assert(sizeof(float)==4 && sizeof(double)==8,"source scalar representation ABI");
#endif
struct dws_object {uint64_t guest,physical;unsigned extent,base_cell,dtype;};
static const struct dws_object dws_objects[] = {
  {UINT64_C(65536),UINT64_C(65536),2u,0u,0u},
  {UINT64_C(69632),UINT64_C(69632),2u,2u,1u}
};
struct dws_pointer {unsigned kind,object,tile,dtype;uint64_t offset;};
static struct dws_pointer dws_object_pointer(unsigned object) {
  DXM_CHECK(object<sizeof(dws_objects)/sizeof(dws_objects[0]),"source-object-domain");
  struct dws_pointer p={1,object,0,dws_objects[object].dtype,0};return p;
}
static uint64_t dws_pointer_bytes(struct dws_pointer p) {
  DXM_CHECK(p.dtype<6,"source-pointer-type");unsigned bytes=dxp_width(p.dtype);
  if(p.kind==1) {
    DXM_CHECK(p.object<sizeof(dws_objects)/sizeof(dws_objects[0]),"source-object-domain");
    const struct dws_object *o=&dws_objects[p.object];
    DXM_CHECK(p.dtype==o->dtype && o->base_cell<DXM_CELLS && o->extent<=DXM_CELLS-o->base_cell,"source-cell-binding");
    uint64_t span=(uint64_t)o->extent*bytes;
    uint64_t begin=DXS_SOURCE_MEMORY;
    uint64_t end=begin+UINT64_C(8)*DXS_SOURCE_TILES*DXS_SOURCE_WORDS+UINT64_C(4)*DXS_SOURCE_TILES+UINT64_C(4)*DXS_SOURCE_REGS+24;
    DXM_CHECK(DXS_SOURCE_MEMORY==UINT64_C(17179869184) && DXS_SOURCE_TILES==32 && DXS_SOURCE_REGS==32 && DXS_SOURCE_WORDS==16384,"source-mmio-profile");
    DXM_CHECK(o->guest<=UINT64_MAX-span && o->physical<=UINT64_MAX-span,"source-object-overflow");
    DXM_CHECK((o->guest+span<=begin || end<=o->guest) && (o->physical+span<=begin || end<=o->physical),"ordinary-mmio-alias-refused");
    return span;
  }
  DXM_CHECK(p.kind==2 || p.kind==3,"source-pointer-domain");
  dxm_tile_halves(p.tile,bytes);return (uint64_t)DXP_VALUE_BOUND*bytes;
}
static struct dws_pointer dws_pointer_offset(struct dws_pointer p,int64_t elements) {
  uint64_t total=dws_pointer_bytes(p),bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<=total && p.offset%bytes==0,"source-pointer-formation");
  if(elements>=0) {
    uint64_t n=(uint64_t)elements;DXM_CHECK(n<=(total-p.offset)/bytes,"source-pointer-formation");p.offset+=n*bytes;
  } else {
    uint64_t n=(uint64_t)(-(elements+1))+1;DXM_CHECK(n<=p.offset/bytes,"source-pointer-formation");p.offset-=n*bytes;
  }
  return p;
}
static uint64_t dws_guest_address(struct dws_pointer p) {
  uint64_t total=dws_pointer_bytes(p);DXM_CHECK(p.offset<=total,"source-pointer-formation");
  if(p.kind==1) return dws_objects[p.object].guest+p.offset;
  return dwi_tile_address(p.dtype,p.tile,p.kind==3)+p.offset;
}
static struct dws_pointer dws_tile_pointer(unsigned dtype,int tile,unsigned noncacheable) {
  DXM_CHECK(tile>=0 && noncacheable<=1,"source-tile-pointer-domain");
  (void)dwi_tile_address(dtype,(unsigned)tile,noncacheable);
  struct dws_pointer p={noncacheable?3u:2u,0,(unsigned)tile,dtype,0};return p;
}
static uint64_t dws_cpu_read_bits(unsigned thread,struct dws_pointer p,int64_t index) {
  p=dws_pointer_offset(p,index);uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<total,"source-one-past-dereference");
  if(p.kind==1) {
    const struct dws_object *o=&dws_objects[p.object];uint64_t physical=o->physical+p.offset;
    return dxc_cpu_read(thread,o->base_cell+(unsigned)(p.offset/bytes),physical,physical+bytes);
  }
  DXM_CHECK(p.kind==2,"noncacheable-cpu-access-outside-source-policy");
  return dxp_cpu_read_bits(thread,p.tile,(unsigned)(p.offset/bytes),p.dtype);
}
static void dws_cpu_write_bits(unsigned thread,struct dws_pointer p,int64_t index,uint64_t bits) {
  p=dws_pointer_offset(p,index);uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(p.dtype);
  DXM_CHECK(p.offset<total,"source-one-past-dereference");
  DXM_CHECK(bytes==8 || bits<=UINT32_MAX,"source-scalar-representation");
  if(p.kind==1) {
    const struct dws_object *o=&dws_objects[p.object];uint64_t physical=o->physical+p.offset;
    dxc_cpu_write(thread,o->base_cell+(unsigned)(p.offset/bytes),physical,physical+bytes,bits);return;
  }
  DXM_CHECK(p.kind==2,"noncacheable-cpu-access-outside-source-policy");
  dxp_cpu_write_bits(thread,p.tile,(unsigned)(p.offset/bytes),p.dtype,bits);
}
static void dws_memory_view(struct dws_pointer p,unsigned dtype,struct dwi_footprint *f,struct dxw_memory *m) {
  uint64_t total=dws_pointer_bytes(p);unsigned bytes=dxp_width(dtype);
  DXM_CHECK(p.kind==1 && p.dtype==dtype && p.offset<total && p.offset%bytes==0,"source-array-pointer-binding");
  const struct dws_object *o=&dws_objects[p.object];
  m->base_cell=o->base_cell+(unsigned)(p.offset/bytes);m->extent=o->extent-(unsigned)(p.offset/bytes);
  m->source_base=o->guest+p.offset;m->source_page_bytes=4096u;
  f->source_base=m->source_base;f->logical_begin=m->source_base;f->logical_end=o->guest+total;
  f->physical_begin=o->physical+p.offset;f->physical_end=o->physical+total;f->line_bytes=64u;
  /* Conservative whole remaining object envelope. Never evaluates a deferred
   * index or RF bound at issue and never grants a source region assignment. */
}
struct dws_print_event {unsigned tile,lane,dtype;uint64_t bits;};
#ifndef DWS_PRINT_EVENTS
#define DWS_PRINT_EVENTS 64
#endif
static struct dws_print_event dws_print_events[DWS_PRINT_EVENTS];
static unsigned dws_print_count;
static void dws_print_record(unsigned tile,unsigned lane,unsigned dtype,uint64_t bits,void *context) {
  (void)context;DXM_CHECK(dws_print_count<DWS_PRINT_EVENTS,"source-print-trace-capacity");
  struct dws_print_event *event=&dws_print_events[dws_print_count++];
  event->tile=tile;event->lane=lane;event->dtype=dtype;event->bits=bits;
}
static uint64_t dws_pack_u32(uint32_t value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static uint32_t dws_unpack_u32(uint64_t raw) { uint32_t bits=(uint32_t)raw;uint32_t value;memcpy(&value,&bits,4);return value; }
static uint32_t dws_cpu_load_u32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==0u,"source-pointer-type");return dws_unpack_u32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_u32(unsigned thread,struct dws_pointer p,int64_t index,uint32_t value) {DXM_CHECK(p.dtype==0u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_u32(value));}
static uint64_t dws_pack_i32(int32_t value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static int32_t dws_unpack_i32(uint64_t raw) { uint32_t bits=(uint32_t)raw;int32_t value;memcpy(&value,&bits,4);return value; }
static int32_t dws_cpu_load_i32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==1u,"source-pointer-type");return dws_unpack_i32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_i32(unsigned thread,struct dws_pointer p,int64_t index,int32_t value) {DXM_CHECK(p.dtype==1u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_i32(value));}
static uint64_t dws_pack_f32(float value) { uint32_t bits=0;memcpy(&bits,&value,4);return bits; }
static float dws_unpack_f32(uint64_t raw) { uint32_t bits=(uint32_t)raw;float value;memcpy(&value,&bits,4);return value; }
static float dws_cpu_load_f32(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==2u,"source-pointer-type");return dws_unpack_f32(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_f32(unsigned thread,struct dws_pointer p,int64_t index,float value) {DXM_CHECK(p.dtype==2u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_f32(value));}
static uint64_t dws_pack_u64(uint64_t value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static uint64_t dws_unpack_u64(uint64_t raw) { uint64_t bits=(uint64_t)raw;uint64_t value;memcpy(&value,&bits,8);return value; }
static uint64_t dws_cpu_load_u64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==3u,"source-pointer-type");return dws_unpack_u64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_u64(unsigned thread,struct dws_pointer p,int64_t index,uint64_t value) {DXM_CHECK(p.dtype==3u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_u64(value));}
static uint64_t dws_pack_i64(int64_t value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static int64_t dws_unpack_i64(uint64_t raw) { uint64_t bits=(uint64_t)raw;int64_t value;memcpy(&value,&bits,8);return value; }
static int64_t dws_cpu_load_i64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==4u,"source-pointer-type");return dws_unpack_i64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_i64(unsigned thread,struct dws_pointer p,int64_t index,int64_t value) {DXM_CHECK(p.dtype==4u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_i64(value));}
static uint64_t dws_pack_f64(double value) { uint64_t bits=0;memcpy(&bits,&value,8);return bits; }
static double dws_unpack_f64(uint64_t raw) { uint64_t bits=(uint64_t)raw;double value;memcpy(&value,&bits,8);return value; }
static double dws_cpu_load_f64(unsigned thread,struct dws_pointer p,int64_t index) {DXM_CHECK(p.dtype==5u,"source-pointer-type");return dws_unpack_f64(dws_cpu_read_bits(thread,p,index));}
static void dws_cpu_store_f64(unsigned thread,struct dws_pointer p,int64_t index,double value) {DXM_CHECK(p.dtype==5u,"source-pointer-type");dws_cpu_write_bits(thread,p,index,dws_pack_f64(value));}
#endif

/*2026-10-16 ET. PRIVATE closed source-call routes. */
#ifndef SWDB_DX_SOURCE_ROUTES_V1_H
#define SWDB_DX_SOURCE_ROUTES_V1_H
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_unsigned_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(0u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(1u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_float(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(2u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_unsigned_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(3u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(4u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_double(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(5u,SPD_id,0u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_unsigned_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(0u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(1u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_float(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(2u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_unsigned_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(3u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(4u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_double(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(5u,SPD_id,1u);}
/* MAA_gem5.hpp:56 3781b69d4af7249210a12448f83b9b5cd125b593ad289e9d3160a3ce936b0fff */
static void dws_add_mem_region(unsigned thread,struct dws_pointer start,struct dws_pointer end) {(void)thread;dwi_add_mem_region(dws_guest_address(start),dws_guest_address(end));}
/* MAA_gem5.hpp:60 b310e561e9966a6190eeece3c13274e4123b2967718bc86babf5990df87c73c5 */
static void dws_clear_mem_region(unsigned thread) {(void)thread;dwi_clear_mem_region();}
/* MAA_gem5.hpp:71 2a9e2e96bbeb7f0c7093c6a3501b5e4d67654d8d360767ce83eb17df57df8eac */
static void dws_alloc_MAA(unsigned thread) {(void)thread;dwi_alloc_MAA();}
/* MAA_gem5.hpp:93 cf708b8c3413e2d8ca92a4fc6c8791df674b603b46a452293b4f0992ef4d4af3 */
static void dws_init_MAA(unsigned thread) {(void)thread;dwi_init_MAA();}
/* MAA_gem5.hpp:98 963dad36a357d2f9063c552ebf4080f5a865896021db3519f3c365d36f507ceb */
static void dws_wait_ready(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");dwi_wait_ready((unsigned)SPD_id);}
/* MAA_gem5.hpp:102 4a0fd5811d735b68236c767b371fcd289c874ce0ebb7f6989a38ce3e8df1a0ab */
static uint16_t dws_get_tile_size(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");return dwi_get_tile_size((unsigned)SPD_id);}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static uint32_t dws_get_reg_unsigned_int(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_u32(dwi_get_reg(thread,0u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static int32_t dws_get_reg_int(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_i32(dwi_get_reg(thread,1u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static float dws_get_reg_float(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_f32(dwi_get_reg(thread,2u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static uint64_t dws_get_reg_unsigned_long(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_u64(dwi_get_reg(thread,3u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static int64_t dws_get_reg_long(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_i64(dwi_get_reg(thread,4u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static double dws_get_reg_double(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_f64(dwi_get_reg(thread,5u,(unsigned)reg_id));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_unsigned_int(unsigned thread,int reg_id,uint32_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,0u,(unsigned)reg_id,dws_pack_u32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_int(unsigned thread,int reg_id,int32_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,1u,(unsigned)reg_id,dws_pack_i32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_float(unsigned thread,int reg_id,float data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,2u,(unsigned)reg_id,dws_pack_f32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_unsigned_long(unsigned thread,int reg_id,uint64_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,3u,(unsigned)reg_id,dws_pack_u64(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_long(unsigned thread,int reg_id,int64_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,4u,(unsigned)reg_id,dws_pack_i64(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_double(unsigned thread,int reg_id,double data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,5u,(unsigned)reg_id,dws_pack_f64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_unsigned_int_args1(unsigned thread,uint32_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,0u,dws_pack_u32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_int_args1(unsigned thread,int32_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,1u,dws_pack_i32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_float_args1(unsigned thread,float data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,2u,dws_pack_f32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_unsigned_long_args1(unsigned thread,uint64_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,3u,dws_pack_u64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_long_args1(unsigned thread,int64_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,4u,dws_pack_i64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_double_args1(unsigned thread,double data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,5u,dws_pack_f64(data));}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_unsigned_int_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,0u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_int_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,1u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_float_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,2u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_unsigned_long_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,3u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_long_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,4u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_double_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,5u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_unsigned_int(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,0u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_int(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,1u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_float(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,2u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_unsigned_long(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,3u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_long(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,4u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_double(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,5u);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_unsigned_int(unsigned thread,uint32_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,0u,dws_pack_u32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_int(unsigned thread,int32_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,1u,dws_pack_i32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_float(unsigned thread,float data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,2u,dws_pack_f32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_unsigned_long(unsigned thread,uint64_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,3u,dws_pack_u64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_long(unsigned thread,int64_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,4u,dws_pack_i64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_double(unsigned thread,double data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,5u,dws_pack_f64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_unsigned_int(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,0u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,0u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_int(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,1u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,1u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_float(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,2u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,2u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_unsigned_long(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,3u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,3u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_long(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,4u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,4u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_double(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,5u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,5u),0);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_unsigned_int(unsigned thread) {(void)thread;return dwi_get_data_type(0u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_int(unsigned thread) {(void)thread;return dwi_get_data_type(1u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_float(unsigned thread) {(void)thread;return dwi_get_data_type(2u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_unsigned_long(unsigned thread) {(void)thread;return dwi_get_data_type(3u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_long(unsigned thread) {(void)thread;return dwi_get_data_type(4u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_double(unsigned thread) {(void)thread;return dwi_get_data_type(5u);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_unsigned_int(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,0u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_int(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,1u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_float(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,2u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_unsigned_long(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,3u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_long(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,4u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_double(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,5u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_unsigned_int(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,0u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_int(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,1u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_float(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,2u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_unsigned_long(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,3u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_long(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,4u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_double(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,5u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_unsigned_int(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,0u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_int(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,1u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_float(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,2u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_unsigned_long(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,3u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_long(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,4u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_double(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,5u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_unsigned_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,0u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,1u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_float(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,2u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_unsigned_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,3u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,4u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_double(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,5u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_unsigned_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,0u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,1u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_float(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,2u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_unsigned_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,3u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,4u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_double(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,5u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,0u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_int(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,1u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_float(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,2u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,3u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_long(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,4u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_double(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,5u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,0u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,1u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,2u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,3u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,4u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,5u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,0u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,1u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,2u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,3u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,4u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,5u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,0u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,1u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,2u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,3u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,4u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,5u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,0u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,1u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,2u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,3u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,4u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,5u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_unsigned_int(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,0u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_int(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,1u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_float(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,2u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_unsigned_long(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,3u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_long(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,4u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_double(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,5u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
static unsigned dws_get_data_type_other(unsigned thread) {(void)thread;return dwi_get_data_type(6);}
#endif


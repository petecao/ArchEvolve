"""Emit standalone DX100 numeric helpers. Created: 2026-10-15 ET.

Prototype only: no state, source-header admission, ABI binding or proof claim.
Dtypes/opcodes match immutable DX100 e4fc4af; caller supplies settled raw bits.
"""

TYPES = {0: ('uint32_t', 32, False), 1: ('int32_t', 32, True),
         3: ('uint64_t', 64, False), 4: ('int64_t', 64, True)}


def _integer_case(dtype, ctype, width, signed):
    utype = f'uint{width}_t'
    maximum = f'INT{width}_MAX' if signed else f'UINT{width}_MAX'
    minimum = f'INT{width}_MIN'
    rows = [f'case {dtype}: {{', f'  {utype} ua=({utype})lhs,ub=({utype})rhs;']
    if signed:
        rows += [f'  {ctype} a,b,z;', '  memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));']
    else:
        rows += [f'  {ctype} a=ua,b=ub,z;']
    rows += ['  switch(op) {']
    for op, symbol in [(0, '+'), (1, '-'), (2, '*'), (3, '/')]:
        rows += [f'  case {op}:']
        guard = None
        if signed:
            guard = {
                0: f'!((b>0 && a>{maximum}-b)||(b<0 && a<{minimum}-b))',
                1: f'!((b<0 && a>{maximum}+b)||(b>0 && a<{minimum}+b))',
                2: f'(a==0 || b==0 || (a>0 ? (b>0 ? a<={maximum}/b : b>={minimum}/a) : '
                   f'(b>0 ? a>={minimum}/b : a>={maximum}/b)))',
                3: f'b!=0 && !(a=={minimum} && b==-1)',
            }[op]
        elif op == 3:
            guard = 'b!=0'
        if guard:
            rows += [f'    if (!dx_num_guard({guard},"numeric.{op}.i{width if signed else 0}")) return DX_NUM_ARITHMETIC;']
        rows += [f'    z=({ctype})(a{symbol}b); break;']
    rows += ['  case 4: z=a<b?a:b; break;', '  case 5: z=a>b?a:b; break;']
    for op, symbol in [(6,'&'), (7,'|'), (8,'^')]:
        rows += [f'  case {op}: *out=({utype})(ua{symbol}ub); return DX_NUM_OK;']
    for op in [9, 10]:
        rows += [f'  case {op}:']
        if signed:
            rows += ['    if (!runtime || runtime->signed_shift_cpp17_arithmetic!=1)',
                     '      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.signed_shift_runtime");']
        rows += [f'    if (!dx_num_guard({"b>=0 && " if signed else ""}b<{width},"numeric.shift_count")) return DX_NUM_ARITHMETIC;']
        if signed and op == 9:
            rows += [f'    if (!dx_num_guard(a>=0 && ua<=(UINT{width}_MAX>>b),"numeric.signed_left")) return DX_NUM_ARITHMETIC;']
        if op == 9:
            rows += [f'    *out=({utype})(ua<<b); return DX_NUM_OK;']
        elif signed:
            rows += [f'    *out=b==0?ua:({utype})((ua>>b)|(a<0?({utype})(UINT{width}_MAX<<({width}-b)):0)); return DX_NUM_OK;']
        else:
            rows += [f'    *out=({utype})(ua>>b); return DX_NUM_OK;']
    for op, symbol in [(11,'>'),(12,'>='),(13,'<'),(14,'<='),(15,'==')]:
        rows += [f'  case {op}: *out=(uint32_t)(a{symbol}b); return DX_NUM_OK;']
    rows += ['  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");', '  }']
    if signed:
        rows += ['  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;']
    else:
        rows += ['  *out=z; return DX_NUM_OK;']
    return '\n'.join(rows + ['}'])



def _floating_case(dtype, ctype, width):
    utype=f'uint{width}_t'
    rows=[f'case {dtype}: {{',
          '  if (op>=6 && op<=10) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_opcode");',
          '  if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");',
          f'  {utype} ua=({utype})lhs,ub=({utype})rhs;',
          f'  {ctype} a,b,z; memcpy(&a,&ua,sizeof(a)); memcpy(&b,&ub,sizeof(b));',
          '  switch(op) {']
    for op,symbol in [(0,'+'),(1,'-'),(2,'*'),(3,'/')]:
        rows += [f'  case {op}: z=a{symbol}b; break;']
    for op in [4,5]:
        ordered='b<a?b:a' if op==4 else 'a<b?b:a'
        rmw='a<b?a:b' if op==4 else 'a>b?a:b'
        rows += [f'  case {op}:',
                 '    if (family==0 && (isnan(a)||isnan(b)) && runtime->alu_minmax_unordered_first!=1)',
                 '      return dx_num_refusal(DX_NUM_RUNTIME,"numeric.alu_minmax_nan_runtime");',
                 f'    z=family==1?({rmw}):({ordered}); break;']
    for op,symbol in [(11,'>'),(12,'>='),(13,'<'),(14,'<='),(15,'==')]:
        rows += [f'  case {op}: *out=(uint32_t)(a{symbol}b); return DX_NUM_OK;']
    rows += ['  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.opcode");',
             '  }', '  memcpy(&ua,&z,sizeof(z)); *out=ua; return DX_NUM_OK;', '}']
    return '\n'.join(rows)


def _initializers():
    rows=['static inline enum dx_num_status dxv_initializer_bits(unsigned dtype,unsigned op,',
          '              const struct dx_num_runtime *runtime,uint64_t *out) {',
          '  if (!out || op>7) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.reduction_opcode");',
          '  switch(dtype) {']
    for dtype,(_,width,signed) in TYPES.items():
        maximum=f'INT{width}_MAX' if signed else f'UINT{width}_MAX'
        minimum=f'(UINT{width}_C(1)<<{width-1})' if signed else '0'
        rows += [f'  case {dtype}:',
                 '    switch(op) {',
                 '    case 0: case 1: case 7: *out=0; break;',
                 '    case 2: case 3: *out=1; break;',
                 f'    case 4: *out={maximum}; break;',
                 f'    case 5: *out={minimum}; break;',
                 f'    case 6: *out=UINT{width}_MAX; break;',
                 '    } return DX_NUM_OK;']
    for dtype,ctype,width,prefix in [(2,'float',32,'FLT'),(5,'double',64,'DBL')]:
        rows += [f'  case {dtype}: {{',
                 '    if (op>5) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.float_reduction_opcode");',
                 '    if (!dx_num_float_runtime(runtime)) return dx_num_refusal(DX_NUM_RUNTIME,"numeric.float_runtime");',
                 f'    {ctype} z; uint{width}_t bits;',
                 '    switch(op) {',
                 '    case 0: case 1: z=0; break;',
                 '    case 2: case 3: z=1; break;',
                 f'    case 4: z={prefix}_MAX; break;',
                 f'    default: z={prefix}_MIN; break;',
                 '    } memcpy(&bits,&z,sizeof(z)); *out=bits; return DX_NUM_OK;', '  }']
    rows += ['  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.dtype");', '  }','}',
             'static inline enum dx_num_status dxv_reduce_bits(unsigned dtype,unsigned op,',
             '       const uint64_t *values,const uint32_t *active,size_t count,',
             '       const struct dx_num_runtime *runtime,uint64_t *out) {',
             '  if (!out || (count && !values)) return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.reduction_storage");',
             '  uint64_t acc,next; enum dx_num_status status=dxv_initializer_bits(dtype,op,runtime,&acc);',
             '  if (status!=DX_NUM_OK) return status;',
             '  for (size_t i=0;i<count;i++) if (!active || active[i]!=0) {',
             '    status=dxv_eval_bits(dtype,op,values[i],acc,0,runtime,&next);',
             '    if (status!=DX_NUM_OK) return status;',
             '    acc=next;', '  }', '  *out=acc; return DX_NUM_OK;', '}']
    return '\n'.join(rows)

def render_header():
    """Emit C11/C++17 raw-bit helpers. Callbacks must preserve failure status."""
    prefix = r'''/* Created2026-10-15 ET. Prototype numeric values; no device/refinement claim. */
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
'''
    suffix = r'''
  default: return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.dtype");
  }
}
''' + _initializers() + r'''
/* Source-faithful ordinary-array domain: reject uint32 intermediate wrap first.
   Object validity, address-space/line correspondence and Addr addition remain caller obligations. */
static inline enum dx_num_status dxv_indirect_offset_bits(unsigned word_size,uint32_t index,uint64_t *out) {
  if (!out || (word_size!=4 && word_size!=8))
    return dx_num_refusal(DX_NUM_UNSUPPORTED,"numeric.word_size");
  if (!dx_num_guard(index<=UINT32_MAX/word_size,"numeric.indirect_offset_wrap")) return DX_NUM_ARITHMETIC;
  *out=(uint64_t)word_size*index; return DX_NUM_OK;
}
#endif
'''
    return prefix + '\n'.join(_integer_case(dtype, *spec) for dtype, spec in TYPES.items()) + '\n' + \
        '\n'.join(_floating_case(*spec) for spec in [(2,'float',32),(5,'double',64)]) + suffix


FLOAT_TYPES = {2: ('float', 32), 5: ('double', 64)}
SOURCE_COMMIT = 'e4fc4afdf894f295442cef3604667a469fab8e62'


def operation_contract(dtype, op, *, family='alu'):
    """Guard/result expressions over decoded typed lhs/rhs/result values.

    Expressions are candidate obligations, NEVER new original-unit preconditions.
    Integer expressions use ACSL mathematical promotion/casts, including truncating
    integer division. No actual ACSL parse/proof evidence is claimed here.
    Float bodies are concrete C; missing IEEE logic is reported instead of axiomatized.
    """
    if type(dtype) is not int or dtype not in TYPES | FLOAT_TYPES or type(op) is not int or \
            not 0 <= op <= 15 or family not in ('alu', 'rmw') or \
            (family == 'rmw' and op not in (0, 4, 5)) or (dtype in FLOAT_TYPES and 6 <= op <= 10):
        raise ValueError('unsupported exact dtype/opcode/family')
    if dtype in FLOAT_TYPES:
        ctype, width = FLOAT_TYPES[dtype]
        return {'dtype': dtype, 'opcode': op, 'family': family, 'ctype': ctype,
                'guard_c': '1', 'guard_acsl': r'\true', 'result_acsl': None,
                'runtime_requirements': [f'IEEE_binary{width}_nearest_even_no_fast_math_no_excess_precision',
                                         'ALU_NaN_minmax_requires_bound_first_unordered_policy']
                                        if family == 'alu' and op in (4, 5) else
                                        [f'IEEE_binary{width}_nearest_even_no_fast_math_no_excess_precision'],
                'logical_boundary': 'IEEE bit-level relation not generated; no real arithmetic stand-in',
                'source': {'commit': SOURCE_COMMIT, 'path': 'src/mem/MAA/ALU.cc' if family == 'alu' else
                           'src/mem/MAA/IndirectAccess.cc', 'type_branch_line':
                           ({2:448,5:706} if family == 'alu' else {2:975,5:1020})[dtype]}}
    ctype, width, signed = TYPES[dtype]
    mod = 1 << width
    minimum, maximum = (-(1 << (width-1)), (1 << (width-1))-1) if signed else (0, mod-1)
    guard, c_guard, runtime = r'\true', '1', []
    symbol = {0:'+',1:'-',2:'*',3:'/',6:'&',7:'|',8:'^',9:'<<',10:'>>',
              11:'>',12:'>=',13:'<',14:'<=',15:'=='}
    if signed and op in (0,1,2):
        expr = f'lhs {symbol[op]} rhs'
        guard = f'{minimum} <= {expr} && {expr} <= {maximum}'
        c_guard = {
            0: f'!((rhs>0 && lhs>INT{width}_MAX-rhs)||(rhs<0 && lhs<INT{width}_MIN-rhs))',
            1: f'!((rhs<0 && lhs>INT{width}_MAX+rhs)||(rhs>0 && lhs<INT{width}_MIN+rhs))',
            2: f'(lhs==0 || rhs==0 || (lhs>0 ? (rhs>0 ? lhs<=INT{width}_MAX/rhs : rhs>=INT{width}_MIN/lhs) : '
               f'(rhs>0 ? lhs>=INT{width}_MIN/rhs : lhs>=INT{width}_MAX/rhs)))',
        }[op]
    elif op == 3:
        guard = f'rhs != 0 && !(lhs == {minimum} && rhs == -1)' if signed else 'rhs != 0'
        c_guard = guard
    elif op in (9,10):
        guard = f'0 <= rhs && rhs < {width}'
        c_guard = f'{"rhs>=0 && " if signed else ""}rhs<{width}'
        if signed:
            runtime = ['cpp17_signed_shift_arithmetic_right']
        if signed and op == 9:
            guard += f' && 0 <= lhs && (lhs << rhs) < {mod}'
            c_guard += f' && lhs>=0 && (uint{width}_t)lhs<=(UINT{width}_MAX>>rhs)'
    if op in (4,5):
        expression = f'(lhs {"<" if op==4 else ">"} rhs ? lhs : rhs)'
    elif op >= 11:
        expression = f'(lhs {symbol[op]} rhs ? 1 : 0)'
    elif not signed and op in (0,1,2,9):
        expression = f'(lhs - rhs + {mod}) % {mod}' if op == 1 else f'(lhs {symbol[op]} rhs) % {mod}'
    elif signed and op == 9:
        expression = f'((lhs << rhs) >= {1 << (width-1)} ? (lhs << rhs) - {mod} : (lhs << rhs))'
    else:
        expression = f'(lhs {symbol[op]} rhs)'
    return {'dtype': dtype, 'opcode': op, 'family': family, 'ctype': ctype,
            'operand_bounds_acsl': f'{minimum} <= lhs <= {maximum} && {minimum} <= rhs <= {maximum}',
            'guard_c': c_guard, 'guard_acsl': guard, 'result_acsl': 'result == ' + expression,
            'runtime_requirements': runtime,
            'logical_boundary': 'Decoded typed integers; caller binds raw-bit conversion and proves guard',
            'source': {'commit': SOURCE_COMMIT, 'path': 'src/mem/MAA/ALU.cc' if family == 'alu' else
                       'src/mem/MAA/IndirectAccess.cc', 'type_branch_line':
                       ({0:266,1:357,3:524,4:615} if family == 'alu' else {0:945,1:960,3:990,4:1005})[dtype]}}


def offset_contract(word_size):
    """Active-lane no-wrap obligation; no assertion of C-object/address validity."""
    if type(word_size) is not int or word_size not in (4,8):
        raise ValueError('only pinned4/8-byte data widths are supported')
    return {'guard_c': f'index <= UINT32_MAX / {word_size}',
            'guard_acsl': f'0 <= index && index <= {((1 << 32)-1)//word_size}',
            'result_acsl': f'byte_offset == {word_size} * index',
            'source': {'commit': SOURCE_COMMIT, 'path': 'src/mem/MAA/IndirectAccess.cc', 'line': 494},
            'boundary': 'Source uint32 intermediate no-wrap only; object/Addr/physical-line obligations remain'}

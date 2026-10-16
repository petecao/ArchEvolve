"""Native controls for the ticket28 emitted value API. Created2026-10-15 ET."""
import importlib.util
import hashlib
import json
import platform
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics/numeric_values.py'


def emitter():
    spec = importlib.util.spec_from_file_location('dx_numeric_values', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native(tmp_path, body, *, cpp=False, returning_callbacks=False):
    (tmp_path / 'numeric.h').write_text(emitter().render_header())
    source = tmp_path / ('control.cc' if cpp else 'control.c')
    source.write_text('''#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
static jmp_buf failure;
static const char *failure_kind;
static const char *failure_rule;
#define DX_NUM_CHECK(c,r) do { if (!(c)) { failure_kind="arithmetic"; failure_rule=(r); longjmp(failure,1); } } while(0)
#define DX_NUM_REFUSE(r) do { failure_kind="domain"; failure_rule=(r); longjmp(failure,1); } while(0)
#include "numeric.h"
''' + r'''
static uint64_t dx_num_eval(unsigned dtype,unsigned op,uint64_t lhs,uint64_t rhs,
    unsigned family,const struct dx_num_runtime *runtime) {
  uint64_t out; assert(dxv_eval_bits(dtype,op,lhs,rhs,family,runtime,&out)==DX_NUM_OK); return out;
}
''' + body)
    if returning_callbacks:
        source.write_text(source.read_text().replace('longjmp(failure,1);', '(void)0;'))
    binary = tmp_path / 'control'
    command = ['/usr/bin/clang++' if cpp else '/usr/bin/clang', '-std=c++17' if cpp else '-std=c11',
               '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
               '-fno-fast-math', '-ffp-contract=off', '-frounding-math', str(source), '-o', str(binary)]
    (tmp_path / 'compile-command.json').write_text(json.dumps(command,indent=2)+'\n')
    version = subprocess.run([command[0], '--version'],text=True,capture_output=True,timeout=10)
    (tmp_path / 'compiler-context.json').write_text(json.dumps({
        'platform':platform.platform(), 'machine':platform.machine(),
        'compiler':command[0], 'compiler_sha256':hashlib.sha256(Path(command[0]).read_bytes()).hexdigest(),
        'version_stdout':version.stdout, 'version_stderr':version.stderr, 'version_status':version.returncode,
        'boundary':'Mac native scalar controls only; does not bind Linux/x86 typedef identities or simulator flags'
    },indent=2)+'\n')
    built = subprocess.run(command, text=True, capture_output=True, timeout=30)
    (tmp_path / 'compile-result.json').write_text(json.dumps({'status':built.returncode,'stdout':built.stdout,'stderr':built.stderr},indent=2)+'\n')
    assert built.returncode == 0, built.stderr
    run = subprocess.run([str(binary)], text=True, capture_output=True, timeout=15,
                         env={**os.environ, 'ASAN_OPTIONS':'detect_leaks=0'})
    (tmp_path / 'native-result.json').write_text(json.dumps({
        'command':[str(binary)], 'ASAN_OPTIONS':'detect_leaks=0', 'status':run.returncode,
        'stdout':run.stdout, 'stderr':run.stderr, 'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()
    },indent=2)+'\n')
    assert run.returncode == 0, run.stdout + run.stderr
    return run.stdout


def test_unsigned_arithmetic_keeps_defined_wrap(tmp_path):
    native(tmp_path, '''int main(void) {
  assert(dx_num_eval(0,0,UINT32_MAX,1,0,0)==0);
  assert(dx_num_eval(0,1,0,1,0,0)==UINT32_MAX);
  assert(dx_num_eval(0,2,UINT32_MAX,2,0,0)==UINT32_C(4294967294));
  return 0;
}''')


def test_integer_values_and_guarded_bad_domains(tmp_path):
    native(tmp_path, r'''static const struct dx_num_runtime bound={1,1,1};
static void bad(unsigned dtype,unsigned op,uint64_t a,uint64_t b,unsigned family,
                const struct dx_num_runtime *rt,const char *kind) {
  if (setjmp(failure)==0) { (void)dx_num_eval(dtype,op,a,b,family,rt); assert(!"expected domain failure"); }
  assert(strcmp(failure_kind,kind)==0);
}
int main(void) {
  assert(dx_num_eval(3,0,UINT64_MAX,1,0,0)==0);
  assert(dx_num_eval(0,0,UINT64_MAX,2,0,0)==1); /* u32 normalization */
  assert(dx_num_eval(1,0,UINT32_C(4294967293),5,0,0)==2);
  assert(dx_num_eval(1,1,UINT32_C(4294967293),5,0,0)==UINT32_C(4294967288));
  assert(dx_num_eval(1,2,UINT32_C(4294967293),5,0,0)==UINT32_C(4294967281));
  assert(dx_num_eval(4,3,UINT64_C(18446744073709551609),2,0,0)==UINT64_C(18446744073709551613));
  assert(dx_num_eval(1,13,UINT32_MAX,0,0,0)==1);
  assert(dx_num_eval(0,13,UINT32_MAX,0,0,0)==0);
  assert(dx_num_eval(4,6,UINT64_MAX,15,0,0)==15);
  assert(dx_num_eval(1,9,1,31,0,&bound)==UINT32_C(2147483648));
  assert(dx_num_eval(1,10,UINT32_C(2147483648),31,0,&bound)==UINT32_MAX);
  assert(dx_num_eval(3,9,1,63,0,0)==UINT64_C(9223372036854775808));
  assert(dx_num_eval(1,4,UINT32_MAX,1,1,0)==UINT32_MAX);
  bad(1,0,INT32_MAX,1,0,0,"arithmetic");
  bad(4,1,UINT64_C(9223372036854775808),1,0,0,"arithmetic");
  bad(1,2,UINT32_C(2147483648),UINT32_MAX,0,0,"arithmetic");
  bad(4,3,UINT64_C(9223372036854775808),UINT64_MAX,0,0,"arithmetic");
  bad(0,3,4,0,0,0,"arithmetic");
  bad(0,9,1,32,0,0,"arithmetic");
  bad(1,9,UINT32_MAX,1,0,&bound,"arithmetic");
  bad(1,10,1,1,0,0,"domain");
  bad(0,16,1,2,0,0,"domain");
  bad(0,1,1,2,1,0,"domain");
  bad(9,0,1,2,0,0,"domain");
  return 0;
}''', cpp=True)


def test_ieee_values_keep_source_specific_selection(tmp_path):
    native(tmp_path, r'''static const struct dx_num_runtime bound={1,1,1};
static const struct dx_num_runtime unordered_unknown={1,1,0};
static void refused(unsigned dtype,unsigned op,uint64_t a,uint64_t b,
                    const struct dx_num_runtime *rt) {
  if (setjmp(failure)==0) { (void)dx_num_eval(dtype,op,a,b,0,rt); assert(!"expected runtime/domain refusal"); }
  assert(strcmp(failure_kind,"domain")==0);
}
int main(void) {
  assert(dx_num_eval(2,0,UINT32_C(0x3f800000),UINT32_C(0x40000000),0,&bound)==UINT32_C(0x40400000));
  assert(dx_num_eval(2,0,UINT32_C(0x4b800000),UINT32_C(0x3f800000),0,&bound)==UINT32_C(0x4b800000));
  assert(dx_num_eval(5,0,UINT64_C(0x3ff0000000000000),UINT64_C(0x4000000000000000),0,&bound)==UINT64_C(0x4008000000000000));
  assert(dx_num_eval(2,15,UINT32_C(0x7fc00001),UINT32_C(0x7fc00001),0,&bound)==0);
  assert(dx_num_eval(2,4,UINT32_C(0x80000000),0,0,&bound)==UINT32_C(0x80000000));
  assert(dx_num_eval(2,4,UINT32_C(0x80000000),0,1,&bound)==0);
  assert(dx_num_eval(2,4,UINT32_C(0x7fc00001),UINT32_C(0x40400000),1,&bound)==UINT32_C(0x40400000));
  assert(dx_num_eval(2,4,UINT32_C(0x40400000),UINT32_C(0x7fc00001),1,&bound)==UINT32_C(0x7fc00001));
  assert(dx_num_eval(2,4,UINT32_C(0x7fc00001),UINT32_C(0x40400000),0,&bound)==UINT32_C(0x7fc00001));
  assert(dx_num_eval(2,3,UINT32_C(0x3f800000),UINT32_C(0x80000000),0,&bound)==UINT32_C(0xff800000));
  assert(dx_num_eval(2,2,UINT32_C(0x7f7fffff),UINT32_C(0x40000000),0,&bound)==UINT32_C(0x7f800000));
  refused(2,6,0,0,&bound);
  refused(5,0,0,0,0);
  refused(2,4,UINT32_C(0x7fc00001),0,&unordered_unknown);
  assert(fesetround(FE_DOWNWARD)==0);
  refused(2,0,0,0,&bound);
  assert(fesetround(FE_TONEAREST)==0);
  return 0;
}''')


def test_reduction_preserves_source_recurrence_and_initializer(tmp_path):
    native(tmp_path, r'''static const struct dx_num_runtime bound={1,1,1};
int main(void) {
  uint64_t out=99;
  const uint64_t sub[]={5,2}, divs[]={2,8}, zeros[]={2,1,3};
  const uint64_t negatives[]={UINT32_C(0xbf800000),UINT32_C(0xc0000000)};
  const uint32_t active[]={1,0,1};
  assert(dxv_reduce_bits(1,1,sub,0,2,0,&out)==DX_NUM_OK && out==UINT32_C(4294967293));
  assert(dxv_reduce_bits(0,3,divs,0,2,0,&out)==DX_NUM_OK && out==4);
  assert(dxv_initializer_bits(1,6,0,&out)==DX_NUM_OK && out==UINT32_MAX);
  assert(dxv_initializer_bits(4,5,0,&out)==DX_NUM_OK && out==UINT64_C(9223372036854775808));
  assert(dxv_reduce_bits(2,5,negatives,0,2,&bound,&out)==DX_NUM_OK && out==UINT32_C(0x00800000));
  assert(dxv_reduce_bits(5,5,0,0,0,&bound,&out)==DX_NUM_OK && out==UINT64_C(0x0010000000000000));
  assert(dxv_reduce_bits(0,3,zeros,active,3,0,&out)==DX_NUM_OK && out==1);
  if (setjmp(failure)==0) { (void)dxv_reduce_bits(0,3,zeros,0,3,0,&out); assert(!"expected accumulator-zero failure"); }
  assert(strcmp(failure_kind,"arithmetic")==0);
  if (setjmp(failure)==0) { (void)dxv_initializer_bits(2,7,&bound,&out); assert(!"float OR reduction unsupported"); }
  assert(strcmp(failure_kind,"domain")==0);
  if (setjmp(failure)==0) { (void)dxv_initializer_bits(0,8,0,&out); assert(!"XOR reduction unsupported"); }
  return 0;
}''', cpp=True)


def test_nonfatal_callbacks_preserve_status_and_output(tmp_path):
    native(tmp_path, r'''int main(void) {
  uint64_t out=UINT64_C(0xfeedface);
  assert(dxv_eval_bits(1,0,INT32_MAX,1,0,0,&out)==DX_NUM_ARITHMETIC);
  assert(out==UINT64_C(0xfeedface));
  assert(strcmp(failure_kind,"arithmetic")==0);
  assert(dxv_eval_bits(2,0,0,0,0,0,&out)==DX_NUM_RUNTIME);
  assert(out==UINT64_C(0xfeedface));
  assert(dxv_eval_bits(0,16,0,0,0,0,&out)==DX_NUM_UNSUPPORTED);
  assert(out==UINT64_C(0xfeedface));
  return 0;
}''', returning_callbacks=True)


def test_contract_expressions_do_not_assume_away_machine_behavior():
    value = emitter()
    wrap = value.operation_contract(0, 1)
    assert wrap['guard_acsl'] == r'\true'
    assert wrap['result_acsl'] == 'result == (lhs - rhs + 4294967296) % 4294967296'
    signed = value.operation_contract(4, 0)
    assert signed['guard_acsl'] == '-9223372036854775808 <= lhs + rhs && lhs + rhs <= 9223372036854775807'
    shift = value.operation_contract(1, 9)
    assert '4294967296' in shift['guard_acsl']
    assert shift['runtime_requirements'] == ['cpp17_signed_shift_arithmetic_right']
    floating = value.operation_contract(2, 0)
    assert floating['result_acsl'] is None
    assert floating['logical_boundary'] == 'IEEE bit-level relation not generated; no real arithmetic stand-in'
    assert value.offset_contract(8)['guard_acsl'] == '0 <= index && index <= 536870911'
    for dtype, op, family in [(2,6,'alu'),(0,16,'alu'),(0,1,'rmw'),(True,0,'alu')]:
        try:
            value.operation_contract(dtype,op,family=family)
        except ValueError:
            pass
        else:
            raise AssertionError('unsupported contract must refuse')


def test_indirect_offset_intermediate_cannot_silently_wrap(tmp_path):
    native(tmp_path, r'''int main(void) {
  uint64_t out;
  assert(dxv_indirect_offset_bits(4,UINT32_C(1073741823),&out)==DX_NUM_OK && out==UINT32_C(4294967292));
  assert(dxv_indirect_offset_bits(8,UINT32_C(536870911),&out)==DX_NUM_OK && out==UINT32_C(4294967288));
  if (setjmp(failure)==0) { (void)dxv_indirect_offset_bits(4,UINT32_C(1073741824),&out); assert(!"would wrap offset to zero"); }
  assert(strcmp(failure_kind,"arithmetic")==0);
  if (setjmp(failure)==0) { (void)dxv_indirect_offset_bits(8,UINT32_C(536870912),&out); assert(!"would wrap offset to zero"); }
  assert(strcmp(failure_kind,"arithmetic")==0);
  return 0;
}''')


def test_every_integer_opcode_uses_the_pinned_numeric_value(tmp_path):
    body = r'''static const struct dx_num_runtime bound={1,1,1};
int main(void) {
  const uint64_t golden[16]={16,10,39,4,3,13,1,15,14,104,1,1,1,0,0,0};
  const unsigned types[4]={0,1,3,4};
  for (unsigned t=0;t<4;t++) for(unsigned op=0;op<16;op++)
    assert(dx_num_eval(types[t],op,13,3,0,&bound)==golden[op]);
  assert(dx_num_eval(1,8,UINT32_MAX,1,0,&bound)==UINT32_C(4294967294));
  assert(dx_num_eval(4,7,UINT64_C(9223372036854775808),1,0,&bound)==UINT64_C(9223372036854775809));
  return 0;
}'''
    c_path=tmp_path/'c'; c_path.mkdir()
    native(c_path,body)
    cpp_path=tmp_path/'cpp'; cpp_path.mkdir()
    native(cpp_path,body,cpp=True)


def test_signed_guard_boundaries_match_mathematical_source_domains(tmp_path):
    rows=[]
    for dtype,width in [(1,32),(4,64)]:
        low, high=-(1<<(width-1)), (1<<(width-1))-1
        edge=[low,low+1,-2,-1,0,1,2,high-1,high]
        for a in edge:
            for b in edge:
                for op,value in [(0,a+b),(1,a-b),(2,a*b)]:
                    status='DX_NUM_OK' if low<=value<=high else 'DX_NUM_ARITHMETIC'
                    bits=value% (1<<width)
                    rows.append(f'  out=99; status=dxv_eval_bits({dtype},{op},UINT64_C({a%(1<<width)}),UINT64_C({b%(1<<width)}),0,0,&out); '
                                f'assert(status=={status}); assert(out==UINT64_C({bits if status=="DX_NUM_OK" else 99}));')
    native(tmp_path,'int main(void) { uint64_t out; enum dx_num_status status;\n'+ '\n'.join(rows)+'\n return 0; }',
           returning_callbacks=True)

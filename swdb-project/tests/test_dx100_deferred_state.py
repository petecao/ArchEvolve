"""2026-10-15 ET. Synthetic executable model API; no actual verifier evidence."""
import importlib.util
import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shlex

import pytest

from swdb import c_lowering


ROOT = Path(__file__).parents[1] / '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics'


def file_pin(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


@functools.lru_cache
def compiler_context(tool):
    from swdb.stdlib_provenance import runtime_identity
    return runtime_identity(tool)


def run_model(tmp_path, body, *, exit_code=0, prelude='', commands=False, numeric=False, actions=False, regions=False, image=False, cpp=False):
    spec = importlib.util.spec_from_file_location('dx_deferred_state', ROOT / 'deferred_state.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    header = module.render_header()
    if numeric:
        spec = importlib.util.spec_from_file_location('dx_numeric_values', ROOT / 'numeric_values.py')
        numeric_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(numeric_module)
        spec = importlib.util.spec_from_file_location('dx_typed_state', ROOT / 'typed_state.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        header = module.render_header(header, numeric_module.render_header())
    if commands:
        spec = importlib.util.spec_from_file_location('dx_command_state', ROOT / 'command_state.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        header = module.render_header(header)
    if actions:
        spec = importlib.util.spec_from_file_location('dx_action_state', ROOT / 'action_state.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        header = module.render_header(header)
    if regions:
        spec = importlib.util.spec_from_file_location('dx_region_state', ROOT / 'region_state.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        header = module.render_header(header)
    if image:
        spec = importlib.util.spec_from_file_location('dx_tile_image', ROOT / 'tile_image.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        header = module.render_header(header, source_tile_words=8, value_bound=6, byte_order='little')
    unit = tmp_path / 'model.c'
    unit.write_text('#include <assert.h>\n#include <stdint.h>\n#include <stdlib.h>\n#include <stdio.h>\n'
                    '#define DXM_CHECK(c,r) do { if (!(c)) { fputs(r,stderr); exit(42); } } while (0)\n'
                    'static unsigned chosen;\n'
                    'static unsigned choose_value(unsigned n) { assert(chosen < n); return chosen; }\n'
                    '#define DXM_CHOOSE(n) choose_value(n)\n'
                    + prelude + '\n' + header + '\n' + body)
    compiler = c_lowering.locate()
    assert not compiler.missing, compiler.missing
    exe = tmp_path / 'model.bin'
    command = [*compiler.command, '-x', 'c++' if cpp else 'c', '-std=c++17' if cpp else '-std=c11', '-O1', '-Wall', '-Werror',
               '-Wno-unused-function', '-fsanitize=address,undefined', '-MD', '-MF', str(tmp_path / 'model.d'),
               str(unit), '-o', str(exe)]
    built = subprocess.run(command,
                           capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30,
                         env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0', 'UBSAN_OPTIONS': 'halt_on_error=1'})
    dependencies = (tmp_path / 'model.d').read_text().replace('\\\n', '').split(':', 1)[1]
    (tmp_path / 'native-receipt.json').write_text(json.dumps({
        'compile_command': command, 'compiler_version': compiler.version, 'runtime_context': compiler_context(compiler),
        'compile_returncode': built.returncode, 'compile_stdout': built.stdout, 'compile_stderr': built.stderr,
        'native_command': [str(exe)], 'native_returncode': ran.returncode,
        'native_stdout': ran.stdout, 'native_stderr': ran.stderr,
        'expected_exit_code': exit_code, 'unit': file_pin(unit), 'executable': file_pin(exe),
        'headers': [file_pin(path) for path in sorted(set(shlex.split(dependencies)))]}, indent=2) + '\n')
    assert ran.returncode == exit_code, ran.stdout + ran.stderr
    return ran


def test_gather_interval_values_freeze_once_at_cover_and_never_include_preissue_values(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxm_reset(); chosen=pick;
    dxm_cpu_write(1, 7, 99);
    dxm_cpu_write(1, 7, 11);
    unsigned read=dxm_issue_read(0, 7);
    dxm_cpu_write(1, 7, 12);
    dxm_cover(read);
    uint64_t observed=dxm_value(read);
    assert(observed == (pick == 0 ? 11 : 12));
    dxm_cpu_write(1, 7, 13);
    assert(dxm_value(read) == observed);
  }
  return 0;
}
''')


def test_global_tile_ownership_rejects_another_thread_and_requires_both_8byte_halves(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxm_reset();
  dxm_claim_tile(0,2,4);
  dxm_use_tile(0,2,4);
  dxm_claim_tile(1,3,4);
  dxm_use_tile(1,3,4);
  dxm_use_tile(0,2,8);
  return 0;
}
''', exit_code=42)
    assert result.stderr == 'tile-ownership'


def test_pending_8byte_destination_blocks_cpu_read_of_its_second_half(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,2,8);
  unsigned root=dxm_constant(1);
  unsigned command=dxc_prepare(0,-1,0,0,4,0,dxc_tile_mask(2,8),0,0);
  dxc_bind(command,root);
  dxc_cpu_tile_access(0,3,4,0);
  return 0;
}
''', exit_code=42, commands=True)
    assert result.stderr == 'pending-tile-write'


@pytest.mark.parametrize('bytes,wait_tile,exit_code', [(8,2,0), (8,3,42), (4,3,0)])
def test_explicit_start_tile_wait_is_global_and_never_invents_a_second_half_wait(tmp_path, bytes, wait_tile, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,2,8);
  unsigned root=dxm_constant(1);
  unsigned command=dxc_prepare(0,-1,0,0,4,0,dxc_tile_mask(2,{bytes}),0,0);
  dxc_bind(command,root);
  dxc_wait_tile({wait_tile});
  dxc_cpu_tile_access(0,3,4,0);
  return 0;
}}
''', exit_code=exit_code, commands=True)
    assert result.stderr == ('pending-tile-write' if exit_code else '')


@pytest.mark.parametrize('target,exit_code', [(2,0),(3,42)])
def test_new_explicit_destination_stalls_prior_start_ids_but_never_aliases_an_8byte_half(tmp_path, target, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,2,8);
  unsigned root=dxm_constant(1);
  unsigned first=dxc_prepare(0,-1,0,0,4,0,dxc_tile_mask(2,8),0,0);
  dxc_bind(first,root);
  unsigned next=dxm_constant(7);
  unsigned second=dxc_prepare(0,-1,0,0,((uint64_t)1<<{target}),0,dxc_tile_mask({target},4),0,0);
  dxc_bind(second,next);
  dxc_cpu_tile_access(0,3,4,0);
  return 0;
}}
''', exit_code=exit_code, commands=True)
    assert result.stderr == ('pending-tile-write' if exit_code else '')


@pytest.mark.parametrize('access,region,exit_code', [(2,0,0), (1,0,42), (2,1,42)])
def test_region_stall_covers_cross_thread_conflicts_only_on_the_same_assigned_region(tmp_path, access, region, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); chosen=0;
  dxm_claim_tile(0,2,4); dxm_claim_tile(1,3,4);
  dxm_cpu_write(1,7,11);
  unsigned first=dxc_prepare(0,0,1,0,4,0,4,28,32);
  unsigned read=dxm_issue_read(0,7);
  dxc_bind(first,read);
  unsigned root=dxm_constant(1);
  unsigned second=dxc_prepare(1,{region},{access},8,0,8,0,36,40);
  dxc_bind(second,root);
  assert(dxm_value(read) == 11);
  return 0;
}}
''', exit_code=exit_code, commands=True)
    assert result.stderr == ('value-before-cover' if exit_code else '')


@pytest.mark.parametrize('thread', [0,1])
def test_store_hazards_cover_the_full_physical_line_for_cpu_reads_from_either_thread(tmp_path, thread):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset();
  struct dxc_span line=dxc_store_span(64,4,64);
  assert(line.begin == 64 && line.end == 128);
  unsigned root=dxm_constant(9);
  unsigned command=dxc_prepare(0,0,2,0,0,0,0,line.begin,line.end);
  dxc_bind(command,root);
  dxc_cpu_memory_access({thread},96,100,0);
  return 0;
}}
''', exit_code=42, commands=True)
    assert result.stderr == 'store-footprint-cpu-access'


def test_read_read_overlap_and_other_thread_cas_keep_the_actual_interval_values(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxc_reset(); chosen=pick; dxm_claim_tile(0,2,4);
    dxm_cpu_write(1,7,1);
    unsigned command=dxc_prepare(0,0,1,0,4,0,4,28,32);
    unsigned read=dxm_issue_read(0,7);
    dxc_bind(command,read);
    assert(dxc_cpu_read(0,7,28,32) == 1);
    uint64_t expected=1;
    assert(dxc_cpu_cas(1,7,28,32,&expected,2) == 1);
    dxc_wait_tile(2);
    assert(dxm_value(read) == (pick == 0 ? 1 : 2));
  }
  return 0;
}
''', commands=True)


@pytest.mark.parametrize('answer,exit_code', [(0,42),(1,0)])
def test_ready_query_can_return_either_answer_and_only_one_covers(tmp_path, answer, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); chosen={answer}; dxm_claim_tile(0,2,4);
  unsigned root=dxm_constant(1);
  unsigned command=dxc_prepare(0,-1,0,0,4,0,4,0,0);
  dxc_bind(command,root);
  assert(dxc_get_tile_ready(2) == {answer});
  dxc_cpu_tile_access(0,2,4,0);
  return 0;
}}
''', exit_code=exit_code, commands=True)
    assert result.stderr == ('pending-tile-write' if exit_code else '')


def test_the_issuing_thread_cannot_write_an_unfinished_gather_cell(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxm_reset(); dxm_cpu_write(0,7,11);
  dxm_issue_read(0,7);
  dxm_cpu_write(0,7,12);
  return 0;
}
''', exit_code=42)
    assert result.stderr == 'same-thread-read-footprint-write'


def test_a_dependent_command_captures_the_producer_version_without_settling_it(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxm_reset(); chosen=pick;
    dxm_cpu_write(1,7,1);
    unsigned producer=dxm_issue_read(0,7);
    unsigned ten=dxm_constant(10);
    unsigned consumer=dxm_issue_binary(0,0,0,producer,ten);
    dxm_cpu_write(1,7,2);
    dxm_cover(consumer);
    uint64_t saved=dxm_value(consumer);
    assert(saved == (pick == 0 ? 11 : 12));
    dxm_cpu_write(1,7,3);
    dxm_cover(consumer);
    assert(dxm_value(consumer) == saved);
    assert(dxm_value(producer) == (pick == 0 ? 1 : 2));
  }
  return 0;
}
''', prelude=r'''
static uint64_t test_add(unsigned dtype, unsigned op, uint64_t a, uint64_t b) {
  assert(dtype == 0 && op == 0); return (uint32_t)a + (uint32_t)b;
}
#define DXM_EVAL(dtype,op,a,b) test_add(dtype,op,a,b)
''')


def test_consumer_completion_covers_its_producer_command_without_early_history_settlement(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxc_reset(); chosen=pick;
    dxm_claim_tile(0,2,4); dxm_claim_tile(0,3,4);
    dxm_cpu_write(1,7,1);
    unsigned producer=dxc_prepare(0,0,1,0,4,0,4,28,32);
    unsigned read=dxm_issue_read(0,7); dxc_bind(producer,read);
    unsigned consumer=dxc_prepare(0,-1,0,4,8,4,8,0,0);
    unsigned ten=dxm_constant(10);
    unsigned sum=dxm_issue_binary(0,0,0,read,ten); dxc_bind(consumer,sum);
    uint64_t expected=1; assert(dxc_cpu_cas(1,7,28,32,&expected,2));
    dxc_wait_tile(3);
    assert(dxm_value(sum) == (pick == 0 ? 11 : 12));
    dxc_cpu_tile_access(0,2,4,0); dxc_cpu_tile_access(0,3,4,0);
  }
  return 0;
}
''', commands=True, prelude=r'''
static uint64_t test_add(unsigned dtype, unsigned op, uint64_t a, uint64_t b) {
  assert(dtype == 0 && op == 0); return (uint32_t)a + (uint32_t)b;
}
#define DXM_EVAL(dtype,op,a,b) test_add(dtype,op,a,b)
''')


def test_unresolved_indices_capture_issue_memory_and_real_writes_without_placeholder_dereferences(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned index_pick=0; index_pick<2; ++index_pick) {
    for (unsigned data_pick=0; data_pick<2; ++data_pick) {
      dxm_reset(); choice_cursor=0; choices[0]=index_pick; choices[1]=data_pick;
      dxm_cpu_write(1,5,0);
      dxm_cpu_write(1,0,11); dxm_cpu_write(1,1,21);
      unsigned index=dxm_issue_read(0,5);
      unsigned gathered=dxm_issue_indexed_read(0,index,0,2);
      dxm_cpu_write(1,5,1);
      dxm_cpu_write(1,0,12); dxm_cpu_write(1,1,22);
      dxm_cover(gathered);
      uint64_t expected=index_pick == 0 ? (data_pick == 0 ? 11 : 12) : (data_pick == 0 ? 21 : 22);
      assert(dxm_value(gathered) == expected);
      dxm_cpu_write(1,0,99); dxm_cpu_write(1,1,99);
      assert(dxm_value(gathered) == expected);
    }
  }
  return 0;
}
''', prelude=r'''
static unsigned choices[2],choice_cursor;
static unsigned sequence_choice(unsigned n) {
  assert(choice_cursor < 2); unsigned pick=choices[choice_cursor++]; assert(pick<n); return pick;
}
#undef DXM_CHOOSE
#define DXM_CHOOSE(n) sequence_choice(n)
''')


@pytest.mark.parametrize('condition', [0,1])
def test_deferred_conditions_do_not_read_or_check_inactive_memory_operands(tmp_path, condition):
    run_model(tmp_path, f'''
int main(void) {{
  dxm_reset(); chosen=0;
  dxm_cpu_write(1,0,9);
  unsigned condition=dxm_constant({condition});
  unsigned index=dxm_constant({0 if condition else 99});
  unsigned loaded=dxm_issue_indexed_read(0,index,0,2);
  unsigned preserved=dxm_constant(44);
  unsigned result=dxm_select(0,condition,loaded,preserved);
  dxm_cover(result);
  assert(dxm_value(result) == {9 if condition else 44});
  return 0;
}}
''')


@pytest.mark.parametrize('dtype,lhs,rhs,result', [
    (0,'0xffffffff','2','1'), (1,'0xfffffffd','5','2'),
    (2,'0x3fc00000','0x40100000','0x40700000'),
    (3,'0xffffffffffffffff','2','1'), (4,'0xfffffffffffffffd','5','2'),
    (5,'0x3ff8000000000000','0x4002000000000000','0x400e000000000000')])
def test_deferred_numeric_values_keep_each_device_types_raw_representation(tmp_path, dtype, lhs, rhs, result):
    run_model(tmp_path, f'''
int main(void) {{
  dxm_reset();
  struct dx_num_runtime native_profile={{0,1,0}};
  dxt_set_runtime(native_profile);
  unsigned left=dxm_constant(UINT64_C({lhs})), right=dxm_constant(UINT64_C({rhs}));
  unsigned sum=dxt_binary(0,{dtype},0,left,right);
  dxm_cover(sum);
  assert(dxm_value(sum) == UINT64_C({result}));
  return 0;
}}
''', numeric=True)


@pytest.mark.parametrize('opcode,exit_code', [(0,0),(16,42)])
def test_inactive_arithmetic_skips_rte_but_cannot_hide_an_unsupported_source_opcode(tmp_path, opcode, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxm_reset();
  unsigned condition=dxm_constant(0), preserved=dxm_constant(7);
  unsigned left=dxm_constant(INT32_MAX), right=dxm_constant(1);
  unsigned operation=dxt_binary(0,1,{opcode},left,right);
  unsigned selected=dxm_select(0,condition,operation,preserved);
  dxm_cover(selected);
  assert(dxm_value(selected) == 7);
  return 0;
}}
''', numeric=True, exit_code=exit_code)
    assert result.stderr == ('numeric-opcode-domain' if exit_code else '')


def test_store_effect_waits_for_captured_producer_versions_and_preserves_history_choices(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxc_reset(); chosen=pick;
    dxm_claim_tile(0,2,4); dxm_claim_tile(0,3,4);
    dxm_cpu_write(1,7,1); dxm_cpu_write(1,0,99);
    unsigned producer=dxc_prepare(0,0,1,0,4,0,4,28,32);
    unsigned read=dxm_issue_read(0,7); dxc_bind(producer,read);
    unsigned alu=dxc_prepare(0,-1,0,4,8,4,8,0,0);
    unsigned ten=dxm_constant(10), sum=dxt_binary(0,0,0,read,ten); dxc_bind(alu,sum);
    unsigned store=dxc_prepare(0,1,2,8,0,8,0,64,128);
    unsigned index=dxm_constant(0), active=dxm_constant(1);
    unsigned effect=dxa_store(store,0,0,1,index,sum,active); dxc_bind(store,effect);
    uint64_t expected=1; assert(dxc_cpu_cas(1,7,28,32,&expected,2));
    dxc_wait_tile(3);
    assert(dxc_cpu_read(1,0,64,68) == (pick == 0 ? 11 : 12));
  }
  return 0;
}
''', commands=True, numeric=True, actions=True)


@pytest.mark.parametrize('active,old,updated', [(1,10,13),(0,77,10)])
def test_rmw_publishes_old_value_once_and_inactive_lanes_preserve_the_old_tile_payload(tmp_path, active, old, updated):
    run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); chosen=0;
  dxm_claim_tile(0,2,4); dxm_claim_tile(0,3,4);
  dxm_cpu_write(1,0,10);
  unsigned command=dxc_prepare(0,0,2,4,8,4,8,64,128);
  unsigned index=dxm_constant(0), value=dxm_constant(3), condition=dxm_constant({active});
  unsigned preserved=dxm_constant(77), old=dxm_result();
  unsigned root=dxa_rmw(command,0,0,0,1,index,value,condition,old,preserved); dxc_bind(command,root);
  dxc_wait_tile(3);
  assert(dxm_value(old) == {old});
  assert(dxc_cpu_read(1,0,64,68) == {updated});
  dxc_wait_tile(3);
  assert(dxm_value(old) == {old});
  assert(dxc_cpu_read(1,0,64,68) == {updated});
  return 0;
}}
''', commands=True, numeric=True, actions=True)


def test_different_regions_do_not_hide_device_conflicts_on_one_physical_store_line(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,2,4); dxm_claim_tile(1,3,4);
  unsigned first=dxc_prepare(0,0,2,4,0,4,0,64,128);
  dxc_bind(first,dxm_constant(1));
  unsigned second=dxc_prepare(1,1,1,0,8,0,8,96,100);
  dxc_bind(second,dxm_constant(2));
  return 0;
}
''', commands=True, exit_code=42)
    assert result.stderr == 'device-memory-footprint-conflict'


def test_duplicate_rmw_old_results_follow_progressive_copied_values_without_global_lane_order(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned first=0; first<2; ++first) {
    dxc_reset(); chosen=first; dxm_claim_tile(0,2,4); dxm_claim_tile(0,3,4);
    dxm_cpu_write(1,0,0);
    unsigned command=dxc_prepare(0,0,2,4,8,4,8,64,128);
    unsigned index=dxm_constant(0), one=dxm_constant(1), two=dxm_constant(2), active=dxm_constant(1);
    unsigned preserved=dxm_constant(77), old_a=dxm_result(), old_b=dxm_result();
    unsigned a=dxa_rmw(command,0,0,0,1,index,one,active,old_a,preserved);
    unsigned b=dxa_rmw(command,0,0,0,1,index,two,active,old_b,preserved);
    dxc_bind(command,dxm_join(a,b)); dxc_wait_tile(3);
    assert(dxc_cpu_read(1,0,64,68) == 3);
    assert(dxm_value(old_a) == (first == 0 ? 0 : 2));
    assert(dxm_value(old_b) == (first == 0 ? 1 : 0));
  }
  return 0;
}
''', commands=True, numeric=True, actions=True)


@pytest.mark.parametrize('end,exit_code', [(180,0),(230,42)])
def test_region_assignment_uses_first_matching_id_and_f2_checks_the_complete_logical_span(tmp_path, end, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset();
  dxr_add(0,100,200); dxr_add(1,120,180); dxr_add(2,220,300);
  assert(dxr_find(150) == 0); assert(dxr_find(250) == 2);
  int assigned=dxr_assign(121);
  assert(assigned == 0);
  dxr_check_span(assigned,120,{end});
  return 0;
}}
''', commands=True, regions=True, exit_code=exit_code)
    assert result.stderr == ('region-footprint-correspondence' if exit_code else '')


@pytest.mark.parametrize('base,index,bytes,address,exit_code', [
    ('64','1073741824',4,'64',42), ('64','3',8,'88',0),
    ('0xfffffffffffffffc','1',8,'4',0)])
def test_raw_device_offset_wrap_is_defined_and_array_correspondence_is_a_separate_checked_domain(tmp_path, base, index, bytes, address, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset();
  assert(dxr_device_address(UINT64_C({base}),UINT32_C({index}),{bytes}) == UINT64_C({address}));
  dxr_array_offset_correspondence(UINT32_C({index}),{bytes});
  return 0;
}}
''', commands=True, regions=True, exit_code=exit_code)
    assert result.stderr == ('index-offset-correspondence' if exit_code else '')


@pytest.mark.parametrize('separate,exit_code', [(0,0),(1,42)])
def test_logical_region_assignment_never_shrinks_the_full_physical_store_line(tmp_path, separate, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,2,4); dxm_claim_tile(1,3,4);
  if ({separate}) {{ dxr_add(0,64,68); dxr_add(1,96,100); }}
  else {{ dxr_add(0,64,128); }}
  unsigned store=dxr_prepare(0,2,64,64,68,4,0,4,0,64,128);
  dxc_bind(store,dxm_constant(1));
  unsigned read=dxr_prepare(1,1,96,96,100,0,8,0,8,96,100);
  dxc_bind(read,dxm_constant(2));
  dxc_cpu_memory_access(1,96,100,0);
  return 0;
}}
''', commands=True, regions=True, exit_code=exit_code)
    assert result.stderr == ('device-memory-footprint-conflict' if exit_code else '')


def test_typed_tile_views_share_physical_bytes_with_source_stride_and_freeze_captured_versions(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_cpu_write_bits(0,1,0,0,UINT64_C(0x55667788));
  dxp_cpu_write_bits(0,1,1,0,UINT64_C(0x11223344));
  assert(dxp_cpu_read_bits(0,1,0,3) == UINT64_C(0x1122334455667788));
  unsigned saved=dxp_capture_bits(1,0,3); dxm_cover(saved);
  dxp_cpu_write_bits(0,1,1,0,UINT64_C(0xaabbccdd));
  assert(dxm_value(saved) == UINT64_C(0x1122334455667788));
  assert(dxp_cpu_read_bits(0,1,0,3) == UINT64_C(0xaabbccdd55667788));
  /* Source stride8 words, model prefix6 values: lane4 crosses to physical t+1. */
  dxp_cpu_write_bits(0,1,4,3,UINT64_C(0x0102030405060708));
  assert(dxp_cpu_read_bits(0,2,0,0) == UINT64_C(0x05060708));
  assert(dxp_cpu_read_bits(0,2,1,0) == UINT64_C(0x01020304));
  return 0;
}
''', commands=True, image=True)


def test_all_six_typed_cpu_views_copy_bits_through_legal_scalar_objects(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_store_f32(0,1,0,1.5f);
  assert(dxp_load_u32(0,1,0) == UINT32_C(0x3fc00000));
  dxp_store_u32(0,1,0,UINT32_C(0xc0000000));
  assert(dxp_load_f32(0,1,0) == -2.0f);
  dxp_store_i32(0,1,0,-3);
  assert(dxp_load_u32(0,1,0) == UINT32_C(0xfffffffd));
  dxp_store_f64(0,1,0,1.5);
  assert(dxp_load_u64(0,1,0) == UINT64_C(0x3ff8000000000000));
  dxp_store_u64(0,1,0,UINT64_C(0xc000000000000000));
  assert(dxp_load_f64(0,1,0) == -2.0);
  dxp_store_i64(0,1,0,-3);
  assert(dxp_load_u64(0,1,0) == UINT64_C(0xfffffffffffffffd));
  return 0;
}
''', commands=True, image=True)


@pytest.mark.parametrize('bytes,exit_code', [(4,0),(8,42)])
def test_one_commands_distinct_start_ids_still_require_disjoint_physical_read_write_halves(tmp_path, bytes, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,1,8);
  unsigned command=dxc_prepare(0,-1,0,4,2,4,dxc_tile_mask(1,{bytes}),0,0);
  dxc_bind(command,dxm_constant(1));
  return 0;
}}
''', commands=True, exit_code=exit_code)
    assert result.stderr == ('intra-command-physical-alias' if exit_code else '')


def test_device_output_bytes_capture_unsettled_versions_across_64_to_32bit_consumers(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxc_reset(); chosen=pick;
    dxm_claim_tile(0,1,8); dxm_claim_tile(0,3,4);
    dxm_cpu_write(1,7,UINT64_C(0x1122334455667788));
    unsigned producer=dxc_prepare(0,0,1,0,2,0,dxc_tile_mask(1,8),56,64);
    unsigned read=dxm_issue_read(0,7);
    dxp_bind_output(producer,1,0,3,read); dxc_bind(producer,read);
    unsigned consumer=dxc_prepare(0,-1,0,2,8,2,8,0,0);
    unsigned input=dxp_capture_bits(1,0,0), one=dxm_constant(1);
    unsigned sum=dxt_binary(0,0,0,input,one);
    dxp_bind_output(consumer,3,0,0,sum); dxc_bind(consumer,sum);
    uint64_t expected=UINT64_C(0x1122334455667788);
    assert(dxc_cpu_cas(1,7,56,64,&expected,UINT64_C(0xaabbccdd01020304)));
    dxc_wait_tile(3);
    uint32_t result=pick == 0 ? UINT32_C(0x55667789) : UINT32_C(0x01020305);
    assert(dxp_load_u32(0,3,0) == result);
    dxp_store_u64(0,1,0,0);
    assert(dxp_load_u32(0,3,0) == result);
  }
  return 0;
}
''', commands=True, numeric=True, image=True)


def test_typed_image_does_not_invent_initial_values(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_store_u32(0,1,0,7);
  (void)dxp_load_u64(0,1,0);
  return 0;
}
''', commands=True, image=True, exit_code=42)
    assert result.stderr == 'tile-value-initialized'


@pytest.mark.parametrize('wide_output,expected', [(True, 'image-command-output-domain'), (False, 'pending-tile-write')])
def test_output_binding_and_cpu_views_enforce_the_same_physical_pair(tmp_path, wide_output, expected):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,1,8);
  unsigned root=dxm_constant(UINT64_C(0x1122334455667788));
  unsigned command=dxc_prepare(0,-1,0,0,2,0,{2 if wide_output else 6},0,0);
  dxp_bind_output(command,1,0,3,root);
  dxc_bind(command,root);
  (void)dxp_load_u32(0,2,0);
  return 0;
}}
''', commands=True, image=True, exit_code=42)
    assert result.stderr == expected


def test_sparse_image_capacity_refuses_before_partial_wide_installation(tmp_path):
    result = run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_store_u64(0,1,0,7);
  return 0;
}
''', commands=True, image=True, prelude='#define DXP_IMAGE_BYTES 4\n', exit_code=42)
    assert result.stderr == 'tile-image-capacity'


def test_typed_image_scalar_memcpy_views_also_compile_as_cpp17(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_store_f64(0,1,0,-0.0);
  assert(dxp_load_u64(0,1,0) == UINT64_C(0x8000000000000000));
  dxp_store_i64(0,1,0,INT64_MIN);
  assert(dxp_load_i64(0,1,0) == INT64_MIN);
  dxp_store_f32(0,1,0,-0.0f);
  assert(dxp_load_u32(0,1,0) == UINT32_C(0x80000000));
  return 0;
}
''', commands=True, image=True, cpp=True)


@pytest.mark.parametrize('observe,exit_code', [(False, 0), (True, 42)])
def test_inactive_rmw_preserves_undefined_tile_bytes_without_reading_them_at_completion(tmp_path, observe, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); chosen=0;
  dxm_claim_tile(0,1,4); dxm_claim_tile(0,2,4);
  dxm_cpu_write(1,0,10);
  unsigned command=dxc_prepare(0,0,2,2,4,2,4,64,128);
  unsigned inactive=dxm_constant(0), unused=dxm_result();
  unsigned preserved=dxp_capture_bits(2,0,0), old=dxm_result();
  unsigned root=dxa_rmw(command,0,0,0,1,unused,unused,inactive,old,preserved);
  dxp_bind_output(command,2,0,0,old); dxc_bind(command,root);
  dxc_wait_tile(2);
  assert(dxc_cpu_read(1,0,64,68) == 10);
  puts("COVERED");
  {'(void)dxp_load_u32(0,2,0);' if observe else ''}
  return 0;
}}
''', commands=True, numeric=True, actions=True, image=True, exit_code=exit_code)
    assert result.stdout == 'COVERED\n'
    assert result.stderr == ('tile-value-initialized' if observe else '')


@pytest.mark.parametrize('active,wide_read,exit_code', [(0,False,0),(0,True,42),(1,True,0)])
def test_conditional_output_preserves_initializedness_independently_for_each_physical_byte(tmp_path, active, wide_read, exit_code):
    result = run_model(tmp_path, f'''
int main(void) {{
  dxc_reset(); dxm_claim_tile(0,1,8);
  dxp_store_u32(0,1,0,UINT32_C(0x12345678));
  unsigned command=dxc_prepare(0,-1,0,0,2,0,6,0,0);
  unsigned condition=dxm_constant({active});
  unsigned payload={f'dxm_constant(UINT64_C(0xaabbccdd55667788))' if active else 'dxm_result()'};
  unsigned root=dxm_select(0,condition,payload,dxm_constant(0));
  dxp_bind_conditional_output(command,1,0,3,condition,payload); dxc_bind(command,root);
  dxc_wait_tile(1); puts("COVERED");
  assert(dxp_load_u32(0,1,0) == UINT32_C({0x55667788 if active else 0x12345678}));
  {'assert(dxp_load_u64(0,1,0) == UINT64_C(0xaabbccdd55667788));' if wide_read else ''}
  return 0;
}}
''', commands=True, image=True, exit_code=exit_code)
    assert result.stdout == 'COVERED\n'
    assert result.stderr == ('tile-value-initialized' if exit_code else '')


def test_failed_cas_expected_and_desired_values_do_not_enter_gather_history(tmp_path):
    run_model(tmp_path, r'''
int main(void) {
  for (unsigned pick=0; pick<2; ++pick) {
    dxm_reset(); chosen=pick;
    dxm_cpu_write(1,7,1);
    unsigned read=dxm_issue_read(0,7);
    uint64_t expected=99;
    assert(dxm_cpu_cas(1,7,&expected,77) == 0);
    assert(expected == 1);
    assert(dxm_cpu_cas(1,7,&expected,2) == 1);
    dxm_cover(read);
    assert(dxm_value(read) == (pick == 0 ? 1 : 2));
  }
  return 0;
}
''')

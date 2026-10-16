"""2026-10-15 ET. Public lower seam prerequisite to ticket28 typed prove controls.

Compiler/native behavior only. No formal verifier or accelerator theorem here.
"""
import json
import os
import subprocess

import pytest

from conftest import run_swdb


def test_typed_initialized_and_uninitialized_register_allocation_keep_distinct_call_abis(tmp_path):
    source = tmp_path / 'typed_calls.cc'
    source.write_text('''template<class T> int get_new_reg();
template<class T> int get_new_reg(T value);
int allocation_pair() {
  int first = get_new_reg<int>();
  int second = get_new_reg<int>(3);
  return first + second;
}
''')
    result = run_swdb('lower', '--source', source, '--function', 'allocation_pair',
                      '--summary', 'get_new_reg=semantics.dx100_0_2', '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    lowered = json.loads(result.stdout)
    assert {row['c_name'] for row in lowered['summaries']} == {'get_new_reg_int_args0', 'get_new_reg_int_args1'}
    text = (tmp_path / 'out/allocation_pair.c').read_text()
    assert 'get_new_reg_int_args0(void)' in text and 'get_new_reg_int_args1(int value)' in text
    assert 'get_new_reg_int_args0()' in text and 'get_new_reg_int_args1(3)' in text


def test_zero_argument_template_calls_keep_each_actual_device_type_binding(tmp_path):
    source = tmp_path / 'typed_zero_arguments.cc'
    source.write_text('''template<class T> int get_data_type();
int device_types() {
  int a = get_data_type<unsigned int>();
  int b = get_data_type<int>();
  int c = get_data_type<float>();
  int d = get_data_type<unsigned long>();
  int e = get_data_type<long>();
  int f = get_data_type<double>();
  return a + b + c + d + e + f;
}
''')
    result = run_swdb('lower', '--source', source, '--function', 'device_types',
                      '--summary', 'get_data_type=semantics.dx100_0_2', '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    lowered = json.loads(result.stdout)
    assert {row['c_name'] for row in lowered['summaries']} == {
        'get_data_type_unsigned_int', 'get_data_type_int', 'get_data_type_float',
        'get_data_type_unsigned_long', 'get_data_type_long', 'get_data_type_double'}


def test_defined_zero_argument_templates_keep_their_values_in_native_cpp_and_lowered_c(tmp_path):
    from swdb import c_lowering
    source = tmp_path / 'type_widths.cc'
    source.write_text('''template<class T> int type_width() { return sizeof(T); }
int all_widths() {
  return type_width<unsigned int>() + type_width<int>() + type_width<float>()
       + type_width<unsigned long>() + type_width<long>() + type_width<double>();
}
''')
    result = run_swdb('lower', '--source', source, '--function', 'all_widths',
                      '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    compiler = c_lowering.locate()
    assert not compiler.missing, compiler.missing
    main = '\nint main(void) { return all_widths() == 36 ? 0 : 1; }\n'
    for language, standard, text in [('c++', 'c++17', source.read_text()),
                                     ('c', 'c11', (tmp_path / 'out/all_widths.c').read_text())]:
        unit = tmp_path / (language + '.txt')
        unit.write_text(text + main)
        executable = tmp_path / (language + '.bin')
        built = subprocess.run([*compiler.command, '-x', language, '-std=' + standard, '-O1',
                                '-fsanitize=address,undefined', str(unit), '-o', str(executable)],
                               capture_output=True, text=True, timeout=60)
        assert built.returncode == 0, built.stderr
        ran = subprocess.run([str(executable)], capture_output=True, text=True, timeout=60,
                             env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0', 'UBSAN_OPTIONS': 'halt_on_error=1'})
        assert ran.returncode == 0, ran.stdout + ran.stderr


def test_a_shared_template_body_binds_calls_in_each_instantiated_owner(tmp_path):
    source = tmp_path / 'nested_template_calls.cc'
    source.write_text('''template<class T> int get_data_type();
template<class T> int read_type() { return get_data_type<T>(); }
int nested_types() { return read_type<int>() + read_type<double>(); }
''')
    result = run_swdb('lower', '--source', source, '--function', 'nested_types',
                      '--summary', 'get_data_type=semantics.dx100_0_2', '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    assert {r['c_name'] for r in json.loads(result.stdout)['summaries']} == {
        'get_data_type_int', 'get_data_type_double'}


@pytest.mark.parametrize('first,second', [('get_new_reg<int>()', 'get_new_reg<int>(3)'),
                                        ('get_new_reg<int>(3)', 'get_new_reg<int>()')])
def test_register_overload_names_are_independent_of_first_use_order(tmp_path, first, second):
    source = tmp_path / 'allocation_order.cc'
    source.write_text('template<class T> int get_new_reg();\ntemplate<class T> int get_new_reg(T value);\n'
                      f'int pair_order() {{ int a = {first}; int b = {second}; return a + b; }}\n')
    result = run_swdb('lower', '--source', source, '--function', 'pair_order',
                      '--summary', 'get_new_reg=semantics.dx100_0_2', '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    assert {r['c_name'] for r in json.loads(result.stdout)['summaries']} == {
        'get_new_reg_int_args0', 'get_new_reg_int_args1'}

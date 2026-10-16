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


@pytest.mark.parametrize('alias, outer', [('uint64_t', 'unsigned long long'), ('int32_t', 'int')])
@pytest.mark.parametrize('placement', ['local', 'return', 'field', 'cast', 'summary'])
def test_a_local_shadow_of_a_fixed_width_typedef_preserves_its_actual_scalar_type(tmp_path, alias, outer, placement):
    """Same width is insufficient: local typedefs can denote floating types."""
    from swdb import c_lowering
    source = tmp_path / 'shadowed_device_typedef.cc'
    source.write_text(f'typedef {outer} {alias};\n'
                      f'int shadowed_type() {{ typedef double {alias}; {alias} x = 0.5; return x == 0.5; }}\n')
    if placement == 'return':
        source.write_text(f'typedef double {alias};\n'
                          f'{alias} identity_value({alias} x) {{ return x; }}\n'
                          'int shadowed_type() { return identity_value(0.5) == 0.5; }\n')
    elif placement == 'field':
        source.write_text(f'typedef double {alias};\nstruct Cell {{ {alias} x; }};\n'
                          'int shadowed_type() { Cell c; c.x = 0.5; return c.x == 0.5; }\n')
    elif placement == 'cast':
        source.write_text(f'typedef double {alias};\n'
                          f'int shadowed_type() {{ return ({alias})0.5 == 0.5; }}\n')
    elif placement == 'summary':
        source.write_text(f'typedef double {alias};\n{alias} identity_value({alias} x);\n'
                          'int shadowed_type() { return identity_value(0.5) == 0.5; }\n')
    summary = ['--summary', 'identity_value=contract.typedef_fixture'] if placement == 'summary' else []
    result = run_swdb('lower', '--source', source, '--function', 'shadowed_type',
                      '--out', tmp_path / 'out', '--format', 'json', *summary)
    assert result.returncode == 0, result.stdout + result.stderr
    compiler = c_lowering.locate()
    for language, standard, text in [('c++', 'c++17', source.read_text()),
                                     ('c', 'c11', (tmp_path / 'out/shadowed_type.c').read_text())]:
        unit = tmp_path / (language + '.txt')
        helper = '\ndouble identity_value(double x) { return x; }\n' if placement == 'summary' else ''
        unit.write_text(text + helper + '\nint main(void) { return shadowed_type() == 1 ? 0 : 1; }\n')
        executable = tmp_path / (language + '.bin')
        built = subprocess.run([*compiler.command, '-x', language, '-std=' + standard, '-O1',
                                '-fsanitize=address,undefined', str(unit), '-o', str(executable)],
                               capture_output=True, text=True, timeout=60)
        assert built.returncode == 0, built.stderr
        ran = subprocess.run([str(executable)], capture_output=True, text=True, timeout=60,
                             env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0', 'UBSAN_OPTIONS': 'halt_on_error=1'})
        assert ran.returncode == 0, (language, text, ran.stdout, ran.stderr)


def test_ambiguous_unresolved_fixed_width_aliases_refuse_without_a_partial_lowering(tmp_path):
    source = tmp_path / 'ambiguous_typedef.cc'
    source.write_text('typedef double uint64_t;\n'
                      'uint64_t identity_value() { typedef unsigned int uint64_t; return 0.5; }\n'
                      'int result() { return identity_value() == 0.5; }\n')
    result = run_swdb('lower', '--source', source, '--function', 'result',
                      '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode != 0 and 'source typedef identity' in result.stderr
    assert not list((tmp_path / 'out').glob('*.c'))


def test_a_member_return_type_cannot_choose_an_unrelated_same_named_typedef(tmp_path):
    source = tmp_path / 'member_typedef.cc'
    source.write_text('typedef int Alias;\nstruct Cell { int pad; typedef double Alias; Alias value() { return 0.5; } };\n'
                      'int result() { Cell c; return c.value() == 0.5; }\n')
    result = run_swdb('lower', '--source', source, '--function', 'result',
                      '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode != 0 and 'ambiguous source typedef identity' in result.stderr, result.stdout + result.stderr
    assert not list((tmp_path / 'out').glob('*.c'))


@pytest.mark.parametrize('placement', ['parameter', 'return', 'local'])
def test_reference_typedefs_require_explicit_source_reference_binding(tmp_path, placement):
    source = tmp_path / 'reference_typedef.cc'
    body = {
        'parameter': 'int result(Ref n) { return n == 0; }',
        'return': 'Ref identity(int &n) { return n; } int result(int &n) { return identity(n) == 0; }',
        'local': 'int result(int n) { Ref r = n; return r == 0; }',
    }[placement]
    source.write_text('typedef int &Ref;\n' + body + '\n')
    result = run_swdb('lower', '--source', source, '--function', 'result',
                      '--out', tmp_path / 'out', '--format', 'json')
    assert result.returncode != 0 and 'reference typedef' in result.stderr, result.stdout + result.stderr
    assert not list((tmp_path / 'out').glob('*.c'))

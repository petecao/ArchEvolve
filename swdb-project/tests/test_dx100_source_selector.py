"""2026-10-16 ET. First public source-bound selector vertical, scripted tools only."""
import hashlib
import json

import yaml
import pytest

from conftest import REPO
from testkit.dx100_trust import run_semantics_fixture
from testkit.dx100_selector import selector_row, prove_selector


def test_public_prove_binds_the_real_header_u32_selector_before_any_scripted_wp_attempt(tmp_path):
    header = REPO / 'apps/dx100/benchmarks/API/MAA_gem5.hpp'
    source = '#include '+json.dumps(str(header))+'\nint trust_fixture(int *p) { (void)p; return (int)get_data_type<uint32_t>(); }\n'
    result, records, _entry, _marker = run_semantics_fixture(
        tmp_path, 'wp', source=source, extra_calls=[selector_row()],
        source_files={'gem5/m5ops.h': '#pragma once\n#include <stdint.h>\n'
                      'extern "C" void m5_add_mem_region(void*,void*,uint64_t);\n'
                      'extern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == 0;')
    assert result.returncode == 0, result.stdout+result.stderr
    record = yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['verdict'] == 'not_proven'  # No actual formal tool is run by this control.
    binding = record['settings']['proof_semantics']['instances'][0]['definition']
    assert binding['kind'] == 'dx100-get-data-type-u32-v1' and binding['value'] == 0
    assert binding['arguments'] == ['unsigned int']
    assert binding['source_mangled'] and binding['source_sha256'] == hashlib.sha256(source.encode()).hexdigest()
    assert 'ret i32 0' in binding['llvm_function']
    assert record['settings']['verifier_launched'] is True and _marker.exists()
    assert record['failure_class'] == 'tool_crash'  # Deliberate stand-in exit99.


@pytest.mark.parametrize('change,reason', [
    ('wrong_type','no proof-semantics template instance'),
    ('impostor','does not originate in the pinned MMIO header'),
    ('declaration','requires the real pinned definition'),
    ('trait_macro','does not fold to UINT32_TYPE0: ret i32 6'),
    ('include_level','does not fold to UINT32_TYPE0: ret i32 6'),
    ('optimizer_macro','does not fold to UINT32_TYPE0: ret i32 6'),
])
def test_public_source_selector_refuses_wrong_type_impostor_declaration_and_effective_trait_change(tmp_path, change, reason):
    header = REPO / 'apps/dx100/benchmarks/API/MAA_gem5.hpp'
    prefix = '#include '+json.dumps(str(header))+'\n'
    argument = 'double' if change == 'wrong_type' else 'unsigned int'
    if change in ('impostor','declaration'):
        prefix = ('enum class DataType : unsigned char { UINT32_TYPE=0 };\n'
                  'template<class T> DataType get_data_type()')
        prefix += ';\n' if change == 'declaration' else ' { return DataType::UINT32_TYPE; }\n'
    elif change in ('trait_macro','include_level','optimizer_macro'):
        condition = {'trait_macro':'1','include_level':'__INCLUDE_LEVEL__ == 0','optimizer_macro':'!defined(__OPTIMIZE__)'}[change]
        prefix = ('#include '+json.dumps(str(header.with_name('MAA.hpp')))+'\n#if '+condition+'\n'
                  '#define is_same is_base_of\n#endif\n#include '+json.dumps(str(header))+'\n#undef is_same\n')
    source = prefix+'int trust_fixture(int *p) { (void)p; return (int)get_data_type<'+argument+'>(); }\n'
    result, records, _entry, marker = run_semantics_fixture(
        tmp_path, 'wp', source=source, extra_calls=[selector_row()],
        source_files={'gem5/m5ops.h': '#pragma once\n#include <stdint.h>\n'
                      'extern "C" void m5_add_mem_region(void*,void*,uint64_t);\n'
                      'extern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == 0;')
    assert result.returncode == 1 and reason in result.stderr, result.stdout+result.stderr
    assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))


def test_fixture_only_unsupported_call_is_refused_before_the_compiler_definition_certificate(tmp_path):
    row = selector_row(); row['supported'] = False
    header = REPO / 'apps/dx100/benchmarks/API/MAA_gem5.hpp'
    source = '#include '+json.dumps(str(header))+'\nint trust_fixture(int *p) { (void)p; return (int)get_data_type<uint32_t>(); }\n'
    result, records, _entry, marker = run_semantics_fixture(
        tmp_path, 'wp', source=source, extra_calls=[row],
        source_files={'gem5/m5ops.h': '#pragma once\n#include <stdint.h>\n'
                      'extern "C" void m5_add_mem_region(void*,void*,uint64_t);\n'
                      'extern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == 0;')
    assert result.returncode == 1 and 'proof-semantics explicitly refuses get_data_type' in result.stderr, result.stdout+result.stderr
    assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))


def test_fixture_only_pure_layout_has_no_device_entry_premises_or_timing_reduction(tmp_path):
    from testkit.dx100_selector import pure_selector
    header = REPO / 'apps/dx100/benchmarks/API/MAA_gem5.hpp'
    source = '#include '+json.dumps(str(header))+'\nint trust_fixture(int *p) { (void)p; return (int)get_data_type<uint32_t>(); }\n'
    result, records, entry, marker = run_semantics_fixture(
        tmp_path, 'wp', source=source, semantics_transform=pure_selector,
        source_files={'gem5/m5ops.h': '#pragma once\n#include <stdint.h>\n'
                      'extern "C" void m5_add_mem_region(void*,void*,uint64_t);\n'
                      'extern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == 0;')
    assert result.returncode == 0, result.stdout+result.stderr
    record = yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['failure_class']=='tool_crash' and marker.exists()
    assert record['settings']['proof_semantics']['unit_requires']==[]
    assert not [a for a in record['assumptions'] if a['kind'] in ('reduction','assumed_clause')]
    assert not any('as if it finished at issue' in a['sentence'] for a in record['assumptions'])
    assert len(yaml.safe_load(entry.read_text())['declaration_inventory']['declarations'])==27


@pytest.mark.parametrize('change', ['wrong_result','wrong_abi'])
def test_source_definition_policy_cannot_certify_a_different_model_contract(tmp_path, change):
    row=selector_row()
    if change=='wrong_result':
        row['instances'][0]['contract']=r'assigns \nothing; ensures \result == 1;'
    else:
        row['instances'][0]['prototype']='int get_data_type_unsigned_int(void)'
    result, records, _entry, marker = run_semantics_fixture(tmp_path,'wp',extra_calls=[row])
    assert result.returncode==1 and 'exact u32 selector prototype and contract' in result.stderr, result.stdout+result.stderr
    assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))


@pytest.mark.parametrize('change,reason', [
    ('device_call','only the single certified u32 selector'),
    ('entry_premise','no device constants, queries or WP premises'),
    ('missing_inventory','complete declarations'),
    ('state','no ghost/device state or logic axioms'),
    ('logic','no ghost/device state or logic axioms'),
    ('model','exact constant selector C body'),
    ('bad_supported','supported must be a boolean'),
])
def test_stateless_layout_does_not_bypass_device_or_logic_admission(tmp_path,change,reason):
    from testkit.dx100_selector import pure_selector
    def changed(data,library):
        pure_selector(data,library)
        if change=='device_call':
            next(r for r in data['calls'] if r['call']=='maa_const')['supported']=True
        elif change=='entry_premise':
            data['wp']={'unit_requires':r'\false'}
        elif change=='missing_inventory':
            del data['declaration_inventory']
        elif change=='bad_supported':
            data['calls'][0]['supported']='false'
        else:
            key={'state':'state','logic':'logic','model':'c'}[change]
            pin=data['model'][key];path=library/pin['path']
            path.write_text({'state':'int fake_state;', 'logic':'axiom fake: 0 == 1;',
                             'model':'unsigned char get_data_type_unsigned_int(void) { return 1; }'}[change])
            pin['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    result,records,_entry,marker=run_semantics_fixture(tmp_path,'wp',semantics_transform=changed)
    assert result.returncode==1 and reason in result.stderr,result.stdout+result.stderr
    assert not marker.exists() and not list(records.path.glob('proofs/*.yaml'))



@pytest.mark.parametrize('expected', [0, 1], ids=['positive','wrong-enum'])
def test_first_gate_pair_uses_identical_source_and_records_its_exact_partial_scope(tmp_path, expected):
    from testkit.dx100_trust import TRUST
    result,records,entry,marker=prove_selector(tmp_path,expected)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['failure_class']=='tool_crash' and marker.exists()
    assert record['settings']['proof_semantics']['unit_requires']==[]
    assert record['settings']['proof_semantics']['unit_ensures']==[]
    assert record['proof_setup_check']['hashes']['dx100_source_selector']
    definition=record['settings']['proof_semantics']['instances'][0]['definition']
    assert hashlib.sha256(definition['preprocessed_source'].encode()).hexdigest()==definition['preprocessed_source_sha256']
    assert definition['preprocess_command'][-1]==definition['source_path']
    assert 'c++-cpp-output' in definition['compiler_command']
    old=entry.parent/'dx100_bfs_0_1.yaml'
    assert old.read_bytes()==(REPO/'library/proof_semantics/dx100_bfs_0_1.yaml').read_bytes()
    assert {r['reference']['id'].split('#')[-1] for r in record['assumptions'] if '#' in r['reference']['id']}==set(TRUST)
    assert not [r for r in record['assumptions'] if r['kind'] in ('reduction','assumed_clause')]

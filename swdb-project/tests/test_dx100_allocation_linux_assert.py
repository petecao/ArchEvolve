"""2026-10-16 ET. Public source qualification with captured glibc assert spelling.

Only compiler/public exit99 stand-in execution; no native program or proof.
"""
import json
from pathlib import Path
import pytest
import yaml
from conftest import REPO
from testkit.dx100_allocation import prove_allocation,CANONICAL_CALLER


def linux_assert_source(*,diagnostic='__extension__ __PRETTY_FUNCTION__',condition='static_cast<bool>(expr)'):
 return ('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA.hpp'))+'\n'
  +'extern "C" void __assert_fail(const char*,const char*,unsigned int,const char*) noexcept(true) __attribute__((noreturn));\n'
  +'#undef assert\n#define assert(expr) ('+condition+' ? void(0) : __assert_fail(#expr, __builtin_FILE(), __builtin_LINE(), '+diagnostic+'))\n'
  +'#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+CANONICAL_CALLER)


def test_public_original_total_allocator_accepts_pure_linux_assert_diagnostic(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102,source=linux_assert_source())
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert marker.exists()and record['verdict']=='not_proven'and record['failure_class']=='tool_crash'
 assert record['subject']=={'kind':'library_summary','id':'contract.dx100_software_allocation_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 assert settings['original_assigns_frame']==['REG_count','SPD_count','region_count']
 assert settings['correctness_scope']=='original total software-counter unit; no hardware progress premise'
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 assert r'terminates \false'not in Path(wp['path']).read_text()


@pytest.mark.parametrize('case',['increment','call','condition','wrong-signature'])
def test_public_allocator_does_not_erase_extension_effects_or_executable_wrappers(tmp_path,case):
 diagnostic={'increment':'__extension__ ((++SPD_count), __PRETTY_FUNCTION__)','call':'__extension__ __swdb_bad_diagnostic()'}.get(case,'__extension__ __PRETTY_FUNCTION__')
 source=linux_assert_source(diagnostic=diagnostic,condition='__extension__ static_cast<bool>(expr)'if case=='condition'else'static_cast<bool>(expr)')
 if case=='call':source='extern const char* __swdb_bad_diagnostic();\n'+source
 if case=='wrong-signature':source=source.replace('noexcept(true)','noexcept(false)')
 result,records,entry,marker=prove_allocation(tmp_path,102,source=source)
 assert result.returncode!=0,result.stdout+result.stderr
 assert 'allocator source assertion'in result.stdout+result.stderr
 assert not marker.exists()
 assert not list((tmp_path/'runs').glob('**/wp_input.c'))


def test_public_host_assertion_shape_remains_admitted_without_native_execution(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102)
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert marker.exists()and record['verdict']=='not_proven'and record['failure_class']=='tool_crash'

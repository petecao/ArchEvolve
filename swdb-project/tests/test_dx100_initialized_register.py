"""2026-10-16 ET. Public initialized-u32 normal-return source gate; no actual WP."""
import json
from pathlib import Path
import yaml
from testkit.dx100_initialized_register import prove_initialized_register


def test_public_initialized_u32_has_ordinary_prewrite_capacity_and_original_partial_frame(tmp_path):
 result,records,entry,marker=prove_initialized_register(tmp_path,711)
 assert result.returncode==0,result.stdout+result.stderr
 record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
 assert marker.exists()and record['verdict']=='not_proven'and record['failure_class']=='tool_crash'
 assert record['subject']=={'kind':'partial_library_summary','id':'contract.dx100_initialized_register_partial_fixture.v1'}
 settings=record['settings']['proof_semantics']
 assert settings['unit_requires']==[]and settings['unit_ensures']==[]
 wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
 text=Path(wp['path']).read_text()
 assert r'requires 0 <= REG_count <= 31;'in text
 assert 'get_new_reg_unsigned_int_args1(7' in text and 'get_new_reg_unsigned_int_args1(11' in text
 assert 'REG_count, SPD_count, region_count, __swdb_dx_reg_words[0..1]'in text
 assert r'terminates \false;'in text
 assert all(c['kind']=='dx100-initialized-u32-register-v1'for c in settings['source_definitions'])

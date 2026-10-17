"""2026-10-16 ET. Public closed stream source/certificate controls; no actual WP."""
import pytest

def test_public_stream_places_partial_policy_inside_combined_original_contract(tmp_path):
    import json,re,yaml
    from pathlib import Path
    from testkit.dx100_stream import prove_stream
    def combined(contract):
        contract['clauses'][0]['acsl']['text']=r'requires \true; assigns \nothing; ensures \result == 1;'
    result,records,entry,marker=prove_stream(tmp_path,1,contract_mutate=combined)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert marker.exists() and record['failure_class']=='tool_crash'
    wp=next(p for p in record['evidence']['reports'] if p.get('name')=='wp_input')
    text=Path(wp['path']).read_text()
    unit=next(m[1]for m in re.finditer(r'/\*@((?:(?!\*/).)+)\*/\s*int trust_fixture\(',text,re.S))
    # The original predicate and frame still appear, with terminates in its
    # grammar position even when all original clauses share one formal half.
    assert re.search(r'requires\s+\\true\s*;\s*terminates\s+\\false\s*;\s*assigns\s+__swdb_dx_stream_meta\s*;\s*ensures\s+\\result\s*==\s*1\s*;',unit),unit

def test_public_stream_refuses_missing_explicit_isolated_entry_certificate_before_adapter(tmp_path):
    from testkit.dx100_stream import prove_stream
    result,records,entry,marker=prove_stream(tmp_path,1,certificate=False)
    assert result.returncode!=0
    assert 'explicit isolated stream entry certificate' in result.stdout+result.stderr
    assert not marker.exists()


@pytest.mark.parametrize('expected',[1,0],ids=['correct-size','wrong-size'])
def test_public_stream_binds_source_entry_and_partial_return_before_scripted_adapter(tmp_path,expected):
    import json,yaml
    from testkit.dx100_stream import prove_stream,BOOT_STATEMENT,NORMAL_RETURN_STATEMENT,COMPRESSION_STATEMENT
    result,records,entry,marker=prove_stream(tmp_path,expected)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['verdict']=='not_proven' and record['failure_class']=='tool_crash'
    assert record['subject']=={'kind':'partial_library_summary','id':'contract.dx100_stream_partial_fixture.v1'}
    assert record['pins']['contract']['id']=='contract.dx100_stream_partial_fixture.v1'
    assert marker.exists(), 'external named exit99 stand-in only'
    assumptions=[a['sentence'] for a in record['assumptions']]
    assert all(s in assumptions for s in (BOOT_STATEMENT,NORMAL_RETURN_STATEMENT,COMPRESSION_STATEMENT))
    settings=record['settings']['proof_semantics']
    assert settings['unit_requires']==[] and settings['unit_ensures']==[]
    assert settings['termination_policy']=='conditional normal return; no hardware liveness'
    assert settings['unit_correctness_policy']['semantics']==record['pins']['proof_semantics']
    assert record['pins']['method_version']['id']=='method.dx100-stream-partial-fixture-v1'
    assert 'unverified' in settings['source_refinement']
    assert {c['call'] for c in settings['source_definitions']}=={'maa_stream_load','wait_ready','get_tile_size'}
    assert record['proof_setup_check']['hashes']['dx100_stream_source']
    # The named stand-in cannot type-check generated WP C. Compile that exact
    # public artifact separately, so void-result arithmetic cannot slip through.
    import subprocess
    from pathlib import Path
    from swdb import c_lowering
    wp=next(p for p in record['evidence']['reports'] if p.get('name')=='wp_input')
    command=[*c_lowering.locate().command,'-x','c','-std=c11','-fsyntax-only',wp['path']]
    compiled=subprocess.run(command,capture_output=True,text=True)
    (tmp_path/'wp-c-syntax-command.json').write_text(json.dumps(command,indent=2)+'\n')
    (tmp_path/'wp-c-syntax.stdout').write_text(compiled.stdout)
    (tmp_path/'wp-c-syntax.stderr').write_text(compiled.stderr)
    assert compiled.returncode==0,compiled.stdout+compiled.stderr
    text=Path(wp['path']).read_text()
    assert text.count(r'terminates \false;')==4
    # ACSL33 requires terminates after requires and before assigns/postconditions.
    # This checks emitted syntax order only; root owns the real parser gate.
    import re
    partial_blocks=[m[1]for m in re.finditer(r'/\*@(.+?)\*/',text,re.S)if r'terminates \false;'in m[1]]
    assert len(partial_blocks)==4
    ranks={'requires':0,'terminates':1,'assigns':2,'ensures':3}
    for block in partial_blocks:
        clauses=re.findall(r'\b(requires|terminates|assigns|ensures)\b',block)
        assert [ranks[c]for c in clauses]==sorted(ranks[c]for c in clauses),block
    assert 'unsigned int stream_input[16] = {7};' in text
    assert '(wait_ready(0) + 0)' not in text
    if expected==1:
        import copy,hashlib
        from types import SimpleNamespace
        from swdb import dx100_stream_source
        certificate=copy.deepcopy(settings['source_definitions'][0])
        function=certificate['operations']['stream']
        certificate['llvm_module']=certificate['llvm_module'].replace(function,function.replace('mfence;','nop;',1),1)
        certificate['llvm_module_sha256']=hashlib.sha256(certificate['llvm_module'].encode()).hexdigest()
        with pytest.raises(dx100_stream_source.Refused,match='compiled MMIO operation'):
            dx100_stream_source.recheck(SimpleNamespace(summaries=[{'semantic_source':certificate}]))


@pytest.mark.parametrize('change',["core_bool","rf_empty","line_element_only","virtual_zero","owner","model"])
def test_public_stream_refuses_changed_entry_environment_or_trusted_model_before_adapter(tmp_path,change):
    import hashlib
    from testkit.dx100_stream import prove_stream
    def mutate(data,library):
        rows=[r for r in data['calls'] if r.get('supported') is True]
        if change=='owner':
            next(r for r in data['rules'] if r['id']=='stream_event_compression')['assumed']['owner']='Unreviewed'
        elif change=='model':
            pin=data['model']['c'];path=library/pin['path']
            path.write_text(path.read_text().replace('int min=0,max=1,stride=1;','int min=0,max=0,stride=1;'))
            pin['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            for row in rows:
                definition=(row['instances'][0] if 'instances' in row else row)['definition']
                if change=='core_bool':definition['entry']['core']=False
                elif change=='rf_empty':definition['entry']['rf_i32']['1']=0
                elif change=='virtual_zero':definition['entry']['input']['nonzero_guest_base']=False
                else:definition['entry']['input']['bytes']=4
    result,records,entry,marker=prove_stream(tmp_path,1,mutate=mutate)
    assert result.returncode!=0,result.stdout+result.stderr
    assert ('isolated stream' in result.stdout+result.stderr)
    assert not marker.exists()


@pytest.mark.parametrize('change',["no_wait","unaligned_input","dead_source_ub"])
def test_public_stream_refuses_noncanonical_source_context_before_adapter(tmp_path,change):
    import json
    from conftest import REPO
    from testkit.dx100_stream import prove_stream
    prefix='#define __volatile__(...) __volatile__(__VA_ARGS__); (void)(1/0)\n' if change=='dead_source_ub' else ''
    source=(prefix+'#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'
        'alignas('+('4' if change=='unaligned_input' else '64')+') uint32_t stream_input[16]={7};\n'
        'int trust_fixture() { maa_stream_load<uint32_t>(stream_input,0,1,2,0,-1); '+
        ('' if change=='no_wait' else 'wait_ready(0); ')+
        'int observed=(int)get_tile_size(0); return observed; }\n')
    result,records,entry,marker=prove_stream(tmp_path,1,source=source)
    assert result.returncode!=0,result.stdout+result.stderr
    assert 'stream' in result.stdout+result.stderr
    assert not marker.exists()



def test_original_total_unit_cannot_receive_partial_contract_overlay_or_generic_proven_subject(tmp_path):
    import json,yaml
    from testkit.dx100_stream import prove_stream
    result,records,entry,marker=prove_stream(tmp_path,1,partial=False)
    assert not marker.exists(), 'original total request must be refused before external WP'
    if result.returncode==0:
        record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
        assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct'
    else:
        assert 'partial' in result.stdout+result.stderr


@pytest.mark.parametrize('change',['semantics_pin','source_policy','method'])
def test_partial_unit_refuses_changed_policy_or_unqualified_method_before_wp(tmp_path,change):
    import json,yaml
    from testkit.dx100_stream import prove_stream
    def mutate_contract(contract):
        policy=contract['proof_unit']['correctness_policy']
        if change=='semantics_pin':policy['semantics']['sha256']='0'*64
        elif change=='source_policy':policy['source_policy']='unqualified-total'
    def mutate_method(method):
        if change=='method':method['id']='method.original-total-fixture'
    result,records,entry,marker=prove_stream(tmp_path,1,contract_mutate=mutate_contract,method_mutate=mutate_method)
    assert not marker.exists()
    if result.returncode==0:
        record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
        assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct'
    else:assert 'partial' in result.stdout+result.stderr

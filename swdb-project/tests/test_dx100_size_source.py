"""2026-10-16 ET. Source-bound fresh-SPD size gate; native/scripted until admitted."""
import importlib

import pytest


def test_fresh_size_source_policy_is_an_explicit_closed_entry_not_an_implicit_default():
    size=importlib.import_module('swdb.dx100_size_source')
    assert size.LAYOUT=='dx100-fresh-spd-size-v1'
    assert size.CERTIFICATE_KIND=='synthetic-fresh-spd-core0-v1'
    with pytest.raises(size.Refused,match='fresh SPD constructor certificate'):
        size.constructor_projection(None)


def test_constructor_projection_has_no_desired_result_parameter_and_initializes_all_read_bytes():
    size=importlib.import_module('swdb.dx100_size_source')
    certificate={'kind':'synthetic-fresh-spd-core0-v1','core':0,'tiles':32,'tile_words':16384,
                 'guest_address_bits':64,'byte_order':'little','epoch':'after-constructor-and-address-setup-before-any-command'}
    projection=size.constructor_projection(certificate)
    assert projection['source_initial_values']=={'status':2,'size':0,'ready':0}
    assert projection['metadata_bytes']==64
    assert len(projection['entry_assignments'])==64
    assert all(' = 0;' in line for line in projection['entry_assignments'])
    assert 'requires' not in '\n'.join(projection['entry_assignments'])


def test_public_size_fixture_refuses_missing_fresh_constructor_certificate_before_any_adapter(tmp_path):
    from testkit.dx100_size import prove_size
    result,records,entry,marker=prove_size(tmp_path,0,certificate=False)
    assert result.returncode!=0
    assert 'fresh SPD constructor certificate' in result.stderr+result.stdout
    assert not marker.exists()


def test_public_size_fixture_binds_real_source_and_explicit_boot_epoch_before_scripted_adapter(tmp_path):
    import json
    import yaml
    from testkit.dx100_size import prove_size,BOOT_STATEMENT
    result,records,entry,marker=prove_size(tmp_path,0)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    assert record['verdict']=='not_proven' and record['failure_class']=='tool_crash'
    assert marker.exists(), 'external named exit99 stand-in only'
    assert any(a['sentence']==BOOT_STATEMENT for a in record['assumptions'])
    assert record['settings']['proof_semantics']['unit_requires']==[]
    assert record['proof_setup_check']['hashes']['dx100_size_source']


def test_native_exact_constructor_and_getsize_excerpts_agree_with_materialized_bytes(tmp_path):
    from testkit.dx100_size_native import run_constructor_projection
    run_constructor_projection(tmp_path)


def test_rehashed_frozen_ir_cannot_change_getter_semantics_after_source_binding(tmp_path):
    import copy,hashlib,json
    from types import SimpleNamespace
    import yaml
    from swdb import dx100_size_source
    from testkit.dx100_size import prove_size
    result,records,entry,marker=prove_size(tmp_path,0)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    certificate=copy.deepcopy(record['settings']['proof_semantics']['source_definitions'][0])
    ir=certificate['llvm_module'];function=certificate['llvm_function'];assert 'mfence;' in function
    certificate['llvm_module']=ir.replace(function,function.replace('mfence;','nop;',1),1)
    certificate['llvm_module_sha256']=hashlib.sha256(certificate['llvm_module'].encode()).hexdigest()
    with pytest.raises(dx100_size_source.Refused,match='compiled operation'):
        dx100_size_source.recheck(SimpleNamespace(summaries=[{'semantic_source':certificate}]))


@pytest.mark.parametrize('key,value',[('core',1),('core',False),('tiles',16),('tile_words',1024),
    ('guest_address_bits',32),('byte_order','big'),('epoch','after-init-MAA'),('desired_result',0)])
def test_constructor_certificate_refuses_other_epochs_geometries_or_desired_result_fields(key,value):
    from swdb import dx100_size_source as size
    certificate=dict(size.BOOT_CERTIFICATE);certificate[key]=value
    with pytest.raises(size.Refused,match='fresh SPD constructor certificate'):
        size.constructor_projection(certificate)


@pytest.mark.parametrize('change,reason',[
    ('owner','owned boot-epoch'),('statement','owned boot-epoch'),('source','changed or repeated source'),
    ('model','changed state/model'),('logic','no ghost state or added axioms'),('entry_premise','no extra constants'),
])
def test_public_size_layout_refuses_changed_trust_source_state_or_extra_premises(tmp_path,change,reason):
    import hashlib
    from testkit.dx100_size import prove_size
    def mutate(data,library):
        if change in ('owner','statement'):
            rule=next(r for r in data['rules'] if r['id']=='fresh_spd_epoch')
            if change=='owner':rule['assumed']['owner']='Unreviewed owner'
            else:rule['statement']='Every caller starts fresh.'
        elif change=='entry_premise':data['wp']={'unit_requires':'\\result == 0'}
        else:
            pin=(next(p for p in next(r for r in data['calls'] if r['call']=='get_tile_size')['definition']['sources'] if p['path'].endswith('/SPD.cc'))
                 if change=='source' else data['model']['c' if change=='model' else 'logic'])
            p=library/pin['path'];text=p.read_text()
            p.write_text(text+'\n// Changed source\n' if change=='source' else
                         text.replace('256U','1U') if change=='model' else 'axiom desired_result: 1 == 0;\n')
            pin['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    result,records,entry,marker=prove_size(tmp_path,0,mutate=mutate)
    assert result.returncode!=0
    assert reason in result.stderr+result.stdout
    assert not marker.exists()


@pytest.mark.parametrize('change,reason',[
    ('geometry','MMIO address setup/geometry'),('stride','MMIO address setup/geometry'),
    ('renamed_base','effective getter/caller tokens'),('fence','effective getter/caller tokens'),
    ('caller_write','leaves the closed boot epoch'),('caller_other_index','leaves the closed boot epoch'),
])
def test_public_size_source_refuses_other_effective_geometry_globals_fence_or_epoch_mutation(tmp_path,change,reason):
    import json
    from conftest import REPO
    from testkit.dx100_size import prove_size
    prefix={'geometry':'#define NUM_CORES 8\n','stride':'#define TILE_SIZE 1024\n',
            'renamed_base':'#define SPD_size_noncacheable renamed_size_base\n',
            'fence':'#define __volatile__\n'}.get(change,'')
    body=('int trust_fixture() { '+('SPD_size_noncacheable=(volatile uint16_t*)0; ' if change=='caller_write' else '')+
          'int observed=(int)get_tile_size('+('1' if change=='caller_other_index' else '0')+'); return observed; }\n')
    source=prefix+'#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'+body
    result,records,entry,marker=prove_size(tmp_path,0,source=source)
    assert result.returncode!=0
    assert reason in result.stderr+result.stdout
    assert not marker.exists()


@pytest.mark.parametrize('expected',[0,1],ids=['correct-size','wrong-size'])
def test_size_pair_keeps_identical_source_and_constructor_bytes_with_explicit_conditional_scope(tmp_path,expected):
    import hashlib,json
    import yaml
    from testkit.dx100_size import prove_size,BOOT_STATEMENT
    result,records,entry,marker=prove_size(tmp_path,expected)
    assert result.returncode==0,result.stdout+result.stderr
    record=yaml.safe_load((records.path/json.loads(result.stdout)['path']).read_text())
    settings=record['settings']['proof_semantics'];cert=settings['source_definitions'][0]
    assert settings['unit_requires']==[] and settings['unit_ensures']==[]
    assert settings['entry_projection']['bytes']==64 and settings['entry_projection']['statement']==BOOT_STATEMENT
    assert cert['entry']['core']==0 and cert['projection']['metadata_bytes']==64
    assert cert['source_mangled'].endswith('_Z13get_tile_sizei')
    assert record['proof_setup_check']['hashes']['dx100_size_source']!=hashlib.sha256(b'[]').hexdigest()
    assert record['verdict']=='not_proven' and record['failure_class']=='tool_crash' and marker.exists()
    assert any(a['sentence']==BOOT_STATEMENT for a in record['assumptions'])
    assert not any(a['kind']=='reduction' or 'as if it finished at issue' in a['sentence'] for a in record['assumptions'])
    reports=record['evidence']['reports'];wp=next(p for p in reports if p.get('name')=='wp_input' or p['path'].endswith('/wp_input.c'))
    text=__import__('pathlib').Path(wp['path']).read_text()
    assert text.count(' = 0;')>=64


def test_canonical_text_lure_cannot_hide_a_macro_argument_write_to_the_mmio_global(tmp_path):
    import json
    from conftest import REPO
    from testkit.dx100_size import prove_size
    canonical='int trust_fixture() { int observed=(int)get_tile_size(0); return observed; }'
    source=('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+'\n'
            'const char *unused_canonical_lure='+json.dumps(canonical)+';\n'
            '#define get_tile_size(id) get_tile_size((SPD_size_noncacheable=(volatile uint16_t*)0, (id)))\n'+canonical+'\n')
    result,records,entry,marker=prove_size(tmp_path,0,source=source)
    assert result.returncode!=0,result.stdout+result.stderr
    assert 'closed caller AST' in result.stderr+result.stdout
    assert not marker.exists()


def test_canonical_getter_text_lure_cannot_hide_macro_inserted_undefined_source_work(tmp_path):
    import json
    from conftest import REPO
    from testkit.dx100_size import prove_size
    api=REPO/'apps/dx100/benchmarks/API'
    getter=('inline volatile uint16_t get_tile_size(int SPD_id) { volatile uint16_t sz = '
            'SPD_size_noncacheable[SPD_id]; __asm__ __volatile__("mfence;"); return sz; }')
    source=('#include '+json.dumps(str(api/'MAA.hpp'))+'\n#include <atomic>\n#include <gem5/m5ops.h>\n'
            'const char *unused_getter_lure=R"lure('+getter+')lure";\n'
            '#define __volatile__(...) __volatile__(__VA_ARGS__); (void)(1 / 0)\n'
            '#include '+json.dumps(str(api/'MAA_gem5.hpp'))+'\n'
            'int trust_fixture() { int observed=(int)get_tile_size(0); return observed; }\n')
    result,records,entry,marker=prove_size(tmp_path,0,source=source)
    assert result.returncode!=0,result.stdout+result.stderr
    assert 'effective getter/caller tokens' in result.stderr+result.stdout
    assert not marker.exists()

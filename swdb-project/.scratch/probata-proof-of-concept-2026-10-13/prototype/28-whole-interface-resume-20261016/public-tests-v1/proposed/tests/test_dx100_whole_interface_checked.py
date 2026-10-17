"""2026-10-16 ET. Future quiet regressions; install after real fixture export.

This module uses actual Library/validate/current/portable-pin APIs. It has no
protocol tools, AST projections, fake Library, fabricated proof or skips.
"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import REPO,run_swdb
from swdb import dx100_whole_checked,paths,proof_semantics,yamlio
from swdb.library import Library
from testkit.dx100_whole_interface_checked import CALLS,LEGACY_SHA,portable_fixture

@pytest.fixture
def checked(tmp_path,monkeypatch):
    root=portable_fixture(REPO/'tests/fixtures/proof/dx100/whole-interface-checked',tmp_path)
    monkeypatch.setattr(paths,'HOME',root['project'])
    return root

def validate(root):
    return run_swdb('validate','--records',root['records'],'--library',root['library'],env=root['env'])

def test_quiet_normal_validate_and_current_use_the_real_new_0_2_entry(checked):
    result=validate(checked);assert result.returncode==0,result.stdout+result.stderr
    library=Library(checked['library']);assert not library.validate()
    current={key:row for key,row in proof_semantics.current(library).items() if row.get('target')=='dx100-mmio'}
    assert set(current)=={checked['manifest']['entry']['id']}
    entry=current[checked['manifest']['entry']['id']]
    assert entry['version']=='0.2' and dx100_whole_checked.checked(entry)
    binding=dx100_whole_checked.policy(library,entry)
    assert binding['source_admission_granted'] is False and binding['WP_summary_supported'] is False

def test_exact_whole_interface_contract_inventory_is_26_names_27_declarations_132_instances(checked):
    library=Library(checked['library']);entry=library.get(checked['manifest']['entry']['id'])
    binding=dx100_whole_checked.policy(library,entry)
    design=dx100_whole_checked.document(dx100_whole_checked.pinned(library,binding['design']))
    assert len(entry['calls'])==26 and {row['call'] for row in entry['calls']}==set(CALLS)
    assert entry['calls']==design['calls']
    assert sum(len(row['source_declarations']) for row in entry['calls'])==27
    assert sum(len(row['typed_arity_instances']) for row in entry['calls'])==132
    assert len(next(row for row in entry['calls'] if row['call']=='get_new_reg')['source_declarations'])==2
    assert all(row['contract']['asserted_domain_checks'] and row['contract']['normal_return_state_value_relation'] for row in entry['calls'])

@pytest.mark.parametrize('call',CALLS)
def test_each_named_call_contract_deletion_is_refused_by_normal_validate(checked,call):
    entry=yamlio.load(checked['entry']);entry['calls']=[row for row in entry['calls'] if row['call']!=call]
    checked['entry'].write_text(json.dumps(entry,sort_keys=True))
    result=validate(checked)
    assert result.returncode==1 and 'Traceback' not in result.stderr,result.stdout+result.stderr
    assert 'per-call contract' in result.stderr or 'contract inventory' in result.stderr,result.stderr

def test_old_0_1_bytes_remain_unchanged_and_are_still_present(checked):
    assert hashlib.sha256(checked['legacy'].read_bytes()).hexdigest()==LEGACY_SHA
    assert hashlib.sha256((REPO/'library/proof_semantics/dx100_bfs_0_1.yaml').read_bytes()).hexdigest()==LEGACY_SHA
    library=Library(checked['library']);old=library.get(checked['manifest']['legacy_entry']['id'])
    assert old['version']=='0.1' and not dx100_whole_checked.checked(old)
    before=checked['legacy'].read_bytes();result=validate(checked)
    assert result.returncode==0,result.stdout+result.stderr
    assert checked['legacy'].read_bytes()==before

def test_real_portable_alias_is_refused_before_Library_resolve_can_hide_it(checked):
    library=Library(checked['library']);entry=yamlio.load(checked['entry'])
    original=entry['checked_body']['components'][0];target=Path(library.resolve(original))
    base=checked['library'] if original['root']=='library' else checked['project']
    alias=base/'__checked_alias';alias.symlink_to(target.parent,target_is_directory=True)
    selected=dict(original,path='__checked_alias/'+target.name)
    assert library.resolve(selected)==target
    with pytest.raises(ValueError,match='physical directory|canonical|regular'):dx100_whole_checked.pinned(library,selected)
    entry['checked_body']['components'][0]=selected;checked['entry'].write_text(json.dumps(entry,sort_keys=True))
    result=validate(checked);assert result.returncode==1 and 'Traceback' not in result.stderr,result.stdout+result.stderr
    assert any(word in result.stderr for word in ('physical directory','canonical','regular')),result.stderr

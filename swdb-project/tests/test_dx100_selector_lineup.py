"""2026-10-16 ET. Explicit actual-only fixture pins; no tool discovery or proofs."""
import copy
import json

import pytest
import yaml

from conftest import FIXTURES
from testkit import dx100_selector as selector

KEY='SWDB_DX100_SELECTOR_ACTUAL_LINEUP'
LINUX={'frama-c-wp':'33.0','z3':'5.1.0','alt-ergo':'2.6.4','cvc5':'1.2.1'}


def fixture_method():
    return yaml.safe_load((FIXTURES/'proof/methods/contract-fixture-1.yaml').read_text())


def test_explicit_linux_binding_repairs_legacy_fixture_mismatch_without_changing_flags(tmp_path):
    method=fixture_method();before=copy.deepcopy(method)
    assert {r['tool']:r['version'] for r in method['lineup'] if r['tool'] in LINUX} != LINUX
    lineup=selector.read_actual_lineup({KEY:json.dumps(LINUX)})
    selector.bind_actual_lineup(method,lineup)
    assert {r['tool']:r['version'] for r in method['lineup'] if r['tool'] in LINUX} == LINUX
    for old,new in zip(before['lineup'],method['lineup']):
        assert {k:v for k,v in new.items() if k!='version'}=={k:v for k,v in old.items() if k!='version'}
        assert new['version']==(LINUX[old['tool']] if old['tool'] in LINUX else old['version'])
    path=tmp_path/'explicit-method.yaml';path.write_text(yaml.safe_dump(method))
    assert yaml.safe_load(path.read_text())==method


@pytest.mark.parametrize('payload',[
    None,'','null','[]','{}',json.dumps({'frama-c-wp':'33.0'}),
    json.dumps({**LINUX,'unknown':'1.0'}),json.dumps({**LINUX,'z3':None}),
    json.dumps({**LINUX,'z3':5.1}),json.dumps({**LINUX,'z3':True}),
    json.dumps({**LINUX,'z3':'5.1.0 trailing'}),json.dumps({**LINUX,'z3':' 5.1.0'}),
    json.dumps({**LINUX,'z3':'5.1'}),json.dumps({**LINUX,'frama-c-wp':'32.0'}),
    '{"frama-c-wp":"33.0","z3":"5.1.0","z3":"4.8.14","alt-ergo":"2.6.4","cvc5":"1.2.1"}',
])
def test_missing_malformed_partial_or_duplicate_actual_lineup_refuses(payload):
    with pytest.raises(ValueError,match='actual selector lineup'):
        selector.read_actual_lineup({} if payload is None else {KEY:payload})


def test_actual_mode_missing_lineup_refuses_before_fixture_or_compiler_work(tmp_path,monkeypatch):
    monkeypatch.delenv(KEY,raising=False)
    def forbidden(*args,**kwargs):
        pytest.fail('fixture/compiler work started before explicit actual lineup validation')
    monkeypatch.setattr('testkit.dx100_trust.run_semantics_fixture',forbidden)
    with pytest.raises(ValueError,match='actual selector lineup'):
        selector.prove_selector(tmp_path,0,actual=True)


def test_actual_mode_passes_explicit_versions_only_through_method_transform(tmp_path,monkeypatch):
    monkeypatch.setenv(KEY,json.dumps(LINUX))
    def capture(*args,**kwargs):
        method=fixture_method();kwargs['method_transform'](method)
        assert {r['tool']:r['version'] for r in method['lineup'] if r['tool'] in LINUX}==LINUX
        assert kwargs['tool_environment']=={}
        return 'captured'
    monkeypatch.setattr('testkit.dx100_trust.run_semantics_fixture',capture)
    assert selector.prove_selector(tmp_path,0,actual=True)=='captured'


def test_standin_mode_ignores_actual_binding_and_keeps_legacy_versions(tmp_path,monkeypatch):
    monkeypatch.setenv(KEY,'invalid unrelated actual-only setting')
    def capture(*args,**kwargs):
        assert kwargs.get('method_transform') is None
        assert kwargs['tool_environment'] is None
        assert {r['tool']:r['version'] for r in fixture_method()['lineup'] if r['tool'] in LINUX}=={
            'frama-c-wp':'33.0','z3':'4.8.14','alt-ergo':'2.6.0','cvc5':'1.2.1'}
        return 'captured'
    monkeypatch.setattr('testkit.dx100_trust.run_semantics_fixture',capture)
    assert selector.prove_selector(tmp_path,0)=='captured'


def test_separately_admitted_mac_lineup_remains_explicit_and_supported():
    mac={**LINUX,'z3':'4.8.14','alt-ergo':'2.6.0'}
    assert selector.read_actual_lineup({KEY:json.dumps(mac)})==mac


@pytest.mark.parametrize('problem',['missing','duplicate','wrong_role'])
def test_actual_lineup_binding_refuses_ambiguous_method_without_partial_mutation(problem):
    method=fixture_method()
    if problem=='missing':
        method['lineup']=[row for row in method['lineup'] if row['tool']!='z3']
    elif problem=='duplicate':
        method['lineup'].append(copy.deepcopy(next(row for row in method['lineup'] if row['tool']=='z3')))
    else:
        next(row for row in method['lineup'] if row['tool']=='z3')['role']='front_end'
    before=copy.deepcopy(method)
    with pytest.raises(ValueError,match='actual selector lineup'):
        selector.bind_actual_lineup(method,LINUX)
    assert method==before

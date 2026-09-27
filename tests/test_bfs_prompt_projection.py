"""Explicit worker-context projection; public synthetic-provider contracts. 2026-09-27 ET."""
import copy
import json
from pathlib import Path
import pytest
import yaml
from test_proposals import proposal_setup
from test_bfs_rewrite import provider
from swdb import artifacts, rewrite
from swdb.cli import Failure

METHOD='omit_unselected_strategy_catalog.v1'


def task(prompt):
    return json.loads(prompt[prompt.index('{"proposal":'):])


def test_public_projection_preserves_source_protections_full_package_and_chain(proposal_setup, provider):
    records,runs,snapshot,request=proposal_setup
    package=records.read('profile_packages/test-package.yaml')
    package['strategies']=[{'strategy':'selected','strategy_sha256':'a'*64,'effect':'keep'},
                           {'strategy':'other','strategy_sha256':'b'*64,'effect':'unrelated'}]
    records.write('profile_packages/test-package.yaml',package)
    original=copy.deepcopy(package)
    patch=yaml.safe_load(request().read_text())['payload']['content']
    path=request(strategy='selected',parameters={'prompt_projection':METHOD},
                 payload={'kind':'natural_language','content':'Use alpha14 only; preserve everything else.'})
    result=records.swdb('submit',path,'--provider-config',provider(patch),'--runs-dir',runs,'--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    proposal=json.loads(result.stdout)
    prompt=next(runs.rglob('prompt.txt')).read_text();projected=task(prompt)
    assert 'profile_package' not in projected
    assert projected['profile_package_context']['strategies']==original['strategies'][:1]
    assert {k:v for k,v in projected['profile_package_context'].items() if k!='strategies'}=={k:v for k,v in original.items() if k!='strategies'}
    assert projected['source_files']['src/bfs.cc']==(Path(snapshot['artifact']['path'])/'src/bfs.cc').read_text()
    assert projected['protected_inputs']==snapshot['protections']
    manifest=projected['prompt_projection']
    assert manifest['full_package']['record_sha256']==artifacts.digest(original)
    assert manifest['omitted_strategy_matches']==[{'index':1,'strategy':'other','sha256':artifacts.digest(original['strategies'][1])}]
    fresh=records.swdb('get',proposal['candidate'],'--chain','--format','json')
    assert fresh.returncode==0,fresh.stderr
    chain=json.loads(fresh.stdout)['records']
    assert chain['test-package']==original
    assert chain[proposal['id']]['request']==yaml.safe_load(path.read_text())
    assert chain[proposal['candidate']]['state']=='unverified'


@pytest.mark.parametrize('method',[None,{},'unknown'])
def test_unknown_opt_in_is_rejected_before_provider(proposal_setup,provider,method):
    records,runs,_,request=proposal_setup
    path=request(strategy='selected',parameters={'prompt_projection':method},payload={'kind':'natural_language','content':'Keep intent.'})
    result=records.swdb('submit',path,'--provider-config',provider(unresolved=['fixture']),'--runs-dir',runs,'--format','json')
    assert result.returncode==1
    assert 'prompt projection' in json.loads(result.stdout)['outcome']['reason']
    assert not list(runs.rglob('provider.json'))


def test_default_context_and_inputs_are_unchanged(proposal_setup):
    records,_,snapshot,request=proposal_setup
    envelope=yaml.safe_load(request(payload={'kind':'natural_language','content':'Keep intent.'}).read_text())
    package=records.read('profile_packages/test-package.yaml');before=copy.deepcopy((envelope,snapshot,package))
    rendered=task(rewrite.prompt_for(envelope,snapshot,package))
    assert rendered['profile_package']==package
    assert not {'profile_package_context','prompt_projection'}&set(rendered)
    assert (envelope,snapshot,package)==before


@pytest.mark.parametrize('fault',['missing-strategy','malformed-catalog','stale-package'])
def test_projection_rejects_ambiguous_or_changed_inputs(proposal_setup,fault):
    records,_,snapshot,request=proposal_setup
    envelope=yaml.safe_load(request(strategy='selected',parameters={'prompt_projection':METHOD},payload={'kind':'natural_language','content':'Keep intent.'}).read_text())
    package=records.read('profile_packages/test-package.yaml')
    if fault=='missing-strategy':envelope.pop('strategy')
    elif fault=='malformed-catalog':package['strategies']=[{'effect':'unknown strategy'}]
    else:package.update(package_version=1,requested_id='test-package',identity_sha256='a'*64)
    with pytest.raises((Failure,ValueError)):rewrite.prompt_for(envelope,snapshot,package)

"""Public bounded rewrite and repair contracts. Updated: 2026-09-25."""

import difflib
import json
import sys
from pathlib import Path

import pytest
import yaml

from test_proposals import proposal_setup
from test_bfs_native import evaluation_setup, evaluate


@pytest.fixture
def provider(tmp_path):
    program = tmp_path / 'provider.py'
    program.write_text('import json,sys,time\nfrom pathlib import Path\n'
                       'prompt=sys.stdin.read()\n'
                       'response=json.loads(Path(sys.argv[1]).read_text())\n'
                       'time.sleep(response.pop("sleep",0))\n'
                       'print(json.dumps(response))\n')
    def make(patch='', unresolved=None, **config):
        response = tmp_path / 'provider-response.json'
        response.write_text(json.dumps({'interpretation':'Apply the submitted parameter adjustment.',
                                        'patch':patch,'unresolved':unresolved or []}))
        path = tmp_path / 'provider.yaml'
        path.write_text(yaml.safe_dump({'kind':'external_fixture',
            'command':[sys.executable,str(program),str(response)],
            'timeout_s':10,'max_repairs':1,'total_seconds':30,**config}))
        return path
    return make


def patch_between(original, changed):
    return ''.join(difflib.unified_diff(original.splitlines(keepends=True), changed.splitlines(keepends=True),
                                      fromfile='a/src/bfs.cc',tofile='b/src/bfs.cc'))


@pytest.mark.parametrize('kind',['natural_language','structured_instructions','annotated_source'])
def test_real_source_edits_from_provider_output_are_durable(proposal_setup, provider, kind):
    records,runs,snapshot,request = proposal_setup
    patch = yaml.safe_load(request().read_text())['payload']['content']
    original = (Path(snapshot['artifact']['path'])/'src/bfs.cc').read_text()
    contents = {'natural_language':'Use alpha 14 instead of 15; preserve everything else.',
                'structured_instructions':{'parameter':'alpha','old':15,'new':14},
                'annotated_source':{'files':{'src/bfs.cc':original.replace('int alpha = 15',
                    '// Requested rewrite: change alpha from 15 to 14.\nint alpha = 15')}}}
    submitted = records.swdb('submit',request(payload={'kind':kind,'content':contents[kind]}),
                             '--provider-config',provider(patch),'--runs-dir',runs,'--format','json')
    assert submitted.returncode == 0, submitted.stderr
    proposal = json.loads(submitted.stdout)
    assert proposal['repair_budget']['repairs'] == 0
    assert proposal['repair_budget']['used_seconds'] > 0
    assert proposal['attempts'][0]['provider']['classification'] == 'contract_fixture'
    later = records.swdb('get',proposal['candidate'],'--chain','--format','json')
    assert later.returncode == 0, later.stderr
    chain = json.loads(later.stdout)['records']
    candidate = chain[proposal['candidate']]
    assert 'int alpha = 14' in (Path(candidate['artifact']['path'])/'src/bfs.cc').read_text()
    assert chain[proposal['id']]['request']['payload']['content'] == contents[kind]
    assert chain[proposal['id']]['interpretation']['patch'] == patch


def test_comments_only_annotation_is_retained_failure(proposal_setup, provider):
    records,runs,snapshot,request = proposal_setup
    original = (Path(snapshot['artifact']['path'])/'src/bfs.cc').read_text()
    annotated = '// Requested rewrite: change alpha from 15 to 14.\n'+original
    path = request(payload={'kind':'annotated_source','content':{'files':{'src/bfs.cc':annotated}}})
    result = records.swdb('submit',path,'--provider-config',provider(patch_between(original,annotated)),
                         '--runs-dir',runs,'--format','json')
    data = json.loads(result.stdout)
    assert result.returncode == 1
    assert 'only comments' in data['outcome']['reason']
    assert 'candidate' not in data
    assert records.swdb('get',data['id']).returncode == 0


def test_conflicting_intent_and_protected_annotation_fail(proposal_setup, provider):
    records,runs,snapshot,request = proposal_setup
    path = request(payload={'kind':'structured_instructions','content':{'alpha':[0,14]}})
    result = records.swdb('submit',path,'--provider-config',provider(unresolved=['conflicting alpha requirements']),
                         '--runs-dir',runs,'--format','json')
    data = json.loads(result.stdout)
    assert result.returncode == 1 and data['outcome']['state'] == 'unresolved'
    original = (Path(snapshot['artifact']['path'])/'src/bfs.cc').read_text()
    patched = original.replace('bool BFSVerifier','bool DisabledVerifier')
    path = request(id='protected-annotation',payload={'kind':'annotated_source',
                   'content':{'files':{'src/bfs.cc':'// Request: disable the verifier.\n'+original}}})
    result = records.swdb('submit',path,'--provider-config',provider(patch_between(original,patched)),
                         '--runs-dir',runs,'--format','json')
    assert result.returncode == 1
    assert 'protected' in json.loads(result.stdout)['outcome']['reason']


def test_provider_timeout_consumes_budget_and_retains_metadata(proposal_setup, provider):
    records,runs,_,request = proposal_setup
    config = provider(timeout_s=1)
    response = config.parent/'provider-response.json'
    data = json.loads(response.read_text()); data['sleep']=10; response.write_text(json.dumps(data))
    result = records.swdb('submit',request(payload={'kind':'natural_language','content':'Adjust alpha to 14.'}),
                         '--provider-config',config,'--runs-dir',runs,'--format','json')
    data = json.loads(result.stdout)
    assert result.returncode == 1
    assert data['repair_budget']['used_seconds'] >= 1
    assert data['attempts'][0]['provider']['state'] == 'interrupted_or_timeout'
    assert records.swdb('get',data['id']).returncode == 0


def test_supplied_patch_repair_keeps_failure_and_enforces_fixed_budget(evaluation_setup, provider):
    records,runs,request,base = evaluation_setup
    result, failed = evaluate(evaluation_setup,mode='build_fail')
    assert result.returncode == 1 and failed['outcome']['stage'] == 'build'
    retained = json.loads(records.swdb('get',base['candidate'],'--format','json').stdout)
    original = (Path(retained['artifact']['path'])/'src/bfs.cc').read_text()
    config = provider(patch_between(original,original.replace('int alpha = 14','int alpha = 13')))
    result = records.swdb('repair',failed['id'],'--provider-config',config,'--runs-dir',runs,'--format','json')
    assert result.returncode == 0, result.stderr
    repaired = json.loads(result.stdout)
    assert len(repaired['attempts']) == 2
    assert repaired['attempts'][1]['trigger_evaluation'] == failed['id']
    assert repaired['attempts'][1]['parent_candidate'] == base['candidate']
    assert repaired['repair_budget']['repairs'] == 1
    later = records.swdb('get',repaired['candidate'],'--chain','--format','json')
    assert base['candidate'] in json.loads(later.stdout)['records']
    result, failed_again = evaluate(evaluation_setup,mode='build_fail',id='eval-repaired',candidate=repaired['candidate'])
    assert result.returncode == 1
    # A later operator configuration cannot increase the first recorded repair limit.
    result = records.swdb('repair',failed_again['id'],'--provider-config',provider(max_repairs=5),
                         '--runs-dir',runs,'--format','json')
    exhausted = json.loads(result.stdout)
    assert result.returncode == 1
    assert 'budget exhausted' in exhausted['outcome']['reason']
    assert exhausted['repair_budget']['repairs'] == 1 and len(exhausted['attempts']) == 2
    assert records.swdb('get',failed['id']).returncode == 0


def test_successful_evaluation_cannot_trigger_performance_tuning(evaluation_setup, provider):
    records,runs,_,_ = evaluation_setup
    result, evaluated = evaluate(evaluation_setup)
    assert result.returncode == 0
    result = records.swdb('repair',evaluated['id'],'--provider-config',provider(),'--runs-dir',runs,'--format','json')
    data = json.loads(result.stdout)
    assert result.returncode == 1
    assert 'regressions do not trigger tuning' in data['outcome']['reason']
    assert len(data['attempts']) == 1

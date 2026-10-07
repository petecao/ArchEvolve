"""Public strict-functional evaluation and estimate handoff. Updated: 2026-10-06 ET."""
import copy
import hashlib
import json
from pathlib import Path
import yaml
from conftest import REPO, run_swdb
from swdb import artifacts
from testkit.analytic import fixture_characterization

CANDIDATE='bfs-functional-read-offload-20261006-a1.proposal.candidate-1'
CERTIFICATION='certification.23f81442358b4dcc8688140a394a1f08'
TARGET='dx100-e4fc4af-functional-analytic-v1'


def prepared(records,tmp_path):
    records.copy_repo()
    # Historical streams, estimates and their functional evaluation copies
    # do not belong to this literal zero-work fixture. Original records are
    # untouched; the copied fixture still uses full public validation.
    for folder in ('workload_characterizations','estimates'):
        for path in (records.path/folder).glob('*.yaml'):
            path.unlink()
    for path in (records.path/'evaluations').glob('*.yaml'):
        data=yaml.safe_load(path.read_text())
        context=data.get('context',{})
        if isinstance(context,dict) and context.get('evaluator')=='swdb.strict-functional-estimate.v1':
            path.unlink()
    # Parameter-filled targets and protocols seal the historical counts removed
    # above. Exclude that complete dependency closure from the copied zero-work
    # fixture; canonical source records remain unchanged and validated separately.
    for path in (records.path/'target_descriptions').glob('*.yaml'):
        if yaml.safe_load(path.read_text()).get('parameter_estimation'):
            path.unlink()
    for path in (records.path/'protocols').glob('*.yaml'):
        snapshot=yaml.safe_load(path.read_text()).get('settings',{}).get('target_description',{})
        if isinstance(snapshot,dict) and snapshot.get('snapshot',{}).get('parameter_estimation'):
            path.unlink()
    candidate=records.read('candidates/'+CANDIDATE+'.yaml')
    count=fixture_characterization(records.path)
    count['subject']={'kind':'candidate','id':CANDIDATE}
    count['binding']['threads']=4
    count['binding']['subject_source_identity']={
        'subject_record_sha256':artifacts.digest(candidate),
        'source_snapshot':candidate['source_snapshot'],
        'candidate_artifact_sha256':candidate['artifact']['sha256'],
        'candidate_diff_sha256':candidate.get('diff_sha256')}
    count.pop('identity_sha256');count['identity_sha256']=artifacts.digest(count)
    records.write('workload_characterizations/fixture.counts.yaml',count)
    target={'kind':'target_description','schema_version':'0.4','id':'fixture.functional.target',
        'status':'draft','created':'2026-10-06','updated':'2026-10-06',
        'provenance':[{'id':'fixture','kind':'source_code','description':'Zero-work binding fixture; no hardware performance claim.'}],
        'format':'swdb.target-description.v1','version':'1','target':TARGET,'threads':4,
        'estimator_variant':'team','calibration_sources':[],'dram_address_layout':None,
        'mechanisms':[{'model':'streaming_bandwidth','parameters':{'bytes_per_s':{
            'value':32,'basis':'reported','source':'Contract fixture.','unit':'bytes/s'}}}]}
    target_file=tmp_path/'target.yaml';target_file.write_text(yaml.safe_dump(target,sort_keys=False))
    freeze=tmp_path/'freeze.yaml';freeze.write_text(yaml.safe_dump({'message_version':'1.0',
        'id':'fixture.functional.protocol','version':1,'settings':{'mode':'estimated',
        'estimator_version':'swdb.analytic.v1','target_description':str(target_file),
        'inputs':['kron-g16-k16'],'sources':[CANDIDATE],'roi':'fixture.stream.v1','threads':4}},sort_keys=False))
    done=run_swdb('freeze-protocol',freeze,'--records',records.path,'--format','json')
    assert done.returncode==0,done.stdout+done.stderr
    request={'message_version':'1.0','id':'fixture.functional.evaluation',
        'candidate':CANDIDATE,'certification':CERTIFICATION,
        'characterization':'fixture.counts','target_description':str(target_file),
        'protocol':json.loads(done.stdout)['id']}
    path=tmp_path/'evaluation.json';path.write_text(json.dumps(request))
    return path


def test_strict_certified_candidate_gets_estimated_handoff_without_target_timing(records,tmp_path):
    path=prepared(records,tmp_path)
    guard=tmp_path/'guard';guard.mkdir()
    sentinel=tmp_path/'unexpected-child'
    (guard/'sitecustomize.py').write_text(
        "import subprocess\nfrom pathlib import Path\n"
        "def refuse(*args,**kwargs):\n"
        "    Path("+repr(str(sentinel))+").write_text('child launched')\n"
        "    raise RuntimeError('functional path launched a child process')\n"
        "subprocess.Popen=refuse\n")
    done=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json',
        env={'PYTHONPATH':str(guard)+':'+str(REPO)})
    assert not sentinel.exists()
    assert done.returncode==0,done.stdout+done.stderr
    data=json.loads(done.stdout)
    assert data['outcome']['state']=='complete'
    assert data['correctness']['state']=='passed'
    assert data['context']['correctness_scope']=='functional-target'
    assert data['context']['hardware_correctness_claim'] is False
    assert data['timing']==[] and data['gain_claim'] is False
    assert data['context']['analytic_estimate']['basis']=='estimated'
    assert data['context']['analytic_estimate']['ratio'] is None
    assert data['context']['analytic_estimate']['verdict']=='within_error'
    rendered=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert rendered.returncode==0,rendered.stdout+rendered.stderr
    message=json.loads(rendered.stdout)
    assert message['format_version']=='1.1'
    assert message['content']['correctness']['scope']=='functional-target'
    assert message['content']['estimate']['ratio'] is None
    assert message['content']['estimate']['error_band'] is None
    assert message['content']['performance_claim']=='none'
    checked=records.validate();assert checked.returncode==0,checked.stdout+checked.stderr

    # The literal caller request must remain tied to the archived result.
    altered=copy.deepcopy(data)
    altered['request']['target_description']='fixture.unrequested.target'
    records.write('evaluations/'+data['id']+'.yaml',altered)
    refused=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert refused.returncode!=0,refused.stdout+refused.stderr
    checked=records.validate()
    assert checked.returncode!=0 and 'functional evaluation request binding' in checked.stdout+checked.stderr
    records.write('evaluations/'+data['id']+'.yaml',data)

    legacy=copy.deepcopy(data)
    legacy['context'].pop('request_sha256',None)
    legacy['request']['target_description']='mbit10.cpu.lanl20261006a2.v2.t1'
    records.write('evaluations/'+data['id']+'.yaml',legacy)
    refused=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert refused.returncode!=0 and 'functional evaluation request binding' in refused.stderr
    records.write('evaluations/'+data['id']+'.yaml',data)

    # A file-sourced target remains portable through its immutable snapshot.
    Path(data['request']['target_description']).unlink()
    rendered=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert rendered.returncode==0,rendered.stdout+rendered.stderr

    # A handoff verifies the archived estimate before publishing compact fields.
    altered=copy.deepcopy(data)
    altered['context']['analytic_estimate']['ratio']=123.0
    records.write('evaluations/'+data['id']+'.yaml',altered)
    refused=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert refused.returncode!=0,refused.stdout+refused.stderr
    checked=records.validate()
    assert checked.returncode!=0 and 'functional estimate reference' in checked.stdout+checked.stderr

    records.write('evaluations/'+data['id']+'.yaml',data)


def test_stale_certification_is_unverified_and_team_refuses_gem5_before_writes(records,tmp_path):
    path=prepared(records,tmp_path)
    request=json.loads(path.read_text())
    stale=records.read('certifications/'+CERTIFICATION+'.yaml')
    stale['id']='fixture.functional.stale-certification'
    stale['command']['version']='obsolete'
    records.write('certifications/'+stale['id']+'.yaml',stale)
    request.update(id='fixture.functional.stale-evaluation',certification=stale['id'])
    path.write_text(json.dumps(request))
    done=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json')
    assert done.returncode==1,done.stdout+done.stderr
    data=json.loads(done.stdout)
    assert data['outcome']['state']=='incompatible'
    assert data['correctness']['state']=='unverified'
    assert 'certify again' in data['outcome']['reason']
    assert not (records.path/'estimates'/(data['id']+'.estimate.yaml')).exists()
    rendered=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json')
    assert rendered.returncode==0,rendered.stdout+rendered.stderr
    assert json.loads(rendered.stdout)['content']['estimate'] is None
    target_path=Path(request['target_description'])
    target=yaml.safe_load(target_path.read_text());target['target']='dx100-e4fc4af-4c'
    target_path.write_text(yaml.safe_dump(target,sort_keys=False))
    request['id']='fixture.functional.gem5-refused';path.write_text(json.dumps(request))
    before={str(p.relative_to(records.path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in records.path.rglob('*.yaml')}
    refused=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json')
    assert refused.returncode!=0 and 'gem5' in refused.stderr
    after={str(p.relative_to(records.path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in records.path.rglob('*.yaml')}
    assert after==before

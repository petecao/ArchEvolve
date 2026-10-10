"""Public strict-functional evaluation and estimate handoff. Updated: 2026-10-10 ET (code review of
ticket 12: copied record closure; the no-child sentinel proves it loaded and also blocks os-level spawns;
the historical certificate is refused as stale; the positive path needs a current-procedure certificate;
a known ratio stays within_error); 2026-10-06 ET."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
import yaml
from conftest import REPO, run_swdb
from swdb import artifacts
from testkit.analytic import fixture_characterization

CANDIDATE='bfs-functional-read-offload-20261006-a1.proposal.candidate-1'
#: Historical: certified under candidate procedure 1.6. Since 2026-10-09 the default is 1.7, so
#: evaluate-functional refuses it as stale (docs/reference/bfs-functional-estimates.md).
CERTIFICATION='certification.23f81442358b4dcc8688140a394a1f08'
TARGET='dx100-e4fc4af-functional-analytic-v1'
BASELINE_SUBJECT='dx100-bfs-scalar'


def current_certification():
    """A repository execution certificate of CANDIDATE that today's candidate procedure accepts, or None."""
    from swdb import certification_procedures as procedures, kernels
    proc=procedures.procedure(procedures.CANDIDATE)
    implementation=yaml.safe_load((REPO/'records/implementations'/(BASELINE_SUBJECT+'.yaml')).read_text())
    manifest=procedures.manifest(proc,REPO/'library',kernels.require(implementation['kernel'],'test lookup'))
    for path in sorted((REPO/'records/certifications').glob('*.yaml')):
        if CANDIDATE.encode() not in path.read_bytes():
            continue
        data=yaml.safe_load(path.read_text())
        command=data.get('command',{})
        if (data.get('candidate',{}).get('id')==CANDIDATE and data.get('verdict')=='certified'
                and data.get('evidence_kind')=='execution' and command.get('version')==proc.version
                and command.get('sources_sha256')==manifest['sources_sha256']):
            return data['id']
    return None


def characterization(records,rid,subject_kind,subject_id,flops):
    """A contract-fixture count with one hand-computed loop (flops floating-point operations)."""
    subject=records.read(('candidates/' if subject_kind=='candidate' else 'implementations/')+subject_id+'.yaml')
    written=records.path/'workload_characterizations/fixture.counts.yaml'
    kept=written.read_bytes() if written.exists() else None
    count=fixture_characterization(records.path)  # the shared template; it writes fixture.counts
    if kept is None:
        written.unlink()
    else:
        written.write_bytes(kept)
    count.update(id=rid,subject={'kind':subject_kind,'id':subject_id})
    count['binding']['threads']=4
    identity={'subject_record_sha256':artifacts.digest(subject)}
    if subject_kind=='candidate':
        identity.update(source_snapshot=subject['source_snapshot'],candidate_artifact_sha256=subject['artifact']['sha256'],
                        candidate_diff_sha256=subject.get('diff_sha256'))
    count['binding']['subject_source_identity']=identity
    if flops:
        fact=lambda value:{'value':value,'basis':'reported','scope':'per_run'}
        count['regions']=[{'id':'fixture.loop','kind':'loop','mapped':True,
            'source_location':{'function':'fixture','line':1},
            'active_workers':{'value':4,'basis':'reported'},
            'worker_context':{'team_sizes':[4],'measurement':'Hand-written contract fixture.'},
            'operation_counts':{'integer':fact(0),'floating_point':fact(flops),'branch':fact(0),'atomic':fact(0)},
            'dynamic_counts':{'loop_iterations':fact(flops)},'footprint_bytes':{'value':0,'basis':'reported'},
            'access_patterns':[],'accelerator_calls':[],'address_stream_counts':{}}]
    count.pop('identity_sha256');count['identity_sha256']=artifacts.digest(count)
    records.write('workload_characterizations/'+rid+'.yaml',count)
    return rid


def prepared(records,tmp_path,*,certification=CERTIFICATION,flops=0):
    # 2026-10-10 ET: only the records this fixture references (tests/conftest.py copy_closure);
    # the copied ~1 GB catalog lost dependencies when historical counts were removed from it.
    records.copy_closure(CANDIDATE,certification,'kron-g16-k16')
    characterization(records,'fixture.counts','candidate',CANDIDATE,flops)
    rates={name+'_ops_per_s':{'value':16.0 if name=='floating_point' else 1e9,'basis':'reported',
        'source':'Hand-computed contract fixture; no hardware performance claim.','unit':'operations/s'}
        for name in ('integer','floating_point','branch','atomic')}
    target={'kind':'target_description','schema_version':'0.4','id':'fixture.functional.target',
        'status':'draft','created':'2026-10-06','updated':'2026-10-06',
        'provenance':[{'id':'fixture','kind':'source_code','description':'Contract fixture; no hardware performance claim.'}],
        'format':'swdb.target-description.v1','version':'1','target':TARGET,'threads':4,
        'estimator_variant':'team','calibration_sources':[],'dram_address_layout':None,
        'mechanisms':[{'model':'compute_throughput','parameters':rates},
            {'model':'streaming_bandwidth','parameters':{'bytes_per_s':{
            'value':32,'basis':'reported','source':'Contract fixture.','unit':'bytes/s'}}}]}
    target_file=tmp_path/'target.yaml';target_file.write_text(yaml.safe_dump(target,sort_keys=False))
    freeze=tmp_path/'freeze.yaml';freeze.write_text(yaml.safe_dump({'message_version':'1.0',
        'id':'fixture.functional.protocol','version':1,'settings':{'mode':'estimated',
        'estimator_version':'swdb.analytic.v1','target_description':str(target_file),
        'inputs':['kron-g16-k16'],'sources':[CANDIDATE,BASELINE_SUBJECT],'roi':'fixture.stream.v1','threads':4}},sort_keys=False))
    done=run_swdb('freeze-protocol',freeze,'--records',records.path,'--format','json')
    assert done.returncode==0,done.stdout+done.stderr
    request={'message_version':'1.0','id':'fixture.functional.evaluation',
        'candidate':CANDIDATE,'certification':certification,
        'characterization':'fixture.counts','target_description':str(target_file),
        'protocol':json.loads(done.stdout)['id']}
    path=tmp_path/'evaluation.json';path.write_text(json.dumps(request))
    return path


def sentinel(tmp_path):
    """sitecustomize that refuses every child-process route and proves it was imported."""
    guard=tmp_path/'guard';guard.mkdir(exist_ok=True)
    child,loaded=tmp_path/'unexpected-child',tmp_path/'sentinel-loaded'
    (guard/'sitecustomize.py').write_text(
        "import os, subprocess\nfrom pathlib import Path\n"
        "Path("+repr(str(loaded))+").write_text('loaded')\n"
        "def refuse(*args,**kwargs):\n"
        "    Path("+repr(str(child))+").write_text('child launched')\n"
        "    raise RuntimeError('functional path launched a child process')\n"
        "subprocess.Popen=refuse\n"
        "for name in ('system','popen','fork','forkpty','posix_spawn','posix_spawnp','execv','execve','execvp','execvpe',\n"
        "             'execl','execle','execlp','execlpe','spawnv','spawnve','spawnvp','spawnvpe','spawnl','spawnle'):\n"
        "    if hasattr(os,name):setattr(os,name,refuse)\n")
    return {'PYTHONPATH':str(guard)+':'+str(REPO)},child,loaded


def baseline_estimate(records,request):
    """The baseline implementation estimated under the same frozen protocol: 64 / 16 = 4 s."""
    rid=characterization(records,'fixture.baseline.counts','implementation',BASELINE_SUBJECT,64)
    done=run_swdb('estimate','--records',records.path,'--characterization',rid,
        '--target-description',request['target_description'],'--protocol',request['protocol'],
        '--id','fixture.baseline.estimate','--format','json')
    assert done.returncode==0,done.stdout+done.stderr
    baseline=json.loads(done.stdout)
    assert baseline['seconds']==pytest.approx(4.0)
    return baseline


def test_dx100_functional_estimate_shows_a_known_ratio_and_stays_within_error(records,tmp_path):
    # D25/story 53 on the ArchEvolve DX100 target: no validated band, so a known ratio is shown
    # and the verdict stays within_error. Needs no certificate.
    request=json.loads(prepared(records,tmp_path,flops=32).read_text())
    baseline=baseline_estimate(records,request)
    done=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts',
        '--target-description',request['target_description'],'--protocol',request['protocol'],
        '--baseline',baseline['id'],'--id','fixture.candidate.estimate','--format','json')
    assert done.returncode==0,done.stdout+done.stderr
    data=json.loads(done.stdout)
    assert data['target']==TARGET and data['basis']=='estimated'
    assert data['seconds']==pytest.approx(2.0) and data['ratio']==pytest.approx(2.0)
    assert data['verdict']=='within_error' and data['error_band'] is None


def test_strict_certified_candidate_gets_estimated_handoff_without_target_timing(records,tmp_path):
    current=current_certification()
    if current is None:
        pytest.skip('needs a certificate of '+CANDIDATE+' under the current default candidate procedure; '
                    'the retained '+CERTIFICATION+' is historical 1.6 (ticket 12 code review, 2026-10-09 ET)')
    path=prepared(records,tmp_path,certification=current,flops=32)
    request=json.loads(path.read_text())
    request['baseline']=baseline_estimate(records,request)['id'];path.write_text(json.dumps(request))
    env,child,loaded=sentinel(tmp_path)
    done=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json',env=env)
    assert loaded.exists() and not child.exists()
    assert done.returncode==0,done.stdout+done.stderr
    data=json.loads(done.stdout)
    assert data['outcome']['state']=='complete'
    assert data['correctness']['state']=='passed'
    assert data['context']['correctness_scope']=='functional-target'
    assert data['context']['hardware_correctness_claim'] is False
    assert data['timing']==[] and data['gain_claim'] is False
    assert data['context']['analytic_estimate']['basis']=='estimated'
    assert data['context']['analytic_estimate']['ratio']==pytest.approx(2.0)
    assert data['context']['analytic_estimate']['verdict']=='within_error'
    rendered=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json',env=env)
    assert rendered.returncode==0,rendered.stdout+rendered.stderr
    assert not child.exists()
    message=json.loads(rendered.stdout)
    assert message['format_version']=='1.1'
    assert message['content']['correctness']['scope']=='functional-target'
    assert message['content']['estimate']['ratio']==pytest.approx(2.0)
    assert message['content']['estimate']['verdict']=='within_error'
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
    # The retained 1.6 certificate is stale under today's default procedure: the whole public
    # path (evaluation and handoff) still starts no child process and creates no estimate.
    path=prepared(records,tmp_path)
    request=json.loads(path.read_text())
    request.update(id='fixture.functional.stale-evaluation');path.write_text(json.dumps(request))
    env,child,loaded=sentinel(tmp_path)
    done=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json',env=env)
    assert loaded.exists() and not child.exists()
    assert done.returncode==1,done.stdout+done.stderr
    data=json.loads(done.stdout)
    assert data['outcome']['state']=='incompatible'
    assert data['correctness']['state']=='unverified'
    assert 'certify again' in data['outcome']['reason'],data['outcome']['reason']
    assert not (records.path/'estimates'/(data['id']+'.estimate.yaml')).exists()
    rendered=run_swdb('handoff-message','evaluation_result',data['id'],
        '--records',records.path,'--format','json',env=env)
    assert rendered.returncode==0,rendered.stdout+rendered.stderr
    assert not child.exists()
    message=json.loads(rendered.stdout)
    assert message['format_version']=='1.1' and message['content']['estimate'] is None
    assert message['content']['correctness']['scope']=='functional-target'
    assert message['content']['correctness']['hardware_correctness_claim'] is False
    # The same request with a version label alone changed is equally stale.
    stale=records.read('certifications/'+CERTIFICATION+'.yaml')
    stale['id']='fixture.functional.stale-certification'
    stale['command']['version']='obsolete'
    records.write('certifications/'+stale['id']+'.yaml',stale)
    request.update(id='fixture.functional.obsolete-evaluation',certification=stale['id'])
    path.write_text(json.dumps(request))
    done=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json')
    assert done.returncode==1 and 'certify again' in json.loads(done.stdout)['outcome']['reason'],done.stdout+done.stderr
    target_path=Path(request['target_description'])
    target=yaml.safe_load(target_path.read_text());target['target']='dx100-e4fc4af-4c'
    target_path.write_text(yaml.safe_dump(target,sort_keys=False))
    request['id']='fixture.functional.gem5-refused';path.write_text(json.dumps(request))
    before={str(p.relative_to(records.path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in records.path.rglob('*.yaml')}
    refused=run_swdb('evaluate-functional',path,'--records',records.path,'--format','json')
    assert refused.returncode!=0 and all(term in refused.stderr for term in ('ADR 0013', 'dx100-e4fc4af-4c', 'gem5')), refused.stderr
    after={str(p.relative_to(records.path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in records.path.rglob('*.yaml')}
    assert after==before

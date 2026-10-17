"""Public generality report projections from independent pinned fixtures. 2026-10-06 ET.

Updated: 2026-10-09 23:10 ET (code review F5/F7): report v2 states code equality as the
shared estimator bundle hash and refuses any estimate or protocol off the reference
bundle; every target without native timing is estimate-only.
"""
import json
import subprocess
import sys
from pathlib import Path
from conftest import REPO
from swdb import artifacts
from swdb.estimate_protocol import estimator_identity


def fixture_request(tmp_path):
    records=tmp_path/'records';records.mkdir()
    def save(area,data):
        path=records/area/(data['id']+'.yaml');path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data))
        return {'id':data['id'],'path':path.relative_to(records).as_posix(),'sha256':artifacts.digest(data)}
    rows=[]
    for kernel in ['bfs','bc','pagerank']:
        implementation={'kind':'implementation','id':'gapbs-pr-jacobi-analytic-v1' if kernel=='pagerank' else 'fixture.'+kernel,
            'kernel':'gapbs-pr' if kernel=='pagerank' else 'gapbs-'+kernel}
        subject_ref=save('implementations',implementation)
        for target,threads,target_id in [('cpu',1,'mbit10'),('dx100',4,'dx100-e4fc4af-functional-analytic-v1'),('maple',2,'maple-isca2022')]:
            stem=f'fixture.{kernel}.{target}';roi='gapbs.functional_trial_lambda.v1' if kernel=='pagerank' or target=='dx100' else 'gapbs.trial_lambda.v1'
            subject={'kind':'implementation','id':implementation['id']}
            td={'kind':'target_description','id':stem+'.target','target':target_id,'threads':threads,
                'extensions':{'estimate_only':True,'accuracy_validation':False,'paired_timing':None} if target=='maple' else {}}
            char={'kind':'workload_characterization','id':stem+'.counts','evidence_kind':'execution','subject':subject,
                'input':'fixture.graph','coverage':{'whole_timed_call':True},
                'source':{'sha256':'ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70' if kernel=='pagerank' else '1'*64,
                    'run_arguments':['-g','8','-k','4','-n','2']},
                'binding':{'state':'verified','roi':roi,'threads':threads},'unmapped_loops':[{'id':'fixture.unmapped','reason':'source shape unknown'}],
                'trials':[{'position':0,'sources':[],'regions':[]},{'position':1,'sources':[],'regions':[]}]}
            char_ref=save('workload_characterizations',char)
            protocol={'kind':'protocol','id':stem+'.protocol','state':'frozen','settings':{
                'mode':'estimated','estimator_sha256':estimator_identity(),'threads':threads,'roi':roi,
                'inputs':['fixture.graph'],'input_run_arguments':{'fixture.graph':char['source']['run_arguments']},
                'target_description':{'id':td['id'],'sha256':artifacts.digest(td),'snapshot':td}}}
            protocol['identity_sha256']=artifacts.digest({'fixture_frozen_settings':protocol['settings']})
            protocol_ref=save('protocols',protocol)
            def region(n):
                return {'id':'fixture.host','seconds':None,'state':'unknown','limiting_bound':None,
                    'bounds':[{'model':'compute_throughput','seconds':None,'state':'unknown','formula':'operations / rate',
                        'inputs':{'operations':{'value':n,'basis':'reported','unit':'operations'},'rate':{'value':None,'basis':'unknown','unit':'operations/s'}},
                        'missing':['rate'],'notes':[]}],
                    'overheads':[{'model':'runtime_call','seconds':None,'state':'unknown','formula':'calls * cost',
                        'inputs':{'calls':{'value':3,'basis':'reported'},'cost':{'value':None,'basis':'unknown'}},'missing':['cost'],'notes':[]}]}
            estimate={'kind':'estimate','id':stem+'.estimate','basis':'estimated','estimator_version':'swdb.analytic.v1',
                'estimator_sha256':estimator_identity(),'characterization':char['id'],'characterization_sha256':char_ref['sha256'],
                'protocol':protocol['id'],'protocol_sha256':protocol['identity_sha256'],'target_description':td['id'],
                'target_description_sha256':artifacts.digest(td),'target_description_snapshot':td,'target':target_id,
                'threads':threads,'subject':subject,'input':'fixture.graph','seconds':None,'ratio':None,'error_band':None,
                'regions':[region(6)],'trials':[{'position':0,'sources':[],'seconds':None,'regions':[region(4)]},
                                              {'position':1,'sources':[],'seconds':None,'regions':[region(8)]}],
                'notes':['Independent report fixture; no application execution claim.']}
            rows.append({'kernel':kernel,'target':target,'subject':subject_ref,'implementation':subject_ref,
                'characterization':char_ref,'protocol':protocol_ref,'estimate':save('estimates',estimate)})
    request={'format':'swdb.generality-report-request.v1','updated':'2026-10-06 ET',
        'scope':'Independent public report fixture; not actual application evidence.','reference':{'kernel':'bfs','target':'dx100'},'pairs':rows}
    request['identity_sha256']=artifacts.digest(request)
    path=tmp_path/'request.json';path.write_text(json.dumps(request))
    return records,path


def run_report(records,request,output,tmp_path):
    return subprocess.run([sys.executable,str(REPO/'scripts/generality_report.py'),'--records',str(records),
        '--request',str(request),'--output',str(output)],cwd=tmp_path,capture_output=True,text=True,timeout=30)


def test_all_nine_reports_preserve_exact_trial_inputs_unknowns_and_source_scope(tmp_path):
    records,request=fixture_request(tmp_path)
    before={p.relative_to(records).as_posix():p.read_bytes() for p in records.rglob('*.yaml')}
    output=tmp_path/'report';done=run_report(records,request,output,tmp_path)
    assert done.returncode==0,done.stdout+done.stderr
    report=json.loads((output/'report.json').read_text())
    assert len(report['pairs'])==9 and report['format']=='swdb.generality-report.v2'
    equality=report['code_equality']
    assert 'estimator_and_mechanism_diff' not in equality and equality['estimator_sha256']==estimator_identity()
    assert artifacts.digest(equality['module_hashes'])==equality['estimator_sha256']
    reference=json.loads(request.read_text())['pairs'][1]
    assert (reference['kernel'],reference['target'])==('bfs','dx100') and equality['reference_estimate']==reference['estimate']
    # D27: only the CPU target has native timing; DX100 and MAPLE rows stand alone.
    assert {(r['target'],r['estimate_only']) for r in report['pairs']}=={('cpu',False),('dx100',True),('maple',True)}
    row=next(row for row in report['pairs'] if row['kernel']=='pagerank' and row['target']=='maple')
    assert row['estimate_only'] is True and row['accuracy_validation'] is False and row['paired_timing'] is None
    assert row['seconds'] is None and row['ratio'] is None and row['error_band'] is None
    assert row['regions'][0]['inputs_scope']=='diagnostic aggregate; exact inputs are in trials'
    assert [trial['regions'][0]['bounds'][0]['inputs']['operations']['value'] for trial in row['trials']]==[4,8]
    assert all(trial['regions'][0]['overheads'][0]['inputs']['cost']['value'] is None for trial in row['trials'])
    assert row['unmapped_loops']==[{'id':'fixture.unmapped','reason':'source shape unknown'}]
    assert {p.relative_to(records).as_posix():p.read_bytes() for p in records.rglob('*.yaml')}==before
    assert 'MAPLE' in (output/'report.md').read_text() and 'unknown' in (output/'report.md').read_text()


def test_frozen_target_snapshot_disagreement_is_refused_after_repinning(tmp_path):
    records,request=fixture_request(tmp_path);data=json.loads(request.read_text());pair=data['pairs'][0]
    protocol_path=records/pair['protocol']['path'];protocol=json.loads(protocol_path.read_text())
    protocol['settings']['target_description']['snapshot']['threads']=4
    protocol_path.write_text(json.dumps(protocol));pair['protocol']['sha256']=artifacts.digest(protocol)
    estimate_path=records/pair['estimate']['path'];estimate=json.loads(estimate_path.read_text())
    estimate['protocol_sha256']=protocol['identity_sha256'];estimate_path.write_text(json.dumps(estimate));pair['estimate']['sha256']=artifacts.digest(estimate)
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'});request.write_text(json.dumps(data))
    output=tmp_path/'report';done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and 'target snapshot' in done.stderr and not output.exists()


def test_trial_source_identity_disagreement_is_refused_after_repinning(tmp_path):
    records,request=fixture_request(tmp_path);data=json.loads(request.read_text());pair=data['pairs'][0]
    path=records/pair['estimate']['path'];estimate=json.loads(path.read_text())
    estimate['trials'][0]['sources']=[999];path.write_text(json.dumps(estimate));pair['estimate']['sha256']=artifacts.digest(estimate)
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'});request.write_text(json.dumps(data))
    output=tmp_path/'report';done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and 'trial identities' in done.stderr and not output.exists()


def repin_bundle(records,request,index,field,value):
    data=json.loads(request.read_text());pair=data['pairs'][index]
    kind='estimate' if field=='estimate' else 'protocol'
    path=records/pair[kind]['path'];record=json.loads(path.read_text())
    if kind=='estimate':record['estimator_sha256']=value
    else:record['settings']['estimator_sha256']=value
    path.write_text(json.dumps(record));pair[kind]['sha256']=artifacts.digest(record)
    if kind=='protocol':
        estimate_path=records/pair['estimate']['path'];estimate=json.loads(estimate_path.read_text())
        record['identity_sha256']=artifacts.digest({'fixture_frozen_settings':record['settings']});path.write_text(json.dumps(record))
        pair['protocol']['sha256']=artifacts.digest(record);estimate['protocol_sha256']=record['identity_sha256']
        estimate_path.write_text(json.dumps(estimate));pair['estimate']['sha256']=artifacts.digest(estimate)
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'});request.write_text(json.dumps(data))


def test_estimate_or_protocol_off_the_reference_bundle_is_refused(tmp_path):
    # Code review F5 (2026-10-09 ET): code equality is the shared bundle hash, so one
    # estimate or protocol frozen with another estimator must stop the whole report.
    for index,field,message in [(5,'estimate','differs from the reference pair'),(8,'protocol','differs from the reference pair'),
                                (1,'estimate','reference estimate bundle differs')]:
        case=tmp_path/f'{field}-{index}';case.mkdir()
        records,request=fixture_request(case)
        repin_bundle(records,request,index,field,'0'*64)
        output=case/'report';done=run_report(records,request,output,case)
        assert done.returncode==2 and message in done.stderr and not output.exists(),(index,field,done.stderr)

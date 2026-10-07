"""Public weak-paper report behavior. Created: 2026-10-06 ET."""
import json
import shutil
import subprocess
import sys
import pytest
from pathlib import Path
from conftest import REPO
from swdb import artifacts

EVIDENCE=REPO/'.scratch/lanl-db-analytic-eval-2026-10-06/evidence'
ACTUAL='bfs.functional.kron-g16.t4.estimate.llm.a2.postfill.a1'


def request_fixture(tmp_path):
    wrapper=json.loads((EVIDENCE/'10-estimation-role-mbit10-20261006-a2-postfill-a1.json').read_text())
    ref=next(row for row in wrapper['new_records'] if row['kind']=='estimate')
    records=tmp_path/'records';(records/'estimates').mkdir(parents=True)
    source=REPO/'records'/ref['path'];copied=records/ref['path'];shutil.copyfile(source,copied)
    request={'format':'swdb.paper-sanity-request.v1','updated':'2026-10-06 ET',
        'source':{'uri':'https://arxiv.org/pdf/2505.23073v2',
            'sha256':'ec18bdc585f32e3da5c0fd467e686dd2137b3db88d4c327d510509213e7c44a3'},
        'observations':[{'kernel':'gapbs-bfs','label':'BFS','ratio':2.9,'unit':'ratio','basis':'reported',
            'locator':'PDF page9, Figure9','approximate':True,'reading_uncertainty':0.1,
            'scope':{'input':'Uniform graphs, 2^20–2^22 nodes, average degree15',
                'cores':4,'algorithm':'Bottom-up BFS','configuration':'Skylake-like; baseline10MB LLC, DX8MB'}}],
        'comparisons':[{'kernel':'gapbs-bfs','estimate':{'id':ACTUAL,'sha256':ref['sha256']},
            'differences':[{'dimension':'input','paper':'Uniform, scale20–22/degree15','estimate':'Kronecker, scale16/requested degree16'},
                {'dimension':'algorithm/ROI','paper':'Bottom-up BFS','estimate':'Complete registered DOBFS read-offload call'},
                {'dimension':'configuration','paper':'Simulated baseline4cores/10MBLLC and DX8MBLLC','estimate':'Source/configuration-only FUNC identity; four requested software threads'}]}]}
    request['identity_sha256']=artifacts.digest(request)
    path=tmp_path/'request.json';path.write_text(json.dumps(request))
    return records,path,copied


def run_report(records,request,output,cwd):
    return subprocess.run([sys.executable,str(REPO/'scripts/paper_sanity_check.py'),
        '--records',str(records),'--request',str(request),'--output',str(output)],
        cwd=cwd,capture_output=True,text=True,timeout=90)


def test_actual_unknown_ratio_stays_incomparable_beside_reported_paper_scope(tmp_path):
    records,request,estimate=request_fixture(tmp_path);before=estimate.read_bytes()
    output=tmp_path/'report';done=run_report(records,request,output,tmp_path)
    assert done.returncode==0,done.stdout+done.stderr
    report=json.loads((output/'report.json').read_text())
    assert report['mode']=='weak_sanity_check' and report['accuracy_validation'] is False
    row=report['rows'][0]
    assert row['estimated_ratio'] is None and row['comparison_state']=='incomparable'
    assert row['reported_ratio']==2.9 and row['paper_basis']=='reported'
    assert row['reading_uncertainty']==0.1 and row['estimated_threads']==4
    assert {x['dimension'] for x in row['differences']}=={'input','algorithm/ROI','configuration'}
    assert estimate.read_bytes()==before
    text=(output/'report.md').read_text()
    assert 'Weak paper sanity check' in text and 'unknown' in text and 'Figure9' in text


def test_changed_reported_observation_is_refused_before_output(tmp_path):
    records,request,estimate=request_fixture(tmp_path);before=estimate.read_bytes()
    data=json.loads(request.read_text());data['observations'][0]['ratio']=9.0
    request.write_text(json.dumps(data));output=tmp_path/'report'
    done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and 'request seal' in done.stderr
    assert not output.exists() and estimate.read_bytes()==before


@pytest.mark.parametrize("field,value", [("basis","measured"),("unit","seconds"),("locator",""),("ratio",float("inf")),("reading_uncertainty",None)])
def test_unqualified_paper_number_is_refused(tmp_path,field,value):
    records,request,_=request_fixture(tmp_path)
    data=json.loads(request.read_text());data['observations'][0][field]=value
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'}) if value!=float('inf') else '0'*64
    request.write_text(json.dumps(data));output=tmp_path/'report'
    done=run_report(records,request,output,tmp_path)
    assert done.returncode==2
    assert not output.exists()


def test_comparison_for_an_uncited_kernel_is_refused(tmp_path):
    records,request,_=request_fixture(tmp_path)
    data=json.loads(request.read_text());data['comparisons'][0]['kernel']='gapbs-bc'
    data['identity_sha256']=artifacts.digest({k:v for k,v in data.items() if k!='identity_sha256'})
    request.write_text(json.dumps(data));output=tmp_path/'report'
    done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and 'comparison kernel' in done.stderr and not output.exists()


def test_changed_estimate_and_existing_output_are_refused(tmp_path):
    from swdb import access
    records,request,estimate=request_fixture(tmp_path)
    original=estimate.read_bytes();data=access.read_record(estimate);data['ratio']=2.0
    estimate.write_text(json.dumps(data));output=tmp_path/'report'
    done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and 'content pin' in done.stderr and not output.exists()
    estimate.write_bytes(original);output.mkdir();marker=output/'report.json';marker.write_text('preserved')
    done=run_report(records,request,output,tmp_path)
    assert done.returncode==2 and marker.read_text()=='preserved'

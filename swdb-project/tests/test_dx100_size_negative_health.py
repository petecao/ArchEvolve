"""2026-10-16 ET. Pure size acceptance controls; no actual tools/probes."""
import hashlib,json
import pytest
from test_dx100_size_actual import assert_size_outcome


def record(tmp_path,*,failure='unknown',results=None):
    native={'version':'1','complete':True,'goals':[
        {'goal':'typed_trust_fixture_ensures','passed':False,'smoke':False,'results':results or ['unknown','timeout']},
        {'goal':'smoke_trust_fixture_entry','passed':True,'smoke':True,'results':['valid']}], 'properties':[]}
    p=tmp_path/'inventory.json';p.write_text(json.dumps(native))
    r={'verdict':'not_proven','failure_class':failure,'goals':[
        {'goal':'typed_trust_fixture_ensures','status':'unknown','smoke':False},
        {'goal':'smoke_trust_fixture_entry','status':'valid','smoke':True}],
       'evidence':{'reports':[{'name':'wp_inventory','path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
    return r,native,p


@pytest.mark.parametrize('failure',['solver_error','out_of_memory','resource_exhausted','tool_crash','parse_error','unsupported_construct'])
def test_wrong_size_rejects_unhealthy_global_outcome_even_when_only_ensures_is_open(tmp_path,failure):
    r,_,_=record(tmp_path,failure=failure)
    with pytest.raises(AssertionError):assert_size_outcome(r,1)


@pytest.mark.parametrize('result',['failed','computing','invalid','unexpected'])
def test_wrong_size_reads_every_native_result_not_just_best_status(tmp_path,result):
    r,_,_=record(tmp_path,results=[result,'unknown','timeout'])
    with pytest.raises(AssertionError):assert_size_outcome(r,1)


@pytest.mark.parametrize('change',['missing','hash','incomplete','extra_goal','duplicate','results_shape'])
def test_wrong_size_requires_complete_pinned_matching_native_inventory(tmp_path,change):
    r,native,p=record(tmp_path)
    if change=='missing':r['evidence']['reports']=[]
    elif change=='hash':r['evidence']['reports'][0]['sha256']='0'*64
    else:
        if change=='incomplete':native['complete']=False
        elif change=='extra_goal':native['goals'].append({'goal':'unread','results':['failed']})
        elif change=='duplicate':native['goals'].append(dict(native['goals'][0]))
        elif change=='results_shape':native['goals'][0]['results']='unknown'
        p.write_text(json.dumps(native));r['evidence']['reports'][0]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(AssertionError):assert_size_outcome(r,1)


@pytest.mark.parametrize('failure',['unknown','timeout'])
def test_wrong_size_retains_healthy_ordinary_nonproof_with_complete_native_inventory(tmp_path,failure):
    r,_,_=record(tmp_path,failure=failure)
    assert_size_outcome(r,1)

def test_positive_size_acceptance_retains_all_valid_ordinary_and_smoke_requirement(tmp_path):
    r,_,_=record(tmp_path);r['verdict']='proven';r['failure_class']=None
    r['goals'][0]['status']='valid';r.pop('evidence')
    assert_size_outcome(r,0)


@pytest.mark.parametrize('results',[[],['untried']])
def test_wrong_size_cannot_count_an_unattempted_ordinary_goal_as_healthy_nonproof(tmp_path,results):
    r,native,p=record(tmp_path)
    native['goals'][0]['results']=results;p.write_text(json.dumps(native))
    r['evidence']['reports'][0]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(AssertionError):assert_size_outcome(r,1)

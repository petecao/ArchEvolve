"""Fresh configuration-only target is admitted without historical execution dependencies. 2026-10-06 ET."""
import json
import yaml
from conftest import REPO,run_swdb

TARGET='dx100-e4fc4af-functional-analytic-v1'
DESCRIPTION='dx100-e4fc4af-functional-analytic-v1.t4'


def test_fresh_functional_target_validates_and_freezes_code_only_dependencies(records,tmp_path):
    records.copy_repo()
    checked=run_swdb('validate','--records',records.path,'--library',REPO/'library')
    assert checked.returncode==0,checked.stdout+checked.stderr
    request=tmp_path/'freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.functional.target.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':DESCRIPTION,
            'inputs':['dx100-functional-kron-g16-k16'],'roi':'gapbs.functional_trial_lambda.v1','threads':4}}))
    result=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    frozen=json.loads(result.stdout)
    assert records.read('hardware_targets/'+TARGET+'.yaml')['backend']['id']=='functional-source'
    assert frozen['settings']['target_description']['snapshot']['calibration_sources']==[]
    dependency=frozen['settings']['dependency_identities']
    assert TARGET in dependency and 'dx100-e4fc4af-4c' not in dependency
    assert all('dx100.mmio' not in rid for rid in dependency)
    assert len([rid for rid in dependency if rid.startswith('dxc_') and rid.endswith('.functional-v1')])==9

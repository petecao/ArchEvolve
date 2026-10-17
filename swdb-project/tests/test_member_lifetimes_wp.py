"""Original Bag/Counter fixture through public WP setup (2026-10-15 ET).

Stand-in controls check admission/replay only. Actual controls separately require
all ordinary initialization/RTE obligations plus fresh smoke; no new requires.
"""
import hashlib
import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, run_swdb, make_records
from swdb import c_lowering
from test_formal_frame import frame_contract, write_library
from test_member_lifetimes import FIXTURE
from test_wp_adapter import fake, method_version, _hints, needs_wp
from test_wp_subset import GROUPS, SEEDED_BUGS

CID='contract.fixture_member_lifetime'


def public_seed(tmp_path, invalid=False):
    source=FIXTURE.read_text()
    if invalid:
        before,after=SEEDED_BUGS[0]
        assert before in source
        source=source.replace(before,after,1)
    records=make_records(tmp_path)
    library=tmp_path/'library';methods=library/'methods';methods.mkdir(parents=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method=method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    function,clauses,_arrays,hints=GROUPS['classes']
    entry=frame_contract(CID,role='enabling',
        concurrency_frame=[{'array':'a','shared_actions':[],'history_reads':False}],
        clauses=[{'id':name,'role':role,'statement':f'Original class fixture clause {name}.',
            'discharge_mode':'runtime_guard','negative_control':{'id':f'{name}-control','check':'fixture'},
            'acsl':{'text':text,'uses':[]},'proof_placement':{'once':'self'}} for name,role,text in clauses])
    entry['proof_unit']={'function':function,'source':{'root':'library','path':'proof_units/classes.cc',
        'sha256':hashlib.sha256(source.encode()).hexdigest()},'array_domains':{'a':{'extent':'n'}}}
    write_library(library,{'proof_units/classes.cc':source,'rewrite_contracts/member_lifetime.yaml':entry})
    hint_file=tmp_path/'class-hints.yaml'
    hint_file.write_text(yaml.safe_dump({'hints':[row for anchor,text in hints for row in _hints(anchor,*text.splitlines())]}))
    return records,method,hint_file


def prove(tmp_path,records,method,hints,**kwargs):
    return run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
        '--runs-dir',tmp_path/'runs','--summary',CID,'--hint-file',hints,'--format','json',**kwargs)


def test_public_original_classes_reaches_execution_with_exact_scalar_lifetimes(tmp_path):
    records,method,hints=public_seed(tmp_path)
    done=prove(tmp_path,records,method,hints,env=fake('unknown'))
    assert done.returncode==0,done.stdout+done.stderr
    row=yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['failure_class']=='unknown',row
    assert row['proof_setup_check']['verdict']=='passed'
    context=row['settings']['member_windows']['certificate']
    assert context['scalar_lifetimes'][0]['references'][0]['local']=='total'
    assert context['input_premises_added']==[]
    assert '-wp-no-filter-init' in row['settings']['flags']


@pytest.mark.parametrize('invalid',[False,True],ids=['safe','seeded_scaling_bug'])
@needs_wp
def test_actual_original_class_fixture_preserves_all_goal_and_smoke_acceptance(tmp_path,invalid):
    records,method,hints=public_seed(tmp_path,invalid)
    done=prove(tmp_path,records,method,hints,env={'SWDB_VERIFIER_RSS_CAP_BYTES':'8589934592'})
    assert done.returncode==0,done.stdout+done.stderr
    row=yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['verdict']==('not_proven' if invalid else 'proven'),row.get('unproven_properties')
    assert row.get('failure_class') not in {'unsupported_construct','parse_error'}
    assert row['proof_setup_check']['verdict']=='passed'
    assert row['settings']['member_windows']['certificate']['input_premises_added']==[]
    assert any(g.get('smoke') for g in row['goals'])
    assert any('rte_initialization' in g['goal'] for g in row['goals'] if not g.get('smoke'))
    if not invalid:
        assert row['goals'] and all(g['status']=='valid' for g in row['goals'])
    else:
        assert row['unproven_properties']

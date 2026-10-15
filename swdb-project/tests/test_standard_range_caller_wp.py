"""Public qualified std::copy caller proofs; created 2026-10-15 ET.

These are real WP controls, run serially under the shared verifier lock. A typed
window is an explicit input premise; physical validity does not enlarge it.
"""
import hashlib
import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, make_records, run_swdb
from swdb import c_lowering, standard_range_calls
from test_formal_frame import frame_contract, write_library
from test_wp_adapter import method_version, needs_wp

SOURCE = '''#include <algorithm>
int safe(int n) { int a[2]={7,9}; int b[2]={0,0}; std::copy(a,a+2,b); return b[1]; }
int empty(int n) { int a[1]; int b[1]; std::copy(a,a,b); return 0; }
int uninitialized(int n) { int a[1]; int b[1]={0}; std::copy(a,a+1,b); return 0; }
int capacity(int *out) { int a[2]={7,9}; std::copy(a,a+2,out); return 0; }
'''


@pytest.fixture(scope='module')
def qualified_callers(tmp_path_factory):
    if bool(c_lowering.locate().missing):pytest.skip('Clang22.1.8 required')
    root=tmp_path_factory.mktemp('qualified-copy-callers')
    records=make_records(root)
    library=root/'library';methods=library/'methods';methods.mkdir(parents=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method=method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    files={'proof_units/copy.cc':SOURCE}
    for name in ('safe','empty','uninitialized','capacity'):
        text=(r'requires \valid(out+(0..1)); assigns out[0..1]; ensures \result == 0;' if name=='capacity' else
              r'assigns \nothing; ensures \result == '+('9;' if name=='safe' else '0;'))
        entry=frame_contract('contract.fixture_copy_'+name,role='enabling',
            concurrency_frame=([{'array':'out','shared_actions':[],'history_reads':False}] if name=='capacity' else []),
            clauses=[{'id':'result','role':'postcondition','statement':'The checked copy has the specified scalar result.',
                'discharge_mode':'runtime_guard','negative_control':{'id':'copy-control','check':'fixture'},
                'acsl':{'text':text,'uses':[]},'proof_placement':{'once':'self'}}])
        entry['proof_unit']={'function':name,'source':{'root':'library','path':'proof_units/copy.cc',
             'sha256':hashlib.sha256(SOURCE.encode()).hexdigest()}}
        if name=='capacity':entry['proof_unit']['array_domains']={'out':{'extent':'1'}}
        files['rewrite_contracts/copy_'+name+'.yaml']=entry
    write_library(library,files)
    def prove(*args):
        done=run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
             '--runs-dir',root/'runs','--format','json',*args,
             env={'SWDB_VERIFIER_RSS_CAP_BYTES':'8589934592'})
        assert done.returncode==0,done.stdout+done.stderr
        return yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    model=prove('--model','std_copy_int')
    assert model['verdict']=='proven',model.get('unproven_properties')
    return prove,model


@needs_wp
@pytest.mark.parametrize('name,expected',[('safe','proven'),('empty','proven'),
    ('uninitialized','not_proven'),('capacity','not_proven')])
def test_exact_caller_range_requires_initialization_and_declared_capacity(qualified_callers,name,expected):
    prove,model=qualified_callers
    record=prove('--summary','contract.fixture_copy_'+name)
    assert record['verdict']==expected,record.get('unproven_properties')
    assert record['settings']['stdlib_provenance']['verdict']=='passed'
    assert record['pins']['standard_range_call_check']==standard_range_calls.identity()
    assert record['pins']['models'][0]['proof_record']==model['id']
    assert record['proof_setup_check']['verdict']=='passed'
    assert '-wp-no-filter-init' in record['settings']['flags']
    ordinary=[g for g in record['goals'] if not g.get('smoke')]
    assert any('swdb_window_copy_' in g['goal'] for g in ordinary)
    if expected=='proven':
        assert ordinary and any(g.get('smoke') for g in record['goals'])
        assert all(g['status']=='valid' for g in record['goals'])
    else:
        assert record['failure_class'] not in ('unsupported_construct','parse_error')
        needle='std_copy_int_requires' if name=='uninitialized' else 'swdb_window_copy_'
        assert any(needle in str(g) for g in record['unproven_properties'])

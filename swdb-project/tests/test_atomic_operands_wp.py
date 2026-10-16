"""Public WP admission refuses dropped atomic operands before launch, 2026-10-15 ET."""
import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES,REPO,make_records,run_swdb
from swdb import c_lowering
from test_formal_frame import frame_contract,write_library
from test_proof_records import _library_roots
from test_wp_adapter import ANCHOR_BEFORE,fake,method_version
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

CASES = {
    'load_side_effect':'__atomic_load_n(p,m++);',
    'success_side_effect':'__atomic_compare_exchange_n(p,e,9,false,m++,0);',
    'failure_side_effect':'__atomic_compare_exchange_n(p,e,9,false,5,m++);',
    'weak_side_effect':'__atomic_compare_exchange_n(p,e,9,(m++,false),5,0);',
    'weak_true':'__atomic_compare_exchange_n(p,e,9,true,5,0);',
    'weak_dynamic':'__atomic_compare_exchange_n(p,e,9,weak,5,0);',
    'order_dynamic':'__atomic_load_n(p,order);',
    'order_volatile':'__atomic_load_n(p,vorder);',
    'order_call':'__atomic_load_n(p,next_atomic_order());',
    'order_rte':'__atomic_load_n(p,0/order);',
    'invalid_load':'__atomic_load_n(p,3);',
    'invalid_store':'__atomic_store_n(p,1,2);',
    'invalid_cas_pair':'__atomic_compare_exchange_n(p,e,9,false,3,2);',
    'thread_fence':'__atomic_thread_fence(m++);',
    'signal_fence':'__atomic_signal_fence(m++);',
    'weak_enum_collision':'__atomic_compare_exchange_n(p,e,9,global_weak_value,5,0);',
    'order_enum_collision':'__atomic_load_n(p,global_bad_order);',
}
pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing),reason='Clang22.1.8 required')


@pytest.fixture(scope='module')
def atomic_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp('atomic-operands-public')
    records = make_records(root)
    copy_record_subset(REPO/'records',records.path,
        sorted(_library_roots() | {'gapbs-bfs-do','gapbs','dx100-gapbs','mbit10'}))
    library = root/'library';shutil.copytree(REPO/'library',library)
    methods = library/'methods';methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method = method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method))
    source = ''.join(f'int atomic_control_{case}() {{ return 0; }}\n' for case in CASES)
    cid = 'contract.fixture_atomic_operands'
    entry = frame_contract(cid,role='enabling',concurrency_frame=[],clauses=[
        {'id':'post','role':'postcondition','statement':'The ordinary context returns zero.',
         'discharge_mode':'runtime_guard','negative_control':{'id':'post-control','check':'fixture'},
         'acsl':{'text':r'assigns \nothing; ensures \result == 0;','uses':[]},'proof_placement':'per_candidate'}])
    files = {'proof_units/atomic_context.cc':source}
    for case in CASES:
        item = dict(entry,id=cid+'_'+case,proof_unit={'function':'atomic_control_'+case,'source':{'root':'library',
            'path':'proof_units/atomic_context.cc','sha256':hashlib.sha256(source.encode()).hexdigest()}})
        files['rewrite_contracts/atomic_operands_'+case+'.yaml'] = item
    write_library(library,files)
    records,runs,_snapshot,request = build_proposal_setup(records,root,copy_all=False)
    units = ('int next_atomic_order() { return 0; }\n'
        'int unrelated_weak() { enum WeakFlag { global_weak_value=0 }; return 0; }\n'
        'enum WeakFlag { global_weak_value=1 };\n'
        'int unrelated_order() { enum OrderFlag { global_bad_order=0 }; return 0; }\n'
        'enum OrderFlag { global_bad_order=3 };\n')+'\n'.join(
        f'int atomic_control_{name}(int *p,int *e,int order,bool weak,volatile int vorder) {{\n'
        f'  int m=0;\n  {statement}\n  return m;\n}}' for name,statement in CASES.items())
    done = records.swdb('submit',request(ANCHOR_BEFORE,units+'\n'+ANCHOR_BEFORE,id='atomic-operands'),
        '--runs-dir',runs,'--format','json')
    assert done.returncode==0,done.stdout+done.stderr
    return root,records,method,cid,json.loads(done.stdout)['candidate']


@pytest.mark.parametrize('case',CASES)
def test_public_atomic_operand_refusal_precedes_any_wp_launch(atomic_seed,case):
    root,records,method,cid,candidate = atomic_seed
    done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
        '--runs-dir',root/'proof-runs','--candidate',candidate,'--function',f'atomic_control_{case}',
        '--contract',cid+'_'+case,'--format','json',env=fake('unknown'))
    assert done.returncode==0,done.stdout+done.stderr
    row = yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['verdict']=='not_proven' and row['failure_class']=='unsupported_construct',row
    assert not row.get('settings',{}).get('verifier_launched') and row['goals']==[]
    assert not any(v['name']=='wp_input' for v in row['evidence']['reports'])
    handler, = [v for v in row['evidence']['reports'] if v['name']=='handler']
    data = Path(handler['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==handler['sha256']
    why = json.loads(data)['why']
    assert 'atomic ' in why and re.search(r'bfs\.cc line \d+',why),why


def test_stale_atomic_translator_pin_stops_without_a_new_proof_record(atomic_seed):
    root,records,method,cid,candidate = atomic_seed
    stale = json.loads(json.dumps(method))
    stale['id'] = 'method.atomic-stale-translator'
    stale['sequence'] = max(yaml.safe_load(p.read_text())['sequence']
                            for p in (root/'library/methods').glob('*.yaml'))+1
    stale['c_lowering']['translators'][0]['sha256'] = '0'*64
    (root/'library/methods/atomic-stale-translator.yaml').write_text(yaml.safe_dump(stale))
    before = set((records.path/'proofs').glob('*.yaml'))
    done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',stale['id'],
        '--runs-dir',root/'proof-runs','--candidate',candidate,'--function','atomic_control_thread_fence',
        '--contract',cid+'_thread_fence','--format','json',env=fake('unknown'))
    assert done.returncode!=0 and 'the C lowering tool' in done.stderr,done.stdout+done.stderr
    assert set((records.path/'proofs').glob('*.yaml'))==before

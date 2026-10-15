"""Required unsupported groups through public WP admission, 2026-10-15 ET.

All seven actual submitted source functions must refuse before verifier launch.
The library contract itself targets a separate ordinary valid fixture, so an
unsupported candidate cannot be mistaken for an invalid library definition.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES,REPO,make_records,run_swdb
from swdb import c_lowering
from test_c_lowering import OUTSIDE
from test_formal_frame import frame_contract,write_library
from test_proof_records import _library_roots
from test_wp_adapter import ANCHOR_BEFORE,fake,method_version
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

KINDS = ('inheritance','virtual function','exception','lambda','RTTI','standard container std::map','stream')
pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing),reason='Clang22.1.8 required')


@pytest.fixture(scope='module')
def seed(tmp_path_factory):
    root = tmp_path_factory.mktemp('unsupported-groups-public')
    records = make_records(root)
    copy_record_subset(REPO/'records',records.path,
        sorted(_library_roots() | {'gapbs-bfs-do','gapbs','dx100-gapbs','mbit10'}))
    library = root/'library';shutil.copytree(REPO/'library',library)
    methods = library/'methods';methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method = method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method))
    source = 'int fixture_admission_context() { return 0; }\n'
    cid = 'contract.fixture_unsupported_groups'
    entry = frame_contract(cid,role='enabling',concurrency_frame=[],clauses=[
        {'id':'post','role':'postcondition','statement':'The ordinary contract fixture returns zero.',
         'discharge_mode':'runtime_guard','negative_control':{'id':'post-control','check':'fixture'},
         'acsl':{'text':r'assigns \nothing; ensures \result == 0;','uses':[]},'proof_placement':'per_candidate'}])
    entry['proof_unit'] = {'function':'fixture_admission_context','source':{'root':'library',
        'path':'proof_units/unsupported_context.cc','sha256':hashlib.sha256(source.encode()).hexdigest()}}
    write_library(library,{'proof_units/unsupported_context.cc':source,'rewrite_contracts/unsupported_groups.yaml':entry})
    records,runs,_snapshot,request = build_proposal_setup(records,root,copy_all=False)
    unit_source = '\n'.join(OUTSIDE[kind].replace('swdb_outside_unit',f'outside_group_{i}') for i,kind in enumerate(KINDS))
    done = records.swdb('submit',request(ANCHOR_BEFORE,unit_source+'\n'+ANCHOR_BEFORE,id='outside-groups'),
        '--runs-dir',runs,'--format','json')
    assert done.returncode == 0,done.stdout+done.stderr
    return root,records,method,cid,json.loads(done.stdout)['candidate']


@pytest.mark.parametrize('kind',KINDS)
def test_each_required_unsupported_construct_reads_not_proven_before_any_wp_launch(seed,kind):
    root,records,method,cid,candidate = seed
    function = f'outside_group_{KINDS.index(kind)}'
    done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
        '--runs-dir',root/'proof-runs','--candidate',candidate,'--function',function,'--contract',cid,
        '--format','json',env=fake('unknown'))
    assert done.returncode == 0,done.stdout+done.stderr
    row = yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['verdict'] == 'not_proven' and row['failure_class'] == 'unsupported_construct',row
    assert row['goals'] == []
    assert not row.get('settings',{}).get('verifier_launched')
    assert not any(v['name']=='wp_input' for v in row.get('evidence',{}).get('reports',[]))
    handler, = [v for v in row['evidence']['reports'] if v['name']=='handler']
    handler_bytes = Path(handler['path']).read_bytes()
    assert hashlib.sha256(handler_bytes).hexdigest() == handler['sha256']
    text = json.loads(handler_bytes)['why']
    assert kind in text,text
    assert re.search(r'bfs\.cc line \d+',text),text

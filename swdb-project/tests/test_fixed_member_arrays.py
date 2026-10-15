"""Exact automatic fixed-array subobjects through lower/prepare, 2026-10-15 ET."""
from pathlib import Path
import pytest
from swdb import c_lowering, wp_pointer_bounds

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')
ORIGINAL = Path(__file__).parent/'fixtures/proof/lowering/templates.cc'


def lower(tmp_path, text=None):
    path = tmp_path/'templates.cc'
    path.write_text(ORIGINAL.read_text() if text is None else text)
    return c_lowering.lower(path, 'swdb_template_unit')


def test_original_two_instantiations_keep_exact_fixed_member_subobjects(tmp_path):
    lowered = lower(tmp_path)
    report = wp_pointer_bounds.check(lowered)
    cert = report['member_windows']
    assert cert['input_premises_added'] == []
    assert cert['protocol'] == 'closed-automatic-fixed-member-arrays-1'
    assert {(a['origin']['element_type'],a['origin']['elements']) for a in cert['accesses']} == {('int',3),('long',2)}
    assert cert['entry'] == 'swdb_template_unit'
    assert set(cert['inline_functions']) == {'twice_int','twice_long','Ring_int_3_put','Ring_int_3_get','Ring_long_2_put','Ring_long_2_get'}
    text, _ = wp_pointer_bounds.prepare(lowered, lowered.text)
    assert 'this->items[this->head % 3] = v' in text
    assert 'requires' not in text


@pytest.mark.parametrize('change', [
    lambda s:s.replace('Ring<int, 3> r;', 'Ring<int, 3> r; Ring<int, 3> alias = r;'),
    lambda s:s.replace('r.head = 0;', 'Ring<int, 3> *alias = &r; r.head = 0;'),
    lambda s:s.replace('int swdb_template_unit(int a, long b)', 'int swdb_template_unit(int a, long b, Ring<int,3> &other)').replace('return r.get(1)', 'return other.get(1)'),
    lambda s:s.replace('T items[N];', 'T items[N][2];').replace('items[head % N] = v;', 'items[head % N][0] = v;').replace('return items[i % N];','return items[i % N][0];'),
])
def test_copy_alias_arbitrary_receiver_and_multidimensional_subobjects_refuse(tmp_path, change):
    with pytest.raises((wp_pointer_bounds.Refused,c_lowering.Unsupported)):
        wp_pointer_bounds.check(lower(tmp_path,change(ORIGINAL.read_text())))


def test_changed_original_receiver_graph_fails_independent_source_reparse(tmp_path):
    lowered = lower(tmp_path)
    path = tmp_path/'templates.cc'
    path.write_text(path.read_text().replace('return r.get(1)', 'return r.get(0)'))
    with pytest.raises(wp_pointer_bounds.Refused,match='changed after planning'):
        wp_pointer_bounds.recheck_source(lowered,{'source':str(path),'kwargs':{}})


def test_public_original_templates_keeps_closed_context_and_mandatory_rte_policy(tmp_path):
    import hashlib,json,shutil,yaml
    from conftest import FIXTURES,make_records,run_swdb
    from test_formal_frame import frame_contract,write_library
    from test_wp_adapter import fake,method_version
    from test_wp_subset import GROUPS
    records = make_records(tmp_path)
    methods = tmp_path/'library/methods'; methods.mkdir(parents=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method = method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method))
    source = ORIGINAL.read_text()
    function,clauses,_arrays,_hints = GROUPS['templates']
    entry = frame_contract('contract.fixture_fixed_arrays',role='enabling',concurrency_frame=[],clauses=[
        {'id':cid,'role':role,'statement':f'Original templates clause {cid}.','discharge_mode':'runtime_guard',
         'negative_control':{'id':cid+'-control','check':'fixture'},'acsl':{'text':text,'uses':[]},
         'proof_placement':{'once':'self'}} for cid,role,text in clauses])
    entry['proof_unit'] = {'function':function,'source':{'root':'library','path':'proof_units/templates.cc',
        'sha256':hashlib.sha256(source.encode()).hexdigest()}}
    write_library(tmp_path/'library',{'proof_units/templates.cc':source,'rewrite_contracts/fixed.yaml':entry})
    done = run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
        '--runs-dir',tmp_path/'runs','--summary',entry['id'],'--format','json',env=fake('unknown'))
    assert done.returncode == 0,done.stdout+done.stderr
    row = yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['failure_class'] == 'unknown',row
    assert row['proof_setup_check']['verdict'] == 'passed'
    assert row['settings']['member_windows']['certificate']['input_premises_added'] == []
    assert '-wp-rte' in row['settings']['flags']
    assert '-wp-no-filter-init' in row['settings']['flags']

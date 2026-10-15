"""Public WP footprint-query source view, 2026-10-15 ET."""
import json
import yaml
import pytest
from conftest import run_swdb
from test_proof_semantics import dx,dx_seed
from test_wp_adapter import fake,needs_wp


def qualify(dx):
    path=dx.root/'library/rewrite_contracts/fixture_dx_footprint.yaml'
    data=yaml.safe_load(path.read_text())
    data['proof_unit']['array_domains']={name:{'extent':'n'} for name in ('q','base')}
    path.write_text(yaml.safe_dump(data,sort_keys=False))


@needs_wp
def test_the_original_gather_footprint_query_reaches_wp_with_ordered_source_reads(dx):
    qualify(dx)
    result=run_swdb('prove','--records',dx.records,'--candidate',dx.candidates['dx'],
        '--function','dxf_footprint','--contract','contract.fixture_dx_footprint',
        '--adapter','wp','--runs-dir',dx.runs,'--format','json',env=fake('unknown'),timeout=600)
    assert result.returncode==0,result.stderr+result.stdout
    row=dx.read(json.loads(result.stdout))
    assert row['failure_class']=='unknown',row
    assert row['proof_setup_check']['verdict']=='passed'
    nested=row['settings']['nested_entry_reads']
    assert len(nested['certificate']['captures'])==1
    assert nested['certificate']['captures'][0]['context']=='query_address'
    assert nested['input_premises_added']==[]
    assert row['settings']['helper_windows']['certificate']['context_count']==1


@needs_wp
@pytest.mark.parametrize('outside',[False,True])
def test_actual_original_footprint_query_and_outside_value_control(dx,outside):
    from test_proof_semantics import prove_wp
    qualify(dx)
    row=prove_wp(dx,'footprint',*(['SWDB_OUTSIDE'] if outside else []))
    assert row['proof_setup_check']['verdict']=='passed'
    assert row['verdict']==('not_proven' if outside else 'proven'),row.get('unproven_properties')
    assert row['settings']['verifier_launched'] is True
    if outside:
        # The generated null+zero normalization branch is unreachable under
        # the original n>=1 precondition. Preserve that negative smoke outcome;
        # the original value postcondition must independently remain open.
        assert any(g['status']!='valid' and 'ensures' in g['goal'] for g in row['goals']),row
        assert all(g['status']=='valid' for g in row['goals'] if not g.get('smoke') and 'ensures' not in g['goal'])
        assert row['failure_class'] in {'unknown','timeout','vacuous_pass'}
    else:
        assert all(g['status']=='valid' for g in row['goals'] if g.get('smoke'))
        assert len(row['settings']['nested_entry_reads']['certificate']['captures'])==1

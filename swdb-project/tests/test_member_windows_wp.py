"""Actual WP controls for the selected-entry member window (2026-10-15 ET).

One getter on one automatic receiver; these do not establish the full class,
constructor/destructor or fixed member-array acceptance frontier.
"""
import json

import pytest
import yaml

from conftest import run_swdb
from test_member_windows import SOURCE,public_seed
from test_wp_adapter import needs_wp


@needs_wp
@pytest.mark.parametrize('invalid_index',[False,True])
def test_original_member_read_requires_ordinary_field_init_and_exact_numeric_window(tmp_path,invalid_index):
    source=SOURCE.replace('b.get(0)','b.get(n)') if invalid_index else SOURCE
    records,method=public_seed(tmp_path,source)
    done=run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
          '--runs-dir',tmp_path/'runs','--summary','contract.fixture_member','--format','json',
          env={'SWDB_VERIFIER_RSS_CAP_BYTES':'8589934592'})
    assert done.returncode==0,done.stdout+done.stderr
    row=yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['verdict']==('not_proven' if invalid_index else 'proven'),row.get('unproven_properties')
    assert row['settings']['member_windows']['certificate']['input_premises_added']==[]
    assert row['proof_setup_check']['verdict']=='passed'
    assert row['settings']['flags'].count('-wp-no-filter-init')==1
    assert row['settings']['flags'].count('-wp-fct=unit')==1
    assert row['settings']['flags'].count('-inline-calls=Buffer_get')==1
    assert any(g.get('smoke') for g in row['goals'])
    assert any('swdb_window_access_' in g['goal'] for g in row['goals'] if not g.get('smoke'))
    if invalid_index:
        assert row['failure_class'] not in {'unsupported_construct','parse_error'}
        assert any('swdb_window_access_' in str(g) for g in row['unproven_properties'])
    else:
        assert row['goals'] and all(g['status']=='valid' for g in row['goals'])
        assert any('rte_initialization' in g['goal'] for g in row['goals'] if not g.get('smoke'))

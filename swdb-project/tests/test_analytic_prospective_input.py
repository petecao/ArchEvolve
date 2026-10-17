"""Prospective generator identity only; no graph execution. Updated: 2026-10-06 ET."""
import pytest
import json
from conftest import run_swdb
from swdb.store import Store


@pytest.mark.parametrize('implementation',['gapbs-bfs-do','gapbs-bc-brandes'])
def test_registered_g17_input_reaches_toolchain_gate_without_build_or_execution(records,tmp_path,implementation):
    records.copy_repo()
    output=tmp_path/'not-built'
    result=run_swdb('characterize','--records',records.path,'--adapter','registered-gapbs',
        '--implementation',implementation,'--input','kron-g17-k16','--threads','1','--trials','5',
        '--object-scopes','--counting-pipeline','source-normalized-v2','--id','fixture.g17.preparation',
        '--llvm-bin',tmp_path/'intentionally-unavailable-llvm','--output',output)
    assert result.returncode==1
    assert 'LLVM 22 is required' in result.stderr
    assert not output.exists()
    assert not (records.path/'workload_characterizations/fixture.g17.preparation.yaml').exists()


def test_prospective_g17_metadata_and_public_view_keep_realized_counts_unknown(records):
    records.copy_repo()
    store=Store(records.path);data=store.get('kron-g17-k16','input');baseline=store.get('kron-g16-k16','input')
    assert data['generator']==dict(baseline['generator'],arguments='-g 17 -k 16')
    assert data['properties']['scale']['value']==17
    assert data['properties']['requested_degree']['value']==16
    assert data['extensions']['prospective_generator_contract']['fixed_seed']['value']==27491095
    assert all(data['properties'][name]['value'] is None and data['properties'][name]['basis']=='unknown'
        for name in ('num_nodes','num_edges_undirected','num_edges_directed','input_density'))
    assert all(item['kind']=='source_code' for item in data['provenance'])
    assert not any(item.get('basis')=='measured' for item in data['properties'].values())
    result=run_swdb('view','gapbs-bfs-do','kron-g17-k16','mbit10','--records',records.path,'--format','json')
    assert result.returncode==0,result.stdout+result.stderr
    view=json.loads(result.stdout)
    assert view['workload_id']=='gapbs-bfs-do@kron-g17-k16@mbit10'
    assert view['metrics']==[]
    assert any('No profile: counts, metrics, and bottleneck are unknown.' in note for note in view['notes'])

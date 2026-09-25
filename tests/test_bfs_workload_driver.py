"""Public registration verifies the campaign's SG widening. Updated 2026-09-25."""
import importlib.util
import json
from pathlib import Path

import pytest

from conftest import REPO
from test_bfs_protocol import _hash, _payload, _workload_request


@pytest.mark.parametrize('directed',[True,False])
def test_widened_graph_has_the_same_loaded_adjacency(records,tmp_path,directed):
    records.copy_repo()
    graph={'num_vertices':6,'directed':directed,'edges':[[0,1],[0,2],[1,3],[2,3]]}
    request=_workload_request(records,tmp_path,graph)
    spec=importlib.util.spec_from_file_location('workload_driver',REPO/'scripts/bfs_generate_workload.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    by_app={r.get('application'):r for r in request['representations']}
    source=Path(by_app['dx100-gapbs']['path'])
    target=tmp_path/'widened.sg64'
    module.widen_sg(source,target)
    by_app['gapbs'].update(path=str(target),sha256=_hash(target))
    request['parser']={'work_dir':str(tmp_path/'parser'),'timeout_s':30}
    result=records.swdb('register-workload',_payload(tmp_path,'widened',request),'--format','json')
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout)
    assert len({r['canonical_sha256'] for r in data['definition']['representations']})==1
    assert data['definition']['realized']['num_vertices']==6

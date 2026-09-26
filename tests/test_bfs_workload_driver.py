"""Public registration verifies the campaign's SG widening. Updated 2026-09-25."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from conftest import REPO
from test_bfs_protocol import _hash, _payload, _workload_request


def test_pinned_converter_enables_symmetrization_for_synthetic_inputs(tmp_path):
    """Exercise the actual parser: absence of -s is not directed generation."""
    compiler=shutil.which('clang++') or shutil.which('g++')
    if compiler is None:
        pytest.skip('C++ compiler unavailable')
    source=tmp_path/'parser.cc'
    source.write_text('#include "command_line.h"\n'
                      'int main(int argc,char** argv) {'
                      ' CLConvert cli(argc,argv,"probe");'
                      ' if (!cli.ParseArgs()) return 2;'
                      ' std::cout << cli.symmetrize() << " " << cli.scale()'
                      ' << " " << cli.degree() << "\\n"; }\n')
    binary=tmp_path/'parser'
    built=subprocess.run([compiler,'-std=c++11','-I'+str(REPO/'apps/dx100/benchmarks/gapbs/src'),
                          str(source),'-o',str(binary)],capture_output=True,text=True,timeout=30)
    assert built.returncode==0,built.stderr
    for options,expected in [(['-u','18'],'1 18 16'),(['-g','18'],'1 18 16'),
                             (['-f','input.el'],'0 -1 16'),(['-s','-f','input.el'],'1 -1 16')]:
        result=subprocess.run([str(binary),*options,'-b','output.sg'],
                              capture_output=True,text=True,timeout=5)
        assert result.returncode==0,result.stderr
        assert result.stdout.strip()==expected


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

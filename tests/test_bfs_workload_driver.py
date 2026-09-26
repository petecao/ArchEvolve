"""Public registration verifies the campaign's SG widening. Updated 2026-09-25."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from conftest import REPO
from test_bfs_protocol import _hash, _payload, _workload_request, _sg


@pytest.mark.parametrize('width', [32, 64])
def test_generated_filenames_load_with_pinned_builder_and_source_picker(tmp_path, width):
    compiler=shutil.which('g++') or shutil.which('clang++')
    flags=['-std=c++11','-fopenmp']
    if sys.platform=='darwin':
        compiler='/opt/homebrew/opt/llvm/bin/clang++'
        runtime=Path('/opt/homebrew/opt/libomp')
        if not Path(compiler).is_file() or not (runtime/'lib/libomp.dylib').is_file():
            pytest.skip('pinned DX100 Builder requires an installed OpenMP C++ compiler/runtime')
        flags += ['-I'+str(runtime/'include'),'-L'+str(runtime/'lib'),'-Wl,-rpath,'+str(runtime/'lib')]
    if compiler is None:
        pytest.skip('C++ compiler unavailable')
    spec=importlib.util.spec_from_file_location('workload_driver',REPO/'scripts/bfs_generate_workload.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    path=module.serialized_paths(tmp_path)[0 if width==32 else 1]
    graph={'num_vertices':6,'directed':False,'edges':[[0,1],[1,2],[2,3]]}
    path.write_bytes(_sg(graph, width//8))
    source=tmp_path/'picker.cc'
    source.write_text('#include "benchmark.h"\n#include "command_line.h"\n'
        'int main(int argc,char** argv) {'
        ' CLBase cli(argc,argv,"source-picker"); if (!cli.ParseArgs()) return 2;'
        ' Builder builder(cli); Graph graph=builder.MakeGraph(); SourcePicker<Graph> picker(graph);'
        ' int source=picker.PickNext(); std::cout << "SWDB_GRAPH " << graph.num_nodes()'
        ' << " " << graph.num_edges_directed() << " " << source << " " << graph.out_degree(source) << "\\n"; }\n')
    headers=REPO/('apps/dx100/benchmarks/gapbs/src' if width==32 else 'apps/gapbs/src')
    binary=tmp_path/'picker'
    built=subprocess.run([compiler,*flags,'-I'+str(headers),str(source),'-o',str(binary)],
                         capture_output=True,text=True,timeout=30)
    assert built.returncode==0,built.stderr
    first=subprocess.run([str(binary),'-f',str(path)],capture_output=True,text=True,timeout=5)
    assert first.returncode==0,first.stdout+first.stderr
    actual=[line.split()[1:] for line in first.stdout.splitlines() if line.startswith('SWDB_GRAPH ')]
    assert len(actual)==1
    vertices,arcs,selected,degree=map(int,actual[0])
    assert (vertices,arcs)==(6,6) and 0<=selected<=3 and degree>0
    second=subprocess.run([str(binary),'-f',str(path)],capture_output=True,text=True,timeout=5)
    assert [line for line in first.stdout.splitlines() if line.startswith('SWDB_GRAPH ')] == [
        line for line in second.stdout.splitlines() if line.startswith('SWDB_GRAPH ')]
    unsupported=tmp_path/('old.sg32' if width==32 else 'old.sg64')
    unsupported.write_bytes(path.read_bytes())
    rejected=subprocess.run([str(binary),'-f',str(unsupported)],capture_output=True,text=True,timeout=5)
    assert rejected.returncode!=0 and 'Unrecognized suffix' in rejected.stdout


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

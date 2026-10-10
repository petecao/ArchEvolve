"""Public registration verifies the campaign's SG widening. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-25."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

import pytest

from conftest import REPO
from testkit.bfs_protocol import _hash, _payload, _workload_request, _sg
from testkit.toolchain import find_cxx, load_script


@pytest.mark.parametrize('interruption', ['deadline', 'signal'])
def test_generator_interrupt_reaps_nested_registration_and_retains_logs(tmp_path, monkeypatch, interruption):
    module = load_script(REPO/'scripts/bfs_generate_workload.py', 'workload_cleanup')
    source=tmp_path/'apps/dx100/benchmarks/gapbs/src'
    source.mkdir(parents=True);(source/'converter.cc').write_text('// explicit compiler fixture\n')
    graph=_sg({'num_vertices':6,'directed':False,'edges':[[0,1],[1,2]]},4)
    converter_code=f'#!{sys.executable}\nimport pathlib,sys\npathlib.Path(sys.argv[-1]).write_bytes({graph!r})\n'
    binaries=tmp_path/'bin';binaries.mkdir()
    compiler=binaries/'g++'
    compiler.write_text(f'#!{sys.executable}\nimport pathlib,sys\np=pathlib.Path(sys.argv[-1]);p.write_text({converter_code!r});p.chmod(0o755)\n')
    compiler.chmod(0o755)
    package=tmp_path/'swdb';package.mkdir()
    (package/'__main__.py').write_text('''import os,pathlib,signal,subprocess,sys,time
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
def stop(signum,frame):
 os.killpg(child.pid,signal.SIGTERM)
 child.wait(timeout=5)
 print('FIXTURE_REGISTER_REAPED',flush=True)
 sys.exit(143)
signal.signal(signal.SIGTERM,stop)
pathlib.Path('nested.pid').write_text(str(child.pid))
if os.environ['GENERATOR_FIXTURE_INTERRUPT']=='signal': os.kill(os.getppid(),signal.SIGTERM)
time.sleep(60)
''')
    class FixtureStore:
        def get(self,*args): return {}
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'Store',lambda path:FixtureStore())
    monkeypatch.setattr(module.socket,'gethostname',lambda:'mbit10')
    monkeypatch.setattr(module.profile,'_verified_lane',lambda *args:None)
    # This Mac fixture tests process ownership, not Linux RLIMIT_AS enforcement.
    monkeypatch.setattr(module.resource,'setrlimit',lambda *args:None)
    monkeypatch.setattr(module.subprocess,'check_output',lambda *args,**kwargs:'fixture-commit\n')
    monkeypatch.setattr(module,'OUTER_SECONDS',3)
    monkeypatch.setattr(module,'CLEANUP_RESERVE_SECONDS',1)
    monkeypatch.setenv('PATH',str(binaries)+os.pathsep+os.environ['PATH'])
    monkeypatch.setenv('GENERATOR_FIXTURE_INTERRUPT',interruption)
    build,runs=tmp_path/'builds',tmp_path/'runs'
    parents=Path.parents
    def fixture_parents(path):
        actual=parents.__get__(path)
        if path in (build/'fixture',runs/'fixture'):
            return (*actual,Path('/data1/yanruj'))
        return actual
    monkeypatch.setattr(Path,'parents',property(fixture_parents))
    monkeypatch.setattr(sys,'argv',[str(REPO/'scripts/bfs_generate_workload.py'),'--id','fixture',
        '--family','uniform_random','--scale','14','--sources','0','--records',str(tmp_path/'records'),
        '--build-dir',str(build),'--runs-dir',str(runs),'--lane','mbit10-evaluation-node1'])
    original={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    expected=subprocess.TimeoutExpired if interruption=='deadline' else InterruptedError
    with pytest.raises(expected): module.main()
    assert all(signal.getsignal(sig)==handler for sig,handler in original.items())
    receipt=json.loads((runs/'fixture/driver.json').read_text())
    assert receipt['state']=='failed'
    stage=receipt['stages'][-1]
    assert stage['stage']=='register' and stage['state']=='interrupted_or_timeout'
    assert stage['returncode']==143 and stage['host_wall_s']<3
    assert stage['stdout_sha256']==_hash(runs/'fixture/register.stdout')
    assert stage['stderr_sha256']==_hash(runs/'fixture/register.stderr')
    assert 'FIXTURE_REGISTER_REAPED' in (runs/'fixture/register.stdout').read_text()
    with pytest.raises(ProcessLookupError): os.kill(int((tmp_path/'nested.pid').read_text()),0)


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
    module = load_script(REPO/'scripts/bfs_generate_workload.py', 'workload_driver')
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
    compiler=find_cxx()
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
    module = load_script(REPO/'scripts/bfs_generate_workload.py', 'workload_driver')
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

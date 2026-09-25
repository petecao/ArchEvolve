"""Compiler discovery and public diagnostic contracts. Updated 2026-09-25.

Local toy compilation is integration evidence, not native BFS acceptance.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from test_bfs_native import evaluation_setup, evaluate
from test_proposals import proposal_setup
from swdb.bfs_discovery import discover, instrument
from swdb.bfs_profiling import parse_callgrind, _discovery_settings
from swdb.cli import Failure


def compiler_inventory():
    for library in ['/opt/homebrew/opt/llvm/lib/libclang.dylib', '/data1/yanruj/llvm18/lib/libclang.so', '/usr/lib/llvm-18/lib/libclang.so.1']:
        if Path(library).is_file():
            resource = sorted((Path(library).parent/'clang').glob('*'))
            arguments = ['-std=c++11', '-fno-openmp', '-Wno-unknown-pragmas']
            if resource: arguments += ['-resource-dir',str(resource[-1])]
            if Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk').exists():
                arguments += ['-isysroot','/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk']
            return library,arguments
    pytest.skip('libclang unavailable; real remote acceptance remains required')


def test_new_helper_nested_scopes_and_single_statement_loops_execute(tmp_path):
    library,args=compiler_inventory()
    source=tmp_path/'toy.cc'
    source.write_text('''
volatile unsigned sink = 0;
unsigned NewlyIntroducedHelper(unsigned n) {
  for(unsigned i=0;i<n;++i) for(unsigned j=0;j<10;++j) sink += i+j;
  unsigned k=0; do ++k; while(k<n);
  return k;
}
unsigned Caller(unsigned n) { return NewlyIntroducedHelper(n); }
''')
    discovery=discover(source,args,library)
    regions=discovery['regions']
    assert {r['name'] for r in regions if r['kind']=='function'} == {'Caller','NewlyIntroducedHelper'}
    assert len([r for r in regions if r['kind']=='loop']) == 3
    assert next(r for r in regions if r['name']=='NewlyIntroducedHelper')['callers']==['Caller']
    rewritten=tmp_path/'instrumented.cc';rewritten.write_bytes(instrument(source,regions))
    driver=tmp_path/'driver.cc';output=tmp_path/'counters.json'
    driver.write_text(f'#define SWDB_REGION_COUNT {len(regions)}\n#include "{REPO}/tools/bfs_profile/runtime.hpp"\n'
        f'#include "{rewritten}"\nint main() {{ swdb_profile::start(); Caller(100); swdb_profile::stop(); swdb_profile::write("{output}"); }}\n')
    compiler=shutil.which('clang++') or shutil.which('g++')
    if not compiler: pytest.skip('C++ compiler unavailable')
    result=subprocess.run([compiler,'-std=c++11','-O2',str(driver),'-o',str(tmp_path/'program')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    subprocess.run([str(tmp_path/'program')],check=True)
    value=json.loads(output.read_text())
    assert value['errors']==0
    rows=value['regions']
    assert all(r['invocations']>0 and r['inclusive_ns']>=r['exclusive_ns']>=0 for r in rows)
    caller=rows[next(i for i,r in enumerate(regions) if r['name']=='Caller')]
    helper=rows[next(i for i,r in enumerate(regions) if r['name']=='NewlyIntroducedHelper')]
    assert caller['inclusive_ns']>=helper['inclusive_ns']
    assert caller['exclusive_ns']<caller['inclusive_ns']


def test_discovery_fails_closed_on_missing_headers_and_skips_unsafe_openmp(tmp_path):
    library,args=compiler_inventory()
    source=tmp_path/'toy.cc';source.write_text('#include "missing-proof.h"\nint f(){return 1;}\n')
    with pytest.raises(ValueError,match='diagnostics'):
        discover(source,args,library)
    source.write_text('''void f(int *a) {
#pragma omp parallel for collapse(2)
for(int i=0;i<4;++i) for(int j=0;j<4;++j) a[i*4+j]=i+j;
}''')
    result=discover(source,args,library)
    assert result['unresolved'] and not any(r['kind']=='loop' for r in result['regions'])


def test_openmp_loop_iteration_is_guarded_on_executing_worker(tmp_path):
    library,args=compiler_inventory()
    source=tmp_path/'toy.cc';source.write_text('''void f(int *a) {
#pragma omp parallel for
for(int i=0;i<4;++i) a[i]=i;
}''')
    result=discover(source,args,library)
    loop=next(r for r in result['regions'] if r['kind']=='loop')
    assert loop['invocation_unit']=='OpenMP loop iteration on the executing worker thread'
    changed=instrument(source,result['regions']).decode()
    assert '#pragma omp parallel for\nfor(int i=0;i<4;++i) {' in changed
    assert changed.count('a[i]=i;')==1


def test_gcc_prefix_restrict_inventory_keeps_original_source_extents(tmp_path):
    library, args = compiler_inventory()
    source = tmp_path/'gnu.cc'
    original = 'unsigned f(unsigned *input){__restrict__ unsigned *p=input;for(unsigned i=0;i<4;++i)p[i]+=1;return p[0];}\n'
    source.write_text(original)
    with pytest.raises(ValueError, match=r'gnu.cc:1:.*restrict'):
        discover(source, args, library)
    macros = tmp_path/'macros.log'; macros.write_text('#define __GNUC__ 13\n#define _OPENMP 201511\n')
    _, adapted = _discovery_settings({'discovery': {'library': library, 'arguments': args}}, 'g++', ['-std=c++11'], [], macros)
    assert '-D__restrict__=' in adapted
    result = discover(source, adapted, library)
    assert result['parser_adaptations'] and 'alias semantics are not inferred' in result['parser_adaptations'][0]
    assert len([r for r in result['regions'] if r['kind']=='loop']) == 1
    rewritten = instrument(source, result['regions']).decode()
    assert '__restrict__ unsigned *p=input;' in rewritten and source.read_text()==original
    macros.write_text('#define __GNUC__ 4\n#define __clang__ 1\n')
    _, clang_args = _discovery_settings({'discovery': {'library': library}}, 'clang++', [], [], macros)
    assert '-D__restrict__=' not in clang_args


def test_pinned_dx100_complete_translation_unit_has_no_parser_errors(tmp_path):
    library, args = compiler_inventory()
    source = REPO/'apps/dx100/benchmarks/gapbs/src/bfs.cc'
    if not source.is_file(): pytest.skip('pinned DX100 checkout unavailable')
    compiler = shutil.which('clang++') or shutil.which('g++')
    if not compiler: pytest.skip('C++ compiler unavailable')
    probe = subprocess.run([compiler, '-dM', '-E', '-v', '-x', 'c++', '/dev/null'], capture_output=True, text=True, check=True)
    macro = tmp_path/'macros.log'; macro.write_text(probe.stdout+probe.stderr)
    # This verifies the GCC-authored pinned source even on the Mac/Clang test host.
    _, adapted = _discovery_settings({'discovery': {'library': library, 'arguments': args+['-D__restrict__=','-D_OPENMP=201511']}},
        compiler, ['-std=c++11','-DFUNC'], [source.parent, REPO/'apps/dx100/benchmarks/API'], macro)
    original = source.read_bytes()
    result = discover(source, adapted, library)
    assert not any(d['severity']>=3 for d in result['diagnostics'])
    assert {'DOBFS','TDStep'} <= {r['name'] for r in result['regions'] if r['kind']=='function'}
    assert any(r['kind']=='loop' for r in result['regions'])
    assert source.read_bytes()==original


def test_callgrind_dynamic_counts_and_missing_events(tmp_path):
    raw=tmp_path/'callgrind.out'
    raw.write_text('events: Ir Dr Dw D1mr D1mw\nsummary: 1000 100 40 7\n')
    assert parse_callgrind(raw)=={'Ir':1000,'Dr':100,'Dw':40,'D1mr':7,'D1mw':0}
    raw.write_text('events: Ir Dr\nsummary: 100 -1\n')
    with pytest.raises(Failure,match='summary'): parse_callgrind(raw)
    raw.write_text('events: Ir Dr\n')
    with pytest.raises(Failure,match='summary'): parse_callgrind(raw)


def test_public_profile_rejects_fixture_execution_and_retains_reason(evaluation_setup,tmp_path):
    records,runs,_,_=evaluation_setup
    _,evaluation=evaluate(evaluation_setup,sources=[0])
    path=tmp_path/'profile.yaml';path.write_text(yaml.safe_dump({'message_version':'1.0','id':'profile-fixture-rejected','evaluation':evaluation['id']}))
    result=records.swdb('bfs-profile',path,'--runs-dir',runs,'--format','json')
    assert result.returncode==1,result.stderr
    data=json.loads(result.stdout)
    assert 'contract-fixture' in data['outcome']['reason']
    fresh=records.swdb('get',data['id'],'--format','json')
    assert json.loads(fresh.stdout)['outcome']==data['outcome']
    mismatch=records.swdb('bfs-hotspots',data['id'],'--kind','function','--evaluation','wrong-evaluation','--format','json')
    assert mismatch.returncode==1 and 'differs' in mismatch.stderr


def test_public_compiled_toy_profile_and_fresh_rankings(records,tmp_path):
    import socket
    library,parse_args=compiler_inventory()
    compiler=shutil.which('clang++') or shutil.which('g++')
    if not compiler: pytest.skip('C++ compiler unavailable')
    records.copy_repo('applications','kernels','implementations','machines')
    keep={'applications/gapbs.yaml','kernels/gapbs-bfs.yaml','implementations/gapbs-bfs-do.yaml','machines/mbit10.yaml'}
    for p in records.path.rglob('*.yaml'):
        if p.relative_to(records.path).as_posix() not in keep: p.unlink()
    source=tmp_path/'toy-app';(source/'src').mkdir(parents=True)
    toy='''#include <iostream>
#include <vector>
#include <queue>
#include <cstdint>
using NodeID=int32_t;
template<class T> using pvector=std::vector<T>;
struct Graph {
 std::vector<std::vector<NodeID>> adj;
 Graph(int64_t n,NodeID**idx,NodeID*edges):adj(n){for(int i=0;i<n;++i)adj[i]=std::vector<NodeID>(idx[i],idx[i+1]);delete[]idx;delete[]edges;}
 Graph(int64_t n,NodeID**idx,NodeID*edges,NodeID**inv,NodeID*iedges):Graph(n,idx,edges){delete[]inv;delete[]iedges;}
 int64_t num_nodes()const{return adj.size();}
};
void UncataloguedHelper(){volatile int sink=0;for(int i=0;i<100;++i)sink+=i;}
pvector<NodeID> DOBFS(const Graph&g,NodeID source,bool){
 UncataloguedHelper();pvector<NodeID>p(g.num_nodes(),-1);p[source]=source;
 std::queue<NodeID>q;q.push(source);
 while(!q.empty()){auto u=q.front();q.pop();for(auto v:g.adj[u])if(p[v]<0){p[v]=u;q.push(v);}}
 return p;
}
bool BFSVerifier(){return true;}
int main(){return 99;}
'''
    (source/'src/bfs.cc').write_text(toy)
    app=records.read('applications/gapbs.yaml');app['source']['local_path']=str(source)
    records.write('applications/gapbs.yaml',app)
    impl=records.read('implementations/gapbs-bfs-do.yaml')
    impl['verification']={'status':'unchecked','evidence':[],'scope':'Compiled toy integration fixture; not workload acceptance.'}
    impl['code']=[{'root':'application','path':'src/bfs.cc','lines':[1,len(toy.splitlines())]}]
    verifier_line=toy.splitlines().index('bool BFSVerifier(){return true;}')+1
    impl['evaluator']['verifier']['code']={'root':'application','path':'src/bfs.cc','lines':[verifier_line,verifier_line]}
    for loop in impl['loops']:
        if loop.get('code'): loop['code']={'root':'application','path':'src/bfs.cc','lines':[17,17]}
    kernel=records.read('kernels/gapbs-bfs.yaml')
    kernel['correctness_check']['verifier']['code']=impl['evaluator']['verifier']['code']
    records.write('kernels/gapbs-bfs.yaml',kernel)
    impl['build'].update(compiler=compiler,flags='-std=c++11 -O2')
    records.write('implementations/gapbs-bfs-do.yaml',impl)
    machine=records.read('machines/mbit10.yaml');machine.update(id='toy-host',hostname=socket.gethostname().split('.')[0],lane_required=False)
    records.write('machines/toy-host.yaml',machine)
    runs=tmp_path/'runs'
    def call(command,*args):
        result=records.swdb(command,*args,'--format','json')
        assert result.returncode==0,result.stderr+'\n'+result.stdout
        return json.loads(result.stdout)
    snapshot=call('source-snapshot','gapbs-bfs-do','--id','toy-source','--runs-dir',runs)
    candidate=call('baseline-candidate',snapshot['id'],'--id','toy-candidate','--runs-dir',runs)
    request={'message_version':'1.0','id':'toy-evaluation','candidate':candidate['id'],'machine':'toy-host','threads':1,
        'sources':[0,4],'repetitions':1,'roi':'bfs.complete_call.v1','budget':{'build_seconds':20,'run_seconds':5,'total_seconds':120},
        'workload':{'family':'contract_fixture','graph':{'num_vertices':5,'directed':True,'edges':[[0,1],[0,2],[1,3],[2,3]]}}}
    file=tmp_path/'evaluation.yaml';file.write_text(yaml.safe_dump(request))
    evaluation=call('evaluate',file,'--runs-dir',runs)
    assert evaluation['correctness']['state']=='passed'
    request={'message_version':'1.0','id':'toy-profile','evaluation':evaluation['id'],'memory':False,
        'discovery':{'library':library,'arguments':parse_args},
        'budget':{'discovery_seconds':20,'build_seconds':20,'run_seconds':5,'total_seconds':120}}
    file=tmp_path/'profile.yaml';file.write_text(yaml.safe_dump(request))
    result=call('bfs-profile',file,'--runs-dir',runs)
    assert result['outcome']['state']=='partial',result['outcome']
    assert '-isystem' in result['discovery']['arguments']
    ranking=call('bfs-hotspots',result['id'],'--kind','function','--evaluation',evaluation['id'])
    assert any(r['name']=='UncataloguedHelper' and r['metrics']['invocations']==2 for r in ranking['regions'])
    assert ranking['ranking']['metric']=='exclusive_function_thread_cpu_seconds'
    assert all(r['metrics']['exclusive_function_thread_cpu_seconds']>=r['metrics']['exclusive_thread_cpu_seconds'] for r in ranking['regions'])
    loops=call('bfs-hotspots',result['id'],'--kind','loop')
    assert any(r['function']=='UncataloguedHelper' for r in loops['regions'])
    assert len(result['executions'])==2 and all(x['correctness']['passed'] for x in result['executions'])
    assert all(not x['available'] for x in result['dynamic_memory'])
    fresh=call('get',result['id'])
    assert fresh['regions']==result['regions'] and fresh['context']['primary_binary_sha256']==evaluation['build']['binary_sha256']

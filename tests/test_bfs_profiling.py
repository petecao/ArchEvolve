"""Compiler discovery and public diagnostic contracts. Updated 2026-09-26.

Local toy compilation is integration evidence, not native BFS acceptance.
"""
import json
import hashlib
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


def test_diagnostic_parent_hash_identifies_the_checked_bytes(tmp_path, monkeypatch):
    from swdb.bfs_profiling import _trial_output
    path = tmp_path/'parents.json'
    payload = json.dumps({'format':'swdb.bfs.native.trial.v1', 'source':0,
        'roi':'bfs.complete_call.v1', 'configured_threads':1, 'duration_s':0.1,
        'parents':[0,0]}).encode()
    path.write_bytes(payload)
    original_open = Path.open
    reads = 0
    def replace_between_reads(self, mode='r', *args, **kwargs):
        nonlocal reads
        if self == path and 'r' in mode:
            reads += 1
            if reads == 2:
                with original_open(path, 'wb') as out: out.write(b'changed after validation')
        return original_open(self, mode, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', replace_between_reads)
    observed = _trial_output(path, {'num_vertices':2,'adjacency':[[1],[]]}, 0, 1)
    assert observed['correctness']['passed']
    assert observed['output_sha256'] == hashlib.sha256(payload).hexdigest()


def test_captured_region_and_callgrind_outputs_keep_exact_byte_identity(tmp_path):
    from swdb.bfs_native import observation_bytes, json_observation, StageFailure
    from swdb.bfs_profiling import _region_observations
    path = tmp_path/'regions.json'
    row = {'index':0,'inclusive_ns':8,'exclusive_ns':5,'invocations':2}
    payload = json.dumps({'format':'swdb.bfs.regions.v1','clock':'CLOCK_THREAD_CPUTIME_ID',
                          'errors':0,'regions':[row]}).encode()
    path.write_bytes(payload)
    rows, digest = _region_observations(path, [{}])
    assert rows == [row] and digest == hashlib.sha256(payload).hexdigest()
    path.write_text('[]')
    with pytest.raises(StageFailure, match='JSON object'):
        json_observation(path, 64, 'test output')
    path.write_bytes(b'x'*65)
    with pytest.raises(StageFailure, match='oversized'):
        observation_bytes(path, 64, 'test output')
    raw = tmp_path/'callgrind.out'
    payload = b'events: Ir Dr Dw\nsummary: 100 20 10\ntotals: 100 20 10\n'
    raw.write_bytes(payload)
    captured, digest = observation_bytes(raw, 1024, 'Callgrind')
    raw.write_text('changed after capture')
    assert parse_callgrind(raw, require_totals=True, raw=captured) == {'Ir':100,'Dr':20,'Dw':10}
    assert digest == hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize('errors,inclusive,exclusive,invocations,valid', [
    (False, 0, 0, 0, False), (0, 1, 0, 0, False),
    (0, 1, 1, 0, False), (0, 0, 0, 1, True), (0, 0, 0, 0, True),
    (0, 10**309, 10**309, 1, False), (0, 0, 0, 2**64, False),
    (0, 2**64-1, 0, 1, True),
])
def test_region_counter_runtime_invariants(tmp_path, errors, inclusive, exclusive, invocations, valid):
    from swdb.bfs_native import StageFailure
    from swdb.bfs_profiling import _region_observations
    path = tmp_path/'regions.json'
    row = {'index':0, 'inclusive_ns':inclusive, 'exclusive_ns':exclusive, 'invocations':invocations}
    path.write_text(json.dumps({'format':'swdb.bfs.regions.v1','clock':'CLOCK_THREAD_CPUTIME_ID',
                               'errors':errors, 'regions':[row]}))
    if valid:
        assert _region_observations(path, [{}])[0] == [row]
    else:
        with pytest.raises(StageFailure): _region_observations(path, [{}])


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


def test_free_function_template_and_loops_execute_for_multiple_instantiations(tmp_path):
    library, args = compiler_inventory()
    source = tmp_path/'template.cc'
    source.write_text('''template<class T> T NewTemplateHelper(T n) {
 T sum=0; for(T i=0;i<n;++i) sum+=i; return sum;
}
int Caller(){return NewTemplateHelper(4)+NewTemplateHelper(5L);}
struct ExcludedMember { template<class T> T method(T n){for(T i=0;i<n;++i){}return n;} };
''')
    result = discover(source, args, library)
    regions = result['regions']
    helper = next(i for i,r in enumerate(regions) if r['kind']=='function' and r['name']=='NewTemplateHelper')
    loops = [i for i,r in enumerate(regions) if r['kind']=='loop' and r['function']=='NewTemplateHelper']
    assert len(loops)==1 and regions[helper]['usr']
    assert not any(r['name']=='method' or r['function']=='method' for r in regions)
    assert any('combines instantiations' in reason for reason in result['limitations'])
    rewritten = tmp_path/'instrumented.cc'; rewritten.write_bytes(instrument(source, regions))
    driver = tmp_path/'driver.cc'; output=tmp_path/'counts.json'
    driver.write_text(f'#define SWDB_REGION_COUNT {len(regions)}\n#include "{REPO}/tools/bfs_profile/runtime.hpp"\n'
        f'#include "{rewritten}"\nint main(){{swdb_profile::start();int value=Caller();swdb_profile::stop();swdb_profile::write("{output}");return value==16?0:1;}}\n')
    compiler=shutil.which('clang++') or shutil.which('g++')
    if not compiler: pytest.skip('C++ compiler unavailable')
    compiled=subprocess.run([compiler,'-std=c++11','-O2',str(driver),'-o',str(tmp_path/'program')],capture_output=True,text=True)
    assert compiled.returncode==0,compiled.stderr
    subprocess.run([str(tmp_path/'program')],check=True)
    counts=json.loads(output.read_text())
    assert counts['errors']==0 and counts['regions'][helper]['invocations']==2
    assert counts['regions'][loops[0]]['invocations']==2


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


@pytest.mark.parametrize('directives', [
    '#if __GNUC__ >= 13\nint CompilerChosen(){return 13;}\n#else\nint MetadataChosen(){return 4;}\n#endif',
    '#define COMPILER_VERSION __GNUC_MINOR__\n#if COMPILER_VERSION > 0\nint f(){return 1;}\n#endif',
    '#if 0\n#if defined(__clang__)\nint hidden(){return 1;}\n#endif\n#endif',
    '#if __has_builtin(__builtin_expect)\nint f(){return 1;}\n#endif',
])
def test_compiler_identity_and_feature_branches_fail_closed(tmp_path, directives):
    library, args = compiler_inventory()
    source = tmp_path/'compiler-branches.cc'
    source.write_text(directives+'\nint always(){return 0;}\n')
    with pytest.raises(ValueError, match='compiler-sensitive source inventory is unresolved'):
        discover(source, args, library)


def test_compiler_names_in_comments_and_strings_are_not_branch_tokens(tmp_path):
    library, args = compiler_inventory()
    source = tmp_path/'compiler-text.cc'
    source.write_text('''// __GNUC__ does not control this function.
/* #if __has_feature(cxx_exceptions) */
const char *f(){return "__clang__";}
const char *g(){return R"(__GNUC_MINOR__)";}
''')
    result = discover(source, args, library)
    assert {r['name'] for r in result['regions']} == {'f', 'g'}
    assert any('predefined compiler macros' in reason for reason in result['limitations'])


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
    raw.write_text('events: Ir Dr Dw\nsummary: 18446744073709551605 0 18446744073709551609\ntotals: 252385 54474 25758\n')
    with pytest.raises(Failure,match='summary'): parse_callgrind(raw,require_totals=True)
    raw.write_text('events: Ir Dr Dw\nsummary: 10 2 1\ntotals: 11 2 1\n')
    with pytest.raises(Failure,match='smaller'): parse_callgrind(raw,require_totals=True)
    raw.write_text('events: Ir Dr D1mr\nsummary: 100 2 3\ntotals: 100 2 3\n')
    with pytest.raises(Failure,match='exceeds'): parse_callgrind(raw,require_totals=True)
    raw.write_text('events: Ir Dr Dw\nsummary: 100 20 10\ntotals: 98 19 10\n')
    assert parse_callgrind(raw,require_totals=True)=={'Ir':100,'Dr':20,'Dw':10}


def test_memory_collector_repeats_each_ordered_source_without_reusing_outputs(tmp_path):
    from swdb.bfs_profiling import _memory
    source = tmp_path/'source.cc'; source.write_text('/* contract fixture */')
    build = tmp_path/'build'; build.mkdir()
    data = {'build':{'directory':str(build)},'artifacts':{},'executions':[],'dynamic_memory':[],
            'context':{'sources':[0,1],'repetitions':2,'threads':1,'candidate_sha256':'fixture'}}
    class FixtureSession:
        folder = tmp_path
        count = 0
        def execute(self, stage, command, timeout, env=None, **details):
            if stage=='memory_collector_identity':
                path=tmp_path/'version.log'; path.write_text('fixture collector'); return path
            if stage=='memory_build': Path(command[-1]).write_text('fixture binary')
            if stage=='memory_execution':
                self.count += 1
                assert details['source']==int(command[-2])
                output = Path(command[-1]); assert not output.exists()
                output.write_text(json.dumps({'format':'swdb.bfs.native.trial.v1','roi':'bfs.complete_call.v1',
                    'source':details['source'],'configured_threads':1,'duration_s':0.01,
                    'parents':[details['source'],details['source']]}))
                raw = Path(next(c.split('=',1)[1] for c in command if c.startswith('--callgrind-out-file=')))
                assert not raw.exists()
                raw.write_text(f'desc: Trigger: Client Request\nevents: Ir Dr Dw D1mr D1mw DLmr DLmw\nsummary: 100 {self.count} 2 0 0 0 0\ntotals: 100 {self.count} 2 0 0 0 0\n')
        def save(self): pass
    session = FixtureSession()
    _memory(session,data,{'memory_model':{'collector':shutil.which('python3')}},source,[], 'fixture-cxx',[],
            tmp_path/'unused-graph',{'num_vertices':2,'adjacency':[[1],[0]]},{},{'build_seconds':1,'run_seconds':1})
    assert [(x['repetition'],x['source_position']) for x in data['executions']]==[(0,0),(0,1),(1,0),(1,1)]
    assert [x['value'] for x in data['dynamic_memory'] if x['metric']=='Dr']==[1,2,3,4]
    assert len({x['raw_artifact'] for x in data['executions']})==4


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


def test_public_legacy_native_hotspots_use_one_quantity_and_keep_unobserved_records(records):
    from swdb.workflow import record
    rows = [
        {'id': 'function:a', 'kind': 'function', 'metrics': {'invocations': 1,
            'exclusive_function_thread_cpu_seconds': 100, 'exclusive_thread_cpu_seconds': 1}},
        {'id': 'function:b', 'kind': 'function', 'metrics': {'invocations': 1, 'exclusive_thread_cpu_seconds': 2}},
        {'id': 'loop:a', 'kind': 'loop', 'metrics': {'invocations': 1, 'exclusive_thread_cpu_seconds': 3}},
        {'id': 'loop:b', 'kind': 'loop', 'metrics': {'invocations': 1, 'exclusive_thread_cpu_seconds': 4}},
        {'id': 'function:unobserved', 'kind': 'function', 'metrics': {'invocations': 0}},
    ]
    data = record('region_profile', 'legacy-native', request={'fixture': True},
        context={'basis': 'measured'}, outcome={'state': 'partial', 'stage': 'fixture', 'reason': None},
        stages=[], regions=rows, dynamic_memory=[], executions=[], raw_artifacts=[], reasons=[], gain_claim=False)
    records.write('region_profiles/legacy-native.yaml', data)
    for kind in ('function', 'loop'):
        result = records.swdb('bfs-hotspots', data['id'], '--kind', kind, '--format', 'json')
        assert result.returncode == 0, result.stderr
        ranked = json.loads(result.stdout)
        assert ranked['ranking']['metric'] == 'exclusive_thread_cpu_seconds'
        assert ranked['ranking']['quantity'] == 'thread CPU time'
        assert [r['id'] for r in ranked['regions']] == [kind + ':b', kind + ':a']
        assert ranked['gain_claim'] is False
    assert json.loads(records.swdb('get', data['id'], '--format', 'json').stdout)['regions'] == rows


def test_public_compiled_toy_profile_and_fresh_rankings(records,tmp_path,monkeypatch):
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
#include <cstdlib>
#include <cstring>
#include <stdexcept>
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
 if(!getenv("OMP_THREAD_LIMIT") || strcmp(getenv("OMP_THREAD_LIMIT"),"2") ||
    !getenv("OMP_WAIT_POLICY") || strcmp(getenv("OMP_WAIT_POLICY"),"PASSIVE") ||
    getenv("GOMP_SPINCOUNT") || getenv("GOMP_CPU_AFFINITY")) throw std::runtime_error("wrong runtime inputs");
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
    monkeypatch.setenv('OMP_THREAD_LIMIT', '2')
    monkeypatch.setenv('OMP_WAIT_POLICY', 'PASSIVE')
    monkeypatch.delenv('GOMP_SPINCOUNT', raising=False)
    monkeypatch.delenv('GOMP_CPU_AFFINITY', raising=False)
    evaluation=call('evaluate',file,'--runs-dir',runs)
    assert evaluation['correctness']['state']=='passed'
    # Actual diagnostic subprocesses must receive the retained inputs, including
    # explicit unsets, despite a different invoking shell. No OpenMP team claim.
    monkeypatch.setenv('OMP_THREAD_LIMIT', '1')
    monkeypatch.setenv('OMP_WAIT_POLICY', 'ACTIVE')
    monkeypatch.setenv('GOMP_SPINCOUNT', '300000')
    monkeypatch.setenv('GOMP_CPU_AFFINITY', '999')
    request={'message_version':'1.0','id':'toy-profile','evaluation':evaluation['id'],'memory':False,
        'discovery':{'library':library,'arguments':parse_args},
        'budget':{'discovery_seconds':20,'build_seconds':20,'run_seconds':5,'total_seconds':120}}
    file=tmp_path/'profile.yaml';file.write_text(yaml.safe_dump(request))
    result=call('bfs-profile',file,'--runs-dir',runs)
    assert result['outcome']['state']=='partial',result['outcome']
    assert result['build']['native_runtime'] == evaluation['build']['native_runtime']
    assert '-isystem' in result['discovery']['arguments']
    assert result['context']['primary_load_average']==evaluation['context']['load_average']
    assert len(result['context']['load_average'])==3
    ranking=call('bfs-hotspots',result['id'],'--kind','function','--evaluation',evaluation['id'])
    assert any(r['name']=='UncataloguedHelper' and r['metrics']['invocations']==2 for r in ranking['regions'])
    assert ranking['ranking']['metric']=='exclusive_function_thread_cpu_seconds'
    assert ranking['ranking']['basis']=='measured' and ranking['ranking']['quantity']=='thread CPU time'
    assert ranking['evidence_kind']=='execution' and ranking['gain_claim'] is False
    assert all(r['metrics']['exclusive_function_thread_cpu_seconds']>=r['metrics']['exclusive_thread_cpu_seconds'] for r in ranking['regions'])
    loops=call('bfs-hotspots',result['id'],'--kind','loop')
    assert loops['ranking']['metric']=='exclusive_thread_cpu_seconds'
    assert loops['ranking']['basis']=='measured' and loops['ranking']['quantity']=='thread CPU time'
    assert any(r['function']=='UncataloguedHelper' for r in loops['regions'])
    assert len(result['executions'])==2 and all(x['correctness']['passed'] for x in result['executions'])
    assert all(not x['available'] for x in result['dynamic_memory'])
    fresh=call('get',result['id'])
    assert fresh['regions']==result['regions'] and fresh['context']['primary_binary_sha256']==evaluation['build']['binary_sha256']
    # A later audit must affect public eligibility, without erasing the original
    # observation or concealing its recorded availability from historical users.
    fresh['dynamic_memory']=[{'metric':'Dw','available':True,'value':2**64-7,
                             'collector':{'name':'Callgrind'},'execution':{'source':0}}]
    fresh.setdefault('extensions',{})['post_collection_audit']={'scope':'dynamic_memory','state':'invalid'}
    records.write('region_profiles/toy-profile.yaml',fresh)
    audited=call('bfs-hotspots',result['id'],'--kind','function')
    assert audited['memory_validation']['state']=='invalid'
    assert audited['dynamic_memory'][0]['recorded_available'] is True
    assert audited['dynamic_memory'][0]['available'] is False
    assert audited['dynamic_memory'][0]['value']==2**64-7
    assert call('get',result['id'])['dynamic_memory'][0]['available'] is True
    # Historical input omissions remain visible and cannot authorize another
    # execution profile from the current invoking environment.
    evaluation['build'].pop('native_runtime')
    records.write('evaluations/' + evaluation['id'] + '.yaml', evaluation)
    assert call('get', evaluation['id']) == evaluation
    request['id'] = 'toy-profile-unknown-runtime'
    file.write_text(yaml.safe_dump(request))
    rejected = records.swdb('bfs-profile', file, '--runs-dir', runs, '--format', 'json')
    assert rejected.returncode == 1
    retained = json.loads(rejected.stdout)
    assert 'runtime inputs are unknown' in retained['outcome']['reason']
    assert not retained['executions']

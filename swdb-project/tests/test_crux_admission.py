"""Crux safety admission at public prove/record seams; created 2026-10-15 ET.

Every verifier command is a stand-in; no solver or real verifier is launched.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, make_records, run_swdb
from test_cbmc_adapter import method_version
from test_formal_frame import frame_contract, write_library
from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='clang 22.1.8 is required')


@pytest.fixture
def proof(tmp_path):
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    marker = tmp_path / 'verifier-launched'
    includes = tmp_path / 'includes'
    includes.mkdir()
    (includes / 'crucible.h').write_text('#include <stdint.h>\n'
        'extern void crucible_assert(uint8_t,const char*,int);\n'
        'extern void crucible_assume(uint8_t,const char*,int);\n'
        'extern int64_t crucible_int64_t(const char*);\n'
        'extern double crucible_double(const char*);\n')
    stub = tmp_path / 'crux.py'
    stub.write_text('import os,sys\nfrom pathlib import Path\n'
        'if "--version" in sys.argv:\n print("crux-llvm version: 0.12");sys.exit(0)\n'
        'Path(os.environ["CRUX_MARKER"]).write_text("launched")\n'
        'print("Invalid magic number\\n bitstream\\n llvm-bitstream");sys.exit(1)\n')
    cbmc_stub = tmp_path / 'cbmc.py'
    cbmc_stub.write_text('import os,sys\nfrom pathlib import Path\n'
        'if "--version" in sys.argv:\n print("6.11.0");sys.exit(0)\n'
        'Path(os.environ["CRUX_MARKER"]).write_text("unexpected cbmc launch");print("[]")\n')
    methods = library / 'methods'
    methods.mkdir(parents=True)
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    (methods / 'cbmc-fixture.yaml').write_text(yaml.safe_dump(method_version(c_lowering.identity()),sort_keys=False))
    env = {'SWDB_FRAMA_C':'none','SWDB_CRUX':f'{sys.executable} {stub}',
           'SWDB_CBMC':f'{sys.executable} {cbmc_stub}',
           'SWDB_CRUX_INCLUDES':str(includes),'CRUX_MARKER':str(marker),
           'SWDB_VERIFIER_LOCK':str(tmp_path/'standin-only.lock')}
    def run(source, adapter='crux-llvm-cxx', *, ok=True, more_env=None, mutate_source=False, arrays=(), define=None):
        frame=[{'array':name,'shared_actions':[],'history_reads':False} for name in arrays]
        entry = frame_contract('contract.fixture_crux_admission',role='enabling',concurrency_frame=frame,clauses=[
            {'id':'result','role':'postcondition','statement':'The fixture result is zero.',
             'discharge_mode':'runtime_guard','negative_control':{'id':'result-control','check':'fixture'},
             'acsl':{'text':'requires n >= 0; assigns \\nothing; ensures \\result == 0;','uses':[]},
             'proof_placement':{'once':'self'}}])
        entry['proof_unit']={'function':'unit','source':{'root':'library','path':'proof_units/unit.cc',
            'sha256':hashlib.sha256(source.encode()).hexdigest()}}
        write_library(library,{'proof_units/unit.cc':source,'rewrite_contracts/admission.yaml':entry})
        controls = {}
        if mutate_source:
            compiler = tmp_path / 'compiler_proxy'
            compiler.write_text(f'#!{sys.executable}\nimport subprocess,sys\nfrom pathlib import Path\n'
                f'result=subprocess.run({list(c_lowering.locate().command)!r}+sys.argv[1:])\n'
                'if "-emit-llvm" in sys.argv and result.returncode==0:\n'
                f' p=Path({str(library / "proof_units/unit.cc")!r});p.write_text(p.read_text()+"\\n// changed after compilation\\n")\n'
                'sys.exit(result.returncode)\n')
            compiler.chmod(0o755)
            controls['SWDB_CLANG']=str(compiler)
        done=run_swdb('prove','--records',records.path,'--summary',entry['id'],'--adapter',adapter,
            '--bounds','{"threads":1,"n":2}','--runs-dir',tmp_path/'runs','--format','json',
            *(['--define',define] if define else []),
            env={**env,**controls,**(more_env or {})})
        if not ok:return done,marker
        assert done.returncode==0,done.stdout+done.stderr
        result=json.loads(done.stdout)
        return yaml.safe_load((records.path/result['path']).read_text()),marker
    return run


@pytest.mark.parametrize('adapter',['crux-llvm-cxx','crux-llvm-c'])
def test_crux_refuses_an_uninitialized_source_read_before_bitcode_or_verifier(proof,adapter):
    record, marker=proof('int unit(int n) { int u; int discarded=u; return 0; }',adapter)
    assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct',record
    admission=record['settings']['bounded_initialization']
    assert admission['verdict']=='refused' and 'initializer' in admission['reason']
    assert not marker.exists()
    assert not any(r['name']=='crux_input' for r in record['evidence']['reports'])


@pytest.mark.parametrize('adapter',['crux-llvm-cxx','crux-llvm-c'])
def test_initialized_primitive_source_reaches_checked_standin_boundary(proof,adapter):
    source='int unit(int n) { int x=n; return x-x; }'
    record,marker=proof(source,adapter)
    assert record['verdict']=='not_proven' and record['failure_class']=='parse_error'
    assert marker.exists() # the controlled reader refused; no real proof result is claimed
    assert record['settings']['bounded_initialization']['verdict']=='passed'
    assert record['proof_setup_check']['runs'][-1]['hashes']['bounded_initialization']
    assert record['settings']['source_admission']['source_sha256']==hashlib.sha256(source.encode()).hexdigest()
    assert record['proof_setup_check']['runs'][-1]['hashes']['bounded_source_admission']


@pytest.mark.parametrize('adapter',['crux-llvm-cxx','crux-llvm-c'])
def test_source_changed_after_bitcode_compilation_is_refused_before_crux(proof,adapter):
    failed,marker=proof('int unit(int n) { return 0; }',adapter,ok=False,mutate_source=True)
    assert failed.returncode != 0
    assert 'proof setup check' in failed.stderr and 'changed' in failed.stderr,failed.stdout+failed.stderr
    assert not marker.exists()


def test_bounded_chain_stops_at_a_shared_source_initialization_refusal(proof):
    record,marker=proof('int unit(int n) { int u; int discarded=u; return 0; }','bounded')
    assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct'
    assert [a['tool'] for a in record['settings']['route']['attempts']]==['cbmc']
    assert not marker.exists()


@pytest.mark.parametrize('adapter',['crux-llvm-cxx','crux-llvm-c'])
@pytest.mark.parametrize('source,arrays',[
    ('int unit(int n) { int a[2][2]={{0,0},{0,0}}; int*p=a[0]; (void)(p+3); return 0; }',()),
    ('int a[2][2]={{0,0},{0,0}};\nint unit(int n) { int*p=a[0]; (void)(p+3); return 0; }',()),
    ('int hidden(int n) { int u; int discarded=u; return 0; }\nint unit(int n) { return hidden(n); }',()),
    ('int unit(int*p,int n) { int*q=p; q=p; return 0; }',('p',)),
])
def test_unsupported_origins_and_entire_helper_closure_fail_closed(proof,adapter,source,arrays):
    record,marker=proof(source,adapter,arrays=arrays)
    assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct',record
    assert record['settings']['bounded_initialization']['verdict']=='refused'
    assert record['settings']['verifier_launched'] is False
    assert not marker.exists()
    assert not any(r['name'].startswith(('crux_input','differential_')) for r in record['evidence']['reports'])


def test_cpp_cut_without_checked_source_analysis_stays_unsupported(proof):
    source='''int unit(int n) {
#ifdef NEED_UNCHECKED_CUT
 auto f=[](){return 0;}; return f();
#else
 return 0;
#endif
}'''
    record,marker=proof(source,define='NEED_UNCHECKED_CUT')
    assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct'
    assert 'no checked source initializedness' in record['settings']['cxx_cut']
    assert record['settings']['verifier_launched'] is False and not marker.exists()


@pytest.mark.parametrize('adapter',['crux-llvm-cxx','crux-llvm-c'])
def test_initialized_harness_pointer_retains_its_one_dimensional_source_origin(proof,adapter):
    record,marker=proof('int unit(int*p,int n) { return p[0]-p[0]; }',adapter,arrays=('p',))
    assert record['failure_class']=='parse_error' and marker.exists()
    assert record['settings']['bounded_initialization']['verdict']=='passed'
    assert 'nonnull' in record['settings']['bounded_initialization']['input_domain']
    assert record['settings']['source_admission']['functions']==['unit']


def test_real_valued_bounded_route_keeps_both_checked_crux_fallbacks(proof):
    record,marker=proof('double unit(int n) { double x=0.0; return x; }','bounded')
    assert record['failure_class']=='parse_error' and marker.exists()
    route=record['settings']['route']
    assert route['real_valued'] is True
    assert [a['tool'] for a in route['attempts']]==['crux-llvm-cxx','crux-llvm-c']
    assert record['settings']['source_admission']['form']=='c'
    assert record['proof_setup_check']['runs'][-1]['hashes']['bounded_source_admission']

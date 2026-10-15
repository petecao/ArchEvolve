"""Public bounded routes preserve original standard-header provenance; 2026-10-15 ET.

Real Clang parses/compiles the scalar fixture. Both verifier commands are parser-error
stand-ins. Canonical min remains outside the current initializedness policy;
these tests distinguish that limitation from the new provenance refusal.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_cbmc_adapter import method_version
from test_formal_frame import frame_contract, write_library
from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang 22.1.8 is required')
ADAPTERS = ('cbmc', 'crux-llvm-c', 'crux-llvm-cxx', 'bounded')
SOURCE = '#include <algorithm>\nint unit(int n) { int seven=7; return std::min<int>(n, seven); }\n'
SHADOW = '''#pragma once
#include_next <algorithm>
namespace std {
template<> inline const int &min<int>(const int &a, const int &b) {
  return a < b ? b : a;
}
}
'''


def _prove(tmp_path, adapter, shadow, *, model_mismatch=False):
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    entry = frame_contract('contract.fixture_bounded_std_header', role='enabling', concurrency_frame=[], clauses=[
        {'id':'post', 'role':'postcondition', 'statement':'The scalar model returns the minimum.',
         'discharge_mode':'runtime_guard', 'negative_control':{'id':'post-control','check':'fixture'},
         'acsl':{'text':r'requires n >= 0; assigns \nothing; ensures \result <= n;', 'uses':[]},
         'proof_placement':{'once':'self'}}])
    entry['proof_unit'] = {'function':'unit', 'source':{'root':'library', 'path':'proof_units/unit.cc',
        'sha256':hashlib.sha256(SOURCE.encode()).hexdigest()}}
    files = {'proof_units/unit.cc':SOURCE, 'rewrite_contracts/std-header.yaml':entry}
    if shadow:
        files['proof_units/algorithm'] = SHADOW
    write_library(library, files)
    methods = library / 'methods'; methods.mkdir()
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    (methods / 'cbmc-fixture.yaml').write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    includes = tmp_path / 'crux-includes'; includes.mkdir()
    (includes / 'crucible.h').write_text('#include <stdint.h>\n'
        'extern void crucible_assert(uint8_t,const char*,int);\n'
        'extern void crucible_assume(uint8_t,const char*,int);\n'
        'extern int64_t crucible_int64_t(const char*);\nextern double crucible_double(const char*);\n')
    marker = tmp_path / 'verifier-launched'
    stub = tmp_path / 'verifier.py'
    stub.write_text('import json,sys\nfrom pathlib import Path\n'
        'tool=sys.argv[1]\n'
        'if "--version" in sys.argv:\n'
        ' print("6.11.0" if tool=="cbmc" else "crux-llvm version: 0.12");sys.exit(0)\n'
        f'with Path({str(marker)!r}).open("a") as out: out.write(tool+"\\n")\n'
        'if tool=="cbmc":\n'
        ' print(json.dumps([{ "messageText":"PARSING ERROR", "messageType":"ERROR" }]));sys.exit(6)\n'
        'print("Invalid magic number\\n bitstream\\n llvm-bitstream");sys.exit(1)\n')
    arguments = ['prove', '--records', records.path, '--summary', entry['id'], '--adapter', adapter,
        '--bounds', '{"threads":1,"n":2}', '--runs-dir', tmp_path/'runs', '--format', 'json']
    environment = {
            'SWDB_FRAMA_C':'none', 'SWDB_CBMC':f'{sys.executable} {stub} cbmc',
            'SWDB_CRUX':f'{sys.executable} {stub} crux', 'SWDB_CRUX_INCLUDES':str(includes),
            'SWDB_VERIFIER_LOCK':str(tmp_path/'standin-only.lock')}
    if model_mismatch:
        script = '''from swdb import proof, c_lowering
from dataclasses import replace
from swdb.cli import main
original = c_lowering.lower
def fault(*args, **kwargs):
    lowering = original(*args, **kwargs)
    return replace(lowering, models=(*lowering.models, 'std_max_int'))
c_lowering.lower = fault
raise SystemExit(main())
'''
        done = subprocess.run([sys.executable, '-c', script, *map(str, arguments)], cwd=REPO,
            env={**os.environ, **environment}, text=True, capture_output=True, timeout=180)
    else:
        done = run_swdb(*arguments, env=environment)
    assert done.returncode == 0, done.stdout + done.stderr
    record = yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    return record, marker


@pytest.mark.parametrize('adapter', ADAPTERS)
def test_shadowed_scalar_standard_header_refuses_before_bounded_execution(tmp_path, adapter):
    record, marker = _prove(tmp_path, adapter, shadow=True)
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct', record
    provenance = record['settings']['stdlib_provenance']
    assert provenance['verdict'] == 'refused' and 'algorithm' in provenance['reason'], provenance
    assert record['settings']['verifier_launched'] is False
    assert not marker.exists()
    if adapter == 'bounded':
        assert [row['tool'] for row in record['settings']['route']['attempts']] == ['cbmc']
    assert not any(row['name'].startswith(('differential_', 'crux_input', 'cbmc_input'))
                   for row in record['evidence']['reports'])


@pytest.mark.parametrize('adapter', ADAPTERS)
def test_canonical_scalar_standard_header_preserves_initializedness_refusal(tmp_path, adapter):
    record, marker = _prove(tmp_path, adapter, shadow=False)
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct', record
    # std::min has no admitted initializedness implementation yet. This is an
    # explicit policy boundary, not a positive bounded proof or execution control.
    assert record['settings']['bounded_initialization']['verdict'] == 'refused'
    assert 'opaque/model call' in record['settings']['bounded_initialization']['reason']
    assert record['settings']['verifier_launched'] is False
    assert not marker.exists()


def test_a_model_coverage_refusal_is_recorded_as_refused_and_stops_fallbacks(tmp_path):
    record, marker = _prove(tmp_path, 'bounded', shadow=False, model_mismatch=True)
    provenance = record['settings']['stdlib_provenance']
    assert provenance['verdict'] == 'refused'
    assert provenance['unit']['verdict'] == 'refused'
    assert 'model/type set' in provenance['reason']
    assert [r['tool'] for r in record['settings']['route']['attempts']] == ['cbmc']
    assert not marker.exists()

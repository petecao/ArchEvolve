"""Public read-only OpenMP ABI projection seam. Updated: 2026-10-06 ET.

Execution selections are hand fixtures, not application observations. Static LLVM
code reading only: no application is linked or executed.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest
from conftest import REPO
from swdb import artifacts


def command(argv, **kwargs):
    result = subprocess.run([str(x) for x in argv], capture_output=True, text=True,
                            timeout=120, **kwargs)
    assert result.returncode == 0, result.stderr + result.stdout
    return result


@pytest.fixture(scope='module')
def static_openmp(tmp_path_factory):
    llvm = Path(os.environ.get('SWDB_LLVM_BIN', '/opt/homebrew/opt/llvm/bin'))
    if not (llvm / 'llvm-config').is_file():
        pytest.skip('LLVM22 required for static projection fixtures')
    if not command([llvm / 'llvm-config', '--version']).stdout.startswith('22.'):
        pytest.skip('LLVM22 required')
    folder = tmp_path_factory.mktemp('openmp-static')
    plugin = folder / ('Characterize.dylib' if sys.platform == 'darwin' else 'Characterize.so')
    flags = shlex.split(command([llvm / 'llvm-config', '--cxxflags', '--ldflags']).stdout)
    link = subprocess.run([llvm / 'llvm-config', '--link-shared', '--libs', 'core',
                           'passes', 'analysis', 'support', '--system-libs'], capture_output=True, text=True)
    if link.returncode == 0: flags += shlex.split(link.stdout)
    elif sys.platform == 'darwin': flags += ['-Wl,-undefined,dynamic_lookup']
    command([llvm / 'clang++', '-shared', '-fPIC', REPO / 'swdb/llvm/Characterize.cpp', *flags, '-o', plugin])
    ir, raw, mapping = (folder / name for name in ('normalized.bc', 'raw.bc', 'source.json'))
    command([llvm / 'clang++', '-g', '-O0', '-Xclang', '-disable-O0-optnone', '-emit-llvm',
             '-c', REPO / 'tests/fixtures/analytic/openmp_abi.cpp', '-o', raw])
    command([llvm / 'opt', '-passes=mem2reg,loop-simplify', raw, '-o', ir])
    env = dict(os.environ, SWDB_COUNT_FUNCTION='', SWDB_INSTRUMENT='0',
               SWDB_SUBJECT='fixture.openmp', SWDB_ANALYSIS_OUTPUT=str(mapping))
    env.pop('SWDB_REGION_MAP', None)
    command([llvm / 'opt', '-load-pass-plugin=' + str(plugin), '-passes=swdb-characterize',
             ir, '-disable-output'], env=env)
    source = json.loads(mapping.read_text())
    assert len(source['unmodeled_calls']) == 7
    rows = [{**call, 'execution_count': {'value': 0, 'basis': 'measured'}}
            for call in source['unmodeled_calls']]
    # Trial0 executes fork/static/reduce/barrier/global-thread; trial1 adds dispatch.
    trials = [{'position': position, 'unmodeled_calls': [
        {**call, 'execution_count': {'value': int(call['site'] in executed), 'basis': 'measured'}}
        for call in rows]} for position, executed in [(0, {0, 1, 3, 4, 5}), (1, {0, 1, 2, 3, 4, 5})]]
    record = {'kind': 'workload_characterization', 'id': 'fixture.openmp.characterization',
              'evidence_kind': 'contract_fixture',
              'static_analysis': {'source_ir_sha256': hashlib.sha256(ir.read_bytes()).hexdigest()},
              'unmodeled_calls': rows, 'trials': trials}
    record['identity_sha256'] = artifacts.digest(record)
    char = folder / 'characterization.json'
    char.write_text(json.dumps(record))
    return {'llvm': llvm, 'ir': ir, 'mapping': mapping, 'char': char, 'record': record}


def project(fixture, output, **paths):
    return subprocess.run([sys.executable, '-m', 'scripts.openmp_call_projection',
        '--llvm-bin', str(fixture['llvm']), '--source-ir', str(paths.get('ir', fixture['ir'])),
        '--source-map', str(paths.get('mapping', fixture['mapping'])),
        '--characterization', str(paths.get('char', fixture['char'])),
        '--output-directory', str(output)], cwd=REPO, capture_output=True, text=True, timeout=120)


def test_projects_all_trial_executed_sites_and_exact_abi_literals(static_openmp, tmp_path):
    originals = {key: static_openmp[key].read_bytes() for key in ('ir', 'mapping', 'char')}
    result = project(static_openmp, tmp_path / 'projection')
    assert result.returncode == 0, result.stderr + result.stdout
    proof = json.loads(result.stdout)
    assert proof['format'] == 'swdb.openmp-call-projection.v1'
    assert proof['source_ir_sha256'] == static_openmp['record']['static_analysis']['source_ir_sha256']
    assert proof['characterization']['sha256'] == artifacts.digest(static_openmp['record'])
    assert proof['all_source_json_sites_cross_checked'] is True
    assert [call['site'] for call in proof['calls']] == [0, 1, 2, 3, 4, 5]
    fork, static, dispatch, reduce, barrier, gtid = proof['calls']
    assert [call['argument_count'] for call in proof['calls']] == [5, 9, 7, 7, 2, 1]
    assert fork['operands'][1] == {'index': 1, 'kind': 'integer', 'bits': 32,
                                    'state': 'constant', 'signed_decimal': '2'}
    assert static['operands'][2]['signed_decimal'] == '34'
    assert static['operands'][7]['signed_decimal'] == '1'
    assert static['operands'][8]['state'] == 'dynamic' and static['operands'][8]['bits'] == 64
    assert dispatch['operands'][2]['state'] == 'dynamic'
    assert dispatch['operands'][6]['signed_decimal'] == '7'
    assert dispatch['execution_trial_positions'] == [1]
    assert reduce['operands'][2]['signed_decimal'] == '1'
    assert reduce['operands'][3]['signed_decimal'] == '128' and reduce['operands'][3]['bits'] == 64
    assert all(call['ident_flags']['signed_decimal'] == '514' for call in proof['calls'])
    assert all(call['llvm_function'] and call['source_location']['line'] > 0 for call in proof['calls'])
    assert all(operand['signed_decimal'] is None and operand['state'] == 'redacted'
               for call in proof['calls'] for operand in call['operands'] if operand['kind'] == 'pointer')
    assert proof['identity_sha256'] == artifacts.digest({k: v for k, v in proof.items() if k != 'identity_sha256'})
    assert proof['receipt']['projector_source_sha256'] and proof['receipt']['compiler_version']
    assert proof['receipt']['compiler_argv'] and proof['receipt']['projection_argv']
    assert proof['receipt']['compiler_sha256'] and proof['receipt']['wrapper_argv']
    assert {key: static_openmp[key].read_bytes() for key in originals} == originals


def test_refuses_conflicting_execution_receipt_without_writing_projection(static_openmp, tmp_path):
    record = json.loads(static_openmp['char'].read_text())
    record['evidence_kind'] = 'execution'
    record['binding'] = {'state': 'verified', 'execution_receipt': {'source_ir_sha256': 'f' * 64}}
    character = tmp_path / 'conflicting-characterization.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'refused', char=character)
    assert result.returncode == 2
    assert 'execution receipt source_ir_sha256 mismatch' in result.stderr
    assert not (tmp_path / 'refused/projection.json').exists()


def test_externally_initialized_ident_flags_remain_unknown(static_openmp, tmp_path):
    text = command([static_openmp['llvm'] / 'opt', '-S', static_openmp['ir'], '-o', '-']).stdout
    assert '@_ZL5ident = internal constant' in text
    ir = tmp_path / 'externally-initialized.ll'
    ir.write_text(text.replace('@_ZL5ident = internal constant',
                               '@_ZL5ident = internal externally_initialized constant'))
    record = json.loads(static_openmp['char'].read_text())
    record['static_analysis']['source_ir_sha256'] = hashlib.sha256(ir.read_bytes()).hexdigest()
    character = tmp_path / 'externally-initialized-characterization.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'external-ident', char=character, ir=ir)
    assert result.returncode == 0, result.stderr + result.stdout
    calls = json.loads(result.stdout)['calls']
    assert calls and all(call['ident_flags']['state'] == 'unknown' for call in calls)
    assert all(call['ident_flags']['signed_decimal'] is None for call in calls)


def test_missing_trial_call_observations_are_not_zero(static_openmp, tmp_path):
    record = json.loads(static_openmp['char'].read_text())
    del record['trials'][1]['unmodeled_calls']
    character = tmp_path / 'missing-trial-observations.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'missing-calls', char=character)
    assert result.returncode == 2
    assert 'trial call observations missing or invalid' in result.stderr
    assert not (tmp_path / 'missing-calls/projection.json').exists()


def test_refuses_different_ir_and_unknown_execution_counts(static_openmp, tmp_path):
    ir = tmp_path / 'different.bc'
    ir.write_bytes(b'different compiler input')
    result = project(static_openmp, tmp_path / 'different-ir', ir=ir)
    assert result.returncode == 2 and 'source_ir_sha256 mismatch' in result.stderr
    assert not (tmp_path / 'different-ir/projection.json').exists()
    record = json.loads(static_openmp['char'].read_text())
    record['trials'][0]['unmodeled_calls'][0]['execution_count'] = {'value': None, 'basis': 'unknown'}
    character = tmp_path / 'unknown-count.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'unknown-count', char=character)
    assert result.returncode == 2 and 'execution count is unknown' in result.stderr
    assert not (tmp_path / 'unknown-count/projection.json').exists()


def test_crosschecks_unexecuted_source_map_sites_against_ir(static_openmp, tmp_path):
    source = json.loads(static_openmp['mapping'].read_text())
    source['unmodeled_calls'][6]['name'] = '__kmpc_wrong_callee'
    mapping = tmp_path / 'wrong-source.json'
    mapping.write_text(json.dumps(source))
    record = json.loads(static_openmp['char'].read_text())
    for call in record['unmodeled_calls']:
        if call['site'] == 6: call['name'] = '__kmpc_wrong_callee'
    for trial in record['trials']:
        for call in trial['unmodeled_calls']:
            if call['site'] == 6: call['name'] = '__kmpc_wrong_callee'
    character = tmp_path / 'wrong-callee-characterization.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'wrong-callee', char=character, mapping=mapping)
    assert result.returncode == 2 and 'call map mismatch at6' in result.stderr.replace('at ', 'at')
    assert not (tmp_path / 'wrong-callee/projection.json').exists()


def test_known_zero_openmp_calls_produce_empty_verified_projection(static_openmp, tmp_path):
    record = json.loads(static_openmp['char'].read_text())
    for trial in record['trials']:
        for call in trial['unmodeled_calls']: call['execution_count']['value'] = 0
    character = tmp_path / 'zero-calls.json'
    character.write_text(json.dumps(record))
    result = project(static_openmp, tmp_path / 'zero-calls', char=character)
    assert result.returncode == 0, result.stderr + result.stdout
    proof = json.loads(result.stdout)
    assert proof['calls'] == []
    assert proof['all_source_json_sites_cross_checked'] is True and proof['enumerated_call_sites'] == 7

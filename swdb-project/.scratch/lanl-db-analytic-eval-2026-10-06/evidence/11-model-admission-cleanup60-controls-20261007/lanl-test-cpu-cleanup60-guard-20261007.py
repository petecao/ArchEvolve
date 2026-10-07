"""Portable production admission/argv checks; no host/native/provider calls."""
import ast
import copy
import hashlib
import io
import json
import math
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from swdb import artifacts, access

T = Path('/private/tmp')
W = Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project')
guard = T / 'lanl-admit-cpu-future-phase-cleanup60-20261007.py'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
actual = access.read_record(W / '.scratch/lanl-db-analytic-eval-2026-10-06/evidence/11-cpu-model-mbit10-20261006-a3.json')['acceptance']
assert actual['source_commit'] == C and actual['estimator_sha256'] == F6
assert actual['identity_sha256'] == artifacts.digest({k: v for k, v in actual.items() if k != 'identity_sha256'})

def seal(value):
    value['identity_sha256'] = artifacts.digest({k: v for k, v in value.items() if k != 'identity_sha256'})
    return value

def checked(value):
    assert value['identity_sha256'] == artifacts.digest({k: v for k, v in value.items() if k != 'identity_sha256'})
    return value

checks = []
cases = [('development', 'ready'), ('holdout', 'ready'), ('report', 'ready'), ('report', 'validated_report'), ('development', 'floor22_not24')]
cases += [('development', name) for name in ('dirty_source', 'dirty_source_late', 'held_lease', 'memory', 'disk_data1', 'disk_data', 'model_id', 'model_negative', 'model_estimator', 'model_timings', 'model_source', 'model_seal', 'prior_model_exit', 'helper_tamper')]
cases += [('holdout', name) for name in ('development_model', 'development_protocols', 'development_timings', 'development_negative_width', 'development_not_ready', 'prior_development_exit')]
cases += [('report', name) for name in ('holdout_model', 'holdout_protocols', 'holdout_timings', 'holdout_state')]

with tempfile.TemporaryDirectory(prefix='lanl-cpu-cleanup60-guard-') as temp:
    base = Path(temp)
    for phase, case in cases:
        root = base / (phase + '-' + case)
        root.mkdir()
        controls = root / 'controls'
        controls.mkdir()
        for name in ('lanl-dispatch-cpu-model-continuation-a3.py', 'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py', 'lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py'):
            (controls / name).write_bytes((T / name).read_bytes())
        meminfo = root / 'meminfo'
        meminfo.write_text('MemAvailable: ' + str((79 if case == 'memory' else 100) * 1024**2) + ' kB\n')
        model = copy.deepcopy(actual)
        if case == 'model_id':model['estimates'][0]['id'] = model['estimates'][1]['id']
        if case == 'model_negative':model['estimates'][0]['seconds'] = -1.0
        if case == 'model_estimator':model['estimator_sha256'] = '0' * 64
        if case == 'model_timings':model['application_performance_timings_collected'] = True
        if case == 'model_source':model['source_commit'] = '0' * 40
        seal(model)
        if case == 'model_seal':model['validation'] += ' tampered after seal'
        development = {'phase': 'development', 'source_commit': C, 'source_clean': True, 'validation': 'OK: portable fixture only', 'application_performance_timings_collected': True, 'frozen_model_acceptance': {'identity_sha256': model['identity_sha256']}, 'protocols': copy.deepcopy(model['protocols']), 'ready_for_holdout': True, 'bands': {k: {'state': 'development', 'width_log': 0.2} for k in ('bfs', 'bc')}}
        holdout = {'phase': 'holdout', 'source_commit': C, 'source_clean': True, 'validation': 'OK: portable fixture only', 'application_performance_timings_collected': True, 'frozen_model_acceptance': {'identity_sha256': model['identity_sha256']}, 'protocols': copy.deepcopy(model['protocols']), 'bands': {k: {'state': 'validated' if case == 'validated_report' else 'failed', 'width_log': 0.2} for k in ('bfs', 'bc')}}
        if case == 'development_model':development['frozen_model_acceptance']['identity_sha256'] = '0' * 64
        if case == 'development_protocols':development['protocols']['bfs']['id'] += '.changed'
        if case == 'development_timings':development['application_performance_timings_collected'] = False
        if case == 'development_negative_width':development['bands']['bfs']['width_log'] = -0.1
        if case == 'development_not_ready':development['ready_for_holdout'] = False
        if case == 'holdout_model':holdout['frozen_model_acceptance']['identity_sha256'] = '0' * 64
        if case == 'holdout_protocols':holdout['protocols']['bc']['id'] += '.changed'
        if case == 'holdout_timings':holdout['application_performance_timings_collected'] = False
        if case == 'holdout_state':holdout['bands']['bfs']['state'] = 'development'
        for name, document in (('model', model), ('development', seal(development)), ('holdout', seal(holdout))):
            raw = root / ('cpu-' + name + '-20261006-a3')
            raw.mkdir()
            code = '1' if case == 'prior_' + name + '_exit' else '0'
            (raw / 'runner-exit-code.txt').write_text(code)
            (raw / 'exit-code.txt').write_text('0')
            (raw / 'final-cleanup.json').write_text(json.dumps({'survivors': {}}))
            (raw / 'lane.json').write_text(json.dumps({'socket_lane': {'node': 0, 'exit_code': 0, 'ended_utc': 'portable fixture', 'numa_memory_policy': 'bind:0'}}))
            (raw / 'acceptance.json').write_text(json.dumps(document))
        if case == 'helper_tamper':
            with (controls / 'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py').open('ab') as file:file.write(b'\n')
        class LocalPaths(ast.NodeTransformer):
            def visit_Constant(self, node):
                mapping = {'/data1/yanruj/lanl-cpu-controls-20261007-a1': str(controls), '/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-': str(root / 'cpu-'), '/proc/meminfo': str(meminfo)}
                if isinstance(node.value, str) and node.value in mapping:
                    return ast.copy_location(ast.Constant(mapping[node.value]), node)
                return node
        tree = ast.fix_missing_locations(LocalPaths().visit(ast.parse(guard.read_text())))
        calls = []
        clean_calls = []
        def clean():
            clean_calls.append(True)
            assert case != 'dirty_source' and not (case == 'dirty_source_late' and len(clean_calls) == 2)
        def all_free():assert case != 'held_lease'
        fake_module = SimpleNamespace(clean=clean, cleanup_module=lambda: SimpleNamespace(all_free=all_free), sealed=checked)
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
        def disk(mount):
            free = 20 if mount == '/data1' and case == 'disk_data1' else 9 if mount == '/data' and case == 'disk_data' else 22 if mount == '/data1' and case == 'floor22_not24' else 30
            return SimpleNamespace(f_bavail=free * 1024**3, f_frsize=1)
        def launch(argv, **kwargs):
            assert kwargs == {'check': True, 'timeout': 240}
            expected_name = 'lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py' if phase == 'report' else 'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py'
            assert argv == ['python3', str(controls / expected_name), *([C] if phase == 'report' else [phase, C])]
            calls.append(argv)
            return SimpleNamespace(returncode=0)
        with patch.object(sys, 'argv', ['portable-parent-guard', phase]), patch('importlib.util.spec_from_file_location', return_value=spec), patch('importlib.util.module_from_spec', return_value=fake_module), patch('os.statvfs', side_effect=disk), patch('os.getloadavg', return_value=(1, 1, 1)), patch('subprocess.run', side_effect=launch), redirect_stdout(io.StringIO()):
            try:exec(compile(tree, 'portable-parent-guard-' + case, 'exec'), {})
            except AssertionError:
                assert case not in {'ready', 'validated_report', 'floor22_not24'} and not calls
                checks.append({'phase': phase, 'case': case, 'refused_before_mocked_launch': True})
            else:
                assert case in {'ready', 'validated_report', 'floor22_not24'} and len(calls) == 1
                checks.append({'phase': phase, 'case': case, 'correct_phase_then_C_or_report_C_argv': True, 'mocked_launches': 1})

proof = {'format': 'swdb.cpu-cleanup60-admission-guard-portable-proof.v1', 'guard_sha256': artifacts.file_hash(guard), 'actual_model_acceptance_identity': actual['identity_sha256'], 'actual_local_admission_identity': 'fe2890f8e7d8c95d6841ddd78b61762667e07c02688567676aca5d8fc4f4e3bd', 'checks': checks, 'cases_passed': len(checks), 'no_actual_dispatch': True, 'no_Store_compiler_application_provider': True, 'scope': 'Production parent dispatch-only guard AST with paths/imports/capacity/launch mocked. Actual model receipt supplies frozen pins; development/holdout receipts are explicitly fabricated portable fixtures and provide no native accuracy evidence.'}
proof['identity_sha256'] = artifacts.digest(proof)
output = T / 'lanl-cpu-cleanup60-admission-guard-portable-proof-20261007.json'
assert not output.exists()
output.write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({'cases_passed': len(checks), 'identity_sha256': proof['identity_sha256'], 'guard_sha256': proof['guard_sha256']}))

"""Public v2 post-seal completion contracts; no hardware claims. Updated: 2026-09-26 ET."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest
import yaml

from test_dx100 import case, execution_request, reference


def assert_downstream_verifier_contract(result):
    from swdb import bfs_protocol
    from swdb.workflow import Failure
    bfs_protocol._check_verifier_identity(result)
    stale = deepcopy(result)
    stale['correctness']['checks'][0]['checker'] = 'dx100.bfs.verifier.v1'
    with pytest.raises(Failure):
        bfs_protocol._check_verifier_identity(stale)
    missing = deepcopy(result)
    del missing['correctness']['checks'][0]['continuation']['exit_witness']
    with pytest.raises(Failure):
        bfs_protocol._check_verifier_identity(missing)


def v2_request(case, behavior):
    data = execution_request(case)
    model = Path(data['model_root'])
    for name in ('bfs.cc', 'benchmark.h'):
        path = model / 'benchmarks/gapbs/src' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('// Protected fixture source identity.\n')
    (model / 'configs/deprecated/example/se.py').write_text(
        "import m5\nevent=m5.simulate()\nprint('Exiting @ tick 31400 because '+event.getCause())\n")
    simulator = Path(data['simulator']['path'])
    program = simulator.read_text().replace(
        "    print('Exiting @ tick 31400 because m5_exit instruction encountered')", r'''    import runpy,types,json,os
    mode=BEHAVIOR
    (out/'config.ini').write_text('\n'.join('[system.switch_cpus%d]\ntype=DerivO3CPU\n' % i for i in range(4)))
    (out/'stats.txt').write_text('---------- Begin Simulation Statistics ----------\nsimTicks 31300\nfinalTick 31400\nsimFreq 1000000000000\n---------- End Simulation Statistics ----------\n')
    tick=[31400]; steps=[]; calls=[0]; enabled=set(); trace_path=[None]
    def enable(name):
        assert calls==[1], 'all additional trace flags must be post-seal'
        assert json.loads((out/'roi-seal.json').read_text())['roi_exit_tick']==31400
        enabled.add(name)
    def disable(name):
        assert calls==[1] and (out/'roi-seal.json').exists()
        enabled.discard(name)
    def output(path):
        assert calls==[1] and (out/'roi-seal.json').exists()
        trace_path[0]=pathlib.Path(path);trace_path[0].write_text('')
    def simulate(*args):
        calls[0]+=1
        if calls[0]==1:
            assert not enabled
            return types.SimpleNamespace(getCause=lambda:'m5_exit instruction encountered',getCode=lambda:0)
        assert enabled=={'SyscallBase','FmtFlag'}
        assert args and 0 < args[0] <= 10**9
        steps.append(args[0]);before=tick[0];tick[0]+=args[0]
        if calls[0]==2:
            parent='SWDB_BFS_RESULT source=%d vertices=3 parent_count=3 parent_fnv1a64=123456789abcdef0' % (1 if mode=='candidate-wrong-source' else 0)
            if mode.startswith('candidate') and mode not in ('candidate-missing-parent','candidate-after-pass'):
                print(parent,flush=True)
            print('Verification: '+('FAIL' if mode=='FAIL' else 'PASS'),flush=True)
            if mode=='candidate-after-pass':print(parent,flush=True)
            if mode!='missing-completion' and not mode.startswith('candidate'):
                print('Verification Time: 0.00001\nAverage Time: 0.00006',flush=True)
        witness_now=mode!='no-exit' and (mode!='delayed' or calls[0]>=3)
        if witness_now:
            with trace_path[0].open('a') as stream:
                stream.write('%d: SyscallBase: system.switch_cpus0: T0 : syscall Calling exit_group(0)...\n' % (before+10))
                stream.write('%d: SyscallBase: system.switch_cpus0: T0 : syscall Returned 0.\n' % (before+10))
        (out/'steps.json').write_text(json.dumps(steps))
        return types.SimpleNamespace(getCause=lambda:('exiting with last active thread context' if mode=='normal' else 'simulate() limit reached'),getCode=lambda:0)
    m5=types.ModuleType('m5');m5.simulate=simulate;m5.curTick=lambda:tick[0]
    m5.options=types.SimpleNamespace(outdir=str(out))
    m5.trace=types.SimpleNamespace(output=output)
    m5.debug=types.SimpleNamespace(flags={name:types.SimpleNamespace(enable=lambda name=name:enable(name),disable=lambda name=name:disable(name)) for name in ('SyscallBase','FmtFlag','MAATrace','MAARangeFuser','MAAIndirect','FmtTicksOff','FmtStackTrace')})
    sys.modules['m5']=m5
    driver=next(arg for arg in args if arg.endswith('dx100_verify.py'))
    runpy.run_path(driver,run_name='__m5_main__')
    if mode=='host-failure':raise SystemExit(9)
'''.replace('BEHAVIOR', repr(behavior)))
    simulator.write_text(program)
    data['simulator'] = reference(simulator)
    data['verification'] = {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': 2500000000,
                            'post_roi_trace': 'SyscallBase'}
    return data


@pytest.mark.parametrize('behavior,state', [
    ('witness', 'complete'), ('normal', 'complete'), ('delayed', 'complete'),
    ('FAIL', 'incorrect'), ('no-exit', 'missing_observation'),
    ('missing-completion', 'missing_observation'), ('host-failure', 'failed')])
def test_public_v2_requires_bound_separate_trace_and_complete_protected_observations(case, behavior, state):
    data = v2_request(case, behavior)
    _, invoke, _ = case
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == state, result['outcome']
    passed = state == 'complete'
    assert result['correctness']['state'] == ('passed' if passed else 'failed' if behavior == 'FAIL' else 'unverified')
    terminal = result['context']['sealed_roi']['verification']
    assert terminal['checker'] == 'dx100.bfs.verifier.v2'
    assert terminal['normal_exit_observed'] is (behavior == 'normal')
    assert terminal['simulated_ticks'] <= data['verification']['max_ticks']
    trace = result['context']['post_roi_trace']
    assert trace['format_flags'] == ['FmtFlag']
    assert trace['enabled_tick'] == 31400
    assert reference(Path(trace['path'])) == {key: trace[key] for key in ('path', 'sha256')}
    steps = json.loads(Path(trace['path']).with_name('steps.json').read_text())
    assert steps == ([10**9, 10**9, 500000000] if behavior == 'no-exit'
                     else [10**9, 10**9] if behavior == 'delayed' else [10**9])
    if passed:
        assert_downstream_verifier_contract(result)
        assert terminal['stop_reason'] == ('normal_exit' if behavior == 'normal' else 'exit_witness')
        assert terminal['exit_witness']['completed'] is True
        assert result['correctness']['checks'][0]['completion_sequence']['observed'] is True
        assert result['context']['verification_parser']['sha256'] == terminal['parser_sha256']
    if behavior == 'host-failure':
        assert terminal['exit_witness']['completed'] is True
        assert result['correctness']['checks'][0]['passed'] is False


def test_public_v2_requires_explicit_trace_before_execution(case):
    data = execution_request(case)
    _, invoke, _ = case
    data['verification'] = {'checker': 'dx100.bfs.verifier.v2', 'max_ticks': 1000}
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'explicit post_roi_trace' in result['outcome']['reason']
    assert not any(stage['stage'] in {'checkpoint', 'simulation'} for stage in result['stages'])


def test_public_v2_retains_trusted_runtime_after_checkout_helpers_change(case, records, monkeypatch):
    from swdb import bfs_coverage
    from swdb.dx100_witness import validate_completed_witness
    data = v2_request(case, 'witness')
    _, invoke, folder = case
    repo = Path(__file__).resolve().parents[1]
    checkout = folder / 'helper-checkout'
    for name in ('schemas', 'vocab'):
        shutil.copytree(repo / name, checkout / name)
    names = ('scripts/dx100_verify.py', 'scripts/dx100_host_memory.py', 'swdb/dx100_witness.py')
    for name in names:
        target = checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, target)
    monkeypatch.setenv('SWDB_HOME', str(checkout))
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'complete', result['outcome']
    context = result['context']
    runtime = context['verification_runtime']
    assert runtime['source_paths_are_provenance_only'] is True
    snapshots = folder / 'runs' / data['id'] / 'verification-runtime'
    for name, row in zip(names, runtime['files']):
        assert row['source'] == {'code_root': str(checkout), 'repository_relative_path': name,
                                 'copied_sha256': reference(checkout / name)['sha256']}
        assert row['snapshot'] == reference(snapshots / name)
        assert row['source']['copied_sha256'] == row['snapshot']['sha256']
        (checkout / name).write_text('# Changed temporary checkout helper after execution.\n')
    assert Path(context['verification_driver']['path']) == snapshots / names[0]
    assert Path(context['host_memory_observer']['path']) == snapshots / names[1]
    assert Path(context['verification_parser']['path']) == snapshots / names[2]
    assert context['instrumentation']['verifier_runtime'] == {
        'driver_sha256': context['verification_driver']['sha256'],
        'parser_sha256': context['verification_parser']['sha256'],
        'observer_sha256': context['host_memory_observer']['sha256']}
    assert validate_completed_witness(result)['completed'] is True
    assert_downstream_verifier_contract(result)
    availability = bfs_coverage._availability([result], context['host'])
    assert availability and all(row['state'] == 'verified' for row in availability), availability


@pytest.mark.parametrize('behavior', ['candidate', 'candidate-missing-parent', 'candidate-wrong-source', 'candidate-after-pass'])
def test_public_v2_candidate_requires_exact_protected_parent_result_before_pass(case, records, behavior):
    from swdb import artifacts, workflow
    data = v2_request(case, behavior)
    request, invoke, folder = case
    repo = Path(__file__).resolve().parents[1]
    records.copy_repo('applications')
    kernel = yaml.safe_load((repo / 'records/kernels/gapbs-bfs.yaml').read_text())
    kernel['baseline_implementation'] = 'dx100-bfs-scalar'
    records.write('kernels/gapbs-bfs.yaml', kernel)
    records.write('implementations/dx100-bfs-scalar.yaml', yaml.safe_load(
        (repo / 'records/implementations/dx100-bfs-scalar.yaml').read_text()))
    model_build = request('model-build')
    model_build['fixture_command'] = [sys.executable, '-c', 'print("fixture model build")']
    assert invoke('dx100-build', model_build)['outcome']['state'] == 'complete'
    root = folder / 'candidate-source'
    source = root / 'benchmarks/gapbs/src/bfs.cc'
    source.parent.mkdir(parents=True)
    verifier = 'bool BFSVerifier() { return true; }'
    source.write_text('// Explicit compilation contract fixture.\n' + verifier + '\n')
    artifact = artifacts.identify(root)
    protections = [{'path': 'benchmarks/gapbs/src/bfs.cc', 'kind': 'verifier', 'text': verifier}]
    records.write('source_snapshots/source.yaml', workflow.record('source_snapshot', 'source',
        implementation='dx100-bfs-scalar', application='dx100-gapbs', revision='fixture',
        artifact=artifact, context={}, protections=protections, regions=[]))
    records.write('candidates/candidate.yaml', workflow.record('candidate', 'candidate',
        implementation='dx100-bfs-scalar', source_snapshot='source', artifact=artifact,
        context={}, protections=protections, state='unverified', artifact_role='source_baseline'))
    assembly = Path(data['model_root']) / 'util/m5/src/abi/x86/m5op.S'
    assembly.parent.mkdir(parents=True)
    assembly.write_text('// Explicit assembly fixture.\n')
    compiler = folder / 'compiler-fixture'
    compiler.write_text(f'#!{sys.executable}\nimport pathlib,sys\n'
        "p=pathlib.Path(sys.argv[sys.argv.index('-o')+1]);p.write_text('#!/bin/sh\\nexit 0\\n');p.chmod(0o755)\n")
    compiler.chmod(0o755)
    build_request = request('candidate-build')
    build_request.update(candidate='candidate', build_evaluation='model-build', function='DOBFS', accelerated=False,
        roi='bfs.complete_call.v1', fixture_compiler=reference(compiler),
        budget={'total_seconds': 60, 'memory_gib': 1, 'storage_gib': 1, 'build_seconds': 10})
    compiled = invoke('dx100-compile', build_request)
    assert compiled['outcome']['state'] == 'complete', compiled['outcome']
    data.update(candidate='candidate', candidate_build=compiled['id'], build_evaluation='model-build',
        binary={'path': compiled['build']['binary'], 'sha256': compiled['build']['binary_sha256']})
    result = invoke('dx100-execute', data)
    valid = behavior == 'candidate'
    assert result['outcome']['state'] == ('complete' if valid else 'missing_observation'), result['outcome']
    assert result['correctness']['state'] == ('passed' if valid else 'unverified')
    check = result['correctness']['checks'][0]
    assert check['completion_sequence']['kind'] == 'protected_candidate'
    assert check['completion_sequence']['observed'] is valid
    if valid:
        assert_downstream_verifier_contract(result)

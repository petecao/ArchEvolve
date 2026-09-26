"""Public DX100 adapter fixtures; never simulator acceptance. Updated: 2026-09-25."""

import hashlib
import json
from pathlib import Path
import socket
import sys

import pytest
import yaml


def reference(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.fixture
def case(records, tmp_path):
    records.copy_repo("operations", "hardware_targets", "machines")
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="fixturehost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/fixturehost.yaml", machine)
    model = tmp_path / "model"
    for name in ("configs/deprecated/example/se.py", "ext/ramulator2/ramulator2/example_gem5_config.yaml"):
        path = model / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Explicit contract fixture, not a hardware model.\n")
    runs = tmp_path / "runs"

    def request(rid="fixture"):
        return {"message_version": "1.0", "id": rid, "fixture": True, "machine": "fixturehost",
                "hardware_target": "dx100-e4fc4af-4c", "model_root": str(model),
                "budget": {"total_seconds": 20, "memory_gib": 1, "storage_gib": 1, "jobs": 1}}

    def invoke(command, data):
        path = tmp_path / f"{data['id']}.yaml"
        path.write_text(yaml.safe_dump(data))
        result = records.swdb(command, path, "--runs-dir", runs, "--lane", "0", "--format", "json")
        assert result.returncode in {0, 1}, result.stderr
        assert result.stdout, result.stderr
        observed = json.loads(result.stdout)
        retrieved = records.swdb("get", data["id"], "--format", "json")
        assert retrieved.returncode == 0, retrieved.stderr
        assert json.loads(retrieved.stdout) == observed
        assert observed["evidence_kind"] == "contract_fixture"
        if "verification" not in data:
            assert observed["correctness"]["state"] == "unverified"
        assert observed["gain_claim"] is False
        return observed

    return request, invoke, tmp_path


@pytest.mark.parametrize("mode", ["success", "failure", "budget"])
def test_build_stages_survive_success_failure_and_timeout(case, mode):
    request, invoke, _ = case
    data = request()
    code = "print('fixture compiler output')" if mode == "success" else "raise SystemExit(7)" if mode == "failure" else "import time; time.sleep(5)"
    data["fixture_command"] = [sys.executable, "-c", code]
    if mode == "budget":
        data["budget"]["total_seconds"] = 1
    result = invoke("dx100-build", data)
    expected = {"complete"} if mode == "success" else {"failed"} if mode == "failure" else {"timed_out", "budget_exhausted"}
    assert result["outcome"]["state"] in expected
    assert result["stages"][-1]["log_sha256"]


def execution_request(case, behavior="normal"):
    request, invoke, folder = case
    data = request()
    simulator = folder / "fake-simulator"
    simulator.write_text(f"#!{sys.executable}\n" + '''import pathlib,sys,time
args=sys.argv[1:]
out=pathlib.Path(next(a.split('=',1)[1] for a in args if a.startswith('--outdir=')))
out.mkdir(exist_ok=True)
if 'AtomicSimpleCPU' in args:
    child=out/'cpt.100'
    child.mkdir()
    (child/'memory').write_bytes(b'fixture checkpoint')
    print('Exiting @ tick 100 because checkpoint')
else:
    (out/'config.ini').write_text('[fixture]\\nkind=contract_fixture\\n')
    (out/'stats.txt').write_text('---------- Begin Simulation Statistics ----------\\nsimTicks 31300\\nsimFreq 1000000000000\\n')
    print('Exiting @ tick 31400 because m5_exit instruction encountered')
''')
    if behavior == "missing-stats":
        simulator.write_text(simulator.read_text().replace("    print('Exiting @ tick 31400", "    (out/'stats.txt').unlink()\n    print('Exiting @ tick 31400"))
    elif behavior == "timeout":
        simulator.write_text(simulator.read_text().replace("else:\n", "else:\n    time.sleep(5)\n"))
    simulator.chmod(0o755)
    binary = folder / "bfs-fixture"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    graph = folder / "graph.sg"
    graph.write_bytes(b'fixture graph serialization')
    data.update(simulator=reference(simulator), binary=reference(binary),
        workload={"id": "fixture-graph", "source": 0, "representation": reference(graph)},
        configuration={"mode": "MAA", "l3_size_mb": 8, "l3_assoc": 16, "tile_elements": 16384},
        budget={"total_seconds": 20, "memory_gib": 1, "storage_gib": 1, "checkpoint_seconds": 5, "run_seconds": 5})
    return data


@pytest.mark.parametrize('suffix', ['.sg32', '.sg64', '.wsg'])
def test_public_execution_rejects_unloadable_serialized_suffix_before_checkpoint(case, suffix):
    data = execution_request(case)
    _, invoke, folder = case
    graph = folder / ('graph' + suffix)
    graph.write_bytes(Path(data['workload']['representation']['path']).read_bytes())
    data['workload']['representation'] = reference(graph)
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'registered serialized SG representation' in result['outcome']['reason']
    assert not any(stage['stage'] in {'checkpoint', 'simulation'} for stage in result['stages'])


@pytest.mark.parametrize('tamper', [False, True])
def test_public_serialized_alias_preserves_registered_identity_and_checkpoint_reuse(case, records, tamper):
    from test_bfs_protocol import _workload_request
    data = execution_request(case)
    _, invoke, folder = case
    repository = Path(__file__).resolve().parents[1]
    kernel = yaml.safe_load((repository / 'records/kernels/gapbs-bfs.yaml').read_text())
    kernel['baseline_implementation'] = 'dx100-bfs-scalar'
    records.write('kernels/gapbs-bfs.yaml', kernel)
    records.write('implementations/dx100-bfs-scalar.yaml', yaml.safe_load(
        (repository / 'records/implementations/dx100-bfs-scalar.yaml').read_text()))
    request = _workload_request(records, folder, {'num_vertices': 3, 'directed': True, 'edges': [[0,1], [1,2]]})
    registration = folder / 'registered.yaml'
    registration.write_text(yaml.safe_dump(request))
    result = records.swdb('register-workload', registration, '--format', 'json')
    assert result.returncode == 0, result.stderr
    workload = json.loads(result.stdout)
    representation = next(row for row in workload['definition']['representations'] if row['application'] == 'dx100-gapbs')
    original = {key: representation[key] for key in ('path', 'sha256')}
    data['workload'] = {'id': workload['id'], 'source': 0, 'representation': original}
    simulator = Path(data['simulator']['path'])
    program = simulator.read_text().replace('args=sys.argv[1:]', '''args=sys.argv[1:]
selected=pathlib.Path(args[args.index('--options')+1].split()[1])
assert selected.suffix=='.sg' and selected.is_file()
''')
    simulator.write_text(program)
    data['simulator'] = reference(simulator)
    first = invoke('dx100-execute', data)
    assert first['outcome']['state'] == 'complete', first['outcome']
    loader = first['context']['loader_input']
    assert loader['original'] == original
    assert loader['alias']['sha256'] == original['sha256']
    assert first['context']['execution_binding']['workload']['representation'] == original
    assert first['context']['execution_binding']['loader_representation'] == loader['alias']
    data.update(id='alias-replay', checkpoint_manifest=first['context']['checkpoint_manifest'])
    if tamper:
        alias = Path(loader['alias']['path'])
        alias.unlink()
        alias.write_bytes(b'changed alias without changing original')
    second = invoke('dx100-execute', data)
    if tamper:
        assert second['outcome']['state'] == 'failed'
        assert 'alias' in second['outcome']['reason']
        assert not any(row['stage'] in {'checkpoint_resolution', 'checkpoint', 'simulation'} for row in second['stages'])
    else:
        assert second['outcome']['state'] == 'complete', second['outcome']
        assert second['context']['loader_input']['alias'] == loader['alias']
        assert second['context']['loader_input']['provenance']['method'] == 'existing_verified_alias'
        assert second['context']['checkpoint_manifest'] == first['context']['checkpoint_manifest']
        assert any(row['stage'] == 'checkpoint_resolution' for row in second['stages'])
        assert not any(row['stage'] == 'checkpoint' for row in second['stages'])


def test_checkpoint_smoke_is_durable_but_unverified_and_stale_checkpoint_rejected(case):
    data = execution_request(case)
    _, invoke, _ = case
    first = invoke("dx100-execute", data)
    assert first["outcome"]["state"] == "complete"
    assert first["timing"] == []
    assert first["context"]["statistics"]["sha256"]
    data["id"] = "different-source"
    data["workload"]["source"] = 1
    data["checkpoint_manifest"] = first["context"]["checkpoint_manifest"]
    second = invoke("dx100-execute", data)
    assert second["outcome"]["state"] == "incompatible"
    assert "checkpoint binding" in second["outcome"]["reason"]
    assert not any(stage["stage"] == "simulation" for stage in second["stages"])


def test_missing_statistics_does_not_infer_success_from_exit_zero(case):
    data = execution_request(case, "missing-stats")
    _, invoke, _ = case
    result = invoke("dx100-execute", data)
    assert result["outcome"]["state"] == "missing_observation"
    assert "statistics" in result["outcome"]["reason"]
    assert result["raw_artifacts"]


def test_exact_checkpoint_reuse_still_runs_a_fresh_distinct_simulation(case):
    data = execution_request(case)
    _, invoke, _ = case
    first = invoke('dx100-execute', data)
    assert first['outcome']['state'] == 'complete'
    data['id'] = 'same-binding-new-execution'
    data['checkpoint_manifest'] = first['context']['checkpoint_manifest']
    second = invoke('dx100-execute', data)
    assert second['outcome']['state'] == 'complete'
    assert second['context']['execution_binding'] == first['context']['execution_binding']
    assert second['context']['checkpoint_manifest'] == first['context']['checkpoint_manifest']
    assert 'checkpoint' not in [stage['stage'] for stage in second['stages']]
    assert 'checkpoint_resolution' in [stage['stage'] for stage in second['stages']]
    first_log = next(stage['log'] for stage in first['stages'] if stage['stage'] == 'simulation')
    second_run = next(stage for stage in second['stages'] if stage['stage'] == 'simulation')
    assert second_run['state'] == 'complete' and second_run['returncode'] == 0
    assert second_run['log'] != first_log
    assert Path(second_run['log']).is_file() and Path(first_log).is_file()


@pytest.mark.parametrize('legacy,changed_cache', [(False, True), (True, False), (True, True), ('missing', False)])
def test_checkpoint_configuration_is_bound_in_manifest_or_explicit_legacy_proof(case, records, legacy, changed_cache):
    from swdb import artifacts
    data = execution_request(case)
    _, invoke, folder = case
    first = invoke('dx100-execute', data)
    assert first['outcome']['state'] == 'complete'
    reference = first['context']['checkpoint_manifest']
    if legacy:
        manifest = json.loads(Path(reference['path']).read_text())
        manifest['format'] = 'swdb.dx100.checkpoint.v1'
        for key in ('modeled_configuration', 'hardware_target'):
            manifest['binding'].pop(key)
        path = folder / 'legacy-checkpoint.json'
        path.write_text(json.dumps(manifest))
        reference = {'path': str(path), 'sha256': artifacts.file_hash(path)}
        first['context'].update(checkpoint_manifest=reference, execution_binding=manifest['binding'],
            execution_binding_sha256=artifacts.digest(manifest['binding']))
        records.write('evaluations/' + first['id'] + '.yaml', first)
        if legacy != 'missing':
            data['checkpoint_evaluation'] = first['id']
    data.update(id='reuse-config', checkpoint_manifest=reference)
    if changed_cache:
        data['configuration']['l3_size_mb'] = 16
    second = invoke('dx100-execute', data)
    assert second['outcome']['state'] == ('incompatible' if changed_cache or legacy == 'missing' else 'complete')
    if changed_cache or legacy == 'missing':
        assert 'configuration' in second['outcome']['reason']
        assert not any(stage['stage'] == 'simulation' for stage in second['stages'])
    else:
        assert second['context']['checkpoint_compatibility_proof']['source_evaluation'] == first['id']
        assert second['context']['checkpoint_compatibility_proof']['proof_sha256']


def test_changed_binary_is_rejected_before_checkpoint(case):
    data = execution_request(case)
    _, invoke, _ = case
    Path(data["binary"]["path"]).write_text("changed")
    result = invoke("dx100-execute", data)
    assert result["outcome"]["state"] == "failed"
    assert "sha256" in result["outcome"]["reason"]
    assert not any(stage["stage"] == "checkpoint" for stage in result["stages"])


def test_author_binary_tile_mismatch_rejected_before_checkpoint(case):
    data = execution_request(case)
    _, invoke, folder = case
    original = Path(data['binary']['path'])
    binary = folder / 'bfs_maa_1K'
    binary.write_bytes(original.read_bytes())
    binary.chmod(0o755)
    data['binary'] = reference(binary)
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'failed'
    assert 'tile size differs' in result['outcome']['reason']
    assert not any(stage['stage'] in {'checkpoint', 'simulation'} for stage in result['stages'])


@pytest.mark.parametrize('unexpected', [False, True])
def test_pinned_empty_checkpoint_template_directory_is_distinguished_from_payload(case, unexpected):
    data = execution_request(case)
    _, invoke, _ = case
    simulator = Path(data['simulator']['path'])
    extra = "    (out/'cpt.%d').mkdir()\n"
    if unexpected:
        extra += "    (out/'cpt.%d'/'unexpected').write_bytes(b'not an empty placeholder')\n"
    simulator.write_text(simulator.read_text().replace('    child.mkdir()\n', '    child.mkdir()\n' + extra))
    data['simulator'] = reference(simulator)
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == ('missing_observation' if unexpected else 'complete')
    if unexpected:
        assert 'unexpected checkpoint entry' in result['outcome']['reason']
        assert not any(stage['stage'] == 'simulation' for stage in result['stages'])


def test_reference_execution_accepts_explicit_four_hour_stage_but_keeps_build_cap(case):
    request, invoke, _ = case
    data = execution_request(case)
    data['budget'].update(total_seconds=18000, checkpoint_seconds=3600, run_seconds=14400)
    result = invoke('dx100-execute', data)
    assert result['outcome']['state'] == 'complete'
    assert result['context']['budget']['run_seconds'] == 14400
    build = request('oversized-build')
    build['budget']['total_seconds'] = 18000
    build['fixture_command'] = [sys.executable, '-c', 'print("must not execute")']
    rejected = invoke('dx100-build', build)
    assert rejected['outcome']['state'] == 'failed'
    assert 'budget.total_seconds' in rejected['outcome']['reason']
    assert not rejected['stages']


def test_simulation_timeout_preserves_checkpoint_and_failed_stage(case):
    data = execution_request(case, "timeout")
    data["budget"]["run_seconds"] = 1
    _, invoke, _ = case
    result = invoke("dx100-execute", data)
    assert result["outcome"]["state"] == "timed_out"
    assert result["context"]["checkpoint_manifest"]["sha256"]
    assert result["stages"][-1]["stage"] == "simulation"
    assert result["stages"][-1]["state"] == "timed_out"


@pytest.mark.parametrize("behavior,expected", [("PASS", "complete"), ("FAIL", "incorrect"),
    ("absent", "missing_observation"), ("ambiguous", "missing_observation"),
    ("wrong-exit", "missing_observation"), ("timeout", "timed_out")])
def test_same_simulation_continuation_seals_roi_and_retains_explicit_verdict(case, behavior, expected):
    data = execution_request(case)
    _, invoke, folder = case
    model = Path(data["model_root"])
    for name in ("bfs.cc", "benchmark.h"):
        path = model / "benchmarks/gapbs/src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// Explicit verifier source identity fixture.\n")
    (model / "configs/deprecated/example/se.py").write_text(
        "import m5,sys,pathlib\nassert sys.path[0] == str(pathlib.Path(__file__).parent)\n"
        "event=m5.simulate()\nprint('Exiting @ tick 31400 because '+event.getCause())\n")
    simulator = Path(data["simulator"]["path"])
    text = simulator.read_text()
    text = text.replace("    print('Exiting @ tick 31400 because m5_exit instruction encountered')", '''    import runpy,types
    (out/'stats.txt').write_text('---------- Begin Simulation Statistics ----------\\nsimTicks 31300\\nfinalTick 31400\\nsimFreq 1000000000000\\nsystem.maa.numInst 4\\n---------- End Simulation Statistics ----------\\n')
    for unit in 'SIAR':
        print(f'30000: system.maa: {unit}[0] End [fixture instruction]')
    counter=[0]
    def simulate(*args):
        counter[0]+=1
        if counter[0]==1:
            return types.SimpleNamespace(getCause=lambda:'m5_exit instruction encountered',getCode=lambda:0)
        assert counter[0]==2, 'must resume the same simulated machine once'
        (out/'stats.txt').write_text('VERIFICATION MODIFIED LIVE STATS\\n')
        mode=BEHAVIOR
        if mode=='timeout':
            time.sleep(5)
        if mode in ('PASS','FAIL','wrong-exit'):
            print('Verification: '+('PASS' if mode=='wrong-exit' else mode),flush=True)
        elif mode=='ambiguous':
            print('Verification: PASS\\nVerification: PASS',flush=True)
        return types.SimpleNamespace(getCause=lambda:('simulate() limit reached' if mode=='wrong-exit' else 'exiting with last active thread context'),getCode=lambda:0)
    m5=types.ModuleType('m5')
    m5.simulate=simulate
    m5.curTick=lambda:31400 if counter[0]==1 else 40000
    m5.options=types.SimpleNamespace(outdir=str(out))
    sys.modules['m5']=m5
    driver=next(arg for arg in args if arg.endswith('dx100_verify.py'))
    runpy.run_path(driver,run_name='__m5_main__')'''.replace("BEHAVIOR", repr(behavior)))
    simulator.write_text(text)
    data["simulator"] = reference(simulator)
    data["verification"] = {"checker": "dx100.bfs.verifier.v1", "max_ticks": 1000000}
    if behavior == "timeout":
        data["budget"]["run_seconds"] = 1
    result = invoke("dx100-execute", data)
    assert result["outcome"]["state"] == expected, result["outcome"]
    assert result["correctness"]["state"] == ("passed" if behavior == "PASS" else "failed" if behavior == "FAIL" else "unverified")
    sealed = Path(result["context"]["statistics"]["path"])
    assert "simTicks 31300" in sealed.read_text()
    assert "VERIFICATION MODIFIED" not in sealed.read_text()
    check = result["correctness"]["checks"][0]
    assert check["binding"]["binary"] == data["binary"]
    assert check["requested_checks"] == 1
    assert check["coverage"]["accelerator_executed"] is True
    assert check["coverage"]["full_tiles"]["state"] == "unobserved"
    assert check["sealed_roi"]["sha256"]

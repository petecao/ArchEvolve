"""Public native paired collection contracts; fixture evidence only. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-26."""

import copy
import json
import shutil
from pathlib import Path

import pytest

from conftest import make_records
from testkit.proposals import build_proposal_setup
from testkit.bfs_native import build_evaluation_setup
from testkit.bfs_native import PROGRAM
from testkit.bfs_protocol import _command, _payload, _settings, _workload_request
from swdb import artifacts


def _collect(records, runs, tmp, request, *, success=True, env=None):
    result = records.swdb("evaluate-pair", _payload(tmp, request["id"], request),
                         "--runs-dir", runs, "--format", "json", env=env)
    assert result.returncode == (0 if success else 1), result.stdout + result.stderr
    return json.loads(result.stdout) if result.stdout else None


@pytest.fixture(scope="module")
def paired_seed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("paired-seed")
    records = make_records(tmp)
    setup = build_evaluation_setup(build_proposal_setup(records, tmp), tmp)
    _, runs, _, base = setup
    compiler = Path(base["build"]["compiler"])
    # Opposing source effects cancel only when the SAME repetition blocks are
    # drawn for both sources and both roles. All durations are artificial.
    program = PROGRAM.replace('"duration_s": 0.025', '"duration_s": duration')
    program = program.replace('data = {"format"', '''
rep = int(out.stem.split('-')[1])
is_baseline = out.parent.name.endswith('.baseline')
duration = float((rep + 1) ** 2 if source == 0 else 1) if is_baseline else float(rep + 1)
with Path(os.environ['SWDB_PAIR_TRACE']).open('a') as trace:
    trace.write(json.dumps({'event': 'trial', 'binary': sys.argv[0], 'output': str(out)}) + '\\n')
data = {"format"''')
    compiler.write_text("#!/usr/bin/env python3\nimport os,sys,json\nfrom pathlib import Path\n"
        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
        "with Path(os.environ['SWDB_PAIR_TRACE']).open('a') as trace: trace.write(json.dumps({'event':'build'})+'\\n')\n"
        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({program!r}); p.chmod(0o755)\n")
    workload = _command(records, "register-workload", _payload(tmp, "workload",
                        _workload_request(records, tmp, base["workload"]["graph"])))
    result = records.swdb("baseline-candidate", "test-source", "--id", "pair-source-baseline",
                         "--runs-dir", runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    baseline = json.loads(result.stdout)["id"]
    settings = _settings(base, workload)
    collection = {"method": "native_paired.v1", "order_seed": 20260926}
    settings["sampling"].update(collection=collection, analysis="paired_repetition_block_bootstrap.v1")
    settings["profitability"].update(minimum_speedup=1.05, bootstrap_seed=20260925, maximum_relative_spread=10)
    frozen = _command(records, "freeze-protocol", _payload(tmp, "policy", {
        "message_version": "1.0", "id": "paired-policy", "version": 1, "settings": settings}))
    request = {"message_version": "1.0", "id": "ab-pair", "collection": collection, "budget": {"total_seconds": 240}}
    for role in ("baseline", "candidate"):
        request[role] = {**copy.deepcopy(base), "id": "ab." + role,
            "candidate": baseline if role == "baseline" else base["candidate"], "protocol_role": role,
            "protocol": frozen["id"], "workload": {"id": workload["id"]},
            "sources": workload["definition"]["sources"], "repetitions": 5,
            "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 240}}
    trace = tmp / "ab-trace.jsonl"
    pair = _collect(records, runs, tmp, request, env={"SWDB_PAIR_TRACE": str(trace)})
    comparison = {"message_version": "1.0", "id": "paired-comparison", "protocol": frozen["id"],
        "baseline_evaluation": pair["baseline_evaluation"], "candidate_evaluation": pair["candidate_evaluation"],
        "comparison_baseline": "gapbs-bfs-do"}
    return records, runs, request, pair, frozen, comparison, trace


@pytest.fixture
def paired_setup(records, paired_seed):
    seed, *data = paired_seed
    shutil.copytree(seed.path, records.path, dirs_exist_ok=True)
    return records, *copy.deepcopy(data)


def test_public_pair_builds_first_preserves_order_and_bootstraps_whole_blocks(paired_setup, tmp_path):
    records, _, request, pair, frozen, comparison, trace = paired_setup
    assert pair["outcome"]["state"] == "complete" and pair["evidence_kind"] == "contract_fixture"
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [row["event"] for row in events] == ["build"] * 2 + ["trial"] * 20
    assert [row["output"] for row in events[2:]] == [row["output"] for row in pair["observations"]]
    assert len({row["output"] for row in events[2:]}) == 20
    for a, b in zip(pair["schedule"][::2], pair["schedule"][1::2]):
        assert a["source"] == b["source"] and a["block"] == b["block"] and a["role"] != b["role"]
    result = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison))
    assert result["decision"]["state"] == "fixture_comparison" and not result["gain_claim"]
    assert result["metrics"]["fixture_ratio"] == pytest.approx(1)
    interval = result["metrics"]["confidence_interval"]
    assert interval["lower"] == pytest.approx(1) and interval["upper"] == pytest.approx(1)
    assert interval["method"] == "paired_repetition_block_bootstrap.v1"
    later = records.swdb("get", result["id"], "--chain", "--format", "json")
    assert later.returncode == 0, later.stderr
    chain = json.loads(later.stdout)["records"]
    assert chain[pair["id"]] == pair
    assert all(chain[pair[role + "_evaluation"]]["context"]["pairing"]["pair_id"] == pair["id"] for role in ("baseline", "candidate"))


def test_same_candidate_aa_reuses_one_executable_and_ten_pairs_balance(paired_setup, tmp_path):
    records, runs, request, _, _, _, _ = paired_setup
    request["id"] = "aa-pair"
    for role in ("baseline", "candidate"):
        request[role].update(id="aa." + role, repetitions=10, candidate=request["baseline"]["candidate"])
        request[role].pop("protocol")
        request[role].pop("protocol_role")
    trace = tmp_path / "aa-trace.jsonl"
    pair = _collect(records, runs, tmp_path, request, env={"SWDB_PAIR_TRACE": str(trace)})
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [row["event"] for row in events] == ["build"] + ["trial"] * 40
    assert len({row["binary"] for row in events[1:]}) == 1
    for source in request["baseline"]["sources"]:
        first = [row["role"] for row in pair["schedule"][::2] if row["source"] == source]
        assert first.count("baseline") == first.count("candidate") == 5
    assert json.loads(records.swdb("get", pair["id"], "--format", "json").stdout) == pair


@pytest.mark.parametrize("fault", ["incomplete", "order", "pair-id", "missing-binding", "timing", "correctness", "missing-observation"])
def test_public_comparison_rejects_changed_or_unpaired_evidence(paired_setup, tmp_path, fault):
    records, _, _, pair, _, comparison, _ = paired_setup
    candidate = records.read("evaluations/" + pair["candidate_evaluation"] + ".yaml")
    if fault == "incomplete": pair["outcome"]["state"] = "failed"
    elif fault == "order": pair["schedule"][0], pair["schedule"][1] = pair["schedule"][1], pair["schedule"][0]
    elif fault == "pair-id": candidate["context"]["pairing"]["pair_id"] = "another-pair"
    elif fault == "missing-binding": candidate["context"].pop("pairing")
    elif fault == "timing": candidate["timing"][0]["pairing"]["sequence"] += 1
    elif fault == "correctness": candidate["correctness"]["checks"][0]["pairing"]["block"] += 1
    else: pair["observations"].pop()
    # Re-sealing the receipt alone cannot excuse a missing grid or invalid order.
    pair["receipt_sha256"] = artifacts.digest({k: v for k, v in pair.items() if k != "receipt_sha256"})
    records.write("evaluation_pairs/" + pair["id"] + ".yaml", pair)
    records.write("evaluations/" + candidate["id"] + ".yaml", candidate)
    result = _command(records, "compare-evaluations", _payload(tmp_path, "bad", comparison), succeeds=False)
    assert result["decision"]["state"] == "rejected" and not result["gain_claim"]


def test_serial_dispatch_cannot_impersonate_paired_collection(paired_setup, tmp_path):
    records, runs, request, *_ = paired_setup
    member = request["baseline"]
    member["id"] = "serial-impostor"
    result = records.swdb("evaluate", _payload(tmp_path, "serial", member), "--runs-dir", runs, "--format", "json")
    assert result.returncode == 1, result.stderr
    evaluation = json.loads(result.stdout)
    assert "collection method" in evaluation["outcome"]["reason"] and not evaluation["timing"]


@pytest.mark.parametrize("fault", ["floor", "analysis", "seed", "count", "collection"])
def test_paired_freeze_rejects_weakened_or_ambiguous_policy(paired_setup, tmp_path, fault):
    records, _, _, _, frozen, *_ = paired_setup
    settings = frozen["settings"]
    if fault == "floor": settings["profitability"]["minimum_speedup"] = 1.01
    elif fault == "analysis": settings["sampling"].pop("analysis")
    elif fault == "seed": settings["profitability"]["bootstrap_seed"] = 17
    elif fault == "count": settings["sampling"]["repetitions"] = 4
    else: settings["sampling"]["collection"]["method"] = "serial.v1"
    result = records.swdb("freeze-protocol", _payload(tmp_path, "invalid-policy", {
        "message_version": "1.0", "id": "invalid-policy", "version": 1, "settings": settings}), "--format", "json")
    assert result.returncode == 1 and result.stderr


def test_failed_pair_retains_partial_checked_evidence(paired_setup, tmp_path):
    records, runs, request, *_ = paired_setup
    request["id"] = "failed-pair"
    for role in ("baseline", "candidate"):
        request[role]["id"] = "failed." + role
    trace = tmp_path / "failure-trace.jsonl"
    pair = _collect(records, runs, tmp_path, request, success=False,
                    env={"SWDB_PAIR_TRACE": str(trace), "SWDB_NATIVE_FIXTURE": "wrong_source"})
    assert pair["outcome"]["state"] == "failed"
    assert not pair["observations"]
    chain = json.loads(records.swdb("get", pair["id"], "--chain", "--format", "json").stdout)["records"]
    evaluations = [chain[pair[role + "_evaluation"]] for role in ("baseline", "candidate")]
    assert sum(len(row["timing"]) for row in evaluations) == 1
    assert any(row["correctness"]["state"] == "failed" for row in evaluations)
    assert all(row["outcome"]["state"] != "running" for row in evaluations)


@pytest.mark.parametrize("fault", ["raw-output", "null-binding", "duration", "null-trial-binding"])
def test_resealed_metadata_cannot_hide_changed_raw_or_missing_binding(paired_setup, tmp_path, fault):
    records, _, _, pair, _, comparison, _ = paired_setup
    baseline = records.read("evaluations/" + pair["baseline_evaluation"] + ".yaml")
    if fault == "null-binding":
        baseline["context"]["pairing"] = None
    elif fault in {"duration", "null-trial-binding"}:
        observation = baseline["timing"][0]
        if fault == "duration":
            observation["duration_s"] *= 2
        else:
            observation["pairing"] = None
            baseline["correctness"]["checks"][0]["pairing"] = None
        receipt = next(row for row in pair["observations"] if row["role"] == "baseline")
        receipt.update(observation_sha256=artifacts.digest(observation),
                       correctness_sha256=artifacts.digest(baseline["correctness"]["checks"][0]))
    else:
        observation = baseline["timing"][0]
        damaged = tmp_path / "damaged-output.json"
        damaged.write_text('{"duration_s": 999}')
        observation["output"] = str(damaged)
        receipt = next(row for row in pair["observations"] if row["role"] == "baseline")
        receipt.update(output=str(damaged), observation_sha256=artifacts.digest(observation))
    pair["evaluation_identities"][baseline["id"]] = artifacts.digest(baseline)
    pair["receipt_sha256"] = artifacts.digest({k: v for k, v in pair.items() if k != "receipt_sha256"})
    records.write("evaluations/" + baseline["id"] + ".yaml", baseline)
    records.write("evaluation_pairs/" + pair["id"] + ".yaml", pair)
    result = _command(records, "compare-evaluations", _payload(tmp_path, "changed-raw", comparison), succeeds=False)
    assert result["decision"]["state"] == "rejected"
    reason = result["decision"]["reasons"][0]
    expected = {"raw-output": "raw execution evidence", "null-binding": "paired collection binding",
                "duration": "hash-bound raw output", "null-trial-binding": "schedule binding"}
    assert expected[fault] in reason


def test_consistently_rehashed_invalid_raw_parents_are_rejected(paired_setup, tmp_path):
    records, _, _, pair, _, comparison, _ = paired_setup
    baseline = records.read("evaluations/" + pair["baseline_evaluation"] + ".yaml")
    observation = baseline["timing"][0]
    check = baseline["correctness"]["checks"][0]
    raw = json.loads(Path(observation["output"]).read_text())
    raw["parents"] = []
    damaged = tmp_path / "rehashed-invalid-parents.json"
    damaged.write_text(json.dumps(raw))
    observation.update(output=str(damaged), output_sha256=artifacts.file_hash(damaged))
    check["output_sha256"] = observation["output_sha256"]
    assert check["passed"] is True  # The retained verdict is deliberately false.
    receipt = next(row for row in pair["observations"] if row["role"] == "baseline")
    receipt.update(output=str(damaged), output_sha256=observation["output_sha256"],
                   observation_sha256=artifacts.digest(observation), correctness_sha256=artifacts.digest(check))
    pair["evaluation_identities"][baseline["id"]] = artifacts.digest(baseline)
    pair["receipt_sha256"] = artifacts.digest({k: v for k, v in pair.items() if k != "receipt_sha256"})
    records.write("evaluations/" + baseline["id"] + ".yaml", baseline)
    records.write("evaluation_pairs/" + pair["id"] + ".yaml", pair)
    result = _command(records, "compare-evaluations", _payload(tmp_path, "invalid-parents", comparison), succeeds=False)
    assert result["decision"]["state"] == "rejected" and not result["gain_claim"]
    assert "parent vector length differs" in result["decision"]["reasons"][0]
    retrieved = records.swdb("get", result["id"], "--format", "json")
    assert retrieved.returncode == 0 and json.loads(retrieved.stdout) == result


def test_paired_admission_reopens_and_revalidates_registered_graph(paired_setup, tmp_path):
    records, _, _, _, frozen, comparison, _ = paired_setup
    workload = records.read("workloads/" + frozen["settings"]["workloads"][0] + ".yaml")
    representation = Path(workload["definition"]["representations"][0]["path"])
    original = representation.read_bytes()
    graph = json.loads(original)
    graph["edges"].append([3, 4])
    # The module seed's graph is restored even if the assertion fails. Each pytest
    # invocation owns its seed directory; no other test/process uses this file.
    try:
        representation.write_text(json.dumps(graph))
        result = _command(records, "compare-evaluations", _payload(tmp_path, "changed-graph", comparison), succeeds=False)
    finally:
        representation.write_bytes(original)
    assert result["decision"]["state"] == "rejected" and not result["gain_claim"]
    assert "representation content hash differs" in result["decision"]["reasons"][0]

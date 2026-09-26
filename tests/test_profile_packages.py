"""Public profile assembly, lookup, and patch handoff. Created 2026-09-25.

Compiler/discovery contract fixtures cannot claim experimental gains.
"""
import copy
import difflib
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from conftest import records as records_fixture
from test_bfs_native import evaluation_setup
from test_bfs_protocol import _payload
from test_proposals import proposal_setup


def _read(records, rid):
    result = records.swdb("get", rid, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def package_seed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("package-seed")
    records = records_fixture.__wrapped__(tmp)
    proposal = proposal_setup.__wrapped__(records, tmp)
    records, runs, evaluate, base = evaluation_setup.__wrapped__(proposal, tmp)
    records.copy_repo("strategies", "intrinsics")
    evaluated = records.swdb("evaluate", evaluate(id="package-evaluation"), "--runs-dir", runs, "--format", "json")
    assert evaluated.returncode == 0, evaluated.stderr
    evaluation = json.loads(evaluated.stdout)
    candidate = _read(records, evaluation["candidate"])
    file = Path(candidate["artifact"]["path"]) / "src/bfs.cc"
    raw = file.read_bytes()
    regions, lines = [], raw.splitlines(keepends=True)
    for kind, first, last in (("function", 67, 89), ("loop", 74, 85)):
        start, end = sum(map(len, lines[:first-1])), sum(map(len, lines[:last]))
        fragment = raw[start:end]
        regions.append({"id": f"fixture-{kind}", "kind": kind, "path": "src/bfs.cc", "lines": [first,last],
                        "byte_range": [start,end], "source_sha256": hashlib.sha256(fragment).hexdigest(),
                        "text": fragment.decode(), "function": "TDStep", "callers": ["DOBFS"], "helpers": [],
                        "metrics": {"inclusive_thread_cpu_seconds": 0.02, "exclusive_thread_cpu_seconds": 0.01, "invocations": 3},
                        "basis": "measured", "scope": "accumulated diagnostic ROI; contract fixture",
                        "artifact_sha256": "d"*64, "source_artifact_sha256": candidate["artifact"]["sha256"]})
    executions, memory = [], []
    for position, source_id in enumerate(evaluation["context"]["sources"]):
        for kind in ("regions", "memory"):
            output = tmp / f"fixture-{kind}-{position}.json"
            output.write_text(json.dumps({"source": source_id, "contract_fixture": True, "value": 123}))
            sha = hashlib.sha256(output.read_bytes()).hexdigest()
            execution = {"kind": kind, "source": source_id, "source_position": position, "repetition": 0,
                         "binary_sha256": "d"*64, "output": str(output), "output_sha256": sha,
                         "evidence_kind": "contract_fixture"}
            if kind == "regions":
                execution.update(region_output=str(output), region_output_sha256=sha)
            else:
                execution.update(raw_artifact=str(output), raw_sha256=sha)
                memory.append({"metric": "data_reads", "available": True, "value": 123, "unit": "accesses",
                               "definition": "fixture cache-model read accesses", "basis": "simulated", "scope": "ROI",
                               "collector": "fixture-model", "artifact_sha256": "d"*64,
                               "source_artifact_sha256": candidate["artifact"]["sha256"],
                               "execution": {"source": source_id, "source_position": position, "repetition": 0},
                               "raw_artifact": str(output), "raw_sha256": sha})
            executions.append(execution)
    profile = {key: copy.deepcopy(evaluation[key]) for key in ("schema_version", "status", "created", "updated", "provenance", "message_version", "producer")}
    profile.update(kind="region_profile", id="package-diagnostics", request={"fixture": True},
                   evaluation=evaluation["id"], candidate=candidate["id"], source_snapshot=candidate["source_snapshot"],
                   implementation=candidate["implementation"], machine=evaluation["machine"],
                   context={**copy.deepcopy(evaluation["context"]), "primary_binary_sha256": evaluation["build"]["binary_sha256"]},
                   discovery={"backend": "contract-fixture", "scope": "two fixture regions", "limitations": ["fixture attribution only"]},
                   outcome={"state": "complete", "stage": "completed", "reason": None}, stages=[], regions=regions,
                   dynamic_memory=memory, executions=executions, raw_artifacts=[], reasons=[], gain_claim=False)
    added = records.swdb("add", _payload(tmp, "profile", profile))
    assert added.returncode == 0, added.stderr
    context = evaluation["context"]
    request = {"message_version": "1.0", "id": "assembled", "implementation": evaluation["implementation"],
               "evaluation": evaluation["id"], "region_profile": profile["id"],
               "context": {"source_sha256": context["candidate_sha256"], "canonical_graph_sha256": context["workload"]["canonical_sha256"],
                           "sources": context["sources"], "target": context["target"], "target_configuration": context["backend_configuration"],
                           "threads": context["threads"], "roi": context["roi"]}}
    return records, request, evaluation, profile, candidate


@pytest.fixture
def package_setup(package_seed, records):
    source, request, evaluation, profile, candidate = package_seed
    shutil.copytree(source.path, records.path, dirs_exist_ok=True)
    return records, copy.deepcopy(request), copy.deepcopy(evaluation), copy.deepcopy(profile), copy.deepcopy(candidate)


def _assemble(records, tmp, request):
    result = records.swdb("profile-package", _payload(tmp, request["id"], request), "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_exact_fixture_package_has_source_and_bidirectional_strategies(package_setup, tmp_path):
    records, request, _, profile, candidate = package_setup
    package = _assemble(records, tmp_path, request)
    assert package["completeness"] == "fixture" and package["gain_claim"] is False
    assert package["evidence"]["classification"] == "contract_fixture"
    assert package["regions"] == [{**r, "source_association": "verified_current_candidate"} for r in profile["regions"]]
    assert package["dynamic_memory"][0]["scope"] == "ROI"
    assert package["evidence"]["full_application"] == candidate["artifact"]
    assert any(f["path"].endswith("graph.h") for f in package["evidence"]["supporting_sources"])
    forward = records.swdb("profile-strategies", package["id"], "--region", "fixture-loop", "--format", "json")
    assert forward.returncode == 0, forward.stderr
    matches = json.loads(forward.stdout)["matches"]
    assert matches and all(m["outcome"] == "undetermined" for m in matches)
    assert all("current_region_semantics" in m["unknown_fields"] and m["measured_outcomes"] is None for m in matches)
    reverse = records.swdb("strategy-regions", "software_prefetch", "--package", package["id"], "--format", "json")
    assert reverse.returncode == 0, reverse.stderr
    reverse = json.loads(reverse.stdout)
    assert reverse["static_matches"] and reverse["profiled_matches"]
    assert all(row["profile_support"] == "incomplete_or_fixture" for row in reverse["profiled_matches"])
    assert not reverse["performance_guarantee"]


@pytest.mark.parametrize("missing", ["memory", "collector", "function", "loop", "profile", "binary", "source", "memory-binary", "execution"])
def test_missing_or_stale_required_evidence_stays_incomplete(package_setup, tmp_path, missing):
    records, request, _, profile, _ = package_setup
    if missing == "memory": profile["dynamic_memory"] = []
    elif missing == "collector":
        for row in profile["dynamic_memory"]: row.pop("collector")
    elif missing in {"function", "loop"}: profile["regions"] = [r for r in profile["regions"] if r["kind"] != missing]
    elif missing == "profile": request.pop("region_profile")
    elif missing == "binary": profile["context"]["primary_binary_sha256"] = "0"*64
    elif missing == "memory-binary": profile["dynamic_memory"][0]["artifact_sha256"] = "0"*64
    elif missing == "execution": profile["executions"] = []
    else: profile["regions"][0]["source_sha256"] = "0"*64
    records.write("region_profiles/package-diagnostics.yaml", profile)
    package = _assemble(records, tmp_path, request)
    assert package["completeness"] == "incomplete" and package["reasons"]
    assert not package["gain_claim"]


@pytest.mark.parametrize("field", ["sources", "source_sha256", "canonical_graph_sha256", "target_configuration", "threads", "roi", "boolean-threads"])
def test_exact_context_does_not_fall_back_to_other_evidence(package_setup, tmp_path, field):
    records, request, _, _, _ = package_setup
    key = "threads" if field == "boolean-threads" else field
    request["context"][key] = {"sources": [4], "source_sha256": "0"*64, "canonical_graph_sha256": "f"*64,
                               "target_configuration": {"other": True}, "threads": 7, "roi": "other", "boolean-threads": True}[field]
    result = records.swdb("profile-package", _payload(tmp_path, "bad-context", request), "--format", "json")
    assert result.returncode == 1 and "differs from evaluation" in result.stderr
    assert not list((records.path / "profile_packages").glob("assembled*.yaml"))


def test_package_rewrites_current_candidate_and_links_survive_rebuild(package_setup, tmp_path):
    records, request, _, _, candidate = package_setup
    package = _assemble(records, tmp_path, request)
    source = _read(records, package["source_snapshot"])
    assert source["artifact"]["sha256"] == candidate["artifact"]["sha256"]
    current = (Path(source["artifact"]["path"]) / "src/bfs.cc").read_text()
    assert "int alpha = 14" in current
    patch = "".join(difflib.unified_diff(current.splitlines(keepends=True), current.replace("int alpha = 14", "int alpha = 13").splitlines(keepends=True),
                                       fromfile="a/src/bfs.cc", tofile="b/src/bfs.cc"))
    proposal = {"message_version": "1.0", "id": "from-package", "producer": {"name": "contract-test", "role": "sw", "test_client": True},
                "profile_package": package["id"], "source_snapshot": source["id"], "implementation": package["implementation"],
                "source_sha256": source["artifact"]["sha256"], "intent": "contract fixture patch from measured candidate source",
                "regions": [package["regions"][0]["id"]], "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, "required_operations": []}
    result = records.swdb("submit", _payload(tmp_path, "proposal", proposal), "--runs-dir", tmp_path / "runs", "--format", "json")
    assert result.returncode == 0, result.stderr + result.stdout
    submitted = json.loads(result.stdout)
    assert records.swdb("build").returncode == 0
    chain = json.loads(records.swdb("get", submitted["candidate"], "--chain", "--format", "json").stdout)["records"]
    assert chain[package["id"]] == package
    assert package["evaluation"] in chain and package["region_profile"] in chain
    assert "int alpha = 13" in (Path(chain[submitted["candidate"]]["artifact"]["path"]) / "src/bfs.cc").read_text()


def test_result_query_discovers_refreshed_profiles_and_packages(package_setup, tmp_path):
    records, request, evaluation, profile, candidate = package_setup
    package = _assemble(records, tmp_path, request)
    assert records.swdb("build").returncode == 0
    for root in (evaluation['id'], candidate['id']):
        result = records.swdb('get', root, '--chain', '--format', 'json')
        assert result.returncode == 0, result.stderr
        chain = json.loads(result.stdout)['records']
        assert chain[evaluation['id']] == evaluation
        assert chain[profile['id']] == profile
        assert chain[package['id']] == package
        assert chain[package['source_snapshot']]['artifact']['sha256'] == candidate['artifact']['sha256']


def test_new_version_preserves_old_package(package_setup, tmp_path):
    records, request, _, _, _ = package_setup
    first = _assemble(records, tmp_path, request)
    again = records.swdb("profile-package", _payload(tmp_path, "duplicate", request), "--format", "json")
    assert again.returncode == 1 and "newer version" in again.stderr
    request["version"] = 2
    second = _assemble(records, tmp_path, request)
    assert first["id"] != second["id"]
    assert _read(records, first["id"]) == first


def test_simulated_attribution_and_correctness_state_remain_distinct(package_setup, tmp_path):
    records, request, evaluation, profile, _ = package_setup
    evaluation["correctness"]["state"] = "unverified"
    for trial in evaluation["timing"]: trial["verified"] = False
    records.write("evaluations/package-evaluation.yaml", evaluation)
    for row in profile["regions"]:
        row["metrics"] = {"inclusive_simulated_seconds": 0.1, "exclusive_simulated_seconds": 0.05, "invocations": 2}
        row["basis"] = "simulated"
        row["scope"] = "accumulated simulated ROI"
    records.write("region_profiles/package-diagnostics.yaml", profile)
    package = _assemble(records, tmp_path, request)
    assert package["completeness"] == "fixture"
    assert package["evidence"]["primary_correctness"]["state"] == "unverified"
    assert all(row["metric"] == "exclusive_simulated_seconds" for row in package["evidence"]["rankings"])
    assert not package["gain_claim"]


def test_query_rejects_changed_package_under_retained_identity(package_setup, tmp_path):
    records, request, _, _, _ = package_setup
    package = _assemble(records, tmp_path, request)
    package["context"]["threads"] = 70
    records.write(f"profile_packages/{package['id']}.yaml", package)
    result = records.swdb("profile-strategies", package["id"], "--format", "json")
    assert result.returncode == 1 and "retained identity" in result.stderr


def test_raw_add_cannot_claim_assembled_completeness(package_setup, tmp_path):
    records, request, _, _, _ = package_setup
    package = _assemble(records, tmp_path, request)
    package.update(id="invented-complete", completeness="complete")
    added = records.swdb("add", _payload(tmp_path, "invented", package))
    assert added.returncode == 1 and "created through profile-package" in added.stderr


def test_new_snapshot_of_a_prior_rewrite_does_not_restore_baseline_semantics(package_setup, tmp_path):
    records, request, evaluation, profile, _ = package_setup
    first = _assemble(records, tmp_path, request)
    result = records.swdb("baseline-candidate", first["source_snapshot"], "--id", "rebased-start",
                          "--runs-dir", tmp_path / "rebased", "--format", "json")
    assert result.returncode == 0, result.stderr
    next_candidate = json.loads(result.stdout)
    evaluate = copy.deepcopy(evaluation["request"])
    evaluate.update(id="rebased-evaluation", candidate=next_candidate["id"])
    result = records.swdb("evaluate", _payload(tmp_path, "rebased-evaluate", evaluate),
                          "--runs-dir", tmp_path / "rebased-runs", "--format", "json")
    assert result.returncode == 0, result.stderr
    next_eval = json.loads(result.stdout)
    profile.update(id="rebased-diagnostics", evaluation=next_eval["id"], candidate=next_candidate["id"],
                   source_snapshot=next_candidate["source_snapshot"],
                   context={**copy.deepcopy(next_eval["context"]), "primary_binary_sha256": next_eval["build"]["binary_sha256"]})
    added = records.swdb("add", _payload(tmp_path, "rebased-profile", profile))
    assert added.returncode == 0, added.stderr
    request.update(id="rebased-package", evaluation=next_eval["id"], region_profile=profile["id"])
    second = _assemble(records, tmp_path, request)
    assert second["strategies"]
    assert all(row["source_correspondence"] == "unresolved_after_rewrite" for row in second["strategies"])


@pytest.mark.parametrize('fault', [None, 'diagnostic-position', 'diagnostic-repetition', 'primary-position'])
def test_simulated_component_preserves_global_frozen_trial_cell(package_setup, tmp_path, fault):
    records, request, evaluation, profile, _ = package_setup
    trial = {'source_position': 2, 'repetition': 1}
    evaluation['context'].update(basis='simulated', protocol_trial=trial, repetitions=1)
    for row in evaluation['timing']:
        row.update(**trial, basis='simulated', quantity='simulated_roi_seconds')
    for row in evaluation['correctness']['checks']:
        row.update(**trial)
    profile['context'].update(basis='simulated', protocol_trial=trial, repetitions=1)
    for row in profile['regions']:
        row['basis'] = 'simulated'
        row['metrics'] = {'inclusive_simulated_seconds': 0.02, 'exclusive_simulated_seconds': 0.01, 'invocations': 3}
    for row in profile['executions']:
        row.update(**trial)
    for row in profile['dynamic_memory']:
        row['execution'].update(**trial)
    if fault == 'diagnostic-position':
        for row in profile['executions']: row['source_position'] = 0
    elif fault == 'diagnostic-repetition':
        for row in profile['executions']: row['repetition'] = 0
    elif fault == 'primary-position':
        for row in evaluation['timing']: row['source_position'] = 0
    records.write('evaluations/package-evaluation.yaml', evaluation)
    records.write('region_profiles/package-diagnostics.yaml', profile)
    result = _assemble(records, tmp_path, request)
    assert result['completeness'] == ('incomplete' if fault else 'fixture')
    assert not result['gain_claim']
    if fault:
        assert any('source sequence' in reason for reason in result['reasons'])
    else:
        assert result['evidence']['diagnostic_executions'][0]['source_position'] == 2
        assert result['evidence']['primary_timing'][0]['repetition'] == 1

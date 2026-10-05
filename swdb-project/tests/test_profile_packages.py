"""Public profile assembly, lookup, and patch handoff. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-26.

Compiler/discovery contract fixtures cannot claim experimental gains.
"""
import copy
import difflib
import json
from pathlib import Path

import pytest

from testkit.bfs_protocol import _payload
from testkit.profile_packages import _assemble, _callgrind_profile, _read


@pytest.mark.parametrize('fault', ['a3-underflow', 'misses-exceed-references', 'll-exceeds-l1',
                                  'noninteger', 'one-bad-execution', 'duplicate', 'split-raw-identity'])
def test_inconsistent_callgrind_group_never_completes_package(package_setup, tmp_path, fault):
    records, request, _, profile, _ = package_setup
    _callgrind_profile(profile, tmp_path, fault)
    records.write('region_profiles/package-diagnostics.yaml', profile)
    package = _assemble(records, tmp_path, request)
    assert package['completeness'] == 'incomplete'
    assert any('Callgrind execution' in reason and 'inconsistent' in reason for reason in package['reasons'])
    assert package['dynamic_memory'] == profile['dynamic_memory']  # Never repair or erase observed values.
    if fault == 'a3-underflow':
        assert any('no available dynamic memory observation' in reason for reason in package['reasons'])
        assert any(row['metric'] == 'Dr' and row['value'] == 0 for row in package['dynamic_memory'])


@pytest.mark.parametrize('fault', [None, 'write-only'])
def test_consistent_callgrind_references_and_misses_remain_available(package_setup, tmp_path, fault):
    records, request, _, profile, _ = package_setup
    _callgrind_profile(profile, tmp_path, fault)
    records.write('region_profiles/package-diagnostics.yaml', profile)
    package = _assemble(records, tmp_path, request)
    assert package['completeness'] == 'fixture' and package['reasons'] == []


@pytest.mark.parametrize('location', ['top-level', 'extensions'])
def test_post_collection_audit_invalidates_previously_plausible_memory(package_setup, tmp_path, location):
    records, request, _, profile, _ = package_setup
    _callgrind_profile(profile, tmp_path)
    container = profile if location == 'top-level' else profile.setdefault('extensions', {})
    container['post_collection_audit'] = {'scope': 'dynamic_memory', 'state': 'invalid',
        'reason': 'explicit contract-fixture invalid ROI attribution', 'original_observations_retained': True,
        'region_observations_affected': False}
    records.write('region_profiles/package-diagnostics.yaml', profile)
    package = _assemble(records, tmp_path, request)
    assert package['completeness'] == 'incomplete'
    assert any('post-collection audit failed' in reason for reason in package['reasons'])
    assert package['dynamic_memory'] == profile['dynamic_memory']


def test_plausible_but_miscopied_callgrind_value_is_not_an_observation(package_setup, tmp_path):
    records, request, _, profile, _ = package_setup
    _callgrind_profile(profile, tmp_path)
    # Both values satisfy every counter inequality; only raw re-parsing catches
    # this possible transcription/collector defect despite its correct file hash.
    profile['dynamic_memory'][0]['value'] = 201
    records.write('region_profiles/package-diagnostics.yaml', profile)
    package = _assemble(records, tmp_path, request)
    assert package['completeness'] == 'incomplete'
    assert any('retained Dr differs from its raw event summary' in reason for reason in package['reasons'])
    assert package['dynamic_memory'][0]['value'] == 201


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

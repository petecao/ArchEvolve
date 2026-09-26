"""Public acceptance reporting fails closed on missing/fixture evidence. Created 2026-09-25."""

import copy
import json

import pytest

from test_bfs_protocol import _payload
from test_profile_packages import package_seed, package_setup
from swdb import artifacts, profile_package


def _report(records, tmp_path, **updates):
    request = {"message_version": "1.0", "id": "coverage", "candidate_protocols": [],
               "artifact_reference_comparisons": [], "controlled_reference_comparisons": [], **updates}
    result = records.swdb("bfs-coverage", _payload(tmp_path, "coverage", request), "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_empty_public_report_keeps_every_required_cell_and_criterion(records, tmp_path):
    records.copy_repo("applications", "kernels", "implementations", "intrinsics", "strategies", "profiles", "inputs", "machines")
    report = _report(records, tmp_path)
    assert report["acceptance"] == "incomplete" and report["gain_claim"] is False
    assert len(report["matrix"]) == 8
    assert {(c["starting_implementation"], c["route"], c["graph_family"]) for c in report["matrix"]} == {
        (source, route, family) for source in ("dx100-bfs-scalar", "gapbs-bfs-do")
        for route in ("instruction", "supplied_code") for family in ("kronecker", "uniform_random")}
    assert all(c["state"] == "incomplete" and c["reasons"] for c in report["matrix"])
    assert set(report["criteria"]) == {f"AC{i:02d}" for i in range(1,21)}
    assert all(r["state"] == "incomplete" for r in report["reference_obligations"].values())


def test_fixture_execution_and_missing_protocol_are_retained_but_never_counted(package_setup, tmp_path):
    records, _, evaluation, _, _ = package_setup
    report = _report(records, tmp_path, candidate_protocols=["missing-frozen-policy"])
    assert report["missing_protocols"] == ["missing-frozen-policy"]
    attempt = next(row for row in report["unassigned_evaluations"] if row["evaluation"] == evaluation["id"])
    assert not attempt["qualified"] and any("fixtures" in reason for reason in attempt["reasons"])
    assert report["history"]["proposal"] and report["history"]["evaluation"]
    assert report["acceptance"] == "incomplete" and not report["qualifying_candidate_gains"]
    before = report["identity_sha256"]
    assert records.swdb("build").returncode == 0
    assert _report(records, tmp_path, candidate_protocols=["missing-frozen-policy"])["identity_sha256"] == before


@pytest.mark.parametrize("case", ["promoted-fixture", "functional-api", "wrong-roi", "missing-correctness", "false-gain"])
def test_claim_labels_cannot_satisfy_real_acceptance(package_setup, tmp_path, case):
    records, _, evaluation, _, _ = package_setup
    if case == "promoted-fixture": evaluation["evidence_kind"] = "execution"
    elif case == "functional-api": evaluation["build"]["flags"].append("-DMAA")
    elif case == "wrong-roi": evaluation["timing"][0]["roi"] = "simulator-host-runtime"
    elif case == "missing-correctness": evaluation["correctness"] = {"state": "unverified", "checks": []}
    else:
        result = {key: copy.deepcopy(evaluation[key]) for key in ("schema_version", "status", "created", "updated", "provenance", "message_version", "producer")}
        result.update(kind="comparison_result", id="unsupported-gain", request={}, decision={"state": "gain", "reasons": []},
                      metrics={"roi_speedup": 1000}, evidence_kind="execution", gain_claim=True,
                      region_comparisons=[], finished_at="2026-09-25T20:00:00Z")
        added = records.swdb("add", _payload(tmp_path, "false-gain", result))
        assert added.returncode == 0, added.stderr
    records.write("evaluations/package-evaluation.yaml", evaluation)
    report = _report(records, tmp_path)
    assert report["acceptance"] == "incomplete" and report["gain_claim"] is False
    assert all(cell["state"] == "incomplete" for cell in report["matrix"])
    if case == "functional-api":
        assert any("functional accelerator" in reason for item in report["unassigned_evaluations"] for reason in item["reasons"])
    if case == "false-gain":
        assert report["comparison_assessments"][0]["qualified"] is False
        assert report["comparison_assessments"][0]["reasons"]


def test_missing_remote_artifacts_are_exposed_as_unverified(package_setup, tmp_path):
    records, _, evaluation, _, candidate = package_setup
    evaluation["context"]["host"] = "unavailable-remote-test-host"
    evaluation["build"]["binary"] = "/nonexistent-bfs-coverage-artifact/binary"
    records.write("evaluations/package-evaluation.yaml", evaluation)
    report = _report(records, tmp_path)
    artifact = next(a for row in report["unassigned_evaluations"] for a in row["artifacts"]
                    if a["path"] == evaluation["build"]["binary"])
    assert artifact["state"] == "remote_unverified"
    assert report["external_verification_complete"] is False


@pytest.mark.parametrize('fault', ['a3-underflow', 'miscopied'])
def test_historical_sealed_package_with_invalid_counts_is_rejected_without_erasing_it(package_setup, tmp_path, fault):
    from test_profile_packages import _assemble, _callgrind_profile
    records, request, evaluation, profile, _ = package_setup
    package = _assemble(records, tmp_path, request)
    _callgrind_profile(profile, tmp_path, 'a3-underflow' if fault == 'a3-underflow' else None)
    if fault == 'miscopied': profile['dynamic_memory'][0]['value'] = 201
    records.write('region_profiles/package-diagnostics.yaml', profile)
    # Represent a historical package whose old assembler accepted these counts.
    # Its seal is correct; only the newly enforced observation semantics reject it.
    package['completeness'] = 'complete'
    package['evidence']['classification'] = 'execution'
    package['dynamic_memory'] = copy.deepcopy(profile['dynamic_memory'])
    package['evidence']['region_profile_sha256'] = artifacts.digest(profile)
    package.pop('identity_sha256')
    package['id'] = package['requested_id']
    package['identity_sha256'] = artifacts.digest(package)
    package['id'] = f"{package['requested_id']}.v{package['package_version']}.{package['identity_sha256'][:16]}"
    profile_package.verify(package)
    records.write(f"profile_packages/{package['id']}.yaml", package)
    report = _report(records, tmp_path)
    observed = next(row for row in report['unassigned_evaluations'] if row['evaluation'] == evaluation['id'])
    rejected = next(row for row in observed['rejected_packages'] if row['id'] == package['id'])
    assert any('Callgrind execution' in reason and ('inconsistent' in reason or 'raw validation failed' in reason)
               for reason in rejected['reasons'])
    assert not report['profiling_demonstrations'] and report['criteria']['AC04']['state'] == 'incomplete'
    retained = records.swdb('get', package['id'], '--format', 'json')
    assert retained.returncode == 0 and json.loads(retained.stdout) == package


@pytest.mark.parametrize("field", ["request", "workload", "check"])
def test_malformed_retained_failure_evidence_does_not_hide_history(package_setup, tmp_path, field):
    records, _, evaluation, _, _ = package_setup
    if field == "request": evaluation["request"] = ["invalid request retained for diagnosis"]
    elif field == "workload": evaluation["context"]["workload"] = "unavailable"
    else: evaluation["correctness"]["checks"] = [{"passed": True, "binding": None}]
    records.write("evaluations/package-evaluation.yaml", evaluation)
    report = _report(records, tmp_path)
    assert report["acceptance"] == "incomplete" and not report["gain_claim"]
    retained = next(row for row in report["history"]["evaluation"] if row["id"] == evaluation["id"])
    assert retained["request"] == evaluation["request"]
    assert any(row["evaluation"] == evaluation["id"] and not row["qualified"] for row in report["unassigned_evaluations"])

"""The public acceptance report over the actual retained records. Created 2026-09-27 ET.

These tests read the repository's real T18/T19 native evidence through the
public `bfs-coverage` and `handoff-message` commands. Raw artifacts stay on
mbit10, so on any other host the paired receipts are checked from record
bindings only and must be reported as `remote_unverified`, never as verified.
"""

import json
import shutil
import socket
import subprocess
import sys

import pytest
import yaml

from conftest import REPO, run_swdb

NATIVE_PROTOCOLS = ["bfs-native-one-thread-dx100-scalar-20260927.0d2d6da657751ff3",
                    "bfs-native-one-thread-upstream-do-20260927.9d4b53fd41e79297"]
T18_KRONECKER = "bfs-native-acceptance-20260927-dx100-patch-b2.kronecker.candidate-1"
NATIVE_CELLS = {"dx100-bfs-scalar/supplied_code/patch/kronecker", "dx100-bfs-scalar/supplied_code/patch/uniform_random",
                "gapbs-bfs-do/instruction/structured_instructions/kronecker",
                "gapbs-bfs-do/instruction/structured_instructions/uniform_random"}

OFF_COLLECTING_HOST = pytest.mark.skipif(socket.gethostname().split(".")[0] == "mbit10",
                                         reason="asserts the remote_unverified classification used off the collecting host")


def _copy(tmp_path):
    shutil.copytree(REPO / "records", tmp_path / "records")
    return tmp_path / "records"


def _report(records, tmp_path, name="report"):
    request = tmp_path / f"{name}.json"
    request.write_text(json.dumps({"message_version": "1.0", "id": name, "candidate_protocols": NATIVE_PROTOCOLS,
                                   "artifact_reference_comparisons": [], "controlled_reference_comparisons": []}))
    done = run_swdb("bfs-coverage", request, "--records", records, "--db", tmp_path / f"{name}.sqlite", "--format", "json")
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


@pytest.fixture(scope="module")
def actual(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("acceptance")
    records = _copy(tmp_path)
    return records, _report(records, tmp_path)


@OFF_COLLECTING_HOST
def test_native_cells_report_real_ids_outcomes_and_unverified_raw_evidence(actual):
    _, report = actual
    cells = {row["cell"]: row for row in report["accounting"]["cells"]}
    assert set(cells) == {f"{c['starting_implementation']}/{c['route']}/{c['payload']}/{c['graph_family']}"
                          for c in report["matrix"]} and len(cells) == 8
    for name in NATIVE_CELLS:
        row = cells[name]
        assert row["state"] == "satisfied_by_retained_metadata"
        assert row["workflow_case"] == "completed" and row["evidence_package"] == "complete"
        assert row["accelerator_use"] == "not_required"
        assert row["comparison_outcome"] == "inconclusive"
        assert row["raw_verification"] == "remote_unverified"
    matrix = {f"{c['starting_implementation']}/{c['route']}/{c['payload']}/{c['graph_family']}": c for c in report["matrix"]}
    kronecker = matrix["dx100-bfs-scalar/supplied_code/patch/kronecker"]["summary"]
    assert kronecker["completed_evaluations"] == [T18_KRONECKER + ".evaluation"]
    assert [row["id"] for row in kronecker["comparisons"]] == [T18_KRONECKER + ".comparison"]
    assert kronecker["comparisons"][0]["protocol"] == NATIVE_PROTOCOLS[0]
    # A qualified inconclusive comparison is never a gain, and nothing is externally verified here.
    assert report["gain_gate"]["state"] == "incomplete" and report["gain_gate"]["qualifying_gains"] == []
    assert {row["decision"] for row in report["gain_gate"]["observed_outcomes"]} == {"inconclusive"}
    assert report["gain_claim"] is False and report["acceptance"] == "incomplete"
    assert report["external_verification_complete"] is False


def test_accelerated_cells_stay_missing_and_failures_stay_visible(actual):
    _, report = actual
    cells = {row["cell"]: row for row in report["accounting"]["cells"]}
    for name, row in cells.items():
        if name in NATIVE_CELLS:
            continue
        assert row["state"] == "incomplete" and row["accelerator_use"] == "missing"
        assert row["comparison_outcome"] == "missing" and row["raw_verification"] == "missing"
    assert set(report["gain_gate"]["cells_without_outcome"]) == set(cells) - NATIVE_CELLS
    failures = report["accounting"]["retained_failures"]
    proposals = {row["id"]: row["state"] for row in failures["proposals"]}
    for n in range(2, 6):
        assert proposals[f"bfs-campaign-preparation-20260925-a1.upstream-annotated-context{n}"] == "failed"
    evaluations = {row["id"]: row["state"] for row in failures["evaluations"]}
    assert evaluations["bfs-native-acceptance-20260927-dx100-patch-b1.uniform-random.candidate-1.evaluation"] == "interrupted"
    uniform = next(c for c in report["matrix"] if c["route"] == "supplied_code"
                   and c["starting_implementation"] == "dx100-bfs-scalar" and c["graph_family"] == "uniform_random")
    assert any(row.get("state") == "interrupted" for row in uniform["summary"]["retained_failures"])
    annotated = next(c for c in report["matrix"] if c["payload"] == "annotated_source" and c["graph_family"] == "kronecker")
    assert {row["id"] for row in annotated["proposals"]} >= {
        f"bfs-campaign-preparation-20260925-a1.upstream-annotated-context{n}" for n in range(1, 7)}
    missing = report["accounting"]["missing"]
    assert "accelerated minimum for dx100-bfs-scalar" in missing and "accelerated minimum for gapbs-bfs-do" in missing
    assert report["criteria"]["AC17"]["state"] == "incomplete" and report["criteria"]["AC18"]["state"] == "incomplete"
    assert set(NATIVE_PROTOCOLS).isdisjoint(report["selection_audit"]["unselected_protocols"])


def test_changed_retained_timing_disqualifies_the_comparison_and_is_not_neutral(tmp_path):
    records = _copy(tmp_path)
    path = records / "evaluations" / f"{T18_KRONECKER}.evaluation.yaml"
    data = yaml.safe_load(path.read_text())
    data["timing"][0]["duration_s"] = data["timing"][0]["duration_s"] * 0.5
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    report = _report(records, tmp_path, "tampered")
    comparison = next(row for row in report["comparison_assessments"] if row["id"] == T18_KRONECKER + ".comparison")
    assert comparison["qualified"] is False and comparison["reasons"]
    cells = {row["cell"]: row for row in report["accounting"]["cells"]}
    kronecker = cells["dx100-bfs-scalar/supplied_code/patch/kronecker"]
    assert kronecker["state"] == "incomplete" and kronecker["comparison_outcome"] == "missing"
    matrix = next(c for c in report["matrix"] if c["route"] == "supplied_code"
                  and c["starting_implementation"] == "dx100-bfs-scalar" and c["graph_family"] == "kronecker")
    assert matrix["summary"]["comparisons"] == []


@pytest.mark.parametrize("message,record,expected", [
    ("evaluation_result", T18_KRONECKER + ".evaluation", "completed_evaluation"),
    ("evaluation_result", "bfs-native-acceptance-20260927-dx100-patch-b1.uniform-random.candidate-1.evaluation",
     "incomplete_evaluation"),
])
def test_evaluation_message_separates_completed_and_incomplete_without_claims(actual, tmp_path, message, record, expected):
    records, _ = actual
    done = run_swdb("handoff-message", message, record, "--records", records, "--db", tmp_path / "m.sqlite", "--format", "json")
    assert done.returncode == 0, done.stderr
    body = json.loads(done.stdout)
    assert body["format"] == "swdb.bfs.handoff.evaluation_result" and body["format_version"] == "1.0"
    assert body["provenance"]["test_client"] is True and body["provenance"]["live_collaborator_integration"] is False
    assert body["content"]["result_class"] == expected and body["content"]["performance_claim"] == "none"
    assert all(ref["state"] == "present" for ref in body["inputs"])


def test_proposal_message_retains_provider_capture_and_edit_format(actual, tmp_path):
    records, _ = actual
    done = run_swdb("handoff-message", "rewrite_proposal", "bfs-campaign-preparation-20260925-a1.upstream-annotated-context6",
                    "--records", records, "--db", tmp_path / "m.sqlite", "--format", "json")
    assert done.returncode == 0, done.stderr
    body = json.loads(done.stdout)
    handling = body["content"]["handling"]
    assert handling["provider"]["output_format"] == "stream-json" and handling["provider"]["edit_format"] == "full_files"
    assert handling["interpretation"]["changed_files"] == ["src/bfs.cc"]
    assert body["content"]["producer"]["role"] == "hw" and body["provenance"]["test_client"] is True
    assert body["content"]["payload"]["kind"] == "annotated_source" and body["content"]["payload"]["sha256"]


def test_checked_in_handoff_examples_are_current():
    done = subprocess.run([sys.executable, "scripts/bfs_handoff_examples.py", "--check"],
                          cwd=REPO, capture_output=True, text=True, timeout=900)
    assert done.returncode == 0, done.stderr


def test_committed_final_report_request_pins_the_current_contract_document():
    from swdb import artifacts
    request = json.loads((REPO / ".scratch/bfs-rewrite-evaluation-2026-09-25/requests/"
                          "acceptance-report-20260927-e1.json").read_text())
    handoff = request["handoff"]
    assert handoff["live_collaborator_integration"] is False
    assert handoff["contracts"] == {"profile_package": "1.0", "rewrite_proposal": "1.0", "evaluation_result": "1.0"}
    assert artifacts.file_hash(REPO / handoff["path"]) == handoff["sha256"]

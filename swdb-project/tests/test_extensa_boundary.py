"""Extensa mode tags, team-boundary refusals and candidate promotion (ticket 48).

Created: 2026-10-03 ET. Fixture records only (evidence_kind contract_fixture); no
record here is execution evidence. Updated 2026-10-05 ET (spec review C1, C3, C9, C18): who
performed a review, promotion evidence of the current contract content, levels from the newest
command version, no promotion from a superseded team protocol.
"""

import copy
import json

import pytest
import yaml

from conftest import REPO, run_swdb
from testkit.bfs_protocol import _command, _payload

CAMPAIGN = "extensa-native-bfs-20261004-a1"
CANDIDATE = "test-proposal.candidate-1"
KRON = "inputs/kron-g16-k16.yaml"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def _tag(records, rel, campaign=CAMPAIGN):
    """Simulate a record that an Extensa campaign created with its tags."""
    data = records.read(rel)
    data.update(mode="extensa", campaign=campaign)
    records.write(rel, data)
    return data


# --- schema and writer ------------------------------------------------------------

@pytest.mark.parametrize("tags, ok, field", [
    ({"mode": "extensa", "campaign": CAMPAIGN}, True, None),
    ({"mode": "extensa"}, False, "campaign"),
    ({"campaign": CAMPAIGN}, False, "mode"),
    ({"mode": "archevolve", "campaign": CAMPAIGN}, False, "mode"),
    ({"mode": "extensa", "campaign": "extensa-cpu-bfs-20261004-a1"}, False, "campaign"),
])
def test_every_record_kind_accepts_only_paired_extensa_tags(repo, tags, ok, field):
    data = repo.read(KRON)
    data.update(tags)
    repo.write(KRON, data)
    result = repo.validate()
    assert (result.returncode == 0) is ok, result.stderr
    if not ok:
        assert KRON in result.stderr and field in result.stderr


def test_repository_records_revalidate_unchanged():
    result = run_swdb("validate")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("change", ["add", "change", "remove"])
def test_writer_refuses_rewriting_mode_or_campaign(repo, change):
    from swdb import writer
    from swdb.cli import Failure
    data = repo.read(KRON)
    if change != "add":
        data.update(mode="extensa", campaign=CAMPAIGN)
        repo.write(KRON, data)
    before = (repo.path / KRON).read_text()
    rewritten = copy.deepcopy(data)
    if change == "add":
        rewritten.update(mode="extensa", campaign=CAMPAIGN)
    elif change == "change":
        rewritten["campaign"] = "extensa-native-bfs-20261004-a2"
    else:
        rewritten.pop("mode"); rewritten.pop("campaign")
    with pytest.raises(Failure, match="set only when a record is created"):
        writer.commit(repo.path, replace=[rewritten])
    assert (repo.path / KRON).read_text() == before
    # An unrelated rewrite that keeps the tags is still allowed.
    same = copy.deepcopy(data)
    same["notes"] = ["unrelated note"]
    writer.commit(repo.path, replace=[same])


def test_candidate_schema_refuses_a_stored_certification_level(protocol_setup):
    records, *_ = protocol_setup
    data = records.read(f"candidates/{CANDIDATE}.yaml")
    data["certification_level"] = "certified"
    records.write(f"candidates/{CANDIDATE}.yaml", data)
    result = records.validate()
    assert result.returncode == 1 and "certification_level" in result.stderr


# --- derived certification level ---------------------------------------------------

def _current(contract="contract.bfs_read_offload"):
    from swdb.library import Library
    return Library(REPO / "library").content_sha256(contract)


def _certification(records, tmp_path, rid, verdict, candidate=CANDIDATE, version="1.5", content=None):
    """A fixture certification; by default of the contract's current content under a named command."""
    data = records.read(f"candidates/{candidate}.yaml")
    passed = verdict == "certified"
    content = content or _current()
    record = {"kind": "certification", "schema_version": "0.4", "id": rid, "status": "draft",
              "created": "2026-10-03", "updated": "2026-10-03",
              "provenance": [{"id": "fixture", "kind": "agent_run", "description": "Contract fixture.", "uri": None}],
              "entry": {"id": "contract.bfs_read_offload", "content_sha256": content},
              "candidate": {"id": candidate, "contract": "contract.bfs_read_offload", "contract_sha256": content,
                            "tree_sha256": data["artifact"]["sha256"]},
              "command": {"version": version}, "host": {"hostname": "fixture"},
              "matrix": [{"cell": "fixture", "status": "passed" if passed else "failed"}],
              "negative_controls": [{"id": "fixture", "status": "rejected"}],
              "verdict": verdict, "evidence_basis": "simulated", "evidence_kind": "contract_fixture"}
    result = records.swdb("add", _payload(tmp_path, rid, record))
    assert result.returncode == 0, result.stderr
    return record


def _level(records):
    result = records.swdb("candidate-level", CANDIDATE, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_level_derives_from_certification_records_only(protocol_setup, tmp_path):
    records, *_ = protocol_setup
    assert _level(records)["level"] == "uncertified"
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    assert _level(records)["level"] == "certified"
    _certification(records, tmp_path, "certification.fixture-fail", "failed")     # same command version
    level = _level(records)
    assert level["level"] == "rejected"
    assert level["certifications"] == ["certification.fixture-fail", "certification.fixture-pass"]
    assert "certification_level" not in records.read(f"candidates/{CANDIDATE}.yaml")


# --- team boundary and promotion, end to end -------------------------------------

def _tag_candidate(records):
    candidate = _tag(records, f"candidates/{CANDIDATE}.yaml")
    _tag(records, f"proposals/{candidate['proposal']}.yaml")
    return candidate


def test_unpromoted_extensa_records_are_refused_by_every_team_command(protocol_setup, tmp_path):
    records, _, protocol, _, evaluations, comparison = protocol_setup
    _tag_candidate(records)
    refused = _command(records, "compare-evaluations", _payload(tmp_path, "compare", comparison), succeeds=False)
    assert refused["decision"]["state"] == "rejected"
    assert f"Extensa record" in refused["decision"]["reasons"][0]
    assert CAMPAIGN in refused["decision"]["reasons"][0]
    handoff = records.swdb("handoff-message", "evaluation_result", evaluations["candidate"]["id"], "--format", "json")
    assert handoff.returncode == 1 and "not promoted" in handoff.stderr and "Extensa record" in handoff.stderr
    proposal = records.read(f"candidates/{CANDIDATE}.yaml")["proposal"]
    handoff = records.swdb("handoff-message", "rewrite_proposal", proposal, "--format", "json")
    assert handoff.returncode == 1 and proposal in handoff.stderr
    request = {"message_version": "1.0", "id": "coverage", "candidate_protocols": [protocol["id"]],
               "artifact_reference_comparisons": [], "controlled_reference_comparisons": [refused["id"]]}
    coverage = records.swdb("bfs-coverage", _payload(tmp_path, "coverage", request), "--format", "json")
    assert coverage.returncode == 1 and "Extensa record" in coverage.stderr
    request["controlled_reference_comparisons"] = []
    coverage = records.swdb("bfs-coverage", _payload(tmp_path, "coverage-scan", request), "--format", "json")
    assert coverage.returncode == 0, coverage.stderr
    report = json.loads(coverage.stdout)
    listed = json.dumps(report)
    assert evaluations["candidate"]["id"] not in listed      # skipped, not counted
    assert evaluations["baseline"]["id"] in listed or report["acceptance"] == "incomplete"


def test_extensa_tagged_evaluations_never_enter_team_results(protocol_setup, tmp_path):
    records, _, _, _, evaluations, _ = protocol_setup
    rel = next(p.relative_to(records.path).as_posix() for p in records.path.glob("evaluations/*.yaml")
               if records.read(p.relative_to(records.path).as_posix())["id"] == evaluations["baseline"]["id"])
    _tag(records, rel)
    handoff = records.swdb("handoff-message", "evaluation_result", evaluations["baseline"]["id"], "--format", "json")
    assert handoff.returncode == 1 and "never enter team results" in handoff.stderr
    assert evaluations["baseline"]["id"] in handoff.stderr


def test_promotion_derives_a_class_protocol_and_unblocks_only_after_reevaluation(protocol_setup, tmp_path):
    records, workload, protocol, _, evaluations, comparison = protocol_setup
    _tag_candidate(records)
    out = tmp_path / "reeval"
    # A promotion needs evidence and a class the team protocol holds.
    missing = records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "contract_fixture",
                           "--output", out, "--library", REPO / "library", "--format", "json")
    assert missing.returncode == 1 and "certification record or its campaign summary" in missing.stderr
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    wrong = records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "kronecker",
                         "--output", out, "--library", REPO / "library", "--format", "json")
    assert wrong.returncode == 1 and "no workload of class" in wrong.stderr
    stranger = records.swdb("promote", CANDIDATE, "--reviewer", "Someone Else", "--protocol", protocol["id"],
                            "--workload-class", "contract_fixture", "--output", out, "--format", "json")
    assert stranger.returncode == 1 and "Yan-Ru Jhou" in stranger.stderr

    promoted = records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "contract_fixture",
                            "--output", out, "--library", REPO / "library", "--format", "json")
    assert promoted.returncode == 0, promoted.stderr
    result = json.loads(promoted.stdout)
    review = result["review"]
    assert review["target_kind"] == "candidate" and review["reviewer"] == "Yan-Ru Jhou"
    assert review["origin"] == {"mode": "extensa", "campaign": CAMPAIGN}
    assert review["evidence"] == ["certification.fixture-pass"]
    derived = json.loads(records.swdb("get", result["derived_protocol"], "--format", "json").stdout)
    assert derived["settings"]["workloads"] == [workload["id"]] and "mode" not in derived
    assert any(CANDIDATE in text for text in derived["settings"]["differences"]["software"])
    (request_row,) = result["requests"]
    request = yaml.safe_load(open(request_row["path"]))
    assert request["origin"]["campaign"] == CAMPAIGN and request["origin"]["review"] == review["id"]
    assert request["protocol"] == derived["id"] and request["candidate"] == CANDIDATE

    # Promoted, but no re-evaluation comparison yet: team commands still refuse.
    comparison.update(id="compare-old-protocol")
    refused = _command(records, "compare-evaluations", _payload(tmp_path, "old", comparison), succeeds=False)
    assert "does not exist yet" in refused["decision"]["reasons"][0]
    handoff = records.swdb("handoff-message", "evaluation_result", evaluations["candidate"]["id"], "--format", "json")
    assert handoff.returncode == 1 and "does not exist yet" in handoff.stderr

    # The re-evaluation under the derived team protocol, through the public evaluator.
    produced = {}
    for role in ("baseline", "candidate"):
        base = copy.deepcopy(evaluations[role]["request"])
        base.update(id=f"reeval-{role}", protocol=derived["id"], protocol_role=role)
        if role == "candidate":
            base.update({k: v for k, v in request.items() if k != "id"})
        result_eval = records.swdb("evaluate", _payload(tmp_path, f"reeval-{role}", base), "--runs-dir",
                                   tmp_path / "runs", "--format", "json",
                                   env={"SWDB_PROTOCOL_DURATION": "0.05" if role == "baseline" else "0.025"})
        assert result_eval.returncode == 0, result_eval.stderr + result_eval.stdout
        produced[role] = json.loads(result_eval.stdout)
    assert "mode" not in produced["candidate"]
    reeval = {**comparison, "id": "compare-reevaluation", "protocol": derived["id"],
              "baseline_evaluation": produced["baseline"]["id"], "candidate_evaluation": produced["candidate"]["id"]}
    accepted = _command(records, "compare-evaluations", _payload(tmp_path, "reeval-compare", reeval))
    assert accepted["decision"]["state"] == "fixture_comparison"
    handoff = records.swdb("handoff-message", "evaluation_result", produced["candidate"]["id"], "--format", "json")
    assert handoff.returncode == 0, handoff.stderr


def test_rejected_candidate_artifact_is_never_promoted(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    _tag_candidate(records)
    _certification(records, tmp_path, "certification.fixture-fail", "failed")
    result = records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "contract_fixture",
                          "--output", tmp_path / "out", "--library", REPO / "library", "--format", "json")
    assert result.returncode == 1 and "never promoted" in result.stderr


def test_archevolve_candidate_needs_no_promotion(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    result = records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "contract_fixture",
                          "--output", tmp_path / "out", "--format", "json")
    assert result.returncode == 1 and "not an Extensa candidate" in result.stderr


# --- spec review C9: the level counts the newest command for the current content ------------

class _Rows:
    def __init__(self, records):
        self.id, self.data, self.kind = records["id"], records, records["kind"]


class _Store:
    """A minimal store (no library beside it) for level derivation."""

    def __init__(self, rows, folder):
        self.rows, self.dir = [_Rows(r) for r in rows], folder

    def get(self, rid, kind=None):
        return next((r.data for r in self.rows if r.id == rid and (kind is None or r.kind == kind)), None)

    def of_kind(self, kind):
        return [r for r in self.rows if r.kind == kind]


def _a7_rejudged():
    path = REPO / ".scratch/typed-library-dx100-bfs-2026-10-03/evaluation/a7-forged-frontier-v2-rejudge-2026-10-04.json"
    return json.loads(path.read_text())["rejudged"]


def _bound(rid, candidate, tree, contract_sha, version, verdict):
    return {"kind": "certification", "id": rid, "verdict": verdict, "command": {"version": version},
            "entry": {"id": "contract.bfs_read_offload", "content_sha256": contract_sha},
            "candidate": {"id": candidate, "contract": "contract.bfs_read_offload", "contract_sha256": contract_sha,
                          "tree_sha256": tree}}


@pytest.mark.parametrize("row", _a7_rejudged(), ids=lambda row: row["candidate"].split(".", 1)[1])
def test_a7_candidates_failed_under_v1_derive_certified_under_v2(row, tmp_path):
    """Spec review C9 (2026-10-05 ET): the six a7 candidates failed certify 1.0 (forged_frontier v1 survived)
    and certified under 1.1 (ticket 67). The level follows the newest command version."""
    from swdb import extensa_boundary
    assert row["a7_verdict"] == "failed" and row["mac_verdict"] == "certified" and row["command_version"] == "1.1"
    candidate = {"kind": "candidate", "id": row["candidate"], "artifact": {"sha256": row["tree_sha256"]},
                 "mode": "extensa", "campaign": "extensa-gem5-bfs-20261004-a7"}
    old = _bound(row["a7_certification"], row["candidate"], row["tree_sha256"], row["contract_sha256"], "1.0", "failed")
    new = _bound(row["mac_certification"], row["candidate"], row["tree_sha256"], row["contract_sha256"], "1.1",
                 "certified")
    store = _Store([candidate, old], tmp_path)
    assert extensa_boundary.certification_level(store, row["candidate"])["level"] == "rejected"
    store = _Store([candidate, old, new], tmp_path)
    level = extensa_boundary.certification_level(store, row["candidate"])
    assert level["level"] == "certified" and level["counted"] == [row["mac_certification"]]
    # A newer command that fails again derives `rejected`.
    newer = _bound("certification.newer", row["candidate"], row["tree_sha256"], row["contract_sha256"], "1.5", "failed")
    assert extensa_boundary.certification_level(_Store([candidate, old, new, newer], tmp_path),
                                                row["candidate"])["level"] == "rejected"


def test_certifications_of_superseded_contract_content_do_not_count(tmp_path):
    from swdb import extensa_boundary
    from swdb.library import Library
    library = Library(REPO / "library")
    candidate = {"kind": "candidate", "id": "cand", "artifact": {"sha256": "1" * 64}, "mode": "extensa",
                 "campaign": "extensa-gem5-bfs-20261004-a7"}
    stale = _bound("certification.stale", "cand", "1" * 64, "b" * 64, "1.5", "failed")
    level = extensa_boundary.certification_level(_Store([candidate, stale], tmp_path), "cand", library)
    assert level["level"] == "uncertified" and level["stale"] == ["certification.stale"]
    current = _bound("certification.current", "cand", "1" * 64, _current(), "1.4", "certified")
    level = extensa_boundary.certification_level(_Store([candidate, stale, current], tmp_path), "cand", library)
    assert level["level"] == "certified" and level["counted"] == ["certification.current"]


# --- spec review C1, C3, C18: promotion -------------------------------------------------------

AGENT = ["--performed-by", "agent", "--delegated-by", "Yan-Ru Jhou", "--delegation",
         "Yan-Ru Jhou's 2026-10-05 delegation (fixture)", "--review-document", "docs/review-fixture.md"]


def _promote(records, protocol, out, *extra):
    return records.swdb("promote", CANDIDATE, "--protocol", protocol["id"], "--workload-class", "contract_fixture",
                        "--output", out, "--library", REPO / "library", "--format", "json", *extra)


def test_agent_review_is_recorded_as_agent_work_and_corrections_fix_old_attributions(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    _tag_candidate(records)
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    incomplete = _promote(records, protocol, tmp_path / "a", "--performed-by", "agent")
    assert incomplete.returncode == 2 and "delegated_by" in incomplete.stderr
    human = json.loads(_promote(records, protocol, tmp_path / "h").stdout)["review"]
    assert "performed_by" not in human and human["provenance"][0]["kind"] == "human_report"
    agent = _promote(records, protocol, tmp_path / "g", *AGENT)
    assert agent.returncode == 0, agent.stderr
    review = json.loads(agent.stdout)["review"]
    assert review["performed_by"] == "agent" and review["delegated_by"] == "Yan-Ru Jhou"
    assert review["provenance"][0]["kind"] == "agent_run" and review["reviewer"] == "Yan-Ru Jhou"
    level = json.loads(records.swdb("candidate-level", CANDIDATE, "--format", "json").stdout)
    assert level["promotion"]["review"] == review["id"]
    assert level["promotion"]["attribution"]["performed_by"] == "agent"

    # The human-attributed review, corrected: it stays unchanged and readers report the correction.
    rel = f"reviews/{human['id']}.yaml"
    before = (records.path / rel).read_bytes()
    corrected = records.swdb("correct-review", human["id"], "--recorded-by", "fixture agent", "--reason",
                             "performed by an agent", *AGENT, "--format", "json")
    assert corrected.returncode == 0, corrected.stderr
    correction = json.loads(corrected.stdout)
    assert (records.path / rel).read_bytes() == before
    assert correction["target_kind"] == "review" and correction["evidence"] == [human["id"]]
    from swdb.library import review_attribution
    from swdb.store import Store
    store = Store(records.path)
    assert review_attribution(store, store.get(human["id"]))["corrected_by"] == correction["id"]
    assert records.validate().returncode == 0

    # An agent review that calls itself a human report, or a correction pinning other content, is invalid.
    forged = {**records.read(f"reviews/{review['id']}.yaml")}
    forged["provenance"] = [{**forged["provenance"][0], "kind": "human_report"}]
    records.write(f"reviews/{review['id']}.yaml", forged)
    result = records.validate()
    assert result.returncode == 1 and "not a human_report" in result.stderr


def test_promotion_needs_a_certification_of_the_current_contract_content(protocol_setup, tmp_path):
    records, _, protocol, *_ = protocol_setup
    _tag_candidate(records)
    _certification(records, tmp_path, "certification.fixture-old", "certified", content="c" * 64)
    stale = _promote(records, protocol, tmp_path / "s")
    assert stale.returncode == 1 and "current content" in stale.stderr
    _certification(records, tmp_path, "certification.fixture-unnamed", "certified", version="fixture")
    unnamed = _promote(records, protocol, tmp_path / "u")
    assert unnamed.returncode == 1 and "named" in unnamed.stderr
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    first = json.loads(_promote(records, protocol, tmp_path / "p").stdout)
    assert first["review"]["evidence"] == ["certification.fixture-pass"]
    # Promoting again from the same team protocol reuses the derived protocol and the written requests.
    again = _promote(records, protocol, tmp_path / "q", *AGENT)
    assert again.returncode == 0, again.stderr
    second = json.loads(again.stdout)
    assert second["derived_protocol"] == first["derived_protocol"]
    assert [r["id"] for r in second["requests"]] == [r["id"] for r in first["requests"]]
    assert second["requests"][0]["reused_from"] == first["review"]["id"]


def test_promotion_refuses_a_superseded_team_protocol(protocol_setup, tmp_path):
    records, _, protocol, protocol_request, *_ = protocol_setup
    _tag_candidate(records)
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    successor = _command(records, "freeze-protocol", _payload(tmp_path, "successor", {
        **protocol_request, "version": 2, "supersedes": protocol["id"]}))
    refused = _promote(records, protocol, tmp_path / "old")
    assert refused.returncode == 1 and "superseded by" in refused.stderr and successor["id"] in refused.stderr
    assert _promote(records, successor, tmp_path / "new").returncode == 0


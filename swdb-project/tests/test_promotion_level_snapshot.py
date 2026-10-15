"""Promotion pins the level; a later drop shows (Probata proof of concept ticket 12).

Created: 2026-10-14 ET. Seams 2 and 4 of the formal-verification map's spec: `swdb promote`,
`swdb candidate-level`, `swdb validate` and `swdb build` (26 item 11). Fixture records only
(evidence_kind contract_fixture); no verifier runs. The Extensa candidate artifact, its team protocol
and certification come from ticket 48's promotion fixture (test_extensa_boundary); its proof record is
written by `swdb prove` and then pinned to a proof-semantics version, as a record made while that
version was current would be.
"""

import hashlib
import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO
from test_extensa_boundary import CANDIDATE, _certification, _tag_candidate
from test_proof_records import _library_roots
from testkit.record_subset import copy_record_subset

ONE = {"threads": 1, "vertices": 3, "edges": 3}
ASSUMPTION = {"kind": "trusted_tool", "reference": {"id": "clang-22.1.8", "sha256": "a" * 64},
              "sentence": "clang 22.1.8 compiles the proof unit correctly."}


@pytest.fixture
def promotable(protocol_setup, tmp_path):
    """A certified Extensa candidate artifact with one proven record (threads = 1) pinning proof semantics v1."""
    records, _workload, protocol, *_ = protocol_setup
    _tag_candidate(records)
    library = records.path.parent / "library"
    copy_record_subset(REPO / "records", records.path, sorted(_library_roots()))     # the library's roots
    shutil.copytree(REPO / "library", library)
    (library / "methods").mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", library / "methods")
    _certification(records, tmp_path, "certification.fixture-pass", "certified")
    case = Case(records, protocol, tmp_path)
    case.proof_id = case.prove(proof_semantics=case.semantics("v1", 1))
    return case


class Case:
    def __init__(self, records, protocol, root):
        self.records, self.protocol, self.root = records, protocol, root
        self.library = records.path.parent / "library"

    def swdb(self, *args):
        return self.records.swdb(*args)

    def semantics(self, name, sequence):
        """A proof-semantics version file in library/proof_semantics/ (ticket 27 writes the real ones).

        Since ticket 20 the folder holds typed-library entries of kind proof_semantics (ID prefix `semantics.`,
        formal_frame, version, rules; no `status`); the level rule's version line still reads `target` and
        `sequence` (the same fixture form as tests/test_level_rule.py since 9280a24c)."""
        folder = self.library / "proof_semantics"
        folder.mkdir(exist_ok=True)
        path = folder / f"{name}.yaml"
        ident = f"semantics.{name}"
        path.write_text(yaml.safe_dump({
            "id": ident, "kind": "proof_semantics", "formal_frame": 1, "version": f"{sequence}.0",
            "target": "dx100", "sequence": sequence,
            "provenance": {"origin": {"intrinsic_specification": "fixture-12"}}, "clauses": [],
            "rules": [{"id": "wait", "statement": f"Fixture proof-semantics version {name}: a read waits for its command.",
                       "assumed": {"owner": "fixture"}}]}, sort_keys=False))
        return {"id": ident, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def prove(self, candidate=CANDIDATE, **pins):
        script = self.root / "script.yaml"
        script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": ONE, "assumptions": [ASSUMPTION]}))
        result = self.swdb("prove", "--candidate", candidate, "--function", "DOBFS", "--adapter", "scripted",
                           "--script", script, "--runs-dir", self.root / "runs-outside-repo",
                           "--contract", "contract.bfs_read_offload", "--format", "json")
        assert result.returncode == 0, result.stderr
        written = json.loads(result.stdout)
        if pins:
            record = written["record"]
            record["pins"].update(pins)
            self.write("proofs", record)
        return written["record"]["id"]

    def write(self, folder, record):
        (self.records.path / folder / f"{record['id']}.yaml").write_text(yaml.safe_dump(record, sort_keys=False))

    def promote(self):
        result = self.swdb("promote", CANDIDATE, "--protocol", self.protocol["id"], "--workload-class",
                           "contract_fixture", "--output", self.root / "reeval", "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)["review"]

    def level(self):
        result = self.swdb("candidate-level", CANDIDATE, "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def review_path(self, review):
        return self.records.path / "reviews" / f"{review['id']}.yaml"


def test_promote_cites_the_counting_proof_records_and_the_level_snapshot(promotable):
    assert promotable.level()["level"] == "proven_within_bounds_threads_1"
    review = promotable.promote()
    assert review["proof_records"] == [promotable.proof_id]
    snapshot = review["level_snapshot"]
    assert snapshot["level"] == "proven_within_bounds_threads_1"
    assert snapshot["level_rule"] == "level-rule.2"
    assert snapshot["records"] == [promotable.proof_id]
    assert snapshot["at"].endswith(" ET") and len(snapshot["at"]) == len("2026-10-14 02:36 ET")
    assert promotable.swdb("validate").returncode == 0


def test_a_later_drop_shows_beside_the_approved_snapshot(promotable):
    review = promotable.promote()
    promotable.semantics("v2", 2)              # a new proof-semantics version lands; the record pins v1
    level = promotable.level()
    assert level["level"] == "certified"
    promotion = level["promotion"]
    assert promotion["review"] == review["id"]
    assert promotion["level_snapshot"] == {"level": "proven_within_bounds_threads_1",
                                           "at": review["level_snapshot"]["at"], "level_rule": "level-rule.2",
                                           "records": [promotable.proof_id]}
    assert promotion["proof_records"] == [promotable.proof_id]
    assert promotion["dropped"] is True


def test_no_drop_while_the_level_holds(promotable):
    promotable.promote()
    assert promotable.level()["promotion"]["dropped"] is False


def _rewrite(case, review, change):
    path = case.review_path(review)
    data = yaml.safe_load(path.read_text())
    change(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _fails(case, *words):
    result = case.swdb("validate")
    assert result.returncode == 1, result.stdout
    for word in words:
        assert word in result.stderr, result.stderr


def test_a_snapshot_without_its_level_rule_version_fails_validation(promotable):
    review = promotable.promote()
    _rewrite(promotable, review, lambda d: d["level_snapshot"].pop("level_rule"))
    _fails(promotable, "level_snapshot", "level_rule")


def test_a_review_citing_a_proof_record_about_another_candidate_fails_validation(promotable):
    review = promotable.promote()
    other = yaml.safe_load((promotable.records.path / "candidates" / f"{CANDIDATE}.yaml").read_text())
    other["id"] = "test-proposal.candidate-2"
    promotable.write("candidates", other)
    record = yaml.safe_load((promotable.records.path / "proofs" / f"{promotable.proof_id}.yaml").read_text())
    record.update(id="proof.t12.other-candidate")
    record["subject"]["candidate"] = other["id"]
    promotable.write("proofs", record)
    assert promotable.swdb("validate").returncode == 0
    _rewrite(promotable, review, lambda d: d["proof_records"].append(record["id"]))
    _fails(promotable, "proof_records", "test-proposal.candidate-2")
    _rewrite(promotable, review, lambda d: (d["proof_records"].pop(), d["level_snapshot"]["records"].append(record["id"])))
    _fails(promotable, "level_snapshot", "test-proposal.candidate-2")


def test_a_snapshot_without_its_proof_records_fails_validation(promotable):
    review = promotable.promote()
    _rewrite(promotable, review, lambda d: d.pop("proof_records"))
    _fails(promotable, "proof_records")


def test_a_candidate_review_written_before_ticket_12_still_validates_and_builds(promotable):
    review = promotable.promote()
    _rewrite(promotable, review, lambda d: (d.pop("proof_records"), d.pop("level_snapshot")))
    assert promotable.swdb("validate").returncode == 0
    assert promotable.swdb("build").returncode == 0
    assert "level_snapshot" not in promotable.level()["promotion"]


def _hashes(case):
    folders = [case.records.path / "proofs", case.records.path / "proposals"]
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for folder in folders for p in sorted(folder.glob("*.yaml"))}


def test_candidate_level_build_and_promotion_leave_proof_records_and_proposals_byte_identical(promotable):
    before = _hashes(promotable)
    assert len([p for p in before if p.parent.name == "proofs"]) == 1 and len(before) > 1
    promotable.level()
    assert promotable.swdb("build").returncode == 0
    promotable.promote()
    promotable.level()
    assert promotable.swdb("build").returncode == 0
    assert _hashes(promotable) == before

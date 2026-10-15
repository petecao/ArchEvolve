"""The level rule: `swdb candidate-level` computes a candidate artifact's full certification level on read.

Created: 2026-10-14 ET (Probata proof of concept ticket 10). Seam 2 of the formal-verification map's
spec (`swdb candidate-level`, existing, extended) and seam 4 (`swdb validate`, `swdb build`). Fixture
certification and proof records only (evidence_kind contract_fixture); no verifier runs. The certified
fixture candidate artifact comes from ticket 04's seed (record closure of its roots, LR-03); proof
records are written as fixture YAML from the record `swdb prove` writes, so each test sets exactly the
pins, subjects and verdicts it needs. Expected levels are hand-derived from the ticket's acceptance.
"""

import copy
import json
import re
import shutil

import pytest
import yaml

from conftest import run_swdb
from test_proof_records import CONTRACT, proof_seed  # noqa: F401  (the certified fixture candidate)

UNBOUNDED = "unbounded"
TOP = {"threads": UNBOUNDED, "vertices": UNBOUNDED, "edges": UNBOUNDED}
ONE = {"threads": 1, "vertices": 3, "edges": 3}
K = {"threads": 3, "vertices": 3, "edges": 3}
CLANG = {"kind": "trusted_tool", "reference": {"id": "clang-22.1.8", "sha256": "a" * 64},
         "sentence": "clang 22.1.8 compiles the proof unit correctly."}
RANK = ["uncertified", "certified", "proven_within_bounds_threads_1", "proven_within_bounds_threads_k",
        "proven_unbounded"]


@pytest.fixture(scope="module")
def template(proof_seed, tmp_path_factory):
    """One record written by `swdb prove` on the seed: the shape every fixture record starts from."""
    source, candidate = proof_seed
    root = tmp_path_factory.mktemp("level-template")
    for name in ("records", "library"):
        shutil.copytree(source / name, root / name)
    script = root / "script.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": ONE, "assumptions": [CLANG]}))
    result = run_swdb("prove", "--records", root / "records", "--candidate", candidate, "--function", "DOBFS",
                      "--adapter", "scripted", "--script", script, "--runs-dir", root / "runs", "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["record"]


@pytest.fixture
def seed(proof_seed, template, tmp_path):
    source, candidate = proof_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidate, template)


class Seed:
    def __init__(self, root, candidate, template):
        self.root, self.candidate, self.template = root, candidate, template
        self.records = root / "records"
        self.library = root / "library"

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args)

    def proof(self, rid, *, verdict="proven", bounds=None, subject=None, pins=None, assumptions=None, **extra):
        """Write a fixture proof record `proof.t10.<rid>` and return its ID.

        `pins` updates the template's pins (a record made when that pin's hash was different);
        `subject` replaces the candidate proof unit; `extra` adds top-level fields."""
        record = copy.deepcopy(self.template)
        record["id"] = f"proof.t10.{rid}"
        record["verdict"] = verdict
        record["bounds"] = dict(bounds or ONE)
        record["assumptions"] = list(assumptions if assumptions is not None else [CLANG])
        record["pins"].update(copy.deepcopy(pins or {}))
        if subject is not None:
            record["subject"] = subject
        record["job"] = dict(record["job"], batch=f"batch.{record['id']}")
        record.update(extra)
        (self.records / "proofs").mkdir(exist_ok=True)
        (self.records / "proofs" / f"{record['id']}.yaml").write_text(yaml.safe_dump(record, sort_keys=False))
        return record["id"]

    def certify(self, rid, contract=CONTRACT, verdict="certified"):
        _certify_contract(self, rid, contract, verdict)

    def level(self):
        result = self.swdb("candidate-level", self.candidate, "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def files(self):
        return {p: p.read_bytes() for p in sorted(self.records.rglob("*.yaml"))}

    def validate(self):
        return self.swdb("validate")


def _certify_contract(seed, rid, contract, verdict, candidate=None):
    """A fixture certification of `contract`'s current content (ticket 04's helper, any contract)."""
    from conftest import REPO
    from swdb.library import Library
    from testkit.bfs_protocol import _payload
    candidate = candidate or seed.candidate
    data = yaml.safe_load((seed.records / "candidates" / f"{candidate}.yaml").read_text())
    content = Library(REPO / "library").content_sha256(contract)
    passed = verdict == "certified"
    record = {"kind": "certification", "schema_version": "0.4", "id": rid, "status": "draft",
              "created": "2026-10-14", "updated": "2026-10-14",
              "provenance": [{"id": "fixture", "kind": "agent_run", "description": "Contract fixture.", "uri": None}],
              "entry": {"id": contract, "content_sha256": content},
              "candidate": {"id": candidate, "contract": contract, "contract_sha256": content,
                            "tree_sha256": data["artifact"]["sha256"]},
              "command": {"version": "1.7"}, "host": {"hostname": "fixture"},
              "matrix": [{"cell": "fixture", "status": "passed" if passed else "failed"}],
              "negative_controls": [{"id": "fixture", "status": "rejected"}],
              "verdict": verdict, "evidence_basis": "simulated", "evidence_kind": "contract_fixture"}
    result = run_swdb("add", "--records", seed.records, "--db", seed.root / "build" / "swdb.sqlite",
                      _payload(seed.root, rid, record))
    assert result.returncode == 0, result.stderr


# --- order ----------------------------------------------------------------------------------

@pytest.mark.parametrize("bounds, expected", [
    (TOP, "proven_unbounded"),
    (K, "proven_within_bounds_threads_k"),
    (ONE, "proven_within_bounds_threads_1"),
    (None, "certified"),
])
def test_each_level_in_rank_order(seed, bounds, expected):
    if bounds is not None:
        seed.proof("one", bounds=bounds)
    level = seed.level()
    assert level["level"] == expected
    assert level["rank"] == RANK.index(expected)
    assert level["level_rule"] == "level-rule.2"


def test_uncertified_ranks_lowest(seed):
    (seed.records / "certifications" / "certification.proof-fixture-pass.yaml").unlink()
    seed.proof("one", bounds=TOP)
    level = seed.level()
    assert level["level"] == "uncertified" and level["rank"] == 0


def test_counting_records_at_both_bounded_sub_rungs_read_threads_k(seed):
    seed.proof("one", bounds=ONE)
    seed.proof("k", bounds=K)
    assert seed.level()["level"] == "proven_within_bounds_threads_k"


def test_unbounded_data_at_one_thread_is_never_proven_unbounded(seed):
    seed.proof("one", bounds={"threads": 1, "vertices": UNBOUNDED, "edges": UNBOUNDED})
    assert seed.level()["level"] == "proven_within_bounds_threads_1"


def test_bounds_above_the_minimum_are_reported_never_ranked(seed):
    seed.proof("a", bounds={"threads": 1, "vertices": 3, "edges": 3})
    seed.proof("b", bounds={"threads": 1, "vertices": 5, "edges": 9})
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_1"
    assert {r["record"]: r["bounds"] for r in level["proof_units"][0]["records"]} == {
        "proof.t10.a": {"threads": 1, "vertices": 3, "edges": 3},
        "proof.t10.b": {"threads": 1, "vertices": 5, "edges": 9}}


# --- pins -------------------------------------------------------------------------------------

ENTRY = "intrinsic.dxc_alu_scalar"          # any library entry: a summary's entry, a reference definition
SECOND_ENTRY = "operation.gather_staging_executor"
PREDECESSOR = "test-proposal.predecessor"
STALE = "0" * 64
NA = {"not_applicable": "This fixture part does not use it."}


def _sha(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stale(pin):
    return dict(pin, sha256=STALE)


def _entry(seed, ident=ENTRY):
    from swdb.library import Library
    return {"id": ident, "sha256": Library(seed.library).content_sha256(ident)}


def _contract(seed):
    return _entry(seed, CONTRACT)


def record_pin(seed, rid):
    """The pin of a proof record (a minimum-bounds derivation): its ID and content digest."""
    from swdb import artifacts
    return {"id": rid, "sha256": artifacts.digest(yaml.safe_load((seed.records / "proofs" / f"{rid}.yaml").read_text()))}


def proof_semantics(seed, name, sequence, target="dx100"):
    """A proof-semantics version file in library/proof_semantics/ (ticket 27 writes the real ones).

    Since ticket 20 the folder holds typed-library entries of kind proof_semantics (ID prefix
    `semantics.`, formal_frame, version, rules; no `status`), so the fixture is one such entry. The
    level rule's version line still reads `target` and `sequence`."""
    folder = seed.library / "proof_semantics"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}.yaml"
    ident = f"semantics.{name}"
    path.write_text(yaml.safe_dump({
        "id": ident, "kind": "proof_semantics", "formal_frame": 1, "version": f"{sequence}.0",
        "target": target, "sequence": sequence,
        "provenance": {"origin": {"intrinsic_specification": "fixture-10"}}, "clauses": [],
        "rules": [{"id": "wait", "statement": f"Fixture proof-semantics version {name}: a read waits for its command.",
                   "assumed": {"owner": "fixture"}}]}, sort_keys=False))
    return {"id": ident, "sha256": _sha(path)}


def method_version(seed, name, sequence, status="frozen"):
    source = seed.library / "methods" / "contract-fixture-1.yaml"
    data = yaml.safe_load(source.read_text())
    data.update(id=f"method.{name}", sequence=sequence, status=status)
    path = seed.library / "methods" / f"{name}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return {"id": f"method.{name}", "sha256": _sha(path)}


def summary(seed, rid="summary", bounds=TOP, entry=ENTRY, pins=None, **extra):
    """A library summary proof record; returns the summaries pin a candidate proof record holds for it."""
    sid = seed.proof(rid, bounds=bounds, subject={"kind": "library_summary", "id": entry},
                     pins={"code": _entry(seed, entry), "contract": NA, "baseline_function": NA, **(pins or {})},
                     **extra)
    return {**_entry(seed, entry), "proof_record": sid}


def contract_part(seed, rid, part, bounds=TOP, verdict="proven", pins=None, **extra):
    """A contract-proof part record of CONTRACT's current content."""
    return seed.proof(rid, bounds=bounds, verdict=verdict,
                      subject={"kind": "contract_proof_part", "id": CONTRACT, "part": part},
                      pins={"code": _contract(seed), "baseline_function": NA, **(pins or {})}, **extra)


def minimum(seed, rid="minimum", bounds=ONE, pins=None):
    """A minimum-bounds derivation record; returns the minimum_bounds pin that names it."""
    return record_pin(seed, contract_part(seed, rid, "minimum_bounds_derivation", bounds=bounds, pins=pins))


def predecessor(seed, bounds=ONE):
    """A certified predecessor candidate artifact with one counting proof record; its snapshot pin."""
    text = (seed.records / "candidates" / f"{seed.candidate}.yaml").read_text()
    (seed.records / "candidates" / f"{PREDECESSOR}.yaml").write_text(
        text.replace(f"id: {seed.candidate}", f"id: {PREDECESSOR}"))
    _certify_contract(seed, "certification.t10-predecessor", CONTRACT, "certified", candidate=PREDECESSOR)
    pin = {"id": PREDECESSOR, "sha256": yaml.safe_load(text)["artifact"]["sha256"]}
    seed.proof("predecessor", bounds=bounds, pins={"code": pin},
               subject={"kind": "candidate_proof_unit", "candidate": PREDECESSOR, "function": "DOBFS"})
    return pin


def _pin_case(seed, case):
    """(pins of a counting record, the pins that differ in the same record made before `case` changed)."""
    pins = seed.template["pins"]
    if case in {"code", "contract", "baseline_function"}:
        return {}, {case: _stale(pins[case])}
    if case == "reference_semantics":
        return {case: _entry(seed)}, {case: _stale(_entry(seed))}
    if case == "proof_semantics":                       # v2 lands; the old record pins v1
        old = proof_semantics(seed, "v1", 1)
        return {case: proof_semantics(seed, "v2", 2)}, {case: old}
    if case == "method_version":                        # method version 2 lands; the old record pins 1
        return {case: method_version(seed, "contract-fixture-2", 2)}, {case: pins[case]}
    if case == "summary_entry":
        pin = summary(seed)
        return {"summaries": [pin]}, {"summaries": [_stale(pin)]}
    if case == "summary_record":                        # the summary's own proof stopped counting
        pin = summary(seed)
        return {"summaries": [pin]}, {"summaries": [summary(seed, "summary-old", pins={"code": _stale(_entry(seed))})]}
    if case == "minimum_bounds":
        pin = minimum(seed)
        return {case: pin}, {case: _stale(pin)}
    if case == "predecessor_snapshot":
        pin = predecessor(seed)
        return {case: pin}, {case: _stale(pin)}
    if case == "build_constant":                        # the derivation it pins ran at TILE_SIZE 2
        pin = minimum(seed, pins={"build_constants": [{"name": "TILE_SIZE", "value": 2}]})
        return ({"minimum_bounds": pin, "build_constants": [{"name": "TILE_SIZE", "value": 2}]},
                {"build_constants": [{"name": "TILE_SIZE", "value": 4}]})
    raise AssertionError(case)


PIN_CASES = {"code": "code", "contract": "contract", "baseline_function": "baseline_function",
             "reference_semantics": "reference_semantics", "proof_semantics": "proof_semantics",
             "method_version": "method_version", "summary_entry": "summaries", "summary_record": "summaries",
             "minimum_bounds": "minimum_bounds", "predecessor_snapshot": "predecessor_snapshot",
             "build_constant": "build_constants"}


@pytest.mark.parametrize("case", sorted(PIN_CASES))
def test_a_changed_pin_stops_the_record_counting_and_names_the_pin(seed, case):
    good, changed = _pin_case(seed, case)
    seed.proof("remaining", bounds=ONE, pins=good)
    seed.proof("changed", bounds=TOP, pins={**good, **changed})
    validated = seed.validate()
    assert validated.returncode == 0, validated.stderr
    before = seed.files()
    level = seed.level()
    assert seed.files() == before                          # nothing is written or rewritten
    assert level["level"] == "proven_within_bounds_threads_1"   # what the remaining record gives
    stale = {s["record"]: s["pins"] for s in level["stale_proofs"]}
    assert "proof.t10.remaining" not in stale
    assert PIN_CASES[case] in {p["pin"] for p in stale["proof.t10.changed"]}, stale


@pytest.mark.parametrize("case", sorted(PIN_CASES))
def test_with_no_counting_record_left_the_candidate_reads_certified(seed, case):
    good, changed = _pin_case(seed, case)
    seed.proof("changed", bounds=TOP, pins={**good, **changed})
    level = seed.level()
    assert level["level"] == "certified" and level["proven"] is None
    assert "proof.t10.changed" in {s["record"] for s in level["stale_proofs"]}


# --- two routes, one proof unit; weakest of across proof units (S11) --------------------------

def test_two_routes_in_one_proof_unit_read_the_higher_level_after_caps(seed):
    pin = predecessor(seed, bounds=ONE)
    seed.proof("route-3", bounds=TOP, route="route_3", pins={"predecessor_snapshot": pin})
    seed.proof("route-1", bounds=TOP, route="route_1")
    level = seed.level()
    assert level["level"] == "proven_unbounded"
    assert [r["record"] for r in level["proof_units"][0]["records"]] == ["proof.t10.route-1"]


def test_control_without_the_route_1_record_the_unit_reads_its_capped_route_3_level(seed):
    pin = predecessor(seed, bounds=ONE)
    seed.proof("route-3", bounds=TOP, route="route_3", pins={"predecessor_snapshot": pin})
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_1"
    unit = level["proof_units"][0]["records"][0]
    assert unit["record"] == "proof.t10.route-3" and unit["bounds"] == ONE
    assert [c.get("candidate") for c in unit["caps"]] == [PREDECESSOR]


SECOND = "contract.bc_read_offload"


def test_across_proof_units_the_weakest_wins_and_each_dimension_shows_its_smallest_bound(seed):
    seed.certify("certification.t10-second", SECOND)
    seed.proof("first", bounds=TOP)
    seed.proof("second", bounds={"threads": 1, "vertices": 4, "edges": UNBOUNDED}, pins={"contract": _entry(seed, SECOND)})
    level = seed.level()
    assert {u["contract"]: u["level"] for u in level["proof_units"]} == {
        CONTRACT: "proven_unbounded", SECOND: "proven_within_bounds_threads_1"}
    assert level["level"] == "proven_within_bounds_threads_1"
    assert level["proven"]["bounds"] == {"threads": 1, "vertices": 4, "edges": UNBOUNDED}


def test_a_proof_unit_with_no_counting_record_reads_certified_and_so_does_the_candidate(seed):
    seed.certify("certification.t10-second", SECOND)
    seed.proof("first", bounds=TOP)
    level = seed.level()
    assert level["level"] == "certified"
    assert {u["contract"]: u["level"] for u in level["proof_units"]} == {CONTRACT: "proven_unbounded",
                                                                          SECOND: "certified"}


# --- cap rule ---------------------------------------------------------------------------------

def test_a_summary_proven_within_bounds_caps_and_is_named(seed):
    pin = summary(seed, bounds={"threads": UNBOUNDED, "lanes": 2})
    seed.proof("unit", bounds=TOP, pins={"summaries": [pin]})
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_k"
    assert level["proven"]["bounds"] == {"threads": UNBOUNDED, "vertices": UNBOUNDED, "edges": UNBOUNDED, "lanes": 2}
    caps = level["proof_units"][0]["records"][0]["caps"]
    assert [(c["kind"], c["record"]) for c in caps] == [("summary", pin["proof_record"])]


@pytest.mark.parametrize("part", ["unit_postcondition", "lifting_lemma", "negative_controls"])
def test_a_contract_proof_part_proven_within_bounds_caps(seed, part):
    rid = contract_part(seed, "part", part, bounds=ONE)
    seed.proof("unit", bounds=TOP)
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_1"
    assert [(c["kind"], c["record"]) for c in level["proof_units"][0]["records"][0]["caps"]] == [
        ("contract_proof_part", rid)]


def test_the_minimum_bounds_derivation_caps_the_records_that_pin_it(seed):
    pin = minimum(seed, bounds=ONE)
    seed.proof("unit", bounds=TOP, pins={"minimum_bounds": pin})
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_1"
    assert [(c["kind"], c["record"]) for c in level["proof_units"][0]["records"][0]["caps"]] == [
        ("minimum_bounds", pin["id"])]


def test_within_one_contract_proof_part_the_highest_record_counts(seed):
    contract_part(seed, "post-bounded", "unit_postcondition", bounds=ONE)
    contract_part(seed, "post-unbounded", "unit_postcondition", bounds=TOP)
    seed.proof("unit", bounds=TOP)
    assert seed.level()["level"] == "proven_unbounded"


def test_an_unproven_contract_proof_part_never_caps(seed):
    contract_part(seed, "post", "unit_postcondition", verdict="not_proven", failure_class="timeout")
    seed.proof("unit", bounds=TOP)
    assert seed.level()["level"] == "proven_unbounded"


def test_when_a_dependency_stops_counting_its_dependents_stop_too(seed):
    old = summary(seed, "summary-old", pins={"code": _stale(_entry(seed))})
    seed.proof("unit", bounds=TOP, pins={"summaries": [old]})
    deeper = seed.proof("over-summary", bounds=TOP, subject={"kind": "library_summary", "id": SECOND_ENTRY},
                        pins={"code": _entry(seed, SECOND_ENTRY), "contract": NA, "baseline_function": NA,
                              "summaries": [old]})
    seed.proof("unit-2", bounds=TOP, pins={"summaries": [{**_entry(seed, SECOND_ENTRY), "proof_record": deeper}]})
    level = seed.level()
    assert level["level"] == "certified"
    stale = {s["record"]: s["pins"] for s in level["stale_proofs"]}
    assert {p.get("dependency") for p in stale["proof.t10.unit"]} == {old["proof_record"]}
    assert {p.get("dependency") for p in stale["proof.t10.unit-2"]} == {deeper}     # transitively


def test_a_contract_proof_part_that_stopped_counting_stops_its_dependents(seed):
    contract_part(seed, "post", "unit_postcondition", pins={"baseline_function": _stale(seed.template["pins"]["baseline_function"])})
    seed.proof("unit", bounds=TOP)
    level = seed.level()
    assert level["level"] == "certified"
    assert level["stale_proofs"][0]["pins"][0]["pin"] == "contract"


def test_a_negative_control_that_proves_voids_the_contract_proof(seed):
    contract_part(seed, "post", "unit_postcondition", bounds=TOP)
    failed = contract_part(seed, "controls", "negative_controls", verdict="refuted",
                           counterexample={"control": "dropped_wait", "expected": "refuted", "got": "proven"})
    seed.proof("unit", bounds=TOP)
    before = seed.files()
    level = seed.level()
    assert seed.files() == before
    assert level["level"] == "certified"
    pins = {s["record"]: s["pins"] for s in level["stale_proofs"]}["proof.t10.unit"]
    assert any(p.get("failed") == failed and p["pin"] == "contract" for p in pins), pins


# --- part names are one list (vocabulary proof_part_names) ------------------------------------------

def test_the_part_vocabulary_holds_every_part_the_level_rule_reads_with_its_subject_kind_and_void():
    from swdb import paths, vocab
    vocabs, problems = vocab.load_all(paths.VOCAB)
    assert not problems
    entries = vocabs.entries["proof_part_names"]
    read = {"negative_controls": ("contract_proof_part", "contract"),
            "minimum_bounds_derivation": ("contract_proof_part", "none"),
            "semantics_controls": ("method_part", "proof_semantics"),
            "concurrency_controls": ("method_part", "method_version"),
            "civl_genmc_agreement": ("method_part", "method_version")}
    for name, (kind, voids) in read.items():
        assert (entries[name]["subject_kind"], entries[name]["voids"]) == (kind, voids)
    assert {"unit_postcondition", "lifting_lemma", "composition_theorem"} <= set(entries)


@pytest.mark.parametrize("subject, reason", [
    ({"kind": "contract_proof_part", "id": CONTRACT, "part": "negative_control"}, "proof_part_names"),
    ({"kind": "method_part", "id": "method.contract-fixture-1", "part": "made_up_check"}, "proof_part_names"),
    ({"kind": "contract_proof_part", "id": CONTRACT, "part": "semantics_controls"}, "method_part"),
    ({"kind": "method_part", "id": "method.contract-fixture-1", "part": "negative_controls"}, "contract_proof_part"),
])
def test_validate_refuses_an_unlisted_part_name_or_one_of_another_subject_kind(seed, subject, reason):
    seed.proof("part", subject=subject, pins={"code": NA, "baseline_function": NA})
    result = seed.validate()
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if "proof.t10.part" in line and "subject.part" in line]
    assert problem and reason in problem[0], result.stderr


@pytest.mark.parametrize("subject", [
    {"kind": "contract_proof_part", "id": CONTRACT, "part": "lifting_lemma"},
    {"kind": "method_part", "id": "method.contract-fixture-1", "part": "concurrency_controls"},
])
def test_control_validate_accepts_a_listed_part_of_its_subject_kind(seed, subject):
    seed.proof("part", subject=subject, pins={"code": NA, "baseline_function": NA})
    result = seed.validate()
    assert result.returncode == 0, result.stderr


# --- failed method parts void their version ------------------------------------------------------

WRONG = {"control": "fixture-control", "expected": "refuted", "got": "proven"}


def method_part(seed, rid, ident, part, pins):
    return seed.proof(rid, verdict="refuted", counterexample=WRONG,
                      subject={"kind": "method_part", "id": ident, "part": part},
                      pins={"code": NA, "contract": NA, "baseline_function": NA, **pins})


@pytest.mark.parametrize("part, kind", [
    ("semantics_controls", "proof_semantics"),
    ("concurrency_controls", "method_version"),
    ("civl_genmc_agreement", "method_version"),          # a CIVL-GenMC contradiction
])
def test_a_failed_method_part_voids_the_current_version_it_tests(seed, part, kind):
    version = proof_semantics(seed, "v1", 1) if kind == "proof_semantics" else seed.template["pins"]["method_version"]
    failed = method_part(seed, "failed", version["id"], part, {kind: version})
    seed.proof("unit", bounds=TOP, pins={kind: version})
    dependent = summary(seed, pins={kind: version})       # a summary that pins it stops counting too,
    seed.proof("via-summary", bounds=TOP, pins={kind: NA, "summaries": [dependent]})   # and so its users
    before = seed.files()
    level = seed.level()
    assert seed.files() == before
    assert level["level"] == "certified"
    pins = {s["record"]: s["pins"] for s in level["stale_proofs"]}["proof.t10.unit"]
    assert [(p["pin"], p.get("failed")) for p in pins] == [(kind, failed)]
    pins = {s["record"]: s["pins"] for s in level["stale_proofs"]}["proof.t10.via-summary"]
    assert [(p["pin"], p.get("dependency")) for p in pins] == [("summaries", dependent["proof_record"])]


def test_control_a_record_that_pins_another_proof_semantics_version_keeps_counting(seed):
    voided = proof_semantics(seed, "v1", 1, target="dx100")
    other = proof_semantics(seed, "other-1", 1, target="other-accelerator")
    method_part(seed, "failed", voided["id"], "semantics_controls", {"proof_semantics": voided})
    seed.proof("unit", bounds=TOP, pins={"proof_semantics": other})
    assert seed.level()["level"] == "proven_unbounded"


def test_control_a_failed_check_of_an_older_method_version_leaves_the_current_one(seed):
    old = seed.template["pins"]["method_version"]
    current = method_version(seed, "contract-fixture-2", 2)
    method_part(seed, "failed", old["id"], "concurrency_controls", {"method_version": old})
    seed.proof("unit", bounds=TOP, pins={"method_version": current})
    assert seed.level()["level"] == "proven_unbounded"


# --- draft method versions (fix-21, 2026-10-14): used only when named; never supersede ------------

def test_a_record_under_a_draft_newer_than_the_current_frozen_version_counts(seed):
    draft = method_version(seed, "contract-fixture-2", 2, status="draft")
    seed.proof("unit", bounds=TOP, pins={"method_version": draft})
    assert seed.level()["level"] == "proven_unbounded"


def test_control_a_newer_draft_never_stops_a_record_under_the_current_frozen_version(seed):
    method_version(seed, "contract-fixture-2", 2, status="draft")
    seed.proof("unit", bounds=TOP)                               # pins frozen contract-fixture-1
    assert seed.level()["level"] == "proven_unbounded"


def test_a_record_under_a_draft_that_a_frozen_version_superseded_stops_counting(seed):
    draft = method_version(seed, "contract-fixture-2", 2, status="draft")
    method_version(seed, "contract-fixture-3", 3)                # the freeze: a new frozen file, sequence 3
    seed.proof("unit", bounds=TOP, pins={"method_version": draft})
    level = seed.level()
    assert level["level"] == "certified"
    assert [p["pin"] for p in level["stale_proofs"][0]["pins"]] == ["method_version"]


# --- assumption entries never cap; verifiers and solvers are entries (S14) ----------------------

def _assume(kind, ident, sentence):
    return {"kind": kind, "reference": {"id": ident, "sha256": "b" * 64}, "sentence": sentence}


SEVEN = [
    _assume("assumed_clause", "contract.bfs_read_offload#L3", "No other thread writes the frontier during the call."),
    _assume("proof_semantics", "semantics.v1", "DX100 follows its proof semantics v1."),
    _assume("summary", "intrinsic.dxc_gather", "dxc_gather meets its summary, not proven in this job."),
    _assume("reduction", "lemma.dx100-reduction", "Finish-at-issue values plus hazard freedom match the hardware."),
    _assume("trusted_tool", "frama-c-wp-33.0", "Frama-C/WP 33.0 reports goals correctly."),
    _assume("written_proof", "theorem.parallel-composition", "The parallel composition theorem holds."),
    _assume("written_proof", "lemma.lifting.bfs_read_offload.bfs", "The lifting lemma carries the unit to the kernel."),
    _assume("platform_choice", "platform.float-as-reals", "Floats are modeled as reals."),
]


def test_assumption_entries_of_all_seven_kinds_never_cap_and_are_listed(seed):
    seed.proof("unit", bounds=TOP, assumptions=SEVEN)
    level = seed.level()
    assert level["level"] == "proven_unbounded"
    assert {k["kind"] for k in SEVEN} == {"assumed_clause", "proof_semantics", "summary", "reduction",
                                          "trusted_tool", "written_proof", "platform_choice"}
    listed = [{k: a[k] for k in ("kind", "reference", "sentence")} for a in level["assumptions"]]
    assert listed == SEVEN
    assert all(a["records"] == ["proof.t10.unit"] for a in level["assumptions"])


def test_the_assumption_set_holds_the_entries_of_the_dependencies_too(seed):
    pin = summary(seed, assumptions=[_assume("trusted_tool", "saw-1.6", "SAW 1.6 reports correctly.")])
    seed.proof("unit", bounds=TOP, pins={"summaries": [pin]})
    level = seed.level()
    assert {(a["reference"]["id"], tuple(a["records"])) for a in level["assumptions"]} == {
        ("clang-22.1.8", ("proof.t10.unit",)), ("saw-1.6", (pin["proof_record"],))}


WP, Z3 = "frama-c-wp-33.0", "z3-4.8.14"


def test_validate_accepts_a_record_whose_tools_are_each_a_trusted_tool_entry(seed):
    seed.proof("unit", bounds=TOP, tools=[WP, Z3],
               assumptions=[CLANG, _assume("trusted_tool", WP, "WP is trusted."), _assume("trusted_tool", Z3, "Z3 is trusted.")])
    result = seed.validate()
    assert result.returncode == 0, result.stderr


def test_validate_refuses_a_record_whose_assumption_set_omits_its_verifier_naming_the_tool(seed):
    seed.proof("unit", bounds=TOP, tools=[WP, Z3], assumptions=[CLANG, _assume("trusted_tool", Z3, "Z3 is trusted.")])
    result = seed.validate()
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if "proof.t10.unit" in line and "tools" in line]
    assert problem and WP in problem[0] and "trusted-tool" in problem[0], result.stderr


def test_prove_writes_the_tools_its_adapter_reports(seed):
    script = seed.root / "script-tools.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": TOP, "tools": [WP],
                                      "assumptions": [_assume("trusted_tool", WP, "WP is trusted.")]}))
    result = seed.swdb("prove", "--candidate", seed.candidate, "--function", "DOBFS", "--adapter", "scripted",
                       "--script", script, "--runs-dir", seed.root / "runs", "--format", "json")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["record"]["tools"] == [WP]
    assert seed.validate().returncode == 0


# --- proven requires certified (O1) --------------------------------------------------------------

def test_code_that_applies_no_contract_keeps_its_certification_level_with_the_direct_proof_beside_it(seed):
    (seed.records / "certifications" / "certification.proof-fixture-pass.yaml").unlink()
    seed.proof("direct", bounds=TOP, route="route_1", pins={"contract": NA})
    level = seed.level()
    assert level["level"] == level["certification_level"] == "uncertified" and level["proven"] is None
    assert level["direct_proofs"] == [{"record": "proof.t10.direct",
                                       "text": "direct proof, no matching contract: proven unbounded"}]


def test_control_a_proof_of_code_certified_only_at_another_content_hash_gives_no_proven_level(seed):
    path = seed.records / "certifications" / "certification.proof-fixture-pass.yaml"
    data = yaml.safe_load(path.read_text())
    data["candidate"]["tree_sha256"] = "c" * 64          # certified at another content hash
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    seed.proof("unit", bounds=TOP)
    level = seed.level()
    assert level["level"] == "uncertified" and level["proven"] is None


def test_control_the_same_proof_of_a_certified_candidate_that_applies_the_contract_reads_proven(seed):
    seed.proof("unit", bounds=TOP, route="route_1")
    level = seed.level()
    assert level["level"] == "proven_unbounded" and level["direct_proofs"] == []


# --- below minimum bounds ---------------------------------------------------------------------------

MIN = {"threads": 1, "lanes": 2, "chunk": 2, "frontier": 2, "vertices": 3, "edges": 3}


def test_a_bounded_record_below_its_pinned_minimum_in_any_dimension_gives_no_level(seed):
    pin = minimum(seed, bounds=MIN)
    seed.proof("unit", bounds=dict(MIN, lanes=1), pins={"minimum_bounds": pin})
    level = seed.level()
    assert level["level"] == "certified"
    assert level["below_minimum"] == [{"record": "proof.t10.unit", "text": "bounded check below minimum",
                                       "dimensions": ["lanes"]}]


def test_a_record_with_failure_class_below_minimum_bounds_says_so(seed):
    seed.proof("unit", verdict="not_proven", failure_class="below_minimum_bounds", bounds=ONE)
    level = seed.level()
    assert level["level"] == "certified"
    assert level["below_minimum"] == [{"record": "proof.t10.unit", "text": "bounded check below minimum",
                                       "dimensions": []}]


def test_control_the_same_record_at_exactly_the_minimum_reads_its_sub_rung(seed):
    pin = minimum(seed, bounds=MIN)
    seed.proof("unit", bounds=MIN, pins={"minimum_bounds": pin})
    level = seed.level()
    assert level["level"] == "proven_within_bounds_threads_1" and level["below_minimum"] == []


# --- skips (O7) --------------------------------------------------------------------------------------

def _skip(seed, rid, reason="no_contract_proof"):
    record = copy.deepcopy(seed.template)
    for name in ("verdict", "bounds", "assumptions", "evidence"):
        record.pop(name, None)
    record.update(id=f"proof.t10.{rid}", skip_reason=reason)
    (seed.records / "proofs").mkdir(exist_ok=True)
    (seed.records / "proofs" / f"{record['id']}.yaml").write_text(yaml.safe_dump(record, sort_keys=False))
    return record["id"]


def test_a_skip_sets_no_level_and_blocks_none(seed):
    skip = _skip(seed, "skip")
    seed.proof("wp", bounds=TOP, route="route_1")
    assert seed.validate().returncode == 0
    level = seed.level()
    assert level["level"] == "proven_unbounded"
    assert level["skipped"] == [{"record": skip, "skip_reason": "no_contract_proof"}]


def test_control_the_skip_record_alone_leaves_the_proof_unit_certified(seed):
    _skip(seed, "skip")
    level = seed.level()
    assert level["level"] == "certified" and level["proof_units"][0]["level"] == "certified"
    assert level["stale_proofs"] == []


# --- replay-label field (owned here) ---------------------------------------------------------------

LABELS = ["reproduced", "proof_semantics_only", "not_reproduced", "undefined_behavior"]
COUNTEREXAMPLE = {"inputs": {"vertices": 3, "edges": [[0, 1], [1, 2]], "source": 0},
                  "violated": "parent[2] differs from the reference"}


def refuted(seed, rid, label=None, **extra):
    fields = {"replay_label": label} if label else {}
    return seed.proof(rid, verdict="refuted", counterexample=COUNTEREXAMPLE, **fields, **extra)


@pytest.mark.parametrize("label", [None, *LABELS])
def test_validate_accepts_a_refuted_record_with_no_label_or_each_label(seed, label):
    refuted(seed, "refuted", label)
    result = seed.validate()
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("write, reason", [
    (lambda seed: refuted(seed, "refuted", "replayed_somehow"), "reproduced"),
    (lambda seed: seed.proof("refuted", replay_label="reproduced"), "only a refuted record"),
    (lambda seed: seed.proof("refuted", verdict="not_proven", failure_class="timeout", replay_label="not_reproduced"),
     "only a refuted record"),
])
def test_validate_refuses_another_value_or_a_label_on_a_record_that_is_not_refuted(seed, write, reason):
    write(seed)
    result = seed.validate()
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if "proof.t10.refuted" in line and "replay_label" in line]
    assert problem and reason in problem[0], result.stderr


def test_build_loads_the_label_with_the_record(seed):
    import sqlite3
    refuted(seed, "labeled", "undefined_behavior")
    refuted(seed, "unlabeled")
    result = seed.swdb("build")
    assert result.returncode == 0, result.stderr
    con = sqlite3.connect(f"file:{seed.root / 'build' / 'swdb.sqlite'}?mode=ro", uri=True)
    try:
        rows = dict(con.execute("SELECT id, replay_label FROM swdb_proofs WHERE id LIKE 'proof.t10.%'"))
    finally:
        con.close()
    assert rows == {"proof.t10.labeled": "undefined_behavior", "proof.t10.unlabeled": None}


# --- refuted -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("label", [*LABELS, None])
def test_a_counting_refuted_record_blocks_every_proven_level_and_sets_the_flag(seed, label):
    seed.proof("proven", bounds=TOP)
    rid = refuted(seed, "refuted", label)
    level = seed.level()
    assert level["level"] == "certified" and level["proven"] is None
    assert level["refuted"]["flag"] is True
    assert level["refuted"]["records"] == [{"record": rid, "replay_label": label}]
    assert level["refuted"]["evidence"] == "unit-level refutation"


def test_control_when_the_refuted_record_stops_counting_the_flag_clears(seed):
    old = proof_semantics(seed, "v1", 1)
    refuted(seed, "refuted", "proof_semantics_only", pins={"proof_semantics": old})
    current = proof_semantics(seed, "v2", 2)                 # a new proof-semantics version lands (13 item 10)
    seed.proof("proven", bounds=TOP, pins={"proof_semantics": current})
    level = seed.level()
    assert level["refuted"]["flag"] is False and level["refuted"]["records"] == []
    assert level["level"] == "proven_unbounded"


def test_no_refuted_record_no_flag(seed):
    seed.proof("proven", bounds=TOP)
    assert seed.level()["refuted"] == {"flag": False, "records": [], "evidence": None, "reproductions": []}


# --- bug ------------------------------------------------------------------------------------------------

def reproduction(seed, rid, cites, **pins):
    return seed.proof(rid, verdict="refuted", counterexample={"input": "graph.fixture", "schedule": None},
                      subject={"kind": "kernel_reproduction", "id": cites}, pins=pins)


def test_a_refutation_reads_bug_only_while_a_counting_reproduction_cites_it(seed):
    rid = refuted(seed, "refuted", "reproduced")
    assert seed.level()["refuted"]["evidence"] == "unit-level refutation"
    repro = reproduction(seed, "repro", rid)
    level = seed.level()
    assert level["refuted"]["evidence"] == "bug" and level["refuted"]["reproductions"] == [repro]


@pytest.mark.parametrize("make", [
    lambda seed, rid: reproduction(seed, "repro", "proof.t10.another-refutation"),
    lambda seed, rid: reproduction(seed, "repro", rid, code=_stale(seed.template["pins"]["code"])),
])
def test_control_a_reproduction_of_another_refutation_or_one_that_stopped_counting_gives_no_bug(seed, make):
    rid = refuted(seed, "refuted", "reproduced")
    refuted(seed, "another-refutation", "reproduced", pins={"code": _stale(seed.template["pins"]["code"])})
    make(seed, rid)
    level = seed.level()
    assert level["refuted"]["evidence"] == "unit-level refutation" and level["refuted"]["reproductions"] == []


def test_control_an_undefined_behavior_refutation_without_a_reproduction_is_unit_level(seed):
    refuted(seed, "refuted", "undefined_behavior")
    level = seed.level()
    assert level["refuted"]["flag"] is True and level["refuted"]["evidence"] == "unit-level refutation"


# --- snapshots and the rule version ------------------------------------------------------------------

def test_the_snapshot_names_level_time_rule_version_and_counting_records(seed):
    seed.proof("unit", bounds=TOP)
    level = seed.level()
    snapshot = level["snapshot"]
    assert set(snapshot) == {"level", "at", "level_rule", "records"}
    assert snapshot["level"] == "proven_unbounded" and snapshot["level_rule"] == "level-rule.2"
    assert snapshot["records"] == ["proof.t10.unit"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} ET", snapshot["at"])


@pytest.mark.parametrize("field", ["level_rule", "level"])
def test_validate_refuses_a_proof_record_that_holds_a_level_rule_field(seed, field):
    seed.proof("unit", bounds=TOP, **{field: "level-rule.2"})
    result = seed.validate()
    assert result.returncode == 1
    problem = [line for line in result.stderr.splitlines() if "proof.t10.unit" in line and field in line]
    assert problem and "level rule" in problem[0], result.stderr


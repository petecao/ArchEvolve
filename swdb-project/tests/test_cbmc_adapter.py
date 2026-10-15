"""The CBMC adapter through `swdb prove --adapter cbmc` (the bounded verifier at threads = 1, on the C lowering).

Created: 2026-10-14 ET (Probata proof of concept ticket 22; Yan-Ru's 13:19 ET decision made CBMC 6.11 on ticket
21's C lowering the bounded verifier, replacing SAW). Design: formal-verification map spec ("Verifier lineup and
order", "Bounds", "Testing Decisions", seam 1); map 11 items 1-4, 8, 9; 16 items 1, 3; 19 items 2, 8.
Format: docs/reference/format-v0.4-cbmc.md. Reference: prototype/06c-cbmc/.

Seam 1 (`swdb prove`), with `swdb validate` and `swdb candidate-level` reading the records. The fixture candidate
artifacts are GAPBS bfs.cc with the CBMC fixture units inserted (one safe, one with the fill's seeded off-by-one),
built through the public workflow and certified by a fixture record. Cases that run CBMC skip cleanly when CBMC
6.11 or clang 22.1.8 is missing; run them inside the machine-wide verifier lock (on the Mac: verifier_run.py).
Scripted faults use a stand-in `cbmc` (SWDB_CBMC) that writes chosen CBMC output.
"""

import hashlib
import json
import shutil
import sys
import threading

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_proof_records import _library_roots
from test_wp_adapter import _certify, method_version as wp_method_version
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

CBMC = FIXTURES / "proof" / "cbmc"
UNITS = (CBMC / "fixture_units.cc").read_text()
ANCHOR_BEFORE = "pvector<NodeID> InitParent(const Graph &g) {"
SEEDED_BUG = ("  for (int i = 0; i < n; ++i) {\n    a[i] = v;", "  for (int i = 0; i < n - 1; ++i) {\n    a[i] = v;")
FILL, KNOB, SMOKE = "contract.fixture_cbmc_fill", "contract.fixture_cbmc_knob", "contract.fixture_cbmc_smoke"
CLAMP, CLAMP_ALL = "contract.fixture_cbmc_clamp", "contract.fixture_cbmc_clamp_all"
TWICE, VACUOUS = "contract.fixture_cbmc_twice", "contract.fixture_cbmc_vacuous"
FILL_BOUNDS = {"threads": 1, "n": 3}
TRUSTED = {"swdb-c-lowering-6", "clang-22.1.8", "swdb-cbmc-translator-3", "cbmc-6.11.0", "cadical-in-cbmc-6.11.0"}
FILL_CLAUSES = [("fill_pre", "legality", "requires n >= 0 && \\valid(a + (0 .. n-1));", "per_candidate"),
                ("fill_post", "postcondition", "assigns a[0 .. n-1];\nensures \\forall integer k; 0 <= k < n ==> a[k] == v;",
                 "per_candidate")]
CLAMP_POST = "assigns \\nothing;\nensures lo <= \\result <= hi;\nensures lo <= x <= hi ==> \\result == x;"
ONCE = {"once": "self"}
# Ticket 23: the C-stub meaning controls, a logic call, \separated, and a real-valued unit.
ADD_ONE, CALL_BAD, CALL_KEEP = "contract.fixture_cbmc_add_one", "contract.fixture_cbmc_call_bad", "contract.fixture_cbmc_call_keep"
CALL_OUTSIDE, TOTAL, TOTAL_WRONG = ("contract.fixture_cbmc_call_outside", "contract.fixture_cbmc_total",
                                    "contract.fixture_cbmc_total_wrong")
CALL_INC = "contract.fixture_cbmc_call_inc"
COPY, HALF, POST_BOUND = "contract.fixture_cbmc_copy", "contract.fixture_cbmc_half", "contract.fixture_cbmc_post_bound"
CALLER_PRE = "requires 1 <= n <= 3 && \\valid(a + (0 .. n-1)) && -1000 <= a[0] <= 1000;"
LOGIC_SUM = ("// version: 1.0\n"
             "logic integer fixture_sum{L}(int *a, integer n) =\n"
             "  n <= 0 ? 0 : fixture_sum(a, n - 1) + a[n - 1];\n")


def _tools_present():
    from swdb import c_lowering, cbmc_adapter
    return not cbmc_adapter.locate()[2] and not c_lowering.locate().missing


needs_cbmc = pytest.mark.skipif(not _tools_present(), reason="CBMC 6.11 or clang 22.1.8 is missing")


# --- the seed ---------------------------------------------------------------------------------------------------

def _contract(cid, function, clauses, frame, knobs=()):
    unit = {"root": "library", "path": "proof_units/cbmc_fixture_units.cc",
            "sha256": hashlib.sha256(UNITS.encode()).hexdigest()}
    return {
        "kind": "rewrite_contract", "id": cid, "formal_frame": 1, "version": "1.0",
        "provenance": {"origin": {"intrinsic_specification": "fixture-22"}},
        "proof_unit": {"source": unit, "function": function},
        "concurrency_frame": frame,
        "clauses": [{"id": name, "role": role, "statement": f"Fixture clause {name}.", "discharge_mode": "runtime_guard",
                     "negative_control": {"id": f"{name}-control", "check": name},
                     "acsl": {"text": text, "uses": list(more[0]) if more else []}, "proof_placement": placement}
                    for name, role, text, placement, *more in clauses],
        "pattern_key": [{"roles": ["index", "target"], "address_shapes": ["stream", "single_valued_indirect"],
                         "update_kind": "read"}],
        "strategies": [], "uses_intrinsics": [], "uses_library_operations": [], "runtime_guards": [],
        "knobs": list(knobs), "preservation_obligations": [], "correctness_check": {"kernel": "fixture", "check": "fixture"},
        "execution_witness": {"check": "fixture"},
        "negative_controls": [{"id": kind, "kind": kind, "check": "fixture"}
                              for kind in ("overlapping_pointer", "double_claim", "dropped_operand")],
        "requirement_map": []}


def method_version(identity):
    """A contract_fixture method version with the real Mac lineup and CBMC as the bounded verifier (sequence 2)."""
    from swdb import cbmc_translator, std_models
    data = wp_method_version(identity)
    data["models"] = {"std_vector": std_models.identity(), "std_pair": std_models.identity()}
    data.update(id="method.cbmc-fixture", description="Fixture method version with CBMC 6.11 as the bounded "
                                                       "verifier on the C lowering (ticket 22 tests).")
    next(row for row in data["lineup"] if row["tool"] == "cbmc")["flags"] = ["--sat-solver", "cadical"]
    data["lineup"].append({"role": "bounded_verifier_fallback", "tool": "crux-llvm", "version": "0.12",
                           "flags": ["--no-compile"]})                       # ticket 23
    data["c_lowering"]["translators"] = [identity["c_lowering"], cbmc_translator.identity()]
    return data


def _contracts():
    array = [{"array": "a", "shared_actions": [], "history_reads": False}]
    knob = {"name": "swdb_fixture_threshold", "default": 4, "range": {"min": 1, "max": 8}, "origin": "fixture",
            "legality_clause": "knob_legal"}
    return {
        "fixture_cbmc_fill": _contract(FILL, "swdb_fixture_fill", FILL_CLAUSES, array),
        "fixture_cbmc_knob": _contract(KNOB, "swdb_fixture_fill_knob", FILL_CLAUSES + [
            ("knob_legal", "legality", "requires 1 <= swdb_fixture_threshold <= 8;", "per_candidate")], array, [knob]),
        "fixture_cbmc_smoke": _contract(SMOKE, "smoke_main", [
            ("smoke_post", "postcondition", "assigns \\nothing;\nensures \\result == 1;", "per_candidate")], []),
        "fixture_cbmc_clamp": _contract(CLAMP, "swdb_fixture_clamp", [
            ("clamp_pre", "legality", "requires lo <= hi;", ONCE),
            ("clamp_post", "postcondition", CLAMP_POST, ONCE)], []),
        "fixture_cbmc_clamp_all": _contract(CLAMP_ALL, "swdb_fixture_clamp_all", [
            ("clamp_all_pre", "legality", "requires n >= 0 && \\valid(a + (0 .. n-1));", "per_candidate"),
            ("clamp_all_post", "postcondition",
             "assigns a[0 .. n-1];\nensures \\forall integer k; 0 <= k < n ==> 0 <= a[k] <= 9;\n"
             "ensures \\forall integer k; 0 <= k < n ==> (0 <= \\old(a[k]) <= 9 ==> a[k] == \\old(a[k]));",
             "per_candidate")], array),
        "fixture_cbmc_twice": _contract(TWICE, "swdb_fixture_twice", [
            ("twice_post", "postcondition", "requires 0 <= n <= 100;\nassigns \\nothing;\nensures \\result == 2 * n;",
             "per_candidate")], []),
        "fixture_cbmc_add_one": _contract(ADD_ONE, "swdb_fixture_add_one", [
            ("add_one_pre", "legality", "requires 0 <= i < n && \\valid(a + (0 .. n-1)) && -1000 <= a[i] <= 1000;", ONCE),
            ("add_one_post", "postcondition", "assigns a[i];\nensures a[i] == \\old(a[i]) + 1;", ONCE)], array),
        "fixture_cbmc_call_bad": _contract(CALL_BAD, "swdb_fixture_call_bad", [
            ("bad_pre", "legality", CALLER_PRE, "per_candidate"),
            ("bad_post", "postcondition", "assigns a[0 .. n-1];\nensures \\result == 0;", "per_candidate")], array),
        "fixture_cbmc_call_keep": _contract(CALL_KEEP, "swdb_fixture_call_keep", [
            ("keep_pre", "legality", CALLER_PRE, "per_candidate"),
            ("keep_post", "postcondition", "assigns a[0 .. n-1];\nensures \\result == \\old(a[0]);",
             "per_candidate")], array),
        "fixture_cbmc_call_outside": _contract(CALL_OUTSIDE, "swdb_fixture_call_outside", [
            ("outside_pre", "legality", CALLER_PRE.replace("1 <= n", "2 <= n"), "per_candidate"),
            ("outside_post", "postcondition", "assigns a[0 .. n-1];\nensures \\result == \\old(a[1]);",
             "per_candidate")], array),
        "fixture_cbmc_call_inc": _contract(CALL_INC, "swdb_fixture_call_inc", [
            ("inc_pre", "legality", CALLER_PRE, "per_candidate"),
            ("inc_post", "postcondition", "assigns a[0 .. n-1];\nensures \\result == \\old(a[0]) + 1;",
             "per_candidate")], array),
        "fixture_cbmc_total": _contract(TOTAL, "swdb_fixture_total", [
            ("total_pre", "legality", "requires 0 <= n && \\valid(a + (0 .. n-1)) && "
                                       "(\\forall integer k; 0 <= k < n ==> -1000 <= a[k] <= 1000);", "per_candidate"),
            ("total_post", "postcondition", "assigns \\nothing;\nensures \\result == fixture_sum(a, n);",
             "per_candidate", ["logic.fixture_sum"])], array),
        "fixture_cbmc_total_wrong": _contract(TOTAL_WRONG, "swdb_fixture_total", [
            ("total_pre", "legality", "requires 0 <= n && \\valid(a + (0 .. n-1)) && "
                                       "(\\forall integer k; 0 <= k < n ==> -1000 <= a[k] <= 1000);", "per_candidate"),
            ("total_post", "postcondition", "assigns \\nothing;\nensures \\result == fixture_sum(a, n - 1);",
             "per_candidate", ["logic.fixture_sum"])], array),
        "fixture_cbmc_copy": _contract(COPY, "swdb_fixture_copy", [
            ("copy_pre", "legality", "requires 0 <= n && \\valid(a + (0 .. n-1)) && \\valid(b + (0 .. n-1)) && "
                                     "\\separated(a + (0 .. n-1), b + (0 .. n-1)) && "
                                     "(\\forall integer k; 0 <= k < n ==> -1000 <= a[k] <= 1000);", "per_candidate"),
            ("copy_post", "postcondition", "assigns b[0 .. n-1];\n"
                                           "ensures \\forall integer k; 0 <= k < n ==> b[k] == \\old(a[k]);",
             "per_candidate")], array + [{"array": "b", "shared_actions": [], "history_reads": False}]),
        "fixture_cbmc_half": _contract(HALF, "swdb_fixture_half", [
            ("half_post", "postcondition", "assigns \\nothing;\nensures \\result == x / 2.0;", "per_candidate")], []),
        "fixture_cbmc_post_bound": _contract(POST_BOUND, "swdb_fixture_total", [
            ("post_bound_pre", "legality", "requires 0 <= n && \\valid(a + (0 .. n-1));", "per_candidate"),
            ("post_bound_post", "postcondition", "assigns \\nothing;\n"
             "ensures \\forall integer k; 0 <= k < \\result ==> a[0] >= -2;", "per_candidate")], array),
        "fixture_cbmc_vacuous": _contract(VACUOUS, "smoke_main", [
            ("vacuous_pre", "legality", "requires x > 100 && x < 0;", "per_candidate"),
            ("vacuous_post", "postcondition", "assigns \\nothing;\nensures \\result == 1;", "per_candidate")], []),
    }


def build_cbmc_seed(path):
    """records/ and library/ under `path`; returns {safe, bug} candidate artifact IDs."""
    from swdb import c_lowering
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    methods = path / "library" / "methods"
    methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    (methods / "cbmc-fixture.yaml").write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    (path / "library" / "proof_units").mkdir()
    (path / "library" / "proof_units" / "cbmc_fixture_units.cc").write_text(UNITS)
    (path / "library" / "logic").mkdir(exist_ok=True)
    (path / "library" / "logic" / "fixture_sum.acsl").write_text(LOGIC_SUM)
    for name, data in _contracts().items():
        (path / "library" / "rewrite_contracts" / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    candidates = {}
    for name, units in (("safe", UNITS), ("bug", UNITS.replace(*SEEDED_BUG))):
        submitted = records.swdb("submit", request(ANCHOR_BEFORE, units + "\n" + ANCHOR_BEFORE, id=f"cbmc-{name}"),
                                 "--runs-dir", runs, "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        candidates[name] = json.loads(submitted.stdout)["candidate"]
        _certify(records.path, path, candidates[name], FILL)
    return candidates


@pytest.fixture(scope="module")
def cbmc_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("cbmc-seed")
    return path, build_cbmc_seed(path)


QUIET = {"SWDB_FRAMA_C": "none"}          # swdb validate's Frama-C type-check is not under test here


class Seed:
    def __init__(self, root, candidates):
        self.root, self.candidates = root, candidates
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args, env=None):
        return run_swdb(command, "--records", self.records, *args, env={**QUIET, **(env or {})})

    def prove(self, function="swdb_fixture_fill", contract=FILL, bounds=None, *extra, candidate="safe", env=None,
              ok=True):
        args = ["--candidate", self.candidates[candidate], "--function", function, "--contract", contract,
                "--adapter", "cbmc", "--runs-dir", self.runs, "--format", "json",
                "--bounds", json.dumps(bounds or FILL_BOUNDS)]
        result = self.swdb("prove", *args, *extra, env=env)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout) if ok else result

    def prove_summary(self, entry=CLAMP, ok=True, bounds=None, env=None):
        result = self.swdb("prove", "--summary", entry, "--adapter", "cbmc", "--runs-dir", self.runs, "--format", "json",
                           "--bounds", json.dumps(bounds or {"threads": 1}), env=env)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout) if ok else result

    def read(self, out):
        return yaml.safe_load((self.records / out["path"]).read_text())

    def report(self, record, name):
        return next(r["path"] for r in record["evidence"]["reports"] if r["name"] == name)


@pytest.fixture
def seed(cbmc_seed, tmp_path):
    source, candidates = cbmc_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


def _handler(seed, record):
    return json.loads(open(seed.report(record, "handler")).read())


# --- the safe fixture, the seeded bug, the smoke pair ---------------------------------------------------------

@needs_cbmc
def test_the_safe_fixture_is_proven_within_its_bounds_on_both_forms(seed):
    record = seed.read(seed.prove())
    assert record["verdict"] == "proven" and record["job"]["adapter"] == "cbmc"
    assert record["bounds"] == FILL_BOUNDS                        # threads = 1 and every size bound, exactly
    assert record["evidence_kind"] == "contract_fixture"
    settings = record["settings"]
    assert settings["unwind"] == 4 and "--unwinding-assertions" in settings["flags"]   # K = n + 1
    assert settings["agreement"]["verdict"] == "agree" and settings["agreement"]["runs"] > 100
    assert settings["agreement"]["domain"]["n"]["values"] == [-1, 0, 1, 2, 3]       # every size up to its bound
    assert settings["forms"] == {"c_lowering": "proven", "cxx": "agrees on the bounded domain"}
    assert {a["reference"]["id"] for a in record["assumptions"] if a["kind"] == "trusted_tool"} == TRUSTED
    assert set(record["tools"]) == TRUSTED
    assert record["pins"]["c_lowering"]["id"] == "swdb_fixture_fill.c"
    assert record["pins"]["translator"]["id"] == "swdb-cbmc-translator-3"
    assert {f"{FILL}#fill_post.ensures1", f"{FILL}#fill_post.assigns1"} <= {g["property"] for g in record["goals"]}
    assert all(g["status"] == "success" for g in record["goals"] if not g["property"].startswith("swdb_reach"))
    assert not (seed.runs / record["id"] / "scratch").exists()
    assert seed.swdb("validate").returncode == 0
    level = seed.swdb("candidate-level", seed.candidates["safe"], "--format", "json")
    assert json.loads(level.stdout)["level"] == "proven_within_bounds_threads_1"


@needs_cbmc
def test_the_translator_is_deterministic_and_pinned(seed):
    first, second = (seed.read(seed.prove()) for _ in range(2))
    inputs = [open(seed.report(r, "cbmc_input"), "rb").read() for r in (first, second)]
    assert inputs[0] == inputs[1] and b"swdb-cbmc-translator 3" in inputs[0]
    assert first["pins"]["translator"] == second["pins"]["translator"]


@needs_cbmc
def test_the_seeded_bug_is_refuted_with_concrete_inputs_that_replay_on_the_cpp(seed):
    record = seed.read(seed.prove(candidate="bug"))
    assert record["verdict"] == "refuted" and "failure_class" not in record
    example = record["counterexample"]
    assert example["property"].startswith(f"{FILL}#fill_post") and example["replay"]["replayed"] is True
    inputs = example["inputs"]
    assert 1 <= inputs["n"] <= 3 and len(inputs["a"]) == 3 and "v" in inputs
    assert record["settings"]["forms"] == {"c_lowering": "refuted", "cxx": "refuted (counterexample replayed)"}
    level = seed.swdb("candidate-level", seed.candidates["bug"], "--format", "json")
    assert json.loads(level.stdout)["refuted"]["flag"] is True


@needs_cbmc
def test_map_07_smoke_pair_proves_the_safe_program_and_refutes_the_seeded_bug_at_41(seed):
    bounds = {"threads": 1}
    proven = seed.read(seed.prove("smoke_main", SMOKE, bounds))
    assert proven["verdict"] == "proven"
    buggy = seed.read(seed.prove("smoke_main", SMOKE, bounds, "--define", "BUGGY"))
    assert buggy["verdict"] == "refuted" and buggy["counterexample"]["inputs"] == {"x": 41}
    assert buggy["pins"]["build_constants"] == [{"name": "BUGGY", "value": "1"}]


@needs_cbmc
def test_a_compared_knob_is_symbolic_within_its_legality_clause_and_a_one_value_bug_names_that_value(seed):
    record = seed.read(seed.prove("swdb_fixture_fill_knob", KNOB))
    assert record["verdict"] == "proven"
    (knob,) = record["settings"]["symbolic_knobs"]
    assert knob["name"] == "swdb_fixture_threshold" and knob["legality_clause"] == "knob_legal"
    assert knob["acsl"] == "requires 1 <= swdb_fixture_threshold <= 8;" and knob["range"] == {"min": 1, "max": 8}
    assert record["pins"]["build_constants"] == []                # the knob is not a build constant
    buggy = seed.read(seed.prove("swdb_fixture_fill_knob", KNOB, None, "--define", "SWDB_SEEDED_KNOB_BUG"))
    assert buggy["verdict"] == "refuted"
    assert buggy["counterexample"]["inputs"]["swdb_fixture_threshold"] == 3     # the one failing legal value


# --- summaries --------------------------------------------------------------------------------------------------

@needs_cbmc
def test_a_callee_summary_is_proven_first_then_pinned_and_used_as_a_stub_in_place_of_its_code(seed):
    refused = seed.prove("swdb_fixture_clamp_all", CLAMP_ALL, {"threads": 1, "n": 2}, ok=False)
    assert "no proven summary record" in refused.stderr
    summary = seed.read(seed.prove_summary())
    assert summary["subject"] == {"kind": "library_summary", "id": CLAMP} and summary["verdict"] == "proven"
    unit = seed.read(seed.prove("swdb_fixture_clamp_all", CLAMP_ALL, {"threads": 1, "n": 2}))
    assert unit["verdict"] == "proven"
    (pin,) = unit["pins"]["summaries"]
    assert pin["id"] == CLAMP and pin["proof_record"] == summary["id"] and pin["sha256"] == summary["pins"]["code"]["sha256"]
    job_c = open(seed.report(unit, "cbmc_input")).read()
    assert "summary stub of swdb_fixture_clamp" in job_c and "x < lo ? lo" not in job_c   # the stub, not the code
    assert seed.swdb("validate").returncode == 0


@needs_cbmc
def test_override_negative_control_a_weakened_summary_no_longer_proves_the_unit(seed):
    path = seed.root / "library" / "rewrite_contracts" / "fixture_cbmc_clamp.yaml"
    data = yaml.safe_load(path.read_text())
    clause = next(c for c in data["clauses"] if c["id"] == "clamp_post")
    clause["acsl"]["text"] = CLAMP_POST.replace("ensures lo <= \\result <= hi;\n", "")       # one postcondition dropped
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    assert seed.read(seed.prove_summary())["verdict"] == "proven"
    unit = seed.read(seed.prove("swdb_fixture_clamp_all", CLAMP_ALL, {"threads": 1, "n": 2}))
    assert unit["verdict"] != "proven"


# --- ticket 23: C-stub meaning (\old over memory in a stub), assumes listed under their summary -------------------

CALLER_BOUNDS = {"threads": 1, "n": 3}


def _with_add_one_summary(seed):
    summary = seed.read(seed.prove_summary(ADD_ONE, bounds={"threads": 1, "n": 2}))
    assert summary["verdict"] == "proven"
    return summary


@needs_cbmc
def test_c_stub_meaning_a_caller_that_breaks_the_callees_precondition_is_refuted_at_the_stubs_assert(seed):
    _with_add_one_summary(seed)
    record = seed.read(seed.prove("swdb_fixture_call_bad", CALL_BAD, CALLER_BOUNDS))
    assert record["verdict"] == "refuted"
    assert record["counterexample"]["property"] == f"{ADD_ONE}#add_one_pre"
    assert record["counterexample"]["replay"]["replayed"] is True


@needs_cbmc
def test_c_stub_meaning_a_caller_expecting_a_location_inside_assigns_to_keep_its_value_is_refuted(seed):
    _with_add_one_summary(seed)
    record = seed.read(seed.prove("swdb_fixture_call_keep", CALL_KEEP, CALLER_BOUNDS))
    assert record["verdict"] == "refuted"
    assert record["counterexample"]["property"] == f"{CALL_KEEP}#keep_post.ensures1"


@needs_cbmc
def test_c_stub_meaning_a_caller_relying_on_a_location_outside_assigns_proves_and_lists_each_assume(seed):
    summary = _with_add_one_summary(seed)
    record = seed.read(seed.prove("swdb_fixture_call_outside", CALL_OUTSIDE, CALLER_BOUNDS))
    assert record["verdict"] == "proven"
    (pin,) = record["pins"]["summaries"]
    assert pin["id"] == ADD_ONE and pin["proof_record"] == summary["id"]
    assert pin["assumes"] == [f"{ADD_ONE}#add_one_post.ensures1"]          # the stub's one generated assume
    job_c = open(seed.report(record, "cbmc_input")).read()
    assume = next(line for line in job_c.splitlines() if "assume from summary" in line)
    assert f"{ADD_ONE} sha256 {pin['sha256'][:16]}" in assume and "add_one_post.ensures1" in assume
    assert seed.swdb("validate").returncode == 0


# --- ticket 23: logic calls and \separated -----------------------------------------------------------------------

@needs_cbmc
def test_a_logic_library_call_in_a_formal_half_is_translated_and_decides_the_verdict(seed):
    assert seed.read(seed.prove("swdb_fixture_total", TOTAL))["verdict"] == "proven"
    wrong = seed.read(seed.prove("swdb_fixture_total", TOTAL_WRONG))
    assert wrong["verdict"] == "refuted" and wrong["counterexample"]["property"] == f"{TOTAL_WRONG}#total_post.ensures1"


@needs_cbmc
def test_separated_arrays_and_an_old_value_under_a_quantifier_prove_the_copy(seed):
    assert seed.read(seed.prove("swdb_fixture_copy", COPY))["verdict"] == "proven"
    buggy = seed.read(seed.prove("swdb_fixture_copy", COPY, None, "--define", "SWDB_SEEDED_FRAME_BUG"))
    assert buggy["verdict"] == "refuted"                            # the frame (assigns) or the \old clause catches it
    assert buggy["counterexample"]["property"] in (f"{COPY}#copy_post.assigns1", f"{COPY}#copy_post.ensures1")


# --- the agreement check and the subset -------------------------------------------------------------------------

@needs_cbmc
def test_a_hand_mutated_c_lowering_disagrees_with_the_cpp_and_stops_the_batch(seed):
    fault = seed.root / "fault.yaml"
    fault.write_text(yaml.safe_dump({"replace": [["for (int i = 0; i < n; ++i)", "for (int i = 0; i < n - 1; ++i)"]]}))
    result = seed.prove(env={"SWDB_CBMC_LOWERING_FAULT": str(fault)}, ok=False)
    assert "c_lowering_disagreement" in result.stderr and "disagree on input" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))       # no verdict recorded


@needs_cbmc
def test_a_unit_outside_the_cpp_subset_gets_no_c_lowering_and_its_record_names_the_reason(seed):
    record = seed.read(seed.prove("InitParent", FILL, {"threads": 1}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert record["settings"]["outside_cpp_subset"].startswith("outside the C++ subset")
    assert "agreement" not in record["settings"] and "forms" not in record["settings"]


# --- budget, bounds and failure classes --------------------------------------------------------------------------

FAKE = f"{sys.executable} {CBMC / 'fake_cbmc.py'}"


def fake(mode, **more):
    from swdb import cbmc_adapter
    return {"SWDB_CBMC": FAKE, "FAKE_CBMC_MODE": mode, "FAKE_CBMC_REAL": " ".join(cbmc_adapter.locate()[0]), **more}


@needs_cbmc
def test_a_job_over_its_budget_is_not_proven_timeout_and_never_retried_smaller(seed):
    record = seed.read(seed.prove("swdb_fixture_fill", FILL, None, "--budget-minutes", "0.02", env=fake("sleep")))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "timeout"
    assert record["bounds"] == FILL_BOUNDS                        # the bounds asked for, never smaller
    assert "never retried at smaller bounds" in _handler(seed, record)["done"]


@needs_cbmc
def test_bounds_other_than_one_thread_and_sizes_are_refused(seed):
    assert "threads = 1" in seed.prove(bounds={"threads": 3, "n": 3}, ok=False).stderr
    assert "size bound" in seed.prove(bounds={"threads": 1}, ok=False).stderr
    assert "not an integer parameter" in seed.prove(bounds={"threads": 1, "vertices": 3}, ok=False).stderr


@needs_cbmc
def test_a_loop_beyond_the_size_bound_is_unwinding_bound_too_small_never_proven(seed):
    record = seed.read(seed.prove("swdb_fixture_twice", TWICE, {"threads": 1, "n": 2}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unwinding_bound_too_small"
    assert _handler(seed, record)["loops"]


@needs_cbmc
def test_contradictory_preconditions_are_a_vacuous_pass_never_proven(seed):
    record = seed.read(seed.prove("smoke_main", VACUOUS, {"threads": 1}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "vacuous_pass"


@needs_cbmc
def test_a_counterexample_that_does_not_replay_is_a_spurious_counterexample_never_a_refutation(seed):
    record = seed.read(seed.prove(env=fake("spurious", FAKE_CBMC_PROPERTY=f"{FILL}#fill_post.ensures1")))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "spurious_counterexample"
    assert "counterexample" not in record and record["unreplayed_counterexample"]["replay"]["replayed"] is False
    assert _handler(seed, record)["repair"] == "never sent to counterexample-guided repair"


@needs_cbmc
def test_a_job_the_watchdog_kills_reads_not_proven_out_of_memory(seed):
    record = seed.read(seed.prove(env={"SWDB_VERIFIER_RSS_CAP_BYTES": str(4 * 2**20)}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "out_of_memory"


@needs_cbmc
@pytest.mark.parametrize("mode, failure_class", [("parse_error", "parse_error"), ("solver_error", "solver_error"),
                                                 ("crash", "tool_crash")])
def test_scripted_cbmc_faults_map_to_their_class_and_run_its_handler(seed, mode, failure_class):
    record = seed.read(seed.prove(env=fake(mode)))
    assert record["verdict"] == "not_proven" and record["failure_class"] == failure_class
    handler = _handler(seed, record)
    assert handler["failure_class"] == failure_class and handler["handler"] and handler["minimal_reproduction"]


@needs_cbmc
def test_an_outcome_with_no_class_stops_the_batch_and_writes_no_record(seed):
    result = seed.prove(env=fake("silent"), ok=False)
    assert "unclassified_cbmc_outcome" in result.stderr and "batch stops" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


@needs_cbmc
def test_installed_tools_that_differ_from_the_method_versions_lineup_run_nothing(seed):
    path = seed.root / "library" / "methods" / "cbmc-fixture.yaml"
    data = yaml.safe_load(path.read_text())
    next(row for row in data["lineup"] if row["tool"] == "cbmc")["version"] = "6.10"
    data.update(id="method.cbmc-other", sequence=3)
    (path.parent / "cbmc-other.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    result = seed.prove(ok=False)
    assert "cbmc 6.11.0 is installed but method version method.cbmc-other pins 6.10" in result.stderr


# --- the machine-wide lock ------------------------------------------------------------------------------------

@needs_cbmc
def test_two_real_cbmc_jobs_started_together_never_overlap(seed, tmp_path):
    """Updated 2026-10-15 ET: the Mac's machine lock has two slots, so exclusion is checked on a private
    one-slot lock (no policy file beside it)."""
    times = tmp_path / "times.txt"
    env = fake("wrap", FAKE_CBMC_TIMES=str(times), SWDB_VERIFIER_LOCK=str(tmp_path / "one-slot.lock"))
    results = []
    threads = [threading.Thread(target=lambda: results.append(seed.prove(env=env))) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(results) == 2 and all(seed.read(r)["verdict"] == "proven" for r in results)
    spans = {}
    for kind, at, pid in (line.split() for line in times.read_text().splitlines()):
        spans.setdefault(pid, {})[kind] = float(at)
    first, second = sorted(spans.values(), key=lambda span: span["start"])
    assert first["end"] <= second["start"], spans


# --- the regression corpus ------------------------------------------------------------------------------------

CORPUS = sorted((FIXTURES / "proof" / "regression_corpus").glob("*.yaml"))


@needs_cbmc
@pytest.mark.parametrize("case", [c for c in CORPUS if yaml.safe_load(c.read_text())["adapter"] == "cbmc"],
                         ids=lambda c: c.stem)
def test_each_cbmc_regression_corpus_case_gives_its_recorded_class_again(seed, case):
    data = yaml.safe_load(case.read_text())
    assert data["cause"].strip()
    given = data["input"]
    env = {}
    if given.get("lowering_fault"):
        fault = seed.root / "fault.yaml"
        fault.write_text(yaml.safe_dump({"replace": given["lowering_fault"]}))
        env["SWDB_CBMC_LOWERING_FAULT"] = str(fault)
    extra = [part for d in given.get("defines") or [] for part in ("--define", d)]
    if data["failure_class"] == "c_lowering_disagreement":             # not a class: the batch stops
        result = seed.prove(given["function"], given["contract"], given["bounds"], *extra, env=env, ok=False)
        assert data["failure_class"] in result.stderr
        return
    record = seed.read(seed.prove(given["function"], given["contract"], given["bounds"], *extra, env=env))
    assert record.get("failure_class") == data["failure_class"]


# --- the bounded gate's target adapter (ticket 14's TargetAdapter.bounded_job contract) ------------------------------

def _target(store_dir, function):
    from swdb.campaign_targets import TargetAdapter

    class Target(TargetAdapter):
        PROOF_FUNCTION = function
    adapter = Target.__new__(Target)                       # the gate hooks read only these two fields
    adapter.campaign, adapter.store_dir = {"target": "native"}, store_dir
    return adapter


def test_the_target_adapters_one_thread_rung_is_a_cbmc_job_and_threads_k_waits_for_civl(tmp_path):
    from swdb.cli import Failure
    adapter = _target(tmp_path, "TDStep")
    assert adapter.bounded_job("candidate.x", FILL, "threads_1", {"threads": 1, "n": 3}) == {"adapter": "cbmc"}
    with pytest.raises(Failure, match="tickets 46, 47"):
        adapter.bounded_job("candidate.x", FILL, "threads_k", {"threads": 3, "n": 3})


@needs_cbmc
def test_the_target_adapter_reads_outside_the_subset_from_the_c_lowering_of_the_proof_function(seed):
    candidate = seed.candidates["safe"]
    assert _target(seed.records, "TDStep").outside_cpp_subset(candidate) is True       # GAPBS TDStep: Graph &
    assert _target(seed.records, "swdb_fixture_fill").outside_cpp_subset(candidate) is False

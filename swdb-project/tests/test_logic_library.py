"""The logic library: versioned shared files, an entry's own file, logic pins in proof records, the sum
library's WP proofs, the \\false check and the CSR fixture.

Created: 2026-10-14 ET (Probata proof of concept ticket 26). Design: formal-verification map 16 items 2, 9
and 12; 24 item 4; 27 item 3. Format: docs/reference/format-v0.4-logic-library.md.

Seams:
- A. `swdb validate --library` on a minimal library (the repository's logic files, fixture entries).
- B. `swdb prove` (scripted adapter) and `swdb candidate-level` on the proof seed: the logic pins and the
  level rule's reading of them. No verifier runs.
- C. `swdb prove-logic` with real Frama-C/WP (skips without Frama-C 33.0 and clang 22.1.8): the sum
  library's lemmas, the \\false check and its negative control, the CSR fixture and its seeded bugs.
  Run these inside the machine-wide verifier lock (verifier_run.py) with the sandbox off.
"""

import json
import shutil

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_formal_frame import UNIT_CC, frame_contract, write_library
from test_proof_records import _Seed, build_proof_seed

LOGIC = REPO / "library" / "logic"
SHARED = ("logic.access", "logic.csr_graph", "logic.sets", "logic.sum")
SUM_LEMMAS = 17
PBAD = "predicate pbad(integer x) = !pbad(x);\n"


def _tools_present():
    from swdb import c_lowering, framac
    return not framac.locate().missing and not c_lowering.locate().missing


needs_wp = pytest.mark.skipif(not _tools_present(), reason="Frama-C 33.0 or clang 22.1.8 is missing")


def minimal_library(root, extra=None):
    """library/ under `root` with the repository's logic files (proof hints included) and `extra` entries."""
    shutil.copytree(LOGIC, root / "logic")
    write_library(root, extra or {})
    return root


def validate(records, root, **env):
    return run_swdb("validate", "--records", records.path, "--library", root, env=env or None)


# --- A. swdb validate ----------------------------------------------------------------------------------

def test_the_shared_logic_files_are_versioned_and_validate(tmp_path):
    records = make_records(tmp_path)
    root = minimal_library(tmp_path / "library")
    checked = validate(records, root)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    from swdb import logic_library
    found = logic_library.files(root)
    assert sorted(found) == list(SHARED)
    assert {f.version for f in found.values()} == {"1.0"}
    if not _tools_present():
        return
    assert "4 logic file(s) type-checked" in checked.stdout


def test_without_framac_logic_files_are_reported_unchecked_never_valid(tmp_path):
    records = make_records(tmp_path)
    root = minimal_library(tmp_path / "library")
    checked = validate(records, root, SWDB_FRAMA_C="none")
    assert checked.returncode == 0, checked.stderr
    assert "4 logic file(s) unchecked" in checked.stdout
    assert "logic file(s) type-checked" not in checked.stdout


def test_range_sum_and_filtered_sum_pass_the_primitive_recursion_rule_and_a_sum_over_hi_does_not(tmp_path):
    """Before any lemma work: both sums recurse on a count n under n <= 0 (map 16 item 2)."""
    records = make_records(tmp_path)
    root = tmp_path / "library"
    (root / "logic").mkdir(parents=True)
    shutil.copy(LOGIC / "sum.acsl", root / "logic")
    # control: a range sum over [lo, hi) that recurses on hi breaks the rule (the reason for a count argument)
    (root / "logic" / "sum_hi.acsl").write_text(
        "// version: 1.0\n"
        "logic real hi_sum{L}(float *x, int *a, integer lo, integer hi) =\n"
        "  hi <= lo ? 0.0 : hi_sum(x, a, lo, hi - 1) + x[a[hi - 1]];\n")
    checked = validate(records, root, SWDB_FRAMA_C="none")
    problems = [line for line in checked.stderr.splitlines() if "/logic/" in line and not line.startswith("UNCHECKED")]
    assert len(problems) == 1 and "sum_hi.acsl: hi_sum:" in problems[0] and "primitive recursive" in problems[0]
    from swdb import acsl_subset
    definitions = acsl_subset.LogicLibrary({"logic.sum": (LOGIC / "sum.acsl").read_text()}).definitions
    for name in ("sum_n", "fsum_n"):
        assert name in definitions[name].calls          # recursive, and accepted as primitive recursive
    assert "sum_n" in definitions["range_sum"].calls and "fsum_n" in definitions["filtered_sum"].calls


def test_a_logic_file_without_a_version_line_is_refused(tmp_path):
    records = make_records(tmp_path)
    root = minimal_library(tmp_path / "library", {"logic/unversioned.acsl": "logic integer twice(integer x) = 2 * x;\n"})
    checked = validate(records, root, SWDB_FRAMA_C="none")
    assert checked.returncode == 1
    problems = [line for line in checked.stderr.splitlines() if "/logic/" in line and not line.startswith("UNCHECKED")]
    assert len(problems) == 1 and "unversioned.acsl: version:" in problems[0], checked.stderr


def own_entries(other_uses_it=False):
    """A fixture contract with its own logic file beside its YAML, and a second contract."""
    own = {"id": "own", "role": "postcondition", "statement": "Fixture clause own.", "discharge_mode": "differential_test",
           "negative_control": {"id": "own-control", "check": "own"}, "proof_placement": "per_candidate",
           "acsl": {"text": "requires n >= 0 && fixture_bounded(parent, n) && at(parent, 0) >= -1;",
                    "uses": ["logic.access", "logic.contract.fixture_own"]}}
    other = dict(own, acsl={"text": "requires n >= 0 && fixture_bounded(parent, n);",
                            "uses": ["logic.contract.fixture_own"]})
    entries = {
        "proof_units/fixture_unit.cc": UNIT_CC,
        "rewrite_contracts/own.yaml": frame_contract("contract.fixture_own", clauses=[own]),
        "rewrite_contracts/own.acsl": "// version: 1.0\n// The fixture contract's own logic file.\n"
                                      "predicate fixture_bounded{L}(int *a, integer n) =\n"
                                      "  \\forall integer k; 0 <= k < n ==> -1 <= a[k] < n;\n",
    }
    if other_uses_it:
        entries["rewrite_contracts/other.yaml"] = frame_contract("contract.fixture_other", clauses=[other])
    return entries


def test_a_contracts_own_logic_file_beside_its_yaml_loads_like_a_shared_file(tmp_path):
    records = make_records(tmp_path)
    root = minimal_library(tmp_path / "library", own_entries())
    checked = validate(records, root)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    from swdb import logic_library
    from swdb.library import Library
    found = logic_library.files(root, Library(root))
    own = found["logic.contract.fixture_own"]
    assert own.owner == "contract.fixture_own" and own.version == "1.0"
    assert own.proofs == root / "rewrite_contracts" / "own.proofs"
    if _tools_present():
        assert "5 logic file(s) type-checked" in checked.stdout
        assert "1 acsl field(s) type-checked" in checked.stdout


def test_another_entry_may_not_use_a_contracts_own_logic_file(tmp_path):
    records = make_records(tmp_path)
    root = minimal_library(tmp_path / "library", own_entries(other_uses_it=True))
    checked = validate(records, root, SWDB_FRAMA_C="none")
    assert checked.returncode == 1
    problems = [line for line in checked.stderr.splitlines() if "logic.contract.fixture_own" in line]
    assert len(problems) == 1 and "other.yaml" in problems[0] and "belongs to another entry" in problems[0]


# --- B. logic pins and the level rule ---------------------------------------------------------------------

LOGIC_CONTRACT = "contract.fixture_logic_pins"


@pytest.fixture(scope="module")
def pin_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("logic-pin-seed")
    candidate = build_proof_seed(path)
    write_library(path / "library", {
        "proof_units/fixture_unit.cc": UNIT_CC,
        "rewrite_contracts/fixture_logic_pins.yaml": frame_contract(LOGIC_CONTRACT, clauses=[
            {"id": "pre", "role": "legality", "statement": "Inputs are in bounds.", "discharge_mode": "runtime_guard",
             "negative_control": {"id": "bad-n", "check": "bounds"}, "proof_placement": "per_candidate",
             "acsl": {"text": "requires n >= 0 && at(parent, 0) >= -1;", "uses": ["logic.access"]}}]),
        "rewrite_contracts/fixture_logic_sum.yaml": frame_contract("contract.fixture_logic_sum", clauses=[
            {"id": "pre", "role": "legality", "statement": "Inputs are in bounds.", "discharge_mode": "runtime_guard",
             "negative_control": {"id": "bad-n", "check": "bounds"}, "proof_placement": "per_candidate",
             "acsl": {"text": "requires n >= 0 && csr_offsets(parent, n);", "uses": ["logic.csr_graph", "logic.sum"]}}]),
    })
    return path, candidate


@pytest.fixture
def pins(pin_seed, tmp_path):
    source, candidate = pin_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return _Seed(tmp_path, candidate)


def _stale(level, rid):
    return [p for s in level["stale_proofs"] if s["record"] == rid for p in s["pins"]]


def test_a_proof_record_pins_each_logic_file_by_version_and_hash_and_an_edit_stops_it_counting(pins):
    first = pins.prove(pins.script(), "--contract", LOGIC_CONTRACT)["record"]
    access = pins.root / "library" / "logic" / "access.acsl"
    sha = __import__("hashlib").sha256(access.read_bytes()).hexdigest()
    assert first["pins"]["logic"] == [{"id": "logic.access", "version": "1.0", "sha256": sha}]
    assert _stale(pins.level(), first["id"]) == []

    access.write_text(access.read_text() + "// an edit: a new hash\n")
    stale = _stale(pins.level(), first["id"])
    assert [p["pin"] for p in stale] == ["logic"] and sha in stale[0]["reason"], stale

    second = pins.prove(pins.script(name="again"), "--contract", LOGIC_CONTRACT)["record"]
    assert second["pins"]["logic"][0]["sha256"] != sha
    level = pins.level()
    assert _stale(level, second["id"]) == [] and [p["pin"] for p in _stale(level, first["id"])] == ["logic"]


def test_a_proof_that_uses_a_file_with_lemmas_needs_a_counting_proof_of_those_lemmas(pins):
    record = pins.prove(pins.script(), "--contract", "contract.fixture_logic_sum")["record"]
    assert [p["id"] for p in record["pins"]["logic"]] == ["logic.csr_graph", "logic.sum"]
    stale = _stale(pins.level(), record["id"])
    assert len(stale) == 1 and stale[0]["pin"] == "logic" and "lemmas of logic.sum 1.0" in stale[0]["reason"], stale


def test_a_contract_without_logic_files_writes_no_logic_pin(pins):
    record = pins.prove(pins.script())["record"]
    assert "logic" not in record["pins"]


# --- C. swdb prove-logic with real WP -----------------------------------------------------------------------

def wp_store(root, logic_text=None):
    """records/ and a minimal library/ (logic files, a real-lineup method version) under `root`."""
    from swdb import c_lowering
    from test_wp_adapter import method_version
    records = make_records(root)
    records.path.mkdir(parents=True, exist_ok=True)
    library = minimal_library(root / "library")
    (library / "methods").mkdir()
    (library / "methods" / "wp-tracer-fixture.yaml").write_text(
        yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    if logic_text is not None:
        (library / "logic" / "sum.acsl").write_text(logic_text)
    return records


def prove_logic(records, root, *args, ok=True):
    result = records.swdb("prove-logic", "--runs-dir", root / "runs-outside-repo", "--format", "json", *args)
    assert (result.returncode == 0) is ok, result.stdout + result.stderr
    return json.loads(result.stdout)["record"] if ok else result


@pytest.fixture(scope="module")
def wp(tmp_path_factory):
    if not _tools_present():
        pytest.skip("Frama-C 33.0 or clang 22.1.8 is missing")
    root = tmp_path_factory.mktemp("logic-wp")
    return root, wp_store(root)


@needs_wp
def test_the_sum_library_lemmas_are_proven_in_wp_over_reals_and_recorded_as_a_method_part(wp):
    root, records = wp
    record = prove_logic(records, root, "--lemmas", "logic.sum")
    assert record["verdict"] == "proven", record.get("goals")
    assert record["subject"] == {"kind": "method_part", "id": "logic.sum", "part": "logic_lemmas"}
    assert len(record["goals"]) == SUM_LEMMAS and all(g["status"] == "valid" for g in record["goals"])
    for lemma in ("ADDITIVITY", "REGROUP_OWNER", "REGROUP_TOTAL", "PERMUTATION"):
        assert any(g["goal"].endswith(f"lemma_{lemma}") for g in record["goals"])
    assert "+real" in record["settings"]["flags"] and len(record["settings"]["scripts"]) == 11
    assert record["pins"]["logic"][0]["id"] == "logic.sum" and record["bounds"] == {"threads": "unbounded"}
    assert records.validate().returncode == 0


@needs_wp
@pytest.mark.parametrize("ident", SHARED)
def test_the_false_check_passes_on_every_shipped_file(wp, ident):
    root, records = wp
    record = prove_logic(records, root, "--false-check", ident)
    assert record["verdict"] == "proven", record
    assert record["subject"]["part"] == "logic_false_check"
    assert [g["status"] for g in record["goals"]] in (["timeout"], ["unknown"])


@needs_wp
def test_a_version_carrying_pbad_lets_wp_prove_false_and_is_refused_and_voids_its_pins(tmp_path):
    """Map 13's pbad in a proposed version 1.1 of logic.sum, run with the recursion check bypassed."""
    bad = tmp_path / "sum-1.1.acsl"
    bad.write_text((LOGIC / "sum.acsl").read_text().replace("// version: 1.0", "// version: 1.1") + PBAD)
    records = wp_store(tmp_path)
    refused = prove_logic(records, tmp_path, "--false-check", "logic.sum", "--file", bad, ok=False)
    assert "allowed-ACSL rules" in refused.stderr and not (records.path / "proofs").exists()   # 20's rule first
    refused = prove_logic(records, tmp_path, "--false-check", "logic.sum", "--file", bad, "--skip-subset-check",
                          ok=False)
    assert refused.returncode == 1 and "logic.sum 1.1 is refused" in refused.stderr
    [path] = (records.path / "proofs").glob("*.yaml")
    record = yaml.safe_load(path.read_text())
    assert record["verdict"] == "refuted" and record["counterexample"]["goal"].endswith("SWDB_FALSE_CHECK")
    assert record["subject"]["part"] == "logic_false_check" and record["pins"]["logic"][0]["version"] == "1.1"
    assert records.validate().returncode == 0
    # a proof that pins the refused version stops counting: the failed part voids it (the level rule)
    lemmas = prove_logic(records, tmp_path, "--lemmas", "logic.sum", "--file", bad, "--skip-subset-check")
    assert lemmas["verdict"] == "proven"                     # pbad is in no lemma's context
    from swdb.level_rule import Rule
    from swdb.store import Store
    stale = Rule(Store(records.path)).status(lemmas["id"])["stale"]
    assert ("logic", record["id"]) in [(p["pin"], p.get("failed")) for p in stale], stale


@needs_wp
@pytest.mark.parametrize("program", ["csr_pull_sum.c", "csr_pull_sum_flat.c"])
def test_the_csr_fixture_proves_through_the_sum_library_and_its_seeded_bug_does_not(wp, program):
    root, records = wp
    uses = ("--uses", "logic.csr_graph", "--uses", "logic.sum")
    record = prove_logic(records, root, "--program", FIXTURES / "logic" / program, *uses)
    assert record["verdict"] == "proven", record.get("unproven_properties")
    assert record["subject"] == {"kind": "calibration_program", "id": program}
    assert any(g["property"] and "UNIT" in g["property"] for g in record["goals"]) or \
        any("UNIT" in (g["goal"] or "") for g in record["goals"])
    assert not any("lemma" in (g["goal"] or "") for g in record["goals"])     # proven once, with the method
    bug = prove_logic(records, root, "--program", FIXTURES / "logic" / program, *uses, "--define", "SEEDED_BUG",
                      "--timeout", "10")             # a hard negative goal: a short solver budget (ticket 08, Z3)
    assert bug["verdict"] == "not_proven" and bug["failure_class"] in ("timeout", "unknown"), bug
    assert bug["pins"]["build_constants"] == [{"name": "SEEDED_BUG", "value": "1"}]

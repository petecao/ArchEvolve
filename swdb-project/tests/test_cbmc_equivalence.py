"""Whole-function equivalence: the bounded direct route and the no-contract baseline (CBMC on a product program).

Created: 2026-10-14 ET (Probata proof of concept ticket 61). Yan-Ru's 13:19 ET decision made CBMC 6.11 on the C
lowering the bounded verifier, so SAW lost this role; the main session (under Yan-Ru's delegation) chose CBMC on a
product program (self-composition) of the two functions' C lowerings, reusing ticket 22's harness. Design:
formal-verification map spec ("Proof routes" (bounded direct), "Bounds", "Evaluation design" (no contract));
decisions 17 item 4, 23 item 2, 24 items 1 and 3. Format: docs/reference/format-v0.4-cbmc.md ("Whole-function
equivalence").

Seam 1 (`swdb prove`), with `swdb validate` and `swdb candidate-level` reading the records. Fixture candidate
artifacts are GAPBS bfs.cc with ticket 22's fixture units inserted, `swdb_fixture_fill` varied per candidate:
the baseline (`base`), a split loop with the same outputs (`split`), the seeded early stop (`bug`), an extra write
to a location the baseline never writes (`extra`), and a loop that runs twice as long (`slow`). Cases that run CBMC
skip cleanly when CBMC 6.11 or clang 22.1.8 is missing; run them inside the machine-wide verifier lock.
"""

import json

import pytest
import yaml

from conftest import make_records, run_swdb
from test_cbmc_adapter import (ANCHOR_BEFORE, FILL, FILL_CLAUSES, TRUSTED, UNITS, _contract, _contracts, fake,
                               method_version, needs_cbmc)
from test_proof_records import _library_roots
from test_wp_adapter import _certify
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

REL = "contract.fixture_cbmc_fill_relational"
FUNCTION = "swdb_fixture_fill"
BOUNDS = {"threads": 1, "n": 3}
BASE_FILL = "void swdb_fixture_fill(int *a, int n, int v) {\n  for (int i = 0; i < n; ++i) {\n    a[i] = v;\n  }\n}"
VARIANTS = {
    "base": BASE_FILL,
    "split": "void swdb_fixture_fill(int *a, int n, int v) {\n  int h = n / 2;\n"
             "  for (int i = 0; i < h; ++i) a[i] = v;\n  for (int i = h; i < n; ++i) a[i] = v;\n}",
    "bug": BASE_FILL.replace("i < n;", "i < n - 1;"),
    "extra": BASE_FILL[:-1] + "  if (n == 1) a[1] = v;\n}",
    "global": BASE_FILL[:-1] + "  swdb_fixture_threshold = v;\n}",
    "slow": "void swdb_fixture_fill(int *a, int n, int v) {\n  if (n > 0) {\n"          # n > 0: no overflow in 2 * n
            "    for (int i = 0; i < 2 * n; ++i) a[i / 2] = v;\n  }\n}",
}
REASON = "Fixture: this unit's output relation is stated relationally (no unit postcondition)."


def build_equivalence_seed(path):
    """records/ and library/ under `path`; returns {variant: candidate ID}, each certified against REL."""
    import shutil

    from conftest import FIXTURES, REPO
    from swdb import c_lowering, cbmc_product
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    methods = path / "library" / "methods"
    methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    method = method_version(c_lowering.identity())
    method["c_lowering"]["translators"].append(cbmc_product.identity())        # the product-program generator
    (methods / "cbmc-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    (path / "library" / "proof_units").mkdir()
    (path / "library" / "proof_units" / "cbmc_fixture_units.cc").write_text(UNITS)
    contracts = _contracts()
    relational = _contract(REL, FUNCTION, FILL_CLAUSES, [{"array": "a", "shared_actions": [], "history_reads": False}])
    relational["relational_template"] = {"reason": REASON}
    contracts["fixture_cbmc_fill_relational"] = relational
    for name, data in contracts.items():
        (path / "library" / "rewrite_contracts" / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    candidates = {}
    for name, fill in VARIANTS.items():
        units = UNITS.replace(BASE_FILL, fill)
        assert name == "base" or units != UNITS
        submitted = records.swdb("submit", request(ANCHOR_BEFORE, units + "\n" + ANCHOR_BEFORE, id=f"equiv-{name}"),
                                 "--runs-dir", runs, "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        candidates[name] = json.loads(submitted.stdout)["candidate"]
        _certify(records.path, path, candidates[name], REL)
    return candidates


@pytest.fixture(scope="module")
def equivalence_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("equivalence-seed")
    return path, build_equivalence_seed(path)


class Seed:
    def __init__(self, root, candidates):
        self.root, self.candidates = root, candidates
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args, env=None):
        return run_swdb(command, "--records", self.records, *args, env={"SWDB_FRAMA_C": "none", **(env or {})})

    def prove(self, candidate, mode="bounded_direct", *extra, baseline="base", bounds=BOUNDS, contract=REL,
              function=FUNCTION, env=None, ok=True):
        args = ["--candidate", self.candidates[candidate], "--function", function, "--adapter", "cbmc",
                "--whole-function", mode, "--runs-dir", self.runs, "--format", "json"]
        if baseline:
            args += ["--baseline-candidate", self.candidates[baseline]]
        if contract and mode == "bounded_direct":
            args += ["--contract", contract]
        if bounds is not None:
            args += ["--bounds", json.dumps(bounds)]
        result = self.swdb("prove", *args, *extra, env=env)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return yaml.safe_load((self.records / json.loads(result.stdout)["path"]).read_text()) if ok else result

    def level(self, candidate):
        result = self.swdb("candidate-level", self.candidates[candidate], "--format", "json")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def report(self, record, name):
        return next(r["path"] for r in record["evidence"]["reports"] if r["name"] == name)


@pytest.fixture
def seed(equivalence_seed, tmp_path):
    import shutil
    source, candidates = equivalence_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


# --- equal and unequal pairs ------------------------------------------------------------------------------------

@needs_cbmc
def test_an_equal_pair_proves_within_bounds_at_one_thread_on_the_bounded_direct_route(seed):
    record = seed.prove("split", "bounded_direct", "--define", "SWDB_FIXTURE_UNUSED=7")
    assert record["verdict"] == "proven" and record["route"] == "bounded_direct"
    assert record["bounds"] == BOUNDS and record["evidence_kind"] == "contract_fixture"
    pins = record["pins"]
    assert pins["code"]["id"] == seed.candidates["split"]                       # both functions' code is pinned
    assert pins["baseline_function"]["id"] == seed.candidates["base"] and pins["baseline_function"]["function"] == FUNCTION
    assert pins["c_lowering"]["id"] == f"{FUNCTION}.c" and pins["baseline_c_lowering"]["id"] == f"{FUNCTION}.c"
    assert pins["c_lowering"]["sha256"] != pins["baseline_c_lowering"]["sha256"]
    assert pins["build_constants"] == [{"name": "SWDB_FIXTURE_UNUSED", "value": "7"}]
    settings = record["settings"]
    assert settings["build_constants_by_build"] == {"candidate": pins["build_constants"],
                                                    "baseline": pins["build_constants"]}
    assert settings["whole_function"] == "bounded_direct" and settings["unwind"] == 4
    assert settings["compared"] == ["a[0]", "a[1]", "a[2]"]          # fill names no global: none to compare
    assert settings["formal_halves"] == [f"{REL}#fill_pre", f"{REL}#fill_post.assigns1", f"{REL}#fill_post.ensures1"]
    assert settings["agreement"]["verdict"] == "agree" and settings["agreement"]["domain"]["n"]["values"] == [-1, 0, 1, 2, 3]
    assert settings["bounds_origin"] == {"kind": "passed"}
    assert set(record["tools"]) == TRUSTED | {"swdb-cbmc-product-1"}
    job_c = open(seed.report(record, "cbmc_input")).read()
    assert "swdb_next()" in job_c and "swdb_base_swdb_fixture_fill(" in job_c       # symbolic inputs, both copies
    assert all(g["status"] == "success" for g in record["goals"] if g["property"].startswith("swdb_equal."))
    assert seed.swdb("validate").returncode == 0
    assert seed.level("split")["level"] == "proven_within_bounds_threads_1"   # counts like any bounded record


@needs_cbmc
def test_an_unequal_pair_is_refuted_with_inputs_the_first_differing_location_and_both_values(seed):
    record = seed.prove("bug", "no_contract_baseline")
    assert record["verdict"] == "refuted"
    example = record["counterexample"]
    assert example["property"].startswith("swdb_equal.a[") and example["replay"]["replayed"] is True
    inputs = example["inputs"]
    assert 1 <= inputs["n"] <= 3 and len(inputs["a"]) == 3
    first = example["first_difference"]
    assert first["location"] == f"a[{inputs['n'] - 1}]"                       # the element the bug skips
    assert first["baseline"] == inputs["v"] and first["candidate"] == inputs["a"][inputs["n"] - 1] != inputs["v"]


@needs_cbmc
def test_a_rewrite_that_also_writes_a_location_the_baseline_never_writes_is_refuted(seed):
    record = seed.prove("extra", "no_contract_baseline")
    assert record["verdict"] == "refuted"
    example = record["counterexample"]
    assert example["inputs"]["n"] == 1 and example["first_difference"]["location"] == "a[1]"
    assert example["first_difference"]["candidate"] == example["inputs"]["v"] != example["inputs"]["a"][1]
    record = seed.prove("global", "no_contract_baseline")         # a global only the candidate's code writes
    assert record["verdict"] == "refuted" and record["settings"]["compared"][-1] == "swdb_fixture_threshold"
    first = record["counterexample"]["first_difference"]
    assert first["location"] == "swdb_fixture_threshold" and first["baseline"] == 4
    assert first["candidate"] == record["counterexample"]["inputs"]["v"] != 4


# --- route guard, cap, bounds -----------------------------------------------------------------------------------

def test_the_bounded_direct_route_is_refused_for_a_unit_with_a_unit_postcondition(seed):
    result = seed.prove("split", "bounded_direct", contract=FILL, ok=False)
    assert "bounded direct route" in result.stderr and "unit postcondition" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


def _scripted(seed, candidate, bounds):
    script = seed.root / "script.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": bounds}))
    result = seed.swdb("prove", "--candidate", seed.candidates[candidate], "--function", FUNCTION, "--contract", REL,
                       "--adapter", "scripted", "--script", script, "--runs-dir", seed.runs, "--format", "json")
    assert result.returncode == 0, result.stderr
    return seed.records / json.loads(result.stdout)["path"]


@pytest.mark.parametrize("bounds", [{"threads": 2, "n": 3}, {"threads": 1, "n": "unbounded"}])
def test_a_bounded_direct_record_above_one_thread_or_unbounded_is_refused_and_never_read_above(seed, bounds):
    from swdb import level_rule
    from swdb.store import Store
    path = _scripted(seed, "split", bounds)
    data = yaml.safe_load(path.read_text())
    assert seed.swdb("validate").returncode == 0
    assert level_rule.candidate_level(Store(seed.records), seed.candidates["split"])["level"] != "certified"
    data["route"] = "bounded_direct"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    refused = seed.swdb("validate")
    assert refused.returncode != 0 and "bounded_direct" in refused.stdout + refused.stderr
    assert seed.swdb("candidate-level", seed.candidates["split"]).returncode != 0      # an invalid store is not read
    assert level_rule.candidate_level(Store(seed.records), seed.candidates["split"])["level"] == "certified"


def _minimum(seed, bounds, contract=REL):
    """A minimum-bounds derivation record of `contract` (fixture YAML, as ticket 10's tests write them)."""
    from swdb.library import Library
    path = _scripted(seed, "base", {"threads": 1, "n": 3})
    data = yaml.safe_load(path.read_text())
    path.unlink()
    content = {"id": contract, "sha256": Library(seed.root / "library").content_sha256(contract)}
    na = {"not_applicable": "A minimum-bounds derivation is about the contract."}
    data.update(id="proof.t61.minimum", bounds=bounds,
                subject={"kind": "contract_proof_part", "id": contract, "part": "minimum_bounds_derivation"})
    data["pins"].update(code=content, contract=content, baseline_function=na)
    data["job"] = dict(data["job"], batch="batch.proof.t61.minimum")
    (seed.records / "proofs" / "proof.t61.minimum.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    return "proof.t61.minimum"


@needs_cbmc
def test_the_bounded_direct_route_runs_at_the_contracts_minimum_bounds_and_below_them_gives_no_level(seed):
    minimum = _minimum(seed, {"threads": 1, "n": 3})
    at = seed.prove("split", "bounded_direct", "--minimum-bounds", minimum, bounds=None)
    assert at["verdict"] == "proven" and at["bounds"] == {"threads": 1, "n": 3}
    assert at["settings"]["bounds_origin"] == {"kind": "minimum_bounds", "record": minimum}
    assert seed.level("split")["level"] == "proven_within_bounds_threads_1"
    for path in (seed.records / "proofs").glob("proof.equiv-split*.yaml"):
        path.unlink()
    below = seed.prove("split", "bounded_direct", "--minimum-bounds", minimum, bounds={"threads": 1, "n": 2})
    assert below["verdict"] == "proven"
    level = seed.level("split")
    assert level["level"] == "certified" and level["below_minimum"][0]["dimensions"] == ["n"]


@needs_cbmc
def test_the_no_contract_baseline_borrows_labeled_bounds_and_never_counts_toward_a_level(seed):
    minimum = _minimum(seed, {"threads": 1, "n": 2})
    record = seed.prove("split", "no_contract_baseline", "--borrowed-bounds", minimum, bounds=None)
    assert record["verdict"] == "proven" and record["route"] == "bounded_direct"
    assert record["bounds"] == {"threads": 1, "n": 2}
    assert record["settings"]["bounds_origin"] == {"kind": "borrowed", "record": minimum, "contract": REL}
    assert "not_applicable" in record["pins"]["contract"] and "not_applicable" in record["pins"]["minimum_bounds"]
    assert seed.swdb("validate").returncode == 0
    level = seed.level("split")                                    # certified fixture; its only record: a measurement
    assert level["level"] == "certified" and level["direct_proofs"] == []
    assert [m["record"] for m in level["baseline_measurements"]] == [record["id"]]
    refuted = seed.prove("extra", "no_contract_baseline")
    assert refuted["verdict"] == "refuted"
    extra = seed.level("extra")
    assert extra["level"] == "certified" and extra["refuted"]["flag"] is False


# --- both forms, the subset, unwinding ---------------------------------------------------------------------------

@needs_cbmc
def test_a_planted_c_lowering_disagreement_stops_the_batch_and_records_nothing(seed):
    fault = seed.root / "fault.yaml"
    fault.write_text(yaml.safe_dump({"replace": [["for (int i = 0; i < n; ++i)", "for (int i = 0; i < n - 1; ++i)"]]}))
    result = seed.prove("split", "bounded_direct", env={"SWDB_CBMC_LOWERING_FAULT": str(fault)}, ok=False)
    assert "c_lowering_disagreement" in result.stderr and "baseline" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


@needs_cbmc
def test_a_function_outside_the_cpp_subset_is_not_proven_and_the_record_says_why(seed):
    record = seed.prove("split", "no_contract_baseline", baseline=None, function="InitParent", bounds={"threads": 1})
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert record["settings"]["outside_cpp_subset"].startswith("outside the C++ subset (candidate)")
    assert record["pins"]["baseline_function"]["function"] == "InitParent"   # default baseline: the source snapshot
    assert "forms" not in record["settings"]


@needs_cbmc
def test_loops_with_different_trip_counts_unwind_each_copy_to_its_own_bound(seed):
    short = seed.prove("slow", "no_contract_baseline")
    assert short["verdict"] == "not_proven" and short["failure_class"] == "unwinding_bound_too_small"
    record = seed.prove("slow", "no_contract_baseline", "--unwindset", f"candidate:{FUNCTION}.0=7")
    assert record["verdict"] == "proven"
    assert record["settings"]["unwindset"] == [f"{FUNCTION}.0:7"]


@needs_cbmc
def test_a_method_version_that_does_not_list_the_product_generator_runs_no_whole_function_job(seed):
    path = seed.root / "library" / "methods" / "cbmc-fixture.yaml"
    data = yaml.safe_load(path.read_text())
    data["c_lowering"]["translators"] = [t for t in data["c_lowering"]["translators"]
                                         if not t["id"].startswith("swdb-cbmc-product")]
    data.update(id="method.cbmc-no-product", sequence=3)
    (path.parent / "cbmc-no-product.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    result = seed.prove("split", "bounded_direct", ok=False)
    assert "swdb-cbmc-product-1" in result.stderr and "method.cbmc-no-product" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


# --- budget and failures -------------------------------------------------------------------------------------------

@needs_cbmc
def test_a_job_over_its_budget_is_timeout_at_unchanged_bounds(seed):
    record = seed.prove("split", "bounded_direct", "--budget-minutes", "0.02", env=fake("sleep"))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "timeout" and record["bounds"] == BOUNDS


@needs_cbmc
def test_an_outcome_with_no_class_stops_the_batch(seed):
    result = seed.prove("split", "bounded_direct", env=fake("silent"), ok=False)
    assert "unclassified_cbmc_outcome" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))

"""Ticket 24's construct groups through `swdb prove --adapter wp`: each safe fixture proves, its seeded bug does not;
each C model and each summary is proven once by its own record, and a unit's record pins them.

Created: 2026-10-14 ET. Updated: 2026-10-15 ET (ticket 24: fail closed on unsupported deallocation lifetimes).
Design: formal-verification map 16 item 6 (the C++
subset), 11 items 3 and 9; format docs/reference/format-v0.4-c-lowering-wp.md.

Seam 1 (`swdb prove`). The candidate artifacts are GAPBS bfs.cc with every construct-group fixture of
tests/fixtures/proof/lowering/ inserted (one safe, one with every group's seeded bug), built through the public
workflow. Each group has a fixture rewrite contract (per-candidate formal halves) and fixture hints at anchors;
the summary entries prove `once: self` formal halves on summary_impls.cc. Cases run real Frama-C/WP and skip
cleanly without Frama-C 33.0 or clang 22.1.8; run pytest outside the verifier lock (each `swdb prove` takes it
per job) with the sandbox off (Why3 needs its socket).
"""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_proof_records import _library_roots
from test_wp_adapter import ANCHOR_BEFORE, _hints, method_version
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

LOWERING = FIXTURES / "proof" / "lowering"
GROUP_FILES = ("classes.cc", "templates.cc", "new_array.cc", "std_models.cc", "omp_atomics.cc", "floats.cc",
               "summaries.cc", "summary_impls.cc", "terminal_release_controls.cc")
UNITS = "\n".join((LOWERING / name).read_text() for name in GROUP_FILES)
IMPLS = (LOWERING / "summary_impls.cc").read_text()
SEEDED_BUGS = (
    ("for (int i = 0; i < n; ++i) data[i] *= k;", "for (int i = 0; i < n; ++i) data[i] *= k + 1;"),   # classes
    ("return r.get(1) + (int)q.get(0)", "return r.get(0) + (int)q.get(0)"),                          # templates
    ("for (int i = 0; i < n; ++i) buf[i] = k;", "for (int i = 0; i <= n; ++i) buf[i] = k;"),         # new[]
    ("std::copy(a, a + n, b);", "std::copy(a, a + n - 1, b);"),                                     # std models
    ("int sum = 0, hits = 0, maxv = 0;", "int sum = 0, hits = 0, maxv = 1;"),                        # OpenMP
    ("__sync_add_and_fetch(p, 3)", "__sync_add_and_fetch(p, 4)"),                                   # atomics
    ("r.value = 0.0;", "r.value = 1.0;"),                                                           # floats
    ("return __dxc_tile_size(tile) + 1;", "return __dxc_tile_size(tile) + 2;"),                     # __dxc_*
    ("  return n;\n}", "  return n + 1;\n}"),                                                       # maa_*
)
def _bounded(array, n, low, high):
    """`array[0 .. n-1]` valid with every element in [low, high] (the formal-half ACSL subset has no valid_read)."""
    return (f"requires \\valid({array} + (0 .. {n} - 1));\n"
            f"requires \\forall integer j; 0 <= j < {n} ==> {low} <= {array}[j] <= {high};")


# group: (unit function, [(clause id, role, ACSL)], interface arrays, hints [(anchor, ACSL)])
GROUPS = {
    "classes": ("swdb_class_unit", [
        ("pre", "legality", "requires 0 <= n <= 4;\n" + _bounded("a", "n", -100, 100)),
        ("post", "postcondition",
         "assigns a[0 .. n-1];\n"
         "ensures mode != 2 ==> \\forall integer j; 0 <= j < n ==> a[j] == \\old(a[j]);\n"
         "ensures mode == 2 ==> \\forall integer j; 0 <= j < n ==> a[j] == 3 * \\old(a[j]);")], ["a"], [
        ("swdb_class_unit.loop1.head",
         "loop invariant 0 <= i <= n;\nloop invariant -100 * i <= counter.count_ <= 100 * i;\n"
         "loop invariant bag.data == a && bag.n == n && counter.total_ == &total;\n"
         "loop assigns i, counter.count_;\nloop variant n - i;"),
        ("Bag_scale.loop1.head",
         "loop invariant 0 <= i <= this->n;\n"
         "loop invariant \\forall integer j; 0 <= j < i ==> this->data[j] == k * \\at(this->data[j], LoopEntry);\n"
         "loop invariant \\forall integer j; i <= j < this->n ==> this->data[j] == \\at(this->data[j], LoopEntry);\n"
         "loop assigns i, this->data[0 .. this->n - 1];\nloop variant this->n - i;"),
        ("swdb_class_sum.loop1.head",
         "loop invariant 0 <= i <= b->n && b->n <= 4;\nloop invariant -300 * i <= s <= 300 * i;\n"
         "loop invariant \\forall integer j; 0 <= j < b->n ==> -300 <= b->data[j] <= 300;\n"
         "loop assigns i, s;\nloop variant b->n - i;")]),
    "templates": ("swdb_template_unit", [
        ("pre", "legality", "requires -1000 <= a <= 1000 && -1000 <= b <= 1000;"),
        ("post", "postcondition", "assigns \\nothing;\nensures \\result == 2 * (a + 1) + 4 * b;")], [], []),
    "std_models": ("swdb_std_unit", [
        ("pre", "legality",
         "requires 0 <= n <= 4 && -1000 <= x <= 1000 && -1000 <= y <= 1000;\n" + _bounded("a", "n", -1000, 1000) +
         "\nrequires \\valid(b + (0 .. n - 1)) && \\separated(a + (0 .. n - 1), b + (0 .. n - 1));"),
        ("post", "postcondition",
         "assigns b[0 .. n-1];\nensures \\forall integer j; 0 <= j < n ==> b[j] == \\old(a[j]);\n"
         "ensures n == 0 ==> \\result == (x < y ? y : x) - (y < x ? y : x) + ((x < y ? y : x) < 7 ? 7 : "
         "(x < y ? y : x));")], ["a", "b"], []),
    "omp": ("swdb_omp_unit", [
        ("pre", "legality", "requires 0 <= n <= 100;\n" + _bounded("a", "n", -100, 100)),
        ("post", "postcondition", "assigns \\nothing;\nensures n == 0 ==> \\result == 0;")], ["a"], [
        ("swdb_omp_unit.loop1.head",
         "loop invariant 0 <= i <= n;\nloop invariant -100 * i <= sum <= 100 * i;\n"
         "loop assigns i, sum;\nloop variant n - i;"),
        ("swdb_omp_unit.loop2.head",
         "loop invariant 0 <= i <= n;\nloop invariant 0 <= hits <= i;\nloop invariant 0 <= maxv <= 100;\n"
         "loop invariant n == 0 ==> maxv == 0;\nloop assigns i, hits, maxv;\nloop variant n - i;")]),
    "atomics": ("swdb_atomics_unit", [
        ("pre", "legality", "requires \\valid(p) && \\valid(e) && \\separated(p, e);\n"
                            "requires -100 <= *p <= 100 && -100 <= *e <= 100 && -100 <= v <= 100;"),
        ("post", "postcondition",
         "assigns *p, *e;\nensures \\old(*p) + v == \\old(*e) ==> *p == 10;\n"
         "ensures \\old(*p) + v != \\old(*e) ==> *e == \\old(*p) + v;")], ["p", "e"], []),
    "floats": ("swdb_float_unit", [
        ("pre", "legality", "requires 0 <= n <= 4 && -10.0 <= scale <= 10.0;\n" + _bounded("a", "n", "-100.0", "100.0")),
        ("post", "postcondition", "assigns \\nothing;\nensures n == 0 ==> \\result == 0.0;")], ["a"], [
        ("swdb_float_unit.loop1.head",
         "loop invariant 0 <= i <= n;\nloop invariant -1000.0 * i <= r.value <= 1000.0 * i;\n"
         "loop invariant -5.0 <= r.weight <= 5.0;\nloop assigns i, r.value;\nloop variant n - i;")]),
    "dxc_summary": ("swdb_dxc_unit", [
        ("pre", "legality", "requires 0 <= tile < 8;"),
        ("post", "postcondition", "assigns \\nothing;\nensures 1 <= \\result <= 3;")], [], []),
    "maa_summary": ("swdb_maa_unit", [
        ("pre", "legality", "requires \\valid(base);"),
        ("post", "postcondition", "assigns \\nothing;\nensures \\result == n;")], ["base"], []),
    "new_array": ("swdb_new_unit", [
        ("pre", "legality", "requires 1 <= n <= 100 && -100 <= k <= 100;"),
        # no assigns clause: WP 33 sees the new[] buffer as caller memory (it has no \\fresh)
        ("post", "postcondition", "ensures \\result == k * n;")], [], [
        ("swdb_new_unit.loop1.head",
         "loop invariant 0 <= i <= n;\nloop invariant \\forall integer j; 0 <= j < i ==> buf[j] == k;\n"
         "loop invariant \\initialized(&buf);\nloop invariant \\initialized(buf + (0 .. i - 1));\n"
         "loop assigns i, buf[0 .. n - 1];\nloop variant n - i;"),
        ("swdb_new_unit.loop2.head",
         "loop invariant 0 <= i <= n;\nloop invariant s == k * i;\nloop assigns i, s;\nloop variant n - i;")]),
}
BUG_UNITS = {   # new_array.cc's two seeded-bug functions, each with its own contract (proven on the safe candidate)
    "new_out_of_range": ("swdb_new_out_of_range", [
        ("pre", "legality", "requires 1 <= n <= 100;"), ("post", "postcondition", "ensures \\result == 0;")], [], []),
    "new_after_delete": ("swdb_new_after_delete", [
        ("pre", "legality", "requires 1 <= n <= 100;"), ("post", "postcondition", "ensures \\result == n;")], [], []),
}
TERMINAL_CONTROLS = (
    "escape_owner_address", "alias_write", "escape_scalar_address", "conditional_delete", "double_delete",
    "later_callback", "ignored_uninitialized_read", "reassigned_owner",
)
for _control in TERMINAL_CONTROLS:
    BUG_UNITS[f"new_{_control}"] = (f"swdb_new_{_control}", [
        ("pre", "legality", "requires 1 <= n <= 100;"),
        ("post", "postcondition", "ensures \\result == n;")], [], [])
SUMMARIES = {   # entry: (function, [(clause id, role, ACSL)], interface arrays)
    "dxc_tile_size": ("__dxc_tile_size", [
        ("pre", "legality", "requires 0 <= tile < 8;"),
        ("post", "postcondition", "assigns \\nothing;\nensures 0 <= \\result <= 2;")], []),
    "maa_const": ("maa_const_i32", [("post", "postcondition", "assigns \\nothing;")], []),
    "maa_indirect_load": ("maa_indirect_load_i32", [
        ("pre", "legality", "requires \\valid(base);"),
        ("post", "postcondition", "assigns \\nothing;")], ["base"]),
}
MODELS = {  # the C models each group's lowering calls
    "std_models": ["std_min_int", "std_max_int", "std_swap_int", "std_copy_int", "std_max_long"],
    "atomics": ["swdb_atomic_load_n_int", "swdb_atomic_store_n_int", "swdb_atomic_fetch_add_int",
                "swdb_atomic_exchange_n_int", "swdb_atomic_compare_exchange_n_int",
                "swdb_sync_bool_compare_and_swap_int", "swdb_sync_val_compare_and_swap_int",
                "swdb_sync_fetch_and_add_int", "swdb_sync_add_and_fetch_int"],
}


def _tools_present():
    from swdb import c_lowering, framac
    return not framac.locate().missing and not c_lowering.locate().missing


needs_wp = pytest.mark.skipif(not _tools_present(), reason="Frama-C 33.0 or clang 22.1.8 is missing")


def _entry(cid, function, source, text, clauses, arrays, placement):
    unit = {"root": "library", "path": f"proof_units/{source}", "sha256": hashlib.sha256(text.encode()).hexdigest()}
    return {
        "kind": "rewrite_contract", "id": cid, "formal_frame": 1, "version": "1.0",
        "provenance": {"origin": {"intrinsic_specification": "fixture-24"}},
        "proof_unit": {"source": unit, "function": function},
        "concurrency_frame": [{"array": a, "shared_actions": [], "history_reads": False} for a in arrays],
        "clauses": [{"id": name, "role": role, "statement": f"Fixture clause {name}.", "discharge_mode": "runtime_guard",
                     "negative_control": {"id": f"{name}-control", "check": name},
                     "acsl": {"text": acsl, "uses": []}, "proof_placement": placement}
                    for name, role, acsl in clauses],
        "pattern_key": [{"roles": ["index", "target"], "address_shapes": ["stream", "single_valued_indirect"],
                         "update_kind": "read"}],
        "strategies": [], "uses_intrinsics": [], "uses_library_operations": [], "runtime_guards": [], "knobs": [],
        "preservation_obligations": [], "correctness_check": {"kernel": "fixture", "check": "fixture"},
        "execution_witness": {"check": "fixture"},
        "negative_controls": [{"id": kind, "kind": kind, "check": "fixture"}
                              for kind in ("overlapping_pointer", "double_claim", "dropped_operand")],
        "requirement_map": []}


def contract_id(group):
    return f"contract.fixture_wp24_{group}"


def summary_id(name):
    return f"contract.fixture_wp24_summary_{name}"


def build_subset_seed(path):
    """records/ and library/ under `path`; returns {safe, bug} candidate artifact IDs."""
    from swdb import c_lowering
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    methods = path / "library" / "methods"
    methods.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    (methods / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
    units = path / "library" / "proof_units"
    units.mkdir()
    (units / "subset_units.cc").write_text(UNITS)
    (units / "summaries").mkdir()                                  # its own folder: one file defines each function
    (units / "summaries" / "summary_impls.cc").write_text(IMPLS)
    contracts = path / "library" / "rewrite_contracts"
    for group, (function, clauses, arrays, _unused) in {**GROUPS, **BUG_UNITS}.items():
        data = _entry(contract_id(group), function, "subset_units.cc", UNITS, clauses, arrays, "per_candidate")
        contracts.joinpath(f"fixture_wp24_{group}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    for name, (function, clauses, arrays) in SUMMARIES.items():
        data = _entry(summary_id(name), function, "summaries/summary_impls.cc", IMPLS, clauses, arrays, {"once": "self"})
        contracts.joinpath(f"fixture_wp24_summary_{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    candidates = {}
    bug = UNITS
    for before, after in SEEDED_BUGS:
        assert before in bug, before
        bug = bug.replace(before, after, 1)
    for name, units_text in (("safe", UNITS), ("bug", bug)):
        submitted = records.swdb("submit", request(ANCHOR_BEFORE, units_text + "\n" + ANCHOR_BEFORE, id=f"wp24-{name}"),
                                 "--runs-dir", runs, "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        candidates[name] = json.loads(submitted.stdout)["candidate"]
    return candidates


class Seed:
    def __init__(self, root, candidates):
        self.root, self.candidates = root, candidates
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args):
        return run_swdb(command, "--records", self.records, *args)

    def prove(self, *args, ok=True):
        result = self.swdb("prove", "--adapter", "wp", "--runs-dir", self.runs, "--format", "json", *args)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return yaml.safe_load((self.records / json.loads(result.stdout)["path"]).read_text()) if ok else result

    def unit(self, group, candidate="safe", function=None, ok=True):
        name, _clauses, _arrays, hints = {**GROUPS, **BUG_UNITS}[group]
        path = self.root / f"hints-{group}.yaml"
        records = [h for a, text in hints for h in _hints(a, *text.splitlines())]       # ticket 35's hint records
        path.write_text(yaml.safe_dump({"hints": records}))
        return self.prove("--candidate", self.candidates[candidate], "--function", function or name,
                          "--contract", contract_id(group), "--hint-file", path, ok=ok)


@pytest.fixture(scope="module")
def subset(tmp_path_factory):
    """The seed with every C model and summary the groups use proven once (their records stay in the store)."""
    if not _tools_present():
        pytest.skip("Frama-C 33.0 or clang 22.1.8 is missing")
    path = tmp_path_factory.mktemp("wp24-seed")
    seed = Seed(path, build_subset_seed(path))
    seed.models = {name: seed.prove("--model", name) for names in MODELS.values() for name in names}
    seed.summaries = {name: seed.prove("--summary", summary_id(name)) for name in SUMMARIES}
    return seed


@needs_wp
def test_each_c_model_is_proven_once_by_its_own_record_about_its_text(subset):
    from swdb import c_lowering
    for name, record in subset.models.items():
        assert record["subject"] == {"kind": "c_model", "id": name}
        assert record["verdict"] == "proven", (name, record.get("unproven_properties"))
        sha = hashlib.sha256(c_lowering.model_text(name).encode()).hexdigest()
        assert record["pins"]["code"] == {"id": name, "sha256": sha}


@needs_wp
def test_each_fixture_summary_is_proven_once_on_its_stand_in_code(subset):
    for name, record in subset.summaries.items():
        assert record["subject"] == {"kind": "library_summary", "id": summary_id(name)}
        assert record["verdict"] == "proven", (name, record.get("unproven_properties"))


@needs_wp
@pytest.mark.parametrize("group", sorted(set(GROUPS) - {"new_array"}))
def test_each_construct_group_safe_fixture_proves_and_its_seeded_bug_does_not(subset, group):
    safe = subset.unit(group)
    assert safe["verdict"] == "proven", (group, safe.get("failure_class"), safe.get("unproven_properties"))
    assert safe["bounds"] == {"threads": 1, "input_size": "unbounded"}
    assert safe["pins"]["naming_rules"]["id"] == "kept-names.3"
    bug = subset.unit(group, candidate="bug")
    assert bug["verdict"] == "not_proven" and "counterexample" not in bug


@needs_wp
@pytest.mark.parametrize("group", sorted(MODELS))
def test_a_unit_that_calls_c_models_pins_each_models_proof_record(subset, group):
    record = subset.unit(group)
    pinned = {p["id"]: p for p in record["pins"]["models"]}
    assert set(pinned) == set(MODELS[group])
    for name, pin in pinned.items():
        assert pin["proof_record"] == subset.models[name]["id"]
        assert pin["sha256"] == subset.models[name]["pins"]["code"]["sha256"]


@needs_wp
@pytest.mark.parametrize("group, entries", [("dxc_summary", ["dxc_tile_size"]),
                                            ("maa_summary", ["maa_const", "maa_indirect_load"])])
def test_a_unit_that_calls_summarized_functions_pins_each_summary_record(subset, group, entries):
    record = subset.unit(group)
    pinned = {p["id"]: p for p in record["pins"]["summaries"]}
    assert set(pinned) == {summary_id(e) for e in entries}
    for entry in entries:
        assert pinned[summary_id(entry)]["proof_record"] == subset.summaries[entry]["id"]


@pytest.fixture(scope="module")
def allocation_subset(tmp_path_factory):
    """Allocation refusal needs no unrelated once-proven std/atomic models or summaries."""
    if not _tools_present():
        pytest.skip("Frama-C 33.0 or clang 22.1.8 is missing")
    path = tmp_path_factory.mktemp("wp24-lifetime-seed")
    return Seed(path, build_subset_seed(path))


@needs_wp
@pytest.mark.parametrize("group", ["new_after_delete", *[f"new_{name}" for name in TERMINAL_CONTROLS]])
def test_wp_refuses_uncertified_deallocation_aliases_escapes_and_later_effects(allocation_subset, group):
    record = allocation_subset.unit(group)
    assert record["verdict"] == "not_proven"
    assert record["failure_class"] == "unsupported_construct"
    assert record["goals"] == []
    assert not any(report["name"] == "wp_input" for report in record.get("evidence", {}).get("reports", []))
    assert any(a["sentence"].startswith("Allocation succeeds") for a in record["assumptions"])


@needs_wp
def test_checked_terminal_delete_allows_the_initialized_nonescaping_array_unit_to_prove(allocation_subset):
    record = allocation_subset.unit("new_array")
    assert record["verdict"] == "proven", record.get("unproven_properties")
    assert record["pins"]["terminal_release_check"]["id"] == "terminal-release-check-2"
    assert record["pins"]["terminal_release_certificate"]["id"] == "swdb_new_unit.terminal-release"
    certificate = record["settings"]["terminal_release"]["certificate"]
    assert certificate["owner"] == "buf" and certificate["initialization"] == "canonical complete fill before every array read"
    paths = {r["name"]: r["path"] for r in record["evidence"]["reports"]}
    original = Path(paths["c_lowering"]).read_text()
    view = Path(paths["terminal_release_view"]).read_text()
    assert "swdb_alloc_delete_array_int(buf);" in original
    assert "swdb_alloc_delete_array_int(buf);" not in view and "assert n >= 0" in view
    assert "swdb_alloc_new_array_int((size_t)(n)) + 0;" in view
    assert "swdb_alloc_new_array_int((size_t)(n)) + 0;" not in original
    assert len(original.splitlines()) == len(view.splitlines())


@needs_wp
@pytest.mark.parametrize("candidate,group", [("safe", "new_out_of_range"), ("bug", "new_array")])
def test_out_of_range_array_access_never_gains_a_terminal_release_proof(allocation_subset, candidate, group):
    record = allocation_subset.unit(group, candidate=candidate)
    assert record["verdict"] == "not_proven"


@needs_wp
def test_a_unit_whose_c_model_has_no_proven_record_runs_nothing(subset, tmp_path):
    fresh = Seed(tmp_path, subset.candidates)
    for name in ("records", "library"):
        shutil.copytree(subset.root / name, tmp_path / name)
    for path in (tmp_path / "records").rglob("*.yaml"):         # model records and the unit records that pin them
        text = path.read_text()
        if "kind: proof" in text and ("c_model" in text or "models:" in text):
            path.unlink()
    result = fresh.unit("std_models", ok=False)
    assert "has no proven record at its current text: run `swdb prove --model std_min_int --adapter wp` first" \
        in result.stderr


@needs_wp
@pytest.mark.parametrize("annotation", ["heap_postcondition", "ghost_hint"])
def test_terminal_release_proof_refuses_heap_observation_and_ghost_effects(allocation_subset, annotation):
    contract = allocation_subset.root / "library" / "rewrite_contracts" / "fixture_wp24_new_array.yaml"
    original = contract.read_text()
    hint_file = allocation_subset.root / f"terminal-release-{annotation}.yaml"
    hints = [h for anchor, text in GROUPS["new_array"][3] for h in _hints(anchor, *text.splitlines())]
    try:
        if annotation == "heap_postcondition":
            data = yaml.safe_load(original)
            data["clauses"][-1]["acsl"]["text"] = "ensures \\valid(&n);"
            contract.write_text(yaml.safe_dump(data, sort_keys=False))
        else:
            hints.append({"anchor": "ghost.globals", "kind": "ghost_declaration", "text": "ghost int observed = 0;",
                          "provenance": {"source": "human"}})
        hint_file.write_text(yaml.safe_dump({"hints": hints}, sort_keys=False))
        record = allocation_subset.prove("--candidate", allocation_subset.candidates["safe"], "--function",
                                         "swdb_new_unit", "--contract", contract_id("new_array"), "--hint-file", hint_file)
        assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
        assert not any(report["name"] == "wp_input" for report in record.get("evidence", {}).get("reports", []))
    finally:
        contract.write_text(original)


@pytest.fixture(scope="module")
def summary_dependency_seed(tmp_path_factory):
    """One real summary proof; mutations exercise public dependency admission before another verifier starts."""
    if not _tools_present():
        pytest.skip("Frama-C 33.0 or clang 22.1.8 is missing")
    path = tmp_path_factory.mktemp("wp-summary-dependency")
    seed = Seed(path, build_subset_seed(path))
    record = seed.prove("--summary", summary_id("dxc_tile_size"))
    assert record["verdict"] == "proven", record
    return path, seed.candidates, record["id"]


@needs_wp
@pytest.mark.parametrize("mutation", ["current", "method", "evidence", "adapter", "setup", "reading", "bounded", "model"])
def test_summary_dependency_requires_current_method_counting_execution_boundary_and_transitive_models(
        summary_dependency_seed, tmp_path, mutation):
    source, candidates, rid = summary_dependency_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    seed = Seed(tmp_path, candidates)
    path = seed.records / "proofs" / f"{rid}.yaml"
    record = yaml.safe_load(path.read_text())
    if mutation == "method":
        old = seed.root / "library" / "methods" / "contract-fixture-1.yaml"
        record["pins"]["method_version"] = {"id": yaml.safe_load(old.read_text())["id"],
                                             "sha256": hashlib.sha256(old.read_bytes()).hexdigest()}
    elif mutation == "evidence":
        record["evidence_kind"] = "execution"
    elif mutation == "adapter":
        record["job"]["adapter"] = "scripted"
    elif mutation == "setup":
        record["proof_setup_check"]["runs"] = []
    elif mutation == "reading":
        record["verdict_reading"]["verdict"] = "not_proven"
    elif mutation == "bounded":
        record["bounds"]["input_size"] = 4
    elif mutation == "model":
        from swdb import c_lowering
        record["pins"]["models"] = [{"id": "std_min_int", "sha256": hashlib.sha256(
            c_lowering.model_text("std_min_int").encode()).hexdigest(), "proof_record": rid}]
    path.write_text(yaml.safe_dump(record, sort_keys=False))
    if mutation == "current":
        proven = seed.unit("dxc_summary")
        assert proven["verdict"] == "proven"
        assert proven["pins"]["summaries"][0]["proof_record"] == rid
    else:
        result = seed.unit("dxc_summary", ok=False)
        assert "no proven summary record" in result.stderr or "validation error" in result.stderr


@pytest.fixture(scope="module")
def initialized_model_subset(tmp_path_factory):
    if not _tools_present():
        pytest.skip("Frama-C 33.0 or clang 22.1.8 is missing")
    path = tmp_path_factory.mktemp("wp-initialized-models")
    seed = Seed(path, build_subset_seed(path))
    seed.model_records = {"std_copy_int": seed.prove("--model", "std_copy_int")}
    code = ("#include <algorithm>\n"
            "int swdb_copy_initialized(int *out) { int source[1] = {7}; std::copy(source, source + 1, out); return 0; }\n"
            "int swdb_copy_uninitialized(int *out) { int source[1]; std::copy(source, source + 1, out); return 0; }\n")
    (path / "library" / "proof_units" / "initialized_copy.cc").write_text(code)
    for label in ("initialized", "uninitialized"):
        cid, function = f"contract.fixture_copy_{label}", f"swdb_copy_{label}"
        data = _entry(cid, function, "initialized_copy.cc", code,
                      [("pre", "legality", "requires \\valid(out);"),
                       ("post", "postcondition", "assigns *out; ensures \\result == 0;")],
                      ["out"], {"once": "self"})
        (path / "library" / "rewrite_contracts" / f"fixture_copy_{label}.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False))
    return seed


@needs_wp
@pytest.mark.parametrize("name", ["std_copy_int", "std_swap_int", "swdb_atomic_load_n_int",
                                   "swdb_atomic_compare_exchange_n_int", "std_pair_int_int_copy_ctor"])
def test_models_prove_initialized_read_and_output_obligations(initialized_model_subset, name):
    seed = initialized_model_subset
    record = seed.model_records.get(name)
    if record is None:
        record = seed.prove("--model", name)
        seed.model_records[name] = record
    assert record["verdict"] == "proven", (name, record.get("unproven_properties"))
    from pathlib import Path
    source = next(row for row in record["evidence"]["reports"] if row["name"] == "wp_input")
    assert "\\initialized" in Path(source["path"]).read_text()
    assert "-rte-initialized @all" in " ".join(record["settings"]["flags"])


@needs_wp
@pytest.mark.parametrize("initialized", [True, False])
def test_a_model_call_requires_initialized_source_even_when_the_postcondition_ignores_its_value(
        initialized_model_subset, initialized):
    label = "initialized" if initialized else "uninitialized"
    record = initialized_model_subset.prove("--summary", f"contract.fixture_copy_{label}")
    assert record["verdict"] == ("proven" if initialized else "not_proven"), record
    if not initialized:
        assert record["unproven_properties"]
        assert any("std_copy_int_requires" in str(goal) for goal in record["unproven_properties"])

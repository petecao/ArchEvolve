"""The DX100 proof semantics for the BFS calls: the versioned entry, its rules and call contracts, and proofs
that use it through `swdb prove --adapter cbmc`.

Created: 2026-10-14 ET (Probata proof of concept ticket 27). Design: formal-verification map 12 items 1-5 and
11, map 14 (the wait rule as gem5 runs it), map 16 item 10 (one ghost state), S3 (ghost capacity); ticket 41's
Rocq hazards (library/rocq/probata/Reduction.v: F2, F5, F6). Format: docs/reference/format-v0.4-proof-semantics.md.

Seams: `swdb validate --library` (seam 4) for the entry and its negative controls; `swdb prove` (seam 1) with
`swdb candidate-level` reading the records for the DX100 fixtures. CBMC cases skip cleanly when CBMC 6.11 or
clang 22.1.8 is missing; run them inside the machine-wide verifier lock (on the Mac: verifier_run.py).
"""
import copy
import json
import os
import re
import shutil

import pytest
import yaml

from conftest import REPO, make_records, run_swdb

ENTRY = "semantics.dx100_bfs_0_1"
ENTRY_FILE = REPO / "library" / "proof_semantics" / "dx100_bfs_0_1.yaml"
GEM5 = "e4fc4afdf894f295442cef3604667a469fab8e62"
INVENTORY = ["add_mem_region", "clear_mem_region", "get_cacheable_tile_pointer", "get_new_reg", "get_new_tile",
             "get_tile_size", "maa_alu_scalar", "maa_const", "maa_indirect_load", "maa_indirect_store_vector",
             "maa_range_loop", "maa_stream_load", "wait_ready"]
QUIET = {"SWDB_FRAMA_C": "none", "SWDB_CLANG": "none"}


def _library(root, extra=None):
    """A small library: the proof semantics and the files its pins name."""
    for folder in ("proof_semantics", "dx100"):
        shutil.copytree(REPO / "library" / folder, root / folder)
    for rel, data in (extra or {}).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(data if isinstance(data, str) else yaml.safe_dump(data, sort_keys=False))


def _problems(stderr):
    found = {}
    for line in stderr.splitlines():
        match = re.match(r"^(/\S+): (\S+): (.*)$", line)
        if match:
            found.setdefault(os.path.basename(match.group(1)), []).append((match.group(2), match.group(3)))
    return found


def _entry():
    return yaml.safe_load(ENTRY_FILE.read_text())


# --- the entry: version, hash, call inventory, citations (seam 4) ----------------------------------------------

def test_the_bfs_proof_semantics_entry_validates_with_a_version_and_one_contract_per_inventory_call(tmp_path):
    records = make_records(tmp_path)
    _library(tmp_path / "library")
    result = run_swdb("validate", "--records", records.path, "--library", tmp_path / "library", env=QUIET)
    assert result.returncode == 0, result.stderr + result.stdout
    data = _entry()
    assert data["kind"] == "proof_semantics" and data["version"] == "0.1" and data["sequence"] == 1
    assert data["hardware_interface"] == {"id": "dx100-mmio", "version": "1.0-e4fc4af", "gem5_commit": GEM5}
    assert sorted(c["call"] for c in data["calls"]) == INVENTORY == sorted(data["inventory"]["calls"])
    assert all(c["contract"].strip() for c in data["calls"])
    rules = {r["id"]: r for r in data["rules"]}
    for rule in rules.values():          # every rule cites gem5 at e4fc4af or is assumed with an owner
        assert ("cites" in rule) != ("assumed" in rule)
        if "cites" in rule:
            assert GEM5.startswith(rule["cites"]["gem5_commit"]) and rule["cites"]["path"].startswith("src/mem/MAA/")
    assert all(set(c["rules"]) <= set(rules) and c["rules"] for c in data["calls"])
    assert {"values"} & {r.split("_")[-1] for r in rules} == {"values"}     # value rules are rules too


def _framac():
    from swdb import framac
    return not framac.locate().missing


@pytest.mark.skipif(not _framac(), reason="Frama-C 33.0 is missing")
def test_framac_type_checks_the_ghost_state_logic_and_every_call_contract(tmp_path):
    records = make_records(tmp_path)
    _library(tmp_path / "library")
    result = run_swdb("validate", "--records", records.path, "--library", tmp_path / "library",
                      env={"SWDB_CLANG": "none"})
    assert result.returncode == 0, result.stderr + result.stdout
    assert "UNCHECKED" not in result.stdout + result.stderr
    data = _entry()
    data["calls"][4]["contract"] = data["calls"][4]["contract"].replace("dx_reg_value[reg] == value",
                                                                        "dx_reg_value[reg] == no_such_name")
    (tmp_path / "library" / "proof_semantics" / "dx100_bfs_0_1.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    refused = run_swdb("validate", "--records", records.path, "--library", tmp_path / "library",
                       env={"SWDB_CLANG": "none"})
    assert refused.returncode == 1 and "refuses the contract of maa_const" in refused.stderr


def test_without_framac_the_contracts_are_reported_unchecked_never_valid(tmp_path):
    records = make_records(tmp_path)
    _library(tmp_path / "library")
    result = run_swdb("validate", "--records", records.path, "--library", tmp_path / "library", env=QUIET)
    assert result.returncode == 0
    assert "UNCHECKED" in result.stdout + result.stderr and "14 ACSL contracts" in result.stdout + result.stderr


def test_the_call_inventory_is_read_from_the_read_offload_lowerings_and_tdstepmaa():
    from swdb import proof_semantics
    data = _entry()
    found = proof_semantics.inventory(REPO / "library", data["inventory"]["sources"])
    assert found == INVENTORY


SEMANTICS_CONTROLS = {
    # name: (change to the entry, expected problem)
    "rule_without_citation": (lambda d: d["rules"][0].pop("cites", None) or d["rules"][0].pop("assumed", None),
                              "exactly one of cites"),
    "citation_at_another_commit": (lambda d: d["rules"][0].__setitem__(
        "cites", {"gem5_commit": "0123456789abcdef0123456789abcdef01234567", "path": "src/mem/MAA/IF.cc",
                  "lines": "193-212"}), "not the pinned gem5 commit"),
    "call_without_contract": (lambda d: d["calls"][0].pop("contract"), "has no ACSL contract"),
    "call_with_unknown_rule": (lambda d: d["calls"][0]["rules"].append("nope"), "names rule nope"),
    "inventory_call_not_listed": (lambda d: d.__setitem__("calls", d["calls"][1:]), "inventory call"),
}


@pytest.fixture(scope="module")
def controls(tmp_path_factory):
    folder = tmp_path_factory.mktemp("semantics-controls")
    records = make_records(folder)
    extra = {}
    for name, (change, _expected) in SEMANTICS_CONTROLS.items():
        data = copy.deepcopy(_entry())
        data["id"] = f"semantics.control_{name}"
        data["target"] = f"control-{name}"
        change(data)
        extra[f"proof_semantics/control_{name}.yaml"] = data
    _library(folder / "library", extra)
    result = run_swdb("validate", "--records", records.path, "--library", folder / "library", env=QUIET)
    return result, _problems(result.stderr)


@pytest.mark.parametrize("name", sorted(SEMANTICS_CONTROLS))
def test_each_proof_semantics_check_is_shown_by_its_control(controls, name):
    result, found = controls
    assert result.returncode == 1
    got = found.get(f"control_{name}.yaml", [])
    assert got and any(SEMANTICS_CONTROLS[name][1] in reason for _field, reason in got), got
    assert "dx100_bfs_0_1.yaml" not in found, found.get("dx100_bfs_0_1.yaml")


def test_a_ghost_array_declared_again_in_the_c_model_is_refused(tmp_path):
    records = make_records(tmp_path)
    _library(tmp_path / "library")
    model = tmp_path / "library" / "proof_semantics" / "dx100_bfs" / "model.h"
    model.write_text(model.read_text() + "\nint dx_tile_writer[DX_NT];\n")
    data = _entry()
    import hashlib
    data["model"]["c"]["sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
    (tmp_path / "library" / "proof_semantics" / "dx100_bfs_0_1.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    result = run_swdb("validate", "--records", records.path, "--library", tmp_path / "library", env=QUIET)
    assert result.returncode == 1
    assert "declared once" in result.stderr and "dx_tile_writer" in result.stderr


# --- proofs that use the proof semantics: swdb prove --adapter cbmc (seam 1) ----------------------------------

DX = REPO / "tests" / "fixtures" / "proof" / "dx100"
# Separately named frontier units leave the original dxf_load helper boundary intact.
# Their pointer calls are direct; host values are observed through the model's tile rows.
DIRECT_UNITS = r"""
int dxf_direct_stream(int *q, int n) {
  maa_const(0, 0);
  maa_const(n, 1);
  maa_const(1, 2);
  maa_stream_load(q, 0, 1, 2, 0, -1);
  wait_ready(0);
  return get_tile_size(0) == n;
}
int dxf_direct_three_reads(int *q, int *base, int n) {
  int *t0 = get_cacheable_tile_pointer(0);
  int *t1 = get_cacheable_tile_pointer(1);
  int *t2 = get_cacheable_tile_pointer(2);
  maa_const(0, 0);
  maa_const(n, 1);
  maa_const(1, 2);
  maa_stream_load(q, 0, 1, 2, 0, -1);
  wait_ready(0);
  int a = t0[0];
  maa_indirect_load(base, 0, 1, -1);
  wait_ready(1);
  int b = t1[0];
  maa_indirect_load(base, 0, 2, -1);
  wait_ready(2);
  int c = t2[0];
  return (0 <= a) & (a < n) & (b == c);
}
"""
UNITS = (DX / "fixture_units.cc").read_text() + DIRECT_UNITS
BASE = ("requires 1 <= n <= 2 && \\valid(q + (0 .. n - 1)) && \\valid({arr} + (0 .. n - 1));\n"
        "requires \\forall integer k; 0 <= k < n ==> 0 <= q[k] < n;")
Q_ONLY = ("requires 1 <= n <= 2 && \\valid(q + (0 .. n - 1));\n"
          "requires \\forall integer k; 0 <= k < n ==> 0 <= q[k] < n;")
RANGE = ("requires 2 <= n <= 3 && \\valid(q + (0 .. n - 1)) && \\valid(offs + (0 .. n - 1));\n"
         "requires \\forall integer k; 0 <= k < n ==> 0 <= q[k] < n - 1;\n"
         "requires \\forall integer k; 0 <= k < n ==> 0 <= offs[k] <= 3;\n"
         "requires \\forall integer k; 0 <= k < n - 1 ==> offs[k] <= offs[k + 1];")
#: contract name: (function, pointer parameters, requires, assigns, size bound of n)
FIXTURES = {
    "direct_stream": ("dxf_direct_stream", ["q"], "requires 0 <= n <= 2 && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
    "direct_three_reads": ("dxf_direct_three_reads", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "summary_wrapper": ("dxf_summary_wrapper", [], "requires 0 <= n <= 2;", "\\nothing", 2),
    "summary_caller": ("dxf_summary_caller", [], "requires 0 <= n <= 2;", "\\nothing", 2),
    "local_storage": ("dxf_local_storage", [], "requires 1 <= n <= 2;", "\\nothing", 2),
    "signed_stream": ("dxf_signed_stream", ["q"], "requires n == 2 && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
    "three_reads": ("dxf_three_reads", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "size": ("dxf_size", ["q"], "requires 0 <= n <= 2 && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
    "cpu_write": ("dxf_cpu_write", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "cpu_memory_overlap": ("dxf_cpu_memory_overlap", ["q", "base"], BASE.format(arr="base"), "base[0 .. n - 1]", 2),
    "device_memory_overlap": ("dxf_device_memory_overlap", ["q", "p"], BASE.format(arr="p"), "p[0 .. n - 1]", 2),
    "store_exit": ("dxf_store_exit", ["q", "p"], BASE.format(arr="p"), "p[0 .. n - 1]", 2),
    "store_source_wait": ("dxf_store_source_wait", ["q", "p"], BASE.format(arr="p"), "p[0 .. n - 1]", 2),
    "transitive": ("dxf_transitive", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "stall_condition": ("dxf_stall_condition", ["q", "p", "base"],
                        BASE.format(arr="p") + "\nrequires \\valid(base + (0 .. n - 1));", "p[0 .. n - 1]", 2),
    "register_write": ("dxf_register_write", ["q"], Q_ONLY, "\\nothing", 2),
    "range_exception": ("dxf_range_exception", ["q", "offs"], RANGE, "\\nothing", 3),
    "condition_wait": ("dxf_condition_wait", ["q", "p"], BASE.format(arr="p"), "p[0 .. n - 1]", 2),
    "unrelated_wait": ("dxf_unrelated_wait", ["q"], Q_ONLY, "\\nothing", 2),
    "value_stream": ("dxf_value_stream", ["q"], Q_ONLY, "\\nothing", 2),
    "value_gather": ("dxf_value_gather", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "value_range": ("dxf_value_range", ["q", "offs"], RANGE + "\nrequires offs[q[0]] < offs[q[0] + 1];", "\\nothing", 3),
    "footprint": ("dxf_footprint", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "capacity": ("dxf_capacity", ["q"], "requires 32 <= n <= 33 && \\valid(q + (0 .. n - 1));", "\\nothing", 32),
}
PROBE = f"{ENTRY}#unready_read@dxf_three_reads.probe"


def _dx_contracts():
    import hashlib
    from test_cbmc_adapter import _contract
    found = {}
    for name, (function, arrays, requires, assigns, _bound) in FIXTURES.items():
        # The fixture supplies initialized input buffers. State this premise explicitly for WP's
        # initialization policy; the bounded harness must justify it from its actual buffer fill.
        requires += "\n" + "\n".join(f"requires \\initialized({a} + (0 .. n - 1));" for a in arrays)
        data = _contract(f"contract.fixture_dx_{name}", function, [
            ("pre", "legality", requires, "per_candidate"),
            ("post", "postcondition", f"assigns {assigns};\nensures \\result == 1;", "per_candidate")],
            [{"array": a, "shared_actions": [], "history_reads": False} for a in arrays])
        if name in {"direct_stream", "direct_three_reads"}:
            # An explicit typed input-window contract addition, independent of validity.
            data["proof_unit"]["array_domains"] = {array: {"extent": "n"} for array in arrays}
        if name == "summary_wrapper":
            for clause in data["clauses"]:
                clause["proof_placement"] = {"once": "self"}
        data["proof_unit"]["source"] = {"root": "library", "path": "proof_units/dx100_fixture_units.cc",
                                        "sha256": hashlib.sha256(UNITS.encode()).hexdigest()}
        found[name] = data
    return found


def build_dx_seed(path):
    """records/ and library/ under `path` with the DX100 fixture units in one candidate artifact."""
    import json
    from conftest import FIXTURES as FIX
    from swdb import c_lowering
    from test_cbmc_adapter import ANCHOR_BEFORE, method_version
    from test_proof_records import _library_roots
    from test_wp_adapter import _certify
    from testkit.proposals import build_proposal_setup
    from testkit.record_subset import copy_record_subset
    records = make_records(path)
    copy_record_subset(REPO / "records", records.path,
                       sorted(_library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10"}))
    shutil.copytree(REPO / "library", path / "library")
    methods = path / "library" / "methods"
    methods.mkdir(exist_ok=True)
    shutil.copy(FIX / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    fixture_method = method_version(c_lowering.identity())
    for tool in fixture_method["lineup"]:
        if tool["tool"] == "frama-c-wp":
            tool["flags"] += ["-wp-prover", "z3,cvc5,alt-ergo"]
    (methods / "cbmc-fixture.yaml").write_text(yaml.safe_dump(fixture_method, sort_keys=False))
    (path / "library" / "proof_units").mkdir()
    (path / "library" / "proof_units" / "dx100_fixture_units.cc").write_text(UNITS)
    for name, data in _dx_contracts().items():
        (path / "library" / "rewrite_contracts" / f"fixture_dx_{name}.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    submitted = records.swdb("submit", request(ANCHOR_BEFORE, UNITS + "\n" + ANCHOR_BEFORE, id="dx100-fixtures"),
                             "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    _certify(records.path, path, candidate, "contract.fixture_dx_three_reads")
    return candidate


@pytest.fixture(scope="module")
def dx_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("dx-seed")
    return path, build_dx_seed(path)


@pytest.fixture
def dx(dx_seed, tmp_path):
    from test_cbmc_adapter import Seed
    source, candidate = dx_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, {"dx": candidate})


def prove(dx, name, *defines, bound=None, ok=True):
    """One `swdb prove --adapter cbmc` job. The timeout allows for waiting on the machine-wide verifier lock."""
    import json
    function, _arrays, _requires, _assigns, default = FIXTURES[name]
    bounds = {"threads": 1, "n": bound if bound is not None else default}
    extra = [arg for define in defines for arg in ("--define", define)]
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"], "--function", function,
                      "--contract", f"contract.fixture_dx_{name}", "--adapter", "cbmc", "--runs-dir", dx.runs,
                      "--format", "json", "--bounds", json.dumps(bounds), *extra,
                      env={"SWDB_FRAMA_C": "none"}, timeout=3600)
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return dx.read(json.loads(result.stdout)) if ok else result


def _cbmc_ready():
    from swdb import c_lowering, cbmc_adapter
    return not cbmc_adapter.locate()[2] and not c_lowering.locate().missing


needs_cbmc = pytest.mark.skipif(not _cbmc_ready(), reason="CBMC 6.11 or clang 22.1.8 is missing")


@needs_cbmc
def test_a_safe_unit_proves_pins_the_proof_semantics_and_lists_it_and_the_reduction_as_assumptions(dx):
    record = prove(dx, "three_reads")
    assert record["verdict"] == "proven", (record.get("failure_class"), record.get("unproven_properties"))
    pin = record["pins"]["proof_semantics"]
    assert pin["id"] == ENTRY and len(pin["sha256"]) == 64
    kinds = {a["kind"]: a["reference"]["id"] for a in record["assumptions"]}
    assert kinds["proof_semantics"] == ENTRY and kinds["reduction"] == "rocq.probata.dx100_reduction"
    semantics = record["settings"]["proof_semantics"]
    assert semantics["calls"] == ["get_cacheable_tile_pointer", "maa_const", "maa_indirect_load", "maa_stream_load",
                                  "wait_ready"]
    assert [p["id"] for p in semantics["probes"]] == [f"dxf_three_reads.probe{k}" for k in (1, 2, 3)]
    assert all(p["access"] == "read" for p in semantics["probes"])
    assert record["settings"]["forms"] == {"c_lowering": "proven", "cxx": "agrees on the bounded domain"}
    job_c = open(dx.report(record, "cbmc_input")).read()
    assert job_c.count("SWDB_TILE_READ(&(") == 3 and "ghost unsigned int" not in job_c
    assert "unsigned int dx_live;" in job_c                      # generated from ghost.acsl, declared once
    cxx = open(dx.report(record, "differential_cxx")).read()
    assert cxx.count("SWDB_TILE_READ(&(") == 3                   # the same probes on the C++


@needs_cbmc
@pytest.mark.parametrize("read", [1, 2, 3])
def test_moving_any_one_tile_read_before_its_wait_is_refuted_at_that_reads_probe_on_both_forms(dx, read):
    record = prove(dx, "three_reads", f"SWDB_EARLY_READ_{read}")
    assert record["verdict"] == "refuted", (record.get("failure_class"), record.get("unproven_properties"))
    example = record["counterexample"]
    assert example["property"] == f"{PROBE}{read}" and example["replay"]["replayed"] is True
    assert record["settings"]["forms"] == {"c_lowering": "refuted", "cxx": "refuted (counterexample replayed)"}


@needs_cbmc
def test_get_tile_size_before_the_covering_wait_is_refuted_and_after_it_proves(dx):
    assert prove(dx, "size")["verdict"] == "proven"
    early = prove(dx, "size", "SWDB_EARLY_SIZE")
    assert early["verdict"] == "refuted"
    assert early["counterexample"]["property"] == f"{ENTRY}#unready_size_read"


@needs_cbmc
def test_a_cpu_write_into_a_tile_an_uncovered_command_reads_is_refuted_and_a_read_is_not(dx):
    assert prove(dx, "cpu_write")["verdict"] == "proven"
    write = prove(dx, "cpu_write", "SWDB_CPU_WRITE")
    assert write["verdict"] == "refuted"
    assert write["counterexample"]["property"] == f"{ENTRY}#cpu_write_overlap@dxf_cpu_write.probe2"


@needs_cbmc
@pytest.mark.parametrize("name", ["store_source_wait", "transitive", "stall_condition", "register_write"])
def test_the_wait_rule_as_gem5_runs_it_proves(dx, name):
    record = prove(dx, name)
    assert record["verdict"] == "proven", (record.get("failure_class"), record.get("counterexample"),
                                           record.get("unproven_properties"))


@needs_cbmc
@pytest.mark.parametrize("name,probe", [("range_exception", "dxf_range_exception.probe1"),
                                        ("condition_wait", "dxf_condition_wait.probe1"),
                                        ("unrelated_wait", "dxf_unrelated_wait.probe1")])
def test_reads_the_wait_rule_does_not_cover_are_refuted(dx, name, probe):
    record = prove(dx, name)
    assert record["verdict"] == "refuted", (record.get("failure_class"), record.get("unproven_properties"))
    assert record["counterexample"]["property"] == f"{ENTRY}#unready_read@{probe}"


@needs_cbmc
@pytest.mark.parametrize("name", ["value_stream", "value_gather", "value_range"])
def test_values_at_issue_prove_and_a_wrong_value_is_refuted(dx, name):
    proven = prove(dx, name)
    assert proven["verdict"] == "proven", (proven.get("failure_class"), proven.get("counterexample"))
    wrong = prove(dx, name, "SWDB_WRONG_VALUE")
    assert wrong["verdict"] == "refuted"
    assert wrong["counterexample"]["property"].startswith(f"contract.fixture_dx_{name}#post")


@needs_cbmc
def test_an_address_in_an_uncovered_gathers_footprint_is_a_member_and_one_outside_is_not(dx):
    member = prove(dx, "footprint")
    assert member["verdict"] == "proven", (member.get("failure_class"), member.get("counterexample"))
    outside = prove(dx, "footprint", "SWDB_OUTSIDE")
    assert outside["verdict"] == "refuted"
    assert outside["counterexample"]["property"].startswith("contract.fixture_dx_footprint#post")


@needs_cbmc
def test_32_uncovered_commands_prove_and_33_end_not_proven_ghost_capacity(dx):
    sizes = ("DX_NT=40", "DX_TS=1")
    within = prove(dx, "capacity", *sizes, bound=32)
    assert within["verdict"] == "proven", (within.get("failure_class"), within.get("unproven_properties"))
    over = prove(dx, "capacity", *sizes, bound=33)
    assert over["verdict"] == "not_proven" and over["failure_class"] == "ghost_capacity"
    assert "counterexample" not in over


def prove_wp(dx, name, *defines, hints=None):
    """One `swdb prove --adapter wp` job (the WP form of the proof semantics), allowing for the verifier lock."""
    import json
    function = FIXTURES[name][0]
    extra = [arg for define in defines for arg in ("--define", define)]
    if hints is None and name in {"store_source_wait", "stall_condition", "condition_wait"}:
        from test_wp_adapter import _hints
        statement = 7 if name == "store_source_wait" else 9
        hints = _hints(f"{function}.s{statement}.before",
            "assert \\forall integer k; 0 <= k < dx_tile_size[0] && k < DX_TS ==> "
            "0 <= (unsigned int)dx_tile_data[0][k] < n;")
        hints.insert(0, {"anchor": f"{function}.entry", "kind": "ghost", "text": "ghost dx_store_bound = n;",
                         "provenance": {"source": "agent"}})
    if hints:
        hint_path = dx.root / "wp-hints.yaml"
        hint_path.write_text(yaml.safe_dump({"hints": hints}, sort_keys=False))
        extra += ["--hint-file", str(hint_path)]
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"], "--function", function,
                      "--contract", f"contract.fixture_dx_{name}", "--adapter", "wp", "--runs-dir", dx.runs,
                      "--format", "json", *extra, timeout=3600)
    assert result.returncode == 0, result.stderr + result.stdout
    return dx.read(json.loads(result.stdout))


def _wp_ready():
    from swdb import c_lowering
    from test_formal_frame import FRAMAC
    return FRAMAC and not c_lowering.locate().missing


needs_wp = pytest.mark.skipif(not _wp_ready(), reason="Frama-C 33.0 or clang 22.1.8 is missing")
#: the fixtures CBMC proves; WP must prove them too (capacity is a bounded notion: WP needs a loop invariant)
WP_SAFE = ["three_reads", "size", "cpu_write", "store_source_wait", "stall_condition", "transitive",
           "register_write", "value_stream", "value_gather", "value_range", "footprint"]
#: the variants CBMC refutes, and the WP property that stays unproven (WP never refutes)
WP_FAULTS = [("three_reads", "SWDB_EARLY_READ_1", "swdb_tile_read_probe"),
             ("three_reads", "SWDB_EARLY_READ_2", "swdb_tile_read_probe"),
             ("three_reads", "SWDB_EARLY_READ_3", "swdb_tile_read_probe"),
             ("size", "SWDB_EARLY_SIZE", "get_tile_size"),
             ("cpu_write", "SWDB_CPU_WRITE", "swdb_tile_write_probe"),
             ("range_exception", None, "swdb_tile_read_probe"),
             ("condition_wait", None, "swdb_tile_read_probe"),
             ("unrelated_wait", None, "swdb_tile_read_probe"),
             ("value_stream", "SWDB_WRONG_VALUE", None),
             ("value_gather", "SWDB_WRONG_VALUE", None),
             ("value_range", "SWDB_WRONG_VALUE", None),
             ("footprint", "SWDB_OUTSIDE", None)]


@needs_wp
@pytest.mark.parametrize("name", WP_SAFE)
def test_wp_proves_every_unit_cbmc_proves_with_the_same_proof_semantics(dx, name):
    record = prove_wp(dx, name)
    assert record["verdict"] == "proven", (record.get("failure_class"), record.get("unproven_properties"))
    if name in {"store_source_wait", "stall_condition"}:
        assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    assert record["pins"]["proof_semantics"]["id"] == ENTRY
    assert {a["kind"] for a in record["assumptions"]} >= {"proof_semantics", "reduction"}
    flags = record["settings"]["flags"]
    assert flags.count("-wp-prover") == 1 and flags[flags.index("-wp-prover") + 1] == "z3,cvc5,alt-ergo"
    assert record["settings"]["proof_semantics"]["unit_requires"]
    probes = record["settings"]["proof_semantics"]["probes"]
    wp_input = open(dx.report(record, "wp_input")).read()
    assert wp_input.count("SWDB_TILE_READ(&(") + wp_input.count("SWDB_TILE_WRITE(&(") == len(probes)
    assert wp_input.count("unsigned int dx_live;") == 1 and "/*@ ghost" in wp_input


@needs_wp
@pytest.mark.parametrize("name,define,call", WP_FAULTS)
def test_wp_leaves_every_unit_cbmc_refutes_not_proven_never_refuted(dx, name, define, call):
    record = prove_wp(dx, name, *([define] if define else []))
    assert record["verdict"] == "not_proven" and "counterexample" not in record
    unproven = json.dumps(record.get("unproven_properties"))
    if call:                                                  # the probe's (or call's) precondition is the one
        assert call in unproven or "precondition" in unproven, unproven


@needs_wp
def test_a_store_frame_bound_that_omits_a_possible_write_stays_not_proven(dx):
    record = prove_wp(dx, "store_source_wait", hints=[
        {"anchor": "dxf_store_source_wait.entry", "kind": "ghost", "text": "ghost dx_store_bound = n - 1;",
         "provenance": {"source": "agent"}}])
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    assert record["verdict"] == "not_proven" and "counterexample" not in record
    assert any("store_indices" in str(g["goal"]) and g["status"] != "valid" for g in record["goals"])


@needs_wp
@pytest.mark.parametrize("adapter", ["cbmc", "wp"])
@pytest.mark.parametrize("capacity", [0, 33])
def test_a_ghost_capacity_outside_the_command_mask_width_is_rejected_before_tools(dx, adapter, capacity):
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", "dxf_three_reads", "--contract", "contract.fixture_dx_three_reads", "--adapter", adapter,
        "--runs-dir", dx.runs, "--format", "json", "--define", f"DX_K={capacity}",
        env={"SWDB_FRAMA_C": "none", "SWDB_CLANG": "none", "SWDB_CBMC": "none"})
    assert result.returncode == 1 and "DX_K must be in 1..32" in result.stderr, result.stderr + result.stdout
    assert not result.stdout.strip()
    assert not list(dx.runs.glob("*/wp/frama-c.log"))
    assert not list(dx.runs.glob("*/cbmc/cbmc_input.c"))


@needs_wp
@pytest.mark.parametrize("commands", [32, 33])
def test_wp_capacity_agrees_at_32_and_leaves_33_not_proven(dx, commands):
    from swdb import proof_semantics
    from swdb.library import Library
    from test_wp_adapter import _hints
    path = dx.root / "library" / "rewrite_contracts" / "fixture_dx_capacity.yaml"
    contract = yaml.safe_load(path.read_text())
    # The source reads q[0]; advertise its complete incoming typed window explicitly.
    contract["proof_unit"]["array_domains"] = {"q": {"extent": "n"}}
    for clause in contract["clauses"]:
        if clause.get("acsl"):
            clause["acsl"]["text"] = clause["acsl"]["text"].replace("32 <= n <= 33", f"n == {commands}")
    path.write_text(yaml.safe_dump(contract, sort_keys=False))
    library = Library(dx.root / "library")
    locations = proof_semantics.wp_locations(library, ENTRY)
    hints = _hints("dxf_capacity.loop1.head",
        "loop invariant 0 <= t <= n;",
        "loop invariant 0 <= dx_count <= t;",
        "loop invariant dx_state_initialized;",
        "loop invariant dx_memory_clear_after_stall(-1, -1, 0);",
        "loop invariant dx_reg_value[0] == 0 && dx_reg_value[1] == 1 && dx_reg_value[2] == 1;",
        "loop invariant dx_reg_writer[0] == -1 && dx_reg_writer[1] == -1 && dx_reg_writer[2] == -1;",
        "loop assigns t, " + ", ".join(locations) + ";",
        "loop variant n - t;")
    record = prove_wp(dx, "capacity", "DX_NT=40", "DX_TS=1", hints=hints)
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    if commands == 32:
        assert record["verdict"] == "proven", record.get("unproven_properties")
    else:
        assert record["verdict"] == "not_proven" and record["failure_class"] == "ghost_capacity"
        assert "counterexample" not in record


@needs_cbmc
def test_a_record_that_pins_an_older_proof_semantics_version_stops_counting(dx):
    import json
    record = prove(dx, "three_reads")
    level = json.loads(dx.swdb("candidate-level", dx.candidates["dx"], "--format", "json").stdout)
    assert level["level"] == "proven_within_bounds_threads_1", level
    newer = _entry()
    newer.update(id="semantics.dx100_bfs_0_2", version="0.2", sequence=2)
    (dx.root / "library" / "proof_semantics" / "dx100_bfs_0_2.yaml").write_text(yaml.safe_dump(newer, sort_keys=False))
    level = json.loads(dx.swdb("candidate-level", dx.candidates["dx"], "--format", "json").stdout)
    assert level["level"] != "proven_within_bounds_threads_1"
    stale = json.dumps(level)
    assert record["id"] in stale and "proof_semantics" in stale

@needs_wp
@pytest.mark.parametrize("text", [
    "ghost dx_tile_writer[0] = -1;",
    "ghost dx_count = 0;",
    "ghost wait_ready(0);",
    "ghost int *alias = &dx_count; *alias = 0;",
    "ghost int dx_count = 0;",
    "ghost dx_store_bound = wait_ready(0);",
    "ghost dx_store_bound = RESET;",
    "ghost dx_store_bound = (dx_count = 0);",
    pytest.param("ghost dx_store_bound = (dx_count >>= 31);", id="ghost-shift-right"),
    pytest.param("ghost dx_store_bound = (dx_count <<= 1);", id="ghost-shift-left"),
    pytest.param("ghost dx_store_bound = (dx_count >>??/\n= 31);", id="ghost-trigraph-shift"),
    "ghost int witness = 0; witness++;",
    "ghost int witness = 0; witness = (*wait_ready)(0);",
])
def test_wp_refuses_hint_that_mutates_the_trusted_semantics_ghost_state(dx, text):
    from test_wp_adapter import fake
    if "RESET" in text:
        import hashlib
        state_path = dx.root / "library" / "proof_semantics" / "dx100_bfs" / "state.h"
        state_path.write_text("#define RESET (dx_count = 0)\n" + state_path.read_text())
        entry_path = dx.root / "library" / "proof_semantics" / "dx100_bfs_0_1.yaml"
        entry = yaml.safe_load(entry_path.read_text())
        entry["model"]["state"]["sha256"] = hashlib.sha256(state_path.read_bytes()).hexdigest()
        entry_path.write_text(yaml.safe_dump(entry, sort_keys=False))
    hint_path = dx.root / "model-state-forgery.yaml"
    hint_path.write_text(yaml.safe_dump({"hints": [{"anchor": "dxf_three_reads.entry", "kind": "ghost",
        "text": text, "provenance": {"source": "agent"}}]}))
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", "dxf_three_reads", "--contract", "contract.fixture_dx_three_reads", "--adapter", "wp",
        "--runs-dir", dx.runs, "--hint-file", hint_path, "--format", "json", env=fake("unknown"), timeout=120)
    assert result.returncode != 0 and "semantics_ghost_ownership" in result.stderr, result.stderr + result.stdout
    assert not list((dx.records / "proofs").glob("*.yaml"))
    assert not list(dx.runs.glob("*/wp/frama-c.log"))


@needs_wp
@pytest.mark.parametrize("text", ["ghost int hint_ready = 0; hint_ready = hint_ready + 1;",
                                  "ghost dx_store_bound = n;",
                                  "ghost dx_store_bound = (n <= 0) ? 0 : n;"])
def test_wp_allows_fresh_scalar_witnesses_without_trusting_them_as_model_updates(dx, text):
    from test_wp_adapter import fake
    hint_path = dx.root / "scalar-witness.yaml"
    hint_path.write_text(yaml.safe_dump({"hints": [{"anchor": "dxf_three_reads.entry", "kind": "ghost",
        "text": text, "provenance": {"source": "agent"}}]}))
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", "dxf_three_reads", "--contract", "contract.fixture_dx_three_reads", "--adapter", "wp",
        "--runs-dir", dx.runs, "--hint-file", hint_path, "--format", "json", env=fake("unknown"), timeout=120)
    assert result.returncode == 0, result.stderr + result.stdout
    record = dx.read(json.loads(result.stdout))
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unknown"
    assert record["proof_setup_check"]["runs"]


@needs_wp
@pytest.mark.parametrize("name", ["direct_stream", "direct_three_reads"])
def test_wp_audited_dx_pointer_calls_prove_only_checked_explicit_input_windows(dx, name):
    record = prove_wp(dx, name)
    assert record["verdict"] == "proven", record.get("unproven_properties")
    guards = [goal for goal in record["goals"] if "swdb_window_call" in goal["goal"] and not goal.get("smoke")]
    assert len(guards) == (1 if name == "direct_stream" else 3)
    assert all(goal["status"] == "valid" for goal in guards)


@needs_wp
def test_wp_dx_window_cannot_be_recovered_from_a_larger_valid_input_range(dx):
    path = dx.root / "library/rewrite_contracts/fixture_dx_direct_stream.yaml"
    contract = yaml.safe_load(path.read_text())
    contract["proof_unit"]["array_domains"]["q"]["extent"] = "n - 1"
    for clause in contract["clauses"]:
        if clause.get("acsl"):
            clause["acsl"]["text"] = clause["acsl"]["text"].replace("0 <= n <= 2", "n == 2")
    path.write_text(yaml.safe_dump(contract, sort_keys=False))
    record = prove_wp(dx, "direct_stream")
    assert record["verdict"] == "not_proven", record
    assert any("swdb_window_call" in goal["goal"] and goal["status"] != "valid"
               for goal in record["goals"]), record


@needs_wp
def test_wp_dx_source_initializedness_is_checked_after_explicit_window_admission(dx):
    path = dx.root / "library/rewrite_contracts/fixture_dx_direct_stream.yaml"
    contract = yaml.safe_load(path.read_text())
    for clause in contract["clauses"]:
        if clause.get("acsl"):
            clause["acsl"]["text"] = clause["acsl"]["text"].replace(
                "requires \\initialized(q + (0 .. n - 1));", "")
    path.write_text(yaml.safe_dump(contract, sort_keys=False))
    record = prove_wp(dx, "direct_stream")
    assert record["verdict"] == "not_proven", record
    assert any("source_initialized" in goal["goal"] and goal["status"] != "valid"
               for goal in record["goals"]), record


@needs_wp
def test_wp_unit_window_does_not_invent_a_domain_for_a_defined_pointer_helper(dx):
    path = dx.root / "library/rewrite_contracts/fixture_dx_three_reads.yaml"
    contract = yaml.safe_load(path.read_text())
    contract["proof_unit"]["array_domains"] = {"q": {"extent": "n"}, "base": {"extent": "n"}}
    path.write_text(yaml.safe_dump(contract, sort_keys=False))
    record = prove_wp(dx, "three_reads")
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct", record
    assert not any(report["name"] == "wp_log" for report in record["evidence"]["reports"])

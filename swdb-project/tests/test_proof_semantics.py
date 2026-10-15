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
UNITS = (DX / "fixture_units.cc").read_text()
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
    "three_reads": ("dxf_three_reads", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
    "size": ("dxf_size", ["q"], "requires 0 <= n <= 2 && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
    "cpu_write": ("dxf_cpu_write", ["q", "base"], BASE.format(arr="base"), "\\nothing", 2),
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
        data = _contract(f"contract.fixture_dx_{name}", function, [
            ("pre", "legality", requires, "per_candidate"),
            ("post", "postcondition", f"assigns {assigns};\nensures \\result == 1;", "per_candidate")],
            [{"array": a, "shared_actions": [], "history_reads": False} for a in arrays])
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
    (methods / "cbmc-fixture.yaml").write_text(yaml.safe_dump(method_version(c_lowering.identity()), sort_keys=False))
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


def prove_wp(dx, name, *defines):
    """One `swdb prove --adapter wp` job (the WP form of the proof semantics), allowing for the verifier lock."""
    import json
    function = FIXTURES[name][0]
    extra = [arg for define in defines for arg in ("--define", define)]
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
    assert record["pins"]["proof_semantics"]["id"] == ENTRY
    assert {a["kind"] for a in record["assumptions"]} >= {"proof_semantics", "reduction"}
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

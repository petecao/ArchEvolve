"""The real WP adapter through `swdb prove --adapter wp` (the A2 tracer), with the machine-wide verifier lock.

Created: 2026-10-14 ET (Probata proof of concept ticket 21). Design: formal-verification map spec ("Proof
command", "Verifier lineup and order", "Proof-hint loop": anchors, frozen flags, verdict reading;
"Testing Decisions", seam 1); map 11 items 1, 3, 8, 9, 10; 13 items 4, 6, 7; 16 items 3, 6; 26 item 5.
Format: docs/reference/format-v0.4-c-lowering-wp.md.

Seam 1 (`swdb prove`), with `swdb validate`, `swdb build` and `swdb candidate-level` reading the records.
The fixture candidate artifacts are GAPBS bfs.cc with the core-subset fixture units inserted (one safe,
one with the seeded off-by-one), built through the public workflow and certified by a fixture record.
Cases that run Frama-C/WP skip cleanly when Frama-C 33.0 or clang 22.1.8 is missing; run them inside the
machine-wide verifier lock (on the Mac: verifier_run.py), with the sandbox off (Why3 needs its socket).
Scripted faults use a stand-in `frama-c` (SWDB_FRAMA_C) that writes chosen WP reports.
"""

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb
from test_proof_records import _library_roots
from testkit.bfs_protocol import _payload
from testkit.proposals import build_proposal_setup
from testkit.record_subset import copy_record_subset

WP = FIXTURES / "proof" / "wp"
UNITS = (WP / "fixture_units.cc").read_text()
ANCHOR_BEFORE = "pvector<NodeID> InitParent(const Graph &g) {"
SEEDED_BUG = ("i < n; ++i", "i < n - 1; ++i")
FILL = "contract.fixture_wp_fill"
SMOKE = "contract.fixture_wp_smoke"


def _hints(anchor, *texts):
    """Hint records (ticket 35) at one anchor, kind read from each text's keyword."""
    kinds = {"loop invariant": "loop_invariant", "loop assigns": "loop_assigns", "loop variant": "loop_variant",
             "assert": "assert"}
    return [{"anchor": anchor, "kind": next(k for p, k in kinds.items() if t.startswith(p)), "text": t,
             "provenance": {"source": "human"}} for t in texts]


FILL_HINTS = _hints("swdb_fixture_fill.loop1.head", "loop invariant 0 <= i <= n;",
                    "loop invariant \\forall integer k; 0 <= k < i ==> a[k] == v;", "loop assigns i, a[0 .. n-1];",
                    "loop variant n - i;")
SMOKE_HINTS = _hints("count_up.loop1.head", "loop invariant 0 <= i <= n;", "loop assigns i;", "loop variant n - i;")
TRUSTED = {"swdb-c-lowering-2", "clang-22.1.8", "frama-c-wp-33.0", "alt-ergo-2.6.4", "z3-5.1.0", "cvc5-1.2.1"}


def _tools_present():
    from swdb import c_lowering, framac
    return not framac.locate().missing and not c_lowering.locate().missing


needs_wp = pytest.mark.skipif(not _tools_present(), reason="Frama-C 33.0 or clang 22.1.8 is missing")


# --- the seed: two fixture candidate artifacts, fixture contracts, a method version with the real lineup -------

def _contract(cid, function, clauses, frame):
    unit = {"root": "library", "path": "proof_units/fixture_units.cc",
            "sha256": hashlib.sha256(UNITS.encode()).hexdigest()}
    return {
        "kind": "rewrite_contract", "id": cid, "formal_frame": 1, "version": "1.0",
        "provenance": {"origin": {"intrinsic_specification": "fixture-21"}},
        "proof_unit": {"source": unit, "function": function},
        "concurrency_frame": frame,
        "clauses": [{"id": name, "role": role, "statement": f"Fixture clause {name}.", "discharge_mode": "runtime_guard",
                     "negative_control": {"id": f"{name}-control", "check": name},
                     "acsl": {"text": text, "uses": []}, "proof_placement": "per_candidate"}
                    for name, role, text in clauses],
        "pattern_key": [{"roles": ["index", "target"], "address_shapes": ["stream", "single_valued_indirect"],
                         "update_kind": "read"}],
        "strategies": [], "uses_intrinsics": [], "uses_library_operations": [], "runtime_guards": [], "knobs": [],
        "preservation_obligations": [], "correctness_check": {"kernel": "fixture", "check": "fixture"},
        "execution_witness": {"check": "fixture"},
        "negative_controls": [{"id": kind, "kind": kind, "check": "fixture"}
                              for kind in ("overlapping_pointer", "double_claim", "dropped_operand")],
        "requirement_map": []}


def method_version(identity):
    """A contract_fixture method version with the real Mac lineup, sequence 2 (current: frozen, from the
    frozen contract fixture). fix-21 (2026-10-14 ET): the lineup is the committed draft's
    (library/methods/probata-draft-1.yaml), so the two never drift; the translator is this checkout's tool."""
    data = yaml.safe_load((FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml").read_text())
    data.update(id="method.wp-tracer-fixture", sequence=2,
                description="Fixture method version with the real WP lineup of the Mac (ticket 21 tests).")
    data["lineup"] = yaml.safe_load((REPO / "library" / "methods" / "probata-draft-1.yaml").read_text())["lineup"]
    data["c_lowering"]["translators"] = [identity["c_lowering"]]
    return data


def build_wp_seed(path):
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
    (path / "library" / "proof_units").mkdir()
    (path / "library" / "proof_units" / "fixture_units.cc").write_text(UNITS)
    contracts = path / "library" / "rewrite_contracts"
    contracts.joinpath("fixture_wp_fill.yaml").write_text(yaml.safe_dump(_contract(
        FILL, "swdb_fixture_fill",
        [("fill_pre", "legality", "requires n >= 0 && \\valid(a + (0 .. n-1));"),
         ("fill_post", "postcondition", "assigns a[0 .. n-1];\nensures \\forall integer k; 0 <= k < n ==> a[k] == v;")],
        [{"array": "a", "shared_actions": [], "history_reads": False}]), sort_keys=False))
    contracts.joinpath("fixture_wp_smoke.yaml").write_text(yaml.safe_dump(_contract(
        SMOKE, "count_up",
        [("smoke_pre", "legality", "requires 0 <= n <= 1000000;"),
         ("smoke_post", "postcondition", "assigns \\nothing;\nensures \\result == n;")], []), sort_keys=False))
    records, runs, _snapshot, request = build_proposal_setup(records, path, copy_all=False)
    candidates = {}
    for name, units in (("safe", UNITS), ("bug", UNITS.replace(*SEEDED_BUG))):
        submitted = records.swdb("submit", request(ANCHOR_BEFORE, units + "\n" + ANCHOR_BEFORE, id=f"wp-{name}"),
                                 "--runs-dir", runs, "--format", "json")
        assert submitted.returncode == 0, submitted.stderr
        candidates[name] = json.loads(submitted.stdout)["candidate"]
        _certify(records.path, path, candidates[name], FILL)   # the level rule reads the fill contract
    return candidates


def _certify(records, root, candidate, contract):
    """A fixture certification of `candidate` against a fixture contract's current content (as test_proof_records)."""
    from swdb.library import Library
    data = yaml.safe_load((records / "candidates" / f"{candidate}.yaml").read_text())
    content = Library(root / "library").content_sha256(contract)
    rid = f"certification.{candidate}.{contract.split('.')[-1]}"
    record = {"kind": "certification", "schema_version": "0.4", "id": rid, "status": "draft",
              "created": "2026-10-14", "updated": "2026-10-14",
              "provenance": [{"id": "fixture", "kind": "agent_run", "description": "Contract fixture.", "uri": None}],
              "entry": {"id": contract, "content_sha256": content},
              "candidate": {"id": candidate, "contract": contract, "contract_sha256": content,
                            "tree_sha256": data["artifact"]["sha256"]},
              "command": {"version": "1.7"}, "host": {"hostname": "fixture"},
              "matrix": [{"cell": "fixture", "status": "passed"}],
              "negative_controls": [{"id": "fixture", "status": "rejected"}],
              "verdict": "certified", "evidence_basis": "simulated", "evidence_kind": "contract_fixture"}
    result = run_swdb("add", "--records", records, "--db", root / "build" / "swdb.sqlite", _payload(root, rid, record))
    assert result.returncode == 0, result.stderr


@pytest.fixture(scope="module")
def wp_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("wp-seed")
    return path, build_wp_seed(path)


class Seed:
    def __init__(self, root, candidates):
        self.root, self.candidates = root, candidates
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def swdb(self, command, *args, env=None):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args, env=env)

    def hints(self, name, hints):
        path = self.root / f"hints-{name}.yaml"
        path.write_text(yaml.safe_dump({"hints": hints}))
        return path

    def prove(self, candidate="safe", function="swdb_fixture_fill", contract=FILL, hints=FILL_HINTS, *extra,
              env=None, ok=True):
        args = ["--candidate", self.candidates[candidate], "--function", function, "--contract", contract,
                "--adapter", "wp", "--runs-dir", self.runs, "--format", "json"]
        if hints is not None:
            args += ["--hint-file", self.hints(f"{candidate}-{function}-{len(hints)}", hints)]
        result = self.swdb("prove", *args, *extra, env=env)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout) if ok else result

    def read(self, out):
        return yaml.safe_load((self.records / out["path"]).read_text())


@pytest.fixture
def seed(wp_seed, tmp_path):
    source, candidates = wp_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


# --- the safe fixture --------------------------------------------------------------------------------------

@needs_wp
def test_the_safe_fixture_is_proven_with_threads_1_bounds_per_goal_solvers_and_trusted_tools(seed):
    out = seed.prove()
    record = seed.read(out)
    assert record["verdict"] == "proven" and record["job"]["adapter"] == "wp"
    assert record["bounds"] == {"threads": 1, "input_size": "unbounded"}
    assert record["evidence_kind"] == "contract_fixture"          # a fixture method version gives fixture evidence
    goals = record["goals"]
    assert goals and all(g["status"] == "valid" and g["solver"] and g["seconds"] >= 0 for g in goals)
    assert {g["solver"] for g in goals} <= {"qed", "alt-ergo", "z3", "cvc5"}
    assert {a["reference"]["id"] for a in record["assumptions"] if a["kind"] == "trusted_tool"} == TRUSTED
    assert set(record["tools"]) == TRUSTED
    assert all(a["sentence"].strip() for a in record["assumptions"])
    assert record["pins"]["c_lowering"]["id"] == "swdb_fixture_fill.c"
    from swdb import c_lowering                                   # ticket 24: the naming rules are pinned too
    assert record["pins"]["naming_rules"] == {"id": "kept-names.2", "sha256": c_lowering.RULES_SHA256}
    settings = record["settings"]
    for flag in ("-wp-cache none", "-wp-model +real", "-machdep x86_64", "-wp-timeout 30"):
        assert flag in " ".join(settings["flags"])
    assert settings["session"] == "fresh" and settings["warning_levels"] == "default"
    for report in record["evidence"]["reports"]:                 # WP log and per-goal report: outside the repo
        assert report["path"].startswith(str(seed.runs)) and \
            hashlib.sha256(open(report["path"], "rb").read()).hexdigest() == report["sha256"]
    assert {r["name"] for r in record["evidence"]["reports"]} >= {"wp_input", "wp_log", "wp_goals", "wp_properties"}
    assert not (seed.runs / record["id"] / "scratch").exists()   # no WP or Why3 scratch left
    assert seed.swdb("validate").returncode == 0
    built = seed.swdb("build")
    assert built.returncode == 0, built.stderr
    level = seed.swdb("candidate-level", seed.candidates["safe"], "--format", "json")
    assert level.returncode == 0, level.stderr
    assert json.loads(level.stdout)["level"] == "proven_within_bounds_threads_1"   # threads = 1, never unbounded


# --- the seeded bug and map 07's smoke pair ------------------------------------------------------------------

def _handler(record):
    return json.loads(open(next(r["path"] for r in record["evidence"]["reports"] if r["name"] == "handler")).read())


@needs_wp
def test_the_seeded_bug_is_not_proven_with_a_class_and_its_unproven_properties_never_refuted(seed):
    record = seed.read(seed.prove("bug"))
    assert record["verdict"] == "not_proven" and record["failure_class"] in ("timeout", "unknown")
    assert "counterexample" not in record and "unreplayed_counterexample" not in record
    unproven = record["unproven_properties"]
    assert any(p["kind"] == "postcondition" and "∀" in p["property"] for p in unproven), unproven
    handler = _handler(record)
    assert handler["failure_class"] == record["failure_class"] and handler["for_hint_loop"]   # goals for the hint loop
    level = seed.swdb("candidate-level", seed.candidates["bug"], "--format", "json")
    assert json.loads(level.stdout)["level"] == "certified"


@needs_wp
def test_map_07_smoke_pair_proves_the_safe_program_and_leaves_the_seeded_bug_not_proven(seed):
    safe = SMOKE_HINTS + _hints("count_up.s2.after", "assert i == n;")
    buggy = SMOKE_HINTS + _hints("count_up.s2.after", "assert i == n + 1;")
    proven = seed.read(seed.prove("safe", "count_up", SMOKE, safe))
    assert proven["verdict"] == "proven"
    record = seed.read(seed.prove("safe", "count_up", SMOKE, buggy))
    assert record["verdict"] == "not_proven" and record["failure_class"] in ("timeout", "unknown")
    assert "counterexample" not in record
    assert [p["kind"] for p in record["unproven_properties"]].count("user assertion") == 1


# --- failure classes: each on a fixture or a scripted fault -------------------------------------------------

FAKE = f"{sys.executable} {WP / 'fake_framac.py'}"


def fake(mode, **more):
    """The environment of a scripted WP fault (non-WP Frama-C calls pass through to the real one)."""
    from swdb import framac
    return {"SWDB_FRAMA_C": FAKE, "FAKE_WP_MODE": mode, "FAKE_WP_REAL": " ".join(framac.locate().command), **more}


@needs_wp
def test_a_wp_user_error_is_a_parse_error_with_a_minimal_reproduction(seed):
    """Updated 2026-10-14 ET (ticket 35): a hint Frama-C cannot parse no longer reaches WP (the proof hint check
    rejects it); WP's own user error (a scripted fault) still reads as parse_error."""
    record = seed.read(seed.prove(env=fake("user_error")))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "parse_error"
    handler = _handler(record)
    assert "wp_input.c" in handler["minimal_reproduction"] and "command.txt" in handler["minimal_reproduction"]


@needs_wp
def test_a_hint_with_an_unbounded_assigns_range_never_reaches_wp(seed):
    """Ticket 07: WP 33 aborts on an infinite range in `loop assigns`. Updated 2026-10-14 ET (ticket 35): the proof
    hint check rejects it (rule unbounded_range) and WP runs without the hint set."""
    hints = FILL_HINTS[:2] + _hints("swdb_fixture_fill.loop1.head", "loop assigns i, a[0 ..];", "loop variant n - i;")
    record = seed.read(seed.prove(hints=hints, env=fake("unknown")))
    assert [(r["hint"], r["rule"]) for r in record["hint_check"]["rejections"]] == [(2, "unbounded_range")]
    assert "a[0 ..]" not in open(next(r["path"] for r in record["evidence"]["reports"] if r["name"] == "wp_input")).read()


@needs_wp
def test_a_function_outside_the_core_subset_is_unsupported_construct_before_any_wp_run(seed):
    record = seed.read(seed.prove("safe", "InitParent", FILL, []))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert "settings" not in record                                 # WP never ran


@needs_wp
def test_a_job_the_watchdog_kills_reads_not_proven_out_of_memory(seed):
    record = seed.read(seed.prove(env={"SWDB_VERIFIER_RSS_CAP_BYTES": str(20 * 2**20)}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "out_of_memory"


@needs_wp
@pytest.mark.parametrize("mode, failure_class", [("unknown", "unknown"), ("solver_error", "solver_error"),
                                                 ("crash", "tool_crash")])
def test_scripted_wp_faults_map_to_their_class_and_run_its_handler(seed, mode, failure_class):
    record = seed.read(seed.prove(env=fake(mode)))
    assert record["verdict"] == "not_proven" and record["failure_class"] == failure_class
    handler = _handler(record)
    assert handler["failure_class"] == failure_class and handler["handler"]


@needs_wp
def test_an_outcome_with_no_class_stops_the_batch_and_writes_no_record(seed):
    result = seed.prove(env=fake("silent"), ok=False)
    assert result.returncode == 1 and "unclassified_wp_outcome" in result.stderr and "batch stops" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


@needs_wp
def test_installed_tools_that_differ_from_the_method_versions_lineup_run_nothing(seed):
    path = seed.root / "library" / "methods" / "wp-tracer-fixture.yaml"
    data = yaml.safe_load(path.read_text())
    next(row for row in data["lineup"] if row["tool"] == "z3")["version"] = "4.8.14"
    data.update(id="method.wp-tracer-other", sequence=3)
    (path.parent / "wp-tracer-other.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    result = seed.prove(ok=False)
    assert "z3 5.1.0 is installed but method version method.wp-tracer-other pins 4.8.14" in result.stderr


# --- the machine-wide lock ------------------------------------------------------------------------------------

@needs_wp
def test_two_real_wp_jobs_started_together_never_overlap(seed, tmp_path):
    times = tmp_path / "times.txt"
    env = fake("wrap", FAKE_WP_TIMES=str(times))
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
    assert first["end"] <= second["start"], spans                # checked from outside: one after the other


# --- the regression corpus ------------------------------------------------------------------------------------

CORPUS = sorted((FIXTURES / "proof" / "regression_corpus").glob("*.yaml"))


@needs_wp
@pytest.mark.parametrize("case", [c for c in CORPUS if yaml.safe_load(c.read_text())["adapter"] == "wp"],
                         ids=lambda c: c.stem)
def test_each_wp_regression_corpus_case_gives_its_recorded_class_again(seed, case):
    data = yaml.safe_load(case.read_text())
    assert data["cause"].strip()
    given = data["input"]
    if "hint_rule" in data:          # ticket 35: the proof hint check catches it before WP (scripted WP run)
        record = seed.read(seed.prove(given["candidate"], given["function"], given["contract"], given["hints"],
                                      env=fake("unknown")))
        assert data["hint_rule"] in {r["rule"] for r in record["hint_check"]["rejections"]}
        assert not record["hint_check"]["reached_wp"]
        return
    record = seed.read(seed.prove(given["candidate"], given["function"], given["contract"], given.get("hints") or []))
    assert record.get("failure_class") == data["failure_class"]

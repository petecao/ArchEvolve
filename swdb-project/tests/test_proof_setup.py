"""Proof setup and fresh WP verdicts through swdb prove (ticket 36). Created: 2026-10-15 ET.

Agreed seam: swdb prove -> validated record, with scripted adapters for prelaunch negative
controls and actual WP fact fixtures for verdict independence. No private-helper assertions.
"""
import json
from pathlib import Path

import pytest

from test_proof_records import proof_seed, seed  # public CLI seed


@pytest.mark.parametrize("flags", [[], ["--unwinding-assertions"],
    ["--unwinding-assertions", "--pointer-overflow-check", "--no-pointer-check"],
    ["--unwinding-assertions", "--pointer-overflow-check", "--no-standard-checks"],
    ["--unwinding-assertions", "--pointer-overflow-check", "--property=harmless"],
    ["--unwinding-assertions", "--pointer-overflow-check", "--function", "harmless"]])
def test_bounded_flags_cannot_omit_pointer_formation_or_hide_safety_properties(seed, flags):
    marker = seed.root / "must-not-run"
    failed = seed.prove(seed.script(setup={"tool": "cbmc", "flags": flags},
                                   run=["/usr/bin/touch", str(marker)]), ok=False)
    assert "cbmc_safety_flags" in failed.stderr
    assert not marker.exists() and not seed.proof_files()


@pytest.mark.parametrize("text", [
    "void f(int parent) { __CPROVER_assume(parent >= -1); }\n",
    "llvm_assume (llvm_term {{ parent_v >= -1 }});\n",
])
def test_scripted_bounded_job_rejects_unattributed_harness_assume_before_command(seed, text):
    marker = seed.root / "must-not-run"
    harness = seed.root / "harness.c"
    harness.write_text(text)
    script = seed.script(setup={"tool": "saw", "inputs": [{"path": str(harness)}]},
                         run=["/usr/bin/touch", str(marker)])
    failed = seed.prove(script, ok=False)
    assert "proof setup check" in failed.stderr
    assert "assumption_provenance" in failed.stderr
    assert not marker.exists()
    assert not seed.proof_files()


def test_successful_scripted_proof_records_versioned_setup_and_method_hash(seed):
    record = seed.prove(seed.script())["record"]
    assert record["proof_setup_check"]["verdict"] == "passed"
    assert record["proof_setup_check"]["check"]["version"] == "1"
    assert record["proof_setup_check"]["method_version"] == record["pins"]["method_version"]
    assert len(record["proof_setup_check"]["check"]["sha256"]) == 64


def _reports(seed, goals, inventory=None, properties=None):
    root = seed.root / "reports"
    root.mkdir(exist_ok=True)
    goalfile, propfile, invfile = (root / n for n in ("goals.json", "props.csv", "inventory.json"))
    goalfile.write_text(json.dumps(goals))
    propfile.write_text("directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n" +
                        "\n".join(f".\twp_input.c\t1\tf\tpostcondition\t{s}\t{p}" for p, s in properties or [("f_ensures", "Valid")]))
    invfile.write_text(json.dumps(inventory or {"version": "1", "complete": True,
        "goals": [{**g, "results": [g.get("verdict", "valid")]} for g in goals], "properties": []}))
    return {"goals": str(goalfile), "properties": str(propfile), "inventory": str(invfile), "functions": ["f"]}


def _valid(name="typed_f_ensures", **kw):
    return {"goal": name, "property": name.removeprefix("typed_"), "function": "f", "smoke": False,
            "passed": True, "verdict": "valid", **kw}


def test_fresh_reader_accepts_directly_proved_automatic_goals_omitted_by_wp_json(seed):
    goal = _valid()
    inventory = {"version": "1", "complete": True, "goals": [
        {**goal, "results": ["valid"]},
        {**_valid("typed_f_terminates"), "results": ["valid"]}], "properties": []}
    reports = _reports(seed, [goal], inventory)
    record = seed.prove(seed.script(wp_reports=reports))["record"]
    assert record["verdict"] == "proven"
    assert record["verdict_reading"]["check"]["version"] == "1"
    assert {g["goal"] for g in record["goals"]} == {"typed_f_ensures", "typed_f_terminates"}


def test_fresh_reader_keeps_multiline_csv_properties_attached_to_their_function(seed):
    reports = _reports(seed, [_valid()])
    with open(reports["properties"], "a") as stream:
        stream.write("\n.\twp_input.c\t20\tunused_model\tcomplete behaviors\tIgnored\tcomplete\n"
                     " allocation, no_allocation\n")
    record = seed.prove(seed.script(wp_reports=reports))["record"]
    assert record["verdict"] == "proven"


@pytest.mark.parametrize("failure", ["lemma", "call_precondition", "callee_termination", "missing_goal"])
def test_locally_valid_target_cannot_hide_an_unproved_premise(seed, failure):
    target = _valid()
    premise = _valid("typed_lemma_unproved" if failure == "lemma" else f"typed_f_{failure}",
                     passed=False, verdict="timeout", function=None if failure == "lemma" else "f")
    goals = [target] + ([] if failure == "missing_goal" else [premise])
    inventory = {"version": "1", "complete": True, "goals": [
        {**target, "results": ["valid"]}, {**premise, "results": ["timeout"]}], "properties": []}
    record = seed.prove(seed.script(wp_reports=_reports(seed, goals, inventory)))["record"]
    assert record["verdict"] == "not_proven"
    assert record["failure_class"] == ("unknown" if failure == "missing_goal" else "timeout")
    assert record["unproven_properties"][0]["goal"] == premise["goal"]


@pytest.mark.parametrize("kind", ["admit", "axiom", "lemma"])
def test_unexpected_extern_stops_batch_even_when_target_valid(seed, kind):
    target = _valid()
    inventory = {"version": "1", "complete": True, "goals": [{**target, "results": ["valid"]}],
                 "properties": [{"property": "injected", "kind": kind, "extern": True}]}
    failed = seed.prove(seed.script(wp_reports=_reports(seed, [target], inventory)), ok=False)
    assert "unexpected_extern" in failed.stderr
    assert not seed.proof_files()


@pytest.mark.parametrize("kind", ["contradictory_preconditions", "contradictory_invariants"])
def test_failed_smoke_goal_voids_locally_valid_proof(seed, kind):
    target, smoke = _valid(), _valid(f"typed_f_wp_smoke_{kind}", smoke=True, passed=False)
    record = seed.prove(seed.script(wp_reports=_reports(seed, [target, smoke])))["record"]
    assert record["verdict"] == "not_proven"
    assert record["failure_class"] == "vacuous_pass"


@pytest.mark.parametrize("flags,rule", [
    (["-wp-cache", "update"], "frozen_flags"),
    (["-wp-cache", "offline"], "frozen_flags"),
    (["-machdep", "x86_32"], "frozen_flags"),
    (["-kernel-warn-key", "ghost:bad-use=active"], "warning_defaults"),
    (["-kernel-warn-key", "annot-error=active"], "warning_defaults"),
    (["-wp-prop=-@lemma"], "property_selection"),
])
def test_wp_setup_refuses_overrides_before_any_verifier_runs(seed, flags, rule):
    marker = seed.root / "must-not-run"
    frozen = ["-wp-cache", "none", "-wp-model", "+real", "-machdep", "x86_64"]
    script = seed.script(setup={"tool": "wp", "flags": frozen + flags}, run=["/usr/bin/touch", str(marker)])
    failed = seed.prove(script, ok=False)
    assert rule in failed.stderr
    assert not marker.exists()


@pytest.mark.parametrize("name", ["FRAMAC_WP_CACHE", "FRAMAC_WP_CACHEDIR", "FRAMAC_WP_SCRIPT"])
def test_setup_refuses_wp_environment_even_for_scripted_bounded_job(seed, monkeypatch, name):
    monkeypatch.setenv(name, "unsafe")
    failed = seed.prove(seed.script(), ok=False)
    assert "wp_environment" in failed.stderr
    assert name in failed.stderr


@pytest.mark.parametrize("control,rule", [
    ({"clauses": [{"id": "requires_parent"}]}, "proof_placement"),
    ({"probes": [{"id": "f.probe1", "origin": "hint"}]}, "hazard_probes"),
    ({"probes": [{"id": "f.probe1", "origin": "generator"}]}, "hazard_probes"),
])
def test_setup_refuses_missing_placement_or_non_generated_probe(seed, control, rule):
    failed = seed.prove(seed.script(setup=control), ok=False)
    assert rule in failed.stderr


def test_planned_input_hash_detects_changed_lowering(seed):
    source = seed.root / "lowering.c"
    source.write_text("int f(void) {return 1;}\n")
    failed = seed.prove(seed.script(setup={"inputs": [{"path": str(source), "sha256": "a" * 64}]}), ok=False)
    assert "input_hash" in failed.stderr


@pytest.mark.parametrize("case,expected", [(0, "proven"), (1, "not_proven"), (2, "not_proven"),
    (3, "not_proven"), (4, "unexpected_extern"), (5, "unexpected_extern"),
    (6, "vacuous_pass"), (7, "vacuous_pass"), (8, "proven"), (9, "not_proven"), (10, "not_proven"), (11, "not_proven"), (12, "unexpected_extern")])
def test_real_wp_facts_read_fresh_goals_and_premises(seed, case, expected):
    from conftest import REPO, FIXTURES
    from swdb import framac
    import sys
    if framac.locate().missing:
        pytest.skip(framac.locate().missing)
    reports = {"goals": "goals.json", "properties": "properties.csv", "inventory": "inventory.json", "functions": ["f", "g"]}
    if case == 8:
        reports["extern_contracts"] = {"maa_summary": {"id": "semantics.fixture", "sha256": "a" * 64}}
    script = seed.script(run=[sys.executable, str(FIXTURES / "proof" / "wp" / "setup_fact_driver.py"), str(REPO), str(case)],
                         wp_reports=reports)
    if expected == "unexpected_extern":
        failed = seed.prove(script, ok=False)
        assert expected in failed.stderr
    else:
        record = seed.prove(script)["record"]
        assert record["verdict"] == ("not_proven" if expected == "vacuous_pass" else expected)
        if expected == "vacuous_pass":
            assert record["failure_class"] == expected
        if case == 8:
            assert any(a["reference"]["id"] == "semantics.fixture" for a in record["assumptions"])
        if case == 11:
            log = Path(record["evidence"]["adapter_log"]["path"]).read_text()
            assert "tampered actual WP cache entries:" in log
            assert "[Cache]" in log


def test_an_unclassified_property_cannot_hide_behind_an_unrelated_timeout(seed):
    target = _valid()
    failure = _valid("typed_f_other", passed=False, verdict="timeout")
    reports = _reports(seed, [target, failure], properties=[("unclassified property", "Unknown")])
    failed = seed.prove(seed.script(wp_reports=reports), ok=False)
    assert "unclassified_wp_outcome" in failed.stderr


def test_existing_wp_session_stops_before_invoking_verifier(seed):
    marker = seed.root / "must-not-run"
    plan = {"tool": "wp", "flags": ["-wp-cache", "none", "-wp-model", "+real", "-machdep", "x86_64"],
            "work_files": {".frama-c/session.json": "{\"verdict\":\"valid\"}"}}
    failed = seed.prove(seed.script(setup=plan, run=["/usr/bin/touch", str(marker)]), ok=False)
    assert "fresh_session" in failed.stderr
    assert not marker.exists()


def test_setup_failure_stops_batch_without_starting_later_jobs(seed):
    bad = seed.script("bad", setup={"probes": [{"id": "missing", "origin": "generator"}]})
    marker = seed.root / "later-job"
    later = seed.script("later", run=["/usr/bin/touch", str(marker)])
    failed = seed.prove(bad, "--script", later, ok=False)
    assert "hazard_probes" in failed.stderr
    assert not marker.exists()
    assert not seed.proof_files()


def test_job_plan_pin_cannot_be_replaced_with_different_run_settings(seed):
    failed = seed.prove(seed.script(setup={"run_plan_sha256": "a" * 64}), ok=False)
    assert "run_plan_hash" in failed.stderr


def test_solver_portfolio_reordering_is_refused_even_with_the_same_solver_set(seed):
    frozen = ["-wp-cache", "none", "-wp-model", "+real", "-machdep", "x86_64"]
    failed = seed.prove(seed.script(setup={"tool": "wp", "flags": frozen + ["-wp-prover", "z3,alt-ergo,cvc5"]}), ok=False)
    assert "solver order differs" in failed.stderr


@pytest.mark.parametrize("change", ["version", "sha256"])
def test_execution_method_must_pin_the_running_checks_version_and_content(seed, change):
    import yaml
    from swdb import proof_setup
    path = seed.root / "library" / "methods" / "contract-fixture-1.yaml"
    data = yaml.safe_load(path.read_text())
    data.update(id="method.setup-control", sequence=3, evidence_kind="execution")
    data["checks"].update(proof_setup.identity())
    data["checks"]["proof_setup_check"][change] = "wrong" if change == "version" else "f" * 64
    (path.parent / "setup-control.yaml").write_text(yaml.safe_dump(data))
    failed = seed.prove(seed.script(), ok=False)
    assert "method_version" in failed.stderr
    assert "does not pin the installed proof_setup_check" in failed.stderr


@pytest.mark.parametrize("changed", ["swdb/cbmc_adapter.py", "swdb/cbmc_equivalence.py", "swdb/wp_adapter.py",
    "swdb/crux_adapter.py", "swdb/rocq_adapter.py", "swdb/proof.py", "vocab/proof_failure_classes.yaml",
    "swdb/cbmc_product.py", "swdb/rss_watchdog.py", "swdb/vocab.py", "swdb/formal_frame.py", "swdb/acsl_subset.py",
    "swdb/framac.py", "swdb/hint_check.py", "swdb/hint_tree.ml"])
def test_changed_verdict_reader_or_failure_vocabulary_invalidates_frozen_method_before_invocation(seed, changed):
    import os
    import shutil
    import subprocess
    import sys
    import yaml
    from conftest import REPO
    from swdb import proof_setup
    from test_proof_records import FUNCTION

    path = seed.root / "library" / "methods" / "reader-control.yaml"
    data = yaml.safe_load((path.parent / "contract-fixture-1.yaml").read_text())
    data.update(id="method.reader-control", sequence=3, evidence_kind="execution")
    data["checks"].update(proof_setup.identity())
    path.write_text(yaml.safe_dump(data))
    runtime = seed.root / "changed-runtime"
    for folder in ("swdb", "schemas", "vocab"):
        shutil.copytree(REPO / folder, runtime / folder, ignore=shutil.ignore_patterns("__pycache__"))
    # Keep the repository's pinned resource roots while selecting the copied
    # vocabulary. This tests installed reader bytes without cloning provenance data.
    paths = runtime / "swdb" / "paths.py"
    paths.write_text(paths.read_text() + '\nVOCAB = Path(__file__).resolve().parent.parent / "vocab"\n')
    target = runtime / changed
    suffix = b"\n(* changed verdict dependency *)\n" if target.suffix == ".ml" else b"\n# changed verdict dependency\n"
    target.write_bytes(target.read_bytes() + suffix)
    marker = seed.root / "must-not-run"
    script = seed.script(run=["/usr/bin/touch", str(marker)])
    result = subprocess.run([sys.executable, "-m", "swdb", "prove", "--records", str(seed.records),
        "--candidate", seed.candidate, "--function", FUNCTION, "--adapter", "scripted", "--script", str(script),
        "--runs-dir", str(seed.runs), "--format", "json", "--method-version", "method.reader-control"],
        cwd=runtime, env={**os.environ, "SWDB_HOME": str(REPO), "PYTHONPATH": str(runtime)},
        capture_output=True, text=True, timeout=60)
    assert result.returncode != 0, result.stdout
    assert "does not pin the installed" in result.stderr, result.stderr
    assert not marker.exists() and not seed.proof_files()

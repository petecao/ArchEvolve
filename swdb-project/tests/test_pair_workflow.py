"""Pair-only public lowering/proof workflow; created 2026-10-15 ET.

Ordinary tests invoke Clang and a parser-error Frama stand-in, never a solver.
Set SWDB_PAIR_ACTUAL=1 only inside a coordinator-admitted actual verifier profile.
Collection performs no tool discovery or version probes.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb

SOURCE = FIXTURES / "proof/lowering/pair_only.cc"
MEMBERS = tuple("std_pair_int_int_" + name for name in
                ("ctor_default", "ctor", "copy_ctor", "operator_assign"))
CONTRACT = "contract.fixture_pair_values"


def _lower(source, function, out, *, ok=True):
    done = run_swdb("lower", "--source", source, "--function", function,
                    "--out", out, "--format", "json")
    assert (done.returncode == 0) is ok, done.stdout + done.stderr
    return json.loads(done.stdout) if ok else done


def _seed(root, *, actual=False, source=SOURCE):
    """Small library/empty store: no catalog, candidate or unrelated vector fixture."""
    from swdb import c_lowering, std_models
    records = make_records(root)
    records.path.mkdir(exist_ok=True)
    library = root / "library"
    methods = library / "methods"
    methods.mkdir(parents=True)
    method = yaml.safe_load((FIXTURES / "proof/methods/contract-fixture-1.yaml").read_text())
    method.update(id="method.pair-workflow-fixture", sequence=2,
                  description="2026-10-15 ET: pair-only original body and caller contract fixture.")
    method["lineup"] = yaml.safe_load((REPO / "library/methods/probata-draft-1.yaml").read_text())["lineup"]
    next(row for row in method["lineup"] if row["tool"] == "frama-c-wp")["flags"] += [
        "-rte-initialized", "@all", "-wp-no-filter-init"]
    method["c_lowering"]["translators"] = [c_lowering.identity()["c_lowering"]]
    method["models"].update(std_vector=std_models.identity(), std_pair=std_models.identity())
    (methods / "pair-workflow-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    units = library / "proof_units"
    units.mkdir()
    shutil.copy(source, units / "pair_only.cc")
    clauses = [("pre", "legality", r"requires -1000 <= x <= 1000 && -1000 <= y <= 1000;"),
               ("post", "postcondition", r"assigns \nothing; ensures \result == 3*x+y;")]
    entry = {
        "kind": "rewrite_contract", "id": CONTRACT, "formal_frame": 1, "version": "1.0",
        "provenance": {"origin": {"intrinsic_specification": "pair-only-fixture-20261015"}},
        "proof_unit": {"function": "swdb_pair_values", "source": {"root": "library",
            "path": "proof_units/pair_only.cc", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}},
        "concurrency_frame": [],
        "clauses": [{"id": name, "role": role, "statement": "Pair fixture " + name,
            "discharge_mode": "runtime_guard", "negative_control": {"id": name + "-control", "check": name},
            "acsl": {"text": text, "uses": []}, "proof_placement": {"once": "self"}}
            for name, role, text in clauses],
        "pattern_key": [{"roles": ["index", "target"], "address_shapes": ["stream", "single_valued_indirect"],
                         "update_kind": "read"}],
        "strategies": [], "uses_intrinsics": [], "uses_library_operations": [], "runtime_guards": [],
        "knobs": [], "preservation_obligations": [], "correctness_check": {"kernel": "fixture", "check": "fixture"},
        "execution_witness": {"check": "fixture"},
        "negative_controls": [{"id": kind, "kind": kind, "check": "fixture"}
            for kind in ("overlapping_pointer", "double_claim", "dropped_operand")], "requirement_map": []}
    contracts = library / "rewrite_contracts"
    contracts.mkdir()
    (contracts / "fixture_pair_values.yaml").write_text(yaml.safe_dump(entry, sort_keys=False))
    wrong = json.loads(json.dumps(entry))
    wrong["id"] = "contract.fixture_pair_wrong_field"
    wrong["proof_unit"]["function"] = "swdb_pair_wrong_field"
    (contracts / "fixture_pair_wrong_field.yaml").write_text(yaml.safe_dump(wrong, sort_keys=False))
    marker = root / "standin-parser-launched"
    env = {}
    if not actual:
        frama = root / "frama-standin.py"
        frama.write_text('import sys\nfrom pathlib import Path\n'
            'if "-version" in sys.argv: print("33.0");sys.exit(0)\n'
            'if "-wp" in sys.argv:\n'
            f' Path({str(marker)!r}).write_text("parser-error stand-in; no solver")\n'
            ' print("[kernel] wp_input.c:3: User Error: scripted fault\\nFrama-C aborted: invalid user input.");sys.exit(1)\n')
        names = {"alt-ergo": "Alt-Ergo", "z3": "Z3", "cvc5": "CVC5"}
        config = root / "why3-standin.conf"
        config.write_text("".join(f'[prover]\nname = "{names[row["tool"]]}"\nversion = "{row["version"]}"\n'
            'command = "/usr/bin/false"\n' for row in method["lineup"] if row["tool"] in names))
        env = {"SWDB_FRAMA_C": f"{sys.executable} {frama}", "WHY3CONFIG": str(config),
               "SWDB_VERIFIER_LOCK": str(root / "standin-only.lock")}

    def prove(*args, ok=True, extra_env=None, runtime=None):
        timeout = 600
        if actual:
            deadline = float(os.environ["SWDB_PAIR_DEADLINE_MONOTONIC"])
            remaining = deadline - time.monotonic()
            assert remaining > 15, "actual pair profile exhausted its prospective wall budget"
            # Leave setup/record-writing headroom; the actual adapter's own
            # process-tree watchdog enforces the remaining per-job allocation.
            args = (*args, "--budget-minutes", str((remaining - 15) / 60))
            timeout = remaining
        command = ("prove", "--records", records.path, "--adapter", "wp",
                   "--method-version", method["id"], "--runs-dir", root / "runs", "--format", "json", *args)
        selected_env = {**env, **(extra_env or {})}
        if runtime:
            done = subprocess.run([sys.executable, "-m", "swdb", *map(str, command)], cwd=runtime,
                                  env={**os.environ, **selected_env}, capture_output=True, text=True, timeout=timeout)
        else:
            done = run_swdb(*command, env=selected_env, timeout=timeout)
        if not ok:
            return done
        assert done.returncode == 0, done.stdout + done.stderr
        return yaml.safe_load((records.path / json.loads(done.stdout)["path"]).read_text())
    return prove, marker


def test_public_pair_lowering_preserves_values_copies_fields_and_self_assignment(tmp_path):
    from swdb import c_lowering
    compiler = c_lowering.locate().command[0]
    functions = ("swdb_pair_values", "swdb_pair_self_assign", "swdb_pair_default")
    lowered = {}
    for function in functions:
        out = tmp_path / function
        report = _lower(SOURCE, function, out)
        assert report["bounded_initialization"]["verdict"] == "passed", json.dumps(report["bounded_initialization"])
        lowered[function] = out / (function + ".c")
    # Each independent executable checks both representations against literal
    # worked examples; the grid then extends finite agreement to 25 pairs.
    for function, expected in ((functions[0], "3*x+y"), (functions[1], "y"), (functions[2], "0")):
        args = "" if function == functions[2] else "x,y"
        harness = ('#include <stdio.h>\nint main(void){int vals[]={-1000,-7,0,11,1000};'
                   'for(int i=0;i<5;i++)for(int j=0;j<5;j++){int x=vals[i],y=vals[j];'
                   f'int r={function}({args}); if(r!=({expected}))return 2;printf("%d\\n",r);}}}}\n')
        outputs = []
        for language, include, flags in (("cxx", SOURCE, ["-std=c++17"]),
                                          ("c", lowered[function], ["-std=c11"])):
            unit = tmp_path / (function + "." + ("cc" if language == "cxx" else "c"))
            unit.write_text(f'#include "{include}"\n' + harness)
            binary = tmp_path / (function + "-" + language)
            tool = compiler if language == "cxx" else compiler.replace("clang++", "clang")
            built = subprocess.run([tool, *flags, "-O1", "-fsanitize=address,undefined",
                                    "-fno-sanitize-recover=all", str(unit), "-o", str(binary)],
                                   capture_output=True, text=True)
            assert built.returncode == 0, built.stderr
            done = subprocess.run([binary], capture_output=True, text=True)
            assert done.returncode == 0, done.stderr
            outputs.append(done.stdout)
        assert outputs[0] == outputs[1] and len(outputs[0].splitlines()) == 25


def test_uninitialized_pair_constructor_input_is_refused_by_public_lowering(tmp_path):
    report = _lower(SOURCE, "swdb_pair_uninitialized", tmp_path / "lower")["bounded_initialization"]
    assert report["verdict"] == "refused" and "initializ" in report["reason"].lower(), report


@pytest.mark.parametrize("operation", ["copy", "assignment", "field_write"])
def test_pair_copy_and_assignment_do_not_initialize_unknown_source_storage(tmp_path, operation):
    statements = {
        "copy": "std::pair<int,int> copied(*source); return copied.first;",
        "assignment": "std::pair<int,int> target; target=*source; return target.second;",
        "field_write": "std::pair<int,int> target; int missing; target.first=missing; return target.first;",
    }
    source = tmp_path / "unknown.cc"
    source.write_text('#include <utility>\nint unknown(std::pair<int,int>*source){' + statements[operation] + '}\n')
    report = _lower(source, "unknown", tmp_path / "lower")["bounded_initialization"]
    assert report["verdict"] == "refused", report


def test_wrong_pair_field_has_a_defined_concrete_witness(tmp_path):
    from swdb import c_lowering
    compiler = c_lowering.locate().command[0]
    unit = tmp_path / "witness.cc"
    unit.write_text(f'#include "{SOURCE}"\nint main(){{return swdb_pair_values(2,5)==11 && '
                    'swdb_pair_wrong_field(2,5)==17 ? 0 : 1;}\n')
    binary = tmp_path / "witness"
    done = subprocess.run([compiler, "-std=c++17", "-fsanitize=address,undefined",
                           "-fno-sanitize-recover=all", unit, "-o", binary], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    done = subprocess.run([binary], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_pair_caller_without_current_member_proofs_never_launches_standin(tmp_path):
    prove, marker = _seed(tmp_path)
    done = prove("--summary", CONTRACT, ok=False)
    assert done.returncode != 0
    assert "no proven record at its current text" in done.stderr, done.stderr
    assert "std_pair_int_int_" in done.stderr
    assert not marker.exists()


def test_changed_initializedness_source_invalidates_frozen_translator_before_standin(tmp_path):
    prove, marker = _seed(tmp_path)
    runtime = tmp_path / "changed-runtime"
    for folder in ("swdb", "schemas", "vocab"):
        shutil.copytree(REPO / folder, runtime / folder, ignore=shutil.ignore_patterns("__pycache__"))
    policy = runtime / "swdb/bounded_std_initialization.py"
    policy.write_text(policy.read_text() + "\n# 2026-10-15 ET: source identity mutation control.\n")
    refused = prove("--model", MEMBERS[0], ok=False,
                    extra_env={"PYTHONPATH": str(runtime), "SWDB_HOME": str(REPO)}, runtime=runtime)
    assert refused.returncode != 0
    assert "translat" in refused.stderr.lower(), refused.stderr
    assert not marker.exists()


@pytest.mark.parametrize("member", MEMBERS)
def test_each_original_pair_body_reaches_public_parser_with_initialization_rte_and_smoke(tmp_path, member):
    from swdb import c_lowering
    prove, marker = _seed(tmp_path)
    record = prove("--model", member)
    assert marker.exists()
    assert record["subject"] == {"kind": "c_model", "id": member}
    assert record["verdict"] == "not_proven" and record["failure_class"] == "parse_error", record
    assert record["pins"]["code"]["sha256"] == hashlib.sha256(c_lowering.model_text(member).encode()).hexdigest()
    assert record["proof_setup_check"]["verdict"] == "passed"
    flags = record["settings"]["flags"]
    assert all(flag in flags for flag in ("-wp-rte", "-rte-initialized", "-wp-no-filter-init", "-wp-smoke-tests"))


@pytest.mark.skipif(os.environ.get("SWDB_PAIR_ACTUAL") != "1", reason="requires explicit coordinator actual admission")
def test_actual_four_pair_bodies_then_unchanged_caller_pin_current_proof_dependencies(tmp_path):
    from swdb import c_lowering
    prove, _ = _seed(tmp_path, actual=True)
    retained = []

    def retain(*args):
        record = prove(*args)
        retained.append(record)
        # Completed records remain inspectable after a later profile failure.
        (tmp_path / "actual-pair-progress.json").write_text(json.dumps([
            {"id": row["id"], "subject": row["subject"], "verdict": row["verdict"], "pins": row["pins"]}
            for row in retained], indent=2) + "\n")
        return record

    models = {member: retain("--model", member) for member in MEMBERS}
    for member, record in models.items():
        assert record["verdict"] == "proven", (member, record)
        assert record["subject"] == {"kind": "c_model", "id": member}
        assert record["pins"]["code"]["sha256"] == hashlib.sha256(c_lowering.model_text(member).encode()).hexdigest()
        assert record["goals"] and all(goal["status"] == "valid" for goal in record["goals"])
    caller = retain("--summary", CONTRACT)
    assert caller["verdict"] == "proven", caller
    pinned = {row["id"]: row for row in caller["pins"]["models"]}
    assert set(pinned) == set(MEMBERS)
    for member, record in models.items():
        assert pinned[member]["proof_record"] == record["id"]
        assert pinned[member]["sha256"] == record["pins"]["code"]["sha256"]
    wrong = retain("--summary", "contract.fixture_pair_wrong_field")
    assert wrong["verdict"] == "not_proven" and wrong["failure_class"] in {"unknown", "timeout"}, wrong
    assert any(not goal.get("smoke") and goal["status"] != "valid" for goal in wrong["goals"])
    assert not any(goal.get("smoke") and goal["status"] != "valid" for goal in wrong["goals"])
    assert len({row["id"] for row in retained}) == 6
    assert len(list((tmp_path / "records/proofs").glob("*.yaml"))) == 6

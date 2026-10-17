"""Pair-only public lowering/proof workflow; created 2026-10-15 ET.

Ordinary tests invoke Clang and a parser-error Frama stand-in, never a solver.
Set SWDB_PAIR_ACTUAL=1 only inside a coordinator-admitted actual verifier profile.
Collection performs no tool discovery or version probes.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import REPO
from testkit.pair_workflow import SOURCE, CONTRACT, _lower, _seed

MEMBERS = tuple("std_pair_int_int_" + name for name in
                ("ctor_default", "ctor", "copy_ctor", "operator_assign"))


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


def test_profile_refuses_output_anywhere_inside_full_checkout_before_creation(tmp_path):
    checkout = tmp_path / "checkout"
    scripts = checkout / "swdb-project/scripts"
    scripts.mkdir(parents=True)
    script = scripts / "probata_pair_profile.py"
    shutil.copy(REPO / "scripts/probata_pair_profile.py", script)
    output = checkout / "outside-project-but-inside-checkout"
    done = subprocess.run([sys.executable, script, "--mode", "controls", "--output", output],
                          capture_output=True, text=True)
    assert done.returncode != 0 and "outside the source checkout" in done.stderr
    assert not output.exists()


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
        assert record["evidence_kind"] == "contract_fixture", record
        assert record["pins"]["method_version"]["id"] == "method.pair-workflow-fixture", record
        assert record["settings"]["rss_cap_bytes"] == 8589934592, record
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
    assert caller["subject"] == {"kind": "library_summary", "id": CONTRACT}, caller
    assert caller["verdict"] == "proven", caller
    pinned = {row["id"]: row for row in caller["pins"]["models"]}
    assert set(pinned) == set(MEMBERS)
    for member, record in models.items():
        assert pinned[member]["proof_record"] == record["id"]
        assert pinned[member]["sha256"] == record["pins"]["code"]["sha256"]
    wrong = retain("--summary", "contract.fixture_pair_wrong_field")
    assert wrong["subject"] == {"kind": "library_summary", "id": "contract.fixture_pair_wrong_field"}, wrong
    assert wrong["verdict"] == "not_proven" and wrong["failure_class"] in {"unknown", "timeout"}, wrong
    assert any(not goal.get("smoke") and goal["status"] != "valid" for goal in wrong["goals"])
    assert not any(goal.get("smoke") and goal["status"] != "valid" for goal in wrong["goals"])
    assert len({row["id"] for row in retained}) == 6
    assert len(list((tmp_path / "records/proofs").glob("*.yaml"))) == 6

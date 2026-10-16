"""2026-10-16 ET. Public mixed pair identity and accepted A2 workflow.

Ordinary controls use Clang/native sanitizers or parser-error stand-ins only.
The complete eight-record formal test requires explicit coordinator admission.
Collection performs no tool discovery. No pointer leaves the source scope.
"""
import hashlib
import json
import os
import subprocess
import time

import pytest
import yaml

from conftest import FIXTURES, run_swdb
from testkit.pair_workflow import _lower, _seed

SOURCE = FIXTURES / "proof/lowering/pair_pointer.cc"
MEMBERS = tuple("std_pair_int_int_ptr_" + name for name in
                ("ctor_default", "ctor", "copy_ctor", "operator_assign"))
CONTRACT = "contract.fixture_pair_pointer_values"
WRONG = "contract.fixture_pair_pointer_wrong_identity"


def _pointer_seed(root, *, actual=False):
    root.mkdir(parents=True, exist_ok=True)
    prove, marker = _seed(root, actual=actual, source=SOURCE)
    from swdb import cbmc_translator
    from swdb.cbmc_adapter import FROZEN
    method_path = root / "library/methods/pair-workflow-fixture.yaml"
    method = yaml.safe_load(method_path.read_bytes())
    method["description"] = "2026-10-16 ET: mixed int/pointer pair fixture; local pointer identity without dereference."
    method["c_lowering"]["translators"].append(cbmc_translator.identity())
    next(row for row in method["lineup"] if row["tool"] == "cbmc")["flags"] = [*FROZEN, "--sat-solver", "cadical"]
    if actual:
        from testkit.dx100_selector import bind_actual_lineup, read_actual_lineup
        bind_actual_lineup(method, read_actual_lineup())
    method_path.write_text(yaml.safe_dump(method, sort_keys=False))
    contracts = root / "library/rewrite_contracts"
    for filename, identity, function in (
            ("fixture_pair_values.yaml", CONTRACT, "swdb_pair_pointer_values"),
            ("fixture_pair_wrong_field.yaml", WRONG, "swdb_pair_pointer_wrong_identity")):
        path = contracts / filename
        entry = yaml.safe_load(path.read_bytes())
        entry["id"] = identity
        entry["proof_unit"]["function"] = function
        entry["provenance"]["origin"]["intrinsic_specification"] = "mixed-pair-pointer-fixture-20261016"
        next(row for row in entry["clauses"] if row["id"] == "post")["acsl"]["text"] = r"assigns \nothing; ensures \result == x+3;"
        path.write_text(yaml.safe_dump(entry, sort_keys=False))
    return prove, marker, method["id"]


def test_mixed_pair_lowering_and_native_identity_agree_without_pointee_access(tmp_path):
    from swdb import c_lowering
    compiler = c_lowering.locate().command[0]
    for function, result, args in (("swdb_pair_pointer_values", "x+3", "x,y"),
                                   ("swdb_pair_pointer_self_assign", "x+1", "x,y"),
                                   ("swdb_pair_pointer_default", "1", "")):
        out = tmp_path / function
        report = _lower(SOURCE, function, out)
        assert report["bounded_initialization"]["verdict"] == "passed", report
        if function.endswith("values"):
            assert set(report["models"]) == set(MEMBERS), report
        assert report["std_models"]["types"] == ["std_pair_int_int_ptr"], report
        harness = ('#include <stdio.h>\nint main(void){int values[]={-1000,-7,0,11,1000};'
                   'for(int i=0;i<5;i++)for(int j=0;j<5;j++){int x=values[i],y=values[j];'
                   f'int got={function}({args});if(got!=({result}))return 2;printf("%d\\n",got);}}}}\n')
        outputs = []
        for label, include, standard in (("cpp", SOURCE, "-std=c++17"),
                                          ("c", out / (function+".c"), "-std=c11")):
            unit = tmp_path / (function+"."+("cc" if label == "cpp" else "c"))
            unit.write_text(f'#include "{include}"\n'+harness)
            binary = tmp_path / (function+"-"+label)
            built = subprocess.run([compiler, "-x", "c++" if label == "cpp" else "c", standard,
                "-O1", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", str(unit), "-o", str(binary)],
                capture_output=True, text=True, timeout=120)
            assert built.returncode == 0, built.stderr
            ran = subprocess.run([binary], capture_output=True, text=True, timeout=30)
            assert ran.returncode == 0 and not ran.stderr, ran.stderr
            outputs.append(ran.stdout)
        assert outputs[0] == outputs[1] and len(outputs[0].splitlines()) == 25


def test_unknown_pointer_pair_input_refuses_and_missing_models_do_not_launch(tmp_path):
    report = _lower(SOURCE, "swdb_pair_pointer_uninitialized", tmp_path / "uninitialized")
    assert report["bounded_initialization"]["verdict"] == "refused", report
    prove, marker, _ = _pointer_seed(tmp_path / "missing-models")
    refused = prove("--summary", CONTRACT, ok=False)
    assert refused.returncode != 0 and "no proven record at its current text" in refused.stderr
    assert "std_pair_int_int_ptr_" in refused.stderr and not marker.exists()


@pytest.mark.parametrize("member", MEMBERS)
def test_each_mixed_pair_body_reaches_public_parser_with_exact_contract(tmp_path, member):
    from swdb import c_lowering
    prove, marker, _ = _pointer_seed(tmp_path)
    record = prove("--model", member)
    assert marker.exists() and record["subject"] == {"kind": "c_model", "id": member}
    assert record["verdict"] == "not_proven" and record["failure_class"] == "parse_error", record
    assert record["pins"]["code"]["sha256"] == hashlib.sha256(c_lowering.model_text(member).encode()).hexdigest()


@pytest.mark.skipif(os.environ.get("SWDB_MIXED_PAIR_ACTUAL") != "1", reason="requires coordinator actual admission")
def test_actual_mixed_pair_bodies_callers_and_bounded_cpp_replay(tmp_path):
    from swdb import c_lowering
    prove, _, method = _pointer_seed(tmp_path, actual=True)
    retained = []
    def retain(record):
        retained.append(record)
        (tmp_path / "actual-mixed-pair-progress.json").write_text(json.dumps(retained, indent=2)+"\n")
        assert record["evidence_kind"] == "contract_fixture", record
        assert record["settings"]["rss_cap_bytes"] == 8589934592, record
        return record
    models = {member: retain(prove("--model", member)) for member in MEMBERS}
    for member, record in models.items():
        assert record["verdict"] == "proven" and record.get("unproven_properties", []) == [], record
        assert record["pins"]["code"]["sha256"] == hashlib.sha256(c_lowering.model_text(member).encode()).hexdigest()
    safe = retain(prove("--summary", CONTRACT))
    assert safe["verdict"] == "proven", safe
    pins = {row["id"]: row for row in safe["pins"]["models"]}
    assert set(pins) == set(MEMBERS)
    for member, record in models.items():
        assert pins[member]["proof_record"] == record["id"]
        assert pins[member]["sha256"] == record["pins"]["code"]["sha256"]
    wrong = retain(prove("--summary", WRONG))
    assert wrong["verdict"] == "not_proven" and wrong["failure_class"] in {"unknown", "timeout"}, wrong
    assert any(not g.get("smoke") and g["status"] != "valid" for g in wrong["goals"])
    assert all(g["status"] == "valid" for g in wrong["goals"] if g.get("smoke"))
    for contract, expected in ((CONTRACT, "proven"), (WRONG, "refuted")):
        remaining = float(os.environ["SWDB_PAIR_DEADLINE_MONOTONIC"])-time.monotonic()
        assert remaining > 15
        done = run_swdb("prove", "--records", tmp_path / "records", "--summary", contract,
            "--method-version", method, "--adapter", "cbmc", "--bounds", '{"threads":1}',
            "--budget-minutes", str((remaining-15)/60), "--runs-dir", tmp_path / "runs",
            "--format", "json", timeout=remaining)
        assert done.returncode == 0, done.stdout+done.stderr
        record = retain(yaml.safe_load((tmp_path / "records" / json.loads(done.stdout)["path"]).read_bytes()))
        assert record["verdict"] == expected, record
        if expected == "proven":
            assert record["settings"]["agreement"]["verdict"] == "agree", record
        else:
            assert record["counterexample"]["replay"]["replayed"] is True, record
            assert record["settings"]["forms"]["cxx"] == "refuted (counterexample replayed)"
    assert len(retained) == 8 and len({row["id"] for row in retained}) == 8

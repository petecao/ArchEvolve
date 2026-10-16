"""Public once-per-member WP contracts; created 2026-10-15 ET (ticket25).

These records check the original C model contracts. The default pointer-forming
members retain their unsupported incoming-origin gate. The separately selected
vector-member method tests that explicit typed-storage domain. Updated 2026-10-16 ET.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import FIXTURES, REPO, make_records
from test_proof_records import _library_roots
from test_wp_adapter import method_version, needs_wp
from test_wp_subset import Seed
from testkit.record_subset import copy_record_subset

NONALLOCATING = ("ctor", "move_ctor", "operator_index", "at", "data", "size", "empty", "begin", "end", "clear", "swap")
PAIR = ("ctor_default", "ctor", "copy_ctor", "operator_assign")
MEMBERS = tuple("std_vector_int_" + name for name in NONALLOCATING) + tuple("std_pair_int_int_" + name for name in PAIR)


@pytest.mark.parametrize("changed", [False, True])
def test_checked_at_view_preserves_the_origin_gate_and_prelaunch_tamper_check(tmp_path, changed):
    """2026-10-15 ET: a checked defensive guard supplies no incoming array-object origin."""
    from dataclasses import replace
    from types import SimpleNamespace
    from swdb import c_lowering, proof, proof_setup, standard_model_view
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    name = "std_vector_int_at"
    unit = proof.ProofUnit(None, name, str(tmp_path), "0" * 64, "c_model." + name, "0" * 64)
    job = proof.Job(unit, (), scratch, tmp_path / "adapter.log", bounds={}, budget_seconds=30)
    method = SimpleNamespace(data={'c_lowering': {'translators': [c_lowering.identity()['c_lowering']]}})
    adapter = SimpleNamespace(name="wp", library=None, method=method)
    proof_setup.begin(job, adapter, {"method_version": {"not_applicable": "Static launch-boundary control."}}, None)
    view = standard_model_view.wp_view(name, c_lowering.model_text(name), scratch)
    source = "\n".join([*c_lowering.HEADERS, view.text]) + "\n"
    text = source
    input_path = scratch / "wp_input.c"
    input_path.write_text(text)
    context = {"pointer_bounds_model_source": source, "wp_expected_text": text,
               "pointer_bounds_report": {},
               "standard_model_view": {"view": replace(view, text=view.text + "\n") if changed else view}}
    flags = ["-wp-cache", "none", "-machdep", "x86_64", "-wp-model", "+real", "-wp-no-filter-init"]
    if changed:
        with pytest.raises(proof.AdapterError, match="checked standard model view changed"):
            proof_setup.check_generated(job, adapter, context, [(input_path, text)], flags)
    else:
        with pytest.raises(proof.AdapterError, match="certified array-object origin"):
            proof_setup.check_generated(job, adapter, context, [(input_path, text)], flags)


def _member_seed(root):
    from swdb import c_lowering, std_models
    records = make_records(root)
    copy_record_subset(REPO / "records", records.path, sorted(_library_roots()))
    shutil.copytree(REPO / "library", root / "library")
    methods = root / "library" / "methods"
    shutil.copy(FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml", methods)
    method = method_version(c_lowering.identity())
    method["models"].update(std_vector=std_models.identity(), std_pair=std_models.identity())
    (methods / "wp-tracer-fixture.yaml").write_text(yaml.safe_dump(method, sort_keys=False))
    return Seed(root, {})


@pytest.fixture(scope="module")
def member_subset(tmp_path_factory):
    return _member_seed(tmp_path_factory.mktemp("wp-standard-members"))


@needs_wp
@pytest.mark.parametrize("member", MEMBERS)
def test_each_nonallocating_standard_member_satisfies_its_actual_model_contract(member_subset, member):
    record = member_subset.prove("--model", member, "--method-version", "method.wp-tracer-fixture")
    if member in {'std_vector_int_operator_index', 'std_vector_int_at', 'std_vector_int_end'}:
        assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct'
        assert 'certified array-object origin' in record['settings']['pointer_bounds']['reason']
        assert record['settings']['verifier_launched'] is False
        return
    assert record["verdict"] == "proven", (member, record)
    assert record["subject"] == {"kind": "c_model", "id": member}
    assert record["evidence_kind"] == "contract_fixture"
    assert record.get("unproven_properties", []) == []
    if member == "std_vector_int_at":
        certificate = record["settings"]["standard_model_view"]
        assert certificate["original_contract_sha256"] == certificate["view_contract_sha256"]
        assert certificate["input_premises_added"] == []
        assert certificate["guard_elision_obligation"] == "at_guard_false"
        assert any("at_guard_false" in goal.get("goal", "") for goal in record["goals"])
        assert "standard_model_view_check" in record["pins"]


@needs_wp
@pytest.mark.parametrize("override", ["missing", "opposite", "value", "duplicate"])
def test_the_real_adapter_requires_the_canonical_initialization_filter_switch_before_verifying(tmp_path, override):
    member_subset = _member_seed(tmp_path)
    method_path = member_subset.root / "library" / "methods" / "wp-tracer-fixture.yaml"
    original = method_path.read_text()
    method = yaml.safe_load(original)
    row = next(row for row in method["lineup"] if row["tool"] == "frama-c-wp")
    flags = row["flags"]
    if override == "missing":
        flags.remove("-wp-no-filter-init")
    elif override == "opposite":
        flags.append("-wp-filter-init")
    elif override == "value":
        flags.append("-wp-no-filter-init=false")
    else:
        flags.append("-wp-no-filter-init")
    before = set((member_subset.records / "proofs").glob("*.yaml"))
    try:
        method_path.write_text(yaml.safe_dump(method, sort_keys=False))
        refused = member_subset.prove("--model", "std_vector_int_ctor", "--method-version", "method.wp-tracer-fixture", ok=False)
        assert "requires exactly -wp-no-filter-init" in refused.stderr
        assert set((member_subset.records / "proofs").glob("*.yaml")) == before
    finally:
        method_path.write_text(original)


@needs_wp
def test_a_changed_at_contract_without_its_bounds_precondition_cannot_use_the_checked_view(tmp_path):
    seed = _member_seed(tmp_path)
    runtime = tmp_path / "changed-runtime"
    for folder in ("swdb", "schemas", "vocab"):
        shutil.copytree(REPO / folder, runtime / folder, ignore=shutil.ignore_patterns("__pycache__"))
    models = runtime / "swdb" / "std_models.py"
    original = models.read_text()
    start, tail = original.split('    elif member == "at":', 1)
    at, end = tail.split('    elif member == "data":', 1)
    assert "_readable(this) && n < this->size" in at
    at = at.replace("_readable(this) && n < this->size", "_readable(this)")
    models.write_text(start + '    elif member == "at":' + at + '    elif member == "data":' + end)
    env = {**os.environ, "SWDB_HOME": str(REPO), "PYTHONPATH": str(runtime)}
    # This is a prospective, freshly pinned method; stale-method rejection must
    # not mask the missing original bounds premise at the actual prove seam.
    refresh = subprocess.run([sys.executable, "-c",
        "import json; from swdb import c_lowering,proof_setup,std_models; "
        "print(json.dumps([c_lowering.identity(),proof_setup.identity(),std_models.identity()]))"],
        cwd=runtime, env=env, capture_output=True, text=True, check=True)
    lowering, checks, model = json.loads(refresh.stdout)
    method_path = seed.root / "library" / "methods" / "wp-tracer-fixture.yaml"
    method = method_version(lowering)
    method["checks"].update(checks)
    method["models"].update(std_vector=model, std_pair=model)
    method_path.write_text(yaml.safe_dump(method, sort_keys=False))
    result = subprocess.run([sys.executable, "-m", "swdb", "prove", "--records", str(seed.records),
        "--adapter", "wp", "--runs-dir", str(seed.runs), "--format", "json", "--model", "std_vector_int_at",
        "--method-version", "method.wp-tracer-fixture"],
        cwd=runtime, env=env, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct", record
    assert not list(seed.runs.glob("*/wp/frama-c.log"))

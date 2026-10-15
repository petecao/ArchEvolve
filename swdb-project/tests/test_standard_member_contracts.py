"""Public once-per-member WP contracts; created 2026-10-15 ET (ticket25).

These records prove the actual C model contract/body. Allocation-bearing members require a
separate checked relation and are deliberately outside this first actual contract-proof batch.
"""
import shutil

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
    assert record["verdict"] == "proven", (member, record)
    assert record["subject"] == {"kind": "c_model", "id": member}
    assert record["evidence_kind"] == "contract_fixture"
    assert record.get("unproven_properties", []) == []


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

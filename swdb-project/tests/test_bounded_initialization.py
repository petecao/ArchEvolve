"""CBMC initializedness admission through public proof records; created 2026-10-15 ET."""

import json

import pytest

import test_cbmc_adapter as cbmc
from test_proof_semantics import dx, dx_seed


def _not_executed(record):
    assert not any(r["name"].startswith(("cbmc_", "differential_")) for r in record["evidence"]["reports"])


CONTROLS = """
#if defined(INIT_LOCAL)
  int u; int discarded = u;
#elif defined(INIT_SELF)
  int u = u;
#elif defined(INIT_ALIAS)
  int u; int *p = &u; int discarded = *p;
#elif defined(INIT_HEAP)
  int *p = new int[2]; int discarded = p[0]; delete[] p;
#elif defined(INIT_PARTIAL)
  int a[2]; a[0] = 1; int discarded = a[1];
#elif defined(INIT_AGGREGATE)
  InitPair p; p.a = 1; int discarded = p.b;
#elif defined(INIT_CALLEE)
  int discarded = init_hidden();
#elif defined(INIT_INITIALIZER_CALL)
  int u; int discarded = init_identity(u);
#elif defined(INIT_DEFAULT_ARGUMENT)
  int discarded = init_default_argument();
#elif defined(INIT_GOOD_ALIAS)
  int u = 1; int *p = &u; int discarded = *p;
#endif
"""


@pytest.fixture(scope="module")
def initialization_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded-initialization")
    units = ("struct InitPair { int a; int b; };\n"
             "int init_hidden() { int u; int discarded = u; return 1; }\n"
             "int init_identity(int x) { return x; }\n" + cbmc.UNITS)
    units = "int init_default_argument(int z = *(new int[1])) { return 0; }\n" + units
    units = units.replace("int smoke_main(int x) {", "int smoke_main(int x) {\n" + CONTROLS)
    units = units.replace("void swdb_fixture_fill(int *a, int n, int v) {", "void swdb_fixture_fill(int *a, int n, int v) {\n"
                          "#ifdef INIT_POINTER_REASSIGN\n int *p = a; p = a;\n#endif\n")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cbmc, "UNITS", units)
        candidates = cbmc.build_cbmc_seed(root)
    return cbmc.Seed(root, candidates)


@cbmc.needs_cbmc
@pytest.mark.parametrize("control", ["LOCAL", "SELF", "ALIAS", "HEAP", "PARTIAL", "AGGREGATE", "CALLEE",
                                     "INITIALIZER_CALL", "GOOD_ALIAS", "POINTER_REASSIGN", "DEFAULT_ARGUMENT"])
def test_uncertain_initializedness_is_unsupported_before_execution(initialization_seed, control):
    seed = initialization_seed
    function, contract, bounds = (("swdb_fixture_fill", cbmc.FILL, {"threads": 1, "n": 2})
                                  if control == "POINTER_REASSIGN" else ("smoke_main", cbmc.SMOKE, {"threads": 1}))
    record = seed.read(seed.prove(function, contract, bounds, "--define", "INIT_" + control))
    assert record["verdict"] == "not_proven", record
    assert record["failure_class"] == "unsupported_construct"
    admission = record["settings"]["bounded_initialization"]
    assert admission["verdict"] == "refused" and admission["reason"]
    assert admission["function"] and admission["source_line"]
    _not_executed(record)


@cbmc.needs_cbmc
def test_initialized_scalars_and_harness_buffers_remain_admitted(initialization_seed):
    seed = initialization_seed
    for function, contract, bounds in (("smoke_main", cbmc.SMOKE, {"threads": 1}),
                                        ("swdb_fixture_fill", cbmc.FILL, {"threads": 1, "n": 2})):
        record = seed.read(seed.prove(function, contract, bounds))
        assert record["verdict"] == "proven", record
        admission = record["settings"]["bounded_initialization"]
        assert admission["verdict"] == "passed"
        assert admission["check"]["id"] == "swdb-bounded-initialization-1"
        assert len(admission["check"]["sha256"]) == 64
        setup = record["proof_setup_check"]
        assert setup["runs"][-1]["hashes"]["bounded_initialization"]


@cbmc.needs_cbmc
def test_cap_zero_does_not_treat_dummy_pointer_storage_as_initialized(initialization_seed):
    seed = initialization_seed
    record = seed.read(seed.prove("swdb_fixture_fill", cbmc.FILL, {"threads": 1}))
    assert record["verdict"] == "not_proven"
    assert "zero" in record["settings"]["bounded_initialization"]["reason"]


@pytest.fixture(scope="module")
def initialization_equivalence_seed(tmp_path_factory):
    import test_cbmc_equivalence as equiv
    root = tmp_path_factory.mktemp("bounded-initialization-equivalence")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(equiv, "VARIANTS", {"base": equiv.BASE_FILL,
            "uninitialized": equiv.BASE_FILL.replace("{", "{ int u; int discarded = u;", 1)})
        candidates = equiv.build_equivalence_seed(root)
    return equiv.Seed(root, candidates)


@cbmc.needs_cbmc
@pytest.mark.parametrize("side", ["candidate", "baseline"])
@pytest.mark.parametrize("mode", ["bounded_direct", "no_contract_baseline"])
def test_whole_function_checks_initializedness_on_both_sides(initialization_equivalence_seed, side, mode):
    seed = initialization_equivalence_seed
    record = seed.prove("uninitialized" if side == "candidate" else "base", mode,
                        baseline="uninitialized" if side == "baseline" else "base")
    assert record["verdict"] == "not_proven", record
    assert record["failure_class"] == "unsupported_construct"
    assert record["settings"]["bounded_initialization"][side]["verdict"] == "refused"
    _not_executed(record)


@cbmc.needs_cbmc
def test_changed_model_body_does_not_inherit_the_known_models_initialization_policy(dx):
    import hashlib
    import yaml
    from test_proof_semantics import prove
    root = dx.records.parent / "library"
    path = root / "proof_semantics" / "dx100_bfs" / "model.h"
    path.write_text(path.read_text().replace("unsigned short get_tile_size(int tile) {",
        "unsigned short get_tile_size(int tile) { int u; int discarded = u;"))
    entry = root / "proof_semantics" / "dx100_bfs_0_1.yaml"
    data = yaml.safe_load(entry.read_text())
    data["model"]["c"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    entry.write_text(yaml.safe_dump(data, sort_keys=False))
    record = prove(dx, "size")
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unsupported_construct"
    assert "exact-content" in record["settings"]["bounded_initialization"]["reason"]
    _not_executed(record)

"""Pointer arithmetic obligations through public CBMC proof routes; created 2026-10-15 ET."""

import json

import pytest

import test_cbmc_adapter as cbmc
import test_cbmc_equivalence as equiv
import test_proof_semantics as dx


@pytest.fixture(scope="module")
def pointer_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded-pointers")
    start = "void swdb_fixture_fill(int *a, int n, int v) {"
    controls = """
#if defined(PTR_OUTSIDE)
  int *discarded = a + 3;
#elif defined(PTR_OUTSIDE_EXPR)
  (void)(a + 3);
#elif defined(PTR_ONE_PAST)
  int *discarded = a + n;
#endif
"""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cbmc, "UNITS", cbmc.UNITS.replace(start, start + controls))
        candidates = cbmc.build_cbmc_seed(root)
    return cbmc.Seed(root, candidates)


@cbmc.needs_cbmc
@pytest.mark.parametrize("define", ["PTR_OUTSIDE", "PTR_OUTSIDE_EXPR"])
def test_discarded_outside_pointer_formation_is_never_proven(pointer_seed, define):
    seed = pointer_seed
    record = seed.read(seed.prove("swdb_fixture_fill", cbmc.FILL, {"threads": 1, "n": 2}, "--define", define))
    assert record["verdict"] == "not_proven", record
    assert "--pointer-overflow-check" in record["settings"]["flags"]
    assert any(g["status"] == "failure" and "pointer" in g["property"] for g in record["goals"])


@cbmc.needs_cbmc
def test_one_past_pointer_formation_remains_legal(pointer_seed):
    seed = pointer_seed
    record = seed.read(seed.prove("swdb_fixture_fill", cbmc.FILL, {"threads": 1, "n": 2}, "--define", "PTR_ONE_PAST"))
    assert record["verdict"] == "proven", record
    assert "--pointer-overflow-check" in record["settings"]["flags"]


@pytest.fixture(scope="module")
def pointer_equivalence_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded-pointer-equivalence")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(equiv, "VARIANTS", {"base": equiv.BASE_FILL,
            "outside": equiv.BASE_FILL.replace("{", "{ int *discarded = a + 3;", 1)})
        candidates = equiv.build_equivalence_seed(root)
    return equiv.Seed(root, candidates)


@cbmc.needs_cbmc
@pytest.mark.parametrize("side", ["candidate", "baseline"])
@pytest.mark.parametrize("mode", ["bounded_direct", "no_contract_baseline"])
def test_both_equivalence_sides_check_pointer_formation(pointer_equivalence_seed, side, mode):
    seed = pointer_equivalence_seed
    record = seed.prove("outside" if side == "candidate" else "base", mode,
                        baseline="outside" if side == "baseline" else "base", bounds={"threads": 1, "n": 2})
    assert record["verdict"] == "not_proven", record
    assert "--pointer-overflow-check" in record["settings"]["flags"]
    assert any(g["status"] == "failure" and "pointer" in g["property"] for g in record["goals"])


@pytest.fixture(scope="module")
def tile_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded-tile-pointers")
    units = dx.UNITS + """
int dxf_tile_extent(int n) {
  int *tile = get_cacheable_tile_pointer(0);
#ifdef TILE_OUTSIDE
  int ignored = tile[3];
#else
  for (int k = 0; k < n; ++k) { int ignored = tile[k]; }
#endif
  return 1;
}
"""
    fixtures = {**dx.FIXTURES, "tile_extent": ("dxf_tile_extent", [], "requires 0 <= n <= 2;", "\\nothing", 2)}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dx, "UNITS", units)
        patch.setattr(dx, "FIXTURES", fixtures)
        candidate = dx.build_dx_seed(root)
    return cbmc.Seed(root, {"safe": candidate})


@cbmc.needs_cbmc
@pytest.mark.parametrize("outside", [True, False])
def test_tile_pointer_checks_its_own_row_extent(tile_seed, outside):
    extra = [arg for define in ("DX_NT=2", "DX_NR=1", "DX_NM=1", "DX_K=1")
             for arg in ("--define", define)]
    if outside:
        extra += ["--define", "TILE_OUTSIDE"]
    record = tile_seed.read(tile_seed.prove("dxf_tile_extent", "contract.fixture_dx_tile_extent",
                                          {"threads": 1, "n": 2}, *extra))
    if outside:
        assert record["verdict"] != "proven", record
        assert any(g["status"] == "failure" and "pointer" in g["property"] for g in record["goals"])
    else:
        assert record["verdict"] == "proven", record

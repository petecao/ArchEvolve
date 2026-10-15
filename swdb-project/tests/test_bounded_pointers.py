"""Pointer arithmetic obligations through public CBMC proof routes; created 2026-10-15 ET."""

import json

import pytest

import test_cbmc_adapter as cbmc
import test_cbmc_equivalence as equiv
import test_proof_semantics as dx
import test_wp_adapter as wp


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
struct PointerFields { int first; int second; int third; };
int dxf_tile_extent(int n) {
  int *tile = get_cacheable_tile_pointer(0);
#ifdef TILE_INIT_ROWS
  int *neighbor = get_cacheable_tile_pointer(1);
  tile[0] = 0; tile[1] = 0; neighbor[0] = 0; neighbor[1] = 0;
#endif
#ifdef TILE_OUTSIDE
  int ignored = tile[3];
#elif defined(TILE_WP_DIRECT)
  int ignored = tile[1];
#else
  for (int k = 0; k < n; ++k) { int ignored = tile[k]; }
#endif
  return 1;
}
int dxf_pointer_formation(int *p, int n) {
#ifdef WP_POINTER_OUTSIDE
  (void)(p + 3);
#else
  (void)(p + n);
#endif
  return 1;
}
int dxf_pointer_modes(int *p, int *q, int n) {
#ifdef WP_POINTER_INCREMENT
  p++;
#elif defined(WP_POINTER_COMPOUND)
  p += n + 1;
#elif defined(WP_POINTER_DIFFERENCE)
  (void)(p - q);
#elif defined(WP_POINTER_CAST)
  (void)((short *)p + 1);
#elif defined(WP_POINTER_SUBOBJECT)
  int a[2][2] = {{0, 0}, {0, 0}}; int *row = a[0]; (void)(row + 3);
#elif defined(WP_POINTER_MEMBER)
  PointerFields fields = {0, 0, 0}; int *member = &fields.first; (void)(member + 2);
#else
  (void)(&p[n + 1]);
#endif
  return 1;
}
int pointer_global_flat[2] = {0, 0};
int dxf_pointer_flat(int n) {
#ifdef WP_POINTER_GLOBAL
  int *p = pointer_global_flat;
#else
  int a[2] = {0, 0}; int *p = a;
#endif
#ifdef WP_POINTER_OUTSIDE
  (void)(p + 3);
#else
  (void)(p + n);
#endif
  return 1;
}
int dxf_pointer_rebound(int *q, int n) { int a[2] = {0,0}; int *p=a; p=q; (void)(p+n); return 1; }
int dxf_pointer_index(int *p, int n) { int ignored = p[0]; return 1; }
int dxf_pointer_null(int *p, int n) { (void)(p + 0); return 1; }
"""
    fixtures = {**dx.FIXTURES, "tile_extent": ("dxf_tile_extent", [], "requires 0 <= n <= 2;", "\\nothing", 2),
                "pointer_formation": ("dxf_pointer_formation", ["p"],
                    "requires n == 2 && \\valid(p + (0 .. n - 1));", "\\nothing", 2),
                "pointer_modes": ("dxf_pointer_modes", ["p", "q"],
                    "requires n == 2 && \\valid(p + (0 .. n - 1)) && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
                "pointer_flat": ("dxf_pointer_flat", [], "requires n == 2;", "\\nothing", 2),
                "pointer_rebound": ("dxf_pointer_rebound", ["q"], "requires n == 2 && \\valid(q + (0 .. n - 1));", "\\nothing", 2),
                "pointer_index": ("dxf_pointer_index", ["p"], "requires n == 2 && \\valid(p + (0 .. n - 1));", "\\nothing", 2),
                "pointer_null": ("dxf_pointer_null", ["p"], "requires n == 0 && p == \\null;", "\\nothing", 0)}
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


@dx.needs_wp
@pytest.mark.parametrize("outside", [True, False])
def test_wp_tile_pointer_checks_its_own_row_extent(tile_seed, outside):
    from conftest import run_swdb
    seed = tile_seed
    extra = [arg for define in ("DX_NT=2", "DX_NR=1", "DX_NM=1", "DX_K=1",
                              "TILE_OUTSIDE" if outside else "TILE_WP_DIRECT", "TILE_INIT_ROWS")
             for arg in ("--define", define)]
    result = run_swdb("prove", "--records", seed.records, "--candidate", seed.candidates["safe"],
        "--function", "dxf_tile_extent", "--contract", "contract.fixture_dx_tile_extent", "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", *extra, timeout=3600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == ("not_proven" if outside else "proven"), record
    if outside:
        assert any("rte_mem_access" in g["goal"] and g["status"] != "valid" for g in record["goals"]), record


@pytest.mark.xfail(strict=True, reason="Pending explicit checked incoming array-object domain; old validity range alone is insufficient")
@dx.needs_wp
@pytest.mark.parametrize("outside", [True, False])
def test_wp_discarded_pointer_formation_checks_bounds_and_allows_one_past(tile_seed, outside):
    from conftest import run_swdb
    seed = tile_seed
    extra = ["--define", "WP_POINTER_OUTSIDE"] if outside else []
    result = run_swdb("prove", "--records", seed.records, "--candidate", seed.candidates["safe"],
        "--function", "dxf_pointer_formation", "--contract", "contract.fixture_dx_pointer_formation", "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", *extra, timeout=3600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == ("not_proven" if outside else "proven"), record
    goals = [g for g in record.get("goals", []) if "swdb_pointer_formation" in g["goal"]]
    assert goals and any(g["status"] != "valid" for g in goals) is outside


@dx.needs_wp
@pytest.mark.parametrize("define", ["WP_POINTER_INCREMENT", "WP_POINTER_COMPOUND", "WP_POINTER_DIFFERENCE", "WP_POINTER_CAST", "WP_POINTER_SUBOBJECT", "WP_POINTER_MEMBER", None])
def test_wp_pointer_mutation_subtraction_and_indexed_address_cannot_bypass_checks(tile_seed, define):
    from conftest import run_swdb
    seed = tile_seed
    extra = ["--define", define] if define else []
    result = run_swdb("prove", "--records", seed.records, "--candidate", seed.candidates["safe"],
        "--function", "dxf_pointer_modes", "--contract", "contract.fixture_dx_pointer_modes", "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", *extra, timeout=3600,
        env=wp.fake("unknown") if define == "WP_POINTER_MEMBER" else None)
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == "not_proven", record
    if define:
        assert record["failure_class"] == "unsupported_construct"
        assert record["settings"]["verifier_launched"] is False
    else:
        assert record["failure_class"] == "unsupported_construct"
        assert record["settings"]["verifier_launched"] is False


@dx.needs_wp
def test_cpp_null_plus_zero_is_preserved_without_c_null_arithmetic(tile_seed):
    from conftest import run_swdb
    seed = tile_seed
    result = run_swdb("prove", "--records", seed.records, "--candidate", seed.candidates["safe"],
        "--function", "dxf_pointer_null", "--contract", "contract.fixture_dx_pointer_null", "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", timeout=3600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == "proven", record
    assert record["settings"]["pointer_bounds"]["sites"][0]["normalized_expression"]


@dx.needs_wp
def test_generated_copy_model_proves_checked_pointer_distance_and_return(tile_seed):
    from conftest import run_swdb
    seed = tile_seed
    result = run_swdb("prove", "--records", seed.records, "--model", "std_copy_int", "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", timeout=3600)
    assert result.returncode == 0, result.stderr + result.stdout
    record = seed.read(json.loads(result.stdout))
    assert record["verdict"] == "proven", record
    assert len(record["settings"]["pointer_bounds"]["sites"]) == 2
    assert all(g["status"] == "valid" for g in record["goals"] if "swdb_model_pointer_formation" in g["goal"])


@pytest.mark.parametrize("function", ["dxf_pointer_formation", "dxf_pointer_index"])
def test_wp_opaque_incoming_array_origins_are_refused_before_verifier(tile_seed, function):
    from conftest import run_swdb
    contract = "pointer_formation" if function.endswith("formation") else "pointer_index"
    result = run_swdb("prove", "--records", tile_seed.records, "--candidate", tile_seed.candidates["safe"],
        "--function", function, "--contract", "contract.fixture_dx_" + contract, "--adapter", "wp",
        "--runs-dir", tile_seed.runs, "--format", "json", timeout=3600, env=wp.fake("unknown"))
    assert result.returncode == 0, result.stderr + result.stdout
    record = tile_seed.read(json.loads(result.stdout))
    assert record["verdict"] == "not_proven", record
    assert record["failure_class"] == "unsupported_construct", record
    assert record["settings"]["verifier_launched"] is False, record
    assert "array-object origin" in record["settings"]["pointer_bounds"]["reason"], record


@dx.needs_wp
@pytest.mark.parametrize("global_origin", [False, True])
def test_wp_concrete_flat_array_allows_legal_one_past(tile_seed, global_origin):
    from conftest import run_swdb
    extra = ["--define", "WP_POINTER_GLOBAL"] if global_origin else []
    result = run_swdb("prove", "--records", tile_seed.records, "--candidate", tile_seed.candidates["safe"],
        "--function", "dxf_pointer_flat", "--contract", "contract.fixture_dx_pointer_flat", "--adapter", "wp",
        "--runs-dir", tile_seed.runs, "--format", "json", timeout=3600, *extra)
    assert result.returncode == 0, result.stderr + result.stdout
    record = tile_seed.read(json.loads(result.stdout))
    assert record["verdict"] == "proven", record
    assert record["settings"]["pointer_bounds"]["sites"][0]["origin"]["elements"] == 2


def test_wp_rebound_alias_cannot_inherit_its_initializer_origin(tile_seed):
    from conftest import run_swdb
    result = run_swdb("prove", "--records", tile_seed.records, "--candidate", tile_seed.candidates["safe"],
        "--function", "dxf_pointer_rebound", "--contract", "contract.fixture_dx_pointer_rebound", "--adapter", "wp",
        "--runs-dir", tile_seed.runs, "--format", "json", timeout=3600, env=wp.fake("unknown"))
    assert result.returncode == 0, result.stderr + result.stdout
    record = tile_seed.read(json.loads(result.stdout))
    assert record["failure_class"] == "unsupported_construct", record
    assert record["settings"]["verifier_launched"] is False


def test_generated_copy_model_records_qualification_before_a_controlled_unknown_verdict(tile_seed):
    from conftest import run_swdb
    result = run_swdb("prove", "--records", tile_seed.records, "--model", "std_copy_int", "--adapter", "wp",
        "--runs-dir", tile_seed.runs, "--format", "json", timeout=3600, env=wp.fake("unknown"))
    assert result.returncode == 0, result.stderr + result.stdout
    record = tile_seed.read(json.loads(result.stdout))
    assert record["failure_class"] == "unknown", record
    assert record["verdict"] == "not_proven"
    assert record["settings"]["standard_range_model"]["domain_role"] == \
        "explicit standard-library valid-range domain; caller discharge required"
    assert record["pins"]["standard_range_model_certificate"]
    # Generic opaque C parameter domains remain closed; the exact checked
    # standalone qualification is covered by test_standard_range_model.py.

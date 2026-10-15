"""Explicit source entry windows through public prove; created 2026-10-15 ET.

The declaration supplies a contract domain, while generated numerical assertions
and independently regenerated source origins still have to pass.
"""
import json
from pathlib import Path

import pytest
import yaml

import test_cbmc_adapter as cbmc
import test_proof_semantics as dx
import test_wp_adapter as wp
from conftest import run_swdb

UNITS = """
int window_form(int *p, int n) {
#ifdef WINDOW_ALIAS
  int *alias = p; (void)(alias + n);
#elif defined(WINDOW_MUTATE_EXTENT)
  n = 3; (void)(p + n);
#elif defined(WINDOW_REBIND)
  int a[4] = {0,0,0,0}; p = a; (void)(p + n);
#else
  (void)(p + n);
#endif
  return 1;
}
int window_read(int *p, int n) {
#ifdef WINDOW_OUTSIDE
  int ignored = p[2];
#elif defined(WINDOW_DEREFERENCE)
  int ignored = *p;
#else
  int ignored = p[1];
#endif
  return 1;
}
int window_null(int *p, int n) { (void)(p+0); return 1; }
int window_unknown_zero(int *p, int n) { (void)(p+0); return 1; }
int window_huge_extent(int *p, int n) { (void)(p+n); return 1; }
int window_bad_extent(int *p, int n) { (void)(p+n); return 1; }
int window_shadow(int *p, int n) { { int n=3; (void)(p+n); } return 1; }
int window_escape(int *p, int n) { int **escaped=&p; (void)escaped; (void)(p+n); return 1; }
int window_helper(int *p, int n) { return p[0]; }
int window_calls(int *p, int n) { int ignored=window_helper(p,n); return 1; }
"""


@pytest.fixture(scope="module")
def window_seed(tmp_path_factory):
    root = tmp_path_factory.mktemp("entry-windows")
    fixtures = {**dx.FIXTURES,
        "window_form": ("window_form", ["p"], "requires n == 2 && \\valid(p+(0..3)) && \\initialized(p+(0..3));", "\\nothing", 4),
        "window_read": ("window_read", ["p"], "requires n == 2 && \\valid(p+(0..3)) && \\initialized(p+(0..3));", "\\nothing", 4),
        "window_null": ("window_null", ["p"], "requires n == 0 && p == \\null;", "\\nothing", 0),
        "window_unknown_zero": ("window_unknown_zero", ["p"], "requires n == 0 && p != \\null;", "\\nothing", 0),
        "window_huge_extent": ("window_huge_extent", ["p"], "requires n == 2 && \\valid(p+(0..3));", "\\nothing", 4),
        "window_bad_extent": ("window_bad_extent", ["p"], "requires n == 2 && \\valid(p+(0..3));", "\\nothing", 4),
        "window_shadow": ("window_shadow", ["p"], "requires n == 2 && \\valid(p+(0..3));", "\\nothing", 4),
        "window_escape": ("window_escape", ["p"], "requires n == 2 && \\valid(p+(0..3));", "\\nothing", 4),
        "window_calls": ("window_calls", ["p"], "requires n == 2 && \\valid(p+(0..3)) && \\initialized(p+(0..3));", "\\nothing", 4),
    }
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dx, "UNITS", dx.UNITS + UNITS)
        patch.setattr(dx, "FIXTURES", fixtures)
        candidate = dx.build_dx_seed(root)
    for path in (root / "library" / "rewrite_contracts").glob("fixture_dx_window_*.yaml"):
        data = yaml.safe_load(path.read_text())
        data["proof_unit"]["array_domains"] = {"p": {"extent": "-n" if data["proof_unit"]["function"] == "window_bad_extent" else "18446744073709551615 * n" if data["proof_unit"]["function"] == "window_huge_extent" else "n"}}
        path.write_text(yaml.safe_dump(data, sort_keys=False))
    return cbmc.Seed(root, {"safe": candidate})


def prove(seed, unit, define=None, *, scripted=False):
    extra = ["--define", define] if define else []
    result = run_swdb("prove", "--records", seed.records, "--candidate", seed.candidates["safe"],
        "--function", unit, "--contract", "contract.fixture_dx_" + unit, "--adapter", "wp",
        "--runs-dir", seed.runs, "--format", "json", *extra, timeout=3600,
        env=wp.fake("unknown") if scripted else None)
    assert result.returncode == 0, result.stderr + result.stdout
    return seed.read(json.loads(result.stdout))


@dx.needs_wp
def test_explicit_entry_window_proves_legal_one_past(window_seed):
    record = prove(window_seed, "window_form")
    assert record["verdict"] == "proven", record
    assert record["settings"]["pointer_bounds"]["entry_windows"]["windows"]["p"]["parameters"] == ["n"]
    assert any("swdb_window" in g["goal"] for g in record["goals"])


@dx.needs_wp
def test_explicit_entry_window_checks_ordinary_indexing(window_seed):
    record = prove(window_seed, "window_read")
    assert record["verdict"] == "proven", record
    assert any("swdb_window_access" in g["goal"] for g in record["goals"])


@dx.needs_wp
@pytest.mark.parametrize("unit,define", [("window_form", "WINDOW_ALIAS"), ("window_read", "WINDOW_DEREFERENCE"), ("window_null", None)])
def test_stable_alias_dereference_and_null_empty_windows_remain_legal(window_seed, unit, define):
    record = prove(window_seed, unit, define)
    assert record["verdict"] == "proven", record


@dx.needs_wp
@pytest.mark.parametrize("unit,define,goal", [
    ("window_form", "WINDOW_MUTATE_EXTENT", "swdb_pointer_formation"),
    ("window_read", "WINDOW_OUTSIDE", "swdb_window_access"),
    ("window_bad_extent", None, "swdb_window_entry"),
    ("window_huge_extent", None, "swdb_window_entry"),
    ("window_unknown_zero", None, "swdb_pointer_formation"),
])
def test_entry_window_is_frozen_and_never_silently_assumed(window_seed, unit, define, goal):
    record = prove(window_seed, unit, define)
    assert record["verdict"] == "not_proven", record
    assert any(goal in g["goal"] and g["status"] != "valid" for g in record["goals"]), record
    assert record["settings"]["pointer_bounds"]["entry_contract"] == record["pins"]["contract"]


@pytest.mark.parametrize("unit,define", [("window_form", "WINDOW_REBIND"), ("window_shadow", None), ("window_escape", None), ("window_calls", None)])
def test_entry_windows_refuse_rebinding_shadow_escape_and_unmodeled_helper_calls(window_seed, unit, define):
    record = prove(window_seed, unit, define, scripted=True)
    assert record["failure_class"] == "unsupported_construct", record
    assert record["settings"]["verifier_launched"] is False, record


def test_imported_window_summary_requires_discharge_even_without_caller_declaration(window_seed):
    contracts = window_seed.root / "library" / "rewrite_contracts"
    caller = contracts / "fixture_dx_window_calls.yaml"
    original = caller.read_text()
    data = yaml.safe_load(original)
    summary = yaml.safe_load(original)
    summary["id"] = "contract.fixture_dx_window_helper_summary"
    summary["proof_unit"]["function"] = "window_helper"
    for clause in summary["clauses"]:
        clause["proof_placement"] = {"once": "self"}
    imported = contracts / "fixture_dx_window_helper_summary.yaml"
    data["proof_unit"].pop("array_domains")
    try:
        caller.write_text(yaml.safe_dump(data, sort_keys=False))
        imported.write_text(yaml.safe_dump(summary, sort_keys=False))
        record = prove(window_seed, "window_calls", scripted=True)
        assert record["failure_class"] == "unsupported_construct", record
        assert record["settings"]["verifier_launched"] is False, record
        assert "imported array-window summaries" in record["settings"]["pointer_bounds"]["reason"]
    finally:
        caller.write_text(original)
        imported.unlink(missing_ok=True)

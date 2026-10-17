"""Main-source insertion coordinates through public lower; created 2026-10-15 ET."""
import json

from test_c_lowering import lower


def test_public_pointer_inventory_preserves_exclusive_source_statement_and_body_spans(tmp_path):
    source = tmp_path / "positions.cc"
    text = "int unit(){ int a[2]={0,0}; (void)(a+2); return 0; }\n"
    source.write_text(text)
    out = tmp_path / "out"
    lower(source, "unit", out)
    report = json.loads((out / "unit.anchors.json").read_text())["pointer_bounds"]
    function = report["source_functions"]["unit"]
    assert text[function["body_begin"]] == "{"
    assert text[function["body_end"] - 1] == "}"
    assert text[function["begin"]:function["end"]] == text.rstrip()
    operation = next(row for row in report["sites"] if not row.get("admission_only"))
    span = operation["source_statement"]
    assert text[span["begin"]:span["end"]] == "(void)(a+2)"
    assert function["body_begin"] < span["begin"] < span["end"] < function["body_end"]


def test_macro_pointer_statements_do_not_receive_invented_original_source_spans(tmp_path):
    source = tmp_path / "macro.cc"
    source.write_text("#define STEP(a) ((void)(a+2))\nint unit(){int a[2]={0,0}; STEP(a); return 0;}\n")
    out = tmp_path / "out"
    lower(source, "unit", out)
    report = json.loads((out / "unit.anchors.json").read_text())["pointer_bounds"]
    operation = next(row for row in report["sites"] if not row.get("admission_only"))
    assert operation["source_statement"] is None

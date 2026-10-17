"""Original float fixture hints through public lower/merge seams; 2026-10-15 ET.

Compiler only: this verifies annotation placement and source preservation, not
establishment/preservation proofs. The actual matrix keeps every RTE obligation.
"""
import json

import pytest
import yaml

from conftest import FIXTURES, REPO, run_swdb
from swdb import c_lowering, hint_check
from test_wp_adapter import _hints
from test_wp_subset import GROUPS


@pytest.mark.skipif(bool(c_lowering.locate().missing), reason="clang 22.1.8 is missing")
def test_original_float_loop_keeps_field_initialization_as_proof_obligations(tmp_path):
    case = yaml.safe_load((FIXTURES / "proof/regression_corpus/wp-float-loop-field-initialization.yaml").read_text())
    given = case["input"]
    result = run_swdb("lower", "--source", REPO / given["source"], "--function", given["function"],
                      "--out", tmp_path, "--format", "json")
    assert result.returncode == 0, result.stderr
    source = (tmp_path / "swdb_float_unit.c").read_text()
    anchors = json.loads((tmp_path / "swdb_float_unit.anchors.json").read_text())["anchors"]
    hints = [hint for anchor, text in GROUPS[given["group"]][3] for hint in _hints(anchor, *text.splitlines())]
    merged = hint_check.merge(source, anchors, hints)
    loop = merged.text.split("/* swdb-anchor swdb_float_unit.loop1.head */", 1)[1].split("for (", 1)[0]
    for field in given["initialized_fields"]:
        assert f"loop invariant \\initialized(&r.{field});" in loop
    assert "loop assigns i, r.value;" in loop
    assert "loop variant n - i;" in loop
    # Invariants are additional proof obligations, never source writes or assumptions.
    assert hint_check.erase(merged.text) == source
    assert {hint["kind"] for hint in hints} == {"loop_invariant", "loop_assigns", "loop_variant"}
    assert "\\initialized(&r)" not in merged.text  # padding is not initialized by field writes
    assert "r.value = 0.0;" in source and "r.weight = (scale * 0.5f);" in source

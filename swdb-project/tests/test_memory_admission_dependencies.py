"""Conservative transitive accelerator-summary admission; created 2026-10-15 ET."""
import pytest
import yaml
from swdb import cbmc_translator as tr, cpu_memory_admission


@pytest.mark.parametrize("group", ["summaries", "models"])
def test_nested_dependencies_cannot_hide_semantics_or_use_missing_records(tmp_path, group):
    def write(name, pins):
        (tmp_path / (name + ".yaml")).write_text(yaml.safe_dump({"id": name, "kind": "proof", "pins": pins}))
    write("outer", {group: [{"proof_record": "inner"}]})
    write("inner", {"proof_semantics": {"not_applicable": "no accelerator"}})
    assert cpu_memory_admission.summary_refusal(tmp_path, ["outer"]) is None
    write("inner", {"proof_semantics": {"id": "semantics.dx100_bfs_0_1", "sha256": "a" * 64},
                    "summaries": [{"proof_record": "outer"}]})
    refused = cpu_memory_admission.summary_refusal(tmp_path, ["outer"])
    assert refused["refused"][0]["kind"] == "opaque_semantics_summary"
    assert refused["refused"][0]["proof_record"] == "inner"
    (tmp_path / "inner.yaml").unlink()
    assert cpu_memory_admission.summary_refusal(tmp_path, ["outer"])["refused"][0]["kind"] == "missing_summary_dependency"


def test_initialized_is_only_justified_for_fully_filled_input_buffer_ranges():
    unit = tr.Interface("f", "int", (("p", "int *", True), ("n", "int", False)))
    text = r"\initialized(p + (0 .. n - 1))"
    translated = tr.expression(text, unit, "harness", caps={"p": 4})
    assert "4LL" in translated and "n" in translated  # range check, never unconditional true
    for mode, extra in [("stub", {}), ("check", {}), ("harness", {"post": True}), ("harness", {})]:
        with pytest.raises(tr.Untranslatable, match="harness-owned input-buffer"):
            tr.expression(text, unit, mode, caps={} if mode == "harness" and not extra else {"p": 4}, **extra)

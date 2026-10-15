"""Ordered nested entry-window reads through prove; created 2026-10-15 ET."""
import json

import yaml

from conftest import run_swdb
from test_proof_semantics import dx, dx_seed
from test_wp_adapter import fake, needs_wp


def _contract(dx):
    path = dx.root / "library/rewrite_contracts/fixture_dx_three_reads.yaml"
    data = yaml.safe_load(path.read_text())
    data["proof_unit"]["array_domains"] = {"q": {"extent": "n"}, "base": {"extent": "n"}}
    path.write_text(yaml.safe_dump(data, sort_keys=False))


@needs_wp
def test_original_three_reads_retains_each_nested_read_as_a_checked_capture(dx):
    _contract(dx)
    result = run_swdb("prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", "dxf_three_reads", "--contract", "contract.fixture_dx_three_reads",
        "--adapter", "wp", "--runs-dir", dx.runs, "--format", "json", env=fake("unknown"), timeout=300)
    assert result.returncode == 0, result.stderr + result.stdout
    record = dx.read(json.loads(result.stdout))
    assert record["failure_class"] == "unknown", record
    nested = record["settings"]["nested_entry_reads"]
    assert len(nested["certificate"]["captures"]) == 2
    assert nested["input_premises_added"] == []
    assert record["settings"]["helper_windows"]["certificate"]["context_count"] == 1
    assert record["pins"]["nested_read_check"] and record["pins"]["nested_read_certificate"]
    report = next(row for row in record["evidence"]["reports"] if row["name"] == "wp_input")
    text = (dx.records / report["path"]).read_text()
    for capture in nested["certificate"]["captures"]:
        assert f'int {capture["name"]} = q[0];' in text
        assert f'base[{capture["name"]}]' in text


@needs_wp
def test_actual_original_three_reads_with_explicit_windows_proves(dx):
    from test_proof_semantics import prove_wp
    _contract(dx)
    record = prove_wp(dx, 'three_reads')
    assert record['verdict'] == 'proven', record.get('unproven_properties')
    assert len(record['settings']['nested_entry_reads']['certificate']['captures']) == 2
    assert record['settings']['helper_windows']['certificate']['context_count'] == 1
    assert record['settings']['nested_entry_reads']['input_premises_added'] == []

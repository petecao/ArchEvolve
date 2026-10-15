"""Checked helper source views through public prove; created 2026-10-15 ET.

Fake-WP controls check admission and fresh provenance, never a proved outcome.
"""
import json
import os
import subprocess
import sys

import pytest
import yaml

from conftest import REPO, run_swdb
from test_proof_semantics import dx, dx_seed
from test_wp_adapter import fake, needs_wp


def _contract(dx, *, domains=True):
    path = dx.root / "library/rewrite_contracts/fixture_dx_size.yaml"
    data = yaml.safe_load(path.read_text())
    if domains:
        data["proof_unit"]["array_domains"] = {"q": {"extent": "n"}}
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _run(dx, *, hints=None, tamper=None):
    args = []
    if hints is not None:
        path = dx.root / "helper-hints.yaml"
        path.write_text(yaml.safe_dump({"hints": hints}, sort_keys=False))
        args = ["--hint-file", str(path)]
    arguments = ["prove", "--records", dx.records, "--candidate", dx.candidates["dx"],
        "--function", "dxf_size", "--contract", "contract.fixture_dx_size",
        "--adapter", "wp", "--runs-dir", dx.runs, "--format", "json", *args]
    if tamper:
        script = '''from swdb import proof, wp_adapter
from swdb.cli import main
original = wp_adapter.WpAdapter._wp
def fault(self, job, path, context):
    view = context['helper_windows']['view']
    if TARGET == 'file':
        view.path.write_text(view.text + '\\n// changed after planning\\n')
    else:
        view.certificate['model_call_count'] = 0
    return original(self, job, path, context)
wp_adapter.WpAdapter._wp = fault
raise SystemExit(main())
'''.replace('TARGET', repr(tamper))
        return subprocess.run([sys.executable, "-c", script, *map(str, arguments)], cwd=REPO,
            env={**os.environ, **fake("unknown")}, text=True, capture_output=True, timeout=180)
    result = run_swdb(*arguments, env=fake("unknown"), timeout=180)
    assert result.returncode == 0, result.stderr + result.stdout
    return dx.read(json.loads(result.stdout))


@needs_wp
def test_helper_contexts_use_entry_windows_without_assuming_a_helper_contract(dx):
    _contract(dx)
    record = _run(dx)
    assert record["failure_class"] == "unknown", record
    helper = record["settings"]["helper_windows"]
    assert helper["certificate"]["context_count"] == 1
    assert helper["certificate"]["model_call_count"] == 4
    assert record["pins"]["helper_window_check"]
    assert record["pins"]["helper_window_certificate"]
    assert record["pins"]["helper_original_lowering"] != record["pins"]["c_lowering"]
    calls = [r for r in record["settings"]["pointer_bounds"]["sites"] if r.get("kind") == "call"]
    assert len(calls) == 1
    assert {r["origin"]["root"] for r in calls} == {"q"}
    assert helper["input_premises_added"] == []
    assert any(a["kind"] == "trusted_tool" and a["reference"] == record["pins"]["helper_window_check"]
               for a in record["assumptions"])
    assert all(s["name"] != "dxf_load" for s in record["pins"]["summaries"])


@needs_wp
def test_helper_view_does_not_synthesize_a_missing_entry_window(dx):
    _contract(dx, domains=False)
    record = _run(dx)
    assert record["failure_class"] == "unsupported_construct"
    assert record["settings"]["verifier_launched"] is False


@needs_wp
def test_helper_view_keeps_source_anchored_hints_closed(dx):
    _contract(dx)
    record = _run(dx, hints=[{"anchor": "dxf_size.entry", "kind": "assert", "text": "assert 1;",
                             "provenance": {"source": "agent"}}])
    assert record["failure_class"] == "unsupported_construct"
    assert "helper" in record["settings"]["helper_windows"]["reason"]
    assert record["settings"]["verifier_launched"] is False


@needs_wp
@pytest.mark.parametrize("tamper", ["file", "certificate"])
def test_changed_helper_view_or_certificate_refuses_before_wp_invocation(dx, tamper):
    _contract(dx)
    result = _run(dx, tamper=tamper)
    assert result.returncode == 1, result.stderr + result.stdout
    assert "proof setup check" in result.stderr, result.stderr
    assert not list(dx.records.glob("proofs/*.yaml"))


@needs_wp
@pytest.mark.parametrize("missing_initializedness", [False, True])
def test_actual_helper_size_proof_retains_original_source_initializedness(dx, missing_initializedness):
    from test_proof_semantics import prove_wp
    _contract(dx)
    if missing_initializedness:
        path = dx.root / "library/rewrite_contracts/fixture_dx_size.yaml"
        data = yaml.safe_load(path.read_text())
        for clause in data["clauses"]:
            if clause.get("acsl"):
                clause["acsl"]["text"] = clause["acsl"]["text"].replace(
                    "requires \\initialized(q + (0 .. n - 1));", "")
        path.write_text(yaml.safe_dump(data, sort_keys=False))
    record = prove_wp(dx, "size")
    if missing_initializedness:
        assert record["verdict"] == "not_proven", record
        assert any("source_initialized" in g["goal"] and g["status"] != "valid" for g in record["goals"])
    else:
        assert record["verdict"] == "proven", record.get("unproven_properties")
    assert record["settings"]["helper_windows"]["certificate"]["context_count"] == 1

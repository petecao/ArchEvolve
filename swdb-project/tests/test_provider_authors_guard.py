"""The provider guard keeps the DX100 authors' accelerated functions out of agent-role inputs.

Created: 2026-10-14 00:45 ET (Probata proof of concept, ticket 01; design spec "Testing Decisions"
seam 4, map 18 item 6, O2 default). Each guarded name has its own case, so dropping any one name
from the guard fails a test. The fixture provider writes a marker when called; a refused input
never reaches it.
"""

import json
import sys

import pytest
import yaml

from swdb import provider_roles, rewrite
from swdb.cli import Failure

REFUSAL = "agent role inputs must be text without authors' accelerated code"
ROLE = provider_roles.Role("read_only_fixture", {"type": "object"})


@pytest.fixture
def fixture_provider(tmp_path):
    """An external fixture provider that leaves a marker file if a call ever opens."""
    marker = tmp_path / "provider-called"
    program = tmp_path / "fixture.py"
    program.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('called')\nprint('{{}}')\n")
    configfile = tmp_path / "provider.yaml"
    configfile.write_text(yaml.safe_dump({"kind": "external_fixture", "command": [sys.executable, str(program)],
                                          "timeout_s": 5, "total_seconds": 5}))
    return rewrite.configuration(configfile), marker


def assert_refused_before_call(files, fixture_provider, folder):
    config, marker = fixture_provider
    with pytest.raises(Failure, match=REFUSAL):
        provider_roles.run(ROLE, files, "read", config, folder)
    assert not folder.exists() and not marker.exists()


GUARDED = ["PBFSMAA", "PageRankPullMAA", "DeltaStepMAA", "BrandesMaa", "TDStepMAA", "DOBFSMAA"]


@pytest.mark.parametrize("name", GUARDED)
def test_authors_function_in_source_file_is_refused_before_provider_call(name, fixture_provider, tmp_path):
    source = f"void {name}(const Graph &g) {{ maa_wait(); }}\n"
    assert_refused_before_call({"code.cc": source}, fixture_provider, tmp_path / "blocked")


@pytest.mark.parametrize("name", GUARDED)
def test_authors_function_in_json_input_is_refused_before_provider_call(name, fixture_provider, tmp_path):
    record = json.dumps({"removed_functions": [name], "summary": "scalar-only snapshot"})
    assert_refused_before_call({"context.json": record}, fixture_provider, tmp_path / "blocked")


BASELINES = ["PBFS", "Brandes", "PageRankPullGS", "DeltaStep", "TDStep", "DOBFS"]


@pytest.mark.parametrize("name", BASELINES)
def test_baseline_function_names_pass_the_guard_and_reach_the_provider(name, fixture_provider, tmp_path):
    config, marker = fixture_provider
    files = {"code.cc": f"void {name}(const Graph &g) {{}}\n",
             "context.json": json.dumps({"baseline_function": name})}
    result, metadata = provider_roles.run(ROLE, files, "read", config, tmp_path / "role")
    assert result == {} and metadata["audit"]["passed"] and marker.read_text() == "called"

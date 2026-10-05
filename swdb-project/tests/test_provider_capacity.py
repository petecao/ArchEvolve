"""Provider capacity is an uncounted D7 outcome (ticket 73). Created 2026-10-05 ET.

Classifies the raw Codex streams of native campaign a7's calls 4 and 5 ("Selected model is at
capacity"), which the harness had counted as failed rewrites. A campaign retries such a call after a
backoff, records it uncounted, and stops `infrastructure_failure` when capacity persists.
"""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from conftest import REPO
from swdb import provider_adapters
from swdb.extensa import search as S
from test_extensa_campaign import (campaign_file, campaign_store, fixture_file, log, provider, rewrite,  # noqa: F401
                                   run, team, team_seed)
from test_bfs_protocol import protocol_seed  # noqa: F401

FIXTURES = REPO / "tests" / "fixtures" / "provider_capacity"
A7_SHA256 = {"a7-call4.stdout.txt": "62c80ca14897b92bdb3604cafc0f18d5fb3a77575844a0ede896c5b1711f2828",
             "a7-call5.stdout.txt": "3463b259906f89e3d44c8d89f6e35f09a1764b749c2b27003256cd885303a0ee"}


def _folder(tmp_path, stdout, stderr=""):
    (tmp_path / "stdout.txt").write_text(stdout)
    (tmp_path / "stderr.txt").write_text(stderr)
    return tmp_path


@pytest.mark.parametrize("name", sorted(A7_SHA256))
def test_a7_raw_capacity_streams_classify_as_provider_capacity(tmp_path, name):
    raw = (FIXTURES / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == A7_SHA256[name]          # the exact retained a7 bytes
    folder = _folder(tmp_path, raw.decode(), (FIXTURES / "a7-stderr.txt").read_text())
    with pytest.raises(provider_adapters.ProviderCapacity, match="at capacity"):
        provider_adapters.check_usage(folder)


@pytest.mark.parametrize("message", [
    "Selected model is at capacity. Please try a different model.",
    "The server is overloaded; please retry",
    "upstream returned status 503 Service Unavailable",
    "stream disconnected before completion: error sending request",
    "Bad Gateway",
])
def test_transient_provider_errors_are_capacity_not_failures(tmp_path, message):
    event = json.dumps({"type": "turn.failed", "error": {"message": message}})
    with pytest.raises(provider_adapters.ProviderCapacity):
        provider_adapters.check_usage(_folder(tmp_path, event + "\n"))


def test_usage_limit_stays_a_usage_limit_and_quoted_text_is_ignored(tmp_path):
    event = json.dumps({"type": "error", "message": "You have hit your usage limit; the model is at capacity"})
    with pytest.raises(provider_adapters.ProviderUnavailable) as caught:
        provider_adapters.check_usage(_folder(tmp_path, event + "\n"))
    assert not isinstance(caught.value, provider_adapters.ProviderCapacity)
    quoted = json.dumps({"type": "item.completed", "item": {"type": "agent_message",
                                                            "text": "the queue is at capacity; service unavailable"}})
    provider_adapters.check_usage(_folder(tmp_path, quoted + "\n"))        # not an error event: no raise


def test_capacity_is_an_uncounted_call_outcome():
    assert S.CallOutcome.PROVIDER_CAPACITY in S.UNCOUNTED_CALL_OUTCOMES


def _capacity_provider(team, rewriting):
    """The campaign fixture provider, whose `capacity` items replay a7 call 4's raw stream."""
    config = provider(team, {"rewriting": rewriting})
    program = team["root"] / "provider.py"
    stream = (FIXTURES / "a7-call4.stdout.txt").read_text()
    program.write_text(program.read_text().replace(
        "if item == 'login':",
        f"if item == 'capacity':\n    sys.stdout.write({stream!r}); sys.exit(1)\nif item == 'login':", 1))
    return config


def test_campaign_retries_a_capacity_call_uncounted_and_continues(team):
    config = _capacity_provider(team, ["capacity", "capacity", rewrite()])
    path = campaign_file(team, budgets={"max_iterations": 1})
    summary = run(team, path, fixture_file(team), config, env={"SWDB_CAPACITY_BACKOFF_S": "0,0,0"})
    (iteration,) = summary["iterations"]
    calls = [c for c in iteration["provider_calls"] if c["role"] == "rewriting"]
    assert [c["outcome"] for c in calls] == ["provider_capacity", "provider_capacity", "completed"]
    assert [c["counted"] for c in calls] == [False, False, True]
    assert all(c["backoff_s"] == 0 for c in calls[:2])
    assert summary["budgets"]["used"]["provider_calls_uncounted"] == 2
    assert "provider_output_invalid" not in iteration["feedback_reasons"]
    assert iteration["candidates"]                                    # the retried call produced a candidate


def test_persistent_capacity_stops_the_campaign_as_infrastructure_failure(team):
    config = _capacity_provider(team, ["capacity"])
    path = campaign_file(team, budgets={"max_iterations": 3})
    summary = run(team, path, fixture_file(team), config, env={"SWDB_CAPACITY_BACKOFF_S": "0,0"})
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "stayed unavailable" in summary["stop_detail"]
    assert summary["iterations"] == []                                  # no iteration completed
    calls = [c for c in summary["interrupted_iteration"]["provider_calls"] if c["role"] == "rewriting"]
    assert len(calls) == 3 and all(c["outcome"] == "provider_capacity" and c["counted"] is False for c in calls)
    assert summary["budgets"]["used"]["provider_calls_uncounted"] == 3
    assert summary["budgets"]["used"]["provider_calls_counted"] == 1          # the setup call only

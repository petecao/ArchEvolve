"""One classification of provider-call outcomes (code review P1). Created 2026-10-05 ET.

The ticket 58 driver caught `ProviderUnavailable`, which absorbed `ProviderCapacity` (recorded
as `usage_limit`), and a guard runtime-limit stop (`GuardInfrastructure`) fell into its generic
`Failure` branch and was counted. Every stop that is not the model's work is now an
`UncountedStop` naming its own call outcome, and the Extensa campaign, its synthesis calls and
the driver share `provider_adapters.classify`. The driver and campaign cases replay the retained
a7 capacity streams and a8 guard receipts through the real role launcher with a fixture provider.
"""

import json

import pytest

from conftest import FIXTURES
from swdb import provider_adapters as adapters
from swdb.cli import Failure
from swdb.extensa import search as S
from testkit.drivers import campaign_root, driver_args, offline_inputs, spec_enough_driver
from testkit.extensa import campaign_file, fixture_file, provider, replay, rewrite, run

LEAVES = (adapters.UsageLimit, adapters.ProviderCapacity, adapters.GuardInfrastructure, adapters.LoginRequired)
A7 = FIXTURES / "provider_capacity" / "a7-call4.stdout.txt"
A8 = {kind: FIXTURES / "provider_guard_a8" / f"a8-call1.{kind}" for kind in ("resource-overrun.json", "guard-audit.json")}
CODEX_STDERR = "Reading additional input from stdin..."
REFRESH_REUSED = ('ERROR: 401 {"error":{"message":"Your refresh token has already been used",'
                  '"code":"refresh_token_reused"}}')


# --- the exception types and the classifier --------------------------------------------------------

def test_uncounted_stops_are_sibling_leaves_naming_their_own_uncounted_outcome():
    for leaf in LEAVES:
        assert issubclass(leaf, adapters.UncountedStop) and issubclass(leaf, Failure)
        assert S.CallOutcome(leaf.outcome) in S.UNCOUNTED_CALL_OUTCOMES
        assert not any(issubclass(leaf, other) for other in LEAVES if other is not leaf)
    assert {S.CallOutcome(leaf.outcome) for leaf in LEAVES} == set(S.UNCOUNTED_CALL_OUTCOMES)
    # ArchEvolve mode's `provider_unavailable` (no repair consumed) groups usage limit and capacity only.
    assert [leaf for leaf in LEAVES if issubclass(leaf, adapters.ProviderUnavailable)] == \
        [adapters.UsageLimit, adapters.ProviderCapacity]


@pytest.mark.parametrize("leaf", LEAVES)
def test_an_uncounted_stop_is_classified_by_its_type_not_its_text(leaf, tmp_path):
    (tmp_path / "stderr.txt").write_text("Error: not logged in; request timed out; invalid JSON; guard audit")
    assert adapters.classify(leaf("usage limit reached; at capacity"), tmp_path) == S.CallOutcome(leaf.outcome)


@pytest.mark.parametrize("stderr", [
    "Error: not logged in",
    REFRESH_REUSED,
    'ERROR: 401 {"error":{"code":"token_invalidated"}}',
    "authentication required",
])
def test_one_login_pattern_reads_the_call_folder_stderr(stderr, tmp_path):
    (tmp_path / "stderr.txt").write_text(stderr)
    assert adapters.classify(Failure("rewrite provider exited 1; retained folder"), tmp_path) == S.CallOutcome.LOGIN
    assert adapters.classify(Failure("rewrite provider exited 1"), tmp_path, detailed=False) == S.CallOutcome.LOGIN
    assert adapters.classify(Failure("rewrite provider exited 1")) == S.CallOutcome.FAILED     # no folder, no login


@pytest.mark.parametrize("message, outcome", [
    ("rewrite provider timed out after 1200 s", S.CallOutcome.TIMEOUT),
    ("rewrite provider returned invalid structured output: x", S.CallOutcome.MALFORMED_OUTPUT),
    ("provider role audit failed: awk program cannot be audited", S.CallOutcome.GUARD_REFUSED),
    ("rewrite provider exited 2", S.CallOutcome.FAILED),
])
def test_counted_failures_keep_the_campaign_classification(message, outcome, tmp_path):
    assert adapters.classify(Failure(message), tmp_path) == outcome
    assert outcome not in S.UNCOUNTED_CALL_OUTCOMES
    # A synthesis call's failure can also be its entry's own validation: only login is read from text.
    assert adapters.classify(Failure(message), detailed=False) == S.CallOutcome.FAILED


def test_none_is_a_completed_call():
    assert adapters.classify(None) == S.CallOutcome.COMPLETED


def test_a7_capacity_stream_is_capacity_not_a_usage_limit(tmp_path):
    (tmp_path / "stdout.txt").write_bytes(A7.read_bytes())
    (tmp_path / "stderr.txt").write_text(CODEX_STDERR)
    with pytest.raises(adapters.UncountedStop) as caught:
        adapters.check_usage(tmp_path)
    assert adapters.classify(caught.value, tmp_path) == S.CallOutcome.PROVIDER_CAPACITY


# --- the ticket 58 driver --------------------------------------------------------------------------

def _driver(tmp_path, monkeypatch, plan):
    module = spec_enough_driver()
    offline_inputs(module, monkeypatch)
    config = provider({"root": tmp_path}, {"testgen": plan})
    return module, driver_args(module, tmp_path, config)


def _ledger(tmp_path):
    return json.loads((campaign_root(tmp_path) / "provider-ledger-a3.json").read_text())["calls"]


def test_driver_records_the_a7_capacity_stop_uncounted_pauses_and_retries_on_resume(tmp_path, monkeypatch):
    module, args = _driver(tmp_path, monkeypatch, [replay(stdout=A7, stderr=CODEX_STDERR),
                                                   {"patch": "--- a/x\n", "unresolved": []}])
    with pytest.raises(Failure, match=r"provider paused \(provider_capacity\); uncounted"):
        module.provider_stage(args)
    (row,) = _ledger(tmp_path)
    assert row["outcome"] == "provider_capacity" and row["counted"] is False     # was usage_limit before P1
    runs = campaign_root(tmp_path) / "runs-a3"
    assert json.loads((runs / "spec-s1" / "failure.json").read_text())["outcome"] == "provider_capacity"
    module.provider_stage(args)                                    # resume: the sample is retried
    rows = _ledger(tmp_path)
    assert [r["outcome"] for r in rows[:2]] == ["provider_capacity", "completed"]
    assert (runs / "spec-s1.paused1" / "failure.json").is_file() and (runs / "spec-s1" / "response.json").is_file()
    assert sum(r["counted"] for r in rows) == len(rows) - 1


def test_driver_leaves_the_a8_guard_runtime_stop_uncounted(tmp_path, monkeypatch):
    module, args = _driver(tmp_path, monkeypatch, [replay(stderr=CODEX_STDERR, call_files={
        name: path for name, path in A8.items()})])
    with pytest.raises(Failure, match=r"provider paused \(guard_infrastructure\); uncounted"):
        module.provider_stage(args)
    (row,) = _ledger(tmp_path)
    assert row["outcome"] == "guard_infrastructure" and row["counted"] is False   # was counted as failed
    assert "threads=17" in row["error"]
    assert not (campaign_root(tmp_path) / "STOP-a3").exists()


def test_driver_reads_a_reused_refresh_token_on_stderr_as_login(tmp_path, monkeypatch):
    module, args = _driver(tmp_path, monkeypatch, [replay(stderr=REFRESH_REUSED)])
    with pytest.raises(Failure, match=r"provider paused \(login\); uncounted"):
        module.provider_stage(args)
    (row,) = _ledger(tmp_path)
    assert row["outcome"] == "login" and row["counted"] is False and "login_source_short_hash" in row


def test_driver_counts_a_failure_that_is_the_models_and_stops_after_two(tmp_path, monkeypatch):
    module, args = _driver(tmp_path, monkeypatch, [{"patch": 7, "unresolved": []}])
    with pytest.raises(Failure, match="the first 2 sessions failed"):
        module.provider_stage(args)
    rows = _ledger(tmp_path)
    assert [(r["outcome"], r["counted"]) for r in rows] == [("malformed_output", True)] * 2


def test_driver_resume_recognizes_paused_rows_of_earlier_attempts(tmp_path):
    module = spec_enough_driver()
    assert module.uncounted({"outcome": "usage_limit", "counted": False})          # a1-a3 row
    assert module.uncounted({"outcome": "provider_capacity"})
    assert not module.uncounted({"outcome": "failed", "counted": True})


# --- the Extensa campaign ----------------------------------------------------------------------------

def test_campaign_reads_a_reused_refresh_token_as_an_uncounted_login_pause(campaign_team):
    """The campaign's own login pattern lacked token_invalidated / refresh_token_reused before P1."""
    path = campaign_file(campaign_team, budgets={"provider_calls_setup": 0})
    config = provider(campaign_team, {"rewriting": [replay(stderr=REFRESH_REUSED), rewrite()]})
    paused = run(campaign_team, path, fixture_file(campaign_team), config)
    assert paused["state"] == "paused" and paused["reason"] == "login"

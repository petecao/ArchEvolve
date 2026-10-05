"""The guard's thread caps follow what they protect (ticket 74). Created 2026-10-05 ET.
Updated 2026-10-05 ET (code review: `guard_runtime_limit`, LIMITS, the shared CPU-list parser, and
the fixture provider's `replay` hook instead of patching its program text).

Replays native campaign a8's calls 1 (setup profiling) and 6 (iteration 5): the guard stopped Codex
after about 0.5 s with "threads=17" (strace 1 + Codex 16: 12 tokio threads, 2 inotify watchers,
main, codex-main) and the Extensa campaign counted both. The provider runtime and the tool commands
the model starts now have separate caps, and a stop for the guard's own runtime limit is an uncounted
infrastructure pause. Runs on the Mac: the a8 receipts are byte copies, and the fixture provider
replays them into its call folder exactly where the observer wrote them on mbit10.
"""

import hashlib
import json
import shutil

import pytest

from conftest import REPO
from swdb import profile, provider_adapters, provider_guard, provider_roles
from swdb.extensa import search as S
from testkit.extensa import campaign_file, fixture_file, log, provider, replay, rewrite, run

FIXTURES = REPO / "tests" / "fixtures" / "provider_guard_a8"
A8_SHA256 = {
    "a8-call1.resource-overrun.json": "94cd7c7dcb80e948d7b935289c900e44095c32ce98164ed8c99aaa502c31d2d5",
    "a8-call1.guard-audit.json": "177d183058a096c673f028247dad5136c06caa1ba20fdc70c0ae6996e9efbfc2",
    "a8-call6.resource-overrun.json": "8449345d004a0bb79650190c96d51580386dcd79415863b8b68d71094ecd7cc4",
    "a8-call6.guard-audit.json": "6995e804ef22dabd086c567e0a50dd4d50be0973c87971a23f8219c8991a454d",
}
LIMITS = provider_guard.LIMITS


def _a8(call):
    rows = json.loads((FIXTURES / f"a8-{call}.resource-overrun.json").read_text())
    audit = json.loads((FIXTURES / f"a8-{call}.guard-audit.json").read_text())
    return rows, audit


def _call_folder(tmp_path, call):
    folder = tmp_path / call
    folder.mkdir()
    for kind in ("resource-overrun.json", "guard-audit.json"):
        shutil.copyfile(FIXTURES / f"a8-{call}.{kind}", folder / kind)
    return folder


def _row(pid, threads, start=1000, rss=1 << 20):
    return {"pid": pid, "start_time_ticks": start, "threads": threads, "resident_bytes": rss}


@pytest.mark.parametrize("name", sorted(A8_SHA256))
def test_a8_receipts_are_the_retained_bytes(name):
    assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == A8_SHA256[name]


@pytest.mark.parametrize("call", ["call1", "call6"])
def test_a8_tree_was_the_codex_runtime_alone_and_fits_the_new_caps(call):
    rows, audit = _a8(call)
    # The old guard charged one aggregate cap: 17 > 16 stopped the call.
    assert sum(r["threads"] for r in rows) == 17
    tracer = audit["process_cleanup"]["tracer_pid"]
    provider = audit["original_provider"]
    codex = next(r for r in rows if r["pid"] == provider["pid"])
    assert codex["tasks"].count("tokio-rt-worker") == 12 and codex["threads"] == 16
    assert {r["pid"] for r in rows} == {tracer, provider["pid"]}           # no tool command had started
    keys = {(r["pid"], r["start_time_ticks"]) for r in rows}
    verdict = provider_guard.resource_scope(rows, keys, LIMITS)
    assert verdict["scope"] is None and verdict["reason"] is None
    assert verdict["runtime"]["threads"] == 17 and verdict["tools"] == {"threads": 0, "resident_bytes": 0,
                                                                        "processes": 0}


@pytest.mark.parametrize("call", ["call1", "call6"])
def test_a8_guard_stops_classify_as_guard_runtime_limits(tmp_path, call):
    reason = provider_guard.guard_runtime_limit(_call_folder(tmp_path, call))
    assert reason and "threads=17" in reason and "legacy aggregate cap" in reason and "within limits" in reason


def test_tool_work_over_its_cap_is_the_models_and_takes_precedence():
    tracer, cli, tool = _row(10, 1), _row(11, 16), _row(12, 17)
    keys = {(10, 1000), (11, 1000)}
    verdict = provider_guard.resource_scope([tracer, cli, tool], keys, LIMITS)
    assert verdict["scope"] == "tools" and verdict["reason"].startswith(provider_guard.RESOURCE_REASON + ": tool threads=17")
    runaway = provider_guard.resource_scope([tracer, _row(11, 64), tool], keys, LIMITS)
    assert runaway["scope"] == "tools"                                     # both over: the tools decide
    runtime = provider_guard.resource_scope([tracer, _row(11, 64), _row(12, 3)], keys, LIMITS)
    assert runtime["scope"] == provider_guard.RUNTIME_SCOPE == "runtime"      # the persisted value is unchanged
    assert "guard runtime limit" in runtime["reason"]
    assert runtime["reason"].startswith(provider_guard.RESOURCE_REASON)


def test_memory_stays_one_aggregate_cap_charged_to_whoever_crossed_it():
    keys = {(11, 1000)}
    half = 17 * 1024**3
    pushed = provider_guard.resource_scope([_row(11, 4, rss=half), _row(12, 2, rss=half)], keys, LIMITS)
    assert pushed["scope"] == "tools"
    alone = provider_guard.resource_scope([_row(11, 4, rss=33 * 1024**3)], keys, LIMITS)
    assert alone["scope"] == "runtime"


def test_a_cli_not_yet_named_by_the_handshake_is_charged_as_a_tool():
    rows, _ = _a8("call1")
    tracer = next(r for r in rows if r["tasks"] == ["strace"])
    verdict = provider_guard.resource_scope(rows, {(tracer["pid"], tracer["start_time_ticks"])}, LIMITS)
    assert verdict["tools"]["threads"] == 16 and verdict["scope"] is None   # still within the tool cap


def _write(folder, audit, record):
    folder.mkdir(exist_ok=True)
    (folder / "guard-audit.json").write_text(json.dumps(audit))
    (folder / "resource-overrun.json").write_text(json.dumps(record))
    return folder


def test_guard_runtime_limit_refuses_anything_but_a_runtime_only_stop(tmp_path):
    rows, audit = _a8("call1")
    assert provider_guard.guard_runtime_limit(tmp_path) is None                                   # no receipts
    # A legacy record whose tool processes were over the tool cap is the model's work.
    tool = {**rows[1], "pid": 999, "start_time_ticks": 1, "threads": 18, "tasks": ["python"] * 18}
    assert provider_guard.guard_runtime_limit(_write(tmp_path / "a", audit, rows + [tool])) is None
    # Any other guard reason (network, cleanup) keeps the call counted.
    other = {**audit, "reasons": audit["reasons"] + ["provider outbound connection is outside the model API"]}
    assert provider_guard.guard_runtime_limit(_write(tmp_path / "b", other, rows)) is None
    assert provider_guard.guard_runtime_limit(_write(tmp_path / "c", {**audit, "passed": True}, rows)) is None
    v2 = {"format": "swdb.guard-overrun.v2", "scope": "tools", "reason": audit["reasons"][0]}
    assert provider_guard.guard_runtime_limit(_write(tmp_path / "d", audit, v2)) is None
    runtime = {**v2, "scope": "runtime", "reason": "provider resource limit exceeded by the provider runtime"}
    assert provider_guard.guard_runtime_limit(_write(tmp_path / "e", audit, runtime)) == runtime["reason"]


def test_the_lane_cpu_check_parses_kernel_cpu_lists_with_the_profile_parser():
    # J4 (2026-10-05 ET): `_task_cpus` reuses the profile's parser instead of a second copy.
    assert profile._cpu_set("1,3-5,32-33\n") == {1, 3, 4, 5, 32, 33}
    assert profile._cpu_set("") == set()


def test_guard_infrastructure_is_an_uncounted_call_outcome():
    assert S.CallOutcome.GUARD_INFRASTRUCTURE in S.UNCOUNTED_CALL_OUTCOMES
    assert not issubclass(provider_adapters.GuardInfrastructure, provider_adapters.ProviderUnavailable)


# --- the role and the campaign ------------------------------------------------------------

def _a8_stop(call):
    """Replays one a8 call's guard receipts into its call folder (where the observer wrote them on
    mbit10) and exits 1, as the stopped CLI did."""
    return replay(stderr="Reading additional input from stdin...",
                  call_files={kind: FIXTURES / f"a8-{call}.{kind}" for kind in ("resource-overrun.json", "guard-audit.json")})


def _replay_provider(campaign_team, plan):
    """The campaign fixture provider; a `guard_a8_*` plan item becomes that a8 call's replay."""
    return provider(campaign_team, {role: [_a8_stop(item.rsplit("_", 1)[1]) if isinstance(item, str)
                                           and item.startswith("guard_a8_") else item for item in items]
                                    for role, items in plan.items()})


def test_role_run_raises_guard_infrastructure_for_the_a8_stop(campaign_team, tmp_path):
    from swdb import rewrite as rewrite_module
    config = rewrite_module.configuration(_replay_provider(campaign_team, {"profiling": ["guard_a8_call1"]}))
    with pytest.raises(provider_adapters.GuardInfrastructure, match="threads=17"):
        provider_roles.run(provider_roles.Role("extensa_profiling", {
            "type": "object", "additionalProperties": False, "required": ["notes"],
            "properties": {"notes": {"type": "array", "items": {"type": "string"}}}}),
            {"source/bfs.cc": "int main() { return 0; }\n"}, "Profile.", config, tmp_path / "call1")


def test_campaign_retries_the_a8_guard_stops_uncounted_and_continues(campaign_team):
    config = _replay_provider(campaign_team, {"profiling": ["guard_a8_call1", {"notes": ["fixture"]}],
                                     "rewriting": ["guard_a8_call6", rewrite()]})
    path = campaign_file(campaign_team, budgets={"max_iterations": 1})
    summary = run(campaign_team, path, fixture_file(campaign_team), config, env={"SWDB_GUARD_RETRY_S": "0"})
    (iteration,) = summary["iterations"]
    calls = [c for c in iteration["provider_calls"] if c["role"] == "rewriting"]
    assert [c["outcome"] for c in calls] == ["guard_infrastructure", "completed"]
    assert [c["counted"] for c in calls] == [False, True]
    assert calls[0]["retry_after_s"] == 0 and "threads=17" in calls[0]["guard_reason"]
    used = summary["budgets"]["used"]
    assert used["provider_calls_uncounted"] == 2                         # setup call 1 and iteration call 6
    roles = [entry["role"] for entry in log(campaign_team)]
    assert roles.count("profiling") == 2 and roles.count("rewriting") == 2
    # Every invocation but the two replayed guard stops is counted (their retries included).
    assert used["provider_calls_counted"] == len(roles) - 2
    assert "provider_output_invalid" not in iteration["feedback_reasons"]
    assert iteration["candidates"]                                       # the retried call produced a candidate


def test_persistent_guard_stops_end_the_campaign_as_infrastructure_failure(campaign_team):
    config = _replay_provider(campaign_team, {"rewriting": ["guard_a8_call6"]})
    path = campaign_file(campaign_team, budgets={"max_iterations": 3})
    summary = run(campaign_team, path, fixture_file(campaign_team), config, env={"SWDB_GUARD_RETRY_S": "0"})
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "stopped 3 consecutive rewriting calls for its own runtime limit" in summary["stop_detail"]
    assert summary["iterations"] == []
    calls = [c for c in summary["interrupted_iteration"]["provider_calls"] if c["role"] == "rewriting"]
    assert len(calls) == 3 and all(c["outcome"] == "guard_infrastructure" and not c["counted"] for c in calls)
    assert summary["budgets"]["used"]["provider_calls_counted"] == 1     # the setup call only

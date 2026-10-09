"""Real campaign target adapters (tickets 56 and 57) on fixture runners.

Created: 2026-10-04 ET. The adapters' evaluator commands are replaced by a fixture runner
(every number comes from the test, labeled here, never evidence); the campaign loop, the
candidate-artifact path (patch, knobs, canonical header), the session-begin check, the
per-role native protocols and paired blocks, the single gem5 baseline per class and the
dispatch preflight memory admission run for real.
"""

import json
from argparse import Namespace
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from swdb import artifacts, campaign, campaign_targets
from swdb.store import Store
from testkit.extensa import knob_rows, provider
from testkit.extensa_targets import CONTRACT, FakeHost, FakeRunner, KRON18_S0, UNIFORM18_S0, common, diff, fake_certify, gem5_campaign, inside_patch, run, write_campaign

GIB = 1024 ** 3
KRON18 = "bfs-20260925-kronecker18.48de8267ac2098d5"
UNIFORM18 = "bfs-20260925-uniform18.cd2169a5c421baf7"
UNIFORM22 = "bfs-20260925-uniform22.f23b09bb0c0601b5"
FORK = "bfs-native-pilot-20260925-dx10018-a1.baseline"
UPSTREAM = "bfs-native-pilot-20260925-upstream18-a2.baseline"


# --- session begin inside the timed call -----------------------------------------------

DOBFS = """pvector<NodeID> DOBFS(const Graph &g, NodeID source, bool logging_enabled = false,
                      int alpha = 1, int beta = 18) {
    init_MAA();
    %s
    t.Start();
    return parent;
}
"""


def test_session_begin_inside_timed_call_passes():
    source = "int helper() { return DOBFS(g, 0); }\n" + DOBFS % "__dxc_session_begin();"
    assert campaign_targets.session_begin_problem(source) is None


@pytest.mark.parametrize("source, reason", [
    ("static int swdb_setup = (__dxc_session_begin(), 0);\n" + DOBFS % "", "outside the timed DOBFS call"),
    ("int main() { __dxc_session_begin(); return 0; }\n" + DOBFS % "", "outside the timed DOBFS call"),
    ("void setup() { __dxc_session_begin(); }\n" + DOBFS % "setup();", "outside the timed DOBFS call"),
    (DOBFS % "// __dxc_session_begin();", "never begins a DX100 session"),
    ("#define __dxc_session_begin() noop()\n" + DOBFS % "__dxc_session_begin();", "macro redefines"),
    ("pvector<NodeID> DOBFS(const Graph &g);\nvoid f() { __dxc_session_begin(); }\n", "is not defined"),
])
def test_session_begin_outside_timed_call_is_refused(source, reason):
    assert reason in campaign_targets.session_begin_problem(source)


# --- fixtures ------------------------------------------------------------------------------


def outside_patch(base):
    return diff(base, "static int swdb_early = (__dxc_session_begin(), 0);\n" + base)


def native_patch(base):
    return diff(base, base + "// campaign fixture edit\n")


# --- gem5 (ticket 57) --------------------------------------------------------------------------


def test_gem5_one_baseline_per_class_point_ratios_and_memory_admission(repo_team, base_source):
    patch = inside_patch(base_source)
    config = provider(repo_team, {"rewriting": [{"patch": patch, "contracts": [CONTRACT],
                                            "knobs": knob_rows({"kronecker": {"frontier_threshold": 32}}), "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02}), FakeHost()
    loop, summary = run(repo_team, gem5_campaign(repo_team), config, runner, host)
    assert summary["stop_reason"] == "max_iterations" and summary["evidence_basis"] == "simulated"
    executes = [c for c in runner.calls if c["command"] == "dx100-execute"]
    baselines = [c for c in executes if c["request"]["protocol_role"] == "baseline"]
    # one baseline evaluation per class serves both iterations' candidates
    assert sorted(c["request"]["workload"]["id"] for c in baselines) == sorted([KRON18_S0, UNIFORM18_S0])
    compares = [c["request"] for c in runner.calls if c["command"] == "compare-evaluations"]
    assert len(compares) == 4
    for cls in ("kronecker", "uniform_random"):
        cited = {c["baseline_evaluation"] for c in compares if f".{cls}." in c["id"]}
        assert cited == {f"extensa-gem5-bfs-20261004-f1.baseline.{cls}.aggregate"}
    assert all(set(c["companion_evaluations"]) == {"timed", "diagnostic"} for c in compares)
    # every gem5 run was admitted against the lane's memory node at 36 GiB first
    gem5_admissions = [p for p in host.preflights if p["memory_bytes"] == 36 * GIB]
    assert len(gem5_admissions) >= len(executes)
    rows = summary["iterations"][0]["candidates"]
    kron = next(r for r in rows if r["class"] == "kronecker")
    assert kron["comparisons"][0]["lower"] == kron["comparisons"][0]["ratio"] == 1.4
    assert kron["comparisons"][0]["spread"] == 0.0 and kron["level"] == "certified"
    per_class = {r["class"]: r for r in summary["per_class"]}
    assert per_class["kronecker"]["verdict"] == "gain" and per_class["uniform_random"]["verdict"] == "no_gain"
    assert all(r["label"] == "single graph per class" for r in summary["per_class"])
    # knobs reach only the kronecker artifact, as a define at the top of bfs.cc, with the header added
    store = Store(loop.store_dir)
    tree = Path(store.get(kron["id"], "candidate")["artifact"]["path"])
    assert (tree / campaign_targets.BFS).read_text().splitlines()[1] == "#define SWDB_KNOB_FRONTIER_THRESHOLD 32"
    assert (tree / campaign_targets.HEADER).read_bytes() == (REPO / "library/dx100/dxc_lowering.hpp").read_bytes()
    candidate = store.get(kron["id"], "candidate")
    assert candidate["mode"] == "extensa" and candidate["campaign"] == "extensa-gem5-bfs-20261004-f1"
    assert store.get("extensa-gem5-bfs-20261004-f1.summary", "campaign_summary") is not None


def test_gem5_session_begin_outside_is_refused_before_any_job(repo_team, base_source):
    config = provider(repo_team, {"rewriting": [{"patch": outside_patch(base_source), "contracts": [CONTRACT],
                                            "knobs": [], "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4}), FakeHost()
    _, summary = run(repo_team, gem5_campaign(repo_team, max_iterations=1), config, runner, host)
    rows = summary["iterations"][0]["candidates"]
    assert {r["level"] for r in rows} == {"rejected"}
    assert all("outside the timed DOBFS call" in r["rejection"] for r in rows)
    assert not [c for c in runner.calls if c["command"] in {"dx100-compile", "dx100-execute"}]
    assert summary["iterations"][0]["feedback_reasons"] == ["correctness_failed"]
    assert {r["verdict"] for r in summary["per_class"]} == {"no_gain"}


def test_gem5_edit_without_contract_is_refused(repo_team, base_source):
    config = provider(repo_team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4})
    _, summary = run(repo_team, gem5_campaign(repo_team, max_iterations=1), config, runner, FakeHost())
    assert {r["level"] for r in summary["iterations"][0]["candidates"]} == {"rejected"}
    assert not [c for c in runner.calls if c["command"] == "dx100-execute"]


# --- native CPU (ticket 56) ----------------------------------------------------------------------

def native_campaign(repo_team, workloads=(KRON18, UNIFORM18), **budgets):
    data = common(repo_team, "extensa-native-bfs-20261004-f1", "native_cpu")
    data.update(baselines=[{"role": "fork_scalar_tdstep", "candidate": FORK},
                           {"role": "upstream_do_bfs", "candidate": UPSTREAM}],
                protocol={"roi": "bfs.complete_call.v1", "threads": 1, "repetitions": 10,
                          "sources": [0, 1234, 7777], "region_pairs": False,
                          "differences": "Extensa native fixture campaign."},
                workload_classes=[{"class": "kronecker", "workload": workloads[0]},
                                  {"class": "uniform_random", "workload": workloads[1]}],
                library={"allowed_tiers": ["shared", "experimental"], "contracts": []})
    data["budgets"].update(budgets)
    return write_campaign(repo_team, data)


def test_native_paired_blocks_against_both_baselines_select_on_fork(repo_team, base_source):
    config = provider(repo_team, {"rewriting": [{"patch": native_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    _, summary = run(repo_team, native_campaign(repo_team, max_iterations=1), config, runner, FakeHost())
    freezes = [c["request"] for c in runner.calls if c["command"] == "freeze-protocol"]
    assert [f["id"] for f in freezes] == ["extensa-native-bfs-20261004-f1.protocol.fork_scalar_tdstep",
                                          "extensa-native-bfs-20261004-f1.protocol.upstream_do_bfs",
                                          "extensa-native-bfs-20261004-f1.protocol.upstream_do_bfs.aa"]
    # Ticket 63: the upstream A/A pilot freezes both sides as the upstream baseline build.
    aa = freezes[2]["settings"]
    assert aa["builds"]["candidate"] == aa["builds"]["baseline"] == freezes[1]["settings"]["builds"]["baseline"]
    upstream = freezes[1]["settings"]["builds"]
    assert upstream["baseline"]["adapter"] == "gapbs_native" and upstream["candidate"]["adapter"] == "dx100_scalar_func"
    assert all(f["settings"]["targets"]["baseline"]["configuration"] == {"lane": "mbit10-evaluation-node0"}
               for f in freezes)
    pairs = [c["request"] for c in runner.calls if c["command"] == "evaluate-pair"]
    pilots = [p for p in pairs if ".pilot." in p["id"]]
    assert len(pilots) == 4 and all(p["baseline"]["candidate"] == p["candidate"]["candidate"] for p in pilots)
    assert all(p["baseline"]["protocol"].endswith(".upstream_do_bfs.aa.0123456789abcdef") == (".upstream_do_bfs." in p["id"])
               for p in pilots)
    blocks = [p for p in pairs if ".pilot." not in p["id"]]
    assert len(blocks) == 4            # two classes x two baselines, each its own paired block
    for p in blocks:
        role = p["id"].rsplit(".", 2)[-2]
        assert p["baseline"]["candidate"] == {"fork_scalar_tdstep": FORK, "upstream_do_bfs": UPSTREAM}[role]
        assert p["baseline"]["protocol"].endswith(f".protocol.{role}.0123456789abcdef")
    assert len({p["baseline"]["id"] for p in blocks}) == 4
    assert summary["pilot"]["passed"] is True
    per_class = {r["class"]: r for r in summary["per_class"]}
    for cls in ("kronecker", "uniform_random"):
        row = per_class[cls]
        assert row["verdict"] == "gain" and row["best_level"] == "uncertified"
        assert row["best_selection_baseline"] == "fork_scalar_tdstep"
        assert row["best_other_baseline"]["role"] == "upstream_do_bfs"
        assert row["best_other_baseline"]["verdict"] == "no_gain"
    assert summary["protocol"]["by_role"].keys() == {"fork_scalar_tdstep", "upstream_do_bfs"}
    assert summary["evidence_basis"] == "measured"


def test_native_pilot_spread_stops_without_provider_call(repo_team, base_source):
    config = provider(repo_team, {})
    runner = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14})
    _, summary = run(repo_team, native_campaign(repo_team), config, runner, FakeHost())
    assert summary["stop_reason"] == "baseline_unstable"
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0
    assert not (repo_team["root"] / "provider-log.jsonl").exists()


def test_native_pilot_gate_is_per_class(repo_team, base_source):
    """Ticket 64 (2026-10-04 ET): an unstable class is not timed; the stable class continues."""
    config = provider(repo_team, {"rewriting": [{"patch": native_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"pilot.uniform_random": 1.0, "pilot.kronecker": 1.0,
                         "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8},
                        spreads={"pilot.uniform_random": 0.14})
    _, summary = run(repo_team, native_campaign(repo_team, max_iterations=1), config, runner, FakeHost())
    assert summary["stop_reason"] != "baseline_unstable"
    assert summary["pilot"]["unstable_classes"] == ["uniform_random"] and summary["pilot"]["passed"] is False
    blocks = [c["request"]["id"] for c in runner.calls
              if c["command"] == "evaluate-pair" and ".pilot." not in c["request"]["id"]]
    assert blocks and all(".kronecker." in rid for rid in blocks)
    per_class = {r["class"]: r for r in summary["per_class"]}
    assert per_class["uniform_random"]["verdict"] == "baseline_unstable"
    assert per_class["kronecker"]["verdict"] == "gain"


def test_native_scale22_exceeds_the_native_evaluator_and_stops(repo_team):
    config = provider(repo_team, {})
    runner = FakeRunner({"pilot": 1.0})
    _, summary = run(repo_team, native_campaign(repo_team, workloads=(KRON18, UNIFORM22)), config, runner, FakeHost())
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "exceeds the native evaluator's materialization limits" in summary["stop_detail"]
    assert not [c for c in runner.calls if c["command"] == "evaluate-pair"]
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0


def test_native_scale22_runs_under_evaluator_v2_protocols(repo_team, base_source):
    """Ticket 63 (2026-10-04 ET): a campaign pinning evaluator v2 admits D4's scale-22 graphs."""
    from swdb import bfs_native_scalable as scalable
    path = native_campaign(repo_team, workloads=("bfs-20261004-kronecker22.3dc69be403db57e9",
                                            "bfs-20261004-uniform22.facb16e6260c3a82"))
    data = yaml.safe_load(path.read_text())
    data["protocol"]["evaluator"] = scalable.EVALUATOR_V2
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner, host = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14}), FakeHost()
    _, summary = run(repo_team, path, provider(repo_team, {}), runner, host)
    assert summary["stop_reason"] == "baseline_unstable"        # reached the pilot, not a setup stop
    freezes = [c["request"]["settings"] for c in runner.calls if c["command"] == "freeze-protocol"]
    template = artifacts.file_hash(scalable.DRIVER_V2)
    assert len(freezes) == 3 and all(
        f["evaluator"] == scalable.EVALUATOR_V2 and f["correctness"]["verifier"] == scalable.VERIFIER_V2
        and all(f["instrumentation"][side] == {"template_sha256": template, "treatment": "included"}
                for side in ("baseline", "candidate")) for f in freezes)
    assert host.preflights and all(p["storage_bytes"] == 2 * campaign_targets.GIB for p in host.preflights)
    assert len([c for c in runner.calls if c["command"] == "evaluate-pair"]) == 4


def test_native_ci_width_rule_and_evaluator_v3_are_frozen_into_every_role_protocol(repo_team, base_source):
    """Tickets 66/67 (2026-10-04 ET): the campaign's CI-width speed rule (circular block analysis,
    gate 0.05, no range threshold) and evaluator v3 (its own driver) reach every frozen protocol;
    an A/A interval of relative width 0.08 fails the pilot in every class."""
    from swdb import bfs_native_scalable as scalable
    from swdb.bfs_protocol import ANALYSIS_CIRCULAR_BLOCK
    path = native_campaign(repo_team, workloads=("bfs-20261004-kronecker22.3dc69be403db57e9",
                                            "bfs-20261004-uniform22.facb16e6260c3a82"))
    data = yaml.safe_load(path.read_text())
    data["protocol"].update(evaluator=scalable.EVALUATOR_V3, speed_rule="swdb.speed_rule.ci_width.v1", repetitions=20)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner, host = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.01}), FakeHost()
    _, summary = run(repo_team, path, provider(repo_team, {}), runner, host)
    assert summary["stop_reason"] == "baseline_unstable"
    assert summary["stop_detail"] == "baseline A/A CI-width gate failed in every class"
    ci = summary["pilot"]["ci_by_class_and_role"]
    assert all(row["relative_width"] == pytest.approx(0.08) and row["passed"] is False
               for roles in ci.values() for row in roles.values())
    freezes = [c["request"]["settings"] for c in runner.calls if c["command"] == "freeze-protocol"]
    template = artifacts.file_hash(scalable.DRIVER_V3)
    assert len(freezes) == 3 and all(
        f["evaluator"] == scalable.EVALUATOR_V3 and f["correctness"]["verifier"] == scalable.VERIFIER_V2
        and all(f["instrumentation"][side] == {"template_sha256": template, "treatment": "included"}
                for side in ("baseline", "candidate"))
        and f["sampling"]["analysis"] == ANALYSIS_CIRCULAR_BLOCK and f["sampling"]["block_length"] == 4
        and f["sampling"]["repetitions"] == 20
        and f["profitability"]["gate"] == {"statistic": "relative_ci_width.v1", "maximum": 0.05}
        and "maximum_relative_spread" not in f["profitability"] for f in freezes)


def test_native_ci_width_v2_reports_upstream_level_mix_and_gates_on_the_fork_only(repo_team, base_source):
    """Ticket 72 (2026-10-04 ET): under ci_width.v2 an upstream A/A failure no longer stops a class; the
    upstream blocks carry a level mix (here `unavailable`: the fake runner writes no evaluations)."""
    from swdb import bfs_native_scalable as scalable
    path = native_campaign(repo_team, workloads=("bfs-20261004-kronecker22.3dc69be403db57e9",
                                            "bfs-20261004-uniform22.facb16e6260c3a82"))
    data = yaml.safe_load(path.read_text())
    data["protocol"].update(evaluator=scalable.EVALUATOR_V3, speed_rule="swdb.speed_rule.ci_width.v2", repetitions=20)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner, host = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.01}), FakeHost()
    _, summary = run(repo_team, path, provider(repo_team, {}), runner, host)
    pilot = summary["pilot"]
    assert pilot["gating_roles"] == ["fork_scalar_tdstep"]
    mix = pilot["level_mix_by_class_and_role"]
    assert set(mix) == {"kronecker", "uniform_random"} and all(set(r) == {"upstream_do_bfs"} for r in mix.values())
    assert all(set(r["upstream_do_bfs"]) == {"baseline", "candidate"} for r in mix.values())


def test_native_workspace_names_the_protected_verifier_and_region_lines(repo_team, base_source):
    """Ticket 73 (2026-10-05 ET): a7's iteration 1 edited BFSVerifier, whose lines the full-source region
    numbers (240-243) point to in the scalar-only workspace copy. The workspace now has PROTECTED.json and
    workspace line spans, and the refusal names the protected region."""
    from swdb.campaign_targets import function_span
    verifier = function_span(base_source, "BFSVerifier")
    tdstep = function_span(base_source, "TDStep")
    assert verifier[0] <= 240 <= verifier[1] and tdstep[1] < verifier[0]
    lines = base_source.splitlines(keepends=True)
    inside = next(i for i in range(verifier[0], verifier[1]) if "return false;" in lines[i])
    edited = "".join(lines[:inside] + [lines[inside].replace("return false;", "return true;")] + lines[inside + 1:])
    config = provider(repo_team, {"rewriting": [{"patch": diff(base_source, edited), "contracts": [], "knobs": [],
                                            "unresolved": []}]})
    runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    loop, summary = run(repo_team, native_campaign(repo_team, max_iterations=1), config, runner, FakeHost())
    workspaces = sorted((loop.folder / "provider").glob("*/workspace"))
    rewriting = [w for w in workspaces if (w / "REGIONS.json").is_file()]
    assert rewriting
    protected = json.loads((rewriting[0] / "PROTECTED.json").read_text())["protected"]
    row = next(r for r in protected if r["kind"] == "verifier")
    assert row["function"] == "BFSVerifier" and row["path"] == f"source/{campaign_targets.BFS}"
    assert row["lines"][0] <= verifier[0] < row["lines"][1] <= verifier[1]     # its comment header, then the body
    regions = json.loads((rewriting[0] / "REGIONS.json").read_text())["regions"]
    assert regions[0]["workspace"] == {"path": f"source/{campaign_targets.BFS}", "function": "TDStep",
                                       "lines": list(tdstep)}
    (candidate,) = [c for it in summary["iterations"] for c in it["candidates"]][:1]
    assert candidate["level"] == "rejected" and "BFSVerifier" in candidate["rejection"]
    assert "never to be edited" in candidate["rejection"]

def test_native_blocks_refuse_while_a_gem5_campaign_holds_the_other_socket(repo_team, base_source):
    config = provider(repo_team, {})
    other = {"lease": "mbit10-evaluation-node1", "mode": "extensa", "target": "dx100_gem5",
             "campaign": "extensa-gem5-bfs-20261004-a1"}
    runner = FakeRunner({"pilot": 1.0})
    _, summary = run(repo_team, native_campaign(repo_team), config, runner, FakeHost(other=other))
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "extensa-gem5-bfs-20261004-a1" in summary["stop_detail"]
    assert not [c for c in runner.calls if c["command"] == "evaluate-pair"]


def test_approved_native_blocks_run_beside_another_campaigns_gem5_and_record_it(repo_team, base_source):
    """Ticket 64 (2026-10-04 ET): approval.gem5_other_socket admits it; the other socket is recorded."""
    other = {"lease": "mbit10-evaluation-node1", "mode": "extensa", "target": "dx100_gem5",
             "campaign": "extensa-gem5-bfs-20261004-a7"}
    path = native_campaign(repo_team)
    data = yaml.safe_load(path.read_text())
    data["approval"]["gem5_other_socket"] = True
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14})
    _, summary = run(repo_team, path, provider(repo_team, {}), runner, FakeHost(other=other))
    assert summary["stop_reason"] == "baseline_unstable"         # the pilot ran; its gate decided
    assert len([c for c in runner.calls if c["command"] == "evaluate-pair"]) == 4
    recorded = summary["pilot"]["other_socket_by_class_and_role"]
    assert recorded["kronecker"]["fork_scalar_tdstep"]["campaign"] == "extensa-gem5-bfs-20261004-a7"


def test_approved_beside_gem5_the_iteration_blocks_also_run(repo_team, base_source):
    """2026-10-04 ET (final code review): the iteration's evaluation honored only the pilot's
    approval check; an approved campaign passed its pilot and then stopped at its first block."""
    other = {"lease": "mbit10-evaluation-node1", "mode": "extensa", "target": "dx100_gem5",
             "campaign": "extensa-gem5-bfs-20261004-a7"}
    path = native_campaign(repo_team, max_iterations=1)
    data = yaml.safe_load(path.read_text())
    data["approval"]["gem5_other_socket"] = True
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    config = provider(repo_team, {"rewriting": [{"patch": native_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    _, summary = run(repo_team, path, config, runner, FakeHost(other=other))
    assert summary["pilot"]["passed"] is True
    assert summary["stop_reason"] != "infrastructure_failure", summary.get("stop_detail")
    (it,) = summary["iterations"]
    assert all(c["comparisons"] for c in it["candidates"])


def test_failed_certificate_with_nothing_named_is_not_certified(tmp_path):
    """2026-10-04 ET (final code review): an empty matrix or no negative controls make the
    certificate `failed`; the adapter must not rebuild that into `certified`."""
    def failed_without_names(store, contract, **kwargs):
        return {"id": "certification.fixture", "verdict": "failed", "matrix": [{"status": "passed"}],
                "negative_controls": []}

    adapter = campaign_targets.TargetAdapter.__new__(campaign_targets.TargetAdapter)
    adapter._certify = failed_without_names
    adapter.store_dir = adapter.folder = adapter.library_root = tmp_path
    outcome = adapter.certify({"id": "candidate.fixture"}, [CONTRACT], 1, "kronecker", 0)
    assert outcome["outcome"] == "failed" and outcome["failed_checks"] == ["certification_failed"]


class SequenceHost(FakeHost):
    """The other socket is held for the first `held` checks, then released."""

    def __init__(self, held):
        super().__init__()
        self.held, self.checks = held, 0

    def other_socket_lease(self, lane, roots):
        self.checks += 1
        if self.checks <= self.held:
            return {"lease": "mbit10-evaluation-node1", "mode": None, "target": None, "campaign": None}
        return None


@pytest.fixture
def lease_root(tmp_path, monkeypatch):
    root = tmp_path / "leases"
    root.mkdir()
    for name in ("mbit10-evaluation", "mbit10-evaluation-node0", "mbit10-evaluation-node1"):
        (root / f"{name}.lease").write_text("")
    monkeypatch.setenv("LACT_LEASE_ROOT", str(root))
    return root


def hold(root, name):
    import fcntl
    stream = (root / f"{name}.lease").open("r")
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return stream


@pytest.mark.parametrize("lane, others", [
    ("mbit10-evaluation-node1", ["mbit10-evaluation-node0", "mbit10-evaluation"]),
    ("mbit10-evaluation-node0", ["mbit10-evaluation-node1", "mbit10-evaluation"])])
def test_other_socket_leases_include_the_legacy_lease(lane, others):
    """Code review S13 (2026-10-05 ET): a held legacy lease occupies a socket (MemAcc ADR 0010)."""
    assert campaign_targets.Host.other_socket_leases(lane) == others


def test_held_legacy_lease_means_the_other_socket_is_not_free(lease_root, tmp_path):
    host = campaign_targets.Host()
    assert host.other_socket_lease("mbit10-evaluation-node1", [str(tmp_path)]) is None
    legacy = hold(lease_root, "mbit10-evaluation")
    try:
        row = host.other_socket_lease("mbit10-evaluation-node1", [str(tmp_path)])
        assert row == {"lease": "mbit10-evaluation", "mode": None, "target": None, "campaign": None}
        node0 = hold(lease_root, "mbit10-evaluation-node0")
        try:
            row = host.other_socket_lease("mbit10-evaluation-node1", [str(tmp_path)])
            assert row["lease"] == "mbit10-evaluation-node0" and row["also_held"] == ["mbit10-evaluation"]
        finally:
            node0.close()
    finally:
        legacy.close()
    # Its own lane's lease never counts as the other socket.
    own = hold(lease_root, "mbit10-evaluation-node1")
    try:
        assert host.other_socket_lease("mbit10-evaluation-node1", [str(tmp_path)]) is None
    finally:
        own.close()


def test_isolated_block_waits_while_only_the_legacy_lease_is_held(lease_root, tmp_path, monkeypatch):
    """With `isolation: other_socket_free`, a held legacy lease alone keeps a native block waiting."""
    monkeypatch.setattr(campaign_targets.NativeAdapter, "ISOLATION_WAIT_S", 0)
    adapter = campaign_targets.NativeAdapter.__new__(campaign_targets.NativeAdapter)
    adapter.campaign = {"protocol": {"isolation": "other_socket_free"}, "runs_root": str(tmp_path)}
    adapter.host, adapter._lane = campaign_targets.Host(), "mbit10-evaluation-node1"
    assert adapter.isolated()["other_socket"] == "released"
    legacy = hold(lease_root, "mbit10-evaluation")
    try:
        with pytest.raises(campaign.Stop, match="mbit10-evaluation"):
            adapter.isolated()
    finally:
        legacy.close()


def test_isolated_native_blocks_wait_for_a_free_other_socket_and_record_it(repo_team, base_source, monkeypatch):
    """Ticket 56 isolation test (2026-10-04 ET): protocol.isolation waits, then records the state."""
    monkeypatch.setattr(campaign_targets.NativeAdapter, "ISOLATION_POLL_S", 0)
    path = native_campaign(repo_team)
    data = yaml.safe_load(path.read_text())
    data["protocol"]["isolation"] = "other_socket_free"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner, host = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14}), SequenceHost(held=3)
    _, summary = run(repo_team, path, provider(repo_team, {}), runner, host)
    assert summary["stop_reason"] == "baseline_unstable"
    isolation = summary["pilot"]["isolation_by_class_and_role"]
    assert isolation["kronecker"]["fork_scalar_tdstep"]["other_socket"] == "released"
    assert all(row["other_socket_at_end"] == "released" for roles in isolation.values() for row in roles.values())
    data["approval"]["gem5_other_socket"] = True
    assert any("protocol.isolation" in p for p in campaign.campaign_problems(data))


def test_gem5_baselines_only_runs_no_provider_call_and_resume_reuses_them(repo_team, base_source):
    config = provider(repo_team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [CONTRACT],
                                            "knobs": [], "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02}), FakeHost()
    path = gem5_campaign(repo_team, max_iterations=1)
    common_args = dict(file=path, records=repo_team["records"], library=None, provider_config=config, runs_root=None,
                       fixture=None, adapter_options={"runner": runner, "host": host, "certify": fake_certify})

    def loop(**extra):
        made = campaign.Campaign(Namespace(**common_args, **extra))
        made.adapter._representation = lambda workload: {"path": f"/fixture/{workload}.sg", "sha256": "2" * 64}
        original = made.adapter.freeze_protocol

        def freeze(settings):
            result = original(settings)
            runner.protocol_settings = made.adapter.protocol["settings"]
            runner.protocol = made.adapter.protocol
            return result
        made.adapter.freeze_protocol = freeze
        return made
    prepared = loop(resume=False, baselines_only=True).run()
    assert prepared["state"] == "prepared"
    assert set(prepared["baselines"]) == {"kronecker/fork_scalar_tdstep", "uniform_random/fork_scalar_tdstep"}
    assert not (repo_team["root"] / "provider-log.jsonl").exists()
    assert len([c for c in runner.calls if c["command"] == "dx100-execute"]) == 2
    resumed = loop(resume=True)
    resumed.adapter.protocol = runner.protocol          # the fixture freeze kept no protocol record
    summary = resumed.run()
    baselines = [c for c in runner.calls if c["command"] == "dx100-execute"
                 and c["request"]["protocol_role"] == "baseline"]
    assert len(baselines) == 2 and summary["stop_reason"] == "max_iterations"
    assert summary["iterations"][0]["candidates"][0]["id"].startswith("extensa-gem5-bfs-20261004-f1.it1.")


# 2026-10-08 ET: certification infrastructure failures preserve interrupted rows, not plateau.
@pytest.mark.parametrize("failure", ["compiler", "trusted_build", "configuration", "trusted_io"])
def test_certification_infrastructure_stops_without_repair_or_plateau(repo_team, base_source, monkeypatch, failure):
    from swdb import certification, certification_process
    from swdb.cli import UsageError

    def broken_certificate(store, contract, **kwargs):
        if failure == "compiler":
            monkeypatch.setenv("SWDB_CERTIFY_CXX", str(repo_team["root"] / "missing-certification-compiler"))
            certification.compiler()
        elif failure == "trusted_build":
            # Exercise the trusted evaluator helper without compiling anything.
            build = certification_process.Build.__new__(certification_process.Build)
            build._evaluator = None
            build.library = build.folder = Path("/fixture")
            build.flags = []
            build.compile = lambda *a, **kw: {"returncode": 1, "log": "/fixture/trusted-build.json"}
            build.evaluator()
        elif failure == "trusted_io":
            raise FileNotFoundError("trusted certification driver is unavailable: fixture")
        else:
            raise UsageError("typed library is invalid: fixture")
        raise AssertionError("infrastructure helper must refuse")

    monkeypatch.setattr("testkit.extensa_targets.fake_certify", broken_certificate)
    config = provider(repo_team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [CONTRACT],
                                             "knobs": [], "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4}), FakeHost()
    loop, summary = run(repo_team, gem5_campaign(repo_team, max_iterations=1), config, runner, host)
    assert summary["stop_reason"] == "infrastructure_failure"
    assert summary["iterations"] == []
    ledger = loop.ledger.to_state()
    assert ledger["iterations_completed"] == 0 and ledger["plateau"] == 0
    interrupted = loop.state["interrupted_iteration"]
    assert interrupted["index"] == 1 and interrupted["provider_calls"]
    assert all(call["role"] != "repair" for call in ledger["calls"])
    assert not [call for call in runner.calls if call["command"] == "dx100-execute"]


@pytest.mark.parametrize("kind,check", [("scope", "certification_aborted"),
                                        ("harness", "harness_scan"),
                                        ("site", "negative_control_site:stale_depth_hint")])
def test_expected_candidate_certificate_refusals_remain_failed_candidates(tmp_path, kind, check):
    from swdb import certification_common as common
    from swdb.cli import Failure, UsageError

    def refused(store, contract, **kwargs):
        if kind == "site":
            raise common.CandidateFailure("candidate source lacks a unique negative-control mutation site: "
                                          "stale_depth_hint", check=check)
        raise common.CandidateUsageError("fixture authored-source refusal", check=check)

    adapter = campaign_targets.TargetAdapter.__new__(campaign_targets.TargetAdapter)
    adapter._certify = refused
    adapter.store_dir = adapter.folder = adapter.library_root = tmp_path
    outcome = adapter.certify({"id": "candidate.fixture"}, [CONTRACT], 1, "kronecker", 0)
    assert outcome == {"record": None, "outcome": "failed", "failed_checks": [check]}
    assert issubclass(common.CandidateFailure, Failure)
    assert issubclass(common.CandidateUsageError, UsageError)


def test_authored_source_refusals_keep_check_names_and_cli_categories():
    from swdb import certification_common as common, certification_faults, certification_isolation, certification_legality
    from swdb.cli import Failure, UsageError

    with pytest.raises(common.CandidateFailure) as site:
        certification_faults.replace_tokens("void f() {}", "missing();", "changed();", "stale_depth_hint")
    assert site.value.check == "negative_control_site:stale_depth_hint"
    with pytest.raises(common.CandidateUsageError) as harness:
        certification_isolation.refuse_scan_findings("", "void f() { swdb_certification_frontier(); }")
    assert harness.value.check == "harness_scan"
    with pytest.raises(common.CandidateFailure) as schedule:
        certification_legality.schedule_control("void f() {}")
    assert schedule.value.check == "negative_control_site:schedule_out_of_range"
    # A missing normative knob declaration is configuration, despite its legacy site message.
    with pytest.raises(Failure) as configuration:
        certification_legality.knob_control("void f() {}", {})
    assert not isinstance(configuration.value, common.CandidateRefusal)
    with pytest.raises(common.CandidateUsageError):
        common.candidate_check(lambda: (_ for _ in ()).throw(UsageError("authored scope mismatch")))
    # CLI categories remain unchanged for each candidate refusal subtype.
    assert isinstance(site.value, Failure) and isinstance(harness.value, UsageError)


@pytest.mark.parametrize("version", ["1.4", "1.5"])
@pytest.mark.parametrize("source", ["bool BFSVerifier() {}", "ANCHOR\nbool BFSVerifier() {}\nANCHOR",
                                   "ANCHOR", "ANCHOR\nbool BFSVerifier() {}\nbool BFSVerifier() {}"])
def test_native_authored_frontier_refusals_are_candidate_failures(tmp_path, monkeypatch, version, source):
    from swdb import certification, certification_common as common, certification_native as native
    from swdb import certification_procedures as procedures

    # Reach the actual authored-source guard without graph generation or a compiler/build.
    monkeypatch.setattr(certification, "matrix_graphs", lambda *a: [])
    monkeypatch.setattr(native, "staging_tail_graph", lambda *a: None)
    (tmp_path / "bfs.cc").write_text(source)
    profile = {"data": {"matrix": {"sources": [0], "threads": [1]},
                        "rewrite_scope": {"file": "bfs.cc"}}, "harness_v14": {},
               "hook": {"anchor": "ANCHOR", "hook_v14": "HOOK"}}
    with pytest.raises(common.CandidateFailure) as refused:
        native.certify_native_v14(tmp_path, tmp_path, tmp_path, profile, None,
                                  procedure=procedures.procedure(procedures.NATIVE, version))
    assert refused.value.check == "certification_aborted"


@pytest.mark.parametrize("phase", ["positive", "trusted_control"])
def test_blinded_instrumentation_distinguishes_authored_and_trusted_control_failures(tmp_path, monkeypatch, phase):
    from types import SimpleNamespace
    from swdb import certification, certification_blinding as blinding, certification_common as common
    from swdb import certification_legality as legality
    from swdb.cli import Failure

    (tmp_path / "candidate.cc").write_text("positive")
    driver = tmp_path / "driver.cc"
    driver.write_text("trusted driver")
    calls = []

    def instrument(text, **kwargs):
        calls.append(text)
        if text == "trusted_bad" or phase == "positive":
            raise Failure("instrumentation lacks protected anchor: fixture")
        return "instrumented positive"

    class Build:
        def __init__(self, *args, **kwargs):
            pass

        def candidate_object(self, *args, **kwargs):
            return {"returncode": 0}

        def link(self, *args, **kwargs):
            return {"returncode": 0}

    monkeypatch.setattr(certification, "matrix_graphs", lambda *a: [("tiny", tmp_path / "tiny.sg")])
    monkeypatch.setattr(certification, "legality_checks", lambda *a, **kw: [])
    monkeypatch.setattr(legality, "applies", lambda *a: True)
    monkeypatch.setattr(legality, "CONTROLS", {"trusted_bad_control": set()})
    monkeypatch.setattr(legality, "control", lambda *a, **kw: {
        "source": "trusted_bad", "fault": None, "site": "candidate_tokens"})
    plugin = SimpleNamespace(certification_source="candidate.cc", binary_stem="fixture",
                             certification_instrument=instrument, certification_controls={},
                             control_source=lambda sources: sources[0])
    procedure = SimpleNamespace(legality="v1", driver_path=lambda *a, **kw: driver)
    with pytest.raises(Failure) as refused:
        blinding.certify_candidate(tmp_path, tmp_path, tmp_path, [1], 1, [0], plugin=plugin,
                                   contract={"fixture": True}, procedure=procedure, build_class=Build)
    assert isinstance(refused.value, common.CandidateRefusal) is (phase == "positive")
    assert calls == (["positive"] if phase == "positive" else ["positive", "trusted_bad"])

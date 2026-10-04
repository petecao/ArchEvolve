"""Real campaign target adapters (tickets 56 and 57) on fixture runners.

Created: 2026-10-04 ET. The adapters' evaluator commands are replaced by a fixture runner
(every number comes from the test, labeled here, never evidence); the campaign loop, the
candidate-artifact path (patch, knobs, canonical header), the session-begin check, the
per-role native protocols and paired blocks, the single gem5 baseline per class and the
dispatch preflight memory admission run for real.
"""

import copy
import difflib
import json
import shutil
from argparse import Namespace
from pathlib import Path

import pytest
import yaml

from conftest import REPO
from swdb import artifacts, campaign, campaign_targets, certification
from swdb.store import Store
from test_extensa_campaign import knob_rows, provider

CONTRACT = "contract.bfs_read_offload"
GIB = 1024 ** 3
KRON18_S0 = "bfs-20260928-kronecker18-s0.cf4283236c5cb50c"
UNIFORM18_S0 = "bfs-20260928-uniform18-s0.8c7e69dfa516e53c"
KRON18 = "bfs-20260925-kronecker18.48de8267ac2098d5"
UNIFORM18 = "bfs-20260925-uniform18.cd2169a5c421baf7"
UNIFORM22 = "bfs-20260925-uniform22.f23b09bb0c0601b5"
FORK = "bfs-native-pilot-20260925-dx10018-a1.baseline"
UPSTREAM = "bfs-native-pilot-20260925-upstream18-a2.baseline"
GEM5_BASELINE = "typed-library-bfs-gem5-20261003-a2.baseline"


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

@pytest.fixture(scope="module")
def base_source(tmp_path_factory):
    folder = tmp_path_factory.mktemp("base")
    tree, _ = certification.materialize_snapshot(Store(REPO / "records"), campaign_targets.SNAPSHOT, folder)
    return (tree / campaign_targets.BFS).read_text()


@pytest.fixture(scope="module")
def team_template(tmp_path_factory):
    root = tmp_path_factory.mktemp("team")
    shutil.copytree(REPO / "records", root / "records")
    return root / "records"


@pytest.fixture
def team(team_template, tmp_path):
    shutil.copytree(team_template, tmp_path / "records")
    return {"records": tmp_path / "records", "root": tmp_path}


def diff(before, after):
    path = campaign_targets.BFS
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile="a/" + path, tofile="b/" + path))


def inside_patch(base):
    return diff(base, base.replace("    init_MAA();\n    t.Start();",
                                   "    init_MAA();\n    __dxc_session_begin();\n    t.Start();", 1))


def outside_patch(base):
    return diff(base, "static int swdb_early = (__dxc_session_begin(), 0);\n" + base)


def native_patch(base):
    return diff(base, base + "// campaign fixture edit\n")


class FakeHost:
    def __init__(self, other=None):
        self.preflights, self.other = [], other

    def lane(self):
        return "mbit10-evaluation-node0"

    def other_socket_lease(self, lane, roots):
        return self.other

    def mark(self, *args):
        pass

    def unmark(self, *args):
        pass

    def preflight(self, runs_dir, lane, *, storage_bytes, memory_bytes):
        self.preflights.append({"lane": lane, "storage_bytes": storage_bytes, "memory_bytes": memory_bytes})
        return {"state": "admitted"}


class FakeRunner:
    """Answers each public evaluator command; numbers are fixture values, not evidence."""

    def __init__(self, ratios, spreads=None):
        self.calls, self.ratios, self.spreads = [], ratios, spreads or {}

    def __call__(self, command, request=None, *, stage, extra=(), timeout=600):
        self.calls.append({"command": command, "stage": stage, "request": copy.deepcopy(request)})
        rid = request["id"]
        if command == "freeze-protocol":
            return 0, {"kind": "protocol", "id": rid + ".0123456789abcdef", "identity_sha256": "0" * 64,
                       "settings": request["settings"]}
        if command == "dx100-compile":
            role = "candidate" if request["accelerated"] else "baseline"
            build = copy.deepcopy(self.protocol_settings["builds"][role])
            if request["parent_gather_diagnostic"]:
                build["flags"] = build["flags"] + ["-DSWDB_DXC_DIAGNOSTIC"]
            build.update(binary="/fixture/bfs", binary_sha256="1" * 64)
            return 0, {"id": rid, "outcome": {"state": "complete"}, "build": build}
        if command == "dx100-execute":
            check = {"passed": True, "coverage": {c: {"state": "observed"}
                                                  for c in ("read_only_executed", "full_tiles", "tail_tiles")}}
            if request.get("protocol_companion"):
                check["parent_gather_race"] = {"outcome": "observed"}
            return 0, {"id": rid, "outcome": {"state": "complete"}, "correctness": {"state": "passed", "checks": [check]}}
        if command == "aggregate-evaluations":
            return 0, {"id": rid, "outcome": {"state": "complete"}}
        if command == "evaluate-pair":
            return 0, {"id": rid, "outcome": {"state": "complete"}}
        if command == "compare-evaluations":
            key = next(k for k in self.ratios if k in rid)
            ratio = self.ratios[key]
            spread = self.spreads.get(key, 0.03)
            return 0, {"id": rid, "decision": {"state": "fixture_comparison"},
                       "metrics": {"roi_speedup": ratio,
                                   "confidence_interval": {"lower": ratio - 0.04, "upper": ratio + 0.04},
                                   "relative_spread": {"baseline": {"0": spread}, "candidate": {"0": spread / 2}}}}
        raise AssertionError(command)


def fake_certify(store, contract, **kw):
    return {"id": "certification.fixture." + kw["candidate"], "verdict": "certified", "matrix": [],
            "negative_controls": []}


def write_campaign(team, data):
    folder = team["root"] / "campaigns" / "extensa"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{data['id']}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def common(team, cid, target):
    return {"format": "swdb.extensa-campaign.v1", "id": cid, "created": "2026-10-04 09:00 ET", "mode": "extensa",
            "kernel": "gapbs-bfs", "target": target, "machine": "mbit10", "base_source": "fork_scalar_tdstep",
            "label": "single graph per class", "regions": ["dx100-bfs-scalar/TDStep:240-243"],
            "provider": {"name": "codex", "model": "gpt-5.6-sol", "effort": "xhigh"},
            "budgets": {"max_iterations": 2, "plateau_iterations": 4, "lane_hours": 24,
                        "provider_calls_per_iteration": 3, "provider_calls_setup": 1, "disk_gb": 20, "lanes": 1},
            "runs_root": str(team["root"] / "runs"),
            "approval": {"by": "Yan-Ru Jhou", "date": "2026-10-03", "scope": "fixture"}}


def run(team, path, config, runner, host):
    args = Namespace(file=path, records=team["records"], library=None, provider_config=config,
                     runs_root=None, fixture=None, resume=False,
                     adapter_options={"runner": runner, "host": host, "certify": fake_certify})
    loop = campaign.Campaign(args)
    if isinstance(loop.adapter, campaign_targets.Gem5Adapter):
        original = loop.adapter.freeze_protocol

        def freeze(settings):
            result = original(settings)
            runner.protocol_settings = loop.adapter.protocol["settings"]
            return result
        loop.adapter.freeze_protocol = freeze
        loop.adapter._representation = lambda workload: {"path": f"/fixture/{workload}.sg", "sha256": "2" * 64}
    return loop, loop.run()


# --- gem5 (ticket 57) --------------------------------------------------------------------------

def gem5_campaign(team, **budgets):
    data = common(team, "extensa-gem5-bfs-20261004-f1", "dx100_gem5")
    data.update(baselines=[{"role": "fork_scalar_tdstep", "candidate": GEM5_BASELINE}],
                protocol={"roi": "bfs.complete_call.v1", "threads": 4, "repetitions": 1, "sources": [0],
                          "region_pairs": False, "differences": "Extensa gem5 fixture campaign."},
                workload_classes=[{"class": "kronecker", "workload": KRON18_S0},
                                  {"class": "uniform_random", "workload": UNIFORM18_S0}],
                library={"allowed_tiers": ["shared", "experimental"], "contracts": [CONTRACT]})
    data["budgets"].update(budgets)
    return write_campaign(team, data)


def test_gem5_one_baseline_per_class_point_ratios_and_memory_admission(team, base_source):
    patch = inside_patch(base_source)
    config = provider(team, {"rewriting": [{"patch": patch, "contracts": [CONTRACT],
                                            "knobs": knob_rows({"kronecker": {"frontier_threshold": 32}}), "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02}), FakeHost()
    loop, summary = run(team, gem5_campaign(team), config, runner, host)
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


def test_gem5_session_begin_outside_is_refused_before_any_job(team, base_source):
    config = provider(team, {"rewriting": [{"patch": outside_patch(base_source), "contracts": [CONTRACT],
                                            "knobs": [], "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4}), FakeHost()
    _, summary = run(team, gem5_campaign(team, max_iterations=1), config, runner, host)
    rows = summary["iterations"][0]["candidates"]
    assert {r["level"] for r in rows} == {"rejected"}
    assert all("outside the timed DOBFS call" in r["rejection"] for r in rows)
    assert not [c for c in runner.calls if c["command"] in {"dx100-compile", "dx100-execute"}]
    assert summary["iterations"][0]["feedback_reasons"] == ["correctness_failed"]
    assert {r["verdict"] for r in summary["per_class"]} == {"no_gain"}


def test_gem5_edit_without_contract_is_refused(team, base_source):
    config = provider(team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4})
    _, summary = run(team, gem5_campaign(team, max_iterations=1), config, runner, FakeHost())
    assert {r["level"] for r in summary["iterations"][0]["candidates"]} == {"rejected"}
    assert not [c for c in runner.calls if c["command"] == "dx100-execute"]


# --- native CPU (ticket 56) ----------------------------------------------------------------------

def native_campaign(team, workloads=(KRON18, UNIFORM18), **budgets):
    data = common(team, "extensa-native-bfs-20261004-f1", "native_cpu")
    data.update(baselines=[{"role": "fork_scalar_tdstep", "candidate": FORK},
                           {"role": "upstream_do_bfs", "candidate": UPSTREAM}],
                protocol={"roi": "bfs.complete_call.v1", "threads": 1, "repetitions": 10,
                          "sources": [0, 1234, 7777], "region_pairs": False,
                          "differences": "Extensa native fixture campaign."},
                workload_classes=[{"class": "kronecker", "workload": workloads[0]},
                                  {"class": "uniform_random", "workload": workloads[1]}],
                library={"allowed_tiers": ["shared", "experimental"], "contracts": []})
    data["budgets"].update(budgets)
    return write_campaign(team, data)


def test_native_paired_blocks_against_both_baselines_select_on_fork(team, base_source):
    config = provider(team, {"rewriting": [{"patch": native_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    _, summary = run(team, native_campaign(team, max_iterations=1), config, runner, FakeHost())
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


def test_native_pilot_spread_stops_without_provider_call(team, base_source):
    config = provider(team, {})
    runner = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14})
    _, summary = run(team, native_campaign(team), config, runner, FakeHost())
    assert summary["stop_reason"] == "baseline_unstable"
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0
    assert not (team["root"] / "provider-log.jsonl").exists()


def test_native_pilot_gate_is_per_class(team, base_source):
    """Ticket 64 (2026-10-04 ET): an unstable class is not timed; the stable class continues."""
    config = provider(team, {"rewriting": [{"patch": native_patch(base_source), "contracts": [],
                                            "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"pilot.uniform_random": 1.0, "pilot.kronecker": 1.0,
                         "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8},
                        spreads={"pilot.uniform_random": 0.14})
    _, summary = run(team, native_campaign(team, max_iterations=1), config, runner, FakeHost())
    assert summary["stop_reason"] != "baseline_unstable"
    assert summary["pilot"]["unstable_classes"] == ["uniform_random"] and summary["pilot"]["passed"] is False
    blocks = [c["request"]["id"] for c in runner.calls
              if c["command"] == "evaluate-pair" and ".pilot." not in c["request"]["id"]]
    assert blocks and all(".kronecker." in rid for rid in blocks)
    per_class = {r["class"]: r for r in summary["per_class"]}
    assert per_class["uniform_random"]["verdict"] == "baseline_unstable"
    assert per_class["kronecker"]["verdict"] == "gain"


def test_native_scale22_exceeds_the_native_evaluator_and_stops(team):
    config = provider(team, {})
    runner = FakeRunner({"pilot": 1.0})
    _, summary = run(team, native_campaign(team, workloads=(KRON18, UNIFORM22)), config, runner, FakeHost())
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "exceeds the native evaluator's materialization limits" in summary["stop_detail"]
    assert not [c for c in runner.calls if c["command"] == "evaluate-pair"]
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0


def test_native_scale22_runs_under_evaluator_v2_protocols(team, base_source):
    """Ticket 63 (2026-10-04 ET): a campaign pinning evaluator v2 admits D4's scale-22 graphs."""
    from swdb import bfs_native_scalable as scalable
    path = native_campaign(team, workloads=("bfs-20261004-kronecker22.3dc69be403db57e9",
                                            "bfs-20261004-uniform22.facb16e6260c3a82"))
    data = yaml.safe_load(path.read_text())
    data["protocol"]["evaluator"] = scalable.EVALUATOR_V2
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    runner, host = FakeRunner({"pilot": 1.0}, spreads={"pilot": 0.14}), FakeHost()
    _, summary = run(team, path, provider(team, {}), runner, host)
    assert summary["stop_reason"] == "baseline_unstable"        # reached the pilot, not a setup stop
    freezes = [c["request"]["settings"] for c in runner.calls if c["command"] == "freeze-protocol"]
    template = artifacts.file_hash(scalable.DRIVER_V2)
    assert len(freezes) == 3 and all(
        f["evaluator"] == scalable.EVALUATOR_V2 and f["correctness"]["verifier"] == scalable.VERIFIER_V2
        and all(f["instrumentation"][side] == {"template_sha256": template, "treatment": "included"}
                for side in ("baseline", "candidate")) for f in freezes)
    assert host.preflights and all(p["storage_bytes"] == 2 * campaign_targets.GIB for p in host.preflights)
    assert len([c for c in runner.calls if c["command"] == "evaluate-pair"]) == 4


def test_native_blocks_refuse_while_a_gem5_campaign_holds_the_other_socket(team, base_source):
    config = provider(team, {})
    other = {"lease": "mbit10-evaluation-node1", "mode": "extensa", "target": "dx100_gem5",
             "campaign": "extensa-gem5-bfs-20261004-a1"}
    runner = FakeRunner({"pilot": 1.0})
    _, summary = run(team, native_campaign(team), config, runner, FakeHost(other=other))
    assert summary["stop_reason"] == "infrastructure_failure"
    assert "extensa-gem5-bfs-20261004-a1" in summary["stop_detail"]
    assert not [c for c in runner.calls if c["command"] == "evaluate-pair"]


def test_gem5_baselines_only_runs_no_provider_call_and_resume_reuses_them(team, base_source):
    config = provider(team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [CONTRACT],
                                            "knobs": [], "unresolved": []}]})
    runner, host = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02}), FakeHost()
    path = gem5_campaign(team, max_iterations=1)
    common_args = dict(file=path, records=team["records"], library=None, provider_config=config, runs_root=None,
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
    assert not (team["root"] / "provider-log.jsonl").exists()
    assert len([c for c in runner.calls if c["command"] == "dx100-execute"]) == 2
    resumed = loop(resume=True)
    resumed.adapter.protocol = runner.protocol          # the fixture freeze kept no protocol record
    summary = resumed.run()
    baselines = [c for c in runner.calls if c["command"] == "dx100-execute"
                 and c["request"]["protocol_role"] == "baseline"]
    assert len(baselines) == 2 and summary["stop_reason"] == "max_iterations"
    assert summary["iterations"][0]["candidates"][0]["id"].startswith("extensa-gem5-bfs-20261004-f1.it1.")

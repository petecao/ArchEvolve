"""Real Extensa target adapters on fixture runners: a copy of the repository records
(`repo_team`, renamed from `team`), fake host and runner, campaign writers. Created
2026-10-05 ET (code review T1), from tests/test_extensa_targets.py."""

import copy
import difflib
import shutil
from argparse import Namespace

import pytest
import yaml

from conftest import REPO
from swdb import campaign, campaign_targets, certification
from swdb.store import Store

CONTRACT = "contract.bfs_read_offload"
KRON18_S0 = "bfs-20260928-kronecker18-s0.cf4283236c5cb50c"
UNIFORM18_S0 = "bfs-20260928-uniform18-s0.8c7e69dfa516e53c"
GEM5_BASELINE = "typed-library-bfs-gem5-20261003-a2.baseline"


@pytest.fixture(scope="module")
def base_source(tmp_path_factory):
    folder = tmp_path_factory.mktemp("base")
    tree, _ = certification.materialize_snapshot(Store(REPO / "records"), campaign_targets.SNAPSHOT, folder)
    return (tree / campaign_targets.BFS).read_text()


@pytest.fixture(scope="module")
def repo_team_template(tmp_path_factory):
    root = tmp_path_factory.mktemp("team")
    shutil.copytree(REPO / "records", root / "records")
    return root / "records"


@pytest.fixture
def repo_team(repo_team_template, tmp_path):
    shutil.copytree(repo_team_template, tmp_path / "records")
    return {"records": tmp_path / "records", "root": tmp_path}


def diff(before, after):
    path = campaign_targets.BFS
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile="a/" + path, tofile="b/" + path))


def inside_patch(base):
    return diff(base, base.replace("    init_MAA();\n    t.Start();",
                                   "    init_MAA();\n    __dxc_session_begin();\n    t.Start();", 1))


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

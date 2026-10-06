"""Extensa campaign fixtures: a seeded team store, campaign and fixture files, and the fixture
provider. Created 2026-10-05 ET (code review T1/T2), moved from tests/test_extensa_campaign.py.

Every provider here is an external_fixture; every number comes from the fixture file and is
labeled contract_fixture, never evidence. `campaign_team` (renamed from `team`) is the seeded
team store; `testkit.extensa_targets.repo_team` is the other, a copy of the repository records.
"""

import json
import shutil
import sys

import pytest
import yaml

from conftest import REPO, run_swdb
from testkit.bfs_protocol import _command, _payload, _workload_request

CID = "extensa-native-bfs-20261004-a1"
GEM5 = "extensa-gem5-bfs-20261004-a1"
CONTRACT = "contract.bfs_read_offload"
PATCH = "--- a/bfs.cc\n+++ b/bfs.cc\n@@ -1 +1 @@\n-int alpha = 15;\n+int alpha = 14;\n"
GIB = 1024 ** 3
#: The plan-item key the fixture provider reads as a replay directive (see `replay`).
REPLAY = "__swdb_replay__"


@pytest.fixture(scope="module")
def campaign_team_seed(protocol_seed, tmp_path_factory):
    """One seeded team store per module: the protocol seed plus a uniform-random workload class."""
    seed, workload, protocol, _request, evaluations, comparison = protocol_seed
    root = tmp_path_factory.mktemp("campaign-team")
    records = root / "records"
    shutil.copytree(seed.path, records)

    class R:
        path = records

        def swdb(self, command, *args, env=None):
            return run_swdb(command, "--records", records, *args, env=env)

        def copy_repo(self, *kinds):
            for folder in kinds:
                shutil.copytree(REPO / "records" / folder, records / folder, dirs_exist_ok=True)
    team = R()
    request = _workload_request(team, root, {"num_vertices": 5, "directed": True,
                                             "edges": [[0, 1], [0, 2], [1, 3], [2, 3]]}, name="uniform-graph")
    request["family"] = "uniform_random"
    uniform = _command(team, "register-workload", _payload(root, "uniform", request))
    compared = _command(team, "compare-evaluations", _payload(root, "compare", comparison))
    return {"records": records, "kronecker": workload["id"], "uniform": uniform["id"], "protocol": protocol["id"],
            "evaluation": evaluations["candidate"]["id"], "candidate": "test-proposal.candidate-1",
            "comparison": compared["id"], "baseline": evaluations["baseline"]["candidate"],
            "machine": "native-testhost"}


@pytest.fixture
def campaign_team(campaign_team_seed, tmp_path):
    """A fresh copy of the seeded team store for one test, with its own root folder."""
    records = tmp_path / "records"
    shutil.copytree(campaign_team_seed["records"], records)
    return {**campaign_team_seed, "records": records, "root": tmp_path}


def campaign_file(team, *, cid=CID, target="native_cpu", **changes):
    data = {"format": "swdb.extensa-campaign.v1", "id": cid, "created": "2026-10-04 09:00 ET", "mode": "extensa",
            "kernel": "gapbs-bfs", "target": target, "machine": team["machine"], "base_source": "fork_scalar_tdstep",
            "baselines": [{"role": "fork_scalar_tdstep", "candidate": team["baseline"]},
                          {"role": "upstream_do_bfs", "candidate": team["candidate"]}],
            "protocol": {"roi": "bfs.complete_call.v1", "threads": 1, "repetitions": 10, "sources": [0, 1234, 7777],
                         "region_pairs": False, "differences": "Extensa campaign fixture: rewrites of TDStep."},
            "workload_classes": [{"class": "kronecker", "workload": team["kronecker"]},
                                 {"class": "uniform_random", "workload": team["uniform"]}],
            "label": "single graph per class",
            "library": {"allowed_tiers": ["shared", "experimental"], "contracts": [CONTRACT]},
            "regions": ["tdstep"], "provider": {"name": "codex", "model": "gpt-5.6-sol", "effort": "xhigh"},
            "budgets": {"max_iterations": 1, "plateau_iterations": 4, "lane_hours": 24,
                        "provider_calls_per_iteration": 3, "provider_calls_setup": 1, "disk_gb": 20, "lanes": 1},
            "runs_root": str(team["root"] / "runs")}
    if target == "dx100_gem5":
        data["baselines"] = data["baselines"][:1]
        data["protocol"].update(repetitions=1, sources=[0])
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key] = {**data[key], **value}
        else:
            data[key] = value
    folder = team["root"] / "campaigns" / "extensa"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{cid}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def comparison(ratio, lower=None, spread=0.05):
    return {"ratio": ratio, "lower": ratio - 0.01 if lower is None else lower, "upper": ratio + 0.01, "spread": spread}


def fixture_file(team, *, iterations=None, **changes):
    row = {cls: {"comparisons": {"fork_scalar_tdstep": comparison(1.2), "upstream_do_bfs": comparison(0.9)}}
           for cls in ("kronecker", "uniform_random")}
    data = {"format": "swdb.extensa-campaign-fixture.v1",
            "templates": {"protocol": team["protocol"], "candidate": team["candidate"],
                          "evaluation": team["evaluation"], "comparison": team["comparison"]},
            "source_files": {"bfs.cc": "int alpha = 15;\n"},
            "pilot": {cls: {"fork_scalar_tdstep": 0.04, "upstream_do_bfs": 0.05} for cls in ("kronecker", "uniform_random")},
            "iterations": iterations or [row], "run_bytes": 2048,
            "preflight": {"disk": "/data1", "free_bytes": 400 * GIB, "free_memory_bytes": 64 * GIB}}
    data.update(changes)
    path = team["root"] / "fixture.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def knob_rows(knobs):
    """The rewrite role's knob rows (2026-10-04 ET) from {class: {name: value}}."""
    return [{"class": cls, "name": name, "value": value}
            for cls, values in (knobs or {}).items() for name, value in values.items()]


def rewrite(contracts=(CONTRACT,), knobs=None, patch=PATCH):
    return {"patch": patch, "contracts": list(contracts), "knobs": knob_rows(knobs), "unresolved": []}


def replay(*, stdout=None, stderr="", exit_code=1, call_files=None):
    """A plan item that makes the fixture provider replay retained output (T2, 2026-10-05 ET).

    The provider prints the bytes of `stdout` (a file) and the text `stderr`, copies each
    `call_files` source into the provider-call folder (its workspace's parent, where the guard
    observer writes its receipts on mbit10), and exits with `exit_code`. This replaces patching
    the provider program's text."""
    return {REPLAY: {"stdout": str(stdout) if stdout else None, "stderr": stderr, "exit": exit_code,
                     "call_files": {name: str(source) for name, source in (call_files or {}).items()}}}


def provider(team, plan):
    """A fixture provider that answers by role, in order, and logs the files it sees.

    A plan item is the JSON answer, `"usage_limit"` or `"login"` (the provider fails with that
    message), or a `replay(...)` directive."""
    plan = {"rewriting": [rewrite()], "repair": [rewrite()], "profiling": [{"notes": ["fixture"]}],
            "testgen": [{"tests": [{"path": "inputs.json", "content": "{}"}], "unresolved": []}], **plan}
    (team["root"] / "plan.json").write_text(json.dumps(plan))
    program = team["root"] / "provider.py"
    program.write_text(f"""import json, shutil, sys
from pathlib import Path
plan =json.loads(Path({str(team['root'] / 'plan.json')!r}).read_text())
state = Path({str(team['root'] / 'provider-state.json')!r})
counts = json.loads(state.read_text()) if state.exists() else {{}}
role = ('repair' if Path('CERTIFICATION.json').exists() else 'rewriting' if Path('REGIONS.json').exists()
        else 'synthesis' if Path('TARGET.json').exists() else 'profiling' if Path('source').exists() else 'testgen')
i = counts.get(role, 0); counts[role] = i + 1; state.write_text(json.dumps(counts))
with open({str(team['root'] / 'provider-log.jsonl')!r}, 'a') as log:
    log.write(json.dumps({{'role': role, 'files': sorted(str(p) for p in Path('.').rglob('*') if p.is_file())}}) + '\\n')
items = plan[role]; item = items[min(i, len(items) - 1)]
if isinstance(item, dict) and {REPLAY!r} in item:
    directive = item[{REPLAY!r}]
    for name, source in directive['call_files'].items():
        shutil.copyfile(source, Path('..') / name)
    if directive['stdout']:
        sys.stdout.write(Path(directive['stdout']).read_text())
    sys.stderr.write(directive['stderr'])
    sys.exit(directive['exit'])
if item == 'usage_limit':
    sys.stderr.write('Error: usage limit reached for this account'); sys.exit(1)
if item == 'login':
    sys.stderr.write('Error: not logged in'); sys.exit(1)
print(json.dumps(item))
""")
    config = team["root"] / "provider.yaml"
    config.write_text(yaml.safe_dump({"kind": "external_fixture", "command": [sys.executable, str(program)],
                                      "timeout_s": 60, "total_seconds": 600}))
    return config


def run(team, path, fixture, config, *extra, expect=0, env=None):
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", config,
                      "--fixture", fixture, "--format", "json", *extra, env=env)
    assert result.returncode == expect, result.stderr + result.stdout
    return json.loads(result.stdout) if result.stdout.strip() else None


def campaign_store(team, cid=CID):
    return team["root"] / "runs" / "extensa" / cid / "records"


def records_of(folder, kind):
    return [yaml.safe_load(p.read_text()) for p in sorted((folder / kind).glob("*.yaml"))] if (folder / kind).is_dir() else []


def log(team):
    path = team["root"] / "provider-log.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

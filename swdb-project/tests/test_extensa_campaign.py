"""Extensa campaigns on contract fixtures: skeleton, speed rule, selection, budgets.

Created: 2026-10-03 ET (tickets 52-54). Every provider is an external_fixture; every
number comes from the fixture file and is labeled contract_fixture, never evidence.
"""

import copy
import json
import shutil
import sys

import pytest
import yaml

from conftest import REPO, run_swdb
from test_bfs_protocol import _command, _payload, _workload_request, protocol_seed  # noqa: F401

CID = "extensa-native-bfs-20261004-a1"
GEM5 = "extensa-gem5-bfs-20261004-a1"
CONTRACT = "contract.bfs_read_offload"
PATCH = "--- a/bfs.cc\n+++ b/bfs.cc\n@@ -1 +1 @@\n-int alpha = 15;\n+int alpha = 14;\n"
GIB = 1024 ** 3


@pytest.fixture(scope="module")
def team_seed(protocol_seed, tmp_path_factory):
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
def team(team_seed, tmp_path):
    records = tmp_path / "records"
    shutil.copytree(team_seed["records"], records)
    return {**team_seed, "records": records, "root": tmp_path}


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


def provider(team, plan):
    """A fixture provider that answers by role, in order, and logs the files it sees."""
    plan = {"rewriting": [rewrite()], "repair": [rewrite()], "profiling": [{"notes": ["fixture"]}],
            "testgen": [{"tests": [{"path": "inputs.json", "content": "{}"}], "unresolved": []}], **plan}
    (team["root"] / "plan.json").write_text(json.dumps(plan))
    program = team["root"] / "provider.py"
    program.write_text(f"""import json, sys
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


def run(team, path, fixture, config, *extra, expect=0):
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", config,
                      "--fixture", fixture, "--format", "json", *extra)
    assert result.returncode == expect, result.stderr + result.stdout
    return json.loads(result.stdout) if result.stdout.strip() else None


def campaign_store(team, cid=CID):
    return team["root"] / "runs" / "extensa" / cid / "records"


def records_of(folder, kind):
    return [yaml.safe_load(p.read_text()) for p in sorted((folder / kind).glob("*.yaml"))] if (folder / kind).is_dir() else []


def log(team):
    path = team["root"] / "provider-log.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


# --- ticket 52: file format and the skeleton ----------------------------------------

@pytest.mark.parametrize("changes, field", [
    ({"target": "dx100_gem5", "cid": GEM5, "protocol": {"repetitions": 10, "sources": [0]}}, "repetitions"),
    ({"target": "dx100_gem5", "cid": GEM5, "protocol": {"repetitions": 1, "sources": [0, 1]}}, "sources"),
    ({"protocol": {"repetitions": 4}}, "repetitions"),
    ({"protocol": {"region_pairs": True}}, "region_pairs"),
    ({"label": "all graphs"}, "label"),
    ({"budgets": {"max_iterations": 9}}, "budgets.max_iterations"),
    ({"budgets": {"lanes": 2}}, "budgets.lanes"),
])
def test_validate_refuses_every_d5_case(team, changes, field):
    changes = copy.deepcopy(changes)
    cid = changes.pop("cid", CID)
    target = changes.pop("target", "native_cpu")
    path = campaign_file(team, cid=cid, target=target, **changes)
    result = run_swdb("validate", "--records", team["records"])
    assert result.returncode == 1 and path.name in result.stderr and field in result.stderr, result.stderr


def test_validate_accepts_named_approvals(team):
    campaign_file(team, budgets={"max_iterations": 9, "lanes": 2},
                  approval={"by": "Yan-Ru Jhou", "date": "2026-10-03", "scope": "fixture",
                            "raised_budgets": ["max_iterations"], "two_lanes": True})
    result = run_swdb("validate", "--records", team["records"])
    assert result.returncode == 0, result.stderr


def test_campaign_without_fixture_uses_the_real_target_adapter(team):
    """Updated 2026-10-04 ET (tickets 56/57): without --fixture the target's real adapter runs;
    off mbit10 it stops before any provider call (its inputs or socket lane are unavailable)."""
    path = campaign_file(team)
    result = run_swdb("campaign", path, "--records", team["records"], "--provider-config", provider(team, {}),
                      "--format", "json")
    summary = json.loads(result.stdout)
    assert summary["stop_reason"] == "infrastructure_failure" and summary["evidence_kind"] == "execution"
    assert summary["budgets"]["used"]["provider_calls_counted"] == 0
    assert not (team["root"] / "provider-log.jsonl").exists()


def test_one_fixture_iteration_end_to_end(team):
    path = campaign_file(team)
    summary = run(team, path, fixture_file(team), provider(team, {}))
    store = campaign_store(team)
    team_ids = {p.stem for p in team["records"].rglob("*.yaml") if "campaign_summaries" not in p.parts}
    created = [yaml.safe_load(p.read_text()) for p in store.rglob("*.yaml") if p.stem not in team_ids]
    kinds = {r["kind"] for r in created}
    assert {"protocol", "candidate", "certification", "evaluation", "comparison_result", "retention",
            "campaign_summary"} <= kinds
    assert all(r.get("mode") == "extensa" and r.get("campaign") == CID for r in created)
    copies = [p for p in store.rglob("*.yaml") if p.stem in team_ids and "campaign_summaries" not in p.parts]
    assert copies and all("mode" not in yaml.safe_load(p.read_text()) for p in copies)
    # the summary is in both stores, tagged, and both stores validate
    team_summary = records_of(team["records"], "campaign_summaries")
    assert [s["id"] for s in team_summary] == [f"{CID}.summary"] and team_summary[0]["mode"] == "extensa"
    for folder in (store, team["records"]):
        result = run_swdb("validate", "--records", folder)
        assert result.returncode == 0, result.stderr
    (it,) = summary["iterations"]
    assert [c["class"] for c in it["candidates"]] == ["kronecker", "uniform_random"]
    assert all(c["level"] == "certified" and c["contracts"] == [CONTRACT] for c in it["candidates"])
    calls = summary["setup"]["provider_calls"] + it["provider_calls"]
    assert [c["role"] for c in calls] == ["profiling", "rewriting", "independent_test_generation"]
    assert all({"role", "model", "effort", "counted"} <= set(c) and c["counted"] for c in calls)
    assert calls[1]["model"] == "gpt-5.6-sol" and calls[1]["effort"] == "xhigh"
    assert summary["stop_reason"] == "max_iterations" and summary["evidence_kind"] == "contract_fixture"
    assert summary["label"] == "single graph per class"
    assert set(it["feedback_reasons"]) == {"certified", "verdict_gain"}


def test_second_iteration_workspace_holds_best_patches_and_feedback_only(team):
    path = campaign_file(team, budgets={"max_iterations": 2})
    run(team, path, fixture_file(team), provider(team, {}))
    rewrites = [entry for entry in log(team) if entry["role"] == "rewriting"]
    assert len(rewrites) == 2
    assert not any(f.startswith("best/") or f == "FEEDBACK.json" for f in rewrites[0]["files"])
    second = set(rewrites[1]["files"])
    assert {"best/kronecker.patch", "best/uniform_random.patch", "FEEDBACK.json", "REGIONS.json"} <= second
    assert not any("records" in f or "workload" in f or f.endswith(".sg") for f in second)


def test_campaign_synthesis_writes_an_experimental_entry_with_campaign_origin(team):
    library = team["root"] / "library"
    shutil.copytree(REPO / "library" / "library_operations", library / "library_operations")
    shutil.copytree(REPO / "library" / "profiles", library / "profiles")
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (library / folder).mkdir()
    good = ("#pragma once\n#include <cstddef>\nstruct SynthBackend {\n  template <typename ValueT, typename IndexT>\n"
            "  static void gather(ValueT* out, const ValueT* source, const IndexT* idx, std::size_t n, std::size_t m) {\n"
            "    (void)m; for (std::size_t i = 0; i < n; ++i) out[i] = source[(std::size_t)idx[i]];\n  }\n};\n")
    config = provider(team, {"rewriting": [rewrite(contracts=())],
                             "synthesis": [{"entry": {"name": "fixture", "summary": "fixture"}, "unresolved": [],
                                            "files": [{"path": "backends/synth_native_cpu_gather.hh",
                                                       "content": good}]}]})
    path = campaign_file(team, library={"allowed_tiers": ["experimental"], "contracts": [], "synthesize": ["gather"]},
                         budgets={"provider_calls_setup": 0})
    summary = run(team, path, fixture_file(team), config, "--library", library)
    (it,) = summary["iterations"]
    assert [c["role"] for c in it["provider_calls"]] == ["rewriting", "synthesis"]
    assert all(c["counted"] for c in it["provider_calls"])
    (added,) = summary["library_entries"]
    assert added["family"] == "gather" and added["state"] == "installed" and added["tier"] == "experimental"
    entry = yaml.safe_load(next((library / "library_operations" / "synthesized").rglob("entry.yaml")).read_text())
    assert entry["id"] == added["entry"] and entry["provenance"]["origin"]["campaign"] == CID
    certifications = [c for c in records_of(campaign_store(team), "certifications") if c["entry"]["id"] == added["entry"]]
    assert certifications and all(c["mode"] == "extensa" and c["campaign"] == CID for c in certifications)
    assert all(c["level"] == "uncertified" for c in it["candidates"])

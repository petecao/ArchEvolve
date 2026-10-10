"""Ticket 80: the base source a campaign may name, and one candidate record per class (spec review C14, C19).

Created: 2026-10-05 ET. Every number comes from a fixture runner and is never evidence.
"""

import pytest
import yaml

from conftest import run_swdb
from swdb import campaign
from swdb.store import Store
from testkit.extensa import CID, GEM5, campaign_file, provider
from testkit.extensa_targets import CONTRACT as READ, FakeHost, FakeRunner, gem5_campaign, inside_patch
from testkit.extensa_targets import run as run_target


# --- C14: the base source must be one the adapters build -----------------------------------------

@pytest.mark.parametrize("target, cid", [("native_cpu", CID), ("dx100_gem5", GEM5)])
def test_a_base_source_no_adapter_builds_candidates_from_is_refused(campaign_team, target, cid):
    data = yaml.safe_load(campaign_file(campaign_team, cid=cid, target=target).read_text())
    data["base_source"] = "upstream_do_bfs"
    problems = campaign.campaign_problems(data)
    assert any(p.startswith("base_source:") and "scalar-only snapshot" in p for p in problems), problems
    path = campaign_file(campaign_team, base_source="upstream_do_bfs")
    result = run_swdb("validate", "--records", campaign_team["records"])
    assert result.returncode == 1 and path.name in result.stderr and "base_source" in result.stderr


# --- C19: one candidate record per class --------------------------------------------------------------

def test_identical_trees_across_classes_get_one_record_per_class(repo_team, base_source):
    config = provider(repo_team, {"rewriting": [{"patch": inside_patch(base_source), "contracts": [READ],
                                                 "knobs": [], "unresolved": []}]})
    runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.4})
    loop, summary = run_target(repo_team, gem5_campaign(repo_team, max_iterations=2, plateau_iterations=4), config,
                               runner, FakeHost())
    first, second = ({c["class"]: c["id"] for c in it["candidates"]} for it in summary["iterations"])
    assert first["kronecker"].endswith(".it1.kronecker.a0") and first["uniform_random"].endswith(".it1.uniform_random.a0")
    assert second == first                       # the same tree again in the same class is that class's artifact
    store = Store(loop.store_dir)
    kron, uniform = store.get(first["kronecker"], "candidate"), store.get(first["uniform_random"], "candidate")
    assert uniform["artifact"] == kron["artifact"]                       # the shared tree, same identity
    assert uniform["extensions"]["shared_tree"]["candidate"] == first["kronecker"]
    assert "extensions" not in kron
    assert not (loop.folder / "sources" / first["uniform_random"] / "source").exists()
    assert store.get(uniform["proposal"], "proposal")["request"]["class"] == "uniform_random"
    assert {r["class"]: r["best"] for r in summary["per_class"]} == first      # each best named after its class

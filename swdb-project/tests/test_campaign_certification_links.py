"""The campaign links every certification record of a candidate artifact, one per contract.

Created: 2026-10-14 00:46 ET (Probata proof of concept, ticket 02). The real native and gem5
adapters run on fixture runners with a scripted certification command, as the target tests
do; the contract-fixture adapter runs through `swdb campaign --fixture`. Every number and
certification here is a fixture, never evidence; no test starts a real target run.
"""

import json

import pytest
import yaml

from conftest import run_swdb
from swdb import campaign, certification_common, workflow
from swdb.extensa_boundary import candidate_certifications
from swdb.store import Store
from testkit.extensa import campaign_file, campaign_store, fixture_file, log, provider, records_of, rewrite
from testkit.extensa import run as run_fixture
from testkit.extensa_targets import (CONTRACT, FakeHost, FakeRunner, common, diff, gem5_campaign, inside_patch, run,
                                     write_campaign)

STAGING = "contract.bfs_tdstep_frontier_staging"
TWO = [CONTRACT, STAGING]
FORK = "bfs-native-pilot-20260925-dx10018-a1.baseline"
UPSTREAM = "bfs-native-pilot-20260925-upstream18-a2.baseline"
KRON18 = "bfs-20260925-kronecker18.48de8267ac2098d5"
UNIFORM18 = "bfs-20260925-uniform18.cd2169a5c421baf7"


class ScriptedCertify:
    """The certification command, scripted: one persisted record per call (fixture, not evidence).

    `failed` maps (contract, attempt) to the failed check it names; `refused` maps a contract to
    the refusal check raised before any record exists."""

    def __init__(self, failed=None, refused=None):
        self.calls, self.failed, self.refused = [], failed or {}, refused or {}

    def __call__(self, store, contract, **kw):
        attempt = int(kw["candidate"].rsplit(".a", 1)[1])      # the repair attempt of the candidate ID
        self.calls.append({"contract": contract, "candidate": kw["candidate"]})
        if contract in self.refused:
            raise certification_common.CandidateUsageError("fixture refusal", check=self.refused[contract])
        candidate = store.get(kw["candidate"], "candidate")
        check = self.failed.get((contract, attempt))
        rid = f"certification.scripted.{kw['candidate']}.{contract.split('.')[-1]}.{len(self.calls)}"
        record = workflow.record(
            "certification", rid, entry={"id": contract, "content_sha256": "0" * 64}, dependencies=[],
            candidate={"id": kw["candidate"], "contract": contract, "contract_sha256": "0" * 64,
                       "tree_sha256": candidate["artifact"]["sha256"]},
            command={"version": "fixture", "contracts": [contract]}, host={"hostname": "scripted"},
            matrix=[{"cell": "fixture", "status": "failed", "reason": check} if check
                    else {"cell": "fixture", "status": "passed"}],
            negative_controls=[{"id": "fixture_control", "status": "rejected"}],
            verdict="failed" if check else "certified", evidence_basis="simulated",
            evidence_kind="contract_fixture", created_at="2026-10-14T04:50:00Z")
        workflow.persist(store.dir, record, create=True)
        return record


@pytest.fixture
def scripted(monkeypatch):
    def install(**kw):
        certify = ScriptedCertify(**kw)
        monkeypatch.setattr("testkit.extensa_targets.fake_certify", certify)
        return certify
    return install


def native_campaign(repo_team, contracts):
    data = common(repo_team, "extensa-native-bfs-20261014-t2", "native_cpu")
    data.update(baselines=[{"role": "fork_scalar_tdstep", "candidate": FORK},
                           {"role": "upstream_do_bfs", "candidate": UPSTREAM}],
                protocol={"roi": "bfs.complete_call.v1", "threads": 1, "repetitions": 10,
                          "sources": [0, 1234, 7777], "region_pairs": False,
                          "differences": "Extensa native fixture campaign."},
                workload_classes=[{"class": "kronecker", "workload": KRON18},
                                  {"class": "uniform_random", "workload": UNIFORM18}],
                library={"allowed_tiers": ["shared", "experimental"], "contracts": list(contracts)})
    data["budgets"].update(max_iterations=1)
    return write_campaign(repo_team, data)


def two_contract_gem5(repo_team, contracts=TWO, **budgets):
    path = gem5_campaign(repo_team, max_iterations=1, **budgets)
    data = yaml.safe_load(path.read_text())
    data["library"]["contracts"] = list(contracts)
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def campaign_for(target, repo_team, base_source, contracts):
    if target == "native_cpu":
        patch = diff(base_source, base_source + "// campaign fixture edit\n")
        path = native_campaign(repo_team, contracts)
        runner = FakeRunner({"pilot": 1.0, "fork_scalar_tdstep": 1.3, "upstream_do_bfs": 0.8})
    else:
        patch = inside_patch(base_source)
        path = two_contract_gem5(repo_team, contracts)
        runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02})
    return path, patch, runner


def assert_links_resolve(store_dir, entry, contracts):
    links = entry["certification"]["records"]
    assert [link["contract"] for link in links] == list(contracts)
    store = Store(store_dir)
    bound, _counted = candidate_certifications(store, entry["id"])
    for link in links:
        assert link["record"] in bound
        record = store.get(link["record"], "certification")
        assert record["candidate"]["id"] == entry["id"] and record["candidate"]["contract"] == link["contract"]


# --- two contracts, both certify (native and gem5 adapters) ---------------------------------

@pytest.mark.parametrize("target", ["native_cpu", "dx100_gem5"])
def test_two_contracts_both_certify_link_both_records_in_contract_order(repo_team, base_source, scripted, target):
    certify = scripted()
    path, patch, runner = campaign_for(target, repo_team, base_source, TWO)
    config = provider(repo_team, {"rewriting": [{"patch": patch, "contracts": TWO, "knobs": [], "unresolved": []}]})
    loop, summary = run(repo_team, path, config, runner, FakeHost())
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    for entry in summary["iterations"][0]["candidates"]:
        assert entry["level"] == "certified"
        calls = [c["contract"] for c in certify.calls if c["candidate"] == entry["id"]]
        assert calls == TWO                                   # one certification per contract
        assert entry["certification"]["outcome"] == "certified"
        assert_links_resolve(loop.store_dir, entry, TWO)


# --- one contract fails, or is refused before any record exists (gem5 adapter) ---------------

def gem5_entries(repo_team, base_source, contracts=TWO, **budgets):
    plan = {"patch": inside_patch(base_source), "contracts": list(contracts), "knobs": [], "unresolved": []}
    session = base_source.replace("    init_MAA();\n    t.Start();", "    init_MAA();\n    __dxc_session_begin();\n    t.Start();", 1)
    repaired = {**plan, "patch": diff(base_source, session + "// repaired\n")}
    config = provider(repo_team, {"rewriting": [plan], "repair": [repaired]})
    runner = FakeRunner({"kronecker": 1.4, "uniform_random": 1.02})
    loop, summary = run(repo_team, two_contract_gem5(repo_team, contracts, **budgets), config, runner, FakeHost())
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    return loop, summary["iterations"][0]["candidates"]


def test_one_contract_fails_both_records_linked_and_checks_named_as_today(repo_team, base_source, scripted):
    scripted(failed={(STAGING, 0): "verifier"})
    loop, entries = gem5_entries(repo_team, base_source, max_repairs=0)
    for entry in entries:
        assert entry["level"] == "rejected"
        assert entry["certification"]["outcome"] == "failed"
        assert entry["certification"]["failed_checks"] == ["verifier"]
        assert_links_resolve(loop.store_dir, entry, TWO)


def test_one_contract_fails_then_the_repair_path_runs_as_today(repo_team, base_source, scripted):
    certify = scripted(failed={(STAGING, 0): "verifier"})
    loop, entries = gem5_entries(repo_team, base_source)
    repairs = [e for e in log(repo_team) if e["role"] == "repair"]
    assert repairs and all("CERTIFICATION.json" in e["files"] for e in repairs)
    kron = next(e for e in entries if e["class"] == "kronecker")
    assert kron["level"] == "certified" and kron["id"].endswith(".a1")
    assert_links_resolve(loop.store_dir, kron, TWO)
    # the failed attempt's two certifications ran against the first candidate artifact
    first = kron["id"][:-1] + "0"
    assert [c["contract"] for c in certify.calls if c["candidate"] == first] == TWO


def test_a_refused_contract_is_linked_without_a_record_and_with_its_refusal(repo_team, base_source, scripted):
    scripted(refused={STAGING: "harness_scan"})
    loop, entries = gem5_entries(repo_team, base_source, max_repairs=0)
    for entry in entries:
        assert entry["level"] == "rejected" and entry["certification"]["outcome"] == "failed"
        first, refused = entry["certification"]["records"]
        assert refused == {"contract": STAGING, "record": None, "refusal": "harness_scan"}
        assert first["contract"] == CONTRACT
        assert Store(loop.store_dir).get(first["record"], "certification")["candidate"]["id"] == entry["id"]
        assert entry["certification"]["failed_checks"] == ["harness_scan"]


def test_one_contract_links_one_record_as_before(repo_team, base_source, scripted):
    scripted()
    loop, entries = gem5_entries(repo_team, base_source, contracts=[CONTRACT])
    for entry in entries:
        assert entry["level"] == "certified"
        (link,) = entry["certification"]["records"]
        assert link == {"contract": CONTRACT, "record": entry["certification"]["record"]}
        assert_links_resolve(loop.store_dir, entry, [CONTRACT])


# --- fixture seam: `swdb campaign --fixture` --------------------------------------------------

def test_fixture_campaign_writes_and_links_one_fixture_certification_per_contract(campaign_team):
    path = campaign_file(campaign_team, library={"contracts": TWO})
    summary = run_fixture(campaign_team, path, fixture_file(campaign_team), provider(campaign_team, {
        "rewriting": [rewrite(contracts=TWO)]}))
    assert summary["stop_reason"] == "max_iterations"
    store = campaign_store(campaign_team)
    certifications = {r["id"]: r for r in records_of(store, "certifications")}
    assert run_swdb("validate", "--records", store).returncode == 0
    for entry in summary["iterations"][0]["candidates"]:
        assert entry["level"] == "certified"
        links = entry["certification"]["records"]
        assert [link["contract"] for link in links] == TWO
        for link in links:
            record = certifications[link["record"]]
            assert record["evidence_kind"] == "contract_fixture"
            assert record["candidate"]["id"] == entry["id"] and record["candidate"]["contract"] == link["contract"]
        level = json.loads(run_swdb("candidate-level", entry["id"], "--records", store, "--format", "json").stdout)
        assert set(level["certifications"]) == {link["record"] for link in links}


# --- a campaign saved before ticket 02 --------------------------------------------------------

def test_a_campaign_saved_with_one_record_per_entry_loads_and_resumes(campaign_team):
    path = campaign_file(campaign_team, budgets={"max_iterations": 2})
    config = provider(campaign_team, {"rewriting": [rewrite(), "usage_limit", rewrite()]})
    paused = run_fixture(campaign_team, path, fixture_file(campaign_team), config)
    assert paused["state"] == "paused"
    state_file = campaign_store(campaign_team).parent / "state.json"
    state = json.loads(state_file.read_text())
    (saved,) = state["iterations"]
    for entry in saved["candidates"]:            # the shape a campaign saved before ticket 02
        entry["certification"].pop("records")
    state_file.write_text(json.dumps(state, indent=2))
    summary = run_fixture(campaign_team, path, fixture_file(campaign_team), config, "--resume")
    assert summary["stop_reason"] == "max_iterations" and summary["budgets"]["used"]["iterations"] == 2
    old, new = summary["iterations"]
    for entry in old["candidates"]:
        assert "records" not in entry["certification"]
        assert campaign.certification_links(entry) == [{"contract": CONTRACT,
                                                         "record": entry["certification"]["record"]}]
    for entry in new["candidates"]:
        assert campaign.certification_links(entry) == entry["certification"]["records"]

"""Experimental enabling contracts and the shared-contracts rule (Probata proof of concept, ticket 63).

Created: 2026-10-14 ET. Seams of the formal-verification map's spec: `swdb campaign --fixture` (seam 3, a
contract-fixture campaign with the scripted verifier adapter), `swdb prove` (seam 1) and the record seams
(seam 4): `swdb validate`, `swdb build`, ArchEvolve mode's `swdb submit`, `swdb certify` and the
`evaluation_result` handoff. Every certification, comparison and proof record of a campaign here is a contract
fixture, never evidence; a scripted provider and the scripted verifier adapter stand in. The new contract is a
copy of the enabling contract `contract.bfs_tdstep_frontier_staging` under a new ID (its reference files are the
library's own); no held-out kernel.
"""

import json
import shutil

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb.library import Library
from test_bounded_gate_campaign import MIN_MANY, MIN_ONE, gate_seed  # noqa: F401
from test_derived_implementations import ALPHA, BETA, D1, entries, implementations
from testkit.extensa import campaign_file, campaign_store, comparison, fixture_file, log, provider, rewrite
from testkit.extensa import run as run_fixture
from testkit.library_promotion import promote

STAGING = "contract.bfs_tdstep_frontier_staging"
READ = "contract.bfs_read_offload"
NEW = "contract.t63_frontier_staging"
NEW_FILE = "rewrite_contracts/t63_frontier_staging.yaml"


def new_contract(drop=(), **changes):
    """The rewriting role's new enabling contract: the staging contract under a new ID (YAML text)."""
    data = yaml.safe_load((REPO / "library" / "rewrite_contracts" / "bfs_tdstep_frontier_staging.yaml").read_text())
    data.update(id=NEW, **changes)
    for name in drop:
        data.pop(name)
    return yaml.safe_dump(data, sort_keys=False)


def answer(contracts=(NEW,), patch=ALPHA, contract=None, **extra):
    """A rewrite answer of a campaign that lets the rewriting role write a new enabling contract."""
    return {**rewrite(contracts=list(contracts), patch=patch),
            "new_contract": new_contract() if contract is None else contract, **extra}


@pytest.fixture
def team(gate_seed, tmp_path):
    """Ticket 14's gated seed: the team store with the records the library names, and the campaign's own
    library (a copy of the repository library plus the contract-fixture method version), which the loop adds
    the new contract to."""
    records, library = tmp_path / "records", tmp_path / "campaign-library"
    shutil.copytree(gate_seed["records"], records)
    shutil.copytree(gate_seed["library"], library)
    return {**gate_seed, "records": records, "library": library, "root": tmp_path}


def row(ratio=1.2, certification="certified", wp=None):
    """A fixture class row: the comparisons, the attempt's certification outcome and the WP job's script."""
    return {"comparisons": {"fork_scalar_tdstep": comparison(ratio), "upstream_do_bfs": comparison(0.9)},
            "certification": [certification], "proof": {"wp": wp or {}}}


def campaign(team, plan, *, tiers=("shared", "experimental"), rows=None, contracts=(STAGING,), starts=None,
             **budgets):
    rows = rows or [{"kronecker": row(), "uniform_random": row()}]
    path = campaign_file(team, library={"contracts": list(contracts), "allowed_tiers": list(tiers),
                                        "new_enabling_contracts": True},
                         budgets={"max_iterations": len(rows), "plateau_iterations": 4, "max_repairs": 0, **budgets},
                         **({"derived_starts": list(starts)} if starts else {}))
    fixture = fixture_file(team, base_snapshot="test-source", iterations=rows, proof={"function": "DOBFS"},
                           contract_proofs={READ: {"minimum_bounds": {"threads_1": MIN_ONE, "threads_k": MIN_MANY}}})
    summary = run_fixture(team, path, fixture, provider(team, plan), "--library", team["library"])
    return summary, campaign_store(team)


# --- the rewriting role writes one --------------------------------------------------------------

def test_the_rewriting_role_writes_a_new_enabling_contract_and_the_loop_adds_it_to_the_library(team):
    library = team["library"]
    summary, store = campaign(team, {"rewriting": [answer()]})
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    kron = entries(summary)["kronecker"]
    assert kron["level"] == "certified" and kron["contracts"] == [NEW], kron
    added = Library(library)
    assert added.files[NEW] == library / NEW_FILE
    entry = added.get(NEW)
    assert entry["kind"] == "rewrite_contract"
    origin = entry["provenance"]["origin"]
    assert origin["kind"] == "extensa_rewriting" and origin["campaign"] == summary["campaign"] and origin["iteration"] == 1
    # experimental (no review), entry status draft: a contract-fixture certification is not execution evidence
    from swdb.store import Store
    assert Library(library, Store(store)).state(NEW) == {"tier": "experimental", "status": "draft"}
    row = summary["iterations"][0]
    assert row["new_contract"] == {"contract": NEW, "state": "added",
                                   "content_sha256": added.content_sha256(NEW), "path": NEW_FILE}
    for command in ("validate", "build"):
        checked = run_swdb(command, "--records", store, *(("--library", library) if command == "validate" else ()))
        assert checked.returncode == 0, (command, checked.stdout + checked.stderr)
    # The rewrite role answers `new_contract` only in such campaigns; its wire schema stays strict.
    from swdb import campaign as campaign_module
    from swdb import provider_roles
    schema = campaign_module._roles(new_contracts=True)["rewriting"].output_schema
    assert "new_contract" in schema["required"]
    assert "new_contract" not in campaign_module._roles()["rewriting"].output_schema["properties"]
    assert provider_roles.strict_problems(provider_roles.wire_schema(schema)) == []
    rewriting = [e for e in log(team) if e["role"] == "rewriting"]
    assert "NEW_CONTRACT.json" in rewriting[0]["files"]


# --- enabling only; Extensa mode only: refused before certification ----------------------------------

def refusals(summary):
    """Per iteration: (the row's new_contract block, the kronecker entry's level and rejection)."""
    return [(r.get("new_contract"), entries(summary, i)["kronecker"]) for i, r in enumerate(summary["iterations"])]


def test_an_offloading_an_invalid_or_a_bundled_new_contract_is_refused_before_certification(team):
    plan = {"rewriting": [answer(contract=new_contract(strategies=["dx100_read_offload"])),
                          answer(contract=new_contract(drop=("correctness_check",))),
                          answer(contracts=(NEW, STAGING))]}
    summary, store = campaign(team, plan, rows=[{"kronecker": row(), "uniform_random": row()}] * 3)
    reasons = ["is not an enabling contract: its strategy dx100_read_offload has an offload effect",
               "fails library validation: correctness_check: required field is missing",
               "applies that contract alone (each rewrite is certified alone)"]
    for (block, kron), words in zip(refusals(summary), reasons):
        assert block["state"] == "refused" and words in block["reason"], block
        assert kron["level"] == "rejected" and kron["rejection_reason"] == "provider_output_invalid"
        assert words in kron["rejection"] and kron["certification"] is None
    assert not (team["library"] / NEW_FILE).exists() and Library(team["library"]).get(NEW) is None
    assert not [c for c in yaml_records(store, "certifications")]


def test_only_a_campaign_whose_tiers_allow_experimental_entries_accepts_a_new_contract(team):
    summary, store = campaign(team, {"rewriting": [answer()]}, tiers=("shared",))
    ((block, kron),) = refusals(summary)
    assert block["state"] == "refused" and "allowed library tiers exclude experimental entries" in block["reason"]
    assert kron["level"] == "rejected" and kron["certification"] is None
    assert not (team["library"] / NEW_FILE).exists()


def yaml_records(store, kind):
    return [yaml.safe_load(p.read_text()) for p in sorted((store / kind).glob("*.yaml"))] if (store / kind).is_dir() else []


def yaml_record(store, kind, rid):
    return yaml.safe_load((store / kind / f"{rid}.yaml").read_text())


# --- a certified result is a derived implementation, built on, then proven by route 1 ----------------

def step(contracts, patch, start=None, contract=None):
    """A rewrite answer of a campaign that lists derived starts and lets the role write a new contract."""
    return {**rewrite(contracts=list(contracts), patch=patch), "start": start, "new_contract": contract}


def test_a_certified_result_is_a_derived_implementation_built_on_and_proven_by_route_1(team):
    rows = [{"kronecker": row(1.5, wp={"proven_at": "wp"}), "uniform_random": row(1.5, wp={"proven_at": "wp"})},
            {"kronecker": row(1.2), "uniform_random": row(1.2)}]
    plan = {"rewriting": [step([NEW], ALPHA, contract=new_contract()), step([READ], BETA, D1)]}
    summary, store = campaign(team, plan, rows=rows, contracts=(READ,), starts=(D1,))
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    first, second = entries(summary, 0)["kronecker"], entries(summary, 1)["kronecker"]
    pin = Library(team["library"]).content_sha256(NEW)
    # Certified alone against its predecessor's snapshot, like any enabling rewrite.
    (link,) = first["certification"]["records"]
    certification = yaml_record(store, "certifications", link["record"])
    assert certification["command"]["contracts"] == [NEW] and certification["entry"] == {"id": NEW, "content_sha256": pin}
    assert certification["evidence_kind"] == "contract_fixture"
    assert yaml_record(store, "candidates", first["id"])["source_snapshot"] == "test-source"
    # A derived implementation whose lineage names the experimental contract (ID, version, content hash).
    assert first["derived_implementation"] == D1
    derived = implementations(store)[D1]
    assert derived["contract_lineage"] == [{"contract": NEW, "version": None, "content_sha256": pin}]
    assert derived["rewrite_links"][0]["certification"] == link["record"]
    # No contract proof, no minimum bounds, no template: the bounded rung skips; nothing else is asked for.
    assert {(j["contract"], j["rung"], j["skip_reason"]) for j in first["bounded_gate"]["jobs"]} == {
        (NEW, "threads_1", "no_contract_proof"), (NEW, "threads_k", "no_contract_proof")}
    assert not [r for r in yaml_records(store, "proofs") if (r.get("subject") or {}).get("id") == NEW]
    # Built on: a later iteration starts from it and applies an offloading contract.
    assert second["start"] == D1 and second["level"] == "certified" and second["contracts"] == [READ]
    assert yaml_record(store, "candidates", second["id"])["source_snapshot"] == f"{D1}.source"
    assert "derived_implementation" not in second
    # Proven by route 1: WP alone (no contract seeds) against the kernel's unit postcondition, pinning the
    # experimental contract's content hash.
    kron = next(c for c in summary["wp_phase"]["classes"] if c["class"] == "kronecker")
    (job,) = [j for j in kron["jobs"] if j["candidate"] == first["id"]]
    assert job["contract"] == NEW and job["stages"] == ["wp"] and job["verdict"] == "proven"
    record = yaml_record(store, "proofs", job["record"])
    assert record["subject"] == {"kind": "candidate_proof_unit", "candidate": first["id"], "function": "DOBFS"}
    assert record["pins"]["contract"] == {"id": NEW, "sha256": pin} and record["evidence_kind"] == "contract_fixture"
    assert "skip_reason" not in record
    for command in ("validate", "build"):
        extra = ("--library", team["library"]) if command == "validate" else ()
        checked = run_swdb(command, "--records", store, *extra)
        assert checked.returncode == 0, (command, checked.stdout + checked.stderr)


def test_a_result_that_fails_certification_makes_no_derived_implementation(team):
    failed = {"kronecker": row(certification="failed"), "uniform_random": row(certification="failed")}
    summary, store = campaign(team, {"rewriting": [answer()]}, rows=[failed])
    kron = entries(summary)["kronecker"]
    assert summary["iterations"][0]["new_contract"]["state"] == "added"
    assert kron["level"] == "rejected" and "derived_implementation" not in kron
    assert not [i for i in implementations(store).values() if (i.get("origin") or {}).get("kind") == "derived"]


# --- ArchEvolve mode: shared contracts only, at every rewrite of a chain ------------------------------
#
# The ArchEvolve-mode store is ticket 18's seed shape: the records the library names, the upstream GAPBS
# snapshot `test-source` and its fixture package. The library holds the staging contract, made shared and
# certified by `swdb promote` over a synthetic execution-certification test double (a review needs execution
# evidence; no certification ran), and the new contract as the loop writes it (experimental, draft). The
# certification of a proposal's candidate artifact is scripted (contract fixture), as in tickets 18 and 19.

@pytest.fixture(scope="module")
def archevolve_seed(tmp_path_factory):
    from conftest import make_records
    from test_proof_records import _library_roots
    from testkit.proposals import build_proposal_setup
    from testkit.record_subset import copy_record_subset
    path = tmp_path_factory.mktemp("t63-archevolve")
    records = make_records(path)
    roots = _library_roots() | {"gapbs-bfs-do", "gapbs", "dx100-gapbs", "mbit10", "packing", "loop_tiling"}
    copy_record_subset(REPO / "records", records.path, sorted(roots))
    shutil.copytree(REPO / "library", path / "library")
    (path / "library" / "methods").mkdir(exist_ok=True)       # the contract-fixture method version (ticket 11)
    shutil.copy(REPO / "tests" / "fixtures" / "proof" / "methods" / "contract-fixture-1.yaml", path / "library" / "methods")
    entry = yaml.safe_load(new_contract())
    entry["provenance"]["origin"] = {"kind": "extensa_rewriting", "campaign": "extensa-native-bfs-20261004-a1",
                                     "iteration": 1}
    (path / "library" / NEW_FILE).write_text(yaml.safe_dump(entry, sort_keys=False))
    records, _runs, snapshot, _request = build_proposal_setup(records, path, copy_all=False)
    promote(records.path, path / "library", STAGING)
    return path, snapshot


class ArchEvolve:
    """One test's copy of the ArchEvolve-mode seed (records and library side by side)."""

    def __init__(self, seed, tmp_path):
        source, self.snapshot = seed
        self.root = tmp_path
        shutil.copytree(source / "records", tmp_path / "records", ignore=shutil.ignore_patterns("*.sqlite", ".swdb.lock"))
        shutil.copytree(source / "library", tmp_path / "library")
        self.records, self.library, self.runs = tmp_path / "records", tmp_path / "library", tmp_path / "runs"

    def swdb(self, command, *args):
        return run_swdb(command, "--records", self.records, *args)

    def request(self, rid, contract=None, *, implementation="gapbs-bfs-do", snapshot="test-source",
                package="test-package", patch=ALPHA):
        """A rewrite proposal (one rewrite of a chain); with `contract`, its library section names it."""
        from swdb.store import Store
        source = Store(self.records).get(snapshot, "source_snapshot")
        data = {"message_version": "1.1" if contract else "1.0", "id": rid,
                "producer": {"name": "t63-proposal-test", "role": "sw", "test_client": True},
                "profile_package": package, "source_snapshot": snapshot, "implementation": implementation,
                "source_sha256": source["artifact"]["sha256"], "intent": "Fixture rewrite; contract test only.",
                "regions": [source["regions"][0]["id"]],
                "constraints": {"editable_files": ["src/bfs.cc"], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, "required_operations": []}
        if contract:
            pin = {"id": contract, "content_sha256": Library(self.library).content_sha256(contract)}
            data["library"] = {"contract": pin, "entries": [], "shipped_files": []}
        path = self.root / f"{rid}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path

    def submit(self, *args, **kw):
        result = self.swdb("submit", self.request(*args, **kw), "--runs-dir", self.runs, "--format", "json")
        return result, (json.loads(result.stdout) if result.stdout.strip() else None)

    def state(self, contract):
        from swdb.store import Store
        return Library(self.library, Store(self.records)).state(contract)


def test_archevolve_mode_refuses_a_proposal_naming_the_experimental_contract_until_promotion(archevolve_seed, tmp_path):
    ae = ArchEvolve(archevolve_seed, tmp_path)
    assert ae.state(NEW) == {"tier": "experimental", "status": "draft"}
    result, proposal = ae.submit("experimental-proposal", NEW)
    assert result.returncode == 1 and proposal["outcome"]["state"] == "rejected", result.stderr
    assert "requires shared certified library entry " + NEW in proposal["outcome"]["reason"]
    assert "candidate" not in proposal
    # Control: once a promotion review makes it shared and it is certified, the same proposal is accepted.
    promote(ae.records, ae.library, NEW)
    assert ae.state(NEW) == {"tier": "shared", "status": "certified"}
    result, proposal = ae.submit("promoted-proposal", NEW)
    assert result.returncode == 0 and proposal["outcome"]["state"] == "candidate_created", result.stderr


def _scripted_certify(store, contract, **kw):
    """The certification command, scripted: a certified contract-fixture record of the contract's current
    content for the candidate artifact (fixture, not evidence)."""
    from swdb import workflow
    candidate = store.get(kw["candidate"], "candidate")
    sha = Library(kw["library"]).content_sha256(contract)
    rid = f"certification.t63.{kw['candidate']}.{contract.removeprefix('contract.')}"
    record = workflow.record(
        "certification", rid, entry={"id": contract, "content_sha256": sha}, dependencies=[],
        candidate={"id": kw["candidate"], "contract": contract, "contract_sha256": sha,
                   "tree_sha256": candidate["artifact"]["sha256"]},
        command={"version": "fixture", "contracts": [contract]}, host={"hostname": "scripted"},
        matrix=[{"cell": "fixture", "status": "passed"}], negative_controls=[{"id": "fixture_control", "status": "rejected"}],
        verdict="certified", evidence_basis="simulated", evidence_kind="contract_fixture",
        created_at="2026-10-14T14:00:00Z")
    workflow.persist(store.dir, record, create=True)
    return record


def _certify(ae, capsys, contract, candidate):
    """`swdb certify` in this process with the scripted certification; returns its JSON output."""
    from swdb import cli
    capsys.readouterr()
    code = cli.main([str(a) for a in ("certify", contract, "--candidate", candidate, "--records", ae.records,
                                      "--library", ae.library, "--runs-dir", ae.runs)])
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out
    return out


def _derived_step(ae, capsys, rid, contract, **request):
    """One rewrite of an ArchEvolve-mode chain: a proposal (its library section naming `contract` when the
    contract is shared, else none), the scripted certification of its candidate artifact under `contract`,
    and the derived implementation `swdb certify` records; returns (derived implementation, its package)."""
    result, proposal = ae.submit(rid, contract if ae.state(contract)["tier"] == "shared" else None, **request)
    assert result.returncode == 0, result.stderr
    out = _certify(ae, capsys, contract, proposal["candidate"])
    derived = out["derived_implementation"]
    made = ae.swdb("fixture-package", f"{derived}.source", "--id", f"{rid}-package")
    assert made.returncode == 0, made.stdout + made.stderr
    return derived, f"{rid}-package"


def on(derived, package):
    """A proposal's target: the derived implementation, its snapshot and its package."""
    return {"implementation": derived, "snapshot": f"{derived}.source", "package": package}


def test_every_rewrite_of_an_archevolve_chain_is_one_proposal_and_names_only_shared_contracts(
        archevolve_seed, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("swdb.certification.certify", _scripted_certify)
    ae = ArchEvolve(archevolve_seed, tmp_path)
    # First rewrite: names the shared enabling contract; accepted, certified, a derived implementation.
    d1, package = _derived_step(ae, capsys, "first-proposal", STAGING)
    # Second rewrite: names the non-shared (experimental) contract; refused at submit.
    result, proposal = ae.submit("second-proposal", NEW, patch=BETA, **on(d1, package))
    assert result.returncode == 1 and "requires shared certified library entry " + NEW in proposal["outcome"]["reason"]
    # A derived implementation with a non-shared contract in its lineage (a proposal without a library section,
    # certified under the experimental contract) is no target either, whatever contract the proposal names.
    dx, package_x = _derived_step(ae, capsys, "experimental-step", NEW)
    for rid, contract in (("on-experimental", STAGING), ("on-experimental-bare", None)):
        result, proposal = ae.submit(rid, contract, patch=BETA, **on(dx, package_x))
        assert result.returncode == 1 and proposal["outcome"]["state"] == "rejected", (rid, result.stderr)
        assert f"derived implementation {dx}'s lineage: contract {NEW} is experimental" in proposal["outcome"]["reason"]
    # Control: the shared contract on the shared chain is accepted.
    result, proposal = ae.submit("third-proposal", STAGING, patch=BETA, **on(d1, package))
    assert result.returncode == 0 and proposal["outcome"]["state"] == "candidate_created", result.stderr


def test_an_archevolve_chains_derived_implementations_stay_in_the_research_database(
        archevolve_seed, tmp_path, monkeypatch, capsys):
    """Only through promotion: the handoff names the final candidate artifact, never a derived implementation."""
    from test_archevolve_proof_path import _evaluate
    monkeypatch.setattr("swdb.certification.certify", _scripted_certify)
    ae = ArchEvolve(archevolve_seed, tmp_path)

    class Records:                                       # the shape `_evaluate` (ticket 18) writes through
        path = ae.records

        def read(self, rel):
            return yaml.safe_load((ae.records / rel).read_text())

        def write(self, rel, data):
            (ae.records / rel).write_text(yaml.safe_dump(data, sort_keys=False))

        def swdb(self, command, *args):
            return ae.swdb(command, *args)

    d1, package = _derived_step(ae, capsys, "first-proposal", STAGING)
    result, proposal = ae.submit("final-proposal", STAGING, patch=BETA, **on(d1, package))
    assert result.returncode == 0, result.stderr
    final = proposal["candidate"]
    _certify(ae, capsys, STAGING, final)                 # the final rewrite is enabling too: a second link
    # The native evaluator does not yet build a candidate artifact whose implementation is a derived
    # implementation (records-root code): the evaluation record is written with that failure, and its handoff
    # is what ArchEvolve receives for the final candidate artifact.
    with pytest.raises(AssertionError, match="native evaluator requires an application-backed candidate"):
        _evaluate(Records(), tmp_path, ae.runs, final, "eval-final")
    sent = ae.swdb("handoff-message", "evaluation_result", "eval-final", "--db", tmp_path / "build.sqlite",
                   "--format", "json")
    assert sent.returncode == 0, sent.stderr
    content = json.loads(sent.stdout)["content"]
    assert content["candidate"] == final
    assert content["software_hardware_pair"]["implementation"] == "gapbs-bfs-do"     # the chain's root
    text = json.dumps(content)
    derived = sorted(p.stem for p in (ae.records / "implementations").glob("*.derived.yaml"))
    assert derived == sorted([f"{d1}", f"{final}.derived"])           # both stay in the store that certified them
    assert not [rid for rid in derived if rid in text], content["software_hardware_pair"]


def test_archevolve_modes_proof_path_refuses_a_candidate_certified_under_a_non_shared_contract(
        archevolve_seed, tmp_path, monkeypatch, capsys):
    from swdb.archevolve_proof import certified_contracts
    monkeypatch.setattr("swdb.certification.certify", _scripted_certify)
    ae = ArchEvolve(archevolve_seed, tmp_path)
    _derived_step(ae, capsys, "experimental-step", NEW)
    plan = tmp_path / "plan.yaml"
    plan.write_text(yaml.safe_dump({"plan": "archevolve_proof_fixture.1", "candidates": [{}]}))
    for step in ("bounded", "unbounded"):
        refused = ae.swdb("prove", "--proof-path", step, "--candidate", "experimental-step.candidate-1", "--function",
                          "DOBFS", "--adapter", "scripted", "--plan", plan, "--runs-dir", tmp_path / "proof-runs",
                          "--format", "json")
        assert refused.returncode != 0 and f"contract {NEW} is experimental" in refused.stderr, refused.stderr
        assert not (ae.records / "proofs").exists()
    # Control: a candidate artifact certified under the shared contract goes on to the proof steps.
    _derived_step(ae, capsys, "shared-step", STAGING)
    assert certified_contracts(ae.records, "shared-step.candidate-1") == [STAGING]

"""Two winners per workload class: the fastest winner and the best-proven winner.

Created: 2026-10-14 ET (Probata proof of concept, ticket 15). Seam 3 of the formal-verification map's spec
(`swdb campaign --fixture`, a contract-fixture campaign with the scripted verifier adapter), seam 2
(`swdb candidate-level`) and seam 4 (`swdb validate`, `swdb build`, `swdb promote`). Every certification,
comparison and proof record here is a contract fixture, never evidence; no real verifier or provider runs.
The fixture and its library (ticket 11's `contract_fixture` method version: 15 minutes per bounded job,
k = 3) come from ticket 14's bounded-gate tests. A fixture class row scripts its candidate artifact's speed
(`comparisons`) and its bounded rungs (`proof`): both rungs proven gives proven within bounds, threads <= k;
a `threads_k` timeout leaves proven within bounds, threads = 1; two timeouts leave certified.
"""

import json

import yaml

from conftest import run_swdb
from test_bounded_gate_campaign import (MIN_ONE, READ, edit, entries, gate_campaign, gate_fixture,  # noqa: F401
                                        gate_seed, level, team)       # gate_seed, team: fixtures
from testkit.bfs_protocol import _payload
from testkit.extensa import campaign_file, campaign_store, comparison, provider, rewrite
from testkit.extensa import run as run_fixture

THREADS_K, THREADS_1, CERTIFIED = "proven_within_bounds_threads_k", "proven_within_bounds_threads_1", "certified"
#: One patch per iteration (one rewrite call per iteration serves every class).
PATCHES = [edit("int alpha = 15", "int alpha = 14"), edit("int beta = 18", "int beta = 17"),
           edit("int alpha = 15", "int alpha = 13"), edit("int beta = 18", "int beta = 16")]


def row(ratio, rungs=THREADS_K, **extra):
    """A fixture class row: a gain at `ratio` and the bounded level its rungs reach."""
    proof = {THREADS_K: {}, THREADS_1: {"threads_k": ["timeout"]},
             CERTIFIED: {"threads_1": ["timeout"], "threads_k": ["timeout"]}}[rungs]
    return {"comparisons": {"fork_scalar_tdstep": comparison(ratio), "upstream_do_bfs": comparison(0.9)},
            "proof": {**proof, **extra}}


def campaign(team, rows, *, plan=None, **budgets):
    """A gated fixture campaign: `rows` is one {class: row} per iteration; the rewrite call of iteration i
    returns PATCHES[i] under READ."""
    fixture = gate_fixture(team, iterations=rows)
    plan = plan or {"rewriting": [rewrite(contracts=[READ], patch=PATCHES[i]) for i in range(len(rows))]}
    return gate_campaign(team, plan, fixture=fixture, **{"max_iterations": len(rows), **budgets})


def per_class(summary, cls):
    return next(c for c in summary["per_class"] if c["class"] == cls)


def winners(rows, cls=None):
    """{winner mark: candidate} of a per-class row, or of one class in an iteration row's `winners`."""
    rows = [r for r in rows if cls is None or r["class"] == cls]
    return {r["winner"]: r["candidate"] for r in rows}


def rewrite_calls(team):
    return [json.loads(line) for line in (team["root"] / "provider-log.jsonl").read_text().splitlines()
            if json.loads(line)["role"] == "rewriting"]


# --- the tracer: both winners tracked inside the loop, shown in best/, reported in the summary ------------------

def test_both_winners_are_tracked_every_iteration_shown_in_best_and_reported_in_the_summary(team):
    rows = [{"kronecker": row(1.5, THREADS_1), "uniform_random": row(1.2)},
            {"kronecker": row(1.2), "uniform_random": row(1.3)},
            {"kronecker": row(1.1, CERTIFIED), "uniform_random": row(1.1, CERTIFIED)}]
    summary, store = campaign(team, rows)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    k1, k2, k3 = (entries(summary, i)["kronecker"][0]["id"] for i in range(3))
    u1, u2, _u3 = (entries(summary, i)["uniform_random"][0]["id"] for i in range(3))
    # After each iteration, the winners from the levels known so far (one row when one candidate wins both).
    tracked = [summary["iterations"][i]["winners"] for i in range(3)]
    assert winners(tracked[0], "kronecker") == {"both": k1}
    assert winners(tracked[1], "kronecker") == {"fastest": k1, "best_proven": k2}   # threads <= k beats = 1
    assert winners(tracked[2], "kronecker") == {"fastest": k1, "best_proven": k2}
    assert winners(tracked[0], "uniform_random") == {"both": u1}
    assert winners(tracked[1], "uniform_random") == {"both": u2}                    # same rung: the faster
    # Each winner's level snapshot matches what `swdb candidate-level` reports (never proven unbounded).
    for rows_now in tracked:
        for winner in rows_now:
            snapshot = winner["level_snapshot"]
            assert snapshot["level"] == level(store, winner["candidate"])["level"] != "proven_unbounded"
            assert snapshot["level_rule"] == "level-rule.1" and snapshot["at"].endswith(" ET")
    # The next rewrite workspace's best/: the fastest winner's patch, and the best-proven winner's when it differs.
    calls = rewrite_calls(team)
    assert calls[1]["best"] == {"best/kronecker.patch": PATCHES[0], "best/uniform_random.patch": PATCHES[0]}
    assert calls[2]["best"] == {"best/kronecker.patch": PATCHES[0], "best/kronecker.best_proven.patch": PATCHES[1],
                                "best/uniform_random.patch": PATCHES[1]}
    # The summary: both winners per class, each with a dated level snapshot; one candidate winning both, once.
    kron, uniform = per_class(summary, "kronecker"), per_class(summary, "uniform_random")
    assert kron["best"] == k1 and kron["best_proven"] == k2
    assert winners(kron["winners"]) == {"fastest": k1, "best_proven": k2}
    assert {w["candidate"]: w["level_snapshot"]["level"] for w in kron["winners"]} == {k1: THREADS_1, k2: THREADS_K}
    assert uniform["winners"] == [w for w in uniform["winners"] if w["winner"] == "both"] and \
        winners(uniform["winners"]) == {"both": u2} and uniform["best"] == uniform["best_proven"] == u2
    # Every candidate artifact stays in the summary with its level and speed.
    for index in range(3):
        for entry in summary["iterations"][index]["candidates"]:
            assert entry["selection"]["lower"] and entry["level_snapshot"]["level"] == level(store, entry["id"])["level"]
    assert entries(summary, 2)["kronecker"][0]["level_snapshot"]["level"] == CERTIFIED and k3


# --- the summary: validated and built; Yan-Ru chooses which winner to promote -------------------------------

def team_summary(team):
    (path,) = (team["records"] / "campaign_summaries").glob("*.yaml")
    return path


def test_the_summary_validates_and_builds_refuses_an_undated_snapshot_and_either_winner_can_be_promoted(team):
    rows = [{"kronecker": row(1.5, THREADS_1), "uniform_random": row(1.2, CERTIFIED)},
            {"kronecker": row(1.2), "uniform_random": row(1.1, CERTIFIED)}]
    summary, store = campaign(team, rows)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    k1, k2 = (entries(summary, i)["kronecker"][0]["id"] for i in range(2))
    kron, uniform = per_class(summary, "kronecker"), per_class(summary, "uniform_random")
    assert winners(kron["winners"]) == {"fastest": k1, "best_proven": k2}
    # A class with no proven gain candidate artifact has no best-proven winner, and its summary says so.
    assert uniform["best_proven"] is None and "proven level" in uniform["best_proven_note"]
    assert [w["winner"] for w in uniform["winners"]] == ["fastest"]
    # Neither winner is marked as the one to promote.
    assert not any("promot" in key or "recommend" in key for key in kron)
    # `swdb validate` and `swdb build` accept the new fields (the team store holds the summary).
    for command in ("validate", "build"):
        result = run_swdb(command, "--records", team["records"])
        assert result.returncode == 0, result.stdout + result.stderr
    # A level snapshot missing its date or its level-rule version is refused.
    path = team_summary(team)
    original = path.read_text()
    for field in ("at", "level_rule"):
        data = yaml.safe_load(original)
        next(c for c in data["per_class"] if c["class"] == "kronecker")["winners"][0]["level_snapshot"].pop(field)
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        result = run_swdb("validate", "--records", team["records"])
        assert result.returncode != 0 and field in result.stdout + result.stderr, field
    path.write_text(original)
    # Yan-Ru chooses: the existing promotion command accepts either winner of the class. Promotion evidence is
    # a certification under a named command version (spec review C3), which a fixture campaign's are not: each
    # winner is certified again under one first, as `swdb promote` asks.
    workload = yaml.safe_load((store / "workloads" / f"{team['kronecker']}.yaml").read_text())
    for index, winner in enumerate((k1, k2)):
        certification = yaml.safe_load((store / "certifications" /
                                        f"{entries(summary, index)['kronecker'][0]['certification']['record']}.yaml").read_text())
        for tag in ("mode", "campaign"):        # `swdb add` takes the untagged form ticket 48's fixture uses
            certification.pop(tag, None)
        certification.update(id=f"certification.{winner}.named", command={"version": "1.5"})
        result = run_swdb("add", "--records", store, _payload(team["root"], f"named-{index}", certification))
        assert result.returncode == 0, result.stdout + result.stderr
    for winner in (k1, k2):
        result = run_swdb("promote", winner, "--records", store, "--protocol", team["protocol"], "--workload-class",
                          workload["definition"]["family"], "--output", team["root"] / f"reeval-{winner}",
                          "--format", "json")
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["review"]["target"]["id"] == winner


# --- the plateau test uses both winners ------------------------------------------------------------------------

def test_the_plateau_stop_waits_while_the_best_proven_winner_still_improves(team):
    rows = [{cls: row(2.0, CERTIFIED) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1, THREADS_1) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1) for cls in ("kronecker", "uniform_random")}]
    summary, _store = campaign(team, rows, plateau_iterations=1)
    # The fastest winner stays put after iteration 1; the best-proven winner improves in iterations 2 and 3,
    # for longer than plateau_iterations: the campaign runs to max_iterations.
    assert summary["stop_reason"] == "max_iterations" and summary["budgets"]["used"]["iterations"] == 3
    fastest = entries(summary, 0)["kronecker"][0]["id"]
    for index in (1, 2):
        it = summary["iterations"][index]
        assert it["improved_winners"] == [{"class": cls, "winner": "best_proven"}
                                          for cls in ("kronecker", "uniform_random")]
        assert winners(it["winners"], "kronecker")["fastest"] == fastest


def test_control_the_plateau_stop_ends_a_campaign_when_neither_winner_improves(team):
    rows = [{cls: row(1.5, THREADS_1) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.2, THREADS_1) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1, THREADS_1) for cls in ("kronecker", "uniform_random")}]
    summary, _store = campaign(team, rows, plateau_iterations=1)
    assert summary["stop_reason"] == "plateau" and summary["budgets"]["used"]["iterations"] == 2
    assert summary["iterations"][1]["improved_winners"] == [] and summary["iterations"][1]["improved_classes"] == []


# --- the fastest winner: the rule is unchanged ----------------------------------------------------------------

def test_with_only_certified_and_uncertified_levels_the_fastest_winner_is_picked_as_before(team):
    """No method version in the library: no gate, no proof record, so no proven level."""
    rows = [{cls: row(1.2) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.5) for cls in ("kronecker", "uniform_random")}]
    plan = {"rewriting": [rewrite(contracts=[READ], patch=PATCHES[0]), rewrite(contracts=[], patch=PATCHES[1])]}
    summary, _store = gate_campaign(team, plan, fixture=gate_fixture(team, iterations=rows), library=False,
                                    max_iterations=2)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    assert "bounded_gate" not in summary
    for cls in ("kronecker", "uniform_random"):
        certified, uncertified = (entries(summary, i)[cls][0] for i in range(2))
        assert certified["level"] == "certified" and uncertified["level"] == "uncertified"
        result = per_class(summary, cls)
        # Certified beats uncertified; the faster uncertified candidate artifact stays listed.
        assert result["best"] == certified["id"] and result["best_level"] == "certified"
        assert result["faster_uncertified"] == [uncertified["id"]]
        assert result["best_proven"] is None and result["best_proven_note"]
        assert [(w["candidate"], w["winner"], w["level_snapshot"]["level"]) for w in result["winners"]] == \
            [(certified["id"], "fastest", "certified")]
        assert uncertified["level_snapshot"]["level"] == "uncertified"
        assert summary["iterations"][1]["improved_winners"] == []  # the faster uncertified one improves nothing


# --- negative controls ------------------------------------------------------------------------------------------

def paused(team, rows, between, first=PATCHES[0], contracts=(READ,)):
    """A gated campaign of len(rows) iterations whose rewrite call of iteration 2 first hits a usage limit, so
    the campaign pauses after iteration 1; `between(store, summary_so_far)` changes the store; then it resumes.
    Iteration 1's rewrite uses `first` under `contracts`; the retried iteration 2 uses PATCHES[1] under READ."""
    fixture = gate_fixture(team, iterations=rows)
    config = provider(team, {"rewriting": [rewrite(contracts=list(contracts), patch=first), "usage_limit",
                                           rewrite(contracts=[READ], patch=PATCHES[1])]})
    path = campaign_file(team, library={"contracts": [READ]}, budgets={"max_iterations": len(rows)})
    first_run = run_fixture(team, path, fixture, config, "--library", team["library"])
    assert first_run["state"] == "paused", first_run
    store = campaign_store(team)
    state = json.loads((store.parent / "state.json").read_text())
    between(store, state["iterations"][0])
    summary = run_fixture(team, path, fixture, config, "--library", team["library"], "--resume")
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    return summary, store


def prove(team, store, candidate, verdict, name):
    """`swdb prove` on a candidate artifact's READ proof unit with the scripted adapter, outside the loop."""
    script = team["root"] / f"{name}.yaml"
    body = {"verdict": verdict, "bounds": MIN_ONE, "assumptions": []}
    if verdict == "refuted":
        body["counterexample"] = {"source": 0, "graph": "3 vertices, 2 edges", "differs_at": "parent[2]"}
    script.write_text(yaml.safe_dump(body))
    result = run_swdb("prove", "--records", store, "--candidate", candidate, "--function", "DOBFS", "--contract", READ,
                      "--adapter", "scripted", "--script", script, "--runs-dir", team["root"] / "proof-runs",
                      "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def test_a_an_uncertified_candidate_given_a_scripted_proven_record_never_becomes_best_proven(team):
    rows = [{cls: row(1.5) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1, THREADS_1) for cls in ("kronecker", "uniform_random")}]
    written = []

    def give_proven(store, iteration):
        (uncertified,) = [c for c in iteration["candidates"] if c["class"] == "kronecker"]
        assert uncertified["level"] == "uncertified"
        written.append(prove(team, store, uncertified["id"], "proven", "proven-uncertified"))

    summary, store = paused(team, rows, give_proven, contracts=())
    uncertified, certified = entries(summary, 0)["kronecker"][0], entries(summary, 1)["kronecker"][0]
    assert written[0]["subject"]["candidate"] == uncertified["id"] and written[0]["verdict"] == "proven"
    # Proven requires certified: the record does not lift its level, and it never becomes best-proven.
    assert level(store, uncertified["id"])["level"] == "uncertified"
    kron = per_class(summary, "kronecker")
    assert kron["best_proven"] == certified["id"] and kron["best"] == certified["id"]
    assert kron["faster_uncertified"] == [uncertified["id"]]
    marks = [w["winner"] for it in summary["iterations"] for w in it["winners"] if w["candidate"] == uncertified["id"]]
    assert marks == ["fastest"]            # after iteration 1 it was the fastest winner, never the best-proven one


def test_b_a_candidate_with_a_counting_refutation_wins_neither_whatever_its_level_or_speed(team):
    rows = [{cls: row(3.0) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1, THREADS_1) for cls in ("kronecker", "uniform_random")}]

    def refute(store, iteration):
        (fast,) = [c for c in iteration["candidates"] if c["class"] == "kronecker"]
        assert level(store, fast["id"])["level"] == THREADS_K     # the fastest and the best proven so far
        prove(team, store, fast["id"], "refuted", "late-refutation")

    summary, store = paused(team, rows, refute)
    refuted, later = entries(summary, 0)["kronecker"][0], entries(summary, 1)["kronecker"][0]
    assert level(store, refuted["id"])["refuted"]["flag"] is True
    assert refuted["selection"]["verdict"] == "gain"           # evaluated before the refutation was written
    kron = per_class(summary, "kronecker")
    assert winners(kron["winners"]) == {"both": later["id"]}
    assert winners(summary["iterations"][1]["winners"], "kronecker") == {"both": later["id"]}
    assert refuted["level_snapshot"]["level"] == CERTIFIED
    # Control: the other class's iteration-1 candidate artifact, not refuted, keeps both wins.
    uniform_first = entries(summary, 0)["uniform_random"][0]["id"]
    assert winners(per_class(summary, "uniform_random")["winners"]) == {"both": uniform_first}


def test_c_bounds_above_the_minimum_are_never_ranked_two_threads_1_candidates_rank_by_speed(team):
    above = {**MIN_ONE, "vertices": 6, "edges": 6}
    rows = [{"kronecker": row(1.1, THREADS_1, threads_1=[{"verdict": "proven", "bounds": above}]),
             "uniform_random": row(1.3, THREADS_1)},
            {"kronecker": row(1.3, THREADS_1),
             "uniform_random": row(1.1, THREADS_1, threads_1=[{"verdict": "proven", "bounds": above}])}]
    summary, store = campaign(team, rows)
    assert summary["stop_reason"] == "max_iterations", summary.get("stop_detail")
    for cls, faster in (("kronecker", 1), ("uniform_random", 0)):
        found = [entries(summary, i)[cls][0] for i in range(2)]
        assert [level(store, e["id"])["level"] for e in found] == [THREADS_1, THREADS_1]
        bounds = [yaml.safe_load((store / "proofs" / f"{job['record']}.yaml").read_text())["bounds"]
                  for e in found for job in e["bounded_gate"]["jobs"] if job["rung"] == "threads_1"]
        assert bounds[1 - faster] == above and bounds[faster] == MIN_ONE      # the slower one proved more
        assert per_class(summary, cls)["best_proven"] == found[faster]["id"]


def test_d_a_candidate_whose_proof_pin_changed_mid_campaign_reads_certified_and_drops_out_of_best_proven(team):
    rows = [{cls: row(1.3) for cls in ("kronecker", "uniform_random")},
            {cls: row(1.1, THREADS_1) for cls in ("kronecker", "uniform_random")}]

    def rederive_minimum_bounds(store, iteration):
        (first,) = [c for c in iteration["candidates"] if c["class"] == "kronecker"]
        assert level(store, first["id"])["level"] == THREADS_K
        # Both rungs' minimum-bounds derivation records change content, so the pins in the records of
        # iteration 1 no longer match (a re-derivation; ticket 33 writes the real ones).
        for path in (store / "proofs").glob("*.contract-fixture.*threads-*.yaml"):
            record = yaml.safe_load(path.read_text())
            record["provenance"].append({"id": "rederived", "kind": "agent_run", "uri": None,
                                         "description": "Contract fixture: the derivation was run again."})
            path.write_text(yaml.safe_dump(record, sort_keys=False))

    summary, store = paused(team, rows, rederive_minimum_bounds)
    first, later = entries(summary, 0)["kronecker"][0], entries(summary, 1)["kronecker"][0]
    after = level(store, first["id"])
    assert after["level"] == CERTIFIED and {p["pin"] for s in after["stale_proofs"] for p in s["pins"]} == \
        {"minimum_bounds"}
    kron = per_class(summary, "kronecker")
    assert kron["best"] == first["id"] and kron["best_proven"] == later["id"]       # the fastest stays fastest
    assert {w["candidate"]: w["level_snapshot"]["level"] for w in kron["winners"]} == \
        {first["id"]: CERTIFIED, later["id"]: THREADS_1}
    # Iteration 1's dated snapshot is never recomputed; iteration 2's tracking reads the level known then.
    assert winners(summary["iterations"][0]["winners"], "kronecker") == {"both": first["id"]}
    assert summary["iterations"][0]["winners"][0]["level_snapshot"]["level"] == THREADS_K
    assert winners(summary["iterations"][1]["winners"], "kronecker") == {"fastest": first["id"],
                                                                         "best_proven": later["id"]}

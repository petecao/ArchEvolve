"""Hint records, the deterministic merger and the proof hint check, through `swdb prove --adapter wp`.

Created: 2026-10-14 ET (Probata proof of concept ticket 35). Design: formal-verification map spec ("Proof-hint
loop": hint form, vocabulary, three checks; "Testing Decisions", seam 1, the seven WP fact files); map 13
items 2, 4, 5, 7, 8, 12; map 24 items 1, 7. Format: docs/reference/format-v0.4-proof-hints.md.

Seam 1 (`swdb prove`) and seam 4 (`swdb validate`, `swdb build`). The proof hint check parses every hint with
the real Frama-C 33.0 (cases skip cleanly when Frama-C or clang 22.1.8 is missing); the WP run itself is the
scripted stand-in `frama-c` of ticket 21 (SWDB_FRAMA_C), so no prover runs. Run inside the machine-wide verifier
lock (on the Mac: verifier_run.py).
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from conftest import FIXTURES, run_swdb
from test_wp_adapter import FILL, Seed, build_wp_seed, fake, needs_wp

HINTS = FIXTURES / "proof" / "hints"
LOOP = "swdb_fixture_fill.loop1.head"
BEFORE = "swdb_fixture_fill.s2.before"
AFTER = "swdb_fixture_fill.s1.after"
GLOBALS = "ghost.globals"
AGENT = {"source": "agent"}


def hint(anchor, kind, text, provenance=AGENT):
    return {"anchor": anchor, "kind": kind, "text": text, "provenance": dict(provenance)}


GOOD = [hint(LOOP, "loop_invariant", "loop invariant 0 <= i <= n;"),
        hint(LOOP, "loop_invariant", "loop invariant \\forall integer k; 0 <= k < i ==> a[k] == v;",
             {"source": "seed", "seed_source": "contract.fixture_wp_fill"}),
        hint(LOOP, "loop_assigns", "loop assigns i, a[0 .. n-1];", {"source": "human"}),
        hint(LOOP, "loop_variant", "loop variant n - i;")]


@pytest.fixture(scope="module")
def hint_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("hint-seed")
    return path, build_wp_seed(path)


class HintSeed(Seed):
    def prove_hints(self, hints, *extra, ok=True, name="set", env=None):
        """`swdb prove --adapter wp` with a hint file; the WP run is the scripted stand-in (one goal unknown)."""
        path = self.root / f"hints-{name}.yaml"
        path.write_text(yaml.safe_dump({"hints": hints}, sort_keys=False))
        args = ["--candidate", self.candidates["safe"], "--function", "swdb_fixture_fill", "--contract", FILL,
                "--adapter", "wp", "--runs-dir", self.runs, "--format", "json", "--hint-file", path]
        result = run_swdb("prove", "--records", self.records, *args, *extra, env=env or fake("unknown"),
                          timeout=3600)                   # the job may queue behind others for the verifier lock
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return self.read(json.loads(result.stdout)) if ok else result


@pytest.fixture
def seed(hint_seed, tmp_path):
    import shutil
    source, candidates = hint_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return HintSeed(tmp_path, candidates)


def report(record, name):
    return Path(next(r["path"] for r in record["evidence"]["reports"] if r["name"] == name))


def rules(record):
    return sorted({r["rule"] for r in record["hint_check"]["rejections"]})


# --- record shape ----------------------------------------------------------------------------------------------

@needs_wp
def test_a_record_carries_the_hint_set_with_provenance_per_hint_and_passes_validate_and_build(seed):
    record = seed.prove_hints(GOOD)
    hint_set = record["hint_set"]
    assert [h["provenance"] for h in hint_set["hints"]] == [
        {"source": "agent"}, {"source": "seed", "seed_source": "contract.fixture_wp_fill"}, {"source": "human"},
        {"source": "agent"}]
    assert {(h["anchor"], h["kind"], h["text"]) for h in hint_set["hints"]} == \
        {(h["anchor"], h["kind"], h["text"]) for h in GOOD}
    assert record["hint_check"]["verdict"] == "accepted" and record["hint_check"]["rejections"] == []
    assert seed.swdb("validate").returncode == 0
    built = seed.swdb("build")
    assert built.returncode == 0, built.stderr
    path = seed.records / "proofs" / f"{record['id']}.yaml"
    broken = yaml.safe_load(path.read_text())
    del broken["hint_set"]["hints"][0]["provenance"]
    path.write_text(yaml.safe_dump(broken, sort_keys=False))
    failed = seed.swdb("validate")
    assert failed.returncode != 0 and "provenance" in failed.stdout + failed.stderr


@needs_wp
@pytest.mark.parametrize("field", ["anchor", "kind", "text", "provenance"])
def test_a_hint_file_whose_record_misses_a_field_is_refused_and_nothing_is_written(seed, field):
    broken = [dict(GOOD[0])]
    del broken[0][field]
    result = seed.prove_hints(broken, ok=False)
    assert field in result.stderr and not list((seed.records / "proofs").glob("*.yaml"))


# --- the deterministic merger ----------------------------------------------------------------------------------

EVERY = yaml.safe_load((HINTS / "every_allowed_kind.yaml").read_text())["hints"]
VOCAB = Path(__file__).resolve().parent.parent / "vocab"


@needs_wp
def test_the_same_lowering_and_hint_set_give_the_same_merged_unit_and_hash_whatever_the_record_order(seed):
    first = seed.prove_hints(EVERY, name="first")
    again = seed.prove_hints(EVERY, name="again")
    shuffled = seed.prove_hints(list(reversed(EVERY[6:])) + EVERY[:6], name="shuffled")   # anchors, kinds reordered
    runs = (first, again, shuffled)
    assert len({r["hint_set"]["sha256"] for r in runs}) == 1
    assert len({r["hint_check"]["merged_sha256"] for r in runs}) == 1
    units = {report(r, "hints_merged").read_bytes() for r in runs}
    assert len(units) == 1 and hashlib.sha256(units.pop()).hexdigest() == first["hint_check"]["merged_sha256"]
    wp_input = report(first, "wp_input").read_text()            # an accepted set reaches WP, merged at its anchors
    assert first["hint_check"]["reached_wp"] and all(h["text"].splitlines()[0] in wp_input for h in EVERY)
    assert first["settings"]["hint_count"] == len(EVERY)


# --- record rules: anchors and the vocabulary -----------------------------------------------------------------

@needs_wp
def test_one_hint_of_each_allowed_kind_is_accepted(seed):
    vocabulary = {e["value"] for e in yaml.safe_load((VOCAB / "proof_hint_kinds.yaml").read_text())["values"]}
    assert {h["kind"] for h in EVERY} == vocabulary
    record = seed.prove_hints(EVERY)
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]["rejections"]


@needs_wp
def test_hint_goal_generation_disables_inherited_provers_and_final_wp_keeps_the_frozen_portfolio(seed):
    # 2026-10-15 ET: Frama-C accumulates repeated -wp-prover selectors; adding none does not remove Z3.
    path = seed.root / "library" / "methods" / "wp-tracer-fixture.yaml"
    method = yaml.safe_load(path.read_text())
    wp = next(row for row in method["lineup"] if row["tool"] == "frama-c-wp")
    wp["flags"] += ["-wp-prover", "z3,cvc5,alt-ergo"]
    path.write_text(yaml.safe_dump(method, sort_keys=False))
    record = seed.prove_hints(GOOD, env=fake("unknown", FAKE_HINT_NO_SOLVERS="1"))
    assert record["hint_check"]["verdict"] == "accepted", record["hint_check"]
    flags = record["settings"]["flags"]
    assert flags.count("-wp-prover") == 1
    assert flags[flags.index("-wp-prover") + 1] == "z3,cvc5,alt-ergo"
    assert "-wp-smoke-tests" in flags


@needs_wp
def test_a_hint_at_an_anchor_the_lowering_did_not_generate_is_rejected_and_the_set_never_reaches_wp(seed):
    record = seed.prove_hints(GOOD + [hint("swdb_fixture_fill.loop9.head", "loop_invariant", "loop invariant 0 <= i;")])
    check = record["hint_check"]
    assert check["verdict"] == "rejected" and not check["reached_wp"]
    assert [(r["hint"], r["rule"]) for r in check["rejections"]] == [(4, "unknown_anchor")]
    assert "loop invariant" not in report(record, "wp_input").read_text()       # WP ran without any hint
    assert record["settings"]["hint_count"] == 0


@needs_wp
@pytest.mark.parametrize("kind, anchor, text, rule", [
    ("check", BEFORE, "check a[i] == a[i];", "kind_not_allowed"),
    ("requires", GLOBALS, "requires n >= 0;", "kind_not_allowed"),
    ("loop_invariant", BEFORE, "loop invariant 0 <= i;", "anchor_kind_mismatch"),
    ("lemma", LOOP, "lemma L: \\true;", "anchor_kind_mismatch")])
def test_a_kind_off_the_vocabulary_or_at_the_wrong_anchor_kind_is_rejected_by_its_rule(seed, kind, anchor, text, rule):
    record = seed.prove_hints(GOOD + [hint(anchor, kind, text)])
    assert [(r["hint"], r["rule"]) for r in record["hint_check"]["rejections"]] == [(4, rule)]


# --- the syntax tree, not a regex -------------------------------------------------------------------------------

@needs_wp
@pytest.mark.parametrize("anchor, kind, text, rule", [
    (LOOP, "loop_invariant", "loop invariant 0 <= i <= n;\nadmit loop invariant i <= n;", "admit"),
    (GLOBALS, "logic", "logic integer grow(integer x) = grow(x) + 1;", "recursive_definition"),
    (LOOP, "loop_invariant", "loop invariant 0 <= i;\n  // only a note\n  admit\n  // another note\n"
                             "  loop invariant i <= n;", "admit"),
    (BEFORE, "ghost", "ghost a[i] = 0;", "interfering_ghost_code")],
    ids=["admit_inside_invariant", "self_referring_logic", "admit_split_by_lines_and_comments", "ghost_writes_real"])
def test_the_syntax_tree_controls_are_rejected_by_rule(seed, anchor, kind, text, rule):
    record = seed.prove_hints(GOOD + [hint(anchor, kind, text)])
    found = [(r["hint"], r["rule"]) for r in record["hint_check"]["rejections"]]
    assert (4, rule) in found and {h for h, _ in found} == {4}, record["hint_check"]["rejections"]
    assert not record["hint_check"]["reached_wp"]


@needs_wp
def test_a_hint_whose_text_is_not_exactly_its_declared_kind_is_a_kind_mismatch(seed):
    record = seed.prove_hints(GOOD + [hint(BEFORE, "assert", "ghost int swdb_k = 0;"),
                                      hint(GLOBALS, "predicate", "logic integer one = 1;")])
    assert [(r["hint"], r["rule"]) for r in record["hint_check"]["rejections"]] == [(4, "kind_mismatch"),
                                                                                    (5, "kind_mismatch")]


# --- erase-and-diff ---------------------------------------------------------------------------------------------

@needs_wp
@pytest.mark.parametrize("text", ["assert 0 <= i; */ a[i] = v + 1; /*@ assert 0 <= i;",
                                  "assert 0 <= i; */ /* a plain comment */ /*@ assert 0 <= i;",
                                  "assert 0 <= i; *\\\n/ a[i] = v + 1; /*@ assert 0 <= i;"],
                         ids=["code", "comment", "line_splice"])
def test_a_text_that_closes_its_annotation_and_adds_code_is_rejected_by_erase_and_diff(seed, text):
    record = seed.prove_hints(GOOD + [hint(BEFORE, "assert", text)])
    assert [(r["hint"], r["rule"]) for r in record["hint_check"]["rejections"]] == [(4, "erase_and_diff")]
    assert "v + 1" not in report(record, "wp_input").read_text()


# --- the seven WP fact files and the planted bad hints ---------------------------------------------------------

PLANTED = yaml.safe_load((HINTS / "planted_bad_hints.yaml").read_text())["sets"]


def test_every_rule_of_the_check_has_a_planted_bad_hint():
    rules_vocabulary = {e["value"] for e in yaml.safe_load((VOCAB / "proof_hint_rules.yaml").read_text())["values"]}
    planted = {h["expect"] for s in PLANTED for h in s["hints"] if h["expect"]}
    assert planted == rules_vocabulary
    facts = " ".join(h["fact"] for s in PLANTED for h in s["hints"])
    for fact_file in ("q1", "q2", "q3", "q4", "q7"):     # q5 (tactics), q6 (smoke tests): not hint-borne (ticket 36)
        assert fact_file in facts


@needs_wp
@pytest.mark.parametrize("planted", PLANTED, ids=lambda s: s["name"])
def test_each_planted_bad_hint_is_rejected_by_its_rule_and_the_set_never_reaches_wp(seed, planted):
    hints = [hint(h["anchor"], h["kind"], h["text"]) for h in planted["hints"]]
    record = seed.prove_hints(hints, name=planted["name"])
    check = record["hint_check"]
    found = {}
    for rejection in check["rejections"]:
        found.setdefault(rejection["hint"], set()).add(rejection["rule"])
    for index, given in enumerate(planted["hints"]):
        if given["expect"]:
            assert given["expect"] in found.get(index, set()), (given, found.get(index), check["rejections"])
    assert None not in found, check["rejections"]                  # every rejection names its hint
    assert check["verdict"] == "rejected" and not check["reached_wp"]
    assert record["settings"]["hint_count"] == 0
    wp_input = report(record, "wp_input").read_text()
    assert not [h["text"] for h in hints if "/*@ " + h["text"].splitlines()[0] in wp_input]   # no hint reached WP
    assert seed.swdb("validate").returncode == 0


# --- ticket 34's frozen wrapper runs this check ----------------------------------------------------------------

@needs_wp
def test_the_proof_hinting_wrapper_runs_this_check_and_answers_each_rejection_by_rule(tmp_path, monkeypatch):
    import test_proof_hinting as role
    from swdb import proof_hinting
    monkeypatch.delenv("SWDB_FRAMA_C", raising=False)                  # the real Frama-C parses the hints
    check = Path(__file__).resolve().parent.parent / "swdb" / "hint_check.py"
    plan = proof_hinting.wrapper_plan(base=role.LOWERING, method_flags=["-wp", "-wp-cache", "none", "-wp-model", "+real"],
                                      seconds_per_solver=30, check=(check, "check"))
    workspace = proof_hinting.prepare(proof_hinting.Inputs(role.files(), role.candidate(), plan), tmp_path / "prepared",
                                      {"kind": "external_fixture", "emulates": "codex"})
    good = {"anchor": "f.loop1.head", "kind": "loop_invariant", "text": "loop invariant 0 <= i <= n;"}
    bad = {"anchor": "f.entry", "kind": "assert", "text": "admit n >= 0;"}
    calls = [("check_hints", {"hints": [good]}), ("check_hints", {"hints": [good, bad]})]
    process = subprocess.run(                         # as role.mcp_session, with time to queue for the verifier lock
        [sys.executable, "-I", str(proof_hinting.WRAPPER), "--state", str(workspace.folder / "wrapper")],
        input="\n".join(json.dumps({"jsonrpc": "2.0", "id": n, "method": "tools/call",
                                    "params": {"name": t, "arguments": a}}) for n, (t, a) in enumerate(calls)) + "\n",
        capture_output=True, text=True, timeout=3600)
    texts = [json.loads(line)["result"]["content"][0]["text"] for line in process.stdout.splitlines()]
    assert texts[0].startswith("Proof hint check passed."), process.stderr
    assert "FAILED" in texts[1] and "hint 1: rule admit" in texts[1] and "never a verdict" in texts[1]


# --- WP only, and versions on every result ---------------------------------------------------------------------

@needs_wp
def test_a_hint_set_on_a_bounded_verifier_job_is_refused(seed, tmp_path):
    path = tmp_path / "hints.yaml"
    path.write_text(yaml.safe_dump({"hints": GOOD}))
    script = tmp_path / "proven.yaml"
    script.write_text(yaml.safe_dump({"verdict": "proven", "bounds": {"threads": 1}, "assumptions": []}))
    result = seed.swdb("prove", "--candidate", seed.candidates["safe"], "--function", "swdb_fixture_fill",
                       "--contract", FILL, "--adapter", "scripted", "--script", script, "--runs-dir", seed.runs,
                       "--hint-file", path)
    assert result.returncode != 0 and "only to the WP adapter" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


@needs_wp
def test_each_check_result_names_the_check_version_and_the_vocabulary_version(seed):
    vocabulary = hashlib.sha256(b"".join((VOCAB / name).read_bytes()
                                         for name in ("proof_hint_kinds.yaml", "proof_hint_rules.yaml"))).hexdigest()
    for record in (seed.prove_hints(GOOD, name="good"),
                   seed.prove_hints(GOOD + [hint(BEFORE, "check", "check 0 <= i;")], name="bad")):
        check = record["hint_check"]
        assert check["check"]["id"] == "proof-hint-check-1" and len(check["check"]["sha256"]) == 64
        assert check["vocabulary"] == {"id": "proof-hint-vocabulary-1", "sha256": vocabulary}

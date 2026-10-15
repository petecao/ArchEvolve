# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# Seams: (a) the edit rules and edit application, (b) the frame seed generator on the stand-in,
# (c) the narrow strategy vocabulary.
import edit_core as E
import frame_seeds as FS
import hints as H
import loop as L

BEST = {"hints": [{"id": "seed1", "anchor": "loop:k_loop", "kind": "loop_assigns", "text": "loop assigns k;"},
                  {"id": "r1c1h1", "anchor": "stmt:entry", "kind": "assert", "text": "assert num_nodes >= 0;"}],
        "failing_goals": [{"goal": "typed_TDStep_ensures_queue_kept"}], "n_open": 1}
ALLOWED = set(H.KINDS) - {"loop_assigns"}


def op(o, goal="typed_TDStep_ensures_queue_kept", hid="", anchor="", kind="", text=""):
    return {"op": o, "goal": goal, "id": hid, "anchor": anchor, "kind": kind, "text": text}


def test_edit_rules_tie_each_operation_to_an_open_goal_and_keep_seeds_fixed():
    rules = lambda ops: {p[1] for p in E.validate(ops, BEST, ALLOWED)}  # noqa: E731
    assert rules([op("add", anchor="stmt:entry", kind="assert", text="assert 1;")]) == set()
    assert "goal_not_open" in rules([op("add", goal="typed_TDStep_assigns", anchor="stmt:entry", kind="assert")])
    assert "seed_fixed" in rules([op("delete", hid="seed1")])
    assert "kind_not_allowed" in rules([op("add", anchor="loop:k_loop", kind="loop_assigns", text="loop assigns k;")])
    assert "edit_too_large" in rules([op("delete", hid="r1c1h1")] * (E.MAX_OPS + 1))
    assert "empty_edit" in rules([])


def test_apply_replaces_edited_hints_and_keeps_the_rest():
    hs = E.apply([op("edit", hid="r1c1h1", text="assert num_edges >= 0;"),
                  op("add", anchor="global", kind="lemma", text="lemma l: \\true;")], BEST, "r2c1", "codex")
    assert [h["id"] for h in hs] == ["seed1", "r2c1h1", "r2c1h2"]
    assert hs[1]["text"] == "assert num_edges >= 0;" and BEST["hints"][1]["text"] == "assert num_nodes >= 0;"


def test_frame_seeds_cover_every_loop_and_widen_varying_ranges_to_the_function_frame():
    seeds = FS.seeds(L.STANDIN_DIR / L.UNIT)
    by = {s["anchor"]: s["text"] for s in seeds}
    assert set(by) == {"loop:chunk_loop", "loop:range_loop", "loop:k_loop", "loop:i_loop", "loop:j_loop"}
    assert by["loop:k_loop"].startswith("loop assigns k, parent->start_[0 .. num_nodes - 1]")
    assert "queue->shared[\\at(queue->shared_in, Pre) .. 36893488147419103231]" in by["loop:j_loop"]
    assert "dxc_reg[c.reg[0]]" in by["loop:chunk_loop"] and "dxc_reg[c.reg[0]]" not in by["loop:range_loop"]
    assert not H.check((L.STANDIN_DIR / L.UNIT).read_text(), seeds)


def test_strategy_vocabulary_allows_wp_tactics_only_and_no_time_argument():
    s1 = {"id": "s1", "anchor": "global", "kind": "strategy",
          "text": '\\wp::strategy P: \\prover("alt-ergo", "z3");'}
    s2 = {"id": "s2", "anchor": "global", "kind": "strategy",
          "text": '\\wp::strategy F: \\tactic("Wp.filter", \\children(P));'}
    att = {"id": "s3", "anchor": "global", "kind": "proof", "text": '\\wp::proof F: "@assigns", inv1;'}
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    assert H.check(standin, [s1, s2, att]) == []
    bad = lambda h, extra=(): {b["rule"] for b in H.check(standin, [s1, s2, *extra, h])}  # noqa: E731
    assert "strategy_prover_timeout" in bad({**s1, "id": "x", "text": '\\wp::strategy Q: \\prover("z3", 300);'})
    assert "strategy_word" in bad({**s1, "id": "x", "text": '\\wp::strategy Q: \\auto("wp:split");'})
    assert "strategy_tactic" in bad({**s1, "id": "x", "text": '\\wp::strategy Q: \\tactic("Wp.absurd");'})
    assert "proof_smoke" in bad({**att, "text": '\\wp::proof F: "smoke";'})
    assert "proof_unknown_strategy" in bad({**att, "text": '\\wp::proof G: "@assigns";'})
    assert "banned_token" in bad({**att, "text": '\\wp::proof F: admit;'})


def test_verdict_reader_skips_strategy_directives_but_not_other_untried_properties():
    props = H.read_report('[    -    ] strategy ("tdstep_standin.c", line 24)\n'
                          '[    -    ] proof ("tdstep_standin.c", line 26)\n'
                          '[    -    ] Assertion \'a\' (file tdstep_standin.c, line 90)\n')
    assert [p["property"][:9] for p in H.verdict_problems(props, set())] == ["Assertion"]


def test_unit_first_counts_seed_frames_as_unit_goals_and_agent_hints_as_hint_goals():
    fails = [{"goal": "typed_TDStep_ensures_a", "hint_ids": []},
             {"goal": "typed_TDStep_loop_assigns_3_part04", "hint_ids": ["seed3"]},
             {"goal": "typed_TDStep_loop_invariant_x_preserved", "hint_ids": ["seed3", "r1c4h3"]},
             {"goal": "typed_lemma_l", "hint_ids": []}]
    assert E.split_counts(fails) == (2, 2)

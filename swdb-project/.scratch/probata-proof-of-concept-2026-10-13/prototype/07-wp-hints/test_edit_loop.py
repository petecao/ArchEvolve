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


# t07e (continuation 3, 2026-10-14 ET)
def test_seed_loop_assigns_merged_with_agent_invariants_stays_a_unit_goal():
    fails = [{"goal": "typed_TDStep_loop_assigns_3_part11", "kind": "loop assigns",
              "hint_ids": ["seed3", "r1c5h3", "r1c7h3"]},
             {"goal": "typed_TDStep_loop_invariant_k_ready_established", "hint_ids": ["seed3", "r1c5h3"]},
             {"goal": "typed_TDStep_assert_td_final_idle", "hint_ids": ["r2fh1"]}]
    assert E.split_counts(fails) == (1, 2)


def test_two_phase_acceptance_keeps_unit_goals_at_zero_and_hint_goals_monotone():
    unit = {"goal": "typed_TDStep_ensures_a", "hint_ids": []}
    h1 = {"goal": "typed_TDStep_assert_a", "hint_ids": ["r1c1h1"]}
    h2 = {"goal": "typed_TDStep_assert_b", "hint_ids": ["r1c1h2"]}
    E.ACCEPT[0], E.CAP[0] = "unit-first", 30
    try:
        E.TWO_PHASE[0] = True
        assert E.decide([h1, h2], 2, [h1])[0]                 # phase 2: hint goals fall
        assert E.decide([h1, h2], 2, [h2, h1])[0]             # phase 2: neutral edit kept
        assert not E.decide([h1], 1, [h1, h2])[0]             # phase 2: hint goals rise
        assert not E.decide([h1, h2], 2, [unit])[0]           # phase 2: a unit goal reopens
        assert E.decide([unit, h1], 2, [h1, h2])[0]           # phase 1 still unit-first
        assert E.phase_of({"failing_goals": [h1], "n_open": 1}) == 2
        assert E.phase_of({"failing_goals": [unit, h1], "n_open": 2}) == 1
        E.TWO_PHASE[0] = False
        # Finding: at 0 unit goals, unit-first already is this monotone rule; (b) changes the phase signal.
        for old, new in [([h1, h2], [h1]), ([h1], [h1, h2]), ([h1, h2], [unit])]:
            E.TWO_PHASE[0] = True
            on = E.decide(old, len(old), new)[0]
            E.TWO_PHASE[0] = False
            assert E.decide(old, len(old), new)[0] == on
        assert E.phase_of({"failing_goals": [h1], "n_open": 1}) == 1
    finally:
        E.TWO_PHASE[0], E.ACCEPT[0], E.CAP[0] = False, "total", E.HINT_OPEN_CAP


def test_live_lock_wait_counts_the_wait_in_progress(tmp_path):
    import time
    import edit_loop as EL
    assert EL.live_lock_wait(tmp_path) == 0.0
    (tmp_path / "lockwait_live.json").write_text('{"settled_s": 30.0, "pending_since": %f}' % (time.time() - 100))
    assert 129 < EL.live_lock_wait(tmp_path) < 140
    (tmp_path / "lockwait_live.json").write_text('{"settled_s": 30.0, "pending_since": null}')
    assert EL.live_lock_wait(tmp_path) == 30.0


def test_goal_print_picks_the_goal_block_by_line_part_and_kind():
    import goal_print as G
    text = ("[wp] Running WP plugin...\n"
            "Goal Preservation of Invariant 'k_ready' (file tdstep_standin.c, line 172):\n"
            "tdstep_standin.c:81: warning from Typed Model:\n - Warning: Hide sub-term definition\n"
            "   Reason: Cast with incompatible pointers types (source: sint32*) (target: sint8*)\n"
            "Assume { Have: P. }\nProve: Q.\n" + "-" * 60 + "\n"
            "Goal Establishment of Invariant 'k_ready' (file tdstep_standin.c, line 172):\nProve: R.\n" + "-" * 60 + "\n"
            "Goal Loop assigns (\"tdstep_standin.c\", line 174) (11/16):\nProve: S.\n" + "-" * 60 + "\n"
            "Goal Loop assigns (\"tdstep_standin.c\", line 174) (12/16):\nProve: T.\n" + "-" * 60 + "\n")
    bl = G.blocks(text)
    assert len(bl) == 4 and "warning" not in bl[0][1]
    pre = G.pick(bl, {"goal": "typed_TDStep_loop_invariant_k_ready_preserved", "line": 172})
    assert [b[1] for b in pre] == ["Assume { Have: P. }\nProve: Q."]
    est = G.pick(bl, {"goal": "typed_TDStep_loop_invariant_k_ready_established", "line": 172})
    assert [b[1] for b in est] == ["Prove: R."]
    part = G.pick(bl, {"goal": "typed_TDStep_loop_assigns_3_part11", "line": 174})
    assert [b[1] for b in part] == ["Prove: S."]
    call = ("Goal Instance of 'Pre-condition (\"dxc_summaries.h\", line %d) in '__dxc_gather'' in 'TDStep' at call "
            "'__dxc_gather' (\"tdstep_standin.c\", line 157)\n:\nProve: %s.\n" + "-" * 60 + "\n")
    bl2 = G.blocks("".join(call % (n, p) for n, p in [(97, "A"), (98, "B"), (99, "C")]))
    got = G.pick(bl2, {"goal": "typed_TDStep_call___dxc_gather_5_dxc_gather_requires_3", "line": 157})
    assert [b[1] for b in got] == ["Prove: C."]
    asg = "Goal Assigns (\"tdstep_standin.c\", line 61) in 'TDStep' (%d/%d):\nProve: %s.\n" + "-" * 60 + "\n"
    bl3 = G.blocks(asg % (2, 2, "N") + asg % (2, 5, "E2") + asg % (5, 5, "E5"))
    assert [b[1] for b in G.pick(bl3, {"goal": "typed_TDStep_assigns_normal_part2", "line": 61})] == ["Prove: N."]
    assert [b[1] for b in G.pick(bl3, {"goal": "typed_TDStep_assigns_exit_part2", "line": 61})] == ["Prove: E2."]
    assert G.selection("typed_lemma_l1", "lemma") == "-wp-prop=l1"
    assert G.selection("typed_TDStep_assigns_exit_part53", "assigns") == "-wp-fct TDStep -wp-prop=@assigns"

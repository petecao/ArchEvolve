# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Updated 2026-10-15 ET: fail-closed ghost-witness ownership guard.
# Seams: merge/erase of hint records, the proof hint check, and the verdict reader.
import pytest

import hints as H

STANDIN = """int f(int n) {
  /* @anchor stmt:entry */
  int s = 0;
  /* @anchor loop:l */
  for (int i = 0; i < n; ++i) {
    s += 1;
  }
  return s;
}
/* @anchor global */
"""


def rec(anchor, kind, text, hid="h1"):
    return {"id": hid, "anchor": anchor, "kind": kind, "text": text}


def test_merge_then_erase_gives_back_the_standin():
    hs = [rec("loop:l", "loop_invariant", "loop invariant 0 <= i <= n;", "h1"),
          rec("loop:l", "loop_assigns", "loop assigns i, s;", "h2"),
          rec("stmt:entry", "assert", "assert n == n;", "h3"),
          rec("global", "predicate", "predicate pos(integer x) = x > 0;", "h4")]
    merged = H.merge(STANDIN, hs)
    assert merged != STANDIN
    assert "/*@ loop invariant 0 <= i <= n;\n      loop assigns i, s; */" in merged  # one block
    assert "/*@ assert n == n; */" in merged
    assert H.erase(merged) == STANDIN


def test_loop_hints_sit_directly_before_the_loop():
    merged = H.merge(STANDIN, [rec("loop:l", "loop_variant", "loop variant n - i;")])
    lines = merged.splitlines()
    k = next(i for i, ln in enumerate(lines) if ln.strip().startswith("for ("))
    assert lines[k - 1].strip() == "// <<< hint"
    assert "loop variant n - i;" in lines[k - 2]


def test_frama_c_error_lines_are_blamed_on_their_hint():
    hs = [rec("stmt:entry", "assert", "assert n == n;", "h3"),
          rec("loop:l", "loop_invariant", "loop invariant 0 <= i <= n;", "h1")]
    merged = H.merge(STANDIN, hs)
    lines = merged.splitlines()
    ln = next(i for i, x in enumerate(lines, 1) if "loop invariant" in x)
    log = f'[kernel:annot-error] tdstep_standin.c:{ln}: Failure: \n  unbound logic variable x.\n'
    blamed = H.blame(merged, log)
    assert [b["ids"] for b in blamed] == [["h1"]]
    assert "loop invariant 0 <= i <= n;" in blamed[0]["line"]


def test_wp_errors_at_a_loop_are_blamed_on_its_loop_annotation():
    hs = [rec("loop:l", "loop_assigns", "loop assigns s, i;", "h2")]
    merged = H.merge(STANDIN, hs)
    ln = next(i for i, x in enumerate(merged.splitlines(), 1) if x.strip().startswith("for ("))
    blamed = H.blame(merged, f"[wp] tdstep_standin.c:{ln}: User Error: \n  Invalid infinite range\n")
    assert [b["ids"] for b in blamed] == [["h2"]]


def test_check_accepts_allowed_kinds():
    hs = [rec("loop:l", "loop_invariant", "loop invariant 0 <= i <= n;"),
          rec("global", "lemma", "lemma l1: \\forall integer x; x + 0 == x;", "h2"),
          rec("stmt:entry", "ghost", "ghost int hint_allowed_scalar = 0;", "h3"),
          rec("global", "logic", "logic integer sq(integer x) = x * x;", "h4")]
    assert H.check(STANDIN, hs) == []


def reasons(hs):
    return [r["rule"] for r in H.check(STANDIN, hs)]


def test_check_rejects_escape_hatches():
    assert "banned_token" in reasons([rec("stmt:entry", "assert", "admit n > 0;")])
    assert "banned_token" in reasons([rec("global", "lemma", "axiom a: \\false;")])
    assert "banned_token" in reasons([rec("global", "predicate", "inductive p(integer x) { case c: p(0); }")])
    assert "banned_token" in reasons([rec("loop:l", "loop_invariant", "loop invariant x; requires \\false;")])
    assert "banned_token" in reasons([rec("loop:l", "loop_variant", "loop variant n - i for R;")])
    assert "banned_token" in reasons([rec("stmt:entry", "assert", "assert \\true; */ int x; /*@ assert \\true;")])
    assert "recursive_definition" in reasons([rec("global", "logic", "logic integer f(integer x) = x <= 0 ? 0 : f(x - 1);")])
    assert "ghost_function" in reasons([rec("global", "ghost", "ghost int gf(int x) { return x; }")])
    assert "unknown_anchor" in reasons([rec("loop:nope", "loop_invariant", "loop invariant \\true;")])
    assert "kind_not_allowed" in reasons([rec("stmt:entry", "requires", "requires n > 0;")])
    assert "kind_text_mismatch" in reasons([rec("stmt:entry", "assert", "loop invariant \\true;")])
    assert "anchor_kind_mismatch" in reasons([rec("stmt:entry", "loop_invariant", "loop invariant \\true;")])


REPORT = """--- Properties of Function 'f'
--------------------------------------------------------------------------------

[  Valid  ] Post-condition 'p1'
            by Wp.typed (v1).
[ Partial ] Post-condition 'p2'
            By Wp.typed (v1), with pending:
             - Assertion 'a'
[    -    ] Assertion 'a'
            tried with Wp.typed (v1).
[ Extern  ] Post-condition (file dxc_summaries.h, line 9)
            Unverifiable but considered Valid.
[ Extern  ] Post-condition (file tdstep_standin.c, line 3)
            Unverifiable but considered Valid.
[  Alarm  ] Pre-condition 'x'
            By Wp.typed (v1), with pending:
             - Unreachable f
--------------------------------------------------------------------------------
--- Status Report Summary
"""


def test_report_reader_flags_everything_but_valid_and_allowed_extern():
    props = H.read_report(REPORT)
    assert [p["status"] for p in props] == ["Valid", "Partial", "-", "Extern", "Extern", "Alarm"]
    bad = H.verdict_problems(props, extern_ok_files={"dxc_summaries.h"})
    kinds = sorted(b["status"] for b in bad)
    assert kinds == ["-", "Alarm", "Extern", "Partial"]


def test_extern_without_a_file_is_judged_by_its_function():
    rep = """--- Properties of Function '__dxc_wait'
--------------------------------------------------------------------------------

[ Extern  ] Assigns nothing
            Unverifiable but considered Valid.
--------------------------------------------------------------------------------
--- Properties of Function 'helper'
--------------------------------------------------------------------------------

[ Extern  ] Assigns nothing
            Unverifiable but considered Valid.
"""
    props = H.read_report(rep)
    assert [p["function"] for p in props] == ["__dxc_wait", "helper"]
    bad = H.verdict_problems(props, extern_ok_files=set(), extern_ok_functions={"__dxc_wait"})
    assert [b["function"] for b in bad] == ["helper"]


def test_summary_functions_are_the_bodyless_declarations():
    header = "/*@ assigns \\nothing; */\nvoid __dxc_wait(int tile);\nint f(int x) { return x; }\n"
    assert H.bodyless_functions(header) == {"__dxc_wait"}


def test_report_reader_passes_a_clean_report():
    clean = "[  Valid  ] Post-condition 'p1'\n            by Wp.typed (v1).\n"
    assert H.verdict_problems(H.read_report(clean), extern_ok_files=set()) == []


def test_failing_goals_get_their_line_and_hint():
    hs = [rec("loop:l", "loop_invariant", "loop invariant 0 <= i <= n;", "h1"),
          rec("stmt:entry", "assert", "assert n == n;", "h3")]
    merged = H.merge(STANDIN, hs)
    lines = merged.splitlines()
    inv = next(i for i, x in enumerate(lines, 1) if "loop invariant" in x)
    asr = next(i for i, x in enumerate(lines, 1) if "assert n == n" in x)
    code = next(i for i, x in enumerate(lines, 1) if "s += 1" in x)
    head = next(i for i, x in enumerate(lines, 1) if x.strip().startswith("for ("))
    goals = [{"goal": "typed_f_loop_invariant_preserved", "file": "/x/tdstep_standin.c", "line": inv, "verdict": "timeout"},
             {"goal": "typed_f_assert", "file": "/x/tdstep_standin.c", "line": asr, "verdict": "timeout"},
             {"goal": "typed_f_call_g_requires", "file": "tdstep_standin.c", "line": code, "verdict": "unknown"},
             {"goal": "typed_f_loop_assigns_part02", "file": "tdstep_standin.c", "line": head, "verdict": "timeout"},
             {"goal": "typed_f_ensures", "file": "tdstep_standin.c", "line": 1, "verdict": "valid", "passed": True},
             {"goal": "typed_f_wp_smoke_x", "smoke": True, "passed": False, "line": 1}]
    pos = H.goal_positions(goals, merged, unit="tdstep_standin.c")
    assert [p["hint_ids"] for p in pos] == [["h1"], ["h3"], [], ["h1"]]
    assert pos[2]["source"] == "s += 1;" and pos[2]["kind"] == "call-site precondition"
    assert pos[0]["kind"] == "loop invariant preserved" and pos[3]["kind"] == "loop assigns"


def test_smoke_goals_must_fail_to_prove():
    goals = [{"goal": "typed_f_wp_smoke_dead_code_s3", "smoke": True, "verdict": "valid", "passed": False},
             {"goal": "typed_f_wp_smoke_default_requires", "smoke": True, "verdict": "timeout", "passed": True},
             {"goal": "typed_f_ensures", "smoke": False, "verdict": "valid", "passed": True}]
    assert [g["goal"] for g in H.smoke_failures(goals)] == ["typed_f_wp_smoke_dead_code_s3"]


# 2026-10-15 ET: hints must not mutate the model they are meant to help prove.
@pytest.mark.parametrize("text", [
    "ghost dxc_pending[0] = 0;",
    "ghost dxc_dep[0] = 0;",
    "ghost dxc_reg[0] = 0;",
    "ghost dxc_tile_len[0] = 0;",
    "ghost int dxc_pending = 0;",
    "ghost int dxc_dep = 0;",
    "ghost int swdb_lqueue_storage = 0;",
    "ghost int bfs_distinct_blocks = 0;",
    "ghost int hint_address = &dxc_pending[0];",
    "ghost int *hint_alias = dxc_pending; *hint_alias = 0;",
    "ghost int hint_call = reset_model();",
    "ghost dx_store_bound = 0;",
    "ghost int hint_macro = DXC_NUM_TILES;",
])
def test_public_hint_check_rejects_trusted_state_writes_and_aliases(text):
    bad = H.check(STANDIN, [rec("stmt:entry", "ghost", text)])
    assert any(b["rule"] == "ghost_ownership" and b["id"] == "h1" for b in bad)


def test_public_hint_check_rejects_ghost_statement_hidden_in_an_assert_hint():
    bad = H.check(STANDIN, [rec("stmt:entry", "assert",
                               "assert 1; ghost dxc_pending[0] = 0;")])
    assert any(b["rule"] == "ghost_ownership" for b in bad)


def test_public_hint_check_preserves_fresh_scalar_witnesses_across_records():
    hs = [rec("stmt:entry", "ghost", "ghost int hint_fresh_scalar = 0;", "w1"),
          rec("stmt:entry", "ghost", "ghost hint_fresh_scalar = n + 1;", "w2")]
    assert H.check(STANDIN, hs) == []
    assert H.erase(H.merge(STANDIN, hs)) == STANDIN


def test_public_hint_check_rejects_duplicate_witness_declarations():
    hs = [rec("stmt:entry", "ghost", "ghost int hint_fresh_scalar = 0;", "w1"),
          rec("stmt:entry", "ghost", "ghost int hint_fresh_scalar = 1;", "w2")]
    assert any(b["rule"] == "ghost_ownership" and b["id"] == "w2"
               for b in H.check(STANDIN, hs))


def test_public_hint_check_preserves_pure_indexed_scalar_snapshots():
    standin = (H.HERE / "standin" / "tdstep_standin.c").read_text()
    hs = [rec("stmt:entry", "ghost", "ghost int hint_old_i = dxc_reg[c.reg[4]];", "i"),
          rec("stmt:entry", "ghost", "ghost int hint_old_j = dxc_reg[c.reg[5]];", "j")]
    assert H.check(standin, hs) == []
    attack = rec("stmt:entry", "ghost",
                 "ghost int hint_reset = dxc_reg[c.reg[4] = 0];", "bad")
    assert any(b["rule"] == "ghost_ownership" for b in H.check(standin, [attack]))


def test_public_hint_check_rejects_indexed_function_pointer_call():
    hs = [rec("stmt:entry", "ghost", "ghost int hint_call = callbacks[0](0);")]
    assert any(b["rule"] == "ghost_ownership" for b in H.check(STANDIN, hs))


def test_strategy_quoted_ghost_word_does_not_become_a_ghost_statement():
    hs = [rec("global", "strategy",
              r'\wp::strategy G: \tactic("Wp.filter", \param("ghost"));')]
    assert H.check(STANDIN, hs) == []


@pytest.mark.parametrize("expression", [
    "(dxc_pending[0] <<= 1)", "(dxc_pending[0] >>= 31)",
    "(n <<= 1)", "(n >>= 1)",
])
def test_ghost_rhs_shift_assignments_cannot_mutate_base_state(expression):
    hs = [rec("stmt:entry", "ghost", f"ghost int hint_shift = {expression};")]
    assert any(b["rule"] == "ghost_ownership" for b in H.check(STANDIN, hs))


def test_ghost_rhs_non_strict_comparisons_remain_allowed():
    hs = [rec("stmt:entry", "ghost", "ghost int hint_le = (n <= 1);", "le"),
          rec("stmt:entry", "ghost", "ghost int hint_ge = (n >= 1);", "ge")]
    assert H.check(STANDIN, hs) == []


@pytest.mark.parametrize("expression", [
    "(dx_count >>??/\n= 31)",
    "(dx_count ?? 1)",
])
def test_ghost_rhs_refuses_preprocessing_trigraph_sequences(expression):
    standin = "int dx_count;\n" + STANDIN
    hs = [rec("stmt:entry", "ghost", f"ghost int hint_trigraph = {expression};")]
    assert any(b["rule"] == "ghost_ownership" for b in H.check(standin, hs))


def test_ghost_rhs_comparison_and_ordinary_ternary_remain_allowed():
    hs = [rec("stmt:entry", "ghost", "ghost int hint_choose = (n <= 1 ? 1 : 0);")]
    assert H.check(STANDIN, hs) == []

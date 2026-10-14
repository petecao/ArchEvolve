# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Seams: merge/erase of hint records, the proof hint check, and the verdict reader.
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
          rec("stmt:entry", "ghost", "ghost int g = 0;", "h3"),
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


def test_smoke_goals_must_fail_to_prove():
    goals = [{"goal": "typed_f_wp_smoke_dead_code_s3", "smoke": True, "verdict": "valid", "passed": False},
             {"goal": "typed_f_wp_smoke_default_requires", "smoke": True, "verdict": "timeout", "passed": True},
             {"goal": "typed_f_ensures", "smoke": False, "verdict": "valid", "passed": True}]
    assert [g["goal"] for g in H.smoke_failures(goals)] == ["typed_f_wp_smoke_dead_code_s3"]

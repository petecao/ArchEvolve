#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# Method24 counted run (plan approved by Yan-Ru 2026-10-16 12:46 ET; ticket 07 "Current resume checkpoint"):
#   1. no-hint round on TDStep (timeout ladder) -> the open goals Codex starts from;
#   2. up to 10 rounds, one Codex call each (one resumed session), with the in-call tools of m24_tool.py
#      (falsify_hints, check_hints, prove_hints, show_goal);
#   3. when the best set proves every TDStep goal and lemma in round mode: the fresh full replay final24
#      (all functions, 30 s per prover, -wp-cache none, fresh session, smoke tests) is the only verdict,
#      then the covering-wait negative control with the same hints (negctl24).
# Budget: 60 minutes of wall time from the start, Codex and WP included; only measured waits for the
# machine-wide verifier lock held by other tickets are excluded (recorded). No hints are pre-seeded.
# Usage: m24.py --out <runs dir> [--budget-min 60] [--rounds 10]
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hints as H  # noqa: E402
import loop as L  # noqa: E402

METHOD = "method25"  # method24 plus the parallel round (round24p) and falsifier construct support
LADDER = [3, 10]
# The 10 s rung runs only when few goals stay open: a measured no-hint 10 s rerun took 483 s and closed
# none of 171 goals (s2-ladder, 2026-10-16), while 98% of past Valid proofs took <= 3 s.
SECOND_RUNG_MAX_OPEN = 40
FINAL_RESERVE_MIN = 9.0
NEG_WAIT = "__dxc_wait(c.tile[5]);"

PROMPT = """You are the proof-hint agent of a proof-hint loop (Frama-C 33.0 / WP, provers Alt-Ergo 2.6.4,
Z3 and CVC5, x86_64 machdep). Your only job: write ACSL proof hints so that WP proves every goal of the C
function TDStep below: its `ensures` clauses (the unit postcondition), the generated `check hazard_*`
annotations, every call precondition, termination, and every hint you add. You never edit code or contracts.

Final answer: JSON {{"hints": [{{"anchor", "kind", "text"}}...], "notes": "..."}}, the COMPLETE hint set.
- anchor: one of the `/* @anchor NAME */` names in tdstep_standin.c (e.g. "loop:k_loop", "stmt:entry", "global").
- kind (the allowed vocabulary, nothing else):
  loop_invariant ("loop invariant P;"), loop_assigns ("loop assigns L;"), loop_variant ("loop variant <integer
  term>;"), all three only at "loop:*" anchors (merged into one annotation right before that loop);
  assert ("assert P;") at "stmt:*" anchors; ghost ("ghost <declaration or statement>") at "stmt:*" or "global";
  predicate / logic (NON-recursive definitions) and lemma ("lemma name: P;", proven in the same run) at "global";
  strategy ("\\wp::strategy ...") with its attachment kind proof ("\\wp::proof S: targets;") at "global".
- Rejected (the set is refused): any admit form, axiom, axiomatic, recursive or inductive definitions,
  contracts (requires/ensures/assumes/behavior/terminates/decreases/exits), ghost functions, body-less
  declarations, `loop variant ... for R`, import, \\from, global invariants, volatile, statement contracts,
  `check`, comment delimiters inside text. Ghost code may only declare fresh scalar ghost variables and assign
  them pure expressions (array reads allowed); it may not write the model's ghost state (dxc_*), real memory
  or call functions. Named facts are fine and encouraged ("loop invariant name: P;").
- Each text is inserted as `/*@ <text> */` right after its anchor line.
- Hint text cannot name C locals that are not in scope at the anchor. Labels: Pre, Here, LoopEntry,
  LoopCurrent (inside predicates/lemmas use your own label parameters). `\\at(e, L)` evaluates ALL of e at L,
  including array indices: write `\\let w = b[i]; \\at(a[w], Pre)` when the index comes from the current state. Ghost variables need C types (int, unsigned, size_t); `integer`/`boolean`
  are logic types for predicate/logic/lemma parameters only.

How to work (general proof-engineering method, not specific to this function):
1. Tools (MCP server "probata"; you have no shell and no file access):
   - falsify_hints(hints): seconds. Evaluates every assert, loop invariant, loop variant and loop assigns
     on 2000 small concrete executions. A hint it reports FALSE is false: fix it, never try to prove it.
   - check_hints(hints): seconds. Vocabulary, Frama-C parse/type check, WP goal generation.
   - prove_hints(hints): minutes. falsify + check, then WP on TDStep's goals and your lemmas (3 s per
     prover, then 10 s when at most 40 goals stay open; conjunctions are split into separate goals, so a failing goal
     names the failing part). It keeps the best set so far.
   - show_goal(goal): one open goal of the best set as WP sees it (hypotheses and conclusion).
   Loop: write hints -> falsify_hints until nothing is refuted -> check_hints until clean -> prove_hints ->
   read the open goals -> fix -> repeat. When prove_hints says ALL goals are proven, return that set at once.
2. Invariants: for each loop, state what the iterations so far have done as a relation between the current
   state and Pre (a processed prefix or a lexicographic cursor), plus the bounds and frame facts later
   statements need. One fact per named invariant. Define a non-recursive predicate once for a shape that
   several loops share, and use the same predicate in every loop, so the loops' invariants compose.
3. Loop assigns: list every location the loop body (and its inner loops and calls) may write, including the
   loop index, locals declared outside the loop, and the model's ghost state. falsify_hints checks frames.
4. Variants: an integer measure that is >= 0 whenever the body is entered and strictly decreases per
   iteration; for a cursor over pairs, combine the two parts into one integer.
5. Contexts: every assertion and invariant above a goal is one of its hypotheses, and every global lemma
   is a hypothesis of every goal. Keep hypotheses small near simple goals; use a lemma only when several
   goals need the same non-trivial step. A goal that WP proved with no hints and fails now fails because of
   the context your hints add.
6. Unproven assertions still act as hypotheses for later goals, so a set can prove the postcondition "under"
   a false or unproven assertion; such a set never passes. Close your own hints too.

Budget: {budget} minutes of wall time for the whole run, WP and your calls included; {reserve} minutes are kept
for the final replay. Minutes used so far: {minutes:.1f}. Round {round} of at most {rounds}.

{feedback}

=== Workspace (read only) ===
{files}
"""


def now_s():
    return time.time()


def write(p, obj):
    Path(p).write_text(json.dumps(obj, indent=1))


def baseline(out):
    """No-hint round with the same ladder as the tool (counted)."""
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    d = L.run_dir(out, "baseline", standin)
    runs, ar = [], None
    for k, tmo in enumerate(LADDER):
        if k and len(ar["failing_goals"]) > SECOND_RUNG_MAX_OPEN:
            break
        wlog, ws = L.verifier(out, d, "round24p", timeout=1200, extra=(out / "round-cache", tmo))
        if ws["exit_code"] != 0:
            raise RuntimeError(f"baseline WP failed: {wlog}")
        ar = L.assess_round(d, wlog)
        runs.append({"timeout_s": tmo, "wall_s": ws["wall_s"], "open": len(ar["failing_goals"]), "n_goals": ar["n_goals"]})
    return d, ar, runs


def feedback_baseline(ar):
    return ("No hints yet. WP without hints (round mode, 3 s then 10 s per prover) leaves these goals open "
            f"({len(ar['failing_goals'])} of {ar['n_goals']}): goal [failure class] kind at file:line: source line\n"
            + L.positions_text(ar["failing_goals"], []))


def submissions(state):
    f = state / "submissions.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def negctl_source(merged):
    """The covering-wait negative control: the same merged file with the wait covering the hints tile removed."""
    assert merged.count(NEG_WAIT) == 1, "negative-control wait not unique"
    return merged.replace(NEG_WAIT, "/* negative control: covering wait removed */")


def final_replay(out, best, tag):
    merged = H.merge((L.STANDIN_DIR / L.UNIT).read_text(), best["hints"])
    d = L.run_dir(out, f"final-{tag}", merged)
    wlog, ws = L.verifier(out, d, "final24", timeout=1800)
    a = L.assess(d, wlog)
    res = {"dir": str(d), "wall_s": ws["wall_s"], "exit": ws["exit_code"], "peak_rss_mb": ws["peak_rss_mb"],
           "log_sha256": ws["log_sha256"], "ok": bool(a["ok"] and ws["exit_code"] == 0), "n_goals": a["n_goals"],
           "failing": a["failing_goals"], "problems": a["problems"], "smoke_failures": a["smoke_failures"],
           "goals_sha256": L.sha(d / "goals.json") if (d / "goals.json").exists() else None,
           "merged_sha256": L.sha(d / L.UNIT)}
    return res


def negative_control(out, best, tag):
    """Same hints, covering wait removed. Pass: the hazard check's consolidated report status is not Valid
    and nothing is refuted (no Bug/Alarm/Invalid status, no `invalid` goal verdict), in a healthy run (exit 0,
    hazard goals present with a timeout/unknown verdict or Valid only under unproven hypotheses, and at least
    one other goal proven by a real prover)."""
    merged = H.merge((L.STANDIN_DIR / L.UNIT).read_text(), best["hints"])
    d = L.run_dir(out, f"negctl-{tag}", negctl_source(merged))
    wlog, ws = L.verifier(out, d, "negctl24", timeout=900)
    text = wlog.read_text(errors="replace")
    rep = text[text.find("[report] Computing properties status"):] if "[report]" in text else ""
    props = H.read_report(rep)
    hazard = [p for p in props if "hazard_hints_read" in p["property"]]
    goals = json.loads((d / "goals.json").read_text()) if (d / "goals.json").exists() else []
    hz_goals = [g for g in goals if "hazard_hints_read" in str(g.get("property", "")) + str(g.get("goal", ""))]
    refuted = any(p["status"] in ("Bug", "Alarm", "Invalid") for p in hazard) or \
        any(g.get("verdict") == "invalid" for g in goals)
    not_valid = bool(hazard) and all(p["status"] != "Valid" for p in hazard)
    healthy = (ws["exit_code"] == 0 and bool(hz_goals) and
               all(g.get("passed") or g.get("verdict") in ("timeout", "unknown", "stepout") for g in hz_goals) and
               any(g.get("passed") and any(p.get("success") and p.get("prover") != "qed" for p in g.get("provers", []))
                   for g in goals if g not in hz_goals))
    return {"dir": str(d), "wall_s": ws["wall_s"], "exit": ws["exit_code"], "hazard_report": hazard,
            "hazard_goals": [{k: g.get(k) for k in ("goal", "verdict", "passed")} for g in hz_goals],
            "refuted": refuted, "not_valid": not_valid, "healthy": healthy,
            "ok": not_valid and not refuted and healthy, "log_sha256": ws["log_sha256"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--budget-min", type=float, default=60.0)
    ap.add_argument("--rounds", type=int, default=10)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"refusing: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    L.OWNER[0] = "t07f"
    t0 = now_s()
    meta = {"method": METHOD, "start": L.now(), "budget_min": a.budget_min, "rounds_max": a.rounds,
            "ladder_s": LADDER, "second_rung_max_open": SECOND_RUNG_MAX_OPEN, "final_reserve_min": FINAL_RESERVE_MIN, "pin": L.PIN,
            "codex_version": subprocess.run([L.CODEX, "--version"], capture_output=True, text=True).stdout.strip(),
            "inputs": {p.name: L.sha(p) for p in sorted(L.STANDIN_DIR.iterdir()) if p.is_file()},
            "scripts": {n: L.sha(HERE / n) for n in ("m24.py", "m24_tool.py", "hints.py", "loop.py", "wp_run.sh",
                                                     "goal_print.py", "falsify/falsify.py", "falsify/acsl_eval.py",
                                                     "falsify/build.py", "falsify/harness.c", "falsify/instances.py")},
            "git_head": subprocess.run(["git", "-C", str(HERE), "rev-parse", "HEAD"], capture_output=True,
                                       text=True).stdout.strip(),
            "git_dirty": subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "--", "."],
                                        capture_output=True, text=True).stdout.strip(),
            "rounds": [], "calls": 0, "usage": {}}
    write(out / "meta.json", meta)
    used = lambda: (now_s() - t0 - L.LOCKWAIT[0]) / 60  # noqa: E731
    L.log(out, f"{METHOD} start, budget {a.budget_min} min")
    bdir, bar, bruns = baseline(out)
    meta["baseline"] = {"dir": str(bdir), "runs": bruns, "open": len(bar["failing_goals"]),
                        "failing_goals": bar["failing_goals"], "minutes": round(used(), 2)}
    write(out / "meta.json", meta)
    L.log(out, f"baseline: {bruns}")
    state = out / "state"
    state.mkdir()
    feedback = feedback_baseline(bar)
    thread = None
    verdict = None
    for r in range(1, a.rounds + 1):
        left = a.budget_min - FINAL_RESERVE_MIN - used()
        if left <= 1.0:
            break
        write(state / "config.json", {"out": str(out), "t0": t0, "budget_min": a.budget_min,
                                      "final_reserve_min": FINAL_RESERVE_MIN, "round": r, "ladder": LADDER, "second_rung_max_open": SECOND_RUNG_MAX_OPEN,
                                      "lockwait_before_s": L.LOCKWAIT[0], "pin": L.PIN, "owner": "t07f", "method": METHOD})
        files = L.workspace_files((L.STANDIN_DIR / L.UNIT).read_text())
        prompt = PROMPT.format(budget=a.budget_min, reserve=FINAL_RESERVE_MIN, minutes=used(), round=r,
                               rounds=a.rounds, feedback=feedback, files=files) if thread is None else (
            f"Round {r} of at most {a.rounds}; minutes used {used():.1f} of {a.budget_min} ({FINAL_RESERVE_MIN} kept "
            f"for the final replay).\n{feedback}\nContinue with the tools and return your complete best hint set.")
        L.mcp_args = lambda st: ["-c", "mcp_servers.probata.command=" + json.dumps(sys.executable),
                                 "-c", "mcp_servers.probata.args=" + json.dumps(["-I", str(HERE / "m24_tool.py"), "--state", str(st)]),
                                 "-c", "mcp_servers.probata.tool_timeout_sec=3600",
                                 "-c", "mcp_servers.probata.startup_timeout_sec=120"]
        n_before = len(submissions(state))
        lw_before = L.LOCKWAIT[0]
        res = L.codex_call(out, r, prompt, resume=thread, turn=0, keep_session=True, mcp_state=state,
                           deadline_s=max(60, left * 60))
        subs = submissions(state)[n_before:]
        if (state / "server_errors.log").exists():
            L.log(out, "tool server errors:\n" + (state / "server_errors.log").read_text()[-3000:])
        tool_lock = max([s.get("lockwait_total_s", 0) for s in subs] or [0])
        L.LOCKWAIT[0] = lw_before + tool_lock  # waits inside the tool process
        thread = res.get("thread") or thread
        meta["calls"] += 1
        if not res.get("usage"):
            meta["usage_incomplete_rounds"] = meta.get("usage_incomplete_rounds", []) + [r]  # no turn.completed
        for k, v in (res.get("usage") or {}).items():
            meta["usage"][k] = meta["usage"].get(k, 0) + v
        rec = {"round": r, "codex": {k: res.get(k) for k in ("exit", "wall_s", "usage", "error", "killed_at_deadline",
                                                             "thread")},
               "tool_calls": len(subs), "tool_results": [s["result"] for s in subs], "minutes": round(used(), 2)}
        # Only the tool's incumbent (best.json) is used; Codex's final answer is recorded, not proven separately.
        rec["final_answer_hints"] = len(res.get("hints") or [])
        best_f = state / "best.json"
        best = json.loads(best_f.read_text()) if best_f.exists() else None
        rec["best_open"] = best["n_open"] if best else None
        meta["rounds"].append(rec)
        write(out / "meta.json", meta)
        L.log(out, f"round {r}: {rec}")
        if best and best["n_open"] == 0:
            fin = final_replay(out, best, f"r{r}")
            rec["final"] = {k: v for k, v in fin.items() if k not in ("failing",)}
            rec["final"]["n_failing"] = len(fin["failing"])
            L.log(out, f"final replay: ok={fin['ok']} failing={len(fin['failing'])} problems={len(fin['problems'])} "
                       f"smoke={len(fin['smoke_failures'])} wall={fin['wall_s']}")
            if fin["ok"]:
                # The budget is judged when the positive replay ends (review S3); the control follows.
                minutes_at_final = round(used(), 2)
                within = minutes_at_final <= a.budget_min
                neg = negative_control(out, best, f"r{r}")
                rec["negative_control"] = neg
                verdict = {"pass": within and neg["ok"], "within_budget": within, "minutes": minutes_at_final,
                           "minutes_incl_negative_control": round(used(), 2),
                           "final": rec["final"], "negative_control_ok": neg["ok"], "hints": best["hints"]}
                write(out / "meta.json", meta)
                break
            feedback = ("The final replay (all functions, 30 s per prover, smoke tests) did NOT pass:\n"
                        + "\n".join(f"- {g['goal']} [{g['failure_class']}]" for g in fin["failing"][:60])
                        + "".join(f"\n- report property not Valid: [{p['status']}] {p['property']}" for p in fin["problems"][:40])
                        + "".join(f"\n- smoke test proved (dead code or inconsistent hints): {g.get('goal')}" for g in fin["smoke_failures"])
                        + "\nFix these and prove again.")
            os.replace(best_f, state / f"best-final-failed-r{r}.json")
            continue
        open_txt = L.positions_text(best["failing_goals"], best["hints"]) if best else "(no set reached WP)"
        feedback = (f"Your call ended. Best set so far: {best['n_open'] if best else '-'} open goals:\n{open_txt}"
                    if best else "Your call ended without any set reaching WP.")
    meta["end"] = L.log(out, "end") or L.now()
    meta["minutes"] = round(used(), 2)
    meta["excluded_lock_wait_s"] = round(L.LOCKWAIT[0], 2)
    meta["verdict"] = verdict or {"pass": False, "reason": "no qualifying final replay within the budget"}
    write(out / "meta.json", meta)
    print(json.dumps(meta["verdict"] if not verdict else {k: v for k, v in verdict.items() if k != "hints"}, indent=1))


if __name__ == "__main__":
    main()

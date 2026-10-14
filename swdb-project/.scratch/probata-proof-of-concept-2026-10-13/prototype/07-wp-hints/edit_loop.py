#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# The spike's proof-hint loop, version 4, with three method changes (each a flag, recorded in meta.json):
#   (a) --monotone: Codex never returns a whole hint set. Through the in-call tool (edit_tool_mcp.py) it
#       proposes small edits (<= edit_core.MAX_OPS operations, each tied to an open goal) against the best
#       set so far; an edit that raises the open-goal count is reverted.
#   (b) --seeds: before the first Codex call, frame_seeds.py writes every loop's `loop assigns` from the
#       code (syntactic write set + callee assigns); WP checks them in the seed round. Seeds are method, not
#       hints: Codex cannot edit them or add `loop assigns`. --frame-filter adds the generic strategy that
#       proves frame goals on a filtered context (see FRAME_FILTER).
#   (c) --strategies: hints may use `\wp::strategy` + `\wp::proof` (WP tactics such as Wp.filter that
#       prune a goal's hypotheses); WP runs with its strategy engine (wp_run.sh round-s / wp-smoke-s).
# Unchanged from t07/t07c: the stand-in, the pass bar (fresh full replay with the frozen flags decides),
# the 60-minute budget (now counted from the seed round), 10 rounds, Codex pin, Codex confinement (shell
# off, read-only sandbox, workspace inline, MCP tool only), round mode at 10 s per prover.
# t07e (continuation 3, 2026-10-14 ET), each a flag recorded in meta.json "method_changes_t07e":
#   --budget-deadline (a): the Codex call deadline runs on the budget clock (lock waits excluded, published
#       live by the in-call tool), not on the wall clock; a generous wall cap guards a hang.
#   --two-phase (b): once the best set's unit goals reach 0, only edits that keep them at 0 and do not
#       raise the open hint goals are accepted (edit_core.TWO_PHASE); the final replay stays reserved.
#   --show-goal (c1): in-call tool show_goal prints an open goal as WP generates it (goal_print.py).
#   (c2) MCP tool timeout 3600 -> 14400 s, so a tool call queued behind other tickets' verifier jobs
#       does not surface to Codex as an error while the tool keeps running.
# Usage: edit_loop.py --out <dir> --round0-from <earlier counted run with the same stand-in> [flags]
import argparse, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path

import edit_core as E
import frame_seeds as FS
import hints as H
import loop as L

HERE = Path(__file__).resolve().parent
OPS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["ops", "notes"],
              "properties": {"notes": {"type": "string"}, "ops": {"type": "array", "items": E.OP_SCHEMA}}}

# Generic, unit-independent (method, provenance "seed"): every `assigns`/`loop assigns` goal that the
# three provers do not prove on the full context is retried after WP's own Wp.filter tactic.
FRAME_FILTER = [
    ("strategy", "\\wp::strategy SeedFrameProvers: \\prover(\"alt-ergo\", \"z3\", \"cvc5\");"),
    ("strategy", "\\wp::strategy SeedFrameFilter: \\tactic(\"Wp.filter\", \\children(SeedFrameProvers));"),
    ("proof", "\\wp::proof SeedFrameFilter: \"@assigns\";"),
]

PROMPT = """You are the proof-hint agent of a proof-hint loop (Frama-C 33.0 / WP, provers Alt-Ergo 2.6.4, Z3,
CVC5, x86_64 machdep). Your job: add ACSL proof hints so that WP proves every goal of the C function TDStep
below (its `ensures` clauses = the unit postcondition, the generated `check hazard_*` annotations, call-site
preconditions, loop goals, termination, frame goals). You never edit code or contracts.

HOW THIS LOOP WORKS (monotone, local editing):
- The loop keeps ONE best hint set. It starts with mechanically generated frame seeds (ids "seed*": every
  loop's `loop assigns`, written from the code; they are fixed, you cannot change them or add `loop assigns`).
- You change the best set only by EDITS: a list of 1-{max_ops} operations, each
  {{"op": "add"|"delete"|"edit", "goal": <name of an OPEN goal this operation targets>, "id": <hint id for
  delete/edit, else "">, "anchor": <anchor for add, else "">, "kind": <kind for add, else "">, "text": <hint
  text for add/edit, else "">}}. At most {max_text} characters of new text per edit.
- propose_edit runs WP with best set + edit. {accept_rule} Otherwise it is REVERTED and the best set stays.
  So: small, targeted steps; keep what works; never rewrite everything.
- Your final JSON answer {{"ops": [...], "notes": "..."}} is one more edit (use an empty list when you have
  nothing more; when propose_edit says ALL goals proven, answer with an empty list at once).

Hint kinds you may add (nothing else): {kinds}.
- anchor: one of the `/* @anchor NAME */` names in tdstep_standin.c ("loop:k_loop", "stmt:entry", "global", ...).
  loop_invariant ("loop invariant P;" or "loop invariant name: P;"), loop_variant ("loop variant <integer term>;")
  only at "loop:*" anchors (merged with the seed into one annotation right before that loop); assert
  ("assert P;") at "stmt:*" anchors; ghost ("ghost <declaration or statement>") at "stmt:*" or "global";
  predicate / logic (NON-recursive) and lemma ("lemma name: P;", proven in the same run) at "global".
{strategy_notes}
- Rejected (the edit is rejected): any admit form, axiom, axiomatic, recursive or inductive definitions,
  contracts (requires/ensures/assumes/behavior/terminates/decreases/exits), ghost functions, body-less
  declarations, `loop variant ... for R`, import, \\from, global invariants, volatile, statement contracts,
  `check`, comment delimiters inside text. Ghost code may not write real memory or call real functions.
- Hint text cannot use C locals not in scope at the anchor. Labels: Pre, Here, LoopEntry, LoopCurrent, Old.
  Ghost variables need C types; `integer`/`boolean` only as logic parameters. Inside `\\at(e, L)` do not name
  C locals that do not exist at L; pass values to a predicate with label parameters instead.
- An assertion or invariant that is not proven still serves as a hypothesis for later goals, so it can make
  other goals look proven; the final run needs every one of them proven. Every assertion, invariant and lemma
  above a goal is in that goal's context: large quantified contexts make provers time out (a goal marked
  REGRESSION was proven without hints and fails now because of context your hints add). Keep hypotheses small
  and local, state facts directly, put an invariant only on the loop that needs it.
- Round mode: {round_timeout} s per prover per goal, TDStep's goals and your lemmas only, no smoke tests. When
  the best set has 0 open goals, the loop runs ONE fresh full WP run (all functions, 30 s, smoke tests); only
  that run decides.

In-call tools (MCP server "probata"; you have no shell and no file access):
- show_best(): the best set (with ids) and its open goals.
- check_edit(ops): edit rules + proof hint check (vocabulary, anchors, Frama-C parse, WP goal generation). Seconds.
- propose_edit(ops): check, then WP; accept or revert as above. Minutes (fewer open goals run faster; results of
  goals your edit does not touch come from a cache).{tool_notes}
Work in a loop: read the open goals, check_edit, propose_edit, read the result, repeat. In-call budget:
{tool_budget:.0f} min from the start of this call{budget_clock_note}; the tool tells you what is left.

Round {round} of at most {rounds}; minutes used so far: {minutes:.1f} of {budget}.

{best}

{open}
{examples}
=== Workspace (read only) ===
{files}
"""

ACCEPT_RULE = {
    "total": "If the number of open goals does not rise, the edit is ACCEPTED and becomes the best set.",
    "unit-first": ("The edit is ACCEPTED (it becomes the best set) when it lowers the number of open UNIT goals\n"
                   "  (the stand-in's own goals: postcondition, hazard checks, call preconditions, frames, termination),\n"
                   "  or keeps that number and does not raise the total. Open goals of your own hints (invariants,\n"
                   "  asserts, lemmas) may rise while unit goals fall, up to {cap} open hint goals; every hint goal must\n"
                   "  be proven in the end.")}

PHASE2_RULE = ("\n  PHASE 2: once every unit goal is proven, the rule changes: an edit is ACCEPTED only if every unit goal\n"
               "  stays proven and the number of open hint goals does not rise. Then close your own hint goals: add\n"
               "  lemmas, asserts, invariants or strategies that support them, fix them, or delete hints that are not\n"
               "  needed. The tool and the open-goal list say which phase you are in.")

SHOW_GOAL_NOTE = ("\n- show_goal(goal): one open goal as WP generates it after Qed simplification (hypotheses and the\n"
                  "  conclusion), so you can see what is missing. Up to a minute; changes nothing.")

STRATEGY_NOTES = """  strategy / proof (at "global"): WP proof strategies that prune or reshape ONE goal's context, e.g.
    "\\\\wp::strategy MyProvers: \\\\prover(\\"alt-ergo\\", \\"z3\\", \\"cvc5\\");"
    "\\\\wp::strategy MyFilter: \\\\tactic(\\"Wp.filter\\", \\\\children(MyProvers));"   (drops hypotheses unrelated to the goal)
    "\\\\wp::proof MyFilter: name1, \\"@ensures\\";"   (attach: property names of your named asserts/invariants or
    TDStep's named clauses, or "@assigns", "@ensures", "@invariant", "@assert", "@check", "@variant")
  Allowed tactics: {tactics}. \\\\prover takes prover names only (no time argument);
  no \\\\auto; never target "smoke". A strategy runs only after the three provers failed on the full goal.
  Strategy names must be new (the seeds use names starting with "Seed")."""


TOOL_TIMEOUT_S = [3600]
WALL_CAP_S = 5 * 3600  # t07e (a): guard only; the budget clock decides


def live_lock_wait(mcp_state):
    """Lock wait of the in-call tool so far (settled + the wait in progress), read from outside the tool."""
    f = Path(mcp_state) / "lockwait_live.json"
    try:
        j = json.loads(f.read_text())
    except (OSError, ValueError):
        return 0.0
    return j.get("settled_s", 0.0) + (time.time() - j["pending_since"] if j.get("pending_since") else 0.0)


def codex_call(out, r, prompt, resume, mcp_state, deadline_s, budget_stop=None):
    """deadline_s: wall-clock deadline (t07d). budget_stop (t07e a): a function returning True once the
    budget clock (wall time minus every lock wait, including the in-call tool's live one) is spent."""
    d = out / f"codex-r{r}"
    ws = d / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "PROMPT.txt").write_text(prompt)
    (d / "schema.json").write_text(json.dumps(OPS_SCHEMA))
    common = ["--model", L.PIN["model"], "-c", "model_reasoning_effort=" + json.dumps(L.PIN["effort"]),
              "-c", 'web_search="disabled"', "-c", "analytics.enabled=false", "-c", "project_doc_max_bytes=0",
              "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check",
              "-c", "mcp_servers.probata.command=" + json.dumps(sys.executable),
              "-c", "mcp_servers.probata.args=" + json.dumps(["-I", str(HERE / "edit_tool_mcp.py"), "--state", str(mcp_state)]),
              "-c", "mcp_servers.probata.tool_timeout_sec=" + str(TOOL_TIMEOUT_S[0]),
              "-c", "mcp_servers.probata.startup_timeout_sec=60"]
    tail = ["--json", "--output-schema", str(d / "schema.json"), "--output-last-message", str(d / "final.json"),
            "--disable", "shell_tool"]
    for f in L.CODEX_DISABLED_FEATURES:
        tail += ["--disable", f]
    if resume:
        argv = [L.CODEX, "exec", "resume", *common, *tail, resume, "-"]
    else:
        argv = [L.CODEX, "exec", *common, "-s", "read-only", "-C", str(ws), *tail, "-"]
    (d / "argv.json").write_text(json.dumps(argv[:-1]))
    t = time.time()
    killed = False
    with open(d / "stdout.jsonl", "w") as fo, open(d / "stderr.txt", "w") as fe:
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=fo, stderr=fe, text=True, start_new_session=True)
        p.stdin.write(prompt)
        p.stdin.close()
        stop_reason = None
        while True:
            try:
                p.wait(timeout=5)
                break
            except subprocess.TimeoutExpired:
                pass
            if budget_stop is None and time.time() - t > deadline_s:
                stop_reason = "wall-clock deadline"
            elif budget_stop is not None and budget_stop():
                stop_reason = "budget-clock deadline"
            elif time.time() - t > WALL_CAP_S:
                stop_reason = "wall cap"
            if stop_reason:
                break
        if stop_reason:
            killed = True
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
    usage, thread = {}, resume
    for ln in (d / "stdout.jsonl").read_text(errors="replace").splitlines():
        try:
            ev = json.loads(ln)
        except ValueError:
            continue
        if ev.get("type") == "thread.started":
            thread = ev.get("thread_id")
        if ev.get("type") == "turn.completed":
            for k, v in (ev.get("usage") or {}).items():
                usage[k] = usage.get(k, 0) + (v or 0)
    res = {"exit": p.returncode, "wall_s": round(time.time() - t, 1), "usage": usage, "thread": thread,
           "killed_at_deadline": killed, "stop_reason": stop_reason, "ops": None, "notes": None, "error": None}
    try:
        data = json.loads((d / "final.json").read_text())
        res["ops"], res["notes"] = data.get("ops") or [], data.get("notes", "")
    except Exception as e:  # noqa: BLE001
        res["error"] = f"{type(e).__name__}: {e}; stderr tail: " + (d / "stderr.txt").read_text(errors="replace")[-800:]
    return res


def tool_state(out, r, a, t0, mode, allowed):
    state = out / f"tool-r{r}"
    state.mkdir(parents=True, exist_ok=True)
    (state / "config.json").write_text(json.dumps({
        "out": str(out), "owner": L.OWNER[0], "t0": t0, "lockwait_before_s": L.LOCKWAIT[0],
        "budget_min": a.budget_min, "final_reserve_min": a.final_reserve_min, "round_timeout": a.round_timeout,
        "round": r, "pin": L.PIN, "mode": mode, "allowed_kinds": sorted(allowed), "accept": E.ACCEPT[0], "hint_cap": E.CAP[0],
        "baseline_passed": sorted(L.BASELINE_PASSED), "two_phase": E.TWO_PHASE[0], "show_goal": a.show_goal,
        "live_file": str(state / "lockwait_live.json") if a.budget_deadline else None}, indent=1))
    return state


def read_tool(state):
    f = state / "submissions.jsonl"
    subs = [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []
    lw = max((s.get("lockwait_total_s", 0) for s in subs), default=0.0)
    L.LOCKWAIT[0] += lw
    return {"calls": len(subs), "lock_wait_s": lw,
            "check_calls": sum(1 for s in subs if s["tool"] == "check_edit"),
            "propose_calls": sum(1 for s in subs if s["tool"] == "propose_edit"),
            "show_goal_calls": sum(1 for s in subs if s["tool"] == "show_goal"),
            "accepted": sum(1 for s in subs if str(s.get("result", "")).startswith("accepted")),
            "reverted": sum(1 for s in subs if str(s.get("result", "")).startswith("reverted")),
            "rejected": sum(1 for s in subs if "rejected" in str(s.get("result", ""))),
            "trace": [[s["n"], s["tool"], s.get("result"), s.get("n_open_before"), s.get("n_open_after"),
                       s.get("wall_s"), len(s.get("ops") or [])] for s in subs],
            "submissions": str(f)}


def budget_s(t0):
    return time.time() - t0 - L.LOCKWAIT[0]


def final_replay(out, r, best, a, t0, final_mode):
    d = L.run_dir(out, f"final-r{r}", (Path(best["dir"]) / L.UNIT).read_text())
    rec = {}
    L.wp_round(out, f"final-r{r}", (L.STANDIN_DIR / L.UNIT).read_text(), best["hints"], rec, mode=final_mode, d=d,
               timeout=max(60, int(a.budget_min * 60 - budget_s(t0)) + 60))
    gj = d / "goals.json"
    fails = H.goal_positions(json.loads(gj.read_text()), (d / L.UNIT).read_text(), L.UNIT, L.headers_text()) \
        if gj.exists() else None
    return {"dir": str(d), "proven": bool(rec.get("proven")), "outcome": rec.get("outcome"), "wp": rec.get("wp"),
            "n_goals": rec.get("n_goals"), "n_problems": len(rec.get("problems") or []),
            "n_smoke_failures": len(rec.get("smoke_failures") or []), "failing_goals": fails,
            "problems": (rec.get("problems") or [])[:100]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--round0-from", help="reuse the no-hint run of an earlier counted run (same stand-in)")
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--budget-min", type=float, default=60)
    ap.add_argument("--round-timeout", type=int, default=10)
    ap.add_argument("--final-reserve-min", type=float, default=15)
    ap.add_argument("--monotone", action="store_true", help="(a) edits against the best set; regressions reverted")
    ap.add_argument("--seeds", action="store_true", help="(b) mechanical frame seeds before the first Codex call")
    ap.add_argument("--frame-filter", action="store_true", help="(b)+(c) generic Wp.filter strategy seed for frame goals")
    ap.add_argument("--strategies", action="store_true", help="(c) strategy hints; WP strategy engine on")
    ap.add_argument("--examples", action="store_true", help="t07c (b): syntax-checked examples in the prompt")
    ap.add_argument("--accept", default="total", choices=["total", "unit-first"],
                    help="(a') acceptance: total open goals (run 7) or unit goals first (run 8 on)")
    ap.add_argument("--hint-cap", type=int, default=E.HINT_OPEN_CAP, help="unit-first: max open hint goals")
    ap.add_argument("--budget-deadline", action="store_true", help="t07e (a): Codex deadline on the budget clock")
    ap.add_argument("--two-phase", action="store_true", help="t07e (b): hint-goal-only phase once unit goals are 0")
    ap.add_argument("--show-goal", action="store_true", help="t07e (c1): in-call show_goal tool")
    ap.add_argument("--tool-timeout-s", type=int, default=3600, help="t07e (c2): MCP tool timeout")
    ap.add_argument("--owner", default="t07d")
    ap.add_argument("--dev-effort", help="DEV ONLY (never a counted run): override the pinned effort")
    ap.add_argument("--dev-no-codex", action="store_true", help="DEV ONLY: stop after the seed round")
    ap.add_argument("--dev-skip-round0", action="store_true", help="DEV ONLY: no no-hint run (no REGRESSION marks)")
    a = ap.parse_args()
    assert a.monotone, "this loop implements method change (a) only"
    E.ACCEPT[0] = a.accept
    E.CAP[0] = a.hint_cap
    E.TWO_PHASE[0] = a.two_phase
    TOOL_TIMEOUT_S[0] = a.tool_timeout_s
    L.OWNER[0] = a.owner
    if a.dev_effort:
        L.PIN["effort"] = a.dev_effort
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mode = "round-s" if (a.strategies or a.frame_filter) else "round"
    final_mode = "wp-smoke-s" if (a.strategies or a.frame_filter) else "wp-smoke"
    allowed = set(H.KINDS) - {"loop_assigns"} if a.seeds else set(H.KINDS)
    if not a.strategies:
        allowed -= {"strategy", "proof"}
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    files = ["loop.py", "hints.py", "wp_run.sh", "edit_loop.py", "edit_core.py", "edit_tool_mcp.py", "frame_seeds.py",
             "goal_print.py"]
    meta = {"started": L.now(), "pin": L.PIN,
            "codex_version": subprocess.run([L.CODEX, "--version"], capture_output=True, text=True).stdout.strip(),
            "standin_sha256": {f: L.sha(L.STANDIN_DIR / f) for f in [L.UNIT] + L.HEADERS},
            "cpp_unit_sha256": L.sha(L.CPP_UNIT), "rounds": a.rounds, "budget_min": a.budget_min,
            "round_timeout_s": a.round_timeout, "final_reserve_min": a.final_reserve_min,
            "method_changes_t07d": {"monotone": a.monotone, "max_ops": E.MAX_OPS, "max_text": E.MAX_TEXT,
                                    "seeds": a.seeds, "frame_filter": a.frame_filter, "strategies": a.strategies,
                                    "examples": a.examples, "mode": mode, "final_mode": final_mode,
                                    "accept": a.accept, "hint_open_cap": a.hint_cap},
            "method_changes_t07e": {"budget_clock_deadline": a.budget_deadline, "two_phase": a.two_phase,
                                    "show_goal": a.show_goal, "mcp_tool_timeout_s": a.tool_timeout_s,
                                    "wall_cap_s": WALL_CAP_S, "seed_frame_goals_are_unit_goals": True},
            "allowed_kinds": sorted(allowed), "harness_sha256": {f: L.sha(HERE / f) for f in files},
            "examples_sha256": {f.name: L.sha(f) for f in sorted(L.EXAMPLES.glob("*")) if f.is_file()} if a.examples else None,
            "dev": bool(a.dev_effort or a.dev_no_codex or a.dev_skip_round0)}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    # Round 0 (no hints, frozen flags, outside the budget, map 13 item 3): own run, or reused from an
    # earlier counted run on the same stand-in (hash checked).
    gj = None
    if a.dev_skip_round0:
        history = [{"round": 0, "outcome": "DEV: skipped"}]
    elif a.round0_from:
        src = Path(a.round0_from)
        old = json.loads((src / "meta.json").read_text())
        assert old["standin_sha256"] == meta["standin_sha256"], "round 0 is from a different stand-in"
        r0 = json.loads((src / "history.json").read_text())[0]
        if r0.get("reused_from"):
            src = Path(r0["reused_from"])
            r0 = json.loads((src / "history.json").read_text())[0]
        gj = src / "round-0" / "goals.json"
        assert L.sha(gj) == r0["wp"]["goals_sha256"], "reused round-0 goals.json changed"
        history = [{"round": 0, "reused_from": str(src), "outcome": r0.get("outcome"),
                    "elapsed_min": r0.get("elapsed_min"), "wp": r0["wp"]}]
        L.log(out, f"round 0: reused from {src} ({r0.get('outcome')})")
    else:
        t_r0 = time.time()
        r0 = {"round": 0, "hints": [], "started": L.now()}
        L.log(out, "round 0: WP with no hints (frozen flags), outside the budget")
        L.wp_round(out, "round-0", standin, [], r0)
        r0["elapsed_min"] = round((time.time() - t_r0) / 60, 2)
        r0.pop("failing_goals", None)
        history = [r0]
        gj = out / "round-0" / "goals.json"
        L.log(out, f"round 0: {r0.get('outcome')} in {r0['elapsed_min']} min")
    if gj is not None:
        L.BASELINE_PASSED.update(g["goal"] for g in json.loads(gj.read_text()) if g.get("passed") and not g.get("smoke"))
    # Budget clock starts at the seed round (seeds are part of the loop: map 13 items 3 and 9).
    t0 = time.time()
    L.LOCKWAIT[0] = 0.0
    seeds = []
    if a.seeds:
        seeds = FS.seeds(L.STANDIN_DIR / L.UNIT)
    if a.frame_filter:
        tag = hashlib.sha256((HERE / "edit_loop.py").read_bytes()).hexdigest()[:12]
        seeds += [{"id": f"seedF{i}", "anchor": "global", "kind": k, "text": t,
                   "provenance": f"seed: edit_loop.py FRAME_FILTER {tag} (generic)"} for i, (k, t) in enumerate(FRAME_FILTER, 1)]
    L.log(out, f"seed round: {len(seeds)} seeds; budget clock at 0")
    rec = {"round": "seeds", "started": L.now(), "hints": seeds}
    chk = {}
    d = L.precheck(out, "seeds", standin, seeds, chk)
    if d is None:
        rec.update(outcome="seeds rejected by the proof hint check", check=chk)
        history.append(rec)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        raise SystemExit("seed check failed: " + json.dumps(chk)[:2000])
    wlog, ws = L.verifier(out, d, mode, timeout=3600, extra=(out / "round-cache", a.round_timeout))
    ar = L.assess_round(d, wlog)
    best = {"hints": seeds, "failing_goals": ar["failing_goals"], "n_open": len(ar["failing_goals"]),
            "n_goals": ar["n_goals"], "dir": str(d), "from": "seeds", "history": ["seeds"]}
    E.save_best(out, best)
    rec.update(round_wp={"exit": ws["exit_code"], "wall_s": ws["wall_s"], "peak_rss_mb": ws["peak_rss_mb"],
                         "n_goals": ar["n_goals"], "n_failing": best["n_open"], "log_sha256": ws["log_sha256"]},
               outcome=f"seed round: {best['n_open']} of {ar['n_goals']} goals open",
               elapsed_min=round(budget_s(t0) / 60, 2))
    history.append(rec)
    (out / "history.json").write_text(json.dumps(history, indent=1))
    L.log(out, rec["outcome"] + f" at {rec['elapsed_min']} min")
    proven, r, thread, final = False, 0, None, None
    if best["n_open"] == 0:
        final = final_replay(out, 0, best, a, t0, final_mode)
        proven = final["proven"]
    examples = L.examples_text() if a.examples else ""
    tactics = ", ".join(sorted(H.STRATEGY_TACTICS))
    while not proven and r < a.rounds and not a.dev_no_codex:
        used = budget_s(t0) / 60
        tool_budget = a.budget_min - a.final_reserve_min - used
        if tool_budget < 1.0:
            L.log(out, f"in-call budget spent at {used:.1f} min")
            break
        r += 1
        best = E.load_best(out)
        state = tool_state(out, r, a, t0, mode, allowed)
        if thread is None:
            prompt = PROMPT.format(
                max_ops=E.MAX_OPS, max_text=E.MAX_TEXT, kinds=", ".join(sorted(allowed)),
                accept_rule=ACCEPT_RULE[a.accept].format(cap=a.hint_cap) + (PHASE2_RULE if a.two_phase else ""),
                tool_notes=SHOW_GOAL_NOTE if a.show_goal else "",
                budget_clock_note=(" (time your tool calls wait for the shared verifier queue is not counted)"
                                   if a.budget_deadline else ""),
                strategy_notes=STRATEGY_NOTES.format(tactics=tactics) if a.strategies else "",
                round_timeout=a.round_timeout, tool_budget=tool_budget, round=r, rounds=a.rounds, minutes=used,
                budget=a.budget_min, best=E.best_text(best), open=E.open_text(best), examples=examples,
                files=L.workspace_files(standin))
        else:
            prompt = (f"Round {r} of at most {a.rounds}; minutes used so far: {used:.1f} of {a.budget_min}; "
                      f"in-call budget for this call {tool_budget:.0f} min. The loop's state is unchanged since your last "
                      f"tool result.\n{E.open_text(best)}\nContinue with the tools; answer with your final edit "
                      "(JSON {\"ops\": [...], \"notes\": ...}) before the in-call budget ends.")
        L.log(out, f"round {r}: Codex call ({'resumed' if thread else 'new'} session, {len(prompt)} chars, best {best['n_open']} open)")
        lw0 = L.LOCKWAIT[0]
        limit_s = (a.budget_min - a.final_reserve_min) * 60 + 120.0  # same 2-min grace as t07d

        def budget_stop(state=state, lw0=lw0, limit_s=limit_s):
            return time.time() - t0 - lw0 - live_lock_wait(state) > limit_s

        c = codex_call(out, r, prompt, thread, state, max(120.0, tool_budget * 60 + 120.0),
                       budget_stop=budget_stop if a.budget_deadline else None)
        thread = c.get("thread") or thread
        tool = read_tool(state)
        rec = {"round": r, "started": L.now(), "phase_at_start": E.phase_of(best),
               "codex": {k: c[k] for k in ("exit", "wall_s", "usage", "error", "killed_at_deadline", "stop_reason")}, "codex_notes": c.get("notes"), "codex_thread": thread, "tool": tool,
               "codex_calls": 1}
        best = E.load_best(out)
        if c.get("ops") and best["n_open"] > 0 and (a.budget_min - a.final_reserve_min) - budget_s(t0) / 60 > 0.5:
            prov = f"codex {L.PIN['model']} {L.PIN['effort']} round {r} final answer"
            fr, nb = E.attempt(out, best, c["ops"], f"r{r}f", prov, mode, a.round_timeout, allowed,
                               timeout_s=max(60, int((a.budget_min - budget_s(t0) / 60) * 60)))
            rec["final_answer_edit"] = {k: fr.get(k) for k in ("result", "n_open_before", "n_open_after", "problems")}
            if nb is not None:
                E.save_best(out, nb)
                best = nb
        rec["best_n_open"] = best["n_open"]
        rec["round_wp"] = {"n_failing": best["n_open"]}  # heartbeat compatibility
        if best["n_open"] == 0 and budget_s(t0) / 60 < a.budget_min:
            L.log(out, f"round {r}: best set proves every round-mode goal; fresh full replay starts")
            final = final_replay(out, r, best, a, t0, final_mode)
            rec["final"] = {k: v for k, v in final.items() if k != "failing_goals"}
            proven = final["proven"]
        rec["outcome"] = ("proven (fresh full replay)" if proven else
                          f"best set {best['n_open']} open goals (round mode)" +
                          (f"; final replay: {final['outcome']}" if rec.get("final") else ""))
        rec["elapsed_min"] = round(budget_s(t0) / 60, 2)
        rec["lock_wait_s_so_far"] = round(L.LOCKWAIT[0], 1)
        history.append(rec)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        L.log(out, f"round {r}: {rec['outcome']} at {rec['elapsed_min']} min")
    best = E.load_best(out)
    summary = {"proven": proven, "within_budget": proven and budget_s(t0) / 60 <= a.budget_min, "rounds": r,
               "codex_calls": r, "elapsed_min": round(budget_s(t0) / 60, 2),
               "lock_wait_excluded_s": round(L.LOCKWAIT[0], 1), "best_n_open": best["n_open"],
               "best_hints": len(best["hints"]), "best_sha256": L.sha(out / "best.json"),
               "tool_calls": sum((h.get("tool") or {}).get("calls", 0) for h in history[2:]),
               "show_goal_calls": sum((h.get("tool") or {}).get("show_goal_calls", 0) for h in history[2:]),
               "best_unit_hint_open": list(E.split_counts(best["failing_goals"])), "phase_at_end": E.phase_of(best),
               "wp_attempts": sum((h.get("tool") or {}).get("propose_calls", 0) for h in history[2:]),
               "tokens": {}, "final": {k: v for k, v in (final or {}).items() if k != "failing_goals"} or None,
               "finished": L.now()}
    for h in history:
        for k, v in ((h.get("codex") or {}).get("usage") or {}).items():
            summary["tokens"][k] = summary["tokens"].get(k, 0) + v
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    L.log(out, f"done: {json.dumps(summary)}")


if __name__ == "__main__":
    main()

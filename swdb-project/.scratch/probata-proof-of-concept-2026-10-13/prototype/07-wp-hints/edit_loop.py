#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# Updated 2026-10-15 ET: fail-closed ghost-witness ownership guard.
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
import staged_search as S
import focused_probe as F
import run_report as R
import terminal_plan as T
import provider_origin as O
import baseline_start as B

HERE = Path(__file__).resolve().parent
OPS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["ops", "notes"],
              "properties": {"notes": {"type": "string"}, "ops": {"type": "array", "items": E.OP_SCHEMA}}}

# Generic, unit-independent (method, provenance "seed"): every `assigns`/`loop assigns` goal that the
# three provers do not prove on the full context is retried after WP's own Wp.filter tactic.
FROZEN_WP_FLAGS = ["-wp-no-filter-init"]  # method18: every mode, including generation and fresh smoke

FRAME_FILTER = [
    ("strategy", "\\wp::strategy SeedFrameProvers: \\prover(\"alt-ergo\", \"z3\", \"cvc5\");"),
    ("strategy", "\\wp::strategy SeedFrameFilter: \\tactic(\"Wp.filter\", \\children(SeedFrameProvers));"),
    ("proof", "\\wp::proof SeedFrameFilter: \"@assigns\";"),
]

PROMPT = """You are the proof-hint agent of a proof-hint loop (Frama-C 33.0 / WP, provers Alt-Ergo 2.6.4, Z3,
CVC5, x86_64 machdep). Your job: add ACSL proof hints so that WP proves every goal of the C function TDStep
below (its `ensures` clauses = the unit postcondition, the generated `check hazard_*` annotations, call-site
preconditions, loop goals, termination, frame goals). You never edit code or contracts.

Algorithmic boundary guidance (method revision, 2026-10-15): the chunk-loop cursor
advances by a full chunk even after a partial final chunk. Reason about the processed
frontier prefix within its actual end; never make a prefix include unprocessed storage
or assume chunk divisibility. Keep range-loop cursor progress, gather source validity
across calls, and queue-flush concatenation as separately checked obligations. No
previous run's hints are supplied or pre-seeded.

Logical-scope guidance (method revision, 2026-10-15): when restating a quantified
postcondition as a bookkeeping assertion, preserve every antecedent and its scope
over the whole conjunction. Appended-output membership is required for newly
discovered vertices, not for every vertex. Check empty frontiers and previsited or
unreachable vertices before spending prover time on a stronger assertion. Correct
or remove an invalid cut even when other goals become easy when it is assumed.

Bridge-first induction (method18 revision, 2026-10-15): first inspect the exact
range-continuation, gather old-base and CAS contracts and state a cutpoint plan.
Build small checked bridges bottom-up. Use stmt:after_neighbor_gather to establish
vertex-index facts before the parent gather, retaining them across the intervening
frontier gather through its frame. Then derive the batch hint/current-parent
relationship from gather and parent updates, so either exact-CAS branch leaves a
consumed vertex visited, including duplicates. Queue membership holds after enqueue,
not in the transient interval after CAS and before push; prove buffered/flushed
queue transfers separately. Never assume parent validity or CAS success.

Only then build scalar edge -> row and batch position -> range -> chunk progress.
Separate issued from consumed pairs: snapshot the pre-issue cursor; use range
coverage to advance consumed progress only after all emitted positions are handled.
Connect empty batches to exhaustion through the contract. Clamp original-frontier
prefixes at the actual end, including a final partial chunk. Safety and queue
bookkeeping alone do not establish visitation completeness. Every bridge retains
its own proof obligations; moving a postcondition into an assertion does not prove it.

Scalar ghost syntax: use one fresh scalar declaration per hint, then separate simple
assignments at anchors where operands are in scope, for example `ghost int snap;`
then `ghost snap = scalar_in_scope;` (illustrative names, not supplied proof hints).
Comma-separated initialized declarations, calls, pointer ghosts, macros and writes
to trusted model ghost state are refused. Scope and frame obligations still apply.

HOW THIS LOOP WORKS (local editing with a checked incumbent):
- The loop keeps ONE checked incumbent; an explicitly enabled debt stage has a separate working set. It starts with mechanically generated frame seeds (ids "seed*": every
  loop's `loop assigns`, written from the code; they are fixed, you cannot change them or add `loop assigns`).
- You change the best set only by EDITS: a list of 1-{max_ops} operations, each
  {{"op": "add"|"delete"|"edit", "goal": <name of an OPEN goal this operation targets>, "id": <hint id for
  delete/edit, else "">, "anchor": <anchor for add, else "">, "kind": <kind for add, else "">, "text": <hint
  text for add/edit, else "">}}. At most {max_text} characters of new text per edit.
- propose_edit runs WP with the active working set (otherwise incumbent) + edit. {accept_rule}
  An edit outside the stated acceptance/staging rules is REVERTED and the incumbent stays.
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

DEBT_RULE = ("\n  METHOD18 BOUNDED DEBT: best.json remains the checked incumbent. A temporary working set may\n"
             "  add at most 4 open hint goals without any increase in open unit goals. Repair it in at most\n"
             "  4 further propose_edit attempts or 5 counted minutes; every attempt and rollback consumes the\n"
             "  same 60-minute budget. A stage starts only with 5 search minutes before the final reserve.\n"
             "  Failed checks also consume a repair attempt; check_edit/show_goal time consumes the clock.\n"
             "  Promotion requires recovering the original incumbent acceptance rule, with no unit-goal\n"
             "  regression. Otherwise roll back to that unchanged incumbent. Temporary debt never counts\n"
             "  as best/proven; every final goal and fresh full smoke run must still pass.")

STAGED_RULE = ("\n  METHOD19: three counted search thirds: bridges, consumption, recovery. The tool reports the\n"
               "  current phase and remaining time. One fresh conversation authors all concrete hints.\n"
               "  A separate temporary candidate may add at most 8 TOTAL open goals, including unit goals,\n"
               "  relative to the captured incumbent. Repair within 4 propose_edit attempts and 300 counted\n"
               "  seconds from first entry; neither edits nor phase changes reset its age. Invalid/rejected\n"
               "  proposals consume repairs and time. The last third permits recovery only: no new stage.\n"
               "  Promotion requires total open goals no higher than the captured incumbent. Otherwise rollback.\n"
               "  All ordinary/hint obligations and the fresh final smoke/covering-wait checks remain mandatory.")


def phase_text(counted_s):
    if E.STAGED[0] is None:
        return ""
    phase = S.phase(E.STAGED[0], counted_s)
    return (f"METHOD{20 if E.STAGED[0].get('method') == F.METHOD else 19} PHASE {phase['index']+1}/3: {phase['name']}; "
            f"counted interval {phase['start_s']:.1f}..{phase['end_s']:.1f} seconds. " + phase['guidance'])


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
WALL_CAP_S = 5 * 3600  # t07e/method19: guard only; the budget clock decides


def live_lock_wait(mcp_state):
    """Lock wait of the in-call tool so far (settled + the wait in progress), read from outside the tool."""
    f = Path(mcp_state) / "lockwait_live.json"
    try:
        j = json.loads(f.read_text())
    except (OSError, ValueError):
        return 0.0
    if L.CLOCK_KIND[0] == "continuous_monotonic":
        return S.wait_seconds(j, S.clock_info(), L.clock())
    if j.get("clock", "wall") != L.CLOCK_KIND[0]:
        return 0.0  # an incompatible clock earns no excluded time
    return max(0.0, j.get("settled_s", 0.0)) + (max(0.0, L.clock() - j["pending_since"]) if j.get("pending_since") is not None else 0.0)


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
    call_config = json.loads((Path(mcp_state) / "config.json").read_text())
    if call_config.get("method20"):
        # Explicit project authorization for these two artifact-producing tools.
        # Preserve truthful write-tool annotations and the read-only sandbox.
        for tool in ("record_design", "focused_probe"):
            common += ["-c", f'mcp_servers.probata.tools.{tool}.approval_mode="approve"']
    tail = ["--json", "--output-schema", str(d / "schema.json"), "--output-last-message", str(d / "final.json"),
            "--disable", "shell_tool"]
    for f in L.CODEX_DISABLED_FEATURES:
        tail += ["--disable", f]
    if resume:
        argv = [L.CODEX, "exec", "resume", *common, *tail, resume, "-"]
    else:
        argv = [L.CODEX, "exec", *common, "-s", "read-only", "-C", str(ws), *tail, "-"]
    (d / "argv.json").write_text(json.dumps(argv[:-1]))
    t = L.clock()
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
            if budget_stop is None and L.clock() - t > deadline_s:
                stop_reason = "wall-clock deadline"
            elif budget_stop is not None and budget_stop():
                stop_reason = "budget-clock deadline"
            elif L.clock() - t > WALL_CAP_S:
                stop_reason = "wall cap"
            if stop_reason:
                break
        if stop_reason:
            killed = True
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=1 if call_config.get("method22") else 60)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
    usage, thread, receipts, usage_valid = {}, resume, 0, True
    for ln in (d / "stdout.jsonl").read_text(errors="replace").splitlines():
        try:
            ev = json.loads(ln)
        except ValueError:
            continue
        if ev.get("type") == "thread.started":
            thread = ev.get("thread_id")
        if ev.get("type") == "turn.completed":
            receipts += 1
            values = ev.get("usage")
            valid = isinstance(values, dict) and all(type(values.get(k)) is int and values[k] >= 0
                for k in ("input_tokens", "output_tokens"))
            valid = valid and all(type(v) is int and v >= 0 for v in (values or {}).values())
            usage_valid = usage_valid and valid
            if valid:
                for k, v in values.items():
                    usage[k] = usage.get(k, 0) + v
    deadline_met = not (budget_stop() if budget_stop is not None else L.clock()-t > deadline_s)
    res = {"exit": p.returncode, "completion_deadline_met": deadline_met, "wall_s": round(L.clock() - t, 1), "usage": usage, "thread": thread,
           "usage_status": "complete" if (not killed and p.returncode == 0 and receipts == 1 and usage_valid) else "partial" if usage else "unavailable",
           "completed_usage_receipts": receipts, "usage_fields_valid": usage_valid,
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
        "live_file": str(state / "lockwait_live.json") if (a.budget_deadline or a.bounded_debt or a.staged_induction) else None,
        "bounded_debt": a.bounded_debt, "staged_search": E.STAGED[0], "method20": a.design_probes,
        "method22": a.terminal_full30, "method23": a.fresh_baseline_start, "proof_search_stop_min": T.PROOF_STOP_MIN if a.terminal_full30 else None,
        "clock_kind": L.CLOCK_KIND[0], "clock_info": S.clock_info() if a.staged_induction else None}, indent=1))
    return state


def read_tool(state):
    f = state / "submissions.jsonl"
    subs = [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []
    if L.CLOCK_KIND[0] == "continuous_monotonic":
        matched = [s for s in subs if s.get("clock") == L.CLOCK_KIND[0] and s.get("clock_info") == S.clock_info()]
        lw = max((S.wait_seconds({**s, "settled_s": s.get("lockwait_total_s"), "pending_since": None},
                  S.clock_info(), L.clock()) for s in matched), default=0.0)
    else:
        lw = max((s.get("lockwait_total_s", 0) for s in subs), default=0.0)
    L.LOCKWAIT[0] += lw
    return {"calls": len(subs), "lock_wait_s": lw,
            "check_calls": sum(1 for s in subs if s["tool"] == "check_edit"),
            "propose_calls": sum(1 for s in subs if s["tool"] == "propose_edit"),
            "show_goal_calls": sum(1 for s in subs if s["tool"] == "show_goal"),
            "focused_calls": sum(1 for s in subs if s["tool"] == "focused_probe"),
            "design_calls": sum(1 for s in subs if s["tool"] == "record_design"),
            "accepted": sum(1 for s in subs if str(s.get("result", "")).startswith("accepted")),
            "staged": sum(1 for s in subs if str(s.get("result", "")).startswith("staged")),
            "reverted": sum(1 for s in subs if str(s.get("result", "")).startswith("reverted")),
            "rejected": sum(1 for s in subs if "rejected" in str(s.get("result", ""))),
            "trace": [[s["n"], s["tool"], s.get("result"), s.get("n_open_before"), s.get("n_open_after"),
                       s.get("wall_s"), len(s.get("ops") or [])] for s in subs],
            "submissions": str(f)}


def budget_s(t0):
    return L.clock() - t0 - L.LOCKWAIT[0]


def final_replay(out, r, best, a, t0, final_mode):
    if a.terminal_full30:
        try:
            T.verify_incumbent(best, expected_out=out)
        except (RuntimeError, OSError, ValueError) as exc:
            return {"proven": False, "outcome": str(exc)}
    d = L.run_dir(out, f"final-r{r}", (Path(best["dir"]) / L.UNIT).read_text())
    rec = {}
    remaining = lambda: a.budget_min * 60 - budget_s(t0) - (T.NEGATIVE_RESERVE_MIN * 60 if a.terminal_full30 else 0)
    if remaining() <= 0:
        return {"proven": False, "outcome": "no positive budget before negative reserve"}
    L.wp_round(out, f"final-r{r}", (L.STANDIN_DIR / L.UNIT).read_text(), best["hints"], rec, mode=final_mode, d=d,
               timeout=(max(1, remaining()) if (a.bounded_debt or a.staged_induction) else
                        max(60, int(a.budget_min * 60 - budget_s(t0)) + 60)),
               **({"remaining_s": remaining} if (a.bounded_debt or a.staged_induction) else {}))
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
    ap.add_argument("--bounded-debt", action="store_true", help="method18: +4 temporary hint goals, 4 repairs/5 counted minutes; incumbent remains separate")
    ap.add_argument("--staged-induction", action="store_true", help="method19: counted three-phase search, +8 temporary total goals; unchanged final acceptance")
    ap.add_argument("--design-probes", action="store_true", help="method20: explicit state design plus diagnostic-only focused probes; requires staged-induction")
    ap.add_argument("--diagnostic-baseline10", action="store_true", help="method21: fresh full diagnostic baseline at10s only; final acceptance stays30s")
    ap.add_argument("--owner", default="t07d")
    ap.add_argument("--dev-effort", help="DEV ONLY (never a counted run): override the pinned effort")
    ap.add_argument("--dev-no-codex", action="store_true", help="DEV ONLY: stop after the seed round")
    ap.add_argument("--dev-skip-round0", action="store_true", help="DEV ONLY: no no-hint run (no REGRESSION marks)")
    ap.add_argument("--terminal-full30", action="store_true", help="method22: zero-seed Codex-only paging/complete receipts; terminal full30 plus negative inside60")
    ap.add_argument("--fresh-baseline-start", action="store_true", help="method23: exact machine task reader and fresh full baseline empty diagnostic initialization")
    a = ap.parse_args()
    if a.fresh_baseline_start and not a.terminal_full30:
        ap.error("method23 fresh-baseline-start requires terminal-full30")
    if a.terminal_full30 and (not a.diagnostic_baseline10 or a.seeds or a.frame_filter or a.examples):
        ap.error("method22 requires diagnostic-baseline10 and forbids seeds, frame-filter and examples")
    if a.design_probes and not a.staged_induction:
        ap.error("method20 design-probes requires the strict staged-induction foundation")
    if a.diagnostic_baseline10 and not a.design_probes:
        ap.error("method21 diagnostic-baseline10 requires the strict method20 foundation")
    assert a.monotone, "this loop implements method change (a) only"
    E.ACCEPT[0] = a.accept
    E.CAP[0] = a.hint_cap
    E.TWO_PHASE[0] = a.two_phase
    if a.staged_induction:
        if a.bounded_debt or a.two_phase or a.accept != "total" or a.round0_from:
            ap.error("method19 needs total acceptance, a fresh baseline, and its own staged policy")
        if a.terminal_full30:
            if a.budget_min != 60 or a.final_reserve_min != 24 or a.round_timeout != 10 or not 1 <= a.rounds <= 10:
                ap.error("method22 requires60 counted minutes,24minute final allocation,10second rounds and1..10rounds")
        elif a.budget_min != 60 or a.final_reserve_min != 8 or not a.seeds:
            ap.error("method19 requires 60 counted minutes, an eight-minute reserve, and mechanical frame seeds")
        if a.dev_effort or a.dev_no_codex or a.dev_skip_round0:
            ap.error("method19 counted policy cannot mix development overrides")
        if Path(a.out).exists() and any(Path(a.out).iterdir()):
            ap.error("method19 requires a fresh output directory")
        L.CLOCK_KIND[0] = "continuous_monotonic"
        S.clock_info()  # fail before any work if the clock cannot be initialized
        S.check_inputs(L.STANDIN_DIR)
    else:
        L.CLOCK_KIND[0] = "wall"
    O.REQUIRED[0] = a.terminal_full30
    strict = a.bounded_debt or a.staged_induction
    E.STAGED[0] = None
    E.DEBT[0] = strict
    TOOL_TIMEOUT_S[0] = a.tool_timeout_s
    L.OWNER[0] = a.owner
    if a.dev_effort:
        L.PIN["effort"] = a.dev_effort
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if (a.bounded_debt or a.staged_induction):
        t0 = L.clock()  # method18 counts baseline, seeds, search, rollback and final replay
        L.LOCKWAIT[0] = 0.0
        E.COUNTED_S[0] = lambda: budget_s(t0)
        E.SEARCH_REMAINING_S[0] = lambda: (T.PROOF_STOP_MIN if a.terminal_full30 else a.budget_min - a.final_reserve_min) * 60 - budget_s(t0)
    mode = "round-s" if (a.strategies or a.frame_filter) else "round"
    final_mode = "wp-smoke-s" if (a.strategies or a.frame_filter) else "wp-smoke"
    allowed = set(H.KINDS) - {"loop_assigns"} if a.seeds else set(H.KINDS)
    if not a.strategies:
        allowed -= {"strategy", "proof"}
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    files = ["loop.py", "hints.py", "wp_run.sh", "edit_loop.py", "edit_core.py", "edit_tool_mcp.py", "frame_seeds.py",
             "goal_print.py", "focused_probe.py"] + (["staged_search.py", "counted_verifier.py", "test_debt.py", "standin/tdstep_standin.c"] if a.staged_induction else [])
    if a.design_probes:
        files += ["test_focused_probe.py"]
    if a.diagnostic_baseline10:
        files += ["run_report.py", "test_baseline_plan.py"]
    if a.terminal_full30:
        files += ["terminal_plan.py", "provider_origin.py", "test_terminal_plan.py"]
    if a.fresh_baseline_start:
        files += ["baseline_start.py", "Probata_task_export.ml", "test_exact_tasks.py", "test_baseline_start.py", "test_inspection_retry.py"]
    meta = {"started": L.now(), "pin": L.PIN,
            "codex_version": subprocess.run([L.CODEX, "--version"], capture_output=True, text=True).stdout.strip(),
            "ghost_hint_guard": H.GHOST_HINT_RULE,
            "frozen_wp_flags": FROZEN_WP_FLAGS,
            "initialization_filtering": "disabled; all resulting obligations remain mandatory",
            "diagnostic_guidance": "state-design-focused-v7" if a.design_probes else "staged-cas-queue-consumption-v6" if a.staged_induction else "bridge-first-consumed-prefix-cas-v5",
            "method18": {"id": "bridge-first-bounded-debt-v1", "added_anchor": "stmt:after_neighbor_gather",
                         "bounded_debt": a.bounded_debt, "hint_debt": E.DEBT_HINTS,
                         "repair_proposals": E.DEBT_REPAIRS, "counted_seconds": E.DEBT_SECONDS,
                         "incumbent_file": "best.json", "working_file": "debt.json",
                         "clock_includes_fresh_round0": a.bounded_debt,
                         "provider_grace_seconds": 0 if (a.bounded_debt or a.staged_induction) else 120,
                         "strict_completion_deadlines": a.bounded_debt,
                         "no_unit_regression": True, "all_goal_fresh_smoke_acceptance_unchanged": True},
            "standin_sha256": {f: L.sha(L.STANDIN_DIR / f) for f in [L.UNIT] + L.HEADERS},
            "cpp_unit_sha256": L.sha(L.CPP_UNIT), "rounds": a.rounds, "budget_min": a.budget_min,
            "round_timeout_s": a.round_timeout, "final_reserve_min": a.final_reserve_min,
            "method_changes_t07d": {"monotone": a.monotone, "max_ops": E.MAX_OPS, "max_text": E.MAX_TEXT,
                                    "seeds": a.seeds, "frame_filter": a.frame_filter, "strategies": a.strategies,
                                    "examples": a.examples, "mode": mode, "final_mode": final_mode,
                                    "accept": a.accept, "hint_open_cap": a.hint_cap},
            "method_changes_t07e": {"budget_clock_deadline": a.budget_deadline or strict, "two_phase": a.two_phase,
                                    "show_goal": a.show_goal, "mcp_tool_timeout_s": a.tool_timeout_s,
                                    "wall_cap_s": WALL_CAP_S, "seed_frame_goals_are_unit_goals": not a.terminal_full30},
            "allowed_kinds": sorted(allowed), "harness_sha256": {f: L.sha(HERE / f) for f in files},
            "examples_sha256": {f.name: L.sha(f) for f in sorted(L.EXAMPLES.glob("*")) if f.is_file()} if a.examples else None,
            "dev": bool(a.dev_effort or a.dev_no_codex or a.dev_skip_round0)}
    if a.staged_induction:
        meta["method19"] = {"check": S.identity(), "clock": S.clock_info(), "total_debt": S.TOTAL_DEBT,
            "repair_proposals": S.REPAIRS, "counted_seconds": S.SECONDS, "phases": list(S.PHASES),
            "incumbent_file": "best.json", "working_file": "debt.json", "fresh_baseline_counted": True,
            "provider_grace_seconds": 0, "strict_completion_deadlines": True,
            "all_goal_fresh_smoke_acceptance_unchanged": True, "historical_source": "996bd62c1dd361845a7d6041167ca762e6d0ee32",
            "historical_input_sha256": S.HISTORICAL_INPUTS,
            "covering_wait_negative": "separate mandatory acceptance control after a proven incumbent; not implied by summary.proven",
            "prototype_rte_boundary": "no production -wp-rte/-rte-initialized @all; no production safety claim"}
    if a.design_probes:
        meta["method20"] = {"check": F.identity(), "focused_results": "diagnostic_only",
            "can_promote": False, "milestones": "complete checked rounds only",
            "design_objectives": list(F.OBJECTIVES), "phase_fractions": [.55,.35,.10],
            "authorized_mcp_approval_modes": {"record_design": "approve", "focused_probe": "approve"},
            "prototype_rte_boundary": "unchanged; no production RTE/initializedness claim"}
    if a.diagnostic_baseline10:
        meta["method21"] = {"id": "diagnostic-baseline10-v1", "diagnostic_only": True,
            "baseline_mode": "baseline-smoke10", "baseline_timeout_s": 10, "final_timeout_s": 30,
            "baseline_full_inventory_and_smoke": True, "fresh_observed_pass_set_only": True,
            "all_original_final_obligations_mandatory": True,
            "confound": "Shorter diagnostic timeout can change baseline statuses and regression pass set; projected time recovery is unmeasured."}
    if a.terminal_full30:
        meta["method19"]["covering_wait_negative"] = "mandatory same-clock identical-hints negative after qualifying positive; included in method22 summary.proven"
        meta["method22"] = {"id": T.METHOD, "mechanical_seeds": False,
            "proof_search_stop_min": T.PROOF_STOP_MIN, "provider_hard_stop_min": T.HARD_STOP_MIN,
            "negative_reserve_min": T.NEGATIVE_RESERVE_MIN, "total_min": 60,
            "terminal_replay_even_with_diagnostic_open": True, "positive_and_negative_counted": True,
            "all_provider_receipts_required": True, "completion_receipt_required": True,
            "timed_admission_boundary": "after required accounting and summary/completion receipt persistence; final informational logging afterward",
            "allocation_sufficiency": "unproven; chosen prospectively"}
    if a.fresh_baseline_start:
        meta["method23"] = {"id": B.METHOD, "exact_machine_goal_tasks": True,
            "initial_incumbent": "fresh full baseline TDStep/global-lemma non-smoke subset; no second round",
            "cross_mode_formula_equivalence_claimed": False,
            "confound": "Baseline mode/status projection replaces initial round-s; scheduling and initial diagnostic pass-set provenance change.",
            "all_final_obligations_mandatory": True}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    # Round 0 is outside the legacy budget; methods18/19 count the fresh baseline.
    # Own run, or reused from an
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
        t_r0 = L.clock()
        r0 = {"round": 0, "hints": [], "started": L.now()}
        baseline_mode = "baseline-smoke10" if a.diagnostic_baseline10 else "wp-smoke"
        if a.diagnostic_baseline10:
            r0["diagnostic_baseline"] = {"mode": baseline_mode, "timeout_s": 10}
        L.log(out, "round 0: WP with no hints (" + baseline_mode + "), " + ("counted from the fresh baseline" if (a.bounded_debt or a.staged_induction) else "outside the budget"))
        L.wp_round(out, "round-0", standin, [], r0,
                   mode=baseline_mode,
                   **({"remaining_s": E.SEARCH_REMAINING_S[0]} if (a.bounded_debt or a.staged_induction) else {}))
        if a.staged_induction:
            try:
                if not r0.get("wp") or r0["wp"].get("exit") != 0:
                    raise RuntimeError("method19 checked run refused: fresh baseline process/check failed")
                log_path = Path(r0["wp"]["log"])
                r0["checked_run"] = S.check_run(log_path.parent, log_path, round_mode=False)
                if E.SEARCH_REMAINING_S[0]() <= 0:
                    raise RuntimeError("method19 checked run refused: baseline completed after search deadline")
            except (RuntimeError, KeyError) as exc:
                r0.update(outcome=str(exc), proven=False)
                (out / "history.json").write_text(json.dumps([r0], indent=1))
                raise SystemExit(str(exc)) from None
        r0["elapsed_min"] = round((L.clock() - t_r0) / 60, 2)
        r0.pop("failing_goals", None)
        history = [r0]
        gj = out / "round-0" / "goals.json"
        L.log(out, f"round 0: {r0.get('outcome')} in {r0['elapsed_min']} min")
    if gj is not None:
        L.BASELINE_PASSED.clear()
        L.BASELINE_PASSED.update(g["goal"] for g in json.loads(gj.read_text()) if g.get("passed") and not g.get("smoke"))
    # Legacy clock starts at seeds. Methods18/19 keep the earlier all-work clock.
    if not (a.bounded_debt or a.staged_induction):
        t0 = L.clock()
        L.LOCKWAIT[0] = 0.0
    E.COUNTED_S[0] = lambda: budget_s(t0)
    E.SEARCH_REMAINING_S[0] = lambda: (T.PROOF_STOP_MIN if a.terminal_full30 else a.budget_min - a.final_reserve_min) * 60 - budget_s(t0)
    if a.fresh_baseline_start:
        best, initial = B.initialize(out)
        E.save_best(out, best)
        rec = {"round": "baseline-initial", "hints": [], "diagnostic_origin": initial,
               "outcome": f"fresh full baseline projection: {best['n_open']} of {best['n_goals']} diagnostic goals open; no round launched",
               "elapsed_min": round(budget_s(t0) / 60, 2)}
        history.append(rec)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        L.log(out, rec["outcome"] + f" at {rec['elapsed_min']} min")
    else:
        seeds = []
        if a.seeds:
            seeds = FS.seeds(L.STANDIN_DIR / L.UNIT)
        if a.frame_filter:
            tag = hashlib.sha256((HERE / "edit_loop.py").read_bytes()).hexdigest()[:12]
            seeds += [{"id": f"seedF{i}", "anchor": "global", "kind": k, "text": t,
                       "provenance": f"seed: edit_loop.py FRAME_FILTER {tag} (generic)"} for i, (k, t) in enumerate(FRAME_FILTER, 1)]
        L.log(out, f"seed round: {len(seeds)} seeds; counted minutes {budget_s(t0) / 60:.2f}")
        rec = {"round": "seeds", "started": L.now(), "hints": seeds}
        chk = {}
        d = L.precheck(out, "seeds", standin, seeds, chk,
                       **({"remaining_s": E.SEARCH_REMAINING_S[0]} if (a.bounded_debt or a.staged_induction) else {}))
        if d is None:
            rec.update(outcome="seeds rejected by the proof hint check", check=chk)
            history.append(rec)
            (out / "history.json").write_text(json.dumps(history, indent=1))
            raise SystemExit("seed check failed: " + json.dumps(chk)[:2000])
        if (a.bounded_debt or a.staged_induction) and E.SEARCH_REMAINING_S[0]() <= 0:
            raise SystemExit("seed round exhausted search time; no provider launch")
        wlog, ws = L.verifier(out, d, mode, timeout=(max(1, E.SEARCH_REMAINING_S[0]()) if (a.bounded_debt or a.staged_induction) else 3600),
                              extra=(out / "round-cache", a.round_timeout))
        if a.staged_induction:
            try:
                rec["checked_run"] = S.check_run(d, wlog, round_mode=True)
                if E.SEARCH_REMAINING_S[0]() <= 0:
                    raise RuntimeError("method19 checked run refused: seed completed after search deadline")
            except RuntimeError as exc:
                rec.update(outcome=str(exc), proven=False)
                history.append(rec)
                (out / "history.json").write_text(json.dumps(history, indent=1))
                raise SystemExit(str(exc)) from None
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
    if a.staged_induction:
        if E.SEARCH_REMAINING_S[0]() <= 0:
            raise SystemExit("seed round exhausted search time; no provider launch")
        E.STAGED[0] = (F.schedule if a.design_probes else S.schedule)(budget_s(t0), (T.PROOF_STOP_MIN if a.terminal_full30 else a.budget_min-a.final_reserve_min)*60)
        meta["method20" if a.design_probes else "method19"]["schedule"] = E.STAGED[0]
        (out / "meta.json").write_text(json.dumps(meta, indent=1))
    proven, r, thread, final = False, 0, None, None
    if best["n_open"] == 0 and not a.terminal_full30:
        final = final_replay(out, 0, best, a, t0, final_mode)
        proven = final["proven"]
    examples = L.examples_text() if a.examples else ""
    tactics = ", ".join(sorted(H.STRATEGY_TACTICS))
    while not proven and r < a.rounds and not a.dev_no_codex:
        used = budget_s(t0) / 60
        tool_budget = (T.PROOF_STOP_MIN if a.terminal_full30 else a.budget_min - a.final_reserve_min) - used
        if tool_budget < 1.0:
            L.log(out, f"in-call budget spent at {used:.1f} min")
            break
        r += 1
        best = E.load_working(out, counted_s=budget_s(t0), remaining_s=tool_budget * 60) if (a.bounded_debt or a.staged_induction) else E.load_best(out)
        state = tool_state(out, r, a, t0, mode, allowed)
        if thread is None:
            prompt = (T.prompt(PROMPT) if a.terminal_full30 else PROMPT).format(
                max_ops=E.MAX_OPS, max_text=E.MAX_TEXT, kinds=", ".join(sorted(allowed)),
                accept_rule=ACCEPT_RULE[a.accept].format(cap=a.hint_cap) + (PHASE2_RULE if a.two_phase else "") + (F.rule(STAGED_RULE) if a.design_probes else STAGED_RULE if a.staged_induction else DEBT_RULE if a.bounded_debt else ""),
                tool_notes=SHOW_GOAL_NOTE if a.show_goal else "",
                budget_clock_note=(" (time your tool calls wait for the shared verifier queue is not counted)"
                                   if (a.budget_deadline or a.bounded_debt or a.staged_induction) else ""),
                strategy_notes=(STRATEGY_NOTES.replace(' (the seeds use names starting with "Seed")', "") if a.terminal_full30 else STRATEGY_NOTES).format(tactics=tactics) if a.strategies else "",
                round_timeout=a.round_timeout, tool_budget=tool_budget, round=r, rounds=a.rounds, minutes=used,
                budget=a.budget_min, best=(E.working_text(out, best).replace("; ids with prefix 'seed' are the fixed frame seeds", "") if a.terminal_full30 else E.working_text(out, best)), open=E.open_text(best) + E.debt_text(out), examples=examples,
                files=L.workspace_files(standin))
        else:
            prompt = (f"Round {r} of at most {a.rounds}; minutes used so far: {used:.1f} of {a.budget_min}; "
                      f"in-call budget for this call {tool_budget:.0f} min. The loop's state is unchanged since your last "
                      f"tool result.\n{E.open_text(best)}{E.debt_text(out)}\nContinue with the tools; answer with your final edit "
                      "(JSON {\"ops\": [...], \"notes\": ...}) before the in-call budget ends.")
        if a.staged_induction:
            prompt += "\n" + phase_text(budget_s(t0))
        L.log(out, f"round {r}: Codex call ({'resumed' if thread else 'new'} session, {len(prompt)} chars, best {best['n_open']} open)")
        lw0 = L.LOCKWAIT[0]
        limit_s = (a.budget_min - a.final_reserve_min) * 60 + (0.0 if (a.bounded_debt or a.staged_induction) else 120.0)
        # Methods18/19 have no provider grace: search cannot spend the final reserve.

        def budget_stop(state=state, lw0=lw0, limit_s=limit_s):
            elapsed = L.clock() - t0 - lw0 - live_lock_wait(state)
            return elapsed >= limit_s if (a.bounded_debt or a.staged_induction) else elapsed > limit_s

        c = codex_call(out, r, prompt, thread, state,
                       max(1.0, tool_budget * 60) if (a.bounded_debt or a.staged_induction) else max(120.0, tool_budget * 60 + 120.0),
                       budget_stop=budget_stop if (a.budget_deadline or a.bounded_debt or a.staged_induction) else None)
        thread = c.get("thread") or thread
        tool = read_tool(state)
        rec = {"round": r, "started": L.now(), "phase_at_start": E.phase_of(best),
               "codex": {k: c.get(k) for k in ("exit", "wall_s", "usage", "usage_status", "completed_usage_receipts", "usage_fields_valid", "completion_deadline_met", "error", "killed_at_deadline", "stop_reason")}, "codex_notes": c.get("notes"), "codex_thread": thread, "tool": tool,
               "codex_calls": 1}
        best = E.load_working(out, counted_s=budget_s(t0), remaining_s=E.SEARCH_REMAINING_S[0]()) if (a.bounded_debt or a.staged_induction) else E.load_best(out)
        if a.terminal_full30 and c.get("ops"):
            O.CONTEXT[0] = {"kind": "final", "round": r, "pin": L.PIN,
                "source_sha256": L.sha(out / f"codex-r{r}" / "final.json")}
        if c.get("ops") and best["n_open"] > 0 and (T.PROOF_STOP_MIN if a.terminal_full30 else a.budget_min - a.final_reserve_min) - budget_s(t0) / 60 > 0.5:
            prov = f"codex {L.PIN['model']} {L.PIN['effort']} round {r} final answer"
            if a.terminal_full30:
                O.CONTEXT[0] = {"kind": "final", "round": r, "pin": L.PIN,
                    "source_sha256": L.sha(out / f"codex-r{r}" / "final.json")}
            fr, nb = E.attempt(out, best, c["ops"], f"r{r}f", prov, mode, a.round_timeout, allowed,
                               timeout_s=(max(1, int(E.SEARCH_REMAINING_S[0]())) if (a.bounded_debt or a.staged_induction) else
                                          max(60, int((a.budget_min - budget_s(t0) / 60) * 60))))
            rec["final_answer_edit"] = fr  # include checked time, artifacts and rollbacks, not only the score
            if nb is not None:
                E.save_best(out, nb)
                best = nb
        elif a.terminal_full30 and c.get("ops"):
            receipt = O.begin(out, best, c["ops"], f"r{r}f", refusal="final edit outside proof window or diagnostic goals already closed")
            rec["final_answer_edit"] = {"result": "refused before attempt", "ops": c["ops"],
                                        "provider_receipt_sha256": receipt["receipt_sha256"]}
        best = E.load_best(out)  # authoritative incumbent only; staged hints never decide a verdict
        rec["debt_status"] = E.debt_status(out) if (a.bounded_debt or a.staged_induction) else None
        rec["best_n_open"] = best["n_open"]
        rec["round_wp"] = {"n_failing": best["n_open"]}  # heartbeat compatibility
        if best["n_open"] == 0 and budget_s(t0) / 60 < a.budget_min and not a.terminal_full30:
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
        if a.terminal_full30 and (best["n_open"] == 0 or c.get("usage_status") != "complete"):
            break
        if a.staged_induction and thread is None:
            L.log(out, "provider returned no resumable conversation; no second fresh conversation is allowed")
            break
    if (a.bounded_debt or a.staged_induction):
        E.rollback_debt(out, "run ended", counted_s=budget_s(t0))
    best = E.load_best(out)
    negative = None
    origin_audit = O.audit(out, best, history) if a.terminal_full30 else None
    provider_usage = T.usage(history) if a.terminal_full30 else None
    if a.terminal_full30:
        final = (final_replay(out, r, best, a, t0, final_mode) if origin_audit["complete"]
                 else {"proven": False, "outcome": "scoped provider origin audit refused"})
        if final["proven"] and provider_usage["admissible"] and origin_audit["complete"]:
            negative = T.negative_replay(out, best, remaining_s=lambda: a.budget_min*60-budget_s(t0), mode=final_mode)
        proven = bool(final["proven"] and provider_usage["admissible"] and origin_audit["complete"] and negative and negative["negative_control_passed"])
    summary = {"proven": proven, "within_budget": proven and budget_s(t0) / 60 <= a.budget_min, "rounds": r,
               "codex_calls": r, "elapsed_min": round(budget_s(t0) / 60, 2),
               "lock_wait_excluded_s": round(L.LOCKWAIT[0], 1), "best_n_open": best["n_open"],
               "best_hints": len(best["hints"]), "best_sha256": L.sha(out / "best.json"),
               "tool_calls": sum((h.get("tool") or {}).get("calls", 0) for h in history[2:]),
               "show_goal_calls": sum((h.get("tool") or {}).get("show_goal_calls", 0) for h in history[2:]),
               "best_unit_hint_open": list(E.split_counts(best["failing_goals"])), "phase_at_end": E.phase_of(best),
               "wp_attempts": sum((h.get("tool") or {}).get("propose_calls", 0) for h in history[2:]) +
                              sum("wp_wall_s" in (h.get("final_answer_edit") or {}) for h in history),
               "proposal_attempts_including_final": sum((h.get("tool") or {}).get("propose_calls", 0) for h in history) +
                              sum(bool(h.get("final_answer_edit")) for h in history),
               "tokens": {}, "final": {k: v for k, v in (final or {}).items() if k != "failing_goals"} or None,
               "finished": L.now(), "bounded_debt": a.bounded_debt, "staged_induction": a.staged_induction,
               "method20": a.design_probes,
               "focused_calls": sum((h.get("tool") or {}).get("focused_calls",0) for h in history),
               "design_calls": sum((h.get("tool") or {}).get("design_calls",0) for h in history),
               "debt_events_sha256": L.sha(out / "debt-events.jsonl") if (out / "debt-events.jsonl").exists() else None}
    if a.fresh_baseline_start:
        summary["method23"] = True
    if a.terminal_full30:
        summary.update(method22=True, provider_usage=provider_usage, provider_origin=origin_audit, negative=negative)
    for h in history:
        for k, v in ((h.get("codex") or {}).get("usage") or {}).items():
            summary["tokens"][k] = summary["tokens"].get(k, 0) + v
    if a.diagnostic_baseline10:
        summary["method21"] = True
        summary["attempt_counts"] = R.attempt_counts(out, history)
        summary["legacy_wp_attempts_meaning"] = "Recorded proposal requests, not completed candidate proof runs; use attempt_counts."
    if a.terminal_full30:
        publication = T.publish(out, summary, counted_s=lambda: budget_s(t0), limit_min=a.budget_min)
        L.log(out, f"publication complete: {json.dumps(publication)}")
    else:
        (out / "summary.json").write_text(json.dumps(summary, indent=1))
    L.log(out, f"done: {json.dumps(summary)}")


if __name__ == "__main__":
    main()

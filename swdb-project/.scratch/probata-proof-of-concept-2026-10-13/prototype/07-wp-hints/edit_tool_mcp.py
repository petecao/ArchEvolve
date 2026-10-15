#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# The in-call check wrapper (map 13 item 6; t07c change d) for method change (a): Codex never submits
# a whole hint set, only an edit (<= edit_core.MAX_OPS operations) against the loop's best set.
#   check_edit(ops): edit rules + proof hint check (vocabulary, anchors, erase-and-diff, Frama-C parse,
#     WP goal generation) on best set + edit. Seconds. Nothing changes.
#   propose_edit(ops): check_edit, then round-mode WP on TDStep's goals and lemmas. The edit replaces
#     the best set only if the open-goal count does not rise; otherwise it is reverted. Minutes.
#   show_best(): the current best set and its open goals.
#   show_goal(goal) (t07e c1): one open goal as WP generates it (no prover). Seconds to a minute.
# t07e: two-phase acceptance (edit_core.TWO_PHASE) and the lock wait published live for the loop's
# budget-clock deadline (loop.LIVE_FILE).
# Reads only the stand-in, its headers and the loop's best.json. Shell stays disabled in Codex.
# Usage (by Codex, via -c mcp_servers.probata.*): edit_tool_mcp.py --state <dir>
import argparse, json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edit_core as E  # noqa: E402
import goal_print as G  # noqa: E402
import loop as L  # noqa: E402
import staged_search as S  # noqa: E402
import focused_probe as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--state", required=True)
A = ap.parse_args()
STATE = Path(A.state)
CFG = json.loads((STATE / "config.json").read_text())
OUT = Path(CFG["out"])
L.OWNER[0] = CFG.get("owner", "t07d")
PIN = CFG.get("pin") or L.PIN
L.BASELINE_PASSED.update(CFG.get("baseline_passed") or [])
ALLOWED = set(CFG["allowed_kinds"])
E.ACCEPT[0] = CFG.get("accept", "total")
E.CAP[0] = CFG.get("hint_cap", E.HINT_OPEN_CAP)
E.TWO_PHASE[0] = bool(CFG.get("two_phase"))
E.STAGED[0] = CFG.get("staged_search")
E.DEBT[0] = bool(CFG.get("bounded_debt") or E.STAGED[0])
L.CLOCK_KIND[0] = CFG.get("clock_kind", "wall")
if E.STAGED[0] and (L.CLOCK_KIND[0] != "continuous_monotonic" or CFG.get("clock_info") != S.clock_info()):
    raise RuntimeError("method19 tool clock does not match the master clock")
L.LIVE_FILE[0] = CFG.get("live_file")
SCHEMA = {"type": "object", "required": ["ops"], "properties": {"ops": {"type": "array", "items": E.OP_SCHEMA}}}
TOOLS = [
    {"name": "check_edit",
     "description": "Check an edit (1-%d operations add/delete/edit, each naming the open goal it targets) against the "
                    "active working set (otherwise incumbent): edit rules, vocabulary and anchors, erase-and-diff, Frama-C 33 parse, WP goal "
                    "generation. Seconds. Changes nothing." % E.MAX_OPS,
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "propose_edit",
     "description": "check_edit, then WP on TDStep's goals and the lemmas with best set + edit. If the number of open "
                    "goals does not rise, the edit is ACCEPTED and becomes the best set; otherwise it is REVERTED. "
                    "Returns the result and the open goals of the (new) best set. Minutes.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "show_best", "description": "The active working hint set (with ids) and open goals; temporary debt is explicitly separated from the checked incumbent.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True}},
]
if CFG.get("show_goal"):
    TOOLS.append(
        {"name": "show_goal",
         "description": "Print one OPEN goal of the best set as WP generates it after Qed simplification (hypotheses "
                        "'Assume'/'Have', conclusion 'Prove'), so you can see why it fails. No prover runs; nothing "
                        "changes. Up to about a minute.",
         "inputSchema": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}}},
         "annotations": {"readOnlyHint": True}})
if CFG.get("method20"):
    if not E.STAGED[0]:
        raise RuntimeError("method20 requires the strict counted staged-search policy")
    TOOLS += [
        {"name":"record_design", "description":"Record your own relation, scope, witness/lifetime, and invalidating operations for CAS history, queue phase, and consumed prefix. Required before proposal/probe. Design only, no proof credit.",
         "inputSchema":{"type":"object","required":["relations"],"properties":{"relations":{"type":"object"}}}},
        {"name":"focused_probe", "description":"Regenerate the exact active candidate inventory, then solve the selected ordinary TDStep goal's closed property class. All results diagnostic only: no scoring, promotion, milestones, debt/clock resets, or final acceptance. All time counts.",
         "inputSchema":{"type":"object","required":["goal"],"properties":{"goal":{"type":"string"}}}},
    ]
TOOL_NAMES = {t["name"] for t in TOOLS}


def budget_used_min():
    lw = CFG.get("lockwait_before_s", 0.0) + L.LOCKWAIT[0]
    return (L.clock() - CFG["t0"] - lw) / 60


def remaining_min():
    return CFG["budget_min"] - CFG["final_reserve_min"] - budget_used_min()


E.COUNTED_S[0] = lambda: budget_used_min() * 60
E.SEARCH_REMAINING_S[0] = lambda: remaining_min() * 60
if E.STAGED[0]:
    TOOLS[1]["description"] += (" Strict staged policy: +8 total temporary goals, four repair proposals/300 counted seconds; last phase recovery only; unchanged incumbent until total recovery. Every final goal and fresh smoke remains mandatory.")
elif E.DEBT[0]:
    TOOLS[1]["description"] += (" Method18: temporary +4 hint debt uses a separate working candidate for at most "
                                "4 repair proposals/5 counted minutes; no unit regression. Promotion recovers "
                                "the incumbent rule; otherwise rollback. Final full proof/smoke acceptance is unchanged.")

N = [0]


def record(tool, rec):
    N[0] += 1
    rec = {"n": N[0], "tool": tool, "lockwait_total_s": L.LOCKWAIT[0], "clock": L.CLOCK_KIND[0],
           "clock_info": S.clock_info() if E.STAGED[0] else None,
           "search_phase": S.phase(E.STAGED[0], budget_used_min()*60) if E.STAGED[0] else None,
           "budget_used_min": round(budget_used_min(), 2), **rec}
    with open(STATE / "submissions.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")


def fmt_rec(rec):
    out = [f"Result: {rec['result']}"]
    for p in rec.get("problems") or []:
        out.append(f"  - op {p[0]}: {p[1]} {p[2]}")
    for x in rec.get("rejections") or []:
        out.append(f"  - {x['id']}: {x['rule']} {x.get('detail', '')}")
    if rec.get("parse_error"):
        out.append("Frama-C output (it stops at the first error):\n" + rec["parse_error"][-2000:])
        if rec.get("blame_text"):
            out.append(rec["blame_text"])
    if rec.get("log_tail"):
        out.append("WP log tail:\n" + rec["log_tail"])
    if rec.get("result", "").startswith("reverted (") and rec.get("failing_goals") is not None:
        fg = rec["failing_goals"]
        base = E.load_working(OUT, counted_s=budget_used_min() * 60, remaining_s=remaining_min() * 60) if E.DEBT[0] else E.load_best(OUT)
        best_names = {g["goal"] for g in base["failing_goals"]}
        new = [g for g in fg if g["goal"] not in best_names]
        out.append(f"Goals your edit newly left open ({len(new)}; first 40):")
        out.append(L.positions_text(new[:40], E.apply(rec["ops"], base, rec["tag"], "")))
    return "\n".join(out)


def call(tool, args):
    phase_note = ""
    if E.STAGED[0]:
        phase = S.phase(E.STAGED[0], budget_used_min()*60)
        phase_note = f"\nMETHOD{20 if CFG.get('method20') else 19} PHASE {phase['index']+1}/3: {phase['name']}; " + phase['guidance']
    best = E.load_working(OUT, counted_s=budget_used_min() * 60, remaining_s=remaining_min() * 60) if E.DEBT[0] else E.load_best(OUT)
    if tool == "show_best":
        return E.working_text(OUT, best) + "\n" + E.open_text(best) + E.debt_text(OUT) + phase_note + f"\nBudget left for in-call work: {remaining_min():.1f} min."
    if remaining_min() <= 0:
        record(tool, {"result": "refused: budget"})
        return (f"Budget for in-call work is spent ({budget_used_min():.1f} of {CFG['budget_min']} min used; "
                f"{CFG['final_reserve_min']} min are kept for the final replay). Return your final answer NOW.")
    if CFG.get("method20") and tool == "record_design":
        rec=F.record_design(OUT,args.get("relations"))
        record(tool,{"result":"design recorded",**rec})
        return "Design recorded, with no proof credit. Author your concrete hints; only full checked rounds can promote."
    if CFG.get("method20") and tool == "focused_probe" and not F.has_design(OUT):
        record(tool,{"result":"refused: state design missing"})
        return "First record your own structured state design using record_design. No concrete hints are supplied."
    tag = f"r{CFG['round']}c{N[0] + 1}"
    if tool == "focused_probe":
        rec=F.run(OUT,best,str(args.get("goal","")),tag,
                  remaining_s=lambda:max(0,E.search_remaining(OUT)),round_timeout=CFG["round_timeout"])
        record(tool,rec)
        if E.DEBT[0]:
            E.load_working(OUT,counted_s=budget_used_min()*60,remaining_s=remaining_min()*60)
        display={k:v for k,v in rec.items() if k not in ("selected","unselected_obligations")}
        display['selected']=[{k:g.get(k) for k in ('goal','passed','verdict')} for g in rec['selected']]
        display['unselected_obligations_count']=len(rec['unselected_obligations'])
        return json.dumps(display,indent=2)+f"\nCounted budget left: {remaining_min():.1f} min."
    if tool == "show_goal":
        t = L.clock()
        text, rec = G.show(OUT, best, str(args.get("goal", "")), tag,
                           **({"timeout_s": max(1, E.search_remaining(OUT))} if E.DEBT[0] else {}))
        rec["wall_s"] = round(L.clock() - t, 1)
        record(tool, rec)
        if E.DEBT[0]:
            E.load_working(OUT, counted_s=budget_used_min() * 60, remaining_s=remaining_min() * 60)
        return text + E.debt_text(OUT) + phase_note + f"\nBudget left for in-call work: {remaining_min():.1f} min."
    ops = args.get("ops") or []
    prov = f"codex {PIN['model']} {PIN['effort']} round {CFG['round']} tool call {N[0] + 1}"
    t = L.clock()
    rec, nb = E.attempt(OUT, best, ops, tag, prov, CFG["mode"], CFG["round_timeout"], ALLOWED,
                        run_wp=(tool == "propose_edit"), timeout_s=(max(1, int(remaining_min() * 60)) if E.DEBT[0] else max(60, int(remaining_min() * 60) + 120)))
    rec["wall_s"] = round(L.clock() - t, 1)
    if nb is not None:
        E.save_best(OUT, nb)
    record(tool, rec)
    text = fmt_rec(rec)
    if nb is not None and E.phase_of(nb) == 2 and E.phase_of(best) == 1:
        text += ("\nPHASE 2 STARTS NOW: every unit goal is proven. From now on an edit is accepted only if every unit goal "
                 "stays proven and the number of open hint goals does not rise.")
    if nb is not None and nb["n_open"] == 0:
        return text + ("\nALL goals proven in round mode. Return your final answer now with an empty ops list; "
                       "the loop runs the fresh full replay.")
    cur = E.load_working(OUT, counted_s=budget_used_min() * 60, remaining_s=remaining_min() * 60) if E.DEBT[0] else E.load_best(OUT)
    if tool == "propose_edit":
        text += "\n" + E.open_text(cur)
        if nb is not None or rec.get("result", "").startswith("staged"):
            text += "\n" + E.working_text(OUT, cur)
    return text + E.debt_text(OUT) + phase_note + f"\nBudget left for in-call work: {remaining_min():.1f} min."


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    mid, method = msg.get("id"), msg.get("method")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}}, "serverInfo": {"name": "probata-edit-check", "version": "0.1"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        p = msg.get("params") or {}
        try:
            if p.get("name") not in TOOL_NAMES:
                raise ValueError(f"unknown tool {p.get('name')}")
            text, err = call(p["name"], p.get("arguments") or {}), False
        except Exception as e:  # noqa: BLE001
            text, err = f"tool error: {type(e).__name__}: {e}", True
            with open(STATE / "server_errors.log", "a") as f:
                f.write(traceback.format_exc() + "\n")
        send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})
    elif mid is not None:
        send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not supported: {method}"}})

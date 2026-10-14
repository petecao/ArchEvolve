#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# The in-call check wrapper (map 13 item 6; t07c change d) for method change (a): Codex never submits
# a whole hint set, only an edit (<= edit_core.MAX_OPS operations) against the loop's best set.
#   check_edit(ops): edit rules + proof hint check (vocabulary, anchors, erase-and-diff, Frama-C parse,
#     WP goal generation) on best set + edit. Seconds. Nothing changes.
#   propose_edit(ops): check_edit, then round-mode WP on TDStep's goals and lemmas. The edit replaces
#     the best set only if the open-goal count does not rise; otherwise it is reverted. Minutes.
#   show_best(): the current best set and its open goals.
# Reads only the stand-in, its headers and the loop's best.json. Shell stays disabled in Codex.
# Usage (by Codex, via -c mcp_servers.probata.*): edit_tool_mcp.py --state <dir>
import argparse, json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edit_core as E  # noqa: E402
import loop as L  # noqa: E402

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
SCHEMA = {"type": "object", "required": ["ops"], "properties": {"ops": {"type": "array", "items": E.OP_SCHEMA}}}
TOOLS = [
    {"name": "check_edit",
     "description": "Check an edit (1-%d operations add/delete/edit, each naming the open goal it targets) against the "
                    "current best hint set: edit rules, vocabulary and anchors, erase-and-diff, Frama-C 33 parse, WP goal "
                    "generation. Seconds. Changes nothing." % E.MAX_OPS,
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "propose_edit",
     "description": "check_edit, then WP on TDStep's goals and the lemmas with best set + edit. If the number of open "
                    "goals does not rise, the edit is ACCEPTED and becomes the best set; otherwise it is REVERTED. "
                    "Returns the result and the open goals of the (new) best set. Minutes.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "show_best", "description": "The current best hint set (with ids) and its open goals.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True}},
]


def budget_used_min():
    lw = CFG.get("lockwait_before_s", 0.0) + L.LOCKWAIT[0]
    return (time.time() - CFG["t0"] - lw) / 60


def remaining_min():
    return CFG["budget_min"] - CFG["final_reserve_min"] - budget_used_min()


N = [0]


def record(tool, rec):
    N[0] += 1
    rec = {"n": N[0], "tool": tool, "lockwait_total_s": round(L.LOCKWAIT[0], 1),
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
        best_names = {g["goal"] for g in E.load_best(OUT)["failing_goals"]}
        new = [g for g in fg if g["goal"] not in best_names]
        out.append(f"Goals your edit newly left open ({len(new)}; first 40):")
        out.append(L.positions_text(new[:40], E.apply(rec["ops"], E.load_best(OUT), rec["tag"], "")))
    return "\n".join(out)


def call(tool, args):
    best = E.load_best(OUT)
    if tool == "show_best":
        return E.best_text(best) + "\n" + E.open_text(best) + f"\nBudget left for in-call work: {remaining_min():.1f} min."
    if remaining_min() <= 0:
        record(tool, {"result": "refused: budget"})
        return (f"Budget for in-call work is spent ({budget_used_min():.1f} of {CFG['budget_min']} min used; "
                f"{CFG['final_reserve_min']} min are kept for the final replay). Return your final answer NOW.")
    ops = args.get("ops") or []
    tag = f"r{CFG['round']}c{N[0] + 1}"
    prov = f"codex {PIN['model']} {PIN['effort']} round {CFG['round']} tool call {N[0] + 1}"
    t = time.time()
    rec, nb = E.attempt(OUT, best, ops, tag, prov, CFG["mode"], CFG["round_timeout"], ALLOWED,
                        run_wp=(tool == "propose_edit"), timeout_s=max(60, int(remaining_min() * 60) + 120))
    rec["wall_s"] = round(time.time() - t, 1)
    if nb is not None:
        E.save_best(OUT, nb)
    record(tool, rec)
    text = fmt_rec(rec)
    if nb is not None and nb["n_open"] == 0:
        return text + ("\nALL goals proven in round mode. Return your final answer now with an empty ops list; "
                       "the loop runs the fresh full replay.")
    cur = E.load_best(OUT)
    if tool == "propose_edit":
        text += "\n" + E.open_text(cur)
        if nb is not None:
            text += "\n" + E.best_text(cur)
    return text + f"\nBudget left for in-call work: {remaining_min():.1f} min."


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
            if p.get("name") not in ("check_edit", "propose_edit", "show_best"):
                raise ValueError(f"unknown tool {p.get('name')}")
            text, err = call(p["name"], p.get("arguments") or {}), False
        except Exception as e:  # noqa: BLE001
            text, err = f"tool error: {type(e).__name__}: {e}", True
            with open(STATE / "server_errors.log", "a") as f:
                f.write(traceback.format_exc() + "\n")
        send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})
    elif mid is not None:
        send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not supported: {method}"}})

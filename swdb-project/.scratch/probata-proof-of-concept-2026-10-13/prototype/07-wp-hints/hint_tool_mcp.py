#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation t07c), throwaway. Created 2026-10-14 ET.
# Method change (d): the in-call check wrapper of map 13 item 6, as an MCP stdio server that Codex
# calls while its shell tool stays disabled. Two tools, both frozen:
#   check_hints(hints): the proof hint check (vocabulary, anchors, erase-and-diff, Frama-C parse,
#     WP goal generation). Seconds.
#   prove_hints(hints): the check, then round-mode WP (TDStep's goals and the lemmas, no smoke tests,
#     round timeout, run-local cache). Minutes. Never a verdict: the loop's fresh full replay decides.
# The server reads only the stand-in and its headers. Every call is appended to
# <state>/submissions.jsonl (hints, result, lock wait), which the loop reads afterwards.
# Usage (by Codex, via -c mcp_servers.probata.*): hint_tool_mcp.py --state <dir>
import argparse, json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hints as H  # noqa: E402
import loop as L  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--state", required=True)
A = ap.parse_args()
STATE = Path(A.state)
CFG = json.loads((STATE / "config.json").read_text())
OUT = Path(CFG["out"])
STANDIN = Path(CFG["standin"]).read_text()
L.OWNER[0] = CFG.get("owner", "t07c")
PIN = CFG.get("pin") or L.PIN
L.BASELINE_PASSED.update(CFG.get("baseline_passed") or [])
HINT_ITEM = {"type": "object", "additionalProperties": False, "required": ["anchor", "kind", "text"],
             "properties": {"anchor": {"type": "string"}, "kind": {"type": "string", "enum": sorted(H.KINDS)},
                            "text": {"type": "string"}}}
SCHEMA = {"type": "object", "required": ["hints"],
          "properties": {"hints": {"type": "array", "items": HINT_ITEM}}}
TOOLS = [
    {"name": "check_hints",
     "description": "Proof hint check of a COMPLETE hint set: vocabulary and anchors, erase-and-diff, Frama-C 33 "
                    "parse and type check, WP goal generation. Returns 'check passed' or the errors, each traced to "
                    "the hint that holds it. Takes seconds. Runs no prover.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "prove_hints",
     "description": "check_hints, then WP on TDStep's goals and your lemmas (Alt-Ergo, Z3, CVC5; round timeout; no "
                    "smoke tests). Returns how many goals were proven and every goal not proven with kind, merged-file "
                    "line, source line and the hint holding it, plus the budget left. Takes minutes.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
]


def budget_used_min():
    # Loop budget clock: wall time since the loop's t0, minus lock waits (loop's before this call + ours).
    lw = CFG.get("lockwait_before_s", 0.0) + L.LOCKWAIT[0]
    return (time.time() - CFG["t0"] - lw) / 60


def remaining_min():
    return CFG["budget_min"] - CFG["final_reserve_min"] - budget_used_min()


N = [0]


def record(tool, hints, result, extra):
    N[0] += 1
    rec = {"n": N[0], "time": L.now(), "tool": tool, "hints": hints, "result": result,
           "lockwait_total_s": round(L.LOCKWAIT[0], 1), "budget_used_min": round(budget_used_min(), 2), **extra}
    with open(STATE / "submissions.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def tag_hints(raw):  # ids r<round>c<call>h<i>
    return [{"id": f"r{CFG['round']}c{N[0] + 1}h{i}", "anchor": h.get("anchor"), "kind": h.get("kind"),
             "text": h.get("text", ""), "provenance": f"codex {PIN['model']} {PIN['effort']} round {CFG['round']} "
             f"tool call {N[0] + 1}"} for i, h in enumerate(raw, 1)]


def run_check(hs, name):
    chk = {}
    d = L.precheck(OUT, name, STANDIN, hs, chk)
    if d is not None:
        return d, "check passed (vocabulary, erase-and-diff, Frama-C parse, WP goal generation)."
    msg = [f"check FAILED: {chk.get('outcome')}"]
    msg += [f"- {x['id']}: {x['rule']} {x.get('detail', '')}" for x in chk.get("rejections") or []]
    if chk.get("parse_error"):
        msg.append("Frama-C output (it stops at the first error; look for the same mistake elsewhere):")
        msg.append(chk["parse_error"][-2500:])
        msg.append(L.blame_text(chk))
    return None, "\n".join(msg)


def call(tool, args):
    raw = args.get("hints") or []
    hs = tag_hints(raw)
    left = remaining_min()
    name = f"round-{CFG['round']}-call{N[0] + 1}"
    if left <= 0:
        text = (f"Budget for in-call checks is spent ({budget_used_min():.1f} of {CFG['budget_min']} min used; "
                f"{CFG['final_reserve_min']} min are kept for the final replay). Return your best hint set NOW.")
        record(tool, hs, "refused: budget", {})
        return text
    t = time.time()
    d, text = run_check(hs, name)
    if d is None or tool == "check_hints":
        record(tool, hs, "check passed" if d is not None else "check failed", {"wall_s": round(time.time() - t, 1)})
        return text + f"\nBudget left for in-call work: {remaining_min():.1f} min."
    wlog, ws = L.verifier(OUT, d, "round", timeout=max(60, int(remaining_min() * 60) + 120),
                          extra=(OUT / "round-cache", CFG["round_timeout"]))
    ar = L.assess_round(d, wlog)
    extra = {"wall_s": round(time.time() - t, 1), "dir": str(d), "wp_wall_s": ws["wall_s"],
             "peak_rss_mb": ws["peak_rss_mb"], "n_goals": ar["n_goals"], "n_failing": len(ar["failing_goals"]),
             "timed_out": ws.get("timed_out")}
    if ws["exit_code"] != 0 or ar["n_tdstep_goals"] == 0:
        record(tool, hs, "wp failed", extra)
        return (f"WP run failed (exit {ws['exit_code']}{', timed out' if ws.get('timed_out') else ''}). Log tail:\n"
                + wlog.read_text(errors="replace")[-2500:] + f"\nBudget left: {remaining_min():.1f} min.")
    if ar["ok"]:
        record(tool, hs, "all proven (round mode)", extra)
        return (f"ALL {ar['n_goals']} goals proven in round mode ({CFG['round_timeout']} s per prover). "
                "Return exactly this hint set now as your final answer; the loop then runs the fresh full replay.")
    record(tool, hs, "not all proven", extra)
    return (f"{ar['n_passed']} of {ar['n_goals']} goals proven ({CFG['round_timeout']} s per prover). Not proven "
            f"({len(ar['failing_goals'])}): goal [failure class] kind at file:line (merged file): source line | hint\n"
            + L.positions_text(ar["failing_goals"], hs)
            + f"\nWP wall time {ws['wall_s']:.0f} s. Budget left for in-call work: {remaining_min():.1f} min.")


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
            "capabilities": {"tools": {}}, "serverInfo": {"name": "probata-hint-check", "version": "0.1"}}})
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        p = msg.get("params") or {}
        try:
            if p.get("name") not in ("check_hints", "prove_hints"):
                raise ValueError(f"unknown tool {p.get('name')}")
            text, err = call(p["name"], p.get("arguments") or {}), False
        except Exception as e:  # noqa: BLE001
            text, err = f"tool error: {type(e).__name__}: {e}", True
            with open(STATE / "server_errors.log", "a") as f:
                f.write(traceback.format_exc() + "\n")
        send({"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})
    elif mid is not None:
        send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not supported: {method}"}})

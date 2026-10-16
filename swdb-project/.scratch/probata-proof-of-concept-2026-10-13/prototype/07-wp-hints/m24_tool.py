#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# The in-call tools of method24 (map 13 item 6), an MCP stdio server Codex calls while its shell stays
# disabled. Frozen; reads only the stand-in, its headers and this run's state.
#   falsify_hints(hints): vocabulary check, then the bounded falsifier (falsify/): every assert, loop
#     invariant, loop variant and loop assigns evaluated on 2000 concrete runs. Seconds.
#   check_hints(hints): the proof hint check (vocabulary, anchors, erase-and-diff, Frama-C parse, WP goal
#     generation). Seconds.
#   prove_hints(hints): falsify, check, then WP on TDStep's goals and the lemmas with the timeout ladder
#     (3 s, then 10 s when at most 40 goals stay open; -wp-split-conj; run-local cache). Minutes. The best set so far
#     is kept as the incumbent. Never a verdict: the driver's fresh final replay decides.
#   show_goal(goal): one open goal of the incumbent as WP generates it (no prover).
# Every call is appended to <state>/submissions.jsonl.
# Usage (by Codex, via -c mcp_servers.probata.*): m24_tool.py --state <dir>
import argparse, json, sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "falsify"))
import hints as H  # noqa: E402
import loop as L  # noqa: E402
import goal_print as G  # noqa: E402
import falsify as F  # noqa: E402

HINT_ITEM = {"type": "object", "additionalProperties": False, "required": ["anchor", "kind", "text"],
             "properties": {"anchor": {"type": "string"}, "kind": {"type": "string", "enum": sorted(H.KINDS)},
                            "text": {"type": "string"}}}
SCHEMA = {"type": "object", "required": ["hints"], "properties": {"hints": {"type": "array", "items": HINT_ITEM}}}
TOOLS = [
    {"name": "falsify_hints",
     "description": "Bounded falsifier on a COMPLETE hint set: evaluates every assert, loop invariant, loop variant "
                    "and loop assigns on 2000 concrete executions of TDStep (num_nodes <= 4, num_edges <= 6, "
                    "TILE_SIZE <= 3). A hint reported FALSE is false (a concrete counterexample is shown); a hint not "
                    "refuted may still be false or unprovable. Seconds. Runs no prover.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "check_hints",
     "description": "Proof hint check of a COMPLETE hint set: vocabulary and anchors, erase-and-diff, Frama-C 33 parse "
                    "and type check, WP goal generation. Seconds. Runs no prover.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "prove_hints",
     "description": "falsify_hints, check_hints, then WP on TDStep's goals and your lemmas (Alt-Ergo, Z3, CVC5; 3 s per "
                    "prover, then 10 s when at most 40 goals stay open; conjunctions split into separate goals). Returns every goal "
                    "not proven with kind, merged-file line, source line and the hint holding it. Minutes. A set with "
                    "a refuted hint is not sent to WP.",
     "inputSchema": SCHEMA, "annotations": {"readOnlyHint": True}},
    {"name": "show_goal",
     "description": "Print one open goal of the best set so far as WP generates it (hypotheses and conclusion, no "
                    "prover). Argument: {\"goal\": \"typed_TDStep_...\"}. Seconds to a minute.",
     "inputSchema": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}}},
     "annotations": {"readOnlyHint": True}},
]


def no_strategies(hs):
    """Method26: strategy hints are inert without the `tip` prover, so they are refused up front."""
    return [{"id": h["id"], "rule": "strategy_not_used",
             "detail": "WP strategies are not applied in this run (no tip prover); remove this hint"}
            for h in hs if h.get("kind") in ("strategy", "proof")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    a = ap.parse_args()
    server = Server(Path(a.state))
    server.serve(sys.stdin, sys.stdout)


class Server:
    def __init__(self, state):
        self.state = state
        self.cfg = json.loads((state / "config.json").read_text())
        self.out = Path(self.cfg["out"])
        self.standin = (L.STANDIN_DIR / L.UNIT).read_text()
        L.OWNER[0] = self.cfg.get("owner", "t07f")
        self.pin = self.cfg.get("pin") or L.PIN
        self.n = 0
        self.fz = F.Falsifier(L.STANDIN_DIR, self.out / f"falsifier-r{self.cfg['round']}")

    # ---- budget ----
    def used_min(self):
        return (time.time() - self.cfg["t0"] - self.cfg.get("lockwait_before_s", 0.0) - L.LOCKWAIT[0]) / 60

    def left_min(self):
        return self.cfg["budget_min"] - self.cfg["final_reserve_min"] - self.used_min()

    def record(self, tool, hints, result, **extra):
        rec = {"n": self.n, "time": L.now(), "tool": tool, "hints": hints, "result": result,
               "lockwait_total_s": round(L.LOCKWAIT[0], 2), "budget_used_min": round(self.used_min(), 2), **extra}
        with open(self.state / "submissions.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")

    def tag(self, raw):
        r = self.cfg["round"]
        return [{"id": f"r{r}c{self.n}h{i}", "anchor": h.get("anchor"), "kind": h.get("kind"),
                 "text": h.get("text", ""),
                 "provenance": f"codex {self.pin['model']} {self.pin['effort']} {self.cfg.get('method', 'method24')} round {r} tool call {self.n}"}
                for i, h in enumerate(raw, 1)]

    def incumbent(self):
        f = self.state / "best.json"
        return json.loads(f.read_text()) if f.exists() else None

    # ---- tools ----
    def falsify(self, hs):
        bad = no_strategies(hs) or H.check(self.standin, hs)
        if bad:
            return None, "Rejected by the vocabulary check:\n" + "\n".join(
                f"- {x['id']}: {x['rule']} {x.get('detail', '')}" for x in bad)
        res = self.fz.run(hs)
        n_ref = sum(1 for r in res.values() if r["verdict"] == "refuted")
        return res, (f"{n_ref} hint(s) refuted on concrete executions.\n" if n_ref else
                     "No hint refuted on the 2000 bounded executions.\n") + F.report_text(hs, res)

    def check(self, hs, name):
        bad = no_strategies(hs)
        if bad:
            return None, "check FAILED: " + "; ".join(f"{x['id']}: {x['detail']}" for x in bad)
        rec = {}
        d = L.precheck(self.out, name, self.standin, hs, rec)
        if d is not None:
            return d, "check passed (vocabulary, erase-and-diff, Frama-C parse, WP goal generation)."
        msg = [f"check FAILED: {rec.get('outcome')}"]
        msg += [f"- {x['id']}: {x['rule']} {x.get('detail', '')}" for x in rec.get("rejections") or []]
        if rec.get("parse_error"):
            msg.append("Frama-C output (it stops at the first error; look for the same mistake elsewhere):")
            msg.append(rec["parse_error"][-2500:])
            msg.append(L.blame_text(rec))
        return None, "\n".join(msg)

    def prove(self, hs, name):
        res, ftext = self.falsify(hs)
        if res is None or any(r["verdict"] == "refuted" for r in res.values()):
            self.record("prove_hints", hs, "refused: falsifier", falsifier=ftext[:4000])
            return "Not sent to WP. " + ftext
        d, ctext = self.check(hs, name)
        if d is None:
            self.record("prove_hints", hs, "check failed")
            return ctext
        t = time.time()
        ladder = self.cfg["ladder"]
        runs = []
        ar = None
        for k, tmo in enumerate(ladder):
            if k and ar and (not ar["failing_goals"] or
                             len(ar["failing_goals"]) > self.cfg.get("second_rung_max_open", 40)):
                break
            remaining_s = max(60, int(self.left_min() * 60))
            wlog, ws = L.verifier(self.out, d, "round24p", timeout=remaining_s + 60,
                                  extra=(self.out / "round-cache", tmo))
            if ws["exit_code"] != 0:
                self.record("prove_hints", hs, "wp failed", dir=str(d), wp=ws)
                return (f"WP run failed (exit {ws['exit_code']}{', timed out' if ws.get('timed_out') else ''}). Log "
                        "tail:\n" + wlog.read_text(errors="replace")[-2500:])
            ar = L.assess_round(d, wlog)
            runs.append({"timeout_s": tmo, "wall_s": ws["wall_s"], "open": len(ar["failing_goals"]),
                         "n_goals": ar["n_goals"], "peak_rss_mb": ws["peak_rss_mb"]})
        n_open = len(ar["failing_goals"])
        best = self.incumbent()
        accepted = best is None or n_open < best["n_open"] or (n_open == best["n_open"] and len(hs) < len(best["hints"]))
        if accepted:
            best = {"hints": hs, "n_open": n_open, "n_goals": ar["n_goals"], "failing_goals": ar["failing_goals"],
                    "dir": str(d), "from_call": self.n}
            (self.state / "best.json").write_text(json.dumps(best, indent=1))
        self.record("prove_hints", hs, "all proven (round mode)" if n_open == 0 else "not all proven",
                    dir=str(d), runs=runs, n_open=n_open, n_goals=ar["n_goals"], accepted=accepted,
                    wall_s=round(time.time() - t, 1))
        head = (f"{'This set is now the best set' if accepted else 'Best set unchanged (it has ' + str(best['n_open']) + ' open goals)'}. "
                f"WP: " + ", ".join(f"{r['open']} open at {r['timeout_s']} s ({r['wall_s']:.0f} s)" for r in runs) + ".\n")
        if n_open == 0:
            return head + (f"ALL {ar['n_goals']} goals proven in round mode. Return exactly this hint set now as your "
                           "final answer; the driver then runs the fresh full replay (all functions, 30 s, smoke tests).")
        return (head + f"{ar['n_passed']} of {ar['n_goals']} goals proven. Not proven ({n_open}): goal [failure class] "
                "kind at file:line (merged file): source line | hint\n" + L.positions_text(ar["failing_goals"], hs)
                + "\nFalsifier: no hint refuted on the bounded executions (they may still be false outside them).")

    def show_goal(self, goal):
        best = self.incumbent()
        if best is None:
            return "No best set yet: run prove_hints first."
        text, rec = G.show(self.out, best, goal, f"r{self.cfg['round']}c{self.n}", timeout_s=300)
        self.record("show_goal", [], rec.get("result"), goal=goal)
        return text

    def call(self, tool, args):
        self.n += 1
        if self.left_min() <= 0:
            self.record(tool, [], "refused: budget")
            return (f"The in-call budget is spent ({self.used_min():.1f} min used; {self.cfg['final_reserve_min']} min "
                    "are kept for the final replay). Return your best hint set NOW.")
        if tool == "show_goal":
            text = self.show_goal(args.get("goal", ""))
        else:
            hs = self.tag(args.get("hints") or [])
            name = f"r{self.cfg['round']}-c{self.n}"
            if tool == "falsify_hints":
                _, text = self.falsify(hs)
                self.record(tool, hs, "falsified", report=text[:4000])
            elif tool == "check_hints":
                d, text = self.check(hs, name)
                self.record(tool, hs, "check passed" if d is not None else "check failed")
            else:
                text = self.prove(hs, name)
        return text + f"\nIn-call budget left: {self.left_min():.1f} min."

    def serve(self, fin, fout):
        def send(obj):
            fout.write(json.dumps(obj) + "\n")
            fout.flush()
        for line in fin:
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
                    "capabilities": {"tools": {}}, "serverInfo": {"name": "probata-m24", "version": "0.1"}}})
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
            elif method == "tools/call":
                p = msg.get("params") or {}
                try:
                    if p.get("name") not in {t["name"] for t in TOOLS}:
                        raise ValueError(f"unknown tool {p.get('name')}")
                    text, err = self.call(p["name"], p.get("arguments") or {}), False
                except Exception as e:  # noqa: BLE001
                    text, err = f"tool error: {type(e).__name__}: {e}", True
                    with open(self.state / "server_errors.log", "a") as f:
                        f.write(traceback.format_exc() + "\n")
                send({"jsonrpc": "2.0", "id": mid,
                      "result": {"content": [{"type": "text", "text": text}], "isError": err}})
            elif mid is not None:
                send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"not supported: {method}"}})


if __name__ == "__main__":
    main()

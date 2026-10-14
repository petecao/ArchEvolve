# PROTOTYPE (Probata PoC ticket 07, continuation 3 "t07e"), throwaway. Created 2026-10-14 ET.
# Method change (c1): the in-call tool show_goal(goal) prints one open goal of the best set as WP
# generates it (after Qed simplification, no prover, nothing proven: wp_run.sh print). A human WP user
# reads the failed goal before fixing an invariant; the agent so far saw only the goal's name and line.
# Reads only the best set's merged stand-in. Never a verdict.
import re
from pathlib import Path

import hints as H
import loop as L

TAGS = {"assigns": "@assigns", "loop assigns": "@assigns", "loop invariant established": "@invariant",
        "loop invariant preserved": "@invariant", "assert": "@assert", "check": "@check", "ensures": "@ensures",
        "loop variant": "@variant", "terminates": "@terminates"}
MAX_CHARS = 14000
_NOISE = re.compile(r"^(\S+:\d+: warning from Typed Model:|\s+- Warning: Hide sub-term definition|\s+Reason: Cast with)")


def selection(goal, kind):
    if goal.startswith("typed_lemma_"):
        return "-wp-prop=" + goal[len("typed_lemma_"):]
    tag = TAGS.get(kind)
    return "-wp-fct TDStep" + (f" -wp-prop={tag}" if tag else "")


def blocks(text):
    """[(header, body)] of the goals in a -wp-print log."""
    out, cur = [], None
    for ln in text.splitlines():
        if ln.startswith("Goal ") and ln.rstrip().endswith(":"):
            if cur:
                out.append(cur)
            cur = [ln, []]
        elif cur is not None:
            if ln.startswith("-" * 40):
                out.append(cur)
                cur = None
            elif not _NOISE.match(ln):
                cur[1].append(ln)
    if cur:
        out.append(cur)
    return [(h, "\n".join(b)) for h, b in out]


def pick(bl, g):
    """Blocks matching the goal: same line; part number, establishment/preservation and names as tie breaks."""
    name, line = g["goal"], int(g.get("line") or 0)
    if name.startswith("typed_lemma_"):
        lem = name[len("typed_lemma_"):]
        return [b for b in bl if f"'{lem}'" in b[0]] or bl[:1]
    cand = [b for b in bl if re.search(rf"line {line}\b", b[0])]
    if name.endswith("_established"):
        cand = [b for b in cand if "Establishment" in b[0]] or cand
    elif name.endswith("_preserved"):
        cand = [b for b in cand if "Preservation" in b[0]] or cand
    m = re.search(r"_part(\d+)$", name)
    if m and len(cand) > 1:
        k = int(m.group(1))
        exact = [b for b in cand if re.search(rf"\({k}/\d+\):$", b[0].rstrip())]
        cand = exact or [b for b in cand if re.search(rf"\({k + 1}/\d+\):$", b[0].rstrip())] or cand
    if len(cand) > 1:
        toks = [t for t in name.split("_") if len(t) > 2 and t not in ("typed", "TDStep", "loop", "invariant",
                                                                          "preserved", "established", "call")]
        scored = sorted(cand, key=lambda b: -sum(t in b[0] for t in toks))
        cand = scored[:2]
    return cand


def show(out, best, goal_name, tag, timeout_s=600):
    """Returns (text, record) for the tool."""
    g = next((x for x in best["failing_goals"] if x["goal"] == goal_name), None)
    if g is None:
        return f"{goal_name!r} is not an open goal of the best set.", {"result": "refused: goal not open"}
    merged = (Path(best["dir"]) / L.UNIT).read_text()
    d = L.run_dir(Path(out), f"goal-{tag}", merged)
    sel = selection(goal_name, g.get("kind") or H.goal_kind(goal_name))
    logf, ws = L.verifier(Path(out), d, "print", timeout=timeout_s, extra=(sel,))
    text = logf.read_text(errors="replace")
    found = pick(blocks(text), g)
    rec = {"result": f"printed {len(found)} goal block(s)", "goal": goal_name, "selection": sel, "dir": str(d),
           "wall_s": ws["wall_s"], "exit": ws["exit_code"], "log_sha256": ws["log_sha256"]}
    if ws["exit_code"] != 0 or not found:
        return (f"Could not print {goal_name} (WP exit {ws['exit_code']}, {len(found)} matching goals).",
                {**rec, "result": "print failed"})
    parts = []
    per = MAX_CHARS // len(found)
    for h, body in found:
        if len(body) > per:
            body = f"[... {len(body) - per} characters of earlier hypotheses cut ...]\n" + body[-per:]
        parts.append(h + "\n" + body)
    head = (f"WP goal for {goal_name} ({g.get('kind')} at merged line {g.get('line')}), as WP generates it after Qed "
            "simplification (no prover ran; 'Assume'/'Have' are hypotheses, 'Prove' is the conclusion):\n")
    return head + "\n\n".join(parts), rec

# PROTOTYPE (Probata PoC ticket 07, continuation 3 "t07e"), throwaway. Created 2026-10-14 ET.
# Method change (c1): the in-call tool show_goal(goal) prints one open goal of the best set as WP
# generates it (after Qed simplification, no prover, nothing proven: wp_run.sh print). A human WP user
# reads the failed goal before fixing an invariant; the agent so far saw only the goal's name and line.
# Reads only the best set's merged stand-in. Never a verdict.
import hashlib
import json
import re
from pathlib import Path

import hints as H
import loop as L

TAGS = {"assigns": "@assigns", "loop assigns": "@assigns", "loop invariant established": "@invariant",
        "loop invariant preserved": "@invariant", "assert": "@assert", "check": "@check", "ensures": "@ensures",
        "loop variant": "@variant"}  # t07e run 10: "@terminates" selects nothing in Frama-C 33; print all of TDStep
MAX_CHARS = 14000
_NOISE = re.compile(r"^(\S+:\d+: warning from Typed Model:|\s+- Warning: Hide sub-term definition|\s+Reason: Cast with)")


def selection(goal, kind):
    if goal.startswith("typed_lemma_"):
        return "-wp-prop=" + goal[len("typed_lemma_"):]
    tag = TAGS.get(kind)
    return "-wp-fct TDStep" + (f" -wp-prop={tag}" if tag else "")


def blocks(text):
    """[(header, body)] of the goals in a -wp-print log."""
    out, cur, pending = [], None, None
    for ln in text.splitlines():
        if pending is not None:  # call-site headers end with a line holding only ":"
            if ln.strip() == ":":
                if cur:
                    out.append(cur)
                cur = [pending + " :", []]
                pending = None
                continue
            pending = None
        if ln.startswith("Goal ") and not ln.rstrip().endswith(":"):
            pending = ln.rstrip()
            continue
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
    if "_call_" in name:
        # 'Instance of Pre-condition (<summary>, line L) in f ... at call f (<unit>, line N) :'; requires_K is
        # the K-th precondition of the callee in source order.
        cand = [b for b in bl if re.search(rf'"{L.UNIT}", line {line}\) :$', b[0])]
        m = re.search(r"_requires_(\d+)$", name)
        if m and cand:
            pre = sorted({int(x.group(1)) for b in cand for x in [re.search(r'Pre-condition \("[^"]+", line (\d+)\)', b[0])] if x})
            k = int(m.group(1))
            if 1 <= k <= len(pre):
                cand = [b for b in cand if f'line {pre[k - 1]}) in' in b[0]]
        return cand[:2]
    m = re.search(r"_ensures_(\w+)$", name)
    if m:  # 'Goal Post-condition '<name>' in 'TDStep':' carries no line (t07e run 10)
        return [b for b in bl if f"Post-condition '{m.group(1)}'" in b[0]][:1]
    if re.search(r"_terminates(_part\d+)?$", name):  # 'Goal Termination-condition (...) in 'TDStep' (k/n):'
        cand = [b for b in bl if b[0].startswith("Goal Termination-condition")]
        m = re.search(r"_part(\d+)$", name)
        k = int(m.group(1)) if m else 1
        return [b for b in cand if re.search(rf"\({k}/\d+\):$", b[0].rstrip())][:1] or cand[:1]
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
    if len(cand) > 1 and "_assigns_normal_" in name:
        cand = cand[:1]   # WP prints the normal-exit frame group before the exit group (checked on run 9's set)
    elif len(cand) > 1 and "_assigns_exit_" in name:
        cand = cand[-1:]
    if len(cand) > 1:
        toks = [t for t in name.split("_") if len(t) > 2 and t not in ("typed", "TDStep", "loop", "invariant",
                                                                          "preserved", "established", "call")]
        scored = sorted(cand, key=lambda b: -sum(t in b[0] for t in toks))
        cand = scored[:2]
    return cand



def pick_exact(bl, g):
    """Method22 refuses absent/ambiguous task identities; no legacy fallback."""
    name = g['goal']
    part = re.search(r'_part(\d+)$', name)

    def split_matches(header):
        split = re.search(r'\((\d+)/\d+\):$', header.rstrip())
        return int(split.group(1)) == (int(part.group(1)) if part else 1) if split else part is None

    if name.startswith('typed_lemma_'):
        lemma = re.escape(name[len('typed_lemma_'):])
        candidates = [b for b in bl if re.match(r"^Goal Lemma ['\"]?" + lemma + r"['\"]?(?:\s|:|$)", b[0])]
    elif (post := re.search(r'_ensures_(\w+?)(?:_part\d+)?$', name)):
        candidates = [b for b in bl if f"Post-condition '{post.group(1)}' in 'TDStep'" in b[0]]
    elif re.search(r'_terminates(?:_part\d+)?$', name):
        candidates = [b for b in bl if b[0].startswith('Goal Termination-condition') and "'TDStep'" in b[0]]
    elif '_call_' in name:
        line = int(g.get('line') or 0)
        candidates = [b for b in bl if re.search(rf'"{re.escape(L.UNIT)}", line {line}\) :$', b[0])]
        pre = re.search(r'_requires_(\d+)(?:_part\d+)?$', name)
        if not pre:
            return []
        lines = sorted({int(m.group(1)) for b in candidates
                        if (m := re.search(r'Pre-condition \("[^"]+", line (\d+)\)', b[0]))})
        index = int(pre.group(1))-1
        if not 0 <= index < len(lines):
            return []
        candidates = [b for b in candidates if f'line {lines[index]}) in' in b[0]]
    else:
        line = int(g.get('line') or 0)
        if line <= 0:
            return []
        unit = re.compile(r'"' + re.escape(L.UNIT) + r'"|\bfile\s+' + re.escape(L.UNIT) + r'(?=\s*[,\)])')
        candidates = [b for b in bl if unit.search(b[0]) and re.search(rf'\bline {line}\b', b[0])]
        kind = g.get('kind') or H.goal_kind(name)
        if kind.startswith('loop invariant'):
            phase = re.search(r'_(established|preserved)(?:_part\d+)?$', name)
            if not phase:
                return []
            word = 'Establishment' if phase.group(1) == 'established' else 'Preservation'
            candidates = [b for b in candidates if word + ' of Invariant' in b[0]]
            label = re.search(r'_loop_invariant_(.+?)_(?:established|preserved)(?:_part\d+)?$', name)
            expected = label.group(1) if label and not label.group(1).isdigit() else None
            candidates = [b for b in candidates if
                ((m.group(1) if (m := re.search(r"of Invariant\s+'([^']+)'", b[0])) else None) == expected)]
        elif kind == 'loop variant':
            candidates = [b for b in candidates if 'variant' in b[0].lower()]
            phase = re.search(r'_(positive|decrease)(?:_part\d+)?$', name)
            if phase:
                stem = 'positiv' if phase.group(1) == 'positive' else 'decreas'
                candidates = [b for b in candidates if stem in b[0].lower()]
        else:
            title = {'loop assigns':'Loop assigns', 'assigns':'Assigns', 'assert':'Assertion', 'check':'Check'}.get(kind)
            if title is None:
                return []
            candidates = [b for b in candidates if b[0].startswith('Goal ' + title)]
            marker = {'assert': 'assert', 'check': 'check', 'loop assigns': 'loop_assigns'}.get(kind)
            label = re.search(r'_' + marker + r'_(.+?)(?:_part\d+)?$', name) if marker else None
            expected = label.group(1) if label and not label.group(1).isdigit() else None
            candidates = [b for b in candidates if
                ((m.group(1) if (m := re.match(r"^Goal " + re.escape(title) + r"\s+'([^']+)'", b[0])) else None) == expected)]
    candidates = [b for b in candidates if split_matches(b[0])]
    return candidates if len(candidates) == 1 else []

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


def show_paged(out, best, goal_name, tag, *, offset=0, task_sha256=None, timeout_s=600):
    """Method22: bounded pages of one fresh active task, never arbitrary paths.

    Created: 2026-10-15 ET. A page receipt pins the complete selected task and
    merged candidate; later pages reuse that artifact without a verifier job.
    """
    refused = lambda why: ("Refused goal task: " + why, {"result": "refused: " + why})
    if type(offset) is not int or offset < 0:
        return refused("offset must be a nonnegative integer")
    if offset and not task_sha256:
        return refused("a later page requires the exact task hash")
    g = next((x for x in best["failing_goals"] if x["goal"] == goal_name), None)
    if g is None:
        return refused("goal not open in active candidate")
    base = (L.STANDIN_DIR / L.UNIT).read_text()
    merged = (Path(best["dir"]) / L.UNIT).read_text()
    if H.check(base, best["hints"]) or H.merge(base, best["hints"]) != merged or H.erase(merged) != base:
        return refused("candidate/source identity mismatch")
    if any((Path(best["dir"]) / h).read_bytes() != (L.STANDIN_DIR / h).read_bytes() for h in L.HEADERS):
        return refused("candidate headers changed")
    source_sha = hashlib.sha256(merged.encode()).hexdigest()
    candidate_sha = hashlib.sha256(json.dumps(best["hints"], sort_keys=True).encode()).hexdigest()
    headers = {h: L.sha(L.STANDIN_DIR / h) for h in L.HEADERS}
    identity = {"source_sha256": source_sha, "candidate_sha256": candidate_sha, "headers_sha256": headers}
    key = hashlib.sha256(json.dumps([identity, goal_name], sort_keys=True).encode()).hexdigest()
    cache = Path(out) / "goal-pages"
    cache.mkdir(exist_ok=True)
    metadata, artifact = cache / (key + ".json"), cache / (key + ".task.txt")
    if not metadata.exists():
        if offset or task_sha256 is not None:
            return refused("task identity is stale or no first page was requested")
        d = L.run_dir(Path(out), f"goal-{tag}", merged)
        sel = selection(goal_name, g.get("kind") or H.goal_kind(goal_name))
        log, ws = L.verifier(Path(out), d, "print", timeout=timeout_s, extra=(sel,))
        selected = pick_exact(blocks(log.read_text(errors="replace")), g)
        if ws["exit_code"] != 0 or not selected:
            return refused("fresh WP task generation failed")
        task = "\n\n".join(header + "\n" + body for header, body in selected)
        artifact.write_text(task)
        receipt = {**identity, "goal": goal_name, "dir": str(d), "selection": sel,
                   "log_sha256": ws["log_sha256"], "log": str(log),
                   "full_task_sha256": L.sha(artifact), "full_task_artifact": str(artifact),
                   "total_chars": len(task)}
        metadata.write_text(json.dumps(receipt, indent=1))
    receipt = json.loads(metadata.read_text())
    if any(receipt.get(k) != v for k, v in identity.items()) or receipt.get("goal") != goal_name:
        return refused("stored task candidate identity mismatch")
    if L.sha(artifact) != receipt["full_task_sha256"] or L.sha(Path(receipt["log"])) != receipt["log_sha256"]:
        return refused("retained task artifact changed")
    if task_sha256 is not None and task_sha256 != receipt["full_task_sha256"]:
        return refused("requested task hash differs from active task")
    task = artifact.read_text()
    if offset > len(task):
        return refused("offset exceeds task length")
    end = min(len(task), offset + MAX_CHARS)
    rec = {**receipt, "result": "printed scoped task page", "offset": offset,
           "returned_chars": end-offset, "earlier_chars_omitted": offset,
           "remaining_chars": len(task)-end, "truncated": end < len(task)}
    return json.dumps(rec, sort_keys=True) + "\n" + task[offset:end], rec

# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# Method change (a): monotone, local hint editing. The loop keeps the best hint set so far (frame
# seeds included) in <out>/best.json. An edit is a short list of operations against that set
# (add / delete / edit), each naming the open goal it targets. An edit that passes the proof hint
# check runs round-mode WP; it replaces the best set only when the open-goal count does not rise.
# Otherwise it is reverted. Shared by edit_loop.py (the loop) and edit_tool_mcp.py (the in-call tool).
# t07e (continuation 3, 2026-10-14 ET): two-phase acceptance (TWO_PHASE) and the seed-frame
# classification fix in is_hint_goal.
import hashlib, json, time
from pathlib import Path

import hints as H
import loop as L

MAX_OPS = 8           # size limit per edit
MAX_TEXT = 6000       # total characters of new hint text per edit
SEED_PREFIX = "seed"  # frame seeds (method change b): never edited by the agent
OP_SCHEMA = {"type": "object", "additionalProperties": False,
             "required": ["op", "goal", "id", "anchor", "kind", "text"],
             "properties": {"op": {"type": "string", "enum": ["add", "delete", "edit"]},
                            "goal": {"type": "string"}, "id": {"type": "string"},
                            "anchor": {"type": "string"}, "kind": {"type": "string"},
                            "text": {"type": "string"}}}


def load_best(out):
    return json.loads((Path(out) / "best.json").read_text())


def save_best(out, best):
    p = Path(out) / "best.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(best, indent=1))
    tmp.replace(p)


def validate(ops, best, allowed_kinds):
    """Problems with an edit before anything runs: [(op index, rule, detail)]."""
    probs = []
    if not ops:
        return [(-1, "empty_edit", "give 1 to %d operations" % MAX_OPS)]
    if len(ops) > MAX_OPS:
        probs.append((-1, "edit_too_large", f"{len(ops)} operations; at most {MAX_OPS} per edit"))
    total = sum(len(o.get("text", "")) for o in ops)
    if total > MAX_TEXT:
        probs.append((-1, "edit_too_large", f"{total} characters of hint text; at most {MAX_TEXT}"))
    open_goals = {g["goal"] for g in best["failing_goals"]}
    ids = {h["id"]: h for h in best["hints"]}
    for i, o in enumerate(ops):
        if o.get("goal") not in open_goals:
            probs.append((i, "goal_not_open", f"{o.get('goal')!r} is not an open goal of the best set"))
        op = o.get("op")
        if op in ("delete", "edit"):
            if o.get("id") not in ids:
                probs.append((i, "unknown_id", o.get("id")))
            elif o["id"].startswith(SEED_PREFIX):
                probs.append((i, "seed_fixed", "frame seeds are fixed (method); add invariants instead"))
        if op in ("add",) and o.get("kind") not in allowed_kinds:
            probs.append((i, "kind_not_allowed", f"{o.get('kind')} (allowed: {', '.join(sorted(allowed_kinds))})"))
        if op == "edit" and o.get("id") in ids and o.get("kind") and o["kind"] != ids[o["id"]]["kind"]:
            probs.append((i, "edit_changes_kind", "an edit keeps the hint's kind and anchor; delete and add instead"))
    return probs


def apply(ops, best, tag, provenance):
    hs = [dict(h) for h in best["hints"]]
    n = 0
    for o in ops:
        if o["op"] == "delete":
            hs = [h for h in hs if h["id"] != o["id"]]
        elif o["op"] == "edit":
            for h in hs:
                if h["id"] == o["id"]:
                    n += 1
                    h["text"] = o["text"]
                    h["provenance"] = provenance + f" (edit of {o['id']})"
                    h["id"] = f"{tag}h{n}"
        else:
            n += 1
            hs.append({"id": f"{tag}h{n}", "anchor": o["anchor"], "kind": o["kind"], "text": o["text"],
                       "provenance": provenance})
    return hs


# Method18 (2026-10-15 ET): bounded search debt changes exploration only.
# best.json remains the checked incumbent; debt.json is never final-verdict input.
DEBT = [False]
DEBT_HINTS, DEBT_REPAIRS, DEBT_SECONDS = 4, 4, 300.0
COUNTED_S = [lambda: 0.0]
SEARCH_REMAINING_S = [lambda: 0.0]  # excludes the reserved final replay


def _debt(out):
    p = Path(out) / "debt.json"
    return json.loads(p.read_text()) if p.exists() else None


def _save_debt(out, state):
    p = Path(out) / "debt.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(p)


def _debt_event(out, event, counted_s, **details):
    with (Path(out) / "debt-events.jsonl").open("a") as stream:
        stream.write(json.dumps({"event": event, "counted_s": counted_s, **details}) + "\n")


def rollback_debt(out, reason, *, counted_s):
    state = _debt(out)
    if state:
        _debt_event(out, "rollback", counted_s, reason=reason, repairs=state["repairs"],
                    working_from=state["candidate"].get("from"))
        (Path(out) / "debt.json").unlink()
    return load_best(out)


def load_working(out, *, counted_s, remaining_s):
    state = _debt(out)
    if state:
        if state["incumbent"] != load_best(out):
            return rollback_debt(out, "incumbent changed", counted_s=counted_s)
        if counted_s - state["started_s"] >= DEBT_SECONDS or remaining_s <= 0:
            return rollback_debt(out, "counted deadline/final reserve", counted_s=counted_s)
        if state["repairs"] >= DEBT_REPAIRS:
            return rollback_debt(out, "repair limit", counted_s=counted_s)
        return state["candidate"]
    return load_best(out)


def start_repair(out, *, counted_s):
    state = _debt(out)
    if state:
        if state["repairs"] >= DEBT_REPAIRS:
            rollback_debt(out, "repair limit", counted_s=counted_s)
            return
        state["repairs"] += 1
        _save_debt(out, state)
        _debt_event(out, "repair", counted_s, number=state["repairs"])


def accept_candidate(out, current, candidate, *, counted_s, remaining_s):
    """A checked proposal's state transition; returns result and only a promoted incumbent.

    All temporary candidates remain separate. Four repairs are allowed after entry;
    the fourth may recover the original rule, but cannot retain debt. Time expiry
    refuses even a late recovery. Unit counts may not rise relative to either state.
    """
    incumbent, state = load_best(out), _debt(out)
    if remaining_s <= 0:
        rollback_debt(out, "search deadline before candidate completed", counted_s=counted_s)
        _debt_event(out, "refused", counted_s, reason="search deadline before candidate completed")
        return "reverted (search deadline)", None
    if state and (state["incumbent"] != incumbent or
                  counted_s - state["started_s"] >= DEBT_SECONDS or remaining_s <= 0):
        rollback_debt(out, "expired before proposal completed", counted_s=counted_s)
        return "reverted (debt expired)", None
    u_inc, h_inc = split_counts(incumbent["failing_goals"])
    u_cur, _ = split_counts(current["failing_goals"])
    u_new, h_new = split_counts(candidate["failing_goals"])
    units_ok = u_new <= min(u_inc, u_cur)
    recovered, why = decide(incumbent["failing_goals"], incumbent["n_open"], candidate["failing_goals"])
    if recovered and units_ok:
        if state:
            _debt_event(out, "promote", counted_s, repairs=state["repairs"], candidate=candidate.get("from"))
            (Path(out) / "debt.json").unlink()
        return "accepted (incumbent rule recovered: " + why + ")", candidate
    fits = units_ok and h_new <= h_inc + DEBT_HINTS and (ACCEPT[0] != "unit-first" or h_new <= CAP[0])
    if fits and (state is not None or remaining_s >= DEBT_SECONDS):
        if state and state["repairs"] >= DEBT_REPAIRS:
            rollback_debt(out, "repair limit without recovery", counted_s=counted_s)
            return "reverted (debt repair limit)", None
        fresh = state is None
        state = state or {"incumbent": incumbent, "started_s": counted_s, "repairs": 0}
        state["candidate"] = candidate
        _save_debt(out, state)
        _debt_event(out, "enter" if fresh else "retain", counted_s, repairs=state["repairs"],
                    unit_open=u_new, hint_open=h_new, candidate=candidate.get("from"))
        return "staged (temporary hint debt; incumbent unchanged)", None
    _debt_event(out, "refused", counted_s, reason="unit regression, hint debt or final reserve")
    # A rejected repair counts, and reaching the fourth forces rollback.
    load_working(out, counted_s=counted_s, remaining_s=remaining_s)
    return "reverted (unit regression, hint debt or final reserve)", None


def debt_status(out):
    state = _debt(out)
    return ({"started_s": state["started_s"], "repairs": state["repairs"],
             "working_from": state["candidate"].get("from"),
             "incumbent_from": state["incumbent"].get("from")} if state else None)


def working_text(out, working):
    text = best_text(working)
    return text.replace("Current best hint set", "Temporary working hint set", 1) if _debt(out) else text


def debt_text(out):
    state = _debt(out)
    if not state:
        return ""
    u, h = split_counts(state["incumbent"]["failing_goals"])
    return (f"\nBOUNDED DEBT: temporary working hints; checked incumbent remains {u} unit + {h} hint goals. "
            f"{state['repairs']}/{DEBT_REPAIRS} repair proposals used; expires at counted second "
            f"{state['started_s'] + DEBT_SECONDS:.1f}. Only recovery of the incumbent rule promotes hints.")


def search_remaining(out):
    left = SEARCH_REMAINING_S[0]()
    state = _debt(out)
    return min(left, DEBT_SECONDS - (COUNTED_S[0]() - state["started_s"])) if state else left


def attempt(out, best, ops, tag, provenance, mode, round_timeout, allowed_kinds, run_wp=True,
            timeout_s=2400):
    if DEBT[0]:
        best = load_working(out, counted_s=COUNTED_S[0](), remaining_s=SEARCH_REMAINING_S[0]())
        if run_wp:
            start_repair(out, counted_s=COUNTED_S[0]())
            state = _debt(out)
            if state:
                timeout_s = max(1, min(timeout_s, DEBT_SECONDS - (COUNTED_S[0]() - state['started_s'])))
    rec, candidate = _checked_attempt(out, best, ops, tag, provenance, mode, round_timeout, allowed_kinds,
                                     run_wp=run_wp, timeout_s=timeout_s, defer_decision=DEBT[0])
    if DEBT[0]:
        if run_wp and candidate is not None:
            rec['failing_goals'] = candidate['failing_goals']
            rec['result'], candidate = accept_candidate(out, best, candidate,
                counted_s=COUNTED_S[0](), remaining_s=SEARCH_REMAINING_S[0]())
        else:
            load_working(out, counted_s=COUNTED_S[0](), remaining_s=SEARCH_REMAINING_S[0]())
        rec['debt'] = debt_status(out)
    return rec, candidate


def _checked_attempt(out, best, ops, tag, provenance, mode, round_timeout, allowed_kinds, run_wp=True,
                     timeout_s=2400, defer_decision=False):
    """One edit attempt. Returns (record, new_best or None)."""
    rec = {"tag": tag, "ops": ops, "time": L.now(), "n_open_before": best["n_open"]}
    probs = validate(ops, best, allowed_kinds)
    if probs:
        rec.update(result="edit rejected (edit rules)", problems=[list(p) for p in probs])
        return rec, None
    chk = {}
    standin = (L.STANDIN_DIR / L.UNIT).read_text()
    t = time.time()
    # t07e (c3): an edit identical to one check_edit just passed against the same best set runs WP in that
    # check's folder (same merged file, same hint ids), with no second check.
    key = hashlib.sha256(json.dumps([best["hints"], ops], sort_keys=True).encode()).hexdigest()
    prev = PASSED_CHECKS.get(key) if run_wp else None
    d = None
    if prev is not None:
        hs = apply(ops, best, prev["tag"], provenance)
        merged = H.merge(standin, hs).encode()
        pd = Path(prev["dir"])
        if (pd / L.UNIT).exists() and not (pd / ".frama-c").exists() and (pd / L.UNIT).read_bytes() == merged:
            d = pd
            rec["check_reused_from"] = str(pd)
    if d is None:
        hs = apply(ops, best, tag, provenance)
        d = L.precheck(Path(out), f"attempt-{tag}", standin, hs, chk,
                       **({"remaining_s": lambda: search_remaining(out)} if DEBT[0] else {}))
        if d is not None and not run_wp:
            PASSED_CHECKS[key] = {"dir": str(d), "tag": tag}
    rec["check_wall_s"] = round(time.time() - t, 1)
    if d is None:
        rec.update(result="edit rejected (proof hint check)", check=chk.get("outcome"),
                   rejections=chk.get("rejections"), parse_error=(chk.get("parse_error") or "")[-2500:],
                   blame_text=L.blame_text(chk))
        return rec, None
    if not run_wp:
        rec["result"] = "check passed"
        return rec, None
    if DEBT[0]:
        remaining = search_remaining(out)
        if remaining <= 0:
            rec.update(result="reverted (search deadline before WP)")
            return rec, None
        timeout_s = min(timeout_s, remaining)
    wlog, ws = L.verifier(Path(out), d, mode, timeout=timeout_s, extra=(Path(out) / "round-cache", round_timeout))
    ar = L.assess_round(d, wlog)
    rec.update(dir=str(d), wp_wall_s=ws["wall_s"], peak_rss_mb=ws["peak_rss_mb"], wp_exit=ws["exit_code"],
               timed_out=ws.get("timed_out"), n_goals=ar["n_goals"], log_sha256=ws["log_sha256"])
    if ws["exit_code"] != 0 or ar["n_tdstep_goals"] == 0:
        rec.update(result="reverted (WP run failed)", log_tail=wlog.read_text(errors="replace")[-2000:])
        return rec, None
    n_open = len(ar["failing_goals"])
    rec["n_open_after"] = n_open
    nb = {"hints": hs, "failing_goals": ar["failing_goals"], "n_open": n_open, "n_goals": ar["n_goals"],
          "dir": str(d), "from": tag, "history": best.get("history", []) + [tag]}
    if defer_decision:
        rec["result"] = "checked candidate"
        rec.update(zip(("n_unit_after", "n_hint_after"), split_counts(ar["failing_goals"])))
        return rec, nb
    ok, why = decide(best["failing_goals"], best["n_open"], ar["failing_goals"])
    rec.update(zip(("n_unit_after", "n_hint_after"), split_counts(ar["failing_goals"])))
    if not ok:
        rec["result"] = f"reverted ({why})"
        rec["failing_goals"] = ar["failing_goals"]
        return rec, None
    rec["result"] = f"accepted ({why})"
    return rec, nb


def decide(old_failing, old_n_open, new_failing):
    """Acceptance of an edit: (accepted, reason)."""
    n_open = len(new_failing)
    u_old, h_old = split_counts(old_failing)
    u_new, h_new = split_counts(new_failing)
    if TWO_PHASE[0] and u_old == 0:
        # t07e (b) phase 2: unit goals stay at 0; open hint goals may not rise (monotone).
        return (u_new == 0 and h_new <= h_old), f"phase 2: unit goals {u_old} -> {u_new}, hint goals {h_old} -> {h_new}"
    if ACCEPT[0] == "unit-first":
        # t07d (a'), run 8 on: unit goals first, then the total; hint goals open capped.
        ok = h_new <= CAP[0] and (u_new < u_old or (u_new == u_old and n_open <= old_n_open))
        return ok, f"unit goals {u_old} -> {u_new}, hint goals {h_old} -> {h_new}, total {old_n_open} -> {n_open}"
    return n_open <= old_n_open, f"open goals {old_n_open} -> {n_open}"


ACCEPT = ["total"]     # "total" (run 7) or "unit-first" (t07d a', run 8 on)
HINT_OPEN_CAP = 15     # unit-first: at most this many open goals that belong to hints (run 8: 15; --hint-cap)
CAP = [HINT_OPEN_CAP]
PASSED_CHECKS = {}     # t07e (c3): merged-file sha256 -> folder where the proof hint check passed
TWO_PHASE = [False]    # t07e method change (b): phase 2 (hint goals only) once unit goals reach 0


def is_hint_goal(g):
    """A goal of the agent's own hints: a lemma, or a goal inside a hint block that is not a seed frame.
    t07e bug fix: a seed `loop assigns` merged into one block with agent invariants was counted as a hint
    goal (its hint_ids hold the agent's ids too). Seeds are method, so their goals are unit goals."""
    name = str(g.get("goal", ""))
    if name.startswith("typed_lemma"):
        return True
    kind = g.get("kind") or H.goal_kind(name)
    if kind == "loop assigns":
        return False
    return any(not i.startswith(SEED_PREFIX) for i in g.get("hint_ids") or [])


def split_counts(failing):
    """(unit goals open, hint goals open)."""
    hint = sum(1 for g in failing if is_hint_goal(g))
    return len(failing) - hint, hint


def phase_of(best):
    """t07e method change (b): phase 2 once the best set's unit goals are 0 (only hint goals left)."""
    if not TWO_PHASE[0]:
        return 1
    return 2 if split_counts(best["failing_goals"])[0] == 0 and best["n_open"] > 0 else 1


def phase_text(best):
    if not TWO_PHASE[0]:
        return ""
    u, h = split_counts(best["failing_goals"])
    if phase_of(best) == 2:
        return (f"PHASE 2 (closing your own hint goals): every unit goal is proven; {h} goals of your own hints are "
                "open. An edit is ACCEPTED only if every unit goal stays proven and the number of open hint goals "
                "does not rise. Add lemmas, asserts, invariants or strategies that support your hints, fix them, or "
                "delete a hint that is not needed (the edit is kept only if the unit goals stay proven).")
    return f"PHASE 1 (unit goals first): {u} unit goals and {h} hint goals open."


def best_text(best, limit=80):
    lines = [f"Current best hint set ({len(best['hints'])} hints; ids with prefix 'seed' are the fixed frame seeds):"]
    for h in best["hints"][:limit]:
        lines.append(f"  {h['id']} [{h['kind']} at {h['anchor']}]: {h['text']}")
    return "\n".join(lines)


def open_text(best):
    ph = phase_text(best)
    return (ph + "\n" if ph else "") + (f"Open goals of the best set ({best['n_open']} of {best.get('n_goals')} not proven): goal [failure class] "
            f"kind at file:line (merged file): source line | hint holding it\n"
            + L.positions_text(best["failing_goals"], best["hints"]))

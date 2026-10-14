"""The iteration ladder: every earlier candidate artifact of an Extensa campaign, shown to its rewrite calls.

Created: 2026-10-14 ET (Probata proof of concept ticket 17). Design: formal-verification map decision 28
(items 1-4, 7, 8, 10 and its build items), 25 item 4 (levels and both winner marks); D8's leakage rules.
Format: docs/reference/format-v0.4-extensa.md ("The iteration ladder").

`LADDER.json` is written by the campaign loop only, never by a provider, and rebuilt whole from campaign
state (`state.json`) for every rewrite workspace from iteration 2 and for every repair workspace of those
iterations. Nothing here reads an earlier `LADDER.json`. One row per earlier candidate artifact, rejected and
repaired ones included; an iteration whose rewrite call returned nothing gets one row with class `-`. No row
cap. Every row passes `check_row`, the ladder's closed-field check (the same rules as D8's feedback check in
`swdb.extensa.search`): a closed column set, the closed feedback reason codes, public failed-check names only
(a surviving negative control only as its aggregate category), no counterexample, no raw timing, no patch.

The workspace version is a record, never a setting: a new campaign records `rewrite_workspace: v2` in its
state and summary; a state or summary without it reads as `v1` (D8's workspace, no ladder), and a `v1`
campaign never gains a ladder on resume.
"""

import json
import numbers
import re

from swdb.extensa.search import _FORBIDDEN_FIELD, FEEDBACK_REASONS, FeedbackError

#: The renderer's version, written into every file (map 28 build items: a versioned renderer).
FORMAT = "swdb.iteration-ladder.v1"
FILE = "LADDER.json"
V1, V2 = "v1", "v2"
#: The levels a row may show: those known inside the loop (map 28 item 4). Proven unbounded never appears.
LEVELS = ("rejected", "uncertified", "certified", "refuted", "proven_within_bounds_threads_1",
          "proven_within_bounds_threads_k")
MARKS = ("fastest", "best_proven", "both", "")
EMPTY_CLASS = "-"
#: The closed column set (map 28 item 3, plus `row` and `repair_of`, which ties a counterexample repair to the
#: row of the candidate artifact it repaired).
COLUMNS = ("row", "iteration", "class", "contracts", "knobs", "level", "verdict", "ratio", "lower", "spread",
           "reason_codes", "failed_checks", "winner", "repair_of")
VERDICTS = ("gain", "no_gain", "inconclusive", None)
#: A refutation's check category: the bounded rung that refuted it (never the counterexample).
CHECK_CATEGORIES = {"threads_1": "bounded_threads_1", "threads_k": "bounded_threads_k"}
NOTE = ("One row per earlier candidate artifact of this campaign, written by the campaign loop from its state. "
        "Levels are the ones known when this file was written; `winner` marks this campaign's current winners.")
_SHORT_TEXT = re.compile(r"^[^\n\r]{0,200}$")


class LadderError(FeedbackError):
    """A ladder row that would disclose something D8 keeps from the rewrite provider."""


def version_of(record):
    """The rewrite workspace version of a campaign state or summary: `v1` when it names none."""
    return (record or {}).get("rewrite_workspace") or V1


def shown(state, iteration):
    """True when this iteration's rewrite and repair workspaces hold `LADDER.json` (v2, from iteration 2)."""
    return version_of(state) == V2 and iteration > 1


# --- the closed-field check -------------------------------------------------------------------------------

def _public(name):
    from swdb import certification_feedback
    return isinstance(name, str) and certification_feedback.public_checks([name]) == [name] and \
        name not in ("control", "negative_control_site") and _SHORT_TEXT.match(name) is not None


def _text(value):
    return isinstance(value, str) and _SHORT_TEXT.match(value) is not None and "@@" not in value \
        and "+++" not in value and "---" not in value


def _number(value):
    return value is None or (isinstance(value, numbers.Real) and not isinstance(value, bool))


def check_row(row):
    """Refuse a row outside the closed column set or carrying anything D8 keeps out; return the row."""
    from swdb.provider_workspace import carries_counterexample
    if not isinstance(row, dict):
        raise LadderError("a ladder row is a mapping")
    unknown = sorted(set(row) - set(COLUMNS))
    if unknown:
        raise LadderError("ladder field outside the closed column set: " + ", ".join(unknown))
    forbidden = sorted(k for k in row if _FORBIDDEN_FIELD.search(k))
    if forbidden or set(row) != set(COLUMNS):
        raise LadderError("ladder row names a forbidden field or misses a column: "
                          + ", ".join(forbidden or sorted(set(COLUMNS) - set(row))))
    if carries_counterexample(FILE, json.dumps(row)):
        raise LadderError("a ladder row carries a counterexample; it goes only to repair")
    problems = []
    if not isinstance(row["row"], int) or row["row"] < 1:
        problems.append("row")
    if not isinstance(row["iteration"], int) or row["iteration"] < 1:
        problems.append("iteration")
    if not _text(row["class"]):
        problems.append("class")
    if not isinstance(row["contracts"], list) or not all(_text(c) for c in row["contracts"]):
        problems.append("contracts")
    knobs = row["knobs"]
    if not isinstance(knobs, dict) or not all(_text(k) and (_text(v) or (_number(v) and v is not None))
                                              for k, v in knobs.items()):
        problems.append("knobs")
    if row["level"] not in LEVELS:
        problems.append("level")
    if row["verdict"] not in VERDICTS:
        problems.append("verdict")
    for name in ("ratio", "lower", "spread"):
        if not _number(row[name]):
            problems.append(name)
    if not isinstance(row["reason_codes"], list) or not all(c in FEEDBACK_REASONS for c in row["reason_codes"]):
        problems.append("reason_codes")
    if not isinstance(row["failed_checks"], list) or not all(_public(c) for c in row["failed_checks"]):
        problems.append("failed_checks (public names only; a surviving control only as its category)")
    if row["winner"] not in MARKS:
        problems.append("winner")
    if row["repair_of"] is not None and (not isinstance(row["repair_of"], int) or row["repair_of"] >= row["row"]):
        problems.append("repair_of")
    if problems:
        raise LadderError("ladder row refused: " + ", ".join(problems))
    return row


# --- rows from campaign state -----------------------------------------------------------------------------

def _level(entry, levels):
    """The level known now: rejected, refuted (the level rule's flag), or the level rule's level; a proven-
    unbounded level read during the loop shows its highest bounded rung (ticket 17 assumption)."""
    if entry.get("level") == "rejected" or not entry.get("id"):
        return "rejected"
    result = levels.get(entry["id"])
    if result is None:
        return entry.get("level") if entry.get("level") in LEVELS else "uncertified"
    if (result.get("refuted") or {}).get("flag"):
        return "refuted"
    level = result.get("level")
    if level == "proven_unbounded":
        return "proven_within_bounds_threads_k"
    return level if level in LEVELS else "uncertified"


def _gate_jobs(entry):
    return (entry.get("bounded_gate") or {}).get("jobs") or []


def refuted_categories(entry):
    """The check categories of the bounded rungs that refuted this entry, in rung order."""
    return list(dict.fromkeys(CHECK_CATEGORIES[j["rung"]] for j in _gate_jobs(entry)
                              if j.get("verdict") == "refuted" and j.get("rung") in CHECK_CATEGORIES))


def timed_out(entry):
    return any(j.get("failure_class") == "timeout" for j in _gate_jobs(entry))


def gate_feedback(entry, cls, feedback):
    """Append the bounded gate's feedback items for one gated entry: `refuted` with its check categories only
    (the counterexample goes only to repair), and `proof_timeout` when a rung ran out of its wall budget."""
    from swdb.extensa.search import Feedback
    if (entry.get("bounded_gate") or {}).get("refuted"):
        feedback.append(Feedback("refuted", "The bounded gate refuted this candidate artifact.",
                                 {"class": cls, "failed_checks": refuted_categories(entry)}).to_dict())
    if timed_out(entry):
        feedback.append(Feedback("proof_timeout", "A bounded proof job ended at its wall budget; that rung gives "
                                 "no level.", {"class": cls}).to_dict())


def _reason_codes(entry):
    codes = []
    outcome = (entry.get("certification") or {}).get("outcome")
    if outcome == "certified":
        codes.append("certified")
    elif entry.get("level") == "uncertified":
        codes.append("uncertified_edit")
    if (entry.get("bounded_gate") or {}).get("refuted"):
        codes.append("refuted")
    if timed_out(entry):
        codes.append("proof_timeout")
    verdict = (entry.get("selection") or {}).get("verdict")
    if verdict:
        codes.append(f"verdict_{verdict}")
    if entry.get("level") == "rejected" and entry.get("rejection_reason"):
        codes.append(entry["rejection_reason"])
    return [c for c in dict.fromkeys(codes) if c in FEEDBACK_REASONS]


def _failed_checks(entry):
    from swdb import certification_feedback
    names = list(entry.get("rejection_failed_checks") or [])
    names += certification_feedback.public_checks((entry.get("certification") or {}).get("failed_checks") or [])
    names += refuted_categories(entry)
    return certification_feedback.public_checks(list(dict.fromkeys(names)))


def _numbers(entry, base_source):
    selection = entry.get("selection") or {}
    base = next((c for c in entry.get("comparisons") or [] if c.get("baseline_role") == base_source), {})
    return {"verdict": selection.get("verdict"), "ratio": selection.get("ratio"), "lower": selection.get("lower"),
            "spread": base.get("spread") if selection else None}


def _knobs(knobs):
    return {str(k): v for k, v in sorted((knobs or {}).items())}


def rows(state, levels, base_source):
    """One checked row per earlier candidate artifact in `state["iterations"]` (completed iterations only)."""
    iterations = state.get("iterations") or []
    marks = {w["candidate"]: w["winner"] for w in (iterations[-1].get("winners") or [])} if iterations else {}
    out, by_id = [], {}
    for iteration in iterations:
        candidates = iteration.get("candidates") or []
        if not candidates:
            reasons = [r for r in iteration.get("feedback_reasons") or [] if r in FEEDBACK_REASONS]
            out.append({"row": len(out) + 1, "iteration": iteration["index"], "class": EMPTY_CLASS, "contracts": [],
                        "knobs": {}, "level": "rejected", "verdict": None, "ratio": None, "lower": None,
                        "spread": None, "reason_codes": reasons or ["provider_output_invalid"], "failed_checks": [],
                        "winner": "", "repair_of": None})
            continue
        for entry in candidates:
            number = len(out) + 1
            parent = (entry.get("repaired_from") or {}).get("candidate")
            out.append({"row": number, "iteration": iteration["index"], "class": entry["class"],
                        "contracts": list(entry.get("contracts") or []), "knobs": _knobs(entry.get("knobs")),
                        "level": _level(entry, levels), **_numbers(entry, base_source),
                        "reason_codes": _reason_codes(entry), "failed_checks": _failed_checks(entry),
                        "winner": marks.get(entry.get("id"), "") if entry.get("id") else "",
                        "repair_of": by_id.get(parent) if parent else None})
            if entry.get("id"):
                by_id[entry["id"]] = number
    return [check_row(row) for row in out]


def render(state, levels, base_source):
    """The whole `LADDER.json` text from campaign state and the levels known now ({candidate ID: level-rule
    result}); deterministic for the same inputs."""
    return json.dumps({"format": FORMAT, "note": NOTE, "rows": rows(state, levels, base_source)}, indent=2) + "\n"

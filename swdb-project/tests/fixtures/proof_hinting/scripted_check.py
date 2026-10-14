"""A scripted proof hint check for the proof_hinting wrapper (Probata PoC ticket 34). Created: 2026-10-14 ET.

Ticket 35 owns the real check; until it lands, the wrapper's check entry is exercised with this one. It
rejects a hint whose anchor is not an anchor of the lowering (rule `anchor`) or whose text holds `admit`
(rule `vocabulary`), and merges the rest as ACSL comments in place of their anchor lines.
"""
import re

ANCHOR_LINE = re.compile(r"^(\s*)/\* swdb-anchor (\S+) \*/$")


def check(base, anchors, hints):
    known = {a["id"] for a in anchors["anchors"]}
    rejections = []
    for index, hint in enumerate(hints):
        if hint["anchor"] not in known:
            rejections.append({"hint": index, "rule": "anchor", "detail": f"no anchor {hint['anchor']}"})
        elif "admit" in hint["text"]:
            rejections.append({"hint": index, "rule": "vocabulary", "detail": "admit is not a proof hint"})
    if rejections:
        return {"passed": False, "rejections": rejections, "merged": None}
    out = []
    for line in base.splitlines():
        match = ANCHOR_LINE.match(line)
        placed = [h for h in hints if match and h["anchor"] == match.group(2)]
        out += [f"{match.group(1)}/*@ {h['kind']} {h['text']} */" for h in placed] if placed else [line]
    return {"passed": True, "rejections": [], "merged": "\n".join(out) + "\n"}

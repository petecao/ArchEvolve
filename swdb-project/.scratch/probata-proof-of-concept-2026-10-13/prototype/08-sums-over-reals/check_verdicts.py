#!/usr/bin/env python3
"""Verdict reading for spike (d), ticket 08 (2026-10-14 ET).

Reads WP's per-goal JSON (-wp-report-json) and the per-property text report (-report), never
the consolidated summary (map 13 item 7; design S7).

  proof     every goal Valid and passed; every smoke test passed (a smoke goal WP proves
            Valid signals dead code); no Extern, Partial or unknown property in the text
            report; every expected lemma has a goal.
  negative  at least one goal unproven (or every goal named in must_fail unproven), and no
            goal refuted: WP must report "not proven", never "invalid".

Usage: check_verdicts.py <stage> <stage-output-dir> [sum_logic.h]
  stage: lemmas | unit (proof);  bug | false-lemma | false-fn (negative)
Prints one line per goal (verdict, passed, provers with time) and exits 1 on any problem.
"""
import json
import re
import sys

REFUTED = {"invalid", "refuted"}


def problems(kind, goals, report_text, expected_lemmas, must_fail=()):
    out = []
    if kind == "proof":
        for g in goals:
            if g.get("smoke"):
                if not g.get("passed"):
                    out.append(f"failed smoke test (dead code or contradiction): {g['goal']}")
            elif g.get("verdict") != "valid" or not g.get("passed"):
                out.append(f"not valid: {g['goal']} ({g.get('verdict')})")
        for line in report_text.splitlines():
            m = re.match(r"\[\s*(Extern|Partial|-|Alarm)\s*\]\s*(.*)", line)
            if m:
                out.append(f"report status {m.group(1)}: {m.group(2)}")
        names = {g["goal"] for g in goals}
        for lemma in expected_lemmas:
            if not any(n.endswith("lemma_" + lemma) for n in names):
                out.append(f"no goal for lemma {lemma}")
    elif kind == "negative":
        for g in goals:
            if g.get("verdict") in REFUTED:
                out.append(f"refuted (a deductive verdict must be 'not proven'): {g['goal']}")
        if must_fail:
            for name in must_fail:
                hits = [g for g in goals if g["goal"].endswith(name) or
                        g["goal"].endswith("lemma_" + name)]
                if not hits:
                    out.append(f"no goal for {name}")
                out += [f"proven but must stay unproven: {g['goal']}"
                        for g in hits if g.get("passed")]
        elif all(g.get("passed") for g in goals if not g.get("smoke")):
            out.append("every goal proven: the negative control was not rejected")
    else:
        raise ValueError(kind)
    return out


def lemma_names(path):
    return re.findall(r"lemma\s+(\w+)\s*:", open(path).read())


def main(argv):
    stage, outdir = argv[1], argv[2]
    goals = json.load(open(f"{outdir}/wp_report.json"))
    text = open(f"{outdir}/frama-c.log").read()
    kind = {"lemmas": "proof", "unit": "proof", "bug": "negative",
            "false-lemma": "negative", "false-fn": "negative"}[stage]
    expected = lemma_names(argv[3]) if len(argv) > 3 and kind == "proof" else []
    must_fail = {"false-lemma": ["FALSE_FROM_LEMMAS"],
                 "false-fn": ["FALSE_FROM_CONTEXT"]}.get(stage, ())
    for g in goals:
        provers = ", ".join(f"{p['prover']} {p['time']:.2f}s x{p['success']}"
                            for p in g.get("provers", []))
        extra = f" script {g.get('proved')}/{g.get('subgoals')}" if "subgoals" in g else ""
        print(f"{g['verdict']:8} passed={str(g.get('passed')):5} smoke={str(g.get('smoke')):5} "
              f"{g['goal']}  [{provers}]{extra}")
    found = problems(kind, goals, text, expected, must_fail)
    for p in found:
        print("PROBLEM:", p)
    print(f"{stage}: {'OK' if not found else 'FAIL'} ({len(goals)} goals)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

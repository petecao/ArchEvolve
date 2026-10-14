#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# The spike's proof-hint loop: no-hint WP run, then up to 10 rounds of (Codex call -> proof hint
# check -> merge -> parse -> erase-and-diff -> fresh WP run), stopping when every property is
# Valid (Extern only in summaries) and every smoke test passed, or when 60 minutes are spent.
# Usage: loop.py --out <runs dir> [--rounds 10] [--budget-min 60] [--variant <c file>] [--hints <json>]
# t07c (2026-10-14 ET) method changes, each behind a flag and recorded in meta.json:
#   --round-mode: hint rounds run WP on TDStep's goals and lemmas only, no smoke tests, a shorter
#     per-prover timeout and a run-local cache; a set that proves there gets ONE fresh full replay
#     with the frozen flags (wp-smoke, -wp-cache none), and only that replay is the verdict.
#   --examples: syntax-checked ACSL examples and the Frama-C errors runs 1-3 hit, in the prompt.
#   --positions: failing goals go back with kind, file:line, source line and the hint holding them.
#   --resume-rounds: one Codex session for the whole run (later rounds send only the feedback).
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

import hints as H

HERE = Path(__file__).resolve().parent
STANDIN_DIR = HERE / "standin"
UNIT = "tdstep_standin.c"
HEADERS = ["dxc_summaries.h", "gapbs_models.h", "bfs_unit.h"]
EXTERN_OK = {"dxc_summaries.h", "gapbs_models.h"}  # summary files (S7)
CPP_UNIT = HERE.parents[3] / "library" / "dx100" / "bfs_read_offload.inc"
VRUN = "/tmp/claude/probata-tools/verifier_run.py"
CODEX = os.path.expanduser("~/.local/bin/codex")
EXAMPLES = HERE / "examples"
sys.path.insert(0, str(HERE.parents[3]))
from swdb.provider_adapters import PINS, CODEX_DISABLED_FEATURES  # noqa: E402

PIN = PINS["codex"]
LOCKWAIT = [0.0]  # seconds spent waiting for the machine-wide verifier lock (other tickets), not counted
HINT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["hints", "notes"],
    "properties": {
        "notes": {"type": "string"},
        "hints": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["anchor", "kind", "text"],
            "properties": {"anchor": {"type": "string"}, "kind": {"type": "string", "enum": sorted(H.KINDS)},
                           "text": {"type": "string"}}}}}}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z")


def log(out, msg):
    line = f"{now()} {msg}"
    print(line, flush=True)
    with open(out / "loop.log", "a") as f:
        f.write(line + "\n")


def run_dir(out, name, text):
    d = out / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for h in HEADERS:
        shutil.copy(STANDIN_DIR / h, d / h)
    (d / UNIT).write_text(text)
    return d


OWNER = ["t07"]


def verifier(out, d, mode, owner=None, timeout=2400, extra=()):
    logf = d / f"{mode}.log"
    t = time.time()
    subprocess.run([VRUN, "--log", str(logf), "--timeout", str(timeout), "--owner", owner or OWNER[0], "--",
                    str(HERE / "wp_run.sh"), mode, str(d), UNIT, *map(str, extra)], stdout=subprocess.DEVNULL)
    summ = json.loads(Path(str(logf) + ".summary.json").read_text())
    summ["wall_incl_lock_s"] = round(time.time() - t, 1)
    LOCKWAIT[0] += summ.get("lock_wait_s", 0)
    return logf, summ


def failure_class(g):
    v = g.get("verdict", "")
    return {"timeout": "timeout", "unknown": "unknown", "stepout": "timeout"}.get(v, v or "unknown")


def assess(d, logf):
    """Verdict reading: per-property report plus per-goal JSON (never the [Valid] line)."""
    text = logf.read_text(errors="replace")
    rep = text[text.find("[report] Computing properties status"):] if "[report]" in text else ""
    props = H.read_report(rep)
    goals = json.loads((d / "goals.json").read_text()) if (d / "goals.json").exists() else []
    goals = goals if isinstance(goals, list) else goals.get("goals", [])
    summary_fns = set()
    for h in EXTERN_OK:
        summary_fns |= H.bodyless_functions((STANDIN_DIR / h).read_text())
    problems = H.verdict_problems(props, EXTERN_OK, summary_fns)
    smoke = H.smoke_failures(goals)
    failing = [{"goal": g.get("goal"), "property": g.get("property"), "failure_class": failure_class(g),
                "provers": g.get("provers")} for g in goals if not g.get("smoke") and not g.get("passed")]
    ok = bool(props) and not problems and not smoke and not failing
    return {"ok": ok, "n_props": len(props), "problems": problems, "smoke_failures": smoke,
            "failing_goals": failing, "n_goals": len(goals)}


def headers_text():
    return {h: (STANDIN_DIR / h).read_text() for h in HEADERS}


def assess_round(d, logf):
    """Round-mode reading (never a verdict): TDStep's goals and the lemmas from the two JSON reports."""
    goals = []
    for name in ("goals.json", "lemmas.json"):
        f = d / name
        if f.exists():
            g = json.loads(f.read_text())
            goals += g if isinstance(g, list) else g.get("goals", [])
    merged = (d / UNIT).read_text()
    failing = H.goal_positions(goals, merged, UNIT, headers_text())
    n_td = sum(1 for g in goals if g.get("function") == "TDStep" or str(g.get("goal", "")).startswith("typed_TDStep"))
    return {"n_goals": len(goals), "n_tdstep_goals": n_td, "failing_goals": failing,
            "ok": n_td > 0 and not failing, "n_passed": sum(1 for g in goals if g.get("passed"))}


PROMPT = """You are the proof-hint agent of a proof-hint loop (Frama-C 33.0 / WP, provers Alt-Ergo 2.6.4,
Z3, CVC5, 30 s per prover per goal, x86_64 machdep). Your only job: write ACSL proof hints so that
WP proves every goal of the C function TDStep below. You never edit code or contracts.

Output: JSON {{"hints": [{{"anchor", "kind", "text"}}...], "notes": "..."}}. Return the COMPLETE hint set
for this round (it replaces the previous set; copy what you want to keep).
- anchor: one of the `/* @anchor NAME */` names in tdstep_standin.c (e.g. "loop:k_loop", "stmt:entry", "global").
- kind (allowed vocabulary, nothing else):
  loop_invariant ("loop invariant P;"), loop_assigns ("loop assigns L;"), loop_variant ("loop variant <integer term>;"),
  all three only at "loop:*" anchors (they are merged into one annotation directly before that loop);
  assert ("assert P;") at "stmt:*" anchors; ghost ("ghost <declaration or statement>") at "stmt:*" or "global";
  predicate / logic (NON-recursive definitions) and lemma ("lemma name: P;", proven in the same run) at "global";
  strategy ("\\wp::strategy ...") at "global".
- Rejected (the whole set is rejected and the round is lost): any admit form, axiom, axiomatic, recursive or
  inductive definitions, contracts (requires/ensures/assumes/behavior/terminates/decreases/exits),
  ghost functions, body-less declarations, `loop variant ... for R`, import, \\from, global invariants,
  volatile, statement contracts, `check`, and comment delimiters inside text. Ghost code may not write
  real (non-ghost) memory or call real functions. Named assertions/invariants are fine ("loop invariant name: P;").
- Each text is inserted as `/*@ <text> */` right after its anchor line; loop hints for one loop are
  joined into one `/*@ ... */` block.
- Hint text cannot reference C locals that are not in scope at the anchor. Labels you can use: Pre, Here,
  LoopEntry, LoopCurrent, Old (in lemmas/predicates use your own label parameters).
- Frama-C 33 syntax rules that reject a whole set: ghost variables need C types (int, unsigned, size_t,
  fixed-size arrays); `integer`/`boolean` are logic types for predicate/logic/lemma parameters only. Inside
  `\\at(e, L)` you may not name C locals that do not exist at L (e.g. a loop variable inside `\\at(..., Pre)`);
  instead pass the value as an argument to a predicate/logic function with label parameters, e.g.
  `predicate P{{L1, L2}}(int *a, integer b) = \\at(a[b], L1) == \\at(a[b], L2);`.
- The stand-in and summaries are fixed; the unit postcondition is TDStep's `ensures` clauses; the
  `check hazard_*` annotations are generated hazard checks and must be proven too.

Round {round} of at most {rounds}; minutes used so far: {minutes:.1f} of {budget}.
{method_notes}
{feedback}

=== Workspace (read only) ===
{files}
"""


ROUND_NOTES = """
How rounds are checked: each hint set first passes the proof hint check (vocabulary, Frama-C parse,
WP goal generation). Then WP proves TDStep's goals and your lemmas (Alt-Ergo, Z3, CVC5, {round_timeout} s
each per goal, no smoke tests). When every one of them is proven, the loop runs ONE fresh full WP run with
the final settings (all functions, 30 s per prover, smoke tests); only that run decides. Keep hints few and
targeted: every assertion and invariant is itself a goal, and large quantified contexts make provers time out.
"""

EXAMPLE_NOTES = """
=== Syntax-checked ACSL examples (Frama-C 33 parses this file and WP proves all its goals) ===
It is an unrelated CSR frontier traversal; it only shows working syntax and common invariant shapes.
{examples}
=== Frama-C errors earlier hint sets hit, and the fix ===
{errors}
"""


def examples_text():
    return EXAMPLE_NOTES.format(examples=(EXAMPLES / "acsl_examples.c").read_text(),
                                errors=(EXAMPLES / "frama_c_errors.txt").read_text())


def method_notes(a):
    parts = []
    if a.round_mode:
        parts.append(ROUND_NOTES.format(round_timeout=a.round_timeout))
    if a.examples:
        parts.append(examples_text())
    return "\n".join(parts)


def positions_text(failing, hint_set):
    by_id = {h["id"]: h for h in hint_set or []}
    out = []
    for g in failing:
        where = f"{g['file']}:{g['line']}"
        hint = ""
        if g.get("hint_ids"):
            hs = [by_id[i] for i in g["hint_ids"] if i in by_id]
            exact = [h for h in hs if h["text"].strip()[:50] and h["text"].strip()[:50] in g["source"]]
            pick = exact or hs
            hint = " | in your hint " + ", ".join(f"{h['id']} ({h['kind']} at {h['anchor']})" for h in pick[:3])
        out.append(f"  - {g['goal']} [{g['failure_class']}] {g['kind']} at {where}: {g['source'][:200]}{hint}")
    return "\n".join(out)


def workspace_files(standin_text):
    parts = []
    for name, text in [(UNIT, standin_text)] + [(h, (STANDIN_DIR / h).read_text()) for h in HEADERS] + \
            [("bfs_read_offload.inc (the C++ proof unit, Peter's read offload)", CPP_UNIT.read_text())]:
        parts.append(f"----- {name} -----\n{text}")
    return "\n".join(parts)


def feedback_text(history, resumed=False):
    if not history:
        return "No hints yet."
    lines = []
    last = history[-1]
    lines.append(f"Previous round {last['round']}: {last['outcome']}.")
    if last.get("rejections"):
        lines.append("Rejected hint set; reasons by rule:")
        lines += [f"  - {r['id']}: {r['rule']} {r.get('detail', '')}" for r in last["rejections"]]
    if last.get("parse_error"):
        lines.append("Frama-C rejected the merged file:\n" + last["parse_error"][-3000:])
        if last.get("blame"):
            lines.append(blame_text(last))
    if last.get("failing_goals") is not None and last.get("positions"):
        lines.append(f"Goals not proven after that round ({len(last['failing_goals'])}): goal [failure class] kind "
                     f"at file:line (lines of the merged file, your hints included): source line | hint holding it")
        lines.append(positions_text(last["failing_goals"], last.get("hints")))
    elif last.get("failing_goals") is not None:
        lines.append(f"Failing goals after that round ({len(last['failing_goals'])}), with failure class:")
        lines += [f"  - {g['goal']} [{g['failure_class']}] {g.get('property') or ''}" for g in last["failing_goals"]]
    if last.get("problems"):
        lines.append("Report properties not Valid:")
        lines += [f"  - [{p['status']}] {p['property']}" for p in last["problems"][:200]]
    if last.get("smoke_failures"):
        lines.append("Smoke tests that WP proved (dead code or inconsistent hints):")
        lines += [f"  - {g.get('goal')}" for g in last["smoke_failures"]]
    if last.get("hints") is not None:
        lines.append("Hint set of that round:\n" + json.dumps(last["hints"], indent=1))
    for h in ([] if resumed else history[:-1]):
        if h.get("rejections") or h.get("parse_error"):
            why = "; ".join(f"{r['id']}: {r['rule']} {r.get('detail', '')}" for r in h.get("rejections") or [])
            lines.append(f"Earlier rejected hint set, round {h['round']}: {why or 'Frama-C parse error'}\n"
                         + json.dumps(h.get("hints"), indent=1)[:6000])
    return "\n".join(lines)


def codex_call(out, r, prompt, resume=None, turn=0, keep_session=False):
    d = out / f"codex-r{r}" / (f"turn{turn}" if keep_session else "")
    ws = out / f"codex-r{r}" / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    d.mkdir(parents=True, exist_ok=True)
    if turn == 0:
        (ws / "PROMPT.txt").write_text(prompt)
        os.chmod(ws / "PROMPT.txt", 0o444)
    (d / "schema.json").write_text(json.dumps(HINT_SCHEMA))
    common = ["--model", PIN["model"], "-c", "model_reasoning_effort=" + json.dumps(PIN["effort"]),
              "-c", 'web_search="disabled"', "-c", "analytics.enabled=false", "-c", "project_doc_max_bytes=0",
              "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check"]
    if not keep_session:
        common.append("--ephemeral")
    tail = ["--json", "--output-schema", str(d / "schema.json"), "--output-last-message", str(d / "final.json"),
            "--disable", "shell_tool"]
    for f in CODEX_DISABLED_FEATURES:
        tail += ["--disable", f]
    if resume:
        argv = [CODEX, "exec", "resume", *common, *tail, resume, "-"]
    else:
        argv = [CODEX, "exec", *common, "-s", "read-only", "-C", str(ws), *tail, "-"]
    (d / "argv.json").write_text(json.dumps(argv[:-1]))
    t = time.time()
    p = subprocess.run(argv, input=prompt, capture_output=True, text=True)
    wall = time.time() - t
    (d / "stdout.jsonl").write_text(p.stdout)
    (d / "stderr.txt").write_text(p.stderr)
    usage, thread = {}, resume
    for ln in p.stdout.splitlines():
        try:
            ev = json.loads(ln)
        except ValueError:
            continue
        if ev.get("type") == "thread.started":
            thread = ev.get("thread_id")
        if ev.get("type") == "turn.completed":
            for k, v in (ev.get("usage") or {}).items():
                usage[k] = usage.get(k, 0) + (v or 0)
    res = {"exit": p.returncode, "wall_s": round(wall, 1), "usage": usage, "hints": None, "error": None,
           "thread": thread}
    try:
        data = json.loads((d / "final.json").read_text())
        tag = f"r{r}t{turn}" if keep_session else f"r{r}"
        res["hints"] = [{"id": f"{tag}h{i}", "anchor": h["anchor"], "kind": h["kind"], "text": h["text"],
                         "provenance": f"codex {PIN['model']} {PIN['effort']} round {r} turn {turn}"}
                        for i, h in enumerate(data["hints"], 1)]
        res["notes"] = data.get("notes", "")
    except Exception as e:  # noqa: BLE001
        res["error"] = f"{type(e).__name__}: {e}; stderr tail: {p.stderr[-800:]}"
    return res


def precheck(out, name, standin, hint_set, record):
    """Proof hint check: vocabulary and anchors, erase-and-diff, Frama-C parse and type check."""
    bad = H.check(standin, hint_set)
    if bad:
        record.update(outcome="rejected (proof hint check)", rejections=bad)
        return None
    merged = H.merge(standin, hint_set)
    if H.erase(merged) != standin:
        record.update(outcome="rejected (erase-and-diff)", rejections=[{"id": "*", "rule": "erase_diff"}])
        return None
    d = run_dir(out, name, merged)
    plog, ps = verifier(out, d, "parse", timeout=600)
    record["parse"] = {"exit": ps["exit_code"], "wall_s": ps["wall_s"]}
    if ps["exit_code"] != 0:
        err = plog.read_text(errors="replace")
        by_id = {h["id"]: h for h in hint_set}
        bl = H.blame(merged, err)
        record.update(outcome="rejected (Frama-C parse/type check)", parse_error=err,
                      blame=[{**b, "hints": [by_id[i] for i in b["ids"] if i in by_id]} for b in bl])
        return None
    glog, gs = verifier(out, d, "wp-gen", timeout=900)
    record["wp_gen"] = {"exit": gs["exit_code"], "wall_s": gs["wall_s"]}
    gtxt = glog.read_text(errors="replace")
    if gs["exit_code"] != 0 or "User Error" in gtxt or "aborted" in gtxt:
        by_id = {h["id"]: h for h in hint_set}
        bl = H.blame(merged, gtxt)
        record.update(outcome="rejected (WP user error while generating goals)", parse_error=gtxt[-4000:],
                      blame=[{**b, "hints": [by_id[i] for i in b["ids"] if i in by_id]} for b in bl])
        return None
    return d


def blame_text(rec):
    out = []
    for b in rec.get("blame") or []:
        out.append(f"Frama-C error at merged line {b['line_no']}: {b['line'].strip()[:400]}")
        hs = b.get("hints") or []
        exact = [h for h in hs if h["text"].strip()[:60] in b["line"]]
        for h in exact or hs:
            out.append(f"  inside your hint block containing {h['id']} ({h['kind']} at {h['anchor']}): {h['text'][:600]}")
    return "\n".join(out)


def wp_round(out, name, standin, hint_set, record, mode="wp-smoke", timeout=7200, d=None):
    if d is None:
        d = precheck(out, name, standin, hint_set, record)
        if d is None:
            return None
    wlog, ws = verifier(out, d, mode, timeout=timeout)
    a = assess(d, wlog)
    if ws["exit_code"] != 0 or a["n_goals"] == 0:
        record.update(wp={"exit": ws["exit_code"], "wall_s": ws["wall_s"], "log": str(wlog),
                          "log_sha256": ws["log_sha256"], "timed_out": ws.get("timed_out")},
                      proven=False, failing_goals=None,
                      parse_error=wlog.read_text(errors="replace")[-4000:],
                      outcome="WP run failed (exit %s, %d goals%s)" % (ws["exit_code"], a["n_goals"],
                                                                     ", budget timeout" if ws.get("timed_out") else ""))
        return a
    record.update(wp={"exit": ws["exit_code"], "wall_s": ws["wall_s"], "peak_rss_mb": ws["peak_rss_mb"],
                      "log": str(wlog), "log_sha256": ws["log_sha256"],
                      "goals_json": str(d / "goals.json"),
                      "goals_sha256": sha(d / "goals.json") if (d / "goals.json").exists() else None},
                  n_goals=a["n_goals"], failing_goals=a["failing_goals"], problems=a["problems"],
                  smoke_failures=a["smoke_failures"], proven=a["ok"],
                  outcome="proven" if a["ok"] else f"not proven ({len(a['failing_goals'])} failing goals, "
                                                    f"{len(a['problems'])} report properties not Valid)")
    return a


def round_wp(out, r, standin, hint_set, rec, d, a, t0):
    """t07c method change (a): round-mode WP on TDStep + lemmas; when all proven, one fresh full replay."""
    wlog, ws = verifier(out, d, "round", timeout=max(60, int(a.budget_min * 60 - budget_s(t0)) + 60),
                        extra=(out / "round-cache", a.round_timeout))
    ar = assess_round(d, wlog)
    rec["round_wp"] = {"exit": ws["exit_code"], "wall_s": ws["wall_s"], "peak_rss_mb": ws["peak_rss_mb"],
                       "log": str(wlog), "log_sha256": ws["log_sha256"], "timed_out": ws.get("timed_out"),
                       "n_goals": ar["n_goals"], "n_passed": ar["n_passed"], "n_failing": len(ar["failing_goals"]),
                       "timeout_s": a.round_timeout}
    rec["positions"] = a.positions
    if ws["exit_code"] != 0 or ar["n_tdstep_goals"] == 0:
        rec.update(proven=False, failing_goals=None, parse_error=wlog.read_text(errors="replace")[-4000:],
                   outcome="round WP run failed (exit %s, %d goals%s)" % (
                       ws["exit_code"], ar["n_goals"], ", budget timeout" if ws.get("timed_out") else ""))
        return
    rec["failing_goals"] = ar["failing_goals"]
    if not ar["ok"]:
        rec.update(proven=False, problems=[], smoke_failures=[],
                   outcome=f"not proven in round mode ({len(ar['failing_goals'])} goals not proven at {a.round_timeout} s)")
        return
    if budget_s(t0) / 60 >= a.budget_min:
        rec.update(proven=False, outcome="round mode proved every goal; budget spent before the final replay")
        return
    log(out, f"round {r}: round mode proved all {ar['n_goals']} goals; fresh full replay starts")
    fin = {}
    d2 = run_dir(out, f"final-r{r}", (d / UNIT).read_text())
    wp_round(out, f"final-r{r}", standin, hint_set, fin, mode="wp-smoke", d=d2,
             timeout=max(60, int(a.budget_min * 60 - budget_s(t0)) + 60))
    rec["final"] = {k: fin.get(k) for k in ("wp", "n_goals", "outcome", "proven")}
    rec["final"]["n_problems"] = len(fin.get("problems") or [])
    rec["final"]["n_smoke_failures"] = len(fin.get("smoke_failures") or [])
    rec["proven"] = bool(fin.get("proven"))
    rec["problems"] = fin.get("problems") or []
    rec["smoke_failures"] = fin.get("smoke_failures") or []
    gj = d2 / "goals.json"
    if gj.exists():
        goals = json.loads(gj.read_text())
        rec["failing_goals"] = H.goal_positions(goals, (d2 / UNIT).read_text(), UNIT, headers_text())
    rec["outcome"] = "proven (fresh full replay)" if rec["proven"] else "final replay: " + str(fin.get("outcome"))


def budget_s(t0):
    return time.time() - t0 - LOCKWAIT[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--budget-min", type=float, default=60)
    ap.add_argument("--only-run", help="hint-set JSON: run WP once with these hints, no Codex")
    ap.add_argument("--variant", help="C file replacing the stand-in (negative control)")
    ap.add_argument("--mode", default="wp-smoke")
    ap.add_argument("--round0-from", help="reuse the no-hint run of an earlier counted run (same stand-in)")
    ap.add_argument("--repair-turns", type=int, default=0,
                    help="in-round repair turns after a failed hint check (same Codex session)")
    ap.add_argument("--round-mode", action="store_true", help="t07c (a): round WP on TDStep + lemmas, final replay")
    ap.add_argument("--round-timeout", type=int, default=10, help="t07c (a): per-prover timeout in round mode")
    ap.add_argument("--examples", action="store_true", help="t07c (b): syntax-checked examples in the prompt")
    ap.add_argument("--positions", action="store_true", help="t07c (c): failing goals with source positions")
    ap.add_argument("--resume-rounds", action="store_true", help="t07c: one Codex session for all rounds")
    ap.add_argument("--owner", default="t07")
    a = ap.parse_args()
    OWNER[0] = a.owner
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    standin = Path(a.variant).read_text() if a.variant else (STANDIN_DIR / UNIT).read_text()
    if a.only_run:
        hs = json.loads(Path(a.only_run).read_text())
        rec = {"round": "only", "hints": hs, "standin_sha256": hashlib.sha256(standin.encode()).hexdigest()}
        bad = H.check(standin, hs)
        if bad:
            rec.update(outcome="rejected", rejections=bad)
        else:
            wp_round(out, "only-run", standin, hs, rec, mode=a.mode)
        (out / "only-run.json").write_text(json.dumps(rec, indent=1))
        log(out, f"only-run: {rec['outcome']}")
        return
    t_start = time.time()
    meta = {"started": now(), "pin": PIN, "codex_version": subprocess.run([CODEX, "--version"], capture_output=True,
            text=True).stdout.strip(), "standin_sha256": {f: sha(STANDIN_DIR / f) for f in [UNIT] + HEADERS},
            "cpp_unit_sha256": sha(CPP_UNIT), "rounds": a.rounds, "budget_min": a.budget_min,
            "wp_flags": (HERE / "wp_run.sh").read_text(), "wp_run_sha256": sha(HERE / "wp_run.sh"),
            "repair_turns": a.repair_turns,
            "method_changes_t07c": {"round_mode": a.round_mode, "round_timeout_s": a.round_timeout,
                                    "examples": a.examples, "positions": a.positions,
                                    "resume_rounds": a.resume_rounds},
            "examples_sha256": {f.name: sha(f) for f in sorted(EXAMPLES.glob("*")) if f.is_file()} if a.examples else None,
            "loop_sha256": sha(HERE / "loop.py"), "hints_sha256": sha(HERE / "hints.py")}
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    history = []
    if a.round0_from:
        src = Path(a.round0_from)
        old_meta = json.loads((src / "meta.json").read_text())
        assert old_meta["standin_sha256"] == meta["standin_sha256"], "round 0 is from a different stand-in"
        rec = json.loads((src / "history.json").read_text())[0]
        rec["reused_from"] = str(src)
        log(out, f"round 0: reused from {src} (same stand-in hashes)")
    else:
        rec = {"round": 0, "hints": [], "started": now()}
        log(out, "round 0: WP with no hints")
        wp_round(out, "round-0", standin, [], rec)
        rec["elapsed_min"] = round((time.time() - t_start) / 60, 2)
    if a.positions and rec.get("wp", {}).get("goals_json"):
        gj = Path(rec["wp"]["goals_json"])
        if not gj.exists() and a.round0_from:  # t07's run folders were renamed after the runs
            gj = Path(a.round0_from) / "round-0" / "goals.json"
            assert sha(gj) == rec["wp"]["goals_sha256"], "reused round-0 goals.json changed"
        if gj.exists():
            rec["failing_goals"] = H.goal_positions(json.loads(gj.read_text()), standin, UNIT, headers_text())
            rec["positions"] = True
    history.append(rec)
    (out / "history.json").write_text(json.dumps(history, indent=1))
    log(out, f"round 0 (no hints, before the counted loop): {rec['outcome']} in {rec['elapsed_min']} min")
    proven = rec.get("proven", False)
    # Assumption (ticket 07 Answer): map 13 item 3 runs WP without hints first; the loop's 60-minute
    # budget (item 11) starts with the first provider call, fed by that run's failing goals.
    t0 = time.time()
    LOCKWAIT[0] = 0.0
    log(out, "counted loop starts (budget clock at 0)")
    r = 0
    thread = None
    keep = a.repair_turns > 0 or a.resume_rounds
    while not proven and r < a.rounds:
        elapsed = budget_s(t0) / 60
        if elapsed >= a.budget_min:
            log(out, f"budget spent at {elapsed:.1f} min")
            break
        r += 1
        if a.resume_rounds and thread:
            prompt = (f"Round {r} of at most {a.rounds}; minutes used so far: {elapsed:.1f} of {a.budget_min}.\n"
                      + feedback_text(history, resumed=True)
                      + "\nReturn the COMPLETE hint set for this round in the same JSON format (it replaces the previous set).")
            log(out, f"round {r}: Codex call, resumed session ({len(prompt)} chars)")
            c = codex_call(out, r, prompt, resume=thread, turn=0, keep_session=True)
        else:
            prompt = PROMPT.format(round=r, rounds=a.rounds, minutes=elapsed, budget=a.budget_min,
                                   method_notes=method_notes(a), feedback=feedback_text(history),
                                   files=workspace_files(standin))
            log(out, f"round {r}: Codex call ({len(prompt)} chars)")
            c = codex_call(out, r, prompt, keep_session=keep)
        rec = {"round": r, "started": now(), "codex": {k: c[k] for k in ("exit", "wall_s", "usage", "error")},
               "codex_notes": c.get("notes"), "hints": c["hints"], "turns": []}
        turn = 0
        while True:
            chk = {}
            d = None
            if c["hints"] is not None:
                d = precheck(out, f"round-{r}-turn{turn}" if keep else f"round-{r}", standin, c["hints"], chk)
            rec["turns"].append({"turn": turn, "codex": {k: c[k] for k in ("exit", "wall_s", "usage", "error")},
                                 "n_hints": len(c["hints"] or []), "check": chk.get("outcome", "passed"),
                                 "rejections": chk.get("rejections"), "parse_error": (chk.get("parse_error") or "")[-3000:]})
            if d is not None or c["hints"] is None or turn >= a.repair_turns or budget_s(t0) / 60 >= a.budget_min:
                break
            turn += 1
            msg = ("The proof hint check rejected your hint set: " + chk.get("outcome", "") + "\n"
                   + "\n".join(f"- {x['id']}: {x['rule']} {x.get('detail', '')}" for x in chk.get("rejections") or [])
                   + ("\nFrama-C output (it stops at the first error; check the whole set for the same mistake):\n"
                      + chk.get("parse_error", "")[-3000:] + "\n" + blame_text(chk) if chk.get("parse_error") else "")
                   + "\nReturn the COMPLETE corrected hint set in the same JSON format.")
            log(out, f"round {r}: repair turn {turn} ({chk.get('outcome')})")
            c = codex_call(out, r, msg, resume=c["thread"], turn=turn, keep_session=True)
            for k, v in (c.get("usage") or {}).items():
                rec["codex"]["usage"][k] = rec["codex"]["usage"].get(k, 0) + v
            rec["codex"]["wall_s"] = round(rec["codex"]["wall_s"] + c["wall_s"], 1)
            rec["hints"] = c["hints"]
            rec["codex_notes"] = c.get("notes")
        thread = c.get("thread") or thread
        rec["codex_thread"] = thread
        rec["codex_calls"] = turn + 1
        if c["hints"] is None:
            rec["outcome"] = f"no hint set (Codex error: {c['error']})"
        elif d is None:
            rec.update({k: v for k, v in chk.items()})
        elif budget_s(t0) / 60 >= a.budget_min:
            rec["outcome"] = "budget spent before the WP run"
        elif a.round_mode:
            round_wp(out, r, standin, c["hints"], rec, d, a, t0)
            proven = rec.get("proven", False)
        else:
            wp_round(out, f"round-{r}", standin, c["hints"], rec, d=d,
                     timeout=max(60, int(a.budget_min * 60 - budget_s(t0)) + 60))
            proven = rec.get("proven", False)
        rec["elapsed_min"] = round(budget_s(t0) / 60, 2)
        rec["lock_wait_s_so_far"] = round(LOCKWAIT[0], 1)
        history.append(rec)
        (out / "history.json").write_text(json.dumps(history, indent=1))
        log(out, f"round {r}: {rec['outcome']} at {rec['elapsed_min']} min")
    summary = {"proven": proven, "rounds": r, "codex_calls": sum(h.get("codex_calls", 1) for h in history[1:]),
               "elapsed_min": round(budget_s(t0) / 60, 2),
               "no_hint_run_min": history[0]["elapsed_min"], "lock_wait_excluded_s": round(LOCKWAIT[0], 1),
               "total_incl_no_hint_min": round((time.time() - t_start) / 60, 2),
               "within_budget": proven and budget_s(t0) / 60 <= a.budget_min,
               "tokens": {}, "finished": now()}
    for h in history:
        for k, v in ((h.get("codex") or {}).get("usage") or {}).items():
            summary["tokens"][k] = summary["tokens"].get(k, 0) + v
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    log(out, f"done: {json.dumps(summary)}")


if __name__ == "__main__":
    main()

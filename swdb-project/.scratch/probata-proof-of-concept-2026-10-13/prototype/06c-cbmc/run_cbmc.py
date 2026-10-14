#!/usr/bin/env python3
"""Ticket 06 continuation (CBMC box), 2026-10-14 ET. Throwaway. Runner and verdict check.

Usage: run_cbmc.py [--check] [--runs DIR] [--host mac|mbit10] [--extra 'cbmc flags'] [--tag T] JOB...
       (JOB = a name from JOBS, or 'all', 'units', 'controls', 'sanity')
Runs the selected CBMC jobs ONE AT A TIME as one verifier_run.py job on the Mac (machine-wide lock,
8 GB watchdog), each job with its own 900 s budget (cbmc_job.py), then checks every verdict against
the table below. --check only re-checks existing logs. On mbit10 (--host mbit10) the caller runs it
inside a socket lane; verifier_run.py is not used there (the lane is the exclusion).

Every job: CBMC 6.11 on the hand-lowered C (unit_peter.c / unit_maa.c + dx100_stubs.h), all
inputs symbolic within the proof-unit preconditions (harness.h), bounds threads 1, lanes 2,
chunk 2, vertices 3, edges <= 3, frontier <= 2, parent in [-3, 3).
Unwinding: --unwind 9 (every fixed loop: 8 tiles, 8 registers, the P2 loops, the 5-step range
fold) and --unwindset per data-dependent loop, from the bounds (CBMC's bound K = iterations + 1,
the loop head is evaluated once more), with --unwinding-assertions: a reachable iteration past a
bound fails the job, so a proof is complete at these bounds.
  chunk loop            ceil(frontier / chunk) = 1 iteration          -> 2
  range loop (for(;;))  <= edges non-empty calls + 1 empty call = 4   -> 5
  lanes loop            <= TILE_SIZE = 2                              -> 3
  CPU frontier loop     <= frontier = 2                               -> 3
  CPU edge loop         <= edges = 3 (out-degree)                     -> 4
  TDStepMAA while       1 (tile path: idx += 2 >= len; CPU path: idx = len) -> 2
  queue flush           <= pushes <= edges + 1 forged duplicate = 4   -> 5
"""
import argparse, glob, json, os, re, shlex, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VR = "/tmp/claude/probata-tools/verifier_run.py"
BUDGET = 900

UNWIND = {
    "peter": "--unwind 9 --unwindset TDStep.0:3,TDStep.1:5,TDStep.2:2,TDStep.3:4,TDStep.4:3,qb_flush.0:5",
    "maa": "--unwind 9 --unwindset TDStepMAA.0:3,TDStepMAA.1:5,TDStepMAA.2:4,TDStepMAA.3:3,TDStepMAA.4:2,qb_flush.0:5",
}
BASE = "--unwinding-assertions --sat-solver cadical --slice-formula --trace"

# name: (unit, -D flags, expected verdict, expected failing checks (refuted: every failed property
# must be one of these, at least one))
JOBS = {
    # faithfulness: ticket 06's SAW concrete input (diagnostics 1 and 6)
    "peter_concrete": ("peter", "-DSWDB_CONCRETE", "proven", []),
    "maa_concrete": ("maa", "-DSWDB_CONCRETE", "proven", []),
    # the two proof units
    "peter": ("peter", "", "proven", []),
    "maa": ("maa", "", "proven", []),
    # the twelve single-thread controls (expected checks as ticket 06's run_spike.sh)
    "peter_dropped_wait": ("peter", "-DSWDB_DXC_FAULT_DROPPED_WAIT", "refuted", ["size_read_before_ready"]),
    "peter_read_before_wait": ("peter", "-DSWDB_DXC_FAULT_READ_BEFORE_WAIT", "refuted", ["tile_read_before_ready"]),
    "peter_index_wrap": ("peter", "-DSWDB_DXC_FAULT_INDEX_WRAP", "refuted", ["stream_bounds"]),
    "peter_forged_frontier": ("peter", "-DSWDB_DXC_FAULT_FORGED_FRONTIER_V2", "refuted", ["P2_reached_pushed_exactly_once"]),
    "peter_dropped_continuation": ("peter", "-DSWDB_DXC_FAULT_DROPPED_CONTINUATION", "refuted",
                                   ["P2_reached_pushed_exactly_once", "P2_parent_is_frontier_neighbor"]),
    "peter_chunk_off_by_one": ("peter", "-DSWDB_DXC_FAULT_CHUNK_OFF_BY_ONE", "refuted", ["tile_truncation"]),
    "peter_skipped_cas_recheck": ("peter", "-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK", "refuted", ["P2_reached_pushed_exactly_once"]),
    "maa_wait_deleted": ("maa", "-DMAA_CONTROL=1", "refuted", ["tile_read_before_ready"]),
    "maa_old_wait_rule": ("maa", "-DMAA_CONTROL=2 -DSWDB_OLD_WAIT_RULE", "refuted", ["tile_read_before_ready"]),
    "maa_cpu_read_parent": ("maa", "-DMAA_CONTROL=3", "refuted", ["cpu_access_overlaps_unfinished"]),
    "maa_wait_tile6": ("maa", "-DMAA_CONTROL=4", "refuted", ["tile_read_before_ready"]),
    "maa_wait_tile7": ("maa", "-DMAA_CONTROL=5", "refuted", ["tile_read_before_ready"]),
    # faithfulness 2: sanity controls (non-vacuity; precondition deletion). Deleting "edge targets are
    # vertices" must be refuted by the checks that rely on it: the gather's memory region (DX100
    # path), CBMC's bounds check on parent[v] (CPU path), and P2's "pushed entry is a vertex".
    "peter_sanity_reach": ("peter", "-DSWDB_SANITY_REACH", "refuted", ["sanity_reach_end", "sanity_reach_accelerated_claim"]),
    "maa_sanity_reach": ("maa", "-DSWDB_SANITY_REACH", "refuted", ["sanity_reach_end", "sanity_reach_accelerated_claim"]),
    "peter_drop_pre_neighbor": ("peter", "-DSWDB_DROP_PRE_NEIGHBOR", "refuted",
                                ["gather_memory_region", "@bounds", "P2_pushed_is_a_vertex"]),
    "maa_drop_pre_neighbor": ("maa", "-DSWDB_DROP_PRE_NEIGHBOR", "refuted",
                              ["gather_memory_region", "@bounds", "P2_pushed_is_a_vertex"]),
    "peter_drop_pre_parent_lower": ("peter", "-DSWDB_DROP_PRE_PARENT_LOWER", "proven", []),
    "maa_drop_pre_parent_lower": ("maa", "-DSWDB_DROP_PRE_PARENT_LOWER", "proven", []),
}
GROUPS = {
    "units": ["peter", "maa"],
    "controls": [j for j in JOBS if JOBS[j][2] == "refuted" and "sanity" not in j and "drop_pre" not in j],
    "sanity": ["peter_concrete", "maa_concrete", "peter_sanity_reach", "maa_sanity_reach", "peter_drop_pre_neighbor",
               "maa_drop_pre_neighbor", "peter_drop_pre_parent_lower", "maa_drop_pre_parent_lower"],
}


def command(name, extra, base=BASE):
    unit, flags, _, _ = JOBS[name]
    return f"cbmc unit_{unit}.c -DSWDB_CBMC {flags} {UNWIND[unit]} {base} {extra}".strip()


RESULT = re.compile(r"^\[([^\]]+)\] (?:line \d+ )?(.*): (SUCCESS|FAILURE|UNKNOWN)$")


def check(name, runs, tag):
    unit, flags, want, sites = JOBS[name]
    log = os.path.join(runs, f"{name}{tag}.log")
    if not os.path.exists(log + ".json"):
        return False, f"MISSING {name}{tag}"
    s = json.load(open(log + ".json"))
    text = open(log).read()
    failed = []
    for line in text.splitlines():
        m = RESULT.match(line.strip())
        if m and m.group(3) == "FAILURE":
            failed.append((m.group(1), m.group(2)))
    unwind_failed = [f for f in failed if ".unwind." in f[0]]
    if s["timed_out"]:
        verdict = "timeout"
    elif "VERIFICATION SUCCESSFUL" in text and s["exit_code"] == 0:
        verdict = "proven"
    elif "VERIFICATION FAILED" in text and s["exit_code"] == 10:
        verdict = "refuted"
    else:
        verdict = f"error(exit {s['exit_code']})"
    ok = verdict == want and not unwind_failed
    detail = ""
    if verdict == "refuted":
        def expected(desc):
            for site in sites:
                if site == "@bounds" and ("bound" in desc or "pointer" in desc or "dereference" in desc):
                    return True
                if desc == site:
                    return True
            return False
        names = sorted(set(d for _, d in failed))
        bad = [d for d in names if not expected(d)]
        has_trace = "Trace for" in text or "Counterexample" in text
        ok = ok and bool(names) and not bad and has_trace
        detail = f" failed={names}" + (f" UNEXPECTED={bad}" if bad else "") + ("" if has_trace else " NO_TRACE")
    if unwind_failed:
        detail += f" UNWINDING_FAILED={unwind_failed}"
    props = re.search(r"\*\* (\d+) of (\d+) failed", text)
    nprops = re.findall(r"^\[[^\]]+\] .*: (?:SUCCESS|FAILURE)", text, re.M)
    status = "PASS" if ok else "FAIL"
    return ok, (f"{status} {name}{tag}: want {want}, got {verdict}; wall {s['wall_seconds']} s; peak {s['peak_rss_mb']} MB; "
                f"properties {len(nprops)}; sha256 {s['log_sha256']}{detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--runs", default="/tmp/claude/probata-runs/t06c")
    ap.add_argument("--host", default="mac")
    ap.add_argument("--extra", default="")
    ap.add_argument("--base", default=BASE, help="replace the solver/slicing flags (encoding attempts)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--budget", type=float, default=BUDGET)
    ap.add_argument("--inside-lock", action="store_true", help="already inside a verifier_run.py job")
    ap.add_argument("jobs", nargs="+")
    a = ap.parse_args()
    names = []
    for j in a.jobs:
        names += list(JOBS) if j == "all" else GROUPS.get(j, [j])
    for n in names:
        if n not in JOBS:
            sys.exit(f"unknown job {n}")
    os.makedirs(a.runs, exist_ok=True)
    if not a.check:
        jobfile = os.path.join(a.runs, f"jobs{a.tag}-{os.getpid()}.tsv")
        with open(jobfile, "w") as f:
            for n in names:
                f.write(f"{os.path.join(a.runs, n + a.tag + '.log')}\t{HERE}\t{command(n, a.extra, a.base)}\n")
        inner = [sys.executable, os.path.join(HERE, "cbmc_job.py"), "--budget", str(a.budget), "--host", a.host, jobfile]
        if a.host == "mac" and not a.inside_lock:
            subprocess.run([VR, "--log", os.path.join(a.runs, f"batch{a.tag}-{os.getpid()}.log"), "--owner", "t06c",
                            "--timeout", str(a.budget * len(names) + 120), "--"] + inner)
        else:
            subprocess.run(inner)
    allok = True
    for n in names:
        ok, line = check(n, a.runs, a.tag)
        print(line)
        allok = allok and ok
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()

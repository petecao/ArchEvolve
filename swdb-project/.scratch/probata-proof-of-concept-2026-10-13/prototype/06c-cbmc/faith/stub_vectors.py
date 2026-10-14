#!/usr/bin/env python3
"""Ticket 06 continuation (CBMC box), 2026-10-14 ET. Throwaway. Faithfulness test 3: the C stubs
(dx100_stubs.h) against ticket 06's SAW summaries (summaries.saw over ghost.cry), call by call.

1. Builds the C lowering natively with -DSWDB_VECTORS for every build (safe units, 12 controls),
   runs ticket 06's SAW concrete input and a pseudo-random 1/STRIDE sample of the bounded domain,
   and logs every summary call: arguments, state before, state after (or the failed CHECK).
2. Writes one Cryptol module per build (vec_<build>.cry) with one Bit per call, from
   stubcheck.cry (which imports ghost.cry unchanged), and evaluates it with Cryptol (SAW 1.6's
   bundled cryptol) in ONE verifier_run.py job: every Bit must be True.
Usage: stub_vectors.py [--stride N] [--out DIR]
"""
import argparse, collections, hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
GHOST_DIR = os.path.join(PROTO, "..", "06-two-lanes")
CRYPTOL = os.path.expanduser("~/opt/verifiers/saw-1.6/saw-1.6-macos-15-ARM64-with-solvers/bin/cryptol")
CLANG = "/opt/homebrew/opt/llvm/bin/clang"
VR = "/tmp/claude/probata-tools/verifier_run.py"

BUILDS = [
    ("peter_safe", "peter", ""),
    ("peter_dropped_wait", "peter", "-DSWDB_DXC_FAULT_DROPPED_WAIT"),
    ("peter_read_before_wait", "peter", "-DSWDB_DXC_FAULT_READ_BEFORE_WAIT"),
    ("peter_index_wrap", "peter", "-DSWDB_DXC_FAULT_INDEX_WRAP"),
    ("peter_forged_frontier", "peter", "-DSWDB_DXC_FAULT_FORGED_FRONTIER_V2"),
    ("peter_dropped_continuation", "peter", "-DSWDB_DXC_FAULT_DROPPED_CONTINUATION"),
    ("peter_chunk_off_by_one", "peter", "-DSWDB_DXC_FAULT_CHUNK_OFF_BY_ONE"),
    ("peter_skipped_cas_recheck", "peter", "-DSWDB_DXC_FAULT_SKIPPED_CAS_RECHECK"),
    ("maa_safe", "maa", ""),
    ("maa_wait_deleted", "maa", "-DMAA_CONTROL=1"),
    ("maa_old_wait_rule", "maa", "-DMAA_CONTROL=2 -DSWDB_OLD_WAIT_RULE"),
    ("maa_cpu_read_parent", "maa", "-DMAA_CONTROL=3"),
    ("maa_wait_tile6", "maa", "-DMAA_CONTROL=4"),
    ("maa_wait_tile7", "maa", "-DMAA_CONTROL=5"),
]
MEM = {0: "qOf", 1: "oOf", 2: "nOf", 3: "pOf"}


def u32(x):
    return str(int(x) & 0xFFFFFFFF)


def lit(words):
    assert len(words) == 115, len(words)
    return "[" + ",".join(u32(w) for w in words) + "] : S"


def bit(b):
    return "True" if b else "False"


def emit(line, old_rule):
    head, pre, post, ret = [x.strip() for x in line.split("|")]
    f = head.split()
    name, a = f[1], [int(x) for x in f[2:10]]
    pre = pre.split()
    ok = not post.startswith("FAIL")
    post = pre if not ok else post.split()
    A = [u32(x) for x in a]
    if name == "const": call = f"vConst {A[0]} {A[1]}"
    elif name == "wait": call = f"vWait {bit(old_rule)} {A[0]}"
    elif name == "size": call = f"vSize {A[0]} {u32(ret)}"
    elif name == "probe_tile": call = f"vProbeTile {A[0]}"
    elif name == "probe_cpu": call = f"vProbeCpu {A[0]} {A[1]}"
    elif name == "poke": call = f"vPoke {A[0]} {A[1]}"
    elif name == "stream_bounds": call = f"vStreamBounds {A[0]} {A[1]} {A[2]}"
    elif name == "stream_capacity": call = f"vStreamCap {A[0]} {A[1]} {A[2]}"
    elif name == "stream_load": call = f"vStreamLoad {bit(a[0] == 1)} {A[1]} {A[2]} {A[3]} {A[4]} {A[5]}"
    elif name == "gather":
        if a[0] < 0:   # no SAW override for this pointer: the call must have failed
            return name, ok, f"~{bit(ok)}"
        call = f"vGather ({MEM[a[0]]} s) {a[1]} {a[0]} {A[2]} {A[3]} {A[4]}"
    elif name == "range": call = "vRange " + " ".join(A)
    elif name == "alu": call = "vAlu " + " ".join(A[:5])
    elif name == "store": call = f"vStore {bit(a[0] == 1)} {A[1]} {A[2]} {A[3]} {A[4]}"
    else: raise SystemExit(f"unknown summary {name}")
    return name, ok, f"{call} s t {bit(ok)} where s = {lit(pre)}; t = {lit(post)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=10000, help="Peter; TDStepMAA uses stride / 6 (its domain is 6x smaller)")
    ap.add_argument("--out", default="/tmp/claude/probata-runs/t06c/faith/vectors")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stats = {}
    mods, mutants = [], []
    for build, unit, flags in BUILDS:
        exe = os.path.join(a.out, f"v_{build}")
        subprocess.run(f"{CLANG} -std=c11 -O1 -DSWDB_NATIVE -DSWDB_VECTORS {flags} {PROTO}/unit_{unit}.c -o {exe}",
                       shell=True, check=True)
        lines = []
        for mode in (["concrete"] if build.endswith("_safe") else []) + [f"vectors {a.stride if unit == 'peter' else max(1, a.stride // 6)}"]:
            out = subprocess.run(f"{exe} {mode}", shell=True, check=True, capture_output=True, text=True).stdout
            lines += [l for l in out.splitlines() if l.startswith("V ")]
        os.remove(exe)
        defs, names = [], []
        cnt = collections.Counter()
        for i, l in enumerate(lines):
            name, ok, body = emit(l, "OLD_WAIT_RULE" in flags)
            cnt[(name, ok)] += 1
            defs.append(f"v{i} = {body}")
            names.append(f"v{i}")
        mod = f"vec_{build}"
        with open(os.path.join(a.out, mod + ".cry"), "w") as f:
            f.write(f"module {mod} where\nimport ghost\nimport stubcheck\n\n" + "\n".join(defs) +
                    f"\n\nresults : [{len(names)}]\nresults = [" + ", ".join(names) + "]\n")
        stats[build] = (len(lines), cnt)
        mods.append(mod)
        if build.endswith("_safe"):
            # Checker sensitivity: the first completed call of each summary, with one tile-memory
            # word of its state after changed by 1. Every one of these Bits must be False.
            mdefs, seen = [], set()
            for l in lines:
                head, pre, post, ret = [x.strip() for x in l.split("|")]
                name = head.split()[1]
                if post.startswith("FAIL") or name in seen:
                    continue
                seen.add(name)
                w = post.split(); w[81] = str(int(w[81]) + 1)
                _, _, body = emit(" | ".join([head, pre, " ".join(w), ret]), False)
                mdefs.append((name, f"m{len(mdefs)} = {body}"))
            mm = f"mut_{build}"
            with open(os.path.join(a.out, mm + ".cry"), "w") as f:
                f.write(f"module {mm} where\nimport ghost\nimport stubcheck\n\n" + "\n".join(d for _, d in mdefs) +
                        f"\n\n// mutated summaries: {' '.join(n for n, _ in mdefs)}\nresults : [{len(mdefs)}]\nresults = ["
                        + ", ".join(f"m{i}" for i in range(len(mdefs))) + "]\n")
            mutants.append(mm)
    # One verifier_run.py job evaluates every module.
    script = os.path.join(a.out, "eval.sh")
    with open(script, "w") as f:
        f.write("#!/bin/sh\n")
        f.write(f"export CRYPTOLPATH={HERE}:{os.path.abspath(GHOST_DIR)}:{a.out}\n")
        for m in mods:
            f.write(f"echo MODULE {m}; {CRYPTOL} {a.out}/{m}.cry -c 'results == ~zero' -c ':set base=2' -c 'results' 2>&1 | grep -v '^Loading'\n")
        for m in mutants:   # expected: results == zero (every mutated call rejected)
            f.write(f"echo MUTANT {m}; {CRYPTOL} {a.out}/{m}.cry -c 'results == zero' -c ':set base=2' -c 'results' 2>&1 | grep -v '^Loading'\n")
    log = os.path.join(a.out, "eval.log")
    subprocess.run([VR, "--log", log, "--owner", "t06c", "--timeout", "3600", "--", "sh", script])
    text = open(log).read()
    print(text)
    for build, (n, cnt) in stats.items():
        print(build, n, dict(sorted((f"{k[0]}:{'ok' if k[1] else 'FAIL'}", v) for k, v in cnt.items())))
    sha = hashlib.sha256(text.encode()).hexdigest()
    print("eval.log sha256", sha)


if __name__ == "__main__":
    main()

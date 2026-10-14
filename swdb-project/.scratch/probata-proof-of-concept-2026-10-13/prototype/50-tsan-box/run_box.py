#!/usr/bin/env python3
"""Ticket 50 box check: does Archer (TSan + OMPT) separate racy from race-free fixtures?

Each fixture is built with clang -fopenmp -fsanitize=thread and run with libarcher
loaded through OMP_TOOL_LIBRARIES, once per thread count, up to --repeats times.
A run counts only if Archer says it attached to a TSan build (ARCHER_OPTIONS=verbose=1).

- racy fixture: passes if some run (of --repeats) prints a TSan data-race report.
- race-free fixture: passes if every run (all --repeats) is quiet.

Run flags follow the upstream Archer lit config (openmp/tools/archer/tests/lit.cfg):
-gdwarf-4 -O1 -fsanitize=thread, TSAN_OPTIONS=ignore_noninstrumented_modules=1,
and the deflake rule (racy tests may need up to 10 runs to show the race).

Writes <out>/results.json (versions, flags, per-run verdicts, log sha256) and exits
0 only if every fixture passes at every thread count.
"""
import argparse, hashlib, json, os, subprocess, sys

ARCHER_ON = "Archer detected OpenMP application with TSan"
RACE = "WARNING: ThreadSanitizer: data race"
CFLAGS = ["-fopenmp", "-gdwarf-4", "-O1", "-fsanitize=thread"]


def sh(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def run_fixture(src, label, a, env_base):
    name = os.path.splitext(os.path.basename(src))[0]
    exe = os.path.join(a.out, "bin", name)
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    cc = [a.cc, *CFLAGS, *sum((["-I", d] for d in a.include), []),
          "-L", a.omp_libdir, "-Wl,-rpath," + a.omp_libdir, src, "-o", exe]
    b = sh(cc)
    rec = {"fixture": src, "label": label, "compile": " ".join(cc),
           "compile_rc": b.returncode, "runs": []}
    if b.returncode != 0:
        rec["compile_err"] = b.stderr[-2000:]
        rec["pass"] = False
        return rec
    ok_all = True
    for t in a.threads:
        env = dict(env_base, OMP_NUM_THREADS=str(t))
        seen_race, attached, quiet_all, n = False, True, True, 0
        for i in range(a.repeats):
            r = sh([exe], env=env)
            out = r.stdout + r.stderr
            log = os.path.join(a.out, "logs", f"{name}.t{t}.r{i}.log")
            os.makedirs(os.path.dirname(log), exist_ok=True)
            open(log, "w").write(out)
            n += 1
            race = RACE in out
            attached = attached and (ARCHER_ON in out)
            seen_race |= race
            quiet_all &= not race
            rec["runs"].append({"threads": t, "rep": i, "rc": r.returncode,
                                "archer_attached": ARCHER_ON in out, "race": race,
                                "log": log,
                                "log_sha256": hashlib.sha256(out.encode()).hexdigest()})
            if label == "racy" and race:
                break  # deflake rule: stop at the first report
        ok = attached and (seen_race if label == "racy" else quiet_all)
        rec.setdefault("by_threads", {})[str(t)] = {
            "runs": n, "archer_attached_every_run": attached,
            "race_reported": seen_race, "pass": ok}
        ok_all &= ok
    rec["pass"] = ok_all
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archer", required=True, help="path to libarcher.dylib")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cc", default="/opt/homebrew/opt/llvm/bin/clang")
    ap.add_argument("--omp-libdir", default="/opt/homebrew/opt/llvm/lib")
    ap.add_argument("--threads", default="2,4")
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--racy", nargs="*", default=[])
    ap.add_argument("--race-free", nargs="*", default=[])
    a = ap.parse_args()
    a.threads = [int(x) for x in a.threads.split(",")]
    os.makedirs(a.out, exist_ok=True)
    env = dict(os.environ,
               OMP_TOOL_LIBRARIES=a.archer,
               ARCHER_OPTIONS="verbose=1 report_data_leak=1",
               TSAN_OPTIONS="ignore_noninstrumented_modules=1")
    recs = [run_fixture(f, "racy", a, env) for f in a.racy]
    recs += [run_fixture(f, "race-free", a, env) for f in a.race_free]
    res = {"cc_version": sh([a.cc, "--version"]).stdout.splitlines()[0],
           "archer": a.archer,
           "archer_sha256": hashlib.sha256(open(a.archer, "rb").read()).hexdigest()
           if os.path.exists(a.archer) else None,
           "cflags": CFLAGS, "threads": a.threads, "repeats": a.repeats,
           "env": {k: env[k] for k in ("OMP_TOOL_LIBRARIES", "ARCHER_OPTIONS", "TSAN_OPTIONS")},
           "fixtures": recs, "pass": all(r["pass"] for r in recs) and bool(recs)}
    json.dump(res, open(os.path.join(a.out, "results.json"), "w"), indent=1)
    for r in recs:
        print(("PASS" if r["pass"] else "FAIL"), r["label"], r["fixture"],
              json.dumps(r.get("by_threads", r.get("compile_err", ""))))
    print("OVERALL", "PASS" if res["pass"] else "FAIL")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

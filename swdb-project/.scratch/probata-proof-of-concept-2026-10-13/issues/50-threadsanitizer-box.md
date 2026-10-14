# 50 — ThreadSanitizer one-day box

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design" (Baselines: a ThreadSanitizer repair baseline runs only if it installs within one day), "Proof-of-concept plan" (A4; time-boxed items end on their fallbacks), "Providers and machines" (Mac rules), "Further Notes" (risk: a Homebrew change breaks LLVM 22)); decisions: [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** 1 day (box)

**What to build:** In one day, find out whether the ThreadSanitizer-accepted repair baseline can run at
all. Install Archer with an instrumented libomp, and run it on the race fixtures: it must report the
race in each racy fixture and stay quiet on each race-free one. If that works within the day, the
evaluation may run the baseline in RQ4. If not, it is recorded as not run, with the reason, and the
paper only cites it.

## Acceptance

- [x] The box start (date and time ET) is recorded. Work stops at one day, with no extension.
- [x] Before any install: free disk (at least 50 GB) and LLVM 22's `clang --version` are recorded.
- [x] The install goes to its own prefix and changes no Homebrew package the analytic evaluator uses.
      After it, LLVM 22 still reports 22.1.8 and the analytic evaluator's LLVM check still passes.
- [x] On success: Archer reports a race on each racy fixture and none on each race-free fixture. Tool
      versions, build flags and thread counts are recorded.
- [x] On failure, or when the day runs out: this ticket's Answer records "not run" and the reason (the
      step that failed and its error).
- [x] The outcome, ran or not run, is stated in this ticket's Answer. It feeds evaluation 09 (whether
      RQ4 can run the baseline) and ticket 59, which waits on this ticket before the freeze.
- [x] Disk used is recorded. Build trees are removed after the box, unless the baseline will run.

## Notes

- **Not in this ticket:** running the baseline as an RQ4 repair mirror
  ([evaluation 09 — RQ4: refutation and repair](../../probata-evaluation-2026-10-13/issues/09-rq4-refutation-and-repair.md));
  45 — Per-thread lowering and 46 — CIVL adapter (the OpenMP race fixtures); 56 — Verifier lineup on
  mbit10; 59 — Method-version review and freeze (waits on this outcome).
- Assumption (not decided in the map): "the race fixtures" are the racy and race-free OpenMP fixtures of
  tickets 45 and 46 if they exist when the box runs. Otherwise, one small pair written for the box: a
  plain store beside a CAS on one location, and the same code with the store removed.
- Assumption (not decided in the map): the box runs on the Mac. If it passes, installing the baseline on
  mbit10 goes with the lineup there (ticket 56).
- Risk: a Homebrew change broke LLVM 22 before (a z3 upgrade, map ticket
  [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)). Check `clang --version` first
  and keep `llvm` pinned.
- Mac: build with a capped job count, one heavy job at a time, under the ~8 GB RSS watchdog.

## Progress (box in flight, 2026-10-14 01:11 ET)

Box start: **2026-10-14 01:06 ET**. Box end: 2026-10-15 01:06 ET (no extension).

- **Pre-install checks (01:06 ET):** `/` has 107 GiB free (`df -h /`). `/opt/homebrew/opt/llvm/bin/clang --version`
  = Homebrew clang 22.1.8. Pinned: `llvm`, `lld`, `z3`. No Homebrew package was installed or changed.
- **What is there already:** brew `llvm` 22.1.8 ships `libomp.dylib` (with OMPT) and
  `lib/clang/22/lib/darwin/libclang_rt.tsan_osx_dynamic.dylib`, but no `libarcher`. Archer since LLVM 10 uses
  OMPT callbacks, so it does not need a separately instrumented libomp. The ticket's "instrumented libomp" is
  the stock OMPT-enabled libomp 22.1.8.
- **Fixtures:** tickets 45 and 46 are not done (`ready-for-agent`), so the box uses the fallback pair in
  `../prototype/50-tsan-box/`: `racy_store_cas.c` (a plain store beside a CAS on `x`) and `racefree_cas.c` (the
  same code with the store removed). Checker: `../prototype/50-tsan-box/run_box.py` (upstream Archer lit flags
  `-gdwarf-4 -O1 -fsanitize=thread`, `TSAN_OPTIONS=ignore_noninstrumented_modules=1`, deflake rule of up to 10
  runs, and every run must show Archer's "attached with TSan" line).
- **Red run (no Archer), 01:09 ET:** TSan itself works on this macOS (Darwin 27, arm64). It reports the racy
  fixture's race, but it also gives a **false race on the race-free fixture at 4 threads** (the `printf` read
  after the join vs. a worker's CAS). This is the false positive that Archer exists to remove. Evidence:
  `/tmp/claude/probata-runs/t50/red/` (`results.json` sha256 `5bd96364…a500ba`, `run.log` sha256 `f1926a14…904e1c`).
- **Archer source:** the 39 files of `openmp/tools/archer` at tag `llvmorg-22.1.8` (tree `2b07b228`), each
  checked against its git blob SHA-1. They are in `/tmp/claude/probata-runs/t50/src/archer-22.1.8/`
  (`ompt-tsan.cpp` sha256 `cc00f7dd…e8fe`). There is no per-component `openmp-22.1.8.src.tar.xz` release
  asset (404).
- **Blocked, 01:10 ET:** the agent's permission gate denied compiling the downloaded source ("code from
  external"). Writing into `~/opt/verifiers/` also needs the sandbox off, and that was denied too. The box is
  **not** failed: no technical step has failed. To continue, Yan-Ru approves the build (one compile, a few
  seconds, about 100 MB RSS), and then `run_box.py` runs with `--archer <prefix>/lib/libarcher.dylib`.
- Disk used so far: 384 KB (`/tmp/claude/probata-runs/t50/`).

## Answer (2026-10-14 02:33 ET)

**Outcome: ran. The ThreadSanitizer-accepted repair baseline can run** (Archer on TSan, Mac, inside the box).
Evaluation 09 may run it in RQ4; ticket 59 may proceed on this outcome.

| Item | Value |
|---|---|
| Box | start 2026-10-14 01:06 ET; finished 02:32 ET (about 1.5 h of the 24 h) |
| Before install | `/` 107 GiB free; Homebrew clang 22.1.8; brew pins `llvm`, `lld`, `z3` |
| Archer | `openmp/tools/archer` at `llvmorg-22.1.8` (39 files, each checked against its git blob SHA-1); `ompt-tsan.cpp` sha256 `cc00f7dd…e8fe` |
| Build | Homebrew clang++ 22.1.8, `-std=c++17 -O2 -g -fPIC -shared -I /opt/homebrew/opt/llvm/lib/clang/22/include`; 1.25 s, 197 MB peak RSS, under `verifier_run.py` |
| Install prefix | `~/opt/verifiers/archer-22.1.8/lib/libarcher.dylib`, sha256 `fd4a1d8e83eee0794d637b9670e049540de080f2f90ec3be4c91c6542a22d878` (own prefix; no Homebrew package changed) |
| libomp | stock Homebrew libomp 22.1.8 (OMPT-enabled; Archer needs nothing else) |
| Fixture flags | `clang -fopenmp -gdwarf-4 -O1 -fsanitize=thread`; `TSAN_OPTIONS=ignore_noninstrumented_modules=1`; `OMP_TOOL_LIBRARIES=<libarcher>`; `ARCHER_OPTIONS=verbose=1` (each run must show Archer attached) |
| Racy fixture `racy_store_cas.c` | race reported at 2 and 4 threads (first run each); Archer attached every run: **pass** |
| Race-free fixture `racefree_cas.c` | no race in 10 of 10 runs at 2 threads and 10 of 10 at 4 threads; Archer attached every run: **pass** |
| Red run (TSan without Archer) | false race on the race-free fixture at 4 threads; Archer removes it (see Progress) |
| After install | clang 22.1.8; analytic evaluator LLVM check `tests/test_openmp_call_projection.py` 12 passed |
| Evidence | `/tmp/claude/probata-runs/t50/green/` (`results.json` sha256 `a82d18fc02692bcdf724623d5c0391a66581de5dbe935cc7289205e162ad2ad6`, `box.log` sha256 `eec03eef…87a`); build log `/tmp/claude/probata-runs/t50/build/build.log`; red run `/tmp/claude/probata-runs/t50/red/` |
| Disk used | 616 KB of run output plus about 0.2 MB for the library and its dSYM |

- **Build trees kept:** the baseline will run (RQ4), so the library and the 39 source files stay. Remove
  `/tmp/claude/probata-runs/t50/src/` after evaluation 09 builds the baseline on mbit10.
- **How it was unblocked:** the agent's permission gate refused the compile twice. Yan-Ru then approved it
  in chat (2026-10-14 02:25 and 02:28 ET), and the main session ran the build and the checker itself.
- Assumption: "the race fixtures" are the fallback pair in `../prototype/50-tsan-box/`, because tickets 45
  and 46 have no fixtures yet. Evaluation 09 should rerun the checker on their OpenMP fixtures once they exist.
- Assumption: the "instrumented libomp" is the stock OMPT-enabled libomp 22.1.8; Archer has used OMPT
  callbacks since LLVM 10.
- **mbit10:** installing Archer there goes with the lineup (ticket 56 left it for this answer). The same
  build command applies, with mbit10's private LLVM 22.1.8 and `--gcc-install-dir` (see ticket 56).

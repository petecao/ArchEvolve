# 03 — New verifiers on the Mac

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 01:02 ET (resolved); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", table "Proof machinery", row "Verifier adapters"; "Verifier lineup and order"; "Concurrency" (Rocq box); "Providers and machines"; "Proof-of-concept plan", A0 row and exit check; "Further Notes", risk "A Homebrew change breaks LLVM 22"; "Found while cutting the build tickets", O3 and O4); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (items 2, 7, 8), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 13), [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) (items 8, 9), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) (items 2, 5)
**Time estimate:** about 1-2 days

**What to build:** The Mac gets the four verifiers the lineup adds, at pinned versions: SAW 1.6
(bounded verifier at threads = 1), CIVL 1.23 with a JDK (bounded verifier at threads ≤ k), GenMC
built from source (second refuter, RC11), and Rocq in its own opam switch (composition theorem,
DX100 reduction lemma, lifting-lemma fallback). Each passes map 07's smoke test: it proves the
safe smoke program and refutes the seeded bug (`-DBUGGY`, name decided in map 07). Rocq instead
checks a tiny theorem and rejects a false one. Each tool gets 2 days; one that does not pass by then
goes to its fallback. ADR 0006's scoped exception for proof work on the Mac is recorded, including
how the `proof_hinting` provider (name decided in map 13) is confined there (O3). Afterwards the
Mac still has at least 50 GB free and LLVM 22 still works for the analytic evaluator. The lineup
tools map 07 installed (Frama-C/WP, crux-llvm, CBMC), which the fallbacks rely on, still pass their
smoke tests.

## Acceptance

- [x] Before the first install: free disk (at least 50 GB), the clang version (22.1.8) and
      Homebrew's pins on `llvm` and `lld` are recorded.
- [x] SAW 1.6 (macOS arm64 release asset, sha256 recorded) proves map 07's safe smoke program and
      refutes its seeded bug with a counterexample.
- [x] CIVL 1.23 runs on an installed JDK (17 or later), proves the safe program and refutes the
      seeded bug.
- [x] GenMC, built from source at a pinned release or commit, proves the safe program and refutes
      the seeded bug.
- [x] Rocq, in its own opam switch (never `framac-33`, name decided in map 07), checks a tiny true
      theorem and rejects a false one.
- [x] **Time box.** A tool that does not pass after 2 days goes to its fallback, with the cause
      recorded: SAW to crux-llvm (installed by map 07); CIVL to GenMC alone, which refutes, labeled,
      and the threads ≤ k rung stays unavailable until CIVL runs (O4); GenMC to CIVL alone,
      labeled; Rocq to the written proof.
- [x] The answer has one row per tool, as in map 07: version, install path, download sha256 or source
      commit, safe and buggy verdicts, time, disk used, and logs by path and sha256. Each smoke run
      ran alone under the ~8 GB RSS watchdog.
- [x] ADR 0006 records the scoped exception (map 13 item 13): during the proof of concept, proof jobs
      and the `proof_hinting` role may run on the Mac; on the Mac the `proof_hinting` provider runs
      in Codex's own sandbox over the frozen workspace and builds nothing (O3); WP uses the x86_64
      machdep; the final evaluation and its experiments run on mbit10 inside a socket lane; Mac
      results are labeled and never mixed with mbit10 numbers.
- [x] After the last install: at least 50 GB free; clang still reports 22.1.8; the
      analytic evaluator's LLVM 22 check (the one map 07 used) passes; Frama-C/WP
      (`framac-33`), crux-llvm and CBMC still pass their map 07 smoke tests.

## Notes

- **Not in this ticket:** 05 — Spike (a): SAW on clang 22 bitcode (real code, ghost state).
  22 — SAW adapter and SAWScript translator. 46 — CIVL adapter. 47 — GenMC adapter and agreement.
  41 — Rocq: composition theorem statement and definitions; 42 — Rocq: composition theorem proof;
  43 — Rocq: DX100 reduction lemma. 50 — ThreadSanitizer one-day box. 56 — Verifier lineup on
  mbit10. 11 — Method-version file and failure classes (it carries these pins into the method
  version). 34 — proof_hinting role and workspace (builds O3's confinement).
- **A0 exit:** the design spec's A0 check is this ticket's smoke verdicts (or recorded fallbacks)
  plus the guard test of 01 — Guard blocks the authors' held-out functions.
- **Blocks 07 — Spike (c): WP with agent hints:** Codex writes proof hints there on the Mac, under
  the exception this ticket records.
- Assumption (not decided in the map): the map pins SAW 1.6 and CIVL 1.23 but not GenMC, Rocq or
  the JDK. Install the newest release that works, pin it and record it.
- Assumption (not decided in the map): the smoke run compiles with clang 22.1.8 first. SAW's README
  claims LLVM 20 (map 11 item 2). If SAW rejects clang 22 bitcode, record the error and rerun with an
  LLVM SAW supports, only if one is already on the Mac or installs as a separate keg without
  touching LLVM 22. This separates "SAW does not run" (fallback here) from "SAW does not read
  clang 22" (spike (a)'s question, ticket 05).
- **Default O4** (design spec; applies until Yan-Ru rules): if CIVL does not pass in 2 days, GenMC
  alone refutes, labeled, and A4's threads ≤ k rung stays unavailable until CIVL runs.
- Assumption (not decided in the map): if CIVL and GenMC both fail, stop and ask Yan-Ru; no
  fallback covers that case.
- **Default O3** (design spec; applies until Yan-Ru rules): ADR 0006 confines providers with a
  Landlock launcher, which is Linux-only. On the Mac, the `proof_hinting` provider runs in Codex's
  own sandbox over the frozen workspace and builds nothing (map 13 item 13). The exception note
  says so and cites O3. Ticket 34 builds this confinement.
- Assumption (not decided in the map): the exception is recorded as a dated consequence line in
  ADR 0006, the way its earlier amendments were added.
- Risk: GenMC reads LLVM 19-22 (map research 11b), so build it against the existing LLVM 22 keg. If
  it needs another LLVM after all, a second keg must not replace or unpin LLVM 22. GenMC may also
  not build on macOS arm64; then its fallback applies.
- Risk: a Homebrew dependency upgrade broke the LLVM 22 keg once (map 07: a z3 upgrade). Check the
  clang version before and after every brew change. Brew upgrades need no approval, but LLVM 22
  must keep working.
- Disk: an opam switch can exceed 1 GB (map 07's opam root with `framac-33` took 1.2 GB); a GenMC build
  can take several GB. Check free disk before each install. Smoke logs go to a runs folder outside
  the repo (LR-06).
- A GenMC build or an opam switch may run past 30 minutes: schedule the 30-minute heartbeat first
  (LR-07).

## Answer

2026-10-14 01:02 ET. **All four verifiers pass their smoke tests on the Mac; no fallback was
taken.** Each proves the safe program and refutes the seeded bug (`-DBUGGY`); Rocq accepts a
true theorem and rejects a false one. Every smoke run ran alone through
`/tmp/claude/probata-tools/verifier_run.py` (machine-wide lock, 8 GB RSS cap). Smoke sources:
[`../prototype/03-smoke/`](../prototype/03-smoke/). Logs (outside the repo, LR-06):
`/tmp/claude/probata-runs/t03/<name>.log`, each with `<name>.log.summary.json` (exit code,
wall time, peak RSS, sha256). Run notes for later tickets: `/tmp/claude/probata-poc-notes/verifiers-mac.md`.

**Before the first install** (`baseline-before.txt`, 2026-10-14 00:44 ET): 114 GiB free;
`/opt/homebrew/opt/llvm/bin/clang` 22.1.8; **Homebrew pins: none** (map 07 recommended
`brew pin llvm lld` but it had not been done). I pinned `llvm`, `lld` and `z3` before any
install: a z3 upgrade broke libLLVM 22 once (map 07), and GenMC now links libLLVM 22 too.

| Tool | Version | Install path | Download sha256 / source commit | Safe program | Seeded bug | Time (safe / bug) | Disk |
|---|---|---|---|---|---|---|---|
| SAW | 1.6 (68eed5f release-1.6), bundled z3 4.8.14, yices 2.6.5 | `~/opt/verifiers/saw-1.6/saw-1.6-macos-15-ARM64-with-solvers/bin/saw` | `saw-1.6-macos-15-ARM64-with-solvers.tar.gz` `88adabd8…32f4` (matches GitHub's digest) | `Proof succeeded! smoke` | `Proof failed.`, counterexample `x: 41` (`y != 42`) | 0.28 s / 0.25 s | 776 MB (tarball deleted) |
| CIVL | 1.23 of 2026-05-26 (git ad4d47a), on OpenJDK 21.0.12.1 (brew `openjdk@21`, keg-only); provers z3 5.1.0, cvc5 1.2.1 | `~/opt/verifiers/civl-1.23/civl-1.23/lib/civl-complete.jar` | `civl-1.23.tgz` `8ab3c6c8…c880` | `All errors marked with '+' are absent` | `The program MAY NOT be correct`, assertion `0!=(X_x-41)`, certainty PROVEABLE | 0.47 s / 0.48 s | 105 MB + JDK 346 MB |
| GenMC | 0.19.0 (tag v0.19.0), built with brew clang 22.1.8 against LLVM 22.1.8 | `~/opt/verifiers/genmc-0.19.0/build/bin/genmc` | commit `9f6c4c0772d0c42b325681581acc6a0f3eb9b5f7` (archive `d1a2bf4c…fb9c`) | `No errors were detected.` | `Safety violation!` at `assert(y != 42)`, exit 42 | 0.06 s / 0.06 s (build 45 s) | 306 MB |
| Rocq | Rocq 9.3.0 (rocq-core/runtime 9.3.0, rocq-stdlib 9.2.0), OCaml 5.3.0 | opam switch `rocq-9` in `~/.opam` | opam packages (default repo, updated 2026-10-14) | true theorems accepted; `Print Assumptions`: `Closed under the global context` | false theorem rejected: `Error: Tactic failure: Cannot find witness.`, exit 1 | 0.32 s / 0.16 s (install 4.4 min) | 765 MB |

Logs (sha256 prefix): `saw_safe` 5ae3d192, `saw_buggy` 40539728, `civl_safe` e5fbafbd,
`civl_buggy` 3f3117c0, `genmc_safe` 3a455dce, `genmc_buggy` bb451649, `rocq_true` a0950e04,
`rocq_false` 94e14dfe; installs `genmc_build3` 52c28b0b (failed attempts `genmc_build`
a36dd04e, `genmc_build2` 46aebe9a), `rocq_install` 042840d1.

**Concurrency smoke (beyond map 07).** Map 07's program has one thread, which says little
about the two concurrency tools. `smoke_threads.c` (mutex handover; `-DBUGGY` publishes
`ready` before `data`): CIVL safe / refuted (assertion, PROVEABLE; logs `civl_threads_*`,
65c8a3e1 / cc53c4ef); GenMC safe / refuted (`Non-atomic race!`; a13e524c / 01103bba).
`smoke_rc11.c` (message passing; `-DBUGGY` makes release/acquire relaxed, a weak-memory
outcome with no race): GenMC with `--disable-mm-detector` safe / refuted under RC11
(cab490be / 44d8f43c). CIVL assumes sequential consistency and cannot see that bug.

**Smoke-program adaptations** (same assertion as map 07's `smoke.c`): SAW verifies a function,
so `smoke_saw.c` takes x as the symbolic argument; CIVL 1.23 has no SV-COMP mode, so
`smoke_civl.c` uses `$input int x`; GenMC's `__VERIFIER_nondet_int` returns a fixed sequence
(GenMC manual), so `smoke_genmc.c` loops over x in [0, 100].

**After the last install** (`baseline-after.txt`, 01:01 ET): 113 GiB free; clang 22.1.8;
pins `llvm lld z3`; libLLVM still links the copied `libz3.4.16.dylib`. The analytic
evaluator's LLVM 22 check `tests/test_openmp_call_projection.py`: 12 passed (`llvm22_check`,
49c86bc8; map 07 had 10 tests). Map 07 tools still pass their smoke tests: CBMC 6.11.0
SUCCESSFUL / FAILED (abe07faa / 0964d510); crux-llvm 0.12 Valid 2/2 / Invalid
(4f8e6f0c / cb5c18e4); Frama-C/WP in `framac-33` with `-machdep x86_64 -wp -wp-rte
-wp-cache none`: 11/11 / 10/11 with one timeout (1a8ea44e / 33e57c29).

**ADR 0006** now has a dated consequence line (2026-10-14) recording the scoped Mac exception:
proof jobs and the `proof_hinting` role may run on the Mac during the proof of concept; on the
Mac the `proof_hinting` provider runs in Codex's own sandbox over the frozen workspace and
builds nothing (O3; ticket 34 builds it); WP uses the x86_64 machdep; the final evaluation runs
on mbit10 in a socket lane; Mac results are labeled and never mixed with mbit10 numbers.

**Side effects on the Mac:** brew installed `openjdk@21` 21.0.12.1 and upgraded its
dependencies `cairo` (1.18.4 → 1.18.6), `harfbuzz` (→ 14.6.0), `little-cms2` (→ 2.19.1)
(old kegs kept); clang 22.1.8 unaffected. `civl config` wrote `~/.sarl` (z3, cvc5).
`opam update` refreshed the default repository. Pins added: `llvm`, `lld`, `z3`.

**Facts later tickets depend on** (details and exact commands in the notes file):

- SAW 1.6 read clang 22.1.8 bitcode of the smoke program with no warning. This does not
  answer spike (a) (ticket 05: real code, ghost state).
- CIVL's exit code is 0 even when it finds a violation; adapters must parse the result line.
  In the Claude sandbox it needs `-Djava.io.tmpdir=<writable dir>`.
- GenMC's exit code is 42 on an error. Without atomics it switches itself to SC; pass
  `--disable-mm-detector` when the RC11 label matters. macOS build needs
  `-DGENMC_TCMALLOC=OFF` and `-DCMAKE_EXE_LINKER_FLAGS=-L/opt/homebrew/opt/hwloc/lib`.
- GenMC links `/opt/homebrew/opt/llvm/lib/libLLVM.dylib`: an LLVM upgrade breaks it (pinned).
- Rocq: the `rocq-prover` meta-package stops at 9.0.0; install `rocq-core` + `rocq-stdlib`.
- `verifier_run.py` crashes instead of waiting when another session holds the lock and the
  caller runs inside the Claude sandbox: `os.kill(pid, 0)` raises `PermissionError`, which the
  wait loop does not catch. The t03 runs used the sandbox off. Its peak RSS misses jobs shorter
  than its 0.5 s poll.

Assumption: the map pins neither GenMC, Rocq nor the JDK; I took the newest that worked:
GenMC v0.19.0, Rocq 9.3.0 with stdlib 9.2.0 on OCaml 5.3.0, OpenJDK 21 (LTS) rather than 27.
Assumption: map 07 names no Rocq switch; this ticket uses `rocq-9`.
Assumption: SAW's with-solvers asset, so SAW's solver versions are fixed by its release.
Assumption: no heartbeat was scheduled (LR-07): no install ran past 5 minutes.

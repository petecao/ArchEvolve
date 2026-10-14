# 03 — New verifiers on the Mac

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
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

- [ ] Before the first install: free disk (at least 50 GB), the clang version (22.1.8) and
      Homebrew's pins on `llvm` and `lld` are recorded.
- [ ] SAW 1.6 (macOS arm64 release asset, sha256 recorded) proves map 07's safe smoke program and
      refutes its seeded bug with a counterexample.
- [ ] CIVL 1.23 runs on an installed JDK (17 or later), proves the safe program and refutes the
      seeded bug.
- [ ] GenMC, built from source at a pinned release or commit, proves the safe program and refutes
      the seeded bug.
- [ ] Rocq, in its own opam switch (never `framac-33`, name decided in map 07), checks a tiny true
      theorem and rejects a false one.
- [ ] **Time box.** A tool that does not pass after 2 days goes to its fallback, with the cause
      recorded: SAW to crux-llvm (installed by map 07); CIVL to GenMC alone, which refutes, labeled,
      and the threads ≤ k rung stays unavailable until CIVL runs (O4); GenMC to CIVL alone,
      labeled; Rocq to the written proof.
- [ ] The answer has one row per tool, as in map 07: version, install path, download sha256 or source
      commit, safe and buggy verdicts, time, disk used, and logs by path and sha256. Each smoke run
      ran alone under the ~8 GB RSS watchdog.
- [ ] ADR 0006 records the scoped exception (map 13 item 13): during the proof of concept, proof jobs
      and the `proof_hinting` role may run on the Mac; on the Mac the `proof_hinting` provider runs
      in Codex's own sandbox over the frozen workspace and builds nothing (O3); WP uses the x86_64
      machdep; the final evaluation and its experiments run on mbit10 inside a socket lane; Mac
      results are labeled and never mixed with mbit10 numbers.
- [ ] After the last install: at least 50 GB free; clang still reports 22.1.8; the
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

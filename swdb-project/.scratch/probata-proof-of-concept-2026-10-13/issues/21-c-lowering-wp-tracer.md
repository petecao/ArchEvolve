# 21 — C lowering and WP adapter (A2 tracer)

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04, 10, 11, 20
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules": proof command, verifier adapters, C lowering tool; "Verifier lineup and order": unbounded verifier, solver portfolio, pinned versions, failure classes; "Proof-hint loop": anchors, frozen flags, verdict reading; "Records and levels": where evidence lives; "Testing Decisions", seam 1; choices S1 and S3); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 1, 3, 8, 9, 10; [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) items 4, 6, 7; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 3, 6; also [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 5 (where evidence lives)
**Time estimate:** about 3 days

**What to build:** The thinnest end-to-end path through A2. Yan-Ru runs `swdb prove` on a small C++ fixture proof unit in the core subset (functions, arrays, loops). Its fixture contract states an ACSL unit postcondition in 20's frame. Our C lowering tool, deterministic code and never an LLM, makes the unit's C lowering. It keeps the C++ names, so the ACSL type-checks unchanged, and it emits stable anchors for later proof hints. The real WP adapter runs Frama-C/WP 33.0 on the C lowering with the solver portfolio (Alt-Ergo, Z3, CVC5) and the frozen flags, reads the verdict per property from its own fresh run with a minimal verdict reader, and writes one proof record. Every failure class WP can emit here maps to 11's vocabulary and has a handler. `swdb prove` also gets the Mac lock (one real verifier job at a time), which every later adapter inherits. The safe fixture and map 07's safe smoke program come back proven. Their bounds say threads = 1, so they give at most proven within bounds (11 item 10); 10's level rule computes the level on read, and no level is written. The seeded bug and map 07's seeded bug come back not proven with a failure class, never refuted.

## Acceptance

- [ ] Determinism: lowering the same fixture twice gives byte-identical C and the same anchor list (same hashes). No provider is called.
- [ ] Names kept: `swdb validate` type-checks the fixture contract's ACSL, written over the C++ names, against the C lowering of the baseline proof unit's signature (16 item 3), with no renaming layer. This replaces 20's hand-written declaration. Control: an ACSL name with no C++ counterpart is refused.
- [ ] Anchors sit at the function entry, each loop head, before and after each statement, and in one ghost-globals slot. Each anchor ID is unique, and the anchor list is written beside the C lowering.
- [ ] `swdb prove` on the safe fixture with the real WP adapter writes one proof record with verdict proven. Its bounds read threads = 1 and every other dimension unbounded. `swdb validate` and `swdb build` accept the record, and 10's level rule reads it as at most proven within bounds.
- [ ] Minimal verdict reader: the verdict is proven only when every property in WP's per-property report of this run is Valid; the consolidated `[ Valid ]` line is never used. The record lists, per goal, the solver that proved it (any one of Alt-Ergo, Z3, CVC5 counts) and its time. 36 owns the full reading rule and its controls.
- [ ] Smoke pair: `swdb prove` on map [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)'s smoke pair (the safe smoke program and its seeded bug, `-DBUGGY`). WP proves the safe program and leaves the seeded bug not proven, never refuted.
- [ ] The adapter always runs with the frozen settings, and the record names them: `-wp-cache none`, a fresh session, default Frama-C warning levels, x86_64 machdep, no WP environment variables, `-wp-model +real`, WP 30 s per solver (the starting value). Frama-C, solver and C lowering tool versions and the C lowering's hash are pinned in the content-hash set.
- [ ] Seeded bug (the fixture with one off-by-one): the record reads not proven, with a failure class from 11's vocabulary file (timeout or unknown expected) and the unproven properties. It has no counterexample and no refuted verdict.
- [ ] Failure classes: every class WP can emit here (parse error, timeout, unknown, out of memory, solver error, tool crash) maps to its entry in 11's vocabulary file and runs that entry's handler (map 11 item 9). Each class is shown on a fixture or a scripted fault. An outcome with no class stops the batch.
- [ ] Regression corpus: each diagnosed failure (cause named) adds a corpus case: the input, its class and its cause. The corpus reruns in the test suite, and each case gives its recorded class again.
- [ ] The assumption set lists, as trusted-tool entries with one plain sentence each: the C lowering tool (11 item 3), clang 22.1.8 (design, "Out of Scope"), Frama-C/WP 33.0, and each solver (Alt-Ergo, Z3, CVC5; design S14).
- [ ] Mac lock: `swdb prove` takes a machine-wide lock before any real verifier job, so a second real job waits until the first ends. Test: two `swdb prove` calls with real WP, started together, never overlap (checked from outside by their start and end times). Every later adapter (22, 23, 46, 47) inherits the lock; none rebuilds it.
- [ ] Mac hygiene: the job runs under the ~8 GB RSS watchdog, and a job the watchdog kills reads not proven, out of memory. WP logs and the per-goal report land in the Mac runs folder outside the repo (host `mac`), named by path and sha256. No WP or Why3 scratch is left after the job.
- [ ] Tests that need Frama-C skip cleanly when it is missing. Fixture records carry `contract_fixture` evidence.

## Notes

- **Not in this ticket:**
  - 04 — Proof record tracer: the `proof` record kind, its tables and the scripted path through `swdb prove`.
  - 10 — Level rule: the level computed on read, which this ticket's record feeds.
  - 22 — SAW adapter and SAWScript translator; 23 — C-stub translator, fallbacks and check mode: the bounded verifier, refutations, and the C++-versus-C-lowering agreement check.
  - 24 — C++ subset widening: every construct beyond functions, arrays and loops, and the "unsupported construct" class for what stays outside.
  - 26 — Logic and sum libraries: the real logic library.
  - 35 — Hint records, merger and proof hint check: the hint merger that uses these anchors.
  - 36 — Proof setup check and verdict reading: the proof setup check, the full verdict-reading rule, and their negative controls (consolidated `[ Valid ]`, a doctored cache, `Extern` read as design S7 says, the seven WP fact files of map ticket 13, smoke goals).
  - 37 — The proof-hint loop: hint rounds (for goals with class timeout or unknown), smoke tests and minimization.
  - 11 — Method-version file and failure classes: the failure-class vocabulary file this adapter maps to.
  - 45 — Per-thread lowering: the program for one symbolic thread of N.
  - 57 — Proof workers in a socket lane: WP jobs on mbit10.
- Assumption (not decided in the map): which of map 11 item 9's handlers serves which class. Parse error: fix the C lowering or the adapter, with a minimal reproduction. Timeout and unknown: the unproven goals are listed for the hint loop (37). Out of memory: rerun with more memory where the host allows; on the Mac the ~8 GB cap stays and the record keeps the class. Solver error and tool crash: fix the adapter, with a minimal reproduction.
- Assumption (not decided in the map): the lock is machine-wide (across processes, test runs included), and a waiting job queues rather than fails. The scripted adapter takes no lock.
- Assumption (not decided in the map): the regression corpus is a set of fixture inputs with their class and cause, rerun by the test suite; one corpus serves every adapter.
- Assumption (not decided in the map): how the C lowering tool reads C++ (for example clang 22.1.8's syntax tree) is an implementation choice. Whatever it uses is pinned in the content-hash set and listed as a trusted tool. If it uses LLVM 22, the analytic evaluator must keep working.
- Frama-C/WP and its solvers are both pinned in the content-hash set and listed as trusted-tool entries (design S14: verifiers and solvers are trusted-tool entries in every assumption set).
- Assumption (not decided in the map): "stable anchors" means anchor IDs are a deterministic function of the code's structure. Stability across unrelated edits is not promised.
- Assumption (not decided in the map): this ticket's proven verdict runs no WP smoke tests (the vacuity check, not map 07's smoke pair); 36 and 37 add them. Its records are fixture evidence only.
- Risk: WP runs fail inside the Bash sandbox (the Why3 socket is blocked; map ticket 11's fact sweep). Run WP jobs outside it.
- WP's "not proven" never refutes. Only the bounded verifier refutes (22).
- Mac: keep at least 50 GB of disk free; the lock built here keeps real verifier jobs to one at a time.

## Later changes
- 2026-10-14 13:19 ET (Yan-Ru accepted ticket 09's A2 changes): the bounded verifier is now CBMC 6.11 on this ticket's C lowering, so this lowering comes before the bounded adapter (22). Each bounded job also runs a C-vs-C++ differential check on the bounded domain (pattern: `prototype/06c-cbmc/faith/`).

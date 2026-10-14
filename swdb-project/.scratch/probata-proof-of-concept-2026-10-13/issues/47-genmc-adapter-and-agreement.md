# 47 — GenMC adapter and agreement

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 46
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order" (threads > 1: they must agree), "Concurrency", "Records and levels", "Proof-of-concept plan" (A0 fallback: GenMC to CIVL alone), "Testing Decisions" (seam 1), S1, S3, O4, O6); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 5, 6), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) (item 5, A0 fallback)
**Time estimate:** about 4 days

**What to build:** GenMC, under RC11, becomes the second refuter for threads > 1. The C lowering emits
a pthreads harness of the per-thread program, and `swdb prove` runs GenMC on it through the verifier
adapter interface. Then one agreement rule holds on every run: CIVL, GenMC and the one-thread verdicts
never contradict. A contradiction stops the batch and voids the method version. Each GenMC verdict
records its version, model, thread count and loop bounds.

## Acceptance

- [ ] 07's safe smoke program proves and its seeded bug refutes through `swdb prove` with the GenMC
      adapter.
- [ ] The lowering emits a pthreads harness for ticket 45's OpenMP fixtures. GenMC finds no violation
      on the race-free fixture and refutes the plain-store fixture, with its trace inline in the
      record.
- [ ] A clean GenMC run sets no level: CIVL alone gives threads ≤ k, and GenMC is the second refuter
      (15 item 9; our reading). `swdb candidate-level` on a fixture with only a clean GenMC record
      stays below the threads ≤ k sub-rung.
- [ ] Each verdict records the GenMC version, model (RC11), thread count and loop bounds. `swdb validate`
      and `swdb build` accept it.
- [ ] Every GenMC refutation carries one of ticket 60's replay labels. A race refutation reads
      "undefined behavior (no strict-layer replay)" (O6): the refutation counts and the batch goes on.
      "Bug" still needs 60's whole-kernel reproduction.
- [ ] Agreement, tested with the scripted adapter: CIVL proves and GenMC refutes on the same bounds, so
      the batch stops and the method version is marked void. Same for a one-thread proof against a
      multi-thread refutation whose trace uses one thread. Agreeing verdicts, timeouts and "not proven"
      pass.
- [ ] With the real tools, agreement holds on every fixture CIVL ran in ticket 46.
- [ ] Loop bounds are computed from the input size bounds, with GenMC's bound-exceeded check on, so a
      too-small bound never passes silently. Negative control: a run with a loop bound set one below
      the computed value gives "not proven", class "unwinding bound too small", never a clean pass.
- [ ] **Failure classes.** Every GenMC failure maps to a class on ticket 11's list; an unlisted one
      stops the batch. Each class GenMC can report gets its handler here (11 item 9: extend the
      lowering or the subset; fix the adapter; watchdog and rerun with more memory; minimal
      reproduction) and at least one corpus case: a small input that makes GenMC report that class,
      kept in the adapters' regression corpus. Corpus cases run in the normal test workflow and check
      the recorded class (LR-04). Each diagnosed GenMC failure joins the corpus.
- [ ] Tests that need GenMC skip cleanly when it is missing. On the Mac, one job at a time under the
      ~8 GB RSS watchdog.

## Notes

- **Not in this ticket:** 46 — CIVL adapter; 48 — Concurrency negative controls (the eight BFS
  controls); 11 — Method-version file and failure classes; 14 — Bounded gate in the campaign;
  60 — Strict-layer replay and whole-kernel reproduction (the replay labels).
- Replay: a GenMC race refutation is labeled like CIVL's (O6). This ticket needs 60's labels and
  inherits 60 through 46 (46 is blocked by 60), so its Blocked by line names only 46.
- Assumption (not decided in the map): which listed classes GenMC can report is found while building
  the adapter and listed in this ticket's Answer. Expected at least: parse error, unsupported
  construct, unwinding bound too small, timeout, out of memory, tool crash, below minimum bounds.
- Assumption (not decided in the map): what "contradict" means. Two verdicts contradict when their
  bounds overlap (thread count and inputs) and one proves while the other refutes. A timeout or "not
  proven" contradicts nothing.
- Assumption (not decided in the map): GenMC runs at the same thread count (k = 3) and input bounds as
  CIVL, so the two verdicts are comparable.
- How a void method version reads: 15 item 9 says a contradiction voids it, but not how. Ticket 10
  carries the assumption: a method part recorded as failed for a version voids that version, and
  every record pinning it stops counting. This ticket records a contradiction that way (a failed
  method part citing both verdicts' IDs) and stops the batch.
- Assumption (not decided in the map): loop bounds follow 19 item 5's rule for unwind limits (computed
  from the sizes, checks always on). 19 item 5 names CBMC and crux-llvm, not GenMC.
- Fallback: if ticket 03 took GenMC's A0 fallback (GenMC to CIVL alone, labeled), this ticket records
  "CIVL alone" and the agreement rule covers CIVL and the one-thread verdicts only. The reverse (O4):
  if CIVL will not run, GenMC alone refutes, labeled, and the threads ≤ k rung stays unavailable until
  CIVL runs.
- Risk: the pthreads harness is emitted by the lowering, a trusted-tool entry. Agreement with CIVL is
  the main check on it.

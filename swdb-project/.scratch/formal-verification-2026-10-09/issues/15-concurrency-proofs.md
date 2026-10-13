# 15 — How do proofs cover concurrency for any thread count?

Created: 2026-10-13
Updated: 2026-10-13 16:09 ET (resolved with Yan-Ru in four grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 15:27 ET)
**Blocked by:** 11, 12
**Map:** `../map.md`

## Question

How do a contract proof and each candidate artifact's proof cover concurrency for any thread
count? Decide:

- what is proven once per rewrite contract (the order-independence lemma: every serial order of
  atomic blocks meets the unit relation; soundness of the reduction to a thread-indexed
  sequential program) and what per candidate artifact (tile and buffer ownership, race freedom,
  barrier alignment, exact chunk cover);
- how the C lowering emits the thread-indexed sequential program for a symbolic thread count N,
  and how relaxed atomic reads and the CAS are modeled in it;
- what the hand-written VerCors PVL model covers and how it is kept faithful to the code;
- how CIVL's bounds (team sizes 1..k) and GenMC's memory model are recorded in a verdict.

The method must be general: GAPBS `bc.cc:106-107` and `sssp.cc:157-160` use the same
"plain read, then CAS" pattern as BFS.

## Comments

- 2026-10-13: input from 11 (graduated from the map's "Concurrency phase" fog). Settled there:
  - **Claim** for every thread count N: race freedom outside atomics and critical sections;
    atomic critical sections, so a run equals some serial order of atomic blocks; every serial
    order meets the unit relation; per-thread tile ownership with no DX100 hazard; exact chunk
    cover.
  - **Thread count** = every N, built with `NUM_CORES` = N and run with N threads
    (`apps/dx100/benchmarks/gapbs/src/bfs.cc:62-63,142,195`); a contract precondition with a
    run-time guard.
  - **Methods:** (A) reduction proven in WP for symbolic N, the only one that sets the level;
    (C) CIVL 1.23 as refuter, GenMC second; (B) VerCors on a hand PVL model, BFS read offload
    only, sets no level, dropped first.
  - **Negative controls:** wait moved outside `critical`; `critical` dropped; one shared tile;
    overlapping chunks; barrier dropped.
  - **Baseline** = its single-thread run. Undefined behavior is a proof obligation; a racy
    candidate is refuted (provisional). The authors' `TDStepMAA` is refuted at threads > 1 (its
    fallback path races, `bfs.cc:205-210`).
  - Facts: [`../research/11-concurrency-verification.md`](../research/11-concurrency-verification.md).
- 2026-10-13: blocked by 12 because the proof needs the DX100 store inside `critical` to be
  complete and visible to other cores before the lock is released; ticket 12 decides that
  semantics.
- 2026-10-13 14:19 ET: input from 12 (now resolved, so this ticket is unblocked):
  - **Overlap rule** (12, item 4): a CPU access by another thread that overlaps an unfinished DX100
    command's footprint is allowed when DX100 only reads; the read returns some value the location
    held while the command ran, never older than the stores made before the command was issued.
    The contract must tolerate it (BFS read offload: the CAS recheck, L4); prove it here. When
    DX100 writes, the overlap is a hazard. Same-thread overlaps with a write are hazards.
  - **Tile ownership** is a proof obligation: the device does not enforce it (research 12).
  - **Store inside `critical`:** finishing before the lock is released is proven by the wait rule;
    the next thread's DX100 load seeing it is a cited rule plus two gem5-corner assumption entries;
    the CPU reads after `omp barrier` rest on the entry "no stale CPU copy survives a DX100 store"
    (owner Eric). One DX100 instance is an assumption entry. Details: 12, item 7.
  - **Peter's read offload races too:** it keeps the plain store `parent[v]=u` after a successful
    CAS (`library/dx100/bfs_read_offload.inc:53,63`) beside other threads' CAS and relaxed loads
    of the same `parent[v]`, the race class 11 found in the authors' fallback path
    (`apps/dx100/benchmarks/gapbs/src/bfs.cc:205-210`). Decide here what 01 decision 9.2
    ("should be proven") means at threads > 1.
- 2026-10-13 15:22 ET: input from 13: the reduction program for symbolic N runs through the proof-hint
  loop with the same vocabulary and checks; CIVL counterexamples go to counterexample-guided
  repair (the rewriting role), never to the proof-hint agent.
- 2026-10-13 15:32 ET: claimed (agent session with Yan-Ru). Grilling round 1 posted (Q1 proof shape for
  every N, Q2 memory model for shared reads, Q3 what proofs trust about OpenMP, Q4 what 01 decision
  9.2 means at N > 1, Q5 CIVL's role and verdict records). Held for round 2: the VerCors model's
  faithfulness, other threads' DX100 commands, barrier alignment, extra negative controls.
- 2026-10-13 15:44 ET: round 1 answers (checkpoint; not yet the answer).
  - **Q1, Q2:** Yan-Ru: "choose the most formal correctness guarantee approach". Chosen: Q1 (b),
    thread-modular (one symbolic thread t of N; other threads seen only through the contract's
    shared actions; composition theorem once for the method); its mechanization is asked in round 2.
    Q2 (a), history read, argued against RC11 (C++'s repaired memory model): per location, a read
    returns a value already written, never older than the newest write the thread has seen. SC
    everywhere is rejected as false under C++ rules.
  - **Q3, Q4, Q5 accepted:** OpenMP runtime as one "trusted tool" entry, thread-id splits and
    uniform control proven; Peter's read offload refuted at N > 1 as written, next version from
    counterexample-guided repair; CIVL fills the bounded-verifier role for threads <= k (k starts at
    3), reopening one line of 11 (item 10, "the only method that sets the level") for the
    within-bounds rung.
  - **New input (Yan-Ru):** Peter's and Josh's code is preliminary and tentative. The DX100 authors
    reshaped the baseline to fit the DX100 API before offloading; Probata may likewise rewrite the
    baseline into an equivalent, DX100-compatible form first. ArchEvolve must handle any input
    code. Term and ticket asked in round 2 (proposed: enabling rewrite).
- 2026-10-13 15:55 ET: round 2 answers (checkpoint; not yet the answer). Accepted: Q7 (other threads'
  DX100 commands are shared actions; writes only inside `critical` or to own memory; tile
  ownership proven per candidate), Q8 (pairwise proof that any two threads agree on every condition
  guarding a barrier or worksharing construct, in WP), Q10 (term **enabling rewrite**; new ticket
  17). Q6: Yan-Ru unsure; standing rule: formal by default, but trade off, about one month of work
  per piece (not absolute), and do the chosen option well; 1-3 months to mechanize the composition
  theorem is too much. Re-asked in round 3. Q9: Yan-Ru asked "are you sure?"; re-check against the
  code and `library/rewrite_contracts/bfs_read_offload.yaml` found two of four proposed controls wrong:
  - "CAS recheck removed" fails at one thread (two edges to one vertex in a chunk both get a stale
    negative hint) and already exists as the contract's `skipped_cas_recheck`
    (`bfs_read_offload.yaml:98-100,231-233`); it tests neither threads nor the history read.
  - "team-size guard removed" changes no verdict: team size = `NUM_CORES` is a precondition the
    proof assumes.
  - Kept: plain store to an atomically updated location; thread-dependent worksharing (`accelerate`,
    `library/dx100/bfs_read_offload.inc:22`). Both need a PoC check that CIVL or GenMC reports them.
  - **Finding:** clause L4 *requires* "the labeled redundant parent store"
    (`bfs_read_offload.yaml:116-119`), so Q4's repair needs a new contract version, not only a new
    candidate artifact.
- 2026-10-13 15:56 ET: round 3 posted (Q6 re-asked as a trade-off, Q9 revised controls, Q11 VerCors out
  of scope, Q12 shared-action kinds, Q13 revisit 11's Q24). New finding: all three proof-of-concept
  candidates race at N > 1 as written: the authors' (plain read and store, `bfs.cc:205-210`), Peter's
  (plain store, `bfs_read_offload.inc:53,63`) and Codex's frontier staging (plain read,
  `library/native/bfs-tdstep-frontier-staging.patch:54`). Codex's contract already removes the
  redundant store (clause C2, `bfs_tdstep_frontier_staging.yaml:150-166`), a precedent for the
  read-offload fix.
- 2026-10-13 16:03 ET: round 3 answers. Accepted: Q9 (keep the plain-store and thread-dependent
  worksharing controls, drop "CAS recheck removed" and "team-size guard removed", add the must-prove
  "re-read after a failed CAS sees the winner"), Q11 (VerCors out of scope), Q12 (fixed set of
  shared-action kinds with commutativity lemmas), Q13 (keep 11's Q24: a racy candidate is refuted;
  repair makes plain reads relaxed atomic loads and removes the redundant store). Q6: Yan-Ru asked
  how (a) differs from (c) and added a standing rule: minimize human effort and construct proofs as
  automatically as possible. Re-explained with a new option (d): an agent writes the Rocq proof,
  Rocq checks it, time-boxed, written proof as fallback.
- 2026-10-13 16:09 ET: Yan-Ru accepted Q6 (d) and confirmed the shared understanding ("agree").

## Answer

2026-10-13 16:09 ET. Decided with Yan-Ru in a grilling session (rounds 1-4 in Comments). Facts:
[research 11b](../research/11-concurrency-verification.md) (concurrency survey),
[research 12](../research/12-dx100-memory-visibility.md), and the code re-checked in this session.
Standing rules added to the map's Notes: any input code; Peter's and Josh's code is tentative;
minimize human effort, construct proofs automatically, about one month of work per piece.

1. **Proof shape: one thread at a time.** WP proves one arbitrary thread t of a symbolic thread
   count N. Other threads appear only through the contract's **shared actions** (glossary). A
   **parallel composition theorem** (glossary), made once for the method, turns the per-thread
   proofs into "every run ends as some serial order of the shared actions would". Chosen over
   simulating every interleaving (Conc2Seq style, a loop that picks any thread): the per-candidate
   work is equally automatic, the goals have no quantifiers over every thread's position, and the
   argument stays sound when reads return stale values. This refines 11 item 10 (A): the C lowering
   emits a program for one symbolic thread t, not for all N.

2. **What is proven where.**

   | Proven | By | What |
   |---|---|---|
   | Once per shared-action kind | WP | its commutativity lemma (item 5) |
   | Once per rewrite contract | WP | its shared actions and their specs; a **sharing class** (glossary) per array between barriers: read-only, thread-owned, changed only through shared actions, or lock-protected; the order-independence lemma (every serial order of its shared actions meets the unit relation), built from the kind lemmas |
   | Once per method | Rocq, or written (item 8) | the parallel composition theorem |
   | Per candidate artifact, automatic | WP | thread t's accesses fit their sharing classes (race freedom); each atomic block or `critical` section implements one shared action; owned ranges, tiles and registers are disjoint for t != t'; chunk splits computed from the thread id cover the frontier exactly once; uniform control (item 6) |

3. **Memory model: the history read, argued against RC11.** A read that other threads may race with
   on purpose (a relaxed atomic load; another thread's DX100 read, ticket 12 item 4) is a
   **history read** (glossary): it returns a value the location already held, never older than the
   newest write this thread has seen (its own reads and writes, and writes ordered before it by a
   barrier, `critical` or a CAS). A CAS (`__sync_*`, `platform_atomics.h:30-31`) is a sequentially
   consistent read-modify-write. A plain access to a location changed only through shared actions
   is a data race, so the candidate artifact is refuted (11 item 11). Assumption entry (trusted
   tool): the pinned compiler and ISA implement RC11, the repaired C++ memory model (Lahav et al.,
   PLDI 2017); the standard's own model allows out-of-thin-air values no compiler produces.
   Rejected: sequential consistency everywhere (false under the C++ rules).

4. **What proofs trust about OpenMP.** One trusted-tool entry for the pinned OpenMP runtime, citing
   OpenMP 5.2: `omp for` gives each iteration to exactly one thread under any schedule; `critical`
   excludes other threads and orders memory; a barrier waits for all threads and orders memory;
   thread ids are distinct, 0 to N-1. Proven, never trusted: chunk splits the code computes from
   the thread id (`apps/dx100/benchmarks/gapbs/src/bfs.cc:142-143`); team size = N (11's run-time
   guard); uniform control.

5. **Shared-action kinds**, a fixed set, each with a commutativity lemma proven once in WP; a new
   kind needs its own lemma:

   | Kind | Where |
   |---|---|
   | Claim (write-once CAS) | BFS `parent`; BC `depths` (`bc.cc:106-107`) |
   | Min-update (CAS loop) | SSSP `dist` (`sssp.cc:157-167`) |
   | Atomic add or OR | BC `path_counts` (`omp atomic`), BC `set_bit_atomic` (`bc.cc:110-113`) |
   | OpenMP reduction | PR `error` (`pr.cc:218`) |
   | Queue reserve (`fetch_and_add`) | every kernel's queue flush (`sliding_queue.h:114-118`) |

   Floating-point adds commute over real arithmetic; rounding stays in the assumption set (09).

6. **Uniform control.** WP proves, for any two threads t and t', that both evaluate every condition
   guarding a barrier or worksharing construct equally: a product of two copies of the control
   skeleton (GPUVerify's barrier-divergence technique, Betts et al. 2012), built with 11 item 5's
   product programs. A static uniformity analysis was rejected (one more trusted tool).

7. **Other threads' DX100 commands are shared actions.** Their reads of shared arrays meet thread t
   as history reads (12 item 4). Their writes are allowed only inside `critical` or into that
   thread's own memory; anything else is a hazard. Tiles and registers are thread-owned, with
   disjointness proven per candidate artifact (12 item 5). Device against device follows gem5's
   region stall (12 item 4); one DX100 instance stays an assumption entry (12 item 7).

8. **The parallel composition theorem is written by an agent in Rocq** (Q6, option d). Codex writes
   the proof and Rocq checks every step; Yan-Ru reviews only its statement and definitions (about
   1-2 pages). Each hypothesis is exactly one per-candidate WP obligation or one assumption entry.
   Time-boxed at about 2 weeks; if the box runs out, the fallback is a written proof (agent-written,
   Codex adversarial review, Yan-Ru approval at promotion) that keeps every Rocq-checked lemma.
   Ticket 12's DX100 reduction lemma goes in the same Rocq development. Until machine-checked, the
   theorem is an assumption entry of kind "reduction". Rejected: a hand-written Rocq proof (1-3
   months, over the cost rule); a written proof only (option a; more reading for Yan-Ru, steps
   unchecked).

9. **Bounded verifiers for N > 1** (reopens one line of 11 item 10, "the only method that sets the
   level", for the within-bounds rung). CIVL 1.23 fills the bounded-verifier role for threads > 1:
   a clean exhaustive run gives proven within bounds with threads <= k (k starts at 3, calibrated
   like 13's budgets); a violation is a refutation. Its interleaving model is sequentially
   consistent (our reading, to confirm), so the lowering encodes history reads for it. GenMC (RC11)
   is the second refuter, on a pthreads harness our lowering emits. Per candidate artifact the
   ladder is SAW (threads = 1) -> CIVL (threads <= k) -> WP (every N, proven unbounded).
   **Agreement on every run:** CIVL and GenMC never contradict a one-thread verdict; a
   contradiction stops the batch and voids the method version. Each verdict records the CIVL
   version, k, input bounds, `-ompLoopDecomp=ALL`, race checking on, the memory-model encoding and
   the solver; for GenMC, its version, model (RC11), thread count and loop bounds.

10. **Racy candidate artifacts are refuted** (11's Q24 kept, Q13). Counterexample-guided repair
    applies one general fix: a plain read of a shared-action location becomes a relaxed atomic load,
    and a redundant plain store is removed. All three proof-of-concept candidates race at N > 1 as
    written: the authors' `TDStepMAA` (plain read and store, `bfs.cc:205-210`), Peter's read offload
    (plain store, `library/dx100/bfs_read_offload.inc:53,63`) and Codex's frontier staging (plain
    read, `library/native/bfs-tdstep-frontier-staging.patch:54`). BC and SSSP as written race the
    same way. Rejected: the assumption entry "aligned plain `int` accesses act as relaxed atomics"
    (GCC's informal model, which Codex's clause C2 relies on).

11. **01 decision 9.2 at N > 1** (Q4). Peter's read offload as written proves at N = 1 and is refuted
    at N > 1, a finding. Its next version, without the redundant store, should prove at every N. It
    comes from counterexample-guided repair on CIVL's race trace (a demonstration of the loop); a
    hand deletion only if the loop fails, labeled hand-made; promotion as usual. Clause L4 requires
    the store (`library/rewrite_contracts/bfs_read_offload.yaml:115-118`), so the contract gets a new
    version too; Codex's clause C2 (`library/rewrite_contracts/bfs_tdstep_frontier_staging.yaml:150`)
    is a precedent. Peter's and Josh's code is preliminary (Yan-Ru): a proof-of-concept candidate,
    never ground truth.

12. **Concurrency negative controls:** seven must be refuted, one must prove. Ticket 11's five
    (`wait_ready(tile3)` outside `critical`; `critical` dropped; one tile shared by all threads; two
    chunks overlapping by one; the barrier before the fallback path dropped), plus: a plain store to
    a location changed only through shared actions; `accelerate`
    (`library/dx100/bfs_read_offload.inc:22`) made thread-dependent, so threads reach different
    `omp for` loops. Must prove: read, failed CAS, re-read sees the winner's value (BC's pattern;
    it keeps the history read's "never older" bound honest). In the proof of concept CIVL or GenMC
    must refute each must-refute control; a control with the wrong verdict voids the method
    version. Rejected after a re-check: "CAS recheck removed" (fails at one thread; already the
    contract's `skipped_cas_recheck`) and "team-size guard removed" (a precondition; no verdict
    changes).

13. **VerCors is out of scope** (Q11): a hand-made PVL model, BFS only, sets no level; against "any
    input" and the cost rule. It removes 11 item 10 (B) and the reduction-vs-VerCors comparison.

14. **Enabling rewrites** (Q10): Yan-Ru's "equivalent baseline" is named **enabling rewrite**
    (glossary), because the baseline implementation is the code as found, which every proof
    compares against. New ticket 17.

15. **Generality.** The per-thread proof, sharing classes, shared-action kinds, history read,
    uniform control and the composition theorem are per method or per kind, not per kernel. BC,
    SSSP and PR map onto the kinds of item 5; their repaired versions rely on the history read's
    "never older" bound.

**Inputs passed on:**
- **Ticket 16:** formal halves must state shared actions by kind, sharing classes per array per
  barrier interval, and history reads; the parallel composition theorem's statement uses the same
  vocabulary.
- **New ticket 17:** how enabling rewrites are proposed, proven and chained with offloading
  rewrites.
- **Map fog (Evaluation plan):** the three-step ladder per candidate artifact; CIVL and GenMC
  agreement; the eight concurrency controls; as-written vs repaired candidates at every N with
  performance compared (11's Q31 hypothesis now covers all three); the Rocq time-box outcome.
- **Map fog (Records):** CIVL and GenMC settings; the parallel composition theorem's version and
  status (Rocq-checked or written); the OpenMP runtime and RC11 entries.
- **Proof-of-concept build items:** new versions of the `bfs_read_offload` contract (L4) and of
  Peter's code; GenMC built from source; CIVL needs a JDK (11).

Glossary: enabling rewrite, shared action, sharing class, history read, parallel composition
theorem added.


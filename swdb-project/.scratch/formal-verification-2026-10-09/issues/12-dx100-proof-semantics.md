# 12 — What semantics do DX100 proofs trust?

Created: 2026-10-09
Updated: 2026-10-13 14:19 ET (resolved with Yan-Ru in three grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 13:36 ET)
**Blocked by:** 05, 08, 14
**Map:** `../map.md`

## Question

What semantics do DX100 proofs trust: the authors' functional model, our strict layer, or a
separate logical model? Who signs off on it (the strict layer is "assumed, owner Eric"), and how
is the gap between the authors' model and the strict layer handled?

## Comments

- 2026-10-09: input from 05: split each DX100 proof into hazards (over a "proof edition" of the
  strict layer: uncovered reads return arbitrary values, not a fixed sentinel) and function (over
  instant completion), linked by a reduction lemma proven once. Never use the functional model
  alone: it would prove `TDStepMAA`.
- 2026-10-09: 05 found two scope gaps in "the strict layer is the trusted semantics" (01, decision
  10): the strict layer does DX100 main-memory reads and writes at issue
  (`library/dx100/strict/MAA_functional.hpp:126,131,170`), so it never flags memory touched by an
  operation still in flight; and the wrong-tile refutation (01, decision 9.1) rests on an assumed
  wait rule that the authors' model may contradict. Ticket 14 checks gem5. Decide here what
  decision 9.1 becomes if gem5 says the wait covers the store.
- 2026-10-09: input from 02: no unbounded tool can trace the strict layer's growing op list and
  recursive `cover()`. Unbounded proofs will trust `maa_*` contracts, which need their own
  evidence against the strict layer.
- 2026-10-09: settled in 01 (amended): proofs use a gem5-matching wait rule (14). This ticket still
  decides the rest: the hazards/function split, evidence for `maa_*` contracts, and memory
  effects that land after the call.
- 2026-10-11: input from 08: no verifier ran on the strict layer as written; proofs ran on
  `prototype/08-wrong-tile/port/strict_port.hpp`, an array port with both wait rules. The only
  evidence that it matches today is differential: 11 fixture scenarios x 2 rules x 3 tile sizes,
  0 diffs. In 08's harness, P1 (hazard) depends only on the control-flow shape, not on data.
  That supports the hazards/function split from 05.
- 2026-10-12 22:52 ET: input from 10: each DX100 lowering is proven once against the semantics this ticket
  picks, and its proven clauses become a summary used in every candidate proof. The summary must
  carry hazard state (which tiles are ready after which wait), so hazard freedom can be proven
  without the inlined port. 10's scale hypothesis depends on such summaries. Who signs off on
  the semantics also signs off on what the summaries may claim.
- 2026-10-13 00:35 ET: input from 11: (1) the concurrency proof needs the DX100 store issued inside
  `critical` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:170-187`) to be complete **and visible to
  other cores** before the lock is released. Research 14 confirmed completion on gem5, not
  cross-core visibility. Until this ticket decides, it is an assumption-set entry (trusted
  accelerator semantics). (2) Summaries come in three generated forms (SAWScript specs, C call
  stubs, ACSL contracts) from one source, the formal halves; the DX100 summaries must carry hazard
  state in all three, and per-thread tile ownership for concurrency (ticket 15). (3) Behavior
  outside the language standard is trusted accelerator semantics; undefined behavior is a proof
  obligation (11, item 11).
- 2026-10-13 13:36 ET: claimed (agent session with Yan-Ru). Grilling round 1 asked. Background research on
  cross-core visibility of DX100 memory accesses on gem5 (coherence with CPU caches, the
  memory-region stall across cores) writes `../research/12-dx100-memory-visibility.md`.
- 2026-10-13 14:05 ET: round 1 checkpoint (not yet the answer). Research 12 back:
  [`../research/12-dx100-memory-visibility.md`](../research/12-dx100-memory-visibility.md).
  - **Q1 (c), accepted:** proofs trust a separate **proof semantics** (glossary), one contract per
    `maa_*` call over ghost hazard state; each rule cites gem5 DX100 source (`e4fc4af`) or is
    "assumed" with an owner; the strict layer is its executable counterpart; gem5 source decides
    disagreements. Yan-Ru added: the functional model is only "functional": it shows what DX100
    computes, not how the device runs; a testing and proof-of-concept aid. Glossary sharpened.
  - **Q2, Q3, Q6 accepted:** values as if each command finished at issue plus hazard assertions,
    joined by a reduction lemma (written proof plus a bounded check; assumption entry until
    machine-checked); element-level memory footprints, device-vs-device by gem5's region stall
    (research 12: it spans all cores of one instance); Yan-Ru approves the proof semantics at
    promotion, uncited rules stay assumed (owner Eric).
  - **Q4, Q5 questioned** by Yan-Ru ("are you sure?"); re-explained in round 2. Q5 check: GCC 16
    and clang 22 at `-O3` reload a tile value after a volatile asm fence without a `"memory"`
    clobber (they fold the two loads when the fence is absent), so the clobber gap is not a
    demonstrated defect.
- 2026-10-13 14:13 ET: round 2 checkpoint. **Accepted:** Q4 (an unready read is an assertion failure;
  "unready" = the tile's producer has not finished; reading a tile an unfinished command only
  reads is not flagged), Q5 (semantics stops at the `maa_*` calls; `MAA_gem5.hpp` is an
  assumption entry; the missing clobber is a portability note), Q10 (contradicting library
  entries get new versions before they yield summaries). **Open:** Q7 (Yan-Ru asked what the strict
  layer is), Q8 ("maybe"), Q9 ("are you sure?").
  - **Re-check of Q9 found a conflict with Q3 (accepted in round 1):** Peter's read offload gathers
    `parent` on DX100 while other threads CAS it (`library/dx100/bfs_read_offload.inc:41,47,53`),
    a race the contract tolerates by design (L3, L4). Q3's "any thread's CPU access overlapping a
    footprint, either side writing, is a hazard" would refute it, though 01 says it should prove.
    Proposed split in round 3.
  - **For ticket 15:** Peter's read offload keeps the plain store `parent[v]=u` after a successful
    CAS (`bfs_read_offload.inc:53,63`), beside other threads' CAS and relaxed loads of the same
    `parent[v]`: the same race class 11 found in the authors' fallback path.
- 2026-10-13 14:19 ET: round 3. Yan-Ru accepted Q3b (the overlap rule split by thread and by
  what DX100 does), Q7 (after a reminder of what the strict layer is), Q8 and Q9 (re-checked,
  with a confidence per part).

## Answer

2026-10-13 14:19 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments). Facts:
[research 14](../research/14-dx100-wait-rule.md) (wait rule) and
[research 12](../research/12-dx100-memory-visibility.md) (memory visibility, source reading only).

**Proofs trust a proof semantics:** a separate description of DX100's `maa_*` calls, written for
verifiers. Not the functional model, not the strict layer as written.

1. **Three models, three jobs.**

   | Model | What it is | Used for |
   |---|---|---|
   | Functional model (the authors') | What each command computes, finished at once. Not how the device runs it (timing, ready bits, order, memory traffic). | A testing and proof-of-concept aid; never trusted by proofs (Yan-Ru) |
   | Strict layer (ours, certify 1.7) | The functional model's results plus hazard tracking, executable | Certification (testing) |
   | **Proof semantics** (new, glossary) | One contract per `maa_*` call over ghost hazard state | Proofs |

   Each rule of the proof semantics, values included, cites the gem5 DX100 device source at
   `e4fc4af` or is marked "assumed" with an owner. When the proof semantics and the strict layer
   disagree, the gem5 source decides, and the wrong one gets a new version. The proof semantics
   is versioned and belongs to every content-hash set (ticket 10, item 6).
2. **Values and timing are split.** Values are computed as if each command finished at issue;
   hazard freedom is asserted separately. A **reduction lemma** joins them: if the code is
   hazard-free, every timing gem5 allows gives the same values. Its side conditions come from
   research 14: one core's commands dispatch in program order but run out of order, made safe by
   the tile dispatch stall (`IF.cc:193-212`) and the memory-region stall (`IF.cc:213-219`). The
   lemma gets a written proof plus a bounded check in the proof of concept (an asynchronous port
   in which each command finishes at any point before its covering wait, compared with
   finish-at-issue). Until machine-checked it is an assumption-set entry of kind "reduction".
3. **An unready read is a hazard** (an assertion failure), not a fixed or arbitrary value.
   - "Unready" means the producer of what is read has not finished. Reading a tile that an
     unfinished command only reads is not flagged; a CPU write to such a tile is a hazard.
   - It covers calls (`get_tile_size`, `get_reg`) and tile-pointer reads. Our C lowering inserts
     a check at each tile-pointer read; on the C++ path the harness generator places a probe
     before each read loop, as 08 did by hand (its P1).
   - `get_tile_ready` may return either answer while commands are pending (gem5's answer depends
     on timing); a "1" counts as a covering wait.
   - Why this costs nothing extra: ticket 09 already puts hazard freedom inside "proven", and a
     fixed or arbitrary value never proves it. Evidence: 08's P1, 19 of 19 goals in 21 s; seeded
     bugs refuted in 6-16 s. A proven-ready read also has an exact value, which helps the value
     proof.
4. **Memory timing** (the strict layer's looser corner). The proof semantics tracks each
   unfinished command's memory footprint per element (indirect: the addresses its index tile
   names; stream: its range).

   | A CPU access overlaps an unfinished DX100 command's footprint | Verdict |
   |---|---|
   | Same thread, either side writes | hazard |
   | Other thread, DX100 only reads | allowed: the read returns some value the location held while the command ran, never older than the stores made before the command was issued. The rewrite contract must tolerate it (BFS read offload: the CAS recheck, L4); ticket 15 proves it. |
   | Other thread, DX100 writes | hazard |

   The middle row exists because Peter's read offload gathers `parent` on DX100 while other
   threads CAS it (`library/dx100/bfs_read_offload.inc:41,47,53`), a race its contract tolerates
   by design. Device against device follows gem5's region stall: issuing a command covers earlier
   unfinished commands on the same registered region when either one writes (research 12: across
   all cores of one instance). The strict layer gets these rules later as a new certify version;
   until then a candidate artifact can certify and still be refuted by proof.
5. **Tile ownership is a hazard the proof checks.** The device does not enforce it: tile numbers
   are one global pool that software splits, and core A's wait counts core B's commands on the
   same tile (research 12).
6. **The semantics stops at the `maa_*` calls.** The MMIO code that implements them
   (`apps/dx100/benchmarks/API/MAA_gem5.hpp`) is an assumption-set entry: "implements the call
   semantics, including ordering", with research 14 as evidence. Portability note on that entry:
   `wait_ready`'s fence has no `"memory"` clobber (`MAA_gem5.hpp:98-101`). GCC 16 and clang 22 at
   `-O3` still treat the volatile asm as a memory barrier (tested 2026-10-13 on arm64 with an arm64
   fence); the GCC manual does not promise it. Never counted against a candidate artifact.
7. **Cross-core visibility** (11's input):

   | Part | Treatment |
   |---|---|
   | Program accesses | proven (item 4) |
   | The store inside `critical` finishes before the lock is released | proven: the wait on tile3 covers the store (research 14) |
   | L5: DX100 reads see CPU stores made before the command was issued | a proof-semantics rule citing research 12 (DX100 reads snoop CPU caches). L3 follows, since `parent` is initialized before `TDStep`. Both leave "assumed" in new library versions (item 10). |
   | The next thread's DX100 load sees the store | a rule citing research 12, plus two gem5 corners it could not rule out (a write reaching L3 after the snoop filter dropped the line; a write passed below L3 when no block can be allocated), each an assumption entry |
   | No stale CPU copy survives a DX100 store (a load or hardware prefetch during the store keeps one) | assumption entry, owner Eric; gem5 does not guarantee it (research 12). Matters only where DX100 writes memory the CPU later reads: `TDStepMAA`'s `parent` store and PR's RMW (`apps/dx100/benchmarks/gapbs/src/pr.cc:242-245`). |
   | One DX100 instance | assumption entry: the region stall spans one instance; the paper's scalability runs use two |

8. **Agreement of the strict layer and the proof semantics**, per proof-semantics version:
   - every rule both model is a fixture scenario run on both (the
     `tests/fixtures/strict_wait_rule.cc` pattern), 0 differences required;
   - rules only the proof semantics has (footprints, the timing-dependent `get_tile_ready`, the
     other-thread read rule) are listed as "stricter than the strict layer";
   - the three generated summary forms (SAWScript specs, C call stubs, ACSL contracts) give the
     same verdict on every fixture scenario.

   The evidence is recorded with the proof-semantics entry of each assumption set.
9. **Negative controls for the semantics itself**, run per proof-semantics version; a control
   with the wrong verdict voids the version. Contract negative controls (ticket 10) only exercise
   the rules a contract happens to use; these exercise every rule.
   - Must be refuted: `TDStepMAA` with its wait deleted (it proves under finish-at-issue); the
     authors' wait under the old wait rule; a CPU read of `parent` by the same thread while its
     DX100 store is unfinished; another thread's CPU read of a line a DX100 store has in flight.
   - Must prove: the authors' wait under the gem5 rule; Peter's other-thread read pattern (DX100
     gathers `parent` while another thread CASes it) raises no hazard.
10. **Summaries claim only what the proof semantics allows.** Library entries whose text
    contradicts it get new versions first; old versions are kept, as with certify 1.7:
    - `completion.assumptions` of the 10 intrinsic YAMLs (`library/intrinsics/dxc_*.yaml`, list in
      the [evidence note](../evidence/strict-gem5-wait-rule-redeclaration-20261009.md));
    - the `dxc_const_i32` result clauses that name the `constant_uncovered` control;
    - L3 and L5 of `bfs_read_offload` and their `bc_read_offload` counterparts, from "assumed" to
      proof-semantics rules.

    Until then those entries yield no summaries. This is a build ticket of the proof-of-concept
    effort.
11. **Sign-off.** Rules that cite gem5 source need no outside sign-off: the citation is the
    evidence. Yan-Ru approves the proof semantics at promotion, as with contract proofs (ticket
    10). Uncited rules stay "assumed, owner Eric" in the assumption set. No message to Eric now.
12. **Generality.** The rules are per `maa_*` call, not per kernel, so they serve BFS, BC, PR and
    SSSP alike. PR's wait on its RMW's source tile (`pr.cc:242-245`) is safe under the gem5 rule;
    its CPU read afterward rests on the stale-copy entry (item 7).

The question in Comments about 01 decision 9.1 was settled by 01's amendment (2026-10-09).

**Inputs passed on:**
- **Ticket 15:** the other-thread read rule and the hazard rows of item 4; tile ownership as a
  proof obligation; the visibility split of item 7; the one-instance entry. Also: Peter's read
  offload keeps the plain store `parent[v]=u` after a successful CAS (`bfs_read_offload.inc:53,63`)
  beside other threads' CAS and relaxed loads of the same `parent[v]`, the race class 11 found in
  the authors' fallback path. Decide there what 01 decision 9.2 ("should be proven") means at
  threads > 1.
- **Ticket 13:** a hazard counterexample replays on the strict layer before it counts as a bug,
  but the proof-only rules (item 8) cannot replay there until the strict layer catches up.
- **New ticket 16** (graduated from the map's "Formal-half language" fog): the proof semantics'
  rules, ghost hazard state and footprints share the formal-half source language.
- **Map fog:** each verdict records the proof-semantics version and its agreement evidence
  (Records); the semantics negative controls and the strict-layer catch-up (Evaluation plan).

Glossary: proof semantics added; functional model sharpened; the assumption-set kind "trusted
accelerator semantics" now reads "the accelerator's proof semantics".

## Later changes

- 2026-10-13 16:50 ET, from [16](16-formal-half-language.md) (items 9-11): new rule: an 8-byte operand
  occupies tiles t and t+1, and ownership and hazards cover both, because gem5's dispatch stall
  compares only t (`SPD.cc:124-133` at `e4fc4af`); no proof-of-concept kernel uses 8-byte tile
  data. The proof semantics is written in ACSL with fixed-size ghost arrays (per tile, per
  register, 32 command slots per thread as an encoding bound). Reference semantics for proofs
  become ACSL definitions in the logic library, proven against the lowered
  `library/dx100/reference.hpp`; per-call intrinsic summaries replace the whole-loop
  `range_loop` reference (`reference.hpp:9`).

# 17 — How do enabling rewrites chain with offloading rewrites?

Created: 2026-10-13 16:09 ET
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session archevolve-42, claimed 2026-10-13 16:21 ET; ticket 16
is held by session archevolve-ea)
**Blocked by:** 15
**Map:** `../map.md`

## Question

How does Extensa Probata propose and prove **enabling rewrites** (glossary: rewrites that offload
nothing and only reshape code so that an offloading rewrite contract can match, as the DX100
authors did by hand), and how are they chained with the offloading rewrites built on top? Decide:

- who proposes an enabling rewrite (the rewriting role in Extensa mode, the site finder, a fixed
  catalog) and how it names the offloading contract it enables;
- what an enabling rewrite's contract states (strategy effect "restructure a loop", its unit
  relation), and whether ticket 15's race fix (plain reads of shared-action locations become
  relaxed atomic loads; redundant plain stores removed) is the first enabling rewrite;
- how proofs chain: when two unit relations compose, how a chain's level is set (its weakest
  link), and when the final candidate artifact is proven directly against the baseline
  implementation instead;
- how a chain is certified and recorded (lineage, content hashes per step).

The answer must handle any input code (map Notes), not only code an expert already reshaped.

## Comments

- 2026-10-13 16:09 ET: graduated from ticket 15 (Q10). Yan-Ru: the DX100 authors reshaped the
  baseline to fit the DX100 API before offloading (compare `TDStepMAA`,
  `apps/dx100/benchmarks/gapbs/src/bfs.cc:66-225`, with `TDStep`, `:227-256`); Probata may likewise
  rewrite the baseline into an equivalent, DX100-compatible form first. The name "equivalent
  baseline" was rejected: the baseline implementation is the code as found, which every proof
  compares against (11, Q30). Chaining is optional: the final candidate artifact can always be
  proven directly against the baseline; a chain only splits one hard relational proof into two
  easier ones. Codex's frontier-staging rewrite (`library/native/bfs-tdstep-frontier-staging.patch`)
  is a CPU-only restructuring already in the library.
- 2026-10-13 16:28 ET: claimed by agent session archevolve-42 (ticket 16 is held by archevolve-ea).
  Facts found (two read-only searches, code re-checked):
  - **Offloading contracts bundle their reshaping today.** Peter's read offload matched the
    baseline `TDStep` directly (pattern key over access-pattern annotations,
    `swdb/site_finder.py:92-103`; `records/campaign_summaries/extensa-gem5-bfs-20261004-a5.summary.yaml:81-92`).
    Its `.inc` replaces the whole function and does its own chunking, small-frontier fallback and
    gather/claim split (`library/dx100/bfs_read_offload.inc:11-72`).
  - **The authors' `TDStepMAA` adds six CPU-expressible reshapes** before its offload: block
    partition by thread id (`bfs.cc:99-101,142-143,195`), chunk-size cascade (`:102-138`),
    small-remainder fallback (`:196-217`), flattened edge loop with a resumable cursor
    (`:153-159,194`), `u` re-gathered per edge (`:163`), buffers plus a separate push phase
    (`:161-193`). BC (`bc.cc:195-235,260-294,296-317`) and SSSP (`sssp.cc:146-264`) repeat the
    cascade, thread blocks, fallback and phase split; PR tiles and strip-mines (`pr.cc:219,233`).
  - **The fork's baseline is itself hand-reshaped from upstream GAPBS:** `g.out_neigh(u)` becomes
    raw `VertexOffsets` / `out_neighbors_` indexing, `scout_count` is dropped, a redundant
    `parent[v] = u` is added (`apps/gapbs/src/bfs.cc:67-88` vs
    `apps/dx100/benchmarks/gapbs/src/bfs.cc:227-259`).
  - **Nothing chains today.** A proposal can target only an implementation's source snapshot
    (`swdb/workflow.py:376-385`); the site finder reads only implementation records' access
    patterns (`swdb/site_finder.py:95`, `swdb/db.py:263-280`); `parent_candidate` is written only
    by repair (`schemas/candidate.schema.json:125-131`, `swdb/workflow.py:520,567`); every Extensa
    iteration starts from the base snapshot (`swdb/campaign_targets.py:395-402,460-475`);
    `swdb certify` takes one contract per run (`swdb/certification.py:1081`). Implementations
    already carry `origin.derived_from` and an ordered `applies` list of strategies
    (`schemas/implementation.schema.json:35-41,542-575`).
  - **Frontier staging conflicts with read offload:** it removes the store read offload's L4
    requires (`library/rewrite_contracts/bfs_tdstep_frontier_staging.yaml:150-171,235`), and the
    read-offload `.inc` replaces the staged code instead of building on it.
  - **Side findings** (read from code, not run): (1) DX100 PR zeroes `incoming_totals` once
    (`apps/dx100/benchmarks/gapbs/src/pr.cc:140-141`), before the iteration loop (`:183`), then adds
    into it every iteration (`:242`) without a reset; the baseline resets per vertex per iteration
    (`:100`). From iteration 2 the scores look wrong unless runs stop after one iteration. Worth a
    run check; a candidate proof example if real. (2) With several contracts per candidate, the
    real campaign adapter certifies each but returns only the first record ID
    (`swdb/campaign_targets.py:555-586`), so the other certification records are unlinked.
  Round 1 posted: Q1 what enabling rewrites are for; Q2 the race fix; Q3 how proofs compose along
  a chain; Q4 where intermediate code lives. Held for round 2: who proposes and how contracts name
  each other; a chain's level; per-link certification and scope checks; content hashes and
  reopening; Extensa-mode and ArchEvolve-mode behavior.
- 2026-10-13 16:35 ET: round 1 answers (checkpoint; not yet the answer). Accepted: Q1 (b), matching
  and splitting (a catalog of recurring reshapes, each with a once-proven template; thin offloading
  contracts; bundled contracts stay legal as one-link chains); Q2 (the race fix stays repair, not an
  enabling rewrite); Q4 (a), a certified enabling result becomes a derived implementation in the
  research database. Q3: Yan-Ru asked "are you sure?". Re-check found two of four bullets wrong:
  - **Template route at N > 1:** "each link proven against its predecessor" needs a ∀∃ relation when
    both programs are multi-threaded (every run of O matched by some run of E;
    `../research/03-prove-once-rewrite-rules.md:23-28`). Our product programs (11 item 5) prove ∀∀.
    Holds at one thread only.
  - **Fallback "prove O directly against B; hints find the coupling invariant":** a direct relational
    proof also needs an alignment, which nothing supplies. Templates come only with contracts, and
    13's hint vocabulary has no alignment kind (`../research/03-prove-once-rewrite-rules.md:51,199`).
  - **Catalog relations:** a catalog reshape is kernel-independent, so its relation cannot be a
    kernel's unit relation; "composition lemma per relation pair" does not fit it.
  - Kept: the unit-postcondition route (BFS) at every N, and the proof-unit boundary rule, plus the
    union of every link's preconditions and assumption-set entries.
  Revised Q3 posted.
- 2026-10-13 16:41 ET: Yan-Ru accepted revised Q3 ("ok"): BFS's unit-postcondition route proves the
  final candidate against B directly; a link that changes the thread split or loop order is proven
  against B (template at one thread; 15's exact cover, kind lemmas and composition theorem at
  N > 1); a link that keeps the split is proven per thread against its predecessor (same shared
  actions, same arguments, same order, given the same shared-memory answers); a failed link falls
  back to a direct bounded check (SAW; CIVL compare mode, unconfirmed); the boundary rule with the
  union of preconditions and assumption entries. Round 2 posted: Q5 who proposes and how contracts
  name each other; Q6 the initial catalog; Q7 per-link certification, level and hashes; Q8 the two
  modes; Q9 the proof-of-concept chain.
- 2026-10-13 16:45 ET: round 2 answers: Q5-Q9 accepted as recommended. Round 3 posted: Q10 terms
  (rewrite chain, predecessor, derived implementation, offload-only contract), plus confirmation of
  the shared understanding.
- 2026-10-13 16:47 ET: Yan-Ru accepted Q10 and confirmed the shared understanding ("yes").

## Answer

2026-10-13 16:47 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments). Facts:
two read-only code searches and the code re-checked in this session (paths in the 16:28 ET
comment).

1. **What enabling rewrites are for: matching and splitting** (Q1 b). An enabling rewrite runs when
   (i) no offloading contract matches the input, or (ii) a reshape that recurs across kernels is
   split out of a bundled offload. New offloading contracts are **offload-only contracts**
   (glossary): they keep their predecessor's thread split and loop order. Bundled contracts
   (Peter's `bfs_read_offload`, whose `.inc` replaces the whole `TDStep`; the authors'
   `TDStepMAA`) stay legal as one-rewrite chains. Today no input needs trigger (i): Peter's
   contract matched the baseline `TDStep` directly.

2. **Initial catalog** (Q6): five enabling contracts, each with a relational template proven once
   and reused across kernels (rough cost: about one week each, about one month in all).

   | Reshape | Seen in |
   |---|---|
   | Thread-block chunking, chunk-size cascade as a knob | BFS `bfs.cc:99-143,195`; BC `bc.cc:195-235`; SSSP `sssp.cc:176-211` |
   | Small-remainder fallback | BFS `bfs.cc:196-217`; BC `bc.cc:296-317`; SSSP `sssp.cc:146-171` |
   | Phase split: gather, then claim or update, then push | BFS `bfs.cc:161-193`; BC `bc.cc:260-294`; SSSP `sssp.cc:237-264` |
   | Buffer materialization (gathered values staged per thread) | BFS `bfs.cc:161-163`; BC and SSSP inside their phase splits (lines above) |
   | Edge-loop flattening with a resumable cursor | BFS `bfs.cc:153-159,194`; PR `pr.cc:233` |

3. **The race fix is not an enabling rewrite** (Q2). It makes no contract match and repairs an
   already refuted candidate artifact; it stays counterexample-guided repair's general fix (15 item
   10) and a clause of the new offloading contract versions (15 item 11). Catalog entries must
   emit race-free code by construction, since a link that changes the thread split is proven at
   N > 1 (item 4).

4. **Proof rule for a rewrite chain** (Q3, revised after "are you sure?"), with B the baseline
   implementation:
   1. **Unit-postcondition route (BFS):** the final candidate artifact is proven against B
      directly at every thread count (C for the candidate; "B meets C" and "C-units satisfy the
      unit relation" proven once, 10 item 2; 15's machinery at N > 1). No chain proof.
   2. **A rewrite that changes the thread split or loop order** (chunking) is proven against B,
      never against its predecessor: its template at one thread; at N > 1, 15's exact chunk cover,
      the shared-action kinds' commutativity lemmas and the parallel composition theorem. No new
      per-pair lemma.
   3. **A rewrite that keeps the thread split** (an offload-only contract) is proven per thread
      against its predecessor: given the same answers from shared memory, both perform the same
      shared actions with the same arguments in the same order. A lockstep product of one thread of
      each, which 11 item 5's product programs prove (a "for all pairs" property). The result
      inherits its predecessor's verdict at every N.
   4. **A rewrite that fails to prove:** the bounded verifier compares the final candidate artifact
      with B directly (SAW at one thread; CIVL's spec-vs-implementation compare mode for threads
      <= k, unconfirmed), giving proven within bounds. No unbounded direct route: a direct
      relational proof needs an alignment, which nothing supplies (templates come only with
      contracts; 13's vocabulary has no alignment kind; `../research/03-prove-once-rewrite-rules.md:51,199`).
   5. **Boundary:** every rewrite keeps the proof unit's boundary (same function, same driver
      loop), so the last contract's lifting lemma covers the chain. The verdict carries the union of
      every rewrite's preconditions and assumption-set entries, each proven at the real call or
      listed (09 item 10).

   Rejected: "each link proven against its predecessor" at N > 1 (needs a for-all-exists relation
   between two multi-threaded programs, `../research/03-prove-once-rewrite-rules.md:23-28`, which our
   product programs do not prove); "the hint loop finds the coupling invariant of a direct proof"
   (no alignment); a composition lemma per relation pair (catalog entries are kernel-independent).

5. **Who proposes, and how contracts name each other** (Q5). The offload-only contract names the
   enabling contracts it requires, in order (ID and version range), as a precondition checked
   against its predecessor's lineage record; pattern keys cannot express "phase split done".
   Enabling contracts never list what they enable. The site finder is unchanged: it matches the
   next contract against the derived implementation (item 6). The profiling agent annotates each
   derived implementation like any implementation; a deterministic check confirms the pattern
   classes the enabling contract's strategy effects predict, and a mismatch blocks the chain. For
   any input: when no catalog entry fits, Extensa mode's rewriting role may write a new
   experimental enabling contract with its template, proven once as a contract proof and used only
   in Extensa mode until promotion.

6. **Intermediate code is a derived implementation** (Q4 a; glossary). A certified enabling result
   is recorded as an implementation with `origin.derived_from` its predecessor and `applies` its
   strategies (`schemas/implementation.schema.json:35-41,542-575`), in the research database
   until promotion. Proposals and the site finder then work on it unchanged. The performance
   comparator stays the root baseline (ADR 0005).

7. **Certification, level and hashes** (Q7).
   - Each rewrite is certified alone against its predecessor's snapshot, one contract per run, as
     `swdb certify` works today (`swdb/certification.py:1081`): enabling rewrites in the native
     family, offloads in the DX100 family, so each family's file-scope check sees only its own
     change. The final candidate artifact also runs the kernel's correctness check against the
     root baseline, always.
   - Level: the weakest verdict among the parts its route depends on (route 1: the final
     candidate's own proof; routes 2-3: the rewrite proven against B plus every per-thread proof
     after it; route 4 records its bounds).
   - Each rewrite's verdict holds for its contract hash, predecessor snapshot hash and result hash.
     A change reopens that rewrite and every one after it; dependent candidate artifacts drop to
     certified until re-proven (10 item 6, extended).

8. **Modes** (Q8). Extensa mode: an iteration may start from the baseline or from a certified
   derived implementation of the same kernel (today it always starts from the base snapshot,
   `swdb/campaign_targets.py:395-402`; a build item). A result is evaluated for speed and ranked
   only when proposed as a final candidate artifact, so intermediate code spends no mbit10
   lane-hours. ArchEvolve mode: shared contracts only; each rewrite is one rewrite proposal, run
   once; only the final candidate artifact is evaluated and handed to the team; a derived
   implementation enters the main database only through promotion.

9. **Proof-of-concept chain** (Q9). (a) Split Peter's bundled read offload into catalog rewrites
   (chunking, fallback, phase split) plus an offload-only read offload on the fork's `TDStep`;
   prove both forms; compare per-candidate proof time and hint rounds (the test of item 1's claim
   that offload-only proofs stay small). (b) Only if (a) passes: an "any input" demo on upstream
   GAPBS `TDStep` (`apps/gapbs/src/bfs.cc:67-88`), with one more catalog entry (inline the
   neighborhood iterator) and `scout_count` in the unit relation (fixed by the newly visited set).
   Rough cost: (a) 1-2 weeks once the catalog templates exist; (b) about 1 more week.

10. **Generality.** The catalog's five reshapes recur in BFS, BC and SSSP (PR shares the
    flattening); the proof rule, records, certification and modes are per contract and kernel.

11. **Defaults (no question asked).** Codex's frontier staging stays a performance contract outside
    the initial catalog; it may be a step of a rewrite chain only when an offload-only contract
    names it. Its conflict with read offload's L4 (`library/rewrite_contracts/bfs_tdstep_frontier_staging.yaml:235`)
    goes away with the new `bfs_read_offload` version that drops the redundant store (15 item 11).

**Side findings** (read from code, not run; recorded here, no new ticket):
- DX100 PR never resets `incoming_totals` between iterations (`apps/dx100/benchmarks/gapbs/src/pr.cc:140-141,183,242`;
  the baseline resets per vertex, `:100`). From iteration 2 the scores look wrong unless runs stop
  after one iteration. Worth a run check; a refutation example for the paper if real.
- With several contracts per candidate, the real campaign adapter certifies each but returns only
  the first record ID (`swdb/campaign_targets.py:555-586`).
- The fork's baseline `TDStep` is itself hand-reshaped from upstream GAPBS (iterator replaced by raw
  CSR arrays, `scout_count` dropped, redundant store added).

**Inputs passed on:**
- **Ticket 16** (resolved at the same time in another session; input left in its Comments): its
  items 3-4 (relations as ACSL predicates with one parameter per side, inside a YAML frame) cover
  the catalog templates and the per-thread lockstep relation (predecessor, result). New YAML-frame
  field, a proof-of-concept build item: an offload-only contract's ordered list of required
  enabling contracts.
- **Map fog (Evaluation plan):** the bundled-vs-chained proof comparison (9a), the upstream GAPBS
  demo (9b), the catalog's template proofs.
- **Map fog (Records):** per rewrite in a chain: contract hash, predecessor snapshot hash, result
  hash, certification record, proof route; derived implementations' lineage of contracts
  (`applies` lists only strategies today).
- **Map fog (Extensa-mode loop):** iteration start from a derived implementation; only final
  candidate artifacts ranked.
- **New fog:** an "alignment" hint kind for direct unbounded proofs without a template (would widen
  13).
- **Proof-of-concept build items:** lineage of contracts on implementation records; campaign start
  from a derived implementation; per-rewrite certification links.

Glossary: rewrite chain, predecessor, derived implementation, offload-only contract added; enabling
rewrite sharpened.

## Later changes

- 2026-10-13 20:41 ET, from [24](24-alignment-hint-kind.md) (item 3): enabling rewrites and rewrite chains are unchanged. Item 2's
  catalog relational templates are not built in this effort: a derived implementation is proven once
  by route 1 (direct, against the kernel's unit postcondition), which every evaluated kernel now has.
  Item 4.3 (offload-only rewrite per thread against its proven predecessor) stays; per final
  candidate, route 3 when its predecessor is proven, else route 1. Item 4.4's bounded-only fallback
  becomes route 1 on every evaluated kernel. Item 9a compares per-candidate proof time of chained
  (route 3) vs direct (route 1) vs bundled.
- 2026-10-13 21:29 ET, from [27](27-proof-of-concept-stages.md) (items 2, 5, 7): item 9a is proof-of-concept stage A5; "9a passes"
  means chained, direct and bundled reach the same level, times recorded. 9b runs only then and is
  the first thing cut if time runs short; A5 itself is third in the cut order.

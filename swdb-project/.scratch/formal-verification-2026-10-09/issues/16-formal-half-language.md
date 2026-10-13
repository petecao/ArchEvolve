# 16 — What language do formal halves and the proof semantics share?

Created: 2026-10-13 14:19 ET
Updated: 2026-10-13 16:49 ET (resolved with Yan-Ru in three grilling rounds)
**Type:** grilling
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session archevolve-ea, claimed 2026-10-13 16:13 ET)
**Blocked by:** 11, 12
**Map:** `../map.md`

## Question

Which single source language do formal halves and the DX100 proof semantics use, so that one
source generates SAWScript specs, C call stubs and ACSL contracts (ticket 11, item 4)? Decide:

- the language: extend the ported Extensa grammar, adopt an existing one (such as an ACSL subset)
  as the source, or a small new one;
- how it states the proof semantics' ghost hazard state (producers, coverage, tile ownership) and
  per-element memory footprints (ticket 12, items 3-5);
- how legality clauses that are natural-language only today get formal halves (BFS read offload:
  L2, L4; L3 and L5 become proof-semantics rules per ticket 12, item 7);
- the declared C++ subset the C lowering accepts (ticket 11, item 3), since formal halves name its
  constructs;
- how each clause names its proof placement: once with a named entry, per candidate, or assumed
  (ticket 10, item 4).

The language must be general: the same source covers the BC, PR and SSSP contracts, not only BFS.

## Comments

- 2026-10-13 14:19 ET: graduated from the map's "Formal-half language" fog when ticket 12
  resolved. Inputs: 09 (formal halves per clause, unit relation), 10 (proof placement, summaries),
  11 (three generated forms from one source; only summary-generated `assume`s allowed), 12 (the
  proof semantics' rules, ghost hazard state and footprints come from the same source; the three
  forms must give the same verdict on every fixture scenario).
- 2026-10-13 15:22 ET: input from 13: proof hints are ACSL records on the C lowering, for WP only. The
  hint vocabulary bans recursive and inductive definitions (WP turns recursive ones into
  unchecked axioms; `../research/13-wp-hint-facts.md`); only the contract's logic library, reviewed
  at promotion, may hold them. Decide where that library lives and in which language.
- 2026-10-13 16:09 ET: input from 15: formal halves must state a contract's shared actions by kind
  (claim, min-update, atomic add or OR, OpenMP reduction, queue reserve), a sharing class per array
  per barrier interval (read-only, thread-owned, changed only through shared actions,
  lock-protected), and history reads. The parallel composition theorem's statement (Rocq) uses the
  same vocabulary, so the language must map onto it.
- 2026-10-13 16:13 ET: claimed (agent session with Yan-Ru). Facts gathered: only L1 has a formal
  half today, a reference pin (`library/rewrite_contracts/bfs_read_offload.yaml:78-92`); L2-L5 and
  the knob clauses are natural-language only. The ported Extensa grammar
  (`swdb/predicate_grammar.py:33-130`) has `+`/`-` only, a closed 11-function alphabet, no user
  functions, ghost state, old values or reals; its one consumer compiles runtime probes
  (`swdb/extensa/probes.py:931`); only `library/library_operations/pack_executor.yaml:87,103` uses
  it. Nothing generates ACSL, SAWScript or SMT. The Mac's Frama-C 33 includes E-ACSL and the ACSL
  importer; SAW is not installed yet.
- 2026-10-13 16:27 ET: round 1 answers (checkpoint; not yet the answer).
  - **Q1 accepted (b):** an ACSL subset inside a YAML frame is the single source. WP reads it
    untranslated; two translators (to SAWScript specs, to C call stubs) are trusted tools; E-ACSL
    gives a runtime-check form. YAML holds what ACSL cannot say (proof placement, sharing classes,
    shared actions, gem5 citations). The Extensa grammar stays for runtime probes only.
  - **Q2 accepted:** the C lowering's subset is defined by construct, not type name: C plus
    references; classes without inheritance or virtual functions; member functions and operators;
    constructors and destructors as explicit calls; templates (instantiated); `new[]`/`delete[]`;
    `enum class`, `constexpr`, `static_assert`; `std::min`, `std::max`, `std::copy`, `std::swap`
    through C models proven once; OpenMP `parallel`, `for` (static, dynamic, `nowait`),
    `critical`, `atomic`, `barrier`, `reduction`; `__sync_*`/`__atomic_*`; `__dxc_*`/`maa_*` calls
    through summaries and the proof semantics. Out at first: inheritance, virtual, exceptions,
    lambdas, RTTI, std containers and streams. Grows through the "unsupported construct" class.
  - **Q4 accepted:** an agent drafts missing formal halves; five gates accept one (parses and
    type-checks; the reference instance proves it; each formally visible negative control is
    refuted by it; its runtime-check form passes every certify run of the reference instance;
    Yan-Ru approves the statement at promotion).
  - **Q3:** Yan-Ru asked "are you sure?". Re-check against the code found three wrong placements in
    the proposal (L1, L3, knob clauses); revised in round 2.
- 2026-10-13 16:32 ET: round 2 posted (Q3 revised; Q5 YAML frame; Q6 names and relations; Q7 logic
  library and reference semantics; Q8 the "C lowering" vs "lowering" term clash; Q9 ghost hazard
  state). Re-check for Q3: L1 is about the candidate's continuation loop (control
  `dropped_continuation`), so per candidate; L3 follows from the L5 rule plus initialization, so
  per candidate; knob clauses are compile-time constants (`library/dx100/bc_read_offload.inc:18`).
  `library/dx100/reference.hpp:9` describes the whole range loop, not one call, and uses
  `std::vector` (outside the subset). gem5 facts for Q9 (upstream `arkhadem/DX100` at
  `e4fc4af`, `src/mem/MAA/`, read file by file; no local checkout): at most 32 commands in flight
  per instance (`MAA.py:16`, `MAA.cc:81,85`; a full instance stalls the issuer, timing only); a new
  command stalls while a pending one uses its destination tile as destination, source or
  condition (`IF.cc:193-212`), so one unfinished writer per tile and no overwrite under pending
  readers; several readers allowed (`SPD.cc:217`); every command names a tile whose wait covers
  it; the region stall is per registered region (`IF.cc:213-219`). Corner: 8-byte data uses
  tiles t and t+1 but the stall compares only t (`SPD.cc:124-133`); the four DX100 kernels use
  4-byte types. The strict layer's op list is unbounded and models neither the 32-slot capacity
  nor the region stall.
- 2026-10-13 16:38 ET: round 2 answers (checkpoint; not yet the answer). All accepted: Q3 (revised
  placements: every `bfs_read_offload` clause per candidate except L5, assumed as a proof-semantics
  rule; `once` for library entries' own clauses and contract-proof parts), Q5 (YAML frame; per
  barrier-interval sharing classes per candidate, proposed by the lowering, proven by WP; refines
  15 item 2), Q6 (ACSL over the C lowering's kept C++ names; relations as ACSL predicates with one
  parameter per side), Q7 (logic library in `library/logic/` plus one per contract; `\false`
  check; ACSL definitions as proof references), Q8 (keep "C lowering", disambiguated in the
  glossary), Q9 (fixed-size ghost arrays, K = 32 as an encoding bound, footprints over current
  index-tile contents, new 8-byte tile-pair rule). Yan-Ru added: **support `std::vector`**
  (reopens Q2's "no std containers"; round 3).
  E-ACSL test (Frama-C 33, scratchpad): translates recursive logic functions, bounded quantifiers,
  `\separated` and reals; turns a simple inductive predicate into a recursive function; drops
  `\old(a[k])` under a quantifier ("\at with logic variable linked to C variable is not yet
  supported. Ignoring annotation."), the form BFS frame clauses need.
  Glossary: C lowering, proof placement, logic library added.
- 2026-10-13 16:46 ET: round 3 answers. **Q10 accepted (a):** `std::vector<T>` (not `bool`) and `std::pair`
  join the subset as modeled types: a C struct plus one C function per member, each with an ACSL
  contract citing the standard's [vector] clauses, trusted as one standard-library entry (like 15's
  OpenMP entry), reused as SAW overrides; growth frees the old buffer; `at` out of range is a proof
  obligation; growth on a shared vector in a parallel region is refuted outside `critical`; new
  assumption entry "allocation succeeds"; ACSL reference definitions are then proven against the
  lowered `reference.hpp`. **Q11:** Yan-Ru asked "are you sure?"; the re-check kept the E-ACSL
  finding and fixed four points (inductive predicates do get an executable form but it can loop on
  a cycle; hints define nothing recursive and axioms are banned; Frama-C checks no termination, so
  primitive recursion is checked syntactically; reals compare with the certify tolerance at run
  time) and added clause kinds and snapshot extent. Revised Q11 accepted.
- 2026-10-13 16:47 ET: input from 17 (resolved in a parallel session, archevolve-42): the formal-half
  language must also state (1) the catalog enabling contracts' relational templates; (2) the
  per-thread lockstep relation of an offload-only contract against its predecessor (same shared
  actions, same arguments, same order, given the same shared-memory answers), as a relation with
  one parameter per side (predecessor, result); (3) in the YAML frame, an offload-only contract's
  ordered list of required enabling contracts (ID and version range), checked against the
  predecessor's lineage record. See `17-enabling-rewrites.md`, Answer items 2, 4, 5.
- 2026-10-13 16:49 ET: Yan-Ru confirmed the shared understanding ("agree").
- 2026-10-13 16:53 ET: Yan-Ru accepted Answer item 13 (ticket 17's inputs) ("ok").

## Answer

2026-10-13 16:49 ET. Decided with Yan-Ru in a grilling session (rounds 1-3 in Comments). Facts: the code
re-checked in this session, an E-ACSL test on the Mac's Frama-C 33, and the gem5 DX100 source at
`e4fc4af` (upstream `arkhadem/DX100`, `src/mem/MAA/`, read file by file).

1. **One source: ACSL inside a YAML frame** (Q1). Formal halves and the proof semantics are
   written in an ACSL subset (item 2) inside the library YAML. WP reads it untranslated. Two of
   our translators, each a trusted-tool entry, generate the SAWScript specs (SAW overrides) and
   the C call stubs (crux-llvm, CBMC); the three forms must agree on every fixture scenario (12,
   item 8). Frama-C parses and type-checks the text, as 13's hint check does. The ported Extensa
   grammar stays for runtime probes only; its formal halves stay "stated" and never feed proofs.
   Rejected: extending the Extensa grammar (6-8 weeks, a semantics we would own, WP would read a
   translation), a new language (the same), Cryptol or SAWScript as the source (WP, which sets
   proven unbounded, would read a translation).

2. **ACSL allowed in a formal half** (Q11). Clause kinds `requires`, `ensures`, and `assigns`
   with index ranges. First-order formulas with quantifiers bounded by integer ranges; `\old` and
   `\at(..., Pre)`; integer and `real` arithmetic; `\valid`, `\separated`, `\result`; calls to
   logic-library definitions that are non-recursive or primitive recursive on a non-negative
   integer argument (the recursive call takes `n-1` under a guard `n <= 0`). The library
   validator checks that rule syntactically, because Frama-C checks no termination (13's
   `pbad(x) = !pbad(x)` proved). Inductive definitions appear only in logic-library lemmas: their
   executable form can loop (E-ACSL turned a reachability inductive into a recursion that never
   ends on a cycle). Axioms nowhere; an unproven fact is an assumption-set entry.

3. **Names and relations** (Q6). Formal halves are ACSL over the C lowering of the baseline proof
   unit's signature. The lowering keeps C++ names (a class becomes a struct of the same name and
   fields, references become pointers, operators become named functions), so Frama-C
   type-checks the text directly and no name-rewriting layer is trusted; the logic library
   offers accessors such as `at(parent, v)`. The SAW translator maps fields through debug
   information. A unit relation or coupling invariant is an ACSL predicate with one parameter per
   side (`unit_rel(b_next, c_next)`); the YAML binds each parameter to the baseline or the
   candidate, and the product-program generator (11, item 5) instantiates it. The lowering's
   naming rules are versioned and belong to the content-hash set.

4. **The YAML frame** (Q3, Q5).
   - **Per clause:** an `acsl:` field (the text and the logic-library entries it uses) beside the
     existing `formal` (reference pins and Extensa predicates, for tests and probes), and a
     required **proof placement** (glossary): `once: <entry>@<version>`, `per_candidate`, or
     `assumed: {kind, rule or owner, evidence}` with a kind from 09's list. It is separate from
     `discharge_mode`, which says how certify tests the clause (L2 is `differential_test` there,
     `per_candidate` here).
   - **`bfs_read_offload`:** L1 (the candidate's continuation loop; its control is
     `dropped_continuation`), L2, L3 (from the L5 rule plus "`parent` is initialized before
     `TDStep`", a proof-unit precondition the lifting lemma discharges), L4, `once_enqueue` and
     the knob clauses (compile-time constants; `library/dx100/bc_read_offload.inc:18`) are
     `per_candidate`. L5 is `assumed`, kind "the accelerator's proof semantics". `once` serves
     library entries' own clauses (`once: self`, such as an intrinsic's `result`) and the parts
     of a contract proof. The contract's `runtime_guards` are not clauses; they are proof-unit
     preconditions discharged in the lifting lemma.
   - **Per contract:** for each array of the proof unit's interface, the shared-action kinds it
     allows (claim, min-update, atomic add or OR, OpenMP reduction, queue reserve) and whether its
     reads are history reads.
   - **Per barrier interval, sharing classes are per candidate** (refines 15, item 2: the
     contract cannot know where a candidate puts its barriers; the authors' `TDStepMAA` adds one).
     The C lowering proposes each class; memory a candidate allocates inside the parallel region
     is thread-owned; WP proves every class, so a wrong proposal fails and never passes.
   - **Per proof-semantics rule:** `cites: {gem5 commit, path, lines}` or `assumed: {owner}`.
   - **Rocq:** shared-action kinds and sharing classes are closed enumerations with one Rocq
     constructor each; every per-candidate WP obligation is named after the theorem hypothesis it
     discharges (15, item 8); a script checks that the three lists agree. A new kind bumps the
     method version.

5. **Missing formal halves** (Q4). An agent drafts them; five gates accept one: (1) it parses and
   type-checks; (2) the reference instance proves it; (3) each negative control a formal check can
   see (10, item 2) is refuted by it; (4) its runtime-check form (item 8) passes on every certify
   run of the reference instance; (5) Yan-Ru approves the statement at promotion. With 15's
   vocabulary the first drafts are small: L2 is the claim kind's write-once rule (a sharing
   declaration on `parent`); L4 is claim plus queue reserve plus one predicate (for each `k`,
   `(frontier[k], vertices[k])` is an edge from this chunk and `hints[k]` is a history read of
   `parent[vertices[k]]`; `library/dx100/bfs_read_offload.inc:39-47`); `once_enqueue` is queue
   reserve plus "push `v` exactly when the claim on `v` succeeds".

6. **The C lowering's subset** (Q2), defined by construct, not by type name: C plus references;
   classes without inheritance or virtual functions; member functions and operators;
   constructors and destructors as explicit calls; templates (instantiated); `new[]`/`delete[]`;
   `enum class`, `constexpr`, `static_assert`; `std::min`, `std::max`, `std::copy`, `std::swap`
   through C models proven once; OpenMP `parallel`, `for` (static, dynamic, `nowait`),
   `critical`, `atomic`, `barrier`, `reduction`; `__sync_*` and `__atomic_*`; `__dxc_*` and
   `maa_*` calls through summaries and the proof semantics; `std::vector<T>` (not `bool`) and
   `std::pair` as modeled types (item 7). Out at first: inheritance, virtual functions,
   exceptions, lambdas, RTTI, other standard containers, streams. Each "unsupported construct"
   failure (11, item 9) extends it. Outside it a candidate reaches at most proven within bounds
   (11, item 3).

7. **`std::vector`** (Q10, Yan-Ru's addition). Modeled, not lowered from libc++: a C struct
   `{data, size, capacity}` and one C function per member (construction by count, by count and
   value, copy, move; destruction; `operator[]`, `at`, `data`, `size`, `empty`; `begin`/`end` and
   range-for; `push_back`, `resize`, `reserve`, `clear`, `swap`), each with an ACSL contract
   citing the standard's `[vector]` clauses and reused as a SAW override, so SAW never runs
   libc++ internals. Growth frees the old buffer, so a stale pointer or iterator fails the proof
   (11, item 11); `at` out of range is a proof obligation (exceptions are out). In a parallel
   region, element accesses follow the sharing class of `data`; growing a shared vector outside
   `critical` is refuted. New assumption entries: the pinned standard library implements the
   modeled members as the standard says (trusted tool, like 15's OpenMP entry); allocation
   succeeds (covers `new[]` too). The rest of the standard library follows one modeled type at a
   time. About 1 week of agent work.

8. **Runtime-check form** (Q11). Our C-stub generator in check mode: it snapshots each `\old`
   range on entry (extent from the quantifier bounds evaluated on entry; a bound that depends on
   the post-state is rejected), runs bounded quantifiers as loops, and compares reals within the
   kernel's certify tolerance (the rounding gap is already an assumption entry; 11, item 6).
   E-ACSL is a cross-check that counts only when it emits no "Ignoring annotation": in the test
   it dropped `\forall integer k; 0 <= k < n ==> b[k] == \old(a[k])` ("\at with logic variable
   linked to C variable is not yet supported"), the form BFS's frame clauses need.

9. **Logic library and proof references** (Q7). Shared entries in `library/logic/<name>.acsl`
   (the CSR graph model, set helpers; used by BFS, BC, SSSP and PR) and one file per contract
   beside its YAML, versioned, pinned by content hash and reviewed at promotion (13, item 12).
   Guard: an inconsistent library makes every negative control prove, which voids the contract
   proof (10, item 2); each version also checks that WP cannot prove `\false` from it alone.
   Each reference semantics gets an ACSL logic definition, proven against the lowered
   `library/dx100/reference.hpp` (possible now that `std::vector` is in the subset); per-call
   intrinsic summaries are written against these definitions. Needed because
   `reference.hpp:9`'s `range_loop` describes the whole loop, not one call with its continuation
   registers.

10. **Ghost hazard state** (Q9). Fixed-size ghost arrays, the same in ACSL ghost code, SAW ghost
    state and C stub globals: per tile {owner, uncovered writer, uncovered readers as a bitmask
    over command slots}; per register {owner, writer}; per thread a table of K command slots
    {kind, tiles, region, base, range or index tile, dependencies}. Footprints are logic
    predicates over the index tile's current contents, with no per-element copy: neither the
    device (a new command stalls while a pending one uses its destination tile as destination,
    source or condition; `IF.cc:193-212`) nor the CPU (hazard rule) can change an index tile
    while its command is uncovered. K = 32 (one instance's command slots; `MAA.py:16`,
    `MAA.cc:81,85`) is an encoding bound, not a semantic rule: more uncovered commands give "not
    proven, ghost capacity", never a refutation; a later version can raise K. SAW ghost state on
    clang 22 bitcode is a proof-of-concept check.

11. **New proof-semantics rule** (ticket 12 follow-up): an 8-byte operand occupies tiles t and
    t+1, and ownership and hazards cover both, because gem5's stall compares only t
    (`SPD.cc:124-133`). No proof-of-concept kernel uses 8-byte tile data (BFS, BC, PR and SSSP use
    `int32` and `float`). The strict layer gets the rule with its catch-up version.

12. **Generality.** Nothing here is BFS-specific: one language, frame, subset, logic library and
    ghost encoding serve every contract and kernel. BC, PR and SSSP relations are predicates per
    item 3; their floats are `real` per 11, item 6.

13. **Ticket 17's inputs fit the frame** (checked after the grilling; Yan-Ru accepted 2026-10-13 16:53 ET):
    a catalog enabling contract's relational template and an offload-only contract's lockstep
    relation are two-sided predicates (item 3), with predecessor and result as the two sides;
    the lockstep relation compares per-thread ghost logs of shared actions (kind, arguments,
    order) under the same shared-memory answers, kept like the ghost arrays of item 10. An
    offload-only contract's ordered list of required enabling contracts (ID and version range)
    is a YAML field (item 4), checked against the predecessor's lineage record.

**Cost** (agent work, estimates): the two translators, check mode and frame, about 3-4 weeks; the
`std::vector` model, about 1 week.

**Inputs passed on:**
- **Ticket 15** (later change): item 2's sharing classes per barrier interval are per candidate.
- **Ticket 12** (later change): the 8-byte tile-pair rule; reference definitions in ACSL.
- **Map fog (Records):** language and translator versions, the lowering's naming-rule version,
  logic-library hashes and `\false`-check results, the standard-library model version and its two
  entries, ghost capacity K, gate results per formal half.
- **Map fog (Evaluation plan):** C-lowering subset coverage including `std::vector`; translator
  agreement on fixtures; how many drafts each formal-half gate rejects; ghost-capacity failures.
- **Map fog (Where real DX100 bugs may hide):** the 8-byte tile-pair corner.
- **Proof-of-concept build items:** library schema fields (`acsl`, `proof_placement`, the
  concurrency frame); the two translators and check mode; the `std::vector` model; logic-library
  files; new versions of `bfs_read_offload` (formal halves for L1-L4 and `once_enqueue`) and of
  the intrinsics' `result` clauses (per call); does SAW support ghost state on clang 22 bitcode.

Glossary: formal half sharpened; C lowering, proof placement, logic library added.

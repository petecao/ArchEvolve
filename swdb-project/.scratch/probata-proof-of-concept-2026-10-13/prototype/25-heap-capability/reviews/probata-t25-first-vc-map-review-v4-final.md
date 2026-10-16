# First source/VC map: final capability-only review

2026-10-15 ET. Read-only final changed-byte review of the three prototype files under `/private/tmp/probata-resume-t25`, base `e3e91b8e998d6c60c8fc12df0520cbfd7b63026a`. No compiler, WP, Why3, prover, test, provider, CBMC or remote execution; no repository edits. Earlier draft reviews remain immutable.

## Verdict: passed for a root-owned first capability admission probe

No remaining blocking source/VC mapping finding identified for the exact int count/value constructor and destructor. The final zero-extent edge is resolved: well_formed requires distinct live allocation bases in addition to range separation, and available excludes every live base, including zero-extent bases. Aliases/subobjects within one identity remain possible; one-past boundary equality is not globally prohibited. This is a uniform allocator-state relation, not an extra original caller precondition.

The final prototype contains 40 target packets: 39 isolated check-lemma packets and one numeric C kernel. Four lemma packets are expected negatives; the other 35 lemmas and numeric kernel are prospective positives. This is not a claim of 40 actual WP goals: the numeric kernel will generate its own ordinary/RTE/initialization/smoke inventory, all of which must be retained and read.

Confirmed corrections across the reviewed passes:

- Fixed reviewed model/module and generated original source hashes close the map to exactly the original int bodies. Extra unmatched writes/branches refuse before packet generation; unchanged source needles alone cannot admit them. Twelve source events bind the original stores, branch, allocation, loop phases and release to their mapped obligations.
- Receiver int-pointer/size/capacity layout is pinned to size24, alignment8 and offsets0/8/16; int uses size4/alignment4. Uniform typed access predicates enforce alignment. Existing valid(this) maps to the receiver typed region; usable allocator output supplies int alignment. No new source requires are inserted.
- Arbitrary incoming well-formed heaps retain issued dead identities, old allocations and escaped aliases. Allocation adds a fresh unbounded identity and uninitialized cells under the declared allocation-success/freshness policy. Available addresses provide live-range separation, base uniqueness and alignment. Allocation-result hypotheses are internal semantic output facts, not caller assumptions.
- Constructor initialization, zero return, six receiver-write RTEs, fresh extent/uninitialized state, capacity-entry, loop prefix establishment/step/exit, numeric overflow/index/variant checks and final original representation/value/frame clauses have corresponding packets. The invariant carries well_formed; allocation availability is propagated at entry. No completed prefix is a trusted axiom.
- Destructor reads original initialized data, checks null/freeable base, releases the actual identity, invalidates all aliases without null rewriting, proves original old-pointer invalidity and preserves other objects. Receiver/data overlap remains allowed within one identity, with no promised valid/reset receiver afterward. Frame distinguishes contents from allocation lifetime.
- Zero-size control now uses a legal available allocation output and proves well-formed nonnull typed formation without readable elements. Legal address reuse fits within the freed extent, proves available/well-formed reallocation and equal address, and keeps the old identity unreadable. The extent condition licenses that control's legal reuse; it is not a finite storage pool, fixed history bound or source caller restriction.
- Omitted-store and wrong-NULL-release controls derive their transitions from exact retained source mutants and test the corresponding original step/post obligation. Stale-read and double-release controls remain expected nonproofs. Desired source postconditions are not imported as axioms.
- Exact packet declarations preserve capability-only status, pending actual validation and unsupported generic caller composition. Typed-cell memory does not claim byte/cast/partial-write or arbitrary element-type semantics. No adapter proof record or complete ticket25 member acceptance is issued by prepare/check.

The project explicitly trusts this reviewed closed source/event/VC translation and uniform heap definitions under its lowerer TCB; no separate external compiler-correctness theorem is required. That does not certify real import syntax, theorem consistency beyond the reviewed definitions, actual solver success, emitted task assumptions or dependency closure. Root must freeze and pin the files, admit the real tool environment, select every isolated target, inspect transitive imported definitions/assumptions, and retain every generated numeric goal. Expected negatives must remain nonproved; a missing/filtered goal is not accepted. Generic caller integration and complete ticket25 acceptance remain future work.

Author-reported public controls were not rerun in this review. This verdict approves the setup for the first capability experiment only; no formal capability success is claimed.

Final reviewed byte pins:
- `heap_bridge.mlw`: `2075199d410ccc50e4b472fa58ebaa8bcca304e24f210cd88bad4fd4900825cf`
- `source_vcs.py`: `b6797e8d6a9180c520cd829542253238a04d766b4e2974b1e185761b58b46363`
- `packets.py`: `dc754e9e5e033e4c00a50dae5d9b1ce7e2fdfa47a9dbaf57dd5b74aa43fdd05f`

# First source/VC map review: revised 39-target draft

2026-10-15 ET. Read-only follow-up at base `e3e91b8e998d6c60c8fc12df0520cbfd7b63026a`, `/private/tmp/probata-resume-t25`. No test/compiler/verifier/prover/Why3/provider/CBMC/remote execution; no repository edits. Initial review remains immutable at `/private/tmp/probata-t25-first-vc-map-review.md`.

## Verdict

The revised source gate, event inventory and exact mutant transitions resolve the main source-admission gaps. Two allocator/typed-state issues still need a bounded correction before treating all mapped heap/RTE obligations as a complete first-pair capability inventory. A partial import-syntax probe can still be labeled as such; this review does not demand a general byte-memory compiler or external soundness theorem.

### 1. Usable typed allocation needs alignment

`available(h,n,a)` now expresses positive address and live-range separation, which fixes the earlier overlap issue. It still admits a=1 for an int allocation. `reads/writes` are range/liveness/permission predicates only; they do not establish typed alignment. If numerical_address is the model's address, source malloc's usable int storage must have pinned target int alignment as a uniform allocator output relation, not a new original caller precondition. Receiver validity likewise needs a declared typed-layout relation (including receiver alignment), inherited from the original valid(this). Add target alignment assertions and mapped checks or state an explicit narrower representation boundary; do not call unaligned range-only goals complete typed RTE coverage.

### 2. Special allocation controls must preserve allocator well-formedness

`control.zero_size.formation` currently allocates at arbitrary a without available and does not require the resulting heap well formed. Negative/overlapping addresses therefore satisfy its formation result because forms only checks liveness/extent. `control.reused_address.stale` similarly allows arbitrary negative/oversized n and can allocate a new range overlapping another live object. Those true formulas show identity invalidation even on malformed outputs, but do not demonstrate the requested legal zero-size/address-reuse controls.

Require the uniform allocator-output relation in these control packets, prove well_formed of their outputs, and bound the reused extent or require its availability after release. These are internal allocation-result facts, not strengthened source caller requires. Carry the same available/well-formed facts through capacity-entry/loop-state composition (or record an explicit separate invariant/frame relation that preserves them), so the source state chain never silently drops the new spatial semantics.

## Revisions accepted in this pass

- Exact REVIEWED_MODEL plus two fixed generated original source hashes refuse unmatched extra writes/branches even when old needles survive. Optional --sources lets public controls exercise that gate. A closed reviewed map is sufficient; no general parser is required.
- Twelve original event entries bind all constructor statements/loop phases and destructor load/release. Six explicit receiver-store RTE targets now cover initial data/size/capacity, allocated data/capacity and final size accesses. Prefix induction and old-heap frame conditions retain their legitimate representation/inductive hypotheses without assuming a finished fill result.
- Omitted-store transition is now extracted from the exact mutated source loop and used to generate failure of the same invariant step. Wrong-NULL-release is extracted from the exact mutated dtor call and used with the same original positive-capacity postcondition. These are source-related controls rather than detached propositions. Fixed source hashes constrain the small recognized patterns.
- Generic caller composition is explicitly unsupported; typed int/receiver cells are distinguished from generic byte/cast/partial-write semantics. Exact manifest declaration comparison rejects tampering that removes pending validation or turns capability preparation into a proof claim.
- Unbounded mathematical next/issued identities, escaped-alias release, receiver-overlap handling, no alias-null rewrite, null release and unrelated-object frame remain appropriate. Uniform live-range separation and prior issued-dead identities are explicit. No constructor/destructor desired-result axioms were introduced.

No further source-event mismatch was identified in the pinned int-only bodies. The nine public CLI controls described by the author were not rerun or independently certified here. Actual imports, generated task assumptions, positive/negative results and complete dependency/goal reading remain unvalidated. The manifest still correctly reports capability_only and verifier_launched=false; no complete member-body proof or generic caller safety theorem exists yet.

Read pins for this draft (re-review later changed bytes separately):
- `heap_bridge.mlw`: `c51b7e3ee1d31983aa92a5f95a1304384c35264c1cd245eb2f6480da625c6858`
- `source_vcs.py`: `71d54c77f940832e82302a0a9e6adb0afb02d4ffeaffb2a2ee85893078c8d04e`
- `packets.py`: `dc754e9e5e033e4c00a50dae5d9b1ce7e2fdfa47a9dbaf57dd5b74aa43fdd05f`
- `test_heap_capability_packets.py`: `c4c5cec7517b4264cab3ce7bbccf63b23d528ef3e1da584f20bddac29c239bad`

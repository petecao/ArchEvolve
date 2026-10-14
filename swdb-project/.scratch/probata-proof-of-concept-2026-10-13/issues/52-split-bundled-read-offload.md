# 52 — Split the bundled read offload

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 19, 31
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes", "Modules" (loop, modes and guards: implementation records, campaign adapter), "Formal-half language and the C++ subset" (YAML frame), "Records and levels", "Proof-of-concept plan" (A5, cut order); O10); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 1, 2, 3, 5, 6, 7, 9 and later changes; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) items 3, 6; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 4, 5, 13; [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) item 5; [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) item 7
**Time estimate:** about 1 week
**Cut order:** 3

**What to build:** Peter's `bfs_read_offload` does everything in one rewrite: it replaces the whole
`TDStep` and does its own chunking, small-frontier fallback and gather/claim split. This ticket splits
it into a rewrite chain on the fork's `TDStep`: three catalog enabling rewrites (thread-block chunking,
small-remainder fallback, phase split), then an offload-only read-offload rewrite. The offload-only
contract names its required enabling contracts in order and is refused on any predecessor whose
lineage lacks them. Each rewrite is certified alone against its predecessor's snapshot. Each certified
enabling result is recorded as a derived implementation, and a deterministic pattern-class check on
each one blocks the chain on a mismatch. Yan-Ru ends up with a certified chain whose every step is on
record, ready for 53 to prove.

## Acceptance

- [ ] **Three enabling contracts in the catalog:** thread-block chunking (the chunk-size cascade as a
  knob), small-remainder fallback, and phase split (gather, then claim, then push). Each offloads
  nothing and only reshapes (strategy effect "restructure a loop"), and never lists what it enables.
  Each states no unit postcondition and records why: "kernel-independent reshape; its results are
  proven by route 1" (design O10, default until Yan-Ru rules: 24 item 2's drafting rule governs
  kernel contracts). `swdb validate` accepts all three. Negative control: a copy of one that
  lists what it enables is rejected (20's frame check, run on these entries).
- [ ] **The offload-only read-offload contract** keeps its predecessor's thread split and loop order.
  It names its required enabling contracts in order, each by ID and version range. It states BFS's
  unit postcondition (24 item 2's drafting rule, which governs kernel contracts; design O10), which
  53's direct route proves. It carries
  its lockstep relation: a two-sided predicate over predecessor and result that compares per-thread
  ghost logs of shared actions (kind, arguments, order) under the same shared-memory answers (16 item
  13). `swdb validate` accepts it.
- [ ] **Lineage check, with negative controls.** Applying the offload-only contract to the last derived
  implementation of the chain is accepted. It is refused, with the reason named, on: the fork's `TDStep`
  itself; a derived implementation missing one required enabling rewrite; one with the required
  rewrites out of order; one whose enabling contract version is outside the named range.
- [ ] **Each rewrite certified alone,** against its predecessor's snapshot, one contract per certify
  run: the enabling rewrites in the native-CPU family, the offload in the DX100 candidate family, so each
  family's file-scope check sees only its own change. Negative control: an enabling-rewrite patch that
  also offloads fails the native-CPU family's check.
- [ ] **Derived implementations recorded.** Each certified enabling result is an implementation record
  with `origin.derived_from` naming its predecessor and with its contract lineage. `swdb validate` and
  `swdb build` accept the three records, and the research database shows the chain from the fork's
  `TDStep` to the final candidate artifact. None enters the main database (that needs promotion).
- [ ] **Pattern-class check.** The profiling agent annotates each derived implementation like any
  implementation. A deterministic check confirms the pattern classes that its enabling contract's
  strategy effects predict; it passes on all three. Negative control: a planted mismatching annotation
  blocks the chain (the next rewrite proposal on that derived implementation is refused, with the
  mismatch named).
- [ ] **Final candidate artifact.** It also passes BFS's correctness check against the root baseline.
  Each rewrite of the chain carries its contract hash, predecessor snapshot hash, result hash and
  certification record ID; every certification record of the chain is linked, none dropped.
- [ ] **Bundled stays legal.** This ticket leaves the bundled `bfs_read_offload` contract (31's version)
  unchanged, and it still certifies as a one-rewrite chain (17 item 1).

## Notes

- **Not in this ticket:**
  - 53 — Chained vs direct vs bundled; A5 exit: every proof of this chain (route 1 on the derived
    implementations, route 3 on the offload-only rewrite), the offload-only contract's contract-proof
    parts, and the timing comparison.
  - 19 — Derived implementations: the lineage fields on implementation records and the start from a
    derived implementation. This ticket fills them for these three.
  - 31 — Five-gate drafting and the new bfs_read_offload version: the new contract version without the
    redundant store.
  - 20 — Formal-half frame: the YAML field for an offload-only contract's ordered required list. This
    ticket fills it and adds the check against the predecessor's lineage.
  - 02 — Campaign adapter returns every certification record: the per-contract record IDs the links
    cite.
  - 54 — Upstream-GAPBS demo: the "inline the neighborhood iterator" catalog entry.
  - The other catalog reshapes (buffer materialization, edge-loop flattening): left for when a contract
    needs them (18 item 5: held-out contracts use catalog reshapes as needed).
  - Catalog relational templates (route 2): not built in this effort (24 item 3). Derived
    implementations are proven by route 1 in 53.
- **Decided rules to keep:** catalog entries must emit race-free code by construction, because a
  rewrite that changes the thread split is proven at every thread count (17 item 3). Enabling rewrites
  and chains are about matching, not proofs (24 item 3).
- Assumption (not decided in the map): the chain order is the order 17 item 9a lists (chunking, then
  small-remainder fallback, then phase split), and the offload-only contract names them in that order.
- Assumption (not decided in the map): the offload-only contract's clauses come from the new
  `bfs_read_offload` version (31), minus what the enabling rewrites now do. So no rewrite in the chain
  keeps the redundant plain store, and 53's bundled arm compares against Peter's repaired code (49).
- Assumption (not decided in the map): Codex drafts the four contracts and their library code (Codex is
  the default for contract drafting, 23 item 7). They stay experimental entries until Yan-Ru's review at
  promotion. Their drafted formal halves go through 31's five gates (16 item 5): gate 1 (`swdb
  validate`) and gate 4 (the check-mode form passes every certify run of the reference instance) run
  here; gates 2 and 3, which need proofs, run in 53; gate 5 is Yan-Ru's at promotion.
- Assumption (not decided in the map): the offload-only contract's reference instance is its library
  code applied to the last derived implementation, because it never applies to the baseline itself.
  This chain's final candidate artifact is that instance.
- **Drafting rule and enabling contracts (design O10, default until Yan-Ru rules):** 24 item 2's
  drafting rule ("every contract states a unit postcondition") was written for kernel contracts and
  governs only them. An enabling contract is kernel-independent, so no kernel's unit relation fits it
  (17 item 4); it states no unit postcondition and records why: route 1 proves its results against
  the kernel's unit postcondition (24 item 3).
- Assumption (not decided in the map): the pattern-class check runs wherever a rewrite proposal targets
  a derived implementation; its refusal shows through the existing record seams. Its exact command is
  not decided.
- If A5 is cut (cut order 3, with 53), RQ3 loses its chained arm and its "chained <= bundled" bar
  (27 item 7; 18, later changes). Route 1 still covers every candidate artifact.

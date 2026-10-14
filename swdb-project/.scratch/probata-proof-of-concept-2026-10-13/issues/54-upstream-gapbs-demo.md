# 54 — Upstream-GAPBS demo

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 53
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof routes" (catalog, any input), "Evaluation design" (BFS extras), "Proof-of-concept plan" (A5, cut order)); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 1, 5, 6, 7, 9 and later changes; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 2, 5, 7; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 3; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 6
**Time estimate:** about 1 week
**Cut order:** 1

**What to build:** The "any input" demo. Start from upstream GAPBS's `TDStep`: code no expert reshaped
for DX100 (it still walks neighbors through the neighborhood iterator and returns `scout_count`). Add
one catalog enabling rewrite, "inline the neighborhood iterator". Build the chain from upstream's
`TDStep` to the offload-only read offload, put `scout_count` in the unit relation, and prove the result
by the same routes as 53. Yan-Ru gets a worked example that Probata handles code an expert never
touched. It runs only after 53 passes, and it is the first thing cut.

## Acceptance

- [ ] **Start gate.** This ticket starts only after 53's A5 exit passed (chained, direct and bundled at
  the same level). Otherwise it does not start.
- [ ] **New catalog entry, "inline the neighborhood iterator".** It offloads nothing, only reshapes
  (neighbor walks become raw CSR indexing), and never lists what it enables. It is certified alone in the
  native-CPU family. Its certified result is a derived implementation of upstream's `TDStep`, and its
  pattern-class check passes; a planted mismatching annotation blocks the chain.
- [ ] **The chain from upstream.** The baseline implementation is upstream GAPBS's `TDStep` as found.
  The chain is: inline the iterator, chunking, small-remainder fallback, phase split, then the
  offload-only read offload. Each rewrite is certified alone against its predecessor's snapshot, and
  each certified enabling result is recorded as a derived implementation.
- [ ] **Lineage check.** The offload-only contract's required-list check accepts this chain's last
  derived implementation, and refuses upstream's `TDStep` itself.
- [ ] **`scout_count` in the unit relation,** fixed by the newly visited set (each newly visited
  vertex's out-degree, summed). Negative control: a seeded result that miscounts `scout_count` is refuted
  by the bounded rung at the contract's minimum bounds.
- [ ] **Contract proof for the `scout_count` version,** as in 53: unit postcondition on the reference
  instance with its two lemmas; order-independence lemma; lifting lemma for upstream's driver; every
  formal-visible negative control refuted (the `scout_count` miscount among them); minimum bounds
  re-derived by the script. Each part a counting proof record.
- [ ] **Same routes as 53.** Route 1 on each derived implementation, once; route 3 on the offload-only
  rewrite against its proven predecessor; route 1 direct on the final candidate artifact. All through
  `swdb prove`, with the bounded rungs before WP.
- [ ] **Result.** Chained and direct reach the same certification level on read (`swdb
  candidate-level`), with per-candidate proof times recorded. The final candidate artifact passes BFS's
  correctness check against upstream's `TDStep`.
- [ ] **Records.** Every record is labeled host `mac` and marks the demo as a BFS extra, outside
  held-out rates. 58 reproduces these verdicts on mbit10. Mac rules hold: one real verifier job at a
  time under the ~8 GB RSS watchdog; at least 50 GB free.

## Notes

- **Not in this ticket:**
  - 52 — Split the bundled read offload: the three catalog entries and the offload-only contract
    reused here.
  - 53 — Chained vs direct vs bundled; A5 exit: the routes and their machinery on the fork's `TDStep`.
  - 58 — Mac verdicts reproduced on mbit10: re-runs this ticket's verdicts on mbit10. 58 waits on
    this ticket; the edge drops if this ticket is cut.
- **Why `scout_count` must be in the unit relation:** upstream's driver uses the returned
  `scout_count` to decide when to switch to the bottom-up step. A rewrite that changed it would change
  the kernel run, so the lifting lemma needs it.
- Assumption (not decided in the map): `scout_count` enters through a new version (or a derived
  contract) of the offload-only contract, with its unit postcondition extended to match. The map decides
  only that `scout_count` is in the unit relation.
- Assumption (not decided in the map): the required-list check accepts a lineage with other enabling
  rewrites before the required ones (here, inline the iterator), as long as the required ones appear in
  order.
- Assumption (not decided in the map): upstream GAPBS's BFS needs its own lifting lemma, proven once,
  because the lifting lemma is per contract and kernel and upstream's driver differs from the fork's.
- Assumption (not decided in the map): each rewrite of the chain is a rewrite proposal applied by the
  rewriting role (Codex), as 17 item 8 describes chains in ArchEvolve mode, not hand-applied library
  code. "Any input" itself means only that the start is code no expert reshaped (17 item 9b).
- **Risk:** the upstream iterator (a template class with operators) must lower inside the C++ subset,
  because the contract proof needs "the baseline meets the unit postcondition". An "unsupported
  construct" failure extends the subset (16 item 6).
- **Cut:** first in the proof of concept's cut order (27 item 7). If cut, the evaluation's BFS extras
  lose the upstream demo, and 58's edge to this ticket drops.
- Assumption (not decided in the map): the chain's five contracts (52's four plus this ticket's new catalog entry) are experimental, and ArchEvolve mode refuses non-shared contracts (63). So either Yan-Ru promotes them (shared) before the chain's proposals, or the chain is applied as library code and each rewrite certified alone, as in 52, outside ArchEvolve mode.

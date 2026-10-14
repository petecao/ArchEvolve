# 19 — Derived implementations

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 04
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "Proof routes", "Loop, modes and guards" (implementation records, campaign loop), "Records and levels" (pins), "ArchEvolve mode", "Testing Decisions" seams 3 and 4); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 5-8 and its Later changes, [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 3, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 2
**Time estimate:** about 2 days

**What to build:** A certified enabling rewrite's result becomes a **derived implementation** in
the research database: an implementation record derived from its predecessor, listing the
strategies it applies and its contract lineage. From then on it behaves like any implementation.
Proposals target its snapshot and the site finder matches contracts against it, with no change to
either. An Extensa iteration may start from a certified derived implementation of the same kernel.
Each rewrite in a rewrite chain carries a link: contract hash, predecessor snapshot hash, result
hash, certification record and proof route. Speed is still compared against the root baseline.
Tested through `swdb validate`, `swdb build` and `swdb campaign --fixture`.

## Acceptance

- [ ] **The record.** Certifying a fixture enabling rewrite yields an implementation record with
  origin kind `derived`, `derived_from` its predecessor, `applies` its strategies in order, and its
  contract lineage (the ordered rewrite contracts applied since the baseline implementation, each
  with ID and version, which an offload-only contract's required list is checked against, plus its
  content hash). `swdb validate` and `swdb build` accept it.
- [ ] **Negative controls for the record.** A rejected or uncertified enabling result yields no
  derived implementation. A lineage that names a contract missing from the library, or skips a
  rewrite of the chain, is refused by `swdb validate`.
- [ ] **Chains of two.** A derived implementation of a derived implementation carries the full
  ordered lineage back to the baseline implementation.
- [ ] **Consumers unchanged.** A rewrite proposal that targets the derived implementation's snapshot
  is accepted by the existing proposal path. The site finder matches a contract against the derived
  implementation's access-pattern annotations. Neither tool's code changes; their existing tests
  pass, plus one new fixture each.
- [ ] **Iteration start.** In a fixture campaign, an iteration starts from a certified derived
  implementation of the same kernel, and its candidate artifact's patch applies to that snapshot.
  Controls: a derived implementation of another kernel is refused; one with no certification record
  is refused.
- [ ] **Root baseline stays the comparator.** A candidate artifact built on a derived implementation
  is certified alone against that derived implementation's snapshot, one contract per run, and also
  runs the kernel's correctness check against the root baseline (17 item 7). Its speed is compared
  against the root baseline, never against its predecessor (ADR 0005).
- [ ] **Per-rewrite links.** Each rewrite in a fixture chain has a link with its contract hash,
  predecessor snapshot hash, result hash, certification record ID (the record 02 links for that
  rewrite's contract) and proof route (read from the route field, defined by 04, of that rewrite's
  proof record; "none yet" when it has no proof record, or one with no route, since the field is
  optional until 62). Fixture: one rewrite with a proof record that names its route shows it, one
  without reads "none yet". Control: a link whose certification record covers a different contract
  or a different predecessor snapshot is refused by `swdb validate`.
- [ ] **A change reopens the rest of the chain.** Changing a predecessor's snapshot makes that
  rewrite's link, and every later link in the chain, read as no longer matching through
  `swdb build`. No record is rewritten.

## Notes

- **Not in this ticket:**
  - 02 — Campaign adapter returns every certification record: the record IDs these links cite.
  - 04 — Proof record tracer: the proof record's route field the links read (04 owns it).
  - 10 — Level rule: dependent candidate artifacts dropping to certified when a pin changes.
  - 20 — Formal-half frame: the offload-only contract's ordered list of required enabling
    contracts.
  - 16 — Post-campaign WP phase and budgets: proving final candidate artifacts after the campaign.
  - 62 — Route choice and predecessor proofs in the campaign: which route proves each final
    candidate artifact, the proofs of earlier rewrites it depends on, and intermediate-rewrite
    marking.
  - 63 — Experimental enabling contracts and the shared-contracts rule: enabling contracts that
    Extensa mode's rewriting role writes, and ArchEvolve mode's shared-contracts-only rule.
  - 52 — Split the bundled read offload: the first real rewrite chain; the check of a predecessor's
    lineage against an offload-only contract's required enabling contracts, and the pattern-class
    check on each derived implementation's annotations (17 item 5). This ticket records the lineage
    those checks read.
  - 53 — Chained vs direct vs bundled; A5 exit: route 1 proofs of derived implementations, route 3
    proofs and the comparison.
  - 54 — Upstream-GAPBS demo: the "any input" demo.
  - 18 — ArchEvolve mode level and handoff block: ArchEvolve-mode proofs and the handoff.
- Proof routes (17 as revised by 24): route 1 proves each derived implementation once, against the
  kernel's unit postcondition. Per final candidate artifact: route 3 when its predecessor is proven,
  else route 1 (choosing the route in a campaign: 62). Route 2 (catalog templates) is not built.
- Until promotion: the derived implementation lives in the research database only. ArchEvolve mode
  lets one enter the main database only through promotion; no path to the main database exists
  today (ADR 0014), and promoting a derived implementation is not built here.
- Assumption (not decided in the map): the record is written when a candidate artifact whose every
  contract is an enabling contract passes certification, in either mode, with no new command. A
  contract counts as enabling when none of its strategy effects offloads.
- Assumption (not decided in the map): the campaign file lists the certified derived
  implementations an iteration may start from, and the rewrite response names its start (the
  baseline when it names none), the way it already names its contracts. Who picks the start is not
  decided; confirm with Yan-Ru before coding if this reading is wrong.
- Intermediate-rewrite marking (a rewrite whose result only feeds a later rewrite: recorded, never
  evaluated, 17 item 8, versus a final candidate artifact) is built by 62. This ticket records
  derived implementations wherever certified enabling results arise and does not change which
  candidate artifacts are evaluated.
- Assumption (not decided in the map): the per-rewrite link sits on the rewrite's result record (the
  derived implementation, or the final candidate artifact). Its proof route is read on demand from
  the route field of the rewrite's proof record (04, a blocker) and reads "none yet" until one
  names a route, so no record is edited (ADR 0016).
- Generality: per kernel and contract; nothing BFS-specific. Contract fixtures only; no held-out
  kernel (BC, PR, SSSP).
- Tests run no verifier job. Full-suite runs on the Mac use at most 2 test workers.

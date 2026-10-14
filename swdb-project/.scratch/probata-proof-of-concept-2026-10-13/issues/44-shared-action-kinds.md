# 44 — Shared-action kinds and commutativity lemmas

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 26, 31, 41
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Concurrency" (shared-action kinds), "Formal-half language and the C++ subset" (YAML frame, Rocq bullet), "Proven once vs per candidate" (the "With the method" and "With each rewrite contract" rows), "Records and levels" (method-version file), "Testing Decisions" (seams 1 and 4), S1, S8); decisions: [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 4 days

**What to build:** The five shared-action kinds become one closed list, used in three places: the
library YAML frame, the method-version file and the Rocq constructors. Each kind gets a commutativity
lemma, proven once in WP through `swdb prove` and kept as a method-part proof record. Floating-point
adds are compared over real arithmetic. A script refuses any disagreement between the YAML kinds, the
sharing classes and the Rocq constructors, so a new kind cannot slip in without a new method version.
Last, WP proves the order-independence lemma of ticket 31's new bfs_read_offload version from the
kind lemmas: every serial order of its shared actions meets its unit relation.

## Acceptance

- [ ] The five kinds are one closed list: claim (write-once CAS), min-update, atomic add or OR, OpenMP
      reduction, queue reserve. Ticket 20's frame field, the method-version file and ticket 41's Rocq
      constructors all carry exactly these five names. The method-version file also lists the four
      sharing-class names (S8).
- [ ] Each kind has one commutativity lemma proven by WP through `swdb prove`. Each is a method-part
      proof record pinning the method version and the logic and sum library hashes. `swdb validate`
      and `swdb build` accept all five.
- [ ] Each lemma counts as proven only when every property in WP's per-property report of its own
      fresh run is Valid (ticket 21's adapter). If ticket 36's smoke tests exist when this ticket
      runs, each lemma also passes them; otherwise the five are re-run through them before the
      freeze.
- [ ] Each lemma has a negative control: the same statement for an operation that does not commute
      (for example a plain overwrite in place of claim, or a non-atomic read-modify-write in place of
      atomic add) is not proven.
- [ ] The floating-point cases of the atomic-add and OpenMP-reduction lemmas use real arithmetic
      (`-wp-model +real`). Their records list rounding as a platform-choice entry (26 item 4).
- [ ] The agreement script passes on the five kinds and four sharing classes. It fails on each negative
      control: a YAML kind missing from the Rocq constructors; a Rocq constructor missing from the YAML
      list; a renamed sharing class; a kind in the YAML that the method-version file does not list.
- [ ] A new kind needs a new method version: the agreement script refuses a fixture that adds a sixth
      kind to all three lists while the method-version ID stays the same.
- [ ] The agreement script runs in the normal test workflow, not only by hand (LR-04).
- [ ] WP proves the order-independence lemma of ticket 31's new bfs_read_offload version (its claim on
      `parent` and its queue reserve at the queue flush) from the kind lemmas. Its proof record is a
      contract-proof part that pins that version's hash and cites the kind lemmas' proof record IDs.

## Notes

- **Not in this ticket:** 20 — Formal-half frame (the frame's field itself); 26 — Logic and sum
  libraries; 41 — Rocq: composition theorem statement and definitions (the constructors);
  45 — Per-thread lowering (per-candidate sharing classes, proposed by the lowering and proven by WP);
  31 — Five-gate drafting and the new bfs_read_offload version (the version the order-independence
  lemma is proven on); 49 — Peter's race repaired; A4 exit
  (re-proves the order-independence lemma on the repaired library code, S5); 11 — Method-version file
  and failure classes. The memory-model meaning in proofs (history reads; a CAS as a sequentially
  consistent read-modify-write) belongs to 45.
- Assumption (not decided in the map): what "commute" means per kind. For claim and queue reserve the
  final memory depends on order (which claimant wins; which slot each push gets). Their lemmas would
  state order independence of what the unit relation can see: the claimed set and "each claimed value
  is one claimant's"; reserved ranges disjoint and covering the total. Yan-Ru reviews these
  statements with the method-version file at the freeze (ticket 59; 26 item 3).
- Assumption (not decided in the map): the per-lemma negative controls above are a vacuity guard the map
  does not name.
- The method-version file lists the four sharing-class names beside the kinds (S8); the script
  compares that list with the Rocq constructors. Sharing classes are assigned per candidate artifact,
  not in the library YAML (16 item 4).
- Assumption (not decided in the map): 16 item 4 says "a script checks that the three lists agree". This
  ticket reads the three lists as YAML kinds, sharing classes and Rocq constructors, as its scope
  states. Matching per-candidate obligation names to theorem hypotheses is left to ticket 45's naming.
- The order-independence lemma is proven on ticket 31's new bfs_read_offload version (this ticket is
  blocked by 31). When ticket 49's repair changes that hash, the record stops counting and ticket 49
  re-proves it.
- Assumption (not decided in the map): the lemma's subject is a contract-proof part (the design spec's
  "With each rewrite contract" row), though 26 item 1's subject list does not name it.
- Assumption (not decided in the map): once-proven lemmas may use hints under the same hint rules
  ([10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) item 8), with provenance
  recorded. If ticket 35's proof hint check is not built yet, these hint sets are rechecked by it
  before the freeze.
- The kind lemmas are generic. They never touch BC, PR or SSSP code, which stay held out until
  ticket 59.
- Mac: one WP job at a time under the ~8 GB RSS watchdog.

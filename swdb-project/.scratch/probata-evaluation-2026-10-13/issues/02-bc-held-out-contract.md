# 02 — BC held-out contract and contract proof

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** proof-of-concept 59
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": held-out contracts, RQ3; "Proven once vs per candidate"; "What a proven verdict asserts"; "Bounds"; "Formal-half language and the C++ subset": the five gates; "Concurrency": shared-action kinds; "Records and levels"; S1: the proof command; O8: the old `bc_read_offload`); decisions: [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) (items 4-5: the YAML frame, the five gates), [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) (offload-only contracts), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 1, 11)
**Time estimate:** about 2-3 weeks of agent work

**What to build:** After the freeze, an agent (Codex, the default provider) drafts BC's output
relation and one offload-only rewrite contract for BC's forward pass, blind to the authors' DX100
code. Its inputs are the baseline `PBFS` and the intrinsic specification. The contract states a unit
postcondition (path counts per frontier edge over real arithmetic; depths, successor bits and the
next frontier as sets) and the shared-action kinds its code may use. Every drafted formal half passes
the five gates. The agent then builds the contract proof: the unit-postcondition lemmas on the
reference instance, the order-independence lemma, the lifting lemma, every formal-visible negative
control refuted, and the minimum bounds. Yan-Ru approves at promotion. Agent time and Yan-Ru's review
hours are recorded for RQ3. When this is done, BC candidate artifacts can get their automatic
per-candidate proofs (05, 07).

## Acceptance

- [ ] **Blind drafting:** every drafting call's provider workspace hash list shows no authors' DX100
      function and no file outside the inputs listed under Notes. The provider workspace and guard
      test refuses an input that names `PBFSMAA` or `BrandesMaa` (BC's DX100 driver; spec O2
      default).
- [ ] BC's output relation is recorded beside BC's correctness check. The contract and its formal
      halves pass `swdb validate` and `swdb build`.
- [ ] The contract is offload-only: it keeps its predecessor's thread split and loop order (`PBFS`
      itself, or the derived implementation the enabling contracts it names produce) and names any
      required enabling contracts in order (ID and version range). It states its unit relation, its
      bound dimensions (thread count among them) and, per interface array of the proof unit, the
      shared-action kinds it allows and whether its reads are history reads. Every kind is in the
      method version's fixed set. Sharing classes are not in the contract: they are per candidate
      artifact (map ticket 16 item 4).
- [ ] The unit postcondition is in the method's ACSL subset: for each edge from a frontier vertex
      to a vertex at the next depth, the target's path count gains the source's, over real
      arithmetic; depths, successor bits and the next frontier as sets (map ticket 24 item 2).
      Rounding appears as a platform-choice assumption entry. Every clause names a proof placement, and the proof setup check rejects a
      copy with one placement removed.
- [ ] Every drafted formal half passes the five gates: it parses and type-checks; the reference
      instance proves it; each formal-visible negative control is refuted by it; its runtime form
      passes every certify run of the reference instance; Yan-Ru approves it. Each rejection is
      recorded with its gate.
- [ ] `swdb prove` writes one proof record per contract-proof part, each with its content-hash set:
      the unit postcondition on the reference instance, with "the baseline meets it" and "two units
      that meet it satisfy the unit relation"; the order-independence lemma; the lifting lemma for
      BC; each formal-visible negative control refuted with the same harness and summaries; the
      minimum-bounds derivation for the single-thread and the multi-thread rung. No formal-visible
      control proves (one that does voids the contract proof, and the draft goes back).
- [ ] The lifting lemma is machine-checked (WP with replayed `Wp.induction` scripts; Rocq as the
      fallback). Until then it is an assumption entry of kind "written proof", and the report says
      so.
- [ ] Yan-Ru approves the contract, the output relation, the formal halves and the minimum bounds at
      promotion. The promotion review cites the proof record IDs.
- [ ] RQ3 inputs are recorded: agent wall time, provider calls and tokens per drafting and proof
      step; Yan-Ru's review hours; the share spent on BC's own logic definitions (path counts). The
      contract proof's final hint sets are kept so they serve as seeds.
- [ ] The contract-proof records that count come from mbit10, inside a socket lane.
- [ ] **Old `bc_read_offload` contract (spec O8):** this ticket records whether it is retired. Default:
      retired for the research questions; the blind contract replaces it there. No RQ subject is
      certified or proven against it. Yan-Ru confirms at promotion.

## Notes

- **Not in this ticket:** 01 — Correctness checks and certification drivers for PR and SSSP (BC's
  check exists); 03 — PR held-out contract and contract proof; 04 — SSSP held-out contract and
  contract proof; 05 — LLM candidate populations; 06 — Authors' code and seeded faults (the authors'
  `PBFSMAA` checked against this contract; seeded faults registered); 08 — RQ3: what a contract buys
  (analysis of the times recorded here).
- **Who proves:** once-proven parts may be human-assisted under the same hint rules, provenance
  "human", reviewed at promotion (map ticket 10 item 8). Per-candidate proofs stay automatic.
- **Soundness does not depend on who drafts:** a contract too weak to lift fails its lifting lemma
  (map ticket 18 item 5).
- Assumption (not decided in the map): the drafting agent also writes the contract's library code,
  so the reference instance is that code applied to `PBFS`. The glossary's other option, the first
  certified candidate artifact, would need 05's population, which waits for this ticket.
- Assumption (not decided in the map): besides `PBFS` and the intrinsic specification, the drafting
  workspace may show method-version material that is not the authors' code: the shared logic library
  with the sum library, library summaries, the proof semantics and the formal-half frame. Map ticket
  18 item 5 names only the first two.
- **Old `bc_read_offload` (spec O8):** it stays untouched before the freeze, so
  [proof-of-concept 31 — Five-gate drafting and the new bfs_read_offload version](../../probata-proof-of-concept-2026-10-13/issues/31-five-gate-drafting-and-read-offload-version.md)
  writes no BC counterpart. It is not a drafting input either: map ticket 18 item 5 says "the
  baseline and the intrinsic specification only". O8 leaves its fate to this ticket; the default
  (retired for the research questions, replaced there by the blind contract) applies until Yan-Ru
  rules.
- Assumption (not decided in the map): "retired" changes no record. Its existing versions and
  records stay as they are (proof records are immutable, ADR 0016); no RQ reads them.
- **Machines:** drafting provider calls run only on mbit10, inside a socket lane (ADR 0006; the Mac
  exception covers only the proof of concept, map ticket 13 item 13). Assumption (not decided in the
  map): verifier jobs outside provider calls may run on the Mac while iterating, under the Mac rules
  (one real verifier job at a time under an ~8 GB RSS watchdog; at least 50 GB free; LLVM 22 kept
  working). Only the mbit10 records count.
- **Risk:** a needed shared-action kind outside the fixed five bumps the method version. That makes
  a new method version, re-runs every held-out kernel, and both runs are reported (map ticket 18
  item 7). Stop and ask Yan-Ru before adding one.
- **Risk:** RQ3's bar (at most 3 weeks of agent time and 1 day of review per contract) may be missed.
  Report the miss; never trim the contract to meet it.
- BC is never cut (effort spec).
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.

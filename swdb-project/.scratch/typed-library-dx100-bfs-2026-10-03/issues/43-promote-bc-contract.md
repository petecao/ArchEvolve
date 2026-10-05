# 43 — Yan-Ru promotes the derived BC contract

Created: 2026-10-03
Updated: 2026-10-05 18:30 ET (addendum: attribution correction, stale hashed note)
**Type:** task
**Status:** resolved
**Blocked by:** 42
**Spec:** `../spec.md`

**What to build:** Yan-Ru reviews the derived BC contract and promotes it to shared before its first ArchEvolve-mode use.

## Acceptance

- [x] The contract is reviewed and promoted with `swdb promote`.
- [x] The certification and review records are committed (local commit; the main session pushes).

## Comments

- 2026-10-03 ET (BC-track agent, ticket 42): `contract.bc_read_offload` is certified (experimental) by `records/certifications/certification.1e389a959ffb4ff9bfdcf4cea9eace06.yaml`; review it and its patch `library/dx100/bc-forward-pass.patch` before `swdb promote`.

## Answer

Resolved 2026-10-03 23:31 ET. Agent-reviewed and promoted under Yan-Ru's 2026-10-03 delegation; revisable by Yan-Ru.

- **Review** (independent reviewer, not the ticket-42 author): [bc-contract-review-2026-10-03.md](../bc-contract-review-2026-10-03.md). Verdict PROMOTE, with no blocking or major finding and no change to the contract, the rewrite or the patch. The citation pin `867fac18…` equals the current BFS contract hash. The rewrite leaves only reads to DX100; the CPU keeps the CAS, queue push, successor bit and path-count update. BC-L1 holds, and control `stale_depth_hint` is rejected by BCVerifier at both tile sizes.
- **Re-run on the Mac:** certification `db570f7f…` ran in a records copy and was not committed. It matches the committed `certification.1e389a959ffb4ff9bfdcf4cea9eace06`: same contract hash, same tree `d6f86eb6…`, 10/10 cells and 18/18 controls rejected. `tests/test_bc_certification.py`: 11 passed.
- **Promotion:** `swdb promote contract.bc_read_offload` wrote `records/reviews/review.contract.bc_read_offload.30a3747420b3.yaml` for content `969276431d91…` with evidence `certification.1e389a959ffb4ff9bfdcf4cea9eace06`. State is now shared/certified, and `swdb validate` reports 489 valid records.
- **Follow-ups (minor):** add an L4 control that mutates the successor-bit edge index or the path-count source; clause `negative_control.check` names are not matched against the observed rejection reasons (inherited from the BFS contract).
- **Codex second opinion:** not obtained. `codex exec` cannot start inside the agent sandbox (Operation not permitted).

## Addendum 2026-10-05 18:30 ET (spec review C1, C20)

- **Attribution.** This review and promotion were performed by an agent under Yan-Ru's 2026-10-03 delegation,
  but `review.contract.bc_read_offload.30a3747420b3` names Yan-Ru as reviewer with provenance `human_report`.
  The record is unchanged; the attribution correction
  `review.correction.review.contract.bc_read_offload.30a3747420b3.11a0ec69d6c9` states the agent review, the
  delegation and the review document, and `swdb get contract.bc_read_offload` reports it. Listed in the spec's
  "Awaiting ratification" section.
- **Stale hashed text.** `library/rewrite_contracts/bc_read_offload.yaml` lines 304–305 (`specification_notes`)
  still say the contract is "experimental until Yan-Ru reviews it (ticket 43)". The note is part of the entry's
  hashed content, so editing it would change the content sha256 and void the certification and review. It is
  to be corrected at the next revision of the contract.


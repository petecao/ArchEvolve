# 19 — Submit a patch that ships the lowering header

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 11, 15
**Spec:** `../spec.md`

**What to build:** A rewrite proposal can carry a patch that adds the lowering header, and submit proves it uses certified, shared library entries and the library's exact header bytes.

## Acceptance

- [x] The rewrite-proposal message (new message version) gains an optional library section: the contract, every cited intrinsic, lowering and library-operation entry with its content sha256, and every shipped file with its lowering entry IDs.
- [x] ArchEvolve-mode submit refuses the proposal unless every cited entry is shared and certified or later for that sha256.
- [x] Submit rejects a header whose sha256 differs from its lowering entries' code-file sha256, and any other new file; the BFS source and the header are the editable files.
- [x] No rewrite provider runs for a patch payload; the producer names the authoring session (provenance kind agent_run).
- [x] Tests go through submit with contract fixtures (prior art: the proposal-submission tests).

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

Completed 2026-10-03 ET. Proposal message1.1 binds the contract, all dependency hashes and declared shipped lowering bytes. The public submit flow refuses stale, fixture-only, experimental, missing-dependency and header/new-file mismatches. The patch authoring session is retained without invoking a rewrite provider. Fifty public library/submit regressions pass, including exact reproduction of certified candidate tree `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`. Execution-envelope/review test doubles stay in isolated temporary stores; no real shared promotion is fabricated. Final Standards/Spec rechecks have no remaining actionable findings.

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.

# 15 — Derived tier and status, and swdb promote for library entries

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** Tier and status are derived from records, and `swdb promote` records Yan-Ru's review of a certified entry.

## Acceptance

- [x] `swdb promote ID` writes a review record (new kind, registered and documented) with reviewer, date, target ID and content sha256; the derived tier becomes shared; promotion never edits an entry, so the content sha256 is unchanged.
- [x] Promotion requires the entry to be certified: a lowering or library operation by its certification record; an intrinsic when all its lowerings are; a rewrite contract by a candidate-artifact certification record that carries its ID and content sha256.
- [x] Entry status (draft, certified, evaluated on target, refuted, inconclusive) is derived from certification records and from evaluations whose proposal cites the entry; `swdb get ENTRY_ID` prints the derived tier and status.
- [x] Experimental entries record an origin: an Extensa campaign ID, an Extensa source commit and path, or the intrinsic specification version for hand-built entries.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

Library status/tier derives from immutable certification, target execution and review records. Promotion pins current content without editing normative entries; changed content loses shared status. Native/fixture checks cannot establish accelerator-target execution.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.

Review correction, 2026-10-03 ET: Fixture receipts cannot derive certification or shared admission. Shared reviews require Yan-Ru Jhou (yanrujhou alias accepted). Completed missing target witnesses refute and cannot be masked by a successful run. State regressions: 31 passed; independent Standards replay confirms both original admission exploits are closed. See [code review](../code-review.md).

Dependency review correction, 2026-10-03 ET: receipts now bind the complete referenced normative entry closure before/after execution. Old unbound receipts remain history and grant no current dependency-bearing certification. All ten lowerings, the candidate and calibration have fresh passing bound receipts; see [promotion packet](../drafts/promotion-review.md). The 119 producer regressions plus exact public delivery reproduction pass (120 total); 35 library-state regressions and independent changed-reference/stale-contract custody rechecks also pass.

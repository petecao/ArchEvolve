# 09 — Library entry shapes and IDs, checked by swdb validate

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Library entries exist in their documented shapes with stable IDs, and `swdb validate` checks them.

## Acceptance

- [x] SWDB's library folder has one subfolder per entry kind; lowerings are grouped by hardware interface and version; entry IDs carry a kind prefix and never collide with record IDs.
- [x] Intrinsic, lowering, library-operation, rewrite-contract and clause shapes match the spec, including lowering code-file sha256, differential-test driver and input set, and rewrite-contract provenance.
- [x] The content sha256 covers normative content only; tier, status, certification results and applications are never stored in an entry.
- [x] Rewrite-contract validation checks the role-named pattern key, knob ranges tied to legality clauses, and negative controls covering the three mandatory kinds; clause validation requires a negative control exactly for the test-discharged modes.
- [x] `swdb validate` enforces these shapes and resolves every pinned reference against its sha256; grammar predicates are checked once ticket 10 lands.
- [x] Fixture entries cover valid and invalid cases; record and format gates stay green.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

Library validation enforces four entry kinds, ID/folder/interface constraints, clause discharge/control requirements, stated formal labels, grammar/reference pins, dependency references and knob legality. Malformed types fail without tracebacks.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.

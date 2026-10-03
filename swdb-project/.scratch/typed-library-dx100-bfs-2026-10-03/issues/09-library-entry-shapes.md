# 09 — Library entry shapes and IDs, checked by swdb validate

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Library entries exist in their documented shapes with stable IDs, and `swdb validate` checks them.

## Acceptance

- [ ] SWDB's library folder has one subfolder per entry kind; lowerings are grouped by hardware interface and version; entry IDs carry a kind prefix and never collide with record IDs.
- [ ] Intrinsic, lowering, library-operation, rewrite-contract and clause shapes match the spec, including lowering code-file sha256, differential-test driver and input set, and rewrite-contract provenance.
- [ ] The content sha256 covers normative content only; tier, status, certification results and applications are never stored in an entry.
- [ ] Rewrite-contract validation checks the role-named pattern key, knob ranges tied to legality clauses, and negative controls covering the three mandatory kinds; clause validation requires a negative control exactly for the test-discharged modes.
- [ ] `swdb validate` enforces these shapes and resolves every pinned reference against its sha256; grammar predicates are checked once ticket 10 lands.
- [ ] Fixture entries cover valid and invalid cases; record and format gates stay green.

## Comments

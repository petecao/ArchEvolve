# 15 — Derived tier and status, and swdb promote for library entries

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** Tier and status are derived from records, and `swdb promote` records Yan-Ru's review of a certified entry.

## Acceptance

- [ ] `swdb promote ID` writes a review record (new kind, registered and documented) with reviewer, date, target ID and content sha256; the derived tier becomes shared; promotion never edits an entry, so the content sha256 is unchanged.
- [ ] Promotion requires the entry to be certified: a lowering or library operation by its certification record; an intrinsic when all its lowerings are; a rewrite contract by a candidate-artifact certification record that carries its ID and content sha256.
- [ ] Entry status (draft, certified, evaluated on target, refuted, inconclusive) is derived from certification records and from evaluations whose proposal cites the entry; `swdb get ENTRY_ID` prints the derived tier and status.
- [ ] Experimental entries record an origin: an Extensa campaign ID, an Extensa source commit and path, or the intrinsic specification version for hand-built entries.

## Comments

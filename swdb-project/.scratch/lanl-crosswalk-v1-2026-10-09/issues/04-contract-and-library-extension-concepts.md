# 04 — Contract and library extension concepts

Created: 2026-10-09
**Type:** slice
**Status:** wontfix
**Blocked by:** 02
**Spec:** `../spec.md`

**What to build:** v1's separable extension lists what SWDB keeps outside LANL's schema: v0's 19
concepts, plus rewrite contracts, contract clauses (with discharge mode and negative control),
library operations, lowerings, and contract bindings to LANL `definitions`, `data_structures`,
kernels and the `kernel_variant_id` target. Each concept is `unverified` and names its source.
Can run in parallel with 03.

- [ ] v1's extension list contains all 19 v0 concepts
- [ ] v1 adds the contract and library concepts listed above, using GLOSSARY.md terms
- [ ] An extension concept claiming verified absence is refused
- [ ] An extension concept citing an undeclared source is refused
- [ ] The v1 document validates

## Comments

Superseded 2026-10-09 ET by [the LANL-shaped database spec](../../lanl-shaped-db-2026-10-09/spec.md): Yan-Ru wants the research database migrated to LANL's shape, not a mapping document.

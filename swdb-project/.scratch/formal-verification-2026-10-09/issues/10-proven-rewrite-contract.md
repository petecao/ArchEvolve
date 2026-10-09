# 10 — What does a proven rewrite contract prove once?

Created: 2026-10-09
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 03, 09
**Map:** `../map.md`

## Question

What does a proven rewrite contract prove once, and what is left to check for each candidate
artifact? Options include:

- proven building blocks: intrinsic lowerings and library operations proven against reference
  semantics, then reused as summaries in candidate proofs;
- a rewrite contract proven sound for all code matching its pattern key;
- both.

Name the per-instance check and say why it stays small enough to scale where Extensa's gates did
not.

## Comments

- 2026-10-09: input from 03: pure prove-once needs code that is an exact template instance,
  which LLM candidates are not. 03 recommends a staged hybrid and suggests rewording decision 2(a)
  in 01 to "contract parts proven once, plus a small per-instance proof". Decide here.
- 2026-10-09: input from 06: LPG (2026) could not prove its generalized rules for all bitwidths
  and fell back to per-width checks; consider applying the two proven levels to contracts too.

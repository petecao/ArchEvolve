# 09 — What does the "proven" level assert about a candidate artifact?

Created: 2026-10-09
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 03
**Map:** `../map.md`

## Question

What exactly does a proven level assert about a candidate artifact? Choose or combine:

- each clause's formal half holds;
- the candidate refines the baseline implementation modulo the kernel's correctness check
  (BFS parents may legitimately differ);
- the candidate meets the kernel's postcondition directly.

Also decide the proof unit (one `TDStep` call per BFS level, or the whole BFS) and which bounds a
proven-within-bounds verdict must declare.

## Comments

- 2026-10-09: input from 03: compare BFS outputs as visited set and per-level frontier sets plus
  parent validity (∀∃ refinement under OpenMP); list the assumption set every proven verdict
  depends on (assumed clauses L3 and L5, reference semantics).

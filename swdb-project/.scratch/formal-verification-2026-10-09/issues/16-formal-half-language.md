# 16 — What language do formal halves and the proof semantics share?

Created: 2026-10-13 14:19 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 11, 12
**Map:** `../map.md`

## Question

Which single source language do formal halves and the DX100 proof semantics use, so that one
source generates SAWScript specs, C call stubs and ACSL contracts (ticket 11, item 4)? Decide:

- the language: extend the ported Extensa grammar, adopt an existing one (such as an ACSL subset)
  as the source, or a small new one;
- how it states the proof semantics' ghost hazard state (producers, coverage, tile ownership) and
  per-element memory footprints (ticket 12, items 3-5);
- how legality clauses that are natural-language only today get formal halves (BFS read offload:
  L2, L4; L3 and L5 become proof-semantics rules per ticket 12, item 7);
- the declared C++ subset the C lowering accepts (ticket 11, item 3), since formal halves name its
  constructs;
- how each clause names its proof placement: once with a named entry, per candidate, or assumed
  (ticket 10, item 4).

The language must be general: the same source covers the BC, PR and SSSP contracts, not only BFS.

## Comments

- 2026-10-13 14:19 ET: graduated from the map's "Formal-half language" fog when ticket 12
  resolved. Inputs: 09 (formal halves per clause, unit relation), 10 (proof placement, summaries),
  11 (three generated forms from one source; only summary-generated `assume`s allowed), 12 (the
  proof semantics' rules, ghost hazard state and footprints come from the same source; the three
  forms must give the same verdict on every fixture scenario).
- 2026-10-13 15:22 ET: input from 13: proof hints are ACSL records on the C lowering, for WP only. The
  hint vocabulary bans recursive and inductive definitions (WP turns recursive ones into
  unchecked axioms; `../research/13-wp-hint-facts.md`); only the contract's logic library, reviewed
  at promotion, may hold them. Decide where that library lives and in which language.

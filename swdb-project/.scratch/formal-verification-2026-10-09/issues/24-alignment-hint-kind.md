# 24 — Should the proof-hint loop gain an alignment hint kind for direct unbounded proofs?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 21
**Map:** `../map.md`

## Question

A final candidate artifact whose rewrite chain fails to prove reaches at most proven within bounds,
because a direct relational proof needs an alignment that nothing supplies (17 item 4.4). Using
research 21, decide:

- whether 13's hint vocabulary gains an **alignment** kind (the proof-hint agent proposes which
  loops of the two programs run in lockstep; our product-program generator builds the product; WP
  proves it), or the gap stays and the paper states it as a limit;
- which checks make an LLM-proposed alignment safe (side conditions the generator or WP must prove;
  13's three checks);
- how it meets concurrency (a per-thread lockstep only, 17 item 4.3; for-all-exists pairs at
  N > 1), the "any input" note and the cost rule;
- the vocabulary version bump and what the evaluation measures (ticket 23).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Direct unbounded proofs without a template" fog.

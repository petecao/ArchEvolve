# 19 — How are a bounded verdict's bounds chosen, and when are they enough?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** claimed
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 19:47 ET)
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

A proven-within-bounds verdict records a value per bound dimension (09 item 11). Nothing yet says
which values the bounded verifier tries, or when a verdict's bounds are large enough to mean
something. Decide:

- **How bounds are chosen per contract:** fixed per contract; grown one step at a time until the
  budget ends (the largest proven bounds recorded); or derived from the contract, for example the
  smallest bounds at which every negative control a formal check can see is refuted (10 item 2).
- **Minimum bounds:** whether a contract declares bounds below which a bounded verdict does not
  give "proven within bounds", and how they are justified (a small-scope argument: which hazards
  and races need two lanes, two chunks, two commands in flight, two threads).
- **Encoding levers** that reach larger bounds, and which one the proof of concept tries first:
  summaries in place of the inlined strict-layer port (10 item 9's 2-lane hypothesis), per-call
  proof-semantics summaries (12, 16 item 10), symbolic sizes.
- **CIVL's team-size bound k** (starts at 3, 15 item 9) and input bounds under the same rule.
- **Comparing verdicts with different bounds** (input to ticket 25's ranking).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Scaling past one lane" fog. Inputs: 08 (crux-llvm
  on the array port proves 1 lane; 2 lanes did not finish in 15 minutes on the Mac); 09 item 11
  (bound dimensions per contract, threads always one; BFS read offload lists threads, vertices,
  edges, tile lanes, knob values, frontier size, unroll depth); 10 item 9 (pass bar: 2 lanes under
  15 minutes with summaries, else the claim drops to 1 lane); 11 item 2 (SAW 1.6 is the bounded
  verifier, summaries as `llvm_verify` overrides; first test: does SAW read clang 22 bitcode).
  Mac rule: one verifier job at a time under an ~8 GB RSS watchdog; larger sweeps on mbit10.

# 23 — Which baselines, ablations and metrics answer each research question, and how are runs repeated?

Created: 2026-10-13 17:02 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 18, 22
**Map:** `../map.md`

## Question

For each research question ticket 18 fixes, decide its baselines, ablations, metrics and run
protocol. Inputs already decided:

- **Baselines named so far:** testing-only certification; the verifier without hints at equal wall
  time (13 item 11); hints without contracts; prior repair loops (ticket 22).
- **Ablations:** seeds on and off (13 item 9, a paper feature); chained vs bundled (17 item 9);
  summaries vs inlined building blocks (10 item 9).
- **Metrics:** proof rate as a curve over the budget; time; hint rounds, provider calls and tokens;
  refutations and bugs by 13 item 10's three evidence steps; escape-hatch attempts by rule (13 item
  8); C-lowering subset coverage on campaign candidates, `std::vector` included (13 item 2, 16 item
  6); translator agreement on fixtures (16 item 1); drafts each formal-half gate rejects (16 item 5);
  ghost-capacity failures (16 item 10); bounds reached (ticket 19); human effort per contract (10
  item 8).
- **Method checks reported as evidence:** the semantics negative controls (12 item 9); the eight
  concurrency controls (15 item 12); CIVL and GenMC agreement (15 item 9); strict layer vs proof
  semantics on fixtures (12 item 8).
- **Concurrency:** the ladder per candidate artifact (SAW threads = 1, CIVL threads <= k, WP every
  N; 15 item 9); as written vs repaired at every N with performance compared (11 Q31, 15 item 10).
- **Protocol:** LLM nondeterminism (repeated runs, provider and model versions); budgets frozen
  after calibration (13 item 11); final runs on mbit10 inside socket lanes; Mac results labeled and
  never mixed with mbit10 timings (13 item 13).

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog (the baselines, metrics and
  per-ticket evaluation items).
- 2026-10-13 17:32 ET: input from 22 (resolved): five baselines that mirror published repair loops and
  the metrics that literature reports (`../research/22-cex-guided-llm-repair.md`, "Suggested
  baselines"); also decide whether a repair that reverts to the baseline implementation counts.
- 2026-10-13 19:48 ET: input from 18 (resolved): the five research questions, their starting pass bars, the population procedure (20 certified
  Codex candidates per contract, at most 60 proposals) and reference instances kept out of rates.

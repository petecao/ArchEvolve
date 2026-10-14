# Map: Extensa Probata proof of concept

Created: 2026-10-14 00:45 ET
Spec: [spec.md](spec.md). Tickets: [issues/](issues/). Integration branch: `probata-poc/integration`.

## Context pointers

One line per resolved ticket: number, one-line result, commit.
- 08 — Spike (d) sums over reals: **pass**. WP proves additivity, regrouping and permutation (17/17 lemmas, 11 replayed `Wp.induction`/`Wp.lemma` scripts) and the CSR pull-sum unit (61/61 goals, smoke tests passed); the seeded bug and `\false` are not proven. Findings: base −1 for `Wp.induction`, typing premises block lemma reuse, Z3 passes 8 GB on hard goals. Commit `ce2b436a` (branch `probata-poc/t08`).

# 16 — Extensa flow A: blind paired estimates

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 06, 09
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** Extensa campaigns (gem5 and native) estimate every candidate artifact and baseline before timing it (D26), record both in the campaign summary, and still select on timing only (D5).

## Acceptance

- [x] A fixture-target campaign test shows paired estimates in the summary.
- [x] Each estimate's time precedes its candidate's timing.
- [x] Selection is identical with and without paired estimates.
- [x] Paired estimates are tagged with the campaign and Extensa mode, and team protocols refuse them.


Claimed: 2026-10-06 21:21 ET. Own `codex/lanl-ticket16` worktree is based exactly
on integrated09 `4eaf95a95ed581f3b258d881a719a33f24c80ab2`. Public campaign,
freeze-protocol, estimate and validate commands are the agreed test seams.
All timing routes, exact input/backend binding and recursive team refusal are
required; unknown premises remain explicit and selection/plateau stays unchanged.

## Answer

Resolved: 2026-10-06 ET. The default enabled Extensa campaign stores immutable
`paired_estimate` records and a durable outcome-access ledger. Native A/A pilots
and both paired sides, gem5 shared baselines, primary and diagnostic companions,
ordinary runs, `--baselines-only` and resume all retain estimates before evaluator
entry. All known class contexts precede the artifact's first current-campaign
outcome. Exact artifact/build/input/policy aliases reuse the original forecast
while the boundary retains each actual candidate ID and execution context.

The portable estimator bundle and policy freeze before setup. Missing history or
changed policy refuses resume before provider/resumed decision access. Copied
summaries validate immutable hashes, UTC chronology and artifact/input/backend
correspondence. Direct and relayed paired-estimate dependencies are refused by
team protocols with ADR 0013; explicit Extensa dispatch remains functional.
Historical summaries without the optional ledger remain valid.

The final narrow public gate passed **12 tests in 575.80 s**. A deliberately slower
synthetic forecast (candidate10s versus baseline0.1s) leaves fixture timing gain
selection, completed iteration count and stop policy identical to pairing-disabled
control. The real adapters use the established fixture evaluator/host seam for
these checks; this proves orchestration, not application performance. After
merging integration `b3898b3`, the tested Python bundle is byte-identical and
**625 portable records validate**. All old record/library/app blobs are retained;
only eight prospectively registered workload records were added.

Real forecasts are explicitly **structural unknowns**, with null seconds and zero
agreement-eligible samples. Exact registered-SG whole-call counts, counted
backend/build/runtime correspondence, required mechanisms/composition and genuine
prospective freshness are not proved by existing observations. The functional
trial-lambda to MMIO complete-call bridge is separately named. Known prior
artifact access is disclosed without durations/ratios; a new ID never certifies
freshness. These unknowns and aliases cannot pad D30's twenty numerical pairs.
The parent owns fresh campaign population/statistical freeze and remote execution.

Evidence: [final public gate](../evidence/16-pairing-final-public-proof-20261006.json),
[integrated acceptance](../evidence/16-integrated-acceptance-proof-20261006.json),
[runbook](../evidence/16-blind-pairing-runbook.md),
[first adapter gate](../evidence/16-pairing-adapters-proof-20261006.json), and
[resume/chronology RED→GREEN](../evidence/16-pairing-integrity-proof-20261006.json).

# Map: Fine-grained estimate attribution and headroom

Created: 2026-10-11 14:51 ET. Updated: 2026-10-12 00:47 ET (final fixes merged into yanrujhou_main; follow-up moved to its own spec); 2026-10-12 00:38 ET (final review fixes F40–F47; current state
cut to checkpoint, blocker and next action); 2026-10-11 23:32 ET (all tickets resolved; code on
yanrujhou_main); 2026-10-11 15:17 ET (ticket 01 resolved; design committed); 2026-10-11 15:14 ET
(tickets re-cut into vertical slices 02–10, approved by Yan-Ru). Spec: [spec.md](spec.md).

## Current state

- **Checkpoint (2026-10-12 00:38 ET):** all tickets 01–10 resolved; spec closed. Final review fixes
  (F40–F47) are merged into `yanrujhou_main`.
- **Blocker:** none for this spec. The real split stays `split_unverified`: both t75 estimates are
  unknown, so the rewritten, untouched and unattributed shares are **unknown**
  ([ticket 03](issues/03-first-real-pair.md#answer) lists every missing piece).
- **Next action:** none for this spec; it is closed. The follow-up (extend the CPU description,
  then rerun 03 and 09 from the saved prospective requests) is its own spec, opened 2026-10-12
  00:42 ET: [cpu-description-t75-pricing-2026-10-12](../cpu-description-t75-pricing-2026-10-12/spec.md).

## Tickets

| # | Ticket | Status | Blocked by |
|---|---|---|---|
| [01](issues/01-review-and-commit-design.md) | Review and commit design | resolved ([answer](issues/01-review-and-commit-design.md#answer)) | — |
| [02](issues/02-tracer-worked-example.md) | First working version: the worked example end to end | resolved ([answer](issues/02-tracer-worked-example.md#answer)) | 01 |
| [03](issues/03-first-real-pair.md) | First real pair: t75 BFS attribution report | resolved, negative: both estimates unknown ([answer](issues/03-first-real-pair.md#answer)) | 02 |
| [04](issues/04-rewrite-site-edge-cases.md) | Rewrite-site edge cases | resolved ([answer](issues/04-rewrite-site-edge-cases.md#answer)) | 02 |
| [05](issues/05-library-intrinsic-offload-labels.md) | Library, intrinsic and offload labels | resolved ([answer](issues/05-library-intrinsic-offload-labels.md#answer)) | 02 |
| [06](issues/06-iteration-two-baselines.md) | Iteration 2: two baselines | resolved ([answer](issues/06-iteration-two-baselines.md#answer)) | 02 |
| [07](issues/07-resource-floor.md) | Resource floor headroom | resolved ([answer](issues/07-resource-floor.md#answer)) | 02 |
| [08](issues/08-catalog-bound-ranking.md) | Catalog bound and full ranking | resolved ([answer](issues/08-catalog-bound-ranking.md#answer)) | 07 |
| [09](issues/09-split-check.md) | Split check on the real pair | resolved, negative: `split_unverified`, no timing ([answer](issues/09-split-check.md#answer)) | 03 |
| [10](issues/10-site-finder-ordering.md) | Site finder uses the ranking | resolved ([answer](issues/10-site-finder-ordering.md#answer)) | 08, 09 |

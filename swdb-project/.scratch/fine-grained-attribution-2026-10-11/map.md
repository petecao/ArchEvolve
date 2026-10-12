# Map: Fine-grained estimate attribution and headroom

Created: 2026-10-11 14:51 ET. Updated: 2026-10-11 15:14 ET (tickets re-cut into vertical slices 02–10,
approved by Yan-Ru); 2026-10-11 23:32 ET (all tickets resolved; code on yanrujhou_main); 2026-10-11 15:17 ET (ticket 01 resolved; design committed). Spec: [spec.md](spec.md).

## Current state

- **Checkpoint (2026-10-11 23:32 ET):** all tickets 01–10 resolved. `swdb attribute` and the site-finder
  ordering are on `yanrujhou_main`; decisions F1–F39 in the spec. 03 and 09 closed negative.
- **Blocker:** the real split stays unverified until the CPU target description can price the t75
  characterizations (allowlist, uncosted calls, bandwidth rate; see ticket 03).
- **Next action (separate ticket, not opened):** extend the CPU description, then rerun 03 and 09 from the
  saved prospective requests.
- **Ticket 03 (2026-10-11 23:17 ET):** negative. Both t75 estimates (uniform22, T1) are unknown, so
  rewritten / untouched / unattributed shares are **unknown**. Main missing piece: the CPU
  description's characterization allowlist (risk B1), plus uncosted OpenMP/allocator/bulk/clock/
  iostream calls. Ticket 09 has no estimated shares: `split_unverified`. Kept on mbit10 for a
  rerun: `/data/yanruj/EvolveSWDB_runs/fga03-real-pair-20261011-a1/a2/{baseline,candidate}-counted`.

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

Frontier after 02: 03–07 can run in parallel. Estimated total: about 3 days of agent work.

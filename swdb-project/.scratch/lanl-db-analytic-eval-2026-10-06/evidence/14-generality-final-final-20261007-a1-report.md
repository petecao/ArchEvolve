# Nine-pair generality report

Updated: 2026-10-07 ET

Fresh final-bundle public estimates of nine exact counted scopes. No new measured performance, PR CPU service/error-band transfer, MAPLE accuracy, or fabricated accelerator observation.

| Kernel | Target | T | Whole-call seconds | Ratio | Scope |
|---|---|---:|---:|---:|---|
| bfs | dx100 | 4 | unknown | unknown | counted scope; see exact missing facts |
| bfs | cpu | 1 | 0.08459283293734217 | unknown | counted scope; see exact missing facts |
| bc | cpu | 1 | 0.64771215194357 | unknown | counted scope; see exact missing facts |
| pagerank | cpu | 1 | unknown | unknown | counted scope; see exact missing facts |
| pagerank | dx100 | 4 | unknown | unknown | counted scope; see exact missing facts |
| pagerank | MAPLE | 2 | unknown | unknown | estimate-only; no paired timing |
| bfs | MAPLE | 2 | unknown | unknown | estimate-only; no paired timing |
| bc | MAPLE | 2 | unknown | unknown | estimate-only; no paired timing |
| bc | dx100 | 4 | unknown | unknown | counted scope; see exact missing facts |

All per-region bounds, overheads, unknowns and exact trial inputs are in report.json. Aggregate regions are diagnostic medians.

Complete estimator bundle: `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`; estimator/mechanism diff is empty.

Jacobi has no CPU error-envelope transfer from the four admitted BF/BC characterizations. MAPLE has no accuracy-validation or paired-timing claim.

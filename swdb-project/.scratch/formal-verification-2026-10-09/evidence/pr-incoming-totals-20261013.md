# Evidence: the authors' DX100 PageRank keeps stale `incoming_totals`

Date: 2026-10-13 19:55 ET. Ticket: [20](../issues/20-dx100-pr-reset-check.md).
Host: the Mac (aarch64), Homebrew clang 22 + libomp. Functional model only; gem5 not run.

## Source under test

- `apps/dx100/benchmarks/gapbs/src/pr.cc`, SHA-256 `9379044698f6…727c0` (matches
  `apps/dx100/SHA256SUMS:39`). Snapshot of `arkhadem/DX100` at `e4fc4afd`, which is also upstream
  HEAD today (`git ls-remote`, 2026-10-13 19:53 ET).

## Build (throwaway, session scratchpad; nothing in the repo changed)

```bash
SRC=swdb-project/apps/dx100
FL="-std=c++11 -O2 -g -fopenmp -I$SRC/benchmarks/API -I$SRC/include \
    -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -DFUNC -DNUM_CORES=4"
clang++ $FL -DTILE_SIZE=16384      $SRC/benchmarks/gapbs/src/pr.cc -o pr_base   # PageRankPullGS
clang++ $FL -DMAA -DTILE_SIZE=$T   $SRC/benchmarks/gapbs/src/pr.cc -o pr_maa_$T # T = 4, 16, 16384
```

`-DFUNC` selects `MAA_functional.hpp`; `-DMAA` selects `PageRankPullMAA` (`pr.cc:314-319`).

## Runs (`-n 1 -v`, default tolerance 1e-4; `Total Error` is `PRVerifier`'s)

| Input | Iterations | Threads | Baseline | DX100 (any `TILE_SIZE`) |
|---|---|---|---|---|
| `-g 6` (Kronecker, 64 vertices) | 1 | 1, 4 | 0.19991 FAIL | 0.19991 FAIL (identical) |
| `-g 6` | 2 | 1, 4 | 0.05791 FAIL | 0.20509 FAIL |
| `-g 6` | 20 | 1, 4 | 0.00003 **PASS** | 17320.57 **FAIL** |
| `-g 10` (1024 vertices) | 1 | 4 | 0.28401 FAIL, top score 483:0.0397 | identical |
| `-g 10` | 20 | 4 | 0.00001 **PASS**, top 483:0.0200 | 15679.31 **FAIL**, top 483:2341.11 |
| `one.el` = edge `0 1` | 2 | 1 | 0.00000 **PASS**, scores 0.075, 0.13875 | 0.42500 **FAIL**, scores 0.075, 0.56375 |
| `star3.el` = `0-1`, `1-2` both ways | 2 | 1 | scores 0.3758, 0.3121, 0.3121 | 0.9425, 0.4538, 0.4538 (sum 1.85) |

Results are the same at 1 and 4 threads and at `TILE_SIZE` 4, 16, 16384.

## Reset probe (scratch copy only)

One line after `pr.cc:184`, `memset(incoming_totals, 0, num_nodes * sizeof(ScoreT));`, makes the
DX100 build match the baseline exactly on `-g 10` at 2 and 20 iterations, 1 and 4 threads (same
top-5 scores, same `Total Error`, PASS at 20). The missing reset is the whole difference.

## Authors' run settings (read from upstream `e4fc4afd`)

- `benchmarks/gapbs/run_pr.sh`: `./pr_maa -f ./serialized_graph_$1.sg -n 1 -v`: no `-i`.
- `scripts/sim.py:381,387,490,496` (gem5): `-f …serialized_graph_{size}.sg -l -n 1`: no `-i`, no `-v`.
- `pr.cc:304`: `CLPageRank cli(argc, argv, "pagerank", 1e-4, 1)`, so `max_iters` defaults to **1**.
  Upstream GAPBS defaults to 20 (the GAPBS copy at `MemAcc/external/benchmarks/gapbs/src/pr.cc:98`).

## Cleanup

Binaries and the partial upstream clone lived in the session scratchpad and were removed after
this note was written.

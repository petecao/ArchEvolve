# Weak paper sanity check

Updated: 2026-10-06 ET

This reported-paper comparison is a sanity check. It does not establish estimator accuracy.

| Kernel | Reported ratio | Estimated ratio | Paper input | Paper cores / estimated software threads | Paper configuration | Scope / state |
|---|---:|---:|---|---|---|---|
| BFS | 2.9 ± 0.1 (reported, approximate) | unknown | Uniform graphs, 2^20–2^22 nodes, average degree 15 | 4 / 4 | gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC | PDF page 9, Figure 9; inputs/configuration on page 8, Table 3 and Section 5; incomparable |
| BC | 2.2 ± 0.1 (reported, approximate) | unknown | Uniform graphs, 2^20–2^22 nodes, average degree 15 | 4 / unknown | gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC | PDF page 9, Figure 9; inputs/configuration on page 8, Table 3 and Section 5; incomparable |
| PageRank | 1.2 ± 0.1 (reported, approximate) | unknown | Uniform graphs, 2^20–2^22 nodes, average degree 15 | 4 / unknown | gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC | PDF page 9, Figure 9; inputs/configuration on page 8, Table 3 and Section 5; incomparable |

## BFS

Estimated ratio is unknown.

Paper scope: {"input": "Uniform graphs, 2^20–2^22 nodes, average degree 15", "cores": 4, "algorithm": "Bottom-up BFS", "configuration": "gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC"}.
Estimated software threads: 4.
- input: paper Uniform scale 20–22, average degree 15; estimate Kronecker scale 16, requested edge factor 16; exact registered input.
- algorithm/ROI: paper Bottom-up BFS; estimate Whole registered DOBFS read-offload trial lambda.
- configuration: paper Simulated four Skylake-like cores, baseline 10 MB LLC versus DX100 8 MB LLC; estimate Source/configuration-only FUNC identity; four requested software threads; hardware/runtime service and overlap unknown.

## BC

No estimate supplied.

Paper scope: {"input": "Uniform graphs, 2^20–2^22 nodes, average degree 15", "cores": 4, "algorithm": "GAPBS betweenness centrality", "configuration": "gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC"}.
Estimated software threads: unknown.

## PageRank

No estimate supplied.

Paper scope: {"input": "Uniform graphs, 2^20–2^22 nodes, average degree 15", "cores": 4, "algorithm": "GAPBS PageRank", "configuration": "gem5/Ramulator Skylake-like 3.2 GHz, 8-wide cores; baseline 10 MB LLC versus DX100 8 MB LLC"}.
Estimated software threads: unknown.

Source: [https://arxiv.org/pdf/2505.23073v2](https://arxiv.org/pdf/2505.23073v2); PDF SHA-256 `ec18bdc585f32e3da5c0fd467e686dd2137b3db88d4c327d510509213e7c44a3`.

Bar-reading uncertainty describes manual plot resolution, not a statistical interval.

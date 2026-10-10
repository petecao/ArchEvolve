Hi Peter,

Our 2026-10-03 first gem5 evaluation of your section 5 BFS read offload passed all four protected original-CSR verifiers and produced these official complete-call ROI results:

| Workload | Fresh scalar, simulated ms | Read-offload candidate, simulated ms | Point ratio |
|---|---:|---:|---:|
| uniform18 | 19.537464 | 12.210534 | 1.60005× |
| Kronecker18 | 18.426703 | 13.135990 | 1.40276× |

Each row is one frozen graph, source 0 and one deterministic replay. Setup is included in the complete-call ROI. These are simulated point ratios, with no statistical confidence across graphs or regional attribution.

The candidate enables MAA while the scalar baseline does not, so these results have joint hardware/software attribution. Both roles use the same CPU, clocks, memory and caches, including an 8MiB/16-way LLC. CPU CAS, the redundant parent store and queue updates remain in the candidate.

Both candidate runs passed the read-only and frontier checks. The separately labeled diagnostic companion exercised 14,546 negative-hint CAS failures with zero L3 violations. This is finite observed evidence; the design's L3/L5 assumptions are not general target guarantees.

Repository: petecao/ArchEvolve, branch yanrujhou_main, publication commit 0a495f4a972fe4a1eaa60fb5a1c148663ada9224.

- Result and evidence boundaries: [result summary](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/timed-a2-r1-result-summary.json#L162).
- uniform18 authoritative comparison: [uniform18 comparison](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/records/comparison_results/typed-library-bfs-gem5-20261003-a2.recovery.r1.w0.comparison.yaml#L33), canonical SHA ce26c3453508a6a2b86b5676127477706a31878d6aec516447e77ab546f178c5.
- Kronecker18 authoritative comparison: [Kronecker18 comparison](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/records/comparison_results/typed-library-bfs-gem5-20261003-a2.recovery.r1.w1.comparison.yaml#L33), canonical SHA 025d9294857b76ebfc2829b60ec5c909251d3b98d6281be9529765d8b82f0c5e.
- Immutable protocol, exact binary/model/input pins and audit: [frozen protocol](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/records/protocols/typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0.yaml#L21) and [independent audit](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/evaluation/timed-a2-r1-independent-audit.json#L5).

The original uniform physical runtime was 4c9bb01; recovery orchestration and the Kronecker runs used 6cfcd24, with the same prepared measured binaries and frozen protocol. The original 300-second aggregation timeout remains a failed receipt. Recovery reused the already passed uniform pair, used a reviewed 3,600-second postprocessing bound and ran only the missing Kronecker pair.

For context only, the retained authors' T17 comparison records report uniform18 3.08059× and Kronecker18 2.79898× under their accelerated implementation: [retained T17 uniform18](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/records/comparison_results/bfs-t17-handoff-20260929-a1.uniform18.yaml#L43) and [retained T17 Kronecker18](https://github.com/petecao/ArchEvolve/blob/0a495f4a972fe4a1eaa60fb5a1c148663ada9224/swdb-project/records/comparison_results/bfs-t17-handoff-20260929-a1.kronecker18.yaml#L43). Those results are separate from this new read-offload pair.

Retained raw traces and logs stay on mbit10. Newly successful checkpoint payloads were automatically pruned with exact path, hash, byte count and intent custody recorded in the repository. Failed checkpoints and receipts remain preserved. The team claim will cite both new comparisons after this message is verified sent.

Yan-Ru

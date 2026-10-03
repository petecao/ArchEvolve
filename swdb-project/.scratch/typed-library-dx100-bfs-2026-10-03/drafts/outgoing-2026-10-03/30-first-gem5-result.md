Hi Peter,

Our 2026-10-03 first gem5 evaluation of your section 5 BFS read offload passed all four protected original-CSR verifiers and produced these official complete-call ROI results:

| Workload | Fresh scalar, simulated ms | Read-offload candidate, simulated ms | Point ratio |
|---|---:|---:|---:|
| uniform18 | 19.537464 | 12.210534 | 1.60005× |
| Kronecker18 | 18.426703 | 13.135990 | 1.40276× |

Each row is one frozen graph, source 0 and one deterministic replay. Setup is included in the complete-call ROI. These are simulated point ratios, with no statistical confidence across graphs or regional attribution.

The candidate enables MAA while the scalar baseline does not, so these results have joint hardware/software attribution. Both roles use the same CPU, clocks, memory and caches, including an 8MiB/16-way LLC. CPU CAS, the redundant parent store and queue updates remain in the candidate.

Both candidate runs passed the read-only and frontier checks. The separately labeled diagnostic companion exercised 14,546 negative-hint CAS failures with zero L3 violations. This is finite observed evidence; the design's L3/L5 assumptions are not general target guarantees.

Repository: petecao/ArchEvolve, branch yanrujhou_main, publication commit PUBLICATION_COMMIT_PENDING.

- One-page result and evidence boundaries: SUMMARY_LINK_PENDING.
- uniform18 authoritative comparison: UNIFORM_COMPARISON_LINK_PENDING, canonical SHA ce26c3453508a6a2b86b5676127477706a31878d6aec516447e77ab546f178c5.
- Kronecker18 authoritative comparison: KRONECKER_COMPARISON_LINK_PENDING, canonical SHA 025d9294857b76ebfc2829b60ec5c909251d3b98d6281be9529765d8b82f0c5e.
- Immutable protocol, exact binary/model/input pins and audit: PROTOCOL_LINK_PENDING and AUDIT_LINK_PENDING.

The original uniform physical runtime was 4c9bb01; recovery orchestration and the Kronecker runs used 6cfcd24, with the same prepared measured binaries and frozen protocol. The original 300-second aggregation timeout remains a failed receipt. Recovery reused the already passed uniform pair, used a reviewed 3,600-second postprocessing bound and ran only the missing Kronecker pair.

For context only, the retained authors' T17 comparison records report uniform18 3.08059× and Kronecker18 2.79898× under their accelerated implementation: T17_UNIFORM_LINK_PENDING and T17_KRONECKER_LINK_PENDING. Those results are separate from this new read-offload pair.

Retained raw traces and logs stay on mbit10. Newly successful checkpoint payloads were automatically pruned with exact path, hash, byte count and intent custody recorded in the repository. Failed checkpoints and receipts remain preserved. The team claim will cite both new comparisons after this message is verified sent.

Yan-Ru

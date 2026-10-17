# First Peter v1.1 gem5 result

Updated: 2026-10-03 ET.

Protocol: `typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0`. Certified tree: `991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1`. L3 was observed for this diagnostic run; the design still assumes L3 and L5.

| Workload | Baseline verifier | Candidate verifier / read-only | Point ratio | Decision | Basis |
| --- | --- | --- | ---: | --- | --- |
| bfs-20260928-uniform18-s0.8c7e69dfa516e53c | passed | passed / observed | 1.60005 | gain | simulated |
| bfs-20260928-kronecker18-s0.cf4283236c5cb50c | passed | passed / observed | 1.40276 | gain | simulated |

Each row is one registered graph, source 0, and one deterministic replay. Ratios use fresh full-source scalar versus certified read-offload executions under this freeze. These are point ratios; no statistical confidence across graphs is claimed. Setup is included in the complete-call ROI. No region attribution was collected.

Authors' accelerated T17 protocol `bfs-t17-controlled-simulator-20260928.952dead4468b86d7` is context only; its numbers are not mixed into these ratios.

Operator draft for Yan-Ru to review and send. Raw output remains on mbit10; evaluations, aggregates, comparisons and custody records are authoritative.

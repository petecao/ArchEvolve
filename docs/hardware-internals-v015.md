# Internal mechanism handoff, revision 0.1.5

This local integration describes how the existing designs operate. It retains seven records, five design families and 39 operation records. The catalog has 84 located claims and 30 source records. It adds no accelerator implementation, hardware port ABI, operation support or measured performance.

| Record | What makes this implementation distinct | Boundary retained |
|---|---|---|
| DX100 paper | A tile exposes indirect work; physical row/line tables group requests, interleaved slice scans issue them, and a word list preserves original element positions. | Author edition and paper-specified behavior; exact reuse/fairness details remain unresolved. |
| DX100 public model | Finite producer-ready admission, physical grouping and duplicate fanout, fixed slice cycling, transport retry and response placement into original `TD[itr]`. | Public e4fc4af observations; not a paper-evaluation binding or private virtualization description. |
| Terminus with CAS | Partition exclusion separates conflicts; task dataflow overlaps work; a task ROB restores enqueue-order results; memory issue is separately resource-gated. | Partition execution, result ordering and CPU/global synchronization are different. |
| Terminus with deferred primitives | The same task framework defers atomic/hash work to CPU handlers while retaining partition ownership. | CPU execution is not engine CAS support; handoff costs and release protocol matter. |
| Prodigy | Demand triggers and prefetch fills traverse a software-provided dependency graph; PFHRs bound lookahead and speculative tracking. | Optional work may be dropped; it does not return required gather values. |
| SpZip Push | Ready DCL operators share fetch/decompression units; queues and markers deliver adjacency streams; delta decoding targets adjacency representation. | Shared destination atomics stay on the CPU; destination prefetch is a separate role. |
| MAPLE | Index chunks feed asynchronous requests; transaction slot identity permits out-of-order replies and ordered FIFO consumption. | Slot reservation, payload readiness, dequeue capacity release and CPU use have separate lifetimes. |

The detailed DX100 walk-through is in [dx100-internal-mechanisms.md](dx100-internal-mechanisms.md). MAPLE's paper and pinned-RTL boundaries remain in [maple-dx100-handoff.md](maple-dx100-handoff.md). Every integrated annotation carries claim references; the source/evidence closure is carried into the existing YAML, Markdown and Mermaid outputs. Diagrams of annotations do not establish wiring.

The Terminus/Prodigy/SpZip integration uses the proposal from local worker commit `1eb455567cb378acd18ae34885030e97ab9d1862`. Its base `ef155cd` was validated before integration: three primary PDF hashes and 188 query-equivalence checks passed. Eighteen source-located claims were integrated. The nineteenth, a PHI compression ablation, stays outside the Push catalog record and is not imported. The incorrect copied Terminus page-offset note on the SpZip source was corrected. The differently named local SpZip PDF is an ISCA 2021 manuscript; filename is not venue evidence.

Operations, types, input/output contracts, ordering/completion obligations, interfaces, legal requirements and parameter states remain unchanged from `ef155cd`. Reference capacities such as PFHR count, task ROB entries and shared queue storage are not new legal tuning ranges. Benefit hypotheses identify conditions and negative cases, not a winner or a speedup prediction.

This remains a prototype for Josh to inspect and match. Simulator realization needs target-specific implementation and validation. Current scope is published mechanisms plus separately labeled implementation observations, not a universal scaffold or executable scheduling specification. Independent review of the integration is pending at initial preparation.

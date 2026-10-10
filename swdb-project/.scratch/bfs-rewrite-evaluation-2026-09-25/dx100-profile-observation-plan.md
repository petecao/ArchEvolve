# One source-bound DX100 observation diagnostic

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

This bounded Ticket 14 check uses the existing tiny graph and unchanged scalar
source. It establishes collection independently of Ticket 13. It does not select
pilot workloads, run a rewrite candidate, test acceleration, or establish a gain.
No protocol is frozen and no previous evaluation is rewritten by this plan.

Use `scripts/dx100_profile_smoke.py` once, with a new identifier and empty external
output directory. Reuse candidate `bfs-dx100-compile-20260925-a1.candidate` and its
existing `.primary.build` and `.diagnostic.build` records. Exact binary hashes are
`bde41a46e02eed2f7f30b3d8abdd8157bbae0c425afa7476e07915a0c1b9b68d` and
`40a215eac6816704b92c0847e24c1aba7abf9c5699c23b2407e55b41b212f483`.
The evaluator rechecks the model, source, protected driver, and compiled artifacts.
No recompilation or source modification occurs.

Register the already retained a4 uniform scale-6, edge-factor-4 graph, source 0,
SHA `00d156b95baa9806c8e7623400e0347770942aee64dbed227309886ee605f78b`,
through the public workload interface. Its parsed loaded adjacency and realized
properties determine the workload identity; the generator description is marked
operator-declared. Use four guest cores and the declared BASE configuration with
8 MiB/16-way LLC and the existing CPU/cache/memory settings. Both artifacts retain
the complete-call ROI. The diagnostic adds explicit source-scope guards; its
durations cannot replace the primary BFS time.

| Bound | Primary | Separate diagnostic |
|---|---:|---:|
| Attempts | 1 | 1 |
| New checkpoint ceiling | 300 s | 300 s |
| Restored run ceiling | 750 s | 270 s |
| Public evaluation total | 1,100 s | 600 s |
| Process-group RSS | 48 GiB | 48 GiB |
| Retained output | 2 GiB | 2 GiB |
| Post-ROI continuation | 10^10 ticks | 10^10 ticks |

The separate 48 GiB observation budget is justified by a6's measured 32.158 GiB
peak and the prior 32 GiB statistics-dump failure. This is not a blanket revision
of the pilot's 32 GiB limit. The cases run sequentially in one verified socket lane,
under a 2,400-second outer timeout and 4 GiB batch output limit. The driver reserves
30 seconds for owned-process cleanup. No failed treatment is retried.

Before dispatch, verify both socket leases and the legacy lease, current lane
helper, owned jobs, exact checkout, input hashes, and free space. Require the
existing conservative 52 GiB selected-node / 64 GiB global capacity gates both
before and inside the lane. Stop on refusal; do not lower the gates or disturb
other users. Retain 30 GiB raw-volume and 10 GiB source-volume free-space reserves.

The driver preserves each exact execution outcome and correctness verdict. It
may collect a complete sealed observation despite a later unverified verdict;
missing seal, configuration, log, counters, source association, or memory metrics
still fail collection. Fresh public retrieval must expose those distinctions.
An observation-complete package is not a successfully verified implementation.
Keep this graph outside the scale-14/18 calibration and final coverage matrix.

The retained discovery explicitly leaves the SIMD loop at line 189 in the unused
`TDStepMAA` helper unresolved. Preserve that limitation; do not claim complete
instrumentation of every lexical region. The collector may be `partial` while
the package has complete identified primary timing, supported function/loop
timings, and memory evidence. Package completeness remains the existing public
contract's decision, with all unsupported/unobserved regions and reasons retained.

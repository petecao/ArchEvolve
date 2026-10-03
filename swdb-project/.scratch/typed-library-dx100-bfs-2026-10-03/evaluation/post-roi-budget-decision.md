# Post-ROI verification budget correction

Updated: 2026-10-03 12:13 ET.

The first a1 timed sample was **uniform18 scalar baseline**. Its post-seal verifier stopped at the planner’s `10**10` tick cap before a protected structural verdict, returned-parent result or exit witness. The published outcome is `missing_observation` with correctness unverified; no candidate sample or ratio exists. Peak sampled simulation RSS was 30.60 GiB, within the unchanged 36 GiB budget. All ten failed-checkpoint files (73,279,622 bytes) and raw evidence remain remote. [Failure summary](timed-a1-failure-summary.json).

Restore the established T17 v2 `10**14` post-seal ceiling for every execution role. Retained completed baseline checks alone required 57/84 billion ticks; this decision does not use a candidate gain. Both independent reviews validate the metadata. Mac raw availability remains `remote_unverified`; no new historical raw audit is claimed.

| Role | Workload | Mode | Requested ceiling | Observed continuation ticks |
|---|---|---|---:|---:|
| baseline | uniform18 | primary | 100,000,000,000,000 | 84,000,000,000 |
| baseline | uniform18 | diagnostic | 100,000,000,000,000 | 84,000,000,000 |
| baseline | kronecker18 | primary | 100,000,000,000,000 | 57,000,000,000 |
| baseline | kronecker18 | diagnostic | 100,000,000,000,000 | 58,000,000,000 |
| candidate | uniform18 | primary | 100,000,000,000,000 | 86,000,000,000 |
| candidate | uniform18 | diagnostic | 100,000,000,000,000 | 86,000,000,000 |
| candidate | kronecker18 | primary | 100,000,000,000,000 | 59,000,000,000 |
| candidate | kronecker18 | diagnostic | 100,000,000,000,000 | 59,000,000,000 |

The cap applies only after ROI sealing. The strict v2 checker, authoritative completion witness, sealed ROI, CPU model, compiler/flags, source, 16GB guest/MMIO and finite read-only/frontier checks remain unchanged. Independent wall-time bounds remain timed 9,000s total / 7,140s run / 1,800s checkpoint, and companion 3,600s total / 2,940s run / 600s checkpoint. Resource budgets stay 36 GiB memory and 8 GiB storage. No post-ROI CPU substitution is introduced.

Four new regressions fail under the original cap (4 failed / 6 passed) and all 168 affected cases pass after correction. Three comparisons against the actual a1 requests prove only `max_ticks` changed. The full identity ledger is 3,756 cases = 3,720 pass + 36 skip, zero unresolved. Both final Standards and Spec reviews pass against fixed source `982d19b23eb0303ecacc938c5334e6479b861197`. [Decision and exact receipts](post-roi-budget-decision.json).

Use fresh attempt **typed-library-bfs-gem5-20261003-a2** with new preparation, protocol and actual binary pins, then same-source companions and all four timed samples. Each rebuilt binary must bind its actual bytes; build-path differences can affect hashes. The candidate primary binary validated by companions must be the exact one timed. Failed a1 IDs, protocol and evidence remain unchanged. This decision and passing local tests do not establish a successful a2 execution or a performance result.

Root’s independent 12:10 ET check confirms source8b68b2f, all socket/legacy leases kernel-free and metadata-released, no owned simulator/driver/wrapper, and approximately43GiB/74GiB disk free before Git synchronization. Fresh selected-node memory/disk/load admission remains mandatory per stage.

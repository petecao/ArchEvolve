# Fresh lease-recovery Linux proof group

Prepared 2026-09-27 ET. Not dispatchable until the exact runtime Git commit, complete Git-derived manifest, operator/configuration hashes, refreshed helper comparison and free lane are sealed.

Fixed ID: `bfs-supervision-lease-recovery-linux-20260927-a1`. Standard fixture IDs are `bfs-simulator-owned-linux-20260927-a6` and `bfs-simulator-interruption-linux-20260927-a6`. No old group roots or receipts are reused.

The single original 600-second group clock and 2-GiB allocation cover all five roots: supplement dispatch, two standard raw roots and their dispatch roots. The private supplement runs the retained 42 cases plus nine actual external-lease flock cases (51 total), followed by five owned-cleanup and two interruption cases. Each stage has 90 seconds including its shared 30-second cleanup; each independent terminal audit has 60 seconds. The three stage/audit pairs fit within 450 seconds, leaving at most 150 seconds for original preflight/final process closure/storage recount and publication. No retries, replenishment or extra allowance. Both prospective T15/T16 plans charge the full reserved 600 seconds/2 GiB regardless of faster completion.

The new behavior requires actual Linux proof from this exact new runtime. Historical 8cb/6a consumer exceptions cannot qualify it. The old immutable group and failures stay unchanged for historical accounting. This group establishes contract behavior only, not simulator correctness, accelerator execution, performance or acceptance.

The new operator is a fixed-ID copy of the reviewed original group flow, with `--lease-recovery` selecting the new private supplement and new prospective plan. Complete stdlib-only Git inventory verification still precedes runtime imports. Existing ownership/auditor primitives supply child supervision and post-exit process/lease verification. `launch.sh` establishes the one original outer clock; it requires Git-materialized, reviewed operator/configuration files and hashes.

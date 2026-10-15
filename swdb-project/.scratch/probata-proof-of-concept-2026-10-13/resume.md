# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Runtime checkpoint: integration `0999dfb7` on `codex/probata-poc-integration`,
based on `yanrujhou_main` at `150930b4`. Includes lowerer 9's integer model-result
normalization, the checked private-vector proof view and named DX100 initialization.
Focused merged-source validation at isolated `7437f3b9`:94 native/lowering and 69
setup cases pass across retained runs; sandbox-only failures were reproduced and
replayed with watchdog permissions. Details remain in ticket24's evidence.
User approval covers scoped implementation, commits, pushes, remote source sync,
two mbit10 CPU lanes and BFS proof-workspace export through Codex/OpenAI.

| Ticket | Current work | Evidence or next action |
|---|---|---|
| 07 | Counted run16 started 06:09 ET, frozen `6acfbe4e` | Fresh hints plus processed-frontier/CSR induction guidance; output `/private/tmp/probata-t07-20261015-run16/`. Run 15 ended not proven with 1 unit and 24 hint obligations. Audit found missing induction information, no concrete false hint. |
| 24 | Focused model-result fix integrated | Four public positive callers and missing-input negative pass; combined-source full constructs await node 1 after pointer policy finalizes. |
| 25 | Nine focused private-vector ownership controls pass across two reports | Safe: 122/122 goals, stale alias sole liveness failure,7 protocol refusals. Nonallocating member/model public acceptance continues; general vector lifetime acceptance remains open. |
| 27 | Exact safe three-read initializedness diagnostic | Shared static rows retain checked caller-input requirements. Quantifier exposure remains incomplete; finite specialization of frozen geometry is planned without new premises. Capacity and remote acceptance remain pending. |
| 36 | Pointer formation and typed-origin audit | Legal/out-of-range row controls and 5 final pointer/model controls pass on staged source. Checking arbitrary primitive input pointer subobject provenance before pinning draft 3; allocation-block bounds alone are insufficient. |
| 41 | Resolved | Approved reconstruction `e23f3715…`, protected/class/ownership lifetime premises and exact guard controls. |
| 42 | Resolved | Production Rocq composition theorem: 209 Qed, closed context, actual record validate/build; no DX100 reduction claim. |

Current count: **32 of 63 resolved**, five claimed. Drafts 1 and 2 are immutable;
reviewed combined identities will create draft 3. No current pointer source or
full construct acceptance is inferred from older checkpoints. Ticket43 remains
blocked by 29; 28 remains unclaimed until 27 closes. No held-out kernels or method
freeze before their dependencies resolve.

Next: finish conservative admission and actual acceptance, merge verified changes,
recompute the ticket frontier and use the two leased remote socket lanes.

## Host coordination

Live preflight at 2026-10-15 06:05 ET found both socket leases and the legacy lease released,
load 0.02/0.06/0.01, about 117 GiB available RAM, 21 GiB free on `/data1` and 97 GiB on
`/data`. The process check found no active proof jobs. Evaluation source remains clean
detached `dd975e72`; the installed wrapper matches its tracked remote blob. These are dispatch observations, not permanent availability claims. New output
uses `/data/yanruj/EvolveSWDB_runs/`; source uses Git worktrees under `/data1/yanruj/`.
The current lane wrapper is in `/data1/yanruj/Memacc-evolveswdb-lane`, verified against
`origin/yanrujhou_main`. The older `/data1/yanruj/Memacc` checkout lacks it and has unrelated
changes; leave that checkout untouched. GPU NVML reports a driver/library mismatch;
CPU proofs do not require the GPU.

Node 1 baseline run: `/data/yanruj/EvolveSWDB_runs/probata-t24-baseline-20261015`, source
`150930b4`, lease generation 591. It exited after fixture setup errors, before proving
the construct groups. The first error is missing `<cstddef>`, not a proof failure.
Output budget was 6 GiB; measured output was 2.4 MiB. Retain original logs and reports
until the diagnosis and acceptance readers finish.

The baseline's isolated reruns diagnosed both the missing C++ header path and linker
path. `r4` supplies `SWDB_CLANG` with GCC 13, `CPLUS_INCLUDE_PATH` and `LIBRARY_PATH`;
the isolated native C++ versus C class fixture passes before the full WP module starts.
These generic subset fixtures use libstdc++; they are not vector-model evidence.
Vector-model admission now requires matching libc++ 22.1.8. The remote LLVM distribution
has matching headers and libraries, but its model jobs need an explicit libc++ compiler
and runtime-library configuration. No cross-library model agreement is inferred. The final
baseline `r4` completed with 17 passed and the known use-after-delete expected failure;
the original report and logs occupy 9.7 MiB and remain on the host.

The 30-minute progress heartbeat is `probata-implementation-progress`; its reports do
not substitute for reading incremental run artifacts.

## Validation and progress reporting

The 2026-10-15 06:00 ET report covered every active ticket and both lanes; next report
is due around 06:30 ET. Run 15 ended not proven after 52.75 counted minutes with1unit
and 24 hint obligations open; no final proof replay ran. Run 16 is active on fresh
hints. Both remote lanes await the final combined source and method checkpoint.

The early structural run disabled clang as well as WP/CBMC; four formal-frame assertions
therefore failed for the wrong tool configuration. One isolated failure passes with clang
restored, and the affected module gives 64 passed, 4 skipped (WP still disabled). A separate
checkout-integrity failure observed the coordinator's Rocq merge, not a test mutation.
That exact test passes in `/private/tmp/probata-validation-20261015` at frozen `3f559789`.
Future validation runs must use an unchanged source worktree. Logs and incremental reports:
`/private/tmp/probata-integration-20261015/`. No whole-catalog validation is claimed.

The early structural run completed: 424 passed, 31 skipped, 6 failed and 1 teardown error
in 1441.73 s. Four failures are the corrected clang configuration above; the two format
failures are covered by ticket 36's passing documentation checks. The teardown error is
the independently passing frozen-worktree replay above. This is diagnostic evidence,
not a clean final integrated-source suite.


Live host check 2026-10-15 03:25 ET: node 0 generation 548, node 1 generation 594
and legacy generation 77 all released; load 0.02/0.38/0.80, `/data1` 21 GiB free,
`/data` 97 GiB free. Root remote checkout is `yanrujhou_main` at `680298a3`;
it is not the frozen evaluation worktree. Both evaluation lanes await final source.
The frozen policy worktree's representative existing safe-fill and smoke-pair WP
regressions also passed: 2 tests, 139.41 s, `/private/tmp/probata-init-wp-regression.jsonl`.

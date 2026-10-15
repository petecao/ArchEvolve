# Probata implementation resumption

Updated: 2026-10-15 ET.

## Current state

Updated: 2026-10-15 09:15 ET. Pushed clean integration is `bfc5e4f6` on
`codex/probata-poc-integration`, based on `yanrujhou_main` at `150930b4`.
It includes primitive checked CBMC windows, exact all-DX imported-call binding,
strict smoke-preserving literal-offset normalization, checked Crux source admission
on both forms, and the closed current-owner `at()`/immediate `data()` views.
Historical actual evidence retains each original source/method pin; later merges
and stand-in checks do not upgrade that proof evidence.

A real public CBMC counterexample on integration `44d50f7e` confirmed that a
changed same-name callee could borrow a summary proved on different code. The
root branch `codex/probata-construct-init` is implementing fresh complete callee
closure equality, current proof/method/evidence binding, checked finite call bounds
and exact pointer-buffer alignment, plus independent prelaunch replay. The changed
callee now refuses before launch; matching scalar and array positives passed early
controls. The final combined CBMC/WP batch is active, so this fix is not yet merged
or accepted. Old array-summary fixtures used an n<=2 summary for n<=3 callers;
positive fixtures now prove the matching bound and a separate negative retains
that mismatch. No domain limitation is silently promoted to a general theorem.

| Ticket | Current evidence | Next action |
|---|---|---|
| 07 | Run17 ended unproven: 2 unit and 17 hint goals; offline audit shows snapshots were attempted then reverted | Prepare method18's smaller bridges and a prospective, explicitly named search/source revision; no run18 launched |
| 24 | Earlier 132-case remote native checkpoint; current-policy full constructs remain open | Finish generic summary binding and replay the combined construct groups |
| 25 | Qualified at pair passed; current data safe/stale pair2 passing tests at `67dfd7a8`, with sole stale goal alias_live_after | Complete wider model/member lifetime acceptance; standalone opaque models stay closed |
| 27 | Direct DX final 9 hardening checks and 2 safe replays pass at `f83fdf04`; helper component reviewed | Wire independently checked contextual helper view into WP, then actual combined acceptance |
| 36 | Primitive remote CBMC 5 passing checks at `07a9a299`; 88 Crux and scripted setup controls pass on root follow-up | Complete source/proof-bound summary eligibility and combined checker replay |
| 41 /42 | Resolved; approved strengthened composition statement, production Rocq 209 Qed | Preserve exact evidence boundary; no DX reduction claim |

**32 of 63 resolved; five claimed.** Drafts 1/2 are immutable; draft 3 is not created.
Ticket 28 remains unclaimed until 27 closes; 43 remains blocked by 29. Held-out kernels
and method freeze remain gated by their dependencies. User authorization includes
implementation, commits/pushes, source sync, two remote lanes and the scoped BFS
workspace export through Codex/OpenAI.

Next: integrate the checked helper and summary fixes, replay combined-source
acceptance, recompute the ticket frontier, then create a new method draft after
runtime identities settle. The 09:05 ET status report was delivered; next due 09:35 ET.

## Host coordination

Latest live readback: 2026-10-15 09:00 ET. Node 0 generation 554, node 1 generation 595
and legacy generation 77 were released; load 0.00/0.02/0.14, 21 GiB free on `/data1`
and 97 GiB on `/data`. Evaluation checkout remained clean detached `07a9a299`.
No proof process appeared in the top CPU inventory. Recheck all leases and load
before either lane is used; this is a timestamped observation.

Latest readback at 2026-10-15 08:38 ET found both socket leases and the legacy lease
released, with load 0.38/0.68/0.61, 21 GiB free on `/data1` and 97 GiB on `/data`.
The frozen detached evaluation checkout is `07a9a299`. Corrected bounded controls
ran on node 0 generation 554 from 08:33:38 to 08:36:48 ET: five passed in 189.77
seconds, wrapper exit 0. Actual proof records show one positive, two intended
refutations replayed on source C++, and one prelaunch mathematical-intermediate
refusal; the fifth test covers source-name collision. All referenced artifact
hashes match. [Bounded evidence](evidence/bounded-entry-windows-mbit10-20261015.json).
Earlier `a3bd6c9a`/`ca6d7ae5` bounded checkpoints preceded the source-name fix;
the corrected-source replay is the acceptance checkpoint.

Earlier `b876dcb3` proof jobs started
at 07:49:32 ET: entry windows on node 0 generation 551 passed 15 tests in 616.97
seconds and released at 07:59:50 ET; owners on node 1 generation 595 passed 16 tests
in 429.57 seconds and released at 07:56:43 ET. Both wrappers exited 0. Compact entry
record audit: [entry-windows-mbit10-20261015.json](evidence/entry-windows-mbit10-20261015.json).
Raw output remains on mbit10; coordinator and ticket acceptance readers still need it.
This snapshot is not a promise of later lane availability; recheck before dispatch.

Earlier native preflight at 2026-10-15 07:14 ET found both socket leases and the legacy lease released,
load 0.11/0.29/0.19, 21 GiB free on `/data1` and 97 GiB on `/data`. The wrapper was fetched
and matched blob `261e7e04a64474020c6d2fd288bee9bab8dd1f5d`. Frozen native replay
`aa7be61c` then passed 132 checks in 69.36 seconds on node 0, generation 550, ending at 07:16 ET.
Its lease is released; node 1 generation 594 and legacy generation 77 remain released in that snapshot.
That native replay used a clean detached checkout at `aa7be61c`; it was subsequently
advanced to `b876dcb3` only after the job ended. The original replay used GNU headers and failed 21 of 133 checks;
matching libc++ 22.1.8 plus GCC 13 driver wrappers fixes configuration; the corrected
raw-endpoint expectation accounts for the remaining test. The corrected native shard
excludes the accidentally selected CBMC query. See ticket 24's native evidence;
this does not establish final proof acceptance. These are dispatch observations,
not permanent availability claims. New output
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

The 2026-10-15 08:35 ET report covered every active ticket and both lanes; next report
is due around 09:05 ET. Run 15 ended not proven after 52.75 counted minutes with 1 unit
and 24 hint obligations open; no final proof replay ran. Run 16 also ended unproven
with 4 unit and 22 hint goals; its final offline audit is recorded. Run 17 finished
at 08:25:15 ET with 2 unit and 17 hint obligations open; no final proof replay ran.
Both remote proof shards completed at `b876dcb3`; the next combined DX/helper/model
checkpoint and final method identities remain pending. The 132-case native checkpoint
passed separately.

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


Historical host snapshot 2026-10-15 03:25 ET: node 0 generation 548, node 1 generation 594
and legacy generation 77 all released; load 0.02/0.38/0.80, `/data1` 21 GiB free,
`/data` 97 GiB free. Root remote checkout is `yanrujhou_main` at `680298a3`;
it is not the frozen evaluation worktree. Both evaluation lanes await final source.
The frozen policy worktree's representative existing safe-fill and smoke-pair WP
regressions also passed: 2 tests, 139.41 s, `/private/tmp/probata-init-wp-regression.jsonl`.

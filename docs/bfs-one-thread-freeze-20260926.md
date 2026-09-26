# Explicit publication from the requested-one-thread calibration

Created: 2026-09-26 ET.

This opt-in route prepares a native protocol from the fixed
`bfs-native-one-thread-pilot-20260926-a1` study. It does not run a measurement,
provider, candidate assessment, repair, or old pilot preparation. The original
serial and four-thread paired publisher routes retain their existing behavior.
The running collector and its prospective plan are unchanged.

The admitted collector commit is exactly
`319645eab0a25c815fa03fe1c372d32b4ba45d10`. Qualification requires the entire
client to finish successfully, all four primary A/A controls to qualify, and all
four fresh one-thread diagnostic packages to complete. A terminal but failed or
`primary_unqualified` client cannot produce a publishable review. Its observed
failure remains evidence, without a retry or threshold adjustment.

## Selection and commands

Use the existing `scripts/bfs_freeze_pilot.py` interface. The top-level selection
keeps `mode: native`, a fresh protocol name/version, the two new source-specific
`packages`, `maximum_relative_spread: 0.10`, the actual spread justification,
`size_selection`, and the four-cell historical `repeatability` mapping. Add the
following explicit selector, and omit the top-level `paired_calibration` key:

```json
{
  "one_thread_calibration": {
    "run_id": "bfs-native-one-thread-pilot-20260926-a1",
    "code_commit": "319645eab0a25c815fa03fe1c372d32b4ba45d10",
    "collector_checkout": "/absolute/pristine/original/collector/checkout",
    "driver_receipt": {"path": "/absolute/final/driver.json", "sha256": "ACTUAL_SHA256"},
    "terminal_receipt": {"path": "/absolute/terminal-validation.json", "sha256": "ACTUAL_SHA256"},
    "packages": ["DX_UNIFORM_FRESH_ID", "UPSTREAM_UNIFORM_FRESH_ID", "DX_KRONECKER_FRESH_ID", "UPSTREAM_KRONECKER_FRESH_ID"],
    "historical_paired_calibration": {
      "pairs": ["FOUR_ORIGINAL_PAIR_IDS_IN_FIXED_ORDER"],
      "driver_receipt": {"path": "/absolute/original/paired/driver.json", "sha256": "ACTUAL_SHA256"},
      "historical_packages": ["FOUR_ORIGINAL_PACKAGE_IDS_IN_FIXED_ORDER"]
    }
  }
}
```

Uppercase values and the checkout path are placeholders, not accepted evidence.
Each historical array must actually contain all four fixed IDs. Fresh package
IDs are the immutable content-addressed IDs returned by the current client;
requested package prefixes cannot substitute. The top-level two packages must
be the selected implementation's uniform and Kronecker members of that fresh
four-package list.

After the actual artifacts exist, preparation and publication use separate new
output directories:

```sh
python3 scripts/bfs_freeze_pilot.py prepare SELECTION.json --records RECORDS --output NEW_REVIEW_DIRECTORY
python3 scripts/bfs_freeze_pilot.py publish NEW_REVIEW_DIRECTORY/review.json --records RECORDS --output NEW_PUBLICATION_DIRECTORY
```

Preparation produces a review, not a frozen record. Publication repeats admission
and requires exact agreement with the reviewed content before invoking the public
`freeze-protocol` command. Missing artifacts, changed identities, unsupported
runtime inputs, or failed shared gates prevent publication.

## Current evidence admission

`scripts/bfs_one_thread_calibration.py` checks the original collector checkout's
exact HEAD, complete tracked runtime inventory, absence of untracked runtime
shadowing, plan bytes, and Python executable/version against the measured
receipt. It then runs only that pinned collector's unchanged
`validate_driver_receipt` reader in a separate process. Its 900-second allowance
includes runtime preflight, with at most 30 additional seconds for owned process
group cleanup. No call to the collector's `main`, evaluator, or provider occurs.
Reader results retain deterministic content hashes so independent prepare and
publish checks can agree exactly. A timeout fails admission; it is not permission
to repeat or extend the measured study.
Shutdown signals are restricted to the still-owned, unreaped reader session.
An unconditional direct-child wait spends the same remaining cleanup deadline,
even when signaling fails; the original readback failure remains the primary
exception. The final output parsing and hashes are included in the shared
900-plus-30-second deadline. An already reaped leader receives no group signal.

The pinned reader reopens the complete four-cell grid, every parent/correctness
check and source/graph/build identity, exact public requests/results, declared
compiler and resolved compiler bytes, capacity and resource observations, phase
and shared clocks, cleanup, and every new diagnostic/public package chain.
The publisher additionally binds the exact pair/member/package record digests
and recomputes both A/A label directions using the fixed policy. All eight
members must have the strict requested runtime map: `OMP_NUM_THREADS=1`,
`OMP_DYNAMIC=FALSE`, `OMP_PROC_BIND=close`, `OMP_PLACES=cores`, and explicit null
for `OMP_THREAD_LIMIT`, `OMP_WAIT_POLICY`, `GOMP_SPINCOUNT`, and
`GOMP_CPU_AFFINITY`. Null means requested unset. These observations do not prove
actual worker team size, scheduling, or placement.

An independent whole-client terminal audit must name the fixed run/commit,
exact final driver, socket-1 lane, outer exit, and released lease snapshot.
Its observed PID/start union must equal the retained driver/pane ancestry,
owned observations, all RSS sample identities, every stage's spawned identity,
every stage's `cleanup.observed`, and final `cleanup.observed`. The reader checks
the current identities again. The sole permitted non-absent identity is the
exact retained tmux pane with state `Z`, zero RSS, and role `tmux_launcher`; no
worker, driver, or arbitrary descendant receives that exception. No shared tmux
process is signaled. Whole-second helper timestamps are interpreted as intervals
while preserving the original pre-helper outer clock and full deadline.

The audit uses `state: complete`, `repository_commit`, `driver`, `lane`,
`outer_exit`, `lease_snapshot`, `observed_at`, `lease_released: true`, and
`owned_processes`. A fully absent union uses
`cleanup_state: terminal_and_reaped` with `owned_processes_absent: true`.
The exact permitted pane zombie uses
`cleanup_state: terminal_no_live_owned_processes`,
`owned_processes_absent: false`, and `owned_processes_nonrunning: true`.

## Historical failures and remaining gates

All four original serial controls and their diagnostic scope remain under
`calibration.historical_serial_control`, including the original false numerical
gain. The old four-thread paired plan and all twelve canonical record hashes
are pinned by the new collector's plan. Their exact timing metadata, original
driver/terminal references, both-direction statistics, and failed 0.10 spread
groups remain under `historical_four_thread_paired_control`. The original
timed-out preparation's hashed receipt and cleanup audit are retained too.

The old paired metadata is not freshly requalified under changed runtime code;
the original old-code preparation did not complete. No historical failure is
deleted, relabeled, used as a new statistical sample, or made an unconditional
veto on this separately versioned configuration. Missing or changed historical
evidence still blocks admission. The new one-thread controls determine the new
configuration's native qualification, and all four fresh diagnostic packages
must describe that same new context. Old four-thread packages cannot substitute.

Sampling remains ten repetitions, zero warmups, the three ordered sources,
balanced order seed 20260926, and paired repetition-block bootstrap analysis.
The fixed .10 spread ceiling, 1.05 minimum speedup, 95% confidence, 2,000 resamples,
and bootstrap seed 20260925 are unchanged. Neither passing A/A controls nor
these four cells establish nominal confidence-interval coverage or power.

The existing shared accelerator size, actual six-replay timing, correctness,
case coverage, and spread gates still apply. A successful native client alone
cannot freeze a protocol, resolve T15, or establish a candidate gain. A future
candidate comparison uses its separately bound fresh assessment context; this
publication route does not relabel its original proposal or provider history.

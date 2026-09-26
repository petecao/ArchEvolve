# Prospective Linux supervision admission

Created 2026-09-26 ET. Preparation only: no fixture, installation, export or
measurement is authorized by this document. The active one-thread pilot remains
pinned at `319645eab0a25c815fa03fe1c372d32b4ba45d10` until its whole terminal
outcome and independent cleanup audit. Its statistical outcome does not change
these fixture requirements.

## Execution order and fixed scope

Run three independent selections sequentially, after the native pilot is fully
terminal and the final reviewed runtime has arrived through Git. Each uses a
new raw directory, one eligible socket through the current normal lane helper,
and a named tmux session. No retry, repair, provider call, real guest execution
or performance measurement is part of a selection.

| Selection | Exact pytest target | Required unskipped cases | New raw root |
|---|---|---:|---|
| Simulator ownership | `tests/test_bfs_owned_execution.py -k linux` | 4 | `/data/yanruj/EvolveSWDB_runs/bfs-simulator-owned-linux-20260926-a1` |
| Public interrupted record | `tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem` | 2 | `/data/yanruj/EvolveSWDB_runs/bfs-simulator-interruption-linux-20260926-a1` |
| Native campaign ownership | `tests/test_bfs_native_execution.py::test_linux_campaign_reaps_detached_child` | 2 | `/data/yanruj/EvolveSWDB_runs/bfs-native-campaign-owned-linux-20260926-a1` |

The first selection includes successful and failed detached-child stages,
nested interruption sharing one cleanup ledger, and the TERM-resistant nested
case. The second uses explicit simulator fixtures and verifies that the public
interrupted record is durable before optional postmortem work raises or stalls.
The third exercises successful and failed native campaign stages with detached
children. These establish process and persistence contracts only.

Use the existing `/data1/yanruj/venvs/evolveswdb-test/bin/python3`; recheck its
resolved executable hash, Python version and pytest version immediately before
execution. The last verified versions were Python 3.12.3 and pytest 9.1.1;
those historical values do not replace the new check. Invoking the venv path
preserves its installed pytest; record its resolved executable separately.
Do not install or change packages. Set `PYTHONDONTWRITEBYTECODE=1`, disable
pytest's cache plugin, and place `TMPDIR`, JUnit, basetemp and all outputs under
the selection's raw directory. No writes belong in a measured checkout or HOME.

## Bounded fixture supervisor

A plain pytest process-group timeout is insufficient for these tests because
they deliberately create independently sessioned children. The thin tracked `scripts/bfs_linux_fixture.py` supervisor reuses `bfs_owned_execution.SharedCleanup`, `Owned`,
`Monitor` and `run_stage`; it does not change the tested helper. It is implemented for independent review and remains unapproved for dispatch.

The outer start is captured in the owned tmux pane before entering the helper.
Each selection has one 90-second absolute ceiling, at most 60 seconds for
pytest and setup, and the same remaining 30 seconds for owned cleanup and final
hashes/persistence. The outer wrapper sends TERM at 60 seconds and KILL 30
seconds later. The supervisor enables subreaper ownership before pytest,
retains exact driver/pane ancestry only through the owned pane, samples its
observed PID/start subtree, and unconditionally reaps its direct child even
when a signal or observation fails. No numeric signal may target a reaped
leader or shared tmux server. A timeout, unknown owned identity, exceeded
reservation, stale telemetry, missing JUnit or nonzero child exit fails the
selection; there is no second attempt.

The fixture-only ceiling is 512 MiB sampled tree RSS and 512 MiB retained
new output, with existing 10-GiB build and 30-GiB raw free-space reserves. A
sampled RSS limit is not a kernel quota. Nominal five-second observation and
30-second maximum gap apply through final writes. Each inner test retains its
own existing finite subprocess limits. An inner timeout does not extend the
outer ceiling. The external terminal audit is read-only and may be recorded
after the selection has ended; its timestamp must not be relabeled as fixture
execution time.

Before a selection, retain both socket and legacy metadata plus kernel locks,
helper Git/script identity, load, disks and node/global capacity. Do not fetch
or alter any active or historical checkout. The final exported fixture code
commit is intentionally unspecified until root's reviewed fixes and minimal
inventory are frozen. No guessed future commit satisfies admission.

## Evidence and independent closure

The supervisor must retain its exact pytest argv/CWD, before/after code and
runtime hashes, start/finish/elapsed, child return code, stdout/stderr and JUnit
hashes, observed PID/start samples, complete known/adopted ownership union,
shared cleanup ledger and every cleanup error. Use `--junitxml=ABSOLUTE_PATH`
and `--basetemp=ABSOLUTE_PATH` in each command. A passed JUnit result alone
cannot establish host process absence.

After the outer wrapper exits, an independent audit reopens all pinned
artifacts and unions pane/helper/timeout/supervisor/pytest identities, every
sample, and direct/adopted identities in the retained test and cleanup
receipts. Recheck each PID together with its start time. Require no matching
live owned process, the exact lease generation released and kernel lock empty,
and matching zero outer/supervisor/pytest exit values. Only the exact captured
pane identity may remain as an explicitly recorded zero-RSS zombie; never
infer this for an arbitrary child. A missing observation or surviving identity
keeps admission failed/unverified, with all bytes retained.

The two simulator proof JSON objects use `swdb.bfs.linux-fixture.v1`, kinds
`owned_cleanup` and `dx100_interruption`, host `mbit10`, platform `linux`,
`evidence_kind: contract_fixture`, state `passed`, integer return code zero,
exact `code_commit`, the runtime subset required by
`bfs_simulator_batch.validate_cleanup_tests`, aware fixture start/finish within
90 seconds, actual pytest command and `{path, sha256}` stdout/JUnit references.
The runner writes only `proof.pending.json`, whose state is
`tests_passed_cleanup_unverified`; public admission rejects it. After independent
closure, seal a distinct immutable `proof.json` with state `passed`, retaining
`pending: {path, sha256}` and `terminal_audit: {path, sha256}`. Never overwrite the
pending file or relabel its time interval. Only these admitted proofs become the
two `linux_cleanup_tests` references. Required test names and zero failure/error/skip are rechecked by the
public admission reader.

The native proof has the same format and kind
`native_campaign_owned_cleanup`, and binds `runtime` exactly to
`bfs_native_campaign.campaign_runtime(export_commit)`. Both parametrizations
`test_linux_campaign_reaps_detached_child[False]` and `[True]` must be present.
Its admission field is `linux_proof: {path, sha256}`. Preserve the independent
terminal-audit reference as additional operational evidence. No proof can be
reused under a different runtime/code commit merely because test names match.


## Concrete invocation after final pin and terminal prerequisites

For each selection, set `KIND` to one of `owned_cleanup`,
`dx100_interruption`, or `native_campaign_owned_cleanup`. Capture `START` and
`END=START+90 seconds` in the owned pane before the helper, and put helper/outer
receipts in the corresponding new sibling `.dispatch` directory. Reopen the
controlled Python and pytest pins before recording the exact expanded argv.

```sh
timeout --signal=TERM --kill-after=30s 60s \
  bash "$LANE_HELPER" "$NODE" "$FIXTURE_ID" --record "$DISPATCH/lane.json" -- \
  env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE \
      -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS -u LD_PRELOAD -u LD_LIBRARY_PATH \
      PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /data1/yanruj/venvs/evolveswdb-test/bin/python3 "$CODE/scripts/bfs_linux_fixture.py" "$KIND" \
      --expected-commit "$COMMIT" --python-sha256 "$PYTHON_SHA256" \
      --pytest-version "$PYTEST_VERSION" --pytest-sha256 "$PYTEST_SHA256" \
      --outer-started "$START" --outer-deadline "$END" \
      --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START_TICKS" --lane "$NODE"
```

The fields above are unresolved preflight substitutions, not permission to guess
identities or move historical checkouts. The actual supervisor and outer exit
values must both be retained; shell pipeline success must not replace either.
The runner rejects optimized Python startup so nested contract assertions remain
enabled and clears explicit pytest plugin injection. It records pytest version/module hash and the controlled Python map,
keeps telemetry active through owned teardown, and leaves the independent
terminal audit to a different post-exit observation. A late failure leaves any
pending result unaccepted; no runner path writes the admitted `proof.json`.

# One bounded native readback: concrete preflight

Created: 2026-09-26 ET. Preparation only. Root must see this preflight and the independent review before Host launches the single attempt.

Fixed source: supervisor `/data1/yanruj/EvolveSWDB_bfs_supervision_20260926_a1` at `3f38a2bf9cde4fb23edebd787a9d4d8ab9549e07`; measured collector `/data1/yanruj/EvolveSWDB_native_one_thread_20260926_a1` at `319645eab0a25c815fa03fe1c372d32b4ba45d10`, using its existing `records`. Both remain unchanged. Host reported them pristine at 18:00:20 ET; actual prelaunch checks remain necessary.

Host's sealed original driver SHA is `81596a440b9114c5f4a6b2edb1d8a799b748ae01c144bc82a218902755115092`; terminal audit SHA `9fe880825baefb4179e14f30310916054aacf2af86b050ec2ad9c05fb37ed0d4`. Host reports completion 17:56:28.630676 ET, outer exit 0, generation402 released, all131 PID/start identities absent in two observations. These are inputs to independent reopening, not a qualification result. The recipe enforces the original 15:07:35.041327–20:11:35.041327 interval and full native cleanup validator.

Prepare the new raw root `/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a1` and its new sibling `.dispatch` only after checking they are unused. Copy the reviewed recipe as `RAW/readback-recipe.py`; copy the fixed selection template as `RAW/selection.json`. Capture actual pane PID/start and whole clock in the owned named tmux pane; replace only the template's two clock placeholders with that aware start and start+990 seconds immediately before the single timeout/helper command. Retain final selection hash and expanded argv in `.dispatch/launch.json`. The future readback lease generation is recorded separately from original native402.

Recipe: `/private/tmp/bfs-native-readback-recipe-20260926.py`, SHA256 `d91d061933c5a5ae49a73227a1a5be79579acb531052621aa5bcc074ca5294eb`. Template: `/private/tmp/bfs-native-readback-selection-template-v2-20260926.json`, SHA256 `7625db24ea8c69586e255e8c8cfeee013469571caece6604998c246a66fb385a`. Its four package IDs and immutable driver/terminal references are fixed; no other input edits.

From the exact supervisor CWD, after fresh health, all relevant kernel locks/leases and full native closure:

```sh
timeout --signal=TERM --kill-after=30s 960s \
  bash /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh \
  0 bfs-native-one-thread-readback-20260926-a1 --record "$DISPATCH/lane.json" -- \
  env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE \
      -u PYTHONOPTIMIZE -u LD_PRELOAD -u LD_LIBRARY_PATH \
      PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PATH=/usr/bin:/bin \
  /usr/bin/python3.12 -s -c \
  'import runpy; runpy.run_path("/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a1/readback-recipe.py", run_name="__main__")' \
  >"$DISPATCH/outer.stdout" 2>"$DISPATCH/outer.stderr"
status=$?
printf '%s\n' "$status" >"$DISPATCH/outer.exit"
exit "$status"
```

Host's last Python observation is 3.12.3, executable SHA `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f`, matching the measured collector. Helper HEAD/upstream `42ce8dce1ecfb949d6e5d4ee3c98c078bc7ddc65`, script SHA `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`. Refresh/reopen these pins; do not substitute another Python.

The timing-only wrapper delegates saved `pinned_readback` once, with unchanged arguments, result and exception. Its existing900+30 remains intact. Cumulative ancillary60 includes startup/helper/imports, terminal checks, package/control/runtime reopening and final hashes; SIGALRM pauses only while the original reader runs. Whole990 is never extended; no second cleanup allowance. Existing `interruption_signals` makes outer TERM unwind through original reader cleanup.

Retain pending/result hashes, stdout/stderr, actual exit and reader/owned process observations. Success requires wrapper exit0, published result hash unchanged, node0 helper released and independently verified no live owned readback work. A late failure withdraws only its new result link; pending bytes remain unaccepted. No retry, prepare/publish, record write, provider, build or measurement. All4 packages and8 directional controls/24 spreads must pass actual reopening before any qualification statement.

At 18:05 ET Host reopened the actual dictionaries and package list: native `audit.driver` includes exactly the retained `bytes: 486592` in the V2 selector; historical paired `audit.driver` has only the two path/SHA keys already retained. All four actual native diagnostic IDs and order equal V2. The original319 validator returns the supplied driver reference unchanged. V1/preflight are preserved as superseded preparation; use only this V2 preflight/template. No actual readback has run.

## Git-only operational transfer — 2026-09-26 ET

The recipe and selection template arrive on mbit10 through the private auxiliary
branch `codex/bfs-native-readback-20260926-a1`. Root records and verifies its exact
commit before use. Fetch that object without moving supervisor HEAD `3f38a2b`;
materialize its exact Git blobs into the unused raw root. Do not copy source from
the Mac over SSH. In the auxiliary commit, the recipe is
`.scratch/bfs-rewrite-evaluation-2026-09-25/requests/native-readback-20260926-a1.py`
and the template is the same path with `.json`. Match their already-reviewed
SHA256 values before the host replaces only the two clock placeholders. This
transfer clarification supersedes the earlier copy wording; all execution
arguments, collector/supervisor identities and timing bounds are unchanged.

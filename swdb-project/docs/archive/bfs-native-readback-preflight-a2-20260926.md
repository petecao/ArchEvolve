# Corrected native readback a2: concrete preflight

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 ET. Prospective; actual Linux proof is sealed; final independent review and fresh host admission remain prerequisites. This is one new bounded metadata readback, not a retry within consumed a1.

Use supervisor `/data1/yanruj/EvolveSWDB_bfs_reader_20260926_a2` at `5e8b750b14679d5962d1e4b40cd5fa0f1b6981b0`. Keep measured collector `/data1/yanruj/EvolveSWDB_native_one_thread_20260926_a1` and its records at `319645eab0a25c815fa03fe1c372d32b4ba45d10`. Neither tree is modified. The original readback a1 remains failed, with incomplete historical reader identity evidence. Its prior pending output is never an a2 input or success result.

Recipe `/private/tmp/bfs-native-readback-a2-recipe-20260926.py`, 17,626 bytes, SHA256 `cc1d2dda1d0c3498c0c12312183249b700fbec983bbba6f0e7e2d40510047339`. Prepared selector `/private/tmp/bfs-native-readback-a2-selection-prepared-20260926.json`, 2,820 bytes, SHA256 `e69e7250ad24135063106dac8764ca1311435bec7eb11141e2b573153b303774`. The template's entire `spec` equals the previously reviewed V2 a1 selection, including native driver `bytes:486592`, the historical driver's exact two-key reference, ordered four actual packages and all failed controls. Only outer clock and actual pane identity remain preparation placeholders. The separately sealed Linux proof reference is fixed.

The native driver SHA remains `81596a440b9114c5f4a6b2edb1d8a799b748ae01c144bc82a218902755115092`, terminal SHA `9fe880825baefb4179e14f30310916054aacf2af86b050ec2ad9c05fb37ed0d4`. The recipe reopens original generation402 and its 15:07:35.041327–20:11:35.041327 ET whole-study clock. Host reported complete native17:56:28.630676, released402, all131 retained identities absent in two passes. These are prerequisites to the one reader, not a qualification result.

## Required manual Linux proof

Before dispatch, seal the authorized one-case test against exact5e8, with original90 seconds inclusive of startup and cleanup, actual1pass0skip, all required exits0 and independent process/lease/kernel closure. Exact selector:

`tests/test_bfs_one_thread_freeze.py::test_linux_fast_reader_retains_actual_unreaped_identity`

Proof format `swdb.bfs.native-reader-linux-proof.v1`: `state:passed`, `host:mbit10`, `platform:linux`, `evidence_kind:contract_fixture`, exact `code_commit` and `selector`, aware `outer_started`, `outer_deadline` exactly90 seconds later, `finished`, separate later `audited_at`, integer `returncode:0`, `python:{path,sha256}`, `pytest_identity:{pid,start_ticks,...}`, and immutable `junit`, `stdout`, `stderr`, `events`, `terminal_audit` references. Event JSONL comes from the test's fresh `--basetemp` and contains fsynced spawn/finished observations for the same reader identity, actual direct reap and exit0. The audit retains the full pane/helper/timeout/pytest/reader/observed union, exact released lease and kernel check; the only optional non-absent identity is the exact zero-RSS owned pane zombie. The recipe reopens hashes, actual JUnit and direct identities; the independent manual audit remains responsible for full kernel/lease closure. No generic fixture route is added and no missing identity is reconstructed.

## Single owned launch

Host must first reopen the pristine code/runtime/Python pins, current upstream helper identity, free socket/legacy leases, kernel locks, current processes, memory/storage capacity, original native closure and the manual Linux proof. Coordinate with other work and the A2 simulator's unchanged21:00 cutoff. This readback may start only19:00–23:43:30 ET2026-09-26 and must end by00:00 ET2026-09-27. Full990 seconds must fit; no shortened-window launch or extension.

Create only unused raw `/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a2` and sibling `.dispatch`. Stage reviewed recipe as `RAW/readback-recipe.py` and template as `RAW/selection.json` through the approved Git path; preserve original local files. Preserve the fixed sealed `linux_proof` ref. In one fresh named tmux pane, capture actual pane PID/start and aware outer start immediately before timeout/helper; set end=start+990 and persist final selection/launch hashes. Derive `TERM_SECONDS` from the same original deadline minus current wall time minus30, refusing nonpositive or extended time. Retain actual expanded argv, environment, clocks and pane/helper/timeout/recipe PID/start identities immediately. These operational observations are not included in deterministic qualification output.

From the exact new supervisor CWD, with `DISPATCH` bound to that fresh sibling and clipped `TERM_SECONDS`:

```sh
timeout --signal=TERM --kill-after=30s "$TERM_SECONDS" \
  bash /data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh \
  0 bfs-native-one-thread-readback-20260926-a2 --record "$DISPATCH/lane.json" -- \
  env -u PYTHONPATH -u PYTHONHOME -u PYTHONSTARTUP -u PYTHONUSERBASE \
      -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
      -u LD_PRELOAD -u LD_LIBRARY_PATH \
      PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PATH=/usr/bin:/bin \
  /usr/bin/python3.12 -s -c \
  'import runpy; runpy.run_path("/data/yanruj/EvolveSWDB_runs/bfs-native-one-thread-readback-20260926-a2/readback-recipe.py", run_name="__main__")' \
  >"$DISPATCH/outer.stdout" 2>"$DISPATCH/outer.stderr"
status=$?
printf '%s\n' "$status" >"$DISPATCH/outer.exit"
exit "$status"
```

Python must retain the measured executable identity: resolved `/usr/bin/python3.12`, last observed3.12.3, SHA `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f`; the manual proof and runtime check reopen it. Helper last known HEAD/current upstream `42ce8dce1ecfb949d6e5d4ee3c98c078bc7ddc65`, script SHA `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`; fresh host admission is required.

## Timing and retained outcome

The original transparent wrapper delegates saved `pinned_readback` exactly once, passing `reader_observer` without changing other arguments, return or exception. Original900 work+30 cleanup stays inside990. Startup/helper/imports, terminal/proof checks, control/package/runtime checks, read-only monitor shutdown and final hashes share60 cumulative ancillary seconds. SIGALRM pauses only during the one reader. No new Owned supervisor or cleanup reserve is created. Existing interruption handlers remain installed through finalization.

Readonly sampled RSS uses existing stat-based `DescendantRSS` and `Monitor`, nominal5/max30 seconds, capped16GiB; telemetry is sampled, not a hard cap. Resource JSONL≤16MiB, reader events≤64KiB. Reader callbacks register real PID/start and fsync each event immediately, before poll/reap. Known identities survive failed telemetry. Snapshot retains root/pane ancestry, sampled/known identities and sampling status; it always says `cleanup_verified:false`. Post-sampling metadata must finish within30 seconds and the smaller original remaining allowance. Failure never publishes readback.json; preserved pending bytes are unaccepted.

Host independently reopens actual result/exit/clock and unions ancestry, all resource rows, known identities, reader events and external wrapper identities after exit, checking every PID/start plus released actual readback generation/kernel. `sampling_finished` does not prove cleanup. A successful result qualifies only the existing native baseline study after all four packages, eight directional controls,24 spreads and exact runtime identities are reopened. It never freezes a protocol, accepts a candidate or claims gain. No provider, build, measurements, source edits or automatic retry. Combined conservative ceiling for consumed a1 and this a2 is1,980 seconds.

## Actual manual prerequisite and review correction

Host sealed the single Linux fixture at18:42:48.498884–18:42:49.746469 ET (1.247585 seconds),1pass0skip/all exits0, exact5e8 runtime. Proof `/data/yanruj/EvolveSWDB_runs/bfs-native-reader-fast-exit-linux-20260926-a1/proof.json` (2,914 bytes), SHA `79f349b0e348e4ee47e63a4a74ff04565497e7c7df45848c6cd9e1aad940b4b1`; terminal audit SHA `dfc60af762b51e2c38ffebd0218d8be4a9b90027691991b737f7f38895df91bc` at18:44:41.296877 ET. Host retained seven PID/start identities; six are absent and only exact pane3079200/start496450134 is Z/RSS0. Generation327 is released and kernel clear in two observations. Spawn and finished contain identical actual reader3079278/start496450236; finished confirms direct reap/exit0. These are contract-fixture lifecycle facts, not native qualification. Source-free local observation `/private/tmp/bfs-native-reader-fast-exit-actual-20260926.json` SHA `f3cc5db3b2039b27dc2733dad725feafcd170eec06947f6bb1395d246f037e2e` retains the full metadata.

Independent review reproduced a finalization error-precedence defect in the first draft: a secondary snapshot-write failure could mask a final sampling error. The new recipe preserves that first error and annotates the secondary error, with no retry or additional reserve. Preserve the original draft and red probe.22 local contract cases, including the unchanged independent probe, pass in0.16 seconds. The first preflight/template remain preparation history; use only this superseding preflight and prepared selector.

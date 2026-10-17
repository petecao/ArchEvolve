# Actual a5 release32 and b08 after — source-only worksheet

No remote operation, producer, collector or scientific command was executed by this worksheet. Construct requests only after actual dispatch/stopped/lane/exit/lease originals exist.

## Fixed routes and current genuine pins

- S: `/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5`; R: `5e12a9796432654d88def24ecea617d16ca605b2`.
- RAW: `/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5`.
- M2: `RAW/manifest.json`, 292401 bytes, file SHA `b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1`, identity `66194a7e99716f5b59ddf081dfec752c34b51f1805470a4514171c53323b06c7`.
- FIRST: `/data/yanruj/EvolveSWDB_runs/lanl17-first-publication-custody-20261008-a5.json`, 7701 bytes, file SHA `e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1`.
- p1 before: `/data/yanruj/EvolveSWDB_runs/lanl17-p1-before-custody-20261008-a5/custody.json`, 3148 bytes, file SHA `e9beba6d829d41c1df9076c7b916eed0772c095de84a44c266ca88eee8a9b821`; observed state absent.
- Account: Linux mbit10, UID/eUID 114316761, user yanruj. HOME `/home/yanruj`; CODEX_HOME `/data1/yanruj/.codex`.
- A: `RAW/attempts/CID/attempt-1`; campaign state: `RAW/campaign-runs/extensa/CID/state.json`. p1 selected node is 0; other campaigns use their actual dispatch node.
- H alias: `/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py`, 38195 bytes, SHA `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`; permission tightening to0600 preserved bytes. Keep failed pre-exec captures historical.

## Release32: exact original descriptors

Use unchanged producer32 (46165 bytes, SHA `32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6`) at `S/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-future-input-controls-20261007-a3/lanl17_parent_capture_projection_producer_a3_20261007.py`.

| Input name | Original path | Encoding / seal | Writer source |
|---|---|---|---|
| manifest_M2 | M2 | json / True | Reuse exact FIRST helper28 writer descriptor |
| dispatch | A/dispatch-preregistration.json | json / True | Exact helper28 source; dispatch executed H |
| stopped | A/stopped-receipt.json | json / True | A/helper.py, exact helper28 bytes |
| wrapper_exit | A/wrapper.exit-code.txt | integer_exit / False | Exact helper28 source that generated the wrapper shell/printf |
| runner_exit | A/runner.exit-code.txt | integer_exit / False | A/helper.py |
| lane | A/lane.json | hash_only / False | Actual M2.wrapper.path (socket_lane.sh), frozen SHA `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8` |
| authoritative_lease_observation | /data1/yanruj/lact-host-lease/mbit10-evaluation-nodeN.meta.json, or existing authoritative native-query original | hash_only / False | Actual hostlock.sh source for direct native metadata; actual existing query writer if query output used |

Every descriptor has exactly `path,bytes,sha256,encoding,sealed,writer_source={path,bytes,sha256}`. Sealed JSON additionally requires `identity_sha256,canonical_ensure_ascii=true,canonical_policy_sources=[{path,bytes,sha256},...]`. Never invent a seal for exit/lane/lease inputs. Use actual current byte counts/hashes and source pins; hostlock size/hash are not inferred here.

Reuse the previously reviewed producer32 request schema and actual FIRST context, with `capture=release`, `campaign=CID`, `attempt=1`, all original32/e342/6a/b08 source pins unchanged. Request whole-object seal: sorted compact JSON, ensure_ascii=True, allow_nan=False.

Observations have exactly `lease_released,lease_generation,checked_utc`. They are actual parent observations, not defaults. `checked_utc >= stopped.ended_utc`. Exit files must be original integer bytes, ≤64 bytes matching `-?[0-9]+\s*`; runner integer must match stopped.runner_exit_code. Preserve a null public_exit_code if that is the actual original.

Read roots must cover S, RAW, external capture parent, writer sources and native lease observation. If using the flat H alias as writer source, cover its explicit path/root; alternatively reuse the verified identical helper descriptor under S and retain executed-H provenance separately. Fresh producer output must be owned under `/data/yanruj/`, outside S and RAW.

Command: `/usr/bin/python3.12 -B PRODUCER32 --request ACTUAL_REQUEST --request-sha256 ACTUAL_REQUEST_FILE_SHA --output FRESH_RELEASE_FILE`.

## Native release: complete the wrapper, then observe generation

Producer32 hashes lane/lease originals without parsing them. Parent must establish release before setting flags:

1. Actual dispatch/stop match CID, attempt, R, M2, policy and stop.dispatch_sha256. Stopped cleanup is subreaper=True, survivors={}, source_clean_after=True, F6 unchanged.
2. Final lane.socket_lane has the actual node/session/lease_name and a completed exit, not initial -1. Generation comes from **this lane's acquired lease_generation**, not dispatch's earlier released snapshot.
3. Wrapper exit file exists after the wrapper command and EXIT trap complete. Check selected-node native metadata state=released, lease.lease_name and generation equal that final lane; preserve original observation bytes. Reuse existing authoritative native lock/service query as needed.
4. Important ordering: hostlock_release writes released metadata **before** unlocking fd9. Metadata released alone is insufficient. The wrapper-exit file is written by the parent shell after wrapper termination, so wait for it plus final lane and native observation. No requirement that all other lanes be free; coordinate the selected lane.
5. Do not reuse the selected node until release32 and b08 after finish, or its metadata generation may change and original rechecks properly refuse. No manual metadata edits or force-unlock.

## b08 after: same account, source, action and originals

B08 is the verified24818-byte source under `S/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-selected-trajectory-controls-20261007-a2r1s1/lanl17_compact_attempt_custody_a2r1_20261007.py`; no alias stage, read_roots flag or marker is required.

Use the actual before common argv, switch phase to `after`, set a fresh after directory, and append:

```text
--before ACTUAL_BEFORE --before-file-sha256 ACTUAL_BEFORE_FILE_SHA
--dispatch A/dispatch-preregistration.json --dispatch-file-sha256 ACTUAL_DISPATCH_FILE_SHA
--stopped A/stopped-receipt.json --stopped-file-sha256 ACTUAL_STOPPED_FILE_SHA
--released ACTUAL_RELEASE_FILE --released-file-sha256 ACTUAL_RELEASE_FILE_SHA
```

Keep `--attempt 1`, no resume/baselines-only flags, and exact M2/FIRST/account pins above. b08 independently rereads fixed A/helper.py, lane and exit files; checks release linkages, original wrapper/runner integer bytes, source cleanliness and owned cleanup; emits fresh AFTER_DIR/custody.json. It captures original state privately and exports only allowed projections. Order: before ≤ dispatch ≤ stop start < stop end ≤ release ≤ after.

## Monitor and terminal decision

Verified monitor: local `/private/tmp/lanl17_campaign_status.py`,14577 bytes,SHA `c87a1eeeb9ec098a081546f019c5c315f30a8ce5a7a7975113e0f719196259a1`. Check actual staged alias before use; `/usr/bin/python3.12 -B MONITOR --manifest M2 --format markdown`. Metadata-only; partial live writes remain unknown. Status tables at least every30min; verify agent/process progress.

Normal terminal requires stopped state and matching summary/ledger; runner/public/wrapper exits all0, infrastructure_error=None, baselines_only=False; reason is max_iterations/plateau/lane_hours/provider_calls/disk. Max_iterations requires8 completed rows; plateau requires ledger plateau≥4. All completed sessions must satisfy retained substantive-call/accounting checks; summary existence or baseline-only work is insufficient. Final ticket17 still requires four such substantive normal trajectories plus original freeze/report order; zero eligible pairs remains unsupported/no-switch.

On a nonterminal stopped attempt, preserve all originals, capture release/after, and inspect actual state/ledger/provider-call accounting before a new attempt with --resume. Nonzero prior exits require unchanged existing unclean-resume custody proving zero unaccounted opened calls and no source/state repair. **Any state.stopped=True is terminal and refuses resume, including infrastructure_failure**; never reset/delete state or blindly rerun/rename a campaign. An infrastructure terminal is not completion; report it for parent diagnosis. A pre-exec bootstrap failure with absent attempt/campaign directories is separate administrative failure; preserve its capture and use a fresh capture only after the concrete cause is fixed.

Source references: producer32:200–246,327–335,420–455; b08:184–211,236–281; helper28:458–480,583–592; auditor6a:1202–1225,1278–1295; hostlock.sh:308–328.

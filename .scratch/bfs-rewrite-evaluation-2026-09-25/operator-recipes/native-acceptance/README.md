# Existing-candidate native acceptance preparation

Created: 2026-09-27 (Eastern Time). Updated: 2026-09-27 12:35 ET.
Status (original): data-only preparation; neither route is admitted or dispatched.

**Executed — 2026-09-27 12:35 ET (Stream B).** Both routes have now executed.
Evidence: [observation](../../observations/native-routes-t18-t19-20260927.json)
and Tickets 18/19.

- `protocol/` holds the two R7 selections and `operation.sh`, used for
  prepare/publish outside a lane.
- `operator.py` holds the proof/admit/launch/close glue. Admission now builds a
  reference-closure record view.
- T18 b1 was interrupted and is retained.
- T18 b2 and T19 b2 are evaluated. All four comparisons are inconclusive under
  the spread veto.
- T19 b1 was admitted but never launched; its admission is retained. The text
  below is the original preparation record.

Assumption: preserve the existing T18 DX100 supplied patch and T19 upstream
structured-instruction candidate, and assess each against separately frozen
one-thread native settings. No provider or repair call is part of this route.
The new prospective IDs reserve no lane, time, disk, or retry allowance.

| Route | Existing candidate | Ready | Still blocking |
| --- | --- | --- | --- |
| T18 | `bfs-campaign-preparation-20260925-a1.dx100-patch.candidate-1` | Original request, exact patch digest, canonical origin and two historical package references | T15 outputs, source-specific qualification/publication, fresh native packages/protocol, runtime-matching native ownership proof, actual lane/capacity admission |
| T19 | `bfs-campaign-preparation-20260925-a1.upstream-instructions.candidate-1` | Original request, retained interpreted patch digest, completed provider provenance and consumed repair budget | Same prerequisites, independently bound to upstream source and workloads |

The route folders contain the actual original request reconstructed from the
canonical proposal record, a reassessment template with fully pinned historical
origin, an admission template with exact current native bounds, and a readiness
receipt. The nulls deliberately prevent these templates from passing the current
driver. Historical records were read locally; remote source files, retained diff
files, protections against actual bytes, and patch replay were **not** reopened.
The record's artifact manifest is a retained identity, not a fresh remote hash check.

`prepare_templates.py` only produces those data files. It checked the actual
initial candidate state, one completed rewrite, payload hash, retained patch
hash, source protection metadata equality, and original provider budget. It
refuses to overwrite a changed existing template. The first local invocation
encountered an omitted optional `parent_candidate`; the check now matches the
production validator's `get(... ) is None` semantics. This was a local preparation
failure before any route output, not an evaluation attempt. No shared code changed.

## Complete the inputs without resetting evidence

1. Retain the original native study and both failed standalone readbacks. Follow
   `docs/bfs-native-qualification-continuation-20260926.md`: after the actual T15
   simulator packages exist, each source's prepare and publish operation must
   consume the original 319-study reader and its original whole-study prerequisites.
   No third standalone reader, replacement study, or new native calibration budget
   is introduced here. A readback closure is not a qualification or protocol freeze.
2. Obtain two fresh native baseline packages and the frozen native protocol for
   each exact source. Fill `assessment` in the reassessment template with canonical
   record digests using `swdb.artifacts.digest`, not YAML file hashes. Preserve the
   historical origin unchanged. All four retained historical package contexts explicitly
   record `threads: 4`; the template checks this before fixing `from_threads: 4`.
   `to_threads: 1` follows the pending fixed one-thread publication policy. Fresh package order must equal CLI order, and the
   fresh workload set, adjacency order, compiler/template/binary and protected source
   identities must satisfy `validate_reassessment`. Historical unobserved runtime
   settings remain unknown. Do not infer them from the current shell.
3. Export the reviewed native runtime through private `codex/bfs-*` Git and use a
   pristine separate host checkout. Pin the entire Git inventory and Python binary
   before importing project code. Do not add files to an active simulator checkout.
   `campaign_runtime(COMMIT)` and `campaign_inputs(args)` supply the actual admission
   fields, after the record view, original proposal JSON and completed reassessment
   are present on the host. Carry records and required source excerpts through Git;
   do not repeat the T17 YAML-only projection that dropped required `.cc` artifacts.
4. Reopen the exact native Linux proof through `validate_linux_proof`. It must match
   that runtime and include both unskipped detached-child native cases, actual
   stdout/JUnit, and independent terminal closure. The successful simulator a5
   proof and its 49 tests do **not** substitute for this native selection. If a
   matching native proof is unavailable, resolve its existing fixture/preparation
   allowance with root before any fixture execution; this packet creates none.
5. Complete admission only after checking current helper versus upstream, both
   socket `.lease` locks and metadata, legacy lease, disk reserves, node/global
   capacity, and ownership. No node is preselected. Node0 was externally occupied
   and node1 running T15 when this preparation was assigned; neither is reserved.
   Use the unchanged 20/24 GiB capacity and 30/10 GiB free-space gates, 16 GiB
   sampled RSS/artifacts and 4 GiB build subset from the admission's bounds.
6. The exact `.dispatch` sibling must exist; raw/source/build directories must be
   new, canonical and disjoint. Put the record view and SQLite/sidecars inside
   `.dispatch`. Retain all wrapper/helper outputs there. Hash the final admission
   file only after its actual contents have been sealed. Existing output roots or
   attempts must not be reused or overwritten.

## Existing driver invocation inside the reviewed wrapper

The following is the complete driver argument shape, not an executable launch
script. Every uppercase variable must come from the sealed source-specific
admission and actual original wrapper. No placeholder is a default.

```sh
"$PYTHON" -s -B "$RUNTIME/scripts/bfs_native_campaign.py" \
  --id "$ID" --existing-candidate "$CANDIDATE" \
  --proposal "$ORIGINAL_PROPOSAL_JSON" --reassessment "$REASSESSMENT_JSON" \
  --packages "$FRESH_PACKAGE_ONE" "$FRESH_PACKAGE_TWO" --protocol "$FROZEN_PROTOCOL" \
  --records "$RECORD_VIEW" --runs-dir "$RUNS" --source-runs-dir "$SOURCES" \
  --build-root "$BUILDS" --lane "$LANE" --total-seconds 14400 \
  --supervision-admission "$ADMISSION" --supervision-sha256 "$ADMISSION_SHA256" \
  --expected-commit "$RUNTIME_COMMIT" \
  --outer-started "$ORIGINAL_STARTED" --outer-deadline "$ORIGINAL_DEADLINE" \
  --pane-pid "$ORIGINAL_PANE_PID" --pane-start-ticks "$ORIGINAL_PANE_START_TICKS"
```

The shell wrapper must capture the original start and named tmux caller's real
pane PID/start ticks before its guards/helper. End = start + 14,400 seconds;
work end = start + 14,370 seconds. Enter only through the current verified
`socket_lane.sh`. GNU timeout must TERM at the **remaining** work interval and
KILL 30 seconds later, never start a new 14,370-second clock after guards. Reject
an exhausted interval. The driver entry and full prospective guard must meet its
own original-clock admission (driver entry at most five seconds after original
start). Do expensive readiness checks before dispatch and verify the sealed
identities again within that entry bound; a slow guard must fail, not reset time. Reuse its existing owned-process supervisor;
introduce no duplicate child supervisor or per-stage cleanup allowance. This
README deliberately leaves the outer wrapper unsealed until the actual runtime,
proof and protocol inputs are available for independent review.

Use the reassessment's exact eight-variable native runtime policy; clear declared
Python import inputs and disable bytecode. Neither `--provider-config` nor
`--repair-config` is allowed. The campaign's existing fixed build/trial/paired
limits remain inside the original 14,400 seconds, including setup and final writes.
A failed candidate assessment is retained; no retry or alternate optimization is
implied by either route ID.

## Closure and evidence boundary

After helper exit, independently bind actual outer exit, the complete owned
PID/start union, lease generation release and kernel state to the driver receipt.
The driver cannot attest its own reaping. Preserve failed outcomes even when all
processes are gone. Use the existing cleanup-ledger validation and
`bfs_native_campaign.validate_storage_accounting` with exact admission, driver
and `.dispatch/terminal-validation.json` references. Include the dispatch sibling,
record artifacts, database and sidecars. Persist the first storage readback inside
`.dispatch`; after all writes, retain a final read-only recount outside the charged
trees. Any later write invalidates that recount. Closure adds no cleanup time.

Acceptance still requires the actual changed-source builds, correctness, native
trials, diagnostic packages, comparisons and fresh public retrieval. No fixture,
metadata check, original provider success, or preserved primary build establishes
native gain or T18/T19 completion.

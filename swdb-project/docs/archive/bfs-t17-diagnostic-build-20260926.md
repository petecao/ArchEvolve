# One retained-candidate diagnostic build

Navigation updated: 2026-09-28 (Eastern Time).

Prepared: 2026-09-26 (Eastern Time). Interface v1; no dispatch or new provider call.

`scripts/bfs_t17_diagnostic_build.py` performs one public `dx100-compile` for
`bfs-t17-diagnostic-build-only-20260926-a1`. Its fixed request is the completed
T17 primary request with only a new ID and `diagnostic_regions:true`. The existing
primary binary `852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527`
is reopened, never rebuilt. Candidate, proposal, source, target, model, compiler,
function, acceleration and complete-call ROI remain fixed. A diagnostic build
does not establish guest correctness, coverage, profiling, timing or gain.

The original wrapper clock is 600 seconds: 570 work plus one shared 30-second
cleanup ledger. One public compile has 240 seconds of work, including its
180-second compiler bound. All preflight, public queries, artifact hashes and
final persistence share the original clock; no retry, repair, provider or guest
operation exists. The new output cap is 2 GiB including raw, its exact `.dispatch`
sibling, record view, SQLite and sidecars, temporary output and the new binary.
The build subset and public compile cap are each 1 GiB. The sampled owned-tree
RSS cap is 16 GiB; node/global admission requires 20/24 GiB available and raw/build
reserves remain 30/10 GiB. These sampled observations are not hard kernel quotas.

The new raw root is `/data/yanruj/EvolveSWDB_runs/bfs-t17-diagnostic-build-only-20260926-a1`.
The wrapper creates only its exact sibling `.dispatch` before launch. Assemble
an isolated record view there at `record-view/records` using same-host Git
materialization of the canonical base plus exactly missing retained provider and
primary metadata. Preserve original provider and scalar checkouts. No held
provider metadata or source payload is exported. Retain the Git commits, tree,
archive and complete initial record manifest in `.dispatch`; admission binds that
manifest. Only the new diagnostic evaluation and empty public-writer lock may be
added during this operation; both remain inside the charged storage root.
The new build and temporary paths are the run ID and run ID plus `.tmp` under
`/data1/yanruj/EvolveSWDB_builds`. All must be unused at admission.

The admission format is `swdb.bfs.t17-diagnostic-build-admission.v1`. It contains
the fixed ID/request SHA, exact `code_commit`, `campaign_runtime` result, node,
aware `prepared_at`, hashed `record_view` manifest and hashed `linux_proof`.
The record-view manifest contains `format: swdb.bfs.record-view.v1`, `records`
(the exact absolute directory), `files` (relative path/bytes/SHA-256 rows), and
`git_provenance` describing the retained same-host materialization. Every initial
record is rehashed before and after the operation. Existing ownership proof is
reusable only for identical tested ownership/Python bytes; retain its actual
proof commit separately from this driver's commit. It is contract evidence for
the reused primitives, not proof that this new driver or diagnostic build ran.

Proof compatibility update — 2026-09-26: the shared reader accepts only the exact
historical four-case selection or the approved five-case selection, with distinct
names and no failures/skips. T17 explicitly requires the five-case variant,
including `test_linux_storage_observation_handles_sqlite_journal_unlink`.
The fifth case additionally binds `scripts/bfs_storage.py` in the tested driver,
sealed proof and selected runtime; its hash is retained in the result. Historical
four-case scalar receipts remain readable, but cannot admit this diagnostic.
The current T17 guard rejects them before any public get or compile. No old proof,
plan, test outcome or consumed build is rewritten, and no extra fixture allowance
is granted. This uses the same already selected owned-proof job, not a third job.


```sh
"$PY" -s "$CODE/scripts/bfs_t17_diagnostic_build.py" \
  --expected-commit "$CODE_COMMIT" --admission "$DISPATCH/admission.json" \
  --admission-sha256 "$ADMISSION_SHA" --lane "$NODE" \
  --outer-started "$ORIGINAL_START" --outer-deadline "$ORIGINAL_START_PLUS_600" \
  --pane-pid "$PANE_PID" --pane-start-ticks "$PANE_START"
```

Capture the original aware clock and pane identity before the normal free-socket
helper and timeout. Use TERM at the original 570-second work boundary and KILL
by 600 seconds; compute remaining time rather than restarting those allowances.
Unset loader, Python and compiler search overrides before Python startup, as in
the scalar-build wrapper. No third lane is permitted. A fresh lease/capacity
check remains necessary; this preparation chooses no absolute launch window.

The supervisor uses the reviewed `SharedCleanup`, `Owned`, `Monitor` and
`run_stage`, together with process-free allocated-byte accounting. It retains
every direct child identity and stage result, continuous five-second observations
(maximum 30-second gap), original provider spending, exact primary artifact
bindings and fresh public diagnostic result/chain. An independent post-helper
audit must union ancestry, all samples, direct children and stage/final cleanup
identities, verify actual exits and lease release, and recount storage after the
last retained dispatch/audit write. The driver does not attest its own reap.
The failed scalar preparation and all four successful scalar build records are
separate evidence; this operation neither reruns nor promotes them.

The admission JSON must be the canonical `RAW.dispatch/admission.json`, without
a file or parent symlink. A hash-matching admission elsewhere is rejected before
public calls, keeping its retained bytes inside the same artifact ceiling.

# Explicit native candidate reassessment

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).
Status: locally implemented and independently reviewed on 2026-09-26. No assessment,
protocol publication, provider call, or source export is authorized by this file.

An existing candidate can keep its original four-thread creation package while
being assessed against separately frozen one-thread baseline packages. This is
an explicit configuration transition under [spec D13](../../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md):
new settings require new comparisons, and unfavorable old results remain intact.
It does not make an old profile into evidence for the new configuration.

The optional `--reassessment MANIFEST.json` argument to
`scripts/bfs_native_campaign.py` is valid only with `--existing-candidate ID`.
`--proposal` still names the exact original JSON request, including its original
profile package, source snapshot, payload, intent, constraints, and requirements.
`--packages` names exactly two fresh assessment baseline packages, in the order
pinned by the manifest. `--protocol` names the independently frozen new protocol.
Both `--provider-config` and `--repair-config` are rejected before public calls.
The default fresh-submit and ordinary same-configuration reuse routes are unchanged.

## Manifest contract

This is a private driver input, not a new public SWDB record or database schema.
It is limited to 1 MiB. Every object below has exactly the shown fields. A record
reference contains its complete ID and canonical `swdb.artifacts.digest(record)`
SHA-256, rather than a YAML file hash. `version` is integer `1`; boolean or float
substitutes are rejected.

```json
{
  "version": 1,
  "kind": "native_candidate_reassessment",
  "origin": {
    "proposal": {"id": "ORIGINAL_PROPOSAL", "sha256": "CANONICAL_RECORD_SHA256"},
    "candidate": {"id": "ORIGINAL_CANDIDATE", "sha256": "CANONICAL_RECORD_SHA256"},
    "profile_package": {"id": "ORIGINAL_CREATION_PACKAGE", "sha256": "CANONICAL_RECORD_SHA256"},
    "source_snapshot": {"id": "ORIGINAL_SOURCE_SNAPSHOT", "sha256": "CANONICAL_RECORD_SHA256"},
    "request_sha256": "CANONICAL_ORIGINAL_REQUEST_SHA256",
    "baseline_packages": [
      {"id": "HISTORICAL_GRAPH_ONE_PACKAGE", "sha256": "CANONICAL_RECORD_SHA256"},
      {"id": "HISTORICAL_GRAPH_TWO_PACKAGE", "sha256": "CANONICAL_RECORD_SHA256"}
    ]
  },
  "assessment": {
    "protocol": {"id": "NEW_FROZEN_PROTOCOL", "sha256": "CANONICAL_RECORD_SHA256"},
    "packages": [
      {"id": "FRESH_GRAPH_ONE_PACKAGE", "sha256": "CANONICAL_RECORD_SHA256"},
      {"id": "FRESH_GRAPH_TWO_PACKAGE", "sha256": "CANONICAL_RECORD_SHA256"}
    ]
  },
  "transition": {
    "from_threads": 4,
    "to_threads": 1,
    "native_runtime": {
      "version": 1,
      "environment": {
        "OMP_NUM_THREADS": "1",
        "OMP_DYNAMIC": "FALSE",
        "OMP_PROC_BIND": "close",
        "OMP_PLACES": "cores",
        "OMP_THREAD_LIMIT": null,
        "OMP_WAIT_POLICY": null,
        "GOMP_SPINCOUNT": null,
        "GOMP_CPU_AFFINITY": null
      }
    }
  }
}
```

The placeholders are intentionally not launchable. The two historical packages
must be distinct, must include the exact original creation package, and must
match the fresh workload set. Historical order is immaterial; fresh package
order must match `--packages`. The second historical reference establishes that
the second graph was not silently changed merely because the original proposal
named only one creation package.

## Admission and retained evidence

Before any evaluation, the driver reopens the pinned records through public
`get`. Both fresh packages must retain complete real execution primaries and
match the new frozen source, workload identities, ordered traversal sources,
target/lane, complete-call ROI, thread count, and strict requested runtime policy.
The new policy is exactly the eight-input map above. Both historical baselines
must retain complete passed four-thread primaries with the original compiler,
compiler version, flags, template, wrapper, and primary binary identities.
Those identities must match the corresponding fresh baseline. Canonical graph,
adjacency order, and canonical-file hashes are compared for both workloads.

Source-snapshot IDs produced by new profile packages are necessarily new. The
driver compares exact source artifact manifests, application/revision/function
context, and evaluator-owned protections instead of replacing the old ID.
Every originally selected region must exist in both fresh packages with the same
source path, byte extent, content hash, text, and function/loop kind. Region
contents and protections are checked against the actual source files.

The original four controlled OpenMP inputs must be present in the historical
build records. If the complete versioned runtime policy was not recorded there,
the receipt retains `policy: null` and explicitly lists the four unobserved
inherited variables. It never fills those unknowns from the fresh policy or the
current shell. An explicitly present malformed policy is rejected. If a valid
historical complete policy exists, every input except `OMP_NUM_THREADS` must
match the new requested policy. These are requested inputs, not evidence of
actual team size, worker placement, or a cause of observed variability.

Acquisition still uses the existing exact-candidate validator and bounded patch
replay. The unchanged original proposal, initial candidate, source artifact,
editable-file constraints, selected regions, semantic protections, interpreted
patch, provider receipt, and already-consumed repair budget remain bound. Prior
repair history is still unsupported. Existing capability checks run against the
original request; unknown or conflicting operation requirements reject reuse.
The original request is never resubmitted, and neither payload nor budget is
reset. After acquisition, the driver checks the origin digests again before
starting comparisons.

The driver retains an exact copy and file hash of the manifest, its canonical
digest, both origin and assessment references, fresh source-record digests,
observed/unknown historical runtime inputs, and the original repair budget.
A build or correctness failure remains an incomplete assessment with one
candidate round and no repair call. This mode adds no provider allowance, trial,
retry, timing budget, profitability threshold, or protocol publication. Existing
campaign wall/resource limits apply to its additional readback and replay work.

The new one-thread calibration publisher remains separate. This interface does
not bypass calibration, the shared accelerator gates, or any empirical acceptance
prerequisite. Synthetic unit records and explicit public fixture tests establish
contract behavior only; they cannot support a freeze or gain claim.

## Prospective execution supervision — 2026-09-26

Actual newly dispatched existing-candidate campaigns require
`--supervision-admission FILE --supervision-sha256 SHA --expected-commit COMMIT`,
`--outer-started ISO --outer-deadline ISO`, and the original tmux
`--pane-pid PID --pane-start-ticks TICKS`. The wrapper captures its start before
entering the socket helper and uses TERM at 14,370 seconds and KILL 30 seconds
later. The exact 14,400-second allowance includes wrapper, helper, admission,
public calls, source replay, resource observations, and final persistence.
The driver cannot start with a reset clock. All stages and finalization share
one 30-second cleanup ledger; neither stages nor failures replenish it.

The admission is `swdb.bfs.native-campaign-admission.v1`, with `id`,
`prepared_at`, `code_commit`, `runtime`, `inputs`, `bounds`, and `linux_proof`.
`runtime` comes from `campaign_runtime(COMMIT)`: complete tracked runtime and
test inventories plus Python executable/version and project configuration.
`inputs` comes from `campaign_inputs(args)` and pins the original proposal file,
existing candidate, reassessment manifest when present, ordered packages,
protocol, lane, records, and new raw/source/build directories. `bounds` must
exactly equal `NATIVE_BOUNDS`. The hashed Linux proof uses
`swdb.bfs.linux-fixture.v1`, `kind: native_campaign_owned_cleanup`,
`evidence_kind: contract_fixture`, the same runtime/code, aware start/finish,
actual pytest command, zero integer return code, and hashed stdout/JUnit.
The actual fixture start-to-finish interval must not exceed 90 seconds.
It must include both cases of
`tests/test_bfs_native_execution.py::test_linux_campaign_reaps_detached_child`
with no failures or skips. These fixtures do not establish native performance.

The native guard uses 16 GiB sampled RSS over the driver and all observed
owned descendants, including separate sessions; 16 GiB of newly retained raw,
source, build, and record artifacts, with a 4 GiB build subset; 20/24 GiB node
and global capacity at expensive-stage admission; and the existing 30/10 GiB
raw/source-build free-space reserves. Nominal sampling is five seconds with a
maximum 30-second gap or guard duration across admission and finalization.
These are sampled observations, not hard memory quotas or true-peak claims.
Native limits do not inherit the simulator helper's memory constant.

Linux subreaper/pidfd ownership captures direct PID/start identities immediately
and cleans adopted descendants before any next public stage. Shutdown failures
still attempt bounded direct-child wait and retain the original failure.
Final resource accounting, output hashes, both receipt writes, and their checks
must fit the original shared clock and cleanup ledger. The receipt retains the
complete ancestry, direct-stage, sampled, and cleanup identity union for an
independent terminal audit, which must also bind the actual outer exit and
released lane generation. The driver cannot attest its own reaping.
The monitor remains active through owned cleanup. Monitor shutdown and final
hash/write accounting use one bounded five-second reservation from the same
ledger. Failure persistence also requires an available reservation: exhaustion
does not permit an emergency write outside the budget. Admission must reject a
nonzero outer result even if the last durable receipt predates that failure.

The generic shared stage helper signals only a still-owned, unreaped session
leader. Once reaped, its numeric process group is no longer safe authority for
a signal. Its independent bounded direct wait preserves original failures, but
it claims neither same-group nor detached-descendant cleanup after leader reap.
This explicitly supersedes the old tests that expected stale numeric signaling;
new Linux Owned tests retain the required whole-tree guarantee. Newly dispatched
existing-candidate acceptance cannot use the generic path. Historical checkouts
and evidence remain unchanged.


Prospective storage correction — 2026-09-26 (Eastern Time)

The exact canonical sibling `str(runs_dir) + ".dispatch"` is part of the existing
16 GiB artifact allowance. It must already exist when the wrapper starts; the
raw, source, and build directories remain new, mutually disjoint paths. All four
directories must be canonical, with no symlink substitution. The admission is
retained at that sibling's `admission.json`. Live samples and final accounting
include wrapper/helper stdout, stderr, launch/admission files, SQLite and its
sidecars, and later terminal evidence. The existing native byte metric and
4 GiB build subset are unchanged. New canonical records outside those four trees
are added separately; a retained record view inside `.dispatch` is counted once.

The driver's last snapshot predates helper and independent terminal-audit writes.
After the full PID/start union and released lane are independently verified, call
`scripts.bfs_native_campaign.validate_storage_accounting(driver_ref, terminal_ref,
admission_ref=original_admission_ref, current=aware_iso)` with the exact hashed
references. The terminal audit must be the sibling's `terminal-validation.json`
and bind the driver, code commit, actual outcome, release, and cleanup state.
The reader reopens the caller-pinned original admission, its fixed bounds and
output roots; it does not accept driver-selected accounting credit or extra roots.
Failed outcomes stay failed even if their retained outputs fit the storage cap.

Persist the first storage readback in `.dispatch`. After all helper, outer exit,
terminal audit, cleanup-ledger audit, and storage-readback writes are complete,
perform a final read-only recount and retain its result outside the charged trees.
Any later write requires another recount. This adds no allowance or cleanup time
and establishes neither process absence, protocol qualification, nor a gain.
Historical records and active checkouts are unchanged. The local regressions are
contract fixtures; fresh actual Linux/runtime admission is still required before
a future candidate campaign.

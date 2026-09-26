# Explicit native candidate reassessment

Created: 2026-09-26 (Eastern Time).
Status: locally implemented and independently reviewed on 2026-09-26. No assessment,
protocol publication, provider call, or source export is authorized by this file.

An existing candidate can keep its original four-thread creation package while
being assessed against separately frozen one-thread baseline packages. This is
an explicit configuration transition under [spec D13](../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md):
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

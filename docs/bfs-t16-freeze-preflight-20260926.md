# T16 public freeze and comparison preflight

Created: 2026-09-26 ET. Read-only check at local HEAD `57846f424d47297bc22d62bbf063da06c7715ea8`; no protocol was frozen, no record changed, and no remote command or build ran.

No local field, version, ROI, source/model or diagnostic-identity mismatch was found. Both requests passed the real current `_validate_settings(..., require_simulation_identity=True)` and initial-version checks. All four protocol/role diagnostic-build validations passed. The sole existing local protocol is unrelated; neither logical T16 name exists locally. Host must confirm the same before publication and reopen its actual external artifact bytes.

| Request | Bytes | File SHA-256 | Settings SHA-256 |
|---|---:|---|---|
| author-reference-freeze-v1.yaml | 10582 | ade4b75e4a59181f3582645b808675eaa5e88519689255749a56070e7f0eba96 | a2b5ba1101647802a393ab416837e736c5e6f2917056a2240576a0fb7aa46dc7 |
| author-matched-control-freeze-v1.yaml | 10652 | 0208354fccf9e7c2b13eb340b1fcfa121f8a443ccac98ba72f8e558b1a339705 | 19b7319d8c2775f5e9f44d0091c3bd29968465701b6105e3bb283b49e1a38a5b |

The complete fixed plan, record, binary, simulator, source, collector and verifier hashes are in `/private/tmp/bfs-t16-freeze-preflight-20260926.json` (SHA-256 `6a2dbaf3558aa28c8d453d45148fc71f3b204ebebf1331f9a49fbc8095d1469b`). Its four actual diagnostic identity checks reuse existing compilation metadata, not new builds.

Both requests use message1.0 and initial protocol version1; their comment's v2 means the selected `dx100.bfs.verifier.v2`, not a second published protocol. They freeze uniform22 workload `bfs-20260925-uniform22.f23b09bb0c0601b5`, actual source2796003, four guest cores, two real repeats, zero warmups and `bfs.dx100.traversal.v1`. Artifact scalar retains10MiB/20-way LLC against MAA8MiB/16-way; matched control uses8MiB/16-way in both roles. The exact modeled command vectors agree with current configuration construction, contingent on the pinned remote Ramulator file.

The source and primary binaries are unchanged author artifacts. Diagnostic binaries remain separate and their two region mappings/collector hashes match retained compilation definitions. Primary instrumentation matches current verifier/parser/observer hashes and post-ROI trace treatment. Complete-call original-adjacency fields belong to A2's different wrapper and must not be inserted into this author-traversal policy. Actual primary and diagnostic executions still need successful v2 checks; preflight supplies no correctness or timing claim.

## Prospective public commands

After successful A2 and ordinary host admission, let `CODE` name the prepared final campaign checkout, `PY` the exact admitted Python, and `OUT` a new external raw directory. Run these within the separately bounded metadata operation. Use an external SQLite path explicitly: the CLI default creates an ignored checkout-root `build/` directory, which conflicts with later clean-root admission.

```sh
"$PY" -m swdb freeze-protocol "$CODE/.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-reference-freeze-v1.yaml" --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/artifact.freeze.json" 2> "$OUT/artifact.freeze.stderr"
"$PY" -m swdb freeze-protocol "$CODE/.scratch/bfs-rewrite-evaluation-2026-09-25/requests/author-matched-control-freeze-v1.yaml" --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/control.freeze.json" 2> "$OUT/control.freeze.stderr"
"$PY" -m swdb get "$ARTIFACT_ID" --chain --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/artifact.get-chain.json" 2> "$OUT/artifact.get-chain.stderr"
"$PY" -m swdb get "$CONTROL_ID" --chain --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/control.get-chain.json" 2> "$OUT/control.get-chain.stderr"
```

Retain each actual exit; do not continue past a failed freeze or retry a logical name. Obtain `ARTIFACT_ID` and `CONTROL_ID` from each successful returned JSON's `id`. The identity includes actual `frozen_at`, so neither suffix nor canonical output filename is knowable beforehand. Check kind=protocol, requested_id matches its YAML, version1, state=frozen, exact settings/workload identities and `verify_immutable`. Fresh chain output is `{root,records}`: `root` must equal that returned ID and `records[ID]` must equal the freeze output.

Set admission `protocols.artifact/control` to `{id: returned ID, sha256: artifacts.digest(full returned record)}`. This digest is neither the YAML file hash, settings hash nor protocol `identity_sha256`. Retain all four distinctly. Import/commit the actual two `records/protocols/<returned ID>.yaml` files together with A2's three canonical outputs before fixing final campaign HEAD and running its standard Linux proofs. These operations do not consume or recreate a native standalone readback.

## After all four actual series

Each series returns its own `.aggregate` ID and two primary evaluations/packages. The two MAA series remain fresh, separately protocol-bound executions. Prepare two public comparison JSONs, with a new result ID for each:

```json
{
  "message_version": "1.0",
  "id": "<new comparison result ID>",
  "protocol": "<actual artifact or control protocol ID>",
  "comparison_baseline": "dx100-bfs-scalar",
  "baseline_evaluation": "<matching returned scalar aggregate ID>",
  "candidate_evaluation": "<matching returned MAA aggregate ID>",
  "region_packages": {
    "<scalar s0/r0 primary evaluation ID>": "<its returned package ID>",
    "<scalar s0/r1 primary evaluation ID>": "<its returned package ID>",
    "<MAA s0/r0 primary evaluation ID>": "<its returned package ID>",
    "<MAA s0/r1 primary evaluation ID>": "<its returned package ID>"
  }
}
```

```sh
"$PY" -m swdb compare-evaluations "$OUT/artifact.compare.request.json" --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/artifact.compare.json" 2> "$OUT/artifact.compare.stderr"
"$PY" -m swdb get "$COMPARISON_ID" --chain --records "$CODE/records" --db "$OUT/swdb.sqlite" --format json > "$OUT/artifact.compare.get-chain.json" 2> "$OUT/artifact.compare.get-chain.stderr"
```

Repeat those two commands for control using its own exact request/result. A rejected comparison is retained with exit1; missing or incompatible evidence cannot become speedup1. Inspect the returned decision and evidence classification, not exit status alone. Correct regressions or no gain do not authorize strategy search; positive gain is not required for T16. Remote raw evidence and actual result/cleanup review remain outstanding.

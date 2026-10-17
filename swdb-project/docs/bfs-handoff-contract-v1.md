# BFS handoff contract, format 1.0 (provisional)

Created: 2026-09-27 16:55 ET. Updated: 2026-09-27 17:05 ET.

This is the provisional collaborator contract from spec decision D06. It is our
proposal and has not been negotiated with Peter or Josh. No live collaborator
agent has submitted anything. Every submission referenced here came from a
representative **test client** (`producer.test_client: true`), and every message
states `live_collaborator_integration: false`.

## Three linked messages

`swdb handoff-message KIND ID` renders each message from an existing master
record. Rendering reads records only. It runs nothing and changes nothing, and it
never upgrades evidence.

| Message (`KIND`) | Rendered from | `format` |
|---|---|---|
| Profile package (`profile_package`) | a `profile_package` record | `swdb.bfs.handoff.profile_package` |
| Rewrite proposal (`rewrite_proposal`) | a `proposal` record (the retained request plus its handling) | `swdb.bfs.handoff.rewrite_proposal` |
| Evaluation result (`evaluation_result`) | an `evaluation` record plus the comparisons and packages that reference it | `swdb.bfs.handoff.evaluation_result` |

```sh
python3 -m swdb handoff-message profile_package   PACKAGE_ID    --format json
python3 -m swdb handoff-message rewrite_proposal  PROPOSAL_ID   --format json
python3 -m swdb handoff-message evaluation_result EVALUATION_ID --format json
```

### Common envelope

| Field | Meaning |
|---|---|
| `format`, `format_version` | Message kind and contract version (`1.0`). This version is independent of the record `schema_version` (currently `0.4`) and of the request `message_version`. |
| `id` | Stable message identity, `KIND/RECORD_ID`. |
| `record` | Source record ID, kind, `schema_version`, and `sha256`: the content digest of the record, so a reader can detect a changed record. |
| `producer` | Producer of the source record. Evaluator-owned records name `swdb` / `operator`. |
| `provenance` | `submission_producer`: the SW/HW producer of the originating proposal. Also `test_client`, `live_collaborator_integration: false`, the record's own provenance, and a plain-language statement. |
| `inputs` | References to input records (`id`, `kind`, `sha256`, `present`/`missing`). A missing input stays listed. |
| `content` | The kind-specific body below. |

YAML and JSON encode the same logical message (`--format yaml|json`).

### Profile package content

The fields cover the D06 row: exact identity, ROI, ranked regions and timing
scope, dynamic memory observations, source/build context, correctness and edit
constraints, applicable strategies, and available hardware interfaces.

- `identity`: implementation, source snapshot and source hash, candidate,
  evaluation, workload (family, canonical adjacency hash, size), sources,
  target and configuration, threads.
- `roi`: ROI ID, the primary quantity as `[basis, quantity]` pairs, trial count,
  and primary binary hash.
- `ranked_regions`: rankings, discovered regions with metrics and basis, discovery
  coverage and limits, and correspondence to the previous profile. Resolved
  regions are counted and unresolved regions are listed. There is never a
  region gain claim.
- `dynamic_memory`: each observation with its collector/model, basis, scope,
  attribution granularity, and raw-artifact hash.
- `source_build_context`, `correctness_and_edit_constraints` (editable files,
  preserved correctness and ROI, protected inputs), `applicable_strategies` (a
  per-strategy count of outcomes, always `performance_guarantee: false`), and
  `hardware_interfaces`.

### Rewrite proposal content

- `producer` (role `sw` or `hw`, `test_client`), `source_profile_package`,
  `target` (implementation, source snapshot/hash, region IDs), `strategy`,
  `intent`, and `parameters`.
- `requirements`: edit constraints, `required_operations` (operation, interface,
  interface version, model revision), `hardware_target`, and
  `require_executable_backend`.
- `payload`: one of four forms: `natural_language`, `structured_instructions`,
  `annotated_source`, or `patch`. Its `sha256` is always present. Text over 4 KiB
  appears as an excerpt with its byte count and hash. Retrieve the full content
  with `swdb get`.
- `handling`: outcome (`candidate_created`, `rejected`, `unresolved`, `failed`),
  the bounded provider settings, repair budget and use, and interpretation
  summary, unresolved items, and changed files. It also lists attempts and the
  candidate ID.

### Evaluation result content

- `result_class` separates `missing_candidate`, `incorrect_candidate`,
  `incomplete_evaluation`, and `completed_evaluation`. Incomplete measurement
  (interrupted, timed out, missing observation, budget exhausted) is never
  reported as an incorrect candidate, and the reverse also holds.
- `proposal`, `candidate`, and `candidate_state`.
- `software_hardware_pair`: implementation, candidate and binary hashes, target,
  basis (`measured` for native, `simulated` for DX100), backend configuration,
  model, and threads.
- `comparison`: explicit `comparison_baseline`, the frozen `protocol` and its
  exact `protocol_binding`, `shared_protocol_bindings`, `protocol_sampling`,
  and every comparison result that names this evaluation. Each comparison
  result carries its decision, ratio, and interval.
- `stage_outcomes`, `outcome`, `correctness` (state, verifier, checks, and passes),
  `roi_measurements` (the ROI and its `[basis, quantity]` pairs; native seconds
  and simulated ticks are never mixed), `instrumentation`, `region_measurements`,
  `profiling`, `raw_artifacts` (host plus path; a path names the host that
  produced it), and `incompleteness`.
- `performance_claim` is `frozen_policy_gain` only when a comparison under a
  frozen policy recorded a gain for this candidate. Otherwise it is `none`.
  Inconclusive, no-gain, regression, and missing outcomes are all `none`.

## Current record formats reflected (2026-09-27)

| Change | Where it appears in the messages |
|---|---|
| **`full_files` edit format** (opt-in; the provider returns complete files and SWDB computes the diff) | `rewrite_proposal.content.handling.provider.edit_format`, `.interpretation.edit_format`, and `.interpretation.changed_files`. The default remains `patch`. |
| **`stream-json` provider capture** (partial output and progress retained on timeout) | `rewrite_proposal.content.handling.provider.output_format` |
| **R10 shared protocol bindings**: one simulator execution serves several frozen protocols only when every role identity matches | `evaluation_result.content.comparison.shared_protocol_bindings`, which lists the additional protocol IDs. The execution retains one exact binding per protocol, and each comparison selects its own binding. |
| **R11 determinism evidence**: a simulated policy may fix one replay per ordered source | `evaluation_result.content.comparison.protocol_sampling.determinism` (`basis: deterministic_simulator_replay.v1` with named evidence) |
| **R12 post-ROI CPU**: an opt-in `AtomicSimpleCPU` verifier continuation after the ROI seal | `evaluation_result.content.instrumentation.post_roi_cpu` |

R10 through R12 are implemented on branch
`codex/bfs-t16-reference-20260927-b1` (commit `974bda5`). Records that use them
are not yet on `main`. The renderer copies these fields from the records
verbatim, so no renderer change is needed when those records arrive. Until then,
the fields are empty or absent in the checked-in examples.

## Examples

[`bfs-handoff-examples/`](bfs-handoff-examples/) holds messages rendered from
actual master records (see its `manifest.json`):

| File | Shows |
|---|---|
| `profile-package.dx100-patch-kronecker.json` | Complete native package of the evaluated T18 candidate: 31 regions, 18 Callgrind memory rows, and correspondence with five unresolved changed regions |
| `rewrite-proposal.sw-patch.json` | SW test-client patch that created the T18 candidate |
| `rewrite-proposal.hw-annotated-full-files.json` | HW test-client annotated source with seven required DX100 operations, captured with `stream-json` and `full_files`; the candidate was created but is not yet evaluated |
| `rewrite-proposal.hw-annotated-failed.json` | Retained failed HW submission (context5: corrupt provider patch; no candidate) |
| `evaluation-result.dx100-patch-kronecker.json` | Completed native evaluation; the frozen-policy comparison is **inconclusive** (1.0004), so `performance_claim: none` |
| `evaluation-result.dx100-patch-uniform-interrupted.json` | Retained interrupted b1 evaluation (`incomplete_evaluation`), which is not an incorrect candidate |

Regenerate the examples, or check that they are current, with:

```sh
python3 scripts/bfs_handoff_examples.py          # rewrite
python3 scripts/bfs_handoff_examples.py --check  # exit 1 if any example is stale
```

When accelerated (T17/T20) evaluations land, add their proposal/evaluation IDs
to the manifest and regenerate. No example is a gain claim.

## Compatibility

- A change that adds a field is `1.x`. A change that removes or renames a field,
  or changes its meaning, is `2.0`. Exact field spelling, enums, and transport
  remain open for review with the collaborators.
- A reader must not treat an absent field as a neutral value. Missing
  correctness, missing comparisons, and missing measurements stay explicit.
- Kernel identity, provenance, and comparison semantics come from the records
  (ADR 0001, ADR 0005). A new transport or collaborator client does not
  redefine them.

# Explorer adapter: DX100 tile candidates pending validation

Eric's `contract.yaml` is now consumable through the existing parameter explorer
CLI. It produces six **source-supported candidate proposals**, not an admitted
legal parameter space:

`1024, 2048, 4096, 8192, 16384, 32768` tile elements.

Each proposal remains `candidate_pending_validation`, with
`independently_validated: false`, `ready_to_execute: false`, and
`eligible_for_performance_ranking: false`. The admitted-configuration list is empty.
No benchmark, compiler, simulator, model API or job launcher runs in this adapter.

## What is imported

- All 26 native model knobs and the source reference defaults. Only
  `num_tile_elements` varies; the other 25 values are **proposed reference freezes**
  until actual launcher/config.ini settings are bound.
- All 12 coupling records, 17 source-file hashes, unresolved-domain notes and
  author-result provenance. Source-supported values stay distinct from validated
  values and from legal domains; those legal domains remain null.
- Matching `TILE_SIZE` and `NUM_CORES` compile constants, the fixed API's per-core
  tile/register constants, expected CLI values and knobs requiring direct
  SimObject configuration. These are declarative build requirements, not executable
  commands. In particular, false Boolean options must not become enabling flags.
- Requests for binary/config.ini hashes, actual topology, workers, input/root/ROI,
  mapping review, correctness, intended-path, resource/address and timing evidence.

The adapter checks the contract and published-result file hashes against Eric's
verification record, source/design editions, inventory and candidate list. It
cross-checks overlapping pinned source hashes against the selected candidate's
source evidence. It does not independently rerun Eric's AST inspection or fetch
and re-audit every source file. The hash checks establish snapshot consistency,
not functional or timing correctness.

The current adapter intentionally supports this first four-core, one-instance,
eight-tile/eight-register-per-core profile. Changes to the source edition, knob
inventory, candidate domain, API geometry or validation claims require explicit
adapter review. There is no silent promotion of a revised contract.

## Mapping the existing catalog names

| Catalog field | Native model field | Treatment |
|---|---|---|
| `tile_elements` | `num_tile_elements` | Preserve the catalog's 16,384 reference; do not overwrite it |
| `effective_tile_elements` | `num_tile_elements` | Proposed tile value for this validation candidate |
| `row_table_rows_per_slice` | `num_row_table_rows_per_slice` | Proposed reference freeze, pending effective config |
| `row_table_entries_per_subslice_row` | `num_row_table_entries_per_subslice_row` | Proposed reference freeze, pending effective config |

Other native knobs remain in the imported inventory; they are not silently added
as validated knobs to the catalog. Original candidates and their
`selected_configuration` fields remain unchanged.

The source support belongs to the pinned authors' BFS implementation. Applying it
to our selected read-offload candidate or the separate five-tile hybrid mapping
still needs a mapping review. The adapter does not transfer an eight-tile kernel's
resource or correctness claims to another implementation.

## What remains blocked or unknown

The adapter checks only straightforward necessary arithmetic bounds for the
proposed reference tuple: uint16 tile-length representability, operand namespace,
and core/instance divisibility. Passing these checks is not full legality.

Execution remains blocked pending actual DRAM topology and row-table slice checks,
effective config.ini values, matching rebuilt binary/constants, worker ownership,
selected mapping, and request-table/address/resource bounds. Source support alone
does not supply these bindings. The generated receipt template requests the later
correctness and intended-path results; it is not an admission receipt itself. Its `input_sha256` is for the actual benchmark
input/graph bundle; the top-level binding of the same name identifies the supplied
feature report. These scopes must not be substituted for one another.

`TILE_SIZE` changes batching/fallback behavior in the pinned BFS, so each point is
a hardware/software experiment. Compile constants and simulator values must match;
reusing an old binary is not valid just because the graph is unchanged.

Source-derived scratchpad payload bytes are reported separately from physical
area: `4 × cores × tiles_per_core × tile_elements`, counting aliased mappings once.
At the reference point this is 2 MiB. It excludes separate table/control costs.
The 32-tile/28-nm area proxy is retained as a **source reference only**; the adapter
does not execute it, fill an area estimate, or interpret it as a general cost model.
Latency, area, power and cost-model fields remain null. The linked detailed cost
documents referenced by Eric's source contract are still absent from this checkout.

## Run the real-contract example

From the repository root, choose a fresh output directory:

```sh
.venv/bin/python tools/demo_dx100_parameter_candidates.py \
  --output-dir .cache/dx100-domain-candidates
```

This builds the normal source-bound BFS/DX100 candidate in memory, imports Eric's
contract and emits the six-point review bundle. The
[checked-in summary](../../../examples/dx100-parameter-candidates/summary.yaml)
contains the six candidate identities and their pending/null status. The full
source snapshots and per-point requests are generated locally.

For an existing DX100 handoff, use its input/catalog hashes from the parent
hardware request or intrinsic-draft provenance:

```sh
.venv/bin/python -m archevolve.parameter_cli dx100-candidates \
  --candidate path/to/candidate.yaml \
  --input-sha256 INPUT_HASH --catalog-sha256 CATALOG_HASH \
  --output-dir .cache/dx100-domain-candidates
```

The contract, verification and published-result paths default to this folder.
Override them together using `--contract`, `--verification`, and
`--published-results` when reviewing a different snapshot. `--max-candidates 1..6`
emits a clearly marked prefix of the six points; it does not expand the domain.
Output files are never overwritten.

## Bundle contents and next step

- `candidate-domain.yaml`: imported source-supported profile, aliases, constraints
  and evidence, with null legal domains.
- `exploration.yaml`: six pending proposals, identities and execution blockers.
- Per candidate: `configuration-proposal.yaml`, `build-validation-request.yaml`
  and `receipt.template.yaml`.
- `strict-space.template.yaml`: the original conservative explorer template,
  still unresolved. It cannot enumerate admitted settings from these candidates.
- Source snapshots and a manifest with input/artifact content hashes.

The candidate-domain format is intentionally distinct from
`bounded-parameter-space-v0.1`; the existing strict enumerator/comparator cannot
consume it as an approved domain. No importer auto-activates a proposal or turns
published author results into a measured local result. Promotion into a reviewed
parameter space and evaluator cohort remains a separate step after complete
configuration, mapping and validation evidence is available.

Tests:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_dx100_parameter_adapter.py' -v
```

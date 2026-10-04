# Records and queries

Updated: 2026-09-30 (Eastern Time).

[Guide](README.md) · [Complete table and query reference](reference/database.md)

## Storage and identity

Edit or add YAML records, then validate. `swdb build` regenerates SQLite from
those records. Queries refresh a stale index; BFS queries load one record
snapshot and check external artifacts separately. An up-to-date index says
nothing about whether a remote binary or raw measurement is available.

Record IDs remain stable. To replace a record, create a new ID and mark the old
record `deprecated` with `deprecated_by`; leave it present so references resolve.
Records start as `draft` and become `reviewed` after human review.

## Read the evidence before the number

| Basis | Meaning |
|---|---|
| `measured` | Produced by execution on a real machine |
| `simulated` | Produced by a model, including Cachegrind |
| `code_reading` | Established from identified source |
| `reported` | Stated by a cited person or publication |
| `inferred` | Derived by a stated rule |
| `unknown` | Not established; value must be `null` |

Unknown is never false. Keep basis, scope, input, thread count, and tool with each
metric. A whole-run count includes work that a kernel-only or ROI count may omit.
A complete profile package describes collection completeness; correctness and
performance qualification are separate checks.

Strategy queries return `legal`, `illegal`, or `undetermined`. Known
contradictions are illegal; missing semantic facts stay unresolved. Read
`check_by_hand` as well as the outcome. Reported benefit is a source claim,
not a measured speedup for your implementation.

## Common queries

Run inside `ArchEvolve/swdb-project/` (`cd swdb-project` from the monorepo root):

```sh
# Find patterns and the strategies that could apply.
python3 -m swdb find --shape ranged_indirect --update read
python3 -m swdb find --strategy packing
python3 -m swdb strategies --pattern gapbs-pr-jacobi/gather-contrib

# Retrieve records and exact workflow history.
python3 -m swdb get RECORD_ID --chain --format json

# Search package-backed regions in either direction.
python3 -m swdb profile-strategies PACKAGE_ID
python3 -m swdb strategy-regions loop_tiling --package PACKAGE_ID

# Inspect all stored record kinds.
python3 -m swdb sql 'select kind, count(*) from records group by kind'
```

Uppercase IDs are placeholders. `implementations KERNEL --applies STRATEGY`
returns historical ancestry-based profile pairs. For an explicit profile pair,
use `compare IMPLEMENTATION --baseline BASELINE --profile PROFILE
--baseline-profile BASELINE_PROFILE --protocol PROTOCOL`. Its diagnostic ratio
does not replace the frozen evaluation workflow's gain decision.

## Tables

| Group | Tables |
|---|---|
| All records and index metadata | `records`, `meta` |
| Source and computation | `applications`, `kernels`, `implementations`, `implementation_contexts` |
| Memory access | `access_patterns`, `steps` |
| Inputs and machines | `inputs`, `input_properties`, `machines`, `machine_flags` |
| Strategies and intrinsics | `strategies`, `strategy_effects`, `strategy_intrinsics`, `applied_strategies`, `implementation_intrinsics`, `intrinsics`, `intrinsic_extensions` |
| Measurements | `profiles`, `metrics` |

The `records.json` column contains every record kind, including workflow records.
Use `json_extract` for fields without a dedicated table. In semantic/property
columns stored as JSON text, distinguish `'true'`, `'false'`, and `'null'` and
check the accompanying basis. See the reference for exact columns and joins.

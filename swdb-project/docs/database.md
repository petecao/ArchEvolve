# Records and queries

Updated: 2026-10-11 (Eastern Time): tables carry the `swdb_` prefix.

[Guide](README.md) · [Complete table and query reference](reference/database.md)

## Storage and identity

Research records are YAML; typed-library entries and pinned code live separately
in `library/`. Validate both. `swdb build` regenerates SQLite from them.
Queries refresh a stale index; BFS queries load one record
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
| `estimated` | Analytic time bound from counted work and target parameters |
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
python3 -m swdb sql 'select kind, count(*) from swdb_records group by kind'
```

Uppercase IDs are placeholders. `implementations KERNEL --applies STRATEGY`
returns historical ancestry-based profile pairs. For an explicit profile pair,
use `compare IMPLEMENTATION --baseline BASELINE --profile PROFILE
--baseline-profile BASELINE_PROFILE --protocol PROTOCOL`. Its diagnostic ratio
does not replace the frozen evaluation workflow's gain decision.

## Tables

| Group | Tables |
|---|---|
| All records and index metadata | `swdb_records`, `swdb_meta` |
| Source and computation | `swdb_applications`, `swdb_kernels`, `swdb_implementations`, `swdb_implementation_contexts` |
| Memory access | `swdb_access_patterns`, `swdb_steps` |
| Inputs and machines | `swdb_inputs`, `swdb_input_properties`, `swdb_machines`, `swdb_machine_flags` |
| Strategies and intrinsics | `swdb_strategies`, `swdb_strategy_effects`, `swdb_strategy_intrinsics`, `swdb_applied_strategies`, `swdb_implementation_intrinsics`, `swdb_intrinsics`, `swdb_intrinsic_extensions` |
| Measurements | `swdb_profiles`, `swdb_metrics` |
| Typed library | `swdb_library_entries`, `swdb_library_dependencies`, `swdb_library_clauses`, `swdb_library_pattern_keys`, `swdb_library_pattern_key_steps` |
| Statement observations | `swdb_statements`, `swdb_statement_steps`, `swdb_statement_facts` |

The `swdb_records.json` column contains every record kind, including workflow records.
Use `json_extract` for fields without a dedicated table. In semantic/property
columns stored as JSON text, distinguish `'true'`, `'false'`, and `'null'` and
check the accompanying basis. See the reference for exact columns and joins.

LANL main-database access is unimplemented. The [crosswalk](compatibility/README.md)
is a validated compatibility draft, separate from research records and queries.

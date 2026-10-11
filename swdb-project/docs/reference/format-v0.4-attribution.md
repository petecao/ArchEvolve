# Attribution reports (`swdb.attribution.v1`)

Created: 2026-10-11 (Eastern Time), fine-grained attribution ticket 02.
Updated: 2026-10-11 ET (ticket 05: library, intrinsic and offload labels; ticket 07: resource
floor, floor headroom and ranking).
Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md`.

**In one line:** `swdb attribute` takes two saved estimates and the two source trees they
counted, and says how much time is in untouched, agent-rewritten and unattributed code.

## What it does, in order

1. Diffs the two source trees itself (never a stored candidate diff).
2. Turns each changed run of lines into one **rewrite site**.
3. Labels every region of both estimates with a **code origin** by file and line.
4. Sums each origin group per trial, then takes the median per group.
5. Computes each region's **resource floor** and **headroom**, and ranks the candidate's
   regions by floor headroom (ticket 07).
6. Writes one validated `attribution` record and indexes it into SQLite.

It only reads saved records. It never re-estimates and never binds a protocol.

## Run it

```sh
python -m swdb attribute --records records \
  --baseline-estimate <estimate ID> --candidate-estimate <estimate ID> \
  --baseline-source <source_snapshot or candidate ID> \
  --candidate-source <source_snapshot or candidate ID> \
  --id <new report ID> --format json
```

It refuses (exit 1, nothing written) when:

- the two estimates differ in `input`, `target_description_sha256`, `threads` or
  `evidence_kind`;
- a source record is not the one its estimate counted (a `candidate` source must be the
  estimate's candidate subject; a `source_snapshot` must name the implementation subject);
- a source tree on disk no longer matches its recorded artifact hash;
- a characterization differs from the hash its estimate pins.

## Labeling rules (this version)

Ticket 04 widens these rules. Today:

| Rule | What it means |
|---|---|
| Path | A region's path is made relative to its own side's tree. A path in neither tree (for example a system header) cannot have changed, so the region is `untouched`. |
| Span | `[min, max]` of the region's start line and its access patterns' lines in the same file. |
| Rewritten | The span overlaps a rewrite site on the same side. |
| Unattributed | The region has no source path or no line. |
| Region IDs | Never compared across sides; they embed subject IDs and lines. |

A region whose ID has no catalog loop still gets a real label from its file and line.

### Library, intrinsic and offload labels (ticket 05)

A region **inside a rewrite site** is relabeled by what it executes. Highest precedence wins:

| Origin | Signal in the counted characterization |
|---|---|
| `offload_command` | an `accelerator_calls[]` entry (a command bound by the functional observation contract) with a nonzero `execution_count`; named by its `event` |
| `intrinsic` | an executed call (`unmodeled_calls[]`, aggregate or any trial) named after a saved `intrinsic` record's C `name`, plain or as an Itanium source name (`12__dxc_gather` inside a mangled name) |
| `library_call` | an executed call naming a typed-library operation's `location.symbol` the same way, or the region or one of its accesses located in that operation's `location.path` (inlined library code keeps its header's file and line) |
| `agent_rewritten` | none of the above |

- Regions outside every site are never relabeled, so a baseline libc or C++ standard library
  call (`strlen`, `std::sort`, `/usr/include/...`) stays `untouched`.
- Typed-library operations come from `--library` (default: the `library/` folder beside the
  records folder). Intrinsics come from the records folder.
- Not detected yet: ISA intrinsics already lowered to `llvm.*` calls, and inlined library code
  in a region whose own start line lies outside the source tree (ticket 04's inlining rule).

## Record fields

Envelope fields are as for every record. `created` and `updated` are the latest `updated`
date of the four inputs, so the same inputs give a byte-identical record.

| Field | Meaning |
|---|---|
| `format` | `swdb.attribution.v1` |
| `baseline_estimate`, `candidate_estimate` | `{id, sha256}` of each saved estimate (`sha256` = record content hash) |
| `baseline_source`, `candidate_source` | `{kind, id, sha256, artifact_sha256}` of each source record and its tree |
| `target_description` | `{id, sha256}` the two estimates share |
| `input`, `threads`, `evidence_kind` | copied from the estimates, which must agree |
| `catalog` | `{kind, id, sha256}` of every `intrinsic` record or `library_operation` entry that labeled a region, sorted by ID; `swdb validate` re-checks intrinsic pins |
| `rewrite_sites` | one row per changed run of lines (below) |
| `regions` | one row per region of each estimate (below) |
| `groups` | one row per code origin, always in the order untouched, agent_rewritten, unattributed (below) |
| `whole_program` | totals and whole-program ratios (below) |
| `ranking` | the candidate's regions in next-iteration order (below) |
| `identity_sha256` | content hash of the record without this field; `swdb validate` checks it |

### `rewrite_sites` rows

| Field | Meaning |
|---|---|
| `id` | `site.<n>`, numbered in path then line order |
| `path` | file path relative to the source tree |
| `baseline_lines`, `candidate_lines` | `[first, last]` changed lines on each side; an empty side is `[p, p - 1]`, the insertion point before line `p` |
| `baseline_regions`, `candidate_regions` | region IDs whose span overlaps the site on that side |

### `regions` rows

| Field | Meaning |
|---|---|
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `origin` | `untouched`, `agent_rewritten`, `library_call`, `intrinsic`, `offload_command` or `unattributed` |
| `reason` | `overlaps_rewrite_site`, `offload_command_in_site`, `intrinsic_in_site`, `library_operation_in_site`, `no_changed_line`, `outside_source_tree` or `no_source_location` |
| `path`, `lines` | relative path and `[first, last]` span; null when unknown |
| `sites` | IDs of the rewrite sites the region overlaps |
| `seconds` | the estimate's own per-region seconds (a diagnostic median; groups do not use it) |
| `evidence` | inside a site: every signal found, `{origin, name}`, highest precedence first (`name` is the event, intrinsic ID or library operation ID); empty otherwise |
| `resource_floor` | the region's resource floor (below) |
| `headroom` | list of `{limit, value, reason}`, one per named limit; today only `resource_floor` |

### `groups` rows

Group seconds are summed per estimate trial (a region absent from a trial counts 0 s), then
medianed. A single-run estimate is one trial. Group medians are **never rescaled**, so
groups need not add up to the total.

| Field | Meaning |
|---|---|
| `origin` | the code origin group; `agent_rewritten` holds every region inside a rewrite site, whatever its origin |
| `baseline_seconds`, `candidate_seconds` | median per-trial group sum on each side; null if any region in it is unknown |
| `baseline_share`, `candidate_share` | group seconds ÷ that estimate's total `seconds` |
| `realized_speedup` | baseline seconds ÷ candidate seconds |
| `drift` | untouched group only: candidate seconds ÷ baseline seconds (1.0 = no side effect) |
| `unknown` | `{side, region, missing}` for each unknown region; `missing` lists its bounds' reasons |
| `origins` | `agent_rewritten` group only: one row per origin in precedence order (`offload_command`, `intrinsic`, `library_call`, `agent_rewritten`) with `origin`, `baseline_seconds`, `candidate_seconds`, `baseline_share`, `candidate_share` and `unknown`, computed the same per-trial way |

A ratio is null when an operand is unknown or the denominator is 0.

### `whole_program`

| Field | Meaning |
|---|---|
| `baseline_seconds`, `candidate_seconds` | the estimates' own totals |
| `total_speedup` | baseline total ÷ candidate total |
| `amdahl_ceiling` | baseline total ÷ untouched candidate seconds: the most any further work on the rewritten part could give |
| `unknown` | every unknown region of both sides, as in `groups` |

### Resource floor (ticket 07)

**In one line:** the fastest the region's counted work could run at the target description's
own rates, ignoring latency and every overhead. It is a limit, never an estimate.

- Floor = max(compute bound, useful-bytes bandwidth bound), spec F6.
- Both terms come from the unchanged `compute_throughput` and `streaming_bandwidth` mechanism
  models, called exactly as the estimator calls them, on the region's own counts.
- Only the estimate's pinned target description is read (`target_description_snapshot`, checked
  against its hash). No other description, no `cache_fit` hit bandwidth, no latency, row, queue or
  overhead mechanism, and no theoretical-peak parameter.
- If the description lacks a model, that term has no rates: zero work gives 0 s, any work gives
  an unknown term naming the missing rate (for example `bytes_per_s`). The floor is then unknown,
  never 0 and never borrowed from another description.
- Trials follow the estimate's rule: floor per trial (a region absent from a trial counts 0 s),
  then the median. So the floor is never above the region's own `seconds`; `swdb validate`
  rejects a record where it is.

| Field | Meaning |
|---|---|
| `seconds` | the floor; null when a term is unknown |
| `limiting_term` | the term with the larger median, `compute_throughput` or `streaming_bandwidth`; null when unknown |
| `terms` | `{model, in_description, seconds, missing}` for the two terms, in that order; `in_description` is false when the description has no such mechanism |
| `missing` | union of the terms' missing counts and rates |

### `headroom` entries

| Field | Meaning |
|---|---|
| `limit` | the named limit: `resource_floor` (ticket 08 adds `catalog_bound`) |
| `value` | region `seconds` ÷ the limit's seconds; null when it cannot be a number |
| `reason` | null, or why `value` is null: `unknown_estimate`, `unknown_limit` or `zero_limit` |

### `ranking` rows

Only candidate regions are ranked: they are what the next iteration starts from. Known floor
headrooms come first, largest first (ties by region ID). Regions whose headroom is null follow
in region-ID order, in their own tier, never mixed with known ones (F7). Ticket 08 puts a
remaining-gain-bound tier before the floor tier.

| Field | Meaning |
|---|---|
| `position` | 1-based place in the whole list |
| `side` | always `candidate` |
| `region` | the candidate estimate's region ID |
| `tier` | `floor_headroom`, or `unknown` for a null headroom |
| `limit` | the limit the value uses: `resource_floor` |
| `value` | the floor headroom; null in the `unknown` tier |
| `reason` | the headroom's null reason, else null |

## Worked example (the test fixture)

Baseline 100 s: untouched 40 s, rewritten 60 s. The candidate's rewritten part takes 30 s.

| Quantity | Value |
|---|---|
| Rewritten share of the baseline | 60 / 100 = 0.6 |
| Rewritten realized speedup | 60 / 30 = 2.0 |
| Untouched drift | 40 / 40 = 1.0 |
| Total speedup | 100 / 70 ≈ 1.43 |
| Amdahl ceiling | 100 / 40 = 2.5 |

The SQLite tables are in [database.md](database.md#attribution-tables).

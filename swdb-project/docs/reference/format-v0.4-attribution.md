# Attribution reports (`swdb.attribution.v1`)

Created: 2026-10-11 (Eastern Time), fine-grained attribution ticket 02.
Updated: 2026-10-11 ET (ticket 05: library, intrinsic and offload labels; ticket 07: resource
floor, floor headroom and ranking; ticket 06 + 07 merge: floors in `this_iteration`; ticket 04:
merged sites, `mixed`, inlined pieces, matched regions, unattributed flag; ticket 08: catalog
bound, remaining gain bound and the full ranking; ticket 09, 2026-10-11 21:17 ET: the split check;
ticket 10, 2026-10-11 21:31 ET: `site_finder.kernel` and `site_finder.target`).
Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md`.

**In one line:** `swdb attribute` takes two saved estimates and the two source trees they
counted, and says how much time is in untouched, agent-rewritten and unattributed code.

## What it does, in order

1. Diffs the two source trees itself (never a stored candidate diff).
2. Turns each changed run of lines into a span, and merges spans one region overlaps into one
   **rewrite site**.
3. Labels every region of both estimates with a **code origin** by file and line.
4. Sums each origin group per trial, then takes the median per group.
5. Computes each region's **resource floor** and **headroom** (ticket 07).
6. Given site-finder regions, computes each region's **catalog bound**, and ranks the
   candidate's regions by **remaining gain bound**, then floor headroom (ticket 08).
7. Writes one validated `attribution` record and indexes it into SQLite.

It only reads saved records. It never re-estimates and never binds a protocol.

## Run it

```sh
python -m swdb attribute --records records \
  --baseline-estimate <estimate ID> --candidate-estimate <estimate ID> \
  --baseline-source <source_snapshot or candidate ID> \
  --candidate-source <source_snapshot or candidate ID> \
  --id <new report ID> --format json \
  [--site-finder <campaign_summary ID> [--site-finder-iteration <index>]]
```

`--site-finder` (ticket 08) names a saved campaign summary; its site-finder regions give the
catalog bounds. `--site-finder-iteration` picks the iteration (default: the last one whose
region rows carry their `why`). Without `--site-finder`, every catalog bound is null with
reason `no_site_finder`, and the ranking is floor-only.

It refuses (exit 1, nothing written) when:

- the two estimates differ in `input`, `target_description_sha256`, `threads` or
  `evidence_kind`;
- a source record is not the one its estimate counted (a `candidate` source must be the
  estimate's candidate subject; a `source_snapshot` must name the implementation subject);
- a source tree on disk no longer matches its recorded artifact hash;
- a characterization differs from the hash its estimate pins;
- `--site-finder` is not a saved `campaign_summary`, or the chosen iteration has no site-finder
  region with its `why`; `--site-finder-iteration` comes without `--site-finder`.

## Labeling rules (this version)

| Rule | What it means |
|---|---|
| Path | A region's path is made relative to its own side's tree. A path in neither tree (for example a system header) cannot have changed. |
| Home span | `[min, max]` of the region's start line and its accesses that lie in the same file **and** inside the region's own lexical function. Without a recognizable function, every same-file access counts. |
| Inlined pieces | Accesses in another file or another function are inlined code (the LLVM pass keeps their own file and line). They form `inlined` pieces, one per file and enclosing function, `[min, max]` of their lines. Files outside the tree add none. |
| Rewritten | Some piece (home or inlined) overlaps a changed span on the same side. An insertion point overlaps only when strictly inside. |
| Mixed | A rewritten region with at least one unchanged line in its pieces. Its whole time stays in the rewritten group (F14). |
| Merged sites | Changed spans that one region overlaps, on either side, merge into one site (transitively). A region is in at most one site, so no time is counted twice. |
| Matched | An untouched region is paired with the other side's untouched region whose home span and inlined pieces equal its own carried through the line diff, with the same kind. Only one-to-one pairs are kept. |
| Unattributed | The region has no source path or no line. |
| Unattributed flag | `unattributed_flagged` is true when the unattributed share of either estimate's total is above 0.1 (F24). The report is still written. |
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
| `site_finder` | ticket 08, only with `--site-finder`: the site-finder regions that gave catalog bounds (below); `swdb validate` re-checks the summary pin |
| `rewrite_sites` | one row per changed run of lines (below) |
| `regions` | one row per region of each estimate (below) |
| `groups` | one row per code origin, always in the order untouched, agent_rewritten, unattributed (below) |
| `whole_program` | totals and whole-program ratios (below) |
| `ranking` | the candidate's regions in next-iteration order (below) |
| `ranking_rule` | ticket 08: one fixed sentence per ranking tier, keyed `remaining_gain_bound`, `floor_headroom` and `unknown`; the first says the remaining gain bound is an **upper limit, never an expected gain** |
| `split_check` | ticket 09, only with `--baseline-profile` and `--candidate-profile`: measured against estimated group shares ([below](#split-check-ticket-09)); absent = not checked |
| `identity_sha256` | content hash of the record without this field; `swdb validate` checks it |

### `rewrite_sites` rows

| Field | Meaning |
|---|---|
| `id` | `site.<n>`, numbered by the site's first span, in path then line order |
| `path` | file path relative to the source tree; null when the spans lie in several files |
| `baseline_lines`, `candidate_lines` | envelope `[min first, max last]` of the spans on each side (a single span: its changed lines; an empty side is `[p, p - 1]`, the insertion point before line `p`); null when the spans lie in several files |
| `spans` | the merged changed runs, each `{path, baseline_lines, candidate_lines}` |
| `baseline_regions`, `candidate_regions` | region IDs whose span overlaps the site on that side |

### `regions` rows

| Field | Meaning |
|---|---|
| `side` | `baseline` or `candidate` |
| `region` | the estimate's region ID |
| `origin` | `untouched`, `agent_rewritten`, `library_call`, `intrinsic`, `offload_command` or `unattributed` |
| `reason` | `overlaps_rewrite_site`, `offload_command_in_site`, `intrinsic_in_site`, `library_operation_in_site`, `no_changed_line`, `outside_source_tree` or `no_source_location` |
| `mixed` | true when the region is rewritten but some line of its pieces is unchanged |
| `path`, `lines` | relative path and `[first, last]` home span; null when unknown |
| `inlined` | `[{path, lines}]` inlined pieces, by their own file and line |
| `sites` | the one merged rewrite site the region overlaps, or empty |
| `seconds` | the estimate's own per-region seconds (a diagnostic median; groups do not use it) |
| `evidence` | inside a site: every signal found, `{origin, name}`, highest precedence first (`name` is the event, intrinsic ID or library operation ID); empty otherwise |
| `matched_region` | the other side's region at the same untouched code, or null |
| `resource_floor` | the region's resource floor (below) |
| `catalog_bound` | the region's catalog bound (below, ticket 08) |
| `headroom` | list of `{limit, value, reason}`, one per named limit: `resource_floor`, then `catalog_bound` |

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
| `unattributed_threshold` | 0.1 |
| `unattributed_flagged` | true when either side's unattributed share is above the threshold; null when neither known share is above it but one is unknown; else false |
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
| `limit` | the named limit: `resource_floor` or `catalog_bound` |
| `value` | region `seconds` ÷ the limit's seconds; null when it cannot be a number |
| `reason` | null, or why `value` is null: `unknown_estimate` (checked first), `zero_limit`, or why the limit is unknown: `unknown_limit` for the floor; the catalog bound's own `reason` (`needs_rewritten_counts`, `unknown_catalog_entry`, `no_catalog_match`, `no_site_finder`) |

### Catalog bound (ticket 08)

**In one line:** the best estimate a known catalog entry, matched to the region by the site
finder, reaches on the region's own counts. It is a limit for the next rewrite, never an
estimate of it (spec F6, F21, F25).

1. **Site-finder regions.** One iteration of the saved campaign summary: its chosen `regions`
   rows, each with `why.source` and the entries in `why.applications`.
2. **Join (F21).** Site-finder lines name the full-source revision, not either tree attributed
   here. So each site-finder region is placed in each side's own tree by the function its ID
   names (`<implementation>/<function>:<first>-<last>`): that function's lexical span in the
   file at `why.source.path`. A region joins it when one of its pieces (home span or inlined
   piece) overlaps that span. It is `mixed` when some piece lies outside the span.
3. **Mechanisms (F25).** An entry's `uses_intrinsics` (directly, or through
   `uses_library_operations`) give hardware operations. The pinned description's functional
   observation commands whose operations they all provide give events. The entry's mechanisms
   are the description's offload mechanisms: `selector.domain: offload`, or `selector.event_ids`
   naming one of those events. No host mechanism is used.
4. **Entry estimate.** The unchanged mechanism models run on the region's own counts with the
   estimator's context, composed as the estimator composes a region (max of resource bounds plus
   additive overheads), per trial, then the median (a region absent from a trial counts 0 s).
5. **Bound.** The lowest known entry estimate (ties by entry ID). Otherwise null, with a reason.

| Region `reason` | When |
|---|---|
| null | some entry estimate is known |
| `needs_rewritten_counts` | an entry's model lacks offload counts only a rewrite produces (a `missing` item starting `address_stream_counts` or `accelerator_calls`) |
| `unknown_catalog_entry` | an entry could not be evaluated for another reason: a missing rate or other input, an entry changed since the site finder pinned it, or one not in the library |
| `no_catalog_match` | no site-finder region joins the region, or no joined entry reaches an offload mechanism of the description |
| `no_site_finder` | no `--site-finder` was given |

`catalog_bound` fields:

| Field | Meaning |
|---|---|
| `seconds` | the bound; null with `reason` |
| `entry` | the entry that gives it, or null |
| `reason` | as in the table above |
| `mixed` | true when some joined site-finder region only partly covers the region |
| `site_finder_regions` | IDs of the joined site-finder regions |
| `entries` | one row per joined entry, by entry ID (below) |
| `missing` | union of the entries' missing counts and rates |

`entries` rows:

| Field | Meaning |
|---|---|
| `entry` | library entry ID |
| `kind` | the site finder's entry kind (`library_operation` or `rewrite_contract`) |
| `content_sha256` | the entry content hash the site finder recorded |
| `site_finder_regions` | the joined site-finder regions that apply this entry |
| `seconds` | the entry's estimate on the region; null with `reason` |
| `reason` | null, `needs_rewritten_counts`, `missing_inputs`, `no_offload_mechanism`, `entry_changed` (library content differs from `content_sha256`) or `not_in_library` |
| `mechanisms` | `{model, accounting, seconds, missing}` per mechanism used, `accounting` = `resource_bound` or `additive_overhead` |
| `missing` | union of the mechanisms' missing items |

Known limits of this version: the join is per function, so every region of the function joins;
offload entries on code that has no offload counts are always `needs_rewritten_counts` (no
projection model, out of scope); on a CPU-only description every entry is `no_catalog_match`.

### `site_finder`

| Field | Meaning |
|---|---|
| `campaign_summary` | `{id, sha256}` of the saved campaign summary |
| `iteration` | the campaign iteration `index` whose regions were used |
| `query_sha256` | that iteration's site-finder query hash, or null |
| `kernel` | ticket 10: the site-finder `kernel` parameter of that iteration (else the summary's), or null |
| `target` | ticket 10: the site-finder target binding (`native_cpu`, `dx100_gem5`), or null. The site finder reads the latest report for its kernel and target and reorders its chosen regions by `ranking` only when `split_check.verdict` is `passed` |
| `regions` | one row per site-finder region: `id`, `function` (from the ID; null if none), `path`, `revision` and `lines` (from `why.source`, full-source revision), `entries` (applied entry IDs) |

### `ranking` rows

Only candidate regions are ranked: they are what the next iteration starts from. Three tiers,
never ranked against each other (F7):

1. `remaining_gain_bound`: regions with a known catalog bound, largest first.
   Remaining gain bound = share × max(0, 1 − catalog bound ÷ estimate), with share = region
   `seconds` ÷ the candidate total. It is an **upper limit** on the share of the total a known
   entry could remove, **never an expected gain** (F12). An entry slower than the current code
   gives 0. A region of 0 s gives 0.
2. `floor_headroom`: regions without a known catalog bound (floor-only), by floor headroom,
   largest first.
3. `unknown`: every null value, in region-ID order. A region with a known catalog bound whose
   remaining gain bound is null stays here with limit `catalog_bound`; it never joins the
   floor tier.

Ties go by region ID.

| Field | Meaning |
|---|---|
| `position` | 1-based place in the whole list |
| `side` | always `candidate` |
| `region` | the candidate estimate's region ID |
| `tier` | `remaining_gain_bound`, `floor_headroom` or `unknown` |
| `limit` | the limit the value uses: `catalog_bound` or `resource_floor` |
| `value` | the remaining gain bound or floor headroom; null in the `unknown` tier |
| `reason` | why the value is null: the floor headroom's reason, or `unknown_estimate`, `unknown_share` (candidate total unknown) or `zero_total`; else null |

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

## Iterations: two baselines (ticket 06, added 2026-10-11 ET)

From iteration 2 on, pass the **previous accepted candidate** too. Nothing in the records marks
a candidate as accepted, so you name it:

```sh
python -m swdb attribute ... \
  --previous-estimate <estimate ID> --previous-source <source_snapshot or candidate ID> \
  [--earlier-source <source ID> ...]
```

- `--earlier-source` (repeatable, oldest first): accepted candidates before the previous one.
  Only their source trees are read. The candidate is iteration 2 + their count.
- Refused when only one of the two `--previous-*` flags is given, when `--earlier-source` comes
  without them, or when the previous estimate differs from the candidate's in `input`,
  `target_description_sha256`, `threads` or `evidence_kind`.

**What changes in the record** (without `--previous-*`, nothing does):

1. The top-level `rewrite_sites`, `regions`, `groups` and `whole_program` stay the
   **cumulative** comparison: original baseline → candidate.
2. A new `this_iteration` block holds the same four fields for **gain this iteration**:
   previous accepted candidate → candidate. Inside it, `baseline` means the previous accepted
   candidate (`side: baseline`, `baseline_lines`, `baseline_seconds`, …).
3. Every region row, in both comparisons, gets `last_changed_iteration`.
4. `this_iteration` region rows also carry `resource_floor` and `headroom` (same row shape).
   The previous candidate's floors come from its own estimate; the candidate's equal the
   cumulative ones. There is one top-level `ranking`: the candidate is the same in both.

| `this_iteration` field | Meaning |
|---|---|
| `iteration` | the candidate's iteration number (2 or more) |
| `previous_estimate` | `{id, sha256}` of the previous accepted candidate's estimate |
| `previous_source` | `{kind, id, sha256, artifact_sha256}` of the source it counted |
| `earlier_sources` | the same pins for each `--earlier-source`, oldest first (index 0 = iteration 1) |
| `rewrite_sites`, `regions`, `groups`, `whole_program` | as above, previous → candidate |

**`last_changed_iteration`** (region rows): the newest iteration that changed the region's code.

- Original baseline regions: 0.
- Other regions: the newest iteration *k* + 1 such that diffing iteration *k*'s tree against the
  region's own version labels the region rewritten. 0 if no diff touches it; null if it has
  no source location (it cannot be placed).
- It uses the same labeling rules as the report, so it follows them when they change.

Worked example (the test fixture). Loops A, B, C. Iteration 1 rewrites B; iteration 2 rewrites A.

| Seconds | A | B | C | Total |
|---|---|---|---|---|
| Original | 40 | 50 | 10 | 100 |
| Iteration 1 (previous) | 40 | 25 | 10 | 75 |
| Iteration 2 (candidate) | 20 | 25 | 10 | 55 |

| Comparison | Rewritten | Untouched | Total speedup | Amdahl ceiling |
|---|---|---|---|---|
| This iteration | A: 40 → 20 | B + C: 35 → 35 | 75 / 55 | 75 / 35 |
| Cumulative | A + B: 90 → 45 | C: 10 → 10 | 100 / 55 | 100 / 10 |

B is untouched this iteration but rewritten cumulatively; its `last_changed_iteration` is 1.
A's is 2, C's is 0.

## Split check (ticket 09)

Added: 2026-10-11 21:17 ET. Spec F15, F18, F19, F23.

**In one line:** time each side natively with `swdb bfs-profile`, then pass both region
profiles to `swdb attribute`; the report says whether the measured split matches the estimated
one.

```sh
python -m swdb attribute ... \
  --baseline-profile <region_profile ID> --candidate-profile <region_profile ID>
```

Use the same flags as the unchecked report, plus the two profiles. Without them the record
has no `split_check` and is otherwise byte-identical.

**The rule** (fixed before timing, F19; recorded in every checked report as `rule`):

- For each group (untouched, agent_rewritten, unattributed) on **both** sides:
  gap = measured share − estimated share.
- `passed` when every |gap| ≤ 0.1 (10 percentage points; 1e-9 float tolerance).
- `split_unverified` otherwise, or when any share is unknown (F23). The report is still
  saved; the site finder ignores its ranking.

**Shares:**

| Share | Formula |
|---|---|
| Estimated | the report's group share: group seconds ÷ that estimate's total `seconds` |
| Measured | group exclusive thread-CPU seconds ÷ all measured scopes' exclusive thread-CPU seconds in that side's profile |

**How a measured scope gets its group.** A scope is one `bfs-profile` source region (function or
loop) with its accumulated `exclusive_thread_cpu_seconds`.

1. Its **exclusive lines** are its `lines` minus the lines of scopes nested inside it (by
   `byte_range`). Exclusive time is spent there. If nothing is left, its full span is used.
2. The report's own labeling rules then apply to those lines with the report's merged rewrite
   sites: any overlap on its side is `agent_rewritten` (`mixed` when some line is unchanged);
   otherwise `untouched` (`no_changed_line`, or `outside_source_tree` when the path is in
   neither tree); no path or lines is `unattributed`.

Example: a function at lines 6-9 holding a rewritten loop at 7-8 keeps its own time on lines 6
and 9, so that time is untouched.

**Refused** (exit 1, nothing written) when:

- only one of the two profile flags is given;
- a profile did not finish (`outcome.state` not `partial` or `complete`; `bfs-profile` ends a
  good run as `partial`);
- a profile timed another tree (`context.candidate_sha256` ≠ that side's source
  `artifact_sha256`);
- a profile timed another input (`context.workload.id` ≠ the estimates' `input`, F18) or
  another thread count;
- a profile is dated before either estimate (`created`, day precision): the check must be
  prospective (LR-02);
- a profile region is not `basis: measured` with numeric `exclusive_thread_cpu_seconds`
  (simulated profiles are not timings).

`swdb validate` re-checks both profile pins, that `rule` equals the fixed rule, and that
`verdict` follows `gaps` and `reasons`.

### `split_check`

| Field | Meaning |
|---|---|
| `verdict` | `passed` or `split_unverified` |
| `rule` | the fixed rule: `id` (`swdb.split_check.v1`), `max_abs_share_gap` (0.1), `tolerance` (1e-9), `statement`, and the definitions `estimated_share` and `measured_share` |
| `reasons` | why it is unverified: `{side, origin, reason}` with `reason` = `gap_above_rule`, `unknown_estimated_share` or `no_measured_time` (`origin` null); empty when passed |
| `profiles` | `baseline` and `candidate` profile pins (below) |
| `measured_shares` | six rows, baseline then candidate, groups in report order: `side`, `origin`, `seconds` (measured exclusive thread-CPU seconds) and `share` (null when nothing was measured) |
| `gaps` | six rows in the same order: `{side, origin, estimated_share, measured_share, gap, within_rule}`; `gap` and `within_rule` are null when a share is unknown |
| `regions` | one row per measured scope: `side`, `region` (profile region ID), `kind`, `path`, `lines`, `origin`, `reason`, `mixed`, `exclusive_lines` (`[first, last]` runs), `sites`, `seconds` |

Profile pin fields: `id`, `sha256` (record content hash), `evaluation`, `machine`, `workload`,
`threads`, `lane`, `load_average` (host load recorded with the profile run),
`primary_load_average` (load during the primary evaluation).

Known limits: a profile covers only the timed translation unit's own scopes; time in inlined
header code is charged to the enclosing scope. Per-group measured shares always add to 1;
estimated shares need not (F4).

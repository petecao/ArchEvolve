# Attribution reports (`swdb.attribution.v1`)

Created: 2026-10-11 (Eastern Time), fine-grained attribution ticket 02.
Updated: 2026-10-11 ET (ticket 05: library, intrinsic and offload labels; ticket 04: merged
sites, `mixed`, inlined pieces, matched regions, unattributed flag).
Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md`.

**In one line:** `swdb attribute` takes two saved estimates and the two source trees they
counted, and says how much time is in untouched, agent-rewritten and unattributed code.

## What it does, in order

1. Diffs the two source trees itself (never a stored candidate diff).
2. Turns each changed run of lines into a span, and merges spans one region overlaps into one
   **rewrite site**.
3. Labels every region of both estimates with a **code origin** by file and line.
4. Sums each origin group per trial, then takes the median per group.
5. Writes one validated `attribution` record and indexes it into SQLite.

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
| `rewrite_sites` | one row per changed run of lines (below) |
| `regions` | one row per region of each estimate (below) |
| `groups` | one row per code origin, always in the order untouched, agent_rewritten, unattributed (below) |
| `whole_program` | totals and whole-program ratios (below) |
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

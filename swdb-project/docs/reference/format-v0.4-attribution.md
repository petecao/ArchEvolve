# Attribution reports (`swdb.attribution.v1`)

Created: 2026-10-11 (Eastern Time), fine-grained attribution ticket 02.
Spec: `.scratch/fine-grained-attribution-2026-10-11/spec.md`.

**In one line:** `swdb attribute` takes two saved estimates and the two source trees they
counted, and says how much time is in untouched, agent-rewritten and unattributed code.

## What it does, in order

1. Diffs the two source trees itself (never a stored candidate diff).
2. Turns each changed run of lines into one **rewrite site**.
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

Ticket 04 widens these rules. Today:

| Rule | What it means |
|---|---|
| Path | A region's path is made relative to its own side's tree. A path in neither tree (for example a system header) cannot have changed, so the region is `untouched`. |
| Span | `[min, max]` of the region's start line and its access patterns' lines in the same file. |
| Rewritten | The span overlaps a rewrite site on the same side. |
| Unattributed | The region has no source path or no line. |
| Region IDs | Never compared across sides; they embed subject IDs and lines. |

A region whose ID has no catalog loop still gets a real label from its file and line.

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
| `rewrite_sites` | one row per changed run of lines (below) |
| `regions` | one row per region of each estimate (below) |
| `groups` | one row per code origin, always in the order untouched, agent_rewritten, unattributed (below) |
| `whole_program` | totals and whole-program ratios (below) |
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
| `origin` | `untouched`, `agent_rewritten` or `unattributed` |
| `reason` | `overlaps_rewrite_site`, `no_changed_line`, `outside_source_tree` or `no_source_location` |
| `path`, `lines` | relative path and `[first, last]` span; null when unknown |
| `sites` | IDs of the rewrite sites the region overlaps |
| `seconds` | the estimate's own per-region seconds (a diagnostic median; groups do not use it) |

### `groups` rows

Group seconds are summed per estimate trial (a region absent from a trial counts 0 s), then
medianed. A single-run estimate is one trial. Group medians are **never rescaled**, so
groups need not add up to the total.

| Field | Meaning |
|---|---|
| `origin` | the code origin |
| `baseline_seconds`, `candidate_seconds` | median per-trial group sum on each side; null if any region in it is unknown |
| `baseline_share`, `candidate_share` | group seconds ÷ that estimate's total `seconds` |
| `realized_speedup` | baseline seconds ÷ candidate seconds |
| `drift` | untouched group only: candidate seconds ÷ baseline seconds (1.0 = no side effect) |
| `unknown` | `{side, region, missing}` for each unknown region; `missing` lists its bounds' reasons |

A ratio is null when an operand is unknown or the denominator is 0.

### `whole_program`

| Field | Meaning |
|---|---|
| `baseline_seconds`, `candidate_seconds` | the estimates' own totals |
| `total_speedup` | baseline total ÷ candidate total |
| `amdahl_ceiling` | baseline total ÷ untouched candidate seconds: the most any further work on the rewritten part could give |
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

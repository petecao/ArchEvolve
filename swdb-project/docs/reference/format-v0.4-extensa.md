# Extensa-mode record fields (format 0.4 addition)

Created: 2026-10-03 (Eastern Time)
Updated: 2026-10-04 (Eastern Time): site-finder fields (ticket 55)

Extensa mode (ADR 0009, ADR 0010; decisions in
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`) adds optional
envelope fields and a candidate-artifact review. Everything here is additive: records
without these fields keep their ArchEvolve-mode meaning and revalidate unchanged.

## Mode tags (ticket 48)

Every record kind accepts two optional envelope fields:

- `mode`: the only value is `extensa`. Absent means ArchEvolve mode.
- `campaign`: the Extensa campaign ID, matching
  `extensa-(native|gem5)-bfs-YYYYMMDD-<letter><n>`. It is required when `mode` is present
  and forbidden otherwise.

The writer sets both only when a record is created. Rewriting an existing record to add,
remove or change either field is refused, and nothing is written. Tags are never
backfilled.

A candidate artifact never stores its certification level. `swdb candidate-level
CANDIDATE` derives it from certification records: `certified` (a certified record for
the candidate), `rejected` (any failed certification) or `uncertified` (none, for
example an edit that used no rewrite contract).

## Team boundary

`swdb compare-evaluations`, `swdb handoff-message` and `swdb bfs-coverage` refuse an
input whose record closure (every record reachable through ID references) holds an
Extensa-tagged record, naming that record. The exceptions:

- a tagged candidate artifact, or its tagged proposal or source snapshot, whose
  candidate is promoted by a candidate review, once a non-rejected comparison under the
  review's derived team protocol exists;
- the re-evaluation comparison itself (`compare-evaluations` under the derived
  protocol);
- a campaign's own comparisons, under an Extensa-tagged protocol, which accept only
  records of the same campaign.

Tagged evaluations, comparisons and protocols never enter team results. Coverage scans
skip refused records instead of failing.

## Candidate reviews

`swdb promote CANDIDATE --protocol TEAM_PROTOCOL --workload-class CLASS --output DIR`
records Yan-Ru's review of an Extensa candidate artifact. The review record has:

- `target_kind`: `candidate` (absent means `library_entry`, the ticket 15 review);
- `target`: the candidate ID and its artifact sha256;
- `evidence`: the candidate's certification records or its campaign summary (no
  `x-ref` restriction for candidate reviews; library reviews keep certification only);
- `origin`: `mode: extensa` and the `campaign`;
- `reevaluation`: the named current `team_protocol`, the derived `protocol` (frozen
  from the team protocol's settings with only the `workloads` of `workload_class`, the
  workload family), and the written evaluation `requests` (`id` and file `sha256`).
  Each request cites the campaign, candidate, review and team protocol under `origin`.

A failed (rejected) candidate artifact is never promoted.

## Campaign files (ticket 52)

`campaigns/extensa/<campaign-id>.yaml`, format `swdb.extensa-campaign.v1`, schema
`schemas/extensa_campaign.schema.json` (an input file, not a record). Fields: `format`,
`id` (`extensa-(native|gem5)-bfs-YYYYMMDD-<letter><n>`, matching the file name), `created`,
`mode` (`extensa`), `kernel` (`gapbs-bfs`), one `target` (`native_cpu` or `dx100_gem5`;
decision D2), `machine`, `base_source` (the baseline role the provider rewrites and
selection uses), `baselines` (each a `role` and its `candidate`), `protocol` (`roi`,
`threads`, `repetitions`, `sources`, `region_pairs`, `differences`), `workload_classes`
(each a `class` and its `workload`), `label` (always `single graph per class`), `library`
(`allowed_tiers`, `contracts`, optional `synthesize` families), `regions` (a fixed list,
or `query`: the query site finder, ticket 55), `provider` (`name`, `model`, `effort`), `budgets`
(`max_iterations`, `plateau_iterations`, `lane_hours`, `provider_calls_per_iteration`,
`provider_calls_setup`, `disk_gb`, `lanes`, optional `max_repairs`), `runs_root` and an
optional `approval` (`by`, `date`, `scope`, `raised_budgets`, `two_lanes`).

`swdb validate` refuses a gem5 campaign with repetitions other than 1 or more than one
source, a native campaign with fewer than 5 repetitions, `region_pairs: true`, another
label, a budget above the spec default without an approval naming it in
`raised_budgets`, and `lanes: 2` without `two_lanes: true`.

## Campaign summary records (ticket 52)

Kind `campaign_summary` (`records/campaign_summaries/`), written once when a campaign
stops, to the campaign store and to the team store. Fields (decision D6): `campaign_file`
(`path`, `sha256`), `swdb_commit`, `extensa_source` (`repository`, `commit`), `target`,
`evidence_basis`, `evidence_kind` (`contract_fixture` for fixture adapters),
`protocol`, `baselines`, `workload_classes`, `label`, `provider`, `pilot` (native A/A
spreads), `setup` (the profiling call), `iterations` (each with `index`, `started`, `ended`,
`regions`, `provider_calls`, `candidates`, `feedback_reasons`, `improved_classes`),
`per_class` (`class`, `verdict`, `best`, `best_level`, `best_selection_baseline`,
`best_other_baseline`, `faster_uncertified`, `label`), `budgets` (`limits`, `used`),
`pauses` (`at`, `reason` usage_limit or login, `resumed_at`), `stop_reason`,
`stop_detail`, `artifacts`, `retentions` and `library_entries`. Candidate records never
store a certification level; the summary's `level_at_summary` is a snapshot.

With `regions: query` (ticket 55), each iteration's `regions` row is a chosen region:
`id` (`<implementation>/<function>:<first line>-<last line>`), a one-line `reason`, and
`why` (`query_sha256`, `statements`, `source` path, revision and lines, and per applying
entry its `entry`, `contract` (null for a library operation), `kind`, `content_sha256`,
`pattern_key` (each key pattern, its matching access patterns and the one `assigned`),
`statements` and every legality clause with `holds` and `reason`). The iteration also
carries `site_finder` (`format`, `query_sha256`, `parameters`, `database` fingerprint and
builder, and `rejected`: each considered site with `entry`, `region` and `reason`), and the
summary carries `site_finder` (`format`, `query_sha256`, `parameters`; null for a fixed
list). The decision procedure is documented in `swdb/site_finder.py`.

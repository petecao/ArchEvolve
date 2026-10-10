# Extensa-mode record fields (format 0.4 addition)

Created: 2026-10-03 (Eastern Time)
Updated: 2026-10-09 23:50 (Eastern Time): agreement report v2, `paired_range` (D29), ledger coverage, D35 start gate, open D30 interpretations
Updated: 2026-10-09 (Eastern Time): artifact-receipt fields and certification failure boundary
Updated: 2026-10-04 (Eastern Time): site-finder fields (ticket 55); campaign isolation and gem5 approval fields
Updated: 2026-10-04 21:30 (Eastern Time): `protocol.speed_rule` and evaluator v3 (tickets 66 and 67)
Updated: 2026-10-05 03:15 (Eastern Time): provider capacity and protected regions (ticket 73)
Updated: 2026-10-05 10:45 (Eastern Time): guard stops for the harness's own runtime limit (ticket 74)
Updated: 2026-10-04 23:25 (Eastern Time): speed rule `swdb.speed_rule.ci_width.v2` (ticket 72)
Updated: 2026-10-05 17:50 (Eastern Time): review attribution and corrections; promotion currency (spec review C1, C3, C9, C18)
Updated: 2026-10-05 22:30 (Eastern Time): campaign budgets, pruning, regions, per-class candidate records and `swdb campaign-export` (ticket 80)

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

Added 2026-10-05 (Eastern Time), spec review C3/C18/C9:

- `swdb promote` cites only certifications of the contract's **current content** that name a
  numbered command version (for example `1.4`), and refuses a candidate whose certifications are
  all for superseded content. A review whose cited certifications are no longer current stops
  counting as a promotion (it stays valid as history).
- It refuses a team protocol that another protocol `supersedes`.
- The derived certification level counts, per contract, only the certifications of the current
  contract content under the newest command version: a failure under an older command (for example
  `forged_frontier` v1 before command 1.1) no longer derives `rejected` once a newer command certifies.

## Who performed a review (spec review C1, 2026-10-05 Eastern Time)

Every review record (library entry or candidate) may say who did the reviewing. `reviewer` stays
the maintainer on whose authority the review counts (ADR 0007).

- `performed_by`: `human` or `agent`; absent means `human` (every record before 2026-10-05).
- `delegated_by`, `delegation`, `review_document`: required for `agent`: the delegating maintainer,
  what was delegated and when, and the repository path of the written review. An agent review's
  provenance is `agent_run`, never `human_report`. `review_document` may also accompany a human review.
- `swdb promote ... --performed-by agent --delegated-by "Yan-Ru Jhou" --delegation TEXT
  --review-document PATH` writes them.

An **attribution correction** fixes the attribution of an earlier review without rewriting it
(`swdb correct-review REVIEW --recorded-by NAME --reason TEXT` plus the options above). It is a
review record with `target_kind: review`, a `target` pinning the corrected review (its ID and the
sha256 of its canonical JSON), `evidence` naming exactly that review, and `attribution` (the four
fields above). `swdb get` of a library entry and `swdb candidate-level` report the attribution of
the current review, corrected when a correction exists.

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

Added 2026-10-04 ET (tickets 56 and 64; documented by the final code review): `protocol`
may set `isolation` (`other_socket_free`: native blocks start only while the other socket's
lease is released, recorded per block) and `evaluator` (the native evaluator version the
campaign's protocols pin). With `approval` field `gem5_other_socket` true, native blocks, pilot and
iterations alike, run while another campaign's gem5 job holds the other socket; that lease
is recorded per block.

Added 2026-10-04 ET (tickets 66 and 67, decided by Yan-Ru): a native `protocol` may set
`speed_rule` (`swdb.speed_rule.range.v1`, the default when absent, or
`swdb.speed_rule.ci_width.v1`). Under the CI-width rule every frozen protocol carries
`sampling.analysis: paired_repetition_circular_block_bootstrap.v1` with `sampling.block_length`
and `profitability.gate` (`statistic: relative_ci_width.v1`, `maximum`) instead of
`maximum_relative_spread`; the comparison's `confidence_interval` adds `block_length` and
`relative_width`, and the summary's `pilot` adds `speed_rule`, `ci_by_class_and_role` and `gate`.
It needs at least 8 repetitions and is refused for gem5. `evaluator` may also name
`swdb.native.evaluator.scalable.v3` (saturating parent narrowing; trial format
`swdb.bfs.native.trial.v3` with `parents_saturated`).

Added 2026-10-04 ET (ticket 72): `speed_rule` may also be `swdb.speed_rule.ci_width.v2`. Its frozen
protocols equal v1's; only the A/A pilot differs: it gates each class on the `base_source` role alone.
The summary's `pilot` adds `gating_roles`, a `gates` flag per role in `ci_by_class_and_role`, and
`level_mix_by_class_and_role`; each upstream DO-BFS comparison row adds `level_mix` (per side: `slow_share`
and `by_source_position` rows with `levels`, `slow_trials`, `trials`, `slow_share`, level medians and
`level_ratio`). The level mix is reporting only.

Added 2026-10-05 ET (ticket 73): a provider call at capacity is recorded with outcome `provider_capacity`,
`counted: false` and its `backoff_s`; when a stop interrupts an iteration, the summary keeps that iteration's
row as `interrupted_iteration`. The rewrite workspace adds `PROTECTED.json`, and REGIONS.json rows may carry
`workspace` (`path`, `function`, `lines`).

Added 2026-10-05 ET (ticket 74): a provider call the guard stopped only for its own provider-runtime thread cap
is recorded with outcome `guard_infrastructure`, `counted: false`, `retry_after_s` and `guard_reason`; after two
retries the campaign stops `infrastructure_failure`. A synthesis call so stopped pauses with that reason.

Added 2026-10-05 22:30 ET (ticket 80, spec review; agent-decided under Yan-Ru's delegation, revisable):

- **Waits are lane time (C6).** A capacity backoff or guard retry wait is charged to `lane_hours` (it runs inside
  the socket lease); `budgets.used.provider_wait_hours` is that part. A wait that would pass the cap is not started:
  the campaign stops `lane_hours`. The calls stay uncounted.
- **gem5 baselines are charged (C5).** A class baseline evaluated inside an iteration is charged and checked like a
  `--baselines-only` one.
- **No test-generation call (C7).** Until a certify command version takes generated differential-test inputs, no
  `independent_test_generation` call is made or charged; an iteration's `skipped_calls` rows (`role`, `contracts`,
  `reason`) record the first use of each contract.
- **Library operations stay out of REGIONS.json (C15).** The iteration's `site_finder` adds `excluded` (`entry`,
  `kind`, `region`, `reason`): each library-operation application the site finder found and the provider was not
  offered. The region itself is still offered (an edit there without a contract is uncertified).
- **Pruning (C8).** Each gem5 comparison prunes its companion runs with the observed run; the per-class gem5
  baselines are pruned when the campaign stops, and a native A/A block's runs after the block. A team claim keeps them.
- **One candidate record per class (C19).** When two classes produce the same tree, the second class gets its own
  candidate record whose `artifact` is the first class's tree, with `extensions.shared_tree` (`candidate`, `path`,
  `note`) naming it; the duplicate tree is removed. The same tree again in the same class reuses that class's ID.
- **Base source (C14).** `swdb validate` refuses a `base_source` other than `fork_scalar_tdstep`: every adapter
  builds candidates from the fork's scalar-only snapshot.

## Exporting a campaign's candidate artifacts (ticket 80, 2026-10-05 ET)

`swdb campaign-export CAMPAIGN_FILE --candidate ID [--candidate ID ...] [--claims] [--dry-run] [--records TEAM]
[--runs-root ROOT]` copies records from the campaign store (`<runs root>/extensa/<campaign>/records/`) into the
team store, byte for byte, tags kept. For each named candidate artifact (listed in the campaign summary, not
rejected): the candidate, every certification bound to it, every evaluation of it (with aggregates over them),
every comparison, evaluation pair or certification that cites them, the retention records of every exported
evaluation, and the closure of all of these. Team claims of the campaign that cite an exported record come along
with their closure (`--claims`: every team claim of the campaign). The sha256 of each source file is checked on
the written file; a record already in the team store must be byte-identical, or nothing is written; the team store
is validated with the new records first. The result (format `swdb.campaign-export.v1`) lists every record as
`copied`, `present` or `would_copy` (dry run), each candidate's derived level and current promotion, and is also
written as a receipt under `<campaign folder>/exports/`. Exporting precedes `swdb promote`; the team boundary keeps
refusing the exported records until the promotion and its team re-evaluation exist.

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

## Prospective paired estimates and agreement

Updated for these fields: 2026-10-07 (Eastern Time).

[Campaign pairing](../../swdb/extensa_pairing.py) records an immutable
`paired_estimate` before reading each timing outcome. It pins `timing_context`,
`context_sha256`, and `estimated_at`; `eligible_for_agreement` distinguishes
usable application estimates from fixtures and unknowns. Current application
pairing has no verified complete-call adapter: real seconds remain null and
cannot become agreement samples. Timing still controls campaign selection.

A summary's `paired_estimates` ledger retains `enabled`, records,
`outcome_accesses`, `outcome_access_started_at`, and optional `timing_contexts`.
`prior_outcome_exposure` records earlier exposure explicitly.
`eligible_application_estimates` currently stays zero; `selection_policy` stays
`unchanged_timing_only`. Validation checks exact context and estimate-before-access
ordering. A ledger does not establish a functional-to-native or MMIO bridge.

Since 2026-10-09, validation of an enabled ledger also needs **coverage**: every timed
candidate comparison and every per-class baseline evaluation in the summary must have a
recorded outcome access preceded by its paired estimate. Deleting an access event makes
the summary invalid.

`paired_range` (optional, D29): `beyond_paired_range` marks an estimate for a graph
beyond gem5's sizes, and agreement reports never count it. It is hashed into
`identity_sha256` only when present, so earlier receipts keep their identity. The
campaign loop never sets it, because a paired estimate's input is the graph its own
campaign times; the label exists for estimates made outside that loop.

[Agreement commands](../../swdb/extensa_agreement.py) use two record kinds:

| Record | Fields and meaning |
|---|---|
| `agreement_policy` | `population` pins selected campaign configurations and `campaign_file_sha256`; workload pins retain `canonical_sha256` and `generation`. `provider_config_sha256`, `statistics`, and `D30` freeze the provider/analysis/admission policy prospectively. |
| `agreement_report` | `policy`, `policy_sha256`, and `policy_snapshot` bind the freeze; `summaries` and `summary_identities` bind inspected campaign results. `reported_at`, `blind_order`, `rank`, `top3`, `gate`, and `recommendation` retain reporting time, ordering, agreement statistics, and whether the unchanged gate was met. |

Run `agreement-freeze --help` and `agreement-report --help` for exact inputs.
A report retains exclusions and unsupported scope; fixture agreement is not
measured application agreement. No report silently enables screening or replaces
the campaign's frozen selection policy. Existing summaries without these fields
retain their historical interpretation.

### Report v2 (2026-10-09)

`agreement-report` now writes `format: swdb.extensa-agreement-report.v2`. Each v1
report is still validated by the v1 analysis, unchanged.

| What v2 does | Fields |
|---|---|
| Matches the candidate's and the baseline's timed forecasts for each base-source comparison | `forecast_ids`, `baseline_forecast_ids`, `estimated_candidate_seconds`, `estimated_baseline_seconds` |
| Derives the estimated speedup (baseline seconds / candidate seconds) and its error against timing | `estimated_speedup`, `relative_error` |
| Counts each artifact pair on one graph once, across campaigns | `pair_identity_sha256`; a repeat gets `repeated_pair_content` |
| Lists every reason a pair is not eligible | `exclusions`: for example `contract_fixture`, `unknown_forecast`, `missing_matching_outcome_request`, `prior_outcome_exposure`, `beyond_paired_range`, `no_verified_complete_call_numeric_adapter` (any forecast with `eligible_for_agreement` false) |
| Sends only eligible pairs to the rank statistics | `rank` (Kendall's tau-b and the frozen dependency-cluster bootstrap) |
| Checks gem5's best against the estimate's top 3 per campaign and workload class | `top3.strata[]`: `best_rank`, `in_top3`, `trivial_cut`, `tied_at_cut` |
| Applies D30 with `>=` on every threshold | `gate.state` (`met`, `not_met`, `unsupported`), `gate.checks`, `gate.failed` |
| Never switches by itself | `recommendation`: `do_not_switch_to_flow_b`, or `d30_met_human_decides` when every check passes |

`blind_order` is `unverified` when a campaign has no timed candidate comparison:
zero checked pairs are no evidence of order.

Today no pair can be eligible: every application forecast is unknown and
`eligible_for_agreement` is `false` by schema.

**Open, pending Yan-Ru's review (not approved):** the frozen v1 statistics and v2 add
choices that D30's text does not state. Among them: at least 4 independent dependency
components; dependency links that make the repository's gem5 campaigns one component;
top 3 per workload class; SHA tie-break at the cut; trivial passes with 3 or fewer
candidates; prior-exposure exclusion of baselines. The full list is in the
[spec](../../.scratch/lanl-db-analytic-eval-2026-10-06/spec.md) under "Open question for
Yan-Ru: implementation interpretations of D30".

### Start gate (D35, 2026-10-09)

No Extensa campaign starts until a *numeric pairing check* passes. That is one real
numeric paired estimate, recorded before its timing, that the strict audit admits.

| Field | Meaning |
|---|---|
| `paired_estimates.numeric_pairing_check` (campaign file) | ID of that `paired_estimate` record in the team store |

`swdb campaign` refuses a new campaign on a real target unless the named record has
numeric seconds, `evidence_kind: execution` and `eligible_for_agreement: true`. The
code does not yet bind the strict audit's admission receipt.

**No check can pass yet.** The current paired-estimate schema keeps every application
estimate unknown and ineligible, so every new real-target start is refused. The
`--fixture` adapter and resumed campaigns are not affected.


## Prospective artifact coverage before certification

[Campaign pairing](../../swdb/extensa_pairing.py), when enabled, records a structural
unknown for each baseline after protocol freeze and every materialized candidate
artifact before admission/certification, including refused and repaired attempts. Each
artifact is covered across the registered workload classes. These receipts run
no candidate code and start no build, provider, or timing job.

The [paired-estimate schema](../../schemas/paired_estimate.schema.json) closes
`timing_context.execution` to these fields when `observation_scope` is present:

| Fields | Meaning |
|---|---|
| `observation_scope`, `backend` | Exactly `artifact_before_certification` and `source_metadata_only` |
| `protocol`, `protocol_identity_sha256`, `protocol_settings_sha256` | Original freeze ID, identity, and digest of its complete settings |
| `protocol_context` | Exactly `target`, `roi`, `threads`, `repetitions`, `sources`, and `workloads`, projected from campaign settings |
| `selected_input` | Empty object; no executable input configuration is claimed |
| `target`, `roi`, `threads`, `sources`, `repetitions` | Must match the projection; the receipt's input must occur in its workloads |

The projection identifies campaign metadata. It establishes no compiled-binary
binding, complete runtime bridge, or functional correctness.

These receipts always have null seconds, unknown state and agreement eligibility
false, even in a numerical fixture. They remain in the campaign summary. An
actual evaluator entry keeps its separate exact request/build forecast and
outcome-access boundary; an artifact-only receipt can never authorize such an
event or enter agreement/ranking/top3 calculations. Untimed or refused artifacts
have no fabricated timing event. Timing-only selection, repair and provider
budgets remain unchanged.

Historical summaries remain valid without this additive coverage. Source/policy
drift requires a fresh prospective campaign and policy; stopped histories are
never resumed or backfilled. This change cannot establish blindness or D30
admission for earlier campaigns with missing actual forecasts/outcomes. The
complete-call numeric adapter remains unavailable, and unsupported/no-switch
reports retain that scientific limitation.

## Certification infrastructure stops the campaign

[Certification dispatch](../../swdb/campaign_targets.py) distinguishes explicit
candidate refusals from infrastructure failures. Authored-source scope, harness
scan, and missing candidate control-site checks remain failed certification
outcomes eligible for bounded repair. Compiler availability, trusted evaluator
build, library/configuration, and trusted-file I/O errors instead stop with
`infrastructure_failure`. The summary retains `interrupted_iteration` and
`stop_detail`; the failure creates no repair call or completed iteration/plateau
increment. See the [certification reference](bfs-typed-library.md#handle-a-certification-refusal-at-the-right-boundary)
for procedure manifests and standalone CLI categories.

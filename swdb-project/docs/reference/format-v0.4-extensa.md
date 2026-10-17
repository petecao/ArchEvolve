# Extensa-mode record fields (format 0.4 addition)

Created: 2026-10-03 (Eastern Time)
Updated: 2026-10-14 16:04 (Eastern Time): code outside the C++ subset skips both bounded rungs; the real one-thread rung is `cbmc` (Probata PoC ticket 22; see [format-v0.4-cbmc.md](format-v0.4-cbmc.md))
Updated: 2026-10-14 (Eastern Time): optional `library.new_enabling_contracts`, rewrite role `new_contract`, iteration row `new_contract` (Probata PoC ticket 63; see [format-v0.4-derived.md](format-v0.4-derived.md))
Updated: 2026-10-14 07:45 (Eastern Time): the WP phase after the campaign stops: `wp_phase`, `budgets.provider_calls_proof`, proof lane-hours and the proof budget lines in `budgets.used`; gate jobs now charged to lane-hours (Probata PoC ticket 16)
Updated: 2026-10-14 07:46 (Eastern Time): the iteration ladder: `LADDER.json`, `rewrite_workspace` in campaign summaries, reasons `refuted` and `proof_timeout` (Probata PoC ticket 17)
Updated: 2026-10-14 06:17 (Eastern Time): two winners per workload class: `winners`, `best_proven`, `level_snapshot` in campaign summaries; `best/<class>.best_proven.patch` (Probata PoC ticket 15)
Updated: 2026-10-14 (Eastern Time): optional `derived_starts` and the entry fields `start`, `derived_implementation` (Probata PoC ticket 19; see [format-v0.4-derived.md](format-v0.4-derived.md))
Updated: 2026-10-14 02:57 (Eastern Time): promotion pins the level: `proof_records` and `level_snapshot` on candidate reviews (Probata PoC ticket 12)
Updated: 2026-10-14 (Eastern Time): per-contract certification links of a candidate entry (Probata PoC ticket 02)
Updated: 2026-10-13 (Eastern Time): D35 field named alone so the format check finds it
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

Added 2026-10-14 (Eastern Time), Probata proof of concept ticket 12 (map decision 26 item 11):
`swdb promote` also writes, from the level rule (`swdb.level_rule.promotion_pin`):

- `proof_records`: the candidate artifact's proof records that count at promotion (skip records
  aside; an empty list when it has none);
- `level_snapshot`: `{level, at: "YYYY-MM-DD HH:MM ET", level_rule, records}`, the dated level snapshot
  ([format-v0.4-level-rule.md](format-v0.4-level-rule.md)); `records` are the proof records that set
  the level. It is never recomputed.

The two come together (each requires the other) and only on a candidate review. `swdb validate`
refuses a snapshot without its `level_rule` version, and a cited proof record (in either field) whose
subject is not the reviewed candidate artifact's proof unit (`swdb.proof.validate_promotion`). Reviews
written before ticket 12 have neither field and stay valid. `swdb candidate-level` shows the current
promotion's snapshot beside the level computed now (`promotion.level_snapshot`, `promotion.dropped`).

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
`provider_calls_setup`, `disk_gb`, `lanes`, optional `max_repairs`, and `provider_calls_proof`, required
when the campaign's library holds a method version (Probata PoC 16)), `runs_root` and an
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
store a certification level; the summary's `level_at_summary` is a snapshot. Since Probata PoC 15 the
per-class `best` fields name the fastest winner, and the summary adds the best-proven winner and dated level
snapshots (see "Two winners per workload class" below).

Each candidate entry's `certification` (null without a contract) holds `outcome`, `level_at_summary`,
`failed_checks` when failed, `record` (the first certification record ID) and, since 2026-10-14 (Probata PoC
ticket 02), `records`: one `{contract, record}` pair per rewrite contract, in contract order, one
`swdb certify` run each. A contract refused before any record exists has `record: null` and its `refusal`
check. An entry saved before then has no `records`; `swdb.campaign.certification_links` reads it as one
pair (`contract` named only when the entry used one contract). The contract-fixture adapter writes the same
shape: one `contract_fixture` certification per contract (a second contract's ID ends in its name).

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

## The bounded gate (Probata PoC 14, 2026-10-14 ET)

Code: `swdb/bounded_gate.py`, called by `swdb/campaign.py`. Refuted code never spends evaluation time.

- **On or off.** The gate is on when the campaign's library (`--library`, default the repository's) holds a
  method version (`library/methods/`) at setup; the campaign state and summary then hold `bounded_gate`
  (`method_version` pin, `budget_minutes` = `budgets.bounded_job_minutes`, `k` = `budgets.civl_k`, `rungs`).
  No fallback default: without a method version the campaign runs as before and writes no `bounded_gate`.
  A resumed campaign refuses a changed method version.
- **Setup.** The campaign folder gets `library/` beside its `records/` (a symlink to the campaign's library),
  so `swdb prove`, `swdb candidate-level` and the repair loop read one library and method version. The
  records the library names (intrinsic records, hardware operations, strategies) are copied from the team
  store. The target then writes or copies its contract proofs (`prepare_proofs`).
- **When.** Each certified candidate artifact, right after its certification records exist and before its
  evaluation step. Uncertified and rejected candidate artifacts get no bounded job.
- **What.** Per rewrite contract (one proof unit each), two rungs through `swdb prove`, in one batch
  (`batch.gate.<candidate>.<hex>`): `threads_1` at the contract's single-thread minimum bounds, and
  `threads_k` at the multi-thread minimum bounds with `threads` = k (the one exception to "minimum only").
  The minimum bounds are the bounds of the counting minimum-bounds derivation record of the contract's
  current content for that rung (threads 1, or more); each record pins it (`pins.minimum_bounds`). Each
  job's wall budget is `budget_minutes`; the rungs run in parallel. A timeout is not proven for that rung
  only: no retry at smaller bounds, and the candidate artifact goes on to evaluation.
- **Skips (O7).** No counting proven contract-proof part of the contract: both rungs skip,
  `no_contract_proof`. Code outside the C++ subset: both rungs skip, `outside_cpp_subset` (ticket 22,
  2026-10-14 ET: CBMC reads the C lowering too). No minimum
  bounds for a rung: that rung skips, `no_minimum_bounds`. A skip is a skip record; the level is kept.
- **Refuted** is read by the level rule (its refuted flag), never stored. A refuted candidate artifact gets
  no evaluator call and cannot win; its first refutation (job order) enters
  `swdb.counterexample_repair.loop(setting="campaign")`, which owns the round cap and the reverted-repair flag.

Candidate entry fields:

| Field | Meaning |
|---|---|
| `bounded_gate` | certified and gated entries only: `batch`, `method_version`, `budget_minutes`, `k`, `jobs` (per contract and rung: `contract`, `rung`, `position`, `record`, and `verdict` [+ `failure_class`], `bounds`, `minimum_bounds`, `wall_seconds`, or `skip_reason`), `refuted`, `refutations` (counting refuted record IDs), `job_hours` |
| `counterexample_repair` | a refuted entry: the loop's `state` (`repaired`, `reverted`, `budget_spent`, `certification_failed`, `provider_failed`, `calls_refused`, or `not_started` when the candidate artifact cannot be repaired here), `reason`, `cap`, `rounds`, `calls`, `repairs`, `reverted_repairs` |
| `repaired_from` | an entry a repair made: `candidate` (the refuted one), `round`, `proposal`, `trigger` (the refutation), `reverted_repair`; `ended` when its certification repair's result was refuted |
| `reverted_repair` | `true` on a flagged repair: it gets no bounded job, keeps the level certification gives it, is evaluated and may compete, and never counts as a repair |

Each repair the loop makes follows its refuted entry in the iteration's `candidates`: certified, gated and,
when it ends the loop unrefuted (repaired, or reverted), evaluated and ranked like any other. A repair that
fails certification uses D7's certification repairs (never a counterexample round); its certified result is
gated and evaluated, and if refuted ends the chain (it has no repair lineage of its own).

**Two counters, one rewriting total.** Every counterexample repair call is charged to the D7 ledger before
it opens (role `counterexample_repair` in the iteration's `provider_calls`; the per-iteration and campaign
caps and lane-hours apply; a refused call ends the loop `calls_refused`). `state.json` and the summary's
`bounded_gate` block hold `repair_counters`: `certification_repairs` (D7 calls, role `repair`),
`counterexample_repair_rounds`, `repairs` and `reverted_repairs`; both kinds of call count in
`budgets.used.provider_calls_counted`. The block's `proof_job_hours` is the gate's proof-job wall time (the
rungs' sum). Ticket 16: a gate run that ran a verifier (not only skips) is also charged to `lane_hours` as lane
time (its elapsed time, or the fixture's `step_hours.proof`) and to the proof lane-hours line.

**Contract fixture** (`swdb campaign --fixture`, with `base_snapshot`): `contract_proofs: {contract: {parts
(default [unit_postcondition]), minimum_bounds: {threads_1, threads_k}}}` writes contract-fixture
contract-proof records into the campaign store at setup; `proof.function` names the proof unit's function;
a class row's `proof` holds per rung a list of verdicts by attempt (`proven`, `refuted`, `timeout`,
`spurious`, or a mapping with `verdict` and scripted-adapter keys such as `run`), `cpp_subset: false`, and
per-contract overrides under `contracts`. A fixture candidate artifact retains its own patch (`diff`). The
real targets read contract proofs from the team store (none exist before tickets 29, 32, 33), name
`TDStep` as the proof function, read every candidate artifact as inside the C++ subset (ticket 24), and
have no bounded verifier adapter yet (22, 46, 47).

## The WP phase (Probata PoC 16, 2026-10-14 ET)

Code: `swdb/wp_phase.py`, called by `swdb/campaign.py` (`Campaign._after_stop`). Design: map decisions 25
items 1, 2, 4 and 13 items 10, 11; spec "Extensa mode". A campaign with a bounded gate (a method version)
runs step 4 of a candidate artifact's path, the unbounded rung, after it stops.

- **When.** After the stop and after the first `campaign_summary` is written (its `wp_phase.state` is
  `not_started`). Each WP job starts only when the target reports no open timing step or gem5 simulation
  (`open_timing_steps`); the wait is recorded in `waits`.
- **Order and stop per class.** `order`: the certified, unrefuted `gain` candidate artifacts of the class,
  fastest first (the lower bound). One candidate artifact at a time; the class is done (`state`
  `proven_unbounded`, `proven` its ID) when the level rule reads one proven unbounded, or `order_spent`
  when every one was tried. A timed-out bounded job or missing minimum bounds does not keep a candidate out.
- **One job per proof unit.** Each rewrite contract of the candidate artifact is one `swdb prove` job and
  one proof record (batch `batch.wp.<candidate>.<hex>`): WP alone, then the contract seeds, then proof-hint
  rounds (`stages`: `wp`, `seeds`, round numbers). Per candidate artifact the method version's
  `hint_rounds`, `hint_loop_wall_minutes` (the job's wall budget) and `wp_seconds_per_solver` apply (copied
  into the block's `budgets`). Not proven after them: failure class `hint_budget_spent`; the candidate keeps
  its level.
- **Skips (O7).** No counting contract-proof part: no `seeds` stage; with a unit postcondition route-1 WP still
  runs, without one a skip record `no_contract_proof`. Outside the C++ subset: a skip record
  `outside_cpp_subset` (no hint loop). A skipped candidate artifact keeps its level; the next one is tried.
- **Two call budgets.** Each hint round charges one call (role `proof_hint`) to the call ledger under
  `budgets.provider_calls_proof` (spec default 30; above it only with an approval entry naming it), never
  to the rewriting total (`provider_calls_counted`) or a per-iteration cap, so a campaign stopped by its
  rewriting total still has its hint calls. Once the cap is spent, the remaining jobs run WP and seeds only.
- **Lane-hours.** Every proof job (the gate's and the phase's) is charged to `lane_hours` and to
  `proof_lane_hours`. A WP job starts only with `hint_loop_wall_minutes` of lane-hours left; otherwise the
  phase ends (`end_reason` `lane_hours`, unfinished classes `unfinished`). A campaign stopped on its
  lane-hours has none left: its phase ends at once. Raising lane-hours still needs the approval entry.
- **Summary rewritten once.** When the phase ends, the summary is rewritten once, replacing the stop-time one
  in the campaign store and the team store (git keeps the first): both winners recomputed (a candidate artifact
  proven unbounded beats a threads ≤ k one), every `level_snapshot` dated at the phase end.
- **Resume.** An interrupted phase (`state` `running`) continues on `--resume` from the candidate artifacts
  already `tried`; a campaign whose phase has `ended` is refused, as a stopped campaign is. A target with no
  WP adapter yet (the real ones, tickets 37 and 55) ends the phase with `end_reason` `failure`.

Summary fields (`campaign_summary`, with `bounded_gate`):

| Field | Meaning |
|---|---|
| `wp_phase` | `state` (`not_started`, `running`, `ended`), `started`, `ended`, `end_reason` (`classes_done`, `lane_hours`, `no_proof_call_budget`, `failure`), `end_detail`, `method_version`, `budgets`, `waits` (`for`, `seconds`, `until`), `provider_calls` (the hint calls: `role`, `invocation`, `candidate`, `outcome`, `counted`, `model`, `effort`), `classes` |
| `classes` (in `wp_phase`) | per class: `class`, `order`, `state` (`running`, `proven_unbounded`, `order_spent`, `unfinished`), `proven`, `tried`, `jobs` |
| `jobs` (in each of `classes`) | per proof unit: `candidate`, `contract`, `position`, `record`, and `verdict` [+ `failure_class`], `stages`, `hint_calls`, `started`, `ended`, `lane_hours`; or `skip_reason` |
| `budgets.used` | adds `proof_lane_hours`, `provider_calls_proof` (hint calls), `certification_repair_calls` and `counterexample_repair_calls` (both also in `provider_calls_counted`); `budgets.limits` adds `provider_calls_proof` |

`state.json` adds `wp_phase`, `proof_lane_hours`, `summary_writes` (`when`: `stop`, `wp_phase_end`; `at`) and
`timeline` (`kind`: `proof_job`, `timing_step` or `gem5_simulation`; `what`, `started`, `ended`), from which
overlap is checked.

**Contract fixture:** a class row's `proof.wp` scripts the WP job: `proven_at` (`wp`, `seeds`, a hint round
number, or absent: never) and `unit_postcondition` (default true); a row without `proof.wp` ends the phase
(`failure`). `open_timing_step: {seconds}` scripts a timing step open when the phase first asks;
`step_hours.proof` charges each proof job. The hint rounds are scripted (no provider runs); ticket 37's
proof-hint loop replaces them.

## Two winners per workload class (Probata PoC 15, 2026-10-14 ET)

Code: `swdb/campaign.py` (`select`, `best_proven`, `winner_rows`, `Campaign._winners`). Design: map decision
25 item 4. Each class has two winners; Yan-Ru chooses which to promote (`swdb promote` accepts either).

- **Fastest winner** (unchanged rule): the fastest `gain` candidate artifact that is not refuted; certified
  beats uncertified, then the lower bound (point ratio on gem5). `faster_uncertified` stays. Key:
  (certified over uncertified, lower bound).
- **Best-proven winner**: among certified `gain` candidate artifacts at a proven level, the highest level
  first (proven unbounded; proven within bounds, threads ≤ k; proven within bounds, threads = 1), then the
  fastest. Bounds above the minimum are never ranked. None when no `gain` candidate artifact reached a proven
  level. Key: (level rank, lower bound).
- **Levels known so far.** Both winners are recomputed after every iteration through the level rule over the
  campaign store and library (what `swdb candidate-level` reports), never stored: the bounded gate gives the
  within-bounds levels; proven unbounded waits for the WP phase (ticket 16, "The WP phase"). A candidate artifact with a counting
  refutation (the level rule's refuted flag) wins neither, even one evaluated before the refutation was
  written; one whose proof records stopped counting (a changed pin) drops to the level it still has.
- **`best/`.** The next rewrite workspace holds `best/<class>.patch`, the fastest winner's patch, and, when
  the best-proven winner is another candidate artifact, `best/<class>.best_proven.patch`; the prompt says
  which is which. `state.json` keeps `bests` (fastest) and `best_proven` (`{id, key, patch}` per class) and
  `patches` (the patch of every `gain` candidate artifact, since a winner can come from any earlier iteration).
- **Plateau.** An iteration improves when either winner of a class improves: its key rises above the key
  after the previous iteration. A winner that drops out is not an improvement.

Summary fields (`campaign_summary`):

| Field | Meaning |
|---|---|
| `winners` (in `per_class`) | one row per distinct winner: `candidate`, `winner` (`fastest`, `best_proven`, or `both` when one candidate artifact wins both, reported once), `level_snapshot`, `ratio`, `lower`. No row is marked as the one to promote |
| `best_proven` (in `per_class`) | the best-proven winner's ID, or null |
| `best_proven_note` (in `per_class`) | present when `best_proven` is null: no `gain` candidate artifact of the class reached a proven level |
| `winners` (in each of `iterations`) | the winner rows of every class after that iteration (each with `class`), from the levels known then |
| `improved_winners` (in each of `iterations`) | `{class, winner}` for each winner whose key rose in that iteration; `improved_classes` lists their classes |
| `level_snapshot` (in each entry of an iteration's `candidates`) | each entry with an ID: its level when the summary was written |

A `level_snapshot` is `{level, at: "YYYY-MM-DD HH:MM ET", level_rule, records}` (`swdb.level_rule.snapshot`;
the proof records that set the level). It is dated, names the level-rule version, and is never recomputed:
`swdb validate` refuses one without `at` or `level_rule`. The per-class `best`, `best_level` and the other
`best_*` fields keep their meaning (the fastest winner), so a summary written before this ticket reads the same.

## The iteration ladder (Probata PoC 17, 2026-10-14 ET)

Code: `swdb/iteration_ladder.py` (`render`, `check_row`, `version_of`), `Campaign._ladder`. Design: map decision
28; D8's leakage rules. The rewrite provider sees every earlier candidate artifact of its own campaign, as
Extensa's loop does. On by default, no off switch.

- **Where.** From iteration 2, every rewrite workspace holds `LADDER.json` beside `FEEDBACK.json` (which stays:
  the previous iteration's explanations) and `REGIONS.json`; the rewrite prompt names it. Every repair workspace
  of that iteration gets the same bytes: a certification repair at `LADDER.json`, a counterexample repair at
  `.swdb-context/LADDER.json` (its prompt lists it as `iteration_ladder`). Iteration 1 and its repairs have none.
- **Written by the loop only.** Rebuilt whole from `state.json` and the levels the level rule reads now, for each
  workspace; never read back. The campaign folder keeps a copy of the latest file (`LADDER.json`), which nothing
  reads. Each provider call's `workspace.json` hashes it (`input_sha256s["LADDER.json"]`; a counterexample
  repair's `iteration_ladder: {path, sha256, bytes}`), so what each call saw is auditable.
- **File.** `{format: "swdb.iteration-ladder.v1", note, rows}`; `format` is the renderer's version. One row per
  earlier candidate artifact, rejected and repaired ones included, in order; an iteration whose rewrite call
  returned nothing gets one row with class `-` and reason `provider_output_invalid`. No row cap, no gaps.
- **Columns** (a closed set, `check_row`): `row` (1, 2, ...), `iteration`, `class`, `contracts`, `knobs`,
  `level`, `verdict`, `ratio`, `lower`, `spread` (against the base-source baseline), `reason_codes` (the closed
  feedback reasons), `failed_checks` (public names only: a surviving negative control only as
  `negative_controls_not_rejected`; a refutation only as its check category `bounded_threads_1` or
  `bounded_threads_k`), `winner` (`fastest`, `best_proven`, `both` or empty, from the last iteration's winner
  rows) and `repair_of` (the row of the candidate artifact a counterexample repair repaired, else null). A
  certification repair stays inside its candidate artifact's row.
- **Levels known so far:** `rejected`, `uncertified`, `certified`, `refuted` (the level rule's refuted flag),
  `proven_within_bounds_threads_1`, `proven_within_bounds_threads_k`. Proven unbounded never appears: a level
  read as proven unbounded during the loop shows `proven_within_bounds_threads_k`.
- **Never in a row:** patches, counterexamples, raw timings, workload files, evaluator inputs, other campaigns'
  artifacts, the authors' accelerated code, or any field outside the column set (`check_row` refuses each).
- **New feedback reasons:** `refuted` (with `failed_checks` naming the check category only) and `proof_timeout`
  (a bounded rung ended at its wall budget) join `FEEDBACK_REASONS`; the bounded gate adds them to FEEDBACK.json.
- **Workspace version.** A new campaign records `rewrite_workspace: v2` in `state.json` and in its summary
  (`rewrite_workspace` in `campaign_summary`). A state or summary without it reads as `v1` (D8's workspace, no
  iteration ladder; the 15 BFS campaigns). A resumed `v1` campaign never gains a ladder; a resumed `v2` campaign
  rebuilds it from state. The campaign file has no such field: one that names `rewrite_workspace` is refused.
- **Rejected entries** in `state.json` and the summary's `iterations[].candidates[]` now keep `rejection_reason`
  (the feedback reason code) and, when the rejection named checks, `rejection_failed_checks` (public names).

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
| `numeric_pairing_check` under `paired_estimates` (campaign file) | ID of that `paired_estimate` record in the team store |

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

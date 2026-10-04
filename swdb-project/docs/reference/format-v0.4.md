# Workflow record format 0.4

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-25 (Eastern Time)
Updated: 2026-10-03 (Eastern Time)

Format 0.4 adds source ownership and workflow records. Existing 0.2 and 0.3 records
retain their meaning; see [source identity](bfs-source-identity.md). The envelope's
`schema_version` versions database records. Independent `message_version: "1.0"`
versions the provisional ensemble handoff. YAML remains authoritative; the SQLite
`records` table carries every new kind for retrieval after an index rebuild.

Public messages may use YAML syntax, but their values must round-trip through
JSON without changing object keys or value types. Binary tags, sets, nonfinite
numbers, recursive aliases, and non-string object keys are rejected. Durable
proposal/evaluation/profile entry points retain invalid message text and its
parse error in a failed record that still supports fresh retrieval and index
rebuild. Protocol and package requests reject incompatible values before
publication. Workflow persistence also checks JSON serializability before
committing metadata, so an invalid value cannot poison the generated index.

## Shared workflow fields

`producer` has `name`, `role` (`sw`, `hw`, `operator`, or `worker`), and the explicit
Boolean `test_client`. A fixture producer is not a live collaborator integration.
All records retain the ordinary envelope dates, provenance, draft/review status,
and stable identity. The internal operator creates metadata; its `agent_run`
provenance does not certify its contents as measured.

An `artifact` contains its absolute external `path`, aggregate `sha256`, and sorted
`files` manifest. Each file has relative `path`, `sha256`, `bytes`, and `executable`
mode. The aggregate hashes the canonical JSON manifest, including paths and modes.
Source snapshots reject symlinks; generated build/cache directories are excluded.
Artifact availability and hash agreement are checked before rewriting or execution.

## Source snapshots and profile packages

A `source_snapshot` records `implementation`, `application`, source `revision`,
`artifact`, source/build/evaluator `context`, declared `regions`, and `protections`. It preserves the
application snapshot before candidate edits. Protections record canonical verifier
text, complete harness files, and simulator ROI calls. Only evaluator-owned code
determines the correctness and timing contract; a proposal cannot waive protections.

A `profile_package` names its `implementation`, `source_snapshot`, and exact
workload/target/ROI `context`. `completeness` is `fixture`, `incomplete`, or `complete`.
It contains `regions`, `dynamic_memory`, `constraints`, collection `evidence`, and
explicit incompleteness `reasons`. `fixture-package` creates a contract fixture with
no execution, correctness, dynamic profiling, or performance evidence. A complete
package requires the later discovery and collector checks; fixture creation cannot
produce one.

## Proposals and candidate artifacts

`submit` accepts a request with `message_version`, `id`, `producer`,
`profile_package`, `source_snapshot`, `implementation`, exact `source_sha256`,
selected `intent`, exact target `regions`, `constraints`, `payload`, and `required_operations`. `payload`
contains `kind` and `content`; the first route accepts an actual unified patch.
`constraints.editable_files` bounds all direct and supporting edits;
`preserve_correctness` and `preserve_roi` must both be true. Every requested
capability must resolve against its declared target/interface before materialization.

A persisted `proposal` retains the original `request`, `payload_sha256`, `outcome`,
`attempts`, and `raw_artifacts`. An outcome has `state`, current `stage`, and `reason`.
States distinguish `submitted`, `rejected`, `unresolved`, `candidate_created`, and
`failed`. Source/package references and `candidate` are attached only after they
resolve. Invalid references in the original request remain available as rejected
input; they are not turned into successful cross-record references.

Each attempt records its `number`, `stage`, `state`, and available failure reason.
The running stage is persisted before starting a child operation. An interrupted
caller can therefore leave an explicit running stage; retrieval never interprets
that state as completion. Original IDs cannot be resubmitted to replace old evidence.

A `candidate` names its `proposal`, `source_snapshot`, originating `implementation`,
new `artifact`, retained `diff`, and `diff_sha256`. Its `state` distinguishes
`unverified`, `incomplete`, `incorrect`, and `checked`; patch creation uses
`unverified`. `context` and `protections` retain evaluator inputs. A later repair may
name a `parent_candidate`; ancestry does not select the performance comparator.

`get ID --chain` retrieves connected workflow records from a freshly regenerated
index. The writer commits metadata before index generation; an indexing failure is
reported with the durable record ID, never as successful submission.

## Public contract example

```sh
python3 -m swdb source-snapshot gapbs-bfs-do --id source-1 --runs-dir /external/runs
python3 -m swdb fixture-package source-1 --id package-1
python3 -m swdb submit proposal.yaml --runs-dir /external/runs
python3 -m swdb get proposal-1 --chain
```

These commands illustrate the contract. Fixture packages and source edits alone
are not acceptance evidence for the real BFS or DX100 campaign.

## Raw-output custody records (2026-10-03)

`retention` records are immutable events. The `event` is `prune`, `prune_intent`,
or `approval`. A prune event names its `evaluation`,
`deleted` path/sha256/byte entries, `reason`, `occurred_at`, `host`, and optional
listing approval. An approval event binds the exact cleanup listing's sha256 and
records `approved_by` as `yanrujhou`; it has no deleted files. Its `listing` binds
`path` and `sha256`. A `prune_intent` event durably records `planned` path/sha256/byte identities before
any deletion; an interrupted event can be reconciled from this receipt. Readers
accept only actual prune events as deletion custody. Public claim and deletion
commands share a custody lock. No event edits an evaluation or reclassifies
missing bytes as freshly verified.
An actual prune event's `intent` names the original intent record; its optional
`approval` names the exact listing approval record. Every deleted entry includes
its `bytes` counted before unlinking.

`team_claim` records either `action` set to `claim`, one or more cited `records`, comma
separated CLI `audience` names, and `recorded_at`; or `action: release`, an
`evaluation`, empty records/audience arrays, and the time. Citation traversal
includes component evaluations of an aggregate and both sides of a comparison.
A claimed run's bulky output stays; a released ArchEvolve run can prune its trace
once the aggregate/comparison or diagnostic rereading records exist.

```console
swdb claim COMPARISON_ID --audience Eric,Josh
swdb claim --release EVALUATION_ID
swdb prune --dry-run --output /data1/yanruj/prune-listing.json
swdb prune --approve /data1/yanruj/prune-listing.json
swdb prune --apply /data1/yanruj/prune-listing.json
```

Dry run lists every file, size, evidence class, and record path reference under
the selected run roots; it proposes only identifiable bulky files. Inputs and
correctness outputs, witness chains, region reports, and companion acceptance
remain protected regardless of size. Apply validates approval, classification,
size, and exact bytes before unlinking. Missing files with a matching path and
sha256 retention receipt are reported as **pruned, sha256 retained**. Missing
local files without such a receipt still fail; named remote evidence retains its
existing `remote_unverified` status.

Dispatch receipts under `context.dispatch_preflight` (or the legacy profile's
`environment.dispatch_preflight`) retain selected disk/free bytes, memory
node/free bytes, planned raw bytes, memory budget, reserve, and admission time.
The reserve is 20 GiB plus the stage's raw budget; native/pair/profile requests
use 2 GiB raw and 4 GiB node memory. Admission never changes a run folder.
The additive `dispatch_preflight` mapping does not alter historical measurements.

Read-only gem5 requests explicitly set `verification.read_only: true`. Their
completed per-opcode trace counts qualify `read_only_executed` only with
S>=1, I>=1, R>=1, A=0, zero indirect stores, and I=3R-S. The existing `executed`
case still requires S/I/R/A unit completion. Exact `Starting TDStep: N elements`
stdout is checked against trusted graph per-depth frontier counts. A frozen
`correctness.companion_cases.parent_gather_race` names workload/source; companion
requests set `protocol_companion: parent_gather_race`. The compare request names
`companion_evaluations: {timed: ID, diagnostic: ID}`. Its diagnostic build alone
sets `parent_gather_diagnostic: true` (`SWDB_DXC_DIAGNOSTIC`), and exact stdout
`SWDB cas_fail_negative_hint=N l3_violations=N` derives observed/refuted/inconclusive
L3 outcomes. Comparison requires observed L3 and the exact timed binary's passed
v2 correctness and frontier checks.

## Provider roles and statement claims (2026-10-03)

Every role has a canonical name, explicit workspace input files and an output
JSON schema. Rewriting retains its source/proposal builder. Independent test
generation, synthesis and profiling use their own inputs. The shared launcher
pins Codex to `gpt-5.6-sol` / `xhigh` or Claude to `claude-sonnet-5-5` / `high`.
Real calls require an mbit10 socket lane before copying credentials or input
files. Inputs exclude evaluator/workload files, other candidate artifacts and
the authors' accelerated code. Read-only roles preserve every input file.

Provider receipts retain `role`, `model`, `effort`, `prompt_sha256`,
`output_schema_sha256`, `lane`, `classification` and the shared process/event
`audit`. For read-only roles, `workspace_manifest` retains `format`, `root`, `home`, `read_only`,
`visible_files`, `immutable_files`, `input_sha256s`, `output_schema_sha256`,
`source_files`, `dropped_build_outputs` and `login_copy_deleted`.
`input_sha256s` maps each visible relative path to its exact byte SHA-256.
`classification` distinguishes `rewrite_provider` from `contract_fixture`;
fixture audit and model pins do not establish a real provider invocation.
Existing timeout, cleanup and guard receipts apply to every role.

An implementation's `extensions.statements.annotations` contains statement
annotations (the `annotations` list) alongside its access-pattern entries. Each may hold additive
`agent_claims` and `annotation_facts` lists. An agent claim contains `field`,
`value`, `basis`, `model`, `effort`, `prompt_sha256`, `input_sha256s` and
`contradicted_by`. Its basis is `code_reading` or `inferred`. An
`expected_cost_rank` claim is always inferred and has an integer value starting
at 1; rank 1 predicts the most last-level read-plus-write misses. The profiling
response requires one rank per statement, a permutation of 1 through N.
`pattern_class` claims give each named pattern's `address_shapes` and
`update_kind`; `index_provenance` claims name statement IDs in dependency-chain
order. Access-pattern claims also carry their originating `statement`.
Original pattern steps, semantics and statement facts remain intact.

Each `contradicted_by` entry records contradictory `evidence`, its `basis`
(`measured`, `simulated` or `reported`) and the applied `rule`. Cost contradictions
also retain `profile_sha256` and `observed_rank`. Existing entries remain intact.
An `annotation_facts` entry contains `field`, `value`, `basis` and `evidence`;
its basis may additionally be `code_reading` or `inferred`. Pattern-class or
index-provenance claims require a differing measured, simulated or person-reported
fact to contradict them. Another source-reading prediction is insufficient.

`source_mappings` in the `statements` extension retains each statement's scalar
`path` and `lines`, `original_source`, `mapping_method`,
`source_derivation_sha256`, `source_sha256`, `source_artifact_sha256` and
`source_snapshot`. Mapping projects through `removed_pinned_line_ranges`; an
additional source derivation requires a unique exact statement-text match.
Distinct mappings append without replacing earlier snapshot mappings.
Removed or ambiguous statements are refused. The provider sees the scalar
TDStep fragment, declared statements and safe semantic context. Per-line ground
truth is withheld from its prediction.

## Separate TDStep debug-line costs (2026-10-03)

The `bfs-profile` request's Boolean `per_line` enables a second Callgrind execution
beside the existing whole-ROI run; it requires `memory: true`. `dynamic_memory`
keeps its whole-ROI meaning. The separate `per_line_memory` array contains TDStep
and its compiler-generated OpenMP function's self costs. The second binary adds
debug information and prevents TDStep inlining. One continuous, all-thread
collection spans the enclosing BFS ROI and emits one client dump before stopping.
Only TDStep and its outlined workers' self-cost rows are retained for statement
attribution. The simulated cache history includes intervening BFS work; these
are aggregate TDStep costs in that history, not independently cold invocations.
This interpretation keeps retained attribution limited to TDStep while avoiding
invalid counter summaries produced by repeated instrumentation starts/stops.

A per-line row contains `path`, `function`, `line`, `events`, `basis`,
`source_artifact_sha256`, `artifact_sha256`, `raw_artifact`, `raw_sha256`,
`execution` and `counter_validation`. `line: 0` means unresolved debug attribution
and is excluded from statement ranges. `events` maps event names to nonnegative
integer self counts below 2^63. `basis` is always `simulated`.
`source_artifact_sha256` binds the evaluated source; `artifact_sha256` binds the
debug binary. `raw_artifact` and `raw_sha256` identify the exact Callgrind dump.
`execution` retains integer `source`, `source_position`, `repetition` and
`dump_position` coordinates. The continuous collector uses one aggregate dump
per source/repetition; `dump_position` does not name a TDStep invocation.
Historical per-invocation rows retain `tdstep_position` instead. Exactly one of
these two coordinates is required, preserving truthful historical identities.
Source-file rows also retain relative `source_path` and `source_file_sha256`,
allowing attribution across identical baseline copies while checking the actual
debug source bytes.

Independent `counter_validation` requires `state: valid` and
`method` equal to `swdb.callgrind.lines.v1`. The parser resolves shared compressed
file/function names and relative instruction/line subpositions, sums repeated
self-cost lines and excludes inclusive cost after a `calls` association.
Counter hierarchy, duplicate identities, undefined compressed names, malformed
positions, integer bounds and multipart ambiguity are checked independently of
whole-ROI counter validation. Summed self costs cannot exceed the raw summary.
See the [Callgrind file format](https://valgrind.org/docs/manual/cl-format.html).

`statement_memory` holds derived facts with `statement`, `path`, `lines`,
`metric` equal to `last_level_misses`, integer `value`, `basis: simulated`, `unit: misses`,
the `profile` reference and `source_artifact_sha256`. The value sums `DLmr + DLmw`
over the mapped line range across all collected source, repetition and dump
coordinates. A line without attributable self cost has value zero. Compiler
line coalescing and inlined-header work limit attribution; scoring refuses data
with no attributable statement costs. Scoring reopens raw bytes, checks hashes
and reparses them; retained TDStep rows must match raw rows exactly.

`swdb annotate IMPLEMENTATION --source-snapshot ID --provider-config FILE
--runs-dir DIR --id RUN_ID` appends profiling claims. Optional `--profile ID`
supplies safe whole-ROI context. `swdb annotate-score IMPLEMENTATION
--source-snapshot ID --region-profile ID --table FILE` scores the latest claims
and drafts Josh's table for Yan-Ru to send. Both support
`--mode archevolve|extensa`; Extensa requires `--campaign` and an external mbit10
campaign record store under `/data1/yanruj` or `/data/yanruj`.

The implementation extension's `statement_annotation_scores` retains
`implementation`, `source_snapshot`, `region_profile`, `region_profile_sha256`,
`basis: simulated`, `gain_claim: false`, `spearman_rank_correlation`,
`top_3_overlap`, `top_3_overlap_count`, `rank_tie_policy`, `top_3_tie_policy`,
`contradiction_rule` and scored `statements`. Each scored statement additionally
has `expected_cost_rank`, `callgrind_rank` and `contradicted`. Observed ties receive
average ranks. Spearman correlation is the Pearson correlation of rank vectors;
constant observed ranks give null and an explicit `correlation_reason`.
Top-3 boundary ties use expected overlap under uniform choice and contribute
fractionally. The cost contradiction rule is absolute rank difference greater
than 1. Annotation reports and Callgrind ranks establish no native or hardware
gain.

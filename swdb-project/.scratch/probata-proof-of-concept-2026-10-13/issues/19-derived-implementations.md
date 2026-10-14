# 19 — Derived implementations

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 03:10 ET (resolved; Answer); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 02, 04
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "Proof routes", "Loop, modes and guards" (implementation records, campaign loop), "Records and levels" (pins), "ArchEvolve mode", "Testing Decisions" seams 3 and 4); decisions: [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) items 5-8 and its Later changes, [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 3, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 2
**Time estimate:** about 2 days

**What to build:** A certified enabling rewrite's result becomes a **derived implementation** in
the research database: an implementation record derived from its predecessor, listing the
strategies it applies and its contract lineage. From then on it behaves like any implementation.
Proposals target its snapshot and the site finder matches contracts against it, with no change to
either. An Extensa iteration may start from a certified derived implementation of the same kernel.
Each rewrite in a rewrite chain carries a link: contract hash, predecessor snapshot hash, result
hash, certification record and proof route. Speed is still compared against the root baseline.
Tested through `swdb validate`, `swdb build` and `swdb campaign --fixture`.

## Acceptance

- [x] **The record.** Certifying a fixture enabling rewrite yields an implementation record with
  origin kind `derived`, `derived_from` its predecessor, `applies` its strategies in order, and its
  contract lineage (the ordered rewrite contracts applied since the baseline implementation, each
  with ID and version, which an offload-only contract's required list is checked against, plus its
  content hash). `swdb validate` and `swdb build` accept it.
- [x] **Negative controls for the record.** A rejected or uncertified enabling result yields no
  derived implementation. A lineage that names a contract missing from the library, or skips a
  rewrite of the chain, is refused by `swdb validate`.
- [x] **Chains of two.** A derived implementation of a derived implementation carries the full
  ordered lineage back to the baseline implementation.
- [x] **Consumers unchanged.** A rewrite proposal that targets the derived implementation's snapshot
  is accepted by the existing proposal path. The site finder matches a contract against the derived
  implementation's access-pattern annotations. Neither tool's code changes; their existing tests
  pass, plus one new fixture each.
- [x] **Iteration start.** In a fixture campaign, an iteration starts from a certified derived
  implementation of the same kernel, and its candidate artifact's patch applies to that snapshot.
  Controls: a derived implementation of another kernel is refused; one with no certification record
  is refused.
- [x] **Root baseline stays the comparator.** A candidate artifact built on a derived implementation
  is certified alone against that derived implementation's snapshot, one contract per run, and also
  runs the kernel's correctness check against the root baseline (17 item 7). Its speed is compared
  against the root baseline, never against its predecessor (ADR 0005).
- [x] **Per-rewrite links.** Each rewrite in a fixture chain has a link with its contract hash,
  predecessor snapshot hash, result hash, certification record ID (the record 02 links for that
  rewrite's contract) and proof route (read from the route field, defined by 04, of that rewrite's
  proof record; "none yet" when it has no proof record, or one with no route, since the field is
  optional until 62). Fixture: one rewrite with a proof record that names its route shows it, one
  without reads "none yet". Control: a link whose certification record covers a different contract
  or a different predecessor snapshot is refused by `swdb validate`.
- [x] **A change reopens the rest of the chain.** Changing a predecessor's snapshot makes that
  rewrite's link, and every later link in the chain, read as no longer matching through
  `swdb build`. No record is rewritten.

## Notes

- **Not in this ticket:**
  - 02 — Campaign adapter returns every certification record: the record IDs these links cite.
  - 04 — Proof record tracer: the proof record's route field the links read (04 owns it).
  - 10 — Level rule: dependent candidate artifacts dropping to certified when a pin changes.
  - 20 — Formal-half frame: the offload-only contract's ordered list of required enabling
    contracts.
  - 16 — Post-campaign WP phase and budgets: proving final candidate artifacts after the campaign.
  - 62 — Route choice and predecessor proofs in the campaign: which route proves each final
    candidate artifact, the proofs of earlier rewrites it depends on, and intermediate-rewrite
    marking.
  - 63 — Experimental enabling contracts and the shared-contracts rule: enabling contracts that
    Extensa mode's rewriting role writes, and ArchEvolve mode's shared-contracts-only rule.
  - 52 — Split the bundled read offload: the first real rewrite chain; the check of a predecessor's
    lineage against an offload-only contract's required enabling contracts, and the pattern-class
    check on each derived implementation's annotations (17 item 5). This ticket records the lineage
    those checks read.
  - 53 — Chained vs direct vs bundled; A5 exit: route 1 proofs of derived implementations, route 3
    proofs and the comparison.
  - 54 — Upstream-GAPBS demo: the "any input" demo.
  - 18 — ArchEvolve mode level and handoff block: ArchEvolve-mode proofs and the handoff.
- Proof routes (17 as revised by 24): route 1 proves each derived implementation once, against the
  kernel's unit postcondition. Per final candidate artifact: route 3 when its predecessor is proven,
  else route 1 (choosing the route in a campaign: 62). Route 2 (catalog templates) is not built.
- Until promotion: the derived implementation lives in the research database only. ArchEvolve mode
  lets one enter the main database only through promotion; no path to the main database exists
  today (ADR 0014), and promoting a derived implementation is not built here.
- Assumption (not decided in the map): the record is written when a candidate artifact whose every
  contract is an enabling contract passes certification, in either mode, with no new command. A
  contract counts as enabling when none of its strategy effects offloads.
- Assumption (not decided in the map): the campaign file lists the certified derived
  implementations an iteration may start from, and the rewrite response names its start (the
  baseline when it names none), the way it already names its contracts. Who picks the start is not
  decided; confirm with Yan-Ru before coding if this reading is wrong.
- Intermediate-rewrite marking (a rewrite whose result only feeds a later rewrite: recorded, never
  evaluated, 17 item 8, versus a final candidate artifact) is built by 62. This ticket records
  derived implementations wherever certified enabling results arise and does not change which
  candidate artifacts are evaluated.
- Assumption (not decided in the map): the per-rewrite link sits on the rewrite's result record (the
  derived implementation, or the final candidate artifact). Its proof route is read on demand from
  the route field of the rewrite's proof record (04, a blocker) and reads "none yet" until one
  names a route, so no record is edited (ADR 0016).
- Generality: per kernel and contract; nothing BFS-specific. Contract fixtures only; no held-out
  kernel (BC, PR, SSSP).
- Tests run no verifier job. Full-suite runs on the Mac use at most 2 test workers.

## Answer

2026-10-14 03:10 ET. Built test-first on branch `probata-poc/t19`. Every acceptance box is met through
the Extensa campaign loop; one gap is listed below (ArchEvolve mode). Interface:
[`docs/reference/format-v0.4-derived.md`](../../../docs/reference/format-v0.4-derived.md); tables in
[`docs/reference/database.md`](../../../docs/reference/database.md#derived-implementation-tables).

**What exists now**

- **`swdb/derived.py`**: `is_enabling` (no strategy effect of kind `offload`), `record` (writes the
  derived implementation `<candidate>.derived` and its snapshot `<candidate>.derived.source`, the
  candidate artifact's tree), `start_problem` and `certification_problem` (iteration start),
  `validate_implementation` and `lineage_problems` (`swdb validate`), `link_rows` and `index`
  (`swdb build`).
- **Implementation schema:** `contract_lineage` (`{contract, version, content_sha256}` per rewrite
  since the baseline implementation) and `rewrite_links` (per contract: `contract`, `contract_sha256`,
  `predecessor_snapshot {id, sha256}`, `result {candidate, snapshot, sha256}`, `certification`).
  Candidate schema: optional `predecessor {implementation, snapshot {id, sha256}}`. Campaign file:
  optional `derived_starts`.
- **Campaign loop** (`swdb/campaign.py`): after certification passes and every contract is enabling,
  `_derive` records the derived implementation (entry field `derived_implementation`, or
  `derived_note` with why not). With `derived_starts`, the rewrite role answers `start`; the start is
  checked (listed, derived, same kernel, every link's certification present, certified and counting,
  snapshot present) before the candidate artifact is built on its snapshot; the workspace holds
  `STARTS.json` and `starts/<id>/<kernel file>`. Comparisons still use the campaign's baseline roles.
- **Fixture adapter** (`swdb/campaign_fixture.py`): optional fixture key `base_snapshot`; with it a
  candidate artifact is a real tree (start tree + patch; `build_failed` when the patch does not
  apply), and a candidate built on a derived implementation gets `predecessor`, `command.start` and a
  `root_baseline_correctness` matrix cell naming the root baseline. Without it nothing changes.
- **Real adapters** (`swdb/campaign_targets.py`): `predecessor_snapshot()` is the scalar-only snapshot;
  a `start` is refused (`provider_output_invalid`). A certified enabling result is recorded (tested on
  the native adapter with a scripted certification).
- **Build:** `swdb_contract_lineage`, `swdb_rewrite_links` (SWDB extension; `matches`/`reason` and
  `proof_route` computed on read). **Validate:** lineage = predecessor's lineage + this rewrite's
  contracts; lineage contracts in the library (when one is given); link certification covers the
  link's contract and result and was built on the link's predecessor snapshot.
- Neither `swdb/workflow.py` (proposal path) nor `swdb/site_finder.py` changed.

**Tests:** `tests/test_derived_implementations.py`, 14 tests: record; negative controls; start
controls (other kernel, no certification, not listed, patch does not apply); chain of two; root
baseline certification cell and comparator; validate controls (missing contract, skipped rewrite,
other contract, other predecessor snapshot); links with `route_1` and `none yet`; reopening on a
changed snapshot; proposal path; site finder; workspace and strict role schema; real native adapter.
Rerun green, one worker, no xdist: `test_crosswalk`, `test_db`, `test_lanl_shape`, `test_format_doc`,
`test_provider_role_schemas`, `test_applies`, `test_validate_rules`, `test_validate_application`,
`test_campaign_structure`, `test_site_finder`, `test_proposals`, `test_records`, `test_strategies`
(253 passed); `test_extensa_campaign`, `test_campaign_certification_links`, `test_extensa_targets`, `test_proof_records`, `test_extensa_boundary`, `test_campaign_candidate_records`, `test_campaign_budget_fixes`, `test_campaign_export`, `test_extensa_machinery` (176 passed, 19 min, log `/tmp/claude/probata-runs/t19/wide2.log`). No verifier job ran. Test scratch: `/tmp/claude/probata-runs/t19/` (pytest base
temps and logs only).

**Gap (not a box, but the ticket's first assumption says "either mode"):** ArchEvolve mode does not
record a derived implementation yet. `swdb certify` on a rewrite proposal's candidate artifact is the
natural hook (one contract per ArchEvolve proposal), but it builds and runs real code, so no test here
could drive it; wiring it untested was not done. ArchEvolve-mode `swdb submit` also refuses an Extensa
campaign's derived implementation (ADR 0013) until promotion, which is not built; the proposal-path
test therefore submits in Extensa mode (`--mode extensa --campaign`), the campaign's own research side.

**Assumptions** (the map leaves these open):

- Assumption: the derived implementation is written by the Extensa campaign loop right after
  certification, one per certified candidate artifact (so one per workload class), with ID
  `<candidate>.derived`, in the campaign's own store; its snapshot is the candidate artifact's tree
  (not copied) with the predecessor snapshot's protections.
- Assumption: `contract_lineage[].version` is null: rewrite contracts carry no version yet (ticket 20
  adds versions); the content hash names the exact entry.
- Assumption: `applies` gets the predecessor's entries, then each contract's strategies in order;
  a target is `unresolved` (except `input`), and a declared parameter is the candidate's knob of the
  same name, else `unresolved`. `swdb validate` accepts `unresolved` targets only on derived
  implementations. Nothing maps a contract to the pattern or loop it rewrote; the profiling agent's
  annotation (17 item 5, ticket 52) names them.
- Assumption: loops and access patterns are copied from the predecessor (minus loop code lines and
  agent claims/annotation facts) as a starting description; no statement annotations are copied.
- Assumption: `code` is one records-root copy of the result's kernel file
  (`implementations/<id>/<path>`, hash-checked by `swdb validate`); `swdb source-snapshot` refuses a
  records-root implementation, so its snapshot is only the one written with it.
- Assumption: `source_baseline`, `evaluator`, `build`, `run` are the predecessor's (the root baseline
  stays the source baseline); `verification.status: unchecked`.
- Assumption: campaign file `derived_starts` (an ID may name a derived implementation the same
  campaign records in an earlier iteration, `<cid>.it<n>.<class>.a<k>.derived`); the rewrite role's
  `start` is required (string or null) only in campaigns that list starts, so other campaigns' role
  schema is unchanged. Who picks the start: the rewriting role, among the listed ones.
- Assumption: "runs the kernel's correctness check against the root baseline" is a fixture
  certification matrix cell `root_baseline_correctness` (baseline: the derived implementation's
  `source_baseline`) with the attempt's outcome; real targets refuse derived starts, so no real
  certify runs it yet.
- Assumption: a final candidate artifact's link is computed from its `predecessor` field (written when
  it is built on a derived implementation) and its certified certification records; no link field is
  stored on candidates.
- Assumption: "matches" compares record hashes (the snapshot record's `artifact.sha256`, the candidate
  artifact's `sha256`, the library's content hash when a library is beside the records); trees are
  not re-hashed at build time.
- Assumption: a link's proof route is the `route` of the first proof record (by ID) whose subject is
  the link's result candidate artifact and whose contract pin is the link's contract; else `none yet`.
- Assumption: strategy records a campaign store lacks are copied from the team store when a derived
  implementation is recorded (as campaign preparation copies its inputs).

**Side findings:**

- The whole repository library cannot validate against an Extensa campaign store (38 library errors:
  the store lacks the intrinsic and operation records the entries cite), so `swdb validate --library`
  on a campaign store fails for reasons unrelated to it. The tests use a minimal library holding only
  the contracts a lineage names.
- A real target's derived implementation can never be a start yet (real adapters build only from the
  scalar-only snapshot); ticket 52's real chain needs that adapter change.

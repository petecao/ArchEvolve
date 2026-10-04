# 52 — Extensa campaign skeleton

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D5, D6, D7, D8, D10)
**Type:** slice
**Status:** resolved
**Blocked by:** 48, 49 (07, 24 resolved)
**Spec:** `../spec.md`

**What to build:** `swdb campaign CAMPAIGN_FILE` runs one iteration of an Extensa campaign end to end on fixtures, with a fixed region list.

## Acceptance

- [x] `schemas/extensa_campaign.schema.json` implements the D5 format (`swdb.extensa-campaign.v1`, one target per file). `swdb validate` checks files under `campaigns/extensa/` and refuses every case D5 lists.
- [x] One fixture iteration runs through `swdb campaign` with these steps:
  1. a fixed region list;
  2. one rewrite-role call returning one patch with per-class knob values;
  3. one candidate artifact per workload class;
  4. certification;
  5. the evaluator (fixture);
  6. record writing;
  7. feedback with D8's content and closed reasons.
- [x] Records go to the campaign record store `<runs root>/extensa/<campaign-id>/records/` (a temporary directory in tests). Every record carries `mode: extensa` and `campaign` (ticket 48).
- [x] Only the summary, promoted candidate artifacts and team claims with their evidence are copied to the team store. New library entries are written to `library/` in the experimental tier with the campaign as origin.
- [x] The new record kind `campaign_summary` (D6 shape, `schemas/campaign_summary.schema.json`) is registered in `vocab/record_kinds.yaml` and the store's kind list and documented in the format reference. The format-document and format-version tests pass.
- [x] Each provider call's role, model, effort and `counted` flag appear in the summary.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:49 ET by the agent under Yan-Ru's standing implementation approval.

What was built:

- `schemas/extensa_campaign.schema.json` (D5 format `swdb.extensa-campaign.v1`, one `target` per
  file) and `swdb/campaign.py:campaign_problems`, run by `swdb validate` over
  `campaigns/extensa/*.yaml` (one added call in `swdb/validate.py`). It refuses every D5 case: gem5
  repetitions other than 1 or more than one source, native repetitions below 5, `region_pairs: true`,
  another label, a budget above the spec default without `approval.raised_budgets` naming it, and
  `lanes: 2` without `approval.two_lanes`.
- `swdb campaign CAMPAIGN_FILE --records TEAM --provider-config P --fixture F [--runs-root R]
  [--library L] [--resume]` (`swdb/campaign.py`): one iteration runs the fixed region list, one
  rewrite-role call (provider launcher role `extensa_rewriting`, structured `{patch, contracts,
  knobs, unresolved}`), one candidate artifact per workload class with that class's knob values,
  certification (contract) or the uncertified label (no contract), the evaluator through a target
  adapter, records, and outcome-free feedback (ported `Feedback`, closed reasons, D8 fields only).
  From iteration 2 the rewrite workspace holds `best/<class>.patch` and `FEEDBACK.json` (test).
- Records go to `<runs root>/extensa/<campaign-id>/records/`. Team inputs are copied there
  untagged; every record the campaign creates carries `mode: extensa` and `campaign` through
  `workflow.CREATION_TAGS` (a two-line addition to `workflow.record`).
- Only the summary is copied to the team store (`writer.commit`). Library synthesis
  (`library.synthesize`) is a charged `synthesis` call; a certified entry is written to the library
  in the experimental tier with the campaign as origin (`library_operations.synthesize`).
- Record kind `campaign_summary` (D6 shape, `schemas/campaign_summary.schema.json`, plus a `setup`
  field for the profiling call), registered in `vocab/record_kinds.yaml` and `store.PLURAL`,
  documented in `docs/reference/format-v0.4-extensa.md`. Each provider call's role, model, effort,
  `counted` flag and classification appear in the summary.
- Target adapter: only `FixtureAdapter` (contract fixture). It clones team-store templates
  (protocol, candidate, evaluation, comparison) into tagged records labeled `contract_fixture`;
  numbers come from the fixture file. Without `--fixture` the command refuses (exit 2): the native
  and gem5 adapters are tickets 56 and 57. `regions: query` refuses until ticket 55.

Tests: `tests/test_extensa_campaign.py` (12 cases): the seven D5 refusals, named approvals, no-adapter
refusal, one fixture iteration end to end (tagged campaign records, untagged team copies, summary in
both stores, both stores validate, provider call fields), iteration-2 workspace content, and campaign
synthesis into a temporary library with the campaign origin. `test_format_doc` and
`test_format_versions` pass.

Assumptions (agent-decided, revisable):

- "Every record carries the tags" applies to records the campaign creates; copied team inputs keep
  their team form.
- A pause retries the iteration with fresh record IDs (`it<n>r<k>`), so no record is rewritten.
- The fixture adapter is the "evaluator (fixture)"; it never claims performance evidence.

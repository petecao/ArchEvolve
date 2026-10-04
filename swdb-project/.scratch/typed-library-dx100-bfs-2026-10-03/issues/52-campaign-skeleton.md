# 52 — Extensa campaign skeleton

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D2, D5, D6, D7, D8, D10)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 48, 49 (07, 24 resolved)
**Spec:** `../spec.md`

**What to build:** `swdb campaign CAMPAIGN_FILE` runs one iteration of an Extensa campaign end to end on fixtures, with a fixed region list.

## Acceptance

- [ ] `schemas/extensa_campaign.schema.json` implements the D5 format (`swdb.extensa-campaign.v1`, one target per file). `swdb validate` checks files under `campaigns/extensa/` and refuses every case D5 lists.
- [ ] One fixture iteration runs through `swdb campaign` with these steps:
  1. a fixed region list;
  2. one rewrite-role call returning one patch with per-class knob values;
  3. one candidate artifact per workload class;
  4. certification;
  5. the evaluator (fixture);
  6. record writing;
  7. feedback with D8's content and closed reasons.
- [ ] Records go to the campaign record store `<runs root>/extensa/<campaign-id>/records/` (a temporary directory in tests). Every record carries `mode: extensa` and `campaign` (ticket 48).
- [ ] Only the summary, promoted candidate artifacts and team claims with their evidence are copied to the team store. New library entries are written to `library/` in the experimental tier with the campaign as origin.
- [ ] The new record kind `campaign_summary` (D6 shape, `schemas/campaign_summary.schema.json`) is registered in `vocab/record_kinds.yaml` and the store's kind list and documented in the format reference. The format-document and format-version tests pass.
- [ ] Each provider call's role, model, effort and `counted` flag appear in the summary.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

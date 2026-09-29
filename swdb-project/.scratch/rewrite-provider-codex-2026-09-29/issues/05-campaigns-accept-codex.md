# 05 — Campaigns and the smoke script accept Codex

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Real campaigns can run with Codex or Claude, and candidates Claude already made stay
reusable. The instruction smoke script uses the default kind and takes a kind override.

## Acceptance

- [x] The native campaign runner accepts real campaigns with either kind and still refuses the fixture provider.
- [x] Campaign reuse accepts existing Claude receipts without model or effort, and a new case covers a Codex receipt.
- [x] The smoke script runs the default kind, and `--kind claude` switches it.

## Answer

Updated: 2026-09-29.

The native campaign admission accepts real Codex or Claude and still refuses external
fixtures. Reuse accepts both kinds while preserving the exact provider receipt and original
repair/time budget; legacy Claude receipts need no model/effort backfill. Submit/repair
supervisor allowances cover the new 1800 s per-call cap. The instruction smoke driver defaults
to Codex, accepts `--kind claude`, and writes the selected kind plus the new time bounds into
its provider configuration.

Validation: the legacy campaign-reuse suite passed as part of **73** focused tests; both
new Codex and legacy unpinned-Claude reuse cases passed (**2/2**). The smoke driver's CLI help
confirms `--kind {codex,claude}`. Real guarded smoke evidence is coordinated on mbit10 by
ticket 10; no real provider sessions ran on the Mac.

Context: `scripts/bfs_native_campaign.py`, `scripts/bfs_instruction_smoke.py`,
`tests/test_bfs_campaign_reuse.py`.

Follow-up on 2026-09-29: the natural-language DX100 smoke defaults to the registered
`bfs-dx100-scalar-only-20260929-a1.source`, rather than regenerating the full author source.
`--source-snapshot` selects another registered scalar-only derivative; missing registration
or a full author snapshot is refused before submission. Full snapshots remain selectable
by explicit author-code reuse proposals through `swdb submit`. Smoke summaries retain the
selected snapshot and provider kind.
Validation for the follow-up: `tests/test_bfs_instruction_smoke.py` completed with **4 passed**,
covering missing scalar registration before provider dispatch, default Codex and explicit
Claude selection, full author-snapshot refusal, and CLI help. The driver also checks that
the selected BFS text has no `TDStepMAA` or `DOBFSMAA` calls/definitions before submission.

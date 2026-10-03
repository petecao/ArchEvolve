# 24 — Retention and team-claim records; readers accept pruned files

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Deleted raw files are recorded in retention records, team claims and releases are recorded, and readers report a pruned file instead of failing.

## Acceptance

- [x] New record kinds retention (one per prune event) and team claim are registered and documented.
- [x] `swdb claim RECORD_ID... --audience NAMES` records one team claim citing one or more records; `swdb claim --release EVALUATION_ID` records that no team claim will cite a run.
- [x] The witness validator, coverage availability check and region comparator report a file with a retention record as "pruned, sha256 retained"; a missing file without one still fails.
- [x] Evaluation records are never edited.
- [x] Compare, aggregate and coverage still pass after a fixture prune, and fail without a retention record.

## Comments

Claimed and implemented by Codex retention/evaluator agent, 2026-10-03 ET.

## Answer

Implemented 2026-10-03 ET with immutable retention and team_claim record kinds, schemas, reference documentation and public `swdb claim` commands. Custody follows referenced evaluations, including aggregate components. Explicit releases cannot override team claims, and claimed runs retain their bulky output. Evaluation records are not changed by pruning.

Witness, coverage trace/package, coverage-availability and region raw-evidence readers accept only matching actual deletion receipts and report `pruned, sha256 retained`; durable intent records never masquerade as deletion receipts. Directory reconciliation checks every removed member against its retained hash and rejects unexpected added/changed files. Missing local bytes without a receipt remain a failure; historical remote-unverified handling remains explicit. A public disposable v2 gzip execution fixture was pruned and its coverage identity and verifier/witness chain revalidated, while the same missing trace without receipts failed. Coverage/profile regressions passed after adding their required operation inventory to fixture seeds. The focused collector/custody/read-only suite passed 58 tests. No remote evidence was deleted.

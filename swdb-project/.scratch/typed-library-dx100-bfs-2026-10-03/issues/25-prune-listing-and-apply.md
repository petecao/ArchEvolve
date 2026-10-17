# 25 — swdb prune: dry run, approval and apply

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 24
**Spec:** `../spec.md`

**What to build:** Yan-Ru can see exactly what a cleanup would delete, and only an approved listing deletes anything.

## Acceptance

- [x] `swdb prune --dry-run` lists every file under the run roots with its size, class (bulky, compact or input) and every record that references its path.
- [x] Inputs (referenced by a workload, source snapshot, build receipt or frozen protocol) are never proposed; only bulky files are.
- [x] `swdb prune --approve LISTING` records Yan-Ru's approval.
- [x] `swdb prune --apply LISTING` refuses an unapproved listing and any entry not classed as bulky; it deletes only the listed files, hashing each first, and writes retention records.
- [x] A dry run deletes nothing (test).

## Comments

Claimed and implemented by Codex retention/evaluator agent, 2026-10-03 ET.

## Answer

Implemented 2026-10-03 ET: dry-run lists every regular file under the selected run roots with size, classification, path references and evaluation owners; only uniquely owned bulky trace/checkpoint files without team custody are proposed. Inputs and compact re-reading evidence take precedence over filename classification. Symlinks and ambiguous ownership are refused. Approval pins the exact listing SHA, and apply requires that recorded approval, all-bulky entries, safe paths, current classification, matching sizes/hashes and fresh team custody.

Deletion serializes against public claims using a separate custody lock. An immutable prune_intent with every planned path/hash/size is durably persisted before the first unlink; successful actual deletions receive their own prune records afterward. Claims created after listing approval still stop apply. Disposable tests prove dry-run deletes nothing, missing approval refuses, changed bytes refuse, late claims refuse, and failed intent persistence leaves all bytes intact. Focused collector/custody/read-only suite: 58 passed. No external/remote deletion has occurred; retrospective cleanup still awaits Yan-Ru's concrete listing approval.

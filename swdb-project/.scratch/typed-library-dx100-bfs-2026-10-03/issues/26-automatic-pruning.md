# 26 — Automatic pruning of bulky raw output (ArchEvolve mode)

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 24
**Spec:** `../spec.md`

**What to build:** The evaluator prunes debug traces and checkpoints on its own, never before the records that re-read them exist. The Extensa-mode rule comes with ticket 54.

## Acceptance

- [x] The gem5 execute command prunes a run's checkpoints when the run completes with correctness passed; failed or interrupted runs keep theirs.
- [x] The comparison command prunes debug traces right after recording a comparison, for each compared run whose re-reading records for its kind exist (gem5 timed run: aggregate and comparison; coverage run: coverage report; profile run: profile package).
- [x] ArchEvolve-mode runs keep debug traces until a team claim cites them or `swdb claim --release` records that none will; runs a team claim cites keep them.
- [x] Files a record names as correctness output, witness chain, region raw report or companion acceptance are never pruned.

## Comments

Claimed and implemented by Codex retention/evaluator agent, 2026-10-03 ET.

## Answer

Implemented 2026-10-03 ET in evaluator completion/comparison hooks and `swdb/retention.py`. Completed correctness-passed gem5 execution may prune checkpoint payloads after its evaluation is durable; failed or interrupted executions retain them. Trace pruning waits for a successful persisted comparison and the actual re-reading records for the run kind: timed components need their aggregate and comparison; companion coverage needs its compact coverage report and explicit companion comparison; diagnostic profiles need their profile package and explicitly linked comparison. Broad ancestry is not treated as sufficient evidence.

ArchEvolve traces also require an explicit release; a team claim always retains them. Correctness output, witness chains, region reports, companion evidence and registered inputs are protected. All automatic deletions use the same durable-intent/hash/custody checks as approved pruning. Disposable fixtures exercise passed versus failed checkpoint retention, comparison prerequisites, release-triggered cleanup and team custody. Focused collector/custody/read-only suite: 58 passed. Real-run pruning acceptance remains contingent on the authorized mbit10 execution batch; no old raw output was deleted.

# 26 — Automatic pruning of bulky raw output (ArchEvolve mode)

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 24
**Spec:** `../spec.md`

**What to build:** The evaluator prunes debug traces and checkpoints on its own, never before the records that re-read them exist. The Extensa-mode rule comes with ticket 54.

## Acceptance

- [ ] The gem5 execute command prunes a run's checkpoints when the run completes with correctness passed; failed or interrupted runs keep theirs.
- [ ] The comparison command prunes debug traces right after recording a comparison, for each compared run whose re-reading records for its kind exist (gem5 timed run: aggregate and comparison; coverage run: coverage report; profile run: profile package).
- [ ] ArchEvolve-mode runs keep debug traces until a team claim cites them or `swdb claim --release` records that none will; runs a team claim cites keep them.
- [ ] Files a record names as correctness output, witness chain, region raw report or companion acceptance are never pruned.

## Comments

# 06 — Implementations apply strategies

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 04
**Spec:** `../spec.md`

**What to build:** an implementation can record the strategies it applies, and the SW
Ensemble Agent can see whether they helped compared with the baseline.

- [ ] The optional implementation field `applies`: an ordered list of `{strategy, target, parameters}`. Existing implementation records validate without edits.
- [ ] Rules, each with a passing and a failing fixture: the strategy resolves; the target is a loop or access-pattern ID in the same record, or `input`, and matches the strategy's target type; each parameter is one the strategy declares.
- [ ] `swdb build` includes applied strategies. `swdb implementations <kernel> --applies <id>` returns each matching implementation with its `applies` entry, its `derived_from`, and for each (input, machine) pair the newest complete profile ID of it and of its baseline, or null when either is missing.
- [ ] Tested with a fixture derived implementation and fixture profiles in a temporary records folder. Documented in the format doc and the query doc.

## Comments

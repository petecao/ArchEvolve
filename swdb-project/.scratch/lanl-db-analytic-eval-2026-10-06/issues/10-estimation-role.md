# 10 — The estimation role fills unknowns

Created: 2026-10-06
**Type:** slice
**Status:** claimed
**Blocked by:** 09
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** A new agent role in the provider launcher, with strict input and output schemas. Input: the characterization, the profile and the target description's unknown entries. Output: a value and a reason per unknown, with basis `estimated`, which becomes a new target-description version (D19). Estimates that depend on a filled value list it and show how much the result moves if it is halved or doubled.

## Acceptance

- [ ] Tests use a stub provider.
- [ ] A value for an already-known parameter is rejected.
- [ ] The role's workspace holds no timings, evaluator code or other candidates.
- [ ] Provider pins and audit are the same as for the other roles.

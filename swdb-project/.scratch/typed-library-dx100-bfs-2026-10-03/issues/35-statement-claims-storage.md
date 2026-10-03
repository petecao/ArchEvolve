# 35 — Agent-claim storage on statement annotations and access patterns

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Statement annotations and access patterns can hold agent claims beside recorded facts.

## Acceptance

- [ ] Each statement annotation and access-pattern entry gains an agent-claims list: value, basis (code_reading or inferred), model, effort, prompt sha256, input sha256s and contradicted-by.
- [ ] Agent claims never overwrite existing facts.
- [ ] Statement lines for the scalar-only snapshot map through its source derivation.
- [ ] The fields are documented and validated; tests cover them.

## Comments

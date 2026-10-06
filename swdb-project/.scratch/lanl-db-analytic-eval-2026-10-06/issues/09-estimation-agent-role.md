# 09 — Estimation agent role: an LLM fills unknown parameters only

Created: 2026-10-06
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 08
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** A new agent role through the provider launcher (ADR 0009) with a strict output schema. Input: the characterization, the profile and the target description's `unknown` entries; it runs once per description version and its values are frozen into it (D19). Output: a value and reason per unknown, with basis `estimated`. Never sees candidate timings.

## Acceptance

- [ ] Role workspace hides evaluator code, timings and other candidates (ADR 0006 / 0009 rules).
- [ ] Output outside the schema, or a value for a known parameter, is rejected.
- [ ] Provider pins and audit as for the other roles.

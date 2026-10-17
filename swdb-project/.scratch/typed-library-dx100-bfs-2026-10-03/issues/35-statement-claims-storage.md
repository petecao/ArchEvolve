# 35 — Agent-claim storage on statement annotations and access patterns

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Statement annotations and access patterns can hold agent claims beside recorded facts.

## Acceptance

- [x] Each statement annotation and access-pattern entry gains an agent-claims list: value, basis (code_reading or inferred), model, effort, prompt sha256, input sha256s and contradicted-by.
- [x] Agent claims never overwrite existing facts.
- [x] Statement lines for the scalar-only snapshot map through its source derivation.
- [x] The fields are documented and validated; tests cover them.

## Comments

## Answer

Implementation schemas now support additive `agent_claims` and `annotation_facts` on statement annotations and access-pattern entries. `swdb/annotation.py` preserves existing facts, records model/effort and exact prompt/input hashes, projects original statement ranges through the scalar snapshot's source derivation, and refuses deleted or ambiguous mappings. Cost predictions remain inferred; only measured, simulated or person-reported evidence can contradict pattern/index claims. Existing contradiction evidence is preserved.

Validation: expanded annotation/parser/mapping/driver tests plus all four format documentation checks pass (28 total); `swdb validate` passes 379 records. Repeated annotation retains earlier distinct snapshot mappings. Public fixture scoring checks raw bytes again, preserves matching profile facts/digest and refuses later raw tampering without changing claims. `docs/reference/format-v0.4.md` documents the new fields, mapping provenance, basis boundaries and scoring rules. Fixture claims remain explicitly classified as contract fixtures; the real seven-statement provider result belongs to ticket 36.

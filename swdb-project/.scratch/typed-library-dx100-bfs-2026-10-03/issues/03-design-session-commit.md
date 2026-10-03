# 03 — Decision records ADR 0007–0011 and the archevolve-handoff tracker updates

Created: 2026-10-03
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** The glossary, spec, map and tickets were committed on 2026-10-03. This ticket adds the decision records the spec lists under "Decision records" and updates the archevolve-handoff tracker; an agent drafts, and Yan-Ru approves the commit.

## Acceptance

- [ ] ADRs 0007–0011 are written, each saying what it amends, narrows or extends (ADR 0001, 0002, 0004, 0006 and the rewrite worker's no-tuning rule); each Status line reads proposed, or accepted if Yan-Ru's commit approval says so, and the commit message records which.
- [ ] ADR 0004 gains an "Updated" line pointing to ADR 0007.
- [ ] Per ADR 0008, the record-kind vocabulary's implementation meaning and the BFS kernel record's note say an implementation passes its correctness check on the hardware target it is written for.
- [ ] Archevolve-handoff tracker: the spec-adapter ticket gets status wontfix (superseded by this spec); the statement-crosswalk ticket is resolved with a pointer to ticket 01's message; the pull-request ticket is blocked by tickets 45, 56, 57, 58 of this feature, each written with this feature folder's name.
- [ ] `swdb validate` and the test suite pass.
- [ ] One commit, created only after Yan-Ru approves.

## Comments

# 03 — Decision records ADR 0007–0011 and the archevolve-handoff tracker updates

Created: 2026-10-03
**Type:** task
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** The glossary, spec, map and tickets were committed on 2026-10-03. This ticket adds the decision records the spec lists under "Decision records" and updates the archevolve-handoff tracker; an agent drafts, and Yan-Ru approves the commit.

## Acceptance

- [x] ADRs 0007–0011 are written, each saying what it amends, narrows or extends (ADR 0001, 0002, 0004, 0006 and the rewrite worker's no-tuning rule); each Status line reads proposed, or accepted if Yan-Ru's commit approval says so, and the commit message records which.
- [x] ADR 0004 gains an "Updated" line pointing to ADR 0007.
- [x] Per ADR 0008, the record-kind vocabulary's implementation meaning and the BFS kernel record's note say an implementation passes its correctness check on the hardware target it is written for.
- [x] Archevolve-handoff tracker: the spec-adapter ticket gets status wontfix (superseded by this spec); the statement-crosswalk ticket is resolved with a pointer to ticket 01's message; the pull-request ticket is blocked by tickets 45, 56, 57, 58 of this feature, each written with this feature folder's name.
- [x] `swdb validate` and the test suite pass.
- [x] One commit, created only after Yan-Ru approves.

## Comments

- 2026-10-03: Claimed by root for the authorized implementation batch. ADRs remain proposed; human send/review receipts are not inferred.

## Answer

Implementation/dispatch checkpoint, 2026-10-03 ET. The proposed ADRs 0007–0011, ADR 0004 pointer, implementation meaning and handoff supersession/PR blockers were committed in the authorized batch f62401c (commit message records proposed status). Validation/regression verification passes. The statement-crosswalk closure still requires ticket 01 actual message receipt; drafts are prepared and no team send is invented. Monitoring continues every 30 minutes; a fresh lease/capacity/source read is required before dispatch.

2026-10-03 08:21 ET closeout: ticket01 has two actual verified Sent receipts.
The handoff map now matches its ticket files: adapter06 is wontfix, crosswalk05
is resolved with the actual Josh mapping receipt, and PR07 explicitly lists
`typed-library-dx100-bfs-2026-10-03` tickets45,56,57,58 as blockers. ADRs remain
proposed, as recorded by implementation commitf62401c; the publication and
subsequent related actions are covered by Yan-Ru's explicit standing approval.
No actual Peter response, PR opening or merge is fabricated.

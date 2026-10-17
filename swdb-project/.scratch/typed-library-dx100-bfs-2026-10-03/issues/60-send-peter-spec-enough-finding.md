# 60 — Send Peter the "is the specification enough?" finding

Created: 2026-10-03
Updated: 2026-10-05 18:20 ET (comment: draft states the inputs, spec review C23)
**Type:** task
**Status:** ready-for-human
**Blocked by:** 58
**Spec:** `../spec.md`

**What to build:** Yan-Ru sends Peter the finding from ticket 58: what an intrinsic specification must contain for a rewrite provider to rebuild the TDStep rewrite.

## Acceptance

- [ ] Ticket 58 has written the draft at `../drafts/outgoing-2026-10-03/60-peter-spec-enough.md`. It holds the per-input table (certified out of samples, controls rejected out of total) and the finding. It cites repository path, lines, branch and commit for every file. It carries no raw run output, only compact results.
- [ ] Yan-Ru reviews and sends it manually and records the send date under Comments. The agent never sends it.

## Comments

- 2026-10-03 ET: created by ticket 47 under Yan-Ru's 2026-10-03 delegation. All communication with Peter, Josh and Eric is draft-only for agents.

- 2026-10-04 ET: ticket 58 wrote the draft (a3 result: 0/9 certified; scalar operands typed as values instead of register handles). Ready for Yan-Ru to review and send.

- 2026-10-05 18:20 ET (spec review C23): the draft now states that every input, including A, also got the scalar
  source, the lowering header and a build note, so input A was the spec plus an executable intrinsic interface.

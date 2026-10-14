# 09 — Spike verdict

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 06, 07, 08
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan": A1 row, overrun rule; "Testing Decisions", not unit tests; "Further Notes", risk table); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (item 2, fallbacks), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md) (items 4 and 8, levers and job budget), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about half a day

**What to build:** The decision that closes stage A1. This ticket gathers the four spike results
(05-08) with their evidence and applies the stop rule. If (b) failed after both levers, or (c)
failed within the box, A2-A6 and the Rocq track stop (see the stop-rule reading in the Notes): the
re-plan goes to Yan-Ru before any A2 ticket starts.
Otherwise the ticket records which bounded verifier A2 uses (SAW or crux-llvm) and what the spike
taught each A2 ticket. No new verifier runs happen here.

## Acceptance

- [ ] A1's exit check, restated from the design ("Proof-of-concept plan", A1 row; map
      [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 3 and 5)
      and answered item by item: "(a)-(d) pass; stop and re-plan with Yan-Ru if (b) fails after both
      levers or (c) fails in the box", where (a) SAW reads clang 22 bitcode and keeps ghost state;
      (b) 2 lanes under 15 min with per-call summaries at threads = 1, on Peter's read offload and
      the authors' `TDStepMAA`, every single-thread control refuted at the hand-derived minimum; (c)
      WP proves one read-offload unit at threads = 1 with agent hints within 60 min; (d) WP proves
      the sum lemmas and one unit of a synthetic CSR pull-sum fixture over reals.
- [ ] One table row per spike, (a) to (d): verdict ("pass", "pass via fallback", "pass with lever
      2" or "fail"), the deciding numbers (wall times, peak RSS, rounds), tool versions, and evidence
      paths with sha256.
- [ ] Each verdict is checked against its own ticket's acceptance list and evidence, not copied from
      its summary line. Any unmet criterion is named.
- [ ] The stop rule is applied in writing. Both conditions are answered "yes" or "no" with the
      evidence: (b) failed after both levers; (c) failed within the box.
- [ ] On a stop: a re-plan note for Yan-Ru names the failed spike, what was tried, and the responses
      the design's risk table gives, and flags the stop-rule reading in the Notes for Yan-Ru to
      confirm. This ticket's Status becomes `ready-for-human`, so 20 — Formal-half frame and 41 —
      Rocq: composition theorem statement and definitions stay blocked.
- [ ] Otherwise: the bounded verifier for A2 is named (SAW 1.6, or crux-llvm 0.12 on the C++ with
      hand stubs), citing 05's recorded decision.
- [ ] Otherwise: one line per A2 ticket (20 to 33, 60 — Strict-layer replay and whole-kernel
      reproduction, 61 — SAW whole-function equivalence (bounded direct route)), saying what the
      spike taught it, or "nothing". This includes whether lever 2 (shape splitting) was needed.
- [ ] A list of every spike verdict in a form A2 can reproduce: subject, variant, verifier, bounds,
      build constants, verdict. A2's exit needs generated artifacts to reproduce every spike verdict
      (33 — Minimum-bounds script and A2 exit).
- [ ] Results the stop rule does not cover follow the design's risk table: SAW failing (a) while
      crux-llvm passes is "pass via fallback" and needs no re-plan; (a) failing under crux-llvm too
      goes to Yan-Ru as an open question; a failed (d) goes to Yan-Ru for a re-plan.
- [ ] Every number is labeled a Mac result. None is a paper number.

## Notes

- **Not in this ticket:** 05 — Spike (a): SAW on clang 22 bitcode, 06 — Spike (b): 2 lanes under 15
  minutes, 07 — Spike (c): WP with agent hints, 08 — Spike (d): sums over reals (the runs
  themselves); 20 — Formal-half frame (the first A2 ticket); 33 — Minimum-bounds script and A2 exit
  (reproduces the spike verdicts with generated artifacts); 41 — Rocq: composition theorem statement
  and definitions (the Rocq track starts with A2, so the stop rule cannot waste it).
- **The spike is not a unit test.** Its recorded verdicts and this exit check judge it (design,
  "Testing Decisions").
- **Time box:** A1 is a 2-week box, not an estimate, so the 1.5x overrun rule does not stretch it.
  Time-boxed items end on their fallbacks.
- Assumption (not decided in the map): on a stop, the Status is `ready-for-human`, not `resolved`.
  Yan-Ru resolves the ticket once the re-plan is decided, which unblocks 20 and 41.
- Assumption (not decided in the map): a spike unfinished when the 2-week box ends counts as failed
  within the box.
- Reading of lever 2 (map 19 item 8, budget per bounded job): (b) "pass with lever 2" needs each
  shape job under 15 minutes, every shape job proven and the count check passed. The total wall
  time from 06 is shown too.
- Assumption (not decided in the map): after a failed (d), whether A2 continues while the re-plan is
  open is Yan-Ru's call; this ticket asks and does not decide.
- Stop-rule reading (flag for Yan-Ru; map 27 item 3 says only "before building anything"): a stop
  pauses A2-A6 and the Rocq track (41-43). The Extensa track (02, 04, 10-19, 55, 63; scripted
  adapter) continues unless Yan-Ru's re-plan says otherwise. Note: 55 also waits on 39, 48 and 60,
  which sit in paused stages, so the Extensa track's exit cannot pass during a stop.
- Assumption (not decided in the map): this ticket writes its verdict into its own Answer only. It
  does not edit the spike tickets or the A2 tickets.

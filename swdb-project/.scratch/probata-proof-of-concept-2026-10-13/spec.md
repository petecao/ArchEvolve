# Spec: Extensa Probata proof of concept

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:20 ET (O2–O10 decided); 2026-10-13 23:07 ET (review: tickets 60–63 added, stage table corrected, Rocq box clarified)
**Type:** spec
**Status:** ready-for-agent
**Blocked by:** None
Owner: Yan-Ru Jhou
Design: [the formal-verification map's spec](../formal-verification-2026-10-09/spec.md). Every decision
lives there or in the map ticket it links. This file only scopes the effort; it never restates a decision.
Tickets: [`issues/`](issues/), 01–63 (see "Numbering" below).

## Summary (read this first)

1. **Destination:** the method version is frozen and committed (ticket 59). Nothing after that belongs here.
2. **What this effort builds:** the proof machinery, records and Extensa-loop changes in the design spec's
   "Modules" tables, calibrated on BFS and the public C suites, first on the Mac, then on mbit10.
3. **What it never touches:** the held-out kernels BC, PR and SSSP. Two synthetic fixtures stand in for
   their riskiest proofs. The evaluation is the next effort
   ([`../probata-evaluation-2026-10-13/`](../probata-evaluation-2026-10-13/)).
4. **Size:** about 21 weeks on the main track (stages A0–A6); side tracks add no calendar time unless they
   slip.

## Stages and tickets

| Stage or track | Tickets | Weeks | Exit check |
|---|---|---|---|
| A0 Setup | 01, 03 | ~0.5 | the guard test (01) and the install verdicts or fallbacks (03) |
| A1 Kill-test spike | 05–09 | 2 (box) | ticket 09 applies the stop rule |
| A2 Foundations | 20–33, 60, 61 | ~6 | ticket 33 |
| A3 Proof-hint loop | 34–40 | ~4 | ticket 39 |
| A4 Concurrency | 44–50 | ~4 | ticket 49 |
| A5 Rewrite chains | 52–54, 62 | 2–3 | ticket 53 |
| A6 mbit10 and freeze | 56–59 | ~2 | ticket 59 |
| Extensa track (from day 1) | 02, 04, 10–19, 55, 63 | — | ticket 55 |
| Rocq track (from A2) | 41–43 | statement, then one 2-week box for 42 and 43 together | ticket 43 (42, then 43) |
| Strict-layer catch-up | 51 | — | ticket 51 |

**Numbering:** 01–59 come blockers first. Tickets 60–63 were added by the review on 2026-10-13 and break
that order: 46, 48, 55, 58 and 59 wait on some of them. A frontier scan still works, because a blocked ticket is
skipped whatever its number.

**O2–O10 are decided** (Yan-Ru approved the defaults, 2026-10-14 00:20 ET). Where a ticket says "O<n>
default" or "until Yan-Ru rules" for one of them, read it as decided.

## Rules for every ticket

- **Decisions come from the design spec.** A detail it leaves open is written as an assumption in the
  ticket's answer, never decided silently. A contradiction goes to Yan-Ru.
- **Mac memory:** one real verifier job at a time on the Mac, under an ~8 GB RSS watchdog; tests run with
  at most 2 workers. Tickets with no shared blocker may proceed in parallel, but their verifier jobs queue.
- **Mac disk:** keep at least 50 GB free. Check that LLVM 22 still works for the analytic evaluator after
  any Homebrew change.
- **Output:** before a large run, record its destination, size budget and readers (LR-06). Mac proof output
  goes to a runs folder outside the repo. Paper numbers come only from mbit10.
- **Long jobs:** a job or ticket set expected to run past 30 minutes gets a 30-minute status heartbeat
  (LR-07).
- **mbit10:** follow the lab-host rules (socket lanes and leases, no sudo, `/data1/yanruj/`).
- **Providers:** Codex is the default for every agentic role; Claude only in the evaluation's
  sensitivity check.
- **Overrun:** a stage at 1.5× its estimate stops for a re-plan with Yan-Ru. Time-boxed tickets (spike,
  Rocq, ThreadSanitizer) end on their fallbacks.
- **Cut order** if time runs short: 54, then 51, then 52, 53 and 62, then 55 (moves after the evaluation).
  Never cut A0–A4, A6 or the record tickets. A "Blocked by" edge marked "drop if cut" disappears with the
  cut ticket.

## Out of scope

Everything the design spec puts out of scope, plus every held-out kernel's contract, population and
research-question run (the evaluation effort).

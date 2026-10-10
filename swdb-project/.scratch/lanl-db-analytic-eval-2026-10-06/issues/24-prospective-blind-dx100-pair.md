# 24 — Prospective blind DX100 pair

Created: 2026-10-09 21:06 ET
Updated: 2026-10-09 22:33 ET (parked as wontfix: timing-only selection is enough for now; reopen if the paper needs estimate/timing agreement)
**Type:** slice
**Status:** wontfix
**Blocked by:** 17
**Spec:** `../spec.md`
**Time estimate:** 1–3 days plus lane time

**Why it exists:** Ticket 17's report found 0 eligible pairs: no campaign recorded
an estimate before timing. This ticket holds the work split out of 17 to produce
the first genuinely blind DX100 pair. One pair tests the path; it does not satisfy
D30 (20 pairs) and does not reopen ticket 18 by itself.

**Yan-Ru decides first:** whether to fund this before or instead of ticket 18's
decision, and whether a later frozen multi-campaign study follows.

**What to build:** One real DX100 complete-call numerical estimate, recorded
before its gem5 timing exists (D26), for the registered BFS candidate.

## Already done (under 17)

- [Complete-call counting shadow](../evidence/17-dx100-complete-call-shadow-20261009/README.md)
- [Protected LLVM count execution](../evidence/17-dx100-protected-llvm-count-execution-20261009/README.md)
- [Complete-call functional observations](../evidence/17-dx100-complete-call-functional-observation-20261009/README.md)
- [Prospective recovery plan](../evidence/17-actual-input-assembly-and-refused-strict-audit-20261009-a5/prospective-recovery.md)

## Remaining prerequisites

1. Fresh certification of the candidate under certification 1.7 (old receipt
   `certification.23f81442…` is refused under current defaults).
2. A supported functional-to-MMIO bridge, keeping the gem5 parked-ready/dispatch
   rule (not a one-cycle setup cost).
3. Supported whole-call costs and composition; missing premises stay unknown.
4. One blind estimate, then its timing, with the order recorded.

## Acceptance

- [ ] Yan-Ru sets scope and priority.
- [ ] One DX100 pair whose estimate receipt precedes its timing, passing the strict audit.

## Answer

2026-10-09 22:33 ET, Yan-Ru: **wontfix (parked).** Timing-only selection is enough for now.
Reopen only if the paper needs estimate/timing agreement; spec rule D35 then applies (no
Extensa campaign before an audited pre-timing numeric estimate). The work already done
under ticket 17 stays linked above.

2026-10-10 09:12 ET: if this ticket reopens, first re-decide the D30 interpretations listed in the spec, and bind the D35 numeric pairing check to the strict audit's admission receipt.

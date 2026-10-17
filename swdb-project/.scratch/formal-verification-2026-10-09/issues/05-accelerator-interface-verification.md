# 05 — How do verifiers model an accelerator's command interface?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

How does prior work give software verifiers a formal model of an accelerator's command
interface, including asynchronous completion and waits, so that code offloading work to it can
be proven?

Cover: ILA/ILAng, 3LA, D2A, Glenside, verified lifting (Tenspiler and similar), DMA and
asynchronous-fence verification, MMIO device models inside software verifiers.

Output: options for using DX100's executable functional model and our strict layer (CPU reads
see a sentinel until a covering wait) as verification semantics, with the cost of each.

## Answer

Resolved 2026-10-09 14:18 ET. Full findings:
[`../research/05-accelerator-interface-verification.md`](../research/05-accelerator-interface-verification.md).

- **Gist:** prior work models a hardware interface in four ways: instant calls, havocked
  state, a concurrent device thread, or ownership that a command takes away and a wait gives
  back. None ships a "sentinel until covering wait" semantics. The closest match is Cell DMA
  race checking (SCRATCH on CBMC, asyncStar), which uses ghost trackers or permissions per
  tag-based wait. ILA and ILAng give per-command semantics but leave asynchrony "outside of
  ILAs".
- **Recommendation:** split each DX100 proof into (H) a hazard obligation over a *proof edition*
  of the strict layer and (F) a functional obligation over instant-completion semantics. The
  proof edition is a rewrite friendly to formal verifiers: uncovered calls become assertions,
  tile reads are havocked instead of returning a fixed sentinel, and main-memory footprints are
  tracked. A reduction lemma (the analog of DRF-SC), proven once on paper, joins H and F.
  Cost: medium.
- **Never use the functional model alone for H:** it would *prove* `TDStepMAA`.
- **Challenges to ticket 01:** (1) the strict layer is synchronous for main memory, so in-flight
  DX100 loads and stores are never flagged; trusting it needs that scope stated. (2) The
  wrong-tile refutation rests on an assumed wait rule (`spec.md:481-485`). The functional model
  sets a store's *source* tile ready on completion (`MAA_functional.hpp:614`), which hints the
  authors meant that wait to cover the store. Confirm with gem5 before ticket 12 fixes the
  semantics.

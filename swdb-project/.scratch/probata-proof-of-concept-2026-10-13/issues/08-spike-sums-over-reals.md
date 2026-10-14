# 08 — Spike (d): sums over reals

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (d) and "Two efforts, split at the freeze"; "Modules", logic library; "Verifier lineup and order", floats as reals; "Further Notes", risk table); decisions: [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 3 days, inside the 2-week box

**What to build:** The spike's test of real-valued sums: the riskiest proof for the held-out PR and
BC kernels, done without touching them. Throwaway ACSL definitions give a range sum and a filtered
sum by an offsets array. WP then proves the sum library's three lemmas: additivity, regrouping a
flat edge range by owner vertex, and permutation of a finite sum. Last, WP proves one unit of a
synthetic CSR pull-sum fixture, written for this test, over real arithmetic. Never a PR unit: PR is
held out.

## Acceptance

- [ ] Throwaway logic definitions of a range sum and a filtered sum by an offsets array (map
      [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 4). Each is
      non-recursive or primitive recursive on a non-negative integer argument (map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 2). No
      axioms.
- [ ] WP 33.0 with `-wp-model +real` proves each lemma: additivity; regrouping a flat edge range by
      owner vertex; permutation of a finite sum. Induction goes through `Wp.induction` scripts,
      saved and replayed on a fresh run (map
      [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 7). Per lemma:
      solver, time and script recorded.
- [ ] `\false` check: WP cannot prove `\false` from the definitions and lemmas alone (map 16 item 9).
- [ ] A synthetic CSR pull-sum fixture in C: each vertex's output is a sum of `float` inputs over
      its in-edge range. Its unit postcondition states each output as a range sum, in map 24 item
      2's form. Sizes are symbolic; threads = 1.
- [ ] WP proves the fixture's unit against that postcondition, using the lemmas. In the
      per-property report of a fresh run (`-wp-cache none`), every goal is Valid and every smoke
      test passed (a smoke goal WP proves Valid signals dead code). No `Extern` outside the
      contracts of summaries and `maa_*` calls, each an assumption entry (design S7).
- [ ] Negative control: a seeded-bug copy of the fixture (one edge range off by one), with the same
      hints, is not proven. WP reports "not proven", never "refuted".
- [ ] Every hint is one of map [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md)
      item 5's allowed kinds. Recursive definitions appear only in the throwaway logic file.
      Provenance is recorded per hint.
- [ ] Rounding is listed as a platform-choice assumption entry (map
      [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 4).
- [ ] Nothing in the fixture comes from the fork's PR or BC code or the authors' DX100 code. The
      Answer says what the fixture was written from.
- [ ] The Answer gives "pass" or "fail" per lemma and for the unit, with times, evidence paths and
      sha256.

## Notes

- **Not in this ticket:** 26 — Logic and sum libraries (the real, versioned sum library); 38 —
  Calibration on the public C suites; 40 — Bucketed-relaxation fixture (SSSP's risk); 09 — Spike
  verdict; evaluation 03 — PR held-out contract and contract proof and evaluation 02 — BC held-out
  contract and contract proof ([evaluation tickets](../../probata-evaluation-2026-10-13/issues/);
  the first PR and BC proofs, after the freeze).
- **Throwaway.** Nothing here becomes the sum library of 26.
- **Held-out rule:** BC, PR and SSSP are never proven or used for calibration before the freeze
  (59 — Method-version review and freeze; map
  [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) items 5 and
  7).
- Assumption (not decided in the map): the fixture's unit is one flat loop over the edge range, the
  flattening case map 24 item 4 names, so the regrouping lemma is used. A nested per-vertex loop
  alone would leave that risk open.
- Assumption (not decided in the map): (d) has no time bar. Per-goal times are recorded, and goals
  that need more than map 13 item 11's starting 30 s per solver are listed for 09.
- A failed (d) is not one of the stop rule's two conditions (map
  [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 3). The
  design's risk table says "re-plan", so 09 hands it to Yan-Ru.
- Assumption (not decided in the map): (d) passes only on WP proofs, as the A1 row says. The
  lifting-lemma fallback to Rocq (map 11 item 7) is not tried here; if WP fails, 09 reports it.
- Assumption (not decided in the map): hints may come from the implementing agent or from Codex.
  The spike is throwaway agent-written work (map 27 item 3), and the sum library is a once-proven
  method part, which need not be fully automatic (map
  [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) item 8 lets
  Yan-Ru assist under the same hint rules). Unlike (c), (d) does not test agent hints.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs and per-goal reports go to a Mac runs
  folder outside the repo, host `mac` (map 26 item 5). If 05 has not yet recorded that folder, record
  its path, size budget and readers before the first run (LR-06).
- **Risks:**
  - WP proved no induction lemma on its own; Alt-Ergo, Z3 and CVC5 all timed out. With
    `Wp.induction`, one of three subgoals was never attempted, cause unresolved (map 11 research).
  - No Rocq in the `framac-33` switch.
  - WP must run outside the agent sandbox: inside it, the Why3 server socket is blocked and WP
    reports `[Failure]`.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog. Keep at least 50 GB
  free.

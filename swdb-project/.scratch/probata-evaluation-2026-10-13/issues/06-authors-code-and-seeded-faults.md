# 06 — Authors' code and seeded faults

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 03, 04 (drop 03 if cut)
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": subjects per held-out kernel; "Refutation, repair and bugs"; "Concurrency": negative controls; "DX100 proof semantics": semantics negative controls; S1, S2; open point O1; O5: repairing the authors' code; O6: replay labels); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [20](../../formal-verification-2026-10-09/issues/20-dx100-pr-reset-check.md), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (items 3-5, 10), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10: replay and "bug"), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md)
**Time estimate:** about 3 days

**What to build:** For each held-out kernel, the authors' DX100 code as written (BC: `PBFSMAA` with
`BrandesMaa`, its DX100 driver, by O2's default; PR: `PageRankPullMAA`; SSSP: `DeltaStepMAA`) is
checked as an ordinary candidate artifact. If it matches the
held-out contract, it runs the normal per-candidate path. If it matches no contract, it keeps the
level certification gives, and its direct proof is reported beside that level (spec O1). Either way
it stays apart from the rates. The authors' PR is refuted and then repaired; the one-line reset is
the expected repair. Each kernel's seeded faults are registered as subjects that must be refuted:
the held-out contract's negative controls, its concurrency-labeled ones included. This gives RQ4 its
fixed fault list. The results on the authors' code go to 09, which owns the authors' row.

## Acceptance

- [ ] For each kernel, a contract-match check decides whether the authors' function as written
      applies the held-out contract. The result is recorded.
- [ ] Matching code runs the per-candidate path: `swdb certify`; the bounded rungs at minimum bounds
      (the one-thread bounded verifier (SAW, or crux-llvm `-f real` for a real-valued unit per
      proof-of-concept 23) at threads = 1; CIVL and GenMC at threads ≤ k); then, unless a bounded
      rung refuted it,
      WP through the proof-hint loop (S6). `swdb candidate-level` computes its level as for any
      candidate artifact.
- [ ] Code that matches no contract keeps the level certification gives. Its direct proof (route 1:
      unit postcondition plus hazard freedom) runs through `swdb prove` and is reported beside the
      level as "direct proof, no matching contract: <verdict>". A test shows `swdb candidate-level`
      gives it no proven level.
- [ ] The authors' code never enters RQ1's rates or RQ4's repair rate. Its results (contract match,
      levels, direct-proof verdicts, PR's refutation and repair) are handed to 09, which owns the
      authors' row.
- [ ] The authors' PR counts as caught when it fails certification under 01's check or is refuted
      (spec O5, map ticket 20). Both results are recorded.
- [ ] The bounded verifier runs on the authors' PR whatever certification says (refute, then
      repair; O1). It refutes at an iteration count of at least 2, with a counterexample. The
      refutation is replayed on the strict layer and labeled (O6's labels). A whole-kernel
      reproduction record (01's PR check failing on a real input) lets "bug" compute on read. Replay
      and reproduction come from
      [proof-of-concept 60 — Strict-layer replay and whole-kernel reproduction](../../probata-proof-of-concept-2026-10-13/issues/60-strict-layer-replay-and-kernel-reproduction.md).
- [ ] The authors' PR goes through counterexample-guided repair: at most 5 rounds, 3 independent
      runs. The loop comes from
      [proof-of-concept 13 — Counterexample-guided repair](../../probata-proof-of-concept-2026-10-13/issues/13-counterexample-guided-repair.md),
      which accepts the refuted record even when the authors' PR failed certification (O1, O5).
      Each repaired candidate artifact is certified and proven again. Each run records whether it
      found the one-line reset; a reverted repair is flagged.
- [ ] Seeded faults are registered per kernel: the held-out contract's negative controls, its
      concurrency-labeled ones included. Each entry has its source and its label (single-thread,
      concurrency phase, runtime only). Formal-visible entries expect "refuted"; runtime-only entries
      are listed by label with no bounded verdict expected. Must-prove controls are listed apart.
      The semantics controls are not registered per kernel (see Notes). The manifest is committed
      before any RQ4 run.
- [ ] Every `proof_hinting` workspace that shows the authors' code has it as the candidate artifact.
      A rewriting workspace shows it only for a repair call in which it is the refuted candidate
      artifact (O5). No population rewriting workspace (05) shows it (provider workspace and guard
      seam).

## Notes

- **Not in this ticket:** 02 — BC held-out contract and contract proof, 03 — PR held-out contract and
  contract proof, 04 — SSSP held-out contract and contract proof; 05 — LLM candidate populations;
  07 — RQ1 and RQ2 runs; 09 — RQ4: refutation and repair (running the seeded faults, their rates,
  repair statistics, mirrors and performance; the authors' row, built from this ticket's results).
- **Why this is known only now:** each contract is drafted blind, so whether the authors' code
  matches it is known only after the freeze (spec O1, "Where it matters").
- **Caught vs refuted (O5):** a certification rejection under 01's check already counts as caught;
  it is reported beside, not as a level. The bounded run still happens, because repair needs a
  counterexample (map ticket 23 item 10; O1). Assumption (not decided in the map): if the bounded
  verifier does not refute the authors' PR at an iteration count of 2, stop and ask Yan-Ru before
  any repair call.
- Assumption (not decided in the map): code that matches no contract gets the bounded rungs
  against the kernel's unit postcondition, at the held-out contract's minimum bounds, raised to an
  iteration count of 2 for PR if the minimum is lower. The design keeps the bounded direct route
  (against the baseline;
  [proof-of-concept 61 — SAW whole-function equivalence (bounded direct route)](../../probata-proof-of-concept-2026-10-13/issues/61-saw-whole-function-equivalence.md))
  only for kernels with no unit postcondition and names no bounds for this case, yet O1 wants such
  code refuted and repaired.
- **BC's subject (O2 default; flag for Yan-Ru):** BC's authors' code subject is `PBFSMAA` with
  `BrandesMaa`, the DX100 Brandes driver that calls it and has its own `maa_*` calls. O2's default
  has the guard name `BrandesMaa` too (user story 77: every authors' DX100 function); this ticket
  reads that as putting it in BC's subject. Ask Yan-Ru before the manifest is committed.
- **Reading (flag for Yan-Ru):** the design lists seeded faults as "each contract's negative
  controls plus the semantics and concurrency controls". This ticket reads "concurrency controls"
  as the contract's own concurrency-labeled negative controls. The semantics controls are proven per
  method and proof-semantics version, so 12 reports them once as method evidence, not per kernel.
  Ask Yan-Ru before the manifest is committed.
- **Repair workspace (O5, default until Yan-Ru rules):** the rewriting role may see the authors'
  code only when it is the refuted candidate artifact under repair, in the evaluation, never in a
  campaign. Proof-of-concept 13 builds this guard exception and the repair of a refuted, uncertified
  authors' candidate artifact. Check that the guard allows this one case before the first repair
  call, and stop and ask Yan-Ru if it does not. Keep these calls apart from 05's population calls.
- Assumption (not decided in the map): repairs of the authors' other refutations, if any, run in 09
  under its protocol. The design shows only the authors' BFS code racing at threads > 1 (design
  spec, "Concurrency"); whether `PBFSMAA` or `DeltaStepMAA` race is known only after these runs.
  This ticket repairs only PR, as its scope says.
- The PR defect is latent at the authors' own setting of 1 iteration (ticket 20 item 4). Say so
  wherever it is reported.
- **Cut order:** if PR is cut, the Blocked by edge to 03 drops (this ticket then waits only on 02
  and 04), and PR's share goes with it: `PageRankPullMAA`'s check, refutation and repair (effort
  spec).
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.

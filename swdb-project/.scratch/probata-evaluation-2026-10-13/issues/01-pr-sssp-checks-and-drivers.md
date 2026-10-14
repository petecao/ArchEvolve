# 01 — Correctness checks and certification drivers for PR and SSSP

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** proof-of-concept 59
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": held-out contracts, PR's correctness check, performance; "Refutation, repair and bugs": the whole-kernel reproduction; "Testing Decisions"); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [20](../../formal-verification-2026-10-09/issues/20-dx100-pr-reset-check.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (item 10), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (item 2, the SSSP side finding), [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (item 10, the "bug" bar)
**Time estimate:** about 1 week

**What to build:** After the freeze, PR and SSSP become kernels SWDB can evaluate and certify, as BC
already is. Each gets a kernel plugin (kernel record, baseline implementation, workloads, native
evaluator run), a correctness check, and an evaluator-owned DX100 certification driver that runs on
the strict layer. PR's check compares every vertex's score with a reference recomputation at a fixed
iteration count of at least 2, on inputs away from the fixed point. It never uses GAPBS's convergence
verifier at the authors' defaults: at 1 iteration that verifier fails correct code too, so it cannot
tell right from wrong (ticket 20). SSSP's check compares distances. Both baselines (`PageRankPullGS`,
`DeltaStep`) pass, and each check rejects its negative controls. Later tickets need this: certifying
held-out candidate artifacts, gate 4 of the five gates, whole-kernel reproductions ("bug"), and RQ4's
performance runs.

## Acceptance

- [ ] PR and SSSP kernel records pass `swdb validate` and `swdb build`. Each names its baseline
      implementation as found in the fork (`PageRankPullGS`; `DeltaStep`), its correctness check with
      its stated tolerance, and its registered workloads.
- [ ] PR's check compares per vertex against an independent reference recomputation at a fixed
      iteration count of at least 2. The count and the tolerance are recorded with the check. GAPBS's
      convergence verifier never decides the verdict.
- [ ] Every registered PR workload is away from the fixed point: the reference's error stays above
      the loop's tolerance after every iteration before the fixed count, so no run exits early
      (ticket 20 item 4). Registration refuses a workload that fails this, and a test shows the
      refusal.
- [ ] SSSP's check compares every vertex's distance with a reference recomputation.
- [ ] Both baselines pass their checks on every registered workload, natively and through their
      DX100 certification driver on the strict layer.
- [ ] PR's check rejects a copy of the baseline whose per-vertex sum carries over between iterations
      (ticket 20's defect pattern, rebuilt on the baseline). The same test shows GAPBS's convergence
      verifier at 1 iteration cannot tell this copy from the baseline, so the fixed count is what
      catches it.
- [ ] Each check rejects its other negative controls (see Notes). Each rejection is attributable to
      the break, not to anything else the code does.
- [ ] A contract-fixture candidate artifact per kernel runs through its DX100 certification driver
      under `swdb certify`. The records carry `contract_fixture` evidence and pass `swdb validate`.
      The driver records outputs from evaluator code the candidate artifact cannot see, as BC's
      driver does.
- [ ] Tests that need LLVM 22 skip cleanly when it is missing. Mac test runs use at most 2 workers.

## Notes

- **Not in this ticket:** 02 — BC held-out contract and contract proof (BC's plugin, check and
  driver already exist); 03 — PR held-out contract and contract proof, and 04 — SSSP held-out
  contract and contract proof (each contract's own checks and negative controls); 06 — Authors' code
  and seeded faults (running the authors' PR and SSSP code against these checks).
- **Held-out rule:** this is the first ticket to touch PR and SSSP, so it starts only after the
  freeze. Its checks, drivers and controls are evaluator code; no agent role sees them.
- Assumption (not decided in the map): the plugins, checks, drivers and controls copy nothing from
  the authors' DX100 functions (`PageRankPullMAA`, `DeltaStepMAA`), so the blind drafting in 03 and
  04 cannot inherit them.
- Assumption (not decided in the map): PR's per-vertex tolerance follows BC's float-epsilon
  comparison (ticket 20 item 6). The exact value is set here and recorded with the check.
- Assumption (not decided in the map): the fixed iteration count is a check setting chosen here (at
  least 2). It is separate from the PR contract's iteration-count bound dimension, which 03 derives.
- Assumption (not decided in the map): SSSP's comparison is exact equality against an independent
  shortest-path recomputation, since weights are integers (map ticket 24 item 2).
- Assumption (not decided in the map): the other negative controls are, for PR, a copy that stops
  after 1 iteration and a copy with one vertex's score perturbed; for SSSP, a copy that skips one
  relaxation (a distance too large) and a copy that undercuts one distance (too small). Add more if
  a check shows a blind spot.
- **Risk:** the fork builds without `NDEBUG`. SSSP's `assert(false)` on a small non-empty current bin
  never fires with the default delta of 1 and positive weights (map ticket 24, side finding); the
  contract needs "delta ≤ least weight". Assumption (not decided in the map): register only SSSP
  workloads with delta ≤ least weight and record delta per workload; a baseline failure outside it
  is a workload error, not a check failure.
- **Cut order:** PR is cut third in the evaluation (effort spec). If PR is cut, this ticket's PR half
  goes with it. SSSP is on the floor.
- Internal findings about the authors' code are never sent to the authors or the team without
  Yan-Ru.

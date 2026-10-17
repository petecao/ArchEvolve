# 05 — LLM candidate populations

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 03, 04 (drop 03 if cut)
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Evaluation design": subjects per held-out kernel, protocol, cost; "Providers and machines"; "Loop, modes and guards": provider guard; "Extensa mode": iteration ladder, start gate); decisions: [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md), [28](../../formal-verification-2026-10-09/issues/28-extensa-iteration-ladder.md)
**Time estimate:** about 1 week plus about 90 mbit10 lane-hours

**What to build:** For each held-out contract (BC, PR, SSSP), the ArchEvolve-mode rewriting role makes
independent rewrite proposals: Codex, model pinned in the run plan, not gated by D35, no iteration
ladder. Proposals are deduplicated by normalized content hash. Each distinct proposal is certified
against its contract. Proposing stops at 20 distinct certified candidate artifacts or 60 proposals,
whichever comes first. The certification rate is reported. Before any proof run, the population is
frozen by content hash. Reference instances are excluded. The result is the fixed set of LLM
candidate artifacts that RQ1, RQ2 and RQ4 measure.

## Acceptance

- [ ] A run plan is committed before the first proposal. It pins the provider kind (Codex), model and
      effort (the design's pin is `gpt-5.6-sol`, effort `xhigh`), the stop rule, and the
      normalization rule for content hashes. A pin change is a new run plan, and the affected
      proposals are redone.
- [ ] Before the first held-out proposal, the provider workspace and guard test passes: inputs naming
      `PBFSMAA`, `PageRankPullMAA`, `DeltaStepMAA` or `BrandesMaa` (BC's DX100 driver; spec O2
      default) are refused.
- [ ] Every proposal is an independent ArchEvolve-mode rewriting call. Its `workspace.json` shows no
      `LADDER.json`, no earlier proposal or other candidate artifact, no authors' DX100 function, and
      no evaluator inputs or workload data (ADR 0009). It runs outside any Extensa campaign, so D35
      does not gate it.
- [ ] Each proposal record carries its provider kind and pin and its normalized content hash. A
      proposal whose hash repeats an earlier one is recorded as a duplicate and not certified again.
- [ ] Each distinct proposal is certified with `swdb certify` against its contract, on mbit10 inside
      a socket lane. Per contract, proposing stops at 20 distinct certified candidate artifacts or 60
      proposals.
- [ ] A proposal whose hash equals its contract's reference instance is excluded from the population
      and listed as excluded.
- [ ] The certification rate per kernel is reported with its counts: proposals made, distinct,
      certified, rejected, uncertified, excluded.
- [ ] The population manifest (kernel, contract, content hash per candidate artifact) is committed
      before any proof run on a member. The first population proof record postdates that commit.
- [ ] Lane-hours used are recorded against the ~90 lane-hour estimate, with host load per batch and
      the run folder actually used.

## Notes

- **Not in this ticket:** 02 — BC held-out contract and contract proof, 03 — PR held-out contract and
  contract proof, 04 — SSSP held-out contract and contract proof (the contracts); 06 — Authors' code
  and seeded faults; 07 — RQ1 and RQ2 runs (the bounded rungs and proof runs on this population);
  09 — RQ4: refutation and repair (refutation rates and repair on this population).
- **Why no ladder:** the population comes from independent calls, so its certification rate stays a
  rate over independent proposals (map ticket 28 item 9).
- **Precision:** about ±22 points per kernel and ±13 pooled (map ticket 18 item 6).
- Assumption (not decided in the map): duplicates count toward the 60-proposal cap, since they are
  proposals made. The rate is reported over both proposals made and distinct proposals.
- Assumption (not decided in the map): the normalization rule (for example, whitespace and comments
  stripped before hashing) is chosen here and recorded in the run plan.
- Assumption (not decided in the map): rejected and uncertified proposals keep their records but are
  not population members, since RQ1 counts certified candidate artifacts that apply a contract.
- Assumption (not decided in the map): population proposals get no certification repair call
  (ArchEvolve mode's one bounded repair, ADR 0010), so the certification rate stays a rate over
  single proposals. Counterexample-guided repair of refuted members is 09's.
- **mbit10:** check both socket leases and the legacy lease before dispatch; run `df -h /data1 /data`
  first; raw output goes to `/data1/yanruj/EvolveSWDB_runs/` (or `/data/yanruj/EvolveSWDB_runs/` when
  `/data1` has under 20 GB free); never more than 2 lanes. The run is past 30 minutes, so post a
  30-minute status heartbeat (LR-07).
- **Cut order:** if PR is cut, PR's share of this ticket goes with it (effort spec), and the
  Blocked by edge to 03 drops: this ticket then waits only on 02 and 04.
- Assumption (not decided in the map): population proposals use the ArchEvolve-mode rewriting role's provider call and `swdb certify` only, not the submit path proof-of-concept 18 extends. No bounded gate, WP or repair runs on them until evaluation 07 and 09.

# 06 — Spike (b): 2 lanes under 15 minutes

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (b); "Proven once vs per candidate", scale pass bar; "Bounds"; "DX100 proof semantics"; "What a proven verdict asserts", harness `assume`s; "Further Notes", risk table); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [08](../../formal-verification-2026-10-09/issues/08-wrong-tile-prototype.md), [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md), [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 4 days, inside the 2-week box

**What to build:** The spike's scale test: does Extensa's scaling failure repeat? In map 08, the
inlined strict-layer port made every safe 2-lane run time out. Here, throwaway agent-written
per-call summaries of the DX100 calls replace that port. With them, the bounded verifier chosen in
05 must prove two real proof units at threads = 1 in a build with `TILE_SIZE` = 2: one `TDStep` call
with Peter's read offload, and one call of the authors' `TDStepMAA`. Each proof must finish in under 15
minutes on the Mac. Every single-thread negative control must be refuted at map 19's hand-derived
minimum bounds. If lever 1 (per-call summaries) is not enough, lever 2 (shape splitting) is tried.
Failing after both levers is a stop condition for 09 — Spike verdict.

## Acceptance

- [ ] One throwaway summary per DX100 call the two units make, used as overrides (SAW specs, or
      crux-llvm hand stubs if 05 chose crux-llvm). They follow map
      [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md)'s rules: values
      as if each command finished at issue; an unready read is an assertion failure; the gem5 wait
      rule. Neither proof inlines the strict-layer port.
- [ ] Every run uses map [19](../../formal-verification-2026-10-09/issues/19-bounded-verdict-bounds.md)'s
      hand-derived minimum: threads 1 (`NUM_CORES` = 1), lanes 2 (`TILE_SIZE` = 2), chunk 2, and
      inputs symbolic up to frontier 2, vertices 3, edges 3. Every build constant is recorded
      exactly.
- [ ] Peter's read offload: the unit is proven (BFS unit postcondition and hazard freedom) in under
      15 minutes wall time. Wall time, peak RSS and solver recorded.
- [ ] The authors' `TDStepMAA`: the unit is proven, same properties, same budget, same records.
- [ ] Peter's read offload: each of the contract's seven single-thread controls (`dropped_wait`,
      `read_before_wait`, `index_wrap`, `forged_frontier`, `dropped_continuation`,
      `chunk_off_by_one`, `skipped_cas_recheck`) is refuted at these bounds, with the same harness
      and summaries, each with a counterexample. The check that fires is attributable to the break
      (glossary: negative control).
- [ ] `TDStepMAA`: each of its single-thread controls (see the assumption below) is refuted the
      same way.
- [ ] The harness has no `assume` beyond summary-generated ones and proof-unit preconditions. Map
      08's `parent[v] >= -1` assume is widened to every value `InitParent` writes (map
      [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) item 10). Map
      08's relabeling (shape mode) is not used (map 19 item 4).
- [ ] If a proof misses 15 minutes with lever 1, lever 2 runs: one job per graph shape, values
      symbolic, with a count check against a closed-form count of shapes. A missing or failed shape
      job leaves the whole verdict "not proven" (map 19 item 4). The 15-minute bar applies to each
      shape job (map 19 item 8: the budget is per bounded job); the total wall time is recorded too.
- [ ] A timeout is recorded as "not proven, timeout" at these bounds. No run falls back to smaller
      bounds or to 1 lane (map 19 items 1 and 8).
- [ ] The Answer has one table row per proof and control: subject, lever, verdict, wall time, peak
      RSS, bounds, evidence path and sha256. Its last line reads "pass", "pass with lever 2" or
      "fail after both levers".

## Notes

- **Not in this ticket:** 05 — Spike (a): SAW on clang 22 bitcode (picks the verifier); 09 — Spike
  verdict (the stop rule); 27 — Proof semantics for the BFS read-offload calls and 30 — Reference
  definitions, per-call summaries and new intrinsic versions (the real summaries); 31 — Five-gate
  drafting and the new bfs_read_offload version (formal halves L1-L4); 32 — BFS contract proof;
  33 — Minimum-bounds script and A2 exit (confirms the hand minimum by script; 2 lanes with generated
  summaries); 29 — Proof-semantics checks (the real semantics negative controls, per proof-semantics
  version); 46 — CIVL adapter, 47 — GenMC adapter and agreement and 48 — Concurrency negative
  controls (multi-thread controls such as `shared_context`).
- **Throwaway.** Nothing here becomes A2 code. A2's exit must reproduce these verdicts with
  generated summaries (33).
- Assumption (not decided in the map): "proven" here means the BFS unit postcondition (map 08's P2)
  plus hazard freedom (P1). Formal halves (A) do not exist until 31.
- Assumption (not decided in the map): `TDStepMAA`'s single-thread controls are the semantics
  negative controls that name it (its wait deleted; the authors' wait under the old wait rule; a
  same-thread read of `parent` while its DX100 store is unfinished; map 12 item 9), plus map 08's two
  wrong-tile bugs (a wait on a tile the store does not name; a wait on the compare's tile). The
  contract's seven controls are mutations of Peter's code, the contract's reference instance.
- Assumption (not decided in the map): `TDStepMAA` runs at the same bounds as Peter's code. Map 19
  derived the minimum for the read offload only.
- Reading of lever 2 (map 19 item 8, budget per bounded job): each shape job must finish in under 15
  minutes, and jobs run one at a time on the Mac. The total wall time is recorded too; 09 shows both.
- Assumption (not decided in the map): verdicts go in this ticket's Answer, not as `proof` records.
  Spike code lives in this effort's `prototype/` folder; logs go to the Mac runs folder outside the
  repo, host `mac` (map 26 item 5), the one 05 records.
- **Risks:**
  - Map 08: crux-llvm on the port proved 1 lane, but no safe 2-lane run finished in 600-900 s. Up to
    six crux jobs at once exhausted the Mac's 36 GB and forced a restart.
  - The 1-lane fallback is withdrawn (map 19 item 1; map
    [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) Later changes):
    one lane cannot see `skipped_cas_recheck`. If both levers fail, candidate artifacts stay certified and
    Yan-Ru re-plans (design risk table).
  - If 05 chose crux-llvm: each loop's unwind limit is computed from the sizes, with unwinding
    assertions on (map 19 item 5).
  - Either verifier: SAW bundles no libc++ bitcode (map 11 research) and crux-llvm cannot run libc++
    22 code (map 07, 08), so throwaway overrides or stubs stand in for any standard-library member
    the unit calls (map 16 item 7 plans the real models; 25 — std::vector and std::pair models
    builds them).
- **Held-out code:** `TDStepMAA` is BFS calibration code. No held-out authors' function
  (`PBFSMAA`, `PageRankPullMAA`, `DeltaStepMAA`, and `BrandesMaa`, BC's DX100 driver, by design
  spec O2's default) is read.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog; a watchdog kill is
  "out of memory", never a pass. Keep at least 50 GB free. The full set (2 proofs plus about 12
  controls, one at a time) can pass 30 minutes, so schedule the 30-minute heartbeat first (LR-07).

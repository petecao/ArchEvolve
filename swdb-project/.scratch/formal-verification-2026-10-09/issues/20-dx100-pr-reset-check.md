# 20 — Does the authors' DX100 PageRank keep stale `incoming_totals` across iterations?

Created: 2026-10-13 17:02 ET
**Type:** task
**Status:** resolved
**Assignee:** Yan-Ru Jhou (agent session, claimed 2026-10-13 19:52 ET)
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

Is 17's side finding real? Read from code, not run: the authors' `PageRankPullMAA` zeroes
`incoming_totals` once (`apps/dx100/benchmarks/gapbs/src/pr.cc:140-141`), before the iteration
loop (`:183`). Every iteration then adds into it through `maa_indirect_rmw_vector(..., ADD_OP)`
(`:242`) and reads it into the new scores (`:249`), with no reset. The baseline starts each vertex
at `incoming_total = 0` in every iteration (`:100`). If real, scores are wrong from iteration 2.

Do (AFK, on the Mac):

1. Build the authors' PR against the functional model (`apps/dx100/benchmarks/API/MAA_functional.hpp`,
   see `make_functional.sh`) and the baseline PR. One thread first, then a few.
2. Run both on a small generated graph for 1, 2 and the default number of iterations. Compare the
   scores and GAPBS's own verifier result.
3. Read which iteration count and tolerance the authors' run scripts use, and whether upstream DX100
   (`arkhadem/DX100`) has the same code.
4. Read (do not run) whether SWDB certification of this code would catch it: which iteration count
   and which tolerance it uses.

Record the facts, the smallest input that shows a difference, and whether it meets 13 item 10's
"bug" bar (a whole-kernel reproduction: a real input on which the kernel fails its correctness
check). The functional model is a testing aid (12 item 1) and gem5 stays out of scope (01 decision
10); the answer says so. Internal finding only: no message to the authors or the team.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Where real DX100 bugs may hide" fog. Lines
  re-checked in code this session. Feeds ticket 18 (bugs as motivating evidence; PR as a possible
  subject).
- 2026-10-13 19:52 ET: claimed (ticket 19 held by another session).

## Answer

Resolved 2026-10-13 19:56 ET, AFK on the Mac. Evidence, commands and the full run table:
[`../evidence/pr-incoming-totals-20261013.md`](../evidence/pr-incoming-totals-20261013.md).

1. **The defect is real.** `PageRankPullMAA` zeroes `incoming_totals` once (`pr.cc:140-141`) and
   never again. From iteration 2, each vertex's sum carries every earlier iteration's sum, so
   scores grow without bound. On a GAPBS Kronecker graph (`-g 10`, 1024 vertices, 20 iterations,
   tolerance 1e-4) the baseline passes `PRVerifier` (error 0.00001) and the DX100 code fails it
   (error 15679; top score 2341 instead of 0.020). Same result at 1 and 4 threads and at
   `TILE_SIZE` 4, 16 and 16384.
2. **Smallest input:** two vertices, one edge `0 -> 1`, two iterations. Baseline scores 0.075 and
   0.13875 pass the verifier; the DX100 code gives 0.075 and 0.56375 and fails (error 0.425).
3. **The missing reset is the whole difference.** One `memset` at the top of each iteration
   (after `pr.cc:184`, scratch copy only) makes the DX100 output match the baseline exactly at 2 and
   20 iterations, 1 and 4 threads.
4. **At 1 iteration the output is correct** (bit-identical top scores and error). That is the
   authors' setting: `pr.cc:304` sets the default `max_iters` to 1 (upstream GAPBS uses 20), and
   neither `run_pr.sh` nor `scripts/sim.py` passes `-i`. Their published PR runs compute correct
   scores; the defect is latent. GAPBS's `PRVerifier` (`pr.cc:285-301`) is a convergence test,
   not a comparison with a reference: it runs one more PageRank step and passes if the scores move
   by less than 1e-4 in total. After 1 iteration the scores have not converged, so it reports FAIL
   for the correct baseline too (`-g 6`: 0.19991; `-g 10`: 0.28401). `run_pr.sh` passes `-v`, so at
   the authors' setting a FAIL is expected and cannot tell correct code from wrong code (inferred:
   their graphs were not run here). Inputs already at the fixed point also hide the defect, because
   the loop exits when the first iteration's error is below tolerance (`pr.cc:260`).
5. **Upstream has the same code.** The snapshot is `arkhadem/DX100` `e4fc4afd`, which is upstream
   HEAD today, and `pr.cc` matches `SHA256SUMS`.
6. **SWDB certification would not catch it today, because it has no PR check.** `swdb/kernels/`
   holds only `bfs.py` and `bc.py`; `library/dx100/certification/` has BFS and BC drivers only.
   The held-out PR check that ticket 18 needs catches it only if it (a) runs at least 2 iterations,
   (b) compares per-vertex scores with a reference recomputation (as BC does at float epsilon,
   `swdb/bc_native.py:114`) and does not rely on `PRVerifier` at 1 iteration, and (c) uses inputs
   that are not already at the fixed point.
7. **It meets 13 item 10's "bug" bar.** This is a whole-kernel reproduction: a real
   GAPBS-generated input on which the kernel fails GAPBS's own correctness check while the
   baseline passes. Scope limits: the run used the functional model, which is a testing aid
   (12 item 1). gem5 was not run (out of scope, 01 decision 10). The defect is in host code (no
   reset), so it does not depend on the model beyond `maa_indirect_rmw_vector(..., ADD_OP)`
   adding into memory. Internal finding only: no message to the authors or the team.

**Re-check (Yan-Ru asked "are you sure?"):** the claim holds only for runs of 2 or more
iterations. The authors' settings (1 iteration) produce correct scores. gem5's indirect RMW was
read, not run (upstream `e4fc4afd`, `src/mem/MAA/IndirectAccess.cc`). It copies the memory line
into `new_data` (`:901`), adds the tile value for `float` (`:975-980`, the same for every data
type), and writes the line back (`:1145-1158`). So gem5 also adds into memory, as the functional model does. The defect does
not depend on which model runs it.

**Inputs passed on:**
- **Ticket 18 (resolved):** confirmed. The authors' PR as written is a held-out candidate that
  must fail certification or be refuted, and it serves as motivating evidence. The one-line reset
  is the expected repair, which makes it a clean RQ4 subject (refute, then repair).
- **Ticket 19:** for PR, the iteration count is a bound dimension with a minimum of 2. Below that
  the defect cannot be seen. This is the same small-scope argument as `skipped_cas_recheck` at
  lanes >= 2. A bounded input must also avoid the fixed point, or the loop exits after the first
  iteration.
- **Ticket 23:** a PR check needs a per-vertex reference comparison at a fixed iteration count
  (item 6 above), not GAPBS's `PRVerifier` at the authors' default settings.


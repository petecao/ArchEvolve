# 20 — Does the authors' DX100 PageRank keep stale `incoming_totals` across iterations?

Created: 2026-10-13 17:02 ET
**Type:** task
**Status:** ready-for-agent
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

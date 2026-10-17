# Draft: correction on the DX100 authors' BFS wait

Created: 2026-10-09 14:40 ET
To: Peter, Josh, Eric (team chat). Not sent; Yan-Ru sends.

---

**Correction: the DX100 authors' BFS waits on the right tile after all.**

On 2026-10-07 (weekly deck, the "who does the writes" slide) I said the authors' `TDStepMAA`
"waits on the wrong tile." On gem5 that is wrong. Their code is correct.

**Why:** in the gem5 MAA device, a store frees its source, index and result tiles in one step,
after every old value is in the result tile. So `wait_ready(tile3)` (the store's source tile)
also covers `tile5`.

- The code: `swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc:179-193`, ArchEvolve
  `yanrujhou_main` @ `1dbbd9ea`:
  https://github.com/petecao/ArchEvolve/blob/1dbbd9ea3ea0529c99da5a6867fba4add001cfb6/swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc#L179-L193
- gem5 evidence (DX100 @ `e4fc4af`, read from source, not simulated):
  - Ready bit = count of unfinished commands naming the tile:
    https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L563-L580
    and `src/mem/MAA/SPD.cc#L120-L139`
  - A store releases all its tiles in one call:
    https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L605-L620
  - `wait_ready` blocks until that count is zero: `src/mem/MAA/CpuSidePort.cc#L295-L315`
  - The store finishes only after all old values are in: `src/mem/MAA/IndirectAccess.cc#L742-L789`

**Where my mistake came from:** our strict layer assumed "waiting on a store's source tile does
not cover the store." That rule was marked assumed (owner Eric) until gem5's ready-bit rule was
confirmed: `swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/spec.md:480-485` @ `1dbbd9ea`.

**What does not change:** the Sep 29 timings (authors about 6.5 ms, ours about 13 ms). The
one-line change waited on `tile5`, which becomes ready in the same step as `tile3`. I have not
re-measured.

**One ask:**
- **Eric and Josh:** does this match your reading of the device? If yes, I'll align the strict
  layer's wait rule with gem5.

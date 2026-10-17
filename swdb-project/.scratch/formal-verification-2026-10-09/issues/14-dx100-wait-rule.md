# 14 — Does a DX100 wait on a store's source tile cover the store's result?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

In DX100's gem5 device model, when does a store's source tile become ready, and when does its
result tile (the old values a store-with-result writes) become ready? Does `wait_ready` on the
source tile guarantee the store finished and its result tile is filled?

Why it matters: the "wrong-tile bug" in the authors' `TDStepMAA`
(`apps/dx100/benchmarks/gapbs/src/bfs.cc:180`, `wait_ready(tile3)` then reads `tile5`) is a bug
only under our strict layer's assumed wait rule
(`.scratch/typed-library-dx100-bfs-2026-10-03/spec.md:481-485`, "assumed, owner Eric"). The
authors' functional model sets the source tile ready only when the store completes, together
with the result tile (`apps/dx100/benchmarks/API/MAA_functional.hpp:570,614,686`). If gem5 does
the same, the authors' code is correct and our strict layer is too strict.

Also answer, if the source shows it: does DX100 execute one core's commands in order, and does
a wait cover earlier commands?

The gem5 device source is not vendored (`apps/dx100/PROVENANCE.md`). Upstream:
https://github.com/arkhadem/DX100 at `e4fc4afdf894f295442cef3604667a469fab8e62`.

## Answer

Answered 2026-10-09 14:33 ET. **Verdict: SAFE.** On gem5, `wait_ready(tile3)` at `bfs.cc:180`
returns only after the store at `bfs.cc:179` has finished, with tile5 and tile4 filled. Our
strict layer is **stricter** than gem5 on this rule, so the "wrong-tile bug" is a strict-layer
finding, not a gem5 bug. Source: DX100 `e4fc4af`, `src/mem/MAA/`.

- **The ready bit is a counter** of unfinished commands that name the tile as a source or
  destination (a condition tile is not counted). Each command marks its tiles not-ready at
  dispatch and ready at finish (`MAA.cc:563-580`, `605-620`; `SPD.cc:120-139`). `wait_ready`
  is a read whose reply the device holds until the count is zero (`CpuSidePort.cc:295-315`,
  `MAA.cc:652-678`).
- **A store releases its result, index and source tiles in one call.** It makes that call only
  after all old values are in the result tile and all its writes have been handed to the memory
  system; DRAM does not acknowledge them (`MAA.cc:607-620`; `IndirectAccess.cc:742-789`,
  `909-918`; `Port.cc:314-326`, `388-400`).
- **A store cannot finish until its condition tile is Finished**, so the ALU that writes tile4 is
  done too (`IndirectAccess.cc:402-410`, `441-459`).
- **Order:** the device accepts one core's commands one at a time, in program order
  (`CpuSidePort.cc:162-170`, `235-250`; `MAA.cc:581-583`), then runs them as data allows, in no
  fixed order (`IF.cc:250-299`). A wait covers an earlier command only if that command names the
  tile, or transitively produces a tile such a command reads. Exception: a range loop that fills
  its output tile does not wait for its input producers (`RangeFuser.cc:166-168`, `214-218`).
- **The strict layer is stricter** on waits and register writes, and **looser** in two corners:
  that range-loop exception, and memory effects, which it applies at the call.

Detail, quotes and the strict-layer comparison: [../research/14-dx100-wait-rule.md](../research/14-dx100-wait-rule.md).

# Research 14: Does a DX100 wait on a store's source tile cover the store's result?

Created: 2026-10-09 14:33 ET
**Ticket:** [14](../issues/14-dx100-wait-rule.md)
**Map:** [../map.md](../map.md)
**Method:** read the gem5 DX100 device source (`src/mem/MAA/`) at DX100
`e4fc4afdf894f295442cef3604667a469fab8e62`, fetched file by file. The fetched `IF.cc` and
`IndirectAccess.cc` match the SHA-256 values that
`records/evaluations/bfs-dx100-witness-20260926-a3.yaml:463-467` recorded from the checkout we
inspected locally, so this is the same revision. Local line numbers are at ArchEvolve `c9220665`.
No simulation was run. Every claim below comes from reading the source.

---

## Verdict: SAFE

The authors' `TDStepMAA` is correct on the gem5 model. `wait_ready(tile3)`
(`apps/dx100/benchmarks/gapbs/src/bfs.cc:180`) returns only after the store at `bfs.cc:179` has
finished. By then tile5 (the old values) and tile4 (the condition) are filled. **Our strict layer
is stricter than gem5 here.** The "wrong-tile bug" is a finding of the strict layer, not a bug on
gem5.

- **A tile's ready bit is a counter.** It counts unfinished commands that name the tile as a
  source or a destination. A tile used only as a condition is not counted. Each command marks its
  tiles not-ready when the device accepts it, and ready when it finishes
  (`MAA.cc:563-580`, `MAA.cc:605-620`, `SPD.cc:120-139`).
- **`wait_ready` is a blocking read.** The device holds back its reply until that counter is zero
  (`CpuSidePort.cc:295-315`, `MAA.cc:652-678`).
- **A store releases all its tiles in one call.** That call first marks the result tile finished
  and ready, then the index and source tiles ready (`MAA.cc:607-620`). The call runs only after
  every old value is in the result tile and every memory write has left the device
  (`IndirectAccess.cc:742-789`, `909-918`; `Port.cc:314-326`, `388-400`).
- **A store cannot finish before its condition tile is finished**
  (`IndirectAccess.cc:402-410`, `441-459`). So the ALU that writes tile4 is done too.
- **Order:** the device accepts one core's commands one at a time, in program order. After that
  they run as their data becomes available, not in program order. A wait covers an earlier
  command only if that command names the tile, or (transitively) produces a tile that such a
  command reads.

---

## 1. When each ready bit is set

The ready counter is a `uint8_t` per tile. It starts at 0. Dispatch decrements it, finish
increments it, and the tile is ready when the counter is 0 (`SPD.cc:120-139`, `SPD.cc:217-224`).
"Dispatch" means the device accepts the command into its instruction file. So a tile is ready
exactly when no accepted, unfinished command names it in a counted role.

Counted roles are only `dst1`, `dst2`, `src1` and `src2` (`MAA.cc:563-580` at dispatch,
`MAA.cc:607-620` at finish). The condition tile (`condSpdID`) appears in neither list.

| Tile | Not ready from | Ready again at | Source |
|---|---|---|---|
| Store's source tile (indirect store or RMW: `src2`; stream store: `src1`) | dispatch | the store's finish, in the same call as the result tile | `MAA.cc:575-580`, `615-620` |
| Store-with-result destination (old values, `dst1`) | dispatch (status also set to Idle) | the store's finish (status set to Finished first) | `MAA.cc:563-568`, `607-610` |
| Index tile of an indirect load or store (`src1`) | dispatch | finish | `MAA.cc:575-577`, `615-617` |
| Load destination (`dst1`) | dispatch | finish | `MAA.cc:563-568`, `607-610` |
| ALU destination (`dst1`); ALU sources `src1`, `src2` | dispatch | finish | same lines |
| Range loop outputs (`dst1`, `dst2`) and inputs (`src1` min, `src2` max) | dispatch | finish | same lines |
| Any condition tile | never marked | never marked | absent from `MAA.cc:563-580` and `607-620` |

How the API's operands map to these roles: `maa_indirect_store_vector` writes `tsrc1` = index,
`tsrc2` = source, `tdst1` = result, `cond` = condition (`MAA_gem5.hpp:289-305`), and the device
decodes the same fields (`CpuSidePort.cc:187-233`). The indirect unit then reads `src1` as index,
`src2` as source, and `dst1` as destination (`IndirectAccess.cc:544-549`).

## 2. What `wait_ready` does on gem5

- **The API side** is a single uncacheable 16-bit load from the tile's ready address, then
  `mfence` (`MAA_gem5.hpp:98-101`). There is no polling loop.
- **The device side:** if the counter is 0, the device replies after one cycle. If not, it parks
  the read packet. `MAA::setTileReady` replies to the parked packets when the counter returns to
  0 (`CpuSidePort.cc:295-315`, `MAA.cc:652-678`).
- **Earlier commands are always counted before the wait arrives:**
  - The device does not acknowledge a command's last word until it accepts the command
    (`CpuSidePort.cc:235-250` sets `respond_immediately = false`; the reply is sent at dispatch,
    `MAA.cc:581-583`).
  - Every `maa_*` call ends with `mfence` (e.g. `MAA_gem5.hpp:191`, `305`).
  - The device panics if a core sends a new command while its previous one has not been accepted
    (`CpuSidePort.cc:162-170`).

  So when the ready read arrives, every earlier command from that core has already decremented
  its counters.

## 3. Does a wait on a store's source tile mean the store finished and its result tile is filled?

Yes, on both counts.

- **The source tile stays not-ready until the store finishes.** The store decrements it at
  dispatch (`MAA.cc:578-580`). It increments it only in `finishInstructionCompute`
  (`MAA.cc:618-620`), and that same call first sets the result tile Finished and ready
  (`MAA.cc:607-610`).
- **The indirect unit finishes only when all its work is done.** It calls
  `finishInstructionCompute` only from its Response state (`IndirectAccess.cc:766-789`). It
  enters Response only when all packets are sent, all expected responses have arrived, and the
  fill is done (`IndirectAccess.cc:742-752`).
- **The result tile is filled before that point.** For each element whose condition is true, the
  old value from the read response is written into the result tile, and only then is the new
  value merged into the line (`IndirectAccess.cc:905-918`, `924-933`). An element whose
  condition is false is only marked finished. Its slot is not written (`IndirectAccess.cc:523-526`).
  The authors' functional model does the same (`MAA_functional.hpp:605-612`).
- **"Finished writing memory" means the writes were handed to the memory system.** Each changed
  line is sent as a `WritebackDirty` (`IndirectAccess.cc:1145-1158`). It counts as done when the
  cache or memory port accepts it (`Port.cc:314-326`, `388-400`; `IndirectAccess.cc:843-866`).
  No acknowledgment from DRAM is awaited (`needsResponse` is false, `Port.cc:320`, `394`).
- **Stream stores behave the same way.** They finish only after all write packets are sent and
  their source and condition tiles are Finished (`StreamAccess.cc:305-342`, `369-377`).

## 4. Order of one core's commands, and what a wait covers

- **Dispatch is in program order, one command at a time** (section 2).
- **Dispatch stalls on hazards.** A new command is refused while:
  - its destination tile is any unfinished command's source, destination or condition tile
    (`IF.cc:193-212`). This blocks write-after-read and write-after-write on tiles.
  - it touches the same registered memory region as an unfinished command and either one writes
    (`IF.cc:213-219`).

  A CPU write to a register is also held until no unfinished command names that register
  (`IF.cc:233-249`, `MAA.cc:510-538`, `CpuSidePort.cc:145-149`).
- **Execution is not in order.** `IF::getReady` scans the instruction slots from a random start.
  It issues any command whose input tiles are being produced or are finished (`IF.cc:250-299`).
  The instruction file holds 8 commands per core by default (`MAA.py:16`). A reader can consume
  a tile element by element while its producer is still writing it (`SPD.cc:140-157`).
- **Coverage is transitive, with one exception.** ALU, stream and indirect commands finish only
  after all their input tiles (source, index, condition) have status Finished
  (`ALU.cc:199-246`; `StreamAccess.cc:305-316`; `IndirectAccess.cc:399-459`). A tile's status
  becomes Idle when its producer is dispatched and Finished when that producer finishes
  (`MAA.cc:566`, `608`). So when a consumer finishes, its producers have finished.
  **Exception:** a range loop that fills its output tile finishes without waiting for the
  producers of its min, max or condition tiles (`RangeFuser.cc:166-168`, `214-218`).
- **So a wait on tile t covers:**
  1. every unfinished command that names t as a source or destination;
  2. transitively, the producers of those commands' inputs, but not through a range loop that
     filled its tile.

  It does not cover unrelated earlier commands. It also does not cover a command that names t
  only as a condition.

## 5. Applied to `TDStepMAA`

The critical section at `bfs.cc:170-181`, with the roles gem5 assigns:

| Line | Command | src1 | src2 | cond | dst1 |
|---|---|---|---|---|---|
| 173 | `tile7 = parent[tile0]` | tile0 | | | tile7 |
| 175 | `tile4 = tile7 < 0` | tile7 | | | tile4 |
| 179 | `if tile4: tile5 = parent[tile0]; parent[tile0] = tile3` | tile0 | tile3 | tile4 | tile5 |
| 180 | `wait_ready(tile3)` | | | | |

The chain of reasoning:

1. `wait_ready(tile3)` blocks until the store (line 179, `src2` = tile3) has finished. It also
   waits for tile3's producer (line 163, `dst1` = tile3).
2. The store has finished, so tile5 is filled and Finished (section 3).
3. The store finished, so tile4 had status Finished, so the ALU on line 175 finished. That in turn
   means the load on line 173, which produces the ALU's input tile7, finished.
4. tile0, which the push loop reads (`bfs.cc:190-191`), comes from the load on line 161. That load
   names tile7 as `src1`, so `wait_ready(tile7)` on line 165 already covered it. The store also
   needed tile0 Finished before it could finish.
5. **No stale CPU cache lines.** A CPU read of a tile marks the tile dirty
   (`CpuSidePort.cc:348-358`). A later command that writes that tile must first wait for the CPU
   copies to be invalidated (`MAA.cc:479-492`, `IF.cc:252-276`). So in later iterations the push
   loop never reads stale tile0, tile4 or tile5 lines.

Result: **SAFE.**

**The authors use this idiom elsewhere too.** `pr.cc:242-245` waits on tile5, the RMW's source
tile, and then the CPU reads `incoming_total`, the memory that RMW wrote.

**Outside this ticket:** `wait_ready`'s `asm volatile("mfence;")` has no `"memory"` clobber
(`MAA_gem5.hpp:100`), so on its own it does not stop the compiler from reordering memory
accesses. Whether the compiler can hoist the tile reads is a C-level question. This ticket did
not check it.

## 6. Our strict layer compared with gem5

Strict layer rule: `.scratch/typed-library-dx100-bfs-2026-10-03/spec.md:476-485`. Code:
`library/dx100/strict/MAA_functional.hpp:67-80` (`issue`, `cover`) and `:117`
(`wait_ready` covers only `tile(id).writer`).

| Aspect | Strict layer | gem5 | Which is stricter |
|---|---|---|---|
| What a wait on t covers directly | the last writer of t | every unfinished command naming t as a source or destination | **strict layer is stricter** |
| Wait on a store's source tile | does not cover the store (`spec.md:480-482`) | covers the store and its result tile | **strict layer is stricter** (the `TDStepMAA` finding) |
| Transitive coverage | all dependencies of the covered command | the same, except through a range loop that filled its tile | strict layer is looser in this corner |
| CPU constant written to a register an unfinished command reads | flagged as a hazard (`spec.md:483`) | the device holds the write until the register is free | strict layer is stricter |
| When a DX100 load or store touches memory | at the call; the CPU sees it at once (`MAA_functional.hpp:170`) | later; only a wait orders it with CPU accesses | strict layer is looser (it does not model memory timing) |
| Program order of dispatch | yes | yes | same |

**Overall:** on the wait rule this ticket asks about, the strict layer is **stricter** than gem5.
It is looser in two corners the ticket did not ask about: range-loop early finish, and memory
timing.

## 7. What this changes for the proof of concept

- **Reclassify the `TDStepMAA` "wrong-tile bug".** The code is correct on gem5, and on the
  functional model, whose ready bits are never cleared, so a wait there never blocks
  (`MAA_functional.hpp:33-36`, `83-85`). It breaks only our stricter rule. Do not present it as a
  bug in the authors' code.
- **Choose one of two options:**
  - (a) **Align the strict rule with gem5.** A wait on t covers every uncovered command that names
    t as an index, source or destination (not as a condition), plus their dependencies, but
    without following a range loop's inputs. The authors' code then passes.
  - (b) **Keep the stricter rule as a deliberate portability discipline.** Report violations as
    "stricter than gem5", not as bugs.

  Either way, the wait entry's "assumed, owner Eric" field can now cite this source instead of an
  assumption.
- **If the PoC claims the strict layer over-approximates gem5,** it must close the two looser
  corners from section 6 first.

---

## Sources

DX100 at `e4fc4afdf894f295442cef3604667a469fab8e62`, directory `src/mem/MAA/`
(base URL `https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/`):

| File | Read scope | Used for |
|---|---|---|
| [SPD.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/SPD.cc) | whole file (268 lines) | ready counter, tile status, element wake-up |
| [SPD.hh](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/SPD.hh) | L20-149 | `setData` marks element finished; `setFakeData` |
| [IF.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc) | whole file (469 lines) | dispatch hazards, random issue, status propagation |
| [MAA.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L466-L720) | L466-720 | dispatch, finish, ready reply |
| [CpuSidePort.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L100-L451) | L100-451 | MMIO decode, delayed acknowledgment, ready read, CPU tile reads |
| [IndirectAccess.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L340-L1210) | L340-1210 | store state machine, result fill, write packets |
| [Port.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc) | L25-80, L290-410 | when a write counts as sent |
| [ALU.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/ALU.cc) | L190-262, L820-870 | ALU finish gating |
| [StreamAccess.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/StreamAccess.cc) | L296-377 | stream finish gating |
| [RangeFuser.cc](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/RangeFuser.cc) | L116-240 | range-loop early finish |
| [MAA.py](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.py) | grep for parameters | 8 instructions per core, 1 MAA by default |

Local files (ArchEvolve `c9220665`, `swdb-project/`):

- `apps/dx100/benchmarks/API/MAA_gem5.hpp:98-101`, `147-149`, `174-305`
- `apps/dx100/benchmarks/API/MAA_functional.hpp:27-36`, `77-85`, `530-776`
- `apps/dx100/benchmarks/gapbs/src/bfs.cc:60-98`, `140-195`; `pr.cc:225-250`
- `library/dx100/strict/MAA_functional.hpp:41-174`
- `.scratch/typed-library-dx100-bfs-2026-10-03/spec.md:462-486`
- `records/evaluations/bfs-dx100-witness-20260926-a3.yaml:460-467` (hash match)

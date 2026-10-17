Created: 2026-10-13 13:50 ET

# Research 12: Is a finished DX100 store visible to other cores?

## Verdict

- **Q2: No.** A DX100 write (`WritebackDirty`) never invalidates or updates a CPU cache. No crossbar snoops it.
- Protection comes earlier, per line. If any cache holds the line, the store first reads it with `ReadExReq` through the coherent L2–L3 crossbar. That read invalidates all L1/L2 copies. The write then lands in the shared L3. If no cache holds the line, the read and the write go straight to DRAM, with no snoop.
- Beyond that, the authors rely on a software rule: no core *stores* to an array while DX100 works on it (paper §3.6, §4.2 "Legality"). The API has no cache flushes.
- **Q4(a): Yes**, on the gem5 model, except in two narrow races (table in Q4(a)). A finished store's data is already in L3 or in DRAM's backing store, and the later load reads it there. With one DX100 instance (the paper's main runs), a load of the same array cannot even dispatch until the store finishes, from any core.
- **Q4(b): Yes, if no core fetched the line while the store ran.** A copy fetched in that window (by a load or a prefetch) stays stale. Nothing in the device, the API, or the paper's rule prevents that: the rule forbids core stores, not core loads.

**Ticket:** [12](../issues/12-dx100-proof-semantics.md) (the cross-core visibility assumption from 11)
**Builds on:** [Research 14](14-dx100-wait-rule.md) (a wait on a store's source tile returns only after the store finished)
**Map:** [../map.md](../map.md)

**Method.** I read the DX100 gem5 fork at `e4fc4afdf894f295442cef3604667a469fab8e62`: a sparse, blobless, shallow clone of `src/mem/MAA`, `configs/`, `scripts/`, `src/mem/*`, `src/mem/cache/`, and `src/cpu/`. I fetched three Ramulator2 files and `src/sim/pseudo_inst.cc` one by one. The paper is arXiv 2505.23073v2 (HTML). The local `apps/dx100/benchmarks/gapbs/src/bfs.cc`, `API/MAA_gem5.hpp`, and `API/MAA.hpp` are byte-identical to the upstream files at that commit (`diff -q`), so local line numbers are upstream line numbers. No simulation was run. Every claim comes from reading source or the paper.

Terms used below:

- **Cache path:** DX100 sends the packet to the L2–L3 crossbar (`tol3bus`), which is coherent.
- **Memory path:** DX100 sends the packet to the non-coherent bus in front of the memory controllers (`membusnc`).
- **Per-line check:** before queuing a packet, DX100 asks the system crossbar whether any cache holds the line. The answer picks the path.

---

## Q1. Where the device sits

**The paper's runs.** The artifact runs `scripts/benchmark.py`, which calls `sim.py`'s `run_simulation` ([README.md:137](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/README.md#L137), [benchmark.py:2](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/benchmark.py#L2), [benchmark.py:31](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/benchmark.py#L31)). Each DX100 run uses `se.py` with `X86O3CPU`, 4 cores, three cache levels, `--maa`, one DX100 instance, and `--maa_l2_uncacheable --maa_l3_uncacheable` ([sim.py:89](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L89), [sim.py:156-157](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L156-L157), [sim.py:194-247](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L194-L247)). The GAP loop passes neither a core count nor an instance count, so the defaults hold ([sim.py:373-389](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L373-L389)). Only the scalability runs differ: 8 cores with 1 or 2 instances ([sim.py:21-22](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L21-L22)).

**The hierarchy.**

| Level | What it is | Source |
|---|---|---|
| L1I, L1D, L2 | private per core | [CacheConfig.py:161-164](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L161-L164), [CacheConfig.py:254-256](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L254-L256) |
| `tol3bus` | L2-to-L3 crossbar; coherent (`L3XBar`), has a snoop filter | [CacheConfig.py:155-158](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L155-L158), [CacheConfig.py:259-263](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L259-L263), [XBar.py:181-188](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/XBar.py#L181-L188) |
| L3 | the shared LLC | [CacheConfig.py:146-159](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L146-L159) |
| `membus` | below the L3; coherent (`SystemXBar`), has a snoop filter, point of coherency | [se.py:287](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/deprecated/example/se.py#L287), [CacheConfig.py:159](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L159), [XBar.py:196-208](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/XBar.py#L196-L208) |
| `membusnc` | below `membus`; non-coherent (`SystemXBarNC`) | [se.py:289-298](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/deprecated/example/se.py#L289-L298), [XBar.py:225](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/XBar.py#L225) |
| memory controllers | Ramulator2, attached to `membusnc` | [MemConfig.py:165-168](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MemConfig.py#L165-L168), [MemConfig.py:305-307](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MemConfig.py#L305-L307) |

**DX100's three port groups.**

- **`cpu_sides`** (one per core) hang off `membus`'s memory side ([MAAConfig.py:168-169](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAAConfig.py#L168-L169)). Core commands reach DX100 through the core's caches and the L3, like device registers below the LLC. All instruction, register, size, and ready addresses are served by port 0 ([MAA.cc:157-160](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L157-L160); [CpuSidePort.cc:153](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L153), [CpuSidePort.cc:279](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L279), [CpuSidePort.cc:296](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L296)).
- **`cache_sides`** (one per core) plug into `tol3bus` as requesters, next to the L2s ([MAAConfig.py:171-172](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAAConfig.py#L171-L172)). Traffic there reaches the shared L3. These ports never take snoops: `isSnooping()` is false ([MAA.hh:150](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.hh#L150)) and a snoop request asserts ([CacheSidePort.cc:49-54](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CacheSidePort.cc#L49-L54)).
- **`mem_sides`** (one per channel) plug into `membusnc` ([MAAConfig.py:174-175](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAAConfig.py#L174-L175)). This path skips the L3 and the coherent `membus`. It does not snoop either ([MAA.hh:126](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.hh#L126)).
- DX100 has no direct link to any L1 or L2.

**One device for all cores.** The config creates one `SharedMAA` object ([MAAConfig.py:138](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAAConfig.py#L138)). Inside it are `num_maas` sets of units; the default is 1 ([MAA/MAA.py:38](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.py#L38), [configs/common/MAA.py:29](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAA.py#L29), [Options.py:241](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/Options.py#L241)).

**Cacheability.** DX100's own address ranges are excluded from L2 and L3 ([MAAConfig.py:177-185](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/MAAConfig.py#L177-L185), flags at [sim.py:241-242](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L241-L242)). The page table maps the scratchpad-data range cacheable and the other DX100 ranges uncacheable ([Simulation.py:739-749](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/Simulation.py#L739-L749)). Application arrays such as `parent` are ordinary cacheable memory. Nothing in the config treats them specially.

## Q2. Do DX100 writes keep CPU caches coherent?

**The write itself does not. The store's read and the per-line check do part of the job. A software rule does the rest.**

Step by step, for each line an indirect store touches:

1. **Per-line check.** Unless "force cache" is on, DX100 sends an express `SnoopReq` toward `membus` ([Port.cc:102-113](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L102-L113), [CpuSidePort.cc:435-439](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L435-L439)). `SnoopReq` is a command the authors added ([packet.cc:269-270](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/packet.cc#L269-L270)). `membus` does not forward it. It only marks the packet "cached" if its snoop filter lists any holder ([coherent_xbar.cc:533-540](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/coherent_xbar.cc#L533-L540)). That filter sees the L3 port, which stands for the L3 and every cache above it. "Cached" picks the cache path; otherwise the memory path ([Port.cc:116-174](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L116-L174)).
   - The check runs when the packet is **queued**, not when it is sent. Queued packets wait for a computed tick ([Port.cc:308-312](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L308-L312), [Port.cc:382-386](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L382-L386)).
   - The store's read and its write are separate packets, each checked on its own. The read's entry is erased when its response arrives ([Port.cc:571](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L571)). The write is a new `sendPacket` call ([IndirectAccess.cc:1158](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L1158)).
   - "Force cache" skips the check. The global switch is off in the paper's runs ([MAA/MAA.py:24](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.py#L24), [sim.py:160](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L160), [sim.py:246-247](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L246-L247)). A per-command switch is set when unique word addresses outnumber words-per-line times unique lines ([IndirectAccess.cc:685-693](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L685-L693)). Both sets are filled together ([IndirectAccess.cc:514-515](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L514-L515)), so by counting this cannot happen. In effect, every indirect packet is checked.
2. **The store's read.** Indirect stores and read-modify-writes read each line with `ReadExReq` ([IndirectAccess.cc:828-832](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L828-L832)). `ReadExReq` carries "invalidate" and "needs writable" ([packet.cc:146-152](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/packet.cc#L146-L152)).
   - **Cache path:** `tol3bus` snoops the L2s its filter lists ([coherent_xbar.cc:213-234](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/coherent_xbar.cc#L213-L234), [snoop_filter.cc:110-113](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/snoop_filter.cc#L110-L113)). Each L2 passes the snoop up to its L1 ([cache.cc:1051-1065](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1051-L1065)). A dirty holder supplies the data ([cache.cc:1155](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1155), [cache.cc:1190-1219](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1190-L1219)). Every holder invalidates its copy ([cache.cc:1039](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1039), [cache.cc:1242-1243](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1242-L1243)). After this read, no L1 or L2 holds the line.
   - **Memory path:** the read goes through `membusnc` to the controller, with no snoop ([MemSidePort.cc:85-88](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MemSidePort.cc#L85-L88)). This is correct only because the check found no cached copy.
3. **The store's write.** One full 64-byte `WritebackDirty` per changed line. It is built from the line DX100 read, with the new values merged in ([IndirectAccess.cc:1145-1158](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L1145-L1158); Research 14 §3).
   - **Cache path:** `WritebackDirty` is an eviction-type command ([packet.cc:91-93](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/packet.cc#L91-L93)). `tol3bus` does not snoop evictions. It only sets a flag from its filter ([coherent_xbar.cc:224-231](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/coherent_xbar.cc#L224-L231)). The L3 writes the data into its block, allocating one if needed, and marks it dirty ([base.cc:1395-1456](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/base.cc#L1395-L1456)). L1 and L2 copies are neither updated nor invalidated.
   - **Memory path:** `membusnc` is non-coherent ([XBar.py:225](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/XBar.py#L225)). The write goes to Ramulator2. Nothing is snooped.
4. **DX100 is never tracked as a holder.** Its cache-side port does not snoop, so the `tol3bus` filter does not record lines DX100 reads ([snoop_filter.cc:70](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/snoop_filter.cc#L70), [snoop_filter.cc:82-83](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/snoop_filter.cc#L82-L83), [snoop_filter.cc:110-113](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/snoop_filter.cc#L110-L113)). Between the store's read and its write, a core can fetch the line again and get the old value. The later write does not touch that copy. No code in the device blocks such a fetch. The paper's rule forbids core stores, not core loads, so it does not cover this case either.

**The one invalidation tool DX100 has is not used for arrays.** The Invalidator sends express `ReadExReq` snoops through `membus` ([Invalidator.cc:385-413](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Invalidator.cc#L385-L413), [CpuSidePort.cc:411-433](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L411-L433)). Its addresses start at the first DX100 range, the scratchpad data ([MAA.cc:99-100](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L99-L100), [Invalidator.cc:350](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Invalidator.cc#L350)). It only clears CPU copies of tile lines.

**How the authors keep CPU and DX100 views coherent:**

- **Per-line routing,** as above. The paper calls this snooping "the coherency directories during the fill stage" into an H bit (§3.6). gem5 does it with the `membus` snoop filter, when each packet is queued.
- **A software rule.** §4.2 "Legality": no core stores to the memory DX100 accesses within the loop body. §3.6: "no cores can modify the cache lines between snooping and issuing the request."
- **Waits.** §4.2: the compiler inserts a wait before a core accesses memory changed by DX100 stores or RMWs.
- **Not used:** no uncacheable mapping for arrays (Q1), and no flush. The API's only fence is `mfence`; it has no `clflush` (`apps/dx100/benchmarks/API/MAA_gem5.hpp`, searched).

## Q3. Does a DX100 load see a CPU's dirty data?

- **Cache path: yes.** A DX100 load reads with `ReadReq` ([IndirectAccess.cc:828-829](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L828-L829)). On `tol3bus` it is snooped to the listed L2s and their L1s. A dirty holder answers with its data ([cache.cc:1155](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1155), [cache.cc:1190-1219](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1190-L1219)). A `ReadReq` does not invalidate; the holder keeps a shared copy ([cache.cc:1174-1177](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L1174-L1177)). Stream loads also use `ReadReq` ([StreamAccess.cc:356-360](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/StreamAccess.cc#L356-L360)) and always go out the cache port, whatever the check says ([Port.cc:143-166](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L143-L166), [Port.cc:439-553](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L439-L553)).
- **Memory path:** taken only when the `membus` filter lists no holder at or above the L3. The filter drops the L3 port only when an eviction from the L3 says no cache above still holds the line ([snoop_filter.cc:137-150](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/snoop_filter.cc#L137-L150); the L3 sets that flag in [cache.cc:205-216](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/cache.cc#L205-L216)). So a line dirty in some L1 or L2 makes the load take the cache path.
- **Window:** the check runs when the packet is queued. A core that fetches and writes the line after the check, but before the DRAM read, is not seen. The legality rule excludes this.
- **Not checked:** whether a core's earlier plain store has left its store queue before its command reaches DX100. The API puts `mfence` after each command (`apps/dx100/benchmarks/API/MAA_gem5.hpp:191`), not before.

## Q4. Visibility after a finished store

"Finished" means every write packet was accepted by the next hop (Research 14 §3; [Port.cc:314-327](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L314-L327), [Port.cc:388-401](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L388-L401)).

**No write is held back after acceptance.**

- **Device:** unsent packets wait in an outstanding map and per-path lists. A later read or write by the same unit to a line with an unsent write is served from it or merged into it ([Port.cc:34-66](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L34-L66)). A different unit hitting that line panics ([Port.cc:36-37](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L36-L37), [Port.cc:53-54](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L53-L54)). Once a write is sent, its entry is erased ([Port.cc:322](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L322), [Port.cc:396](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/Port.cc#L396)). A store finishes only after all its writes are sent ([IndirectAccess.cc:843-866](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IndirectAccess.cc#L843-L866)). So a finished store leaves nothing in the device.
- **Ports:** sends call `sendTimingReq` directly ([CacheSidePort.cc:104](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CacheSidePort.cc#L104), [MemSidePort.cc:87](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MemSidePort.cc#L87)). The ports' deferred queue is unused; its send function asserts ([MemSidePort.cc:94-98](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MemSidePort.cc#L94-L98)).
- **Crossbars:** both forward a request in the same call ([coherent_xbar.cc:284](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/coherent_xbar.cc#L284), [noncoherent_xbar.cc:147](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/noncoherent_xbar.cc#L147)).
- **L3:** performs the access when it receives the packet ([base.cc:458-485](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/base.cc#L458-L485)).
- **Ramulator2:** the wrapper writes the backing store when it accepts a write ([ramulator2.cc:197-223](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/ramulator2.cc#L197-L223)). A read takes its data when it completes ([ramulator2.cc:170-196](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/ramulator2.cc#L170-L196)). The controller in use is `Generic` ([example_gem5_config.yaml:17-21](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/ext/ramulator2/ramulator2/example_gem5_config.yaml#L17-L21), [generic_dram_controller.cpp:12](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/ext/ramulator2/ramulator2/src/dram_controller/impl/generic_dram_controller.cpp#L12)). It never calls back for a write, so there is no second, late write ([generic_dram_controller.cpp:180-187](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/ext/ramulator2/ramulator2/src/dram_controller/impl/generic_dram_controller.cpp#L180-L187), [generic_dram_controller.cpp:239-255](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/ext/ramulator2/ramulator2/src/dram_controller/impl/generic_dram_controller.cpp#L239-L255)). It forwards a read that matches a queued write ([generic_dram_controller.cpp:98-109](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/ext/ramulator2/ramulator2/src/dram_controller/impl/generic_dram_controller.cpp#L98-L109)).
- **One path not traced:** if the L3 cannot allocate a block for the write, it passes the write down ([base.cc:1419-1426](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/base.cc#L1419-L1426)). A later read is then ordered by gem5's standard L3 write buffer. I did not check that code.

### Q4(a). A later DX100 load, sent by another core

- **Dispatch order.** With one instance, all cores share one instruction file (Q6). A read of an array waits while any write to that array is unfinished ([IF.cc:213-218](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L213-L218)). The instance has one indirect unit, which runs one command at a time ([MAA.cc:94-98](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L94-L98), [MAA.cc:410-423](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L410-L423)). So the load's packets are created after the store's writes were accepted.
- **Then it depends on the two paths:**

| Store went to | Load goes to | Load reads from | New value? |
|---|---|---|---|
| L3 (cache path) | cache path | L3, or a cache above it | yes |
| DRAM (memory path) | memory path | Ramulator2 backing store | yes |
| DRAM | cache path, because a core fetched the line meanwhile | that cache | yes if fetched after the write; no if fetched during the store |
| L3 | memory path | DRAM | no |

- **The last row** needs the `membus` filter to drop the line while the L3 holds the new data. That can happen only if the L3 and all caches above evicted the line between the write's check and its arrival. The write would then allocate a fresh L3 block ([base.cc:1419-1428](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/cache/base.cc#L1419-L1428)) without passing `membus`. I found no code that prevents this. I did not determine whether it occurs.
- **In `TDStepMAA`:** core B sends its `parent` load (`apps/dx100/benchmarks/gapbs/src/bfs.cc:173`) only after core A's `wait_ready(tile3)` returned (`bfs.cc:180`). Research 14 shows that means A's store finished.

### Q4(b). A later plain CPU load on another core

- **Cache-path store:** the store's `ReadExReq` removed every L1/L2 copy (Q2 step 2). The CPU load misses its private caches and reads the L3, which has the new data. Exception: a copy fetched between the store's read and its write (Q2 step 4).
- **Memory-path store:** no cache held the line at the check. The CPU load misses down to DRAM and reads the backing store, which has the new data. Exception: a copy fetched between the check and the write. The write does not snoop.
- **Prefetchers count as fetches.** The paper's DX100 runs enable stride prefetchers in the L1D and the L2 ([sim.py:94](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L94), [sim.py:176](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L176), [sim.py:207-208](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L207-L208), [sim.py:220-221](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/scripts/sim.py#L220-L221); [CacheConfig.py:174-201](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/configs/common/CacheConfig.py#L174-L201)). Whether one touches a `parent` line in the window is not determinable from source.
- **The paper's rule does not cover this window.** It forbids core stores to the array (§4.2), not core loads or prefetches.
- **In `TDStepMAA`:** inside the DX100 branch (`bfs.cc:139-195`), `parent` is touched only by DX100 commands (`bfs.cc:173`, `179`). Plain CPU loads and CAS on `parent` happen only in the CPU branch (`bfs.cc:205-210`), after `#pragma omp barrier` (`bfs.cc:197`). Every DX100 store was waited on inside the critical section before that.

## Q5. The memory-region dispatch stall (`IF.cc:213-219`)

- **Whose commands:** every valid command in the instruction file of the issuing core's instance ([IF.cc:185-221](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L185-L221)). The instance is `core_id % num_maas` ([CpuSidePort.cc:182-183](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L182-L183)). There is no core filter. With one instance, that is **every core's** unfinished commands.
- **Granularity: a registered region,** not a line or an element. Each memory command gets the region that holds its base address ([CpuSidePort.cc:241-245](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L241-L245), [MAA.cc:227-238](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L227-L238)). Only that region counts. Software registers regions with an m5 pseudo-op (`API/MAA_gem5.hpp:56-69`; [pseudo_inst.cc:561-562](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/sim/pseudo_inst.cc#L561-L562); [MAA.cc:200-217](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L200-L217)). `TDStepMAA` registers `queue`, `VertexOffsets`, `out_neighbors`, and `parent` as regions 6–9 (`bfs.cc:68-72`).
- **Which commands write:** stream store, indirect store (scalar and vector), indirect RMW (scalar and vector). Stream load and indirect load read. ALU and range loop are compute and carry no region ([CpuSidePort.cc:201-212](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L201-L212)).
- **The rule:** a new write stalls on any unfinished read or write of the same region. A new read stalls on any unfinished write of the same region. Read after read does not stall ([IF.cc:213-218](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L213-L218)).
- **"Unfinished"** means still valid in the instruction file. A command leaves at finish ([IF.cc:303-306](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L303-L306)).
- **With two or more instances** (scalability runs only), each instance has its own file. Cross-instance order goes through a region protocol checked at issue ([IF.cc:293](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L293), [MAA.cc:364-366](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L364-L366)). I did not trace it.

## Q6. Tiles and cores

- **Tiles are one shared pool.** The scratchpad holds `num_tiles_per_core × num_cores` tiles ([MAA.cc:51](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L51), [MAA.cc:83](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L83)). Commands carry raw 8-bit tile numbers ([CpuSidePort.cc:187-192](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L187-L192), [CpuSidePort.cc:217-231](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L217-L231)). I found no check that a tile belongs to the issuing core. `num_tiles_per_core` only sizes the pool.
- **Software splits the pool.** `DOBFSMAA` gives each thread 8 tiles from one global counter, inside `omp critical` (`bfs.cc:379-398`; `API/MAA_gem5.hpp:137-145`; `API/MAA.hpp:20-27`). `TDStepMAA` uses only its thread's tiles (`bfs.cc:76-92`).
- **Can core A name core B's tile?** Yes. Nothing in the device stops it.
- **Is the instruction file shared?** Yes, per instance. Its size is `num_instructions_per_core × cores per instance` ([MAA.cc:85-87](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L85-L87)). A new command takes any free slot; there is no per-core quota ([IF.cc:185-191](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L185-L191), [IF.cc:222-229](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L222-L229)). Tile hazards also span all cores in the file ([IF.cc:193-212](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/IF.cc#L193-L212)). A core's identity is the order in which its requester ID first appeared ([CpuSidePort.cc:122-128](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L122-L128), [CpuSidePort.cc:176-183](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L176-L183)).
- **Does core A's `wait_ready(t)` count core B's commands?** Yes. The ready counter is per tile number, not per core ([SPD.cc:120-139](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/SPD.cc#L120-L139)). Any core's command changes it at dispatch and finish ([MAA.cc:563-580](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L563-L580), [MAA.cc:607-620](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L607-L620)). A ready read looks up the tile from the address alone ([CpuSidePort.cc:295-314](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/CpuSidePort.cc#L295-L314)). Parked reads sit in one global list and are answered on port 0 ([MAA.cc:652-678](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/src/mem/MAA/MAA.cc#L652-L678)).

## Q7. What the paper says

**Paper:** A. Khadem et al., "DX100: A Programmable Data Access Accelerator for Indirection," ISCA 2025 (52nd International Symposium on Computer Architecture). arXiv 2505.23073; DOI 10.1145/3695053.3731015 per the University of Michigan Deep Blue record. The artifact README also names ISCA 2025 ([README.md:3](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/README.md#L3)).

On **coherence**, the paper says:

- §2.2: DX100 bypasses buffers by "directly injecting DRAM requests into the memory controller, while taking the coherency protocol into consideration."
- §3 overview: "DX100 is integrated as a modular memory-mapped component within the coherent fabric connected via the network-on-chip to system components."
- §3.6: "To maintain coherency, Interface snoops the coherency directories during the fill stage to check if the required cache line is valid, storing this information in the H bit of the Row Table. In the request stage, the interface routes the access to the LLC using the Cache Interface if the H bit is set; otherwise, it issues the access directly to memory controllers using the DRAM Interface. This approach ensures correctness, as DX100 maintains exclusive write access to the indirect arrays within the ROI (Section 4.2 – Legality). Thus, no cores can modify the cache lines between snooping and issuing the request."
- §3.6: "All DX100 memory regions are uncacheable, except for scratchpad data." A Coherency Agent invalidates cached scratchpad lines of an instruction's source and destination tiles at dispatch.
- §4.2 "Legality": "Transforming and offloading indirect memory accesses to DX100 requires that no core stores to the memory regions accessed by DX100 within the loop body."
- §6.6: with several instances, a coarse region protocol keeps one writer per array. "This protocol operates independently of the primary multicore coherence mechanism, as DX100 assumes that cores do not simultaneously modify arrays (Section 4.2 – Legality)."

On **synchronization**, the paper says:

- §3.5: ready bits are cleared at dispatch for all source and destination tiles and set at retire. "This bit allows the synchronization between cores with DX100."
- §4.2: "the compiler inserts a wait API call when synchronization is required. This occurs before the core reads data from the scratchpad produced by load, ALU, or range fuser instructions, or when accessing global memory modified by DX100's RMW or store operations."

On **memory consistency:** I found no statement of a consistency model. The paper never says how DX100 writes are ordered against core loads, beyond the wait and the legality rule. It never says a DX100 write invalidates core caches. I found no statement about core loads or prefetches of an array while DX100 writes it; the legality rule names only stores. (Searched the full HTML text for "coheren", "consisten", "invalidat", "snoop", "fence".)

---

## Side findings (not asked)

- **The check differs from the paper's wording.** The paper snoops "coherency directories during the fill stage." gem5 asks the `membus` snoop filter when each packet is queued, once for the read and again for the write (Q2 step 1).
- **The paper's BFS footnote does not match the artifact code.** §5 footnote 1: "We follow prior work by evaluating bottom-up BFS ... DX100 can also accelerate data access in top-down BFS." The artifact's DX100 BFS runs only `TDStepMAA`, the top-down step (`bfs.cc:418-422`, `bfs.cc:525`).
- **The force-cache heuristic is dead code by counting** (Q2 step 1). Not confirmed by a run.

---

## Sources

DX100 at `e4fc4afdf894f295442cef3604667a469fab8e62`. Base URL: `https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/`.

| File (under base) | Read scope | Used for |
|---|---|---|
| `src/mem/MAA/Port.cc` | whole file (611 lines) | per-line check, path choice, send, acceptance |
| `src/mem/MAA/CacheSidePort.cc`, `MemSidePort.cc` | whole files | port sends, no snooping |
| `src/mem/MAA/CpuSidePort.cc` | L100-451 | command decode, core identity, ready read, snoop send |
| `src/mem/MAA/MAA.cc` | L40-200, L200-260, L330-720 | construction, regions, issue, dispatch, finish |
| `src/mem/MAA/MAA.hh` | L55-260 | port classes |
| `src/mem/MAA/IF.cc` | L150-469 | hazards, shared slots, finish |
| `src/mem/MAA/IndirectAccess.cc` | L500-520, L600-700, L810-870, L1128-1165 | read and write packet types, force-cache rule |
| `src/mem/MAA/Invalidator.cc` | L32-70, L300-455 | scratchpad-only invalidation |
| `src/mem/MAA/SPD.cc` | L120-139 | per-tile ready counter |
| `src/mem/MAA/StreamAccess.cc` | grep | stream read type |
| `src/mem/MAA/MAA.py` | grep | defaults |
| `src/mem/coherent_xbar.cc` | L140-300, L495-560, L1068-1095 | eviction not snooped, `SnoopReq` answered by filter, forwarding |
| `src/mem/snoop_filter.cc` | L60-175 | non-snooping requesters not tracked |
| `src/mem/noncoherent_xbar.cc` | grep | forwarding |
| `src/mem/packet.cc`, `packet.hh` | grep | command attributes, `SnoopReq` |
| `src/mem/XBar.py` | L104-235 | crossbar classes and snoop filters |
| `src/mem/cache/cache.cc` | L1027-1080, L1150-1245 | snoop handling |
| `src/mem/cache/base.cc` | L458-500, L1330-1470 | access on receipt, writeback into L3 |
| `src/mem/ramulator2.cc` | L151-275 | write applied at acceptance |
| `src/sim/pseudo_inst.cc` | grep | region registration |
| `ext/ramulator2/ramulator2/src/dram_controller/impl/generic_dram_controller.cpp` | L1-260 | controller callbacks, forwarding |
| `ext/ramulator2/ramulator2/example_gem5_config.yaml` | whole file | controller in use |
| `configs/common/MAAConfig.py`, `configs/common/MAA.py` | whole files | DX100 wiring and defaults |
| `configs/common/CacheConfig.py` | L85-266 | cache hierarchy |
| `configs/common/MemConfig.py` | L160-310 | memory controller wiring |
| `configs/common/Simulation.py` | L730-760 | page mapping of DX100 ranges |
| `configs/common/Options.py` | grep | DX100 flags |
| `configs/deprecated/example/se.py` | L270-316 | bus setup |
| `scripts/sim.py`, `scripts/benchmark.py`, `README.md` | relevant parts | paper-run command lines |

Paper: [arXiv 2505.23073v2 (HTML)](https://arxiv.org/html/2505.23073v2), §2.2, §3, §3.5, §3.6, §4.1, §4.2, §5, §6.6. Venue record: [Deep Blue](https://deepblue.lib.umich.edu/items/900c79f8-9497-4572-b232-37ec1253de51).

Local files (ArchEvolve `655a4651`, `swdb-project/`):

- `apps/dx100/benchmarks/gapbs/src/bfs.cc:63-92`, `139-216`, `379-422`, `525`
- `apps/dx100/benchmarks/API/MAA_gem5.hpp:56-101`, `137-145`, `174-191`
- `apps/dx100/benchmarks/API/MAA.hpp:15-27`
- `.scratch/formal-verification-2026-10-09/research/14-dx100-wait-rule.md`

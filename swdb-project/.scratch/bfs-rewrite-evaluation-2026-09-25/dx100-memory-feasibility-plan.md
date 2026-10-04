# DX100 fixed host-memory feasibility observation

Created: 2026-09-25 (Eastern Time). This is a simulator bring-up diagnostic, not a
performance workload, candidate selection, or revision of the pilot's 32 GiB cap.

## Evidence and allocation estimate

Attempt `bfs-dx100-smoke-20260925-a5` restored the exact a4 checkpoint under the
unchanged 16 GiB guest configuration, traversed the 64-node graph, and entered the
first statistics dump. Its sampled process-group RSS reached 33,684,892 KiB
(32.12 GiB), exceeding its 32 GiB cap. The owned process group was terminated; no
ROI seal or completed verifier was observed. Partial statistics occupy only
531 KiB. This remains a failed, unverified execution.

The pinned source is `e4fc4afdf894f295442cef3604667a469fab8e62`. Its
`src/mem/physical.cc:435–494` restores nonzero words using a bounded temporary
buffer; it does not create a second full 16 GiB guest-memory copy.
`src/mem/packet.hh` defines 256 command regions and 61 command slots, while
`src/mem/cache/base.cc:2085–2277` creates 15 vector/formula statistics for every
command in each region plus a total region. The actual a5 `config.ini` has 21
caches, so there are 21 × 257 × 61 = 329,217 command groups and 4,938,255
vector/formula statistics before other model statistics. Its SHA-256 is
`7f03ea31171cb70d236d41512a115b83a99be25e11fff2c2cfe236faf6819a13`.

The retained configuration and constructors imply **50 requestors**, pending
runtime confirmation: 3 system requestors; 16 instruction/data requestors from
4 Atomic and 4 O3 CPUs; 18 page-table walkers; 12 stride prefetchers; and 1 MAA.
Of their names, 38 exceed the libstdc++ small-string capacity of 15 characters;
their character buffers require 846 bytes per statistic before allocator
rounding. `System::_getRequestorId` strips the `system.` prefix and deduplicates
names. `CacheCmdStats::regStatsFromParent` copies all names into every statistic.
`VectorInfo::enable` also allocates a requestor-sized description vector.

Static debug-type queries on the existing gem5 binary, without execution or
attachment, report `sizeof(StatStor)=8`, `sizeof(std::string)=32`,
`sizeof(VectorInfoProxy<Vector>)=216`, `sizeof(FormulaInfoProxy<Formula>)=216`,
and `sizeof(CacheCmdStats)=552`. For the installed libstdc++ growth strategy,
50 incremental subname insertions are estimated to leave capacity 64. The
following subtotal assumes all command statistics have been visited at a dump.

| Component | Estimated GiB | Basis |
|---|---:|---|
| Subname string objects (capacity 64) and description objects (50) | 16.78 | 4,938,255 × (64+50) × 32 |
| Long-name characters, including terminators | 3.89 | 4,938,255 × 846 |
| Nine counter vectors: storage and pointer arrays | 2.21 | 329,217 × 9 × 50 × (8+8) |
| One cached result vector per statistic | 1.84 | 4,938,255 × 50 × 8 |
| Six binary formula nodes and two referenced-formula result vectors | 0.98 | 329,217 × 8 × 50 × 8 |
| Command groups and information proxies | 1.16 | 329,217 × 552 + 4,938,255 × 216 |
| **Payload subtotal** | **26.86** | Excludes allocator rounding and other allocations |

`ldd` on the actual binary identifies `libtcmalloc_minimal.so.4`; glibc allocator
fragmentation is therefore not assumed. As a sensitivity estimate, rounding each
of the 38 long names to a 32-byte allocation raises the subtotal to **28.56 GiB**.
This is not an allocator measurement or RSS upper bound. It excludes formula
node objects, statistic descriptions, maps, other model components, Python,
allocator caches, transient growth allocations, executable mappings and resident
guest pages. These omissions plausibly explain the observed 32.12 GiB but do not
prove the peak will fit 48 GiB. The estimate does not justify changing statistics,
modeled hardware, guest memory, allocator, or workload to obtain a favorable run.

## One finite next attempt

Run exactly one new attempt, `bfs-dx100-smoke-20260925-a6`, after this plan and its
observer code are committed, reviewed and pushed, and the native profiling job
has released its lane. Require a fresh lane/legacy-lease/load/disk/memory check,
with at least 64 GiB host MemAvailable before claiming the free lane. Strict
NUMA binding also requires at least 52 GiB under the explicitly reviewed
kernel-based capacity estimate below. The original free-plus-clean-cache gate
rejected dispatch at 21:22 ET; this revision is based on kernel accounting before
any new simulation or candidate assessment. Retain both nodes’ meminfo and zone
watermarks. Do not drop caches or change NUMA policy. Use the
normal verified socket-lane helper. Keep a4's exact graph ID, path, source, binary,
checkpoint manifest and modeled configuration; select the explicit
`--checkpoint-evaluation bfs-dx100-smoke-20260925-a4` compatibility proof path.

Bounds: **48 GiB process-group RSS**, **750 seconds restore/run**, **1,100 seconds
adapter total**, **1,200 seconds outer timeout**, and **2 GiB raw output**. The
unused checkpoint allocation remains 300 seconds. No model rebuild, allocator
change, model/statistics reduction, guest-memory change or graph regeneration is
permitted. The 48 GiB cap provides finite diagnostic headroom over the measured
32.12 GiB, not a guarantee of success. After a 48 GiB failure, stop this path and
retain unresolved host cost; do not increase its cap or repeat until success.
A successful bring-up observation may inform a separately justified pilot-plan
revision before candidate assessment. The current pilot cap remains 32 GiB.

The observer records only the owned process group's RSS and PIDs, simulator-log
byte offset and latest phase on a nominal five-second schedule, plus a terminal
sample if the memory limit is exceeded. It does not retain other jobs' process
information. Host phase hooks forward each original `instantiate`, `simulate`
and statistics `dump` call once, preserving arguments/results, without inserting
modeled events or extra statistics dumps. Each phase records its host timestamp,
self RSS/high-water values and up to six read-only numeric properties from the
already-linked tcmalloc; missing properties remain absent. Total phase records
are capped at 128. Observation wall cost is explicitly separate from BFS timing.

After instantiation, direct `Root.resolveStat('system.l3.ReadReq_T.hits')` reads
one vector's size and at most 256 names to confirm requestor cardinality. The
observer never walks the full statistics tree, evaluates a statistic value,
materializes all names, or calls `get_simstat`. Driver and observer file hashes,
phase logs and RSS logs are retained in the execution evidence, including on
failure. Sampled RSS may miss peaks between samples; it is not an exact maximum.


## Reviewed capacity estimate revision — 2026-09-25

The original gate excluded all reclaimable slab. Linux's documented
`MemAvailable` estimate explicitly includes reclaimable slab while reserving
watermarks and accounting for potentially unreclaimable cache. See the
[kernel memory accounting documentation](https://docs.kernel.org/filesystems/proc.html#meminfo).
The v6.8 primary implementation is
[`si_mem_available` in mm/show_mem.c](https://github.com/torvalds/linux/blob/v6.8/mm/show_mem.c)
and [`calculate_totalreserve_pages` in mm/page_alloc.c](https://github.com/torvalds/linux/blob/v6.8/mm/page_alloc.c).
The fetched source SHA-256 values are respectively
`29c0c6f784bf30c666e0f8416e0e4c36ca65bdcbbd4ecccc0218b40bf24aee18` and
`5ec6e187b4b7134cf7e4d4eafb6525b29d88d3c2e9b0c9e79436103a077afcd0`.
These are upstream v6.8 source references for the host's 6.8 kernel family, not
an assertion that its Ubuntu kernel has an identical complete source tree.

The approved helper `scripts/dx100_capacity.py` applies that algorithm to the
selected socket's counters, with additional conservative exclusions. All
arithmetic uses integer pages and is converted to KiB only afterward:

- `F` is node `MemFree`; `L` sums its zones' low watermarks.
- `R` sums `min(managed, high + max(protection))` over that node's zones.
- `C` is `max(0, Active(file) + Inactive(file) − Dirty − Writeback)`.
- `S` is `SReclaimable`; miscellaneous reclaimable kernel memory is excluded.
- `A = max(0, F − R + C − min(C/2,L) + S − min(S/2,L))`, with integer division.
- Discount `A` by another **1 GiB** for estimation uncertainty. Require the
  discounted result to be **at least 52 GiB**, and global `MemAvailable` to be
  **at least 64 GiB**, using exact integer thresholds without rounding up.

The retained 21:37:33 ET preclaim receipt gives node 1's 30.3888 GiB free,
2.4751 GiB clean file LRU and 20.7223 GiB reclaimable slab. Its low-water sum
was 111,484 KiB (including an empty Movable zone's 32-page watermark) and
reserved memory 177,400 KiB. The algorithm produced 55,788,836 KiB (53.2044 GiB),
or **54,740,260 KiB (52.2044 GiB)** after the extra discount. This replaces the
earlier illustrative normal-zone-only arithmetic; the executable helper has
always included every zone. The selected-socket
threshold leaves 4 GiB above the 48 GiB process-group limit in addition to that
1 GiB discount and kernel reserves. These values illustrate the algorithm;
they are not authorization to reuse an old capacity observation.

The 21:30:22–21:30:52 ET read-only observation showed zero increases in swap,
allocation stalls, direct/kswapd page scans or steals, slab scans and OOM counts.
Memory PSI averages were zero; the full-stall cumulative counter increased by
62 microseconds. This quiet interval does not prove reclaim will succeed during
a later workload. `/proc/slabinfo` and named `/sys/kernel/slab` counters denied
unprivileged access, so no claim is made about slab classes, ownership or exact
reclaimability. The slab exists without an owned simulator and is separate from
its process RSS. Reclaiming it is left entirely to normal kernel policy.

Immediately before lane claim, run the helper against fresh files and retain
its timestamped raw inputs, calculation, source hash and result; repeat inside
the verified lane before simulation if acquisition/setup delayed dispatch.
Failure holds the attempt. The helper does not allocate workload memory, change
policy, trigger reclamation, count anonymous memory as reclaimable, or guarantee
freedom from NUMA OOM. Normal lane/load/storage checks still apply. This revision
changes only a host-capacity estimate; the single-attempt count, 48 GiB RSS cap,
guest/model/statistics/ROI identities, and pilot's 32 GiB cap remain unchanged.

## Output collection alternatives — 2026-09-25

Pinned `VectorInfo::enable` allocates requestor-sized name and description
storage before collection. Format options such as `desc=False` and `spaces=False`
do not remove that storage. `Text::visit(VectorInfo)` evaluates `info.result()`
and copies names before printing; formulas use the same visitor. About 2.82 GiB
of the estimate consists of lazily populated result vectors, but the larger
fixed names/counters/information allocation persists independently of output.

The existing `--stats-root` mechanism filters whole SimObject subtrees. Selecting
only MAA omits root `simTicks`/`simFreq` and cache observations; selecting the root
restores the entire traversal. It is therefore not a compatible one-flag
replacement for current evidence. A bespoke selected-statistic visitor might
retain a defined subset without changing simulated work, but would require a
separate audited collection contract and exact metric/timing validation. It
would not remove the fixed statistic allocation or unrelated kernel slab.
No output filtering, statistic deletion, allocator setting or model patch is
part of a6.


## One-attempt outcome — 2026-09-25, 23:31 ET

Attempt a6 consumed the one authorized 48 GiB execution on lane 1, generation
395. The fresh preclaim and in-lane discounted node estimates were 55,016,988
and 55,080,236 KiB, both above the unchanged 54,525,952 KiB threshold; global
capacity also passed. Original modeled hardware, checkpoint and statistics
remained unchanged. The bounded observer confirmed the estimated requestor
count of 50. Actual sampled peak RSS was 33,719,536 KiB (32.158 GiB), consistent
with the prior 32 GiB failure and below this attempt's cap. The first dump
finished at 113.46 seconds of model runtime; the post-ROI verification loop
reached its fixed tick limit at 341.04 seconds. Total lane occupation was
416 seconds, within all wall-time and storage limits.

The model sealed the ROI and printed same-guest PASS, then failed the separate
normal-termination requirement. This is a retained compatibility/correctness
observation, not a reason to repeat the memory experiment or increase its cap.
The prior gate refusals consumed no execution; this actual attempt consumed one.
[The a6 receipt](observations/dx100-smoke-a6.json) binds capacity receipts,
phase/RSS samples, allocator values, sealed statistics and final event. The
pilot's separate 32 GiB bound is not revised by this observation.

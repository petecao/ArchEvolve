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
NUMA binding also requires at least 52 GiB on that socket as MemFree plus
max(0, FilePages − Shmem − Dirty − Writeback). Retain both nodes’ meminfo, including
anonymous and slab fields; do not count anonymous, shared-memory, dirty pages or
slab reclamation as available headroom. Do not drop caches or change NUMA policy.
Use the
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

# DX100 preflight and execution design

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-25 17:16 ET

This is a read-only preflight and proposed bounded execution design. It does not
record a successful build, simulation, correctness check, or performance result.
The user authorized implementation and remote execution on 2026-09-25; root-agent
coordination still controls dependency ordering and the two socket lanes.

## Live host snapshot

Observed on mbit10 at 2026-09-25 16:54–16:55 ET; recheck before dispatch.

| Resource | Observation | Execution consequence |
|---|---|---|
| Node 0 lease | Released, generation 264 | Available to claim, subject to fresh checks |
| Node 1 lease | Released, generation 374 | Available to claim, subject to fresh checks |
| Legacy lease | Released, generation 77 | No legacy lease conflict observed |
| Load | 5.25 / 6.44 / 7.55 at last snapshot | Other-user training remains active |
| RAM | 125 GiB total; 111 GiB available | Two 35 GB simulations plausibly fit; measure actual use |
| `/data1` | 22 GiB free | Source/build may consume the remaining margin |
| `/data` | 198 GiB free | Put raw output under `/data/yanruj/EvolveSWDB_runs/` |
| Hardware counters | `perf_event_paranoid=4` | Native hardware events unavailable |
| Compiler/build | GCC 13.3; SCons 4.5.2; Python 3.12 headers; CMake | Actual compatibility remains to be built |
| Dependencies | zlib/protobuf headers present; libelf pkg-config unavailable | Optional versus mandatory dependency checks belong to the build |
| Remote EvolveSWDB | `main`, `a38dfac2e4849235158ec2cdfb2d2623ffe6b963` | Sync an exact implemented commit before execution |
| Lane checkout | `/data1/yanruj/Memacc-evolveswdb-lane`, clean, `c40ad13e5a689d169ceba58aa765a7edfb243538` | Matches live origin `yanrujhou_main`; use its lane script |
| Main Memacc | Old/dirty `a4521f3b5a265fdc9a4c6f80e065ac25d5e0badb`; no lane script | Preserve it; do not dispatch from it |

Lane-script SHA-256: `00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8`.
No DX100/gem5 checkout was found in a depth-four search under `/data1/yanruj`
and `/data/yanruj`; this does not establish absence elsewhere on the host.
Source preparation subsequently cloned the pinned upstream revision by git into
`/data1/yanruj/DX100-bfs-e4fc4af` at 17:12 ET. No model build or measurement had
started at that point.

## Pinned source findings

The clean inspection checkout `/private/tmp/codex-dx100-bfs-inspect-20260925`
resolves to `e4fc4afdf894f295442cef3604667a469fab8e62` (204 MiB). All source
references below use that revision of [DX100](https://github.com/arkhadem/DX100/tree/e4fc4afdf894f295442cef3604667a469fab8e62).

| Finding | Source | Consequence |
|---|---|---|
| Artifact BFS input is **uniform random**, scale 22, default degree 16 | `benchmarks/gapbs/run_g_gen.sh` invokes `converter -u`; `scripts/sim.py:373–391` selects scale 22 | Do not label the artifact as Kronecker or infer identity from `serialized_graph_22.sg` |
| Authors use four guest cores, 16 GB guest memory, 3.2 GHz CPU/system clocks, Ramulator2 and two channels | `scripts/sim.py:90–115,192–250` | Preserve exact configuration and actual clock periods |
| BASE LLC is 10 MB, 20-way; accelerated LLC is 8 MB, 16-way | `scripts/sim.py:103–108,177–190` | Preserve artifact pair and separately run a matched-LLC control |
| API supports NUM_CORES 4, 8, 16 with 16/32/64 GB memory-map base | `benchmarks/API/MAA_gem5.hpp:12–20` | Do not reduce modeled memory below the API mapping without an explicit interface change |
| Author acceleration requires remaining frontier strictly greater than `NUM_CORES * 1024` | `benchmarks/gapbs/src/bfs.cc:103–139` | Small graphs can be entirely scalar; observed accelerator counters are required |
| Each core allocates eight tiles and eight registers | `benchmarks/gapbs/src/bfs.cc:370–389`; `benchmarks/API/MAA.hpp` | Four-core default consumes 32 tiles and 32 registers; wrappers must budget resources |
| ROI is reset/dump around traversal levels, queue advancement, normalization | `benchmarks/gapbs/src/bfs.cc:328–353,403–434` | Initialization and verification remain excluded for the DX100 ROI |
| `m5_exit(0)` precedes return to `BenchmarkKernel` | Same BFS source; `src/sim/pseudo_inst.cc:154–168` | Default simulator loop exits before the enclosing verifier |
| Verification prints PASS/FAIL but `main` returns zero either way | `benchmarks/gapbs/src/benchmark.h:109–113`; `bfs.cc:534–535` | Parse an explicit verdict for the exact timed binary and workload |
| Checkpoint helper declares `force_rerun_sim` but callers pass `force_rerun`; body also reads `force_rerun` | `scripts/sim.py:118–120,380–383` | Use an identified SWDB adapter instead of executing the broken artifact dispatcher |
| Parser divides simTicks by 313 | `scripts/parse.py:282–283` | Read simFreq and actual config clock period; retain raw ticks |
| Artifact build scripts use unbounded make or `-j32`, build all suites, and generate five scales | `scripts/make.sh`, `scripts/make_fast.sh`, `benchmarks/gapbs/build.sh` | Invoke only bounded BFS/model targets through a socket lane |

The README's approximately 6 GB/35-minute build and approximately 35 GB per
simulation estimates describe the artifact, not measured BFS-only costs here.

## Proposed implementation contracts

Keep model revision/configuration, memory-mapped software interface, evaluator
backend, and physical host as separate identities. Operation contracts should
point to both the API declaration and model implementation. The initial BFS set
is `maa_const`, `maa_stream_load`, `maa_indirect_load`, `maa_range_loop`,
`maa_alu_scalar` with LT, `maa_indirect_store_vector`, tile/register allocation,
tile access, and completion operations. The API contains additional stream,
indirect RMW, vector ALU, and reduction operations that may be cataloged with
the same source-backed discipline.

`cond_tile=-1` denotes no mask; active masks are tile values. Indirect store can
return the old value to a destination tile. In `IndirectAccess.cc:900–940`,
entries for a returned cache line read and update one local buffer sequentially;
repeated indices therefore observe preceding updates in that processing order.
This does not establish general atomicity against concurrent CPU writers or
other accelerator operations. Preserve the author BFS critical section and
do not advertise a CPU CAS contract. Cross-unit ordering and global duplicate
winner order remain unsupported unless separately established. API issue uses
`mfence`; completion uses a ready-register load plus `mfence`. An instruction
issue fence alone does not demonstrate operation completion.

Execution records should bind the exact model/binary/source hashes, graph and
source vertex, options/configuration, checkpoint manifest, build/toolchain,
lane receipt, start/end/host cost, exit cause and raw artifact paths. A checkpoint
is valid only for its binary, graph/options, guest core/memory layout and model
revision; fresh output directories prevent stale statistics from looking complete.

For exact timed-binary checking, prefer an evaluator-owned Python simulation
driver that resumes once after `m5_exit instruction encountered`, preserves the
already completed ROI statistics interval, and continues the same guest until
the explicit verifier and final process exit. Bound continuation count and time;
retain the first ROI dump separately from subsequent terminal statistics. This
is a proposed mechanism, not yet verified to work. Use `-n 1 -v -r SOURCE` per
execution and count completed checks rather than assuming guest trial counts.

The model exposes `system.maa.numInst_INDRD`, `numInst_INDWR`, `numInst_RANGE`
and memory-access counters. These establish executed accelerator work when
positive in the sealed ROI. Zero-valued counters can be omitted by gem5's
`nozero` flag, so absence is not positive evidence. ROI cache/memory counters
are simulated observations; they do not give loop-specific attribution.
Selected-region timing can use the existing `-l` per-level `td`/`td_maa`
observations with accumulated inclusive scope, subject to the pilot confirming
guest timer precision and correspondence. New helper/loop discovery must still
use the shared profiler and exact source mappings; the MAA counters alone do
not satisfy discovery.

## Proposed bounds and dispatch order

Assumption for the initial build: one clean pinned DX100 clone under
`/data1/yanruj/`, build with `-j8` on one leased socket, maximum 2 hours and two
diagnosed attempts, 48 GiB resident-memory ceiling, 10 GiB build-storage budget.
All build caches and temporary files stay under `/data1/yanruj/`; logs and run
outputs go to `/data/yanruj/EvolveSWDB_runs/`. Build Ramulator2, x86 m5ops and
gem5.opt, then only scalar/author BFS and converter; gem5.opt can first service
both atomic checkpoints and O3 runs, avoiding an unnecessary second full build.
Stop and retain a stage failure if the bounds are reached.

Assumption for bring-up: four guest cores, one graph/source per run, at most two
30-minute smoke attempts per scalar/accelerated case, 48 GiB resident-memory
ceiling per simulation, 20 GiB raw-storage budget per smoke group. This proves
backend/continuation only. The baseline pilot must then select sizes from
measured cost and path coverage; g14/g16 are candidate calibration sizes, not
a frozen protocol. Strict frontier threshold means g12 cannot establish author
acceleration at four cores. Artifact urand-u22 remains a separate required case.

Root assigns lanes immediately before launch. Read all three leases and live
load/storage, fetch/verify the lane checkout, and execute every build or run
through its `socket_lane.sh` inside a named tmux session with timeout. The socket
lease is authoritative; advisory coordination must not replace it. Record host
conditions per run and retain incomplete outcomes. Candidate assessment waits
for the actual baseline/reference calibration and protocol freeze.

## Concrete build plan

`scripts/dx100_build.py` implements the staged build below, requires a held
socket lease with matching affinity/memory binding, and writes a durable
`build-receipt.json` plus stage logs to a new external output directory. It
samples the build process group's RSS every two seconds, checks source/build
and raw-output usage every 30 seconds, and terminates the group on bound or
monitor failure. Raw build evidence is additionally capped at 2 GiB. Monitoring
is sampled rather than a kernel-enforced aggregate-memory guarantee; normal
termination and signal interruption preserve completed stage evidence. Syntax
and argument parsing were checked locally; no model build is implied.

Use the pinned source in `/data1/yanruj/DX100-bfs-e4fc4af`. Clone by git and
verify HEAD; never copy the Mac checkout's build products. GCC 13.3 is selected
because it is installed and supports Ramulator2's C++20 requirement. The
artifact lists GCC 12 and Clang 15 as tested compilers; GCC 13 compatibility
remains an actual build check. Ramulator2 fetches yaml-cpp `yaml-cpp-0.7.0`,
spdlog `v1.11.0`, and argparse `v2.9`; retain their resolved commits in the build
manifest. Existing mandatory gem5 dependencies checked here are Python 3.12
development headers/library, zlib 1.3, protobuf 3.21.12/protoc, m4, SCons, and
tcmalloc. Missing optional libelf/capstone must not silently trigger a package
installation or change the required simulated model.

The following commands are the payload of a timeout-bound socket-lane job,
not commands to run unconfined. The root launcher must record host conditions,
enforce memory/storage/elapsed-time limits, and capture all stdout/stderr.

```sh
export TMPDIR=/data1/yanruj/DX100-bfs-e4fc4af/.tmp
export XDG_CACHE_HOME=/data1/yanruj/DX100-bfs-e4fc4af/.cache
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd /data1/yanruj/DX100-bfs-e4fc4af
git rev-parse HEAD
cmake -S ext/ramulator2/ramulator2 -B ext/ramulator2/ramulator2/build \
  -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13
cmake --build ext/ramulator2/ramulator2/build --target ramulator --parallel 8
scons -C util/m5 build/x86/out/m5 -j8
scons defconfig build/X86 build_opts/X86
scons setconfig build/X86 RUBY=n USE_SYSTEMC=n
scons build/X86/gem5.opt -j8 CXX=g++-13 CC=gcc-13
make -C benchmarks/gapbs -j4 CXX=g++-13 \
  CXX_FLAGS='-std=c++11 -O3 -Wall -g3 -fopenmp -DGEM5' \
  bfs bfs_maa bfs_maa_1K converter
```

`build_opts/X86` selects only the x86 ISA. Its default enables Ruby and the
global default enables SystemC; disable those unused components because this
evaluation uses classic caches and Ramulator2. This changes compiled feature
availability, not the selected CPU/cache/memory model. Record the resolved
Kconfig. `gem5.opt` retains debug traces needed for diagnostics and can run both
AtomicSimpleCPU checkpoints and X86O3CPU evaluation. A second `gem5.fast` build
is optional only if measured checkpoint cost justifies it within the same budget.

Initial checkpoint invocation uses `gem5.opt`, an absolute fresh outdir,
`configs/deprecated/example/se.py --cpu-type AtomicSimpleCPU -n 4
--mem-size 16GB --max-checkpoints 1 --cmd ABSOLUTE_BFS --options
'-f ABSOLUTE_GRAPH -l -n 1 -v -r SOURCE'`. Stopping immediately at the first
checkpoint avoids accidentally running the accelerated memory-mapped path in
an atomic system without its hardware. This command is a bring-up design until
the public evaluator executes and records it. A restore selects
`--checkpoint-dir EXACT_CHECKPOINT_DIR -r 1`, preserves the same binary/options,
and applies the identified O3/cache/Ramulator2 configuration. Do not reuse the
artifact script's destructive directory cleanup or treat an existing stats file
as a completed run.

## Initial BFS operation data

All declarations are in `benchmarks/API/MAA_gem5.hpp`; types resolve through
`MAA.hpp`. The table deliberately restricts acceptance to the BFS-required
`int32_t`/`uint32_t` path. Other declared types can be cataloged without claiming
all combinations or ordering properties were executed.

| Stable suggested operation ID | Declaration and backend | Effects and restrictions |
|---|---|---|
| `dx100.mmio.v1.const.i32` | `maa_const<int32_t>(value, dst_reg)` at line 147; register MMIO | Writes one allocated scalar register; no main-memory effect |
| `dx100.mmio.v1.stream-load.i32` | `maa_stream_load<int32_t>(base,min_reg,max_reg,stride_reg,dst_tile,cond_tile=-1)` at line 232; `StreamAccess.cc` | Loads the indexed half-open range into a tile; destination size belongs to the completed tile; range/stride must be valid |
| `dx100.mmio.v1.indirect-load.i32` | `maa_indirect_load<int32_t>(base,idx_tile,dst_tile,cond_tile=-1)` at line 270; `IndirectAccess.cc` | Gathers valid masked indices; requires live mapped base and allocated index/destination tiles; repeated reads permitted |
| `dx100.mmio.v1.range-loop.i32` | `maa_range_loop<int32_t>(last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile=-1)` at line 366; `RangeFuser.cc` | Expands nested index ranges in bounded output tiles, updates continuation registers; both output tile sizes and completion matter |
| `dx100.mmio.v1.alu-scalar-lt.i32` | `maa_alu_scalar<int32_t>(src_tile,reg,dst_tile,Operation_t::LT_OP,cond_tile=-1)` at line 175; `ALU.cc:411–413` | Produces a comparison tile consumed as a mask; does not load/store application memory |
| `dx100.mmio.v1.indirect-store-vector.i32` | `maa_indirect_store_vector<int32_t>(base,idx_tile,src_tile,cond_tile=-1,dst_tile=-1)` at line 289; `IndirectAccess.cc:900–940` | Masked scatter; optional destination receives each old value; repeated-address processing order is model-defined, not an API-level CPU CAS or global atomicity guarantee |
| `dx100.mmio.v1.wait-ready` | `wait_ready(tile)` at line 98; ready-register access in `CpuSidePort.cc`/`SPD.cc` | Completion access plus mfence before CPU consumes tile results; issue fences do not substitute for this |

Common requirements: x86 memory-mapped API; model revision above; `-DGEM5`,
`-DNUM_CORES=4`, appropriate `-DTILE_SIZE`; m5ops and API headers; model
configuration matching the MMIO memory base and scratchpad allocation; live
mapped arrays; no unsupported CPU ISA-flag substitution. Interface availability
is `source-supported`; executable readiness remains `not-built` until a linked
build receipt exists. A wrapper inherits every requirement of its constituent
operations, and unknown required semantics reject execution.

## Source fingerprints

SHA-256 over the clean pinned checkout's exact bytes:

| Source | SHA-256 |
|---|---|
| `build_opts/X86` | `a8dac70193018cfca0339bc452ccd6c8d3cb766b2ea945ee2470eb4939d34978` |
| `benchmarks/API/MAA.hpp` | `4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd` |
| `benchmarks/API/MAA_gem5.hpp` | `5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174` |
| `benchmarks/API/MAA_functional.hpp` | `ff8b2c9ccbb8b61ec28845f4b4c279db4c2dc40d73a74c5e8f4fa0bf9b92eedc` |
| `benchmarks/gapbs/src/bfs.cc` | `6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465` |
| `benchmarks/gapbs/src/benchmark.h` | `87c20752c8437dd5152d00e7c995bedfab15b8929219f85846f47e0f9a4b339f` |
| `benchmarks/gapbs/run_g_gen.sh` | `40d36226245283c805e18c5c6d91a6dcfafa289ef14b292c18813515391a748c` |
| `src/mem/MAA/IndirectAccess.cc` | `7e238a370f25ff5a7a1211548630a291d6358c32d8a199fc58bfacd37d1d35db` |
| `src/mem/MAA/RangeFuser.cc` | `27a3713469a44031829d638b3e865f714cd63a0423c493d78cbcc07dd9b7d42e` |
| `src/mem/MAA/StreamAccess.cc` | `5fe78a94f0d690396cdfbcdd9b0082e57cbdb4a6b445a7282b2533a33852d47b` |
| `src/mem/MAA/ALU.cc` | `3eab45bf9847d5b1a97df2149ad2aa67b46f8e72c000d54bd01c384fa608e0e6` |
| `configs/common/Simulation.py` | `8e19c4ccbd1dcad555016e9e7479e9e89d3e0ada75cd5a444098a4e41c2c83b2` |
| `ext/ramulator2/ramulator2/CMakeLists.txt` | `19a7a50236b5a2daf7a304af2995eeba11b00c97e8e709ead619dd0177f0db75` |
| `ext/ramulator2/ramulator2/example_gem5_config.yaml` | `aca6e27b58afdfbfd80b7ec41c3f0e7e574a1fc7355a3512981ead823f68731b` |
| `scripts/sim.py` | `82c8d78e4339f1be9249c0e92db8a8d5f9654310f1fe4dc91680da6a9e0f7681` |

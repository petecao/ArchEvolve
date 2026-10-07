# Independent native service calibration

Created: 2026-10-06 ET. Ticket11; implementation in progress.

`import-cpu-service-calibration` retains service/driver elapsed trials and their
explicit event counts in a typed `cpu_service_calibration` record. It does not read
application timings. The cost is paired elapsed difference divided by the counted
work; raw subtraction values and spread remain visible. Any nonpositive residual
keeps the parameter unknown instead of clamping it to zero.

The portable runner times an independent clock-call loop and a matched driver. It
uses a pilot to select bounded work, alternates measurement order, retains every
trial, and consumes returned checksums outside timing. Compilation, pilot and
trials share the wall budget. Raw output stays outside the project; repetitions
are capped at11, wall time at900s and output at25MiB. Portable contract runs require `--fixture`; actual native admission is checked separately.

An explicitly labeled fixture requires `--fixture` and keeps parameter basis `reported`. Native clock import requires actual Linux/x86_64 LLVM22 timing on the registered
machine, a verified socket lane, clean committed source, a physical core, hash-bound
loaded C/C++ libraries, at least 7 repetitions and 0.05s paired pilot durations.
Counts and timed work use the identical shared header. Governor/turbo paths are
recorded as null when unavailable; no settings are changed. Adding
`--llvm-bin` runs six separate LLVM22 source-normalized-v2 count points against
the same shared service body:32/64/96 service iterations and matched drivers. The
clock numerator must be exactly one opaque ABI call per service iteration and
zero in the driver. The receipt retains the actual ABI name, pipeline, shared
header and count-driver hashes, observer hashes and all six characterization
hashes. These instrumented runs never supply elapsed calibration values.
The receipt format is `swdb.cpu-service-calibration.v1`, with `machine`, `threads`,
`context`, `settings.repetitions`, `services[]` and canonical `identity_sha256`.
Each service names its unit, event definition, execution scope and denominator,
and retains paired `events`, `gross_seconds`, `driver_seconds` and order per trial.

```sh
python3 -m swdb cpu-service-calibrate --records "$COPIED_RECORDS" \
  --output "$EXTERNAL_SERVICE_OUTPUT" --fixture --repetitions 3 \
  --min-trial-s 0.002 --max-wall-s 60 --format json
python3 -m swdb import-cpu-service-calibration --records "$COPIED_RECORDS" \
  --receipt "$FIXTURE_RECEIPT" --id fixture.service.cost --fixture --format json
python3 -m swdb validate --records "$COPIED_RECORDS"
```

The CPU band will use fresh LLVM22/libomp T1 development timings and a separate
held-out input after implementation, independent calibration and development width
freeze. Historical GCC/libgomp baselines and candidate artifacts stay in honest
estimate/exclusion reports. Missing cost, memory-state or observation scope remains
unknown. Native CPU timing continues to decide CPU evaluations.

`native_service_costs` consumes exact region-filtered call site counts through the
shared composition API. Descriptions select ABI names and seconds/call parameters
under host/serial-T1 scope; supported opaque service costs are additive. Full
site/count coverage clears that call only after a known service result. Zero
executions need no rate, counted callee bodies receive no second charge, and
unsupported length/lifecycle selectors or missing rates remain unknown.

`--count-only --llvm-bin ...` creates `count-proof.json` in the external raw folder
with `timings_collected: false`; it emits no elapsed trials or service rates. The
importer refuses this distinct `swdb.cpu-service-count-only.v1` format. Native
count-only execution retains the same verified lane, clean source and loaded ABI
identities, and is independent of application development/holdout timings.

Native count-only command inside the parent-owned node0 socket lane:

```sh
python3 -m swdb cpu-service-calibrate --records records --machine mbit10 \
  --lane mbit10-evaluation-node0 --count-only --max-wall-s 600 \
  --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$NEW_EXTERNAL_COUNT_FOLDER" --format json
```

`--lane` is the exact lease-name claim, not a NUMA index. The numeric `0` claim
stopped the first remote attempt before any proof; that attempt supplies no
count/timing evidence. The corrected named lease still requires the real ancestor,
CPU affinity, memory bind policy and held lease checks; a matching string alone
does not authorize native execution. Use outer timeout900s and raw data mounts.

## Exact allocator cells (2026-10-06 ET)

`cpu-service-calibrate --service-group allocator` separately times array/scalar
allocation and deletion. The default matrix has20 cells: array sizes8192,65536,
227416,262144,524288B and scalar sizes8,16,32,64,128B, each with allocation and
free cost. These are the complete observed T1 BFS/BC allocation/lifetime bins in
`evidence/registered-counts-t1-mbit10-20261006-a1.json`. Different allocation/free
262144B totals reflect the ROI lifetime boundary. Explicit `--size` values test
all four operations at each selected bin.

One batch has at most65536 events and64MiB of live requested payload. A timed
pair has at most16777216 events, seven alternating-order repetitions,900s wall
budget,64MiB counted-build budget and a separate25MiB timed-data budget. Timed payload is untouched; the cap describes
requested live payload, not measured RSS. The gross pilot selects a batch count
with25% duration margin; native admission requires every gross repetition to
reach50ms. Each paired driver duration is retained even when shorter than50ms.
Unresolved subtraction remains null without clamping negative residuals.

The shared noinline C++11 body must retain all four ABI calls under actualO3
optimization. A separate source-normalized-v2 proof executes each operation at
3/5 events, service/driver, smallest/largest byte bins. It retains observed
allocation and free-lifetime size bins, exact ABI, count hashes and the shared
source identity. Count-only mode never runs the native timer or emits elapsed
receipts. Preparations and cleanup are outside both the counted service ROI and
timed segments.

The construction is `fresh_process_repeated_allocate_free_batches`. It measures
that construction's effective costs; transfer to the application's retained heap
state is **inferred** and requires an explicit model assumption. No physical
residency, page-fault rate or instruction-issue latency is claimed. Calibration
records preserve GLIBC_TUNABLES, actual MALLOC_* variables, preload/audit and
library-search controls. Their absence is meaningful only under the declared
scope. Legacy counted receipts lack this allocator-control declaration and cannot
prove equality. The glibc allocator [tunables](https://sourceware.org/glibc/manual/latest/html_node/Memory-Allocation-Tunables.html)
include cache and mapping thresholds, so matching requested sizes alone does not
establish allocator-state equivalence.

Parent-dispatched commands, in a clean immutable Linux checkout and a real named
node0 lease (raw folder must be new; use a different folder for each phase):

```sh
python3 -m swdb cpu-service-calibrate --records "$SWDB_RAW_RECORDS" \
  --service-group allocator --count-only --machine mbit10 \
  --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_ALLOCATOR_COUNT_RAW" --max-wall-s 600 --format json
```

After count proof and release of any other socket timing job:

```sh
python3 -m swdb cpu-service-calibrate --records "$SWDB_RAW_RECORDS" \
  --service-group allocator --machine mbit10 \
  --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_ALLOCATOR_ELAPSED_RAW" --repetitions 7 \
  --min-trial-s .05 --max-wall-s 900 --format json
python3 -m swdb import-cpu-service-calibration --records "$SWDB_RAW_RECORDS" \
  --receipt "$SWDB_ALLOCATOR_ELAPSED_RAW/receipt.json" \
  --id mbit10.cpu.lanl20261006.service.allocator.a1 --format json
python3 -m swdb validate --records "$SWDB_RAW_RECORDS"
```

Use600s inner/900s outer for count-only and900s inner/1200s outer for elapsed.
Keep node1 idle during elapsed calibration. Raw binaries, IR and logs stay remote;
only the typed service record and compact receipt metadata enter Git. Application
accuracy remains unsupported until every executed memory/runtime service and the
matched original-driver timing scope are admitted independently.

### Allocator count-build budget preregistration (2026-10-06 ET)

The first native count-only attempt at source00c03f3 stopped safely after
26,312,382B of build evidence crossed the original25MiB guard. Linux produces
about1,064,400B per point, dominated by894,368B `Characterize.so` files; all32
points therefore require about34.1MB before compact proof metadata. The failed
a1 folder remains preserved and supplies no numerator or elapsed receipt.

The a2 contract assigns **64MiB to counted build artifacts** and preserves the
separate **25MiB timed-data cap**. All32 points, exact ABIs, observed byte/lifetime
bins, source identities, timing criteria and20-cell matrix stay unchanged.
`--count-build-cap-mib` can lower the build limit to exercise a fail-closed check;
it cannot exceed64. Every file is budgeted: top-level pilot/partial-trial/receipt
data uses the timed budget; every other file uses the build budget. A failure
retains partial sealed point records and emits no admitted proof/timing receipt.
Final JSON receipt sizes are checked before publication too. This change neither pools a1
with a2 nor removes duplicate sealed compiler artifacts.

### Exact allocator bins in a target description

The `native_service_costs` selector may select exact `known_length_bins` for
`_Znam`/`_Znwm` and exact `allocation_lifetime_size_bins` for `_ZdaPv`/`_ZdlPv`.
Each selection declares `unit: seconds/call`, `bins: [{bytes, parameter}]`, and
`scope_assumption: {regime: fresh_process_repeated_allocate_free_batches,
transfer_basis: inferred}`. Every executed byte bin at that exact source site
must have a known independently measured parameter; its scoped counts must sum
to the full opaque-site count. Unknown lengths, lifetimes, rates, or partial
coverage retain the opaque call and null its cost. The allocator regime cannot
cover bulk copies or other ABIs. This explicitly inferred state transfer does
not establish physical cache state, page faults, or payload initialization cost.

### Bind services without modifying a running calibration source

The separate public module command derives a fresh description and pins the
complete counted characterization plus typed service records:

```sh
python3 -m swdb.cpu_service_binding --records "$SWDB_RECORDS" \
  --target-description mbit10.cpu.lanl20261006a2.v2.t1 \
  --characterization bfs.kron-g16.t1.characterization.a1 \
  --calibration mbit10.cpu.lanl20261006.service.clock.a1 \
  --id mbit10.cpu.lanl20261006.services.bfs.t1.a1 --format json
```

Repeat `--calibration` for additional independently measured groups. Fixture
inputs require `--fixture`. Existing descriptions and measurements remain
byte-identical. Compiler/C/C++ library mismatches and unproven allocator-control
absence produce null parameters with explicit reasons; the original measured
trials remain in their dependency records. Consumption requires the pinned
characterization hash in the model context, so another workload cannot silently
inherit the original context admission. This binding contributes no application
timing or error-band evidence.

### Conditional logical memory service

`memory_service_scenario` selects `scenario: resident_serial_constructed_requests`,
`transfer_basis: inferred`, `object_scope: logical_requests_and_bounded_referent_views`,
`domain: host`, `worker_scope: serial_T1`, and the exact `characterization_sha256`.
Its `requests` list maps each executed `{update_kind, element_bytes}` to a
`seconds/request` parameter. All known scoped logical requests must sum to the
retained useful-byte count; every executed cell needs its own supported cost.
Missing costs preserve the known compute bound and null the total. Partial
allocation-relative unions do not become cache-residency or page-fault evidence:
the model retains unknown object and bounded-view facts and supplies a conditional
resident scenario only. It covers no opaque callee or separate first-touch cost.
The model composes as a mechanism bound with compute, avoiding a second additive
charge for the same constructed instructions. Native rates are pending independent
counted service/driver and elapsed receipts; the public hand fixtures are reported
contracts only.

### Preregistered clock a2 control refresh

The historical `e71ed828` clock record retains its original bytes and measured
trials. It declares no allocator/interposer environment scope, so the fresh
binding path leaves its interposer compatibility unknown. Clock a2 repeats the
same `CpuServiceWork.h`/timer/count helper, six 32/64/96 service/driver proof
points, seven alternating paired trials, 134217728-event cap, and 0.05s minimum
for both gross and driver durations. It adds only an explicit actual MALLOC_/
GLIBC/LD_PRELOAD/LD_AUDIT/library-search snapshot with null absence semantics.
The newly captured controls are not backfilled into the earlier record. Nonnull
interposers remain unsupported for transfer until their execution scope is proven.
The library-search paths are retained, while binding compares actual critical
C/C++ library hashes; differing unused search paths do not establish a mismatch.

Both sockets must be idle for this native elapsed refresh. Use a clean immutable
Git checkout and a new external raw directory; all earlier raw directories stay
preserved. The named socket lease is still verified from live OS/lease state.

```sh
python3 -m swdb cpu-service-calibrate --records "$SWDB_RAW_RECORDS" \
  --machine mbit10 --lane mbit10-evaluation-node0 \
  --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_SERVICE_CLOCK_A2_RAW" \
  --repetitions 7 --min-trial-s .05 --max-wall-s 600 --format json
python3 -m swdb import-cpu-service-calibration --records "$SWDB_RAW_RECORDS" \
  --receipt "$SWDB_SERVICE_CLOCK_A2_RAW/receipt.json" \
  --id mbit10.cpu.lanl20261006.service.clock.a2 --format json
python3 -m swdb validate --records "$SWDB_RAW_RECORDS"
```

Use a 900s outer containment timeout and retain the runner's process-group signal
cleanup. Export only the typed compact record and receipt metadata through Git;
this refresh remains independent service calibration, not application accuracy.

### Preregistered independent memory request cells

The separate `python3 -m swdb.cpu_memory_calibration` runner constructs twenty
cells: dependent permuted-ring reads, sequential volatile writes, uncontended
sequentially consistent add, and deterministic compare-and-swap success/failure,
each at 4B/8B and 32KiB/8MiB data footprints. A stable `service_memory32` or
`service_memory64` wrapper encloses the same typed body in the count and timing
programs. Forty separate public count points cover both widths and every primitive
at n=3/5 with service/driver invocation; the driver has zero source requests, and
every service has exactly n requests of its declared update kind and width. Both
source-normalized operation inventories are retained. O3 IR is retained and its
volatile-load/store, add and compare-and-swap lowering must be checked independently.

The timing process prepares/touches buffers and performs an untimed warm-up.
Each measured batch visits the complete requested data footprint; CAS success
uses each prepared zero slot once and checks its observed success count, while
failure checks zero successes. No concurrent worker modifies the constructed
objects. The conditional-loop/index driver is separately timed and subtracted;
negative or unresolved residuals remain unknown. The subtraction is effective
constructed work, not an isolated physical instruction latency. Shape/dependence,
residency, and outcome transfer to an application remain explicitly inferred;
this runner provides no first-touch/page-fault or full-allocation evidence.

Budgets are seven alternating pairs with gross duration >=0.05s, at most 900s
inner wall time, 134217728 requests per trial, <=8MiB data plus <=8MiB permutation
arrays, 64MiB counted-build artifacts, and separate 25MiB timed data. All partial
sealed artifacts remain after failure. The named native socket lease, immutable
Git source, LLVM22 compiler, actual C/C++ libraries, and explicit interposer controls
are required. Keep the other socket idle for elapsed collection. Count-only proof
may be dispatched separately with a new raw ID; it supplies no elapsed evidence.

```sh
python3 -m swdb.cpu_memory_calibration --records "$SWDB_RAW_RECORDS" \
  --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_MEMORY_RAW" --repetitions 7 --min-trial-s .05 --max-wall-s 900
```

Use 1200s outer containment. Add `--count-only --max-wall-s 600` for a separate
forty-point proof. Native dispatch remains gated on the tested full-width proof,
complete native receipt/import validation, and a clean source tip. No native rates
or application accuracy are established by the local reported hand fixtures.


The separate byte-read follow-up is preregistered because the actual g16/T1
inventory contains executed 1B read requests. Use only `--operation read
--element-bytes 1 --footprint-bytes 256`; the runner rejects larger byte rings or
other byte primitives. An 8-bit index follows one complete 256-element permuted
cycle, verified before timing; every timed batch retains its verified cycle extent.
Four independent n=3/5 service/driver count points establish 1B logical reads,
without widening to 4B or claiming a 32KiB/8MiB working set. Its scope is
`fixed_small_byte_read_constructed_requests`; application locality transfer is
inferred and the physical cache level remains unverified. O3 retention checks the
separate `service_memory8` volatile i8 read. No byte-write/RMW/CAS rate is supplied.

The twenty-cell primary and one-cell byte follow-up use separate raw receipts and
are never pooled. Native import validates the complete selected typed count
matrix, source/observer/compiler/runtime hashes, optimized primitive retention,
full-footprint workloads, alternating orders and deterministic CAS outcomes.
Every native gross duration must resolve >=0.05s; paired driver values and all
negative residuals are preserved, with unresolved service parameters null.
The forty-point primary public proof and four-point byte proof pass on the local
LLVM22 toolchain; these are reported portable proofs, not native elapsed evidence.

```sh
python3 -m swdb import-cpu-service-calibration --records "$SWDB_RAW_RECORDS" \
  --receipt "$SWDB_MEMORY_RAW/receipt.json" \
  --id mbit10.cpu.lanl20261006.service.memory.a1 --format json
python3 -m swdb.cpu_memory_calibration --records "$SWDB_RAW_RECORDS" \
  --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --output "$SWDB_BYTE_READ_RAW" --operation read --element-bytes 1 \
  --footprint-bytes 256 --repetitions 7 --min-trial-s .05 --max-wall-s 600
python3 -m swdb import-cpu-service-calibration --records "$SWDB_RAW_RECORDS" \
  --receipt "$SWDB_BYTE_READ_RAW/receipt.json" \
  --id mbit10.cpu.lanl20261006.service.byte-read.a1 --format json
python3 -m swdb validate --records "$SWDB_RAW_RECORDS"
```

Keep the other socket idle throughout both elapsed commands. Use separate 1200s
and 900s outer containment timeouts, preserve process-group signal cleanup, and
retain raw count/build/timing artifacts remotely. Export typed calibration records
and compact receipt/context/trial metadata through Git; do not export raw IR,
binaries or addresses. Neither native cell establishes application accuracy.

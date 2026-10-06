# Native CPU calibration

Created: 2026-10-06 ET. Ticket 07; raw results are not accuracy validation.

`cpu-calibrate` builds a native C++17 timer and counts its shared compute functions
separately with the LLVM 22 source-normalized characterizer. The timer has no LLVM
counting instrumentation. Import creates a distinct target description for each T;
all bandwidth and compute rates are aggregate work divided by one wall interval.

```sh
python3 -m swdb cpu-calibrate --records records --output "$RUN/calibration" \
  --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --threads 1,2,4,8,16 --chains 1,2,4,8,16,32 \
  --working-set-bytes 268435456 --cache-bytes 8388608 \
  --repetitions 7 --min-trial-s .2 --max-wall-s 1800
python3 -m swdb import-cpu-calibration --records "$COPIED_RECORDS" \
  --receipt "$RUN/calibration/receipt.json" --id-prefix mbit10.cpu.RUN_ID
```

Enter the first command through the approved `socket_lane.sh`, after checking both
socket leases and the legacy lease, load, memory, source commit and disk. The parent
agent owns that dispatch. Native mode verifies the registered host and live lease,
NUMA affinity and bind policy; workers pin to separate physical cores and first-touch
their partition. It requires a clean commit, at least 20 GiB free, a large footprint
at least 8 times the live kernel-reported LLC, and a smaller cache footprint.
Unavailable governor/turbo files are recorded as null. No system settings change.

The default matrix includes stream read/write, single-valued and offset-defined
fixed-fanout-16 ranged indirect reads, data-dependent merge, warm cache stream,
single cold cache stream, and 1–32 independent pointer chains. Pointer nodes are
64 bytes apart but contribute **8 useful bytes/load**. Indirect payload bytes and
index/offset helper bytes are separate; elapsed includes helper work. Merge counts
executed head reads and output writes, not just unique input footprint. For N
merged outputs, N−1 compare/select steps each read two heads, reread the selected
head and write it; the last tail element reads/writes once: `4*N−2` source accesses
per worker/pass, 4 useful bytes each. Optimized reuse of a loaded head does not
change the source-element convention. Checksum/control bookkeeping is excluded
from the payload numerator. Ranged offsets are loaded once into begin/end values
per row, retaining two 8-byte offset elements plus 16 4-byte indices as helpers. Stream
counts one 4-byte read and one 4-byte write per element. A compiler-only pass fence
retains repeated stream/merge stores; it emits no hardware memory fence.

Each cell pilots complete partition traversals, freezes its pass count, and retains
all elapsed trials, checksums and balanced per-worker work. The cold cache group
uses exactly one pass after an untimed 3×LLC eviction (capped at 128 MiB), so it is
exempt from the minimum-duration target; repeating warm passes would corrupt its
cache-state interpretation. Eviction is a construction, not counter proof of the
serving cache level. Warm-cache rate is distinct from large-footprint bandwidth.
Cache capacity is kernel-reported; footprint, level, sharing and access shape
remain attached to the rate. Cold does not mean page faults or measured bus traffic.

The integer, FP, branch and uncontended per-worker atomic kernels use the same
`CpuWork.h` for the timer and separate counting driver. Three independent count
points (32,64,96 iterations) verify `a*n+b`; work over T workers is
`a*sum(worker_iterations)+b*T`. Compiler optimization may vectorize, fuse or convert
branches: these are **effective constructed-work rates**, not physical issue or
retired instruction rates. FMA follows the characterizer's two-FP-op convention.
Counting receipts, coefficients, validation points and source hashes are retained.

Dependent effective latency is C=1 elapsed divided by completed loads per worker.
The full chain curve retains inferred `rate/thread × dependent seconds/load`;
`effective_requests_per_thread` uses the median of the last three C points only
when their median rates span at most 15%, their elapsed spread is at most 25%, and
the balanced-worker/equal-footprint premise holds. Otherwise it stays unknown.
The criterion, points and failed premises remain in the description. A plateau
under this constructed work does not establish physical MSHR capacity. Model transfer from
this reference latency is an assumption. Every parameter retains its basis and
source. Per-trial elapsed/rate spread stays in `extensions.cpu_calibration`.
Shape-specific bandwidth rates stay there until a model explicitly consumes them.

Caps: T≤16; C≤32; 3–11 repetitions; active large footprint≤512 MiB;
cache footprint≤16 MiB; constructed resident storage≤1.5 GiB; raw output≤50 MiB;
wall budget≤1800 seconds. Timeout terminates the subprocess group. Partial trials
stay in the external folder; a failed run yields no importable complete receipt.
No address streams or raw output enter Git. Cell order is recorded in the receipt;
series are collected consecutively, so retained start/end load and spread expose
only some drift. A second lane must be a separately identified run/context.

For a small portable contract check, add `--fixture` and small footprints. Fixture
rates import only with explicit `--fixture` and carry basis `reported`; relabeling
those results as native measured evidence is rejected. After a real run, import
into copied records, validate them, and rerun the T=1 analytic fixture. Verify the
estimate's `target_description_sha256` against the canonical description digest.
A fixture rerun proves immutable hash binding, not a CPU error band.

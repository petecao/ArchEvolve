# Native CPU calibration

Created: 2026-10-06 ET. Updated: 2026-10-09 23:10 ET (code review: checkout commit,
machine record, raw-output roots, measured rates the estimator does not use). Ticket 07;
raw results are not accuracy validation.

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

Since 2026-10-09 23:10 ET (code review):
- The receipt's `commit` and `dirty` come from `git -C <ArchEvolve checkout>`, whatever
  directory the command starts in. Before this fix they came from the caller's working
  directory, so a lane started from another checkout (such as Memacc's
  `socket_lane.sh` folder) recorded that checkout's commit.
- The context pins `machine_sha256`, the digest of the machine record it ran under.
- Raw output must be outside the Git checkout in every mode. Native output must be
  under `/data1/yanruj/EvolveSWDB_runs` or `/data/yanruj/EvolveSWDB_runs`.
- The other socket's lease and the legacy lease are still checked by the operator through
  `socket_lane.sh`. The runner verifies only its own lease.

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

Known gap (code review, 2026-10-09 23:10 ET): the spec asks for bandwidth per access type
in the description with basis `measured`. Only the stream rate is a mechanism parameter.
The measured single-valued indirect, ranged indirect and merge rates are kept only in
`extensions.cpu_calibration.series`, with no basis field, and no estimator model reads
them. Non-stream accesses are priced from the pointer-chase latency and the inferred
requests per thread. The merge cell's inputs also alternate strictly (`2i` against `2i+1`),
so it is a best case for branch prediction, not a general data-dependent merge.

Caps: T≤16; C≤128 (default sweep ends at32); 3–11 repetitions; active large footprint≤512 MiB;
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


The preregistered second run extends the pointer sweep to C=1,16,32,64,128 under
the same total footprint and unchanged plateau criterion. It uses a fresh run/version
and a900-second wall budget. The first run's unknown parameters remain unchanged;
no timings from different contexts are pooled. See the campaign's compact evidence
and chain-extension preregistration for the observed rationale.


The 2026-10-06 a1/a2 receipts' compute `footprint_bytes` field records the requested
working-set budget, not an allocated payload. Their integer/FP/branch functions
use scalar state; atomic uses one private 8-byte word per worker. That field was
never a compute-rate numerator or cache bound. Those immutable receipts and target
versions are preserved. New receipts retain `requested_working_set_bytes` and set
compute `footprint_bytes` to zero, or `8*T` for the atomic word; register/stack/runtime
allocation is outside this logical-payload field. Memory-kernel footprints keep
the declared partition budget and their explicit helper-byte scope.

After integrating the workload's fixed source-normalized-v2 pipeline, compare all
12 compute count points without rerunning native timings:

```sh
python3 scripts/mbit10/cpu_count_equivalence.py \
  --runtime "$COUNT_WORKTREE/swdb-project" \
  --source "$CALIBRATION_WORKTREE/swdb-project/swdb/native/CpuCount.cpp" \
  --records records \
  --previous .scratch/lanl-db-analytic-eval-2026-10-06/evidence/cpu-calibration-mbit10-20261006-a1.json \
  --output "$RUN/count-equivalence" \
  --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13
```

The counting runtime must be a clean version that exposes the public
`--counting-pipeline source-normalized-v2` seam. The shared header must match the
old counted/timed source hash. The helper runs only the 32/64/96-point public
characterizations, with a 900-second wall budget, per-point timeout, 50 MiB raw cap
and child-group cleanup. It retains original/new pipeline IDs/passes, coefficients,
validation points and characterization hashes. Original a1 pipeline identification
comes from its fixed source recipe when the earlier receipt omitted that field.
Identical coefficients establish this constructed-work numerator equivalence only;
changed coefficients require a new target version using unchanged native timings
and explicit lineage. Raw count outputs stay remote; only compact metadata enters Git.


Calibration imports now write `cpu_calibration` records and list their resolvable
IDs in `calibration_sources`. The typed record retains the receipt hash, native
backend/evidence class, exact compiler/source/lane context, balanced elapsed/work
trials, spread, compute-count proofs and inference premises. Its canonical content
identity and frozen protocol dependency hash make later metadata changes detectable.
Human-readable explanations remain in provenance and each parameter's `source`.

For an older immutable description whose calibration citation was explanatory text,
create a fresh binding instead of editing it:

```sh
python3 -m swdb bind-cpu-calibration --records "$COPIED_RECORDS" \
  --target-description mbit10.cpu.lanl20261006a2.t4 \
  --id-prefix mbit10.cpu.lanl20261006a2.v2 \
  --count-equivalence .scratch/lanl-db-analytic-eval-2026-10-06/evidence/cpu-count-equivalence-mbit10-20261006-a2.json
```

Repeat `--target-description` for other T values from the same intended version.
The new target version pins typed evidence and retains the original receipt and
canonical target hash as lineage. It preserves every native elapsed/work trial,
corrects the compute logical-footprint metadata with the original fields retained
in lineage, and applies the independently counted v2 numerators. A count-only proof
can cover another receipt only when shared source, compiler/architecture, old
validation points and coefficients match exactly; this never pools native timings.
Changed numerators recompute constructed-work rates from the unchanged trials in a
fresh version. Original a1/a2 descriptions stay unchanged. The public freeze must
resolve and pin the new calibration record; the ADR 0013 guard is retained.


The completed campaign's [bound-calibration receipt](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/bound-calibration-fixture-mbit10-20261006-a1.json)
pins the final corrected-v2 proof, all five fresh target versions, typed native
calibration records and the actual T1 stream fixture. Seven trials/cell retain
spread; native a1 and a2 contexts are not pooled. The a2 stream-only aggregate rate
and inferred effective requests per worker are:

| T | Useful stream GB/s (decimal) | Dependent seconds/load | Effective requests/thread (inferred) |
|---|---|---|---|
|1|15.0715|9.4149508e-8|10.5333|
|2|25.1918|8.8465306e-8|10.7836|
|4|36.1323|8.7040395e-8|11.3717|
|8|45.8879|8.7422160e-8|7.8826|
|16|58.0234|9.0175053e-8|4.2190|

Consume a target only with matching proven worker scope. The T1 fixture's canonical
target hash is `a5d6c34b6d1d4be0c90a3ade95f9941ae64c9b5e76270aa26889db8cf8a499d2`;
its estimate is `lanl.bound-v2.fixture.20261006.estimate`, labeled `contract_fixture`.
Use explicit `--counting-pipeline source-normalized-v2`, `--threads 1`, and matching
`fixture.stream.v1` ROI when repeating the 17-element public stream check. Freeze a
fresh protocol after Python/model changes; the current receipt pins the combined
`b5acc909` implementation bundle. Its known bounds verify binding, not a native CPU
error band. The T4 application reports preserve incomplete totals.

Warm/cold cache stream throughput cannot supply cache-resident dependent-load
latency, arbitrary store/RMW service or fresh-allocation first-touch cost. Additional
independent generic service measurements and declared residency scenarios need
fresh target versions; they belong to ticket 11.

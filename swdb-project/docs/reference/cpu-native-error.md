# Scoped native CPU error evidence

Created: 2026-10-06 ET. Updated: 2026-10-09 23:10 ET (code review of tickets 07/11).
Ticket 11 is resolved (2026-10-07 09:56 ET); the code-review changes are listed at the end.

The validation collector is a separate original GAPBS driver scope. It preserves
five advancing deterministic SourcePicker calls in one process, including their
allocator state, and retains all five printed `Trial Time` values. Original output
has a10µs quantum; each value carries a±5µs rounding interval. A separate fresh
`-v` process checks all five calls. Verification never runs between admitted timed
calls. Existing `evaluate`/`evaluate-pair` timing and selection continue unchanged.

Native collection requires a prior frozen estimated protocol, clean committed
source, a real named mbit10 socket lease, one pinned physical core, and the exact
counted LLVM22 compiler and loaded C/C++/libomp hashes. It reproduces the counted
OMP/KMP/GOMP and library-search environment. Missing historical runtime facts are
unsupported. Graph identity pins deterministic source/input/thread generation
plus observed nodes/edges/directedness; no CSR-content digest is claimed.

## Outcome-free T1 inventory first

The parent owns remote checkout synchronization, socket-lane dispatch and leases.
Run the following sequentially inside node0 with node1 idle. Choose a fresh raw
folder, copy canonical records there, and keep raw outputs remote. The registered
ROI is `gapbs.trial_lambda.v1`; BFS and BC are separate five-call characterizations.
The source tip must stay clean and immutable during this phase.

```sh
SWDB_CPU_RAW=/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-t1-counts-20261006-a1
SWDB_CPU_LLVM=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin
SWDB_CPU_OMP=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
mkdir -p "$SWDB_CPU_RAW"
cp -a records "$SWDB_CPU_RAW/records"
OMP_PROC_BIND=close OMP_PLACES=cores python3 -m swdb characterize \
  --records "$SWDB_CPU_RAW/records" --adapter registered-gapbs \
  --implementation gapbs-bfs-do --input kron-g16-k16 --threads 1 --trials 5 \
  --id bfs.kron-g16.t1.characterization.a1 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --run-library-path "$SWDB_CPU_OMP" --timeout-s 900 \
  --output "$SWDB_CPU_RAW/bfs-counted" --format json > "$SWDB_CPU_RAW/bfs-characterization.json"
OMP_PROC_BIND=close OMP_PLACES=cores python3 -m swdb characterize \
  --records "$SWDB_CPU_RAW/records" --adapter registered-gapbs \
  --implementation gapbs-bc-brandes --input kron-g16-k16 --threads 1 --trials 5 \
  --id bc.kron-g16.t1.characterization.a1 --llvm-bin "$SWDB_CPU_LLVM" \
  --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 \
  --run-library-path "$SWDB_CPU_OMP" --timeout-s 900 \
  --output "$SWDB_CPU_RAW/bc-counted" --format json > "$SWDB_CPU_RAW/bc-characterization.json"
```

This phase supplies count/context evidence only. Inspect exact executed call
sites, length/lifetime bins, request widths/update kinds, logical first-access
pages and unknown object volumes before choosing new independent calibration
cells. Unknown shapes stay unknown; a declared memory-service scenario may use
complete requests without inventing address shapes. Stream rates cannot become
dependent-load, allocator or page-service costs by renaming them.

## Timing after independent model/calibration freeze

Freeze a protocol with the selected target ID, input and exact counted run
arguments. It pins the entire Python estimator bundle and typed calibration
closure. Use the persisted protocol ID in this command; `--fixture` is forbidden
for actual evidence. Reuse the exact run-library path list from counting.

```sh
python3 -m swdb collect-cpu-native-validation --records "$SWDB_CPU_RAW/records" \
  --characterization bfs.kron-g16.t1.characterization.a1 \
  --estimate-protocol "$SWDB_CPU_PROTOCOL" \
  --id bfs.kron-g16.t1.native-validation.a1 --machine mbit10 \
  --lane mbit10-evaluation-node0 --llvm-bin "$SWDB_CPU_LLVM" \
  --run-library-path "$SWDB_CPU_OMP" --max-wall-s 900 \
  --output "$SWDB_CPU_RAW/bfs-native-validation" --format json
```

BC uses its own characterization and validation ID. The raw binary, logs and
trial outputs stay remote; only typed records and compact receipt metadata enter
Git. Historical GCC13/libgomp profiles and fresh-process evaluator candidates
retain explicit compiler/runtime/ROI/state/source-policy exclusions from this
LLVM22/libomp original-driver scope.

`freeze-cpu-error-band --estimate ID [--validation ID] --id ID` retains immutable
pair hashes and full per-region diagnostic bounds. A missing native validation or
required cost creates a `failed` record with null width. A known development width
is still unvalidated; a fixture width never becomes native confidence. A failed
or null width prohibits held-out timing. When supported, g17 requires
`--development-band ID` frozen before timing; it cannot widen that width after
observing the held-out outcome. Bands apply only to their expressly validated
source/kernel/workload/thread/target scope.

## Code-review changes (2026-10-09 23:10 ET)

**A held-out input must be unseen.** `collect-cpu-native-validation --development-band`
refuses an input that already has a `cpu_native_validation` record for the same
implementation, thread count and evidence kind, in any phase and under any band.
`validate-cpu-error-band` adds the missing reason `unobserved_heldout_input` when an
earlier timing of that input exists. This blocks two shortcuts: timing the same held-out
input again until it passes, and reusing an input whose outcome is already known
(for example BC g17) as "held-out" for a retuned model. Only `cpu_native_validation`
records are checked; other native timings of the same workload (profiles,
evaluations) are not.

**D25 arithmetic.** `three_state(ratio, width)` in `swdb/cpu_error_band.py` holds the rule:
the ratio interval is `log(ratio) ± 2 × width`; `estimated_gain` if the lower end is above
`log 1.05`, `estimated_no_gain` if the upper end is below it, otherwise `within_error`.
The public `verdict` uses it only for a validated native band. A reported fixture band
that passed held-out shows `error_band.fixture_verdict` (with the interval) so the rule
is tested through the public `estimate` command; `verdict` stays `within_error`.

**Large errors.** New bands use format `swdb.cpu-error-band.v2`. Each known error above
`log 1.25` gets a `large_errors` row: direction, the five largest predicted regions,
their limiting bounds and their share of the predicted seconds. This is forecast-only.
It never assigns observed error to regions, and per-region medians need not add up to the
whole-call median. `validate` recomputes the rows. The four v1 band records from
2026-10-07 are unchanged and carry no `large_errors`; their explanations are in the
ticket 11 evidence READMEs.

**Which description the band measures.** All four bands (BFS and BC, development and
held-out) pin `mbit10.cpu.lanl20261006.t1.services.v1`. When that description was bound,
its `memory_service_scenario` replaced the measured `streaming_bandwidth`,
`requests_in_flight_latency` and `cache_fit` mechanisms from ticket 07
(`swdb/cpu_service_binding.py`, the memory branch of `bind`). That scenario charges every
logical read the cost of a serial dependent random load over an 8 MiB footprint, and
its basis is `inferred`. It is more than 99.98% of each forecast. So the validated BFS
envelope (about 55×) says nothing about the measured ticket 07 bandwidth and concurrency
values. Those have never been checked against native timing.

**Paired estimates in CPU evaluations.** An ArchEvolve-mode CPU evaluation gets a numeric
paired estimate only when a matched estimate was saved beforehand for every source slot.
That means running `characterize --adapter registered-cpu --evaluation-request` and then
`estimate`, both before `evaluate`. Otherwise `paired_estimate.state` is `unavailable`,
with null seconds. Neither `evaluate` nor a campaign produces the estimate by itself.
Extensa-mode evaluations record only the `excluded` state, with no `analytic_pairing` stage
and no `context.analytic_evaluator_scope`. In an archived `unavailable` or `excluded`
state, `validate` refuses any seconds, kernel seconds, estimate or slots. The unused
`known` state was removed from the evaluation schema; no record used it.

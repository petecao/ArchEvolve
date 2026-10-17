# Eric's launcher, topology, ROI and baseline follow-up

This answers the four questions preceding the standalone Great Lakes run. The [source receipt](source-receipt.json) pins 20 relevant files to `e4fc4afdf894f295442cef3604667a469fab8e62`. The existing [validation workflow](../README.md) remains the owner of environment/build/input/provenance and correctness admission.

## 1. Launcher and actual DRAM topology

There is a [completed local 16K/four-core execution witness](historical-witness.json), with the [exact recorded command](historical-command.txt). It ran BFS scale20, one trial, using a 2GB smoke mapping and an instrumented `gem5.opt.ovl_base`. It reached the ROI exit with nonzero read/range instructions. Its exact historical runtime source/binary hash has not been reconstructed. It stopped before BFSVerifier. Treat it as a working launch/activity witness, with its explicit differences, rather than a correctness-verified execution of the untouched pin.

The runtime reports:

```
CH: 2, RA: 1, BG: 4, BA: 4, RO: 65536, CO: 1024
```

The included [ramulator.yaml](ramulator.yaml) is byte-identical to the pinned `ext/ramulator2/ramulator2/example_gem5_config.yaml`: `DDR4_8Gb_x8`, `DDR4_3200W`, `RoBaRaCoCh`, FRFCFS, AllBank refresh and controller queue32. **Keep YAML `channel: 1`, `rank: 1` with gem5 `--mem-channels 2`.** There are two gem5/Ramulator controller systems; the effective organization reported to MAA has two channels. Setting YAML channels to2 is a different, unreviewed configuration.

Thus `B=2×1×4×4=32`, `Smin=2×2×1=4`, and the slice family is `{4,8,16,32}`. Initial32 is a valid member. At32slices, there is one subslice/slice,64rows/slice,8burst entries/row and16,384 nominal burst-entry slots. That equality with the16K tile length is a reference coincidence, not a universal capacity constraint.

[launch_16k.sh](launch_16k.sh) provides a complete **reviewed command template** adapted to the stock four-core **16GB** API mapping and Josh's MAA-enabled CPU control. It preserves the historical cache/clock/prefetch settings and supplies `--env` explicitly to the guest. Both variants have the same8MB L3, CPU settings, MAA mapping and memory system. This isolates the software/offload treatment; it is not the authors' area-compensated CPU baseline, which gives BASE extra L3 capacity.

Use separate checkpoints per graph and binary, with fresh paths and a reviewed verification tick budget:

```sh
handoff=/path/to/ArchEvolve/docs/designs/dx100-reference-validation/eric-handoff
dx=/path/to/clean-pinned-DX100
gem5=$dx/build/X86/gem5.opt
binary=/path/to/fresh/bfs-gem5-dx100  # repeat separately for the CPU binary
graph=/path/to/hashed/kronecker18.sg
guest_env=/path/to/ArchEvolve/examples/dx100-reference-validation/guest.env
checkpoint=/path/to/fresh-checkpoint-directory
run=/path/to/fresh-run-directory
bash "$handoff/launch_16k.sh" checkpoint "$dx" "$gem5" "$binary" "$graph" "$checkpoint" "$checkpoint" "$guest_env"
# Set VERIFY_MAX_TICKS from the reviewed simulated verification budget.
bash "$handoff/launch_16k.sh" restore "$dx" "$gem5" "$binary" "$graph" "$run" "$checkpoint" "$guest_env"
```

The checkpoint phase uses AtomicSimpleCPU and stops at the guest's pre-ROI checkpoint. The restore phase uses X86O3CPU,4cores,3.2GHz,16GB,2memory channels,1MAA,16Ktiles and32initial slices. Preserve guest `OMP_NUM_THREADS=4`, `OMP_DYNAMIC=FALSE`, `OMP_PROC_BIND=false`; the outside-parallel-region `ROI started: 1 threads` message is not worker-count evidence. Bind and hash the compiler, actual binaries, Ramulator library, source, graph and effective config.ini through the existing workflow. The loader/library path may need a site-specific binding.

The raw pinned `run_gem5_all.py` is not a ready launcher: `add_command_run_MAA` starts with `return None`, and the scripts contain author-local paths. Its command-construction code is useful reference material, not proof that invoking that script launches a run.

## 2. Verification after ROI without modifying the pin

The stock `m5_exit` stops `benchCheckpoints` before `BenchmarkKernel` calls BFSVerifier. Stock `-v`, a zero host exit and `ROI End!!!` do not establish correctness. I have not found an already target-validated continuation wrapper for the untouched pin.

The supplied [continue_to_verifier.py](continue_to_verifier.py) implements a new continuation adapter while leaving the pinned BFS and simulator files unchanged:

1. It hooks `Simulation.benchCheckpoints` only within this config-wrapper process and delegates its initial checkpoint/run handling to the original function.
2. It requires the first event to be the zero-code ROI `m5_exit`.
3. Before resuming, it freezes exactly one complete explicit guest dump into `roi.stats.txt`. Source `Text::end()` flushes the output; incomplete or multiple windows are rejected.
4. It reads the actual registered read/range instruction counters, retaining their values and snapshot identities. It does not reset counters, issue an extra dump or fabricate absent statistics.
5. It resumes simulation within an explicit tick budget, also capped by the original remaining run budget. It requires a zero-code `exiting with last active thread context` event. Another ROI exit, timeout or failure is rejected.
6. It writes `exit-events.json`. Guest completion remains separate from the existing collector's requirement for exactly one `Verification: PASS` and no failure diagnostics.

This adapter has passed local mocked event/snapshot/collector tests; **its gem5 and Great Lakes execution remain pending**. Run the planned single-trial smoke first and retain the complete event chain. No target-validation claim is made for the new launcher.

## 3. Exact stats window and accelerator witness

For the single-trial pinned control flow with no periodic/work-event dumps, use the explicit dump **before** `m5_work_end`, `ROI End!!!` and `m5_exit`. In the observed historical run it is block0. The later exit dump is a different window:

| Historical block | simTicks | MAA cycles_TOTAL | indirect reads | range instructions |
|---|---:|---:|---:|---:|
| Explicit ROI, block0 |25,561,820,454|81,667,158|6,567|2,161|
| Exit, block1 |25,563,529,121|81,672,617|6,567|2,161|

Do not silently select the last dump. The new wrapper freezes the ROI first, while final stats can include verifier and shutdown work. It never resets the ROI snapshot.

For the accelerated BFS require **both** `system.maa.numInst_INDRD > 0` and `system.maa.numInst_RANGE > 0` in that ROI. Supplementary activity counters in the historical ROI include:

- `system.maa.numInst = 17903`;
- `system.maa.numInst_STRRD = 84`;
- `system.maa.I0_IND_NumInsts = 8644`;
- `system.maa.I0_IND_NumWordsInserted = 102973607`;
- `system.maa.I0_IND_NumUniqueCacheLineInserted = 34693292`.

`cycles_TOTAL`, a `TDStepMAA` entry log or frontiers alone do not prove offload. Small frontiers can take the CPU fallback. For the CPU control require zero read/range instructions, a passing verifier and the same bound graph/root/thread settings.

**Zero suppression matters:** these instruction counters have `statistics::nozero`. The stock text dump can omit them when idle, and the existing collector correctly treats missing counters as unresolved. The wrapper queries their registered `ScalarInfo.value` explicitly. It creates `roi.stats.explicit-counters.txt`, preserving every raw value and adding only an omitted counter that is actually registered and reads exactly zero. Missing registration, missing positive values and raw/live mismatches fail. The raw ROI snapshot and `roi-counter-values.json` retain this derivation and hashes.

For collection, bind `artifacts.stats` to `roi.stats.explicit-counters.txt`, `stats_block_index: 0`, and `artifacts.exit_events` to `exit-events.json`. Retain `roi.stats.txt` and the counter sidecar for review. Continue to bind full build, input and configuration receipts; the wrapper does not authenticate them or make an incomplete receipt acceptable.

## 4. CPU baseline convention

For **this first standalone pair**, use the existing workflow's **MAA enabled but idle** CPU control: identical CPU/cache/memory/MMIO/MAA configuration, stock CPU BFS binary without `-DMAA`, and zero read/range instructions within ROI. Initialization stays before the ROI. No separately modified CPU baseline is required for this convention. Do not reuse an accelerated-binary checkpoint for the baseline.

Source nuance: `DOBFS` does call `alloc_MAA/init_MAA`, but `alloc_MAA` sets pointers and registers address regions; it does not itself dereference the device. The region pseudo-ops guard device registration with `hasMAA()`. Thus the source calls alone do not prove that a no-MAA stock baseline is impossible. A no-accelerator baseline is a separate configuration requiring its own launch/build/correctness review and receipt. It should not replace the current MAA-idle comparison implicitly. I do not have a complete correctness-verified stock no-MAA comparison at this exact pin to present as established evidence.

The effective outstanding-packet settings are **32,768**, as Josh identified: `MAAConfig.py` overrides declared512 defaults with `max(512,2×instances×tile_elements)`. The historical config has32,768 too; that setting alone is not a source modification.

## Local verification and remaining target check

The [local validation receipt](local-validation.json) records wrapper/collector regression checks and the source-object audit. No Great Lakes login, build, scheduler submission or gem5 verification run was performed for this addition. The next acceptance event is one bounded baseline/DX100 smoke per graph that reaches the verifier, preserves the explicit ROI dump and passes both correctness and intended-path checks.

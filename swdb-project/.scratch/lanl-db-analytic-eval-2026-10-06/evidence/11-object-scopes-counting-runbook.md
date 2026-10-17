# Fresh native T1 bounded-object counting

Updated: 2026-10-06 20:23 ET. Source prerequisite only; no application timing or CPU cost claim.

Use a clean Git-synced checkout containing implementation `8bbb89076b767aae8aa8e894498eff38da140194` and the separately
coordinated09 primitive/source-proof tip, if included. Run in `swdb-project/`. Parent owns
source sync, records copy, socket leases and dispatch. Create a fresh output directory
and copy current authoritative records into its `records/` child before execution.
Keep all prior characterization IDs, output directories and historical record bytes intact.

The commands explicitly enable the additive object-scope observer. Five independent
registered source selections retain the exact `gapbs.trial_lambda.v1` boundary and
`source-normalized-v2` recipe. Whole-allocation facts and four-byte call-scoped ABI referent
views remain distinct; unknown object extents/unsupported lifetimes stay unknown.

```sh
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bfs-do --input kron-g16-k16 --threads 1 --trials 5 --object-scopes --counting-pipeline source-normalized-v2 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/counted --id bfs.kron-g16.t1.characterization.objects.a1 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bfs/characterization.json
```

```sh
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bc-brandes --input kron-g16-k16 --threads 1 --trials 5 --object-scopes --counting-pipeline source-normalized-v2 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/counted --id bc.kron-g16.t1.characterization.objects.a1 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-20261006-a1/bc/characterization.json
```

Then run `python3 -m swdb validate --records` with that exact records directory. Export only
new canonical YAML and compact metadata: source/binary/count/pipeline/runtime hashes, the
optional sealed object-scope contract, five per-trial request partitions, named missing
facts, full allocation-relative versus view-relative unions and executed call sizes.
Keep raw LLVM IR, binaries and source stdout on mbit10; no pointer/address stream export.
Verify `full_allocation_requests + bounded_view_requests + unresolved_requests` equals
executed requests whenever all are known; unresolved equals `unknown_object_requests`.
View-only evidence never supplies full allocation page/lifetime/residency facts.

The source commands are exact argument-list equivalents of the existing tested registered
T1 adapter, with a public-tested opt-in and fresh names. Their g16 outcomes remain pending
until parent dispatch and validation. Source hashes and portable evidence are in
[the public proof](11-bounded-object-scopes-public-proof.json).


## Prospective scale17 input

The new typed [kron-g17-k16 input](../../../records/inputs/kron-g17-k16.yaml) changes the
selected scale to 17 and retains degree 16, built-in Kronecker flags and pinned source seed
27491095. Its realized node/edge counts and density remain null. Source-generation admission
was tested through the public registered adapter and stopped at an intentionally unavailable
LLVM toolchain; no graph or application timing was collected. The g17 run argument lists
are `['-g','17','-k','16','-n','5']` for BFS and that list plus `['-i','1']` for BC.

Use fresh records/output folders and IDs for these executions. Parent combines the final
object observer and 09 primitive semantics before clean source sync and dispatch.

```sh
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bfs-do --input kron-g17-k16 --threads 1 --trials 5 --object-scopes --counting-pipeline source-normalized-v2 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/counted --id bfs.kron-g17.t1.characterization.objects.a1 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bfs/characterization.json
```

```sh
python3 -m swdb characterize --records /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/records --adapter registered-gapbs --implementation gapbs-bc-brandes --input kron-g17-k16 --threads 1 --trials 5 --object-scopes --counting-pipeline source-normalized-v2 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --run-library-path /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu --timeout-s 1800 --output /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/counted --id bc.kron-g17.t1.characterization.objects.a1 --format json > /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-object-counts-g17-20261006-a1/bc/characterization.json
```

Portable registration/validation evidence is in
[the prospective input proof](11-prospective-g17-input-proof.json). Actual g16/g17 BFS/BC
outcomes remain pending; this registration never substitutes source-derived requested
parameters for realized graph properties.

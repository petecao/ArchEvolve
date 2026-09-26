# DX100 serialized loader inputs

Updated: 2026-09-25 (Eastern Time)

Both pinned GAPBS loaders select serialized graphs by filename extension.
Unweighted BFS requires `.sg`; `.wsg` denotes weighted data, and `.sg32` or
`.sg64` enters the unsupported text-reader path. The registered format and
canonical adjacency remain the workload identity, independently of its name.

For a registered SG32 or SG64 representation with another suffix,
`dx100-execute` creates an evaluator-owned `.sg` alias under
`RUNS_DIR/dx100-loader-inputs/APPLICATION-SERIALIZED_SHA256.sg`. SG32 is selected
for DX100's loader and SG64 for upstream's loader. The existing registered
representation and native evaluation records are preserved. Unregistered
non-`.sg` inputs fail before checkpointing because their serialization contract
is unavailable.

`context.loader_input` retains the original representation, alias path/hash,
application, serialization, and creation/reuse provenance. A regular hardlink is
preferred; cross-filesystem fallback streams bounded chunks under the remaining
execution and storage budgets, verifies the completed bytes, and publishes
without replacing an existing alias. Partial copies are removed. The creating
execution charges a copied alias to its raw-storage budget; reuse allocates no
new copy. Every existing alias must be a regular, non-symlink file with the exact
recorded hash. No stale alias is repaired or overwritten silently.

The stable alias path/hash enters `execution_binding.loader_representation` and
the guest options. Per-attempt provenance distinguishes creation from reuse but
does not change checkpoint compatibility. Both the registered input and alias
are rehashed before detailed dispatch and after execution. A subsequent trial
can therefore reuse its exactly bound checkpoint without changing guest paths.
An input already named `.sg`, including the retained tiny a4 checkpoint input,
keeps its existing path and binding without an added alias field.

Public fixture tests establish identity retention, changed-alias rejection and
checkpoint reuse; bounded-copy tests establish time/storage refusal and cleanup.
These do not establish successful execution of a real simulated BFS.

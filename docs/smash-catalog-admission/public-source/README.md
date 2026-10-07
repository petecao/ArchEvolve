# Public SMASH software binding and next implementation obligations

The official [CMU-SAFARI/SMASH snapshot](https://github.com/CMU-SAFARI/SMASH/tree/70af92c09e6e36ee4fef80c926c9e56b79784bb9)
is bound to commit `70af92c09e6e36ee4fef80c926c9e56b79784bb9`. Its complete
35-entry Git tree and eleven selected source files are recorded in
[source-binding.json](source-binding.json), with Git blob and SHA-256 identities.
Those identities were independently rechecked during publication. No third-party
source snapshot, executable or matrix input is redistributed here.

The inspected bitmap header implements software indexing with CTZ. The SpMV
Makefile declares a native software build; its SIM hook functions require an
external zsim/sniper handler to populate BMU results. No such handler or BMU RTL
is bound by this inspected snapshot. This narrows implementation identity without
changing the catalog's assist-only paper interface.

The public consumer differs from the printed Algorithm 1 expression used in
our earlier conditional witness: it assigns the output, increments the column,
and transitions rows using a strict greater-than boundary. Actual accumulation
and row-end behavior need separate source fixtures. The NZA builder and vector
warmup also require deterministic initialization plus an independent whole-array
oracle before this snapshot can be used as a numerical reference. No full kernel
was executed to infer an empirical failure.

A new primitive fixture reproduces passing zero to `__builtin_ctzl` before the
function checks its input. The reviewed minimal fix guards zero before CTZ,
returning zero under the existing convention and retaining the nonzero
expression. The fixture's original zero case fails under UBSan; guarded zero,
bit0, bit1, multi-bit and bit63 cases pass. A zero return does not mean bit0 is
present. Full-indexer zero reachability and correctness remain unproved.
[Guard binding](guard-binding.json) records the exact parent/corrected hashes;
[scope review](scope-review.json) separates this primitive fix from kernel and
hardware acceptance. The private exact-parent materializer is owner commit
`5cdeb6a4`, lane `smash_public_realization_2026_10_06`; no patch is silently
applied to public or live code.

The next software work is actual consumer/end-bound fixtures followed by
deterministic initialization and complete scalar-oracle integration. An actual
BMU experiment additionally needs authenticated handler/RTL, register/queue ABI,
physical input ownership and completion behavior. Existing catalog capabilities
and all prior scientific results are unchanged.

The [typed-mask source review](wordmask-review.md) records a subsequent minimal
three-site correction for narrow signed-int shifts on the 64-bit bitmap registers.
It composes with the zero guard and preserves the distinction between primitive
behavior and complete indexer/kernel correctness.

The [coherent repair batch](repair-batch/README.md) now supplies portable
exact-parent constructor/setter/reader/capacity transformations and new fixture
extraction. It admits only the tested complete same-ratio metadata domain;
NZA values and whole-kernel numerical correctness remain unbound.

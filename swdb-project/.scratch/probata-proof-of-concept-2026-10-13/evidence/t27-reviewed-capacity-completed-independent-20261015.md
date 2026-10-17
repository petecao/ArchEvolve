# Reviewed capacity acceptance — 2026-10-15 ET

The reviewed capacity profile at frozen `b9a34bbbcaa1670a7e4653f78e220da94af01a08`
finished naturally: **3/3 tests passed**, four actual framework records, exit 0.

| Case | Actual result | Ordinary / smoke |
| --- | --- | --- |
| WP32 | `proven` | 49/49 Valid; 11/11 smoke passed |
| WP33 | `not_proven/ghost_capacity` | 47/49 Valid; 11/11 smoke passed |
| CBMC32 | `proven`, explicit n=32 | No failed semantic property |
| CBMC33 | `not_proven/ghost_capacity`, explicit n=33 | `swdb.ghost_capacity` failed; no source counterexample |

WP establishes and preserves the added writer-history invariant for both 32 and
33. The previously timed-out memory-clear preservation and memory-domain call
precondition are Valid. WP33 retains two ordinary timeouts: named ghost capacity
and `dx_issuable`, whose definition includes the same `0 <= dx_count < DX_K`
bound. Neither negative adapter result claims a source counterexample or refutation.
The original source/code/contract/baseline/semantics/method/defines/ordinary-C/
naming pins match the failed WP32 record exactly; the new ordinary invariant is
the changed proof aid. All RTE, initializedness, cache, solver and smoke policies
remain required, with passed setup and actual launch.

The independent read-only final audit rehashed 40 references / 44 unique files
with no mismatch, checked the current method/lowerer, four expected outcomes,
new invariant goals, clean unchanged source and both guard exits. The inner guard
used 610.165 seconds and peaked at 2,934,345,728 bytes; the outer guard used
612.073 seconds and peaked at 2,984,677,376 bytes. There was no OOM or timeout.
Node0 generation575 ended naturally at 22:21:42 UTC. Exact record hashes, flags,
resource receipts and boundaries are in
[t27-reviewed-capacity-completed-independent-20261015.json](t27-reviewed-capacity-completed-independent-20261015.json).
The failed earlier `0e7f2327` record remains retained separately.

A separate **prospective** two-lane safe scheduling plan uses the historical717
per-case call times. Two existing `wp-safe -k` filters partition all11 expected
collector IDs into five/six cases with historical sums 2,976.605/2,975.596 seconds.
It changes no harness and launched no collector/compiler/job. Source/method and
lane selection remain the coordinator's responsibility; historical times are not
a fresh completion guarantee. Exact filters, IDs, weights and report hash are in
[t27-prospective-safe-two-shards-20261015.json](t27-prospective-safe-two-shards-20261015.json).

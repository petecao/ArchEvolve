# Fresh safe CPU proof admission — 2026-10-15 ET

The chosen single-CPU safe profile at exact frozen
`0e7f232762e4555aa9435a3a3622923fad8ee928` completed naturally: **1/1 passed**,
exit 0. The actual WP record is `proven`: **58/58 ordinary goals Valid and 19/19
smoke checks passed**, including 11 named initializedness and 9 RTE goals.
Record SHA-256: `dce81bb505f9198d57635c2292fc5a229d1ec01e3b003844858270fc1debd033`.

Independent read-only admission checked the exact CPU collector ID, all ordinary
and smoke outcomes, actual launch/current passed setup, mandatory RTE/init/cache/
solver/smoke flags, current semantics/method/lowerer pins, explicit entry premises,
clean unchanged source and natural lane/guard exits. It rehashed **864 physical
references / 865 files** without mismatch. The test call took 327.187 seconds;
the inner guard took 387.225 seconds and peaked at 3,991,732,224 bytes. The outer
guard took 389.256 seconds and peaked at 4,043,112,448 bytes; neither guard timed
out nor exceeded its 8 GiB process-tree cap. Node0 released naturally at 23:30:02 UTC.

The result is conditional on the pinned original entry-contract and recorded
unit-requires premises, including separation from generated ghost state. It does
not establish general CPU/device memory overlap or source-language/ACSL agreement.
The separately completed bounded CPU-write negative remains its source-qualified
replayed counterexample; the WP negative remains `not_proven` with its ordinary
write-probe precondition timed out. No record is upgraded across adapters.

Exact record, collector, flags, assumptions, hashes and resource receipts:
[t27-composed-safe-cpu-completed-independent-20261015.json](t27-composed-safe-cpu-completed-independent-20261015.json).
This admits only CPU1, **1/11** fresh safe units. The currently chosen remainder
is Arest4 plus B1(size, value_stream, value_range) and B2(three_reads, value_gather,
footprint); original A5 and B6 were superseded before launch. The coordinator
retains dispatch ownership; no new job or source change occurred during admission.

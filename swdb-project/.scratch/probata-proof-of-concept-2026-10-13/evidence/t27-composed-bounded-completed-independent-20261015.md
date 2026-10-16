# Current bounded completion and negative checkpoint — 2026-10-15 ET

The exact frozen `0e7f232762e4555aa9435a3a3622923fad8ee928` bounded profile
finished naturally: **35/35 cases passed**, exit 0. Its 24 retained CBMC records
contain 12 positive results and 12 replayed counterexamples at the intended
source hazard or postcondition. Positive records have no failed semantic
property and retain the expected failed `swdb_reach.end` completion sentinel;
that sentinel is not a failed source assertion. Every negative counterexample
matches a failed ordinary property and is marked replayed. Admission, native,
capacity-rejection and stale-pin cases remain included in the 35 test outcomes.

The independent read-only artifact audit verified 180 physical references / 204
unique files with no mismatch, current method/lowerer pins, clean unchanged source,
natural lane release and successful guards. The inner guard took 528.402 seconds
and peaked at 369,811,456 bytes; the outer guard took 530.426 seconds and peaked at
421,076,992 bytes. Neither timed out nor exceeded the 8 GiB process-tree cap.
Raw outputs stay on mbit10. Exact records, bounds, properties, hashes and resource
receipts are in
[t27-composed-bounded-completed-independent-20261015.json](t27-composed-bounded-completed-independent-20261015.json).
This closes the bounded profile at its explicit source and bounds; it does not
establish unbounded WP or general source-language/ACSL agreement.

At the separate negative profile's 22:06:35 UTC checkpoint, **5/13 cases** had
passed. All five remain `not_proven`, with their named ordinary read/size/write
precondition timed out. The first four retain their explicit failed smoke checks;
the CPU-write case has 64/65 ordinary goals Valid and all 21 smoke checks Valid.
The five-record audit verified 6,890 physical references / 938 files without
mismatch. This snapshot does not claim whole-profile completion, refutation or
any upgrade of a failed smoke result. Exact per-record outcomes are in
[t27-composed-negative-five-records-independent-20261015.json](t27-composed-negative-five-records-independent-20261015.json).

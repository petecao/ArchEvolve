# Current negative-profile closure — 2026-10-15 ET

The exact frozen `0e7f232762e4555aa9435a3a3622923fad8ee928` negative profile
finished naturally: **13/13 tests passed**, exit 0. Every actual WP record remains
`not_proven`, with exactly its intended ordinary hazard or original postcondition
timed out. There are **1,008/1,021 ordinary goals Valid**, 180 named initialization
and 189 RTE goals. All 13 required ordinary failures stay explicit; no source
counterexample or WP refutation is claimed.

Smoke outcomes are **283/318 passed**, with all35 failed smoke checks retained:
the first three early-read controls, early-size control and outside-footprint
query carry their original failed checks. Five records remain `vacuous_pass` and
eight `timeout`. The outside query retains its independent `ensures` timeout,
51/52 ordinary Valid, 17/18 smoke passed and exact failed
`typed_real_dxf_footprint_wp_smoke_dead_code_s20`. It is not upgraded to a theorem.

The final shortened store-frame control has 90/91 ordinary goals Valid and all 29
smoke checks passed. Its accepted hint leaves the ordinary
`maa_indirect_store_vector_requires_store_indices` obligation timed out. The
original source, contracts and RTE/initializedness policy remain unchanged.

The independent read-only closure verified the exact 13-case union, actual
verifier launches, current passed setup, required RTE/init/cache/solver/smoke flags,
current method/lowerer/semantics identities, unchanged exact source, natural lane
release and both guard exits. It rehashed **18,091 references / 1,084 files** without
mismatch. The inner guard took 8,012.081 seconds and peaked at 4,503,732,224 bytes;
the outer guard took 8,014.396 seconds and peaked at 4,555,112,448 bytes. There was
no OOM or timeout. Node1 generation 603 ended naturally at 23:26:43 UTC.

Exact records, ordinary and failed-smoke goal identities, physical hashes,
resource receipts and audit-script pin are in
[t27-composed-negative-completed-independent-20261015.json](t27-composed-negative-completed-independent-20261015.json).
Raw outputs remain on mbit10. These are proofs under pinned contract/semantics
premises, including explicit incoming typed windows; they do not establish
general source-language/ACSL agreement or CPU/device overlap. Ticket 27 stays
claimed until the fresh safe subsets complete.

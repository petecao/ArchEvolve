# Ticket 27 current matrix closure — 2026-10-15 ET

**62/62 cases passed across seven naturally completed, disjoint profiles**, with
52 unique framework records: 25 `proven`, 12 bounded `refuted` with C++ replay,
and 15 `not_proven`. These are actual verifier records and goal reports; pytest
success alone is not the proof evidence.

| Closed profile | Cases | Records | Actual outcome |
| --- | --- | --- | --- |
| Bounded/native/entry controls | 35 | 24 | 12 proven; 12 refuted with replay |
| Capacity | 3 | 4 | WP/CBMC 32 proven; both 33 not_proven/ghost_capacity |
| WP negatives | 13 | 13 | All not_proven; original ordinary failures retained |
| WP safe CPU | 1 | 1 | Proven |
| WP safe Arest | 4 | 4 | Proven |
| WP safe B1 | 3 | 3 | Proven |
| WP safe B2 | 3 | 3 | Proven |
| Total | **62** | **52** | **25 proven / 12 refuted / 15 not_proven** |

All 11 fresh safe WP units prove **792/792 ordinary goals**
and pass **252/252 smoke checks**, including
143 initialization and 141 RTE obligations. Each has an actual
launch and current passed setup; required RTE, initializedness, cache-none,
30-second serial prover portfolio and smoke policy remain unchanged.
The 13 negative WP records retain 1,008/1,021 ordinary Valid and 283/318 smoke
passed: all 35 failed smoke checks remain explicit. Outside-footprint is still
`not_proven/vacuous_pass`, with independent ensures timeout and failed generated
s20 branch smoke. No WP source refutation or counterexample is inferred.

The final inventory independently rehashes all 52 record files and final profile
reports/resources; it checks exact actual collector IDs against the committed
matrix/component selectors, uniqueness/coverage, no skipped/failed cases,
JUnit agreement, clean unchanged source, natural guards/leases and equality of
complete configured runtime provenance across all seven profiles. Individual
strict receipts separately rehash their referenced physical artifacts and read
actual goals/policy; their exact JSON hashes are pinned in the inventory.

All profiles use source `0e7f232762e4555aa9435a3a3622923fad8ee928` except capacity,
which uses reviewed `b9a34bbbcaa1670a7e4653f78e220da94af01a08`. Capacity adds one
ordinary, established/preserved stream-writer-history invariant; original
source/code/contract/semantics/method/C pins and production/runtime bytes match
`0e7f2327`. The earlier failed capacity 32 and historical `717` safe run remain historical.
Configured compiler wrapper, actual driver/parser and header identity are
retained; native link/transitive DSO closure is outside this identity boundary.

Acceptance uses Yan-Ru's approved CBMC replacement for SAW, paired with WP and
C++ replay. F6 makes register overlap a hazard, so the adopted wait scope is tile
producer transitivity plus register-write holding; no unsupported register
producer wait theorem is claimed. Qualified typed input windows, disjoint
ordinary/ghost storage and library call contracts remain explicit premises.
CPU/device footprint-overlap expansion (28), general C++/ACSL/C-stub agreement
(29), Rocq reduction discharge (43), and promotion review (59) remain separate.
The reduction remains an assumption.

[Complete inventory, exact source/runtime pins, records, resources and strict receipt hashes](t27-current-matrix-completed-independent-20261015.json).
Raw directories and physical producer checkouts remain retained on mbit10; no
raw verifier outputs were copied into the repository.

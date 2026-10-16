# Fresh original float pair at the repaired source

Updated: 2026-10-15 ET. Exact evaluation source: `0e7f232762e4555aa9435a3a3622923fad8ee928`.
This closes the current float pair, while the complete original matrix remains running.

The safe row passes after 155.27 seconds: all 48 ordinary and five smoke goals
are Valid, including all 12 RTE initializedness goals. The seeded row is accepted
as not proven after 196.02 seconds: 47 ordinary Valid and the attributable
`swdb_float_unit_loop_invariant_2_established` timeout; all 12 initializedness
goals remain present. One smoke goal is Valid and four are failed smoke probes.
This is an open ordinary obligation, not a solver counterexample or proof of
an incorrect postcondition. The finite native seeded witness is separate evidence.

The original body and contract remain unchanged. The only float hint change is
the separately reviewed pair of ordinary loop invariants for initializedness of
`r.value` and `r.weight`; neither is a function precondition or an assumed input.
Both rows actually launch and pass setup with mandatory RTE, all initializedness,
smoke, no-cache and x86_64 flags. The first fresh `std_min_int` dependency row is
also accepted (five ordinary and two smoke Valid), without promoting later pending
model/caller rows to accepted results.

The immutable [compact snapshot](t24-current-float-pair-0e7f2327-20261015.json)
checks exact physical sources/Git blobs, original full fixture/seed/clauses/hints,
current method/translator/setup/naming pins, record/report/artifact hashes and
ordinary/smoke inventories. It has zero integrity errors and zero acceptance
blockers for its three completed rows. Raw solver artifacts remain on mbit10;
the full running matrix, lease resources and eventual cleanup are not finalized
by this snapshot. Historical `9b75f4a2` float failure receipts remain unchanged.

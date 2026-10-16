# Closed constructor and lifetime gluing duties

2026-10-16 ET. Source preparation; no formal execution or source admission.

The public `vector_reallocation_closed_lifetime.prepare/check` seam reconstructs
the complete reviewed closed no-growth source view, the original/qualified
constructor and destructor inverses, and every canonical target. The original
caller contract remains unchanged. `check_launch` always refuses admission.

Six independent check lemmas connect source-local facts to the private incoming
observer: automatic receiver entry, constructor frame projection, exact source
buffer identity/history, zero cleanup, positive constructor exit image, and
positive cleanup. Both positive goals retain the same full antecedent; neither
imports its sibling conclusion. Cleanup keeps the actual heap release followed
by automatic scope end, with the scalar captured before both transitions.

The buffer-history target uses the actual source prefix
`before = begin_automatic(entry,24,a)` and `receiver = fresh_id(entry)`.
It proves the next allocation identity was never issued in the incoming heap,
is distinct from the receiver, and survives the constructor's initial stores.
The incoming observer alone cannot establish this history fact.

Current complete constructor35, destructor11 and private-frame9 dependencies
are mandatory pending requirements, with exact canonical target hashes. The
module does not import an older result or create a proof record. Source/Typed
scalar/field/value/init correspondence, source allocator binding, complete
ordinary/RTE/init/frame/smoke evidence and task/hypothesis review remain open.

The explicit allocator/library TCB includes successful allocation, fresh valid
freeable output, incoming-memory framing, and correct release/lifetime effects.
Allocation success alone is insufficient. Full-TU screening and default
allocator spelling do not establish absence of separately linked replacements
or interposition. Any future source-facing method and record must name and pin
the complete model TCB. These mathematical duties do not prove native WP33
`freeable`, `fresh` or dangling predicates.

The public tests use the registered shared no-growth lowering fixture and
exercise packet contents plus cleanup, observer, dependency and extra-file
tampering. The isolated retained-parser harness records RED2 for the missing
module and final GREEN2 with all four tamper cases. It blocks process/native
execution and records zero attempts. Its historical first GREEN retained one
incorrect test expectation for the explicit positive-state name; that
expectation and the tamper mutation were corrected before final verification.
These controls do not execute a compiler or prove a mathematical target.

Both independent source review axes pass at module `ac631823…` and test
`fd873570…`. The 16-file, 126,265-byte canonical source packet is retained in
`inert-reviewed-working-source/`. Exact pins, control receipts and review
boundaries are in `../../evidence/t25-closed-lifetime-glue-preparation-20261016.json`,
`../../evidence/t25-closed-lifetime-glue-spec-review-20261016.md`, and
`../../evidence/t25-closed-lifetime-root-standards-review-20261016.json`.

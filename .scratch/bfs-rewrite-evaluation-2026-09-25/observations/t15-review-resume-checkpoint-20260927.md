# T15 independent review resume checkpoint

Updated: 2026-09-27 Eastern Time. Saved during the user's explicit stop-and-sync request.

The user subsequently approved the reviewed incremental T15 allocation of
48 hours / 96 GiB and similar necessary bounded recoveries. This supersedes the
historical proposal-only authorization hold. It does not waive scientific,
resource, provenance, serialization or failure-preservation requirements.
**No new T15 allocation clock, absolute start/end, admission or empirical execution
was started by this reviewer.**

The concrete allocation document passed independent review before that approval.
Its historical review receipt is preserved unchanged as
[t15-allocation-decision-revised-independent-review-20260927.json](t15-allocation-decision-revised-independent-review-20260927.json).
The old `not authorization` verdict records the review's timing; it is not a new
approval request or a revocation of the later user approval.

On resume, independently review the author's new T15 plan/controller and focused
tests before export or dispatch. No such implementation was supplied or reviewed
by this worker before the stop. Verify:

- Original T15 failures, 14,433 seconds / 22,482,972,672 bytes, and original expired
  deadlines remain immutable and visible, separately from the approved increment.
- Incremental 172,800 seconds = 3,600 preparation + 82,800 uniform + 82,800 Kronecker
  + 3,570 finalization + 30 scientific-supervisor cleanup. Fresh proof cleanup stays
  inside its existing at-most-600-second preparation envelope.
- Incremental 96 GiB includes 4 GiB overhead; the two series share at most 92 GiB,
  each capped at 60 GiB and the remaining aggregate less reserved overhead.
- T15 serializes after independently verified T16 terminal closure, including
  owned-process absence, settled cleanup, lease release and stable retained storage.
  Do not equate the current stop or a driver exit with verified closure.
- All unchanged 12 primary/diagnostic pairs remain required. First-pair feasibility
  is the first existing pair, not an extra attempt. The unproven 120-second profile
  collection limit remains a fail-stop condition without automatic retry/widening.
- Runtime-matching proof, exact source/model/compiler bindings, live capacity,
  126-GiB output-mount free-space requirement, separate build reserve and socket
  lease checks remain mandatory. Set concrete start/end only on the authorized
  resumed admission path; elapsed paused time does not create a running clock.

Independent review work owned at stop: this checkpoint and the preserved revised
allocation review receipt. The decision document and prospective implementation
belong to the author/root. No source files, runtime checkout, remote evidence,
provider submission or scientific job were changed by this reviewer during this
closeout. T16 interruption closure review, if requested by root, is read-only
closeout work and is recorded separately.

## Stop verification — 2026-09-27 09:44 ET

The [independent T16 stop readback](t16-user-stop-independent-20260927.json)
verified physical quiescence twice: 694 absent identities and only the exact
launching pane as a zero-RSS zombie; node1 lease generation451 is released.
Retained raw plus dispatch storage is stable at619,712,512 bytes. The wrapper
exited1 at09:43:34.951657947 ET. However, strict cleanup validation **failed with
outstanding reservations**. Original driver and ledger hashes remain unchanged.
Do not treat physical termination as a successful settled cleanup audit or as
satisfaction of the T15 serialization prerequisite. On resume, diagnose and handle
that preserved accounting failure prospectively before admission; this checkpoint
does not authorize rewriting old evidence or restarting an attempt.

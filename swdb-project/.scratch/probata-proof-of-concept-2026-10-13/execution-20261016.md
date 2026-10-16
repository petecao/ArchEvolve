# Tickets 25 and 28 — active execution

Updated: 2026-10-16 ET.

User explicitly resumed tickets 25 and 28 with implementation, tests, reviews,
commits, pushes to `yanrujhou_main`, and mbit10 evaluation authorized. The saved
pause remains historical. External Claude Code owns ticket 7; its changes,
runtime slots, and lease ownership must be preserved.

Baseline: `c978393b119a3614229a37f0f2c8ca2a097c750b` on `yanrujhou_main`.

1. [x] Read governing rules, ticket acceptance criteria, and saved checkpoints;
   claim tickets 25 and 28.
2. [x] Repair/review the next public run packets and inspect
   current resources before admitting any compiler or verifier.
3. [ ] **In progress:** run fresh guarded evaluations through available socket lanes; repair
   failures without weakening contracts or using sibling proofs as premises.
4. [ ] Run appropriate focused checks and the full default suite; complete
   independent Standards and Spec reviews.
5. [ ] Reconcile acceptance criteria and tickets, commit only owned changes,
   push, verify remote source synchronization, and release owned resources.

## Ownership and assumptions

- Root coordinates source freezes, Git publication, actual tool admission,
  shared resource usage, and tracker reconciliation.
- `ticket25` owns ticket 25 source/preparation; `ticket28` owns ticket 28.
  `lane_coordination` performs read-only host/runtime preflight.
- Existing synthetic/public test seams are the agreed test boundaries under
  the user's autonomous delegation. New acceptance checks must observe public
  behavior and preserve every scientific criterion.
- Existing scoped proof results retain their original identities and limits.
  Tests, stand-ins, syntax checks, and mathematical sublemmas do not establish
  complete member-body, caller, hardware, or ticket acceptance.
- At most two mbit10 jobs, one per socket, only through current
  `socket_lane.sh`. Fresh leases and process state decide availability; neither
  lane is reserved by this document.
- Preserve uncommitted ticket 7 and unrelated cleanup scratch. Do not resurrect
  the retired integration branch or blindly execute historical tmp commands.

## Current evidence

- Ticket 25 copied-prefix diagnostic: all ten fresh leaves report proven at
  source `c978393b`, node 0 generation 603, 2026-10-16 12:59:03–13:00:31 ET.
  Outer guard: exit 0, 88.003 seconds, 790,986,752-byte peak RSS, no timeout/OOM.
  Independent cold audit is pending. This is conditional mathematical evidence;
  full grow61/reserve67/member/caller acceptance is not implied.
- Ticket 28 public V3 compiler/scripted-persistence workflow passed exactly one
  JUnit case, zero skips/failures/errors. Guard: exit 0, 52.661 seconds,
  2452.453 MiB peak RSS under a 4 GiB cap; source/runtime unchanged, private
  caches absent. One recovered inspection denial has no final failure or
  unconfirmed children. [Root result](evidence/t28-public-v3-root-execution-20261016.json).
- Reviewed source additions preserve unsupported caller admission. The new
  reserve-entry application raises the prospective caller inventory to 128;
  historical 127-target preparations keep their original identities. The
  initialized-register formal pair remains unexecuted pending source freeze.

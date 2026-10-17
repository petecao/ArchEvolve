# Capacity loop hint repair — 2026-10-15 ET

Status: compiler/annotation GREEN; independent review and actual capacity rerun pending.

Frozen `0e7f2327` capacity acceptance naturally exited 1 after the first WP32 case.
The record is `not_proven/memory_domain`: 45/47 ordinary goals Valid, 11/11
smoke checks passed, five initializedness and four RTE goals retained. The two
ordinary timeouts are the old memory-clear invariant preservation and the
stream-load memory-domain precondition. WP33 and the CBMC32/33 pair did not run.
Setup passed and the actual verifier retained required RTE/initialization/smoke
flags. The independent producer audit rehashed 13 references / 14 files without
mismatch. The worker guard used 397.421 seconds and peaked at 2,929,098,752 bytes;
there was no OOM or watchdog timeout. The source remained clean at `0e7f2327`.

The original unit enqueues only stream loads. Idle tile writers start at -1;
each stream call gives the destination writer kind `DX_STREAM_LOAD`, while
`dx_kept`/`dx_same_slot` preserve other live writers' kinds. The existing loop
hints do not expose that history when `DX_NT=40` selects the quantified form of
memory-clear. The repair adds one agent-authored ordinary invariant: every valid
tile writer has stream-load kind. It retains the old memory-clear/count/register
invariants, frame and variant. Source, entry preconditions, contracts, semantics,
assertions and runtime-error policy are unchanged. Establishment and preservation
of the added invariant remain obligations for WP; there is no assumed fact or
new axiom.

The compiler/merge control first failed on the missing invariant, then passed.
The final corpus-driven replay passed 1/1 in 0.63 seconds (guard 0.869 seconds,
peak 173,113,344 bytes), verifies explicit agent provenance and the original
stream call, and checks that annotation erasure reproduces ordinary C exactly.
This replay establishes annotation placement and erasure only. Actual WP32
success, WP33 ghost-capacity failure and CBMC32/33 agreement remain required.

Exact record, policy, physical hashes, raw RED/GREEN receipts and resource
boundaries: [compact evidence](t27-capacity-hint-repair-20261015.json).

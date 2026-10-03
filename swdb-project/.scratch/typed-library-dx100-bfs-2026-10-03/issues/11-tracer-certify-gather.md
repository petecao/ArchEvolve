# 11 — Tracer: certify the gather lowering and its setup intrinsics end to end

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05, 09
**Spec:** `../spec.md`

**What to build:** `swdb certify` certifies the `__dxc_gather` lowering and the setup intrinsics it needs on the Mac, through every layer: intrinsic record, library entry, lowering header, strict layer, certification command and certification record.

## Acceptance

- [ ] The strict layer (drop-in functional interface selected by include path, with the spec's build recipe) implements program-order effects, sentinel reads until a covering wait, per-thread ownership and the constant-load-into-uncovered-register hazard for every call these intrinsics make; the wait rules are recorded in the wait entry's completion field as assumed, owner Eric.
- [ ] The lowering header (C++11; canonical copy in the library folder; never placed in the vendored DX100 snapshot) has session begin (once per BFS call, after the existing DX100 setup), per-thread context allocation (8 tiles and 8 registers per thread under mutual exclusion, with the defensive thread-count assertion), constant load, wait (held read, fence, compiler barrier), the capacity static assertion, the gather lowering, and the instrumentation hooks (accelerated-chunk hook; compare-and-swap probe, empty unless the diagnostic define is set).
- [ ] Gather, session begin, per-thread context, constant load and wait each have an intrinsic record, a library entry, a differential-test driver and a certification record.
- [ ] `swdb certify ENTRY_ID [--runs-dir DIR]` runs each differential test against reference semantics with negative controls (dropped wait, read before wait, a second session begin, a context shared by two threads, a constant written to another thread's register); a control counts only if it builds and then fails a named check, including a differential mismatch, and an invalid control blocks certification.
- [ ] The Mac input form `--snapshot ID --patch FILE` rebuilds the tree from the vendored source and checks its manifest digest.
- [ ] The certification record kind is registered and documented; exit codes are 0, 1 and 2.

## Comments

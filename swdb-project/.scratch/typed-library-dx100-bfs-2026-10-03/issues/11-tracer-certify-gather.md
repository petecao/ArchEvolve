# 11 — Tracer: certify the gather lowering and its setup intrinsics end to end

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 05, 09
**Spec:** `../spec.md`

**What to build:** `swdb certify` certifies the `__dxc_gather` lowering and the setup intrinsics it needs on the Mac, through every layer: intrinsic record, library entry, lowering header, strict layer, certification command and certification record.

## Acceptance

- [x] The strict layer (drop-in functional interface selected by include path, with the spec's build recipe) implements program-order effects, sentinel reads until a covering wait, per-thread ownership and the constant-load-into-uncovered-register hazard for every call these intrinsics make; the wait rules are recorded in the wait entry's completion field as assumed, owner Eric.
- [x] The lowering header (C++11; canonical copy in the library folder; never placed in the vendored DX100 snapshot) has session begin (once per BFS call, after the existing DX100 setup), per-thread context allocation (8 tiles and 8 registers per thread under mutual exclusion, with the defensive thread-count assertion), constant load, wait (held read, fence, compiler barrier), the capacity static assertion, the gather lowering, and the instrumentation hooks (accelerated-chunk hook; compare-and-swap probe, empty unless the diagnostic define is set).
- [x] Gather, session begin, per-thread context, constant load and wait each have an intrinsic record, a library entry, a differential-test driver and a certification record.
- [x] `swdb certify ENTRY_ID [--runs-dir DIR]` runs each differential test against reference semantics with negative controls (dropped wait, read before wait, a second session begin, a context shared by two threads, a constant written to another thread's register); a control counts only if it builds and then fails a named check, including a differential mismatch, and an invalid control blocks certification.
- [x] The Mac input form `--snapshot ID --patch FILE` rebuilds the tree from the vendored source and checks its manifest digest.
- [x] The certification record kind is registered and documented; exit codes are 0, 1 and 2.

## Comments

Claimed by Codex strict-library/certification agent, 2026-10-03.

## Answer

Completed 2026-10-03 ET. Implemented the strict drop-in API, canonical C++11 lowering header, independent scalar reference semantics, real differential driver, source reconstruction, and public certification command. Each operation builds and executes both positive cases and its named controls. Gather/setup receipts: gather: `certification.68d181644cfb4ea38b10543fbea8ad7b`, session_begin: `certification.fe7b205ea86d4bb3b8ca4fde2df05c0d`, thread_context: `certification.0f0445fceae549398e79522fb4263ce5`, const_i32: `certification.3ce440da9ced4acb8315447ef9fd1fba`, wait: `certification.a246311c98194743b142f3dac3868cae`. Intrinsic status derives from these lowering records. Invalid controls (build failure, timeout, crash, or wrong named check) fail certification; the CLI uses exit codes 0, 1, and 2.

Canonical code: `library/dx100/dxc_lowering.hpp`; strict interface and no-op m5 calls: `library/dx100/strict/`; executable reference semantics: `library/dx100/reference.hpp`; driver: `library/dx100/drivers/differential.cc`; command: `swdb/certification.py`.

Evidence scope: strict functional certification on the Mac, basis `simulated`; no target timing or hardware-coherence proof. L3/L5 and ready-bit semantics remain assumptions owned by Eric pending target evidence. Focused verification: `python -m pytest -q tests/test_typed_certification.py` — 86 passed. Raw build/run/control outputs remain under `/private/tmp/swdb-typed-library-certification-20261003/` and are named by the certification records.

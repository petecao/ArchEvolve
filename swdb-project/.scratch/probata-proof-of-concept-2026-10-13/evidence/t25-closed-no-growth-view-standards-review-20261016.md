# Closed no-growth view: independent Standards review

Date: 2026-10-16 ET.

**CHANGES REQUESTED for one newly duplicated test seed. The production preparation module passes this Standards review within its expressly unsupported proof/launch scope.**

Reviewed physical production SHA256 `758092d5997274b29e22f2196c46af361b7cfdfd5c9eb83ee328ae6a877eb757`, test SHA256 `99be4b68a902bf278b5dbb9e25ce57e2eabf51a4be9dd41f7d24bf26956925dd`, the public pure harness and preparation evidence. Governing root/nested AGENTS, `.claude/rules/`, `tests/conftest.py` and the source-view/lifetime/private-frame dependencies were read. Branch is `yanrujhou_main`. Review used source/Git/AST/hash reads only; no test, production module, compiler, solver, native tool, SSH or runtime helper was executed for this review.

## Finding

**P2 — Consolidate the newly copied compiler seed through testkit.** `tests/test_vector_reallocation_closed_view.py:8–18` repeats the fixture source, exact contract and module-scoped `lowered_no_growth` fixture already defined in `tests/test_vector_reallocation_caller_view.py:7–17`. These two modules now maintain the same real Clang lowering setup separately, creating drift and repeated compiler work. `tests/conftest.py:3–6` documents that fixtures shared by several modules live in registered `tests/testkit/` modules, with plain builders for module seeds. Move the shared fixture/data to an appropriate testkit plugin or plain builder and have both modules use it. Preserve the public view seam and avoid test-module imports or fixture `__wrapped__` access. This applies to the new duplication; it does not request unrelated fixture cleanup.

## Production and test assessment

- The module offers a small `prepare/check/check_launch` interface. It composes the existing full source/call/CFG checks instead of adding an alternative parser or a source fallback. Exact occurrence checks and complete inverse edit restoration bind every source reduction.
- Model identity, original-TU substitution/provenance binding, original data requires and reserve requires remain checked. The constructor call and current body dependency remain explicit. Scalar capture precedes terminal cleanup; the otherwise dead fallback is removed only under the existing complete unconditional-return CFG certificate.
- Cleanup is recorded as an alternate pending source-to-VC interpretation with actual `Heap.release` and automatic scope end, freeable/frame/noescape duties and allocator/library TCB boundaries. No proof record is accepted, `source_typed_bridge_established` is false, and `check_launch` always refuses after checking. Source hashes alone grant no current body, Typed, lifetime or caller proof.
- The public tests inspect generated C/certificate/formal output and reject altered executable output, CFG, lifetime transition and original-TU provenance. They do not copy the transform or use private implementation helpers. Exact source fragments are material outputs of this deliberately narrow source projection. The retained-parser pure harness is labeled a replay/control, with explicit false proof/caller acceptance; it does not claim fresh compiler or native proof success.
- US spelling and Eastern `YYYY-MM-DD` dating conform. Dictionary certificates, frozen view data and regeneration checks follow neighboring modules. No new public dispatcher, adapter/setup hook or unrelated root change was introduced. Fowler/deep-module judgment supports this isolated seam; no abstraction redesign is required for this scoped addition.

A separate Spec review owns source semantics. This Standards result does not admit an actual closed-view proof, private cleanup theorem, native freeable predicate, runtime bridge or caller result. Author and root receive the fixture-only change request; the reviewed implementation is preserved.

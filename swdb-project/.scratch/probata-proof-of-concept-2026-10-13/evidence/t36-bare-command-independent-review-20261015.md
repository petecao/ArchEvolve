# Ticket 36 bare compiler command review

Updated: 2026-10-15 ET. Read-only scoped review of `/private/tmp/probata-resume-t36` versus `2033c174`; no tests, compiler, Frama-C, solver, provider, or remote jobs were invoked by the reviewer.

**PASS.** The only diff is `tests/test_proof_compiler_identity.py`; `swdb/` and `library/` have no diff from `2033c174`. Replacing the external stand-in's `os.execv` with `os.execvp` preserves the selected argument vector and process environment while correctly resolving a bare executable through PATH. Absolute executable selections continue to use their explicit paths. The multiple-frontend negative control's text replacement is updated to match the new spelling, preserving that injection seam.

The new control uses public `swdb lower`. Before prepending its isolated compiler-bin directory, it resolves the original selected executable to prevent wrapper recursion. It then selects bare `clang++` for the external stand-in and requires successful lowering of a scalar identity function. No SWDB collaborator is mocked. This is test-tool portability evidence, not a runtime-policy change or scientific theorem.

Both retained command receipts explicitly set `SWDB_FRAMA_C=none`. This scalar lowering path exercises clang AST generation and static lowering admissions, without invoking proof/typecheck APIs. The RED log reproduces the old `execv` bare-name launch failure: one failure in 1.06 s. The GREEN log records one pass in 1.15 s. RED guard metadata: exit 1, 1.518 s, peak 137,805,824 bytes; GREEN: exit 0, 1.619 s, peak 139,542,528 bytes. Neither timed out nor exhausted memory. These observations cover only the selected portability control; they do not reclassify the earlier broader setup batches or establish actual verifier acceptance.

No remaining blocker found. The coordinator still needs to confirm the final setup selection count after including this new control.

# 07 — Required ISA from intrinsics

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03, 05
**Spec:** `../spec.md`

**What to build:** an implementation's ISA needs come from the intrinsics it calls, a
build that doesn't enable them fails validation, and profiling refuses a machine that
can't run the code.

- [ ] The optional implementation field `uses_intrinsics`, whose IDs must resolve.
- [ ] The required ISA is the union of those intrinsics' extensions. Validation fails when the build flags don't enable it (an explicit `-m<extension>`, or a `-march` value the tool knows includes it). An unknown `-march` value fails with a message naming it. There is a passing and a failing fixture for each of the three cases.
- [ ] `swdb profile` refuses when the machine lists no flags or lacks a required extension. This check runs before the host check and before any build, so the tests run on the Mac (one fixture machine without `avx512f`, one with no flags).
- [ ] Documented in the v0.3 format doc.

## Comments

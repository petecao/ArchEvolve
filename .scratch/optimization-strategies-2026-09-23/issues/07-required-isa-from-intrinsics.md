# 07 — Required ISA from intrinsics

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 03, 05
**Spec:** `../spec.md`

**What to build:** an implementation's ISA needs come from the intrinsics it calls, a
build that doesn't enable them fails validation, and profiling refuses a machine that
can't run the code.

- [x] The optional implementation field `uses_intrinsics`, whose IDs must resolve.
- [x] The required ISA is the union of those intrinsics' extensions. Validation fails when the build flags don't enable it (an explicit `-m<extension>`, or a `-march` value the tool knows includes it). An unknown `-march` value fails with a message naming it. There is a passing and a failing fixture for each of the three cases.
- [x] `swdb profile` refuses when the machine lists no flags or lacks a required extension. This check runs before the host check and before any build, so the tests run on the Mac (one fixture machine without `avx512f`, one with no flags).
- [x] Documented in the v0.3 format doc.

## Comments

- 2026-09-23 (ET), code review: build flags are now read as GCC reads them. The last
  `-march` gives the starting set, and explicit `-m`/`-mno-` flags apply on top of it
  wherever they appear. `-mno-sse4`, `-mgeneral-regs-only`, and `-m32`/`-m16` are
  handled. `swdb profile` also refuses when the build flags enable extensions the machine
  lacks, even without intrinsics (auto-vectorization); there `-march=native` is accepted,
  because the build runs on the machine. Tests added in `tests/test_required_isa.py`.

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- New optional implementation field `uses_intrinsics` (IDs resolve through x-ref), stored
  in table `implementation_intrinsics`. Existing implementations need no edit.
- `swdb/isa.py` derives the required ISA as the union of the intrinsics'
  `isa_extensions`. What `build.flags` enables:
  - explicit `-m<ext>` flags, in compiler spelling (`-msse4.1` → `sse4_1`), with GCC's
    implications (`-mavx512f` implies AVX2 down to SSE);
  - `-mno-<ext>`;
  - `-march` values from a table (`x86-64` through `-v4`, and Intel and AMD cores
    including `icelake-server` for mbit10);
  - SSE and SSE2 always, as the x86-64 baseline.
  An unknown `-march` fails naming it, and so does `-march=native`, because it depends on
  the build host.
- Rule in `swdb/rules.py`: validation fails when the flags do not enable a required
  extension. The message names the intrinsic and the `-m` flag to add. Passing and
  failing fixtures cover the explicit flag, a known `-march`, and an unknown `-march`.
- `swdb profile` refuses right after loading the records, before the thread, host, and
  lane checks and before any build or run. It refuses when the machine lists no
  `cpu.flags` or lacks an extension. The tests run on the Mac with a fixture machine
  without AVX-512 and one without flags, both on a foreign hostname to prove the order.
- Documented in `docs/format-v0.3.md` (implementation section and changelog) and
  `docs/database.md`. Tests: `tests/test_required_isa.py` (13 tests).
- Decision: the check follows GCC's documented implications only. AVX-512F is not taken
  to imply FMA. Where the tool is unsure, it enables less, so a build may be refused but
  is never passed wrongly.

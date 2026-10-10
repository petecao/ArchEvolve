# 03 — Intrinsic records

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** intrinsics are recorded once, with their ISA needs and memory
behavior, and can be listed from the database.

- [x] The intrinsic record kind: `name` (exact C name), `isa_family`, `isa_extensions` (`lscpu` flag names), `header`, `memory_kind`, `address_shape` (or null), `element_bits`, `lanes`, and a vendor-reference source.
- [x] Vocabularies for ISA families (x86 now), ISA extensions, and intrinsic memory kinds. Adding Arm or RISC-V later needs only new vocab values.
- [x] IDs are the C name without leading underscores; a leading-underscore ID fails with the ID rule's message.
- [x] `swdb add` and `add --agent` work for intrinsics.
- [x] The seeds `mm512_i32gather_ps` (`_mm512_i32gather_ps`; x86, avx512f, gather) and `mm_prefetch` (`_mm_prefetch`; x86, sse, prefetch), checked against the Intel Intrinsics Guide.
- [x] `swdb build` includes intrinsics, so `swdb sql` can list them. Documented in the v0.3 format doc.
- [x] Each rule has a passing and a failing fixture.

## Comments

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- New record kind `intrinsic` (`schemas/intrinsic.schema.json`, folder `records/intrinsics/`).
  New vocabularies `isa_families` (x86), `isa_extensions` (`lscpu` names, from `sse` to the
  AVX-512 subsets), and `intrinsic_memory_kinds`. New provenance kind `vendor_reference`.
- Rules (`swdb/rules.py`):
  - The ID equals the C name without leading underscores. A leading-underscore ID fails
    with the ID pattern message.
  - An intrinsic has a `vendor_reference` provenance entry with a URI.
  - `memory_kind: none` goes with `address_shape: null`.
- Seeds: `mm512_i32gather_ps` (`_mm512_i32gather_ps`; x86, avx512f, gather,
  single_valued_indirect, 32 bits x 16 lanes, immintrin.h) and `mm_prefetch`
  (`_mm_prefetch`; x86, sse, prefetch, xmmintrin.h).
- Source check: the Intel Intrinsics Guide page could not be fetched automatically. It
  returned "Access Denied" and renders with JavaScript. The records cite the guide URL and
  say so, and the facts were checked against GCC's `avx512fintrin.h` and `xmmintrin.h`
  and the Rust `core::arch` docs, which reproduce Intel's text. **A person should confirm
  the two guide entries before setting `status: reviewed`.**
- `swdb build` fills `intrinsics`, `intrinsic_extensions`, and `machine_flags`
  (`docs/database.md`), so `swdb sql` lists intrinsics.
- Documented in `docs/format-v0.3.md` section 11. Tests: `tests/test_intrinsics.py`
  (10 tests).
- Decisions:
  - `address_shape` is null for `_mm_prefetch`: the instruction takes one address the
    caller computed, so the calling access pattern records the shape.
  - The memory-kind vocabulary adds `none` for non-memory intrinsics, so `memory_kind`
    can stay required.

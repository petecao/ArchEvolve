# 03 — Intrinsic records

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** intrinsics are recorded once, with their ISA needs and memory
behavior, and can be listed from the database.

- [ ] The intrinsic record kind: `name` (exact C name), `isa_family`, `isa_extensions` (`lscpu` flag names), `header`, `memory_kind`, `address_shape` (or null), `element_bits`, `lanes`, and a vendor-reference source.
- [ ] Vocabularies for ISA families (x86 now), ISA extensions, and intrinsic memory kinds. Adding Arm or RISC-V later needs only new vocab values.
- [ ] IDs are the C name without leading underscores; a leading-underscore ID fails with the ID rule's message.
- [ ] `swdb add` and `add --agent` work for intrinsics.
- [ ] The seeds `mm512_i32gather_ps` (`_mm512_i32gather_ps`; x86, avx512f, gather) and `mm_prefetch` (`_mm_prefetch`; x86, sse, prefetch), checked against the Intel Intrinsics Guide.
- [ ] `swdb build` includes intrinsics, so `swdb sql` can list them. Documented in the v0.3 format doc.
- [ ] Each rule has a passing and a failing fixture.

## Comments

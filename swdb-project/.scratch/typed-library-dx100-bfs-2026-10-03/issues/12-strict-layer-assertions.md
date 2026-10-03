# 12 — Strict layer: byte-offset, truncation and memory-region assertions

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11
**Spec:** `../spec.md`

**What to build:** The strict layer also catches 32-bit byte-offset overflow, silent tile truncation, and DX100 accesses outside the registered memory regions, from any thread.

## Acceptance

- [ ] Each assertion rejects its own negative control.
- [ ] Memory-region checks work in strict builds on every thread, because the strict layer defines the memory-region calls the vendored functional interface lacks.
- [ ] The certifications from ticket 11 still pass.

## Comments

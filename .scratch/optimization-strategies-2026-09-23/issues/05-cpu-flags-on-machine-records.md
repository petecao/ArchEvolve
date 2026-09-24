# 05 — CPU flags on machine records

Created: 2026-09-23
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** machine records list the CPU's ISA flags, so ISA checks have facts to
check against.

- [ ] `swdb capture-machine` stores the `lscpu` `Flags:` line as a sorted `cpu.flags` list. The saved mbit10 capture fixture already has the line; the parse test asserts `avx512f` is in the list.
- [ ] `cpu.flags` is optional in the schema; a rule requires it on machine records at 0.3. A 0.2 machine without flags still validates, and a 0.3 machine without them fails.
- [ ] mbit10 is recaptured read-only over ssh (load the `mbit10-runs` skill first), and its record is replaced at 0.3. The Answer states which AVX-512 flags are present.
- [ ] Documented in the v0.3 format doc.

## Comments

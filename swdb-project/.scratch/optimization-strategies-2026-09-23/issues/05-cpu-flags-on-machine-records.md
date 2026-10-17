# 05 — CPU flags on machine records

Created: 2026-09-23
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** machine records list the CPU's ISA flags, so ISA checks have facts to
check against.

- [x] `swdb capture-machine` stores the `lscpu` `Flags:` line as a sorted `cpu.flags` list. The saved mbit10 capture fixture already has the line; the parse test asserts `avx512f` is in the list.
- [x] `cpu.flags` is optional in the schema; a rule requires it on machine records at 0.3. A 0.2 machine without flags still validates, and a 0.3 machine without them fails.
- [x] mbit10 is recaptured read-only over ssh (load the `mbit10-runs` skill first), and its record is replaced at 0.3. The Answer states which AVX-512 flags are present.
- [x] Documented in the v0.3 format doc.

## Comments

## Answer

Resolved 2026-09-23 (ET) on branch `optimization-strategies`.

- `swdb capture-machine` parses the `lscpu` `Flags:` line into a sorted `cpu.flags` list and
  now writes records at 0.3 (`swdb/machine.py`). A capture with no `Flags:` line fails.
- `schemas/machine.schema.json`: `cpu.flags` is optional; an `if schema_version == "0.3"`
  clause requires it. A 0.2 machine without flags validates, and a 0.3 machine without
  them fails with "a machine record at format 0.3 lists its CPU's ISA flags".
- mbit10 was recaptured read-only over ssh on 2026-09-23 22:37 ET. No job was started,
  nothing was written on the host, and no lane was needed. `records/machines/mbit10.yaml`
  is now at 0.3 with 148 flags. Every other captured fact is unchanged. `created` is kept,
  and `updated` is 2026-09-23 (ET).
- AVX-512 flags present on mbit10: `avx512f`, `avx512cd`, `avx512bw`, `avx512dq`,
  `avx512vl`, `avx512ifma`, `avx512vbmi`, `avx512_vbmi2`, `avx512_vnni`, `avx512_bitalg`,
  `avx512_vpopcntdq`.
- The parse test asserts `avx512f` (and `sse`) is in the list. Documented in
  `docs/format-v0.3.md` (machine table and changelog).
- Existing issue, not fixed: `capture-machine` takes `created`/`updated` from the UTC
  capture date, which can be one day ahead of Eastern.

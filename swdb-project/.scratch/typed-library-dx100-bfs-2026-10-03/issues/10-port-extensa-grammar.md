# 10 — Port Extensa's predicate grammar into the library validator

Created: 2026-10-03
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 09
**Spec:** `../spec.md`

**What to build:** Formal halves written in Extensa's predicate grammar are parse-checked by `swdb validate`, without any MemAcc dependency.

## Acceptance

- [ ] MemAcc's L3 predicate-language grammar module is ported alone (not its runtime-probe grammar, and no Z3 or SMT modules), from the pinned MemAcc commit.
- [ ] Its parser library is vendored inside SWDB's package with its MIT license and version recorded.
- [ ] Each ported file has an SPDX header with the license from ticket 02 and a provenance header (MemAcc commit and path); a provenance list names every ported file.
- [ ] `swdb validate` parses every grammar predicate and refuses a proven formal label; it runs with only PyYAML and jsonschema installed.

## Comments

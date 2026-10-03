# 10 — Port Extensa's predicate grammar into the library validator

Created: 2026-10-03
**Type:** slice
**Status:** resolved
**Blocked by:** 02, 09
**Spec:** `../spec.md`

**What to build:** Formal halves written in Extensa's predicate grammar are parse-checked by `swdb validate`, without any MemAcc dependency.

## Acceptance

- [x] MemAcc's L3 predicate-language grammar module is ported alone (not its runtime-probe grammar, and no Z3 or SMT modules), from the pinned MemAcc commit.
- [x] Its parser library is vendored inside SWDB's package with its MIT license and version recorded.
- [x] Each ported file has an SPDX header with the license from ticket 02 and a provenance header (MemAcc commit and path); a provenance list names every ported file.
- [x] `swdb validate` parses every grammar predicate and refuses a proven formal label; it runs with only PyYAML and jsonschema installed.

## Comments

- 2026-10-03: Yan-Ru instructed proceeding as if Peter approves Apache-2.0 WITH LLVM-exception; Peter confirmation remains pending. Port pinned to MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76.

## Answer

The isolated Extensa predicate grammar is ported at af3d6d7f7a69a72facdc3b95b42e78c952f44a76 with vendored Lark 1.3.1 and license/provenance files. Yan-Ru explicitly authorized proceeding under assumed Peter approval on 2026-10-03; Peter confirmation remains ticket02.

Validation: current library/record validation passes379 records; focused library/strategy tests49passed; full suite and final two-axis review remain batch closeout gates.

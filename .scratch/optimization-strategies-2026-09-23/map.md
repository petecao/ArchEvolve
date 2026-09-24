# Map: Optimization strategies and intrinsics

Created: 2026-09-23
Updated: 2026-09-23
Spec: `spec.md` (ready-for-agent). Glossary: `CONTEXT.md`. Decision: ADR 0004.

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Accept format 0.3 (prefactor) | — | resolved |
| 02 | Packing, end to end | 01 | ready-for-agent |
| 03 | Intrinsic records | 01 | ready-for-agent |
| 04 | The other four seed strategies | 02, 03 | ready-for-agent |
| 05 | CPU flags on machine records | 01 | ready-for-agent |
| 06 | Implementations apply strategies | 04 | ready-for-agent |
| 07 | Required ISA from intrinsics | 03, 05 | ready-for-agent |

Frontier now: 01. After 01: 02, 03, 05 in parallel.

## Context pointers

(Append one line per resolved ticket: ticket number, date, where its result lives.)
- 01 (2026-09-23): envelope accepts 0.2 and 0.3; `docs/format-v0.3.md`; tests in `tests/test_format_versions.py`, `tests/test_format_doc.py`.

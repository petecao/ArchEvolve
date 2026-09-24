# Map: Optimization strategies and intrinsics

Created: 2026-09-23
Updated: 2026-09-23
Spec: `spec.md` (ready-for-agent). Glossary: `CONTEXT.md`. Decision: ADR 0004.

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Accept format 0.3 (prefactor) | — | resolved |
| 02 | Packing, end to end | 01 | resolved |
| 03 | Intrinsic records | 01 | resolved |
| 04 | The other four seed strategies | 02, 03 | resolved |
| 05 | CPU flags on machine records | 01 | resolved |
| 06 | Implementations apply strategies | 04 | ready-for-agent |
| 07 | Required ISA from intrinsics | 03, 05 | resolved |

Frontier now: 01. After 01: 02, 03, 05 in parallel.

## Context pointers

(Append one line per resolved ticket: ticket number, date, where its result lives.)
- 01 (2026-09-23): envelope accepts 0.2 and 0.3; `docs/format-v0.3.md`; tests in `tests/test_format_versions.py`, `tests/test_format_doc.py`.
- 05 (2026-09-23): `cpu.flags` in `swdb/machine.py` and `schemas/machine.schema.json`; mbit10 recaptured at 0.3 in `records/machines/mbit10.yaml`; tests in `tests/test_machine_capture.py`.
- 03 (2026-09-23): intrinsic kind in `schemas/intrinsic.schema.json`, rules in `swdb/rules.py`, seeds in `records/intrinsics/`; tests `tests/test_intrinsics.py`; format doc section 11.
- 02 (2026-09-23): strategy kind in `schemas/strategy.schema.json`, identity and legality in `swdb/strategy.py`, queries in `swdb/db.py`; seed `records/strategies/packing.yaml`; tests `tests/test_strategies.py`; format doc section 12, `docs/database.md` Queries.
- 04 (2026-09-23): effect kinds and loop/input targets in `schemas/strategy.schema.json` and `swdb/strategy.py`; loop/input queries in `swdb/db.py`; four seeds in `records/strategies/`; procedure `docs/adding-a-strategy.md`; tests `tests/test_strategy_kinds.py`.
- 07 (2026-09-23): required ISA in `swdb/isa.py` (rule in `swdb/rules.py`, profile refusal in `swdb/profile.py`); `uses_intrinsics` in `schemas/implementation.schema.json`; tests `tests/test_required_isa.py`.

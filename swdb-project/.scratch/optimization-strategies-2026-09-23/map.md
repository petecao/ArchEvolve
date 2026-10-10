# Map: Optimization strategies and intrinsics

Created: 2026-09-23
Updated: 2026-09-24
Spec: `spec.md` (ready-for-agent). Glossary: `GLOSSARY.md`. Decision: ADR 0004.

| # | Ticket | Blocked by | Status |
|---|---|---|---|
| 01 | Accept format 0.3 (prefactor) | — | resolved |
| 02 | Packing, end to end | 01 | resolved |
| 03 | Intrinsic records | 01 | resolved |
| 04 | The other four seed strategies | 02, 03 | resolved |
| 05 | CPU flags on machine records | 01 | resolved |
| 06 | Implementations apply strategies | 04 | resolved |
| 07 | Required ISA from intrinsics | 03, 05 | resolved |

All seven tickets resolved 2026-09-23/24 (ET) on branch `optimization-strategies`, merged
into `main`. Two code-review passes were addressed (ticket Comments on 02, 06, 07).

Evaluation (2026-09-24 00:18 ET): the full suite passes on the Mac (312 passed, 3 skipped)
and on mbit10 at commit 9c3d616 (313 passed, 2 skipped, including the lab-host profile
tests). The mbit10 run was inside socket lane node1 (lease generation 358, load 1.85 at
start). The other lane held a MemAcc job. It used system jsonschema 4.10.3 and pytest from
`/data1/yanruj/venvs/evolveswdb-test`. Raw output:
`/data1/yanruj/EvolveSWDB_runs/evolveswdb-optstrat-suite-20260924t040553z/`.

## Context pointers

(Append one line per resolved ticket: ticket number, date, where its result lives.)
- 01 (2026-09-23): envelope accepts 0.2 and 0.3; `docs/format-v0.3.md`; tests in `tests/test_format_versions.py`, `tests/test_format_doc.py`.
- 05 (2026-09-23): `cpu.flags` in `swdb/machine.py` and `schemas/machine.schema.json`; mbit10 recaptured at 0.3 in `records/machines/mbit10.yaml`; tests in `tests/test_machine_capture.py`.
- 03 (2026-09-23): intrinsic kind in `schemas/intrinsic.schema.json`, rules in `swdb/rules.py`, seeds in `records/intrinsics/`; tests `tests/test_intrinsics.py`; format doc section 11.
- 02 (2026-09-23): strategy kind in `schemas/strategy.schema.json`, identity and legality in `swdb/strategy.py`, queries in `swdb/db.py`; seed `records/strategies/packing.yaml`; tests `tests/test_strategies.py`; format doc section 12, `docs/database.md` Queries.
- 04 (2026-09-23): effect kinds and loop/input targets in `schemas/strategy.schema.json` and `swdb/strategy.py`; loop/input queries in `swdb/db.py`; four seeds in `records/strategies/`; procedure `docs/adding-a-strategy.md`; tests `tests/test_strategy_kinds.py`.
- 07 (2026-09-23): required ISA in `swdb/isa.py` (rule in `swdb/rules.py`, profile refusal in `swdb/profile.py`); `uses_intrinsics` in `schemas/implementation.schema.json`; tests `tests/test_required_isa.py`.
- 06 (2026-09-23): `applies` in `schemas/implementation.schema.json`, rules in `swdb/rules.py`, `--applies` query in `swdb/db.py` (`applying`); tests `tests/test_applies.py`.

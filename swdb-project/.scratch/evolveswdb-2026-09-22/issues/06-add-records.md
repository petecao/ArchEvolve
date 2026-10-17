# 06 — Adding records (`swdb add`)

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** 05
**Spec:** `../spec.md`

**What to build:** A person or an agent adds a record through the tool, and it lands in
the right place, validated, marked for review, and visible to the next query.

- [x] `swdb add <file>` validates the record, writes it to its canonical location (derived from its kind and ID), and rebuilds the database.
- [x] An invalid record or a duplicate ID is rejected, and nothing is written.
- [x] Records added by an agent carry `provenance.kind: agent_run` and `status: draft`.
- [x] Round trip: a record added through the tool shows up in the next `validate`, `build`, and query.

## Comments

## Answer

Resolved 2026-09-22.

- `swdb add <file> [--agent --agent-name NAME]` (`swdb/writer.py`): validates the whole
  folder as it would be afterwards, writes `<kind plural>/<id>.yaml`, rebuilds SQLite.
- Invalid record, cross-record error, or duplicate ID → exit 1, nothing written.
- `--agent` → `status: draft` plus an `agent_run` provenance entry.
- Round trip tested (`tests/test_add.py`): the added record appears in the next
  `validate`, `build`, `sql`, `implementations`, and `view`.
- One writer at a time per records folder (file lock).

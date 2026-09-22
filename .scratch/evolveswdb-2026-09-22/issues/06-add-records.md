# 06 — Adding records (`swdb add`)

Created: 2026-09-22
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 05
**Spec:** `../spec.md`

**What to build:** A person or an agent adds a record through the tool, and it lands in
the right place, validated, marked for review, and visible to the next query.

- [ ] `swdb add <file>` validates the record, writes it to its canonical location (derived from its kind and ID), and rebuilds the database.
- [ ] An invalid record or a duplicate ID is rejected, and nothing is written.
- [ ] Records added by an agent carry `provenance.kind: agent_run` and `status: draft`.
- [ ] Round trip: a record added through the tool shows up in the next `validate`, `build`, and query.

## Comments

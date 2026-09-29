# 07 — Audit of the provider event log

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02, 06
**Spec:** `../spec.md`

**What to build:** After every workspace session, SWDB audits the provider's event log (Codex JSON events,
Claude stream tool events) and fails the attempt, with a stored reason, when it finds a file
access outside the visible set, a command touching the login file, or a network command. If
ticket 02 found no Codex command wrapper, any outbound connection other than the model API
also fails the attempt.

## Acceptance

- [ ] Fixture sessions with scripted events fail with the right reason for each case, and a clean session passes.
- [ ] The event log is retained as a raw artifact and linked from the proposal.
- [ ] The audit result is recorded in the proposal's provider block.

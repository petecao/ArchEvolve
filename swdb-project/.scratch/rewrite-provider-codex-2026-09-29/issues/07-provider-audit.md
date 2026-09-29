# 07 — Audit of the provider event log

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** 02, 06
**Spec:** `../spec.md`

**What to build:** After every workspace session, SWDB audits the provider's event log (Codex JSON events,
Claude stream tool events) and fails the attempt, with a stored reason, when it finds a file
access outside the visible set, a command touching the login file, or a network command. If
ticket 02 found no Codex command wrapper, any outbound connection other than the model API
also fails the attempt.

## Acceptance

- [x] Fixture sessions with scripted events fail with the right reason for each case, and a clean session passes.
- [x] The event log is retained as a raw artifact and linked from the proposal.
- [x] The audit result is recorded in the proposal's provider block.

## Comments

2026-09-29: Claimed by provider_workspace agent for workspace derivation, diff, audit, and public fixture coverage.

## Answer

2026-09-29

Implemented `swdb/provider_audit.py`. It parses Codex command/file-change items and Claude tool-use events, checks absolute and relative file paths and shell working-directory changes, rejects login-file/provider-home touches, rejects network commands and forbidden tools, and incorporates the independent guard's network trace result. Unknown actionable tool types and malformed event lines fail closed. Claude `StructuredOutput` events are schema transport and are independently validated by the CLI adapter.

The audit runs on successful and exceptional workspace exits. Each attempt retains the full raw stdout event log with path, byte count, and SHA-256, plus `audit.json` and its result in both the attempt receipt and proposal provider block. A security audit failure takes precedence over a coincident provider-availability error, so it cannot refund the attempt as a mere usage limit. Provider-supplied `model_api` assertions cannot authorize connections.

Validation (2026-09-29): **40 passed** public workspace/audit fixture cases, followed by **8 passed** added focused cases. Both Codex and Claude streams cover clean actions, forbidden file reads, login touches, network commands, forbidden tools, malformed logs, forged network authorization, timeout retention, and the repair path. Tests assert public proposal/candidate/raw artifacts and do not call workspace or audit internals. Linux guard enforcement and real model API evidence are tracked by tickets 02, 08, and 10.

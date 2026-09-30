# 07 — Audit of the provider event log

Created: 2026-09-29 (Eastern Time)
Updated: 2026-09-29 (Eastern Time)
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

2026-09-29 (Eastern Time)

Implemented `swdb/provider_audit.py`. It parses Codex command/file-change items and Claude tool-use events, checks absolute and relative file paths and shell working-directory changes, rejects login-file/provider-home touches, rejects network commands and forbidden tools, and incorporates the independent guard's network trace result. Unknown actionable tool types and malformed event lines fail closed. Claude `StructuredOutput` events are schema transport and are independently validated by the CLI adapter.

The audit runs on successful and exceptional workspace exits. Each attempt retains the full raw stdout event log with path, byte count, and SHA-256, plus `audit.json` and its result in both the attempt receipt and proposal provider block. A security audit failure takes precedence over a coincident provider-availability error, so it cannot refund the attempt as a mere usage limit. Provider-supplied `model_api` assertions cannot authorize connections.

The parser audits direct commands and recursively parses explicit shell-wrapper bodies. It rejects unresolved command/file substitutions, delegated execution, and opaque inline interpreter programs. Claude Glob patterns and optional base paths are checked together; executable paths and attached/separate compiler file options are also checked against the workspace policy. Ordinary workspace scripts and synthetic binaries may run under the guard; auditing their invocation does not prove their source semantics.

Both real providers receive shared guidance to use direct editing tools for source changes and literal shell operands for workspace reads, builds, and synthetic runs, avoiding inline interpreters, loops, heredocs, delegation, and regex-based code transformations. This guidance does not waive or guarantee the audit.

Validation (2026-09-29 ET): the fresh local public workspace module passed **195 tests** in **396.70 seconds** after the parser fixes. A subsequent narrow run verifying guidance delivery through Codex arguments and Claude stdin, plus protected-input rejection, passed **14 tests** in **29.67 seconds**. The literal exit-status fix passed **42 focused public cases** in **83.03 seconds** on the Mac and **132.56 seconds** on Linux A7 at `c8a666f`. It permits printable literal fragments around numeric `$?` solely in echo/printf data, preserving refusals of path/glob fragments, other variables, substitutions and concatenated numeric-test arguments. Both event formats cover clean actions, forbidden file reads, login touches, network commands, forbidden tools, malformed logs, forged network authorization, timeout retention, and repair. Assertions use public proposal/candidate/raw artifacts rather than workspace or audit internals.

Linux A6 passed **222 guard/pins/workspace tests in 1428.56 seconds** at `4f5d152`. Its retained-log subprocess exposed a harmless Claude exit-status label refusal, corrected by the narrow fix and confirmed by A7. The official current-parser re-audit passes both historical toy logs and the Claude DX100 failure. The original Codex DX100 A1 attempt remains **failed** because its in-place `sed` regex transformation cannot be safely resolved; its historical receipt is unchanged and is not the current acceptance attempt. Fresh public DX100 A2 at `c8a666f` passes both original/current event audits and guards: Codex creates a candidate with independently passed source-0/3/8 native structural checks; Claude retains an OAuth-expired failure, with no candidate or BFS result. Details and raw identities are in [guarded provider evidence](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml) and tickets 02, 08 and 10. Final independent code review remains pending until the separate T17 work completes.

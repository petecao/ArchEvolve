# 07 — Audit of the provider event log

Created: 2026-09-29 (Eastern Time)
Updated: 2026-09-29 23:20 ET
**Type:** slice
**Status:** resolved
**Blocked by:** None
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

2026-09-29 21:02 ET: Reopened after the independent review reproduced outside
file operands hidden in inline AWK/SED programs, `find -exec`, an absolute `env`
wrapper, and compiler forwarding/time/ccache wrappers. These scripted-event
submissions passed the audit; they do not demonstrate a forbidden read under
Landlock. Parser repairs, focused public tests and fresh Linux/current-log checks
are required before closure.

2026-09-29 21:59 ET: The utility, compiler/search and attached-option repairs are
implemented. Linux A8 passed 329 cases at `d50a39f`; A9 passed 226 selected cases
at `de6dce1`, with all six retained-log decisions matching expectations in both
runs. The last attachment repair adds 70 public cases, with focused runs of
126 passed (283.55 s) and 62 passed (158.34 s); selections overlap. Independent
current-blob checks reject four short-selector repros and pass 24 data/pattern/
scratch-write cases. Final Linux A10 and the whole-diff review remain pending.

2026-09-29 22:25 ET: Linux A10 passed all 443 workspace cases in 1402.63 s at
`a7cca27`, and all six retained-log decisions matched expectations. A subsequent
manual review reproduced four unexpected scripted-event approvals for
`git ls-remote origin` and `rsync other:src .`, one per command and event format.
The tests did not execute network calls. These are recognized network operations
even without a URL in the command; see the primary [Git remote-query manual](https://git-scm.com/docs/git-ls-remote)
and [rsync manual](https://download.samba.org/pub/rsync/rsync.1). Command-position
classification, nearby data/local-command regressions and fresh Linux A11 checks
are required before closure.

## Answer

2026-09-29 22:37 ET: Independent checks reproduced six further scripted-event
admissions at audit blob `79ced791`: abbreviated remote add/set-head options and
remote archive options. Git documents [unambiguous long-option abbreviations and
short-option bundles](https://git-scm.com/docs/api-parse-options.html). The repair
now uses a bounded remote-option grammar, classifies recognized query/fetch
controls, refuses unsupported mutations and archive operations, and preserves
local status/diff/search and literal command data. The frozen audit blob is
`f25cb8ddf96360c17f9313a7cf2b551ce621e87b`; 104 public cases are added over A10.
Focused local/independent checks and Linux A11 are pending before closure.

2026-09-29 22:44 ET: The Git grammar recheck passed 46 rejection and 22 supported
positive cases. The same independent check then reproduced four Python prefix
admissions. A bounded interpreter-prefix grammar now consumes bundles, attached/
separate module and warning/runtime options, hash-pyc mode and option terminators,
verifies the script operand, and refuses unsupported controls. Its semantics are
based on the [Python 3.12 command-line reference](https://docs.python.org/3.12/using/cmdline.html).
Audit blob `62fe75f4efc5e79b435fb5d5390fc1ae7b4dc31b` is frozen; the workspace
module collects 575 cases, including 132 additions. Linux A11 selects all additions
and 84 existing audit/nested/script/context/repair cases. Two fictional context-read
fixture commands were corrected to actual `cat` reads; product workspace code is
unchanged. Local/independent checks and Linux A11 remain pending.

2026-09-29 (Eastern Time)

Implemented `swdb/provider_audit.py`. It parses Codex command/file-change items and Claude tool-use events, checks absolute and relative file paths and shell working-directory changes, rejects login-file/provider-home touches, rejects network commands and forbidden tools, and incorporates the independent guard's network trace result. Unknown actionable tool types and malformed event lines fail closed. Claude `StructuredOutput` events are schema transport and are independently validated by the CLI adapter.

The audit runs on successful and exceptional workspace exits. Each attempt retains the full raw stdout event log with path, byte count, and SHA-256, plus `audit.json` and its result in both the attempt receipt and proposal provider block. A security audit failure takes precedence over a coincident provider-availability error, so it cannot refund the attempt as a mere usage limit. Provider-supplied `model_api` assertions cannot authorize connections.

The parser audits direct commands and recursively parses explicit shell-wrapper bodies. It rejects unresolved command/file substitutions, delegated execution, and opaque inline interpreter programs. Claude Glob patterns and optional base paths are checked together; executable paths and attached/separate compiler file options are also checked against the workspace policy. Ordinary workspace scripts and synthetic binaries may run under the guard; auditing their invocation does not prove their source semantics.

Both real providers receive shared guidance to use direct editing tools for source changes and literal shell operands for workspace reads, builds, and synthetic runs, avoiding inline interpreters, loops, heredocs, delegation, and regex-based code transformations. This guidance does not waive or guarantee the audit.

Validation (2026-09-29 ET): the fresh local public workspace module passed **195 tests** in **396.70 seconds** after the parser fixes. A subsequent narrow run verifying guidance delivery through Codex arguments and Claude stdin, plus protected-input rejection, passed **14 tests** in **29.67 seconds**. The literal exit-status fix passed **42 focused public cases** in **83.03 seconds** on the Mac and **132.56 seconds** on Linux A7 at `c8a666f`. It permits printable literal fragments around numeric `$?` solely in echo/printf data, preserving refusals of path/glob fragments, other variables, substitutions and concatenated numeric-test arguments. Both event formats cover clean actions, forbidden file reads, login touches, network commands, forbidden tools, malformed logs, forged network authorization, timeout retention, and repair. Assertions use public proposal/candidate/raw artifacts rather than workspace or audit internals.

Linux A6 passed **222 guard/pins/workspace tests in 1428.56 seconds** at `4f5d152`. Its retained-log subprocess exposed a harmless Claude exit-status label refusal, corrected by the narrow fix and confirmed by A7. The official current-parser re-audit passes both historical toy logs and the Claude DX100 failure. The original Codex DX100 A1 attempt remains **failed** because its in-place `sed` regex transformation cannot be safely resolved; its historical receipt is unchanged and is not the current acceptance attempt. Fresh public DX100 A2 at `c8a666f` passes both original/current event audits and guards: Codex creates a candidate with independently passed source-0/3/8 native structural checks; Claude retains an OAuth-expired failure, with no candidate or BFS result. Details and raw identities are in [guarded provider evidence](../../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml) and tickets 02, 08 and 10. T17 is complete. Linux A10 passed all 443 workspace cases and six retained-log expectations. Final Linux A11 passed 216 selected cases in 695.71 s at `3a73c6c`, including all 132 additions, and all six retained-log expectations. The subsequent whole-diff review is pending.

2026-09-29 22:59 ET: Implementation acceptance closed. At frozen audit blob
`62fe75f4`, the final local selection passed 154 cases (321.82 s); independent
checks passed 114 cases (76 expected refusals, 38 admissions). Linux A11 at
`3a73c6c` passed 216 cases with no failures/skips in 695.71 s, followed by all
six expected retained-log audit decisions. Node0 generation 429 recorded load
1.11 and released with exit0 at 22:58:53 ET. Raw receipts/hashes are in the
linked evidence. Final whole-diff Standards/Spec review follows this closure.

2026-09-29 23:20 ET: Both independent whole-diff review axes are complete. No Spec
issue was found; Standards' one P3 duplication judgement was repaired at
`8889e175`, and both independent rechecks are clear. The final public workflow
selection passed 45 cases in 673.40 s, with no failures/skips. The audit blob is
unchanged from Linux A11. See the [review report](../validation/code-review.md).

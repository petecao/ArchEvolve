# 03 — Codex as a pinned rewrite provider (prompt-only mode)

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** `swdb submit` can use Codex as the rewrite provider, and Codex is the default kind. Codex
runs as `gpt-5.6-sol` at `xhigh`; Claude runs as `claude-sonnet-5-5` at `high`. The pins live
in code, cannot be overridden, and are recorded with the CLI version in every proposal. The
fixture provider can emulate either kind (`emulates: codex|claude`), which is how this is
tested.

## Acceptance

- [x] Through `swdb submit` with a fixture emulating Codex: it receives the pinned model and effort, the final-message schema, JSON event output, and an empty standard input; the proposal records kind, model, effort, and version.
- [x] A provider configuration without `kind` runs Codex.
- [x] Through `swdb submit` with a fixture emulating Claude: it receives the pinned model and effort, and the proposal records them.
- [x] A configuration that sets a model or effort is refused with a clear message.
- [x] Codex whole-file answers use a list of path and content pairs (valid under strict structured output) and are converted back before the existing whole-file path.
- [x] `budget_usd` is recorded as not enforced for Codex; existing records without model or effort still validate.

## Answer

Updated: 2026-09-29.

Codex is the default kind. Real kinds use constants `gpt-5.6-sol` / `xhigh` and
`claude-sonnet-5-5` / `high`; model and effort configuration overrides are refused. Fixtures
can emulate either CLI while remaining classified as contract fixtures. Receipts retain
resolved kind, pins, CLI version, workspace mode, guard policy, audit, and whether the dollar
budget is enforced. Codex takes empty standard input and emits JSON events plus a retained
final message; strict whole-file answers use path/content pairs and are normalized before
SWDB computes the existing protected diff. Its schema/final files reside in the guarded
provider home. Historical records remain schema-valid without invented pins.

Validation: `tests/test_provider_pins.py` completed with **13 passed** for pinned Codex and
Claude submissions, override rejection, strict whole files, default kind, quota retry,
provider identity and time bounds. Additional prompt-only audit cases both passed, including
a quota error following forbidden tool activity. Existing legacy suites: **73 passed**.

Implementation choice: Codex prompt-only input above 96 KiB fails explicitly because Linux
limits one argv argument to 128 KiB and the contract requires empty standard input; workspace
mode avoids carrying full source in argv. Prompt-only tool execution is disabled and emitted
tool activity is audited as a failure. Real prompt/workspace calls require the Linux guard.

Context: `swdb/provider_adapters.py`, `swdb/rewrite.py`, `schemas/proposal.schema.json`,
`tests/test_provider_pins.py`.

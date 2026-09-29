# 03 — Codex as a pinned rewrite provider (prompt-only mode)

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** 01
**Spec:** `../spec.md`

**What to build:** `swdb submit` can use Codex as the rewrite provider, and Codex is the default kind. Codex
runs as `gpt-5.6-sol` at `xhigh`; Claude runs as `claude-sonnet-5-5` at `high`. The pins live
in code, cannot be overridden, and are recorded with the CLI version in every proposal. The
fixture provider can emulate either kind (`emulates: codex|claude`), which is how this is
tested.

## Acceptance

- [ ] Through `swdb submit` with a fixture emulating Codex: it receives the pinned model and effort, the final-message schema, JSON event output, and an empty standard input; the proposal records kind, model, effort, and version.
- [ ] A provider configuration without `kind` runs Codex.
- [ ] Through `swdb submit` with a fixture emulating Claude: it receives the pinned model and effort, and the proposal records them.
- [ ] A configuration that sets a model or effort is refused with a clear message.
- [ ] Codex whole-file answers use a list of path and content pairs (valid under strict structured output) and are converted back before the existing whole-file path.
- [ ] `budget_usd` is recorded as not enforced for Codex; existing records without model or effort still validate.

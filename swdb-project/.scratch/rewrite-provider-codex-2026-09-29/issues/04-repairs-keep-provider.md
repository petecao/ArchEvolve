# 04 — Repairs keep their provider; usage limits don't consume repairs

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** A repair always uses the kind, model, and effort of the proposal's first attempt. A
ChatGPT usage-limit error is recorded as `provider_unavailable` instead of a failed rewrite.
The new time caps apply.

## Acceptance

- [ ] `swdb repair` with a different kind, model, or effort than the first attempt is refused; with the same one it proceeds.
- [ ] A fixture that reports a usage-limit error produces the outcome `provider_unavailable`; the repair count is unchanged and the proposal can be retried.
- [ ] Per-call time is capped at 1800 s with a 1200 s default; the total stays capped at 3600 s.

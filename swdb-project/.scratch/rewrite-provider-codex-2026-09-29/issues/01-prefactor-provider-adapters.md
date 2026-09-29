# 01 — Prefactor: one interface for all provider kinds

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The rewrite path handles each rewrite provider kind through one adapter (command line,
version capture, response extraction, error detection). Claude and the fixture provider
become adapters, so Codex can be added as one new adapter. Behavior does not change.

## Acceptance

- [ ] Every existing rewrite, stream-capture, whole-file, prompt-projection, and campaign-reuse test passes unchanged.
- [ ] No kind-specific branches remain in the shared provider-call path; adding a kind means adding and registering one adapter.
- [ ] The Claude command line recorded in a proposal is identical to before for the same configuration.

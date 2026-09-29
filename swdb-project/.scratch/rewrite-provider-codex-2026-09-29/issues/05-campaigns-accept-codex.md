# 05 — Campaigns and the smoke script accept Codex

Created: 2026-09-29
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** Real campaigns can run with Codex or Claude, and candidates Claude already made stay
reusable. The instruction smoke script uses the default kind and takes a kind override.

## Acceptance

- [ ] The native campaign runner accepts real campaigns with either kind and still refuses the fixture provider.
- [ ] Campaign reuse accepts existing Claude receipts without model or effort, and a new case covers a Codex receipt.
- [ ] The smoke script runs the default kind, and `--kind claude` switches it.

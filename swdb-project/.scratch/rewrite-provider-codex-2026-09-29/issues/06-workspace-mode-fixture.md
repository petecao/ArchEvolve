# 06 — Workspace mode with the fixture provider

Created: 2026-09-29
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** `swdb submit` runs the provider in a provider workspace by default. SWDB derives the visible
set from the rewrite proposal, builds the workspace and a per-run provider home, gives the
provider a prompt with the proposal and a map of the workspace, and takes the edit as the
diff between the workspace and the starting snapshot. Real kinds refuse workspace mode until
ticket 08 adds the guard; the fixture exercises the whole path.

## Acceptance

- [ ] The workspace holds exactly the derived visible set; a file the proposal names is added and recorded.
- [ ] A fixture edit to an allowed file becomes the candidate's diff; build outputs are dropped; a new file outside the allowed list fails the attempt with a stored reason.
- [ ] The per-run provider home holds only a login-file copy, which is deleted when the session ends; the rest is retained.
- [ ] The existing protections still apply (a protected-input change or a comment-only edit is rejected).
- [ ] `workspace: false` behaves exactly as before, and real kinds in workspace mode refuse with a clear message until the guard exists.

## Comments

2026-09-29: Claimed by provider_workspace agent for workspace derivation, diff, audit, and public fixture coverage.

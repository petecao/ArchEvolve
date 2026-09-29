# 06 — Workspace mode with the fixture provider

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`

**What to build:** `swdb submit` runs the provider in a provider workspace by default. SWDB derives the visible
set from the rewrite proposal, builds the workspace and a per-run provider home, gives the
provider a prompt with the proposal and a map of the workspace, and takes the edit as the
diff between the workspace and the starting snapshot. Real kinds refuse workspace mode until
ticket 08 adds the guard; the fixture exercises the whole path.

## Acceptance

- [x] The workspace holds exactly the derived visible set; a file the proposal names is added and recorded.
- [x] A fixture edit to an allowed file becomes the candidate's diff; build outputs are dropped; a new file outside the allowed list fails the attempt with a stored reason.
- [x] The per-run provider home holds only a login-file copy, which is deleted when the session ends; the rest is retained.
- [x] The existing protections still apply (a protected-input change or a comment-only edit is rejected).
- [x] `workspace: false` behaves exactly as before, and real kinds in workspace mode refuse with a clear message until the guard exists.

## Comments

2026-09-29: Claimed by provider_workspace agent for workspace derivation, diff, audit, and public fixture coverage.

## Answer

2026-09-29

Implemented `swdb/provider_workspace.py` and the shared public submit/repair integration. The workspace derives snapshot source, selected regions, the profile package, selected strategy, required operation headers, and proposal `visible_files`; exact protected verifier fragments are hidden and restored before diff creation. Known workload/evaluator paths and project instruction/configuration surfaces are excluded. Extra names and the complete visible/immutable map are retained in each attempt's workspace manifest.

Workspace edits become a real Git diff against the starting source. Immutable input changes, symbolic links, binary source edits, unapproved new files, and altered protected placeholders fail before candidate creation. Compiled build outputs are recorded and dropped. Temporary synthetic test sources may be created under `build/` but must be deleted before finishing; leftover source helpers remain rejected. The existing candidate protections and actual-code-change check still apply.

Each run uses a fresh owner-only provider home. Real kinds receive only a copy of their login file; contract fixtures receive an explicit synthetic login copy. Cleanup deletes that copy on success, timeout, guard refusal, and provider failure, while retaining other CLI artifacts. Real modes use the SWDB guard and remain fail closed where it cannot run. Legacy prompt-only routes remain selected by `workspace: false`.

Validation (2026-09-29): `tests/test_provider_workspace.py` completed **40 passed** in 89.27 s; eight added focused public-seam cases for annotated-source hiding, preservation of structured payload fields, and audit precedence completed **8 passed** in 17.97 s. Both Codex and Claude public repairs were also verified (**2 passed**). These are contract fixtures, not provider-performance evidence. Required operation headers without an exact local source identity fail closed rather than reading a model/evaluator repository.

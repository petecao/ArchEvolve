# 01 — Prefactor: one interface for all provider kinds

Created: 2026-09-29
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The rewrite path handles each rewrite provider kind through one adapter (command line,
version capture, response extraction, error detection). Claude and the fixture provider
become adapters, so Codex can be added as one new adapter. Behavior does not change.

## Acceptance

- [x] Every existing rewrite, stream-capture, whole-file, prompt-projection, and campaign-reuse test passes unchanged.
- [x] No kind-specific branches remain in the shared provider-call path; adding a kind means adding and registering one adapter.
- [ ] The Claude command line recorded in a proposal is identical to before for the same configuration.

## Answer

Updated: 2026-09-29.

`swdb/provider_adapters.py` owns each kind's command, version capture, response schema,
response extraction and normalization. `rewrite.interpret` owns process capture and guard
callbacks through this adapter interface; it has no Claude/Codex execution branches.
The legacy Claude prompt transport options remain intact. Ticket 03 deliberately appends
the required model/effort pins, so its final recorded argv differs by those required pins.
Historical fixture configurations now explicitly select `workspace: false`; the fake
Claude stream executable uses `external_fixture` with `emulates: claude` so the Mac never
runs a real provider without the Linux guard.

Validation: the existing rewrite, full-file, stream, prompt-projection and campaign-reuse
suite completed with **73 passed**. The additional Codex/legacy-Claude reuse cases completed
with **2 passed**. No real provider sessions ran on the Mac.

Context: `swdb/provider_adapters.py`, `swdb/rewrite.py`, `tests/test_provider_pins.py`.

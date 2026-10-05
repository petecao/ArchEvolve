# 79 — Certify 1.5 behavior changes made inside ticket 78 (commit 93a2a94): awaiting ratification

Created: 2026-10-05 18:25 ET (by the spec review of tickets 38–78, finding C13)
**Type:** task
**Status:** ready-for-human
**Blocked by:** None — can start immediately
**Spec:** `../spec.md` ("Awaiting ratification"; certification command, "Evaluator process");
[75](75-certify-a8-frontier-staging.md), [76](76-attributed-blinded-certification.md),
[78](78-certification-evaluator-process.md)

**What to decide:** Yan-Ru ratifies or reverses two certification behavior changes. Yan-Ru scoped ticket 78
as an engineering refactor (record-keeping in a separate evaluator process). Commit `93a2a94` (2026-10-05
15:07 ET, "Ticket 78 (ticket 75 review items)") also changed what certification accepts, to close two
open items of ticket 75's review. Both are **agent-decided under delegation; awaiting ratification**. This
ticket only records them; nothing was changed by it.

## The changes in 93a2a94

1. **Nonce-named record files (certify 1.4 and 1.5, DX100; native runs used nonce names since ticket
   75).** A run's record file was named after its log (`<cell or control>.log.record`), so a candidate
   reading `/proc/self/fd` could learn which fault ran. It is now `run-<nonce>.record`; the log keeps the mapping.
   (`swdb/certification_blinding.py` `run`; `swdb/certification_process.py` `record_path`.)
   Records of earlier runs keep their meaning.
2. **DX100 authored-directive rule (certify 1.5 only).** Before any build, certify 1.5 refuses a
   candidate-authored conditional directive (`#if`, `#ifdef`, `#ifndef`, `#elif`, the token `defined`)
   and any `#define` or `#undef` of a certification seam macro, except a contract knob default
   (`#ifndef M` / `#define M ...` / `#endif`) and the `#ifdef SWDB_DXC_DIAGNOSTIC` block.
   (`swdb/certification_process.py` `directive_findings`, `refuse_directives`; called from
   `swdb/certification.py` `certify`.) Certify 1.3 and 1.4 keep 1.3's scan. Ticket 75's native rule
   (only `#pragma omp`) would have refused ticket 20, ticket 42 and both a7 bests, which is why the
   DX100 form is narrower.

Tests: `tests/test_certification_process.py` (added in the same commit).

## What Yan-Ru needs to answer

- Keep both changes as part of certify 1.5 (and the record names for 1.4), or move either to a new
  command version.
- Whether the DX100 directive rule's two exceptions are the right ones.

## Comments

- 2026-10-05 18:25 ET: created by the code-review agent from spec review C13; listed in the spec's
  "Awaiting ratification" section.

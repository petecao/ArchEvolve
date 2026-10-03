# 49 — Port Extensa's machinery

Created: 2026-10-03
**Type:** slice
**Status:** needs-triage
**Blocked by:** 07, 10, 11, 47
**Spec:** `../spec.md`

**What to build:** Extensa's runtime-probe contract checks, certification profiles and synthesis work inside SWDB.

## Acceptance

- [ ] Contract predicates compile into runtime probes in certification builds only.
- [ ] Certification profiles extend `swdb certify`; there is no second certifier.
- [ ] Synthesis of library entries works through the provider launcher.
- [ ] Ported files carry SPDX and provenance headers; Extensa's agent runtime, timing and speed rule are not ported.

## Comments

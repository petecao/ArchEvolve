# 51 — Seed the experimental tier from Extensa

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 50
**Spec:** `../spec.md`

**What to build:** Native-CPU Extensa campaigns have entries to work with from the start.

## Acceptance

- [ ] Four entries enter the experimental tier as standalone C++11 headers under `library/library_operations/`. Each carries SPDX and provenance headers, and its origin is MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76` with the paths below:
  - binning: `UpdateBinningExecutor` (`DataLayoutAPI/update_binning.hh`, `transformations/binned/binned_update_executor.yaml`);
  - relabeling: `VertexRelabelExecutor` (`DataLayoutAPI/vertex_relabel.hh`, `transformations/relabel/vertex_relabel_executor.yaml`);
  - regrouping: `RegroupExecutor` (`DataLayoutAPI/data_layout.hh`, `transformations/regroup/regroup_executor.yaml`);
  - gather staging: `GatherStagingExecutor` (`DataLayoutAPI/gather_staging.hh`, `transformations/staging/gather_staging_executor.yaml`).
- [ ] Only base variants are ported (no team, deterministic, tiled or fused variants).
- [ ] Each entry has a plain C++ reference semantics, a differential-test driver, at least three negative controls and a certification profile (matrix plus controls). `swdb certify` certifies each entry and rejects every control by a named check.
- [ ] Each entry declares its BFS-relevant pattern key, so the site finder (ticket 55) can match it.
- [ ] `swdb/extensa/PROVENANCE.md` lists every new file.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

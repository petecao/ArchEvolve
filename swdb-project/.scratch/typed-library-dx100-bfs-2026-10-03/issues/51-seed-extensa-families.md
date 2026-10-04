# 51 — Seed the experimental tier from Extensa

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** resolved
**Blocked by:** 50
**Spec:** `../spec.md`

**What to build:** Native-CPU Extensa campaigns have entries to work with from the start.

## Acceptance

- [x] Four entries enter the experimental tier as standalone C++11 headers under `library/library_operations/`. Each carries SPDX and provenance headers, and its origin is MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76` with the paths below:
  - binning: `UpdateBinningExecutor` (`DataLayoutAPI/update_binning.hh`, `transformations/binned/binned_update_executor.yaml`);
  - relabeling: `VertexRelabelExecutor` (`DataLayoutAPI/vertex_relabel.hh`, `transformations/relabel/vertex_relabel_executor.yaml`);
  - regrouping: `RegroupExecutor` (`DataLayoutAPI/data_layout.hh`, `transformations/regroup/regroup_executor.yaml`);
  - gather staging: `GatherStagingExecutor` (`DataLayoutAPI/gather_staging.hh`, `transformations/staging/gather_staging_executor.yaml`).
- [x] Only base variants are ported (no team, deterministic, tiled or fused variants).
- [x] Each entry has a plain C++ reference semantics, a differential-test driver, at least three negative controls and a certification profile (matrix plus controls). `swdb certify` certifies each entry and rejects every control by a named check.
- [x] Each entry declares its BFS-relevant pattern key, so the site finder (ticket 55) can match it.
- [x] `swdb/extensa/PROVENANCE.md` lists every new file.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:12 ET (agent, under Yan-Ru's standing implementation approval).

Four experimental-tier entries, each a standalone C++11 header under `library/library_operations/`
with SPDX and provenance headers, origin MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76` and the
paths below; base variants only (no team, deterministic, tiled or fused code):

| Entry | Body | Family (harness) | Controls (named check) |
|---|---|---|---|
| `operation.update_binning_executor` | `binning.hh` (`UpdateBinningExecutor`, `DataLayoutAPI/update_binning.hh`, `transformations/binned/binned_update_executor.yaml`) | `bin_drain` | dropped_last_record, double_drain (differential_mismatch), aliasing_write (frame_violation) |
| `operation.vertex_relabel_executor` | `relabel.hh` (`VertexRelabelExecutor`, `DataLayoutAPI/vertex_relabel.hh`, `transformations/relabel/vertex_relabel_executor.yaml`) | `relabel` | inverse_direction, skip_last_vertex (differential_mismatch), aliasing_write (frame_violation) |
| `operation.regroup_executor` | `regroup.hh` (`RegroupExecutor`, `DataLayoutAPI/data_layout.hh`, `transformations/regroup/regroup_executor.yaml`) | `regroup` | transposed_layout, dropped_last_array (differential_mismatch), aliasing_write (frame_violation) |
| `operation.gather_staging_executor` | `gather_staging.hh` (`GatherStagingExecutor`, `DataLayoutAPI/gather_staging.hh`, `transformations/staging/gather_staging_executor.yaml`) | `gather_stream` | partial_drain, index_shift (differential_mismatch), aliasing_write (frame_violation) |

- Each has a plain C++ reference (`swdb_ref::` in `reference/movement_reference.hh`), a
  differential driver (ported family templates plus an executor adapter
  `drivers/<entry>_cand.cpp.tmpl`), three controls in `controls/`, and a profile in
  `library/profiles/<entry>.yaml` (sanitized and OpenMP 4-thread builds, 8 post-hoc-seeded cases).
- `swdb certify operation.<entry> --profile <entry>` certifies each, and every control is rejected
  by its named check (test).
- Each declares a BFS-relevant `pattern_key` (roles, address shapes, update kind from the
  vocabularies; `swdb validate` checks it via `library_operations.pattern_key_problems`) for the
  ticket 55 site finder.
- `swdb/extensa/PROVENANCE.md` lists every new file.

Tests: `tests/test_extensa_library_operations.py` now 21 cases (all five seeded entries certify
with named-check rejections; origin, pattern key, controls and profile agreement; C++11 `-O3`
builds; DX100 and pattern-key validation refusals): 21 passed.

Assumptions (agent-decided, revisable):

- Relabeling has no Extensa synthesis driver; an SWDB `relabel` shape class and templates
  (adapted from the gather templates, marked as SWDB additions) certify `permute_values`.
- `build_degree_order` keeps its total order but uses `std::stable_sort` instead of MemAcc's
  parallel merge (an optimization variant). Binning's `scatter_add` lambdas became functors.
- Pattern keys are agent-chosen from each contract's loop shape and stay revisable at ticket 55.

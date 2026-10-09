# Evidence: gem5 wait rule in the strict layer, and the digest re-declaration

Created: 2026-10-09 15:30 ET
**Why:** [research 14](../research/14-dx100-wait-rule.md) refuted the strict layer's wait rule on
gem5's DX100 device. Yan-Ru asked for the fix on 2026-10-09.
**Base:** ArchEvolve `59059e2d` (`yanrujhou_main`). All runs on the Mac (aarch64, GCC `g++-16`), no gem5.

---

## Summary

- **New versions:** candidate certify **1.7** (1.6 + gem5 wait rule) and lowering certify **1.2**
  (1.1 + gem5 wait rule). Both are now the defaults.
- **Old versions:** candidate 1.3-1.6, native 1.3-1.5 and lowering 1.1 keep their behavior. Their
  digests are re-declared only because file bytes changed.
- **Finding:** Peter's read offload **fails** candidate 1.7 (`read_before_wait`). It certifies under
  1.6. The cause is the range-loop exception plus a gem5 rule the strict layer does not model (see
  "Finding" below). The candidate was not changed.

## What changed

| File | Change | Read by |
|---|---|---|
| `library/dx100/strict/MAA_functional.hpp` | New `#ifdef SWDB_STRICT_WAIT_RULE_GEM5` blocks. Each replaced function keeps its old text byte for byte under `#ifndef`. | candidate 1.3-1.7, lowering 1.1-1.2 |
| `swdb/certification.py` | `CONTROLS_GEM5_WAIT`, `STORE_CONTROL`, `wait_rule` parameters, `evaluate_trusted_gem5_wait`, calibration content digest for 1.2 | every candidate, native and lowering version |
| `swdb/certification_process.py` | `Build.evaluator_defines = ()`, `Gem5WaitBuild`, `_build_class` | candidate 1.5-1.7, native 1.5 |
| `swdb/certification_procedures.py` | `wait_rule` field (left out of `definition()` while None), 1.7, lowering 1.2, defaults | the definition row only |

## How old behavior was shown unchanged

1. **Strict header, preprocessed.** Without the define, `g++-16 -E -P` of the old and new header gives
   identical text for `-std=c++11` and `-std=c++17`, each at `TILE_SIZE` 1024 and 16384 (`cmp`: equal).
2. **Manifests.** For every old version, the definition row is unchanged. Putting the old bytes of the
   three edited files back into the current manifest reproduces the old frozen digest exactly. So no
   other file row changed.
3. **Python paths.** With `wait_rule=None`, every old path computes the same values as before:
   - `certify_lowering` uses `CONTROLS` and runs `wrong_store_wait` with check `read_before_wait`;
   - calibration still patches `wait_ready(tile3)` to `wait_ready(tile5)` and builds with `-DMAA` only;
   - `Build.evaluator()` gets the same flags (`evaluator_defines` is empty);
   - the 1.1 calibration content digest dict is unchanged.
4. **Runs** (records not persisted; summaries were kept in the session scratchpad):
   - calibration under lowering 1.1: **certified**, every control rejected (`wrong_store_wait`
     by `read_before_wait`);
   - Peter's candidate (`contract.bfs_read_offload`, `peter-section5.patch`) under candidate 1.6:
     **certified**, 10/10 cells, 20/20 controls rejected.
5. **Tests:** `tests/test_strict_wait_rule.py` runs every scenario under both rules. The old rule keeps
   its old results (sentinel after a source-tile wait, `constant_uncovered_register` on a held constant).

## Re-declared digests

| Version | Old frozen digest | New digest | Edited rows |
|---|---|---|---|
| candidate 1.3 | `6c75a1b1…` | `51e6e839…` | certification.py, MAA_functional.hpp |
| candidate 1.4 | `90c7a0bf…` | `f0d79cf5…` | certification.py, MAA_functional.hpp |
| candidate 1.5 | `0310109a…` | `47d1964d…` | + certification_process.py |
| candidate 1.6 | `3593fa57…` | `1a520cc2…` | + certification_process.py |
| native 1.3 | `5fafe536…` | `4b32c8f9…` | certification.py |
| native 1.4 | `b8a4932a…` | `98c68dbf…` | certification.py |
| native 1.5 | `fc5a7e51…` | `26d3fce0…` | certification.py, certification_process.py |
| lowering 1.1 | `1d14a816…` | `92545c60…` | certification.py, MAA_functional.hpp |

The unpinned-file hash of `dx100/strict/MAA_functional.hpp` in
`tests/test_certification_procedures.py` is re-declared too (`e90354b1…` to `388ffc19…`).

**Side effects:**

- Certification records made before this change name the old digests.
  `swdb evaluate-functional` accepts only a receipt at the current default version and manifest. It
  now needs a new candidate 1.7 certification.
- The calibration content digest hashes the whole `dx100/strict` folder, so 1.1 calibration records
  get a new `entry.content_sha256`.

## The gem5 rule as implemented

Source: research 14, sections 1, 4 and 6.

1. **What a wait covers.** A wait on tile t covers every uncovered command that names t as
   src1/src2/dst1/dst2 (never as a condition), plus t's writer. Coverage is transitive over each
   command's tile and register producers.
2. **Range-loop exception.** Coverage does not follow the tile inputs of a range loop that filled its
   tile (`is.size()==TILE_SIZE`). Register producers are still followed.
3. **Ready bit.** `get_tile_ready(t)` is 1 only when no uncovered command names t and t's writer is
   covered.
4. **Held constant.** `maa_const`/`set_reg` covers the register's uncovered readers instead of failing
   `constant_uncovered_register`.

Roles per call: stream load dst1=dst; indirect load src1=index, dst1=dst; ALU src1=src, dst1=dst;
indirect store src1=index, src2=src, dst1=result; range loop src1=min, src2=max, dst1=rows,
dst2=columns.

**Evaluator check:** `library/dx100/certification/v1_5/evaluator.cc` marks need no change. A CPU
buffer changes only when its tile's writer becomes covered, and the marks compare exactly that.

## Results under the new versions

- **Calibration, lowering 1.2: certified.** It ran the unmodified authors' `TDStepMAA` (10/10 cells).
  All 7 controls were rejected; `dropped_store_wait` was rejected by `read_before_wait` at both tile
  sizes.
- **Lowering 1.2 controls:** every row of `CONTROLS_GEM5_WAIT` is rejected by its named check, at
  both tile sizes. Four old controls are accepted by the new rule, so lowering 1.2 replaces them:
  - `wrong_store_wait`;
  - `constant_uncovered` for const_i32, wait and stream_load.
- **Peter's candidate, candidate 1.7: failed.**
  - Cells: 9 of 10 fail with `strict_layer_assertion` / `read_before_wait`. Only kronecker-10 at
    tile size 16384 passes.
  - Controls: 15 rejected, 5 `invalid` (because their positive cell failed).
- **BC read offload, candidate 1.7: failed the same way.** Same cells (9 of 10, `read_before_wait`),
  same loop structure (`library/dx100/bc_read_offload.inc:44-58`).
- **Tests that hit the same finding:** 9 full-certification tests failed at the new default for the
  same reason (`read_before_wait`):
  - `tests/test_certification_controls.py`: 5 tests;
  - `tests/test_certification_legality.py`: 3 tests;
  - `tests/test_bc_certification.py::test_bc_forward_pass_certifies_with_every_control_rejected`.

  They test the control and legality machinery, not the wait rule, so they are pinned to candidate
  1.6 (the `_certify` helper's `PINNED_VERSION`; `version='1.6'` in the BC test). Re-point them to the
  default once the finding below is decided.
- **Test runs** (2026-10-09, Mac):
  - the 22 certification-related test files: 681 passed, 6 failed. The BC test then passed after its
    pin. The other 5 fail identically on base `59059e2d`, so they predate this change; they come from
    records state:
    - `test_functional_evaluation.py`: 2 tests;
    - `test_functional_target_description.py`: 1 test;
    - `test_typed_dispatch_retention.py`: 1 test;
    - `test_typed_gem5_driver.py::test_prepare_ignores_a_newer_receipt_without_current_dependencies`.
  - The full suite did not finish: `tests/test_add.py` alone ran past 5 minutes without output.

## Finding: why Peter's candidate fails 1.7

`library/dx100/bfs_read_offload.inc:30-44`, one chunk:

1. The stream load writes tile0. The two row-bound gathers read tile0.
2. The range loop fills its tile. `__dxc_wait(tile7)` covers it, but under the exception not the
   gathers or the stream load behind it.
3. The loop then gathers into tile0 again. Tile0 is still named by those uncovered commands.
4. The CPU reads tile0 after waiting on tile3 and tile5. `get_tile_ready(tile0)` is 0, so
   `read_before_wait` fires.

`tests/test_strict_wait_rule.py::test_the_read_offload_chunk_reads_tile0_uncovered_under_gem5_after_a_filled_range_loop`
reproduces this in 15 lines.

**Probably not a hazard on gem5.** IF.cc:193-212 (research 14, section 4) refuses to dispatch a command
whose destination tile is the source or destination of an unfinished command. Dispatch is in program
order and acknowledged before the next call. So the gather into tile0 cannot be accepted until the
stream load and the row-bound gathers have finished. The strict layer does not model this dispatch
stall, so here it is stricter than gem5.

This rests on reading the source only; it was not shown on gem5.

**Open for Yan-Ru.** Add a fifth rule: issuing a command covers the uncovered commands that name its
destination tile, the tile counterpart of the held-constant rule. That would be a new version (1.8 /
lowering 1.3). It was not added here because it was not in the approved semantics.

## Library entry text that now contradicts the rule

These were not edited, because changing them changes content hashes.

- **`completion.assumptions` of 10 intrinsics:** "A tile wait covers its producer and transitive
  dependencies, not unrelated operations or a store source."
  - Files: `library/intrinsics/dxc_{wait,const_i32,alu_scalar,stream_load,tile_size,session_begin,gather,thread_context,range_loop,tile_pointer}.yaml`.
  - Under 1.7 / lowering 1.2 a wait does cover a store through its source tile, and coverage stops
    at a filled range loop's tile inputs.
  - `owner: Eric` and "assumed" can now cite research 14.
- **`constant_uncovered` / `constant_uncovered_register`:** the `result` clause of
  `library/intrinsics/dxc_const_i32.yaml` and of
  `library/lowerings/dx100-mmio/1.0-e4fc4af/dxc_const_i32.yaml` names this control. The gem5 rule
  accepts it, and lowering 1.2 replaces it with `truncation`.

## Still open

- **Memory-effect timing.** The strict layer applies DX100 loads and stores to main memory at the
  call. On gem5 only a wait orders them with CPU accesses (research 14, section 6). Until this is
  modeled, the strict layer is looser than gem5 there.

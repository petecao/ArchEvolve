# Evidence: gem5 wait rule in the strict layer, and the digest re-declaration

Created: 2026-10-09 15:30 ET
Updated: 2026-10-09 17:55 ET (rule 5, the dispatch stall on tiles, added to 1.7 and lowering 1.2
in place; both were unmerged and unpublished. All results below are re-run with rule 5.)
**Why:** [research 14](../research/14-dx100-wait-rule.md) refuted the strict layer's wait rule on
gem5's DX100 device. Yan-Ru asked for the fix on 2026-10-09.
**Base:** ArchEvolve `59059e2d` (`yanrujhou_main`). All runs on the Mac (aarch64, GCC `g++-16`), no gem5.

---

## Summary

- **New versions:** candidate certify **1.7** (1.6 + gem5 wait rule) and lowering certify **1.2**
  (1.1 + gem5 wait rule). Both are the defaults.
- **Old versions:** candidate 1.3-1.6, native 1.3-1.5 and lowering 1.1 keep their behavior. Their
  digests are re-declared only because file bytes changed.
- **Results under the new versions:**
  - calibration (lowering 1.2): **certified**;
  - Peter's read offload (candidate 1.7): **certified**;
  - BC read offload (candidate 1.7): **certified**.
- **Rule 5 decided it.** Without rule 5 (first cut, 15:30 ET) both read offloads failed with
  `read_before_wait`; with rule 5 both certify.

## The gem5 rule as implemented

Source: research 14, sections 1, 4 and 6. Everything below sits behind `-DSWDB_STRICT_WAIT_RULE_GEM5`.

1. **What a wait covers.** A wait on tile t covers every uncovered command that names t as
   src1/src2/dst1/dst2 (never as a condition), plus t's writer. Coverage is transitive over each
   command's tile and register producers.
2. **Range-loop exception** (RangeFuser.cc:166-168, 214-218). Coverage does not follow the tile inputs
   of a range loop that filled its tile (`is.size()==TILE_SIZE`). Register producers are still followed.
3. **Ready bit.** `get_tile_ready(t)` is 1 only when no uncovered command names t and t's writer is
   covered.
4. **Held constant** (IF.cc:233-249, MAA.cc:510-538, CpuSidePort.cc:145-149). `maa_const`/`set_reg`
   covers the register's uncovered readers instead of failing `constant_uncovered_register`.
5. **Dispatch stall on tiles** (IF.cc:193-212). Issuing a command first covers every uncovered command
   that names any of its destination tiles as a source, destination or condition. Coverage is
   transitive, with the rule 2 exception.
   - The device does not accept the new command until those commands finish.
   - Condition users are tracked for this rule only (`users[t]`); rule 1 still ignores them.
   - The memory-region stall (IF.cc:213-219) is not modeled; it belongs to the memory-timing work.

Roles per call: stream load dst1=dst; indirect load src1=index, dst1=dst; ALU src1=src, dst1=dst;
indirect store src1=index, src2=src, dst1=result; range loop src1=min, src2=max, dst1=rows,
dst2=columns. The condition tile is never a counted role.

**Evaluator check:** `library/dx100/certification/v1_5/evaluator.cc` marks need no change. A CPU
buffer changes only when its tile's writer becomes covered, and the marks compare exactly that.

## What changed

| File | Change | Read by |
|---|---|---|
| `library/dx100/strict/MAA_functional.hpp` | New `#ifdef SWDB_STRICT_WAIT_RULE_GEM5` blocks. Each replaced function keeps its old text byte for byte under `#ifndef`. | candidate 1.3-1.7, lowering 1.1-1.2 |
| `swdb/certification.py` | `CONTROLS_GEM5_WAIT`, `STORE_CONTROL`, `wait_rule` parameters, `evaluate_trusted_gem5_wait`, calibration content digest for 1.2 (`fix: None`, `wait_rule: gem5`) | every candidate, native and lowering version |
| `swdb/certification_process.py` | `Build.evaluator_defines = ()`, `Gem5WaitBuild`, `_build_class` | candidate 1.5-1.7, native 1.5 |
| `swdb/certification_procedures.py` | `wait_rule` field (left out of `definition()` while None), 1.7, lowering 1.2, defaults | the definition row only |

## How old behavior was shown unchanged

Re-checked after rule 5.

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
4. **Runs before rule 5** (it does not touch old-mode code). Records were not persisted.
   - Calibration under lowering 1.1: **certified**; `wrong_store_wait` was rejected by
     `read_before_wait`.
   - Peter's candidate under 1.6: **certified**, 10/10 cells and 20/20 controls rejected.
5. **Tests:** `tests/test_strict_wait_rule.py` runs every scenario under both rules. The old rule keeps
   its old results.

## Frozen digests (final, with rule 5)

| Version | Digest before this change | Digest now | Edited rows |
|---|---|---|---|
| candidate 1.3 | `6c75a1b1…` | `f6d59b94…` | certification.py, MAA_functional.hpp |
| candidate 1.4 | `90c7a0bf…` | `d4a02b72…` | certification.py, MAA_functional.hpp |
| candidate 1.5 | `0310109a…` | `e2d1413b…` | + certification_process.py |
| candidate 1.6 | `3593fa57…` | `81e4697d…` | + certification_process.py |
| candidate 1.7 | new | `9dedc2a9…` | |
| native 1.3 | `5fafe536…` | `4b32c8f9…` | certification.py |
| native 1.4 | `b8a4932a…` | `98c68dbf…` | certification.py |
| native 1.5 | `fc5a7e51…` | `26d3fce0…` | certification.py, certification_process.py |
| lowering 1.1 | `1d14a816…` | `bd98d864…` | certification.py, MAA_functional.hpp |
| lowering 1.2 | new | `0c9bab29…` | |

The unpinned-file hash of `dx100/strict/MAA_functional.hpp` in
`tests/test_certification_procedures.py` is re-declared too (`e90354b1…` to `a24a8163…`).

**Side effects:**

- Certification records made before this change name the old digests.
  `swdb evaluate-functional` accepts only a receipt at the current default version and manifest. It
  now needs a new candidate 1.7 certification.
- The calibration content digest hashes the whole `dx100/strict` folder, so 1.1 calibration records
  get a new `entry.content_sha256`.

## Results under the new versions

All runs below include rule 5.

- **Calibration, lowering 1.2: certified.** It ran the unmodified authors' `TDStepMAA` (10/10 cells).
  All 7 controls were rejected; `dropped_store_wait` was rejected by `read_before_wait` at both tile
  sizes.
- **Peter's candidate, candidate 1.7: certified.** `contract.bfs_read_offload` with
  `peter-section5.patch`: 10/10 cells passed, 20/20 controls rejected, every enforceable clause
  control matched.
- **BC forward pass, candidate 1.7: certified.**
  `tests/test_bc_certification.py::test_bc_forward_pass_certifies_with_every_control_rejected` runs at
  the default again.
- **Lowering 1.2 controls:** every row of `CONTROLS_GEM5_WAIT` is rejected by its named check, at both
  tile sizes. Four old controls are accepted by the new rule, so lowering 1.2 replaces them:
  - `wrong_store_wait`;
  - `constant_uncovered` for const_i32, wait and stream_load.
- **Un-pinned tests:** the 8 Peter-derived control and legality tests and the BC test had been pinned
  to 1.6 between 15:33 and 17:50 ET. They run at the default again.
- **Test runs** (with rule 5):
  - the 22 certification-related test files: **686 passed, 5 failed**; `tests/test_strict_wait_rule.py`
    alone: 101 passed.
  - **The 5 failures predate this change.** They fail identically on base `59059e2d` and do not use the
    strict layer; they fail on records state:
    - `test_functional_evaluation.py`: 2 tests, and `test_functional_target_description.py`: 1 test.
      `freeze-protocol` validation of the copied records fails on LANL CPU records whose
      characterization dependencies are missing from the fixture subset; this happens before any
      certification.
    - `test_typed_dispatch_retention.py`: refused by ADR 0013's gem5 refusal.
    - `test_typed_gem5_driver.py::test_prepare_ignores_a_newer_receipt_without_current_dependencies`:
      selects a newer committed receipt than the test expects.
  - The full suite did not finish on this Mac: `tests/test_add.py` alone ran past 5 minutes without
    output.

## What rule 5 resolved

Without rule 5, Peter's and BC's read offloads failed 1.7 (`read_before_wait`, 9 of 10 cells). One
chunk of `library/dx100/bfs_read_offload.inc:30-44`:

1. The stream load writes tile0. The two row-bound gathers read tile0.
2. The range loop fills its tile. Under rule 2, `__dxc_wait(tile7)` does not cover the gathers or the
   stream load behind them.
3. The CPU then reads tile0 while those commands are still uncovered.

**What rule 5 changes:** the gather that next writes tile0 covers both commands, exactly as gem5
refuses to accept it until they finish.

`tests/test_strict_wait_rule.py::test_the_read_offload_chunk_reads_tile0_covered_after_a_filled_range_loop`
is the reproduction, now passing.

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
  call. On gem5 only a wait orders them with CPU accesses (research 14, section 6). The memory-region
  dispatch stall (IF.cc:213-219) belongs to the same work. Until both are modeled, the strict layer is
  looser than gem5 there.

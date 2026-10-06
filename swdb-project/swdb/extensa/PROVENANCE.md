# Extensa port provenance

Date: 2026-10-03 ET
Updated: 2026-10-05 ET (code review: wording kept on purpose; unused rollback helpers noted)

Source: `MaizeHPC/MemAcc` commit `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, read only from
the local checkout. License: `Apache-2.0 WITH LLVM-exception` (MemAcc `LICENSE`), under the
accepted Q66 assumption: Yan-Ru authorized it on 2026-10-03, pending Peter's confirmation
(ticket 02). If Peter names another license, a follow-up ticket relabels every file below
and every file in `swdb/_vendor/PROVENANCE.md`.

Scope: decision D1 of
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`. Each file
carries an SPDX header and a provenance header naming its MemAcc source path. Nothing on
D1's not-ported list is imported or copied (`tests/test_extensa_machinery.py` checks).

Upstream wording is kept on purpose in ported files whose logic is unchanged (for example
"oracle", "harness" or "campaign" used alone), so they stay comparable with their MemAcc source;
SWDB's own prose follows `CONTEXT.md`.

`plan_rollback` and `apply_rollback` in `swdb/extensa/search.py` are ported from
`refiner/a5/search.py` but no SWDB code calls them (only `tests/test_extensa_machinery.py`): an
Extensa campaign rebuilds each candidate artifact from the snapshot instead of rolling a worktree
back. They are kept, unchanged, until a caller needs them or a cleanup ticket removes them
(noted 2026-10-05, spec review C25).

## Ported files (ticket 49)

| SWDB file | MemAcc source (under the repository root) | Notes |
|---|---|---|
| `swdb/extensa/__init__.py` | `AgenticRefiner/refiner/` | package marker |
| `swdb/extensa/search.py` | `AgenticRefiner/refiner/a5/search.py`, `AgenticRefiner/refiner/a5/outcomes.py` (outcome and stop-reason types only) | iteration-based plateau; D6 stop reasons; D7 call accounting; D8 feedback fields |
| `swdb/extensa/leakage.py` | `AgenticRefiner/refiner/a5/leakage.py` | unchanged patterns |
| `swdb/extensa/probes.py` | `AgenticRefiner/refiner/legality_testing/contract_check.py`, `AgenticRefiner/refiner/legality_testing/dsl_contract.py` | emitter, negative controls, splice, read-back; no extent upgrade, no CUDA, no region scan |
| `swdb/extensa/profiles.py` | `AgenticRefiner/refiner/a5_certification_profiles.py` | data model and validation only |
| `swdb/extensa/synthesis/__init__.py` | `AgenticRefiner/refiner/synthesis/__init__.py` | package marker |
| `swdb/extensa/synthesis/certify.py` | `AgenticRefiner/refiner/synthesis/certify.py` | two-binary build, post-hoc seed, sanitizer precondition, named checks |
| `swdb/extensa/synthesis/mutants.py` | `AgenticRefiner/refiner/synthesis/mutants.py` | self-contained mutant headers |
| `swdb/extensa/synthesis/families.py` | `AgenticRefiner/refiner/synthesis/families.py` | fixed BFS-relevant family table; contracts from SWDB's typed library |
| `swdb/extensa/synthesis/spec.py` | `AgenticRefiner/refiner/synthesis/spec.py` | cpu_like harness only |
| `swdb/extensa/synthesis/synthesize.py` | `AgenticRefiner/refiner/synthesis/synthesize.py` | provider launcher `synthesis` role |
| `swdb/extensa/synthesis/testgen_backend.py` | `AgenticRefiner/refiner/synthesis/testgen_backend.py` | provider launcher `independent_test_generation` role |
| `swdb/extensa/synthesis/targets/__init__.py` | `AgenticRefiner/refiner/synthesis/targets/__init__.py` | package marker |
| `swdb/extensa/synthesis/targets/base.py` | `AgenticRefiner/refiner/synthesis/targets/base.py` | unchanged |
| `swdb/extensa/synthesis/targets/cpu_like.py` | `AgenticRefiner/refiner/synthesis/targets/cpu_like.py` | imports only |
| `swdb/extensa/synthesis/differential_oracle.py` | `AgenticRefiner/refiner/differential_oracle.py` | unchanged |
| `swdb/extensa/synthesis/shape_classes.py` | `AgenticRefiner/refiner/synthesis/shape_classes.py` | pack, regroup, gather, gather_stream and bin_drain generators only |
| `library/library_operations/drivers/{gather,regroup,gather_stream,bin_drain}_{ref,cand,run}.cpp.tmpl` | `AgenticRefiner/refiner/synthesis/drivers/` same names | SWDB reference header; no timing; frame check |

## Ported files (ticket 50)

| SWDB file | MemAcc source | Notes |
|---|---|---|
| `library/library_operations/drivers/pack_{ref,cand,run}.cpp.tmpl` | `AgenticRefiner/refiner/synthesis/drivers/pack_{ref,cand,run}.cpp.tmpl` | runtime chain depth; no timing; frame check |
| `library/library_operations/drivers/pack_executor_cand.cpp.tmpl` | `AgenticRefiner/refiner/synthesis/drivers/pack_cand.cpp.tmpl` | drives `PackExecutor` instead of a SynthBackend hook |
| `library/library_operations/pack.hh` | `DataLayoutAPI/data_layout.hh`, `DataLayoutAPI/data_layout_impl.hh` (`PackExecutor` base path) | entry `operation.pack_executor`; semantics from `AgenticRefiner/transformations/pack/pack_executor.yaml`; adds a `packed_size()` accessor |
| `library/library_operations/controls/pack_executor.{off_by_one_index,dropped_chain_level,aliasing_write}.hh` | as `pack.hh` | negative controls: one mutation each |
| `library/library_operations/pack_executor.yaml` (entry, not code) | semantics of `AgenticRefiner/transformations/pack/pack_executor.yaml` | experimental tier; origin is the Extensa commit and paths |

## Ported files (ticket 51)

| SWDB file | MemAcc source | Notes |
|---|---|---|
| `library/library_operations/binning.hh` | `DataLayoutAPI/update_binning.hh` (`BinPlan`, `CpuBinDrainBackend`, `UpdateBinningExecutor`) | entry `operation.update_binning_executor`; semantics `AgenticRefiner/transformations/binned/binned_update_executor.yaml`; base Fast path, no advisor |
| `library/library_operations/relabel.hh` | `DataLayoutAPI/vertex_relabel.hh` (`VertexRelabelExecutor`) | entry `operation.vertex_relabel_executor`; semantics `AgenticRefiner/transformations/relabel/vertex_relabel_executor.yaml`; `std::stable_sort` replaces the parallel merge |
| `library/library_operations/regroup.hh` | `DataLayoutAPI/data_layout.hh`, `DataLayoutAPI/data_layout_impl.hh` (`RegroupExecutor`) | entry `operation.regroup_executor`; semantics `AgenticRefiner/transformations/regroup/regroup_executor.yaml` |
| `library/library_operations/gather_staging.hh` | `DataLayoutAPI/gather_staging.hh` (`GatherStagingExecutor`) | entry `operation.gather_staging_executor`; semantics `AgenticRefiner/transformations/staging/gather_staging_executor.yaml` |
| `library/library_operations/drivers/{update_binning,vertex_relabel,regroup,gather_staging}_executor_cand.cpp.tmpl` | `AgenticRefiner/refiner/synthesis/drivers/{bin_drain,gather,regroup,gather_stream}_cand.cpp.tmpl` | drive the executor class |
| `library/library_operations/drivers/relabel_{ref,cand,run}.cpp.tmpl` | `AgenticRefiner/refiner/synthesis/drivers/gather_{ref,cand,run}.cpp.tmpl` | SWDB addition adapted for relabeling |
| `library/library_operations/controls/{update_binning,vertex_relabel,regroup,gather_staging}_executor.*.hh` | as the body they mutate | three negative controls per entry |
| `library/library_operations/certification/v1_1/driver.cc` | `AgenticRefiner/refiner/synthesis/drivers/{pack,gather,regroup,bin_drain,gather_stream}_run.cpp.tmpl` | ticket 77 (2026-10-05 ET): trusted 1.1 driver; same arguments, inputs, canary and frame check; records instead of prints |

## Original SWDB files that use the port (not ported, no MemAcc header)

`swdb/library_operations.py`, `swdb/extensa_boundary.py`, `swdb/campaign.py`,
`library/library_operations/reference/movement_reference.hh`; from ticket 77 (2026-10-05 ET)
`swdb/library_operation_blinding.py` and `library/library_operations/certification/v1_1/record.cc`.

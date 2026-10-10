# 50 — Tracer: certify one library operation (packing)

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** resolved
**Blocked by:** 11, 47 (all resolved). Ticket 02 removed: this ticket proceeds under the accepted Q66 assumption (Apache-2.0 WITH LLVM-exception, pending Peter's confirmation).
**Spec:** `../spec.md`

**What to build:** A library operation certifies end to end against a plain C++ reference.

## Acceptance

- [x] `library/library_operations/pack.hh` holds the base `PackExecutor` path (one-level and chained `load_to_pack`), extracted from MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76` `DataLayoutAPI/data_layout.hh` and `data_layout_impl.hh` with only its dependencies. It builds with `-std=c++11 -O3` and carries SPDX and provenance headers.
- [x] Its library entry is in the experimental tier, with origin set to the Extensa commit and the paths `DataLayoutAPI/data_layout.hh` and `AgenticRefiner/transformations/pack/pack_executor.yaml`. Its semantics come from that YAML (`output_equivalence: bitwise_identical`).
- [x] A plain C++ reference semantics, a differential-test driver adapted from `refiner/synthesis/drivers/pack_{ref,cand,run}.cpp.tmpl`, and at least three negative controls exist. The controls are an off-by-one index, a dropped chain level and an aliasing write. `swdb certify` certifies the entry and rejects each control by a named check.
- [x] `swdb validate` rejects a library-operation body that includes a DX100 header or calls any `maa_*` function (fixture test).
- [x] The entry and its files are listed in `swdb/extensa/PROVENANCE.md` (created here if ticket 49 has not created it yet).

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 21:08 ET (agent, under Yan-Ru's standing implementation approval).

What was built:

- `library/library_operations/pack.hh`: the base `PackExecutor` path (`initialize_packed_array`,
  one-level and chained `load_to_pack`, `get_packed_value`, `packed_ref`, `write_packed_value`)
  from MemAcc `DataLayoutAPI/data_layout.hh` and `data_layout_impl.hh`, timer removed, standalone
  C++11, SPDX and provenance headers. Builds with `-std=c++11 -O3` (test).
- Entry `operation.pack_executor` (`library/library_operations/pack_executor.yaml`): experimental
  tier (no review), origin MemAcc commit plus `DataLayoutAPI/data_layout.hh`,
  `DataLayoutAPI/data_layout_impl.hh` and `AgenticRefiner/transformations/pack/pack_executor.yaml`;
  semantics from that YAML (`output_equivalence: bitwise_identical`), its two structured legality
  predicates as formal halves (`alias(src[], packed[]) == false`; the chain read-only predicate,
  discharged `assumed` with the frame check as evidence).
- Plain C++ reference `swdb_ref::pack_gather` (`reference/movement_reference.hh`), driver
  `drivers/pack_{ref,cand,run}.cpp.tmpl` adapted from Extensa's pack templates (runtime depth 1
  or 2, no timing, frame check) and the adapter `drivers/pack_executor_cand.cpp.tmpl` that drives
  `PackExecutor`.
- Three negative controls in `controls/`: `off_by_one_index` (differential_mismatch),
  `dropped_chain_level` (differential_mismatch), `aliasing_write` (frame_violation).
- Profile `library/profiles/pack_executor.yaml`: sanitized and OpenMP (4 threads) builds,
  12 cases (depth 1 and 2, six index patterns), sizes n=257, n_src=1031.
- `swdb certify operation.pack_executor --profile pack_executor` certifies: both differential cells
  and the contract-probe cell pass; every control is rejected by its named check.
- `swdb validate` rejects a library-operation body that includes a DX100 header (`MAA*`,
  `dxc_*`, `*dx100*`) or calls `maa_*` (`swdb/library_operations.body_problems`, hooked in
  `Library.validate`).
- `swdb/extensa/PROVENANCE.md` lists the body, adapter, controls, templates and entry.

Tests: `tests/test_extensa_library_operations.py` (8 cases at this commit): certification with
named-check rejection of all three controls, probe in the certification build only (the OpenMP
candidate binary is probe-free), origin and headers, C++11 `-O3` build, three DX100 body
rejections. With `tests/test_extensa_machinery.py`: 36 passed.

Assumptions (agent-decided, revisable):

- The packed-buffer read API is used by the adapter (`get_packed_value`); `packed_size()` is a small
  SWDB accessor addition, noted in PROVENANCE.md.
- The aliasing control writes through `const_cast` into the source; the driver's input frame check
  is the named check that catches it.

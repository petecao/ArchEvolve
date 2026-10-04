# 50 — Tracer: certify one library operation (packing)

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md) D1, D11)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 47 (all resolved). Ticket 02 removed: this ticket proceeds under the accepted Q66 assumption (Apache-2.0 WITH LLVM-exception, pending Peter's confirmation).
**Spec:** `../spec.md`

**What to build:** A library operation certifies end to end against a plain C++ reference.

## Acceptance

- [ ] `library/library_operations/pack.hh` holds the base `PackExecutor` path (one-level and chained `load_to_pack`), extracted from MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76` `DataLayoutAPI/data_layout.hh` and `data_layout_impl.hh` with only its dependencies. It builds with `-std=c++11 -O3` and carries SPDX and provenance headers.
- [ ] Its library entry is in the experimental tier, with origin set to the Extensa commit and the paths `DataLayoutAPI/data_layout.hh` and `AgenticRefiner/transformations/pack/pack_executor.yaml`. Its semantics come from that YAML (`output_equivalence: bitwise_identical`).
- [ ] A plain C++ reference semantics, a differential-test driver adapted from `refiner/synthesis/drivers/pack_{ref,cand,run}.cpp.tmpl`, and at least three negative controls exist. The controls are an off-by-one index, a dropped chain level and an aliasing write. `swdb certify` certifies the entry and rejects each control by a named check.
- [ ] `swdb validate` rejects a library-operation body that includes a DX100 header or calls any `maa_*` function (fixture test).
- [ ] The entry and its files are listed in `swdb/extensa/PROVENANCE.md` (created here if ticket 49 has not created it yet).

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

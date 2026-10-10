# TMU mapping admission, revision 0.1.6

The catalog now includes `tmu-micro2023-fig8-spmv`, an exact mapping reference for the Tensor Marshaling Unit in MICRO 2023. This is the reviewed Fig. 8 two-lane CSR-SpMV operand-and-callback sequence. It is not the 2025 Tensor Manipulation Unit, a general gather API, or a validated simulator implementation.

Use an explicit inspection query:

```sh
python -m archevolve.hardware_catalog query --operation read --subtype csr_spmv_two_lane_operand_event_supply --design tmu-micro2023-fig8-spmv
```

An untyped exact query returns `mapping_reference`. Concrete payload/index widths return `needs_evidence`. Generic gather and stream-load queries do not select this record. Existing BFS candidate generation cannot invent its callback grammar. A separately supplied exact mapping intent retains the callback/operand result contract and requirements in comparison and intrinsic handoffs.

TMU supplies matrix/vector operands and ordered `ri`/`re` events; CPU callbacks perform multiplication, reduction, accumulation and result stores. The mapping excludes engine scatter, reduction and atomic-update directions. These exclusions are scoped to this mapping rather than hypothetical TMU extensions.

All ten requirements remain returned. Five contracts remain explicitly unknown: typed representation/ABI, physical response association, output-chunk consumption/reuse/final partial delivery, precise fault/drain/replay, and visibility beyond the paper-private assumptions. Empty/odd rows and numerical order remain adapter obligations. No public runnable artifact or concrete intrinsic signature is supplied.

The admitted source, twelve claims and mapping record are unchanged from [the standalone proposal](proposals/tmu-micro2023/proposed-catalog.json), reviewed at `53a85a43a230dc74b4cf1b98ffcbbbfc7c70d89d`. [Independent review](review/tmu-micro2023/README.md) accepted reference admission with 30 targeted checks and primary PDF/locator inspection. It does not certify executable mapping legality, hardware correctness, completion, coherence or performance.

Revision 0.1.6 has eight records across six families, 44 operation records, 96 claims and 31 sources. Four of the five added operation records are explicit unsupported-direction exclusions, not added accelerator instructions. The seven earlier design records and their operations remain unchanged.

The proposal and independent-review scripts reproduce their historical trial against base `6868383` in the preserved worker worktrees. Their original reports remain bound to that base; running them against the already-admitted catalog would attempt a duplicate addition. For the current catalog, use normal catalog validation and `tests/test_tmu_catalog_admission.py`, which checks the admitted record, generic-selection exclusion, typed unknowns and generated handoff preservation.

Integration validation: catalog schema/reference checks pass and the full software suite passes 97 tests. The admitted record and its source/claim objects equal the reviewed proposal, and the seven previous operation contracts and parameter states are retained. These software checks are not accelerator execution or a target performance result.

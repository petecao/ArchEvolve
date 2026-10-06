# Hardware mechanisms: October 6 handoff

The canonical catalog is [hardware-v0.1.yaml](../../catalog/hardware-v0.1.yaml), format v0.1/data revision 0.1.9: **10 records, 46 operations, 131 claims and 39 sources**. The records represent eight design families; versions, configurations and specific mappings are kept separate.

The three recently admitted mappings are TMU MICRO 2023 Fig.8 operand/event delivery, COBRA HPCA 2022 tuple binning and AXI-Pack DATE 2024 SELL staging. Their precise operation subtypes prevent a generic BFS gather from inheriting an unrelated mapping. DRT remains a research proposal outside this catalog's operation vocabulary.

## Mechanism evidence coverage

“Described” means located source evidence in a particular edition. It does not prove every policy, a valid mapping, fairness, coherence, timing or performance. Completion descriptions must be read with their stated visibility limits. “Unknown” is retained when the primary source or admitted annotation does not establish that dimension. TMU's detailed mechanism pass is the next catalog update.

| Record | Buffering | Coalescing | Reordering | Issue | Dependencies | Completion |
|---|---|---|---|---|---|---|
| dx100-paper-v2 | described | described | described | described | described | unknown |
| dx100-artifact-e4fc4af | described | described | described | described | described | described |
| terminus-micro2024-cas | described | unknown | described | described | unknown | described |
| terminus-micro2024-deferred | described | unknown | described | described | described | described |
| prodigy-hpca2021 | described | unknown | unknown | described | described | unknown |
| spzip-isca2021-push | described | unknown | unknown | described | unknown | described |
| maple-isca2022 | described | unknown | described | described | described | described |
| tmu-micro2023-fig8-spmv | unknown | unknown | unknown | unknown | unknown | unknown |
| cobra-hpca2022-tuple-binning | described | unknown | described | described | unknown | described |
| axi-pack-date2024-sell-required-l2-gather | described | described | described | unknown | described | described |

## What Josh can use

- [Machine-readable MAPLE fields](mechanism-handoff.json): thirteen located fields covering the required producer/consumer path, response ordering, credits, memory routes and explicit unknowns.
- [Compact MAPLE/DX100 comparison](compact-comparison.json): mechanism differences with source/scaffold scope retained.
- [Implementation requirements](implementation-requirements.json): what a concrete simulator implementation still needs to establish.
- [Executable finite scaffold](../../examples/mechanism-scaffolds/finite_gather.py): reservation/response/consume and line/offset association examples. It is **untimed and illustrative**, not an implementation of either published accelerator.
- [Published-model DX100 walkthrough](../dx100-internal-mechanisms.md) and [earlier mechanism annotations](../hardware-internals-v015.md).

MAPLE LIMA_PRODUCE performs the required queue-backed operation; ordinary LIMA/prefetch work is distinct. Slot reservation, response readiness, FIFO consumption/capacity release and CPU final use are separate events. Target-A coalescing and universal fairness/drain/reuse guarantees remain unknown. Pinned supplemental API/RTL observations are not authenticated to every paper-evaluated configuration.

The DX100 side of the finite comparison is a scoped local source abstraction, distinct from the catalog's public e4fc artifact and current private e766 model. Its caller-selected line order, 64-byte lines, generations and ACK-retained credits are declared fixture policies. They must not become implicit hardware capabilities or tuning defaults.

This revision adds source-backed mechanism annotations and shares local reviewed admissions. It does not change existing operation contracts, datatype support, requirements, parameter states or interface semantics. No runtime correctness, speedup, hardware wiring or composition legality is certified.

# Hardware catalog v0.1 — start here

Eric supplies the hardware knowledge. Josh owns architecture selection/composition and its implementation; Peter derives the software specification; Yan-Ru rewrites the benchmark.

The catalog is now the offline pipeline's default. Data revision 0.1.14 contains fourteen records and 53 operations, including scoped TMU, COBRA and AXI-Pack mappings and the explicit Pipette queue/RA and PHI bulk-scatter interfaces. The [current internal-mechanism handoff](mechanism-handoff-2026-10-06/README.md) includes the expanded MAPLE contract and an executable association scaffold. The [Pipette admission](pipette-catalog-admission/README.md) adds a committed/speculative queue lifecycle subset. Implementations and hardware performance remain unverified.

## What is here

- [catalog/hardware-v0.1.yaml](../catalog/hardware-v0.1.yaml): fourteen source-scoped records covering DX100 paper/artifact, two Terminus configurations, Prodigy, SpZip, MAPLE, TMU, COBRA, AXI-Pack, Pipette, PHI, ExTensor and Fifer; 53 operations.
- [Field reference](hardware-catalog-format.md): input, output, operation support, requirements, parameters and evidence fields.
- [Source evidence](hardware-catalog-evidence.md): paper/artifact distinctions and limitations.
- `archevolve/hardware_catalog.py`: optional validation/inspection/query interface. Direct YAML loading is also supported.

## First use

```sh
python -m pip install -r requirements.txt
python -m archevolve.hardware_catalog validate
python -m archevolve.hardware_catalog list
python -m archevolve.hardware_catalog query --operation read --subtype gather --pattern indirect
python -m archevolve.hardware_catalog query --operation read_modify_write --subtype cas --role execute
```

```python
from archevolve.hardware_catalog import load_catalog, query_catalog
catalog, digest = load_catalog()
result = query_catalog(catalog, operation="read", subtype="gather",
                       address_pattern="indirect")
```

A query returns relevant source-backed capabilities and unresolved conditions. A match is not a legal rewrite or a performance recommendation. Prefetch assistance does not supply the required gather result; returned-old data does not establish CAS semantics. Fixed reference sizes are not chosen tuning values.

## Scope of tonight's prototype

The catalog describes existing design/version/configuration operations. It is not an exhaustive survey, a simulator generator, or a composable hardware building-block library. MAPLE is now represented; MAD, IMPICA, HATS and other important families remain possible future coverage. Reusable mechanisms and compatibility constraints are still needed for general composition; these ten records are grounded examples, not the only architectures the agent may propose.

Suggested integration: read this YAML as hardware knowledge alongside Peter's features. Josh decides how to retrieve/use it and how to realize a candidate; keep its source editions, support status and unresolved requirements attached. No coupling to Eric's separate offline demo is required.

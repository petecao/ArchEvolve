# Hardware catalog v0.1 — start here

Eric supplies the hardware knowledge. Josh owns architecture selection/composition and its implementation; Peter derives the software specification; Yan-Ru rewrites the benchmark.

This handoff adds a standalone catalog and optional loader. It does not switch the existing pipeline to it or modify the ensemble agent, normalizer, seed, profiles or generated diagrams.

## What is here

- [catalog/hardware-v0.1.yaml](../catalog/hardware-v0.1.yaml): six source-scoped records covering DX100 paper/artifact, two Terminus configurations, Prodigy and a SpZip mapping; 32 operations.
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

The catalog describes existing design/version/configuration operations. It is not an exhaustive survey, a simulator generator, or a composable hardware building-block library. MAPLE, MAD, IMPICA, HATS and other important families are being reviewed for expanded coverage. The next representation step is reusable mechanisms plus compatibility constraints; these six records are grounded examples, not the only architectures the agent may propose.

Suggested integration: read this YAML as hardware knowledge alongside Peter's features. Josh decides how to retrieve/use it and how to realize a candidate; keep its source editions, support status and unresolved requirements attached. No coupling to Eric's separate offline demo is required.

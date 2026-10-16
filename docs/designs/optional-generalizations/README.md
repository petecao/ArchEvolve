# Optional generalizations: proposal stage

The pipeline now proposes small generalizations alongside the **minimum observed
capability request**. These are candidates for the meeting's “cheap generalization”
idea; the tool does **not** establish that they are cheap, supported or legal.

Each proposal exposes one explicit integer offset or scale constant as a
configurable input. It preserves the observed value as the baseline setting and
retains the original block's types, source mappings, dependencies and obligations.
The minimum plan, catalog, selected candidates and parameter domains are unchanged.

![Minimum and optional generalization review flow](flow.svg)

## Concrete examples

| Case | Observed annotation | Optional request | Known baseline setting |
|---|---|---|---|
| BFS row end | `VertexOffsets[u + 1]` | `VertexOffsets[u + offset]` | `offset = 1` |
| Synthetic streaming access | `Y[i + 2]` | `Y[i + offset]` | `offset = 2` |
| Synthetic nested index producer | `D[2*i + 1]` | `D[2*i + offset]` | `offset = 1` |
| Same synthetic producer, separate proposal | `D[2*i + 1]` | `D[scale*i + 1]` | `scale = 2` |

For the original BFS, the row-end offset remains **1**. Other offsets would change
which edges are traversed; they are not free performance-tuning settings for BFS.
The proposal concerns possible hardware reuse for separately specified kernels.

The generated names are collision-free `ae_offset` / `ae_scale`. Each proposal
changes only one literal; the two nested-index proposals are alternatives, not an
automatic combined affine extension. The BFS annotation includes both row-start
and row-end accesses; only the row-end literal changes.

- [BFS review table and diagram](examples/bfs/generalizations.md)
- [BFS proposal YAML](examples/bfs/generalization-proposals.yaml)
- [BFS paired requests](examples/bfs/generalization-queries.yaml)
- [Synthetic mixed-access review](examples/mixed/generalizations.md)
- [Synthetic mixed-access proposal YAML](examples/mixed/generalization-proposals.yaml)

The synthetic input is the existing [mixed-access source sketch](../../../examples/planning/mixed-access.pseudo.cpp),
not a measured benchmark. BFS uses the manually bound source annotation at the
pinned artifact revision; it does not infer `u+1` from average stride statistics.

## What stays unknown

Every proposal explicitly leaves these fields null:

- Additional hardware support and requirements.
- Computation location: host, index producer, existing accelerator interface or a
  genuinely new hardware mechanism.
- Parameter width, signedness, legal values and configuration granularity.
- Software/interface changes and admitted parameter domain.
- Incremental area, power, latency and the cost model.

`cheapness_assessed`, `legality_verified`, `ready_for_implementation`, and
`selected` are all false. An observed constant is **not evidence that existing
hardware hardwires it**. The CPU or existing API may already supply the value;
the incremental hardware cost could be zero, but that remains unassessed.

Potential reuse across other constants is labeled a coverage hypothesis. No new
constant value, negative-offset case, datatype, atomic operation, ordering rule,
concurrency guarantee or workload is admitted by this stage. Integer arithmetic
in the annotation does not prove the source program's numeric/bounds behavior.

## How proposal generation works

1. Read the already computed minimum plan. Inspect only read requests.
2. Use their reported index expressions and source-context access expressions
   bound to the member's statement IDs. Do not mine arbitrary surrounding code.
3. Parse a small annotation grammar: names, attributes, subscripts, integer
   addition/subtraction/multiplication and signed literals. A top-level `and` may
   separate source-annotation subscripts; it is not emitted as executable C++.
4. For an explicit offset or scale literal, propose replacing that one occurrence
   with a fresh parameter name. Keep the original value and AST location.
5. Verify that restoring the observed literal restores the annotation AST.
   This is a **syntactic check**, not program/hardware equivalence verification.
6. Emit review questions and two separate requests: minimum and optional extension.

Function calls, casts, shifts, division, floating literals, Boolean expressions
outside the annotation list convention, unsupported C++ syntax and oversized
expressions are skipped with diagnostics. The parser never evaluates an expression.
No constant folding, macro expansion, datatype widening, automatic index-depth
extension or arbitrary source rewrite is implemented.

The default proposal budget is 32 (maximum engine setting 256). Truncation is
reported; these are software output limits, not legal hardware ranges. Identical
plan/site inputs yield stable proposal IDs. The minimum plan remains a separate
immutable artifact with `optional_generalizations: []`; the populated proposals
live in the new review artifacts rather than changing its selection contract.

## Minimum versus generalized database queries

The paired-query file contains the original block request and its existing
catalog coverage. The separate `capability-extension-query-v0.1` request contains
the full unchanged base request plus the explicit configurable-arithmetic request.

The current catalog's typed predicates describe operations, address patterns,
payload types and index widths. They do not establish these new configurable-index
requirements. Therefore the generalized result remains:

```yaml
status: unresolved_capability_not_expressed_by_current_catalog_predicates
supported: null
matching_designs: null
hardware_requirements: null
```

The existing matcher explicitly rejects a capability-extension query rather than
silently projecting it back to an ordinary gather/stream query. Minimum matches
are shown for context only; they do not certify the extension. Baseline query
results carry catalog ID, revision and a canonical-content hash. This differs
from the raw YAML-file hash used by the normal hardware-request provenance.

Eric/the hardware database can answer whether the minimum implementation already
supports the operand, what extension would be needed, and which legal parameter
domain applies. Cost comparison must use the same baseline mapping/configuration
and process/model assumptions. No generalized candidate is automatically selected
or forwarded as an implementation-ready intrinsic.

## Integration and output

The normal forward pipeline and saved-proposal bridge now emit:

- `generalization-proposals.yaml`: source-bound optional proposals and unknowns.
- `generalization-queries.yaml`: paired minimum/extension requests and unresolved answers.
- `generalizations.md` and `generalizations.mmd`: review table and architecture view.

The saved-proposal feedback records optional proposal IDs with unresolved support
and cost. These optional items do not change the minimum proposal's status or
enter performance ranking. Saved hardware choices still accept only existing
catalog design/role selections; they cannot select a new extension through an
extra field. Proposal generation and reviewing support/cost are distinct steps.

The same hand-authored replay choices were refreshed against the new pipeline's
implementation pins. The updated replay summary comes from a fresh run; previous
frozen run packages and source evidence were not overwritten.

Reproduce the BFS and mixed examples in a fresh directory:

```sh
.venv/bin/python tools/demo_generalizations.py --output-dir .cache/generalizations-demo
```

Or inspect an existing minimum plan against a catalog:

```sh
.venv/bin/python -m archevolve.generalization_cli \
  --plan path/to/hardware-plan.yaml --catalog catalog/hardware-v0.1.yaml \
  --max-proposals 32 --output-dir .cache/generalizations-review
.venv/bin/python -m unittest discover -s tests -p 'test_generalizations.py' -v
```

The standalone command snapshots the plan/catalog, refuses output overwrites and
makes no model/evaluator calls. The [example manifest](examples/manifest.json)
pins source inputs, generator files and generated artifacts. Actual RTL/API
changes, admitted domains, incremental costs and performance comparisons remain
unresolved pending owner/evaluator evidence.

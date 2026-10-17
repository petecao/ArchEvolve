# Hardware planning before catalog lookup

Requests for capability groups, not a physical partition, proved composition or cost-optimal clustering.

| Proposed block | Source requests | Required shapes | Catalog option status |
|---|---|---|---|
| block-indexed-read-d9d3cdfc04 | gather-a-read, gather-c-read | indirect | options_for_review |
| block-stream-read-3e4c92e98e | stream-x-read, stream-y-read | sequential | options_for_review |

## Before: independent requests

```mermaid
flowchart LR
  db["Hardware catalog"]
  r0["gather-a-read: A"] --> q0["Independent access query"]
  q0 --> db
  r1["gather-c-read: C"] --> q1["Independent access query"]
  q1 --> db
  r2["stream-x-read: X"] --> q2["Independent access query"]
  q2 --> db
  r3["stream-y-read: Y"] --> q3["Independent access query"]
  q3 --> db
```

## After: capability planning

```mermaid
flowchart LR
  db["Hardware catalog: options per planned block"]
  r0["gather-a-read: A"] --> b0
  r1["gather-c-read: C"] --> b0
  r2["stream-x-read: X"] --> b1
  r3["stream-y-read: Y"] --> b1
  b0["Indexed-read group (2 access requests)<br/>indirect"] --> db
  b1["Streaming-read group (2 access requests)<br/>sequential"] --> db
```

Grouping suggests shared capabilities, not simultaneous execution, a physical partition or permission to reorder.
Source dependencies, mutable reads, unresolved resources and CPU effects remain in the YAML.
A catalog option must cover every typed clause using one design record and one execution role.
Partial matches are retained as diagnostics, not silently combined into a new accelerator.

[Plan](hardware-plan.yaml) · [Catalog results](block-catalog-results.yaml)

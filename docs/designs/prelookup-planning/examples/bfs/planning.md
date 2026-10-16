# Hardware planning before catalog lookup

Requests for capability groups, not a physical partition, proved composition or cost-optimal clustering.

| Proposed block | Source requests | Required shapes | Catalog option status |
|---|---|---|---|
| block-indexed-read-5d48e03303 | access-02-read, access-03-read, access-04-read | indirect, ranged_indirect | options_for_review |
| block-effect-read_modify_write-cas-6e560e8702 | access-04-update | indirect | options_for_review |
| block-stream-read-bf7778b743 | access-01-read | sequential | options_for_review |

## Before: independent requests

```mermaid
flowchart LR
  db["Hardware catalog"]
  r0["access-01-read: queue.shared"] --> q0["Independent access query"]
  q0 --> db
  r1["access-02-read: VertexOffsets"] --> q1["Independent access query"]
  q1 --> db
  r2["access-03-read: g.out_neighbors_"] --> q2["Independent access query"]
  q2 --> db
  r3["access-04-read: parent"] --> q3["Independent access query"]
  q3 --> db
  r4["access-04-update: parent"] --> q4["Independent access query"]
  q4 --> db
```

## After: capability planning

```mermaid
flowchart LR
  db["Hardware catalog: options per planned block"]
  r0["access-01-read: queue.shared"] --> b2
  r1["access-02-read: VertexOffsets"] --> b0
  r2["access-03-read: g.out_neighbors_"] --> b0
  r3["access-04-read: parent"] --> b0
  r4["access-04-update: parent"] --> b1
  b0["Indexed-read group (3 access requests)<br/>indirect, ranged_indirect"] --> db
  b1["Separate update request (1 access requests)<br/>indirect"] --> db
  b2["Streaming-read group (1 access requests)<br/>sequential"] --> db
```

Grouping suggests shared capabilities, not simultaneous execution, a physical partition or permission to reorder.
Source dependencies, mutable reads, unresolved resources and CPU effects remain in the YAML.
A catalog option must cover every typed clause using one design record and one execution role.
Partial matches are retained as diagnostics, not silently combined into a new accelerator.

[Plan](hardware-plan.yaml) · [Catalog results](block-catalog-results.yaml)

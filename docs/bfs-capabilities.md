# BFS accelerator capability contract

Created: 2026-09-25 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

`swdb capabilities dx100-e4fc4af-4c --format json` returns the selected hardware
target and its supported operation records. These records describe the pinned
source and implementing model. They do not claim that the model was built,
that a binary executed, or that a candidate passed correctness. CPU intrinsic
queries retain their existing ISA-flag semantics independently.

The initial seven contracts cover signed 32-bit BFS register writes, streaming
and indirect loads, range expansion, scalar less-than, indirect vector stores,
and completion waits. Other DX100 calls and types are not implicitly supported
by these identities. Source evidence and build design are in
[the DX100 design](bfs-dx100-design.md).

## Proposal requirements

A proposal selects `hardware_target` and an optional `required_operations` list.
Each leaf requires exact operation, interface, interface-version, and model-
revision strings. Optional `semantics` requires exact values of named supported
semantic properties. Unknown, unsupported, mismatching, or malformed required
facts yield a durable unresolved capability outcome before candidate creation.

```yaml
hardware_target: dx100-e4fc4af-4c
require_executable_backend: false
required_operations:
  - wrapper: parent-update-sequence
    requires:
      - operation: dx100.mmio.v1.indirect-store-vector.i32
        interface: dx100-mmio
        interface_version: 1.0-e4fc4af
        model_revision: e4fc4afdf894f295442cef3604667a469fab8e62
        semantics:
          masked: true
          returns_old_value: true
```

A wrapper is a name plus a nonempty `requires` sequence; it inherits every
leaf requirement and cannot introduce support merely by naming a generated
symbol. Empty declarations, unknown required operations, unsupported semantic
claims, and identity conflicts remain unresolved. Expansion is bounded to
128 entries and eight nested levels. No other wrapper fields are interpreted.

`require_executable_backend: true` requires an identified `hardware_target`
marked built or verified with identified build evidence, even when
`required_operations` is empty or omitted. A missing or unknown target and a
source-only target produce a retained unresolved capability outcome before
candidate creation. The later evaluator must reopen and verify the exact
artifacts before executing. `false` or an omitted flag permits source-level
proposal work and does not bypass execution checks. For example, requiring
`cpu_atomic: true` on the scatter operation is unresolved: neither the API
name nor its optional returned old values establishes CPU CAS semantics.

## Operation records

`kind: operation`, `schema_version: '0.4'`, and the normal envelope fields apply.
The additional fields are:

| Field | Meaning |
|---|---|
| `name` | Actual source-level operation name |
| `interface` | Software interface `id` and `version` |
| `model` | Implementing model `id` and pinned 40-digit Git `revision` |
| `backend` | Evaluator backend identity, separate from interface and host |
| `support` | `source_supported`, `unknown`, or `unsupported` |
| `signature` | Exact callable signature or restricted operation specialization |
| `types` | Types covered by this contract; other API types are not inferred |
| `memory_effects` | Main-memory and scratchpad/register effects |
| `masks` | Predicate behavior and unmasked sentinel |
| `repeated_indices` | Duplicate-address behavior and unresolved ordering |
| `ordering` | Required issue ordering and concurrency restrictions |
| `completion` | Required completion interface before consuming results |
| `resources` | Operand-slot bounds `tiles`, `scalar_registers`, and `allocation` requirements |
| `build` | Required `headers`, `defines`, and `dependencies` |
| `semantics` | Named facts with `state`, `value`, `basis`, and `description` |
| `declaration_evidence` | API evidence with `uri`, source `path`, `sha256`, and inclusive `lines` |
| `implementation_evidence` | Corresponding executable-model source evidence with the same fields |

Resource counts are maximum distinct operands for one call, including optional
mask/result tiles. A sequence must also budget its concurrently live values;
per-call counts do not establish that the whole sequence fits. Exact CPU-versus-
accelerator ordering and duplicate winners remain unknown unless a contract
explicitly supports the required property.

## Hardware target records

`kind: hardware_target`, `schema_version: '0.4'`, and the normal envelope fields
apply. The additional fields are:

| Field | Meaning |
|---|---|
| `name` | Human-readable target name |
| `model` | Model `id` and pinned Git `revision` |
| `interface` | Software interface `id` and `version` |
| `backend` | Backend `id`, `readiness`, and `build_evidence` |
| `execution_host` | Optional physical `machine` reference; null until selected |
| `configuration` | Concrete target capabilities/settings; the evaluation protocol adds its exact comparison settings |
| `operations` | Operation record IDs supported by the selected target |
| `source_evidence` | Target source evidence with `uri`, `path`, `sha256`, and inclusive `lines` |

`backend.readiness` is `source_supported`, `built`, `verified`, or `unavailable`.
`build_evidence` contains identified `uri` and `sha256` entries; built/verified
states require at least one. These records describe readiness, while actual
execution results bind and verify binaries, configuration, workload, and host.

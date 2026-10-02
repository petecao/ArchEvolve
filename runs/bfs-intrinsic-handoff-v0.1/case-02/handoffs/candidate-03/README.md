# Draft intrinsic descriptions

Candidate: **terminus-micro2024-cas:update_execute** (needs_evidence).

Generated from located catalog contracts. Peter owns the concrete software spec; Eric resolves hardware constraints. ABI and implementation are pending review.

[Candidate and evidence](candidate.yaml) · [Structured draft](intrinsic-draft.yaml) · [Interface diagram](interface.mmd) · [Workload context](context.mmd) · [Mechanism checklist](mechanisms.mmd)

## term-cas

Propose cas for the matched accesses to parent, subject to the catalog's mapping requirements.

Role: **execute**. Source support: **paper_specified**. Realization: **native_primitive**.

### Inputs and placement

The following are workload intents. The exact operand list and signature require Peter/Eric's specification.

| Request | Array | Pattern | Requested payload / index bits | Statements |
|---|---|---|---|---|
| access-04-update | parent | indirect | int32 / 32 | bfs-td-parent-cas |

Design-wide software contract: Task dataflow graph and PE/operator configuration; task arguments, partition mapping and deferred handlers.

Invocation: Core instructions enqueue/dequeue tasks, acquire/release partitions and respond to deferred operations.

### Result and behavior

Result: success_flag

Validity: Active inputs only.

Old-value behavior: unknown

Ordering: Local partition SWMR and partition queues protect conflicts; ROB preserves task enqueue result order. Shared-memory locks are additionally required across engines.

Completion: Task completion releases its partition; finished task waits for ROB turn before result dequeue.

Visibility: Task-level paper promise; precise CPU/cache write-visibility event beyond synchronization is unknown.

Type evidence: No universal datatype contract asserted.

Missing capability evidence: index_width_bits, payload_types

Missing workload evidence: none in the typed query; runtime placement/legality still require review

**Mutable target:** establish load freshness and synchronization before buffering or hoisting the access.

Limitations:

- Requires memory-unit/L2 atomic support. Not fetch-old.

## Preconditions and legality

The following catalog requirements remain undischarged:

- **term-graph** (Specific task and sparse data structure): Supply and map an actual task graph with return wiring and data-dependent traversal.
- **term-partitions** (Local engine and participating core): Ensure every conflicting task/host access obeys partition acquisition and release; wait for acquire notification.
- **term-global** (Shared writable data structures): Use shared-memory synchronization for conflicts across cores/engines.
- **term-atomics** (CAS primitive in this configuration): Establish memory-unit and L2 CAS support.

## Related accesses and side effects

A shared request group carries source context; it does not establish hardware fusion.

Reported workload update to preserve: CAS(addr=&parent[v], expected=curr_val, new_val=u). This is source/workload intent, not the proposed intrinsic signature.

- **bfs-td-traversal-and-discovery**: Source dependency chain from frontier load through row bounds and neighbor traversal to parent read and conditional CAS. The successful CAS also controls an explicit parent store and queue append. This context group is a manual proposal, not a proved single-accelerator mapping.
  Covered: access-04-update. Uncovered: access-01-read, access-02-read, access-03-read, access-04-read.

## Internal mechanism information

- **buffering**: unknown; annotation needed from Eric
- **coalescing**: unknown; annotation needed from Eric
- **reordering**: unknown; annotation needed from Eric
- **issue_policy**: unknown; annotation needed from Eric
- **dependency_tracking**: unknown; annotation needed from Eric
- **completion**: unknown; annotation needed from Eric

Missing descriptions do not imply that the hardware lacks the mechanism. No speedup is inferred from operation matching.

## Next review

- **Peter**: Confirm the matching source statements, region, phase and allowable replacement scope. Manual bindings are proposals; profiling placement is not confirmed.
- **Peter/Eric**: Specify exact operands, index arithmetic, masks/produced lengths, concrete types, invocation and completion API for each chosen operation or sequence.
- **Peter/Eric**: Discharge ownership, numeric domains, mutable-load freshness, ordering, repeated-target/concurrency and result validity requirements. Preserve CAS success and queue side effects.
- **Eric**: Add located internal buffering/coalescing/reordering/issue/dependency/completion details and conditions limiting performance.
- **Josh/Eric**: Establish whether related requests can share one legal mapping; the workload group and interface view do not prove combined execution.
- **Yan-Ru**: After Peter's spec is agreed, choose or synthesize an implementation and verify the rewritten kernel against the frozen correctness oracle.

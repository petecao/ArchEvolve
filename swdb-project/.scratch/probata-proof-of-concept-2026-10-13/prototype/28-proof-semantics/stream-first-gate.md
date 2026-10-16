# One-element stream metadata gate — 2026-10-16 ET

Prospective source/state refinement; actual public proof unrun. This successor
preserves the independent size freeze7e64298f and its external entry. First
caller scope: one nonempty u32 load with RF int32 values0/1/1 at IDs0/1/2,
core0/destination0/no condition, followed by real wait_ready(0), then size1 on
normal return (wrong0 on unchanged source). Payload CPU reads are excluded.

The approved seams are a source-pinned one-element stream transition API and
native source-excerpt comparison, followed by normal public `swdb prove`
positive/refusal controls. Finite trace tests cannot establish device liveness
or full source refinement. The implementation must not infer completion from
packet acknowledgement or call an eager prototype cover from a returned stub.

| Relation | Source / explicit conditional premise | Required boundary |
|---|---|---|
| Boot / RF / region | Pinned SPD constructor, explicit32tile/16384word/4core configuration; explicit RF0/1/1 and registered initialized line mapping | alloc/init never imply device freshness or RF contents |
| Original call | Exact real u32 template/default argument and original caller AST; three volatile64 stores plus fence | Strings/native packet equality alone cannot certify actual body/order |
| Packet/dispatch | Partial three-word receiver; successful IF dispatch marks Idle/unfinished and uint8 ready0→255; final-store acknowledgement | Acknowledgement never means completed data transfer |
| Request/response | Signed-int0/1/1 arithmetic, one nonzero aligned64B translated input line, exact request-table/response identity | Empty/reversed ranges, zero stride, other indices, unmatched responses refused |
| Memory environment | Explicit whole64B initialized object, mapping, stable coherent response/no conflicting CPU/device writes across all cores | Four-byte disjointness or distinct C objects alone insufficient |
| Completion | Response accounting, packets-sent and timing quiescence before size1/Finished/ready255→0 | No early size/readiness publication; bytes, initialization, lane-finished, status and ready distinct |
| Returned wait | Real core0 blockinguint16 read returns1 only after ready0 | Conditional normal return; no total returning stub or fairness theorem |
| Formal policy | Explicit closed-layout partial correctness at blocking helper and caller; no general ACSL relaxation | No implicit terminates=true, finite delay cap or desired-result premise |

Mapping/coherence/isolated fresh epoch premises will be recorded with the
Probata proof-semantics maintainer as owner, pending Yan-Ru59 review. These are
conditional source/environment bindings, not claims of physical boot, proved
MMU/coherence implementation, or all-caller safety. The full interface/current
production0.2 and ticket28 remain open. Source notes and29 checked pins:
`/private/tmp/probata-t28-stream-load-correspondence-20261016.{md,json}`.

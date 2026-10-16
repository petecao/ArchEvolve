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

The post-issue model phase is logically uncovered, not a theorem that physical
hardware remains Idle when the CPU receives its acknowledgement. Completion may
already have occurred. An isolated no-observation/no-interference correspondence
can defer its unobserved events to returned wait; that relation remains an
explicit source-model obligation with maintainer ownership/pending59. Native
SPD snapshots compare selected event prefixes only, not every possible schedule.
The real wait's conditional return must establish completion in either case.

Additional immutable RequestTable closure source was read on2026-10-16:
Tables.hh SHA5ea6a7caff7ca690aa9ce19096c0e686dfa52716e4dbf19d17348c9235011b43
and Tables.cc SHA9bd8aa4103fb6e7617fdd4c514a917329b8e7b8345738ed6e5d82f818df7dfa6,
at the samee4fc4af commit. RequestTable::get_entries matches exactly by physical
line, removes only that line's valid entries and leaves unmatched entries intact.
The selected empty positive-capacity table maps one lane0/word0 entry. Full MMU
translation/coherence closure is still separate: StreamAccess::translatePacket
asserts synchronous completed fault-free translation, so that source-domain
condition must be explicit, never silently assumed for arbitrary timing MMUs.

## Explicit partial subject — 2026-10-16 ET

The original total-correctness summary is refused. This fixture declares a
separately versioned original unit `contract.dx100_stream_partial_fixture.v1`,
an exact `proof_unit.correctness_policy` binding the current fixture semantics
ID/hash and source policy, and its own partial fixture method. Its record subject
is `partial_library_summary`; existing generic `library_summary` dependency
readers cannot consume that record. Only this explicitly qualified original
contract admits `terminates \false` for the enclosing unit as well as all three
MMIO helpers. A successful conditional postcondition would establish no total
correctness, progress or hardware liveness result.

The event compression still has an unverified all-schedule source-refinement
duty. The source epoch, stable mapped coherent full64-byte line, absence of
competing commands/writes from every core and lack of intermediate observations
are explicit owned environment premises pending59. Native source-event prefix
agreement establishes finite feasibility and metadata projection only. The
assumed contract/body and compression relation are identified as unverified TCB
duties in every touched record. They are not desired-result premises or a source
refinement theorem. Whole ticket28 remains incomplete.

The early native test name about an acknowledgement leaving the tile unfinished
meant the selected immediate dispatch prefix. It has been renamed to say that
explicitly: hardware may already complete before the CPU observes its ack. No
claim equates the logical uncovered phase with the physical state at ack return.

Two preformal compiler controls exposed inherited lowering gaps: void source
calls were incorrectly given integer identity arithmetic; partial array
initializers serialized through Clang's `array_filler` lost their explicit
prefix. Type-driven integer identity and a checked scalar-prefix representation
repair these paths. Native C++/C ASan+UBSan controls retain `{7}` and `{7,2}` with
zero-filled remainders. Ambiguous, nested-filler or designated forms refuse.
The input's original64-byte extent/alignment is independently source-bound;
ordinary modular function entry does not assume that its current value is7.

The public input epoch explicitly requires a nonzero virtual base. StreamAccess
uses zero as its initial last-block sentinel; a nonempty line at virtual0 is
outside this source domain. The existing native guard already refused guest0;
the public owned environment certificate now states that boundary directly.
Physical0 is not declared a universal hardware error by this condition.

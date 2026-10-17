# Private lifetime frame: independent source review

Date: 2026-10-16 ET. Reviewer: `prefix10_review`.

**PASS as isolated preparation of nine pending conditional mathematical duties.**
No blocking source issue found. This review read source, retained artifacts and
receipts, used standard-library AST/JSON/hash operations and read-only Git, and
did not import the project or run its tests, harness, compiler, native tools,
solver, verifier or SSH.

| Reviewed source | SHA-256 |
| --- | --- |
| `swdb/vector_reallocation_private_frame.py` (8,197 bytes) | `062c68a138b4aeb0887f50490d405f3b1fdd50284e6e8404e096df02568982da` |
| `tests/test_vector_reallocation_private_frame.py` (3,086 bytes) | `57201957c346f832b7f63bd48d92714171ff876beb3a062d6bae905ff389be5e` |
| `swdb/heap_reallocation.mlw` (8,386 bytes) | `a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5` |

The heap theory is byte-identical to exact baseline
`c978393b119a3614229a37f0f2c8ca2a097c750b`. No heap semantics or current packet
counts change. Source search finds the new module referenced only by its own
artifact tests; it adds no adapter or caller-admission route.

## Mathematical assessment

The observation relation quantifies over every identity live in the incoming
`entry` heap. For each, `same_object` preserves allocated/alive/dynamic/writable
flags, extent and address; contents and initialization are preserved at every
integer position. It deliberately hides the identity counter, private allocation
history and dead private cells. This is an observational relation, not heap
equality or a source-level `assigns` theorem (`vector_reallocation_private_frame.py:12–25`).

| Duty | Why its conditional statement is sound in the unchanged theory |
| --- | --- |
| `entry.reflexive` | Each field, cell and initialization fact equals itself. |
| `automatic.frame` | Well-formedness excludes `fresh_id(h) = h.next` from all issued/live old identities; the total placement operation only changes that fresh identity and `next`. |
| `allocation.frame` | The assumed frame makes every incoming live identity live in `now`. Well-formedness of `now` puts each below `now.next`, so allocation at `fresh_id(now)` cannot affect them. This does not require an empty incoming heap. |
| `integer_store.frame` | A target not live in `entry` differs from every observed identity; nested memory/init updates affect only that target. |
| `pointer_store.frame` | The same separation argument applies to pointer-tag stores, including their initialization update. |
| `release.frame` | Release is identity for null or changes only the target's alive flag. Its target is outside the incoming live set. |
| `automatic_end.frame` | The existing `end_automatic` definition is release, with the same separation condition. |
| `cleanup.observation` | Both cleanup identities are outside the incoming live set, so their real release/scope-end transitions preserve it. Equality of each observed component also relates `now` to the cleaned heap. |
| `cleanup.exists_scalar` | Choose `final` as the actual cleanup result. At zero count the buffer is null and scalar is zero. At positive count, `int32_region` and `filled_prefix(...,7)` establish the first initialized integer cell and its value; capture it from `now`, then apply the preceding frame argument. No dead-buffer load is taken from `final`. |

The absence of availability/access premises from the elementary frame lemmas is
appropriate for these claims: the theory's transitions are total functions and
the conclusions concern only preservation of other identities. They do not
claim that the transition was legal C, that the resulting whole heap is
well-formed, or that actual source placement satisfies those arguments.

The final duty's receiver/buffer freshness, frame, typed receiver footprint,
dynamic/freeable buffer, initialized integer region and filled prefix are
explicit **local-state antecedents**. They have not been derived from the
original caller's entry contract. The module keeps that boundary explicit in
`proof_admission`, empty caller-premise/record lists and eight pending source
requirements (`103–124`). Actual source cleanup order, allocator TCB/internal
effects, nonescape, completed constructor/member dependencies and Typed+Var
correspondence remain open. Observational framing alone cannot establish
source-level allocator effects or the original `assigns` clause.

The new prelude contains definitions only. Each duty is emitted as a pending
`check lemma`, with no `axiom` or `assume` law and no previously admitted proof
dependency. Existing heap operations remain imported unchanged. No theorem has
been executed or admitted by this review.

## Artifact and retained-control assessment

The public `prepare`/`check` artifact includes the full theory, prelude, nine
separate goal files and manifest. Checker identity binds both module and theory.
The checker requires exact file and directory membership, refuses redirected or
special descendant paths, and compares every canonical byte (`130–155`).

The controls exercise public preparation/checking and refusal after four material
changes: replacing cleanup by `now` in the final goal, removing initialization
from observation, falsely marking the source/Typed bridge established, and adding
an acceptance file. Their assertions also preserve existential final heap/scalar,
pre-cleanup scalar loading, all nine duty identities and pending acceptance.
These are meaningful artifact-integrity checks; they do not prove the lemmas.

The retained RED receipt reports five missing-module failures; GREEN reports five
passes with zero external/native attempts. The green module/theory/test copies
match current bytes. Independently reconstructing each goal from AST string
literals matches the retained green artifact, all nine manifest hashes and their
pending statuses. The harness uses a blank isolated package, restricted module
imports and an execution audit hook. This review inspected rather than reran it.

| Retained evidence | SHA-256 |
| --- | --- |
| `prototype/25-prefix10-resume-20261016/run_pure_private_frame.py` | `6cf188aba554c575d41a9bfb407784f258fedb498241e78d85f96d7478d6b287` |
| `/private/tmp/probata-resume-20261016-t25-private-frame-red/result.json` | `88f7c7e3ec31e40cfa1b89f6f16962c168fa116ff89deea3b8105e84ca067aad` |
| `/private/tmp/probata-resume-20261016-t25-private-frame-green/result.json` | `e0c035f27893fae4cc027d4edf450205eda1ea8a67200e654a60c08ad947a55b` |

This PASS supports retaining the isolated preparation. Fresh mathematical proofs,
source/Typed admission, original-caller proof and ticket acceptance remain open.

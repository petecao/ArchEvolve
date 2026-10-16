# Pure source-selector first gate

Created: 2026-10-16 ET. Ticket 28 remains partial.

The first vertical slice binds the actual pinned MMIO header's
`get_data_type<uint32_t>()` specialization, its canonical `unsigned int` source
argument, and its unsigned-char `DataType` return ABI to a closed C/ACSL constant
selector. It uses the public `swdb prove --summary ... --adapter wp` workflow.
The original C++ function has no entry precondition, state, or pointer parameters.
The positive and wrong-enum contracts use identical source bytes and differ only
in the desired postcondition (result zero versus one).

The fixture-only 0.2 library retains 0.1 byte-for-byte and inventories all 26 names
and 27 declarations, including both register allocator overloads and diagnostic
and pure helper calls. Only the u32 selector is admitted. All other rows state
`supported: false`; their false ACSL contracts/placeholders provide explicit
inventory/refusal bookkeeping and do not certify their C++ ABIs or behavior.
The five required trust entries identify the exact version/rule hash. Their
owner text distinguishes Eric's stale-copy premise from maintainer-owned premises
pending human freeze review in ticket 59. They are recorded even though this
pure helper makes no hardware command. No at-issue/history, initialization,
progress, ownership, IEEE, or reduction theorem is claimed by this slice.

Compiler controls include wrong source type, same-value source impostor,
declaration-only substitution, changed effective type traits, include-depth and
optimization-macro counterexamples, mismatched model ABI/result, explicit
unsupported calls, and attempts to use the stateless layout for device state,
entry assumptions, logic axioms, or extra active calls. The include-depth and
optimization controls first reproduced a material defect in an include-based O2
probe. The corrected certificate freezes preprocessing of the original main TU
under parser flags, then compiles those exact tokens plus its probe without
another preprocessing pass. Compiler/runtime and dependency bytes are pinned;
this is a trusted compiler fact and does not by itself prove the public target.

The prospective actual gate is `run_selector_acceptance.sh FULL_SHA pair`, with
`PROBATA_PYTHON` and an external `PROBATA_OUTPUT` supplied by the coordinator.
`positive` and `negative` select disjoint individual cases. The coordinator owns
live lane/global-lock preflight and wraps the entire script, including provenance
bootstrap, in one 8 GiB process-tree guard with a prospective 1,200-second whole
budget. The method uses the pinned three-solver portfolio, 30 seconds per goal,
mandatory RTE, initialization checks for every body, unfiltered initialization,
fresh cache/session, smoke checks, and one WP worker. No actual formal run is
admitted merely by committing this runner. Actual controls remain skipped unless
the coordinator deliberately sets the admission flag through this script.

A successful first gate would establish only this source-bound pure helper and
the public record/assumption path. A stateful size/readiness vertical follows;
full ticket 28 still requires all interface behaviors, typed storage/source
correspondence, CPU overlap, interthread history, ownership, region ordering,
visibility and progress premises, and the complete positive/negative matrix.

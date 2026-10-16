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


Actual fixture lineup — 2026-10-16 ET: the initial21ed Linux attempt stopped
before WP because the copied Mac fixture pinned Z3/Alt-Ergo4.8.14/2.6.0 rather
than admitted5.1.0/2.6.4. Its raw exit1 remains historical evidence; no actual
proof result is claimed. The successor requires an explicit coordinator input:
`SWDB_DX100_SELECTOR_ACTUAL_LINEUP` is a JSON object with exactly `frama-c-wp`,
`z3`, `alt-ergo` and `cvc5` version strings. The reviewed Linux binding is
`{"frama-c-wp":"33.0","z3":"5.1.0","alt-ergo":"2.6.4","cvc5":"1.2.1"}`.
There is no discovery/default in actual mode. Missing, partial, duplicate,
unknown-key, malformed-version or non33Frama input refuses before fixture work;
the runner validates before its compiler-provenance bootstrap. A separately
admitted Mac run can supply its exact solver versions explicitly.

Only four version fields in the copied synthetic method change. Production
backend method/runtime comparisons, source/model contracts, original caller,
mandatory flags and30-second portfolio budgets remain unchanged. The generated
method YAML and its proof-record pin bind those versions; runner runtime metadata
also records the explicit map. Stand-in mode ignores this actual-only setting
and retains its prior fixture versions. Root must bind the same map to its
reviewed binary/config metadata and admit a fresh clean-source run; this repair
and its pure/compiler/stand-in controls do not establish actual acceptance.

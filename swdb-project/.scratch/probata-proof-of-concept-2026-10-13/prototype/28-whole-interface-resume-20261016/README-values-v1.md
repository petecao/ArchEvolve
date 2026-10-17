# Deferred whole-interface value slice

2026-10-16 ET. Source-only implementation for independent review. No compiler,
native binary, verifier, SSH or production module was executed. The earlier
source packet remains byte-for-byte unchanged.

`value_builders.py` now supplies fixed private builders for all11 command
families. `whole_closed_routes_v1.h` selects each builder internally, so these
routes expose no callback parameter to a lowered caller. Existing private
adapters cover the other15 names and both register-allocation overloads. The
new source does not register public support or change current version0.2.

| Family | Deferred implementation |
| --- | --- |
| ALU scalar/vector | Immutable source tile/size and RF captures; size agreement; typed active arithmetic; comparison outputs useu32; inactive bytes retain their previous version. |
| ALU reduce | Source initializer, ascending lane fold `source OP accumulator`, active-only evaluation and typed RF output. Float MIN/MAX retain the actual source initializer constants. |
| Indirect load | Captured u32 indices and conditions, immutable size agreement, indexed issue-to-cover history reads and preserved inactive bytes. |
| Indirect store scalar/vector | Typed deferred stores, full existing line hazards, optional progressively modified old-result publication and inactive old-version aliases. |
| Indirect RMW scalar/vector | Existing ADD/MIN/MAX completion actions; six typed numeric paths; arbitrary permitted action order and optional old output. |
| Stream load/store | Source signed-int RF count formula and per-lane index; deferred source arithmetic guards and history/actions. No at-issue size/address evaluation. |
| Range loop | Exact pinned `RangeFuser.cc` continuation projection; INT32 regardless of T1; two tile outputs, two RF continuation outputs and two starting-tile sizes. |

Six exact, single-occurrence edits extend only the generated backend. A new
guard/pass-through node evaluates its predicate before the guarded value at
cover. It preserves immutable descending IDs and lazy branch selection. The
other edits add optional old-result publication for plain stores using the
existing action completion layer. `backend-extension-v1.json` retains both
sides of every edit; inverse substitution must recover the frozen original
backend hash. No original backend generator was edited.

All bounds remain classified checks. In addition to the original packet
obligations, the current value domain requires:

- Complete input/output values and sizes fit the selected two-element prefix.
  A larger possible deferred size refuses at cover, before its active values.
- Stream calls have nonnegative minimum, positive stride and nonempty range.
  Signed source byte multiplication, page-loop increment and stride increment
  must fit. The page size comes from an explicit runtime mapping; no configured
  page/line/physical translation is inferred here.
- A typed ordinary-array mapping supplies source base, base cell and extent.
  Its complete object fits the logical envelope; index, arithmetic, guest
  addition and typed-cell bounds remain checked. Actual C-object/physical
  provenance must be bound by compiler integration.
- Range inputs have equal sizes, nonnegative starting row, continuation j>=-1,
  positive stride and selected unsigned minima/maxima representable asint32.
  Signed postincrement is checked even after the final emitted element. The
  complete output fits the prefix, strictly below source tile capacity; source
  capacity stops in the middle of a row remain refused by this profile.

The primary range source was retained separately by root at commit
`e4fc4afdf894f295442cef3604667a469fab8e62`. Its Work loop uses unsigned bounds
against signed continuation state; this slice checks the stated common domain
before applying the equivalent signed/count projection. Skipped rows preserve
j, active completed rows reset j to-1, and an entry row beyond size remains
unchanged. This is an owned source/MMIO normal-return recipe, not a new hardware
or body theorem requirement.

Five pure source/algebra controls pass. They check exact reversible backend
edits, all11 fixed routes, absence of issue-time `dxm_cover`/`dxm_value` calls,
guard-first/lazy initializedness, immutable history versions, and54 direct
primary-loop versus count/slot range cases. These controls do not execute C.
The initial log records one positive-fixture mistake: a continuation requested
six outputs from a two-value profile; the corrected valid fixture requests one.

`whole_values_native_v1.c` is an **unexecuted** harness with86 prospective
controls:66 family/type cases,6 other-thread history→dependent-ALU cases,
6 subtraction fold-order cases,2 progressive old-result order cases and6
classified refusal cases. Its checks include inactive uninitialized operands,
known values remaining pending, deferred size/stride failures and active divide
by zero. These86 are new authored controls, separate from any historical native
results. Root can admit C11/C++17 sanitizer execution after source review.

The production seams remain concrete: register the closed source-definition
policy, bind an actual full-TU/ABI closure, copy typed scalar object bits, map
every CPU C-object/guest/physical access, compose the fixed builder route, replay
the source closure and evaluate public synthetic verdicts through the auditor.
Candidate code must not obtain private runtime setters, state arrays or builder
entry points. These integration and actual-evaluation steps remain necessary;
optional hardware refinement research is not a blocker.

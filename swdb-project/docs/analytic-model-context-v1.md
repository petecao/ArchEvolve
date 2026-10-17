# Analytic model context and composition

Updated: 2026-10-09 ET (code review fixes for tickets 09, 10 and 13; see the last
section). First written 2026-10-06 ET. The optional counting facts follow in ticket09;
this first foundation commit establishes the model and composition interface for ticket11.

`analytic_models.evaluate(region, mechanism, models=(), target_threads=1,
*, context=None)` retains the existing positional API. Context contains the frozen
`target_description_sha256`, `configured_threads`, `observation_contract`,
`selected_domain`, `composition_contract`, and exact region-filtered `source_calls`.
Missing or unsupported selection/context must produce a strict unknown bound.

Mechanisms optionally declare `accounting: resource_bound | additive_overhead`;
resource bound is the historical default. `selector` is model-defined. Existing
models refuse selectors they cannot interpret. `offload_setup` selects exact
semantic `event_ids`, counts `accelerator_calls`, and charges `seconds_per_event`
once as an additive overhead. An empty legacy list does not prove zero commands.

Each exclusive region is its largest required resource bound plus its declared
additive overheads. An unknown required component makes its region and total null.
Each trial is composed independently; the full-call median is computed afterward.
Diagnostic region/component medians cannot be summed into that full-call median.

The registry reserves `native_service_costs` and `memory_service_scenario` for
`swdb.analytic_cpu_service`. Its functions receive `(region, mechanism,
*, context=None)` and return the existing strict bound object. An unavailable
module returns an explicit unknown. A known result may return
`inputs.covered_calls: [{site, execution_count}]`; composition clears a missing
external body cost only when its exact site and full nonnegative observed count
match. Partial or unknown cost coverage does not waive an opaque body.

`analytic_extensions.finalize_estimate(result, *, store, protocol,
characterization, target_description)` delegates to the optional
`swdb.cpu_error_band` module after baseline ratio composition and before record
writing. Absence preserves the existing null error band and `within_error` verdict.
Ticket11 owns the optional module and separately frozen band dependency; a target
must never depend on its own band.

Changing the Python implementation bundle requires a fresh frozen protocol.
Historical records still validate against their historical snapshots and hashes.
All artificial test counts/rates retain `contract_fixture` evidence and fixture
binding; none is application or measured hardware evidence.

## Optional live object facts

Updated: 2026-10-06 ET. `swdb.live-count-context.v1` / `swdb.access.v2` adds
`observation_contract` and `memory_service_counts` optionally. Old records and
counted-payload hashes keep their original definition when these fields are absent.
The optional contract and all region/trial facts enter the registered count seal.
The runtime bundle digest includes both CountingRuntime.cpp and LiveObjects.hpp.

The process registry observes supported standard C/Itanium heap allocator calls
throughout the translation unit. It survives ROI resets; free/reallocation ends a
lifetime, and interior aliases retain its base/extent. Exact allocator ABIs exclude
placement-new/delete aliases. Opaque allocator bodies and unregistered stack/global
objects remain unknown. Runtime code is compiled separately without instrumentation.

`--state-budget` caps the object registry, persistent logical page state and each
trial's service sufficient sets. Existing virtual footprints compact overlapping
intervals and have the same declared interval cap. Overflow preserves known useful
request/byte work but marks affected unions/pages null with a named missing reason.
No address, base, access sequence, or decoded row list is serialized.

`region.memory_service_counts` has format `swdb.memory-service-counts.v1`, scoped
`per_run` or `per_trial`, method `source_normalized_ir_allocation_relative`, state,
missing reasons, and an assumption hash. `requests_by_update_kind` maps read/write/
RMW kinds to `[{element_bytes, requests: {value,basis,scope}}]`. Useful bytes,
lifetime line union, logical first-read/write pages, pre/in-ROI allocation pages,
and unknown-object request count use ordinary fact wrappers.

Lines are a declared logical 64-byte reporting convention; pages are logical 4096-byte
allocation-relative units. First access means first access **observed by the selected
normalized source observer**, including its observed pre-ROI accesses. Opaque
initialization, physical residency and native minor faults are unobserved. These
source accesses can be eliminated or hoisted by native optimization; they are never
physical CPU misses or measured hardware transactions. Fresh-page/residency cost
scenarios require separate assumptions and evidence.

Manual begin/end fixture calls retain independent trials with their original fixture
binding. Registered GAPBS source/input/ROI rules are unchanged. Aggregate and trial
regions share one strict schema; missing optional fields mean unobserved, not zero.

Executed call shapes use `swdb.call-shape-counts.v1`. Each region records exact
per-site length histograms and free-call allocation-lifetime size histograms,
with scoped execution counts. The standard allocator registry resolves a free
only while that exact allocation is live. Unknown lengths/lifetimes and bins
refused by the global state budget remain explicit; execution totals still
include them. No pointer, allocation list, or call order is serialized. A model
requiring lengths must cover every counted bin and unknown event before clearing
an opaque call cost. Registered C++11 source flags also apply to the runtime.

Optional `observation_contract.native_runtime` seals the actual counted process's
loaded-image inventory, available file hashes, Clang binary/version, and only
OMP/KMP/GOMP/MALLOC settings plus library, interposer and allocator controls from its launch environment. A sealed `swdb.native-environment.v1` scope lists prefixes and exact variable names; exact controls retain an explicit null when unset, and omitted prefix variables mean unset under that declared scope. Old receipts without the declaration cannot prove the expanded scope.
This is the instrumented count binary's identity; it does not certify a separate
native timing binary. A library unavailable as a regular file (for example a
macOS shared-cache image) keeps its hash null and a named missing fact. Historical
receipts without this optional field keep their prior identity and unknown scope.

Every observer entry and serializer uses a thread-local reentrancy guard. C++
weak-ODR helpers linked from the instrumented application can therefore serve the
runtime without recursing into its locked counters or charging observer work.
The guard affects that observer thread only; other application workers retain
normal accounting. The counted contract names this isolation policy.

Generic offload resource models consume only the requested target-description
hash's `swdb.logical-address-counts.v1` entry at `derived_logical_transactions`
level. Selectors declare `domain: offload`; unsupported selectors remain unknown.
`reorder_window_rows` applies row-group miss/hit service divided by effective
memory parallelism. `fetch_queue` takes the maximum of admission service and the
capacity/latency lower bound. `tile_staging` divides dynamic semantic staged
bytes by staging rate. These resource bounds compete; semantic issue/setup
remains additive. Known zero work needs no unused parameters. Unknown work or a
wrong target hash keeps the bound and total null. None measures physical queue
occupancy, row-buffer behavior, bus traffic, or asynchronous execution.


## Live functional command observations

Updated: 2026-10-06 ET. A target optionally declares
`swdb.functional-observation.v1`: exact command/backend aliases, intrinsic and
operation IDs, source hashes, operand bindings, target-access producers and
bookkeeping source functions. Production references pin shipped files. Commands
are bound before inlining; access roles use the original debug subprogram plus
its file hash after normalization. A same-array reference check cannot inflate
target traffic. Unmatched target access roles remain unknown. Explicit debug
`#line` overrides are refused for production bindings.

Thread-local guards deduplicate only declared nested backend aliases. They clear
on normal and Itanium unwind paths. A bounded shadow depth suppresses deeper
unsupported observations until those frames leave; unknown scope survives in
the receipt. Observer scaffolding is tagged and excluded from source work. Signed
negative active extents are unknown. Offload-only regions remain in trial records.

Target reads expand to declared transaction lines and close independent fixed
logical windows, including incomplete tails. Window state is bounded; exhaustion
keeps supported request totals while affected row/coalescing facts become null.
Placement is explicitly allocation-lifetime-relative and inferred. Its hash,
layout hash, request policy hash and window hash bind each target-specific count.
Addresses, access sequences and decoded rows stay in process memory. This does
not establish physical placement, hardware traffic, row state or scheduling.

The native fixture suite hand-checks alias deduplication, straddling byte ranges,
partial windows, missing objects/windows, row/nesting budgets, reference-check
attribution and unwind restoration. Fixture evidence remains `contract_fixture`.


## Count reuse under an identical observation contract (2026-10-06 ET)

A new functional characterization retains its complete counted target-description snapshot and a canonical, versioned `swdb.observation-policy.v1` digest. Its classification table remains immutable for historical validation; later classification changes require a new policy version. Only named rate/cost parameters with their declared units and record metadata/provenance are classified as observation independent. The model, selector, accounting policy, target identity, thread count, commands, aliases, source/backend pins, widths, layout, request/coalescing policy, logical window and placement remain in the digest. Literal values are required by the v1 layout/window/request schema. If a retained policy field names a removed rate parameter, its resolved fact is also pinned. Every extra or unknown field/parameter remains in the digest; it cannot gain admission by resembling a rate. Queue/cache capacity changes also require fresh counts under this conservative rule.

The original characterization and execution receipt are never rewritten. An estimate for a rates-only description exposes `count_reuse` with both counted and requested target hashes, the unchanged characterization hash, complete policy digest and original observation-context hash. The original context includes the state budget, source/LLVM/runtime bundle identities, loaded libraries and declared environment controls. Production normative bindings also pin the counted registered target configuration. Changing the original context fails its count receipt; a new description cannot request a new state budget through reuse. Changing any observation policy requires a fresh count. Historical descriptions/counts continue to work at their exact original hash; historical receipts without the complete snapshot cannot reuse rows for a changed description.

Numeric provenance is still checked recursively by ADR 0013 and pinned by the frozen protocol. A rates-only change does not waive input/source/ROI/trial/runtime binding, grant physical DRAM placement or convert logical row groups into measured row hits. Error-band bindings are independently frozen protocol evidence and never modify the counted observation policy.

## Exact source memory primitives

Updated: 2026-10-06 ET. Optional `access_patterns[].primitive_semantics` uses
`swdb.source-memory-primitive.v1` and describes the normalized LLVM load/store/
atomicrmw/cmpxchg instruction. It retains scalar value kind and bit width (pointer
width comes from that module's DataLayout), vector flag, exact LLVM ordering,
CAS failure ordering and weak flag, volatility, and exact atomic update opcode.
A store can retain its arithmetic value producer's opcode; this alone does not
establish a read-modify-write or matching loaded address. Existing access IDs,
coarse update buckets, counts and callback ABIs are unchanged.

Model context `source_accesses` contains that region's exact static/dynamic access
patterns, including trial-scoped element counts. A service model must cover every
executed site in each claimed kind/width cell and refuse unsupported or absent
primitive facts. The optional facts are source semantics, never native instruction
counts, physical requests, or CPU timing evidence. Historical absent fields remain
unknown; registered receipts seal new facts with their counted payload.

## Code review fixes (2026-10-09 ET)

These rules apply to new counts and estimates. Existing records keep their saved
payloads and still validate.

**Unknown work ranks.** Each unknown row in the parameter report now has
`work_multiplier` and `work_rank`.
- `work_multiplier` is the counted work the parameter scales in its own bounds:
  operations for a compute rate, bytes for a bandwidth or staging rate, requests for
  a row, queue or latency parameter, events for setup.
- Each trial sums its region rows. The value is the trial median, or the run sum
  when there are no trials. Unknown work stays null.
- `work_rank` is a dense rank by descending work among unknowns with the **same
  unit**. At any common value, a bound of that unit grows linearly with its work.
- Unknowns with different units are never ranked against each other. Without values
  they share no scale. `impact_rank` stays null for every unknown.
- Validation replays both fields from the saved bounds.

**Mechanisms that share a model.** The report matches each parameter to its own
mechanism by order: the k-th row of a model in one field is the k-th mechanism with
that model and accounting. Labels after the first carry `#2`, `#3` and so on. The
per-region trial summary now keeps every same-model row instead of merging them.

**Outside-operand accesses.** A target-role access can reach a registered heap or
global object that is not the command's declared operand.
- By default it is backend scratch, as before: for example DX100 tiles. It is
  counted in raw `outside_operand_accesses` and noted on the region's logical counts.
- A description can list events in
  `outside_operand_policy.unknown_events` (with `basis` and `source`). For those
  events, such an access marks the command's counts unknown, with missing reason
  `target_access_outside_declared_operand`.
- Stack temporaries never trigger it.

**Event-selected staging.** `tile_staging` accepts `selector.event_ids`. It sums
the selected commands' exact useful bytes, and only when the region's logical
`staged_bytes` is known. An event the counted contract does not declare is unknown,
never zero. Row and queue counts are recorded per region only. For them, an event
selector stays unknown until per-event logical counts exist.

**Execution gaps.** `offload_setup` is unknown when the region's logical counts list
a command execution gap: `command_nesting_state_budget`, `unmatched_command_leave`,
`command_crosses_roi` or `semantic_command_binding`. Before this fix, a suppressed
or unmatched frame could undercount events while the result still looked known. The
characterization's `semantic_commands.complete` now merges every trial's gaps, not
only the first trial's.

**Layout.** A declared DRAM layout needs at least one `row` bit field. The optional
`dram_address_layout_provenance` (`basis`, `source`) records where the bit positions
come from. It needs a declared layout.

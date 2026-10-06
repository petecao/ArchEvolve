# Analytic model context and composition

Updated: 2026-10-06 ET. The optional counting facts follow in ticket09; this first
foundation commit establishes the model and composition interface for ticket11.

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
OMP/KMP/GOMP settings plus library search paths from its execution environment.
This is the instrumented count binary's identity; it does not certify a separate
native timing binary. A library unavailable as a regular file (for example a
macOS shared-cache image) keeps its hash null and a named missing fact. Historical
receipts without this optional field keep their prior identity and unknown scope.

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

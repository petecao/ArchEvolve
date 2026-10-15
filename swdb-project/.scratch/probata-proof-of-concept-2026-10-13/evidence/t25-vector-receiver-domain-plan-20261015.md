# Qualified nonallocating vector receiver models

Created: 2026-10-15 ET. Prospective design; no body proof or caller admission yet.

The first control is the public standalone `std_vector_int_operator_index` body.
Current policy refuses its opaque `this->data` origin before WP. The proposed exact
standard-model qualification states a live typed int backing array of capacity
`this->capacity`, initialized only through the live `this->size` prefix. The first slice adds no receiver/backing separation condition. The live typed
backing-object/lifetime domain is a supplementary semantic assumption absent from
the current readable predicate, never inferred from `valid` or initialization.
Size/capacity arithmetic, readable receiver, initialization and formation bounds
remain ordinary obligations under the original contract. No ACSL input premise is
added. The proof must be described as conditional on that typed representation.

The first slice is index-only; end/at remain later prospective work. Only exact
pinned nonallocating model functions may ever receive the domain.
The at guard retains its existing separately checked defensive-guard view. Check
original canonical hashes and exact AST parameter/field bindings; no arbitrary
member expression, same-spelled local, changed layout, allocation or pointer cast
gets an origin. Reconstruct the domain/view and original bytes before launch, pin
its checker/certificate in setup and settings, and retain all existing generic
pointer checks. No old input contract, source or WP obligation is suppressed.

First implementation deliberately refuses consumption of these newly qualified
model summaries by generic callers until a checked caller-domain discharge exists.
A successful standalone body record cannot silently justify arbitrary caller
storage. Existing owner/pipeline projections must keep their own explicit source
and allocation relations, and must not be relabeled as member body proofs.

Controls: original public prelaunch RED; exact qualified public stand-in GREEN;
changed model/field binding/layout/domain/view/contract/policy refusals; omitted
qualification and added hidden function refuse; bounds and initialization remain
present; generic caller cannot borrow qualified summary. Independently review
before one actual index body and a missing-domain negative. Extend to end/at only
after that first accepted original result. Allocating bodies remain separate work.

## User-requested closeout — 2026-10-15 ET

Deferred before implementation. No runtime source, proof checker, model contract
or caller admission was changed. Independent design review is saved beside this
plan. Original public control fails as expected at the existing prelaunch opaque
origin refusal (one failing future-feature assertion,1.28s; guarded wall1.62s).
The expected-feature test is retained as plain text under
`prototype/25-vector-receiver-domain/expected-feature-control.py.txt`, outside the
active test suite. Do not treat it as a passing regression or accepted feature.
Resume with an independently reviewed index-only conditional domain, explicit
supplementary assumptions and mandatory generic caller refusal. Do not infer
receiver/backing separation or capacity<=PTRDIFF_MAX from readable.

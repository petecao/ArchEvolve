# Independent vector receiver-domain design review

Created: 2026-10-15 ET. Review of the prospective index-only plan against current
`standard_range_model.py`, `std_models.py`, `wp_pointer_bounds.py` and
`wp_adapter.py`. Read-only code review; no solver, native run or body-proof credit.

Recommendation: proceed with **only `std_vector_int_operator_index`** as an
explicitly representation-qualified standalone body. The plan's exact canonical
source/AST/replay checks and generic-caller refusal are appropriate. The following
conditions bound that recommendation.

1. Separate additional semantic assumptions from unchanged ACSL text. Current
   `vector_readable` requires readable initialized receiver storage, size <=
   capacity, capacity-range validity and initialized live prefix. It does not
   state that the backing range belongs to one live typed allocation/object of
   the declared extent. That object/lifetime relation is an explicit additional
   representation domain, even if `acsl_input_premises_added` remains empty.
   Record it in the certificate and proof's assumptions/settings; describe any
   proof as conditional on it. An unqualified contract-body theorem is unsupported.
2. Omit receiver/backing separation from the first slice. The read-only index
   body needs no such strengthening. Current `vector_readable` does not imply
   separation, so adding it silently would reduce the original contract domain.
   If a later transformation requires it, list it as a supplementary semantic
   premise and make caller discharge explicit. Similarly, do not borrow
   capacity <= max_size from `vector_valid`: it is absent from `vector_readable`.
3. Preserve original size/capacity, n<size, validity, initializedness and pointer
   formation checks. Domain metadata grants an object origin, never numeric
   inequalities, initializedness, allocation success or a pre-proven RTE result.
   Scope the backing-object fact to positive capacity; zero capacity has the
   original null/data relation and must not acquire a fictitious positive object.
   Use entry-state immutable field bindings; no alias/rebinding/call exemption.
4. Close every caller entry point before any accepted qualified body record can
   be reused. `_imports` currently looks up standard models by content hash and
   imports proven contracts. Both ordinary model imports and summary routes must
   refuse this new qualification unless the existing checked owner/pipeline path
   independently establishes its own representation relation. A proven standalone
   record must not silently become an unrestricted reusable summary. Retain its
   semantic domain in read-time/current-record validation, not only launch logs.
5. Reconstruct qualification from exact canonical bytes and original AST IDs at
   launch; compare complete input/view, checker identity, fields, source and pins.
   The explicit no-qualification negative must stop before WP. A separate added
   hidden-function/mutated-field/view/contract/policy control should demonstrate
   the qualification cannot leak to another function or same-spelled expression.

The precedent in `standard_range_model` is a useful interface pattern, not evidence
that vector receiver facts already follow from the old ACSL contract. An index
body result says nothing about allocating members, arbitrary receivers, all C++
object lifetimes or finite native equivalence. Extend to end/at only after the
first original actual result and source/certificate audit; keep the original
end null/zero branch and the separately checked at guard intact.

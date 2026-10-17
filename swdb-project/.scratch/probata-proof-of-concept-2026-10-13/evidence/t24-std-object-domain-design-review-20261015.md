# Independent std empty-range contract review

Reviewed 2026-10-15 ET. Worktree `/private/tmp/probata-resume-t24`, observed HEAD `81ab6c06058e37fb4fbed399b48fb471d9787f0e`. Read-only review; no compiler, verifier, or remote jobs launched.

## Verdict

No blocking soundness objection to adding a separately named `std_models_object_domain` fixture contract on the identical original source/function. This is a conservative sufficient domain for the current checked pointer-origin proxy. It does not establish the original contract or characterize every valid C++17 empty range. Actual WP acceptance remains unverified until a fresh record proves every ordinary and smoke goal with unchanged RTE/initialization policy and fresh model dependencies.

## Exact proposed additional domain

Retain every original pre/post clause, source byte, and assertion, adding for each `p` in `{a,b}`:

```acsl
requires n == 0 ==> (p == \null || \valid_read(p) ||
  (\base_addr(p - 1) == \base_addr(p) && \valid_read(p - 1)));
```

For `n == 0`, this is exactly sufficient for `_in_object_or_one_past(p,p)` or the existing null-plus-zero alternative: live readable objects satisfy the first validity disjunct; live one-past values satisfy the same-base readable-predecessor disjunct; null is separately admitted. No initialized value is needed at n=0 because the unchanged function/model executes no element access. Requiring read validity of destination `b` at n=0 is sufficient and conservative; there is no destination write then. For n>0 the original valid/initialized source range, writable destination range, numerical bounds and separation continue to govern the caller. The new clause does not add a hidden adapter premise or change runtime semantics.

## C++17 interpretation and coverage

- N4659 [expr.add]/4 defines addition within an array including one-past, with a nonarray object treated as a one-element array. [expr.add]/7 explicitly defines null plus zero and null-null subtraction. Keep null admitted.
- N4659 [forward.iterators]/2 explicitly permits equal value-initialized iterators and describes the empty-sequence interpretation. Pointer types are covered by forward-iterator requirements. The general statement about singular iterators must not be used to reject all default/value-initialized null iterators.
- N4659 [iterator.requirements.general]/7-9 distinguishes dereferenceability from past-the-end and defines valid empty ranges. An empty range does not itself provide a dereferenceable object. Therefore the old empty `valid(a+(0..n-1))` precondition does not entail the current object-origin assertion at n=0.
- N4659 [alg.copy]/1-3 performs zero assignments on an empty range and returns the destination advanced by zero. The caller source still contains `a+n`; explicit object-or-null coverage supplies the narrower sufficient domain for it.
- N4659 [expr.new]/7 explicitly permits a zero-element allocation. Such a result need not satisfy readable-current-element or readable-predecessor proxy clauses. Retain zero-size live allocation as uncovered by this new fixture contract; do not infer UB from failure of the proxy or ASan poison status. Native successful executions are observations, not a portable-semantics theorem.
- Dangling/nonobject diagnostics must remain excluded from defined-input agreement. In particular, copying an invalid pointer value alone is implementation-defined under [basic.stc]/4, while the original pointer arithmetic/library iterator use introduces additional validity requirements; avoid a blanket statement that every mere dangling-pointer copy is UB.

## Required experiment labeling

Preserve the original `std_models` contract and its failed actual record as a named contract-gap negative. Run both safe and seeded sources against the distinct new object-domain contract; do not relabel a new success as proving the original contract. Keep all five original model proofs/dependencies fresh and preserve ordinary pointer-origin, RTE, initialization and smoke goals. A safe success plus seeded nonproof meets the fixture-witness requirement only within the explicitly documented narrower domain. Describe nullable empty inputs as live-object-or-null empty domains, rather than claiming that every accepted null input owns a live array.

## Native artifact inspected

`/private/tmp/probata-t24-std-empty-native-20261015/report.json`, SHA-256 `fc7e5e262e117e0ef15015649a1fe389c93dd818f5d1856315d29d026802aaa5`; original fixture, generated C, and harness inspected. Null/live-base/live-one-past/nonempty controls agree, zero-size is separately labeled diagnostic, invalid inputs excluded, and sanitizer-positive bad read fails. These observations support the diagnosis but do not substitute for the pending WP record.

## Primary references

- https://timsong-cpp.github.io/cppwp/n4659/expr.add
- https://timsong-cpp.github.io/cppwp/n4659/forward.iterators
- https://timsong-cpp.github.io/cppwp/n4659/iterator.requirements.general
- https://timsong-cpp.github.io/cppwp/n4659/alg.copy
- https://timsong-cpp.github.io/cppwp/n4659/expr.new
- https://timsong-cpp.github.io/cppwp/n4659/basic.stc

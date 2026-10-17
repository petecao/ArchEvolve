# Typed allocating constructor derivation

Date: 2026-10-16 ET.

This is a checked source grammar/effect interpretation and a candidate
mathematical derivation. It is not a physical C/Typed encoding, a solver result,
a model-body record or source/caller admission. The original nine C units,
including their clauses and logical annotations, are unchanged and retained.

The original FP count/value and copy postconditions and loop invariants use
plain ACSL equality, which is logical real_of_float/double equality, not the C
comparison represented by eq_float/eq_double. Nonfinite promotion is total but
unspecified under ACSL1.24 section2.2.5. C NaN nonreflexivity does not by itself
falsify an original ACSL clause, and no such counterexample is claimed here.
Explicit nonfinite source/class/mode coverage needs a reviewed model successor.
WP Real erasure does not establish that coverage. The exact
bit-transport candidate and the proposed value/class relation are distinct:
same-format NaNs may retain their class while their payload/sign/quiet bits
change. No relation between different FP formats is granted. Signed zero may
compare equal without bit identity. No operation converts a payload to int or
real, performs FP arithmetic, or assumes reflexive C equality for NaN.

Pointer payloads contain an abstract noninteger value token/category and a
separate symbolic representation. Same token with changed representation can
denote the same pointer value. Different tokens with the same representation
are not thereby equated. A null representation remains symbolic. These
mathematical values do not grant arbitrary raw-bit source validity or any
pointee validity, ownership, lifetime, bounds or dereference.

An arbitrary incoming source-memory component I is paired with the selected
receiver region R, fresh backing region F, and private automatic counter A.
I is not empty and is not restricted to the payload datatype. This product is
an interpretation condition to discharge from source storage and allocation;
it is not a new library caller requires or an opaque global Owners premise.
The original assigns *this region is permitted to change. Every other incoming
live byte/value/init observation and every incoming allocation identity/history
is framed if that source-domain separation is established. Dead physical
addresses may be reused; dead physical bytes are not claimed preserved.

For a positive count n and stride w in {4,8}, allocate selects logical next.
well_formed places every issued old identity strictly below next; hence no old
issued identity, live or dead, equals the new backing key. available supplies
the candidate alignment and live-range separation. The new extent is w*n,
not the existing int allocator's hard-coded 4*n. Initial payloads remain
uninitialized. Actual source allocator freshness, valid aligned writable
storage, freeability and framing are explicit unproved implementation TCB.

The exact source zero branch returns after three header stores, with no
allocation, payload access or counter lifetime. For positive n the checked
body allocates once, stores capacity, fills/copies, ends k's scope, then stores
size. No extra callee, pointer escape, free, arbitrary annotation or effect is
accepted by the full-source equality and whole-body grammar checks.

The empty prefix is vacuous. At k<n substitute n=k+remaining+1, remaining>=0.
The store ends at w*(k+1), leaving w*remaining bytes. For earlier j<k substitute
k=j+distance+1; byte distance is w*(distance+1)>0, so the exact map store keeps
every earlier cell and initialization observation. The counter increases
without size_t overflow under the conditional original max_size byte bounds;
n-k decreases by one. The exit invariant contains k=n and a whole writable
region, not a contradictory requirement to write the one-past element.

Copy additionally maintains the full unchanged source image and either an
exact copied prefix or value/class-copied prefix. Its fresh destination key
differs from the source key, so each put keeps every source cell/init entry.
The original readable/receiver-separated precondition alone is not asserted
to imply all byte bounds or receiver/source-backing separation before the
initial receiver stores. Source-created object/storage images must discharge
those conditions. No source-frame or desired sibling theorem is an opaque
premise of another mathematical leaf.

For class filling/copying, stored is quantified separately from input, has the
same scalar kind, and satisfies value_copy to the input/source element.
The step preserves the previous class prefix and adds the current relation;
it never requires stored bits equal input bits. The relation is reflexive for
NaNs by the same-format class arm, not by C equality. Exact bit transport is a
stronger candidate useful only when a selected implementation justifies it.

All emitted leaves retain their complete mathematical premises and no project
lemma dependencies. Their parsing, normal full WP/Why3 native outcome,
goal/property/CSV/task/import/support closure and actual source/mode/allocator
bindings remain pending. The source/library/allocation and representation
TCB is explicit in manifest.json; allocation success alone supplies no frame.
check_launch always refuses until separately reviewed actual evidence and
public admission exist. No historical record or model identity is rewritten.

Checked unbounded affine certificates:

{
  "double": {
    "alignment_rule": "base is stride-aligned; offset is stride*k; no actual pointer integer conversion",
    "all_nonnegative_parameters_checked": true,
    "distance_basis": [
      "distance",
      "j",
      "1"
    ],
    "earlier_store_distance_coefficients": [
      8,
      0,
      8
    ],
    "maximum_bytes": 18446744073709551608,
    "maximum_count": 2305843009213693951,
    "remainder_basis": [
      "k",
      "remaining",
      "1"
    ],
    "remaining_after_increment_coefficients": [
      0,
      1,
      0
    ],
    "remaining_after_store_coefficients": [
      0,
      8,
      0
    ],
    "step_substitution": "n = k + remaining + 1; k = j + distance + 1",
    "store_cases": [
      "j = k: exact typed payload and initialization",
      "j < k: positive stride distance; map-store keeps prior element",
      "different incoming identity: map-store keeps every typed value/init cell"
    ],
    "stride": 8,
    "variant_decrease": 1,
    "zero_case": "no allocation, no payload read/store, no loop-counter activation; original header zeros only"
  },
  "float": {
    "alignment_rule": "base is stride-aligned; offset is stride*k; no actual pointer integer conversion",
    "all_nonnegative_parameters_checked": true,
    "distance_basis": [
      "distance",
      "j",
      "1"
    ],
    "earlier_store_distance_coefficients": [
      4,
      0,
      4
    ],
    "maximum_bytes": 18446744073709551612,
    "maximum_count": 4611686018427387903,
    "remainder_basis": [
      "k",
      "remaining",
      "1"
    ],
    "remaining_after_increment_coefficients": [
      0,
      1,
      0
    ],
    "remaining_after_store_coefficients": [
      0,
      4,
      0
    ],
    "step_substitution": "n = k + remaining + 1; k = j + distance + 1",
    "store_cases": [
      "j = k: exact typed payload and initialization",
      "j < k: positive stride distance; map-store keeps prior element",
      "different incoming identity: map-store keeps every typed value/init cell"
    ],
    "stride": 4,
    "variant_decrease": 1,
    "zero_case": "no allocation, no payload read/store, no loop-counter activation; original header zeros only"
  },
  "int *": {
    "alignment_rule": "base is stride-aligned; offset is stride*k; no actual pointer integer conversion",
    "all_nonnegative_parameters_checked": true,
    "distance_basis": [
      "distance",
      "j",
      "1"
    ],
    "earlier_store_distance_coefficients": [
      8,
      0,
      8
    ],
    "maximum_bytes": 18446744073709551608,
    "maximum_count": 2305843009213693951,
    "remainder_basis": [
      "k",
      "remaining",
      "1"
    ],
    "remaining_after_increment_coefficients": [
      0,
      1,
      0
    ],
    "remaining_after_store_coefficients": [
      0,
      8,
      0
    ],
    "step_substitution": "n = k + remaining + 1; k = j + distance + 1",
    "store_cases": [
      "j = k: exact typed payload and initialization",
      "j < k: positive stride distance; map-store keeps prior element",
      "different incoming identity: map-store keeps every typed value/init cell"
    ],
    "stride": 8,
    "variant_decrease": 1,
    "zero_case": "no allocation, no payload read/store, no loop-counter activation; original header zeros only"
  }
}

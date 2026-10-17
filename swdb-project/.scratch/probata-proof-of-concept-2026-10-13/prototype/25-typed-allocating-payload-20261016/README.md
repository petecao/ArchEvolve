# Typed allocating payload limb

Date: 2026-10-16 ET.

The new vector_allocating_payload API checks the complete original ctor_count,
ctor_count_value and copy_ctor units for float, double and int*. It materializes
nine unchanged sources, exact layout-view inverses, definitions-only typed
payload semantics, unchanged Heap definitions, full conditional mathematical
leaves and a source/effect derivation through declaration/prepare/check.
check_launch always refuses. No compiler, native, WP, Why3, solver, SSH or public
proof run is represented by this folder.

The original model remains swdb-std-models-2, SHA-256
cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2.
No shared model, lowerer, adapter, setup, existing theory, fixture or historical
proof artifact was edited. Exact type-registry declaration slices and values
enter the new identity; its observed whole container is retained separately.

Six vertical RED/GREEN cycles are retained under history. The final five public
tests pass with zero external attempts. The seam is the approved pure model/
source artifact boundary. No synthetic compiler certificate or proof goal is
fabricated. The sixth cycle fixes a substantive research error: early snapshots
conflated plain ACSL float equality with C floating comparison. Those snapshots
remain historical; their erroneous original-contract counterexample claim is
withdrawn in the final source and manifest.

ACSL1.24 section2.2.5 interprets plain float/double equality through total
real_of_float/double promotions; nonfinite promotion is unspecified. C comparison
uses eq_float/eq_double. NaN nonreflexivity in C therefore does not by itself
falsify an original plain ACSL clause. The primary manual is
https://www.frama-c.com/download/frama-c-acsl-implementation.pdf.
Lead25's pinned primary-source observation ad89871f also traces logic_typing,
LogicSemantics and Cfloat. No actual parser observation was made. The observed
Cfloat Real model erases FP values to reals and classifies NaN/infinity false;
that path alone cannot establish explicit IEEE/nonfinite source coverage.

All original annotations and historic evidence stay intact. Root requested a
reviewed explicit model successor with a nonfinite value/class relation and a
new identity/consumer rebind. This isolated candidate defines value_copy and
class-prefix fill/copy induction: same-format NaNs can relate despite changed
payload/sign/quiet bits. NaN-to-infinity and cross-format NaNs do not relate.
Separate non-NaN C-comparison lifting is conditional mathematics, not a permanent
caller restriction or proof of the original plain ACSL clauses.

Floating payloads use nominal binary32/binary64 sign/exponent/fraction bit
fields; there is no integer or real surrogate. Pointer payloads retain an
abstract noninteger value token/category and separate representation bits.
Same value may have changed representation; equal bits do not equate distinct
tokens. Null bits remain symbolic. No arbitrary raw pointer bits, pointee
validity, dereference, source object identity, ownership or lifetime follows.
Bit-exact transport is a stronger candidate needing selected implementation/
representation evidence; generic C++ assignment and signaling NaNs are not
presumed bit-preserving.

The source checker binds the full original model/helpers/contracts and exact
header stores, zero return, allocation, capacity store, loop annotations and
typed fill/copy, counter scope and size store. It rejects unaccounted calls,
annotations, extra effects and alternate pointer reads. Width-aware allocation
uses width*n, not Heap's int-specific 4*n for eight-byte payloads. Unbounded
affine certificates check store end, earlier-cell separation and n-k decrease.
The exit invariant is satisfiable at k=n and requires no one-past store.
Exact-copy and class-copy induction retain the complete unchanged source image.

Arbitrary incoming source memory is unrestricted outside original assigns
*this. Allocation identities/dead identity history and live bytes are framed
separately; reused dead physical bytes are not promised unchanged. Parameter/
counter storage is separate. This conditional product is not an empty incoming
heap, total Typed encoding or opaque global Owners premise. Original copy
readable/receiver separation is not asserted to imply every byte bound or
receiver/source-backing separation before initial header stores; source-created
storage images must discharge those facts.

Remaining gates: independent Spec/Standards review; actual mathematical parsing
and normal native/ordinary/property/CSV/task/hypothesis/import/support audit;
typed storage/layout/allocator/representation/FP-mode binding; complete source
clause/RTE/init/frame/CFG ledger; the reviewed model successor and consumer
rebind; public compiler/model/caller/framework admission. The plain library and
allocation-success assumptions plus freshness, validity, alignment, freeability,
framing, release and interposition TCB are explicit. Success alone grants no frame.

# Private-array reentry successor

2026-10-16 ET. Prospective hand-model feasibility only; no formal/source/allocator
acceptance. The six-site Git freeze `3940afd0` and its 43-control evidence remain
unchanged. This successor adds four source fixtures, bringing the exact site set
to ten. The four model C/header files and the original six site sources remain
byte-identical to that freeze.

`reentry-positive.c` and `reentry-missing-store.c` create the same uninitialized
typed private array inside a two-iteration lexical block, using the actual
constructor/binder path. The destructor marker is immediately followed by block
exit on each iteration. Both lifetimes write before reading in the positive.
The negative writes only in the first lifetime; the second lifetime omits the
store and reads cell 0. No reset, initialization assertion, synthetic mask fact,
poison or havoc is inserted. This specifically tests reuse of the same lexical
array declaration across retirement/reentry.

`modular-entry-positive.c` and `modular-entry-missing-store.c` call the same
`swdb_lifetime_entry` function twice. Each entry declares its own private array,
constructs and destroys its buffer on the same path. The first call requests a
store and the second requests no store. The positive entry always performs the
real store; the negative entry obeys the request, leaving its second read unsafe.
The negative entry has no `requires write` or initialized-payload premise.
Its conditional value postcondition does not assert initializedness. These two
TUs contain two root functions, which must both enter the complete ordinary/RTE/
smoke census; the other eight TUs have one root function. All twenty header bodies
remain included in every TU, with no function/property filtering.

The ten-family compiler/native profile passes 56 controls under shared B and
the 8 GiB/120-second guard. New missing-store cases each produce exactly one
`core.uninitialized.Assign` diagnostic at their intended source fixture, while
both new positives produce no diagnostic. Undefined negatives are never natively
executed. The already-defined helper and three-way TD native executions are
retained. Raw results are outside the checkout at
`/private/tmp/probata-t07-private-array-reentry-controls1-20261016`.

This is compiler analysis, not a WP initializedness or lifetime proof. The two
loop TUs intentionally have no loop proof hints. Unrelated open loop/frame/value
obligations cannot count as the intended negative result. Generation must retain
the complete universe, and cold review must identify the actual payload-read
initializedness formula separately from metadata/pointer initialization and all
other goals. A generation-only component cannot prove either positive acceptance
or negative rejection. No blanket true/false init-map fact or forced memory
classification is permitted.

The generator records the researched e4fc4af header hash but does not establish
the selected real C++ header/macro/include closure. Its manifest now explicitly
marks that physical source-closure gate **REFUSED_NOT_IMPLEMENTED**. The actual
project unit is byte-pinned; that alone does not bind a different selected header
or compilation context. A finite component can claim only behavior of the exact
hand-model inputs. Full allocator, C++/device/source, physical alignment, same-array
provenance, lifetime, full TD and counted admission remain refused until the
independent source gate and actual init-map/reentry components close.

No Frama-C, Why3, solver, provider, version/config command or SSH process was run
for this successor. Root alone owns any actual formal entry and its resource lease.

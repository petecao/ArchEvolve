# Format v0.4: the `std::vector` and `std::pair` models

Updated: 2026-10-15 ET; created: 2026-10-14 ET (Probata proof of concept ticket 25). Design: formal-verification map 16 items 6 and 7,
11 item 11. Code: `swdb/std_models.py` (the models), `swdb/c_lowering.py` (the hooks), the CBMC and WP
adapters (records). Related: [format-v0.4-c-lowering-wp.md](format-v0.4-c-lowering-wp.md),
[format-v0.4-cbmc.md](format-v0.4-cbmc.md).

## In one paragraph

No verifier ever runs libc++. The C lowering tool turns `std::vector<T>` and `std::pair<A, B>` into C structs
and every use of a modeled member into a call of a C function. Each function has an ACSL contract that cites
its clause of the C++17 standard. CBMC runs the C bodies; WP reads the contracts. Growth frees the old buffer,
so a stale pointer or iterator is a memory error that CBMC refutes. `at` out of range is an obligation.

## The types

| C++ | C | Notes |
|---|---|---|
| `std::vector<T>` | `struct std_vector_<t> { T *data; size_t size; size_t capacity; }` | `T`: an integer, floating-point or pointer type, not `bool` |
| `std::pair<A, B>` | `struct std_pair_<a>_<b> { A first; B second; }` | `A`, `B`: the same element types; `first` and `second` keep their names |
| `std::vector<T>::iterator` | `T *` | libc++'s `__wrap_iter<T *>` wraps one pointer |

`<t>` is spelled as for templates (`int`, `unsigned_long`, `int_ptr`). Each vector struct has two ACSL
predicates: `std_vector_<t>_valid` (writable) and `std_vector_<t>_readable`.

## The members

| Member | C function | Clause cited |
|---|---|---|
| `vector()` | `_ctor` | `[vector.cons]` |
| `vector(n)`, `vector(n, value)` | `_ctor_count`, `_ctor_count_value` | `[vector.cons]` |
| copy, move construction | `_copy_ctor`, `_move_ctor` | `[container.requirements.general]` |
| destruction (at scope end) | `_dtor` | `[container.requirements.general]` |
| `operator[]`, `at` | `_operator_index`, `_at` | `[sequence.reqmts]` |
| `data()` | `_data` | `[vector.data]` |
| `size()`, `empty()`, `begin()`, `end()` | `_size`, `_empty`, `_begin`, `_end` | `[container.requirements.general]` |
| range-for | `__rangeN`, `__beginN`, `__endN`, a pointer loop | `[stmt.ranged]` (the lowering, not a function) |
| `push_back` | `_push_back` | `[vector.modifiers]` |
| `resize`, `reserve` | `_resize`, `_reserve` | `[vector.capacity]` |
| `clear` | `_clear` | `[sequence.reqmts]` |
| `swap` (member and `std::swap`) | `_swap` | `[vector.special]` |
| `pair()`, `pair(x, y)`, copy, `=` | `_ctor_default`, `_ctor`, `_copy_ctor`, `_operator_assign` | `[pairs.pair]` |

Any other member (`pop_back`, `back`, `insert`, vector `=` and so on) reads `unsupported construct` and names
it. So does `std::vector<bool>`, a vector of a class, and a class with a vector member.

## What the contracts say

- **Growth.** `push_back`, `resize` and `reserve` name `*this` (data, size, capacity) and the buffer they write
  in `assigns`. When the new size passes the old capacity, `ensures !\valid(\old(this->data))`: the old
  buffer is gone. Otherwise `data` is unchanged. In a parallel region this makes growth a write to the
  vector under its sharing class (tickets 45 and 46 check it).
- **`at` and `operator[]`.** Both `require n < this->size`. For `at`, the C++ throws `std::out_of_range`;
  exceptions are outside the subset, so the C body calls `SWDB_MODEL_FAIL` (CBMC: a failed check named
  `std.vector.at.out_of_range`). For `operator[]`, it is undefined behavior; the body calls
  `SWDB_MODEL_REQUIRE` (CBMC: a check; natively nothing, like libc++).
- **What the standard leaves open** follows the pinned libc++ 22.1.8, so counterexamples replay on the C++:
  capacity grows to `max(2 * capacity, new size)`, `reserve(n)` and a copy allocate exactly. Contracts state
  only what the standard says.
- **Allocation** never fails in the bodies (`malloc`, no null check): an assumption entry. CBMC 6 lets
  `malloc` return NULL by default, so the CBMC adapter adds `--no-malloc-may-fail` (in `settings.flags`) exactly
  when the lowering allocates (a model or `new[]`), the same condition as the entry.

The bounded adapter probes the selected clang headers and refuses model jobs unless
`_LIBCPP_VERSION` is `220108` (libc++ 22.1.8). The record names that implementation and version in
`settings.standard_library`. Clang 22 paired with Linux libstdc++ is not admitted by this model.

## The method version

A job on a unit that uses a model runs only when the method version's `models.std_vector` (and
`models.std_pair`, when a pair is used) equals `swdb.std_models.identity()`, as for the translators; else no
job runs and no record is written.

## The version and the pin

`swdb.std_models.identity()` is `{id: swdb-std-models-<MODELS_VERSION>, sha256}`, the sha256 of
`swdb/std_models.py`. Changing any contract, body or layout gives a new pin.

| Field | Where | Meaning |
|---|---|---|
| `std_models` | `swdb lower` output, `<name>.anchors.json` | `{id, sha256, types}`: the model version and the struct names used |
| `allocation` | `swdb lower` output, `<name>.anchors.json` | `true` when the C allocates (a vector model or `new[]`) |
| `pins.std_models` | proof record | the model version's `{id, sha256}`, exactly when the unit uses a modeled type |
| `settings.std_models` | CBMC proof record | the struct names used |

## Assumption entries

Every proof record (CBMC or WP) of a unit adds:

| When | Kind | Reference | Sentence starts |
|---|---|---|---|
| it uses a modeled type | `trusted_tool` | the model version | "The pinned standard library (libc++ of clang 22.1.8) implements the modeled members of ..." |
| it uses a modeled type or `new[]` | `trusted_tool` | the model version, or the C lowering tool for `new[]` alone | "Allocation succeeds: ..." |

A unit that uses neither adds neither.

## Model proof records

`swdb prove --model NAME --adapter wp` uses the existing C-model interface. The record subject is
`{kind: c_model, id: NAME}`, and `pins.code`/`pins.contract` hash the complete generated C text, including the
contracts of helpers. Proven dependencies are recorded through `pins.models`. There is no separate
`--summary model.NAME` mechanism.

Model texts are rebuilt by `swdb.c_lowering.model_text(NAME)` and contain the struct definition, ACSL
predicates and required helper bodies. Pair models can be proven individually. Vector members involving
release are refused by WP until the allocation lifetime model is validated; this is incomplete acceptance.

## Allocation in WP

The allocator is `swdb_alloc_<t>(n)` (`allocates \result; ensures \fresh(\result, n * sizeof(T)) &&
\valid(\result + (0 .. n - 1))`) and `swdb_free(p)` (`requires p == \null || \freeable(p); frees p`):
contract-only under Frama-C (`__FRAMAC__`), `malloc`/`free` elsewhere, trusted under "allocation succeeds".
Growth members carry `allocates this->data; frees this->data`.

WP 33 does not implement `\fresh`, `\freeable`, `allocates` or `frees` ("Allocation, initialization and
danglingness not yet implemented"): it degenerates those terms. On the 23 model functions of the vector_pair
fixture (2026-10-14, 10 s per solver) 309 of 327 goals prove; the 18 open goals are exactly those:

| Cause | Goals |
|---|---|
| `\freeable` (free's and grow's precondition) | `dtor_call_swdb_free_requires`, `grow_call_swdb_free_requires`, `push_back`/`reserve`/`resize_call_std_vector_int_grow_requires_2` |
| `\fresh` (new buffer separate from old memory) | `grow_loop_invariant_2_preserved`, `grow_ensures_2`, `grow_assigns_{normal,exit}_part3`, `copy_ctor_ensures`, `copy_ctor_loop_invariant_2_preserved`, `copy_ctor_assigns_normal_part7`, `ctor_count[_value]_assigns_normal_part7`, `push_back_assigns_normal_part4`, `resize_assigns_normal_part4` |
| `frees` (old buffer invalid after) | `dtor_ensures`, `grow_ensures_3` |

Those diagnostic counts are historical evidence from 2026-10-14, not a current completion claim.
WP units containing uncertified vector release remain unsupported. CBMC executes real allocation/free
within its admitted bounded source protocol. A checked owner/liveness WP view remains research; a fixed
finite pool would change the unbounded scope and cannot silently replace that acceptance.

## Not built yet

- WP proofs of growing members and of units that grow a vector (the table above).


Model version 2 (2026-10-15) makes initializedness explicit: pair copy/assignment require initialized
source objects, constructors establish initialized destinations, and vector invariants require an
initialized representation plus the live element prefix. Spare capacity remains uninitialized storage.
These contracts accompany mandatory WP initialization checks; they make no additional lifetime claim.
Model and summary dependencies must count under the caller's exact method and evidence boundary; a
proof made before that policy cannot satisfy the new method merely because the code text matches.

## Checked private vector view (2026-10-15 ET)

The WP adapter can stage a closed `vector<int>` protocol with one count-value constructor,
one `data()` alias, one growing append and scalar observations. The original contract keeps
`assigns \nothing`; the checked relation projects writes to fresh, nonescaping private storage.
WP proves the separate private-view frame, functional facts and alias-liveness obligations.
`vector_ownership_check` pins the checker; `vector_ownership_certificate` pins the source/view
bytes, contracts and structural frame certificate; `vector_ownership_allocator` pins the
explicit trusted fresh-allocation and separation contracts. Neither fresh storage nor source-frame
preservation is inferred from unsupported WP allocation clauses. The checker is included in the
setup/reader identity and revalidates the view before launch. The nine focused controls pass across two reports (five completed calls in an unfinished run,
four in a completed finishing run); the exact evidence is recorded in ticket25. General vector
lifetime acceptance remains pending.


## Bounded initializedness admission (2026-10-15)

Lowerer8 adds `standard_policy` inside generator-owned `bounded_initialization` metadata.
`swdb/bounded_std_initialization.py` audits the exact model-version2 source hash, with its own source
included in the checker and lowerer identities. A model-body change needs a new audit even when a
method file pins that changed body. This policy adds no initializedness or lifetime assumption.

The admitted protocol uses initialized local scalar-element vectors and pairs. It supports vector
default/count/count-value construction, `push_back`, `size`, `empty`, `operator[]`, `at`, `data`,
`begin`, `end`, automatic destruction and the canonical range-for with a scalar copied loop variable;
pair default/value construction and `first`/`second` accesses are admitted. These exact model bodies
initialize every live element. Access through the indexed member requires its executable index check;
spare capacity is excluded. Pointer elements, copy/move construction, pair assignment, shrinking/clear,
reserve/swap, aliases and other member protocols remain conservative refusals in this initial policy.

Raw data/iterator reads require a literal index within a definite initialized live prefix at capture.
Conditional or possibly zero-trip appends do not enlarge that prefix. Integer conversions never infer
a larger prefix from the unconverted literal. Raw pointer arithmetic, casts, escaping calls, returned
standard storage and reference range variables are refused. The real CBMC allocation and pointer
checks still decide stale-pointer lifetime failures after growth; initialized ghost sizes do not stand
in for liveness. The matched libc++22.1.8 differential requirement remains in force.

The original maximum proof, stale-data and stale-iterator replayed refutations, unchecked `at`
refutation and checked-`at` proof are retained. This bounded restoration does not satisfy the open
unbounded WP vector-lifetime acceptance.


The defensive `std_vector_int_at` WP model job has a separate checked view. For the exact audited
model-version2 C text, pinned Clang C parsing checks the pure `n >= this->size` abort guard and
unchanged `this->data + n` return. The view replaces that guard with the named checked assertion
`at_guard_false: n < this->size`; WP must prove it under the unchanged original contract. Original
and view contract digests match, and no input precondition is added. The original/native/CBMC model
retains the abort. Changed bodies or missing bounds contracts refuse this exact view. The source,
view, C-AST shape, mapping certificate and checker are reported/pinned and regenerated before WP.
`standard_model_view_check` pins the relation checker; `standard_model_view_certificate` pins its
exact source/view and unchanged-contract mapping. Generated pointer checks are applied after that
checked view and regenerated in the same order at launch.
This avoids a dead defensive branch failing smoke checks without exempting any smoke obligation.

The required boolean `-wp-no-filter-init` retains initialized representation predicates in ordinary
memory goals: WP33's default aggressive initialization filter can discard an entire predicate atom
that also carries validity facts. This optimization change adds no semantic premise. Raw invalid,
uninitialized, wrong-postcondition, stale-alias and contradictory-precondition controls remain open
or fail smoke. The prospective member contract fixtures (14 original bodies plus this checked `at`
view) precede the separate array-object provenance gate; they do not establish a final production
method, all member/lifetime acceptance, or a stronger model input domain.

Closed-owner origin integration checkpoint (2026-10-15 ET): `model_domains.py` independently audits
the generated two-site vector view's C AST, allocation calls, pointer bindings, exact loop effects,
array/indirect accesses and immediately preceding numerical/liveness guards. Its source certificate
binds the captured alias by function/name/source declaration range to the initial typed allocation,
with extent frozen at entry. The growing append invalidates that alias. Backing extents and live
prefixes are separate; spare capacity grants no source read permission. Every modeled source call
records its exact C-model text pin and origin transition. The existing source/native malloc/free
models remain unchanged. The proof record explicitly states the pinned typed allocator/model
relation; WP validity is not treated as an array-object origin proof.

The lowerer/adapter integration must store that source certificate in `pointer_bounds.owner`, map
source access records to their independently checked view guards, and freshly recheck source and
view before launch. A source registry alone grants no waiver. Generic modeled fields/parameters,
standalone domain-qualified model jobs, additional allocation sites and wider member protocols
remain refused. Current prelaunch fault controls exercise public proof records; they do not supply
real-WP acceptance for the combined origin method.

### Original-model heap proof view (2026-10-16 ET)

The exact int count/value constructor and destructor have a separately checked
unbounded heap VC translation. Their original C bodies, contracts and model
version remain unchanged. The accepted first-pair capability experiment is
distinct from the public `swdb prove --model` integration; no prototype result
is loaded as a model proof record.

The public view reconstructs the original source/event/clause/RTE/init/frame/
lifetime map and selects every positive obligation associated with that member
(27 for construction, 11 for destruction). Each input contains one isolated
`check lemma`, or the complete arithmetic/layout C kernel. WP uses its default
complete property selection: there is no property selector or warning-policy
exception. Every target must pass the ordinary fresh generated-goal reader;
global targets must be owned by their sole mapped lemma with no imported project
dependency. The numeric kernel retains all ordinary and smoke obligations and
its separately discharged local assertion dependencies. Timeout, missing goals,
unclassified reports or a failed smoke cannot establish a model proof.

`heap_model_view_check` pins the translator, checker, heap definitions and linked
metadata helper. `heap_model_view_certificate` pins the original-source mapping
and complete selected target inventory. `heap_model_foundations` pins the exact
standard Why3 and Frama-C Qed/Cint support sources. A metadata-only native helper
reads the actual Why3 load path; it must be the selected switch's standard
library. The Frama-C share path must match the reader's WP package, foreign
shadow roots are refused, and source/configuration bindings are rechecked before
each launch. No project desired theorem is imported as an axiom.

All targets share the remaining public wall budget and the process-tree RSS
watchdog. Each has a fresh report set, and the record retains its command,
resources and complete reports. No caller premise is added: incoming heaps are
arbitrary, allocation identities are unbounded, old allocations and escaped
aliases persist, and receiver/buffer overlap remains in the destructor domain.
Successful allocation is an explicit constructor assumption; the destructor
does not acquire that assumption. Generic caller composition, other members or
element types, byte/partial-store semantics, source hints and build defines are
outside this exact view.

The coordinator-admitted public profile at exact `cea5652b` completed on
2026-10-16 ET. Both fresh fixture records pass schema and independent cold review:
the constructor's 27 targets contain 36 Valid ordinary goals and one passing
numeric smoke; the destructor's 11 targets contain 11 Valid ordinary goals.
Every one of the 108 fresh emitted tasks has the same formula body as its
previously audited same-input task; proof results were obtained afresh. Current
Linux runtime, method, setup/reader identities, all source and standard-support
bindings, and the numeric local dependency DAG were checked. This establishes
these two original member bodies under the declared translation, allocation and
tool TCB. It does not adopt the records into the production store, compose a
generic caller, establish other members or prove formal C++ equivalence.
See the [independent actual review](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-public-heap-cold-review-cea5652b-20261016.md).

The original `std_vector_int_ctor_count` now has a separately prepared mapping:
its exact source fill `(int)0` explicitly instantiates the universal value
semantics at zero. Its full original source/contract and eleven source events
are independently reconstructed, and all 27 positive targets, including the
complete numeric kernel, require fresh execution. Checker policy 2 admits this
additional member; the original model version and heap definitions are unchanged.
Its public preparation controls and synthetic successful record persistence pass;
actual proof acceptance remains pending. The first-pair acceptance above stays
bound to exact CEA, without promoting those records across new checker pins.

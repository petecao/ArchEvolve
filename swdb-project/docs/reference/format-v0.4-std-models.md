# Format v0.4: the `std::vector` and `std::pair` models

Created: 2026-10-14 ET (Probata proof of concept ticket 25). Design: formal-verification map 16 items 6 and 7,
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

## Not built yet

- Proving each model contract against its C function once, as a record (`library_summary`): models are not
  library entries, so `swdb prove --summary` cannot name them yet. One exploratory WP job (2026-10-14, the
  frozen WP flags with a 10 s solver timeout, `-wp-fct` on the 23 model functions of the vector_pair fixture)
  proved 293 of 322 goals. Every member that neither allocates nor frees proved fully (`ctor`, `move_ctor`,
  `size`, `empty`, `data`, `begin`, `end`, `operator_index`, `at`, `clear`, `swap`, `reserve`, all pair
  members). The 29 open goals sit in `grow`, `dtor`, `push_back`, `resize` and the allocating constructors:
  `malloc`'s result validity, `free`'s `freeable` precondition and the libc heap-status `assigns`. Closing them
  needs an ACSL form of "allocation succeeds" that WP accepts.
- WP proofs of units that use the models.

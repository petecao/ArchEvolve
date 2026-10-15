"""The `std::vector<T>` and `std::pair<A, B>` models: a C struct per type plus one C function per member, each
with an ACSL contract citing the C++ standard's clause for it.

Created: 2026-10-14 ET (Probata proof of concept ticket 25). Design: formal-verification map 16 items 6 and 7
(`std::vector<T>` (not `bool`) and `std::pair` as modeled types; growth frees the old buffer; `at` out of range
is a proof obligation; new assumption entries), 11 item 11 (undefined behavior is a proof obligation).
Format: docs/reference/format-v0.4-std-models.md.

- Modeled, never lowered from libc++: the C lowering tool (`swdb.c_lowering`) turns each use of a modeled member
  into a call of its C function here, so no verifier ever runs libc++ internals.
- Citations name clauses of ISO/IEC 14882:2017 (C++17), the `-std` the C lowering parses with: `[vector.cons]`,
  `[vector.capacity]`, `[vector.data]`, `[vector.modifiers]`, `[vector.special]`, `[sequence.reqmts]`,
  `[container.requirements.general]`, `[stmt.ranged]` and `[pairs.pair]`.
- What the standard leaves to the implementation (the growth policy: when `capacity()` grows and by how much)
  follows the pinned libc++ 22.1.8 (`__recommend`: twice the capacity, at least the new size; `reserve(n)` and a
  copy allocate exactly), so a counterexample on the C lowering replays on the C++. A contract states only what
  the standard says: reallocation happens exactly when the new size exceeds the old capacity, and then the old
  buffer is no longer valid (stated through `\\valid` in `ensures`, 20's allowed-ACSL rules), so CBMC detects a stale pointer
  or iterator. WP refuses units with releases pending sound lifetime support.
- `at(n)` with `n >= size()` throws `std::out_of_range`; exceptions are outside the subset, so the contract makes
  `n < size()` the caller's obligation, and the C body calls `SWDB_MODEL_FAIL` (CBMC: a failed assertion; the
  native harness: a failed check; standalone: `abort()`, what an uncaught exception does). `operator[]` with
  `n >= size()` is undefined behavior: its contract requires `n < size()` and the body calls
  `SWDB_MODEL_REQUIRE` (CBMC: an assertion; native: nothing).
- Elements are scalars (integers, floating point) or pointers; `std::vector<bool>` and class elements are
  outside the model. Iterators are pointers (libc++'s `__wrap_iter<T *>` wraps one).
- Allocation succeeds (an assumption entry of every record that uses a model that allocates): the bodies call
  `swdb_alloc_<t>` and `swdb_free`. For WP (`__FRAMAC__`) these are contract-only stubs (`allocates`/`\\fresh`,
  `frees`/`\\freeable`), never proven; elsewhere they are `malloc` and `free`, with no null check.
- Model proof units (swdb.c_lowering): every vector and pair model function can be rebuilt from its C name alone and
  proven once with `swdb prove --model <name> --adapter wp`.
"""

import hashlib
import re
from pathlib import Path

MODELS_ID = "swdb-std-models"
MODELS_VERSION = "2"                 # bump on any change to a contract, a body or the struct layout
OUT_OF_RANGE = "std.vector.at.out_of_range"     # the failed-check name; the CBMC harness prints it for the C++ too
INDEX_PRECONDITION = "std.vector.operator_index.n_below_size"
VECTOR_MEMBERS = ("ctor", "ctor_count", "ctor_count_value", "copy_ctor", "move_ctor", "dtor", "operator_index", "at",
                  "data", "size", "empty", "begin", "end", "push_back", "resize", "reserve", "clear", "swap")
PAIR_MEMBERS = ("ctor_default", "ctor", "copy_ctor", "operator_assign")
ALLOCATING = {"ctor_count", "ctor_count_value", "copy_ctor", "push_back", "resize", "reserve"}
STANDARD = "ISO/IEC 14882:2017 (C++17)"
SENTENCE_LIBRARY = ("The pinned standard library (libc++ of clang {clang}) implements the modeled members of {types} as "
                    "the C++ standard ({standard}) says, as the model {model} states them.")
SENTENCE_ALLOCATION = "Allocation succeeds: every malloc (std::vector growth, new[]) returns usable memory, never null."


def identity(path=None):
    """{id, sha256} of the model version: the sha256 of this module's source (every contract, body and layout)."""
    source = Path(path) if path else Path(__file__)
    return {"id": f"{MODELS_ID}-{MODELS_VERSION}", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def assumptions(lowering, clang_version, lowering_tool):
    """The assumption entries a proof record of this C lowering adds (map 16 item 7): "the pinned standard library
    implements the modeled members as the standard says" (trusted tool; reference: the model version) when it uses a
    model, and "allocation succeeds" (trusted tool; reference: the model version, or the C lowering tool that lowers
    new[] to malloc) when it allocates. `lowering_tool`: {id, sha256} of the C lowering tool."""
    found = []
    model = identity()
    if lowering.std_models:
        types = ", ".join(lowering.std_models)
        found.append({"kind": "trusted_tool", "reference": dict(model),
                      "sentence": SENTENCE_LIBRARY.format(clang=clang_version, types=types, standard=STANDARD,
                                                          model=model["id"])})
    if lowering.allocation:
        found.append({"kind": "trusted_tool", "reference": dict(model if lowering.std_models else lowering_tool),
                      "sentence": SENTENCE_ALLOCATION})
    return found


def method_problem(method, lowering):
    """Why the method version does not admit this lowering's models (its `models.std_vector` / `models.std_pair`
    must be this model version), or None. A mismatch runs nothing, as for the translators."""
    found = identity()
    section = method.data.get("models") or {}
    for key, prefix in (("std_vector", "std_vector_"), ("std_pair", "std_pair_")):
        if not any(name.startswith(prefix) for name in lowering.std_models):
            continue
        pinned = section.get(key) if isinstance(section, dict) else None
        if not isinstance(pinned, dict) or {k: pinned.get(k) for k in ("id", "sha256")} != found:
            return (f"the C lowering uses the {key} model {found['id']} (sha256 {found['sha256'][:12]}...), but "
                    f"method version {method.id} pins models.{key} = {pinned}")
    return None


def pins(lowering):
    """The content-hash set's `std_models` pin ({id, sha256} of the model version) when the C uses a model."""
    return {"std_models": identity()} if lowering.std_models else {}


MACROS = """\
/* swdb-std-models: the model's two check hooks (CBMC and the native harness define them first). */
#ifndef SWDB_MODEL_REQUIRE
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#endif
#ifndef SWDB_MODEL_FAIL
#define SWDB_MODEL_FAIL(name) abort()
#endif"""


def _max(t):
    """libc++'s max_size(): min(SIZE_MAX / sizeof(T), PTRDIFF_MAX), as C (and ACSL, whose annotations are preprocessed)."""
    return f"((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof({t}) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof({t}))"


def _decl(t, name):
    return f"{t}{name}" if t.endswith("*") else f"{t} {name}"


def vector_struct_fields(t):
    return [f"{_decl(t + ' *', 'data')};", "size_t size;", "size_t capacity;"]


def vector_logic(v, t):
    """The validity predicate of one vector struct (ACSL only)."""
    return (f"/* swdb-std-models: the representation invariant of {v} (data, size, capacity). */\n"
            f"/*@ predicate {v}_valid({v} *v) =\n"
            f"      \\valid(v) && \\initialized(v) && v->size <= v->capacity && v->capacity <= {_max(t)} &&\n"
            f"      (v->capacity == 0 ? v->data == \\null : \\valid(v->data + (0 .. v->capacity - 1))) &&\n"
            f"      \\initialized(v->data + (0 .. v->size - 1));\n"
            f"    predicate {v}_readable({v} *v) =\n"
            f"      \\valid_read(v) && \\initialized(v) && v->size <= v->capacity &&\n"
            f"      (v->capacity == 0 ? v->data == \\null : \\valid(v->data + (0 .. v->capacity - 1))) &&\n"
            f"      \\initialized(v->data + (0 .. v->size - 1));\n*/")


def _mangle(t):
    return re.sub(r"\s+", "_", re.sub(r"\s*\*", " ptr", t.strip()))


def allocator(t):
    """[(C name, C text)] of the allocator models: their contracts are the "allocation succeeds" assumption (map 16
    item 7), so WP reads them and never proves them; CBMC and the native runs use malloc and free."""
    a = f"swdb_alloc_{_mangle(t)}"
    alloc = (f"/* swdb-std-models allocator (trusted: \"allocation succeeds\"): n fresh, valid elements. */\n"
             f"#ifdef __FRAMAC__\n"
             f"/*@ requires n >= 0;\n    assigns \\nothing;\n    allocates \\result;\n"
             f"    ensures \\fresh(\\result, n * sizeof({t})) && \\valid(\\result + (0 .. n - 1)); */\n"
             f"{_decl(t + ' *', a)}(size_t n);\n"
             f"#else\n"
             f"static inline {_decl(t + ' *', a)}(size_t n) {{ return ({t} *)malloc(n * sizeof({t})); }}\n"
             f"#endif")
    free = ("/* swdb-std-models deallocator (trusted with the allocator). */\n"
            "#ifdef __FRAMAC__\n"
            "/*@ requires p == \\null || \\freeable(p);\n    assigns \\nothing;\n    frees p; */\n"
            "void swdb_free(void *p);\n"
            "#else\n"
            "static inline void swdb_free(void *p) { free(p); }\n"
            "#endif")
    return [(a, alloc), ("swdb_free", free)]


def _helpers(v, t):
    """libc++'s growth policy (implementation-defined by the standard): __recommend and the reallocation step."""
    recommend = (
        f"/* swdb-std-models helper: libc++ __recommend (the capacity a growth to new_size asks for). The standard leaves\n"
        f"   the growth policy to the implementation ([vector.capacity] p1 note: capacity() >= size()). */\n"
        f"/*@ requires {v}_readable(this) && new_size <= {_max(t)};\n"
        f"    assigns \\nothing;\n"
        f"    ensures new_size <= \\result <= {_max(t)}; */\n"
        f"static size_t {v}_recommend(const {v} *this, size_t new_size) {{\n"
        f"  size_t ms = {_max(t)};\n"
        f"  if (this->capacity >= ms / 2) return ms;\n"
        f"  return 2 * this->capacity > new_size ? 2 * this->capacity : new_size;\n}}")
    grow = (
        f"/* swdb-std-models helper: reallocation to capacity cap (allocate, move the elements, free the old buffer). */\n"
        f"/*@ requires {v}_valid(this) && this->size <= cap && cap > this->capacity && cap <= {_max(t)};\n"
        f"    requires this->capacity == 0 || \\freeable(this->data);\n"
        f"    assigns *this;\n"
        f"    allocates this->data;\n"
        f"    frees this->data;\n"
        f"    ensures {v}_valid(this) && this->capacity == cap && this->size == \\old(this->size);\n"
        f"    ensures \\forall integer k; 0 <= k < this->size ==> this->data[k] == \\old(this->data[k]);\n"
        f"    ensures \\old(this->capacity) > 0 ==> !\\valid(\\old(this->data)); */\n"
        f"static void {v}_grow({v} *this, size_t cap) {{\n"
        f"  {_decl(t + ' *', 'fresh')} = swdb_alloc_{_mangle(t)}(cap);   /* allocation succeeds (assumption entry) */\n"
        f"  /*@ loop invariant 0 <= k <= this->size;\n"
        f"      loop invariant \\forall integer j; 0 <= j < k ==> fresh[j] == this->data[j];\n"
        f"      loop invariant \\initialized(fresh + (0 .. k - 1));\n"
        f"      loop assigns k, fresh[0 .. cap - 1];\n"
        f"      loop variant this->size - k; */\n"
        f"  for (size_t k = 0; k < this->size; ++k) fresh[k] = this->data[k];\n"
        f"  swdb_free(this->data);\n"
        f"  this->data = fresh;\n"
        f"  this->capacity = cap;\n}}")
    return recommend, grow


def vector_member(v, t, member):
    """[(C name, C text)] for one vector member: its helpers first, then the member itself."""
    m = _max(t)
    zero = f"({t})0"
    ref = f"{t} *" if not t.endswith("*") else f"{t}*"
    out = []
    if member in ALLOCATING or member == "dtor":
        out += allocator(t)
    if member in ("push_back", "resize", "reserve"):
        recommend, grow = _helpers(v, t)
        if member != "reserve":
            out.append((f"{v}_recommend", recommend))
        out.append((f"{v}_grow", grow))
    if member == "ctor":
        text = (f"/* [vector.cons] p1, [container.requirements.general] Table 83 (X u;): an empty vector. */\n"
                f"/*@ requires \\valid(this);\n    assigns *this;\n"
                f"    ensures {v}_valid(this) && this->size == 0; */\n"
                f"static void {v}_ctor({v} *this) {{ this->data = NULL; this->size = 0; this->capacity = 0; }}")
    elif member in ("ctor_count", "ctor_count_value"):
        value = member == "ctor_count_value"
        what = ("[vector.cons] p6-p7: vector(size_type n, const T& value): n copies of value." if value else
                "[vector.cons] p3-p4: explicit vector(size_type n): n value-initialized elements.")
        fill = "value" if value else zero
        params = f"{v} *this, size_t n" + (f", {_decl(t, 'value')}" if value else "")
        text = (f"/* {what} */\n"
                f"/*@ requires \\valid(this) && n <= {m};\n    assigns *this;\n    allocates this->data;\n"
                f"    ensures {v}_valid(this) && this->size == n;\n"
                f"    ensures \\forall integer k; 0 <= k < n ==> this->data[k] == {'value' if value else '0'}; */\n"
                f"static void {v}_{member}({params}) {{\n"
                f"  this->data = NULL; this->size = 0; this->capacity = 0;\n"
                f"  if (n == 0) return;\n"
                f"  this->data = swdb_alloc_{_mangle(t)}(n);   /* allocation succeeds (assumption entry) */\n"
                f"  this->capacity = n;\n"
                f"  /*@ loop invariant 0 <= k <= n;\n"
                f"      loop invariant \\forall integer j; 0 <= j < k ==> this->data[j] == {'value' if value else '0'};\n"
                f"      loop invariant \\initialized(this->data + (0 .. k - 1));\n"
                f"      loop assigns k, this->data[0 .. n - 1];\n      loop variant n - k; */\n"
                f"  for (size_t k = 0; k < n; ++k) this->data[k] = {fill};\n"
                f"  this->size = n;\n}}")
    elif member == "copy_ctor":
        text = (f"/* [container.requirements.general] Table 83 (X u(a);): u == a; [vector.cons]. */\n"
                f"/*@ requires \\valid(this) && {v}_readable(other) && \\separated(this, other);\n    assigns *this;\n"
                f"    allocates this->data;\n"
                f"    ensures {v}_valid(this) && this->size == other->size;\n"
                f"    ensures \\forall integer k; 0 <= k < other->size ==> this->data[k] == other->data[k]; */\n"
                f"static void {v}_copy_ctor({v} *this, const {v} *other) {{\n"
                f"  this->data = NULL; this->size = 0; this->capacity = 0;\n"
                f"  if (other->size == 0) return;\n"
                f"  this->data = swdb_alloc_{_mangle(t)}(other->size);   /* allocation succeeds (assumption entry) */\n"
                f"  this->capacity = other->size;\n"
                f"  /*@ loop invariant 0 <= k <= other->size;\n"
                f"      loop invariant \\forall integer j; 0 <= j < k ==> this->data[j] == other->data[j];\n"
                f"      loop invariant \\initialized(this->data + (0 .. k - 1));\n"
                f"      loop assigns k, this->data[0 .. other->size - 1];\n      loop variant other->size - k; */\n"
                f"  for (size_t k = 0; k < other->size; ++k) this->data[k] = other->data[k];\n"
                f"  this->size = other->size;\n}}")
    elif member == "move_ctor":
        text = (f"/* [container.requirements.general] Table 83 (X u(rv);): u holds rv's former value; rv is left valid. */\n"
                f"/*@ requires \\valid(this) && {v}_valid(other) && \\separated(this, other);\n"
                f"    assigns *this, *other;\n"
                f"    ensures {v}_valid(this) && {v}_valid(other);\n"
                f"    ensures this->data == \\old(other->data) && this->size == \\old(other->size); */\n"
                f"static void {v}_move_ctor({v} *this, {v} *other) {{\n"
                f"  *this = *other;\n  other->data = NULL; other->size = 0; other->capacity = 0;\n}}")
    elif member == "dtor":
        text = (f"/* [container.requirements.general] Table 83 (a.~X()): destroys the elements, frees all memory. */\n"
                f"/*@ requires {v}_valid(this) && (this->capacity == 0 || \\freeable(this->data));\n    assigns \\nothing;\n"
                f"    frees this->data;\n"
                f"    ensures \\old(this->capacity) > 0 ==> !\\valid(\\old(this->data)); */\n"
                f"static void {v}_dtor({v} *this) {{ swdb_free(this->data); }}")
    elif member == "operator_index":
        text = (f"/* [sequence.reqmts] Table 88 (a[n]: *(a.begin() + n)); n < size() is the caller's obligation. */\n"
                f"/*@ requires {v}_readable(this) && n < this->size;\n    assigns \\nothing;\n"
                f"    ensures \\result == this->data + n; */\n"
                f"static {ref}{v}_operator_index(const {v} *this, size_t n) {{\n"
                f"  SWDB_MODEL_REQUIRE(n < this->size, \"{INDEX_PRECONDITION}\");\n"
                f"  return this->data + n;\n}}")
    elif member == "at":
        text = (f"/* [sequence.reqmts] Table 88 (a.at(n): *(a.begin() + n); throws out_of_range if n >= a.size()).\n"
                f"   Exceptions are outside the subset: n < size() is the caller's obligation. */\n"
                f"/*@ requires {v}_readable(this) && n < this->size;\n    assigns \\nothing;\n"
                f"    ensures \\result == this->data + n; */\n"
                f"static {ref}{v}_at(const {v} *this, size_t n) {{\n"
                f"  if (n >= this->size) SWDB_MODEL_FAIL(\"{OUT_OF_RANGE}\");\n"
                f"  return this->data + n;\n}}")
    elif member == "data":
        text = (f"/* [vector.data] p1: [data(), data() + size()) is a valid range. */\n"
                f"/*@ requires {v}_readable(this);\n    assigns \\nothing;\n    ensures \\result == this->data; */\n"
                f"static {ref}{v}_data(const {v} *this) {{ return this->data; }}")
    elif member == "size":
        text = (f"/* [container.requirements.general] Table 83 (a.size()). */\n"
                f"/*@ requires {v}_readable(this);\n    assigns \\nothing;\n    ensures \\result == this->size; */\n"
                f"static size_t {v}_size(const {v} *this) {{ return this->size; }}")
    elif member == "empty":
        text = (f"/* [container.requirements.general] Table 83 (a.empty(): a.begin() == a.end()). */\n"
                f"/*@ requires {v}_readable(this);\n    assigns \\nothing;\n"
                f"    ensures \\result <==> this->size == 0; */\n"
                f"static bool {v}_empty(const {v} *this) {{ return this->size == 0; }}")
    elif member == "begin":
        text = (f"/* [container.requirements.general] Table 83 (a.begin()); the iterator is a pointer. */\n"
                f"/*@ requires {v}_readable(this);\n    assigns \\nothing;\n    ensures \\result == this->data; */\n"
                f"static {ref}{v}_begin(const {v} *this) {{ return this->data; }}")
    elif member == "end":
        text = (f"/* [container.requirements.general] Table 83 (a.end(): past the end); the iterator is a pointer. */\n"
                f"/*@ requires {v}_readable(this);\n    assigns \\nothing;\n"
                f"    ensures \\result == this->data + this->size; */\n"
                f"static {ref}{v}_end(const {v} *this) {{ return this->size == 0 ? this->data : this->data + this->size; }}")
    elif member == "push_back":
        text = (f"/* [vector.modifiers] p1: push_back(const T& x) appends x; it causes reallocation if the new size is\n"
                f"   greater than the old capacity (every pointer, reference and iterator then becomes invalid). */\n"
                f"/*@ requires {v}_valid(this) && this->size < {m};\n"
                f"    assigns *this, this->data[this->size];\n    allocates this->data;\n    frees this->data;\n"
                f"    ensures {v}_valid(this) && this->size == \\old(this->size) + 1;\n"
                f"    ensures this->data[\\old(this->size)] == x;\n"
                f"    ensures \\forall integer k; 0 <= k < \\old(this->size) ==> this->data[k] == \\old(this->data[k]);\n"
                f"    ensures \\old(this->size) < \\old(this->capacity) ==> this->data == \\old(this->data);\n"
                f"    ensures \\old(this->size) == \\old(this->capacity) && \\old(this->capacity) > 0 ==>\n"
                f"            !\\valid(\\old(this->data)); */\n"
                f"static void {v}_push_back({v} *this, {_decl(t, 'x')}) {{\n"
                f"  if (this->size == this->capacity) {v}_grow(this, {v}_recommend(this, this->size + 1));\n"
                f"  this->data[this->size] = x;\n"
                f"  this->size += 1;\n}}")
    elif member == "resize":
        text = (f"/* [vector.capacity] p13-p15: resize(sz) erases the last size() - sz elements, or appends sz - size()\n"
                f"   value-initialized ones; reallocation happens if sz is greater than the old capacity. */\n"
                f"/*@ requires {v}_valid(this) && n <= {m};\n"
                f"    assigns *this, this->data[0 .. this->capacity - 1];\n    allocates this->data;\n    frees this->data;\n"
                f"    ensures {v}_valid(this) && this->size == n;\n"
                f"    ensures \\forall integer k; 0 <= k < n && k < \\old(this->size) ==> this->data[k] == \\old(this->data[k]);\n"
                f"    ensures \\forall integer k; \\old(this->size) <= k < n ==> this->data[k] == 0;\n"
                f"    ensures n <= \\old(this->capacity) ==> this->data == \\old(this->data);\n"
                f"    ensures n > \\old(this->capacity) && \\old(this->capacity) > 0 ==> !\\valid(\\old(this->data)); */\n"
                f"static void {v}_resize({v} *this, size_t n) {{\n"
                f"  if (n > this->capacity) {v}_grow(this, {v}_recommend(this, n));\n"
                f"  size_t k = this->size;\n"
                f"  /*@ loop invariant this->size <= k && (k <= n || k == this->size);\n"
                f"      loop invariant \\forall integer j; this->size <= j < k ==> this->data[j] == 0;\n"
                f"      loop invariant \\initialized(this->data + (0 .. k - 1));\n"
                f"      loop assigns k, this->data[this->size .. n - 1];\n      loop variant n - k; */\n"
                f"  for (; k < n; ++k) this->data[k] = {zero};\n"
                f"  this->size = n;\n}}")
    elif member == "reserve":
        text = (f"/* [vector.capacity] p3-p5: reserve(n): if n > capacity(), reallocation happens (capacity() >= n after);\n"
                f"   n > max_size() throws length_error: an exception, so n <= max_size() is the caller's obligation. */\n"
                f"/*@ requires {v}_valid(this) && n <= {m};\n"
                f"    assigns *this;\n    allocates this->data;\n    frees this->data;\n"
                f"    ensures {v}_valid(this) && this->size == \\old(this->size) && this->capacity >= n;\n"
                f"    ensures \\forall integer k; 0 <= k < this->size ==> this->data[k] == \\old(this->data[k]);\n"
                f"    ensures n <= \\old(this->capacity) ==> this->data == \\old(this->data);\n"
                f"    ensures n > \\old(this->capacity) && \\old(this->capacity) > 0 ==> !\\valid(\\old(this->data)); */\n"
                f"static void {v}_reserve({v} *this, size_t n) {{\n"
                f"  if (n > this->capacity) {v}_grow(this, n);\n}}")
    elif member == "clear":
        text = (f"/* [sequence.reqmts] Table 88 (a.clear(): destroys every element; a.empty() after). */\n"
                f"/*@ requires {v}_valid(this);\n    assigns this->size;\n"
                f"    ensures {v}_valid(this) && this->size == 0; */\n"
                f"static void {v}_clear({v} *this) {{ this->size = 0; }}")
    elif member == "swap":
        text = (f"/* [vector.special] p1, [container.requirements.general] Table 83 (a.swap(b): exchanges the contents;\n"
                f"   no iterator is invalidated). */\n"
                f"/*@ requires {v}_valid(this) && {v}_valid(other) && \\separated(this, other);\n"
                f"    assigns *this, *other;\n"
                f"    ensures this->data == \\old(other->data) && this->size == \\old(other->size);\n"
                f"    ensures other->data == \\old(this->data) && other->size == \\old(this->size);\n"
                f"    ensures {v}_valid(this) && {v}_valid(other); */\n"
                f"static void {v}_swap({v} *this, {v} *other) {{ {v} t = *this; *this = *other; *other = t; }}")
    else:
        raise KeyError(member)
    out.append((f"{v}_{member}", text))
    return out


def pair_member(p, a, b, member):
    """(C name, C text) of one pair member."""
    if member == "ctor_default":
        text = (f"/* [pairs.pair] p2-p3: pair(): value-initializes first and second. */\n"
                f"/*@ requires \\valid(this);\n    assigns *this;\n"
                f"    ensures this->first == 0 && this->second == 0; */\n"
                f"static void {p}_ctor_default({p} *this) {{ this->first = ({a})0; this->second = ({b})0; }}")
    elif member == "ctor":
        text = (f"/* [pairs.pair] p5-p11: pair(x, y): initializes first with x and second with y. */\n"
                f"/*@ requires \\valid(this);\n    assigns *this;\n"
                f"    ensures this->first == x && this->second == y; */\n"
                f"static void {p}_ctor({p} *this, {_decl(a, 'x')}, {_decl(b, 'y')}) {{ this->first = x; this->second = y; }}")
    elif member == "copy_ctor":
        text = (f"/* [pairs.pair] p2 (pair(const pair&) = default): copies first and second. */\n"
                f"/*@ requires \\valid(this) && \\valid_read(other) && \\initialized(other);\n    assigns *this;\n"
                f"    ensures this->first == \\old(other->first) && this->second == \\old(other->second); */\n"
                f"static void {p}_copy_ctor({p} *this, const {p} *other) {{ *this = *other; }}")
    elif member == "operator_assign":
        text = (f"/* [pairs.pair] p15-p17: operator=(const pair& p) assigns p.first to first and p.second to second;\n"
                f"   returns *this. */\n"
                f"/*@ requires \\valid(this) && \\valid_read(other) && \\initialized(other);\n    assigns *this;\n"
                f"    ensures this->first == \\old(other->first) && this->second == \\old(other->second);\n"
                f"    ensures \\result == this; */\n"
                f"static {p} *{p}_operator_assign({p} *this, const {p} *other) {{ *this = *other; return this; }}")
    else:
        raise KeyError(member)
    text = text.replace("    ensures ", "    ensures \\initialized(this);\n    ensures ", 1)
    return f"{p}_{member}", text


# --- model proof units (swdb.c_lowering) ------------------------------------------------------------------------------

def _element(mangled):
    """The C element type whose mangled spelling is `mangled` (scalars and pointers to them), or None."""
    from swdb import c_lowering
    stars = 0
    while mangled.endswith("_ptr"):
        mangled, stars = mangled[:-4], stars + 1
    for name in sorted(c_lowering.INTEGER_TYPES | c_lowering.FLOAT_TYPES | set(c_lowering.INTERNAL_TYPES.values())):
        if _mangle(name) == mangled:
            return name + (" " + "*" * stars if stars else "")
    return None


def _vector_types(v, t):
    return (f"typedef struct {v} {v};\nstruct {v} {{ {' '.join(vector_struct_fields(t))} }};\n{MACROS}\n"
            f"{vector_logic(v, t)}")


def _vector_unit(match):
    v, member = match.group(1), match.group(2)
    t = _element(v[len("std_vector_"):])
    if t is None or t == "bool":
        return None
    head = [(f"{v}_types", _vector_types(v, t))]
    if member in ("recommend", "grow"):
        recommend, grow = _helpers(v, t)
        return head + (allocator(t) + [(f"{v}_grow", grow)] if member == "grow" else [(f"{v}_recommend", recommend)])
    return head + vector_member(v, t, member)


def _pair_unit(match):
    rest, member = match.group(1), match.group(2)
    words = rest.split("_")
    for cut in range(1, len(words)):
        a, b = _element("_".join(words[:cut])), _element("_".join(words[cut:]))
        if a and b:
            p = f"std_pair_{rest}"
            types = f"typedef struct {p} {p};\nstruct {p} {{ {_decl(a, 'first')}; {_decl(b, 'second')}; }};"
            return [(f"{p}_types", types), pair_member(p, a, b, member)]
    return None


def model_text(name):
    """Self-contained C text for the public `swdb prove --model NAME` seam."""
    members = "|".join(sorted(set(VECTOR_MEMBERS) | {"recommend", "grow"}, key=len, reverse=True))
    match = re.fullmatch(rf"(std_vector_\w+?)_({members})", name)
    definitions = _vector_unit(match) if match else None
    if definitions is None:
        match = re.fullmatch(rf"std_pair_(\w+?)_({'|'.join(sorted(PAIR_MEMBERS, key=len, reverse=True))})", name)
        definitions = _pair_unit(match) if match else None
    return "\n".join(text for _, text in definitions) if definitions else None

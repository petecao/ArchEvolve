# 25 — std::vector and std::pair models

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 20:05 ET (Answer); 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 22, 24
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Formal-half language and the C++ subset": the C++ subset and the standard-library model; "Modules", library content: the `std::vector` and `std::pair` models; "What a proven verdict asserts": the assumption set; "Records and levels": the method-version file lists the `std::vector` model; "Testing Decisions", seam 1; choice S1); decisions: [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 6, 7; also [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 11 (undefined behavior is a proof obligation)
**Time estimate:** about 1 week

**What to build:** Candidate artifacts that use `std::vector<T>` (not `bool`) or `std::pair` can be proven, and no verifier ever runs libc++ internals. Each type is modeled: a C struct (for the vector: data, size, capacity) plus one C function per member, each with an ACSL contract citing the standard's clauses (`[vector]` for the vector). Vector members: construction by count, by count and value, copy, move; destruction; `operator[]`, `at`, `data`, `size`, `empty`; `begin`, `end` and range-for; `push_back`, `resize`, `reserve`, `clear`, `swap`. The C lowering tool lowers each use to a model call; WP reads the ACSL; 22's translator turns the same contracts into SAW overrides. The model catches what tests miss. Growth frees the old buffer, so a stale pointer or iterator fails the proof. `at` out of range is a proof obligation. Growing a shared vector outside `critical` is stated here as a sharing-class obligation of the model. Its tests live elsewhere: the WP obligation in 45 — Per-thread lowering (it reads not proven, since WP never refutes), and the refutation at threads ≥ 2 in 46 — CIVL adapter. Proof records gain two assumption entries: "the pinned standard library implements the modeled members as the standard says" (trusted tool) and "allocation succeeds".

## Acceptance

- [ ] Each modeled member has a C function and an ACSL contract citing the standard's clause for it (`[vector]` for vector members). `swdb prove` proves every contract against its C function once, recorded with subject "a library entry's summary".
- [ ] A fixture proof unit that uses vector members (`size`, `operator[]`, `push_back`, range-for) and `std::pair` lowers, proves in WP, and proves in SAW on the C++ with the model's overrides in place of libc++ code. The C++ and C lowering verdicts agree.
- [ ] SAW's overrides reach the model struct's fields through debug information (16 item 3). The record lists the model's summary as used.
- [ ] Stale pointer: a fixture that keeps `data()` or an iterator across a growing `push_back` and then reads through it is refuted by the bounded verifier with a counterexample. WP does not prove it.
- [ ] `at`: a call whose index may reach `size()` is refuted; the same call behind a bounds check proves.
- [ ] Shared growth as a sharing-class obligation (16 item 7): each member that can reallocate (`push_back`, `resize`, `reserve`) names in `assigns` the struct fields and buffer it writes, so in a parallel region a growth is a write to the vector under its sharing class. No test here: 45 checks the WP obligation, 46 the CIVL refutation at k ≥ 2.
- [ ] Assumption entries: every proof record of a unit that uses the model lists "the pinned standard library implements the modeled members as the standard says" (kind trusted tool) and "allocation succeeds", each with its reference (ID and hash) and plain sentence. A unit that uses `new[]` also lists "allocation succeeds". A unit that uses neither lists neither.
- [ ] `std::vector<bool>` and any unmodeled member read not proven, "unsupported construct".
- [ ] The model has a version, pinned in every dependent record's content-hash set. Changing one member's contract gives a new pin.
- [ ] On the Mac, real jobs go through 21's lock, one at a time, under the ~8 GB RSS watchdog. Tests that need SAW, Frama-C or LLVM 22 skip cleanly. Fixtures use no BC, PR or SSSP code.

## Notes

- **Not in this ticket:**
  - 24 — C++ subset widening: every other construct, including the C lowering of `new[]`.
  - 45 — Per-thread lowering: element accesses in a parallel region following the sharing class of `data`, and the WP obligation for shared growth outside `critical` (not proven).
  - 46 — CIVL adapter: the threads ≥ 2 refutation of shared growth outside `critical`, using this model.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions: ACSL reference definitions proven against the lowered reference code, which this model makes possible.
  - 26 — Logic and sum libraries: logic-library accessors.
  - 11 — Method-version file and failure classes: listing this model in the method-version file.
- Assumption (not decided in the map): `std::pair`'s modeled members are construction, copy, assignment, `first` and `second`. Others join when a fixture needs them. The map names only `[vector]`; the pair's contracts cite the standard's `[pairs]` clauses.
- Assumption (not decided in the map): the citations name clauses of the C++ standard edition the fork builds with.
- Removed (review, 2026-10-13): a single-thread precondition on growth members, checked against ghost state kept by the C lowering of OpenMP. SAW on the C++ cannot see that state, so the C++ and C-lowering verdicts would disagree on the shared-growth fixture, which breaks 22's agreement rule.
- Flag for Yan-Ru: the map's "refuted" (16 item 7) is met in 46 (CIVL at k ≥ 2), which is blocked by this ticket; 45's WP obligation can only read not proven, since WP never refutes. 25 is upstream of 45 (through 44, 31 and 30) and of 46.
- Assumption (not decided in the map): the model's contracts follow 20's allowed-ACSL rules, so "growth frees the old buffer" is stated in `ensures` through `\valid` (the old buffer is no longer valid), not with a `frees` clause.
- Assumption (not decided in the map): the map names no kind for "allocation succeeds". Proposed: trusted tool, like the standard-library entry.
- Assumption (not decided in the map): one proof record per model version covers all its members' contracts.
- A read through a stale pointer is undefined behavior, so it is a proof obligation and a bounded counterexample refutes it (11 item 11).
- The rest of the standard library follows one modeled type at a time (16 item 7).

## Answer

2026-10-14 20:05 ET. **Resolved, partly.** The models exist, the C lowering uses them, and CBMC proves the
fixture unit, refutes stale pointers and iterators, and refutes an unchecked `at`. The WP boxes are **not met**
(see "Not met"). Branch `probata-poc/t25`. Interface doc:
[`format-v0.4-std-models.md`](../../../docs/reference/format-v0.4-std-models.md).

**What was built**

| Piece | Where |
|---|---|
| The models: `std_vector_<t>` {data, size, capacity}, `std_pair_<a>_<b>` {first, second}; 18 vector and 4 pair member functions, each with an ACSL contract citing its C++17 clause; libc++'s growth policy; `identity()`, `assumptions()`, `pins()`, `method_problem()` | `swdb/std_models.py` (`swdb-std-models-1`) |
| Lowering hooks next to `_Printer._std`: types, constructors, destructors at scope end, member calls, `operator[]`, pair `=`, iterators as `T *`, range-for, `std::swap`; `return` out of a destroying scope (`swdb_return`); `break`/`continue` check only their loop's scopes; `vector`/`pair` lifted out of `STD_CONTAINERS`. `TOOL_VERSION` 3, `kept-names.3` | `swdb/c_lowering.py` |
| CBMC: model pin, settings, assumption entries, method-version check, `--no-malloc-may-fail` when the lowering allocates; differential under AddressSanitizer when the lowering allocates (an input with undefined behavior on either side is no agreement evidence, counted in `undefined_behavior_runs`); C++ cut includes `<vector>` | `swdb/cbmc_adapter.py` |
| Translator 2: `SWDB_MODEL_REQUIRE`/`SWDB_MODEL_FAIL` hooks; the C++ harness turns `std::out_of_range` into the model's failed check | `swdb/cbmc_translator.py` |
| WP: same pin, assumption entries and method-version check | `swdb/wp_adapter.py` |
| Proof schema `pins.std_models`; method-version draft `method.probata-draft-2` (lowering 3, translator 2, `models`) | `schemas/proof.schema.json`, `library/methods/probata-draft-2.yaml` |
| Fixtures | `tests/fixtures/proof/lowering/vector_pair.cc` (+ harness), `tests/fixtures/proof/cbmc/vector_units.cc` |

**Acceptance, box by box**

- Each member has a C function and a contract citing its clause: **met** (`test_each_modeled_member_has_a_c_function...`;
  the contracts type-check in Frama-C). Proven once as a `library_summary` record: **not met** (below).
- Fixture unit (`size`, `operator[]`, `push_back`, range-for, `std::pair`): lowers, and CBMC proves it with the
  C-vs-C++ differential agreeing (C++ on real libc++): **met**. WP proof: **not met**.
- "SAW overrides through debug info": per ticket 22's translation, CBMC runs the model **bodies** on the C
  lowering, never libc++; the record lists the model in `pins.std_models` and `settings.std_models`: **met** in
  that form (Assumption below).
- Stale pointer (`data()`) and stale iterator (`begin()`) across a growing `push_back`: refuted by CBMC, the
  counterexample (`n = 1`) replays on the C++ under AddressSanitizer: **met**. "WP does not prove it": **not run**.
- `at`: refuted when `k` may reach `size()` (property `std.vector.at.out_of_range`, replayed on the C++); the same
  call behind a bounds check proves: **met**.
- Shared growth: `push_back`, `resize`, `reserve` name `*this` and the buffer in `assigns` and state the old buffer
  invalid after growth: **met** (`test_a_reallocating_member_...`).
- Assumption entries (library: trusted tool; allocation: trusted tool), `new[]` alone lists allocation only,
  neither lists neither: **met** (CBMC records and `std_models.assumptions`; WP adapter wired, not run).
- `std::vector<bool>` and unmodeled members (`pop_back`, vector `=`, pair `swap`, vector of a class, range-for
  over an array): unsupported construct with name and line: **met**.
- Version pinned in every dependent record; one changed contract gives a new pin: **met**. The method version
  must pin the same model, else no job runs.
- Lock, watchdog, clean skips, no BC/PR/SSSP code: **met**.

**Not met, and why**

- WP. One exploratory WP job on the 23 model functions (frozen flags, 10 s solver timeout) proved 293 of 322 goals:
  every member that neither allocates nor frees proved fully. The 29 open goals are `malloc` result validity,
  `free`'s `freeable` precondition and libc heap-status `assigns` in `grow`, `dtor`, `push_back`, `resize` and the
  allocating constructors. Closing them needs an ACSL form of "allocation succeeds" that WP 33 accepts (no
  `\fresh`, ticket 07). Until then the unit-level WP proof and the stale-pointer "not proven" WP run wait too.
  Log `/tmp/claude/probata-runs/t25/wp-models/wp.log` (sha256 `670e9248ceb9f693`...).
- Model proof record: models are not library entries, so `swdb prove --summary` cannot name them; ticket 24 has
  the same gap for `std::min` and friends. Suggest one follow-up for both.

**Assumptions** (not decided in the map)

- Assumption: CBMC runs the model bodies, not stubs from the contracts (ticket 22's hand-off said `tr.stub`). A stub
  cannot free a buffer, so a stale pointer would go unseen; the bodies are short, reviewed C. WP still reads the
  contracts.
- Assumption: the growth policy (when capacity grows, by how much) follows libc++ 22.1.8, so counterexamples replay;
  contracts state only what the standard says.
- Assumption: elements are scalars or pointers in model version 1; classes, `bool` and nested vectors are refused.
- Assumption: iterators are `T *`; a range-for keeps clang's `__rangeN`, `__beginN`, `__endN` names.
- Assumption: "allocation succeeds" is kind `trusted_tool` (the ticket's proposal; `platform_choice` also fits).
  Its reference is the model version, or the C lowering tool when only `new[]` allocates.
- Assumption: in the differential, an input where either side's sanitizer fires is excluded from agreement (UB has
  no defined output); CBMC refutes it on its own.

**Side findings**

- CBMC 6 lets `malloc` return NULL by default: every allocating unit got spurious NULL failures until the adapter
  passed `--no-malloc-may-fail` (tied to the allocation entry). Ticket 24's `new[]` fixtures will hit this under CBMC.
- A call returning a reference used as a statement (`p = q` on a pair, also 24's class operators) printed
  `(*f(...));`, which `-Wall -Werror` rejects; fixed by dropping the `*`.
- ACSL predicates cannot take `const` struct pointers in Frama-C 33 (caught by the type-check test).

**Evidence.** Targeted runs (no xdist, `-m "not whole_store"`): `tests/test_c_lowering.py` 65 passed;
`tests/test_std_models.py` 5 passed + 1 that timed out at 600 s in the verifier queue, rerun alone: passed
(`report-r12.jsonl` sha256 `acd62b6245278123`..., `report-r13.jsonl` `5a6372e9772c152d`...). Post-merge numbers:
see the commit. Runs: `/tmp/claude/probata-runs/t25/`.

**Interface notes**

- 30 (reference definitions): reference code using `std::vector<T>` lowers now; contracts can use
  `std_vector_<t>_valid(v)`, `v->data`, `v->size`. A helper function taking a vector cannot be in the C++ cut of
  the differential yet (its C prototype names the model struct): keep vectors local to the unit, or extend
  `Code.cxx_text`.
- 45/46 (parallel regions): growth members' `assigns *this, this->data[...]` is the write to read against the
  sharing class; element access goes through `std_vector_<t>_operator_index` (or `data()` pointers).
- 11/59: `method.probata-draft-2` carries `models`; it must be regenerated if 24 edits the lowering again
  (`/tmp/claude/probata-runs/t25/make_draft2.py`).

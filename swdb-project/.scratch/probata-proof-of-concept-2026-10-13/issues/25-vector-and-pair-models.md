# 25 — std::vector and std::pair models

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
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

## Resume checkpoint — 2026-10-15

Status remains `claimed`: vector growth does not yet satisfy the WP acceptance criterion.
Recovered the prior vector/pair model implementation from `probata-poc/t25` into the current integration
architecture, retaining `swdb prove --model NAME`, subject `c_model`, and `pins.models`. The obsolete
`swdb.models` / `--summary model.NAME` path is not recovered. The lowering retains ticket 24's C models,
summary parameter names and restrict qualifiers, plus ticket 27's hazard probes.

Current validation: `tests/test_c_lowering.py`: **65 passed** (51.64 s), report
`/private/tmp/t25-lowering-all.jsonl`; `tests/test_std_models.py` bounded tests: **6 passed** (39.28 s), report
`/private/tmp/t25-report-models3.jsonl`. The bounded proof of the vector/pair maximum fixture succeeds;
stale `data()` and iterator reads are refuted with replayed C++ sanitizer counterexamples; unchecked `at`
is refuted and checked `at` proves. These jobs used the verifier lock and RSS watchdog. A first sandboxed
attempt failed because macOS denied the watchdog process-tree inspection; the authorized unsandboxed rerun
passed. No watchdog was disabled.

Assumption: scalar and pointer elements remain the model's declared subset. CBMC executes the reviewed C
model bodies with real malloc/free, rather than assuming contracts that cannot express lifetimes in its
stub translator. A changed model source changes its version pin and method admission check.

WP 33 still cannot establish allocation/deallocation lifetime facts. Existing retained diagnostic
`/tmp/claude/probata-runs/t25/wp-models/wp2.log`, lines 37–49, explicitly says allocation, initialization and
danglingness are not implemented; its historical 309/327 goals is partial evidence only. The safe current
fallback refuses units containing releases, including implicit vector destruction, before WP. Ticket 27's
adapter integration adds that fail-closed check. No expected failure or paused skip counts as completion.

A future sound remedy needs either a verifier with supported allocation lifetimes or a validated transformation
that carries allocation identities and liveness through every pointer alias and dereference. Adding ghost
size/capacity fields alone does not make a raw stale `T *` read invalid and is insufficient. A bounded fixed
storage pool would change the unbounded proof scope, so it cannot silently replace the accepted model.

The recovered pair constructor also proves through the public `swdb prove --model std_pair_int_int_ctor
--adapter wp` seam: **1 passed** (18.24 s), `/private/tmp/t25-pair-model.jsonl`; the resulting subject is
`c_model` and `swdb validate` accepts the record. This does not discharge vector allocation obligations.

Standard-library admission (2026-10-15): the concrete growth policy is libc++ 22.1.8, not whichever STL
clang happens to select. The bounded adapter now probes `<vector>` and admits model jobs only with
`_LIBCPP_VERSION=220108`; otherwise it records `not_proven / unsupported_construct` before differential or
CBMC execution. Local headers match. The matched public vector proof passed (16.23 s) and the public
unmatched-library refusal passed (13.72 s), reports `/private/tmp/t25-model-stl-check.jsonl` and
`/private/tmp/t25-stl-refusal.jsonl`. Linux clang using libstdc++ 13 is outside this model and cannot supply
its bounded differential evidence. A single stale translator-version literal in the broader adapter
regression was corrected; that broader subset was not completed.


Initialized model/dependency checkpoint — 2026-10-15 ET: model version2 requires initialized read
inputs and establishes initialized written outputs (copy/swap/atomics/pair; vector representation
and live element prefix, excluding spare capacity). The original copy contract failed the new
mandatory WP init checks; repaired public model records for copy, swap, atomic load, compare-exchange
and pair copy all prove. The initialized copy caller proves; an uninitialized source is refused by
its precondition even when the caller post ignores the copied value. Seven invalid dependency
controls refuse, and the current-method summary control proves. `level-rule.4` now checks C-model
text pins and transitive model dependencies; WP requires counting same-method/evidence dependencies.
Reports: `/private/tmp/probata-lifetime-research-2026-10-15/model-init-{red,green2}.jsonl`,
`model-artifact-assertions.json`, `summary-current-control.json`. The green2 run had13passing tests
and one goal-name-only assertion failure; all five actual model records were proven and the corrected
artifact assertions passed for all five without repeating successful verifier runs. The level-rule
regression passed97tests. Status stays **claimed** because general vector deallocation is unsupported.

# 25 — std::vector and std::pair models

Created: 2026-10-13 22:17 ET
Updated: 2026-10-16 ET (four original int/int pair bodies and exact-dependency caller profile accepted; wider ticket remains open); 2026-10-15 ET (original vector/pair maximum workflow WP view accepted; member/bounded frontier remains open); 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 22, 24
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Formal-half language and the C++ subset": the C++ subset and the standard-library model; "Modules", library content: the `std::vector` and `std::pair` models; "What a proven verdict asserts": the assumption set; "Records and levels": the method-version file lists the `std::vector` model; "Testing Decisions", seam 1; choice S1); decisions: [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 6, 7; also [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 11 (undefined behavior is a proof obligation)
**Time estimate:** about 1 week

**What to build:** Candidate artifacts that use `std::vector<T>` (not `bool`) or `std::pair` can be proven, and no verifier ever runs libc++ internals. Each type is modeled: a C struct (for the vector: data, size, capacity) plus one C function per member, each with an ACSL contract citing the standard's clauses (`[vector]` for the vector). Vector members: construction by count, by count and value, copy, move; destruction; `operator[]`, `at`, `data`, `size`, `empty`; `begin`, `end` and range-for; `push_back`, `resize`, `reserve`, `clear`, `swap`. The C lowering tool lowers each use to a model call; WP reads the ACSL; 22's translator turns the same contracts into SAW overrides. The model catches what tests miss. Growth frees the old buffer, so a stale pointer or iterator fails the proof. `at` out of range is a proof obligation. Growing a shared vector outside `critical` is stated here as a sharing-class obligation of the model. Its tests live elsewhere: the WP obligation in 45 — Per-thread lowering (it reads not proven, since WP never refutes), and the refutation at threads ≥ 2 in 46 — CIVL adapter. Proof records gain two assumption entries: "the pinned standard library implements the modeled members as the standard says" (trusted tool) and "allocation succeeds".

## Active implementation — 2026-10-15 21:14 ET

Ticket 24's independently reviewed closure is published at `29709232`, releasing
this dependency gate. Implementation resumes under the user's ongoing approval.
The first slice is a capability demonstration for the original count-value
constructor/destructor through a source-mapped unbounded heap verification view;
it does not claim complete member-body acceptance. The prior bounded controls
and their exact freezes remain unchanged. The coordinator owns actual verifier
admission and both mbit10 lanes.

### First original-body capability preparation — 2026-10-15 ET

The isolated `prototype/25-heap-capability/` now prepares 42 mapped packets for
unchanged int count/value construction and destruction: 41 isolated global check
lemmas (including 4 negative controls and 2 constructive source-entry feasibility
witnesses), plus one actual C arithmetic/layout kernel retaining all its goals.
The incoming heap remains arbitrary and identities are unbounded mathematical
integers. Explicit source/event/clause/RTE/init/frame/lifetime bindings, canonical
input reconstruction and the original full-source gate are reviewed; no desired
postcondition axioms or new original caller premises are added. Generic caller
composition and byte/partial-store translation remain unsupported.

Twenty-one compiler-free public preparation/runner controls pass after merging
integration `f439edf0`; no formal tool has been launched. The first runner review's
four findings are fixed and final independent review passed at `024db66c`
(29 retained pins verified, zero mismatches). Coordinator admission is pending. Actual WP33 import syntax, imported proposition/task hypotheses and all
mapped results remain unvalidated. This is not a model-body proof record or a
completed acceptance item. Evidence:
`../evidence/t25-heap-capability-preparation-20261015.json`; final review:
`../evidence/t25-capability-final-review-v5-024db66c.md`.

### First admitted import failure and stage-order repair — 2026-10-15 ET

The coordinator admitted exact `024db66c` on node1/lane610 with the reviewed v2
entry. Canonical 42 packets, nine selected executable hashes/versions, two WP
artifact hashes, three package bindings and absent ambient WP settings passed.
The first actual Frama-C command exited 1 during initial parsing: `Library Heap
not found` / `no such type Heap::heap`. No generated goal inventory exists; this
is a retained capability failure, not an accepted negative or body proof. The
whole guarded command naturally exited 1 in 1.941s, peak 166,588,416 bytes, without
OOM/timeout; source remained unchanged and the lane released.

The command configured `-wp-library` only after the first `-then`; initial parsing
already imports the heap. The minimal repair supplies the identical pinned path
before the first input parse, retaining it in the later WP phase. A real public
plan RED fails on the old phase ordering; all 22 compiler-free controls then pass.
The heap semantics, all 42 targets, source/event map, original model bytes and
result policy are unchanged. Independent source/entry-v3 diff review passed at `c5216796`; a fresh admitted
actual replay remains required. Review: `../evidence/t25-import-stage-review-c5216796-v3-20261015.md`. Evidence: `../evidence/t25-first-import-failure-v1-20261015.json`
and `../evidence/t25-import-stage-repair-controls-20261015.json`.

### Second admitted import failure and lexical repair — 2026-10-15 ET

The v3 replay at `c5216796` passed the exact canonical manifest comparison with
`024db66c` (`31edfdaf...657ab`), tool/package/ambient checks, and reached the custom
Why3 file. It stopped at `heap_bridge.mlw:72` on the predicate identifier `reads`;
Why3 1.8.2 reserves `reads` and `writes` for effect clauses. Frama-C exited 125,
with no generated goal inventory. The whole run naturally exited 1 in 1.899s,
peak 169,115,648 bytes, without timeout/OOM; source remained unchanged and lane 611
released. This is a preserved syntax failure, not a negative proof result.

The repair uniformly renames these two exported predicates to `can_read` and
`can_write`, including every mapped reference. Inverse substitution recovers all
three changed translation files byte-for-byte. A public lexical RED catches the
old declarations; all 23 compiler-free controls then pass. The original clauses,
mathematical formulas, primitive meanings and 42 target identities remain intact.
Independent alpha review passed at `9d8ca764`: all three source files and 42
packets inverse-restore exactly. A separate coordinator-admitted Why3
`prove --type-only` gate over the exact new Git blob is next, using the existing frozen bootstrap to avoid another full source
clone before grammar/type feasibility is known. No solver/model-record success
is claimed. Evidence: `../evidence/t25-reserved-name-failure-v1-20261015.json` and
`../evidence/t25-effect-keyword-repair-controls-20261015.json`.

### Exact theory syntax/type gate accepted — 2026-10-15 ET

The coordinator's node0/lane 584 type-only run used unchanged bootstrap `c5216796`
and exact new theory commit `9d8ca764`, Git blob `8b3c2bf3...`, content SHA
`5186c27f...`. Pinned Why3 1.8.2 `prove --type-only` accepted the entire theory in
0.0677s, peak 32,890,880 bytes; the whole guarded command exited 0 in 0.6519s,
peak 62,087,168 bytes. There was no timeout/OOM; bootstrap remained clean and the
lane naturally released. Only the unused witness dummy warning remains.

The cold read-only audit checked 70 physical references with zero mismatches,
including nine executables, two WP artifacts (pinned but unused by this type-only
command), configuration, staged theory and 57 standard-library files. Fresh Git
extraction matches the staged bytes; the declared library tree digest matches
`520d9875...`. Evidence: `../evidence/t25-typecheck-cold-audit-v1-9d8ca764-20261015.json`.
The separately retained entry review records the old-bootstrap/new-input boundary.
Independent cold-result/v4-entry review passed: all 70 physical references and
eight raw metadata pins were freshly rehashed, including launched entry/argv
bindings. Actual whole/wrapper budgets were 600/720 seconds. Receipt:
`../evidence/t25-typecheck-cold-and-v4-entry-review-20261015.md`.

This accepts grammar/types only, following [Why3's type-only option](https://why3.org/doc/manpages.html).
It runs no WP or solver, creates no model-body proof record, and establishes no
Frama-C import, source contract, or imported-task hypothesis result. The reviewed
full 42-packet replay is next under coordinator admission; all acceptance boxes
remain open.

### Actual import admitted; diagnostic option failure — 2026-10-15 ET

The v4 full 42 replay at `9d8ca764` passed initial Frama-C parsing/import and
retained normalized C. It then stopped on the unsupported option `-wp-dkey`,
before generating any WP goal. The fresh inventory has zero goals, an unproved
`check_lemma_t25_control_ctor_premises_feasible` property and a module container;
it is not a missing inventory or proof acceptance. The whole run naturally
exited 1 in 1.960s, peak 169,758,720 bytes, without OOM/timeout; source stayed unchanged.

Installed Frama-C33 source identifies `-wp-msg-key` as the actual category option.
The repair uses it in both parsing and WP phases, retaining `print-generated`,
`why3:compile`, `prover:pp_task` and adding `why3:import` to retain the import
inventory. A public plan RED catches the bad flag; all 24 compiler-free controls
pass after the repair. No original formula, target, precondition, heap semantics
or required proof flag changes. Independent source review passed at `9881fff2`
(three primary-source and six control pins verified). Before another full 42
replay, the coordinator
will admit one genuine lemma with actual option-help recognition and complete
import/task/report evidence. Existing input producers remain immutable.
Source review: `../evidence/t25-message-category-review-9881fff2-20261015.md`.
Evidence: `../evidence/t25-diagnostic-option-failure-v2-20261015.json` and
`../evidence/t25-message-category-repair-controls-20261015.json`.

### Representative genuine WP import and task path — 2026-10-15 ET

The coordinator admitted a single source-entry feasibility lemma using immutable
`9d8ca764` theory/packets and the separately reviewed external v2 entry. The
prospective repaired `9881fff2` runner was not executed by this gate. Actual WP
help recognized every selected option; normal Frama-C import, fresh reader,
report inventory and prepared prover-task generation completed. The sole owned
ordinary goal is Valid by CVC5 (0.0359s); Alt-Ergo timed out at its 10-second
solver limit. No project Extern or lemma dependency appears. The generated CSV
contains its header only; the module container remains present in the complete
inventory and was processed by the unchanged production reader.

The whole guarded command exited 0 in 12.836s, peak 436,568,064 bytes, without
whole-command timeout or OOM; the source remained exact and clean. Four prover
task files survive. A cold physical audit checked 30 retained references
(including four repeated task references) with zero hash mismatches. Static
entry review is retained separately from the actual result. Evidence:
`../evidence/t25-representative-entry-review-v2-9881fff2-20261015.md` and
`../evidence/t25-representative-cold-physical-v1-9d8ca764-20261015.json`.

This one constructive feasibility witness is not the arbitrary-heap member-body
proof. Actual task hypotheses include standard Why3 absolute-value/division and
Frama-C Qed arithmetic support in addition to `int.Int`; that closure must be
explicitly inventoried, rather than reading the theory comment as exhaustive.
Independent cold review now accepts this representative's task/import closure:
the CVC5 task has 22 explicitly inventoried standard arithmetic support
assertions, nine constant-map definitional equations and one negated exact
target; there is no imported project desired/current/future lemma. The Alt-Ergo
task adds standard real-arithmetic, split and datatype support. Four task files
comprise two actual
solver tasks and their header-only diagnostic copies. The reviewer checked 26
profile pin instances and 57 standard-library files with zero mismatches, and
pinned the additional Frama-C Qed source. Receipt:
`../evidence/t25-representative-task-closure-and-v5-review-v2-20261015.md`.
The prior receipt is retained; v2 clarifies the Alt-Ergo real-typed order axiom.

The full 42 obligations, all negative controls, numeric RTE/init/smoke goals and
each later task's closure still require actual validation. The prospective v5
entry at published `e56c62dd` changes only its expected commit and passes static
review; it has not run. No acceptance box closes and no `c_model` record is
created by this representative result.

### Complete first-pair capability accepted — 2026-10-15 ET

The coordinator's fresh full run at exact published `e56c62dd` completed all 42
expectations: 37 positive global check lemmas are Valid; the original arithmetic
kernel has ten Valid ordinary goals and one passing normal-reader smoke; four
negative controls remain `not_proven/timeout`. These are 42 matching outcomes,
not 42 proved statements or four refutations. The whole worker exited 0 in
248.222s, peak 535,871,488 bytes; the outer guard exited 0 in 250.254s, peak
587,251,712 bytes, with no watchdog timeout/OOM. Source-after and independent Git
reads confirm exact clean source; lane 613 naturally ended at 03:42:11Z.

Independent cold review verified 508 unique physical references with zero
mismatches, catalogued 500 raw files and reconciled all 132 task files as 66
solver/diagnostic pairs equal after their headers. Every task's hypotheses and
source-specific definitions were checked. Standard support formula bodies match
the representative audit; the numeric kernel additionally uses pinned Frama-C
Cint range/conversion/projection lemmas. Its local dependency graph is acyclic;
seven of its 13 properties have dependencies, all referencing separately Valid
goals. The global
check-lemma rows have no Extern or property dependencies.

The reviewed 12-event original-body map covers initial stores, arbitrary incoming
heap, old-buffer retention, allocation identity/extent/init/frame, unbounded
prefix establishment/step/exit, numeric arithmetic, final post/frame and
destructor read/free/lifetime/frame, including receiver-buffer overlap. No
original caller premise or desired-result axiom was added. This accepts the
capability for the exact original int count/value constructor and destructor
under the explicitly inventoried trusted lowerer/allocator/standard-support TCB.
Evidence: `../evidence/t25-full42-cold-summary-v1-e56c62dd-20261015.json` and
`../evidence/t25-full42-cold-closure-review-e56c62dd-20261015.md`.

The run creates zero production `c_model` records. Public source-mapped heap-view
integration, other members/types, generic caller composition and all ticket
acceptance boxes remain open. The next vertical slice is fresh public
`swdb prove --model` evidence; this capability profile is never promoted from a
cache into such a record.

### Public first-pair heap proof integration prepared — 2026-10-16 ET

The new production heap-view module reconstructs the accepted exact original
mapping and executes each member's positive targets afresh through ordinary
`swdb prove --model`: 27 constructor targets and 11 destructor targets. Default
complete property selection, `+real`, RTE/init/smoke/cache/machdep/portfolio
checks and the normal report reader remain mandatory. Each launch independently
rebuilds all source/VC inputs and checks its sole target ownership. A native
metadata-only helper binds actual Why3 import roots and exact standard support
sources to the selected WP package; shadow roots refuse. Three explicit record
pins retain checker, source certificate and standard foundations. All targets
consume one remaining public wall budget.

Real public RED controls preserve the old allocation refusal and the ignored
build-define admission gap. The final focused native/compiler/stand-in suite
passes 40 cases; the actual-only target skips. It covers both source models,
self-consistent original-source/obligation/theory tampering, shadow imports,
unmapped defines, remaining-budget forwarding, canonical math promotion and
existing ordinary WP launch guards. Final parent formal tools are explicitly
disabled. No actual WP/prover or model-body proof is inferred from these
controls. Evidence: `../evidence/t25-public-heap-preparation-controls-20261016.json`.

The opt-in `scripts/probata_heap_model_profile.py` prepares a fresh two-record
public profile. It requires exact clean source and separate coordinator admission
under one worker/8 GiB guards, with two 1800-second public budgets and a
4200-second whole budget plus wrapper margin. Public actual acceptance, remaining
vector members and generic caller composition are still open.

### Successful public-record writer review correction — 2026-10-16 ET

Independent review blocked the first public-route freeze `31798b27`: after all
successful targets, the aggregate receipt added a key forbidden by the closed
proof schema. A new eleven-target synthetic destructor control reproduces the
public writer refusal; the minimal fix keeps the standard two-key attestation
and retains every child reading in settings. The control then persists a
schema-valid record. The affected public suite passes nine controls with the
actual-only target skipped. Synthetic results are orchestration controls, never
actual proof evidence; the original failure and all producer receipts remain.

Final independent review passes at clean `cea5652b`, after merging integration
`20764a3e`: 25 evidence references and 11 source pins match. Theory, source
mapping, obligations, schema and proof policy are unchanged. The exact CEA
source is the prospective coordinator-owned actual profile input; no actual
public heap proof has run and no acceptance checkbox closes here. See
[writer RED/GREEN](../evidence/t25-public-heap-aggregate-schema-controls-20261016.json),
[blocked review](../evidence/t25-public-heap-source-review-31798b27-20261016.md)
and [final addendum](../evidence/t25-public-heap-source-addendum-cea5652b-20261016.md).

### Fresh original count/value constructor and destructor accepted — 2026-10-16 ET

The reviewed public profile completed at exact clean `cea5652b`. Two fresh
schema-valid `c_model` fixture records are accepted under the explicit
source-to-unbounded-heap translation, allocation, tool and standard-support TCB.
Construction proves all 27 mapped targets (36 ordinary Valid plus one passing
numeric smoke); destruction proves all 11 targets (11 ordinary Valid). All 38
targets retain fresh normal reports and current setup/reader bindings. No
synthetic or prototype proof result is promoted. The original source/contracts
and arbitrary-heap/alias/lifetime domains are unchanged, with no new caller
premise or finite identity bound.

Independent cold review checked all 108 emitted task bodies against the prior
semantic closure, the numeric closed acyclic dependency graph, exact current
Linux runtime/method/source/configuration/foundation bindings, and both persisted
records. All 1,514 checks pass; 482 physical references have zero mismatch. All 749
raw files (43,289,454 bytes) remain remote. Whole/outer guards exited 0 in
446.397/448.044s, peak 1.09/1.14 GB, with no OOM or watchdog timeout. Source stayed
clean; node 1 generation 614 released naturally at 2026-10-16T04:40:57Z. Finite
process visibility limits and unavailable GPU metadata remain explicit.

This closes this two-member public-body limb only. No production-store adoption,
generic caller composition, unchanged growth-body proof or formal C++ equivalence
is claimed, and ticket25 remains claimed with its acceptance boxes open. The
next approved slice is the original int count constructor with explicit zero
initialization; source-domain ownership gaps in growth require a separately
declared model/domain repair and caller discharge. See
[actual review](../evidence/t25-public-heap-cold-review-cea5652b-20261016.md),
[snapshot](../evidence/t25-public-heap-cold-snapshot-final-cea5652b-20261016.json)
and [next slice/domain plan](../prototype/25-remaining-int-model-plan.md).

### Original zero-initializing count constructor prepared — 2026-10-16 ET

The next public slice maps exact `std_vector_int_ctor_count` source and contract,
with no model-version change or extra caller premise. It explicitly specializes
the reviewed universal-value transition at source literal `(int)0`, reconstructs
all eleven source events and C1-C9 obligations, and selects 27 positive targets
including the complete numeric kernel. All 42 existing canonical packet bytes
remain unchanged; 28 distinct count packets append (27 positive and one
omitted-store translator control). The heap definitions are unchanged and the
checker policy becomes 2; old accepted records retain their exact frozen pins.

The public RED preserves the prior allocation refusal, then GREEN reaches the
checked parse-error stand-in. Final controls pass 39 cases with two actual-only
targets skipped. Nonzero fill/postcondition, extra-write and omitted-prefix
tampering refuse before launch; the full 27-target synthetic record passes
normal reading and schema persistence with numeric/smoke reports. These are
preparation controls, never actual proof evidence. Independent source/mapping review passes at clean `bb7170ac`: all 70 canonical
payloads were reconstructed independently, all 51 retained references match,
and the literal-zero specialization, complete source mapping and public
record/deadline checks have no blocker. A coordinator-admitted fresh one-record
profile and actual cold audit remain required; no successful first-pair formal
run is repeated. Review: [source review](../evidence/t25-count-ctor-source-review-bb7170ac-20261016.md). Growth-domain repair and caller
composition remain separate. See
[preparation evidence](../evidence/t25-count-ctor-preparation-controls-20261016.json)
and [preserved packet hashes](../evidence/t25-count-ctor-canonical-comparison-20261016.json).

### Qualified reallocation-domain preparation — 2026-10-16 ET

A separately named `vector-reallocation-domain-3` candidate now prepares public
count/value constructor, grow, reserve and destructor model sources. The original
v2 catalog, contracts and accepted freezes remain unchanged. Every candidate
currently returns not proven before verifier launch; this is preparation toward
a complete public caller composition, not acceptance of a repaired body.

Nonempty backing must be freeable and have a distinct allocation base from the
receiver. Byte-range separation alone does not prevent a free from killing a
receiver in the same larger allocation. This is unary reallocation eligibility,
not exclusive ownership. Cross-view rights and liveness remain caller
obligations, and raw escaped aliases remain legal until release. Construction
keeps its original precondition and adds eligibility/exact-capacity results;
grow/reserve require and preserve eligibility. Destruction retains its original
broader overlap domain. No source premise is silently added to an old contract.

Public RED/GREEN controls retain missing-model, record-schema, original-source
binding and exact-capacity failures. The final preparation envelope passes seven
controls, including two unchanged original heap paths. Four defined native
growth states per original/qualified C body preserve behavior; no invalid-growth,
ASan or actual formal diagnostic ran. Complete unbounded source/VC mapping, fresh
body proofs and source-backed caller discharge are still pending. The full
source fixture includes safe, growth-stale and no-growth alias paths with guarded
empty behavior. See [coverage matrix](../prototype/25-acceptance-coverage-20261016.md),
[candidate/caller plan](../prototype/25-reallocation-domain/README.md) and
[preparation evidence](../evidence/t25-reallocation-domain-preparation-controls-20261016.json).

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


Aggregate-copy side finding — 2026-10-15 ET: the real WP public summary seam initially proved an
ignored copy from an uninitialized ordinary aggregate. Lowerer7 now requires the exact source object
valid and initialized before local/member implicit copy construction. The ignored negative fails
its named user assertion; the initialized positive proves (2 tests,77.36s). Implicit assignment and
unsupported expression contexts fail closed. This is a conservative declared subset while CWG2264
remains under discussion, not a universal C++ UB classification. Reports:
`/private/tmp/probata-aggregate-init-{red,green}.jsonl`. Ticket25 remains claimed; no new WP vector
lifetime acceptance is established by this change.

Final lowerer7 checkpoint: both ignored uninitialized local/member-copy records are `not_proven`
on the generated initialized-source assertion; both initialized local/member copies prove. The
member negative's first pytest assertion was overly specific about WP's truncated goal name; the
corrected semantic assertion passed against both completed negative artifacts without rerunning
those successful negative verifier jobs. Final positive pair:2passed21.33s. Focused lowering:86passed
53.86s including the retained spike native differential;6additional public refusal/order controls
passed1.75s. Reports: `/private/tmp/probata-aggregate-init-final.jsonl` (one test-name assertion failure),
`/private/tmp/probata-aggregate-negative-artifact-assertions.json`,
`/private/tmp/probata-aggregate-init-positive-final.jsonl`,
`/private/tmp/probata-aggregate-lower-green3.jsonl`,
`/private/tmp/probata-aggregate-lower-only-final.jsonl`. All source changes are hash pinned; the
remaining bounded standard-object policy is separate follow-on work.


Bounded initializedness restoration — 2026-10-15 ET: lowerer8 adds the source-hashed
`bounded_std_initialization.py` protocol for initialized scalar standard objects/live prefixes. The
exact std_models2 source body hash is audited separately. Default/count/count-value construction,
append/accessors/index/at, scalar copied range variables and ordinary pair construction/fields are
admitted; spare-capacity reads, unknown or conditional raw prefixes, escaped/cast origins, manual heap
and uninitialized model arguments refuse before execution. Copy/move, resize/clear/reserve/swap,
pointer elements, reference range variables and other untracked protocols stay unsupported. The
checker and lowerer identities both cover the new helper. No body, allocation-success assumption or
lifetime premise was changed.

The five original real CBMC outcomes are restored with mandatory pointer-overflow checks: maximum
PROVEN; stale data and iterator REFUTED with replay; unchecked at REFUTED and checked at PROVEN.
Temporary strict xfails were removed only after the original jobs passed with `--runxfail`. Thirteen
public refusal controls and a changed-model-body audit control pass. A narrowing-count control
reproduced and fixed a new prefix-inference issue: `(unsigned char)256` must not count as256 initialized
elements. Larger converted literals now need a checked constant folder and do not establish a prefix.

After merging integration6497f4f8 (including ticket36 pointer/row/reader policy), the final standard
model plus primitive initializedness suite passed **50 tests,0xfails** in543.83s, with shared verifier
slot waits included. Report:`/private/tmp/probata-std-init-combined-final.jsonl`; compact actual-case
evidence:[t25-bounded-standard-initialization-20261015.json](../evidence/t25-bounded-standard-initialization-20261015.json).
These are `contract_fixture` records and bounded outcomes, not production or unbounded vector WP
acceptance. Ticket25 stays **claimed**. An outside-repository research design at
`/private/tmp/probata-lifetime-research-2026-10-15/vector-owner-view-design.md` outlines separate checked
allocator separation and pointer/buffer-liveness obligations; it is not implemented or claimed proven.


Checked ownership slice checkpoint — 2026-10-15 ET: commit2662f3fc adds a relational WP view for a
closed scalar-vector count-value construction, one captured data alias, optional pre-growth saved
read, one growing append and scalar return. The source has scalar-only input/output, no globals or
escape, and exact audited model-version2 bodies. Every alias read asserts liveness; growth invalidates
it. Source/native artifacts keep ordinary malloc/free. The original `assigns nothing` frame is checked
structurally from source-fresh owned writes and no escape; WP proves a separately reported exact
private-region frame. The checker/certificate and explicit fresh-allocation premise are pinned and
revalidated. This is not a WP proof of the original growing member's ACSL body.

Nine focused public controls passed **as the union of two runs**: the original report has five
completed passing calls (safe, stale, clear, copied alias, local address) but **no SessionFinish**;
the coordinator's finishing report has four passing refusal calls and SessionFinish0 (72.17s).
The safe record is PROVEN with122/122 generated goals and11/11 smoke; the stale record is NOT_PROVEN
with109/110 and11/11 smoke, with only the named `alias_live_after` assertion open. The seven unknown
protocol/address controls refuse before WP. Reports: `/private/tmp/probata-vector-owner-public-green2.jsonl`
and `/private/tmp/probata-vector-owner-refusals-finish.jsonl`. The frozen setup/reader regressions
passed55tests and the new helper-byte execution-method refusal passed1test. Compact records/report
hashes and exact boundaries are in
[t25-checked-vector-ownership-20261015.json](../evidence/t25-checked-vector-ownership-20261015.json).
These are contract-fixture records on the2662 source checkpoint; integration0999dfb7 was merged before
follow-on work. No single completed nine-test run, production-method acceptance or general ticket25
completion is claimed. Repeated allocation sites, iterator protocols, copy/move/resize/reserve/clear/swap,
opaque effects and escaping pointers remain outside this WP slice. Status stays **claimed**.


Standard member contract checkpoint — 2026-10-15 ET: the WP33 default initialization optimization
removed whole representation-predicate hypotheses (including validity) from ordinary RTE goals.
Raw proof display and installed primary source locate the filter at `Conditions.InitFilter` and
`wp_parameters.FilterInit`. Requiring the exact boolean `-wp-no-filter-init` retains existing facts;
no premise or model body changed. Policy-only commit830bc769 has60 scripted setup/reader controls;
four public invalid-switch controls subsequently pass with fresh immutable fixture methods. Raw
null/uninitialized reads, wrong postcondition, contradictory precondition(smoke), and stale alias
remain unproved. A stronger-precondition diagnostic is explicitly excluded from original-contract
acceptance.

The public once-per-member batch proved14 original nonallocating vector/pair model contracts.
The remaining `at` contract's defensive abort failed strict dead-branch smoke despite valid ordinary
goals. A separate exact-model/hash/C-AST checked view replaces only its pure out-of-range guard with
`assert at_guard_false: n < this->size`, under its unchanged original contract. Original/native/CBMC
abort remains. The actual public checked-at final pair passed2tests: at PROVEN8/8reported goals with
smoke and the named assertion counted; a freshly pinned changed-model contract without its bound
refuses before WP. Two public model/checker controls pass separately. The checker is included in
the frozen setup/reader closure and has explicit checker/certificate pins and prelaunch regeneration.

Evidence:[t25-standard-member-contracts-20261015.json](../evidence/t25-standard-member-contracts-20261015.json).
The first batch is honestly14PASS5FAIL: one at smoke gap and four test-isolation assertions masked by
immutable-method validation. Those four pass in a subsequent isolated run; the at pair passes after
the checked view. No single all-member green session is claimed. These contract-fixture results
precede the incoming-pointer array-object domain gate being developed in ticket36; array provenance,
owner/control-buffer separation, general repeated allocation and broader vector lifetime protocols
remain open. Status stays **claimed**.


Final scoped setup validation: **75PASS227.11s** in
`/private/tmp/probata-t25-at-view-setup-canonical.jsonl` (SessionFinish0), with the actual fact driver
also using `-wp-no-filter-init`. Original at proof source and clean handoff helper/adapter/setup bytes
match exactly. A prior mistakenly sandboxed run had62PASS13FAIL because macOS denied the watchdog's
process-tree read; those failures produced no accepted proof evidence. The13 actual controls passed
with escalation, followed by the complete75-test canonical run. No watchdog or smoke check was disabled.


Closed-owner origin staging — 2026-10-15 ET: API82e6af76 supplies exact source declaration/call
registries and an independent C-AST checker for the closed two-site ownership view. Entry-frozen
initial/growth extents are distinguished from live element prefixes; every source/view access maps
to numerical and alias-liveness guards. The C checker audits all bindings, allocation calls, loop
conditions/bodies, capture/invalidation and guard placement rather than exempting an owned view.
Source/native model bodies and the original source contract are unchanged. A pinned trusted-tool
sentence explicitly identifies the typed source allocator/model relation; numerical validity alone
is not used as provenance.

The new public prelaunch report first failed because no origin certificate was recorded. Its first
implementation passed with the seven existing source-protocol refusals (8PASS49.69s); final metadata
control passed1test7.79s. A separate public renderer-mutation batch passed3tests21.59s: source/method
hashes are freshly recomputed, but shifted alias initialization and weakened liveness predicates
still refuse before a verifier. The final batch passed4tests42.77s, including a moved bounds-guard refusal.
Report:`/private/tmp/probata-owner-origin-tamper-final.jsonl` (SessionFinish0). These use stand-in WP and provide no new proven/unbounded production record.

Ticket36 owns the pending lowerer/adapter/source-to-view coupling and transitive helper pins. The
existing nine actual ownership controls must be rerun under that combined method after integration.
No generic field-origin exemption, standalone model-domain acceptance or general ticket25 resolution
is claimed. Status stays **claimed**.

Compact staging evidence:[t25-closed-owner-origins-20261015.json](../evidence/t25-closed-owner-origins-20261015.json).


Closed-owner origin actual replay — 2026-10-15 ET: frozen b876dcb3 remote node1 shard completed
16PASS/SessionFinish0. Actual safe record has119/119ordinaryVALID+11/11smokePASS; stale has
104/105ordinaryVALID+11/11smokePASS, with only distinct open goal alias_live_after. Raw smoke
contradiction attempts time out and are classified as passing smoke by the strict reader. Stale is
NOT_PROVEN, not a WP counterexample. All checked artifact paths/hashes match in place. The fixture
method declares legacy check placeholders; actual returned records separately pin/pass version1
setup/reader. This is contract_fixture evidence for the closed two-site relation, not production
method3 or generic vector/member acceptance. Source-frame projection remains checked structurally;
WP proves the private view frame. Imported typed allocator/model separation is explicit trust.
Evidence:[t25-closed-owner-remote-20261015.json](../evidence/t25-closed-owner-remote-20261015.json).
Outside audit:/private/tmp/probata-owner-remote-b876dcb3-audit.md. Status stays claimed.

Next read-only slice — 2026-10-15 ET: locally owned at() receives an exact per-call qualified domain
with frozen growth extent/live prefix, persistent receiver declaration, producing append model pin,
independent exact defensive-at C-AST audit and checked caller range guard. No user precondition is
added, and standalone incoming-field models keep their conservative refusal. Public prelaunch RED
reproduced unsupported_construct before implementation; after the new relation it reaches the
explicit missing CXXMemberCallExpr source-binding hook (owned by ticket36). No actual new at() WP
acceptance is claimed by this staging checkpoint; shared hook and fresh combined replay follow.


Qualified at handoff — 2026-10-15 ET: public standalone at refusal GREEN1/6.59s; no WP
log is produced. Two public RED sessions each terminate cleanly with one failed test: initial
unsupported call, then the known missing exact member-call source-span hook. Four admission/fault
controls plus two actual safe/out-of-range controls are now written. The other three admission
controls and both actual WP controls remain pending combined ticket36 hook; no new at proof is
claimed. The negative original scalar contract ignores the chosen value, so the at(2) range guard
must fail for n=1 independently of a functional postcondition. A freshly pinned renderer deleting
only that checked guard must refuse via the independent generated-C access checker. Source/native
abort, original contracts and standalone opaque model admission remain unchanged. No heldout or
remote job started for this slice. Evidence:[t25-qualified-owner-at-staging-20261015.json](../evidence/t25-qualified-owner-at-staging-20261015.json).


### Exact qualified at source hook — 2026-10-15 ET

The merge replay reproduced the missing member-call span binding through the public CLI
(one failing test in 2.19s). The narrow hook now resolves each alias/index/at access by exact
AST kind and source span, then binds its persistent receiver declaration ID. An at access
additionally rechecks the exact defensive-at model relation and qualified receiver. The lowerer
content identity now includes `standard_model_view.py` transitively. Four fake-verifier/prelaunch
controls pass **4/4 in 22.83s**, including opaque standalone-model refusal, checked bounds without
new input premises, and refusal after renderer guard deletion. Original safe/stale protocols also
regenerate and recertify. The two actual at WP controls were excluded and remain pending; no
generic member-domain admission or ticket closure is claimed. Evidence:
`evidence/owner-at-source-binding-merge-20261015.json`.


Qualified at actual checkpoint — 2026-10-15 ET: at frozen integration3f177e63, both actual
public controls PASS188.77s. Safe-at PROVEN121ordinaryVALID+11smokePASS (132complete inventoried
and reported goals). Original missing-bounds contract requires only n>=1 and ignores the selected
value: NOT_PROVEN105/106ordinaryVALID+11smokePASS (117complete inventoried/reported goals).
Its sole distinct open ordinary goal is owner_at_guard_1; downstream index/storage/initialization/
read-validity properties are partially proven because they depend on that open assertion, not
independent unconditional successes. No new requires was introduced. Both records pass the actual
strict setup/reader, retain exact source/view/qualified-call certificates and have matching hashes
for every checked report artifact. Raw smoke contradiction attempts time out and count as passing
smoke. The negative is not a WP refutation or CEX. Original-frame projection is structural;
WP proves the distinct private view frame. These are contract_fixture records, not standalone
C-model proofs or general ticket25 acceptance. One local worker, shared2slotlock,8GiB RSS cap;
source/HEAD remained frozen. Retained outputs are <5MiB on APFS with69GiB free at preflight.
Evidence:[t25-qualified-owner-at-actual-20261015.json](../evidence/t25-qualified-owner-at-actual-20261015.json).
Full selected metadata:/private/tmp/probata-owner-at-actual-3f177e63-audit.json. Status stays claimed.


Current-owner data staging — 2026-10-15 ET: the closed two-site grammar permits only an
immediate scalar *v.data() after its sole growth. Exact outer/inner source spans and persistent
receiver bind the read to the append producer and current typed allocation. The full data-model
text/hash and independently parsed pure this->data return are audited; live-prefix and backing
bounds have separate checked assertions at the actual C read. No source/native body or user
contract changes. Existing delegated binding requires no shared core hook. Unchecked pointer
offsets/casts refuse; new current data reads do not revive the initial alias; rehashed weaker
guards/changed returned root/changed model contract refuse before WP. Final8stand-in controls
PASS28.69s; existing11owner/at stand-in regressions PASS65.64s before the final exact data-text
hash guard. Correctly targeted changed-contract RED exposed an unhandled substring extraction,
not an accepted proof; the exact-content refusal fixes it. Two earlier attempts failed in test
setup and are excluded from the intended RED evidence. Actual safe/stale data tests are written
but pending coordinated execution. Status stays claimed; no general model-domain acceptance.
Evidence:[t25-current-owner-data-staging-20261015.json](../evidence/t25-current-owner-data-staging-20261015.json).


Current-owner data actual checkpoint — 2026-10-15 ET: at frozen67dfd7a8 the public pair
PASS2/184.49s. Immediate current-owner data read PROVEN105/105ordinaryVALID+11smokePASS,
116complete inventoried/reported goals. Adding a subsequent read of the initial captured alias
is NOT_PROVEN111/112ordinaryVALID+11smokePASS,123complete inventoried/reported goals; sole
open ordinary goal alias_live_after. The fresh read does not revive its stale predecessor.
Downstream RTE/functional properties in the negative remain conditional/partially proven on
that open assertion, not unconditional safety claims. All checked report hashes and goalsets
match. Actual setup/strictreader pass; source/HEAD stayed frozen with one local worker under
shared2slotlock and8GiB RSS cap (peak353/499MB). Outputs3.7MiB are retained on APFS, preflight
67GiBfree/68%memoryfree. Raw smoke attempts time out and pass strict smoke checking. These are
contract_fixture source-to-view records; no standalone C-model domain, bounded refutation or
whole25 completion is claimed. Frame projection remains structural and allocator/library trust
explicit. Source/native malloc/free and original scalar contracts are unchanged. Status claimed.
Evidence:[t25-current-owner-data-actual-20261015.json](../evidence/t25-current-owner-data-actual-20261015.json).
Outside audit:/private/tmp/probata-owner-data-actual-67dfd7a8-audit.json.


Data handoff validation — 2026-10-15 ET: integration through19c64cb0 merged cleanly.
At combined b6b932fc, new8prelaunch controls PASS29.20s; standalone opaque at refusal passes
separately1test5.74s. Both sessions use stand-in WP; actual safe/stale evidence above remains
pinned67dfd7a8 and is not relabeled as a postmerge proof. No active job remains. No shared
lowerer/adapter hook was added by this data slice; exact source binding stays delegated to
model_domains and all existing source/view regeneration and helper pins remain in force.


Whole vector workflow API staging — 2026-10-15 ET: next frontier is the existing exact
swdb_fixture_vec_max input-copy/push loop, pair maximum, range-for, size/index scan and return.
The new relation projects private storage to unchanged input values; allocation count is symbolic/
unbounded, with no fixed pool or repeated private-address key. Exact full fixture source-token
closure, target AST/signature/int templates and all12model-text pins reject source allocation
hooks, handlers, custom allocators/elements, escapes and extra effects. The imported allocator
frame (preexisting input unchanged) is explicit; successful return alone would not justify
ignoring a handler with observable effects. Every transition lists its separate standalone C-body
proof requirement and does not invent proof IDs. Array origin and input initialization are
explicit in the new WP test's original contract; no view requires is injected. User source/native
and ordinary lowered C remain retained. Helper source/view C AST inventory is implemented;
public prelaunch remains RED until ticket36 forwards entry-window metadata and binds exact
source copy-read/scalar append IDs. The first attempt used unsupported valid_read vocabulary and
is excluded from the intended RED; corrected contract yields unsupported_construct. No actual
WP acceptance, generic model-domain relaxation or ticket completion is claimed.
Plan:/private/tmp/probata-vector-completion-plan.md.
Evidence:[t25-vector-pipeline-api-20261015.json](../evidence/t25-vector-pipeline-api-20261015.json).


Pipeline source-control baseline — 2026-10-15 ET: six public source/refusal controls pass
16.26s before the positive core hook. Wrong append value, captured alias, mutation during range,
comments-split operator-new override, extra global and absent typed window all refuse without WP.
These must run again after the positive path is admitted; a coarse earlier refusal is not proof
of full new checker coverage. Safe whole-workflow and bad-comparison actual tests are written;
neither has been launched. Only the bad comparison is admitted as a second structural variant,
preserving the changed source branch so WP must reject the original maximum specification.
The allocation contract's existing no-preexisting-write frame has its own explicit pin/assumption;
ambient callbacks are not ruled out merely because an allocation eventually succeeds.
Standard provenance admission gap — 2026-10-15 ET: public owner-data source reaches stand-in WP
when a candidate-local `vector` header includes genuine libc++ and adds a global-writing replacement
operator new (original1RED5.84s, `/private/tmp/probata-header-provenance-red.jsonl`). This is an
admission gap, not an actual falseproof. The new `stdlib_provenance` helper checks the full original
TU with matching pinned native libclang, compares exact-driver physical include closure, pins every
transitive header and modeled declaration/binding, rejects std namespace injection, allocation hooks,
handler registration (including global constructors/function pointers), and macro rewriting. Native
parser and actual driver/wrapper bytes are explicit transitive identities. Effective `-###` frontend
args are forwarded into libclang; undeclared wrapper definitions/header injections refuse rather than
silently changing the interpretation. Ordinary project headers and GAPBS pvector diagnostic pass.
Canonical include configuration, source declarations and header contents are rechecked before launch.
Ambient callbacks outside the TU remain the explicit allocator frame premise; allocation success alone
is insufficient, and no new source input requires is added. The reusable source seam covers all std
model symbols (including min/max/copy/swap) and new[]; shared lower/report and both adapter consumers
are being integrated separately by the coordinator. No universal repair or whole-vector acceptance is
claimed before combined public replays. Outside design/evidence pointer:
`/private/tmp/probata-stdlib-provenance-design.md`. Ticket25 remains claimed.


### Original full-TU admission integration — 2026-10-15 10:49 ET

The native libclang certificate is now bound through all standard-model consumer
paths and replayed immediately before differential execution or solver launch.
Twenty focused source/allocator/bounded-route controls and four stand-in prelaunch
controls pass. Independent review's custom unqualified allocator and fallback
coverage diagnostic findings are repaired. Actual WP current-owner/stale-alias
acceptance is running at frozen `00b16733`; no new actual success is claimed here.
[Focused evidence](../evidence/stdlib-source-provenance-20261015.json). General
vector/member and whole-pipeline acceptance remain open.


### Source gate actual acceptance — 2026-10-15 10:53 ET

Frozen `00b16733` passed the actual current-owner/stale-alias pair: **2 passed in
243.20s**, peak 651 MiB under the shared 8 GiB watchdog. The safe record has
105 ordinary Valid goals and 11 passing smoke checks. The stale record retains
one timed-out `alias_live_after` obligation (111 ordinary Valid plus 11 passing
smoke checks), so it remains not proven. Both original-TU certificates and shared
setup replays pass; all referenced artifact hashes and the prospective runtime
manifest match. The audit resolves pytest symlink aliases before counting records.
[Actual evidence](../evidence/stdlib-source-provenance-actual-20261015.json).
The gate's focused admission and actual pair are accepted; wider vector/member
acceptance and the ticket remain open.


### Original vector/pair workflow — 2026-10-15 ET

The unchanged `tests/fixtures/proof/cbmc/vector_units.cc` maximum function now
proves through the public WP seam under its explicit `a:n` typed input-window
and initializedness contract. Its original push/copy loop, pair maximum,
range-for, size/index scan and scalar result are retained by an exact checked
private-storage projection. Growth/allocation count is symbolic; no fixed pool
or repeated private-address key is used. The source and view both keep
`assigns \nothing;`, and their contract hashes agree.

On frozen `0cc88ffc`, the actual pair passed **2 tests in 182.53 seconds**, peak
0.95 GiB under the 8 GiB watchdog and adapter-owned verifier lease:

| Source | Ordinary goals | Smoke | Verdict |
| --- | --- | --- | --- |
| Unchanged maximum workflow | 77 Valid | 12 passed | proven |
| Changed maximum comparison (`>`→`<`) | 76 Valid, one invariant-preservation timeout | 12 passed | not proven |

Both jobs pass setup, strict fresh-cache reading and the full original-TU
standard-header/declaration gate. The negative is an unproven ordinary obligation,
not a refutation or an ignored smoke failure. [Compact evidence](../evidence/wp-vector-pipeline-20261015.json)
independently checks 173 retained artifact hashes across 23 unique records and
794 original-source/header pins. Pytest symlink aliases are resolved before counting.
The current integration merge after the run changes only run18 documentation;
current runtime identities still equal the actual preflight pins.

The first actual checkpoint, `a876e3a6`, is retained as **not proven**: all 72
ordinary safe-case goals passed, but strict smoke rejected the unreachable
fallback arm of the final conditional. The checked view now normalizes only
that exact pure, initialized integer selector into complementary Boolean products.
Exactly one product is zero, so each product and their sum remain representable
and preserve the original selected value. The original C++ and contract are
unchanged; RTE, initializedness and smoke remain enabled. This rule does not admit
effectful or potentially uninitialized conditional operands. Both fresh-pin fault
controls (noncomplementary multipliers and changed fallback) refuse before WP.

The full source-token closure, target AST, 12 model-text pins and all eight
explicit/implicit standard member/iterator calls are certified. The generic
origin pass exempts only their freshly bound AST identities and the exact source
input read mapped to checked view guards. Every other source operation keeps its
ordinary checks. Independent view checks cover declaration storage/TLS/attributes,
exact local types, extra globals, all phase bodies, annotations and guard placement.
Fifteen stand-in admission/source/renderer controls passed before the return
normalization; its two new fault controls passed afterward. A rehashed static-pair
renderer first reached stand-in WP (diagnosed admission RED, no actual false proof)
and now refuses under the independent checker.

This is an explicitly attributed source-to-view relation, not a proof of every
original allocating C-model body. Records pin the pipeline checker and allocator,
retain standard-library/allocation-success and fresh-frame premises, and mark every
qualified member `standalone_body_proof: false`; no fabricated once-per-member
proof dependencies are added. No immutable method file changed; these are
`contract_fixture` records. Ticket25 stays **claimed**: general member-body proofs,
wider protocols/types and matched bounded/native acceptance under the eventual
combined method remain required.


### Focused Linux owner acceptance — 2026-10-15 12:14 ET

At frozen `d3a5dd48`, current-owner data safe proves 105 ordinary/11 smoke goals.
The stale alias remains not_proven with 111 ordinary Valid, one alias_live_after
timeout and 11 smoke goals passed. Both actual records correctly report attempted
WP invocation. This repairs the earlier prelaunch parser failure without upgrading
its historical5c record or closing wider vector/pair acceptance. Ticket stays claimed.
[Audited source, records and reports](../evidence/focused-parser-owner-final-20261015.json).


### Current bounded maximum admission diagnostic — 2026-10-15 12:37 ET

The smallest original bounded maximum test was replayed alone on mbit10 at frozen
`2629bdfd`, with unchanged source/contract and n=3. It failed its expected-proven
assertion: the adapter returned `not_proven / unsupported_construct` **before CBMC
or native differential execution**, because the full original GAPBS TU's genuine
`/usr/include/inttypes.h` was classified as a noncanonical standard header. The
shadow detector's libc++ relative-name inventory includes `inttypes.h`, but the
clean five-header baseline does not include that system C header. No bounded
refutation or theorem failure is inferred from this admission refusal.

One test failed in131.71s; guarded wall132.17s, peak439,922,688bytes under8GiB, no
OOM/timeout. Socket0generation562 released at12:37:01ET; socket1 was left free.
One record, two artifact references including adapter log,715 absolute physical-file
pins and200 runtime/test/fixture/reader/schema pins match; the certificate self-hash
and unchanged clean source check pass. Raw4.54MB-scale output remains remote for
the coordinator/acceptance/audit readers. No broader batch ran and no contract,
typed-origin, initializedness or smoke policy was relaxed.
[Compact failure audit](../evidence/t25-bounded-max-current-20261015.json).
Ticket remains claimed; a canonical C-header context repair must precede another
current bounded acceptance attempt. Historical5488 bounded and0cc WP evidence keep
their original source/method boundaries.


### Canonical header repairs and same-case replay — 2026-10-15 12:52 ET

The public compiler control reproduced the inttypes false refusal, then passed
after the clean canonical probe included `<cinttypes>`; original compiler/platform
physical header hashes remain in both closures. Two malicious project `inttypes.h`/
`cinttypes` include-next allocation-hook shadows refuse before and after. Sixteen
compiler/context controls pass43.62s; no system-header path whitelist was added.

The same original bounded maximum at frozen`feb92b5b` then passed that check but
refused on canonical libc++ iostream's own `_LIBCPP_IOSTREAM` guard. That separate
control failed1test150.34s with no CBMC/differential, peak430,682,112bytes; its
record/two artifacts,1,569declared physical-file pins and201runtime/test pins match.
The macro check now distinguishes the independently resolved physical canonical
root from candidate/project definitions. Clean iostream RED and project guard
negative were captured before the repair;18compiler/context controls pass59.65s
afterward, preserving project guard and allocation-hook refusals. The coordinator
independently reviewed both narrow changes.

Only the same n=3 bounded maximum is replaying at frozen`ce94128b`, node0generation564
(started12:51:01ET; exact lane metadata authoritative). One worker,8GiB/1800s and1GiB
planned output; node1 remains free. No broader batch or theorem success is claimed.
[Repair, intermediate refusal and launch metadata](../evidence/t25-canonical-header-repair-20261015.json).


### Fresh original bounded maximum accepted — 2026-10-15 13:11 ET

The third historical attempt at `ce94128b` passed both earlier repairs but refused
prelaunch on the platform getopt header's own guard. Its one record/two artifacts,
1,569 declared physical-file pins and201 runtime/test pins match; no verifier ran.
The targeted repair now binds actual inclusion spellings and physical targets,
probes safe angle includes with the clean driver without project includes/defines/
include environment, and requires exact physical/hash matches. Clean platform
closures supply **macro-origin trust only**; declaration/body checks remain closed.
No `/usr/include` whitelist is added. Project include-next hooks, same-name guards,
spoofed system-header pragmas, custom symlinks and source/build macros refuse. A
separate RED showed a fileless explicit-D guard had escaped the prior macro screen;
the final check also covers those definitions. The 25 compiler/context controls pass
103.79 s, with four WP stand-ins excluded; coordinator independent review is green.

Only the original n=3 maximum was replayed at frozen`d874c4dc`: **1 passed in 224.48 s**,
guarded wall 224.91 s, peak 512,581,632 bytes under 8 GiB. CBMC proves 310 ordinary properties
and its reachability assertion fails as expected, retaining unwind 4, unwinding
assertions, pointer-overflow checks and allocation-success policy. Native C/C++
outputs agree on 625 recorded grid cases with zero UB; that differential is not a
formal C++ proof. Matched libc++ 22.1.8, standard-model2/library/allocation premises,
passed setup and true invocation metadata remain explicit. Original fixture bytes
match the historical 0cc source; no contract/domain change or finite WP projection
was introduced.

One record/eight artifact references, 1,599 declared absolute physical-file pins,
202 runtime/test/fixture/reader/schema pins and the certificate self-hash match.
Source remains clean/unchanged; node 0 generation 565 released 13:08:59 ET. Raw 11.8 MB
remains remote for named readers. The earlier three refusals retain their own
records/pins. No stale/at batch, allocating member-body proof, general origin or
whole-ticket completion is claimed.
[Actual audit](../evidence/t25-bounded-max-accepted-20261015.json),
[repair controls and historical refusals](../evidence/t25-canonical-header-repair-20261015.json).


### Original stale-data replay input recovery — 2026-10-15 13:45 ET

The first original stale-data control at `e28eb7f0` retains its **1 failed in
194.09 s** outcome. Its actual proof record already refuted the deallocated-object
read with passed setup and a matching source-C++ heap-use-after-free sanitizer
fault, but the test failed because replay inputs were absent. The native harness
printed inputs and flushed only after the target returned; sanitizer termination
therefore discarded captured stdout before `_replay` could parse it. This was an
input-metadata failure, not a counterexample integer-decoding defect.

The narrow `bc457086` repair flushes stdout after printing all normalized replay
inputs and before entering the target. An independently reviewed native regression
failed before and passed after the change (0.56 s each). Contracts, bounds, oracle
casts, fixture source and CBMC translation semantics were unchanged.

Only the original stale-data case was replayed at frozen `bc457086`, node 0
generation 567: **1 passed in 226.98 s**, guarded wall 227.39 s, peak 508,973,056
bytes with no watchdog/OOM failure. Its record is `refuted`, setup passed and the
verifier launched. Recovered inputs are `n=1, a=[-1]`; the original source C++
replays the matching heap-use-after-free fault. The 15-case native differential
includes five UB cases, which remain excluded from ordinary defined-behavior
agreement. This is one bounded refutation with concrete source replay, not a
universal C++ lifetime theorem.

The coordinator checked nine artifact references, 3,394 absolute physical-file
references across 1,064 unique files, 203 runtime/test/schema source pins and the
certificate self-hash: no mismatches. The source remained clean and unchanged;
node 0 released at 13:36:03 ET. Raw output (12,312,876 bytes) remains remote for the
named acceptance/audit readers. No iterator/at batch ran. The earlier failed test
is retained, and ticket 25 remains claimed for the broader member/lifetime/origin
acceptance frontier.
[Final compact audit](../evidence/t25-stale-data-replay-flush-20261015.json).


### Original iterator and at controls accepted — 2026-10-15 13:57 ET

The two original bounded controls completed at clean frozen `94769312` with no
watchdog/OOM failure. Node 0 generation 568 passed the stale-iterator test in
222.45 s (guarded wall 222.89 s; peak 511,770,624 bytes). Its record is `refuted`,
setup passed, with 194 ordinary successes, one deallocated-object failure and
15 unknown properties retained. Inputs `n=1,a=[-1]` replay the matching original
source-C++ heap-use-after-free fault. The 15-case finite C/C++ differential agrees
on defined behavior; five UB cases remain explicitly excluded.

Node 1 generation 600 passed the original combined at()/guarded-at test in
302.84 s (guarded wall 303.26 s; peak 595,640,320 bytes). The unchecked subject is
`refuted`: 112 ordinary properties pass and its out-of-range check fails. Inputs
`n=0,k=0` replay the same `std.vector.at.out_of_range` source-C++ check. The guarded
subject is `proven` with all 119 ordinary properties passing. Each subject's
28-case finite C/C++ differential agrees with zero UB. All three records retain
one intentional failing end-reachability assertion, separately from ordinary
properties. Unwinding assertions, pointer-overflow checks and allocation-success
policy remain explicit (unwind 2 for iterator, 3 for at controls).

The read-only remote audit matched three records, 26 report/log references,
9,462 declared absolute physical-file references across 838 unique paths,
203 runtime/test/schema source pins per lane and all three provenance certificate
self-hashes. Repeated declared references are counted; the exact audit scope is
in the compact metadata. No mismatch occurred. Raw output remains remote
(12,280,012 / 18,857,471 bytes) for the coordinator, ticket acceptance and independent
audit readers. Source-after checks are clean and unchanged. Live readback at
13:56 ET found socket generations 568/600 and legacy 77 released, no owned
evaluation process, load 0.40/0.85/0.76 and 21/95 GiB free on `/data1`/`/data`.

These are bounded records with finite source replay/agreement, not universal
C++ equivalence, allocating member-body proofs or complete ticket acceptance.
Ticket 25 remains claimed; further evaluation is deferred for this closeout.
[Final compact audit](../evidence/t25-next-controls-accepted-20261015.json),
[prospective launch](../evidence/t25-next-controls-launch-20261015.json).


### User-paused checkpoint — 2026-10-15 ET

Implementation, evaluation and provider work are paused by user direction. The
claim is released for a later session; acceptance is not complete. Closeout
review, documentation, merge and cleanup continue separately.

Bounded maximum, stale-data/iterator replay and unchecked/guarded at controls
are retained with their exact-source pins. General allocating member-body proofs,
receiver-domain admission and complete WP/bounded agreement remain incomplete;
the receiver-domain design is prospective. Ticket 24 still blocks this ticket.
See [accepted controls](../evidence/t25-next-controls-accepted-20261015.json) and
[deferred design](../evidence/t25-vector-receiver-domain-deferred-20261015.json).


### Scoped pair member-body and caller acceptance — 2026-10-16 ET

The six-record pair-only actual profile passed at frozen `1278f2d9` on mbit10
socket 0 generation 586. The original int/int default/value/copy/assignment C
bodies prove **31 ordinary goals and four smoke goals**. The safe copied-value,
field-access and assignment caller proves **24 ordinary goals and nine smoke
goals**, with exact dependencies on those four proven model records. The
wrong-field caller keeps the same postcondition and retains one ordinary ensures
timeout, **23 other ordinary Valid goals and nine passing smoke goals**. It is
`not_proven`, not a refutation. Original model text/contracts are unchanged.

The read-only cold audit matches all six strict fresh-report verdicts, goal lists,
Linux project-context runtime identities, fixture-method pins and model dependency
IDs. It checks 2,023 declared physical-file references across 1,005 unique hashed
files, 198 source modules and eleven profile source pins with no errors. The Mac
composite is not used as a Linux expectation. RTE, initializedness and smoke
remain enabled; all six records retain `contract_fixture` evidence.

The whole guard exits 0 in 282.61 seconds, peak 733,483,008 bytes; the outer guard
exits 0 in 284.70 seconds, peak 784,863,232 bytes. Neither reports OOM or timeout.
Source remains clean and unchanged; the lane naturally releases at 00:22:33 ET.
Three finite poststop command-line/cwd metadata scans find no matching run/source
process and explicitly retain cwd access denials for `(sd-pam)` and `sshd`.
No environment/token scan, universal process-absence or cleanup claim is made.

[Scoped actual audit](../evidence/probata-t25-pair-actual-audit-20261016.md),
[exact record/dependency summary](../evidence/probata-t25-pair-actual-summary-20261016.json),
[compact complete cold metadata](../evidence/probata-t25-pair-cold-audit-v3-1278f2d9-20261016.json).
Raw reports remain remote for the coordinator, ticket acceptance and independent
review. Ticket 25 stays **claimed**: wider standard-model/member types, heap and
lifetime integration, and eventual combined-method acceptance remain open.


### Fresh original count constructor accepted — 2026-10-16 01:17 ET

One fresh public `std_vector_int_ctor_count` fixture record is accepted at exact
`bb7170ac09081cd02562b747d7cccb17ba8c6ced` under the declared source-translation,
allocator, tool and standard-support TCB. Record SHA256
`b8e999897786e46ce516ddbad952ae4ab130fa42b81569cbc71263732e3be687`
is schema-valid and proven: all 27 fresh targets, 36 ordinary Valid goals and
one passing numeric smoke, with complete current setup/normal-reader bindings.
Original body/contract, caller domain and model version remain unchanged.

Independent cold review passes all 1,031 checks and 342 physical reference
instances with zero mismatch. All 84 parsed task streams match the previously
audited universal-value tasks: 58 identical and 26 differ only by capture-free
specialization of the quantified value to zero. No other logical command,
heap definition or support assertion differs. Linux project runtime, method,
source, foundation/import bindings and the closed numeric dependency DAG match.
No cached or synthetic result is promoted, and no original caller premise or
finite heap identity bound is added.

All 614 raw files (23,021,394 bytes) remain remote. Whole/outer guards exit 0 in
371.990/374.078 seconds, peak 1,067,044,864/1,118,425,088 bytes, with one 8 GiB
worker and no OOM/watchdog timeout. Exact source stays clean. Node 0 generation
587 naturally releases at 2026-10-16T05:10:04Z = 01:10:04 ET; node 1 and legacy
leases are released at the final finite observation. Process cwd permission and
vanished-read limits remain explicit; no universal absence or new GPU state is
claimed. The actual monitored raw budget remains 8 GiB, with its earlier 1 GiB
proposal preserved in the separate clarification.

This accepts only the original count-constructor public-body limb under its TCB.
No production-store adoption, generic caller/growth proof, formal C++ equivalence
or ticket closure follows. Ticket25 remains **claimed**, all acceptance boxes
remain open, and the owner's separate ownership/domain work is excluded.
[Independent review](../evidence/t25-count-ctor-cold-review-bb7170ac-20261016.md),
[exact review metadata](../evidence/t25-count-ctor-cold-review-bb7170ac-20261016.json),
[compact final snapshot](../evidence/t25-count-ctor-cold-snapshot-final-bb7170ac-20261016.json).

### Qualified reallocation source/caller preparation — 2026-10-16 ET

The explicit v3 preparation now binds every emitted executable helper and
inverse-restores the complete original v2 source after the disclosed domain/name
edits. Public lowering separately records exact physical source/C/header pins
and pending constructor, data, reserve, index/read and destructor obligations
for the three original qualified-vertical caller fixtures. It grants no origins,
adds no caller premise and never selects v3 models or launches a verifier.
Eleven serial compiler/native controls pass; the real source-byte, signed-count
and missing-call REDs remain retained. The independent f32 preparation review
passed 78 physical references; its scope remains unsupported preparation.
Evidence: `../evidence/t25-reallocation-caller-source-preparation-20261016.json`.

The independent `../evidence/t25-v3-vertical-domain-review-20261016.md` inventories
all new copy/frame/qualification/caller/lifetime duties. Typed source-int loads
and automatic receiver lifetime mapping remain necessary before fresh public
proof. No original growth contract, qualified body, caller domain, exclusive
ownership or wider type/member acceptance is claimed. Ticket25 remains claimed.

### Qualified typed-source and lifetime draft — 2026-10-16 ET

Public preparation now emits 30 constructor, 20 grow, 26 reserve/helper and 11
destructor pending targets, plus ten source-local caller lifetime/data/guard
duties. Copying uses arbitrary entry-snapshot integer values; concrete feasibility
controls remain separate from quantified incoming-heap obligations. The route
still returns unsupported before any verifier. Nineteen compiler/native controls
pass (51.65 s); 34 defined caller inputs agree between original C++ and lowered C.
No stale or effective-type-undefined source was executed.

Independent review identified that initialized bytes/old representation do not
entail integer cells or effective-type safety. The explicitly qualified v3 domain
now requires a source image from the selected WP Typed/Machine integer chunk,
with caller discharge from admitted typed constructions/stores. Its runtime
binding is pending. The destructor's broad element-free domain is preserved.
No global pointer-map premise, exclusive owner token, desired-result axiom,
original raw-growth proof or complete caller acceptance is claimed. Source,
clause/frame/cleanup/dependency closure and fresh normal-reader proof remain open.
The coordinator owns the prospective minimal theory type gate and all actual
jobs. Evidence: `../evidence/t25-reallocation-pending-heap-map-controls-v2-20261016.json`.


## Qualified-v3 pending-source integration — 2026-10-16 02:45 ET

Exact304e03ac097352e78c3d3a637e13e951bef51dd0 is published as prospective source for the separately planned exact-Git-blob type-only gate. The original v2 catalog and accepted heap bridge/VC/packet/view remain unchanged. New explicit qualified constructor/grow/reserve/dtor lookup records the candidate model/domain/theory and emits30/20/26/11 pending targets, but always returns not_proven/unsupported_construct before verifier launch. Caller AST receipts retain original v2 calls, no known origins and no added premises; ten source-local placement/history/frame/data/guard duties are pending. [Preparation README](../prototype/25-reallocation-domain/README.md), [integration review](../evidence/t07-t25-preparation-integration-review-20261016.md).

Typed WP integer-source embedding and non-dynamic automatic-object lifetime definitions are drafts, with selected-runtime/source binding and full source/clause/frame/type/import/task/body/caller completeness unproved. Arbitrary entry-snapshot copying is not uniform-fill reuse; constructor capacity/eligibility are qualified postconditions to prove and destructor overlap scope stays broad. The latest preparation packet's407 references rehash without mismatch. Retained19 compiler/native controls and34 defined C/C++ caller comparisons are finite evidence, not a universal or stale-alias/UB proof. No formal/compiler job was run by integration; no type/proof result follows merely from publication. Status remains claimed and no dependency/default/current-catalog record is upgraded. Selector770's separate final cold record audit remains pending.

## Qualified-v3 grammar/type-only cold acceptance — 2026-10-16 03:02 ET

[Independent cold review](../evidence/t25-typecheck-independent-cold-review-304e03ac-20261016.md) accepts only Why3 grammar/types for exact source`304e03ac097352e78c3d3a637e13e951bef51dd0` and Git blob`af3f31aefa824f6f407a5124b9acf5a21e4d0b09`.153 local reference instances/86 unique files and all9 raw files/33,685B match with zero errors. Actual guard exit0/0.377270875s/50.53125MiB,600s whole/8GiB, no recorded timeout/inspection failure/unconfirmed child. Finite post-exit scans/absent leases are historical bounded observations only.

Exactly one known unused-variable dummy warning is present at line25. The immutable [original receipt](../evidence/t25-mac-typecheck-original-receipt-v2-304e03ac-20261016.json) SHA f458c60a83e184ab015b6ac7f4ab81ceac1d12356a5183fa3832129e708c00e8 incorrectly says warnings=[] because its parser missed comma/location-form diagnostics. Independent complete retained-output comparison classifies that warning; the old receipt is not rewritten and no actual rerun occurred. Future parser/canonical rebuild successors remain separate and are not adopted by this closeout.

No solver, imported WP task/hypothesis, source-image,87 model/10 caller duties, model/body/caller composition, public model dependency or whole-ticket acceptance follows. Qualified-v3 public models still return not_proven/unsupported_construct before verifier launch. Existing pair/heap/count accepted records retain their own identities. Ticket25 stays claimed; no frontier resolves.

<!-- 2026-10-16 ET scoped preparation addendum; no acceptance checkbox change. -->

The qualified v3 reallocation preparation now reconstructs the exact source,
event/clause/helper map, packets and import directory independently of staged
hash claims. Eight tamper controls and the composed 28-control compiler/native
profile pass; the public route remains unsupported before launch. The root's
exact-304e03ac Why3 type-only run exited zero with one known unused-parameter
warning, classified in a separate passive addendum after the original regex
missed its format. This is grammar/type evidence only. Full WP import/task,
selected typed-source image, model bodies, caller cleanup/dependencies and wider
member/type coverage remain open. See
[canonical reconstruction](../evidence/t25-reallocation-canonical-rebuild-controls-20261016.json)
and [passive warning addendum](../evidence/t25-mac-typecheck-passive-warning-audit-v1-304e03ac-20261016.json).

2026-10-16 03:10 ET canonical preparation publication: exactd22bc6c5 (packetd1d3b3e0) passes the [independent canonical review](../evidence/t25-canonical-rebuild-independent-review-d22bc6c5-20261016.md). Complete canonical reconstruction rejects staged-source/statement/theory hash forgery, dropped coverage rows, extra import files and symlinks; it retains the trusted finite source-owner map boundary. The changed compound model identity does not promote old records. Public routes remain unsupported/no-launch, all source-image/import/task/body/caller duties open. Backend01771 remains separate/unreviewed and excluded. The earlier03:02 note's future canonical source is now published only as preparation; its old actual304 warning-parser defect/result remain immutable. Ticket25 stays claimed.

## Qualified standalone backend preparation published — 2026-10-16 03:32 ET

Exact01771a839893975bba389ee0adcbec2aecdb88ac is published through43d652b5 after [independent static PASS](../evidence/t25-qualified-backend-independent-review-01771a83-20261016.md). The distinct qualified model route now reaches the existing serial ordinary engine after canonical packet/subject hash/import membership and selected WP Typed/Machine source checks before every launch. Earlier304/d22 no-launch records remain historical. Qualified positive records cannot serve as original-v2 body contracts or C++ caller proofs; generic caller/lifetime/type/eligibility discharge stays unsupported/pending. Destructor broad pointer/free domain adds no element image restriction. Root40-pass profile is compiler/native metadata plus named Python Frama stand-ins; one synthetic20-target success remains synthetic.18 retained records/schema and941 report-reference pins match, not actual model proof evidence. [Root admission](../evidence/root-t25-017-native-control-admission-20261016.json) and [outer receipt](../evidence/root-t25-017-native-control-outer-20261016.json) retain explicit scope and prior direct-query refusal history. Source successor248 is excluded pending review. All actual import/task/body/caller/cleanup/dependency/fullticket gates remain open; status claimed.

### 2026-10-16 ET — C++17 capacity and caller correspondence preparation

The public lowerer now binds the prospective caller's exact-capacity witness to
the actual admitted libc++22.1.8 constructor/allocation headers under C++17. It
refuses changed language, macro, omitted-header, hash and physical-header inputs.
This is implementation-specific correspondence, with no new caller premise and
no assumption of the qualified C model's pending `capacity == count` postcondition.
The composed Clang/native caller and pure canonical-packet profile passed 21/21
in 59.96s (guard 60.72s, 371 MB, no OOM/timeout). Public capacity RED and all controls
are retained in `evidence/t25-caller-capacity-controls-20261016.json`.

Frozen017's separate backend static review is retained in
`evidence/t25-qualified-backend-independent-review-01771a83-20261016.{md,json}`.
It reports 7 source pins, 18 schema-valid scripted records and 941 report references
with zero mismatches. Root-owned selected compiler/setup controls passed 40/40;
all Frama processes in that profile were named stand-ins. No actual qualified
model/caller proof or ticket acceptance checkbox is claimed by this preparation.

## Reviewed caller source preparation — 2026-10-16 03:51 ET

Exact42844b9aafe2a8af860e09bf5a6fbbec25a42c74 including248 lifetime is integrated after [independent source PASS](../evidence/t25-caller-source-independent-review-42844b9a-20261016.md):10 immutable source-pin instances/23 anchor instances/31 run/header references match. Complete lowered scalar capture, one normal-return cleanup, unreachable fallback and lexical lifetime-end duties are bound without origins/premises/adopted dependencies. Capacity==count is only an admitted libc++22.1.8 C++17 source witness; its model post and caller branches still require proof. Original v2 caller model selection and unsupported generic composition remain. The older03:32 held248 note is superseded only for source preparation, never actual caller proof.

Root reports exact017 representative WP/Why3 import/task generation ended03:45:36 ET with actual tool generation but entry exit1 because of a legitimate empty-ID imported module property and multiline check-lemma description. Task log20,647B,1goal/2properties/results[], sentinel absent; guard7.153422s/207.421875MiB/no events. Pure reader repair and complete task cold audit are pending; no actual rerun, original-exit rewrite, body/caller proof or whole-ticket acceptance. The frozen017 control checkout/artifacts remain untouched by integration.

## Representative017 WP/Why3 generation cold closeout — 2026-10-16 04:06 ET

[Independent cold PASS](../evidence/t25-qualified-generation-independent-cold-review-01771a83-20261016.md) accepts one exact import/task-generation feasibility observation at01771a839893975bba389ee0adcbec2aecdb88ac, selected grow.entry.int_projection packetb5dbe9939b460efa5503b1cbba8a891f5cdb940a8d44835f3fd04da307a74b3f. Frama child returned0 and printed the complete20,647B task log; original entryv3/guard exit1 and generation_completed=false remain immutable. The refusal was the legitimate empty-ID imported IPModule property and newline-formatted check-lemma description. Separate reader-v4 accepts exactly that source-bound module row and check lemma, retaining both. Retained schema controls reproduce RED1+12 negative refusals then13GREEN; no actual v4 rerun occurred. [Parent passive review](../evidence/t25-qualified-generation-passive-review-v1-01771a83-20261016.md).

Actual inventory has one ordinary goal passed=false/results[], two properties and no smoke, native verdict none/all prover successes0, header-only CSV and three identical normalized snapshots. Exactly two unused-dummy warnings at the selected Heap theory line25/characters18–23 remain classified without a general warning waiver. Actual -wp-gen/config/no-autodetection/sentinel and primary Generate control flow bind task construction before prover execution; sentinel absence alone is not universal process evidence. Guard7.153422s/207.421875MiB had no timeout/inspection/child failure. Root settlement has three historical finite empty sweeps and leases absent. Entryv3's final runtime/config postchecks were not reached after the refusal; later passive rehashes are later snapshots, not evidence those checks ran or an atomic immutability claim.

The passive audit reports723 checks; independent review rehashed1376 unique local files (1371 input pins+5 derived outputs), zero mismatch. The complete printed theory contains three source predicate definitions and one unproved wp_goal, retaining bounded values/representation/size-zero-or-distinct allocation premises and project_int_region conclusion. Project Heap adds zero axioms/lemmas. Complete imports/clones retain30 modules/56 source proposition declarations, explicitly not a flattened instantiated Task axiom count or an independent foundational proof. Arithmetic/map/Qed/BuiltIn remain declared trusted foundations. Driver-prepared/solver-submitted task bytes do not exist in this path. No ordinary Valid, smoke/nonvacuity, model-body, original-v2, generic source/C++ caller/lifetime/cleanup or full-ticket proof follows. A fresh normal public20-target qualified-grow profile remains inert and unadmitted. Ticket stays claimed. [Census](../evidence/t25-qualified-generation-passive-v3-generation-census.json), [full import source closure](../evidence/t25-qualified-generation-passive-v3-import-source-closure.json), [preservation manifest](../evidence/t07-t25-generation-cold-preservation-20261016.json).

The exact retained printed task SHA c4a1d9071061d193256423265ebecfab58caceb26cf3d9cc803c377fd5776cb3 has13 whitespace-only lines. They are preserved as actual evidence; this publication does not claim blanket diffcheck cleanliness. All other staged paths pass. Historical07 artifacts retain their separately documented47 warnings, and the prior size reader its2 warnings, unchanged.

### Caller count conversion and request target — 2026-10-16 ET

The public lowering now retains the physical signed-count parameter span and
maps its constructor conversion and reserve request to an explicit numeric C
kernel. Growth preserves `(size_t)n + 1`; no-growth preserves `(size_t)n`.
Selected signed-int and size representations, exact conversion, capacity bound
and request arithmetic are separate pending obligations. The source input's
`0 <= n` remains a pending discharge from a caller contract. It is not inferred
from typing or samples, inserted into the executable source, or accepted as an
unproved global premise.

One real public-lowering RED failed on the missing target, then the same control
passed after implementation. Seven scoped compiler/native controls pass in
31.45s (guard 31.8043s, 366,837,760-byte peak, no OOM/timeout). Nine defined numeric
observations cover 0, 7 and INT_MAX for both growth functions and the no-growth
function under UBSan; no stale-pointer branch executes. These are preparation
controls, not formal arithmetic, model or caller proofs. Exact sources, raw
commands/logs/resources and native artifacts are pinned in
`evidence/t25-caller-numeric-controls-20261016.json`.

Frozen 017 standalone source and every existing actual producer remain untouched.
Full caller state/frame/typed-image/cleanup composition, current ordinary model
dependency eligibility and actual ordinary/smoke proof records remain open. All
original acceptance boxes stay open.

### Prospective projection split and caller lexical repair — 2026-10-16 ET

The original 017 full-grow attempt remains partial: two producer-reported
successes, the integer projection target unproved, and 17 targets unexecuted.
The coordinator preserves that run and owns its independent cold audit. A
prospective source successor decomposes only the projection conjunction into
two isolated obligations with the same complete premise, one for represented
heap and one for every bounded projected int cell. Exact existing predicate
spans, fresh-index checks and explicit AND ownership bind the expansion. The
original whole target remains reference-only; no desired theorem is assumed.
All other 19 target C inputs and their indices are byte-identical. The new
inventory is 21 grow and 27 reserve targets; complete fresh proof is required.
No old record is promoted and no model body, contract or heap definition changes.

Caller preparation regenerates 79 pending targets under this successor and
still admits no current model records or actual public contract identity. A
concrete review blocker in the earlier lexical matcher is fixed: whole-clause
patterns preserve keyword/operator boundaries and cannot concatenate annotation
fragments into different tokens. Public RED reproduced the malformed-token
acceptance; the final 42-control compiler/pure batch passes in 40.40s (guard
40.7701s, 308,838,400-byte peak, no OOM/timeout). No formal tool executes in this
profile. Exact sources, old review, reference target and controls are pinned in
`evidence/t25-projection-split-and-lexical-controls-20261016.json`. Independent
source review, affected actual diagnostics, full public model and caller proofs,
and all remaining member/type acceptance remain open.

## Qualified public20 partial checkpoint — 2026-10-16 04:58 ET

[Original G589 pre-public failure](../evidence/t25-qualified-grow-prepublic-failure-v1-20261016.md) preserves workspace/records FileNotFoundError, no public proof command/record, original49raw files and entry/outer1.1553consumer equality was pre-seed only; final public postchecks were not reached. Root's later416module physical/Git checks are later snapshots, not executed original postchecks.

Second node0G590 exact017 attempt reached the normal public CLI and stopped at target3:2producer-reported successes, grow.entry.int_projection timeout,17unexecuted. PublicCLI returned0 and persisted one not_proven/timeout record with3goals; profile/guard exit1 in121.500689s568,692,736B, outer123.580s621,645,824B, no guardOOM/whole timeout. Complete378-file/23,369,201B remote manifest and21embedded selected metadata rows reconcile locally; no remote raw rehash/copy by integration. Source-consumer1553-file pre/post equality,416module physical/Git checks and three finite empty poststop sweeps/leases released are retained root observations. [Immutable partial metadata](../evidence/t25-qualified-grow-partial-actual-metadata-v2-20261016.json). Full task/hypothesis/ordinary/smoke cold audit and diagnosis remain pending. These2success rows do not establish the complete20target/model, original-v2 or caller theorem. Numeric0e78 is pending preparation only. Ticket stays claimed.

## Exact017 partial cold classification — 2026-10-16 ET

The exact017 partial actual now passes independent cold classification: two isolated CVC5Valid check lemmas after Alt-ErgoTimeout; projection Alt-ErgoTimeout/CVC5Unknown/Z3Unknown;17 targets unexecuted and zero C smokes. PublicCLI0/draft not_proven-timeout and guard/profile1 remain unchanged. Root passive5267checks/2919indexed references plus1553opaque source-consumer streams have0errors; the independent integration review reconciles retained local metadata and does not repeat remote raw hashing. All378new/49prior raw files remain remote.208module files mean416physical+Git checks; V1 count defect stayed inert, V2 policy identical.14materialized SMTs are not14submissions. No full20/model/body/original-v2/caller/refutation/ticket25 acceptance. [Final cold audit](../evidence/t25-qualified-grow-partial-final-cold-audit-v2-20261016.md), [independent integration review](../evidence/t25-qualified-grow-partial-independent-integration-review-20261016.md).

Status stays claimed. Prospective projection/lexical c0d has been composed with reviewed integration in the author worktree; exact merged controls/public readiness remain pending and no historical result is promoted.

### Current reporter merge and projection preparation — 2026-10-16 ET

The prospective source is merged with the current reporter/property-closure and
smoke-observation policy at exact `2e01d27d`. Forty-two canonical packet and Clang
controls pass in 40.88 seconds; the 8 GiB serial guard reports no timeout or OOM.
Independent merged-source review confirms all 21 targets, the 19 unchanged 017
inputs, exact original projection reference and both source-definition bindings.
Model/theory bytes and the full projection premise stay unchanged. Evidence:
`../evidence/t25-merged-projection-controls-2e01d27d-20261016.json`.

This accepts merged preparation only. The coordinator-owned scripted public
21-target/schema/persistence controls and any fresh actual projection/full-model
run remain pending. No original v2 or generic caller admission follows, and the
old 017 partial producer remains immutable. All acceptance boxes stay open.

### Merged full-21 scripted persistence accepted — 2026-10-16 ET

The coordinator's exact clean `0f10e088` compiler/native profile passed all three
public controls, with production and test bytes identical to runtime candidate
`2e01d27d`. Native OCaml setup was exercised; all Frama/WP commands targeted
named Python stand-ins. The synthetic successful record persists all 21 runs,
30 synthetic ordinary goals and one healthy smoke observation, with the normal
two-key reader attestation and schema. The named parser-error and prelaunch
self-consistent axiom-refusal controls also pass. A passive cold read checks
both schema-valid records, all 240 record/report references and all 21 normal reader
results; source-before/after match across 1,898 exact tracked inputs.

The worker tree completed in 16.03 seconds, with no timeout, OOM, inspection
event or unconfirmed child. Its 180-second inner and 240-second outer worker
guards exclude source preflight/final hashing from that timing claim. Retained
raw is 41.59 MB, within the 256 MiB planning allowance. Evidence:
`../evidence/t25-grow21-scripted-public-controls-20261016.json`.

This completes the current workflow/schema preparation gate only. The independently
reviewed inert full-21 packet still needs coordinator admission, fresh actual
results and complete task/import/hypothesis cold review. No old 017 partial
record is promoted. Original v2, generic caller composition, remaining members
and element/type breadth remain open; this ticket is still claimed.

## Current source publication boundary — 2026-10-16 ET

Exact evaluated-source2e01 is published through the reviewed25301741 packet; root must evaluate2e01, not the merge or receipt commit. Both projection pieces retain the full original antecedent and mandatory AND ownership; original whole projection is reference-only, other19payloads unchanged.316package Git pins and15physical reviewed source pins match. Root3named scripted public/schema/native-OCaml controls pass in16.034838s/374.53125MiB with noevents/children/OOM/timeout; all403retained control artifact pins match. This completes source/workflow readiness only, no actual proof. Caller79targets/five unadmitted model requirements, public contract identity, full21/model/original-v2/caller/ticket25 acceptance remain open. [Integration review](../evidence/t25-projection-publication-integration-review-20261016.md), [root source/entry review](../evidence/t25-grow21-root-source-change-review-2e01d27d-20261016.md), [scripted controls](../evidence/t25-grow21-scripted-public-controls-20261016.json).

This supersedes dated pending-controls preparation statements only. Status stays claimed; no historical record promotion.

### Exact projected-cell definition decomposition — 2026-10-16 ET

The retained `2e01d27d` actual run reached four leaves: feasibility and receiver
reads were CVC5 Valid; the representation piece was Z3 Valid. The cell piece
remained open (Alt-Ergo Timeout, CVC5 Unknown, Z3 Unknown), leaving 17 targets
and the numeric smoke unexecuted. Source inspection finds no counterstate;
these solver outcomes do not themselves explain the cause or establish a
refutation. The full actual producer and its independent cold review stay separate.

The prospective successor expands the exact unchanged `int32_at` definition
into four independent duties: typed access, initializedness, integer-tag/load
identity and signed32 bounds. Each retains the complete original premise and
fresh-index range. All four are required jointly; none assumes a sibling or
witness theorem. Exact source-definition/substitution bindings and the old
cell target are retained, with the latter reference-only. All other 20 target
C files and indices remain byte-identical to `2e01d27d`; the heap theory and
source contracts do not change.

A public canonical RED records the old 21-versus-24 inventory. The single
GREEN, 26 compiler-free closure controls and 51 affected packet/Clang controls
pass; dropping components, adding sibling dependencies, weakening premises,
capturing the index or altering references/definition bindings fails closed.
Current prospective counts are grow24, reserve30 and caller82 pending targets;
the separately checkpointed caller applications are not included here. Evidence:
`../evidence/t25-cell-conjunction-preparation-controls-20261016.json`.

Independent review and a separately admitted four-leaf diagnostic must precede
any full24 replay. No current proof record, caller dispatcher, model verdict or
ticket acceptance is granted by this preparation. All previous inputs, outcomes
and the old 017/2e01 partial producers remain unchanged.

### 2026-10-16 06:06 ET — fresh grow21 partial cold and dtor settlement

[Final grow21 cold closeout](../evidence/t25-grow21-partial-final-cold-audit-v1-20261016.md) at exact2e01 accepts partial classification only:two CVC5 Valid leaves and Z3 representation Valid; cells retains Alt-Ergo Timeout/CVC5 Unknown/Z3 Unknown,17targets unexecuted,0Csmokes. Root5653checks3272indexed refs plus1582opaque consumers0errors;397current raw and378prior017files retained. The20materialized SMTs do not certify submissions. Full model/caller/original-v2/refutation and the representation/cells AND group remain false. [Integration reconciliation](../evidence/grow21-e4-independent-integration-review-20261016.md) rehashes15local artifact references without remote repetition.

Separate exact2e01/node1G619 dtor11 settled05:48:41 ET:producer11/11nativeValid,0Csmokes,guard95.784901578s971689984B/outer97.817638761s1025167360B,exit0/noOOMtimeout. [Metadata](../evidence/t25-dtor11-actual-metadata-v1-20261016.json) and [admission only](../evidence/reviewed-t25-qualified-dtor11-public-v1-launch-2e01d27d-20261016.json) remain distinct; independent complete cold/model acceptance is pending. All417rawfiles24,183,685B and exact2e01/oldML229 source remain unchanged. No full25 closure.


### Reviewed cell components and scripted public persistence (2026-10-16 ET)

The exact four-way projected-cell definition expansion is independently reviewed
at merged source `046f6b9e64d45777a8032951ced04f942fc9c3c2`. All four duties
retain the full original antecedent and fresh index; the representation duty is
also mandatory. Twenty other current canonical inputs and both reference inputs
remain unchanged. The independent review records no added premise, axiom or
sibling theorem dependency. The merged affected profile passes 51 controls.

Root separately executed all three native OCaml/helper/report and scripted
public workflow controls at this exact source: 24 persisted child runs and
setup checks, 34 synthetic goals (33 ordinary and one smoke), parser-error
handling and prelaunch axiom-tamper refusal. The retained artifacts are stand-ins,
not scientific proof. Passive rereading checks 451 artifact-manifest entries and
268 proof-report references with zero mismatches. The source snapshots are
identical before and after; outer guard 23.89702525 seconds / 432,586,752 bytes
and inner guard 20.279271375 seconds / 334.578125 MiB report no resource events.

The separately versioned four-leaf diagnostic v4 now copies the normal engine's
sole-source-lemma ownership census. A real pure RED on v3 and 12 GREEN controls
cover that repair. Its entry review passes, but root-native lifecycle checks,
actual diagnostic admission and independent task/hypothesis closure remain
pending. The full current 24-target public model remains unproved; the 20
nonselected diagnostic targets remain unexecuted. The prior exact-2e01 partial
(three ordinary producer successes, cell timeout, 17 unexecuted, no C smoke),
original-017 partial, and unmerged caller checkpoint remain separate. No original
v2, generic caller, full member/type coverage or ticket acceptance is claimed.

Evidence: `evidence/t25-cell-components-independent-source-review-046f6b9e-20261016.{md,json}`,
`evidence/t25-cell-components-merged-controls-v1-046f6b9e-20261016.json`,
`evidence/t25-grow24-scripted-public-cold-v1-20261016.json` and
`evidence/t25-cell4-diagnostic-independent-review-v4-046f6b9e-20261016.{md,json}`.

### 2026-10-16 06:25 ET — scoped destructor11 root acceptance

[Separate root decision](../evidence/t25-dtor11-scoped-root-decision-20261016.json) ACCEPTS exact2e01 qualified destructor D1-D7 source-VC evidence:all11nativeValid(10Alt-Ergo,1CVC5) under explicit translation/FramaWP/Why3/solver/standardmap/QedTCB. [Independent cold decision](../evidence/t25-dtor11-independent-cold-decision-20261016.md) preserves root6097physicalchecks3303indexedrefs0errors/1582opaqueconsumers and all417raw24183685B+378priorraw, complete11owner/property graph closures/source queries. Broadreceiver overlap/aliases remain; no bufferintimage/numericC target or genericzero-smoke waiver.24materialized SMTs are not certified submissions. Original coldreader model_acceptance=false/root_acceptance_required=true stays immutable; this separate decision supplies only narrow source-bound eligibility after normal current-code/canonicalchecks, with no original-v2/C++body/caller/full25 promotion.

Reviewed046f cellconjunction preparation and docs d013 are integrated after root3native/public controlsPASS:24runs/setup34syntheticgoals1smoke persisted, no actualformal/modelproof. Allfour full-A cells and unchangedrepr are required;20other2e01Cfiles/theory unchanged. The separate fourleafdiagnostic/native lifecycle/rootadmission and full24proof remain pending. Grow21partial source/checker/3Valid+cellsopen/17unexecuted evidence is unchanged.

[Root real-seed lifecycle receipt](../evidence/t25-cell4-real-seed-lifecycle-compact-v1-20261016.json) also passes at exact046f:real seed creation, reused-workspace refusal and3synthetic ownership attacks, no formal tools. Guard1.131735s75.046875MiB/outer1.199102s119111680B; source pre/postequal. Earlier dispatchV1 stopped pre-worker on046f→docs-onlyd013; V2 explicitly binds AUTHORd013/CANDIDATE046f. Fullfourleafdiagnostic/currentmodel/caller acceptance remains false. Compact receipt plus12local references rehashed before preservation, no new execution.

[Root cell4 bootstrap V5 independent review](../evidence/t25-cell4-root-bootstrap-independent-review-v5-20261016.md) passes passive delta checks:unchanged embeddedv4entry/expected,324source/helperGitpins/sixconsumerIDs, three earlyClang/ambient functions AST-identical reviewedstreamV6. It is admission preparation only, not fourleaf execution/proof/full24acceptance; root alone performs fresh resource/lane/storage admission.

### 2026-10-16 06:40 ET — recovery and new cell4 admission

[Obsolete2e01 retention](../evidence/2e01-source-retention-compact-receipt-20261016.md) preserves exact source/ref/restore/fullremote manifests before non-force removal of clean checkout:10,130sourcefiles reconstructable,2rawroots/1,001entries unchanged,1,635,606,528B reclaimed. Literal symlinks retained; removed-source referents may require reconstruction. Primarybefore/afteridentical; finite trustedOS exclusions/process scans are not universalidleproof. Historical destructor scopedacceptance and grow21partial stayunchanged; no reviewerremotehash/removal.

Root launched exact046f/node0G593 cell4 diagnostic06:35:50ET; [admission only](../evidence/reviewed-t25-cell4-diagnostic-v1-launch-046f6b9e-20261016.json) reports214physical/Git modulechecks0errors/cleandetachedsource,1200whole1320outer/8GiB1worker. Root reports G593 settled06:36:03ET before solver execution:AttributeError WPAdapter(actualclassWpAdapter), diagnostic_completefalse/runs[]/all4unexecuted, no reportcompile/formalleaf. Guard1/10.152794290s289931264B/outer1/12.550548360s342884352B,noOOMtimeout. [Passive failure capture](../evidence/t25-cell4-first-failure-preservation-20261016.md) retains279rawfiles2,342,157B,complete24canonical/compiler/method and10metadata-manifestbindings0mismatch. Root3/real-seed controls did notexerciseadapterconstruction; narrow externalV5casefix plus actual native setup/checklaunchall4 gate required before anynewattempt. No full24/callerproof; integrationtip is not the evaluatedproducer.


### 2026-10-16 07:19 ET — real setup, isolated four-cell producer checkpoint, full24 preparation

[Bounded checkpoint](../evidence/t25-cell4-g594-g595-checkpoint-20261016.md) preserves actualG594 all4 real native prelaunch setup checks, no solvers/24formal targets unexecuted. [SeparateG595](../evidence/t25-cell4-g595-producer-checkpoint-20261016.json) is root-reported4/4diagnosticproven at exact046f;214module admission checks0errors. Native/task/hypothesis/solver cold classification remains pending; walltime alone does not attribute a timeout or winner. Other20model duties are unexecuted, no publicmodelrecord/full24/caller/originalv2/ticket acceptance. OriginalG593 API-casefailure is retained unchanged.

[Full24 normalpublic inner review](../evidence/t25-grow24-independent-entry-review-v1-046f6b9e-20261016.md) and [hardenedrootbootstrapPASS](../evidence/t25-grow24-root-bootstrap-independent-review-v2-20261016.md) bind source046f,324Gitpins/sixconsumer trees/currentG594 projectcomposite, all24fresh targets and actual derived goal census, not synthetic34. Root alone may freshly admit1800whole1920outer/8GiB1worker; no earlier4leafproof is imported and no full24actual is claimed here. Complete native/RTE/init/smoke/task/import/hypothesis/source/resource cold review remains mandatory even after future producer success.

[ObsoleteMaccontrols017 retention](../evidence/mac-controls017-retention-preservation-20261016.md) removes only the clean completed root-owned detached source after fsyncedfull9858filemanifest/ref/restore; raw/active/primary unchanged. Source now reconstructable, not physically present. No scientificresult/ticketstatus changes.

Root subsequently dispatched [full24 normalpublicG596 admission](../evidence/reviewed-t25-qualified-grow24-public-v1-launch-046f6b9e-20261016.json) at07:19:10ET/node0, exact046,1800whole1920outer/8GiB1worker,214physical/Git modules0errors. Running at root handoff with no result/acceptance yet. No4leafrecord is imported; all24fresh obligations remain mandatory.


### 2026-10-16 07:36 ET — full24 G596 partial producer checkpoint

Root reports fresh normalpublicG596 at exact046 settled with10targetsproven then grow.copy.establishTimeout;13targets remainunexecuted, including numericC. Guardexit1/266.526063s867,831,808B,outerexit1/268.625474s921,309,184B,sourceclean/naturalrelease. This is a partial producer handoff, not independently accepted task/hypothesis/native evidence; owner passiveauditpending. [Original admission](../evidence/reviewed-t25-qualified-grow24-public-v1-launch-046f6b9e-20261016.json) stays unchanged. No full24model/caller/originalv2/full25 acceptance or earlier4leafreuse.


## 2026-10-16 08:05 ET scoped cold checkpoint

Root accepts only [four math diagnostics](../evidence/t25-cell4-scoped-root-decision-v1-20261016.md), with [independent support/goal reconciliation](../evidence/t25-cell4-merger-independent-cold-review-v1-20261016.md). ZeroCsmokes/publicrecordfalse/legacychecker0 versus fresh8c42 remain explicit. Separate full24G596 remains10producer-proven/copy.establishTimeout/13unexecuted including numeric; ctor30G621reports29producer-proven/one positive-posttimeout/0unexecuted, final cold pending. No fullmodel/caller/originalv2/body/ticket acceptance. [Combined evidence](../evidence/probata-frontier-cold-checkpoint-20261016-0805.md).


### 2026-10-16 ET — prospective copy-establishment AND15 preparation

The original046 full public grow run remains not_proven after ten successful targets, open `grow.copy.establish`, and thirteen unexecuted targets. Its actual query is bound to the unchanged source formula. A source-definition transformation now expands the conclusion into fifteen independent full-premise obligations, with exact conjunction reconstruction and capture-free simultaneous substitution. The original whole target is retained as an unexecuted reference; no sibling theorem, extra premise, C body/contract or heap-theory change is introduced. The other23 grow inputs are byte-identical.

Seven new compiler-free tests plus26 affected packet cases pass. Prospective inventories are grow38/reserve44/constructor30/destructor11 and96 pending caller duties. Public/native/schema controls and independent equivalence review remain pending; there is no successor actual proof or new model/caller acceptance. See `../prototype/25-copy-establish-and15-20261016.md` and `../evidence/t25-copy-establish-and15-preparation-20261016.json`. Ticket25 remains claimed with all final acceptance criteria open.

Independent AND15 source equivalence review passes at a20; merged4bab retains its exact source. Root-owned three scripted public/native workflow controls pass:38 run/setup entries,48 synthetic goals/one smoke, parser-error and tamper refusal, and unchanged source before/after. These controls run no actual Frama/Why3/solver and establish no successor model/caller proof. See `../evidence/t25-and15-scripted-public-controls-4babafd2-20261016.json` and `../evidence/t25-copy-establish-and15-independent-source-review-a20f7a98-20261016.md`.

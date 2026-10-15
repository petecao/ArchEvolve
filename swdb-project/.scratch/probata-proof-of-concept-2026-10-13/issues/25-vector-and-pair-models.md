# 25 — std::vector and std::pair models

Created: 2026-10-13 22:17 ET
Updated: 2026-10-15 ET (original vector/pair maximum workflow WP view accepted; member/bounded frontier remains open); 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
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

# 36 — Proof setup check and verdict reading

Created: 2026-10-13 22:17 ET
Updated: 2026-10-15 ET (source-bound summary and remote replay checkpoint)
**Type:** slice
**Status:** claimed
**Blocked by:** 11, 21, 27
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Three checks; "Verifier lineup and order": one summary source, failure classes; "What a proven verdict asserts": harness `assume`s; "Records and levels": method-version file; "Testing Decisions", seam 1; user stories 15, 21, 30, 31, 33; S1, S3, S7); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 7, 10), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) (item 4), [09](../../formal-verification-2026-10-09/issues/09-what-proven-asserts.md) (item 10), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) (items 3, 10)
**Time estimate:** about 3 days

**What to build:** Two frozen, versioned checks inside `swdb prove`, so a proof cannot pass by
changing its own setup or by a misread report. Before every verifier run, the **proof setup check**
confirms the inputs and settings are the frozen ones: only summary-generated `assume`s; the
generator-made hazard probes present; every clause has a proof placement; the hashes of contract,
summaries, lowering and run plan; the frozen WP flags; and a run that matches the method-version
file. A pass goes into the proof record; a fail stops the batch. After the run, **verdict
reading** uses WP's per-property report from that fresh run: every goal, lemma, call-site
precondition and termination goal must be Valid, every smoke test must pass, and no `Extern` may
appear outside the contracts of summaries and `maa_*` calls (both readings are design S7). It
never trusts the consolidated `[ Valid ]` or a cache. Smoke tests void a vacuous proof. Each check
is tested with its negative controls.

## Acceptance

- [ ] **Always first.** `swdb prove` runs the proof setup check before every verifier run it makes,
      bounded runs included (scripted-adapter control: a non-summary `assume` on a SAW job is
      refused). On a pass, the proof record carries the result and the check's version. On a fail,
      no verifier runs and `swdb prove` stops the batch, naming the failing rule (assumption below).
- [ ] **`assume`s.** Only `assume`s a summary generates pass (map 11 item 4). Controls: the 08
      prototype's harness `assume` (`parent[v] >= -1`, which real callers violate); a hand-added
      `assume` in the C lowering. Both refused.
- [ ] **Hazard probes and placements.** Controls: a fixture unit with one generated hazard probe
      deleted; a probe supplied as a hint instead of by the generator; a clause with no proof
      placement. Each refused.
- [ ] **Hashes.** The check records the hashes of contract, summaries, lowering and run plan, and
      each must match the hash pinned for the job. Changing any one after the job is planned →
      refused.
- [ ] **Frozen flags.** Each control refused: `-wp-cache update` and `-wp-cache offline` (only
      `-wp-cache none` passes); an existing WP session in the working folder (not a fresh session); a
      Frama-C warning key moved off its default (for example `ghost:bad-use`, or `annot-error` below
      abort, which drops ill-formed annotations, research 13 Q7); a machdep other than
      x86_64; any WP environment variable set (`FRAMAC_WP_CACHE`, `FRAMAC_WP_CACHEDIR`,
      `FRAMAC_WP_SCRIPT`).
- [ ] **Method-version match.** A tool, solver or flag that differs from the method-version file
      is refused. On a pass, the record names the method version's ID and hash.
- [ ] **Per-property reading.** No fact-file control reads as proven, though WP prints its target
      `[ Valid ]`. A goal resting on an unproven lemma, on a failed call-site precondition, or on a
      callee whose termination fails reads "not proven" with the failing goal's class. A goal resting
      on an `admit` or an `axiom` (an unexpected `Extern`) stops the batch. `Extern` on a summary's
      or a `maa_*` call's contract is accepted, each one an assumption entry (S7). The consolidated
      status is never read.
- [ ] **Doctored cache.** The tampered cache entry from map ticket 13's facts (a false goal edited to
      `valid`) cannot make a goal Valid: the verdict comes only from the loop's own fresh run.
- [ ] **Smoke tests.** Every smoke test must pass (S7: a smoke goal WP proves Valid signals dead
      code). A failed smoke test voids the proof with failure class "vacuous pass". Controls:
      contradictory preconditions; contradictory loop invariants.
- [ ] **Failure classes.** A "not proven" reading carries the class the WP adapter (21) gave each
      unproven goal, or "vacuous pass" for a failed smoke test. Timeout and unknown are marked for
      the proof-hint loop (37 routes them). Any not-Valid property with no class stops the batch.

## Notes

- **Not in this ticket:** 35 — Hint records, merger and proof hint check (hint-borne escape
  hatches); 37 — The proof-hint loop (when smoke tests run on the final hint set, minimization,
  rounds); 11 — Method-version file and failure classes (the file and the class list this ticket
  reads); 27 — Proof semantics for the BFS read-offload calls (generates the hazard probes this
  check looks for); 21 — C lowering and WP adapter (A2 tracer) (the WP run itself and its per-goal
  failure classes); 10 — Level rule (what a verdict does to the level).
- Controls come from the seven WP fact files of map ticket 13 (report statuses, tactic scripts,
  smoke tests, other constructs, and the flag cases in the others), listed in
  [research 13](../../formal-verification-2026-10-09/research/13-wp-hint-facts.md).
- **`Extern` and smoke goals (design S7).** WP prints the contracts of summaries and `maa_*` calls
  (body-less) as `Extern`, so "no `Extern`" means none outside those contracts, each of which is an
  assumption entry. "Every smoke goal Valid" means every smoke test passed (`passed: true`); a smoke
  goal WP proves Valid signals dead code (research 13, Q6 and Q7). Any other `Extern` has no failure
  class, so it stops the batch (26 item 10).
- **Flag for Yan-Ru:** S7 accepts `Extern` only on those contracts. If a once-proven logic-library
  lemma reaches WP admitted, it falls outside S7 and stops the batch. Raise it before working
  around it.
- **Harness `assume`s, stricter rule kept.** Map 09 item 10 also let a harness `assume` stand when it
  is proven at every real call or listed as a reduction. The later map 11 item 4 allows only
  `assume`s a summary generates. This check follows map 11 item 4.
- Assumption (not decided in the map): the reading compares the goals WP generated with the goals
  it reports, so a goal left out as never tried counts as not proven. Research 13 Q5:
  `-wp-prover none` or `script` drops untried goals from the report.
- Assumption (not decided in the map): no single WP output has everything. Research 13 Q4: the JSON
  goal report lacks admit and axiom data; the CSV report leaves out lemmas and axioms. The reading
  combines outputs from the same run; the choice is tested against the report-status, tactic-script
  and smoke-test fact files.
- The mapping from WP's per-goal outcomes to failure classes belongs to 21 — C lowering and WP
  adapter (A2 tracer), as 11 assigns it. This ticket only reads it and adds "vacuous pass".
- Assumption (not decided in the map): a failed proof setup check matches no failure class, so it
  stops the batch until root-caused and writes no proof record, as 11 does for an unlisted class
  (map 26 item 10: a failure outside the list stops the batch).
- Assumption (not decided in the map): on a bounded-verifier run the setup check covers the same
  items except the WP flags; that tool's frozen flags come from the method-version file.

## Implementation checkpoint — 2026-10-15 ET

Implemented the universal setup preflight, per-invocation generated-input check,
and fresh WP property reader in `swdb/proof_setup.py` and `swdb/proof_report.ml`.
The WP, CBMC, crux-llvm and whole-function CBMC adapters call the generated-input
check immediately before their verifier process. A real successful verdict without
that check is refused by `swdb prove`. Schemas and
`docs/reference/format-v0.4-proof-setup.md` describe both attestations; production
execution methods must pin each check's version and content hash. Historical
fixture methods remain fixture evidence.

The reader enumerates generated Wpo obligations, actual individual prover results,
property dependencies and user include closure. Automatically proved obligations
omitted from WP JSON require direct valid results; omitted untried obligations stay
not proven. No consolidated Valid summary establishes proof. Unexpected Externs
stop the batch; exact pinned summary, C-model and DX100 contract Externs become
individual assumption entries. Failed smoke tests invalidate the result while
retaining each original goal and failure class. Lemmas are never filtered out to
make a target pass.

Assumption resolved with the project coordinator: bounded harness restrictions
are reconstructed from pinned bounds and the formal unit's declared preconditions.
They are explicit input-domain restrictions, distinct from summary postconditions.
An undeclared `parent[v] >= -1` restriction is still refused. A unit's own Ignored
preconditions describe its conditional theorem; failed call-site preconditions
remain proof obligations. Neither check discharges lifting obligations at callers.

Validation before the final semantics ghost-state hardening: 48 setup/documentation
controls passed in 149.65 s, including 13 real Frama-C fact controls and the actual
doctor-cache experiment; two additional production version/hash controls passed;
three direct CBMC/baseline/chain controls passed; all 15 existing WP adapter cases
passed (safe and seeded-bug pair, then the other 13). Logs are local under
`/private/tmp/probata-t36-{verified,method-controls,bounded,wp-verified}.jsonl`.
The packaged wheel also contains byte-identical Python/ML check assets.

A subsequent cross-ticket review found that Frama-C permits ghost hints to mutate
the trusted semantics ghost model. The setup guard now restricts semantics-job ghost
hints to fresh scalar witnesses and the checked `dx_store_bound` witness; direct
model writes, pointer/indexed writes, shadowing, calls, mutation expressions and
macro expansion fail closed before hint goal generation and before final WP.
Non-semantics hint behavior is unchanged. The dedicated public CLI adversarial and
accepted-witness controls passed: **12 passed in 95.52 s**, using the final checker
identity below. The macro control first reproduced an accepted hint containing a
model-state mutation; the guarded run refuses it before any WP process. The log is
`/private/tmp/probata-t36-ghost-final.jsonl`. Ticket 27's prover-free hint-generation
fix is integrated; the final WP portfolio remains unchanged.

Both `proof_setup_check` and `verdict_reading` have version `1` and content hash
`7a303ac2a9714010ea42f29964e81b62b7ae6a9bca0fb21318deb76974e6b9cc`.
Integration was merged before handoff; no source changes followed the final guard
validation. The earlier real fact controls exercised the same report reader; the
subsequent checker changes only added the semantics hint guard.

Status remains `claimed`: ticket 27's final real WP semantics acceptance is still a
required dependency. This checkpoint does not assert that all ticket-27 units have
passed, that Rocq composition is proved, or that a production campaign is proven.

### Follow-up ghost expression guard — 2026-10-15 03:14 ET

A public CLI negative control reproduced a shift-assignment bypass:
`dx_store_bound = (dx_count >>= 31)` passed the old expression check and mutated
trusted model state. The expression grammar now explicitly refuses both shift
assignments and trigraph introducers (`??`), including line-spliced shift operators.
Ordinary relational comparisons remain admitted. The right-shift control failed
before the fix; the full final focus suite passed **16 tests in 205.88 s**.
Logs: `/private/tmp/probata-ghost-shift-{red2,green}.{log,jsonl}`.
Both check identities are now version `1`, sha256
`5f5b3e343880fe65990a3aa47b335415cb2fee9cfa6e74fa8ceb7f80f9afe71f`.
The production composition record in ticket 42 pins this exact checker through
immutable `method.probata-draft-2`. Earlier checker identities above are historical.
Ticket 27's remaining acceptance and CPU-memory admission work still block resolution.

### Multiline property report repair — 2026-10-15 ET

Frama-C's unquoted, indented continuation lines in libc complete/disjoint-behavior
properties became synthetic rows with missing function/status under DictReader. A
public scripted-report control reproduced the spurious unclassified outcome. The
reader now reconstructs complete TSV rows and attaches only indented single-cell
continuations to the preceding property; incomplete column rows and unindented
fragments still stop the batch. It retains function, status and dependency scope;
this is not a relaxation of Extern attribution or permission to ignore failed goals.
The control is red before the fix and green after it. A real uninitialized new-array
job now produces its expected not-proven record rather than an unclassified parser
failure. All 121 focused policy/report/formal-frame tests pass in 114.92 s.
Both check identities remain version `1`, content hash `48a828aa532aabaa24caffbbd2289464c28a0f0901e9c47528540bccb1afa092`.
Draft 2's older pinned identity remains immutable; new jobs need a new method file.

### Pointer bounds and complete reader pins — 2026-10-15 ET

CBMC 6.11 raw controls exposed a specific pointer-formation gap: discarded `a + 3`
for `int a[2]` produced zero baseline properties and verification success. Adding
`--pointer-overflow-check` rejects it; one-past formation remains legal. Unrelated
array subtraction already fails the default checks, so this work does not claim a
subtraction gap. The [primary CBMC memory-model documentation](https://diffblue.github.io/cbmc/cprover-manual/md_memory-primitives.html)
describes the object/offset model and the pointer-overflow option. Both public
proof and both whole-function equivalence modes now retain this flag on each side;
model-loop discovery uses the same safety settings. The setup check rejects check
suppression, property filtering and entrypoint overrides, including tool-prefix
arguments. The public discarded-formation control was red before the fix.

The flag alone did not enforce DX100 tile extents: the old two-dimensional C state
let `tile0[3]` cross a two-element row while remaining within its enclosing CBMC
object, and the public proof incorrectly succeeded. Bounded model generation now
emits one static C array object per tile plus an initialized pointer table. WP's
state declaration stays unchanged. Each row's name/extent and generated bytes are
recorded in the admission certificate and regenerated before invocation. The exact
C-model body `88298dbb9176640fd8ec2d0c6e31386dd51849411b08df7cebf7f12eab1d22ce`
was independently reviewed after the native pointer-arithmetic repair, including
negative stream offsets from an interior base and per-row object classification.
The failing row read now has failed pointer obligations; the valid variable-index
loop proves with 21 unit pointer obligations. No heap-success premise was added.

The old check hash also omitted adapter verdict readers and the failure-class
vocabulary. Public copied-runtime controls reproduced stale-pin acceptance after
changing those bytes. The content identity now hashes named, separately framed
dependencies: the setup/ML report reader, adapter/common verdict processing,
domain/formal/hint checks, RSS result accounting and the actual failure vocabulary.
All 15 changed-dependency controls refuse before the marker command executes.
Setup and verdict-reading identities remain version `1`, with content hash
`c8c31e02cfb1126d0730541c3de8d6a03825c10c8ee51db5f03c0453a1cbd968`.

Final focused validation passed **80 tests in 314.19 s**, including all setup
controls, public proof/equivalence controls, valid indexed tile loops, and native
C/C++ sanitizer plus CBMC query controls. A separate documentation/method run
passed 83 tests and found two stale expectations: missing `memory_domain` and
current mandatory flags applied to immutable draft 2. The vocabulary expectation
is fixed (five documentation/vocabulary checks pass); the method assertion must
target the forthcoming draft 3. Draft 2 is unchanged. Evidence, raw commands,
hashes and the preserved negative results are in
`evidence/cbmc-pointers-20261015.json`. Integration's lowerer 7 was merged before
handoff; the combined identity is recorded there. The post-merge public proof,
equivalence, tile, native-query and signed-stream CBMC recheck passed **14 tests
in 230.78 s** (35 unrelated cases deselected). This remains a scoped safety
repair, not general C++ undefined-behavior freedom. Ticket 27 still blocks resolution.

### WP pointer formation and array-origin boundary — 2026-10-15 ET

The same row-extent issue also affected WP's original two-dimensional state. The shared
WP prelude and annotation typecheck input now use independent static tile arrays with a
constant pointer table; every caller/store separation clause quantifies over all rows.
The public negative retains a failed final memory-access goal, while all four legal setup
writes are Valid. The legal in-row positive proves. Static storage and the existing pinned
semantics supply these objects; no allocation-success or hidden input premise was added.

Generic discarded pointer arithmetic was separately red: WP33 RTE could prove an unused
out-of-range `p + 3`. The lowering now inventories formation across the emitted closure;
its WP view adds checked named bounds obligations and preserves C++17 null-plus-zero with
conditional C normalization. Mutation, casts, pointer subtraction, effectful placement and
unmodeled subobjects refuse. Generated C model definitions receive their own Clang inventory.

An additional uncached audit found the precise provenance limit: allocation validity can
prove an imported summary's three-element precondition for a two-element local/global row.
Struct-member variants instead fail. `object_pointer` proves target liveness even across
rows; WP33 reports `pointer_comparable` undefined and cannot prove even a genuine flat
one-past comparison. No unsupported predicate, axiom, smoke waiver or new assumption is used.

The resulting conservative gate requires an origin certificate for arithmetic **and ordinary
indexing**, including retained callees. It admits concrete one-dimensional local/global
primitive arrays, immutable aliases, the existing certified terminal typed allocation, and
exact-content/entry/geometry-pinned DX100 rows. Rebinding, references, address escapes and
unknown calls invalidate aliases. Incoming pointer parameters and opaque generated C-model
parameter operations refuse until an explicit array-window domain and caller discharge
exist. Existing concurrency array lists and numeric `valid` ranges do not supply that domain.
Exact null-plus-zero remains checked; invalid nonnull pointers get no zero-offset exemption.

Validation: **8 public proof controls passed in 449.11s** (tile negative/positive, exact null,
local/global flat one-past, opaque arithmetic/indexing and rebound-alias refusal). After the
final internal AST-ID map was scoped by function, **8 public lowering controls passed in 2.75s**;
IDs never enter records. A new sequence 3 fixture method pins the final checker hashes: its
actual flat one-past replay proves and its copy model refuses before verifier launch. The
old methods remain unchanged. Three desired generic/copy positive acceptance cases remain
strict expected failures pending the explicit domain slice; no acceptance is replaced by a
refusal and called complete. Broader old fixture expectations still need that domain work.

Compact commands, uncached raw goal outcomes, source/log/inventory hashes, identities and
validated records: `evidence/wp-pointer-origins-20261015.json`. Full raw evidence is retained
under `/private/tmp/probata-cbmc-pointers/`; final fixture artifacts use the dedicated
`/private/tmp/probata-t36-tests/origin-final/` root. The next slice must pin/export explicit
array windows and independently discharge imported-summary/model domains from caller
origins. Ticket 36 stays **claimed**, blocked by ticket 27 and combined method/acceptance.

Integration handoff `964feccc` merges parent `0d3e6c18`, retaining no-filter initializedness
checks and the checked standard-model view alongside the origin gate. The post-merge public
lowering controls pass **8/8 in 1.98s**. This union changes the setup/reader hash (recorded in
the evidence), so final method pins must be recomputed after the parent finishes composition.

### Explicit entry-window slice — 2026-10-15 ET

Direct primitive parameters can now use the pinned `proof_unit.array_domains` contract declaration.
The source AST independently binds stable pointer parameters/aliases; every extent scalar is frozen
at entry. Checked assertions establish nonnegative/target-sized extent, null-empty consistency,
inclusive one-past formation and strict access bounds. They add no preconditions. Setup regenerates
the complete source lowering/certificate immediately before launch. Scripted, CBMC and Crux domain
admission remains closed. Retained helper calls, escaped/rebound/shadowed bindings and imported
domain-bearing summaries without caller discharge refuse, even if the caller declares no domain.

The typed-window declaration is an explicit advertised input-contract premise. WP33 checks its
numeric projection and ordinary RTE; smoke coverage is projected logical preconditions, not a proof
that every combination of typed-domain and formal conditions is realizable. A real oversized-domain
control first proved incorrectly; the checked target byte-capacity assertion closes that gap.

The frozen public batch passed **14/14 in 467.69s**, including real legal formation/index/alias/
dereference/null-empty proofs, failed frozen-extent/strict-one-past/negative-and-oversized-extent/
invalid-nonnull-zero obligations, and four prelaunch source-binding refusals. Evidence:
`evidence/wp-entry-windows-20261015.json`. This is a scoped checkpoint; imported calls, closed-owner
mapping and DX100 host-footprint discharge are separate work in progress. Ticket 36 stays claimed.


### Closed-owner source/view coupling — 2026-10-15 ET

The checked vector relation now populates `pointer_bounds.owner` directly from the original AST.
Every retained alias/member observation is bound by exact source range to the registry's
entry-frozen allocation and independently checked renamed-view range/liveness guards. No generic
source-name assertion is injected into the renamed view. Both checker modules contribute to the
lowerer identity and `model_domains.py` is included in the frozen setup/reader closure. Admission
requires the checked owner view, while prelaunch regenerates the source and both certificates.
The new public coupling control first failed because the lowerer registry was absent; coupling and
three rehashed renderer/guard controls subsequently passed **4/4 in 29.69s**. Actual owner WP
acceptance is still pending on the combined source; no generic model-origin waiver is introduced.

Final source/view prelaunch controls pass **11/11 in 71.22s**; changed checker-byte method refusal
passes **1/1 in 10.34s**. Commands/log digests and combined identities are in
`evidence/wp-entry-windows-20261015.json`.


### Independent merge review: private-view annotations — 2026-10-15 ET

The merge review found that Clang's C inventory ignored added ACSL after the pinned allocator
prefix. A direct replay accepted injected axiomatic, function-precondition and line-style
precondition annotations before the repair; all three now refuse. The private view admits only
checked named assertions, its two exact generated loop blocks and its two exact liveness ghost
effects before the adapter inserts the separately checked source contract. Public fake-verifier
origin and renderer-tampering controls pass **7/7 in 67.06s**; these are prelaunch controls, not
actual WP acceptance. Runner collection is entry windows **15**, owner **16**. Evidence:
`evidence/owner-annotation-merge-review-20261015.json`. Ticket 36 remains claimed, with combined
safe/stale WP replay pending.


### DX100 call-origin coupling checkpoint — 2026-10-15 ET

The lowering inventories audited host-pointer calls regardless of whether the unit declares a
window. Each candidate needs an independently resolved full-TU global imported callee, canonical
signature, exact semantics-entry/model/geometry policy, safe standalone placement and stable
entry-window origin. Only that transient source call key avoids pointer-escape invalidation.
Checked call-state footprint assertions retain the entry-frozen extent and exact current offset;
all original command/initializedness/separation obligations remain. Retained helpers and missing
window metadata refuse rather than inherit a silent premise. Tile-pointer producers also require
exact imported binding keys; source definitions, namespaces and unrecognized linkage/code
attributes refuse. Prelaunch reparses the entire source and rederives live policy factories.

The first actual direct-stream proof passed **155.85s**; the final frozen batch's stream replay
also passed. The full 14-control actual/prelaunch batch is running at this checkpoint, so broader
acceptance is pending. Supporting public binding controls passed 3/3 before the producer/attribute
extension; the attribute fixture's first attempt refused at C++ parse time because its redeclaration
followed earlier uses, and the fixture now attributes the original declaration instead. A final
public checker-byte invalidation control passed 1/1 in 11.00s; 17 component controls pass in 1.14s.
The source insertion API additionally records exclusive `source_statement` spans and
`source_functions` body/definition spans, with macros providing no invented statement positions;
2 public lowering controls pass in 0.62s. No bounded domain admission or method 3 claim is added.


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


### Primitive bounded entry-window checkpoint — 2026-10-15 ET

Direct real CBMC now admits one straight-line primitive function with explicit entry
windows, exact source statement/operation bindings and the existing initializedness
gate. It inserts the same checked numerical bounds and immutable entry snapshots into
lowered C and source C++ replay. Every mathematical intermediate must fit a checked
signed 128-bit representation. Nonnull physical capacity is explicit and can exceed
the logical window; helpers, models, imported domain summaries, whole-function, Crux,
automatic bounded-chain and runtime-check domain paths remain closed.

Frozen source `07a9a299`: five remote controls pass in 189.77 seconds, node 0 lease
554, wrapper exit 0. The positive has 44 successful non-reachability properties and
one expected failing reachability witness. The two numerical negatives have exactly
one failing window property each and replay that same property on C++; oversized
mathematical intermediates refuse before launch. All referenced evidence hashes match.
[Compact remote evidence](../evidence/bounded-entry-windows-mbit10-20261015.json).

Independent review found that the earlier snapshot name could shadow a source global
in both generated views; native output changed 9 to 2 despite differential agreement.
A regression reproduced the defect before the fix. Reserved source/reference names,
including hidden header declarations, now refuse. The corrected source was independently
reviewed and remotely replayed; 40 component checks and two source/header collision
regressions pass. No old pre-fix admission is promoted. The checker bytes join translator
and setup/reader identities. Native agreement is its recorded finite draw set, not
exhaustive coverage of every machine-integer value.

Crux fallback initializedness/source alignment is being fixed separately; its earlier
CBMC-only differential callback regression was removed from the shared method. Method
drafts 1/2 stay immutable, draft 3 remains pending, and this ticket remains `claimed`.


### DX100 direct-call final hardening — 2026-10-15 ET

The full original batch finished **13 passed / 1 failed in 1440.90s**. The failed legal offset-gather
proof correctly remained `vacuous_pass`: generic normalization of literal `+1` introduced an
`if (1 == 0)` branch and strict smoke detected it. The repair folds only exact AST integer literals:
zero returns the base and nonzero retains the original arithmetic. All checked numerical bounds
remain; no smoke result is waived.

Every audited imported DX100 call now receives the same full-TU global binding, exact prototype and
model-policy check, including scalar register commands. Templates and source-defined scalar commands
cannot borrow the hardware contract. Retained source declarations in the reserved `dx_`/`DX_`
proof-state namespace refuse before a generated guard can bind to shadow state. Host footprints,
tile-pointer producers and every live policy are independently regenerated before launch.

Final hardening passed **9/9 in 353.90s**, including the actual repaired offset-gather proof and
eight prelaunch binding/alias/state-shadow refusals. The same final source then passed both actual
stream and three-read proofs: **2/2 in 406.20s**, peak **3,417,423,872 bytes**, no timeout or OOM.
The stream has 31 ordinary Valid goals and 13 passing smoke goals; three-read has 87 ordinary Valid
goals and 31 passing smoke goals. The repaired gather has 45 ordinary Valid goals and 17 passing
smoke goals. Component/source-span checks pass **19/19 in 1.28s**. All 25 preserved proof records'
listed artifact hashes were independently checked while producing
`evidence/wp-dx-call-windows-20261015.json`, which retains the original strict-smoke failure.

This checkpoint covers direct audited calls under explicit typed entry-window input-contract
premises. The original pointer-helper case still refuses; the separately staged checked contextual
helper module has not been wired into the adapter. Pointer region/query calls without a checked
footprint policy and generic imported domains remain unsupported. Ticket 36 remains **claimed**,
with ticket 27 and final combined method/acceptance still open. Immutable method files are unchanged.


Independent integration review — 2026-10-15 ET: the merged source passes **35 non-solver
component/source-span/collision/math/doc controls in 2.16s**. Additional direct AST checks retain
six exact import bindings on the safe fixture and refuse source-defined scalar commands, template
producers, namespace impostors, wrong signatures and shadow proof state. Literal zero/nonzero and
variable offset forms retain their distinct normalization policies. Fresh prelaunch source replay
includes import-only jobs and current library policies; the bounded checker/source closure remains
complete. No new real verifier replay or historical-method evidence upgrade is claimed by this merge.


### Crux source-admission integration — 2026-10-15 ET

Both Crux forms now require the retained source closure to pass the initialized-input policy;
an unanalyzed C++ cut remains unsupported. Fresh prelaunch replay regenerates the source, current
summary stubs and exact harness/view. Explicit source-policy refusal stops the bounded route,
and `bounded_chain.py` joins the frozen checker closure. Independent merged validation passes
**24 stand-in/doc/method-pin controls in 18.06s**; no real solver was run. The complete DX/bounded
checker dependency union is preserved. Generic imported-summary proof-source/bounds eligibility
is still an open, separately owned gap: refreshed stub identity does not certify eligibility.
Ticket 36 remains claimed. Evidence: `evidence/crux-source-admission-20261015.json`.

### Checked contextual helper adapter — 2026-10-15 ET

The staged helper transformation is now coupled to the public WP adapter. It is attempted only
when an original DX100 unit with retained helpers needs an origin relation. The closed grammar
expands annotation-free acyclic primitive void helpers, captures actual arguments once and retains
audited imported calls in order. An independent full-TU AST comparison checks the transformation;
the normal origin/CPU-domain/initializedness/RTE checks still inspect the effective lowering.
No helper requires or window is synthesized. The original source/lowering and effective source/
lowering have separate immutable pins and reports, and both lowerings plus the AST relation are
freshly regenerated before invocation. Source-anchored hints remain refused in this slice.

The first public RED reproduced the old unsupported boundary. Integration controls then exposed
the real candidate's UTF-8 comments and a scratch-lifetime evidence bug. Byte-oriented editing now
preserves Clang offsets and unedited source bytes, and the private source view persists under the
WP evidence directory. Matcher closures are released after the same checks to avoid retaining
full-TU ASTs into subsequent checks/verifier execution. Both helper bytes and parser bytes are
pinned transitively; altered helper-checker bytes refuse under the frozen method.

Validation: **35 helper components + 1 public stale-pin control pass in 15.81s**. Five public
fake-WP controls pass **5/5 in 332.13s**, covering admission/reporting, missing entry windows,
source hints, changed private source and changed certificate. Those five precede the nonsemantic
matcher-closure release; the final component and actual runs use the final checker bytes.
The actual size fixture and missing-input-initializedness control pass **2/2 in 512.71s** under
the 8 GiB outer watchdog (peak **7,301,693,440 bytes**, no OOM or timeout). Safe: **38 ordinary
Valid + 15 smoke PASS**. Missing initializedness: **37/38 ordinary Valid + 15 smoke PASS**;
the only open goal is `typed_real_dxf_size_call_maa_stream_load_requires_source_initialized`.
All listed artifacts of five preserved proof records were independently hash-checked in
`evidence/wp-helper-windows-20261015.json`.

The original three-read helper source still refuses `base[q[0]]` because nested memory reads are
outside the checked offset grammar. This is a separate source-operation obligation, not permission
to waive the origin gate. No production method 3, full ticket-27 acceptance or ticket-36 resolution
is claimed. The next slice must account independently for the inner read's bounds/initializedness
and the outer read's numerical bound, preserving evaluation and exact source bindings.

The parent summary-binding/owner checkpoint `45560225` is integrated after the frozen actual pair.
Both setup checks and named dependency lists are retained; summary binding inspects the effective
source while the helper certificate retains the original source. A post-merge public fake-WP
composition replay passes **1/1 in 131.81s** (peak 6,743,965,696 bytes). Its generated C lowering and
WP input are byte-identical to the actual safe proof above. This replay establishes admission and
composition only; the actual proof records retain their exact pre-merge method/checker identity.


### Generic summary definition/proof binding — 2026-10-15 ET

A real public CBMC control on `44d50f7e` confirmed a false proof: the candidate's
same-name clamp returned zero while the summary was proved on the correct clamp.
Both native views agreed on the changed implementation. An exact source-span
native witness with `a=[1], n=1` returns `[0]`, violating the caller's preserved-value
postcondition. Name equality and native agreement did not establish summary validity.

`summary_bindings.py` now independently resolves the actual global call and
compares complete fresh callee C closures, ignoring only the generated provenance
banner. It requires the proof's exact current method/checker, implementation
lowering hash, build constants, contract/code pins, named real adapter and
retained artifact hashes. Generic globals/persistent state, external-only
declarations and model/summary dependencies remain closed. WP retains its stricter
unbounded/current-WP dependency policy. Every imported binding is replayed before
launch and must match both its generator-owned plan and summary pins. WP preserves
the binding report through final settings construction. CBMC/Crux choose the newest
eligible proof, so a newer stale-method record cannot mask a valid predecessor.

Finite arguments must follow from literals or unmodified caller entry bounds.
Pointer arguments must be distinct entry-buffer bases of exactly the proved
physical capacity. The old add-one positives proved only `n<=2` for `n<=3` callers;
they now prove `n<=3`, and a separate negative checks the former mismatch. No
finite proof silently supplies an unbounded contract.

Validation covers 15 distinct actual/public controls across selected runs:
11 passed in the initial 13-control batch; its two stale-method test fixtures
used invalid all-zero hashes and failed record validation before this gate.
Both corrected fixtures use a valid older method pin and pass (72.63 seconds).
Two further controls show both Crux forms refuse before their solver launches
(59.79 seconds; their library summary was proved by CBMC). Matching WP and CBMC
imports and all three corrected bounded stub-meaning controls pass. Runtime
manifest hashes remained unchanged throughout. An earlier 88-case Crux/scripted
setup batch passed; it is not actual Crux proof evidence. The record-evidence
mutation control deliberately changes one artifact hash; every other audited
artifact hash matches. This checkpoint does not resolve ticket36 or draft 3.

Evidence: [summary-source-binding-20261015.json](../evidence/summary-source-binding-20261015.json).
Regression: `tests/test_summary_source_binding.py`, including corpus case
`summary-same-name-different-body.yaml`.


## Checkpoint — 2026-10-15 09:53 ET: frozen mbit10 replay

Source `fddb1462dfb9ff8d7885521bc6edaf367d97a12e` (merged into integration
`45560225`) ran in two socket lanes from 09:32 ET. Node 0 native shard passed 132
checks with one deselected in 145.05s; node 1 bounded/source-summary shard passed 17
checks in 581.79s. Both wrappers exited 0 and leases released. The audit covers 27
retained proof records: all referenced artifact hashes match except the deliberately
zeroed report pin in the evidence-mutation negative control. That dependency control
is not accepted as a proof. Raw output remains remote for its readers; only compact
metadata is exported. [Evidence](../evidence/summary-source-binding-mbit10-20261015.json).
This checkpoint does not close the ticket's remaining acceptance criteria.


## Checkpoint — 2026-10-15 10:49 ET: helper/construct remote audit

Frozen `1ece49b8` ran in two socket lanes from 09:57 ET. Entry-window and actual
helper controls passed **17/17 in 1428.35s** on node 1, generation 597. Constructs
on node 0, generation 556, stopped at its first failure: **5 passed, 1 failed in
1268.59s**. The failure is the standalone `std_copy_int` model's uncertified opaque
pointer origin, before WP launch, with zero goals. It is not a failing numerical
proof or full construct acceptance. A separate qualified model-body repair is under
review; caller range discharge remains required.

All referenced artifact hashes match across 43 retained records. Both socket leases
and the legacy lease were released at the 10:49 ET live readback; load was
0.32/0.07/0.30, `/data1` had 21 GiB and `/data` had 97 GiB free. Raw results remain
remote for coordinator, ticket acceptance and independent audit readers.
[Compact audit](../evidence/helper-construct-mbit10-20261015.json). This checkpoint
does not resolve the ticket. Recheck live state before dispatch.


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

### Nested entry-read checkpoint — 2026-10-15 ET

`nested_entry_reads.py` supplies a separate checked source view for one-level
`base[q[k]]` reads in pure returns. It captures each original inner plain-int read
once, retains the inner bounds/validity/initializedness checks before that capture,
and checks the outer bound against its value. Both direct pointer parameters need
explicit typed entry windows. No scalar mathematical expression gains permission
to read memory, and no contract premise is synthesized. Checked helper expansion
may precede this view; original, intermediate and final sources/lowerings and both
independent AST relations are replayed before launch. Schema/source/checker pins
and persistent view/certificate artifacts cover the additional stage.

The closed executable dependency check refuses globals, unexpanded source/header
bodies, default-argument evaluation, member/indirect calls, location-dependent
expressions and declaration/statement attributes (including implicit cleanup
calls). Capture variables must have ordinary automatic storage, with no TLS,
static storage or attributes. Independent review reproduced a cached-static
renderer fault accepted by the first checker, while the downstream lowerer still
refused it; the explicit storage check and same-byte-length fault controls now
reject it directly. All unedited byte regions and header dependencies are checked.

Evidence: [compact manifest](../evidence/wp-nested-entry-reads-20261015.json).
The original three-read candidate at `a185bc8b` proves with **112 ordinary Valid
properties and 31 passing smoke tests**, under the 8 GiB process-tree cap
(455.54 s, peak 5,843,206,144 bytes). This actual run precedes the stricter
storage/attribute refusal. Final-source `18e7a7f0` passes **60 structural/helper
controls** and **8 public controls** (175.28 s, peak 880,541,696 bytes): a fresh
primitive nested read proves; inner-window, outer-window, missing-initializedness
and null-inner controls each leave exactly their intended checked property open;
changed view, certificate and window binding stop before WP. Every persisted
report in the manifest was independently rehashed. The obsolete original
three-read refusal expectation is replaced by a missing-entry-window control;
its supported explicit-window behavior has separate actual acceptance evidence.

Ticket 36 remains **claimed**. These are scoped fixture checkpoints; they neither
freeze production method 3 nor close the complete ticket-27 acceptance matrix.

Two focused existing regressions also pass at `18e7a7f0` (166.98 s, peak
5,134,909,440 bytes): original three-read source without declared entry windows
still refuses before WP, and the existing legal one-past entry-window fixture
still proves. The manifest includes both records and their checked report hashes.


### Nested initializer scope — 2026-10-15 11:21 ET

Frozen `f9ace980` extends the checked nested-read view to one automatic plain-int
initializer in a braced block. Fresh read captures precede the original declaration
in that same block. Exact original declaration locations and later references are
independently matched; static/TLS/type/root/sibling mutations refuse before WP.
No source memory read or input premise is removed. The existing pure-return slice
and all ordinary bounds/initializedness checks remain active.

The corrected original-policy public control fails as unsupported (3.66s); its
new stand-in reaches WP. Thirty-one public mutation/component controls pass in
22.80s. Actual WP produces the four expected outcomes in130.33s: safe PROVEN
(14 ordinary Valid +1 passing smoke); each missing inner/outer window and missing
inner initializedness remains NOT_PROVEN on its independent obligation (13 ordinary
Valid +1 timeout +1 passing smoke). Pytest reports3passed/1failed solely because
the last assertion guessed a prover goal spelling; the corrected semantic
initialization-property assertion passes against all four retained records. No
successful actual job was repeated. Two earlier test-helper API errors are retained
and excluded from semantic RED/GREEN evidence.

All report hashes and runtime manifest entries match. Test-only assertion changes
are explicit. [Evidence](../evidence/wp-nested-initializers-20261015.json).
Helper/nested statement-anchor hints and the full store/capacity acceptance remain
open; this checkpoint does not resolve the ticket.


### Original-TU parser context repair — 2026-10-15 ET

Linux's original 134-pass/1-failure native shard exposed a reconstructed CAPI
header order mismatch: its implicit driver defaults preceded captured libc++
paths. Suppressing those defaults fixes the original compatibility-header failure.
Independent follow-up found a second, material CPATH/CPLUS_INCLUDE_PATH ordering
gap: repeated environment search could hide an explicit-include allocation hook
even with identical physical dependency sets. Its public lower control reproduced
RED; no verifier was launched. The parser now runs in an isolated child with
include environment variables removed. All original driver queries retain the
original environment explicitly, and worker failures refuse.

At `7e663aaf`, 13 targeted Mac controls pass (36.47 s), and six Linux public
compiler/stand-in controls pass (87.005 s; peak 374,874,112 bytes under 8 GiB).
The earlier header-only `b5855894` checkpoint separately passes three Linux
controls. Both reserved node-0 leases released; the frozen primary remote source
and concurrent node-1 job were untouched. These results do not upgrade historical
proof pins or close ticket 36.
[Compact evidence](../evidence/stdlib-parser-context-20261015.json).


Merged runtime `77624eec` preserves the checked owner-call and standard-copy call
sets together, as well as all checker/lowerer source identities. Fourteen focused
combined compiler/stand-in controls pass (100.94s, peak450,658,304bytes under8GiB),
including both positive source views, declaration/return fault refusals, exact
callee/request coverage and worker failures. This is composition evidence only;
new actual caller proofs remain coordinator-owned. Ticket36 stays claimed.


### Final frozen Linux checkpoint audit — 2026-10-15 11:46 ET

Frozen `5c2a` jobs finish with native134passed/1failed and entry19passed/1failed,
both exit1. The original owner-data safe test has zero WP goals and no WP log:
it stops before launch on the same CAPI libc++ compatibility-header context
refusal repaired at `7e663aaf`. Its selected stale-alias successor is not reached
because `--maxfail=1` stops the shard. This is a prelaunch failure, not a failed
owner theorem. Twenty-three deduplicated proof YAMLs parse; all155 report
references (153 unique files) and2,852 declared absolute file-pin references
match retained bytes, with916 unique files hashed. No solver was rerun for audit.

A prospective metadata correction remains necessary: some actual positive WP
records retain `verifier_launched:false` despite WP logs and proof goals. These
historical records stay immutable; current acceptance is traced to their artifacts.
[Compact final audit](../evidence/source-gate-final-frozen-5c-20261015.json).


### Prospective WP invocation metadata — 2026-10-15 ET

`b4dc2748` sets `settings.verifier_launched:true` only after generated-input,
source and pin checks pass, immediately before invoking the WP watchdog. True
means attempted verifier invocation, not successful completion or proof. Real
prelaunch source refusal retains false. The public stand-in regression first
reproduces1failed/1passed; the correction gives2passed in47.06s under8GiB
(peak408,092,672bytes), with no actual solver. Historical5c records are unchanged.
[Evidence](../evidence/wp-launch-metadata-20261015.json). Ticket36 stays claimed.

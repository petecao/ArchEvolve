# 28 — Proof semantics for the remaining maa_* calls

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 27
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("DX100 proof semantics", "Concurrency" (history read), "What a proven verdict asserts" (the seven assumption kinds), "Testing Decisions", S1, S2); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [14](../../formal-verification-2026-10-09/issues/14-dx100-wait-rule.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md)
**Time estimate:** about 1 week

**What to build:** The proof semantics grows to the whole DX100 interface, so DX100 code of any kernel can be proven against it, not only BFS. Every remaining `maa_*` call of `dx100-mmio 1.0-e4fc4af` gets its contract, written per call from the interface and the gem5 source, never from a kernel. The new version adds the memory rules ticket 27 left out: a CPU access that overlaps an unfinished command's footprint (split by thread and by what DX100 does), device-against-device ordering by gem5's region stall, tile ownership as a proof obligation, the 8-byte tile pair, and a `get_tile_ready` that may answer either way. It also writes down what proofs trust at the call boundary and across cores: the MMIO code and the visibility entries of map 12 item 7. End to end: `swdb prove` on synthetic fixtures gives the verdict each rule predicts, and every verdict lists the matching assumption entries.

## Active implementation — 2026-10-15 21:19 ET

Ticket 27's independently reviewed closure is published at `af10a946`, releasing
this dependency gate. A new semantics version will preserve the readable 0.1
version and use the complete pinned interface declaration inventory. All fixtures
remain synthetic; implementation and actual evaluation admission are separate.
The coordinator owns both mbit10 lanes and actual verifier scheduling.

## Acceptance

- [ ] **Whole interface, per call.** The new version has exactly one contract per call of `dx100-mmio 1.0-e4fc4af`. Negative control: with one contract deleted, `swdb validate` refuses the version. Every new rule, values included, cites gem5 at `e4fc4af` or is assumed with an owner. Every fixture is synthetic; no held-out kernel code is read or proven.
- [ ] **Overlap, same thread** (map 12 item 4). Through `swdb prove`, the issuing thread's CPU read of an element inside an unfinished DX100 store's footprint is refuted; so is its CPU write into an unfinished gather's footprint. A same-thread CPU read inside an unfinished gather's footprint (neither side writes) proves.
- [ ] **Overlap, other thread.** Another thread's CAS on an element that an unfinished gather reads raises no hazard. The gathered value is a history read: some value the element held while the command ran, never older than the stores made before issue. A fixture asserting "the value at issue or the CAS's value" proves; one asserting "the value at issue" is refuted. Another thread's CPU read of an element inside an unfinished DX100 store's footprint is refuted.
- [ ] **Region stall** (device against device). Issuing a command covers earlier unfinished commands on the same registered region when either one writes, whichever thread of the one instance issued them: a fixture that relies on it proves. Two read-only commands on one region, or a writing command on another region, cover nothing: fixtures that rely on them are refuted.
- [ ] **Tile ownership is a proof obligation.** A thread's command or tile-pointer access on a tile another thread owns is refuted; disjoint tiles prove. The device does not enforce ownership: tile numbers are one global pool, and a wait counts other cores' commands on the same tile.
- [ ] **8-byte tile pair** (map 16 item 11). An 8-byte operand in tile t occupies t and t+1; ownership and hazards cover both. While a command whose 8-byte destination is t is uncovered, another command that writes t+1, or a CPU read of t+1, is refuted. Owning only t is refuted. The same fixtures with a 4-byte operand prove.
- [ ] **`get_tile_ready`.** While commands are pending it may return either answer. A fixture that loops until it returns 1 and then reads proves (a 1 counts as a covering wait). A fixture that reads after a 0 without waiting, or relies on a 0 while commands are pending, is refuted.
- [ ] **Visibility rules** (map 12 item 7). L5 is a rule citing research 12's gem5 lines: DX100 reads see CPU stores made before the command was issued. A fixture whose gather after a CPU store reads the stored value proves; asserting the old value is refuted. "The next thread's DX100 load sees the store" is a cited rule. "The store inside `critical` finishes before the lock is released" follows from the wait rule: a fixture asserting that a DX100 store issued in a block has finished at the block's end proves with its covering wait and is refuted without it.
- [ ] **What proofs trust, written down.** Every proof record whose content-hash set includes this version lists these assumption entries, each with a kind, a reference (ID and hash) and one plain sentence: the MMIO code "implements the call semantics, including ordering" (evidence research 14), with its portability note (the wait's fence has no `"memory"` clobber; never counted against a candidate artifact); the two gem5 corners behind the next-thread rule; "no stale CPU copy survives a DX100 store" (owner Eric); "one DX100 instance". Through `swdb candidate-level`, none of them caps a level.
- [ ] **New version, old kept.** The version is new. Ticket 27's version stays readable and still validates.

## Notes

- **Not in this ticket:** 27 — Proof semantics for the BFS read-offload calls (those calls, the ghost state, the wait rule, the probes). 29 — Proof-semantics checks (strict-layer agreement, the three forms, the semantics negative controls). 30 — Reference definitions, per-call summaries and new intrinsic versions. 31 — Five-gate drafting and the new bfs_read_offload version (the L3 and L5 placements in the `bfs_read_offload` contract; `bc_read_offload` stays untouched before the freeze, O8). 44 — Shared-action kinds and commutativity lemmas and 45 — Per-thread lowering (other threads' DX100 commands as shared actions; tile disjointness per candidate artifact). 49 — Peter's race repaired; A4 exit (proves that the read offload tolerates the history read, through L4). 51 — Strict-layer catch-up (the strict layer gets the memory-timing rule; the 8-byte rule waits until after the evaluation). 43 — Rocq: DX100 reduction lemma.
- Rules are per call, not per kernel, so they serve BFS, BC, PR and SSSP alike (map 12 item 12). Fixtures that exercise calls BFS never makes are written for the test.
- Assumption (not decided in the map): in a fixture, "another thread" is a second thread ID issuing calls in one fixed sequential order. This lets the single-thread bounded verifier judge the other-thread rules now. Real interleavings come with 46 — CIVL adapter and 47 — GenMC adapter and agreement.
- Assumption (not decided in the map): every entry above (the MMIO code, each of the two gem5 corners, the stale-copy entry, one DX100 instance) has kind "proof semantics" (the glossary's "the accelerator's proof semantics"). Map 12 items 6-7 name them but give no kind. For the MMIO code, "trusted tool" is the other reading.
- Assumption (not decided in the map): the entries are listed in every verdict whose content-hash set includes this version, not only where the proof used the rule they back. Sound but noisy. Trimming per rule (for example, the stale-copy entry only where DX100 writes memory the CPU later reads) needs Yan-Ru.
- Assumption (not decided in the map): the interface's call list comes from the hardware interface entry `dx100-mmio 1.0-e4fc4af`. If that entry lists no calls, the list is read from the interface at `e4fc4af` and recorded with the version.
- Risk: research 12 read gem5 source only. Two corners stay open: a write reaching L3 after the snoop filter dropped the line, and a write passed below L3 when no block can be allocated. The region stall spans one instance; the paper's scalability runs use two.
- Evidence: [research 12](../../formal-verification-2026-10-09/research/12-dx100-memory-visibility.md), [research 14](../../formal-verification-2026-10-09/research/14-dx100-wait-rule.md). No message to Eric or the DX100 authors (out of scope).
- Fixture proof records carry `contract_fixture` evidence. Mac: one real verifier job at a time under the ~8 GB RSS watchdog; tests skip cleanly when a verifier is missing.

## Implementation checkpoint — 2026-10-15 ET

The first public validation slice now checks the complete immutable two-header
surface independently of the BFS-use regex: 26 names / 27 declarations, including
`print_tile`, `get_data_type`, noncacheable pointer and both register-allocation
overloads. Three RED/GREEN cycles demonstrate refusal of the smaller BFS set and
the missing initialized overload. Eighteen scripted controls pass with compiler
and verifier tools disabled, under workerB and the 8GiB/time guard. The accepted
structural fixture uses explicitly unreachable added contracts, so it establishes
no new call behavior. No semantics0.2 entry is current; all0.1 library bytes remain
unchanged. Typed contracts/models, memory/history/pair rules and actual synthetic
acceptance remain incomplete; status stays **claimed**.
[Implementation boundaries and next slices](../prototype/28-proof-semantics/README.md),
[exact RED/GREEN evidence](../evidence/t28-declaration-inventory-controls-20261015.json).

Typed-call compiler prerequisite — 2026-10-15 ET: two public `swdb lower` RED
controls exposed a template-allocation overload collision and silent collapse of
six zero-argument type specializations. Both are repaired through exact same-TU
source-call/declaration binding and deterministic arity suffixes. Ten
compiler/native controls pass, including native C++/C width behavior under
ASan/UBSan. No actual verifier or new semantics0.2call acceptance is claimed.
[Exact compiler evidence](../evidence/t28-typed-call-abi-controls-20261015.json).
The separate source-reading correction to optional indirect old-value results is
recorded [here](../prototype/28-proof-semantics/indirect-old-value-correction-20261015.md);
future contracts must use the alias to the modified copied line. Ticket remains
**claimed**; all substantive memory/history/ownership/pair and full-call actual
acceptance criteria remain active.

Trust-record prerequisite — 2026-10-15 ET: both public adapter paths now list
explicitly marked per-rule trust entries on every verdict using the version,
including prelaunch refusal records. Thirteen controls pass using version/parse
stand-ins and scripted fixture level records; all five entries remain noncapping.
A reproduced post-validation entry mutation is refused, preventing cached text
from receiving a new file hash. WP's earlier validation-time probe consistently
records the subsequently loaded version. No actual verifier ran, no new
production semantics version is current and the substantive acceptance boxes
remain open. [Exact evidence](../evidence/t28-trust-record-controls-20261015.json).

Typed-instance prerequisite — 2026-10-15 ET: concrete type/arity contracts now
replace a template family's generic fallback; baseline validation/source binding
refuses missing/ambiguous selectors, C ABI mismatches and unpinned source bodies.
Both allocation declarations remain mandatory and selected instances appear in
adapter settings. Focused39/39 and overlapping final29/29 compiler/native/
stand-in controls pass. A separate genuine changed-module RED/GREEN closes the
checker identity over the imported contract-routing module; a fresh identity-bound
scripted method accepts. No actual formal tool ran. Actual header-body/ABI
bindings and all substantive new call/state/value/history/memory acceptance
remain active, so no box is checked and status stays **claimed**.
[Exact evidence and partial-domain boundaries](../evidence/t28-typed-instance-controls-20261015.json).

Source-type prerequisite — 2026-10-15 ET: native REDs exposed familiar typedef
spellings hiding different local/return types and a class/global alias collision.
Source desugaring/unique unresolved targets now prevent that reinterpretation.
Pointer typedef parameters retain explicit array domains; unsupported reference
typedefs refuse before partial C output. Final49/49 focused compiler/native/
stand-in controls pass, including exact constant atomic golden output. No actual
formal tool ran; no old producer result is upgraded. The numeric per-call,
memory/history/ownership/pair implementation and new-version actual acceptance
remain incomplete. [Exact evidence](../evidence/t28-source-typedef-identity-controls-20261015.json).

Deferred-state prerequisite — 2026-10-15 ET: first generated C prototype APIs
retain issue-to-cover history values, producer versions and immutable observed
results; unresolved indices use issue images and actual write logs. Command
checks distinguish physical tile halves from explicit hardware IDs, global
ownership, exact region-conflict coverage, readiness answers and full physical
store-line CPU hazards. Final22/22 native controls pass under ASan/UBSan and the
workerB guard; no actual verifier, public proof acceptance or whole-call coverage
is claimed. Deferred write/RMW effects, full typed/source mappings, per-call
wrappers and formal IEEE relations remain active. No current semantics0.2entry
exists; status stays **claimed** and every acceptance box remains unchecked.
[Design](../prototype/28-proof-semantics/deferred-state-design.md),
[exact source/native/RED pins](../evidence/t28-deferred-state-initial-controls-20261015.json).

Numeric/action successor — 2026-10-15 ET:36/36 native prototype controls cover
the six raw-bit numeric types, consumer completion dependencies, deferred stores,
immutable RMW old values and inactive preservation, duplicate-entry order and
cross-region full-line device hazards. These are logical completion effects
qualified by no-interference and future checked source/address/F2 mappings;
no exact packet schedule or public/actual proof is claimed. Readiness still
allows zero forever, so mandatory polling termination remains unproven until a
source/trust-bound progress domain is established. No extra wait or desired
postcondition is assumed. All acceptance boxes stay open and status stays
**claimed**. [Exact successor evidence](../evidence/t28-deferred-actions-numeric-controls-20261015.json).

Region/address successor — 2026-10-15 ET:43/43 native prototype controls retain
source registration/first-ID lookup and F2 logical footprint checks separately
from physical store-line hazards. The raw address helper preserves defined
unsigned product/Addr wrap; the array correspondence guard is a caller obligation,
not source UB or a new original-unit precondition. Complete MMIO setup/source
wrappers/typed storage and public proofs remain open. A prospective finite-progress
environment assumption has explicit maintainer ownership and pending59freeze
review; current demonic readiness remains without a termination claim. All boxes
stay open and status stays **claimed**.
[Exact evidence and intermediate-run exclusion](../evidence/t28-region-address-controls-20261015.json).

Typed byte-image successor — 2026-10-16 ET:53/53 native C11/C++17 controls pass
for shared physical bytes, six scalar views, separate source stride/prefix,
deferred producer outputs and paired CPU/command hazards. Missing bytes,
insufficient physical output masks and sparse capacity refuse. This supplies no
source pointer/ABI or formal IEEE certificate; full-call wrappers and public
actual acceptance remain incomplete. All boxes stay open and status stays
**claimed**. [Exact RED/GREEN and physical pins](../evidence/t28-tile-byte-image-controls-20261016.json).

Inactive byte preservation — 2026-10-16 ET:58/58 native controls pass after two
RED profiles. Inactive completion preserves undefined payload without observing
it; later reads still fail as appropriate. Byte-wise conditional versions retain
initialized32-bit subviews without inventing upper64-bit initializedness. No
public/actual proof or whole-interface closure is claimed; all boxes remain open.
[Exact evidence](../evidence/t28-inactive-byte-preservation-controls-20261016.json).

Register successor — 2026-10-16 ET:75/75 native controls pass for source-shaped
register allocation/storage and exact explicit-ID CPU-write stalls, preserving
conservative second-half conflicts and noncovering reads. One deliberately
expected RF excerpt UBSan case establishes the configured native alignment
counterexample, not general source agreement. Setup/source wrappers, formal
IEEE/raw-image coherence, unbounded readiness progress and public actual acceptance
remain active. No boxes are checked; status remains **claimed**.
[Exact evidence](../evidence/t28-register-state-controls-20261016.json).

Setup successor — 2026-10-16 ET:81/81 native controls pass for exact six MMIO
regions, source32tile/16384word physical geometry independent of prefix2,
nonclearing alloc/init, source int8 conversion and last-pair/ownership boundaries.
One expected RF source alignmentUB case remains explicit. Complete source-call/
CPU routing, formal IEEE/raw-image and unbounded progress/source simulation,
new-version public acceptance remain open; all boxes unchecked, status **claimed**.
[Exact evidence](../evidence/t28-setup-state-controls-20261016.json).

Size-version successor — 2026-10-16 ET:86/86 native controls pass for separate
immutable size metadata, deferred capture, later source reuse, starting-tile-only
updates and noncovering CPU queries. Unknown entry metadata is an explicit
valid/quiescent prototype domain, not an established source-entry certificate.
Full source-call/CPU admission, IEEE/raw-image and progress/source simulation,
new-version public actual acceptance remain open. All boxes stay unchecked,
status **claimed**. [Exact evidence](../evidence/t28-size-state-controls-20261016.json).


Mathematical rank type gate — 2026-10-16 01:03 ET: exact9704c54b passed all three admitted syntax/type checks; independent cold review rehashed83 physical files with zero mismatches. Guard0.669s/46.3125MiB, no resource/cleanup failure, source clean. This accepts syntax/types only, with no VC, recursive termination, positive/negative proof, hardware fairness or source correspondence claim. Next admission is read-only expanded Why3 configuration metadata before a separately reviewed complete VC portfolio; existing partial_prover sections expand automatically, so no alternate configuration is proposed. [Actual receipt](../evidence/t28-rank-type-actual-20261016.json), [cold review](../evidence/probata-t28-rank-type-cold-review-v2-20261016.md).

Expanded Why3 metadata — 2026-10-16 01:23 ET: four admitted read-only calls each exited0, preserving existing configuration and all ten expanded prover variants/recursive driver closures. The original entry/guard exited1 after collection because its RC reader did not support raw multiline strategy strings. No metadata rerun: a separate pure parser with25 passing controls and483-check independent cold audit accepted the captured metadata observations, with zero errors; original failure remains immutable. No solver/version/VC/proof claim. [Actual and correction](../evidence/t28-rank-config-actual-and-reader-correction-20261016.json), [cold audit](../evidence/probata-t28-rank-config-cold-audit-v1-20261016.md). A separately reviewed whole-module rank VC recipe is next.

## Pure source-selector public vertical — 2026-10-16 ET

The first source-bound public workflow is implemented at source checkpoint
`1ddedf6085078bb78f446558365fc747f2c75fc1`: the real-header
`get_data_type<uint32_t>()` specialization is checked against canonical source
identity, its unsigned-char return ABI, immutable header bytes, and a constant
LLVM result after freezing the original main-TU preprocessing. A closed,
fixture-only stateless 0.2 entry inventories all 26 names/27 declarations and
explicitly refuses every other call. The retained 0.1 entry is unchanged.

The final composed compiler/scripted batch passed 68 controls and skipped two
actual formal cases (175.47 seconds, peak 3.26 GB, no OOM or timeout). Genuine
RED controls and repaired source-context, model-contract, dependency-closure and
nonempty prelaunch-witness boundaries are retained. See
`evidence/t28-selector-first-vertical-controls-20261016.{json,md}` and
`prototype/28-proof-semantics/selector-first-gate.md`. These controls establish
public plumbing and compiler/refusal behavior only; no actual proof or full
interface acceptance is claimed. The unchanged-source positive/wrong-enum
coordinator-only actual runner is committed, awaiting independent review and
root admission. A stateful size/readiness vertical follows this first gate.
All whole-ticket acceptance boxes remain open.


2026-10-16 readiness correction checkpoint (prototype only): the prior86-native
packet incorrectly expected an8-byte role's second-half wait not to cover. That
expectation is retracted; historical raw files and receipts remain unchanged.
Pinned MAA dispatch/finish and SPD counter code count both halves of src/dst
roles, excluding condition-only roles. The successor separates counted masks
from condition-inclusive hazards and starting-ID dispatch stalls. Source-backed
RED3fail/2pass becomes96native GREEN under ASan/UBSan. A checked source-role
wrapper, actual stateful proof and full interface acceptance are still open.
The real header supplies a blocking ready-range read returning1, not the logical
demonic query used by this prototype. All acceptance boxes remain unchecked.

## Conditional mathematical rank gate and selector publication — 2026-10-16 01:49 ET

The whole-module rank gate at exact `9704c54b838863dd838d18a20dd0ade1633d5027` completed all eight actual Why3 calls. Core5, arbitrary-finite-delay family4 and all-false1 are directly Valid; the separate absent-premise negative retains native sat, healthy solver exit0, Why3 `Unknown` + LF + `(sat)` and expected proof-command exit2. Original actual entry/guard/root exit1 and complete=false remain immutable: the original offline reader rejected that formatting before recording its negative submission receipt. Independent cold reconstruction binds all11 actual submitted SMT inputs to complete emitted bytes and native outputs. [Actual and complete reviews](../evidence/t28-rank-whole-actual-and-cold-acceptance-20261016.json), [independent mathematical/context audit](../evidence/t28-rank-whole-independent-cold-review-20261016.md), [supplemental v3 cold audit](../evidence/t28-rank-whole-cold-audit-v3-20261016.md).

The conditional result assumes a fixed trace and a mathematical rank nonnegative on future polls, strictly decreasing whenever not ready. All core assertion/variant/recursive-precondition/postcondition tasks and the acyclic four-post family were independently reviewed; no desired-result axiom or imported unconditional progress theorem is admitted. The family supports every mathematical n>=0, without a finite C-counter bound. It does not prove a device/environment supplies the rank or fairness premise. Separate pure formatting controls/cold audit repair only retained-output interpretation; no rerun or historical exit upgrade. Whole2.423s/147.25MiB, no resource/inspection/child failure; finite settlement limits retained. No MMIO/source-to-trace/public-composition/current0.2/full-ticket claim follows.

Final source-selector freeze `21edecf2d8a06234290e06861b6724dc76dd346e` is published as an ancestor of integration `4bb53cd7`. [Independent review](../evidence/t28-selector-first-vertical-independent-review-20261016.md) accepted the original-main-TU certificate, exact ABI/callee/source pins, partial26-name/27-declaration fixture and refusal boundaries. Wrong-enum acceptance now rejects vacuous_pass and requires all smoke statuses valid (retained RED2/GREEN4 plus2 actual skips). The original68-pass/2-skip compiler/scripted receipt remains historical and unchanged. At this01:49 checkpoint external entry/admission remained pending; root subsequently reports node1G615 exact21ed launched01:51 ET and ended01:52:23 ET with actual guard exit1 before WP invocation: fixture method Z3/Alt-Ergo pins4.8.14/2.6.0 mismatch admitted Linux5.1.0/2.6.4. Source stayed clean and leases released; separate fixture metadata repair is pending. Launcher exit0 and the independent local JSON pretty-printer exit1 remain distinct. No actual selector proof result follows. No production current0.2 acceptance follows. Ticket28 remains claimed with whole-ticket boxes open.

2026-10-16 actual-selector fixture repair checkpoint: after the historical21ed
pre-WP version mismatch, the fixture now requires an explicit four-tool actual
lineup from its coordinator, with missing/partial/duplicate/malformed inputs
refused before fixture work. Only copied method version fields change; all
production, installed0.1, source/model contracts, mandatory flags and backend
runtime comparisons remain unchanged. The runner validates before compiler
bootstrap and persists the map. RED19fail/1pass becomes28pass/2actualSKIP, plus
three existing public compiler/stand-in regressions. A named exit99 public
control pins the explicit Linux method versions and remains not_proven/tool_crash.
No actual proof result or whole-ticket acceptance follows. See
`evidence/t28-selector-explicit-lineup-controls-20261016.{json,md}`. Root owns a
fresh reviewed clean-source actual gate; the old raw failure is unchanged.


## Selector failure preserved; explicit fixture lineup prepared — 2026-10-16 02:00 ET

The final495-check [cold failure audit](../evidence/t28-selector-prelaunch-failure-21edecf2-20261016.md) preserves exact21ed node1G615: zero WP proof records, wrong-enum unexecuted, Mac fixture Z3/Alt-Ergo4.8.14/2.6.0 mismatched Linux5.1.0/2.6.4. Guard exit1/23.6279450804s/1,743,654,912B, no OOM/timeout; launcher0 and the independent local pretty-print wrapper1 are distinct. The raw77 files/375,635B remain remote;202 physical/Git bootstrap modules,29 selected source pins, reviewed entry/tool/config/57-file stdlib and runtime identities match with zero errors. Three finite same-UID process observations and released leases are not universal absence. [Admission snapshot](../evidence/reviewed-t28-selector-v1-launch-21edecf2-20261015.json) retains its mutable lane-hash boundary and historical date; the later cold audit is the final failure/settlement record, not an upgrade to success.

[Reviewed fixture repair](../evidence/t28-selector-lineup-independent-review-20261016.md) at executable source`770df40eeb5e3034862f61b79b6bcaad5fa620a7`, packaged in`b618b44c`, requires an explicit strict four-tool actual map before fixture/compiler provenance work. It changes only the copied method's four version fields, keeping normal production runtime matching, budgets, flags, source/contract and smoke/nonvacuity assertions unchanged. Missing/duplicate/partial/unknown/malformed input refuses; stand-in mode retains its old versions. Retained RED19fail/1pass becomes final28pass/2actualSKIP, with3 additional legacy controls;957 local reference pins including all919 producer physical references rehash without mismatch. These are pure/compiler/named-stand-in controls, not a new actual proof.

[External entryv3 static review](../evidence/t28-selector-entry-v3-independent-review-20261016.md) passes with30 exact770 source pins, reviewed Linux map and unchanged nested output/collection/runtime/guard checks. Exact770 remains the prospective actual producer; no new run is admitted by this checkpoint and no old21ed result is relabeled. Root owns fresh preflight, dispatch and independent settled actual audit. Status remains claimed; no installed current0.2, stateful-source or whole-ticket acceptance.

## Scoped selector770 actual closeout — 2026-10-16 03:02 ET

[Independent cold review](../evidence/t28-selector-770-independent-cold-review-20261016.md) accepts the exact public selector fixture caller workflow at source`770df40eeb5e3034862f61b79b6bcaad5fa620a7`, node1G616. [Compact acceptance](../evidence/t28-selector-770-scoped-actual-acceptance-20261016.json) binds both record hashes; [full metadata](../evidence/t28-selector-supplemental-actual-v5-770df40e-20261016.json) retains source/runtime/certificates/goal/property/CSV/TRUST closure. Positive record9cc082e7 is proven with7/7 ordinary Valid. Wrong-enum42d1da40 is not_proven/timeout:6/7 ordinary Valid and one open ensures, **not refuted**. Each record has9 goals/13 properties/9 CSV rows. All4 smoke rows are raw timeout/nonvalid with passed=true, normalized by native smoke Stats to proved1/external success1/time0; do not call them direct Valid, zero solver runtime, or a satisfiability proof.

Helper ensures/assigns remain explicit source-certified Extern assumptions, not body proofs. Its implicit exits false/terminates true remain Unknown, unselected, non-Extern with no generated goals/targets/dependencies/origins: implementation_verified=false. The narrow helper-owner/native-caller dead-call bridge is source-backed, not a general exemption. Full26-name/27-declaration interface support, stateful/current0.2 implementation, physical source mapping, hardware fairness and whole28 remain open. No checkbox or ticket status changes.

Root's pinned [v5 passive reader execution](../evidence/t28-selector-cold-readers-execution-v5-770df40e-20261016.json) reports6005 pin checks/2589 files/zero errors; [settlement](../evidence/t28-selector-root-settlement-v1-770df40e-20261016.json) reports471 checks and all146 raw files/17,364,662B stable twice. The independent reviewer locally checked171 manifest pins,66 exact770 source-policy blobs,11 primary sources and complete two-record CSV/property/goal attribution, without remote rehash, compiler/formal/native/probe/SSH calls. Nine primary sources are reported equal on Linux/Mac; two additional source references are local only. Raw remains remote. Guard exit0/156.995s/1,811,578,880B; outer159.017s/1,864,515,584B, no recorded OOM/timeout. Three finite settlement sweeps and absent leases do not establish universal current process absence.

All failed attempts remain unchanged: original21edG615 pre-WP method mismatch (launcher0/local pretty-printer1/actual guard1); passive reader v1 owner-context refusal, v3b wrong smoke-normalization demand, v4b CSV implicit-property/predicate-payload refusal. Local zero-byte v3/v4 JSON receipts and stderr are pre-SSH wrapper failures, distinct from v3b/v4b. V5's unchanged-policy pure correction has100 retained controls and needs no formal rerun. [Preservation manifest](../evidence/t28-selector-770-closeout-preservation-manifest-20261016.json) binds byte-identical archived readers/reviews/metadata. Later integration source changes do not upgrade the immutable770 producer. Status stays claimed;35 resolved/25 ready-for-agent/3 claimed overall.


## First stateful fresh-SPD size preparation — 2026-10-16 ET

Source7e64298fd1d81359e8db586883243b31d57bef3b binds one unchanged
`get_tile_size(0)` caller to actual header/ABI/original AST/frozen preprocessing,
volatile-load/fence/MMIO operations and pinned SPD constructor byte projection.
Its explicit synthetic core0/configured boot epoch is a recorded maintainer-owned
environment/source-model premise pending Yan-Ru59, never arbitrary-caller or
physical-boot freshness. All64 read bytes derive ordinary constructor assignments;
no desired-result original-unit precondition/axiom is inserted. Other25 names
remain explicitly refused in the complete26-name/27-declaration fixture;0.1 is
unchanged. Same-AST caller and getter gates reject macro/string lures, including
source UB hidden by optimization; a coherently rehashed getter-fence mutation is
rechecked before launch.

Final compiler/native/scripted controls pass34 with3actualSKIP (75.57s/341MB),
then4 post-integration controls pass (26.88s/345MB). Named exit99 records stay
not_proven/tool_crash, with no actual stateful verifier execution. See
[evidence packet](../evidence/t28-size-first-vertical-controls-20261016.md) and
[obligation map](../prototype/28-proof-semantics/size-first-gate.md). An inert
Linux correct0/wrong1 entry,353-source allowlist and explicit method/runtime
closure are prepared; pure runtime refusal controls retain RED6fail/4pass and
GREEN10pass. Root owns independent review/publication/fresh preflight/actual
admission. Actual source-model agreement, remaining interface/state transitions,
production current0.2 and all whole-ticket acceptance boxes remain open.

2026-10-16 03:10 ET integration checkpoint: [root static review](../evidence/t28-size-root-static-review-v2-7e64298f-20261016.md) and [composition review](../evidence/t28-t25-source-preparation-integration-review-20261016.md) accept size7e642 publication/preparation only, with353 exact Git pins and1400 physical preparation references rechecked here. The explicit conditional fresh-SPD premise/private64-byte representation remains visible; no actual WP result yet. Root alone may admit exact7e642 after fresh preflight. Current integration also composes independent T25 canonical preparation; historical selector770 records retain their exact older checker/runtime. Full interface/current0.2/hardware/source composition and ticket28 remain open.


2026-10-16 strict stateful negative acceptance successor: root reports original
7e642 actual positive8/8ordinary+2smoke, but the negative is solver_error with
failed/unknown/timeout native ensures results despite pytest exit0. Preserve that
historical result; it is not healthy negative acceptance. Separate test-only
successor2b25ee6c now rejects solver/resource failures and every unhealthy native
result, requires complete pinned matching goal inventory and actual attempted
ordinary nonproof, while retaining ensures-only-open/smoke/RTE/nonvacuity and
positive criteria. Pure RED13fail/5pass becomes24pass/3actualSKIP; no production,
method/source/model changes or formal rerun. See
[evidence](../evidence/t28-size-negative-health-controls-20261016.md). Root owns
remote cold audit, error diagnosis, independent review and future actual admission.

2026-10-16 03:32 ET: [independent negative-health review](../evidence/t28-size-negative-health-independent-review-83b90ed5-20261016.md) passes exact test-only83b90ed57e8421d9b6551baed44548f97215bd6b.2 test-source pins/15 physical references/all3 JUnit censuses match; final24 pure passes/3actual skips. It changes no production/library/API or original7e642 actual bytes. Root's original node0G588 ended03:15:22 ET, guard0/131.4438s/1.111GB/two pytest passes, yet negative d7bd0367 is solver_error with Failed/Unknown/Timeout, **not healthy and not refuted**. Positive f68eef75's8 ordinary+2smoke remains provisional pending full cold audit. No clean pair acceptance, actual rerun, current0.2 or ticket closure follows. Historical selected-source, record and guard exits remain unchanged; root owns any future repinned admission. Status35/25/3 unchanged.

2026-10-16 03:34 ET coarse settlement preservation: root's [810-check metadata audit](../evidence/t28-size-root-settlement-v1-7e64298f-20261016.json), SHA fd48386cee1dbaa67b0334f2fc05305170a33ee21538122101bec8f9ad2c7e50, retains all167 raw files/17,515,385B stable with exact7e642/source/guard/lane identities. Root ran this coarse passive audit; integration only verifies/copies its pinned metadata, without remote rehash. Positive acceptance and negative-error cause remain pending detailed independent audit; no clean pair or actual rerun is claimed.

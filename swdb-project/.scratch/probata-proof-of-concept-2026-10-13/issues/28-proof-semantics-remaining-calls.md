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

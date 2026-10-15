# 27 — Proof semantics for the BFS read-offload calls

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:18 ET (review fixes, round 5); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
**Blocked by:** 22
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("DX100 proof semantics", "Formal-half language and the C++ subset", "Modules" (library content), "Testing Decisions", S1, S2, S3); decisions: [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [14](../../formal-verification-2026-10-09/issues/14-dx100-wait-rule.md)
**Time estimate:** about 1 week

**What to build:** The first version of the DX100 proof semantics, scoped to the `maa_*` calls that the BFS read offload (through its lowerings) and the authors' `TDStepMAA` make. After this ticket, a proof that uses those calls trusts one ACSL contract per call, not the strict layer. Values come out as if each command finished at issue. Separately, reading a tile whose producer has not finished fails an assertion. The C lowering puts a generated hazard probe at every tile-pointer read. Hazard state lives in fixed-size ghost arrays declared once in the ACSL source; SAW's ghost state, and later the C stubs, carry the same arrays (map 16 item 10). End to end: `swdb prove` on a small DX100 fixture refutes a tile read placed before its covering wait, proves the same unit with the wait, and writes a proof record that pins this proof-semantics version.

## Acceptance

- [ ] **Coverage and citations.** The proof-semantics entry has a version and a content hash. It lists the calls it covers: every `dx100-mmio 1.0-e4fc4af` call that the BFS read offload's lowerings or `TDStepMAA` make, one ACSL contract each. Every rule, values included, cites gem5 DX100 source at `e4fc4af` or is assumed with an owner. `swdb validate` accepts the entry. Negative controls: `swdb validate` refuses a rule with neither `cites:` (gem5 commit, path, lines) nor `assumed: {owner}`, a citation at any other commit, and a listed call with no contract.
- [ ] **Unready read is a hazard** (map 12 item 3). Through `swdb prove` with the real bounded-verifier adapter, a fixture unit that reads a tile through a tile pointer before its covering wait is refuted, and the counterexample names the hazard probe. The same unit with the wait proves. `get_tile_size` before the covering wait is refuted the same way. A CPU write into a tile that an unfinished command reads is refuted; a CPU read of that tile is not flagged.
- [ ] **A probe at every tile-pointer read.** On a fixture with three tile-pointer reads, moving any one read before its wait is refuted at that read's probe, on the C++ path and on the C lowering, with agreeing verdicts. WP proves the safe unit and leaves each unsafe one "not proven", never refuted.
- [ ] **Wait rule as gem5 runs it** (map 14). These fixtures prove: a wait on a store's source tile covers the store and its result tile; a wait covers a command transitively through the tile and register producers it reads; issuing a command whose destination is tile t first covers every uncovered command that names t in any role, condition included (the tile dispatch stall); writing a constant into a register first covers every uncovered command that names that register (the device holds the write). These are refuted: reading an input producer's tile after waiting only on a range loop that filled its output tile (the range-loop exception); reading a command's output after a wait on a tile it names only as its condition; reading after a wait on an unrelated tile.
- [ ] **Values at issue.** A gather, stream-load or range-loop fixture whose read after the covering wait equals the call's computed value proves. The same fixture asserting a wrong value is refuted.
- [ ] **Footprints.** Each unfinished command's footprint is a logic predicate over ghost state and the current index-tile contents (indirect: the addresses its index tile names; stream: its range), with no per-element copy. A fixture asserting that an address in an uncovered gather's footprint is a member proves; asserting membership of an address outside it is refuted. (Overlap verdicts are ticket 28.)
- [ ] **Ghost capacity** (S3). A safe fixture with 32 uncovered commands in one thread proves. With 33 it ends "not proven", failure class ghost capacity, never refuted.
- [ ] **One ghost state, declared once** (map 16 item 10). The ghost arrays are declared once, in the ACSL source: per tile {owner, uncovered writer, uncovered readers as a bitmask over command slots}; per register {owner, writer}; per thread K = 32 command slots {kind, tiles, region, base, range or index tile, dependencies}. SAW (generated SAWScript) and WP (the ACSL as written) agree on every fixture above: both prove the safe ones, and WP leaves "not proven" each one SAW refutes. (The C-stub form is ticket 29's three-form check.)
- [ ] **Versioned.** Every proof record `swdb prove` writes with these contracts pins the proof-semantics version and lists the proof semantics in its assumption set. Through `swdb candidate-level`, a fixture record that pins an older version stops counting.

## Notes

- **Not in this ticket:** 28 — Proof semantics for the remaining maa_* calls (the other calls; footprint overlap rules; region stall; tile ownership as an obligation; the 8-byte tile pair; `get_tile_ready`; the MMIO and visibility entries). 29 — Proof-semantics checks (strict-layer agreement; three-form agreement on the semantics scenarios, C stubs included; the semantics negative controls; the reduction lemma's check). 30 — Reference definitions, per-call summaries and new intrinsic versions. 21 — C lowering and WP adapter (A2 tracer) and 22 — SAW adapter and SAWScript translator: this ticket uses them. 23 — C-stub translator, fallbacks and check mode (the C-stub form; not a blocker here). 36 — Proof setup check and verdict reading (it checks that probes are present and generator-made). 43 — Rocq: DX100 reduction lemma. 51 — Strict-layer catch-up.
- Why no per-element copy of a footprint: neither the device (the dispatch stall) nor the CPU (the hazard rule) can change an index tile while its command is uncovered (map 16 item 10).
- K = 32 is an encoding bound (one instance's command slots), not a semantic rule. A later version can raise it.
- On the C++ path the harness generator places a probe before each read loop (map 12 item 3, as the 08 prototype did by hand). Assumption (not decided in the map): this ticket builds that generator step beside the C lowering's probe, because the bounded verifier's verdicts on the C++ and on the C lowering must agree.
- Assumption (not decided in the map): the version written here is a working version that ticket 28 supersedes. Records that pin it stop counting then. A record that pins a version before ticket 29's checks reads "proof semantics unchecked" until they pass (29's assumption).
- Assumption (not decided in the map): the call inventory is read from the BFS read offload's lowerings and `TDStepMAA` at the ticket's start and recorded in the version. A later code change reopens it.
- This ticket checks no C-stub form: 23 is not its blocker. Ticket 29 (blocked by 23) owns three-form agreement on the semantics scenarios.
- Uncited rules stay "assumed, owner Eric" (map 12 item 11). No message to Eric now. Yan-Ru approves the proof semantics at promotion, not in this ticket; ticket 29 prepares its review packet for his review at the freeze (59).
- Risk: SAW ghost state on clang 22 bitcode is spike (a)'s question. If ticket 09 sent the bounded verifier to its crux-llvm fallback, the ghost state goes into that path's stubs instead. Follow ticket 09's verdict.
- Risk: splitting values from hazards rests on the reduction lemma. It is an assumption entry of kind reduction until Rocq checks it (ticket 43; map 12 item 2). Ticket 29 adds its written proof and bounded check, which do not remove the entry.
- Fixture proof records carry `contract_fixture` evidence. Mac: one real verifier job at a time under the ~8 GB RSS watchdog; tests skip cleanly when a verifier is missing.

## Answer

2026-10-14 18:10 ET. **Resolved with the bounded verifier CBMC (Yan-Ru's 13:19 ET decision); the WP half of
two boxes is not met** (below). Branch `probata-poc/t27`. Interface doc:
[`format-v0.4-proof-semantics.md`](../../../docs/reference/format-v0.4-proof-semantics.md).

**What was built**

| Piece | Where |
|---|---|
| Proof semantics 0.1 `semantics.dx100_bfs_0_1` (13 calls, 22 rules, inventory, constants) | `library/proof_semantics/dx100_bfs_0_1.yaml` |
| Ghost state declared once (ACSL), device state, C model (CBMC form), ACSL logic (WP form) | `library/proof_semantics/dx100_bfs/{ghost.acsl,state.h,model.h,logic.acsl}` |
| Entry checks, call inventory, model generation (`model_for`, `covered_names`) | `swdb/proof_semantics.py`, hook in `swdb/formal_frame.py` |
| Generated hazard probes at every tile-pointer access (C lowering) and the same probes on the C++ cut | `swdb/c_lowering.py` (`semantics=`), `swdb/cbmc_adapter.py` (`_probed`) |
| Bounded jobs with the model: ghost init + tile havoc in the harness, model `--unwindset`, `ghost_capacity`, pin and assumptions | `swdb/cbmc_adapter.py`, `swdb/cbmc_translator.py` (`setup`, `state`) |
| DX100 fixture units (15 units, variants by build constant) | `tests/fixtures/proof/dx100/fixture_units.cc` |
| Entry generator (rules, contracts, inventory; rerun after a model edit) | `prototype/27-proof-semantics/gen_entry.py` |

**Acceptance, box by box** (`tests/test_proof_semantics.py`)

- Coverage and citations: met. Version `0.1`, sequence 1, content hash (file sha256 pinned by records). 13 calls,
  one ACSL contract each, all type-checked by Frama-C 33.0 in `swdb validate`. 19 rules cite gem5 DX100 at
  `e4fc4af` (file, lines; files fetched and hashed, `IF.cc` and `IndirectAccess.cc` match the witness record's
  sha256), 3 are assumed with owner Eric (`regions`, `stream_operands`, `store_duplicate_order`). Controls refused: no citation and no owner, a citation at another commit, a call with no contract,
  a call naming an unknown rule, an inventory call with no row, a ghost array declared again in the C model.
- Unready read: met on CBMC. Each early read is refuted at its probe and replays on the C++; `get_tile_size`
  before the wait is refuted (`#unready_size_read`); a CPU write into a tile an uncovered gather reads is refuted
  (`#cpu_write_overlap@dxf_cpu_write.probe2`); the CPU read of that tile proves.
- A probe at every tile-pointer read: met on CBMC (C lowering and C++ cut carry the same three probes; moving
  read N refutes at `dxf_three_reads.probeN`, replayed). **WP not met:** the WP adapter does not yet take the
  proof semantics (contracts for the calls, probes as ACSL assertions). Not run.
- Wait rule as gem5 runs it: met. Prove: store source wait, transitive producer, dispatch stall through a
  condition tile, register write. Refuted: range-loop exception, condition-only wait, unrelated wait.
  "Through register producers" is replaced by F6 (see disagreements).
- Values at issue: met for stream load, gather and range loop (proves; the wrong value is refuted at the
  postcondition).
- Footprints: met. `swdb_dx_in_footprint` is a query over ghost state and the current index tile (no copy);
  member proves, an address past the indices is refuted.
- Ghost capacity: met. 32 uncovered stream loads prove (CBMC 3.2 s); 33 end not proven, `ghost_capacity`, no
  counterexample (`DX_NT=40 DX_TS=1`).
- One ghost state, declared once: met for the declaration (ghost.acsl; the C globals are generated; a second
  declaration is refused). **Agreement not met:** "SAW and WP agree" became "CBMC and WP agree"; WP was not run
  on the fixtures (same reason as above). The C model and the ACSL contracts are two hand-written forms;
  ticket 29 checks them against each other, ticket 30 generates the C form.
- Versioned: met. Every record with a covered call pins `pins.proof_semantics` and lists `proof_semantics` and
  `reduction` (`rocq.probata.dx100_reduction`, sha256 of `Reduction.v`) assumptions. Adding version 0.2
  (sequence 2) makes the 0.1 record stop counting in `swdb candidate-level`.

**Disagreements with ticket 41's Rocq statement (for the main session)**

- **Rocq `covered` lacks two gem5 covers this ticket requires.** 0.1 covers at issue (a command whose dispatch
  stalls on uncovered ones, `IF.cc:193-212`) and at a CPU register write (`IF.cc:233-249`). Rocq's `covered`
  only starts at a wait (`cov_direct`), so its `pending` set is larger and `obl_hazard_free_own` stronger:
  `dx100_reduction` as stated does not back proofs that rely on these two covers (fixtures
  `stall_condition`, `register_write`). Both are already constraints of `timed_run`, so two constructors
  (issue-stall, register-write) should keep the lemma true. Needs ticket 41's re-approval and ticket 43.
- F6 adopted: register overlap with an uncovered command is a hazard, so "a wait covers through register
  producers" (this ticket's text) never arises; 0.1 follows F6.
- F5 (`cov_stall`) is subsumed: 0.1 covers stalled commands eagerly at the issue.
- F2 and the region stall are not in 0.1 (ticket 28), and neither are CPU-versus-DX100 memory overlap hazards
  (`hazard_own` memory clauses). So a 0.1 proof does not discharge all of `obl_hazard_free_own`; 0.1 is a
  working version that 28 supersedes (the ticket's own assumption).

**Assumptions** (not decided in the map)

- Assumption: fixtures and the model use core-subset spellings of the dx100-mmio calls (`int` instantiation,
  every operand explicit, condition `-1` when unused); the templates and default arguments wait for ticket 24.
- Assumption: under CBMC "SAW refutes, WP not proven" reads "CBMC refutes with a C++ replay"; the C++ form is
  the replay and the differential run (ticket 22's translation), with the probes cut into the C++ at the same
  source ranges.
- Assumption: a probe check is tile-granular (any uncovered writer of the tile), a write probe also refuses
  uncovered readers; `&p[i]` counts as a write. A tile pointer used other than `p[i]`, `*p`, `*(p + i)` is
  outside the subset.
- Assumption: proof-semantics contracts are Frama-C type-checked but not held to the formal-half subset (ghost
  state, bitwise operators); they are trusted, never executed by check mode. Range-loop and store contracts
  state weaker (sound) value facts than the C model; ticket 29 compares the forms.
- Assumption: tile contents start havocked from the oracle (part of the bounded domain); sizes and registers 0.
- Assumption: the C lowering (version 2 after ticket 24) and the translator keep their version numbers: their
  output is byte-identical without a proof semantics; records pin both by sha256. The covered calls reach the
  lowering as ticket 24's `summaries` (calls kept, prototype only); probes come from `semantics=`.
- Assumption: `get_tile_ready` is not in the inventory (strict layer only, `#ifdef SWDB_STRICT`); ticket 28.

**Tests** (Mac; serial; pytest outside the lock, each CBMC job takes the lock): `tests/test_proof_semantics.py`
29 cases; full run 25 passed, 2 failed on fixture defects (a wrong-value variant overflowed; the symbolic
capacity bound took over 9 min), both fixed and rerun: 2 passed. After merging the integration tip (2dff3f58;
probes ported onto ticket 24's lowering): `test_proof_semantics.py`, `test_format_doc.py`, `test_formal_frame.py`,
`test_c_lowering.py`, `test_cbmc_adapter.py`, `test_level_rule.py` (`-m "not whole_store"`): **274 passed** in
57 min (most of it waiting for the shared verifier lock). Logs `/tmp/claude/probata-runs/t27/pytest-final3.log`,
report log `report-final3.jsonl`; earlier `pytest-c.log`, `pytest-e.log`. gem5 sources:
`/tmp/claude/probata-runs/t27/gem5/`. Prove jobs in the tests allow an hour for the lock (the default 600 s timed
out once under contention, with CBMC itself at 0.3 s).

**Interface notes**

- 28: supersede with `sequence: 2`; add calls, F2 regions, memory overlap probes (CPU accesses vs
  `swdb_dx_in_footprint`), ownership; extend the inventory roles if new sources come.
- 29: compare `model.h` with the ACSL contracts (`swdb.proof_semantics.acsl_source`) and with 23's stubs.
- 30: generate `model.h`; `model_for` is the consumer (ghost globals already generated from `ghost.acsl`).
- 36: probes are in `settings.proof_semantics.probes` and `Lowering.probes` (id, access, C++ range).
- Rocq: the two missing covers (issue stall, register write) — Rocq statement revised by 41's follow-up.

## Progress (paused)

2026-10-14 22:38 ET. The CBMC half is merged (integration 1672b48a). The WP half is partly done; Status stays
`claimed` (Yan-Ru paused the effort).

- **Done.** `swdb/wp_adapter.py` takes the proof semantics: same lowering (summaries + probes), the WP form at
  `ghost.globals` (`swdb.proof_semantics.wp_prelude`: constants, probe macros calling contracted probe functions,
  `ghost.acsl` as written, `state.h`, `logic.acsl`, the called contracts), `requires dx_idle` and array separation on
  the unit, ghost/device state added to its `assigns`; records pin and assume the semantics as CBMC does. The call
  contracts were rewritten in a per-tile view (`logic.acsl`: `dx_wait_covers`, `dx_stall_covers`, `dx_kept`,
  `dx_new_slot`, `dx_issuable`) with no shifts or masks: Z3, Alt-Ergo and CVC5 time out on constant shift-and-mask
  facts (checked on a 3-line file). New ghost fields `dx_count`, `dx_reg_named`, `dx_reg_a/b/c` (model maintains
  them). Fixture helper `dxf_load` became a macro (WP has no contract for helpers). Generator split:
  `prototype/27-proof-semantics/contracts_wp.py`.
- **WP results** (Frama-C 33.0, 30 s per prover, `/tmp/claude/probata-runs/t27/wp/summary2.txt`): proven
  three_reads 62/62, size, cpu_write, transitive, register_write, value_stream, value_gather, value_range, footprint.
  Every CBMC-refuted variant run so far stays not proven at the probe (or call) CBMC names: early reads 1-3,
  early size, CPU write, range exception, unrelated wait.
- **Open.** (1) store_source_wait and stall_condition: everything proves except the unit's `assigns` against the
  store's set-comprehension `assigns` (2 goals each); next step: give the store contract an index bound the
  provers use (for example `requires` all active indices in `[0, bound)` with `assigns data[0 .. bound - 1]`), or
  a proof hint. (2) condition_wait and the wrong-value / outside-footprint variants were not run to completion.
  (3) The WP tests in `tests/test_proof_semantics.py` (`needs_wp`, sandbox off for Why3) were written but not run
  through `swdb prove` yet; the two store fixtures are left out of `WP_SAFE` until (1).
- (4) Merging the integration tip conflicted with ticket 25's rewrite of `swdb/wp_adapter.py`; the merge keeps
  ticket 25's file, so the WP adapter changes live only in commit `84563b2e` and must be ported onto it (the WP
  tests are marked skip until then). `proof_semantics.wp_prelude` / `wp_locations` and the contracts stay.
- (5) The fixture helper `dxf_load` is a function again: the `DXF_LOAD` macro used for the WP runs breaks the
  CBMC C++ cut (the cut copies function text, not macros). WP needs the helper inlined (ticket 25's adapter adds
  `-inline-calls` for lowered callees; check it covers this).
- **Next step.** Port the adapter changes (4), check (5), fix (1), then run `pytest tests/test_proof_semantics.py -k wp` with the sandbox off, record the
  numbers here, and resolve.

## Resumed implementation — 2026-10-15 02:02 ET

Status remains `claimed`; the WP acceptance is running. Integration branch
`codex/probata-poc-integration`; implementer branch `codex/probata-t27`.

- Restored proof-semantics lowering, call contracts, probes, pins and assumptions in the current WP adapter,
  preserving ticket 25's summary/model interfaces (`8344da11`, then integration merge `3ed49971`).
- Fixed a trusted-contract frame defect: command contracts omitted `dx_reg_a/b/c` even though their C model
  writes those arrays and their postconditions read them. The frame now includes all three (`9b429230`).
- Added every previously excluded WP store/wait fixture and the 32/33 capacity pair. A real Mac WP run proved
  capacity 32 with a checked loop hint set; 33 remained not proven, `timeout` before a named capacity obligation
  was added (`b6bc3009`). The named obligation's new classification still needs its green run.
- Seven entry/citation/Frama-C validation controls passed after the contract edits. The first real mbit10
  diagnostic at `9b429230` passed `three_reads`, `size`, and `cpu_write`; `store_source_wait` timed out on its
  assigns inclusion. That diagnostic was stopped after this red result; it is not a full acceptance run.
- The next store attempt uses a checked assertion that all active index-tile elements are in `[0,n)`
  (`c466499e`). It runs through ticket 36's independent generated-goal inventory, smoke tests and setup check
  (`d9e10634`). Raw output: `/data/yanruj/EvolveSWDB_runs/probata-t27-20261015/store-hint`, tmux
  `probata-t27-hint`, coordinated socket 0. Source is frozen while the run is active.
- Remaining: finish that exact-frame attempt (use a conservative allocation frame if necessary); rerun all
  proof-semantics acceptance and WP regressions on the combined integration; record actual outcomes here.
  The serial portfolio order is now Z3, CVC5, Alt-Ergo (`7378075c`), with the same tools and budgets; the next
  run will test this scheduling choice. No runtime speed claim is established.

2026-10-15 follow-up: the checked index assertion proved, but the exact indirect frame still timed out
(74/76 generated goals valid, two assigns goals not proven). The next form uses a checked ghost frame
witness `dx_store_bound = n` and a named obligation that every selected store index lies within it. The
unit's original formal half is unchanged; the store frame is conservatively `data[0 .. dx_store_bound-1]`.
The proof-only scalar is declared once in `ghost.acsl`; the C model ignores it. Its insufficient-bound
control and safe fixtures remain pending. Also closed a generated-model validity gap: overriding `DX_K`
outside `1..32` is refused before any tool, consistent with the 32-bit slot masks. All four public controls
(0/33, CBMC/WP), including disabled tool executables, pass; Frama-C validates the updated entry and contracts.


## Soundness and acceptance checkpoint — 2026-10-15 04:06 ET

Status remains `claimed`; full acceptance must use the combined initializedness and memory policies.
The earlier remote `branchless` run at `dd975e72` passed all six targeted cases in 3291.80 s: both store
fixtures, three reads, the insufficient store-frame witness, and capacity 32/33. Its scope is the prior
method and declared model, not the current final acceptance or a hardware timing claim. Raw outputs remain
at `/data/yanruj/EvolveSWDB_runs/probata-t27-20261015/branchless` on mbit10.

- Store frames now use the checked `dx_store_bound` witness and selected-index obligation, preserving the
  original unit frame. DX_K outside 1..32 is rejected before tools; capacity 32/33 also passed the strict
  reader on Mac (2 cases, 571.32 s).
- Added conservative ordinary CPU effect admission from clang AST identities, including macro-expanded
  accesses. CPU writes and opaque effects are refused; reads after a device store require the later memory
  model. Prefix reads have checked intraprocedural statement ordering. Transitive summary/model proof
  dependencies cannot hide accelerator semantics behind a scalar summary boundary (`21fa9b2d`).
- Added checked device-memory serialization after destination-stall coverage and no pending store at unit
  exit, before formal poststate observations (`ca438d12`). Pending reads remain explicit state and require
  caller hazard/lifetime handling. A source-derived cache-line interference concern motivates this domain;
  no gem5 lost-update replay is claimed. Dedicated `memory_domain` failures never refute the program.
- Red controls reproduced old-model success for uncovered store/store overlap and store-return without
  wait. After the changes, all six bounded domain/exit cases plus the safe CBMC regression passed (7 cases,
  240.30 s). Explicit initialized fixture inputs reproduced an unsupported translation; the narrow
  harness-owned-buffer translation now passes its real bounded control. Three focused translator/dependency
  controls pass. The real WP size fixture passed with mandatory initializedness (217.80 s); the public
  once-proven-wrapper/caller boundary control passed.
- Remaining: finish the frozen focused batch, add local-storage lifetime admission controls, merge the
  audited bounded-initialization gate and current terminal checker, freeze method draft 3, then run complete
  coordinated remote safe/unsafe acceptance and update this ticket with final evidence.

## Initialized-state acceptance checkpoint — 2026-10-15 06:26 ET

Status remains `claimed`; final remote acceptance has not launched. The combined mandatory
initializedness policy exposed receiver-slot and device-state proof obligations that earlier acceptance
had not checked. The production repair at `3b092a46` names the fixed device-storage initialization
invariant, preserves it in the explicitly trusted device call contracts, and checks selected caller-memory
reads with `source_initialized` preconditions. This does not assume caller inputs initialized. Imported
nonnull tile-pointer and integer/bool call results use an equivalent `+0` receiver expression for Frama-C
33's modular-call initialization handling; arbitrary nullable pointers and floating results are excluded.
The bounded/native model body is unchanged by this repair. Independent contract/body agreement remains
in ticket 29's scope.

- An actual public negative control removed only the caller-buffer initializedness premise while retaining
  validity and observing only device size. The earlier setup proved it; the repaired setup returns
  `not_proven` on the named `maa_stream_load_requires_source_initialized` obligation. This control passed
  in three retained combined-policy runs, most recently the 06:14 run below.
- The repaired three-read unit now proves its receiver and memory-access RTE goals, but three checked
  `swdb_tile_read_probe_requires_initialized_read` preconditions still time out. Distinct WP static tile
  objects from ticket 36 preserve row bounds; they do not resolve these three initialization obligations.
- A finite expansion of the recognized initialization predicate (`880e006c`) typechecks (7 controls,
  5.13 s), but the actual public pair still reports one pass and one failure in 582.33 s: the caller-input
  negative passes and the safe three-read case retains those exact three timeouts. Raw outputs are at
  `/private/tmp/probata-t27-init-finite-green`; its source is pinned to `880e006c`.
- A separate prospective `-wp-no-filter-init` diagnostic is queued under the shared machine verifier lock
  and 8 GiB RSS cap using that exact retained generated C input. It has no frozen-method proof record and
  is not final acceptance. Root and ticket 25 are checking the same default WP initialization-hypothesis
  filtering behavior against positive, wrong-postcondition, missing-validity and smoke controls before
  choosing a prospective method flag. No running source or frozen method was changed.

Remaining: settle the initialization proof policy with actual safe and negative records, merge the final
pointer/model changes, freeze the combined method, then run the source-pinned safe and unsafe mbit10
shards. Node 1 must be handed back for the complete constructs module after its unsafe shard finishes.


2026-10-15 06:35 ET diagnostic result: on the identical retained generated input, adding only the
prospective `-wp-no-filter-init` switch passes the unchanged strict reader: 100 ordinary obligations and
31 smoke checks, 131 generated and 131 reported, no unproven goal (234.41 s; 913,555,456-byte peak RSS).
A second copy with the finite entry/postcondition consequences removed also passes all 131 obligations
(228.63 s; 889,798,656-byte peak). Raw reports, generated-goal inventories, source, exact commands and
strict-reading results remain in `/private/tmp/probata-t27-init-nofilter` and
`/private/tmp/probata-t27-init-nofilter-minimal`. These are prospective raw diagnostics, not frozen-method
proof records. The finite expansion is therefore removed; the named initialization invariant, checked
selected caller-memory initialization, and exact receiver normalization remain. The public CLI safe/negative
pair and final combined remote acceptance still need the prospectively pinned filter policy.

2026-10-15 06:43 ET public CLI checkpoint: the safe three-read unit and uninitialized-caller-input control
both pass their test expectations at `2d2d12e6` (2 cases, 338.00 s). The safe record is `proven`: 100 ordinary
goals and 31 smoke checks pass; the initialization-negative record is `not_proven`: 35 ordinary goals and
15 smoke checks pass, with the single named `maa_stream_load_requires_source_initialized` goal timing out.
Both setup checks pass and both use verdict-reader hash
`597851262253a38e35ac6211eb5a89594c535fb3e98d0f3d64366e5aa28666df`. The safe WP process took 225.13 s and
892,190,720-byte peak RSS. The method explicitly includes `-rte-initialized @all`, `-wp-no-filter-init`,
`-wp-smoke-tests`, cache `none`, and the Z3/CVC5/Alt-Ergo serial portfolio. Raw records/reports remain under
`/private/tmp/probata-t27-init-public-nofilter`, with report log at the matching `.jsonl` path.

The finite expansion is absent. Final acceptance is still pending the combined ticket-36 pointer-origin
admission update and prospective final method pin; this local checkpoint does not resolve ticket 27 or
substitute for the coordinated remote safe/unsafe shards.

The merged setup/strict-reader controls also pass (63 scripted cases, 102.29 s; real WP fact cases excluded),
including initialization-filter override refusal and the combined pointer/ownership checker-source closure.
Report log: `/private/tmp/probata-t27-merged-setup.jsonl`. The unfinished member-contract acceptance module
from the policy donor branch remains with ticket 25 rather than being copied into this ticket's handoff.

## Checked DX100 input-window frontier — 2026-10-15 07:44 ET

Status remains `claimed`. The prior initializedness checkpoint does not establish typed array origins at
opaque device calls. A unit declaration such as `q: n` is an explicit formal input-window addition; it is
not inferred from `\valid`, initializedness, a larger backing allocation or the accelerator register state.

- `ea1c75b0` adds the scoped `dx_array_domains` checker and a proof-semantics policy factory. Eligibility
  requires the exact audited C/ghost/state components, current entry and generated model hashes, geometry
  and checker identity. It supports the host-pointer footprints of stream load, indirect load and vector
  store. A checked assertion reads the call-prestate register range/stride or unsigned index-tile values
  and requires every selected address, including the actual pointer offset, to lie in the frozen input
  window. It adds no requires or assumptions. Unknown call forms, operand effects, incomplete origins and
  unsupported placement remain refused.
- The first checker accepts only certified entry-window origins. It never defaults a missing offset to
  zero for aliases, concrete arrays or semantic rows. Only an individually validated imported call AST node
  can be exempted from pointer-binding escape invalidation; source definitions and other calls remain
  closed. Ticket 36 owns the lowering, placement, complete-inventory and fresh source/policy replay hooks.
- Seventeen component controls pass in 0.88 s, including real Clang call ASTs, stale component pins, missing
  or wrong origins, operand effects, capture-free quantifiers, geometry changes and Frama-C typechecking
  of the generated guards. Report: `/private/tmp/probata-dx-call-component.jsonl`. These are component
  checks, not end-to-end proof acceptance.
- `d7d5aa66` and `8201b783` add separately named direct stream, three-read and offset-gather fixtures with
  explicit input windows. The original `dxf_load` helper fixture is retained; top-level metadata does not
  invent a helper entry domain. The direct three-read frontier observes three tile values and consistency,
  and does not replace the original functional-observation fixture. Additional controls keep a larger valid
  memory range from rescuing a smaller advertised window, reject a gather read through a legal one-past
  offset and retain the independent initialized-input obligation. The WP capacity test explicitly adds its
  `q: n` declaration in that contract fork.
- The public direct-stream positive is RED at the expected old factory boundary (51.36 s): the declaration
  is refused before WP because the source-origin call certificate is not integrated yet. Report:
  `/private/tmp/probata-dx-domain-public-red.jsonl`. Seven new frontier cases collect. No real WP job was
  launched for this RED control, and no new model body was substituted into a running evaluation.

Remaining: integrate ticket 36's exact call-site/placement and fresh-replay hooks, run the public frontier
and capacity controls with the real WP adapter under the shared lock, review the combined source, then
freeze the next method before coordinated remote acceptance. Existing native agreement remains separate
from this pending proof-admission frontier.

After merging reviewed entry/owner integration `7e15176f` into this branch, the same direct-stream control
is RED at the next prelaunch boundary (64.68 s): `unsupported_construct`, `verifier_launched: false`, with
an unstable entry binding caused by the not-yet-audited device pointer call. No WP log is produced. Report:
`/private/tmp/probata-dx-domain-call-red.jsonl`. An additional pending control fixes the entry window at
n==2, grows the call-state end register to three, and supplies a larger valid/initialized physical range;
its checked stream footprint must still reject the third cell. Eight frontier controls now collect.

## Transparent helper-view component checkpoint — 2026-10-15 ET

Status remains `claimed`. `helper_windows.prepare` / `check_view` add a checked C++ view for main-file,
global, acyclic void helpers with plain `int` / `int *` formals and straight-line imported calls. Each
standalone helper call in a braced unit context becomes a fresh block of by-value actual captures and the
original ordered calls. Nested helpers get separate captures per context. Pointer captures retain the bare
caller binding so the existing origin checker can trace them to the original unit window; no helper entry
window, requires clause or assumption is synthesized. Source outside replaced call statements is preserved,
including physical newline counts. Model callees use global qualification to prevent caller-local capture.

The trusted transformation boundary is explicit in the recorded assumption and checker/certificate pins.
A separately parsed complete Clang AST must match every unchanged unit operation, each typed capture,
original helper operation, declaration binding and call order. Residual reachable helper calls, recursion,
annotations, effects or arithmetic in helper operands, unsupported placement, function-pointer calls,
attributes, exception specifications and imported names with source definitions are refused. The certificate
pins full preprocessor dependencies (including macro-only headers), source/view bytes, imports, tool version,
parse implementation and contexts. Immediately before use, `check_view` rereads the actual view and reparses
both source and view; changed source, headers, imports or certificate are refused.

The 32 component controls pass in 6.31 s. They include the original `dxf_store_exit` fixture with both
`dxf_load` contexts expanded, branch/nested contexts, later invalid callers, a deliberately broken generator
caught by independent AST checking, and native original/view traces with the same ordered device calls and
actual values before/after changing n. Report: `/private/tmp/probata-helper-windows-component.jsonl`.
These are transformation checks, not WP or final proof acceptance. Ticket 36 still owns the adapter's
original/view provenance split, fresh prelaunch source/lowering replays and the ordinary checked window
assertions on the resulting view. Hints remain closed for this slice. The original three-read fixture also
contains nested ordinary memory operands, which remain a separate unsupported frontier.

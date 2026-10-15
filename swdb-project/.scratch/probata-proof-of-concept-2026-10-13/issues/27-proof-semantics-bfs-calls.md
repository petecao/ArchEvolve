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

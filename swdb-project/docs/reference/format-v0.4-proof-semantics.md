# The DX100 proof semantics (entries, checks, bounded jobs)

Created: 2026-10-14 ET, Probata proof of concept ticket 27. Updated: 2026-10-15 ET.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/27-proof-semantics-bfs-calls.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("DX100 proof semantics"), map 12 items 1-5 and 11, map 14
(the wait rule), map 16 item 10 (one ghost state), S3 (ghost capacity). Rocq: `library/rocq/probata/Reduction.v`.
Code: `swdb/proof_semantics.py`; hooks in `swdb/formal_frame.py`, `swdb/c_lowering.py` (probes),
`swdb/cbmc_adapter.py` and `swdb/cbmc_translator.py` (the bounded job). Tests: `tests/test_proof_semantics.py`.
Ordinary-memory admission: `swdb/cpu_effects.py`, `swdb/cpu_memory_admission.py`;
controls: `tests/test_proof_semantics_admission.py`.

**In one line:** a proof that calls DX100 trusts one versioned proof semantics: one ACSL contract and one C
model per call, values as if each command finished at issue, and a hazard check (a generated probe) at every
tile-pointer read and write; every proof record pins the version.

## The entry (`library/proof_semantics/<name>.yaml`, kind `proof_semantics`)

Ticket 20's fields (`formal_frame: 1`, `version`, `rules`, empty `clauses`) plus, for an entry that covers calls:

| Field | Meaning |
|---|---|
| `sequence`, `target` | The version line: the current version of a target has the highest sequence. A record that pins any other version stops counting (`swdb.level_rule.current_versions`, file sha256). |
| `hardware_interface` | `{id, version, gem5_commit}`: `dx100-mmio`, `1.0-e4fc4af`, the full commit. Every `rules[].cites.gem5_commit` must be a prefix (7+ digits) of it. |
| `constants` | Default build constants of the model: `DX_K` (command slots, K = 32), `DX_NT` tiles, `DX_NR` registers, `DX_NM` regions, `DX_TS` tile size. `--define NAME=VALUE` overrides one. |
| `inventory` | `{read, sources, calls}`: the pinned sources the call list was read from (roles `lowerings`, `offload`, `setup`, `function`) and the calls found. A changed source fails its pin: reopen the inventory. |
| `ghost.acsl` | Pinned ACSL file: the ghost state, declared once (`ghost <type> <name>[...];` lines). |
| `model` | Pinned `state` (device state, C), `c` (the C model, the CBMC form) and `logic` (ACSL logic for the contracts). |
| `calls` | One row per covered call: `call`, `prototype` (core-subset C), `contract` (ACSL), `rules` (rule IDs), `lowerings`, `used_by`. |
| `queries` | Ghost queries a fixture may call (not hardware calls): `query`, `prototype`, `contract`. |

### What `swdb validate` refuses

- a rule with neither `cites` nor `assumed: {owner}` (ticket 20), or a citation at another gem5 commit;
- a listed call with no contract or no prototype; a call naming a rule the entry does not hold;
- an inventory call with no call row; a moved or edited inventory source (pin);
- a ghost array declared again in `state.h` or `model.h` (declared once, in `ghost.acsl`);
- a contract, logic or ghost declaration Frama-C 33.0 refuses (parse and type check, no WP). Without
  Frama-C the contracts are reported `UNCHECKED`, never valid.

Proof-semantics contracts are type-checked, not held to the formal-half subset: they use ghost state and bitwise
operators, and they are trusted (an assumption entry), never executed by check mode.

## Version 0.1 (`semantics.dx100_bfs_0_1`)

- **Calls (13):** `maa_const`, `maa_stream_load`, `maa_indirect_load`, `maa_range_loop`, `maa_alu_scalar` (LT
  only), `maa_indirect_store_vector`, `wait_ready`, `get_tile_size`, `get_cacheable_tile_pointer`,
  `get_new_tile`, `get_new_reg`, `add_mem_region`, `clear_mem_region`. `get_tile_ready` is strict-layer only.
- **Core-subset spellings:** the `int` instantiation, every operand explicit (condition `-1` when unused).
  The templates and default arguments of `MAA_gem5.hpp` wait for ticket 24.
- **Coverage:** `wait_ready(t)` covers every uncovered command naming t as src1, src2, dst1 or dst2, then the
  producers of their input tiles, never through a range loop. Issuing a command first covers every uncovered
  command naming its destination tile in any role (the dispatch stall). `maa_const` first covers every uncovered
  command naming its register.
- **Hazards (named checks):** `#unready_read@<probe>`, `#cpu_write_overlap@<probe>`, `#unready_size_read`,
  `#register_overlap` (F6), the operand rules; `swdb.ghost_capacity` (more than K uncovered commands).
- **Not in 0.1 (ticket 28):** permissive CPU/device and device/device memory overlap, the region stall and unregistered accesses (F2),
  tile ownership as an obligation, conditions on loads and ALU commands, other ALU operations.

### Checked memory domain until ticket 28

An indirect store copies a whole line, changes selected words, and emits a whole-line `WritebackDirty`
(`IndirectAccess.cc:898-940,1145-1158` at `e4fc4af`). Consequently, disjoint selected elements do not establish
absence of interference. This is a source-derived reason for conservative admission; no gem5 replay of a
lost-update schedule is claimed here. `dx_in_footprint` remains a selected-element query, not a cache-line
interference proof.

- A compiler-owned inventory covers every lowered function, ordinary memory read/write, atomic operation,
  modeled call and opaque summary. Both adapters reject ordinary CPU writes and opaque effects before a
  verifier runs, including writes after a wait. Tile accesses already covered by generated probes keep their
  existing hazard checks. The anchors report retains the inventory; collector and admission-policy source
  participate in the C lowering tool hash, alongside the separately pinned input source.
- For a unit with a device store, ordinary CPU reads must be in its acyclic prefix before every store-issue
  top-level statement. Reads in a callee, a loop-containing unit or the same statement as a store are refused.
  This admits the fixture's `old0` read before issue and rejects an ordinary read after issue, even after a wait.
- A once-proven summary or C model cannot hide this boundary. Both adapters traverse the selected proof
  records through summary and model dependencies. Any inherited accelerator semantics makes that opaque
  call `not_proven / memory_domain` until its contract encodes a checked pending-command and ownership
  boundary. Missing or unclassified dependency records also fail closed.
- Device commands have a separate checked domain: after destination-stall coverage, a store requires no
  uncovered memory command, and a load requires no uncovered store. The bounded model checks live slots;
  WP checks the named `memory_domain` precondition using a conservative direct-stall predicate. Extra
  transitive coverage may leave a safe unit not proven. No no-interference premise is assumed.
- Both adapters check that no device store remains pending at unit exit, before formal poststate observations.
  WP adds the named `memory_domain_exit` postcondition; the bounded harness checks all live slots after the
  unit call. Pending reads remain explicit state for the capacity case; callers still need hazard and lifetime
  checks when composing such units. This boundary is checked, never an assumed no-interference premise.
- A checked domain failure ends `not_proven / memory_domain`, without a counterexample. WP retains
  every failing obligation and never refutes. Ticket 28 can replace these restrictions with checked overlap
  rules and ordinary-memory probes; these restrictions do not claim its full memory model is implemented.

Native agreement and replay use the explicit flat 64-bit `uintptr_t` data-address ABI of the
selected Clang target (x86_64 on mbit10; AArch64 on the Mac), with 32-bit `int`; compilation checks the
widths, and records state the platform premise. Queries compare unsigned aligned element-address
ordinals, never unrelated C/C++ pointers. CBMC retains allocation-object and offset guards. This avoids
undefined cross-object pointer subtraction; C and C++ query controls also run address, invalid-pointer-pair
and undefined-behavior sanitizers. The intermediate spelling with direct `uintptr_t` subtraction was
defined arithmetic but triggered the sanitizer's pointer-subtraction heuristic; the ordinal spelling
retains exact remainder and range checks without disabling a sanitizer.

## Bounded jobs (`swdb prove --adapter cbmc`)

- The covered calls and queries reach the C lowering as ticket 24's `summaries` (each call kept, prototype
  only; `swdb.proof_semantics.lowering_options`), and the lowering puts a probe at every element access through
  a tile pointer: `(*SWDB_TILE_READ(&(p[i]), "<function>.probe<N>"))` (writes: `SWDB_TILE_WRITE`). A tile pointer
  used any other way is outside the subset. The C++ cut gets the same probes at the same source ranges.
- `job.c` = harness prelude, the generated model (constants, `DX_RULE`, ghost globals from `ghost.acsl`,
  `state.h`, `model.h`), the C lowering, the harness. The harness runs `swdb_dx_init()` and draws every tile
  element from the oracle (havoc) before the unit runs.
- The model's loops get their own unwinding bound (`--unwindset`, from `cbmc --show-loops`).
- A `DX_K` override outside `1..32` is rejected before any verifier: command masks have 32 bits. Other
  recorded shape constants still support the synthetic capacity fixtures (`DX_NT=40`, `DX_TS=1`).
- A failed `swdb.ghost_capacity` ends **not proven, `ghost_capacity`**, never refuted.
- The record pins `pins.proof_semantics` `{id, sha256}` and lists two assumption entries: `proof_semantics`
  (the entry) and `reduction` (`rocq.probata.dx100_reduction`, sha256 of `Reduction.v`; proof: ticket 43).
  `settings.proof_semantics` names the entry, the calls and every probe.

## Unbounded jobs (`swdb prove --adapter wp`)

- The same C lowering (same summaries, same probes). At `ghost.globals` WP gets the WP form
  (`swdb.proof_semantics.wp_prelude`): the size constants; the probe macros, each a call of a contracted probe
  function (`wp.probes`: `swdb_tile_read_probe` requires `dx_read_ok`, `swdb_tile_write_probe` requires
  `dx_write_ok`); `ghost.acsl` as written inside one `/*@ ghost ... */` block; `state.h`; `logic.acsl`; and the
  contract of every call and query the unit makes.
- The unit's contract gets `requires dx_idle` (the ghost state g0, as CBMC's `swdb_dx_init`), one
  `\base_addr` separation per pointer parameter and device array (`wp.separate_from`), and the ghost and device
  state in every `assigns` clause (`swdb.proof_semantics.wp_locations`). These generated initial-state and
  separation premises are listed in `settings.proof_semantics.unit_requires` and in an `assumed_clause` record
  entry, making the proof model's domain explicit alongside the original formal half. Each call
  separately proves its operand and separation preconditions.
- The WP contracts state a per-tile view (`dx_wait_covers`, `dx_stall_covers`, `dx_kept`, `dx_new_slot`,
  `dx_issuable` in `logic.acsl`): consequences of the C model, with no shifts or masks for the provers (Z3,
  Alt-Ergo and CVC5 time out on constant shift-and-mask facts). The transitive clause of a wait names tiles
  0-7 one by one; with more tiles it claims less, never more.
- The store's WP frame is `data[0 .. dx_store_bound - 1]`. The proof-only ghost scalar `dx_store_bound`
  is a caller-selected frame witness: a checked ghost hint sets it, and the call requires every selected index
  to be within it. Calls preserve this scalar; a caller loop that changes it must include it in `loop assigns`,
  checked by WP. It changes no device values or hazards; the bounded C model ignores it. The fixtures set
  it to `n`, keeping their original `assigns p[0 .. n - 1]` contracts. An insufficient witness leaves a named
  `store_indices` precondition unproved. This avoids WP's incomplete treatment of indirect assigns sets.
  Command frames include all three register-index arrays (`dx_reg_a`, `dx_reg_b`, `dx_reg_c`) that the C model writes.
- A probe that WP cannot prove leaves the unit not proven; WP never refutes. Records pin and assume the proof
  semantics as the CBMC adapter does. The capacity fixture supplies loop invariants through the checked hint
  interface: 32 uncovered commands prove; an unproved named capacity precondition ends not proven with
  failure class `ghost_capacity`, without a counterexample.

## For later tickets

- 28: the remaining calls and rules; supersede 0.1 with `sequence: 2`.
- 29: three-form agreement (ACSL contracts, C model, C stubs) and the semantics negative controls.
- 30: generate the C model from the one source; this version's `model.h` is hand-written.
- 36: check that every tile-pointer access has a generator-made probe (`settings.proof_semantics.probes`).

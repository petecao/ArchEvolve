# Probata Rocq development: review guide and hypothesis table

Created: 2026-10-14 ET (ticket 41). Updated: 2026-10-14 21:30 ET (`Reduction.v` revised by the
main session under Yan-Ru's delegation: two covers from ticket 27, see "Later change: ticket 27
covers"); 2026-10-14 14:35 ET (revision after Codex's review and the main session's decisions
under Yan-Ru's delegation).

## One-page summary (read this first)

**What this is.** Two statements, in Rocq, that the rest of Probata leans on. No proofs yet:
tickets 42 and 43 write them, and Rocq will check every step.

**1. Parallel composition theorem** (`parallel_composition`, [`Composition.v`](Composition.v)).
WP proves one thread t of N at a time. This theorem says why that is enough. If each thread:

- touches each array only as its sharing class allows (read-only, owned, shared actions only,
  or inside `critical`);
- owns memory, tiles and registers no other thread owns at the same time;
- makes each `critical` section one shared action on one location;
- splits work by thread id so every iteration runs once;
- reaches the same barriers and worksharing loops as every other thread;
- runs in a team of exactly N threads;
- lets a DX100 command stay unfinished past a barrier only if it wrote nothing anyone reads;

then **every finished run has a serial twin**: each thread does exactly the same steps, barrier
intervals and critical sections happen one after another, every read outside a
shared-actions-only array sees the latest write, and the final memory is the same.

It trusts three things, each one assumption entry: the compiler and ISA implement RC11 (with
`__sync_*` builtins as full barriers); the OpenMP 5.2 runtime keeps its promises; and DX100 reads
behave as the DX100 proof semantics says.

**2. DX100 reduction lemma** (`dx100_reduction`, [`Reduction.v`](Reduction.v)). Proofs pretend each
DX100 command finishes the moment it is issued. This lemma says the pretense is safe. If the
command contracts are well formed, and no hazard occurs in the pretend world, then every timing
gem5 allows ends with the same observations and the same memory as the pretend world.
A command stops being "pending" in the pretend world at the first step that gem5 holds until
it has finished: a wait that covers it, the issue of a later command its dispatch stalls on, or
a CPU write of a register it names.

**What the review decides.** Whether these two statements say the right thing. Approval is
recorded with the files' sha256 in ticket 41; any later change needs a new approval.

**Open item carried to ticket 43 (M6).** The reduction lemma orders CPU steps in one global
sequence; the composition theorem uses RC11. Ticket 43 must show why this split is sound:
either issues and waits act as fences in the CPU model, or hazard freedom makes DX100 timing
unobservable under RC11.

## What you review (and what you do not)

- **Review:** `Vocabulary.v` (5 shared-action kinds, 4 sharing classes), `Composition.v`,
  `Reduction.v`. About 5 + 4 printed pages: every definition stays explicit (F3).
- **Do not review:** proofs (none yet), [`Sanity.v`](Sanity.v) and [`negative/`](negative/)
  (machine checks, results at the end).

## Hypothesis table: `parallel_composition`

Each hypothesis is one per-candidate WP obligation **or** one assumption entry, never both.
A WP obligation for a candidate is named after the hypothesis it discharges (16 item 4).

| Rocq name | Kind | Discharged by | Plain sentence |
|---|---|---|---|
| `obl_class_fit` | per-candidate WP obligation | WP, one symbolic thread t | Whenever the other threads' accesses fit their sharing classes, thread t's accesses fit theirs too (race freedom, 15 item 2). Inside `critical`, no shared-actions-only location is touched. |
| `obl_owned_disjoint` | per-candidate WP obligation | WP, two-copy product | No location (owned range, tile or register) is owned by two threads in the same barrier interval (15 item 2). |
| `obl_atomic_blocks` | per-candidate WP obligation | WP, one symbolic thread t | Each critical section names one shared action (kind, argument, location), reads that location first, writes only it, leaves the action's result there, and holds no barrier (15 item 2). |
| `obl_chunk_cover` | per-candidate WP obligation | WP (arithmetic over t and N, plus thread t's loop) | Chunk splits computed from the thread id cover each loop's iteration space exactly once, and thread t runs exactly its chunk (15 items 2, 4). |
| `obl_uniform_control` | per-candidate WP obligation | WP, two-copy product (GPUVerify style) | Any two threads reach the same barriers and worksharing constructs in the same order (15 item 6). |
| `obl_team_size` | per-candidate WP obligation | WP over the run-time guard | The team has exactly N threads (15 item 4; 11's guard). |
| `obl_dx100_quiet` | per-candidate WP obligation | WP over the ghost hazard state | No own CPU access conflicts with a DX100 command before a wait covers it; a command may stay uncovered past a barrier or a critical exit only if it writes only tile elements that are dead there (F1, refined). |
| `memory_ok` (premise; uses `hb_cpu`) | assumption entry, **platform choice** | "The pinned compiler and ISA implement RC11, and each `__sync_*` builtin is a fully fenced read-modify-write" (15 item 3; 26 item 4; M1). Stronger than C++ seq_cst RMWs; stated as such. | Reads are history reads over program order and the fenced-atomic order; an atomic read-modify-write reads the latest write; a failed CAS writes nothing. |
| `omp_ok` (premise; its first clause uses `hb` with `omp_sync`) | assumption entry, **trusted tool** | "The pinned OpenMP runtime implements OpenMP 5.2" (15 item 4) | Barrier and `critical` order memory; thread ids are 0 to N-1; a barrier waits for all threads; `critical` excludes other threads; `omp for` gives each iteration to exactly one thread. |
| `device_ok` (premise; uses `hb`) | assumption entry, **proof semantics** | The pinned DX100 proof-semantics version (12 items 4, 7) | A DX100 read returns a value the location held while the command ran, never older than the stores made before issue. |

**Not hypotheses: the subject of the theorem.** `program_run X` and `complete X` say what
"every run" ranges over: X is a finished run of the thread-indexed program.

**Lowering obligation outside Rocq: `cover_sound` (open, ticket 45).** The per-thread lowering
must relate each thread's composition trace to its at-issue run: command id c = the command's
issue position; the `DeviceRead c`/`DeviceWrite c` events are exactly the command's footprint;
`DeviceCovered c` sits only where `Reduction.covered` covers command c; DX100 read values reach
the thread only through the command's outputs; `Shared`'s `fence` flag and kind match the code.
WP checks the ghost parts; the formal bridge lemma is not written yet (Codex round-2 finding
2). The composition model has no waits, so Rocq cannot state it there.

**Validity conditions of the premises.** `omp_ok` holds only for programs with uniform control
(OpenMP leaves divergent barriers undefined); `obl_uniform_control` supplies that. `device_ok`'s
bound "before the wait that covers it" relies on `cover_sound` and the reduction lemma.

## Hypothesis table: `dx100_reduction`

| Rocq name | Kind | Discharged by | Plain sentence |
|---|---|---|---|
| `contracts_ok` (premise) | assumption entry, **proof semantics** | The pinned DX100 proof-semantics version (12 item 1) | Each command's writes depend only on what it reads; a command that writes memory says so; the tile and register elements it touches lie in the tiles and registers it names. |
| `obl_hazard_free_own` | per-candidate WP obligation | WP over the ghost hazard state, one thread | A core never reads what its own pending command writes, never writes what its pending command reads or writes, uses only its own tiles and registers, keeps DX100 memory accesses inside the registered regions the command names (F2), and never runs a command that shares a register with a pending one where either writes (F6) (12 items 3-5). |
| `obl_hazard_free_cross` | per-candidate WP obligation | WP, two-copy product | A core never touches what another core's pending command writes, nor writes a tile another core's pending command reads (12 item 4). |

**Not hypotheses: the subject.** `timed_run T` and `complete_timed T` say what "every timing
gem5 allows" ranges over. Each clause cites the gem5 source it models (research 14 at
`e4fc4af`), so it needs no sign-off beyond the citation (12 item 11).

**Linked assumption entry.** "One DX100 instance" (12 item 7) is built into `timed_run`: all
cores share one instruction file, so the stalls compare every core's unfinished commands.

## Modeling choices (all accepted by the main session, 2026-10-14 14:12 ET)

| # | Choice |
|---|---|
| M1 | `memory_ok` renders RC11 with one global order that agrees with each location's modification order. A `__sync_*` builtin is a full barrier (`sync_fence`); a relaxed atomic (plain `omp atomic`) is not (`fence = false`). |
| M2 | In the composition model, a DX100 command's reads and writes sit at its issue. A DX100 read may still return a value another thread writes later, until a wait covers the command. |
| M3 | A critical section implements one shared action on one location. Multi-location critical sections (the authors' batch store in `TDStepMAA`) do not meet `obl_atomic_blocks`. |
| M4 | A CAS loop (min-update) appears as one `Shared MinUpdate` event, emitted only with WP's proof that the loop implements the kind. |
| M5 | Worksharing constructs are numbered in the order a thread reaches them; each has a fixed iteration space. |
| M6 | The reduction lemma orders CPU steps in one global sequence. **Flag: open obligation for ticket 43** (see the summary). |
| M7 | A command reads each element at some time while it runs, and writes all its results at one step. |
| M8 | 8-byte operands (tiles t and t+1) are not modeled; no proof-of-concept kernel uses them. |
| M9 | The theorem ends at "a serial order of the shared actions"; the contract's order-independence lemma joins it through proof-record dependencies. |
| M10 | Other threads' DX100 commands are history reads plus the owned and lock-protected classes, not a sixth shared-action kind. |

## Findings and their decisions

- **F1 (accepted, refined).** A command may stay uncovered past a barrier, or past the exit of
  a critical section it was issued in, only if it writes tile elements only and those are dead
  there: not read again before a later command overwrites them. The main session's wording
  said "before a covered overwrite"; this uses "before a later command's overwrite", because
  gem5's WAW dispatch stall (`IF.cc:193-212`) already finishes the old command before the
  overwriting one dispatches, and the overwriting commands in both candidates are themselves
  covered only later. Candidate check below.
- **F2 (accepted).** A DX100 memory access outside some registered region holding it, or in no
  registered region, is a hazard. `in_region` is a relation; no disjointness is assumed
  (`TDStepMAA` uses bases `queue.shared` and `queue.shared + min` in one registered region,
  `bfs.cc:147,163,230`).
- **F3 (accepted).** Length about 5 + 4 pages; every definition stays explicit; this summary
  added.
- **F4 (provenance).** Drafted by Claude (`claude-opus-5-5`, Claude Code subagent). Reviewed
  adversarially by Codex (`gpt-5.6-sol`, effort `xhigh`, read-only), twice. The proofs (42, 43)
  stay Codex's.
- **F6 (new, from Codex round 2).** DX100 commands write registers (the range loop advances its
  cursor registers). No cited gem5 rule orders device against device on a register, so two
  pending commands sharing a register where either writes is a hazard. Both candidates wait on
  tile7 before the next range loop (`bfs_read_offload.inc:37`, `bfs.cc:165`), so they meet it.
  If research finds gem5 orders register dependencies, this hazard can become a stall.
- **F5 (new, from the candidate check).** The proof semantics' coverage rule needed a third
  case (`cov_stall`): a covered command also covers every earlier command that would have
  stalled its dispatch (`IF.cc:193-219`). Without it, `TDStepMAA`'s stream load `bfs.cc:147`
  never counts as covered, and the CPU read of tile0 at `bfs.cc:191` would be an unready-read
  hazard although gem5 orders it.

### F1 check on both candidates

**Peter's read offload** (`library/dx100/bfs_read_offload.inc`). Commands: `:30` stream load to
tile0; `:31`, `:32` gathers to tile1, tile2; `:36` range loop to tile6, tile7; `:39` gather to
tile0; `:40` to tile3; `:41` gather of `parent` to tile5. Waits `:37` (tile7), `:42` (tile3,
tile5). Coverage: `:37` covers `:36`; `:42` covers `:40`, `:41`, then `:39` (producer of `:41`'s
index), `:36` (producer of `:39`), and by `cov_stall` `:30`, `:31`, `:32` (`:39` writes tile0).
On the empty-chunk path (`:38`, `count == 0`) `:30`-`:32` stay uncovered and may reach the
region's implicit barrier after `:67`. They write tiles only, and tiles 0-2 are next read only
after the next chunk's (or next call's) `:30`-`:32` overwrite them. Own conflicts: the CPU reads
tiles at `:43`-`:46` and CASes `parent` at `:47` only after `:42`. No critical section.
**Result: meets the refined rule.**

**Authors' `TDStepMAA`** (`apps/dx100/benchmarks/gapbs/src/bfs.cc`). Commands: `:147` stream load
to tile0; `:149`, `:151` to tile1, tile2; `:159` range loop to tile6, tile7; `:161` to tile0;
`:163` to tile3. Wait `:165` (tile7) covers `:159`, `:161`, and by `cov_stall` `:147`, `:149`,
`:151`. On the `break` path (`:167-168`) `:163` stays uncovered and may reach the barrier at
`:197` or the region's implicit barrier after `:220`. It writes tile3 only, and tile3 is next
read only by `:179` after the next round's `:163` overwrites it. Critical section `:170-187`:
`:180` (`wait_ready(tile3)`) covers the store `:179`, its producers `:161`, `:163`, `:175`, and
`:173` (producer of `:175`), so every command, including the memory-writing store, is covered
before the exit. Own conflicts: tile reads at `:190-191` come after `:180`.
**Result: meets the refined rule.** The first draft's rule (everything covered before a
barrier) failed both candidates on these paths, as the main session predicted.

## Codex adversarial review: disposition

Round 1 (`/tmp/claude/probata-runs/t41/codex-review.md`, 12 findings):

| # | Finding | Disposition |
|---|---|---|
| 1 | `dx100_reduction` false: command metadata unconstrained | **Accepted:** `contracts_ok` premise. |
| 2 | `memory_ok` stronger than RC11 (SC order between RMWs as hb) | **Accepted in part:** kept as decided (M1), renamed to "RC11 with `__sync_*` as full barriers", and limited to `fence = true` RMWs; relaxed `omp atomic` gets no such edge. |
| 3 | `TileReady false` gives no witness (constructive blocker) | **Accepted:** rule split by cases. |
| 4 | commands need not have a covering wait | **Rejected:** real code leaves commands uncovered (`bfs.cc:163` on the break path; F1 check); `complete_timed` already requires every command to finish before the run ends, and the wait rule covers every wait that occurs. |
| 5 | `DeviceQuiet` unchecked | **Accepted:** per-command `DeviceCovered c` markers, plus the named lowering obligation `cover_sound`. |
| 6 | `WaitReady`/`TileReady` skip ownership | **Accepted.** |
| 7 | premises not one-to-one | **Accepted in part:** OpenMP ordering factored into `omp_sync`; `contracts_ok` separate. Rejected the rest: `device_ok` reusing `read_ok`/`hb` is a definitional dependency, not a second assumption entry. |
| 8 | `obl_hazard_free` is a whole-run property | **Accepted:** split into `obl_hazard_free_own` (one thread) and `obl_hazard_free_cross` (pairs). |
| 9 | failed CAS modeled as a write | **Accepted:** `sa_new` returns `option`. |
| 10 | atomic blocks exclude DX100 in critical | **Accepted in part:** the first read may be any non-shared read (DeviceRead included); multi-location blocks stay unsupported (M3). |
| 11 | stale-read sanity example outside the program class | **Accepted:** now a `__sync` CAS plus a relaxed load, with `stale_run_fits`. The suggested negative Rocq test of finding 1's counterexample is **rejected** for now: `contracts_ok` removes it, and building the counterexample in Rocq costs more than it checks. |
| 12 | page budget unmet | **Accepted** as F3 (decided). |

Round 2 (`/tmp/claude/probata-runs/t41/codex-review2.md`, 8 findings; R2, R4, R8 judged fixed):

| # | Finding | Disposition |
|---|---|---|
| 1 | `dx100_reduction` still false: two commands writing one register are unordered | **Accepted:** register overlap with a pending command is a hazard (F6). |
| 2 | `cover_sound` not formally connected (ids vs issue positions, completeness of device events) | **Accepted as an open obligation** for ticket 45 (specified above); the formal bridge lemma is out of 41's scope. |
| 3 | dead-read exemption vacuous for a command with no outputs; reads could steer the program | **Accepted in part:** `dead_after` now requires at least one output. "Reads reach the thread only through outputs" is part of `cover_sound`. |
| 4 | the fenced-`__sync` edge is a stronger platform axiom than RC11 | **Accepted:** stated explicitly as its own platform assumption ("fully fenced read-modify-write"), not derived from RC11. |
| 5 | premises still not one-to-one (OpenMP edges inside `memory_ok`) | **Accepted:** `memory_ok` now uses `hb_cpu` (program order + fenced atomics) only; OpenMP's ordering is the first clause of `omp_ok`, over `hb`. `device_ok` uses `hb` by definition (its promise is about stores ordered before issue by any means). |
| 6 | hazard split is syntactic; no lifting lemma | **Rejected:** both obligations have the rely form of `obl_class_fit` (one core, or a pair, against every environment the run allows); WP's per-thread encoding over-approximates that environment, so no separate lifting step exists. |
| 7 | read-only critical sections pass `implements_shared_action` | **Accepted:** a named `(k, a, l, old)` is required in both cases. |
| 8 | ticket record describes the first draft; page budget | **Accepted:** hashes refreshed; page budget amended by decision F3. |

Round 3 (`codex-review3.md`, truth only): **counterexample to `parallel_composition`, accepted.**
A critical section that touched a shared-actions-only location, or held a barrier, could not be
made contiguous in any serial twin. Fix: inside `critical` a thread touches no
shared-actions-only location (`fits_event`), and a critical block holds no barrier
(`obl_atomic_blocks`; OpenMP 5.2 already forbids a barrier nested in `critical`). Both candidates
are unaffected for F1; `TDStepMAA`'s critical section already falls outside the supported class
(M3).

Round 4 (`codex-review4.md`, truth only, after that fix): **no counterexample found** for either
statement; the round-2 and round-3 runs are excluded by the new hypotheses. Open (not truth
findings): `cover_sound` bridge for ticket 45; M6 split for ticket 43. This verdict is about the
approved `Reduction.v` of 14:12 ET (sha256 `8a779482…`); round 5 below covers the revision.

## Later change: ticket 27 covers (2026-10-14 21:30 ET)

Revised by the main session under Yan-Ru's delegation. Source: ticket 27's Answer,
"Disagreements with ticket 41's Rocq statement". Proof semantics 0.1 covers a command in two
places `covered` lacked, so `dx100_reduction` did not back proofs relying on them (fixtures
`stall_condition`, `register_write`). `Composition.v` and `Vocabulary.v` are unchanged.

| Change in `Reduction.v` | gem5 at `e4fc4af` | Mirrors `timed_run` clause |
|---|---|---|
| `cov_issue`: the issue of k' at step m covers every earlier command k with `stalls k k'` | dispatch stall `IF.cc:193-212` (tile), `IF.cc:213-219` (region); the CPU's issuing store is acknowledged only at dispatch (`CpuSidePort.cc:235-250`, `MAA.cc:581-583`; research 14 section 2) | dispatch stall |
| `cov_reg_write`: a CPU write at step m of an element of register g covers every earlier command naming g | `IF.cc:233-249` (`MAA.cc:510-538`, `CpuSidePort.cc:145-149`) | register write |
| `pending A n j` now excludes covers at step j itself (`m <= j`, was `m < j`) | the covering step acts only after the command finished | `unfinished T n j` (finish before j) |

Why the inclusive boundary: with `m < j`, a CPU register write would still see the commands it
covers as pending at its own step and be a same-thread overlap hazard (`hazard_own`, `CpuWrite`
case), so `cov_reg_write` would not help the `register_write` fixture. For waits and issues the
change is harmless: their own steps carry only ownership hazards. `cov_stall` (F5) is now
implied by `cov_issue` as far as `pending` goes; it stays, so no proof that used it breaks.

Each base cover only removes a command from `pending` at a step where `timed_run` forces it to
have finished, so the smaller pending set (weaker `obl_hazard_free_*`, stricter `at_issue_run`)
should keep the lemma true. Region covers go beyond 0.1 (ticket 28 adds the region stall);
they are sound against `timed_run`, which uses the same `stalls`.

Sanity lemmas added (`Sanity.v`, all `Qed`, no axiom): `stall_covered`, `stall_not_pending`,
`reg_write_covered`, `reg_write_not_pending`; `no_wait_before_step_2` became
`no_cover_up_to_step_2` for the inclusive boundary.

Round 5 (`/tmp/claude/probata-runs/t41b/codex-review.md`, sha256 `9dc000a6…`; `gpt-5.6-sol`,
`xhigh`, read-only): **no counterexample found.** Codex confirms both covers sound against
`timed_run` and gem5 (cross-core included, one instance), the inclusive boundary correct, and
every cover of model 0.1 present in Rocq. Findings:

| # | Finding | Disposition |
|---|---|---|
| 1 | blocker: new hash not recorded or approved in ticket 41 | **Accepted:** ticket 41 Later changes and approval record updated (new hash, old one superseded). |
| 2 | major: `contracts_ok` does not tie `regions_of` / `writes_memory` to gem5's assigned region and access class, so a wrong descriptor could invent a region cover | **Accepted in part, no statement change.** The same descriptors already drive `timed_run`'s approved dispatch-stall clause, so a wrong descriptor narrows "every timing gem5 allows" there too; it is not new with `cov_issue`. Descriptor faithfulness (each command's `regions_of` is gem5's assigned region, `writes_memory` its READ/WRITE/COMPUTE class) joins the `cover_sound` lowering obligation (ticket 45) and proof semantics' region rules (ticket 28). Note for 43. |
| 3 | major: this guide still describes wait-only coverage and scopes round 4 to the old hash | **Accepted:** this section, the summary sentence, and the round-4 scope note. |
| 4 | minor: comments equate coverage with waits; closure rules called step rules | **Accepted:** `Reduction.v` header and `covered` comments now say "covering step" and separate base covers from closure rules. |

## Composition.v revision in progress: well-bracketed critical sections (paused 2026-10-14 22:40 ET)

**Not approved; the effort is paused.** Branch `probata-poc/t41c` (from `probata-poc/t42`).

- **Decision** (main session under Yan-Ru's delegation, 2026-10-14 22:24 ET): ticket 42's
  stray-`Exit` counterexample is excluded by `omp_ok`, the trusted-tool entry "the pinned OpenMP
  runtime implements OpenMP 5.2": `critical` is a structured block, so each thread's
  `Enter`/`Exit` events are well bracketed. Not a per-candidate obligation.
- **Done:** `brackets_ok` and `omp_ok`'s new last clause
  `forall t, brackets_ok (proj X t) false = true`; `Sanity.v` lemma `stray_exit_excluded`
  (ticket 42's exact run is not `omp_ok`; Qed, no axiom).
- **Lowering obligation (ticket 45), next to `cover_sound`:** the per-thread lowering must
  preserve the bracketing: each thread's `Enter`/`Exit` events come from OpenMP `critical`
  structured blocks, in order, none dropped or added.
- **Codex round t41c-1** (`/tmp/claude/probata-runs/t41c/codex-review1.md`, sha256 `020368a8…`;
  `gpt-5.6-sol`, `xhigh`, read-only): **counterexample, open.** Both critical sections are well
  bracketed. Thread 1 issues `DeviceRead cA A 1` on a `LockProtected` A inside its critical
  section, leaves `cA` uncovered past its `Exit` (allowed: `cA` writes only a dead tile, F1),
  and `device_ok` lets that read take its value from thread 0's later `Write A 1` inside thread
  0's critical section. With a second device read (`cB` of `SharedActionsOnly` B, sourced from
  thread 1's later `Shared B`), the covers force `WA < CoverA < SharedB < CoverB`, so thread
  1's events fall inside thread 0's critical window: no serial twin exists. Codex checked all
  3,003 projection-preserving orders. Root cause: a command left uncovered past a critical exit
  may still *read* lock-protected data written by a later critical section. Ticket 42's
  `t42_device_safe` finding is the same reversal.
- **Fix candidates (need a decision):** (a) F1's exemption covers only commands that read no
  `LockProtected` location (a command reading lock-protected data must be covered before the
  `Exit`); (b) `device_ok` refuses a source from another thread's critical section that begins
  after the reading command's critical section ends; (c) fold into `dead_after`: the command's
  reads must also be outside lock-protected arrays. (a) is the smallest and matches 12 item 7's
  intent; both candidates' critical sections already cover their commands before the exit
  (F1 check above).

## Machine checks

- Rocq 9.3.0 (opam switch `rocq-9`, rocq-stdlib 9.2.0) accepts `Vocabulary.v`, `Composition.v`,
  `Reduction.v` and `Sanity.v`. Build: `rocq compile -Q . Probata <file>` in a copy outside the
  repo, through `verifier_run.py`.
- `Print Assumptions` lists only the two open theorems (`Admitted`); no axiom anywhere.
- Sanity lemmas, all `Qed`, "Closed under the global context": enumerations have exactly 5 and 4
  members; `stale_run_fits`, `stale_history_read_allowed`, `history_read_not_always_latest`
  (inside the program class a relaxed load may be stale); `read_own_write`;
  `failed_cas_reread_sees_winner` (15 item 12's must-prove control); `unready_read_is_hazard`
  (12 item 9); since 21:30 ET also `stall_covered`, `stall_not_pending`, `reg_write_covered`,
  `reg_write_not_pending` (ticket 27's two covers).
- Negative check: `negative/HistoryReadIsLatest_FALSE.v` (history reads are SC) is rejected at
  its unprovable branch, as required.

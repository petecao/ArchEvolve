# Probata Rocq development: review guide and hypothesis table

Created: 2026-10-14 ET (ticket 41). Status: **draft, waiting for Yan-Ru's review.**

## What you review (and what you do not)

- **Review:** two statements and their definitions.
  - `parallel_composition` in [`Composition.v`](Composition.v): about 4.5 printed pages.
  - `dx100_reduction` in [`Reduction.v`](Reduction.v): about 3.5 printed pages.
  - The closed vocabularies in [`Vocabulary.v`](Vocabulary.v): 5 shared-action kinds, 4 sharing classes.
- **Do not review:** proofs (there are none yet; tickets 42 and 43 write them), [`Sanity.v`](Sanity.v)
  and [`negative/`](negative/) (machine checks, results below).
- **Your approval** goes into ticket 41's Answer: date and time ET, plus the sha256 of
  `Vocabulary.v`, `Composition.v` and `Reduction.v`. Any later change needs a new approval.

## Composition theorem in one sentence

If every thread's accesses fit their sharing classes, owned memory is disjoint, each critical
section is one shared action, chunk splits cover each worksharing loop once, control is uniform,
the team has N threads and DX100 commands finish before barriers, then every finished run of N
threads has a **serial twin**: the same events per thread, critical sections and barrier intervals
one after another, every read outside a shared-actions-only array returning the latest write, and
the same final memory.

## Hypothesis table: `parallel_composition`

Each hypothesis is one per-candidate WP obligation **or** one assumption entry, never both.
A WP obligation for a candidate is named after the hypothesis it discharges (16 item 4).

| Rocq name | Kind | Discharged by | Plain sentence |
|---|---|---|---|
| `obl_class_fit` | per-candidate WP obligation | WP, one symbolic thread t | Whenever the other threads' accesses fit their sharing classes, thread t's accesses fit theirs too (race freedom, 15 item 2). |
| `obl_owned_disjoint` | per-candidate WP obligation | WP, two-copy product | No location (owned range, tile or register) is owned by two threads in the same barrier interval (15 item 2). |
| `obl_atomic_blocks` | per-candidate WP obligation | WP, one symbolic thread t | Each critical section reads one location first, writes only it, and leaves one shared action's result there (15 item 2). |
| `obl_chunk_cover` | per-candidate WP obligation | WP (pure arithmetic over t and N, plus thread t's loop) | Chunk splits computed from the thread id cover each loop's iteration space exactly once, and thread t runs exactly its chunk (15 items 2, 4). |
| `obl_uniform_control` | per-candidate WP obligation | WP, two-copy product (GPUVerify style) | Any two threads reach the same barriers and worksharing constructs in the same order (15 item 6). |
| `obl_team_size` | per-candidate WP obligation | WP over the run-time guard | The team has exactly N threads (15 item 4; 11's guard). |
| `obl_dx100_quiet` | per-candidate WP obligation | WP over the ghost hazard state | Each DX100 access of thread t is covered by waits before t's next barrier, before t leaves a critical section, and before t's own conflicting CPU access (12 items 3-5, 7; **new, see F1**). |
| `memory_ok` (premise) | assumption entry, **platform choice** | "The pinned compiler and ISA implement RC11" (15 item 3; 26 item 4) | Reads are history reads; a CAS is a sequentially consistent read-modify-write. |
| `omp_ok` (premise) | assumption entry, **trusted tool** | "The pinned OpenMP runtime implements OpenMP 5.2" (15 item 4) | Thread ids are 0 to N-1; a barrier waits for all threads; `critical` excludes other threads; `omp for` gives each iteration to exactly one thread. |
| `device_ok` (premise) | assumption entry, **proof semantics** | The pinned DX100 proof-semantics version (12 items 4, 7) | A DX100 read returns a value the location held while the command ran, never older than the stores made before issue. |

**Not hypotheses: the subject of the theorem.** `program_run X` and `complete X` say what
"every run" ranges over: X is a finished run of the thread-indexed program. They are not facts
about a candidate and need no evidence.

**Where barrier and `critical` "order memory".** That part of the OpenMP entry lives in the
definition `hb` (edges `sync_barrier`, `sync_critical`), which `memory_ok` uses.

**Validity conditions of the three premises.** `omp_ok` is valid only for programs with uniform
control (OpenMP leaves divergent barriers undefined); `obl_uniform_control` supplies that.
`device_ok`'s bound "up to the thread's next `DeviceQuiet`" is valid only where `DeviceQuiet`
marks a point where all of the thread's commands are covered; `obl_dx100_quiet` and the
reduction lemma supply that.

## Hypothesis table: `dx100_reduction`

| Rocq name | Kind | Discharged by | Plain sentence |
|---|---|---|---|
| `obl_hazard_free` | per-candidate WP obligation | WP over the proof semantics' ghost hazard state | No run that executes every command at its issue reaches a hazard (12 items 3-5). |

**Not hypotheses: the subject.** `timed_run T` and `complete_timed T` say what "every timing
gem5 allows" ranges over. Each clause of `timed_run` cites the gem5 source it models
(research 14 at `e4fc4af`), so it needs no sign-off beyond the citation (12 item 11).

**Hazard-free** (`hazard` in Reduction.v) is the proof semantics' own definition:
unready read; CPU write to a tile an unfinished command reads; same-thread overlap with an
unfinished command's footprint where either side writes; other-thread overlap with an unfinished
DX100 write; a tile or register the thread does not own; plus one addition (F2). Device against
device is not a hazard: `timed_run` models the region stall instead.

**Linked assumption entry.** "One DX100 instance" (12 item 7) is built into `timed_run`: all
cores share one instruction file, so the dispatch and region stalls compare every core's
unfinished commands.

## Modeling choices to confirm

Each is a choice the decisions leave open. Answer yes, or name the change.

| # | Choice | Why |
|---|---|---|
| M1 | `memory_ok` renders RC11 with one global order of events that agrees with each location's modification order; a CAS (`__sync_*`) is a full fence (edge `sync_shared`). | `__sync_*` are full barriers. Every location is either race-free or written only by SC read-modify-writes (class fit), so such an order exists. Argued, not proven. |
| M2 | In the composition model, a DX100 command's reads and writes sit at its issue. A DX100 read may still return a value another thread writes later, up to the issuing thread's next `DeviceQuiet`. | The reduction lemma licenses "at issue" for the issuing thread; 12 item 4 allows the later value for other threads. |
| M3 | A critical section implements one shared action on **one** location. | Matches 15 item 2 literally. A critical section that stores a batch (the authors' `TDStepMAA`) does not meet `obl_atomic_blocks`; it is refuted at threads > 1 anyway (11). |
| M4 | A CAS loop (min-update) appears as one `Shared MinUpdate` event. | The C lowering emits that event only with WP's proof that the loop implements the kind (same obligation, `atomic_blocks`). |
| M5 | Worksharing constructs are numbered in the order a thread reaches them; each has a fixed iteration space. | The proof-of-concept regions reach each construct once. A loop whose space is computed inside the region is outside this statement. |
| M6 | The reduction lemma orders CPU steps in one global sequence (sequential consistency). | It studies DX100 timing only. Weak CPU memory belongs to the composition theorem. The two statements are joined by the proof records, not inside Rocq. |
| M7 | A command reads each element at some time while it runs, and writes all its results at one step. | Writes cannot be observed early: overlapping a DX100 write is a hazard, and the region stall orders device against device. |
| M8 | 8-byte operands (tiles t and t+1, 12 Later changes) are not modeled. | No proof-of-concept kernel uses them. |
| M9 | The theorem ends at "a serial order of the shared actions"; the contract's order-independence lemma joins it through proof-record dependencies. | Ticket 41 assumption. You may ask for a Rocq corollary. |
| M10 | Other threads' DX100 commands are history reads plus the owned and lock-protected classes, not a sixth shared-action kind. | Ticket 41 assumption (15 items 5 and 7). |

## Findings that need your decision

- **F1 (new obligation).** A DX100 read issued before a barrier may finish after it. 12 item 4
  allows an other-thread write to overlap it, so it could see a value written in the next
  interval, and a read-only class would no longer protect it. `obl_dx100_quiet` therefore
  requires every command to be covered before the thread's next barrier (and before leaving a
  critical section). This is stricter than 12. The proof-of-concept candidates already wait
  inside each chunk, so they should meet it.
- **F2 (new hazard).** gem5's region stall compares registered regions only. A DX100 memory
  access outside its command's registered regions escapes the stall, so `hazard` flags it.
  `region_of` is a function, which assumes the registered regions are disjoint.
- **F3 (length).** About 4.5 + 3.5 pages against "about 2". Every obligation and premise is
  spelled out so that it maps to exactly one row above. Shortening would hide definitions.
- **F4 (provenance).** The ticket says Codex drafts. This draft was written by Claude
  (`claude-opus-5-5`, a Claude Code subagent of the main session); Codex (`gpt-5.6-sol`,
  effort `xhigh`) was started as an adversarial reviewer; its output lands in
  `/tmp/claude/probata-runs/t41/codex-review.md` (ticket 41's Answer). You decide whether Codex
  should redraft.

## Machine checks (ticket 41)

- Rocq 9.3.0 (opam switch `rocq-9`, rocq-stdlib 9.2.0) accepts `Vocabulary.v`, `Composition.v`,
  `Reduction.v` and `Sanity.v`.
- `Print Assumptions` lists only the two open theorems themselves (`Admitted`); no axiom is
  declared anywhere.
- Sanity lemmas, all `Qed`, each "Closed under the global context":
  - the enumerations have exactly 5 and 4 members;
  - `stale_history_read_allowed` and `history_read_not_always_latest`: a history read may return
    a stale value (the model is not sequential consistency);
  - `read_own_write`: a plain read after the thread's own write returns it;
  - `failed_cas_reread_sees_winner`: 15 item 12's must-prove control (read, failed CAS, re-read
    sees the winner);
  - `unready_read_is_hazard`: a same-thread read during the thread's unfinished DX100 store is a
    hazard (12 item 9).
- Negative check: `negative/HistoryReadIsLatest_FALSE.v` claims sequential consistency for history
  reads. Rocq rejects it at the unprovable branch, as required.
- Build: `rocq compile -Q . Probata <file>` in a copy outside the repo, through
  `verifier_run.py` (one verifier job at a time, 8 GB RSS watchdog).

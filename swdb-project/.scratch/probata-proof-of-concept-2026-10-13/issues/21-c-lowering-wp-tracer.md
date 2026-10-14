# 21 — C lowering and WP adapter (A2 tracer)

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes); 2026-10-14 15:30 ET (resolved); 2026-10-14 15:45 ET (fix-21: method-version lifecycle, first real draft)
**Type:** slice
**Status:** resolved
**Blocked by:** 04, 10, 11, 20
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules": proof command, verifier adapters, C lowering tool; "Verifier lineup and order": unbounded verifier, solver portfolio, pinned versions, failure classes; "Proof-hint loop": anchors, frozen flags, verdict reading; "Records and levels": where evidence lives; "Testing Decisions", seam 1; choices S1 and S3); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 1, 3, 8, 9, 10; [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) items 4, 6, 7; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 3, 6; also [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 5 (where evidence lives)
**Time estimate:** about 3 days

**What to build:** The thinnest end-to-end path through A2. Yan-Ru runs `swdb prove` on a small C++ fixture proof unit in the core subset (functions, arrays, loops). Its fixture contract states an ACSL unit postcondition in 20's frame. Our C lowering tool, deterministic code and never an LLM, makes the unit's C lowering. It keeps the C++ names, so the ACSL type-checks unchanged, and it emits stable anchors for later proof hints. The real WP adapter runs Frama-C/WP 33.0 on the C lowering with the solver portfolio (Alt-Ergo, Z3, CVC5) and the frozen flags, reads the verdict per property from its own fresh run with a minimal verdict reader, and writes one proof record. Every failure class WP can emit here maps to 11's vocabulary and has a handler. `swdb prove` also gets the Mac lock (one real verifier job at a time), which every later adapter inherits. The safe fixture and map 07's safe smoke program come back proven. Their bounds say threads = 1, so they give at most proven within bounds (11 item 10); 10's level rule computes the level on read, and no level is written. The seeded bug and map 07's seeded bug come back not proven with a failure class, never refuted.

## Acceptance

- [ ] Determinism: lowering the same fixture twice gives byte-identical C and the same anchor list (same hashes). No provider is called.
- [ ] Names kept: `swdb validate` type-checks the fixture contract's ACSL, written over the C++ names, against the C lowering of the baseline proof unit's signature (16 item 3), with no renaming layer. This replaces 20's hand-written declaration. Control: an ACSL name with no C++ counterpart is refused.
- [ ] Anchors sit at the function entry, each loop head, before and after each statement, and in one ghost-globals slot. Each anchor ID is unique, and the anchor list is written beside the C lowering.
- [ ] `swdb prove` on the safe fixture with the real WP adapter writes one proof record with verdict proven. Its bounds read threads = 1 and every other dimension unbounded. `swdb validate` and `swdb build` accept the record, and 10's level rule reads it as at most proven within bounds.
- [ ] Minimal verdict reader: the verdict is proven only when every property in WP's per-property report of this run is Valid; the consolidated `[ Valid ]` line is never used. The record lists, per goal, the solver that proved it (any one of Alt-Ergo, Z3, CVC5 counts) and its time. 36 owns the full reading rule and its controls.
- [ ] Smoke pair: `swdb prove` on map [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md)'s smoke pair (the safe smoke program and its seeded bug, `-DBUGGY`). WP proves the safe program and leaves the seeded bug not proven, never refuted.
- [ ] The adapter always runs with the frozen settings, and the record names them: `-wp-cache none`, a fresh session, default Frama-C warning levels, x86_64 machdep, no WP environment variables, `-wp-model +real`, WP 30 s per solver (the starting value). Frama-C, solver and C lowering tool versions and the C lowering's hash are pinned in the content-hash set.
- [ ] Seeded bug (the fixture with one off-by-one): the record reads not proven, with a failure class from 11's vocabulary file (timeout or unknown expected) and the unproven properties. It has no counterexample and no refuted verdict.
- [ ] Failure classes: every class WP can emit here (parse error, timeout, unknown, out of memory, solver error, tool crash) maps to its entry in 11's vocabulary file and runs that entry's handler (map 11 item 9). Each class is shown on a fixture or a scripted fault. An outcome with no class stops the batch.
- [ ] Regression corpus: each diagnosed failure (cause named) adds a corpus case: the input, its class and its cause. The corpus reruns in the test suite, and each case gives its recorded class again.
- [ ] The assumption set lists, as trusted-tool entries with one plain sentence each: the C lowering tool (11 item 3), clang 22.1.8 (design, "Out of Scope"), Frama-C/WP 33.0, and each solver (Alt-Ergo, Z3, CVC5; design S14).
- [ ] Mac lock: `swdb prove` takes a machine-wide lock before any real verifier job, so a second real job waits until the first ends. Test: two `swdb prove` calls with real WP, started together, never overlap (checked from outside by their start and end times). Every later adapter (22, 23, 46, 47) inherits the lock; none rebuilds it.
- [ ] Mac hygiene: the job runs under the ~8 GB RSS watchdog, and a job the watchdog kills reads not proven, out of memory. WP logs and the per-goal report land in the Mac runs folder outside the repo (host `mac`), named by path and sha256. No WP or Why3 scratch is left after the job.
- [ ] Tests that need Frama-C skip cleanly when it is missing. Fixture records carry `contract_fixture` evidence.

## Notes

- **Not in this ticket:**
  - 04 — Proof record tracer: the `proof` record kind, its tables and the scripted path through `swdb prove`.
  - 10 — Level rule: the level computed on read, which this ticket's record feeds.
  - 22 — SAW adapter and SAWScript translator; 23 — C-stub translator, fallbacks and check mode: the bounded verifier, refutations, and the C++-versus-C-lowering agreement check.
  - 24 — C++ subset widening: every construct beyond functions, arrays and loops, and the "unsupported construct" class for what stays outside.
  - 26 — Logic and sum libraries: the real logic library.
  - 35 — Hint records, merger and proof hint check: the hint merger that uses these anchors.
  - 36 — Proof setup check and verdict reading: the proof setup check, the full verdict-reading rule, and their negative controls (consolidated `[ Valid ]`, a doctored cache, `Extern` read as design S7 says, the seven WP fact files of map ticket 13, smoke goals).
  - 37 — The proof-hint loop: hint rounds (for goals with class timeout or unknown), smoke tests and minimization.
  - 11 — Method-version file and failure classes: the failure-class vocabulary file this adapter maps to.
  - 45 — Per-thread lowering: the program for one symbolic thread of N.
  - 57 — Proof workers in a socket lane: WP jobs on mbit10.
- Assumption (not decided in the map): which of map 11 item 9's handlers serves which class. Parse error: fix the C lowering or the adapter, with a minimal reproduction. Timeout and unknown: the unproven goals are listed for the hint loop (37). Out of memory: rerun with more memory where the host allows; on the Mac the ~8 GB cap stays and the record keeps the class. Solver error and tool crash: fix the adapter, with a minimal reproduction.
- Assumption (not decided in the map): the lock is machine-wide (across processes, test runs included), and a waiting job queues rather than fails. The scripted adapter takes no lock.
- Assumption (not decided in the map): the regression corpus is a set of fixture inputs with their class and cause, rerun by the test suite; one corpus serves every adapter.
- Assumption (not decided in the map): how the C lowering tool reads C++ (for example clang 22.1.8's syntax tree) is an implementation choice. Whatever it uses is pinned in the content-hash set and listed as a trusted tool. If it uses LLVM 22, the analytic evaluator must keep working.
- Frama-C/WP and its solvers are both pinned in the content-hash set and listed as trusted-tool entries (design S14: verifiers and solvers are trusted-tool entries in every assumption set).
- Assumption (not decided in the map): "stable anchors" means anchor IDs are a deterministic function of the code's structure. Stability across unrelated edits is not promised.
- Assumption (not decided in the map): this ticket's proven verdict runs no WP smoke tests (the vacuity check, not map 07's smoke pair); 36 and 37 add them. Its records are fixture evidence only.
- Risk: WP runs fail inside the Bash sandbox (the Why3 socket is blocked; map ticket 11's fact sweep). Run WP jobs outside it.
- WP's "not proven" never refutes. Only the bounded verifier refutes (22).
- Mac: keep at least 50 GB of disk free; the lock built here keeps real verifier jobs to one at a time.

## Later changes
- 2026-10-14 13:19 ET (Yan-Ru accepted ticket 09's A2 changes): the bounded verifier is now CBMC 6.11 on this ticket's C lowering, so this lowering comes before the bounded adapter (22). Each bounded job also runs a C-vs-C++ differential check on the bounded domain (pattern: `prototype/06c-cbmc/faith/`).

## Answer

2026-10-14 15:30 ET. **Resolved.** Every acceptance box is met on the fixtures below; one dispatch
expectation (the generated lowering matching the hand lowering of the spike units) is not, because those
units are outside the core subset (ticket 24). Branch `probata-poc/t21`. Interface doc:
[`format-v0.4-c-lowering-wp.md`](../../../docs/reference/format-v0.4-c-lowering-wp.md).

**What was built**

| Piece | Where |
|---|---|
| C lowering tool `swdb lower` (clang 22.1.8 JSON syntax tree to C; kept names; anchors; `Unsupported` / `ParseError`) | `swdb/c_lowering.py` |
| Real WP adapter `swdb prove --adapter wp` (input builder, lineup check, frozen run, minimal verdict reader, handlers) | `swdb/wp_adapter.py` |
| Machine-wide verifier lock (same protocol as `verifier_run.py`; nested hold inside its holder) | `swdb/verifier_lock.py`, used in `swdb/proof.py` |
| `Verdict.record_fields / pins / reports`; `evidence_kind: execution`; `--hint-file`, `--define` | `swdb/proof.py`, `schemas/proof.schema.json` |
| `proof_unit: {source, function}` replaces the hand prototype; concurrency frame names every interface array | `swdb/formal_frame.py` |
| `evidence_kind: execution` for method versions | `schemas/library/method_version.schema.json` |
| Regression corpus (3 cases) | `tests/fixtures/proof/regression_corpus/` |

**Acceptance, box by box**

- Determinism: two lowerings give identical bytes and anchor lists; no provider exists in the path.
- Names kept: `swdb validate` type-checks formal halves against the lowered signature; `num_nodes` (no
  C++ counterpart) and a hand `prototype` are refused (`test_formal_frame.py`).
- Anchors: entry, loop heads, before/after each statement, one `ghost.globals`, plus a `contract` slot per
  function; unique IDs; `<f>.anchors.json` beside the C (worked example asserted literally).
- Safe fixture (`swdb_fixture_fill`): proven, bounds `{threads: 1, input_size: unbounded}`; `swdb validate`
  and `swdb build` accept it; `swdb candidate-level` reads `proven_within_bounds_threads_1`.
- Verdict reader: proven only if every `-report-csv` property is `Valid` and every `-wp-report-json` goal
  passed; per-goal `solver` and `seconds` in `goals`. Finding: the per-property CSV omits loop-variant
  properties, so the goal report is read too.
- Smoke pair (map 07's `count_up`): safe proven; seeded bug (`assert i == n + 1`) not proven, never refuted.
- Frozen settings named in `settings`; tool versions checked against the method version's lineup (a
  mismatch runs nothing); the C lowering's hash is `pins.c_lowering`.
- Seeded bug (`i < n - 1`): not proven, `timeout`, `unproven_properties` holds the postcondition; no
  counterexample.
- Failure classes, each shown: `parse_error` (bad hint, real WP), `timeout` (seeded bug, real),
  `unknown`, `solver_error`, `tool_crash` (scripted stand-in `frama-c`), `out_of_memory` (real WP under a
  20 MiB cap), `unsupported_construct` (GAPBS `InitParent`). Each writes `wp/handler.json`. An outcome with
  no class stops the batch, no record.
- Regression corpus: 3 cases (hint syntax error; spike unit member access; GAPBS function outside the
  subset), each rerun by the suite and giving its class again.
- Assumption set: six `trusted_tool` entries with one sentence each and binary sha256s
  (`swdb-c-lowering-1`, `clang-22.1.8`, `frama-c-wp-33.0`, `alt-ergo-2.6.4`, `z3-5.1.0`, `cvc5-1.2.1`).
- Mac lock: two `swdb prove` with real WP started together never overlap (start/end times written by a
  wrapper `frama-c`, outside swdb). 22/23/46/47 inherit it by setting `real = True`.
- Mac hygiene: RSS watchdog (8 GiB; `SWDB_VERIFIER_RSS_CAP_BYTES`); WP logs and reports under
  `<runs-dir>/<record>/wp/`, named in `evidence.reports` by path and sha256; scratch (and `TMPDIR`) deleted.
- Missing tools: WP tests skip without Frama-C 33.0 or clang 22.1.8; fixture records carry
  `contract_fixture` (they run under a fixture method version).

**Tests** (Mac; serial; no xdist; WP runs inside `verifier_run.py`, sandbox off):

- `tests/test_c_lowering.py`, `tests/test_wp_adapter.py`, `tests/test_formal_frame.py`: **98 passed** in
  166 s after merging the integration tip (peak 863 MB). Log `/tmp/claude/probata-runs/t21/pytest-final-locked.log`
  (sha256 `c61f00763a6a3ce5`...), report log `/tmp/claude/probata-runs/t21/report-final-locked.jsonl`
  (`6ecf446b2739a89e`...).
- `tests/test_format_doc.py`, `test_proof_records.py`, `test_proof_method_version.py`,
  `test_proof_run_fields.py`, `test_level_rule.py`, `test_proof_lane.py`, `test_archevolve_proof_path.py`:
  **286 passed, 1 skipped, 5 failed** in 572 s, with `SWDB_FRAMA_C=none`, outside the lock (no verifier).
  The 5 failures are `test_level_rule.py` cases that **also fail on the integration tip** (checked on a
  clean checkout of `6c0dcf7d`; side finding below). Report log
  `/tmp/claude/probata-runs/t21/report-final-unlocked.jsonl` (`4475a767756d0844`...).
- Run output: `/tmp/claude/probata-runs/t21/` (pytest temp folders are disposable after merge).

**Assumptions** (the ticket's Notes assumptions are implemented as written; these are new):

- Assumption: the fixture candidate artifacts are GAPBS `bfs.cc` with the fixture units inserted through
  the public proposal workflow (`tests/fixtures/proof/wp/fixture_units.cc`); the C++ file is found by
  scanning the tree for the one definition of the function.
- Assumption: map 07's smoke pair keeps its code; its contract (`requires`, `assigns`, `ensures`) is a
  fixture contract and its loop annotations and assertion are fixture hints at anchors (`--hint-file`,
  only `loop invariant/assigns/variant` at loop heads and `assert` elsewhere; ticket 35 replaces this).
  The seeded bug is the hint `assert i == n + 1`, as in map 07.
- Assumption: WP bounds are `{threads: 1, input_size: unbounded}` (one dimension name for "every input size").
- Assumption: per-goal class precedence `solver_error` > `timeout` > `unknown`; `stepout` reads as timeout;
  a not-`Valid` property with no failing goal is unclassified (stops the batch).
- Assumption: `evidence_kind` is `execution` only for a real adapter under a method version whose
  `evidence_kind` is `execution`; under a `contract_fixture` method version the record stays a fixture.
- Assumption: the lock path is `SWDB_VERIFIER_LOCK`, else `/tmp/claude/swdb-verifier.lock` when `/tmp/claude`
  exists, else `/tmp/swdb-verifier-<uid>.lock`; inside the holder's process tree a job takes `<lock>/nested`.
- Assumption: a hint with an unbounded range (`a[i ..]`) is refused before WP runs (ticket 07: WP 33 aborts).
- Assumption: a baseline proof unit outside the subset makes its formal halves refused at validate time;
  a missing clang makes them unchecked.

**Not done, and why**

- No real `library/methods/` draft is committed (11's hand-off). A real method file becomes the current
  method version in every test seed that copies the repository library (10 test files expect
  `method.contract-fixture-1`) and turns on 14's bounded gate. The real Mac lineup is in
  `tests/test_wp_adapter.py::method_version` (clang 22.1.8, CBMC 6.11, Frama-C/WP 33.0, Alt-Ergo 2.6.4,
  Z3 5.1.0, CVC5 1.2.1). Decision for the main session: where and when to commit the first real one.
- The generated lowering does not yet match the hand lowering `prototype/06c-cbmc/unit_*.c`: the spike units
  use classes, references and templates (24's subset). The tool refuses them cleanly ("member access"),
  and that refusal is a corpus case.

**Side findings**

- 5 cases of `tests/test_level_rule.py` fail on the integration tip, before this ticket: they write
  `library/proof_semantics/v1.yaml` as plain files, and ticket 20 made `proof_semantics` a library kind
  that needs `formal_frame`, `rules` and the `semantics.` prefix. Needs a fix in 10's test fixtures.
- Fixture method version `contract-fixture-1.yaml` pins Z3 4.8.14; the Mac has Z3 5.1.0.

**Interface notes**

- 22/23 (CBMC): `swdb.c_lowering.lower(source, function, includes, defines)`; set `real = True` and
  `from_args` on the adapter to get the lock and the call context; differential pattern in
  `tests/test_c_lowering.py` (C and C++ with one shared harness, outputs identical).
- 24: widen `c_lowering._Printer`; keep refusals as `Unsupported`; bump `TOOL_VERSION`; the spike units'
  hand lowering is the reference.
- 26: logic files used by a clause are inserted at `ghost.globals`.
- 27: `pins.proof_semantics` is still not applicable.
- 34/35/37: anchors in `<f>.anchors.json`; `WpAdapter._input` places hints; retry from `goals` and
  `unproven_properties`; handler output lists `for_hint_loop`.
- 36: replace `wp_adapter.read_outcome`; keep the class table in the doc.

**Later changes** (2026-10-14 15:45 ET, follow-up branch `probata-poc/fix-21`)

- Assumption (main-session decision, 2026-10-14): method versions get a lifecycle, `status: draft | frozen`.
  - `method_version.current()` returns the highest-sequence **frozen** version. A draft never becomes current.
  - A draft is used only when named: `swdb prove --method-version <id>`, or the campaign file's new optional
    `method_version`. The bounded gate and the WP phase then run under it, and the gate passes it to `swdb prove`.
  - The bounded gate stays off unless the campaign pins a method version or a frozen one exists.
  - Ticket 59 is the freeze: it flips the status and fills in the review.
- Assumption (not decided above): the freeze is a **new file** (`status: frozen`, next `sequence`), not an
  in-place edit. A status flip changes the file's bytes, so records that pin the draft would otherwise fail
  `swdb validate`. Records under the draft stop counting at the freeze; 59 replays them.
- Assumption: the level rule (still `level-rule.1`) counts a record under the current frozen version, or under
  a draft whose `sequence` is higher than that version's. Two frozen files never share a `sequence`; a draft may.
- Assumption: the repair cap reads the method version the refuted proof record pins (else the current one).
  ArchEvolve mode has no campaign file, so it uses the current frozen version only.
- Interface change: `TargetAdapter.prepare_proofs(store_dir, method=None)` gets the gate's method-version pin
  (22/46/47/55: contract-proof records pin that one).
- The first real draft is committed: `library/methods/probata-draft-1.yaml` (`method.probata-draft-1`,
  sequence 1, `evidence_kind: execution`).
  - Lineup: clang 22.1.8; CBMC 6.11 as the bounded verifier (Yan-Ru, 13:19 ET; SAW and crux-llvm left the
    lineup); CIVL 1.23; GenMC 0.19.0; Frama-C/WP 33.0 with Alt-Ergo 2.6.4, Z3 5.1.0 and CVC5 1.2.1;
    Rocq 9.3.0.
  - Budgets: ticket 11's starting values (tickets 11 and 16). Ghost capacity K = 32 (design spec).
  - WP flags add `-wp-par 1` (ticket 08) and `-machdep x86_64` to the frozen pair. The adapter also appends
    both itself, so they appear twice on the command line (harmless).
  - CBMC flags are ticket 22's tested `--sat-solver cadical`; its adapter adds `--unwind K` and
    `--unwinding-assertions` per job.
  - Translators: the C lowering tool (`swdb-c-lowering-1`) and ticket 22's CBMC translator
    (`swdb-cbmc-translator-1`), each by its source sha256 after merging 22. A change to either tool (24
    widens the lowering) needs the next draft before an adapter run with `--method-version`.
  - Logic library (after merging 26): `files` pins ticket 26's four shared files at 1.0 as
    `{id, version, sha256}`, and `sum_library` pins `logic.sum` 1.0. Assumption: the section's `sha256` is the
    digest of the `files` list (the schema gained optional `files` and an optional reference `version`).
  - `not_yet_built`: `acsl_version` (36 confirms it), `checks` (35, 36), `prompts` (34, 37), `models` (25),
    `rocq_development` (41-43).
- `swdb prove-logic` (26) takes `--method-version` too; without it, it runs under the current frozen version.
- The contract fixture `tests/fixtures/proof/methods/contract-fixture-1.yaml` is now `frozen`, so it stays
  the current method version of test seeds. `tests/test_wp_adapter.py::method_version` takes its lineup
  from the committed draft.
- The side finding is fixed: `test_level_rule.py`'s proof-semantics fixtures now write ticket 20 entries.

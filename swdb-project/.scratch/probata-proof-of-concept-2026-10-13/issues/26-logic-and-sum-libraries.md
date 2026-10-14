# 26 — Logic and sum libraries

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 16:40 ET (Answer)
**Type:** slice
**Status:** resolved
**Blocked by:** 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Modules", library content: logic library; "Formal-half language and the C++ subset": allowed ACSL, primitive recursion; user story 53: primitive recursion and the `\false` check; "Records and levels": the method-version file lists the shared logic library with the sum library; "Proven once vs per candidate": the "with the method" row; "Evaluation design": RQ3 counts the sum library's one-time cost; "Proof-of-concept plan": A1 (d) and A2; "Testing Decisions"); decisions: [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 2, 9, 12; [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) item 4; also [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) item 3 (a synthetic fixture, never PR)
**Time estimate:** about 1-2 weeks

**What to build:** Formal halves and proofs get the shared definitions they call, held to rules that stop WP from proving false things. The shared logic library (the CSR graph model, set helpers, and accessors such as `at(parent, v)`, name decided in map 16) lives in `library/logic/<name>.acsl` (name decided in map 16); each contract may own one more file beside its YAML. Every file is versioned and pinned by content hash in each proof record that uses it. Each version passes 20's allowed-ACSL rules (non-recursive or primitive-recursive definitions, inductive definitions only in lemmas, no axioms), and WP cannot prove `\false` from the library alone. The sum library is a method-level part: a range sum defined over a count argument (a sum from `lo` over `n` elements, recursing on `n`), a filtered sum by an offsets array (the flattening case) defined the same way, and three lemmas: additivity, regrouping a flat edge range by owner vertex, and permutation of a finite sum. All are proven in WP over reals. It is tested on the calibration suites (Code2Inv, X509-parser, Frama-C-problems) and a CSR fixture, never on PR or BC.

## Acceptance

- [ ] Shared files for the CSR graph model, set helpers and accessors exist, each with a version, and `swdb validate` accepts them. A fixture contract's own file beside its YAML loads the same way.
- [ ] A proof record that uses a logic file pins that file's version and hash in its content-hash set. Editing the file gives a new hash, so a re-run records a new pin and the old record's pin no longer matches.
- [ ] First, before any lemma work: the range sum and the filtered sum, each over a count argument (a sum from `lo` over `n` elements, recursing on `n` with base case `n <= 0`), pass 20's primitive-recursion rule in `swdb validate`.
- [ ] Every library file and version passes 20's rules in `swdb validate` (recursion, inductive definitions only in lemmas, no axioms). 20's negative controls (`pbad(x) = !pbad(x)`, a call on `n+1`, no base case, `axiom`, an inductive predicate called from a formal half) stand for these rules; they are cited, not re-tested.
- [ ] `\false` check per version: it passes on the shipped library. Negative control: a library version carrying map ticket 13's `pbad` definition (run with the recursion check bypassed) lets WP prove `\false`, and that version is refused. The result is recorded per version.
- [ ] Sum library: the range sum and the filtered sum are defined over reals by the count recursion above. Additivity, regrouping and permutation are each proven in WP with `-wp-model +real`, and each proof is recorded (subject: a method part).
- [ ] CSR fixture: a synthetic CSR pull-sum unit (each vertex's value is the sum over its incoming edge range) proves in WP against its unit postcondition through the sum library. A flattened variant (one flat edge loop) proves against the same unit postcondition through the regrouping lemma. A seeded bug in each reads not proven.
- [ ] Calibration suites: their tasks that sum over a range prove with the sum library in place of their own definitions. The answer lists the tasks used.
- [ ] No test, fixture or record uses BC, PR or SSSP code. The ticket's answer records the agent time spent on the sum library, since RQ3 counts its one-time cost.
- [ ] On the Mac, WP jobs go through 21's lock, one at a time, under the ~8 GB RSS watchdog. Tests that need Frama-C skip cleanly.

## Notes

- **Not in this ticket:**
  - 20 — Formal-half frame: the allowed-ACSL rules inside `swdb validate` (recursion, inductive definitions, axioms) with their negative controls, and the `acsl` field. This ticket runs those rules on the real library files and cites 20's controls.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions: an ACSL definition of each reference semantics, proven against the lowered reference code.
  - 31 — Five-gate drafting and the new bfs_read_offload version: `bfs_read_offload`'s own per-contract file.
  - 40 — Bucketed-relaxation fixture: the SSSP-style fixture that uses this library.
  - 44 — Shared-action kinds and commutativity lemmas: the kinds' lemmas.
  - 33 — Minimum-bounds script and A2 exit: showing the generated library reproduces spike (d)'s verdict (08 — Spike (d): sums over reals).
  - 38 — Calibration on the public C suites: the proof-hint loop's runs on the suites. This ticket only proves the suites' range-sum tasks with the sum library.
  - [evaluation 02](../../probata-evaluation-2026-10-13/issues/02-bc-held-out-contract.md) — BC held-out contract and contract proof; [evaluation 04](../../probata-evaluation-2026-10-13/issues/04-sssp-held-out-contract.md) — SSSP held-out contract and contract proof: kernel-specific definitions (BC's path counts, SSSP's distance), drafted after the freeze.
- Assumption (not decided in the map): this ticket writes the shared files plus the CSR fixture's and calibration fixtures' per-contract files. Real contracts' files come with their contracts (31 for `bfs_read_offload`).
- Why a count argument: 16 item 2 admits only a recursive call on `n-1` of a non-negative integer argument, under a guard `n <= 0`. A sum over `[lo, hi)` that recurses on `hi` fails that rule.
- Assumption (not decided in the map): the `\false` check result is a proof record (subject: a method part for the shared library; a contract-proof part for a per-contract file).
- Assumption (not decided in the map): if a sum lemma needs induction, its `Wp.induction` script is saved and replayed on every run, as map ticket 11 item 7 does for lifting lemmas. Once-proven parts may be human-assisted under the same hint rules (10 item 8).
- Assumption (not decided in the map): "tested on the calibration suites" means the suite tasks that sum over a range. If a suite has none, the answer says so and the CSR fixture carries the test.
- WP not proving `\false` is evidence, not a consistency proof. The main guard stays the contract proof's negative controls: an inconsistent library makes every control prove, which voids the contract proof (16 item 9).
- Risk (design spec, "Further Notes"): WP may not handle real-valued sums at our sizes. Spike (d) tests this first; if it fails here, re-plan with Yan-Ru.
- The library is reviewed at promotion (13 item 12). The shared part, with the sum library, belongs to the method version.
- Held-out kernels (BC, PR, SSSP) are never proven or used for calibration before the freeze (59 — Method-version review and freeze).
- WP runs fail inside the Bash sandbox (the Why3 socket is blocked); run WP jobs outside it.

## Answer

2026-10-14 16:40 ET. **Resolved, with one acceptance box not met** (the calibration suites: they are not on the
Mac; see "Not done"). Branch `probata-poc/t26`. Interface doc:
[`format-v0.4-logic-library.md`](../../../docs/reference/format-v0.4-logic-library.md).

**What was built**

| Piece | Where |
|---|---|
| Shared logic files, version 1.0: CSR graph model, set helpers, accessors (`at(parent, v)`), the sum library | `library/logic/{csr_graph,sets,access,sum}.acsl` |
| The sum library's proof hints and saved WP scripts (11 `Wp.induction`/`Wp.lemma` scripts, replayed every run) | `library/logic/proofs/sum/` |
| Versions (`// version:` first line), an entry's own file beside its YAML (ID `logic.<entry ID>`, only that entry uses it), a Frama-C type check per file | `swdb/logic_library.py`, `swdb/formal_frame.py`, `swdb/cli.py` |
| `pins.logic` `[{id, version, sha256}]` in every proof record whose formal halves use logic files | `swdb/proof.py`, `schemas/proof.schema.json`, `swdb/db.py` |
| Level rule: a changed file stops the record counting; a shared file with lemmas needs a counting `logic_lemmas` record; a failed `\false` check voids its version | `swdb/level_rule.py` |
| `swdb prove-logic` (`--lemmas`, `--false-check`, `--program`; `--file` checks a proposed version) | `swdb/logic_library.py` |
| Part names `logic_lemmas`, `logic_false_check` (`voids: logic`), `contract_logic_lemmas`, `contract_logic_false_check` | `vocab/proof_part_names.yaml` |
| WP adapter: `-wp-prop=-@lemma` (library lemmas are proven once, with the method); an entry's own file at `ghost.globals` | `swdb/wp_adapter.py` |
| CSR fixture: nested pull-sum and flattened pull-sum, one seeded bug each | `tests/fixtures/logic/csr_pull_sum{,_flat}.c` |

**Acceptance, box by box**

- [x] Shared files with versions; `swdb validate` accepts them and Frama-C type-checks each ("4 logic file(s)
  type-checked"). A fixture contract's own file beside its YAML loads the same way; another entry using it is refused.
- [x] Pins: `swdb prove` writes `pins.logic` (version and sha256). Editing `access.acsl` makes the record stale
  (pin `logic`); a re-run records the new pin and counts; the old one stays stale.
- [x] First: `range_sum`/`sum_n` and `filtered_sum`/`fsum_n` recurse on a count `n` under `n <= 0` and pass 20's rule;
  the control (a sum over `[lo, hi)` recursing on `hi`) is refused.
- [x] Every file passes 20's rules in `swdb validate`; 20's negative controls are cited, not re-tested (still green
  in `tests/test_formal_frame.py`).
- [x] `\false` check per version: passes on all four shipped files (Alt-Ergo/Z3/CVC5 time out at 10 s each; peak
  1.2 GB). Negative control: `logic.sum` 1.1 = 1.0 plus map 13's `pbad`, run with `--skip-subset-check`: WP proves
  `\false` (Alt-Ergo, 18 ms), the record is refuted, the version is refused (exit 1), and a proof pinning it is void.
  20's rule refuses the same file first without the bypass.
- [x] Sum library over reals by count recursion; additivity, regrouping (per owner and total) and permutation
  proven in WP with `-wp-model +real`, recorded as method part `logic_lemmas`: 17/17 goals, fresh session, scripts
  replayed. Slowest: `REGROUP_TOTAL`, about 12.5 s (Alt-Ergo, inside its induction script); job about 66 s, 0.8 GB.
- [x] CSR fixture: the nested unit and the flattened unit (one flat edge loop, through `REGROUP_OWNER`) prove
  against the same `UNIT` postcondition (30 and 38 goals; slowest 0.82 s, `PARTIAL` preserved). Each seeded bug
  reads not proven (`timeout`), never refuted.
- [ ] **Calibration suites: not met.** Code2Inv, X509-parser and Frama-C-problems are not on the Mac (ticket 38
  installs them). The CSR fixture carries the test, as the Notes allow when a suite is missing. Assumption: the
  suite tasks go through `swdb prove-logic --program <task.c> --uses logic.sum` once 38 has them.
- [x] No test, fixture or record uses BC, PR or SSSP code. Agent time on the sum library: see below.
- [x] Every WP job ran inside the machine-wide lock (`verifier_lock` nested in `verifier_run.py`), one at a time,
  under the 8 GB watchdog; WP tests skip without Frama-C 33.0 or clang 22.1.8.

**Agent time (RQ3, the sum library's one-time cost):** spike (d) about 2.5 h (ticket 08) plus about 0.5 h here
(port, the `\max`/`\min` rewrite the subset needed, script regeneration, replay). Ticket 26 as a whole: about
1.1 h of agent wall time (Claude Code subagent), 2026-10-14 15:35 to 16:40 ET, of which about 25 min waited on
the shared verifier lock.

**Tests** (Mac, serial, no xdist; WP tests inside `verifier_run.py`, sandbox off):
- `tests/test_logic_library.py`, `test_formal_frame.py`, `test_wp_adapter.py`, `test_level_rule.py`,
  `test_proof_records.py`, `test_format_doc.py`, `test_db.py::test_every_table_and_column_is_documented`, one run
  inside `verifier_run.py`: **234 passed, 5 failed** in 17 min (peak 1.4 GB). Log
  `/tmp/claude/probata-runs/t26/pytest-full1.log` (sha256 `4d6188b161a0d465`...), report log
  `/tmp/claude/probata-runs/t26/report-full1.jsonl` (`e1a0f1f01fa03ed5`...).
- After merging the integration tip (`2b3f39dd`): the same set again, **234 passed, 5 failed** (the same 5) in
  17 min. Log `/tmp/claude/probata-runs/t26/pytest-merged.log` (`4bb2f3642dcede24`...), report log
  `/tmp/claude/probata-runs/t26/report-merged.jsonl` (`db8429e4cffb1229`...).
- The 5 failures are the `test_level_rule.py` proof-semantics cases that ticket 21 found failing on the
  integration tip before this ticket ("entry ID requires prefix semantics."; 10's fixtures vs 20's
  `proof_semantics` kind). Same names, same message; not caused here.
- `tests/test_formal_frame.py` changed (stale under this ticket): its fixture logic files gained the version line,
  and its unchecked counts leave out the new per-file logic lines.
- WP experiments and run output: `/tmp/claude/probata-runs/t26/` (e1: script generation and replay; e2: `-wp-prop`
  check; e3: the `\false`-check design with and without `pbad`). Pytest temp folders there are disposable after merge.

**Assumptions** (new; the Notes' assumptions are implemented as written):

- Assumption: a file's version is its first line `// version: <dotted numbers>`; older versions live in git, and a
  record pins version plus sha256.
- Assumption: an entry's own file is `<entry file>.acsl` beside the YAML, ID `logic.<entry ID>`; only that entry may
  list it; its proofs are contract-proof parts, so the level rule's contract-part rule covers them.
- Assumption: a lemma file's hints live outside the `.acsl` (the subset refuses `\wp::` annotations in a logic file):
  `library/logic/proofs/<name>/hints.acsl` and `script/*.json`.
- Assumption: the `\false` check is one generated lemma that mentions every definition through uninterpreted
  wrappers, after the file's lemmas (WP sends only mentioned definitions, research 13 Q2). Verdict `proven` = no
  solver proved `\false` within 10 s per solver (evidence, not a consistency proof); `refuted` = WP proved it.
- Assumption: a refuted `\false` check voids every record pinning that file sha256, even a version that is not
  (or never was) the library's file.
- Assumption: logic-part records carry bounds `{threads: unbounded}` (a logic fact never caps a level).
- Assumption: the CSR fixture and calibration tasks are `calibration_program` subjects, proven by
  `swdb prove-logic --program` on hand-written C. The C lowering refuses floating point (ticket 24's subset), so a
  real-valued unit cannot go through `swdb prove --adapter wp` yet.
- Assumption: the WP adapter always passes `-wp-prop=-@lemma` (hint files cannot hold lemmas, so nothing else changes).

**Interface notes**

- 30: write reference definitions as logic files (shared or the entry's own); prove their lemmas with
  `swdb prove-logic --lemmas`; candidate records then pin them and depend on that record.
- 40: the bucketed-relaxation fixture can reuse `logic.csr_graph` and `logic.sum` and the `--program` route.
- 44: put the shared-action kinds' commutativity lemmas in a logic file with hints in `proofs/<name>/`; generate
  scripts with `--generate-scripts`, then replay with `--lemmas`.
- 24: float types and literals in the C lowering are what a real-valued unit needs to go through `swdb prove`.
- 21/36: the per-candidate WP run excludes lemma goals; 36's full reading should keep that.
- Method version (main session): `logic_library` should pin the four files (sum library = `logic.sum` 1.0) once a
  real `library/methods/` file exists.

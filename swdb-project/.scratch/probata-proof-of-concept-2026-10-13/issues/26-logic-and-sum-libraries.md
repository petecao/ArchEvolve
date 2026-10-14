# 26 — Logic and sum libraries

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
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

# 35 — Hint records, merger and proof hint check

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 20:41 ET (resolved; Answer below); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Hint form, Vocabulary, Three checks; "Testing Decisions", seam 1, the seven WP fact files; user stories 28, 29, 34; S1); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 2, 4, 5, 7, 8, 12), [24](../../formal-verification-2026-10-09/issues/24-alignment-hint-kind.md) (items 1, 7: no alignment hint kind; vocabulary unchanged)
**Time estimate:** about 3 days

**What to build:** Proof hints become data: `{anchor, kind, text}` records. A deterministic merger
inserts them at the anchors the C lowering generates. Before a merged unit can reach WP, the proof
hint check judges the hint set: every anchor exists; every kind is on the versioned vocabulary
list; the text parses with Frama-C's ACSL parser and its syntax tree is checked (not a regex);
erasing the hints gives back the lowering unchanged. Every rejection is recorded by rule. The seven
WP fact files of map ticket 13 and a set of planted bad hints are the negative controls; every
allowed kind is accepted. Tested through `swdb prove` with fixture hint sets and a scripted
verifier adapter, plus real Frama-C for the parser (skips cleanly when missing). No provider and no
loop are needed (34 and 37 come later).

## Acceptance

- [ ] **Record shape.** A hint set is a list of `{anchor, kind, text}` records with provenance per
      hint: agent, seed (with its source) or human. A proof record that carries one passes
      `swdb validate` and `swdb build`; a record with a missing field fails.
- [ ] **Deterministic merger.** The same lowering and hint set give a byte-identical merged unit and
      the same hint-set hash on every run.
- [ ] **Anchors.** A hint at an anchor the lowering did not generate is rejected under the anchor
      rule.
- [ ] **Vocabulary, versioned.** Allowed: `loop invariant`, `loop assigns`, `loop variant` with an
      integer measure, `assert`, ghost declarations and statements, non-recursive
      `predicate`/`logic` definitions, `lemma` (proven in the same run; 36's verdict reading enforces
      that), `\wp::strategy` hints. A fixture hint set with one hint of each allowed kind passes. A
      kind on no list (for example `check`) is rejected: the map rejects everything not allowed.
- [ ] **Syntax tree, not regex.** Each text parses with Frama-C's ACSL parser and its tree must match
      the declared kind. Controls: a `loop invariant` record whose text also holds an `admit`; a
      "non-recursive" `logic` definition that refers to itself; an `admit` split by line breaks and
      comments; a ghost statement that writes real memory (Frama-C's kernel refuses it at its
      default `ghost:bad-use` level; erasing it would leave the lowering unchanged, so erase-and-diff
      cannot be what catches it). All rejected by rule.
- [ ] **Erase-and-diff.** Removing the merged hints gives back the lowering byte for byte. Control:
      a text that closes the annotation comment and adds C code is rejected by this rule.
- [ ] **Fact-file controls.** Every hint-borne escape hatch in the seven WP fact files of map ticket
      13 is rejected, each under its own rule: interfering ghost code; recursive and `inductive`
      definitions; every `admit` form; `axiom`; contracts (`requires`, `ensures`, `assumes`,
      `behavior`); ghost functions; body-less declarations; `loop variant … for R`;
      `import \wp::why3:`; `\from`; `global invariant`; `volatile` clauses; statement contracts.
- [ ] **Planted bad hints.** A stored set of planted bad hints (at least one per rejected kind and
      per rule above) is each rejected by its rule. Through `swdb prove`, a rejected set never
      reaches WP, and the proof record lists every rejected hint with its rule.
- [ ] **WP only.** A merged hint set goes only to the WP adapter. Control: `swdb prove` refuses a
      hint set on a bounded-verifier job (map 13 item 2; user story 28).
- [ ] **Versions on every result.** Each check result names the check version and the vocabulary
      version.

## Notes

- **Not in this ticket:** 21 — C lowering and WP adapter (A2 tracer) (generates the anchors: function
  entry, each loop head, before and after each statement, one ghost-globals slot); 34 —
  proof_hinting role and workspace (the agent that writes hints and the wrapper that exposes this
  check); 36 — Proof setup check and verdict reading (flags, cache, report statuses, smoke tests,
  and that every lemma is proven in the same run); 37 — The proof-hint loop (a rejected set uses up
  its round, reasons go back to the agent, seeds dropped Houdini-style); 26 — Logic and sum
  libraries (the only home of recursive or inductive definitions); 11 — Method-version file and
  failure classes (the method-version file cites the vocabulary and check versions).
- Not hint-borne, so not this check's controls: the WP cache, flags, report statuses and smoke tests
  (fact files on report statuses, tactic scripts and smoke tests). They are ticket 36's controls.
  The fact files are listed in
  [research 13](../../formal-verification-2026-10-09/research/13-wp-hint-facts.md).
- Yan-Ru may revise the vocabulary later (map 13 item 5). Any change makes a new vocabulary version.
- Assumption (not decided in the map): the hint-set hash is taken over the records in a canonical
  order, so record order does not change it.
- Assumption (not decided in the map): a `\wp::strategy` hint may name only WP's predefined tactics
  and provers. Research 13 Q5: custom tactics can break soundness; they load only from command-line
  plug-ins, which ticket 36's frozen flags exclude.
- Assumption (not decided in the map): rule names and the vocabulary file's name and location are
  set here; the method-version file cites them.
- Assumption (not decided in the map): `swdb prove` takes a hint set as an input, as a contract
  proof's human hints need (map 13 item 12). That makes this check testable before 34 and 37.
- Assumption (not decided in the map): outside the loop, a job whose only hint set is rejected runs
  WP without it and records the rejections. No failure class names "hint set rejected"; inside the
  loop a rejection just uses up its round (37). If Yan-Ru wants a class for it, it joins the
  failure-class list (11) first.

## Answer

2026-10-14 20:41 ET. **Resolved.** Every acceptance box is met through `swdb prove --adapter wp` (seam 1) and `swdb validate` /
`swdb build` (seam 4), with real Frama-C 33.0 parsing every hint and the scripted WP stand-in of ticket 21 for the
WP run. Branch `probata-poc/t35`. Interface doc:
[`format-v0.4-proof-hints.md`](../../../docs/reference/format-v0.4-proof-hints.md).

**What was built**

| Piece | Where |
|---|---|
| Hint records `{anchor, kind, text, provenance}`, hint-set hash, deterministic merger, C-level erase, the check (`judge`, and `check(base, anchors, hints)` for 34's wrapper) | `swdb/hint_check.py` |
| Frama-C syntax-tree reader (an OCaml module compiled with the switch's `ocamlfind`, loaded with `-load-module`; prints every annotation node with its lines) | `swdb/hint_tree.ml` |
| Versioned vocabulary (kinds with anchor kinds, merge rank, tree nodes) and the rules | `vocab/proof_hint_kinds.yaml`, `vocab/proof_hint_rules.yaml` (pinned: `proof-hint-vocabulary-1`) |
| WP adapter runs the check before WP; a rejected set never reaches WP; record fields `hint_set`, `hint_check`; reports `hints`, `hints_merged`, `hint_check` | `swdb/wp_adapter.py`, `swdb/proof.py`, `schemas/proof.schema.json` |
| Any non-WP adapter refuses `--hint-file` | `swdb/proof.py` |
| Fixtures: one hint of each allowed kind; planted bad hints (4 sets, every rule, the fact files) | `tests/fixtures/proof/hints/` |

**Acceptance, box by box**

- Record shape: a record with the hint set (provenance per hint: agent, seed with `seed_source`, human) passes
  `swdb validate` and `swdb build`; deleting a hint's `provenance` fails validate; a hint file missing any field
  is refused with nothing written.
- Deterministic merger: three runs (same set twice, once reordered across anchors and kinds) give the same
  hint-set hash, the same merged-unit sha256 and byte-identical `hints_merged` files.
- Anchors: a hint at `loop9.head` is rejected `unknown_anchor`; WP ran without any hint (`hint_count` 0).
- Vocabulary, versioned: the every-kind fixture covers all 9 kinds and is accepted; `check`/`requires` kinds are
  `kind_not_allowed`; a loop invariant at a statement anchor and a lemma at a loop head are `anchor_kind_mismatch`.
- Syntax tree, not regex: `loop invariant` plus `admit loop invariant` → `admit`; self-referring `logic` →
  `recursive_definition`; `admit` split by line breaks and `//` comments → `admit`; ghost write to `a[i]` →
  `interfering_ghost_code` (Frama-C's `ghost:bad-use`). Text of the wrong kind → `kind_mismatch`.
- Erase-and-diff: a text that closes its comment and adds code, one that adds a plain comment, and one with a
  line splice are each `erase_and_diff`; the injected code is not in WP's input.
- Fact-file controls and planted bad hints: `tests/fixtures/proof/hints/planted_bad_hints.yaml` holds 42 planted bad
  hints (plus 6 support hints) in 4 sets (one `swdb prove` each); every rule of `proof_hint_rules` is planted (a test checks the coverage), with the
  q1, q2, q3, q4 and q7 fact files' hint-borne escape hatches: ghost writes to real memory, ghost
  break/return/real call/cast (`interfering_ghost_code`); recursive logic and predicate, inductive; admit assert,
  admit loop invariant, admit lemma, axiom, axiomatic; check assert/lemma/loop invariant; contracts with
  requires/ensures/assumes/behavior and admit requires; ghost functions with and without a body; body-less logic
  and reads-only predicate; `loop variant … for R`; `import \wp::why3:`; `\from`; global invariant; volatile
  clause; statement contract; unbounded loop assigns; logic type and `calls` (`not_on_vocabulary`); an unknown
  WP tactic (`wp_generation_error`). Each is rejected by its rule, every rejection names its hint, the set never
  reaches WP (none of its annotations is in WP's input) and the record passes `swdb validate`. The largest set
  needed 17 Frama-C runs. q5 (tactics) and q6 (smoke tests) are not hint-borne (ticket 36).
- WP only: `swdb prove --adapter scripted --hint-file` exits non-zero ("only to the WP adapter"), no record.
- Versions: every result names `proof-hint-check-1` (sha256 of `hint_check.py` + `hint_tree.ml`) and
  `proof-hint-vocabulary-1` (sha256 of the two vocabulary files).

**Tests** (Mac; serial, no xdist, `-m "not whole_store"`; pytest outside the verifier lock, every Frama-C/WP job
takes it per job; sandbox off for Why3):

- After merging the integration tip `2dff3f58`: `tests/test_proof_hint_check.py`, `test_wp_adapter.py`,
  `test_format_doc.py`, `test_proof_hinting.py`: **100 passed** (99 in one run, plus the wrapper test rerun alone
  after a 120 s test timeout hit while the check queued for the lock). Report logs
  `/tmp/claude/probata-runs/t35/report-merged.jsonl` (sha256 `63011a4d709e0979`...) and `report-wrapper.jsonl`
  (`471aa4950f4cf201`...). Wall time was dominated by lock queues (up to 9 waiters).
- Before that merge (tip `bedb57c7`): `tests/test_logic_library.py`, `test_proof_records.py`: **59 passed**
  (`report-final3.jsonl`, `5ac6374c1f7640c4`...).
- Run output: `/tmp/claude/probata-runs/t35/` (pytest temp folders, explore files; disposable after merge).

**Assumptions** (beyond the ticket's Notes, which are implemented as written; the canonical-order one refined):

- Assumption: canonical order is anchor order, then the kind's rank, then the set's own order. Two hints of equal
  rank at one anchor keep their order (ACSL and ghost code are declare-before-use), so only that reorder changes
  the hash. Provenance is not hashed.
- Assumption: the hints of one loop head share one annotation comment (Frama-C 33 refuses a second loop comment:
  "syntax error"), each hint on its own lines.
- Assumption: kind names are snake_case (`loop_invariant`, ..., `wp_strategy`) and the text holds the ACSL keyword.
  `wp_strategy` covers `\wp::strategy` and `\wp::proof` (a strategy does nothing unattached; Wp.lemma and
  Wp.induction hints of ticket 08 both pass). WP keeps tactic names out of the tree; an unknown tactic is
  caught by the WP goal-generation stage (`wp_generation_error`).
- Assumption: Frama-C's tree makes every axiom an admit lemma, so an `admit lemma` is rejected as `axiom`; a
  non-integer loop variant is refused by the kernel's type check (`parse_error`), so no separate rule.
- Assumption: a hint relying on a rejected hint (for example a name it declares) is itself rejected (`parse_error`).
- Assumption: "Ghost code breaks CFG starting at" names the statement where the CFG change starts (often real
  code), so that error is blamed by removal (ghost hints first, nearest first); other errors by line.
- Finding: Frama-C drops an unused body-less prototype, so an unused body-less ghost function leaves no node
  (`kind_mismatch`); a called one without a contract is refused by the kernel ("No definition, nor assigns
  specification for ghost function": `interfering_ghost_code`); a called one with a contract is `ghost_function`.

**Not done, and why**

- No DB table for rejections: `swdb build` stores the full record JSON in `swdb_proofs`, which the evaluation's
  escape-hatch count (map 13 item 8) can query; a table can follow when 37 needs it.
- The method-version file does not yet cite the check and vocabulary versions (tickets 11/59 own the file).

**Side findings**

- 34's prompt and fixtures describe hints as `{kind: "loop invariant", text: "0 <= i <= n;"}`; the record shape is
  now `{kind: loop_invariant, text: "loop invariant 0 <= i <= n;"}` (vocabulary values). 34's prompt should list
  the kind values; its plan hash-pins only `hint_check.py`, not `hint_tree.ml` (use `hint_check.identity()`).
- 34's `base` must keep anchor lines: build it with `hint_check.wp_base(lowering, anchors, context)`.
- Incident (2026-10-14 ~17:10 ET): one of my earlier test runs held the machine-wide lock across a pytest batch,
  and a loop bug of mine (a shadowed variable in the merger, since fixed) grew it to 8 GiB before the watchdog
  killed it. Later runs follow the new rule: pytest outside the lock, the code takes it per job (`swdb prove`,
  and `hint_check.check` takes it itself for the wrapper path).

**Interface notes**

- 34: `check=(swdb/hint_check.py, "check")`; `check(base, anchors, hints) -> {passed, rejections[{hint, anchor, kind,
  rule, detail}], merged, ...}`; anchors may be the anchors.json mapping; hints need no provenance.
- 36: lemmas proven in the same run and strategy flags (`tip`) are the verdict reading's; `hint_check.rejections`
  uses vocabulary `proof_hint_rules`.
- 37: `hint_check.judge(base, anchors, hints, workdir, wp_flags=)`; `accepted` lists indices reaching WP (all or
  none); seeds are records with `provenance: {source: seed, seed_source}`; drop a failing seed by index.
- 38: calibration hint sets use the same records and check.

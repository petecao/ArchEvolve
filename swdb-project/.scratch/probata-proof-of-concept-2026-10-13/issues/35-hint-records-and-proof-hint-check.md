# 35 — Hint records, merger and proof hint check

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
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

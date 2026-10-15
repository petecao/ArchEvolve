# Hint records, the merger and the proof hint check

Created: 2026-10-14 ET, Probata proof of concept ticket 35.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/35-hint-records-and-proof-hint-check.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Proof-hint loop": hint form, vocabulary, three checks), map 13
items 2, 4, 5, 7, 8, 12; map 24 items 1, 7.
Code: `swdb/hint_check.py` (records, merger, check), `swdb/hint_tree.ml` (the Frama-C syntax-tree reader),
`swdb/wp_adapter.py` (where the check runs). Vocabularies: `vocab/proof_hint_kinds.yaml`, `vocab/proof_hint_rules.yaml`.
Tests: `tests/test_proof_hint_check.py`.

**In one line:** a hint is data, `{anchor, kind, text, provenance}`; a deterministic merger puts it at a C
lowering anchor; the proof hint check reads Frama-C's syntax tree of every hint and lets a hint set reach WP only
when every hint is exactly an allowed kind.

## The hint file and a hint record

```
swdb prove ... --adapter wp --hint-file <hints.yaml>
```

```yaml
hints:
  - anchor: swdb_fixture_fill.loop1.head      # an anchor of <f>.anchors.json
    kind: loop_invariant                     # a value of vocabulary proof_hint_kinds
    text: "loop invariant 0 <= i <= n;"      # the ACSL, keyword included
    provenance: {source: agent}              # agent | seed | human
  - anchor: ghost.globals
    kind: lemma
    text: "lemma twice_nonneg: \\forall integer x; 0 <= x ==> 0 <= twice(x);"
    provenance: {source: seed, seed_source: contract.fixture_wp_fill}
```

- Every record has exactly `anchor`, `kind`, `text` and `provenance`; a missing or extra field refuses the file
  (`swdb prove` exits 1, nothing written).
- `provenance.source` is `agent` (the proof-hint agent), `seed` (with `seed_source`: the contract proof or
  proven candidate it came from) or `human` (a contract proof's hints, map 13 item 12).
- **WP only.** Any adapter other than `wp` (a bounded-verifier job) refuses `--hint-file` (map 13 item 2).

## The merger

- Each hint becomes one ACSL annotation comment `/*@ <text> */` on its own lines, right after its anchor line
  (anchor lines stay). The hints of one loop head share one comment, each hint on its own lines: Frama-C takes
  a loop's annotations from one comment only.
- **Canonical order:** anchors in lowering order, then the kind's `rank` (vocabulary field), then the hint set's
  own order. Reordering hints across anchors or kinds changes nothing; two hints of equal rank at one anchor
  keep their order (ACSL and ghost code are declare-before-use).
- WP's input is the same merge with the contract at `<f>.contract` and the logic files at `ghost.globals`,
  inserted before the hints at their anchor.
- **Hint-set hash** (`hint_set.sha256`): sha256 of the records' `anchor`, `kind` and `text` in canonical order
  (provenance aside, so a seed and an agent hint with the same text hash alike).

## The proof hint check

Stages, in order; every rejection is recorded with a rule of vocabulary `proof_hint_rules`. **One rejection
rejects the whole set**: it never reaches WP, which then runs without hints (assumption, ticket 35), and the
record lists every rejected hint with its rule.

1. **Record:** the anchor exists (`unknown_anchor`), the kind is on `proof_hint_kinds` (`kind_not_allowed`;
   the vocabulary rejects everything it does not allow), the kind may sit at that anchor kind
   (`anchor_kind_mismatch`).
2. **Erase-and-diff** (`erase_and_diff`): erasing the annotation comments from the merged unit (a C lexer:
   comments, strings, line splices) gives back the C lowering byte for byte (the erased WP input without hints,
   which is the C lowering's code), per hint and for the set.
   A text that closes its comment and adds code, a plain comment or a line splice fails here.
3. **Parse:** Frama-C 33.0 parses and type-checks the merged unit with the contract and logic files, default
   warning levels (`annot-error` and `ghost:bad-use` abort). Each error line is blamed on the hint whose lines
   hold it (or the hint block right above it); that hint is rejected (`interfering_ghost_code` for ghost code
   that writes real memory, changes real control flow or calls a real function; else `parse_error`) and the
   parse repeats without it. "Ghost code breaks CFG starting at" names the statement where the change starts
   (often real code), so that error is blamed by removal: the first hint (ghost hints first, nearest first)
   whose removal makes it go away. An error no hint explains rejects the set (`parse_error`, `hint: null`).
4. **Syntax tree:** the Frama-C module `hint_tree.ml` (compiled with the switch's `ocamlfind` and loaded with
   `-load-module`) prints every annotation node with its lines. Each node is given to the hint whose lines hold
   it and judged: `admit`, `check`, `axiom`, `recursive_definition`, `inductive_definition`,
   `bodyless_declaration`, `contract`, `statement_contract`, `ghost_function`, `variant_relation`,
   `import`, `from_clause`, `global_invariant`, `volatile_clause`, `unbounded_range`, `not_on_vocabulary`.
   A hint whose tree is not exactly its declared kind (another kind, more than one annotation, none) is
   `kind_mismatch`. Frama-C's tree makes every axiom an admit lemma, so an `admit lemma` is rejected as `axiom`;
   a non-integer loop variant never reaches the tree (the kernel's type check refuses it: `parse_error`).
5. **WP goal generation** (`wp_generation_error`): WP with the method version's frozen flags and
   `-wp-prover none` generates the goals of an otherwise accepted set (spike (c): WP refuses some sets the
   parser accepts). Errors are blamed like stage 3.

| Kind (`proof_hint_kinds`) | Anchor kinds | Syntax tree it must be |
|---|---|---|
| `loop_invariant` | `loop_head` | one loop invariant, not admit or check, for no behavior |
| `loop_assigns` | `loop_head` | one loop assigns, bounded ranges, no `\from` (one per loop) |
| `loop_variant` | `loop_head` | one loop variant, integer measure, no `for R` |
| `assert` | `entry`, `before`, `after` | one assertion, not admit or check |
| `ghost` | `ghost_globals`, `entry`, `before`, `after` | ghost variables and ghost statements only |
| `predicate`, `logic` | `ghost_globals` | one non-recursive definition with a body |
| `lemma` | `ghost_globals` | one lemma, not admit or check (ticket 36 requires it proven in the same run) |
| `wp_strategy` | `ghost_globals` | one `\wp::strategy` definition or `\wp::proof` attachment |

- `wp_strategy`: WP keeps a strategy's tactic and prover names outside the syntax tree, so the tree check
  cannot read them. Only WP's predefined tactics exist because the frozen flags load no tactic plug-in
  (research 13 Q5). A strategy has effect only when WP runs with a `tip` prover (ticket 36's flags).

## What the proof record holds (on top of [format-v0.4-c-lowering-wp.md](format-v0.4-c-lowering-wp.md))

| Field | Meaning |
|---|---|
| `hint_set` | `sha256` (the hint-set hash) and `hints` (the records as given, each with `provenance`) |
| `hint_check`: `check` | `{id: proof-hint-check-<N>, sha256}`; the sha256 covers `swdb/hint_check.py` and `swdb/hint_tree.ml` |
| `hint_check`: `vocabulary` | `{id: proof-hint-vocabulary-<N>, sha256}` of `proof_hint_kinds.yaml` + `proof_hint_rules.yaml` |
| `hint_check`: `verdict` | `accepted` or `rejected` |
| `hint_check`: `rejections` | per rejection: `hint` (index in `hint_set.hints`, `null` for the set), `anchor`, `kind`, `rule`, `detail` |
| `hint_check`: `merged_sha256` | sha256 of the merged unit (lowering plus hints; the `hints_merged` report) |
| `hint_check`: `frama_c_runs` | Frama-C runs the check made (parse repeats, WP goal generation) |
| `hint_check`: `reached_wp` | whether the hints reached WP (true only when accepted) |
| `settings.hint_count` | hints that reached WP |
| `evidence.reports` | adds `hints` (the hint file), `hints_merged` (the merged unit), `hint_check` (the full result) |

**Versions.** `VOCABULARY_VERSION` in `swdb/hint_check.py` pins the two vocabulary files' sha256: a changed file
without a new version stops the check ("changed ... without a new version"). Any change to the vocabulary
(map 13 item 5: Yan-Ru may revise it) is a new vocabulary version; any change to the check's code changes its
sha256. The method-version file cites both (tickets 11, 59).

## For later tickets

- 34 (`proof_hinting` role): the frozen wrapper's check is `check=(<path of swdb/hint_check.py>, "check")`:
  `check(base, anchors, hints) -> {passed, rejections: [{hint, anchor, kind, rule, detail}], merged, ...}`, where
  `base = swdb.hint_check.wp_base(lowering_text, anchors, context)` (WP's input without hints; anchor lines kept,
  so the anchors still exist; ticket 21's old `_input` dropped them) and `anchors` the list or the whole
  `<f>.anchors.json`. Hints need no provenance there. It runs no WP goal generation (prove_hints runs WP).
- 37: `swdb.hint_check.judge(base, anchors, hints, workdir, wp_flags=)` is the full check with goal generation
  (what `swdb prove` runs); `accepted` lists the indices that reach WP.
- 36: the lemma rule (proven in the same run) and the strategy flags are the verdict reading's; a hint set adds
  no `Extern`.
- 37: a rejected set uses up its round; seeds are hint records with `provenance.source: seed`; drop a failing
  seed Houdini-style by index.
- Regression corpus: a case may name `hint_rule` (the check's rule) instead of a WP failure class when the check
  catches the failure before WP; such a case runs with the scripted WP stand-in.

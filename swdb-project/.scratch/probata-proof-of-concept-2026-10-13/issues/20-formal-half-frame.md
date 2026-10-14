# 20 — Formal-half frame

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 14:20 ET (resolved; Answer appended); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 09
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Formal-half language and the C++ subset": allowed ACSL and the YAML frame; "Proven once vs per candidate": proof placement; "Proof routes": an offload-only contract's required enabling contracts; "Concurrency": shared-action kinds and history reads; "DX100 proof semantics": a gem5 citation or an owner per rule; "What a proven verdict asserts": the seven assumption kinds; "Testing Decisions", seam 4); decisions: [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 2, 4, 13; [17](../../formal-verification-2026-10-09/issues/17-enabling-rewrites.md) item 5; [10](../../formal-verification-2026-10-09/issues/10-proven-rewrite-contract.md) item 4; also [15](../../formal-verification-2026-10-09/issues/15-concurrency-proofs.md) item 5 (the kinds), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) item 4 (assumption kinds), [12](../../formal-verification-2026-10-09/issues/12-dx100-proof-semantics.md) item 1 (citations)
**Time estimate:** about 2 days

**What to build:** A contract author (an agent or Yan-Ru) writes formal halves as ACSL inside the library YAML, and `swdb validate` says at once whether the frame is complete and the ACSL is well formed. Each clause gains an `acsl` field (the text plus the logic-library entries it calls) and a required proof placement: `once: <entry>@<version>` (or `once: self` for an entry's own clauses), `per_candidate`, or `assumed` with its kind, its rule or owner, and its evidence. Each rewrite contract gains its concurrency frame: for each array of the proof unit's interface, the shared-action kinds it allows and whether its reads are history reads. An offload-only contract gains its ordered list of required enabling contracts (ID and version range). Each proof-semantics rule carries `cites: {gem5 commit, path, lines}` or `assumed: {owner}`. `swdb validate` parses and type-checks the ACSL through Frama-C, enforces the full allowed-ACSL list of map 16 item 2 (clause kinds, bounded quantifiers, labels, arithmetic, built-ins, logic calls, primitive recursion, inductive definitions, no axioms), and refuses a clause with no proof placement. Every check is shown by its negative controls on fixture entries. Every later A2 ticket writes into this frame.

## Acceptance

- [x] A fixture library that uses every new field passes `swdb validate` and `swdb build`: one clause per placement form, a contract with its concurrency frame, an offload-only contract with two required enabling contracts, and one proof-semantics rule of each kind. The required-contract list reads back in its written order.
- [x] A clause with no proof placement is refused; the message names the entry and the clause ID. Placement stays separate from `discharge_mode`: a clause with `discharge_mode: differential_test` and placement `per_candidate` validates.
- [x] `assumed` placements: a kind outside the seven (assumed clause, proof semantics, summary, reduction, trusted tool, written proof, platform choice) is refused. A missing rule-or-owner, or missing evidence, is refused.
- [x] Frama-C 33.0 parses and type-checks each `acsl` text. Well-formed text passes. A syntax error and a type error (an undeclared name) are each refused, with Frama-C's message attached.
- [x] Allowed ACSL (16 item 2): each rule below is enforced by `swdb validate` and shown by its negative control.
- [x] Clause kinds: `requires`, `ensures`, and `assigns` with index ranges pass. A named `behavior` and `assigns \everything` are each refused.
- [x] Quantifiers: a first-order quantifier bounded by an integer range passes. Each of these is refused: a `\forall integer k` with no range guard; a quantifier over a `real` variable; a `\lambda` (and so ACSL's built-in `\sum`).
- [x] Labels: `\old` and `\at(..., Pre)` pass. `\at` with any other label (for example `Post`, or a C label) is refused.
- [x] Arithmetic: integer and `real` arithmetic pass. A floating-point logic built-in (for example `\round_double`) is refused.
- [x] Built-ins: `\valid`, `\separated` and `\result` pass. Any other memory built-in (for example `\block_length` or `\initialized`) is refused.
- [x] Logic calls: a call to a definition in a logic-library entry the clause lists passes. A call to a logic name defined in the formal half itself, or in no listed entry, is refused.
- [x] Recursion rule: a non-recursive definition passes; a primitive-recursive one passes (the recursive call takes `n-1` of a non-negative integer argument, with a base case for `n <= 0`). Each of these is refused: `pbad(x) = !pbad(x)`; a recursive call on `n+1`; a recursion with no base case.
- [x] Inductive definitions: one used by a lemma inside a logic-library file passes. An inductive definition written in a formal half, and a formal half that calls an inductive predicate, are each refused.
- [x] `axiom` is refused, both in a formal half and in a logic-library file the formal half calls.
- [x] Concurrency frame: each of the five kinds (claim, min-update, atomic add or OR, OpenMP reduction, queue reserve) passes. An unknown kind is refused. The history-read flag accepts only yes or no.
- [x] Offload-only frame: a required contract with an unknown ID, or a malformed version range, is refused. An enabling contract that lists what it enables is refused.
- [x] Proof-semantics rules: a rule with `cites` passes; a rule with `assumed: {owner}` passes; a rule with neither is refused.
- [x] Tests that need Frama-C skip cleanly when it is missing. With Frama-C missing, `swdb validate` reports each `acsl` field as unchecked, never as valid.

## Notes

- **Not in this ticket:**
  - 21 — C lowering and WP adapter (A2 tracer): the lowered signature that formal halves are written over.
  - 22 — SAW adapter and SAWScript translator; 23 — C-stub translator, fallbacks and check mode: the generated forms of each formal half.
  - 26 — Logic and sum libraries: the real logic-library files, their versions and hashes, and the `\false` check. It runs this ticket's rules on every library file and cites the controls here instead of re-testing them.
  - 27 — Proof semantics for the BFS read-offload calls; 28 — Proof semantics for the remaining maa_* calls: the rules themselves.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions; 31 — Five-gate drafting and the new bfs_read_offload version: placements on real entries (for `bfs_read_offload`: L1-L4, `once_enqueue` and the knob clauses `per_candidate`; L5 `assumed`, kind proof semantics).
  - 36 — Proof setup check and verdict reading: confirms every clause has a placement before each verifier run.
  - 19 — Derived implementations: contract lineage on implementation records, which the required-enabling list is checked against. That check is not here.
  - 44 — Shared-action kinds and commutativity lemmas: the script that checks the kinds match the Rocq constructors.
  - 45 — Per-thread lowering: sharing classes per barrier interval. They are per candidate (proposed by the C lowering, proven by WP) and never appear in the YAML.
- Assumption (not decided in the map): the placement is required in entries written in the new frame (marked by a frame version). Existing entries keep validating and give no proven verdict; 36's proof setup check refuses them at proof time. New versions of real entries come in 30 and 31.
- Assumption (not decided in the map): until 21's C lowering exists, ACSL is type-checked against a hand-written C declaration of the fixture proof unit's signature, with the x86_64 machdep WP runs use. 21 switches `swdb validate` to the lowered signature.
- Assumption (not decided in the map): with Frama-C missing, `swdb validate` flags `acsl` fields as unchecked (above) instead of failing the whole run. Yan-Ru may prefer a hard failure.
- Assumption (not decided in the map): `once: <entry>@<version>` must name an entry and version present in the library.
- Assumption (not decided in the map): mutual recursion is refused. The syntactic rule cannot see a decreasing argument across functions.
- Assumption (not decided in the map): ACSL constants (`\true`, `\false`, `\null`, `\nothing`) pass, and so do `assigns \nothing` and a scalar location in `assigns`. Only `\everything` and other forms that are neither a range nor a single location are refused.
- Assumption (not decided in the map): the inductive rule is transitive. A formal half may not reach an inductive predicate through a library definition either, since the executable form can loop either way (16 item 2).
- Assumption (not decided in the map): a rule with both `cites` and `assumed` is refused. 16 item 4's "or" is read as exclusive.
- Assumption (not decided in the map): how a contract is marked offload-only or enabling (a field, or derived from its strategies) is open. This ticket adds the smallest marker the checks need.
- Assumption (not decided in the map): where proof-semantics rules live (their own library entry kind, or a section of an intrinsic entry) is open. This ticket adds the frame with a fixture entry only.
- The existing `formal` field (reference pins and Extensa predicates, for tests and probes) stays beside `acsl`. The ported Extensa grammar never feeds proofs (16 item 1).
- Frama-C lives in the opam switch `framac-33`. No Homebrew change is needed; LLVM 22 is untouched.

## Answer

2026-10-14 14:05 ET. **Resolved: every acceptance item is met**, each check shown by its negative
control in `tests/test_formal_frame.py` at seam 4 (`swdb validate --library`, `swdb build`,
`swdb sql`). The negative controls share one fixture library and one validate run; each control
is its own entry (or logic file), and the test checks that only the expected check fires for it.

**What was built**

| Piece | Where |
|---|---|
| Frame checks (marker, version, placements, concurrency frame, offload-only and enabling roles, proof-semantics rules) | `swdb/formal_frame.py` |
| Allowed-ACSL subset (map 16 item 2) for formal halves and logic-library files: syntactic, works without Frama-C | `swdb/acsl_subset.py` |
| Frama-C 33.0 parse and type check (x86_64 machdep, annotation errors fatal, message attached) | `swdb/framac.py` |
| New entry kind `proof_semantics` (`library/proof_semantics/`, prefix `semantics.`); schema fields | `swdb/library.py`, `schemas/library/library_entry.schema.json` |
| Vocabulary of the five shared-action kinds | `vocab/shared_action_kinds.yaml` |
| `UNCHECKED:` lines and counts in `swdb validate` output | `swdb/cli.py`, `swdb/validate.py` |
| Tables `swdb_library_clause_placements`, `_concurrency_frame`, `_shared_actions`, `_required_contracts` (with `position`), `swdb_proof_semantics_rules` | `swdb/db.py`, `docs/reference/database.md` |
| Interface doc for later tickets | `docs/reference/format-v0.4-formal-frame.md` |

**Tests** (Mac; runs under `/tmp/claude/probata-runs/t20/`):

- `tests/test_formal_frame.py`: **61 passed** in 7.3 s under `verifier_run.py` (peak 224 MB; Frama-C
  33.0 present, so no skip). Log `/tmp/claude/probata-runs/t20/pytest-5.log` (sha256 `4b239a49631c5eae`...),
  report log `/tmp/claude/probata-runs/t20/report-5.jsonl` (`57417350d995b423`...).
- `tests/test_format_doc.py`, `tests/test_typed_library.py`, `tests/test_library_index.py`,
  `tests/test_db.py::test_every_table_and_column_is_documented`: **88 passed** in 17.6 min, with
  `SWDB_FRAMA_C=none` and outside the verifier lock (they reach no verifier). Log `/tmp/claude/probata-runs/t20/pytest-4.log`
  (`4434be17ac7afa29`...). The 17 minutes are `test_library_index`'s record-closure copy, not
  this change.
- One regression found and fixed on the way: `clauses: 42` crashed the frame check
  (`test_malformed_types_fail_without_a_traceback`).
- No test needed the network; all outputs are under `/tmp/claude/probata-runs/t20/` (about 50 MB of pytest temp folders,
  disposable once the main session has merged).

**Assumptions** (the ticket's Notes assumptions are all implemented as written; these are new):

- Assumption: the frame is tool-neutral. The ticket names no SAWScript field, so nothing SAW-specific
  was dropped; per Yan-Ru's 13:19 ET decision the generated forms are C stubs (CBMC, ticket 22/23)
  and ACSL read as written (WP). Nothing in the frame names a verifier.
- Assumption: the frame marker is `formal_frame: 1` with a required `version` (dotted numbers, quoted
  string). Entries without it keep validating and may carry no frame field (`version` excepted,
  which ticket 19 already reads). The library had no entry versions; `once` and version ranges
  compare against this field.
- Assumption: `proof_unit: {prototype, types?}` holds the hand-written C declaration (the ticket's
  Notes assumption); the formal half is type-checked as a contract on that prototype, after the
  listed logic files. A frame entry with `acsl` must have it.
- Assumption: logic-library files are `library/logic/<name>.acsl` (plain ACSL global annotations),
  ID `logic.<name>`; every file in that folder is checked. Ticket 26 adds versions and hashes.
- Assumption: definition bodies in logic files follow the formal-half expression rules (bounded
  quantifiers, no `\lambda`, no float or other memory built-ins) because check mode executes them;
  labels are free there, and lemma and inductive-case bodies are free (proven, never executed).
- Assumption: the primitive-recursion base case is `n <= 0 ? base : step` (or `n <= 0 || step` for a
  predicate), with every recursive call passing exactly `n - 1`. A logic declaration without a body
  is refused (only an axiom could define it); so is an `axiomatic` block.
- Assumption: a quantifier guard counts only as plain comparison chains joined by top-level `&&`
  (before `==>` for `\forall`; the whole body for `\exists`). A disjunctive guard is refused
  (control `disjunct_guard`). Bounds must not mention the variable.
- Assumption: `\valid_read` is refused (map 16 lists only `\valid`); `float`/`double` type names are
  refused in formal halves (use `real`); `assigns \from` is refused.
- Assumption: a clause that breaks the subset is not sent to Frama-C (one refusal per cause).
  Frama-C runs once per entry and per clause only when the entry fails; results are cached per
  process.
- Assumption: Frama-C comes from `SWDB_FRAMA_C` (`none` disables it), else opam switch `framac-33`,
  else PATH; another version counts as missing (reported unchecked). `swdb validate` runs the
  parse-only check without the machine-wide verifier lock (about 0.4 s and 50 MB per run); test runs
  that reach Frama-C went through `verifier_run.py`.
- Assumption: `assumed.rule` is `<proof_semantics entry>#<rule id>` and must resolve; `rule` or
  `owner` (at least one) and non-empty `evidence` (text or list).
- Assumption: a required enabling contract must be a rewrite contract marked
  `contract_role: enabling`; only an offload-only contract may carry the list; ranges are
  comma-separated `>=`, `>`, `<=`, `<`, `==` bounds. Whether the named contract's current version
  satisfies the range is not checked (52 checks lineages).
- Assumption: proof-semantics rules carry `id`, `statement` and exactly one of `cites` /
  `assumed`; their ACSL text comes with 27/28 (an extra key is refused until then).

**Not done here (by design):** the concurrency frame is not yet checked against the proof unit's
pointer parameters (21, with the lowered signature).

**Interface notes:**

- 21: replace `proof_unit.prototype` with the C lowering's signature (`swdb.formal_frame._source`
  builds the check file); add the interface-array completeness check; add the real `evidence_kind`.
- 22/23: translate `acsl.text` (+ `acsl.uses` logic files) to C stubs; read placements from
  `swdb_library_clause_placements`; rule citations from `swdb_proof_semantics_rules`.
- 26: put real files in `library/logic/`; `swdb validate` already runs these rules on each file.
- 31: write the new `bfs_read_offload` version with `formal_frame: 1`, `version`, `proof_unit`,
  `concurrency_frame` (parent: claim + history reads; frontier: queue_reserve) and placements.
- 36: refuse at proof time an entry without `formal_frame` or a clause without placement.
- 52: `required_enabling_contracts` (ordered; `swdb_library_required_contracts.position`) vs
  `contract_lineage[].version`; range grammar `swdb.formal_frame.RANGE`.

# The formal-half frame of typed-library entries

Created: 2026-10-14 13:45 ET, Probata proof of concept ticket 20. Updated: 2026-10-14 15:10 ET, ticket 21
(`proof_unit` names the baseline C++ source; the formal halves type-check against its C lowering; the
concurrency frame must name every interface array). Updated: 2026-10-15 ET
(explicit initializedness predicates for WP runtime-error obligations).
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/20-formal-half-frame.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Formal-half language and the C++ subset"), map 16
items 2, 4 and 13, 17 item 5, 10 item 4, 15 item 5, 26 item 4, 12 item 1.
Code: `swdb/formal_frame.py` (frame), `swdb/acsl_subset.py` (allowed ACSL), `swdb/framac.py` (Frama-C).
Tests: `tests/test_formal_frame.py`. Tables: [database.md](database.md#formal-half-frame-tables).

**In one line:** a library entry with `formal_frame: 1` carries ACSL formal halves with a proof
placement per clause, and `swdb validate` says at once whether the frame is complete and the ACSL is in
the allowed subset and type-checks.

## Entry fields

| Field | Where | Meaning |
|---|---|---|
| `formal_frame` | any entry | `1`: the entry is written in this frame. Without it no frame field is allowed, and the entry gives no proven verdict. |
| `version` | frame entries | Dotted numbers as a quoted string (`"1.0"`). `once` placements and version ranges name it. |
| `proof_unit` | entries with `acsl`, frame rewrite contracts | `{source, function, types?}`: `source` pins the baseline proof unit's C++ file (`root`, `path`, `sha256`), `function` names it. The formal halves type-check against the C lowering of its signature (`swdb lower`, kept C++ names, no renaming layer; ticket 21). A hand-written `prototype` is refused. `types` pins a C header. Without clang 22.1.8 every formal half is reported unchecked; a baseline outside the core subset is refused. |
| `concurrency_frame` | frame rewrite contracts (required) | One row per interface array: `array`, `shared_actions` (vocabulary `shared_action_kinds`; empty list allowed), `history_reads` (YAML yes/no). Ticket 21: every pointer parameter of the lowered proof unit has a row, and every row names one. |
| `contract_role` | rewrite contracts (optional) | `offload_only` or `enabling`. The smallest marker the checks need. |
| `required_enabling_contracts` | offload-only contracts (required there only) | Ordered list of `{contract, versions}`. Each names an `enabling` contract; `versions` is comma-separated bounds (`">=2.0, <3.0"`). `swdb build` keeps the written order. |
| `enables` | never | Refused: an enabling contract never lists what it enables. |
| `rules` | `proof_semantics` entries | Each `{id, statement, cites | assumed}`: `cites: {gem5_commit, path, lines}` or `assumed: {owner}`, exactly one. |

A proof-semantics entry is the new kind `proof_semantics` (folder `library/proof_semantics/`, ID prefix
`semantics.`). It needs `formal_frame`, `version`, `rules` and an empty `clauses` list. The ACSL of each
rule comes with tickets 27 and 28.

## Clause fields

| Field | Meaning |
|---|---|
| `acsl` | `{text, uses}`: the formal half and the logic-library entry IDs it calls (`logic.<name>`). Optional; a clause with `acsl` needs no `formal` or `natural_language_only`. The existing `formal` field stays for tests and probes. |
| `proof_placement` | Required in a frame entry. `per_candidate`; `{once: self}` or `{once: <entry>@<version>}` (the entry and version must be in the library); or `{assumed: {kind, rule or owner, evidence}}` with a kind from vocabulary `proof_assumption_kinds`. A `rule` is `<proof_semantics entry>#<rule id>`. Separate from `discharge_mode`. |

## Allowed ACSL (map 16 item 2)

| Rule | Passes | Refused |
|---|---|---|
| Clause kinds | `requires`, `ensures`, `assigns` with `\nothing`, single locations, bounded ranges | `behavior`, `assigns \everything`, an unbounded range, any other clause kind |
| Quantifiers | `\forall integer k; lo <= k < hi ==> ...`, `\exists integer k; lo <= k < hi && ...` | no lower or upper bound in a plain comparison chain of the guard; a non-integer variable (`real`, pointers); `\lambda` and so `\sum`, `\numof`, ... |
| Labels | `\old(e)`, `\at(e, Pre)` | `\at` with any other label |
| Arithmetic | integer and `real` | floating-point built-ins (`\round_double`, ...); the types `float` and `double` |
| Built-ins | `\valid`, `\separated`, `\result`, `\true`, `\false`, `\null`, `\nothing` | any other (`\block_length`, `\initialized`, `\valid_read`, ...) |
| Logic calls | a definition in a listed logic-library entry | a name defined in the formal half itself or in no listed entry; reaching an inductive predicate or an axiom-only name |
| Definitions in a formal half | none | `logic`, `predicate`, `lemma`, `inductive`, `axiomatic`, `axiom` |

## Logic-library files

- `library/logic/<name>.acsl`, entry ID `logic.<name>`: plain ACSL global annotations (no `/*@ */`).
- Allowed: `logic` and `predicate` definitions with a body, `inductive` definitions, `lemma`s.
- A definition is non-recursive or primitive recursive: every recursive call passes `n - 1` of one
  integer parameter `n`, and the body is `n <= 0 ? base : step` (or, for a predicate,
  `n <= 0 || step`) with no recursive call in the base. Mutual recursion is refused.
- No `axiom`, no `axiomatic` block, no declaration without a body.
- Definition bodies follow the expression rules above, except that labels are free; lemma and
  inductive-case bodies are free (they are proven, never executed).
- Ticket 26 (done): a `// version:` first line, an entry's own file beside its YAML, a Frama-C type check per
  file, pins and the `\false` check: [format-v0.4-logic-library.md](format-v0.4-logic-library.md).

## Frama-C

- `swdb validate` type-checks every formal half that passes the subset with Frama-C 33.0: the used
  logic files, then the formal half, then the prototype, parsed with `-machdep x86_64` and annotation
  errors fatal. Frama-C's message is attached to the refusal.
- Frama-C comes from `SWDB_FRAMA_C` (a command line; `none` disables it), else the opam switch
  `framac-33`, else `frama-c` on PATH. Another version counts as missing.
- **Missing Frama-C:** each `acsl` field is printed as `UNCHECKED: ...` and counted in the `OK` line
  ("N acsl field(s) unchecked"); never as valid. The run still exits 0.

## For later tickets

- 21 (done): `proof_unit.source` + `function` replace the prototype; the concurrency frame names every
  pointer parameter of the proof unit.
- 26 (done): real logic files in `library/logic/` (`csr_graph`, `sets`, `access`, `sum`); see the logic-library doc.
- 30/31: placements on real entries (new entry versions in the frame).
- 36: refuse an entry without `formal_frame` (or a clause without placement) at proof time.
- 44: compare vocabulary `shared_action_kinds` with the Rocq constructors.
- 52: check a lineage against `required_enabling_contracts` (range grammar: `swdb.formal_frame.RANGE`; each
  bound is `>=`, `>`, `<=`, `<` or `==` and a dotted version).

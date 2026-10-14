# Method-version files (`library/methods/<version>.yaml`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 11.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/11-method-version-and-failure-classes.md`;
design: `.scratch/formal-verification-2026-10-09/spec.md` ("Records and levels"), map 26 item 3, S8.
Schema: `schemas/library/method_version.schema.json`. Code: `swdb/method_version.py`.

**In one line:** one reviewed file per method version lists everything a candidate artifact's
proofs use apart from the rewrite contract, the candidate artifact and the proof semantics; every
proof record pins it by ID and file sha256.

## Rules

- **Where:** `library/methods/<version>.yaml`, ID `method.<version>` (the file name).
- **Never edited in place.** Changing any byte makes a new method version (glossary): write a new
  file with a higher `sequence`. A proof record whose pin's sha256 no longer matches its file fails
  `swdb validate`; the fix is a new file, never an edited record.
- **Old files stay**, so old pins still resolve. The current method version is the one with the
  highest `sequence`; `swdb prove` pins it. Ticket 10's level rule decides that a record pinning an
  older one no longer counts.
- **Drafts and the freeze.** `status` is `draft` or `frozen`. A draft may mark a section
  `{not_yet_built: <sentence>}`; a frozen file may not. The ticket that lands a section writes the
  next draft; 59 freezes one after Yan-Ru's review.
- **Evidence kind:** `contract_fixture` only so far (tests). Ticket 21 adds the value for the first
  real method version once the lineup is installed.

## Fields

| Field | Meaning |
|---|---|
| `id`, `kind` (`method_version`), `sequence`, `status`, `created`, `evidence_kind`, `description` | identity and state |
| `lineup` | every tool, solver and front end: `{role, tool, version, flags, commit?}`. `version` is one exact version (digits and dots: no range, wildcard or `latest`); `flags` is required (an explicit `[]` passes) |
| `civl` | CIVL settings (its k is in `budgets`) |
| `genmc` | GenMC settings |
| `openmp_runtime` | the OpenMP runtime |
| `c_lowering` | `subset`, `translators`, `naming_rules` (references `{id, sha256}`) |
| `acsl_version` | the ACSL language version |
| `proof_hint_vocabulary` | the allowed proof-hint kinds |
| `checks` | `proof_setup_check`, `proof_hint_check`, `verdict_reading`, each `{version}` |
| `budgets` | per candidate: `hint_rounds` (start 10), `hint_loop_wall_minutes` (60), `bounded_job_minutes` (15), `counterexample_repair_rounds` (5) (25 item 2); `wp_seconds_per_solver` (30; 13 item 11); `civl_k` (3, at least 2; 15 item 9, S8) |
| `prompts` | the prompts, as references |
| `shared_action_kinds` | the shared-action kinds |
| `sharing_classes` | the sharing-class names (S8) |
| `logic_library` | `{id, sha256, sum_library}`: the shared logic library, the sum library included |
| `models` | `std_vector`, `std_pair` (S8) |
| `rocq_development` | `{id, sha256, composition_theorem, dx100_reduction_lemma}` (S8; tickets 41-43) |
| `ghost_capacity_k` | ghost capacity K |

`swdb validate` names each missing section, part or budget. Kept out, as decided: the proof
semantics (its own version, owned by the hardware target) and the level rule (versioned apart, so
a rule change never voids proofs).

## For later tickets

- `swdb.method_version.current(library_root)`, `.pin(version)`, `.pin_problem(pin, library_root)`,
  `.load(library_root)`, `.sections()`.
- 14 reads `budgets.bounded_job_minutes` and `budgets.civl_k`; 16 reads the per-candidate budgets;
  36 confirms each run matches the file; 59 refuses `not_yet_built` and freezes a version.
